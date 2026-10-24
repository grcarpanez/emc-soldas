"""
Serviços e regras de negócio para o Módulo de Tesouraria, Contas a Pagar/Receber e Caixa Real.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 10).
"""
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError

from apps.financeiro.models import (
    ContaBancaria,
    MeioPagamento,
    CategoriaFinanceira,
    LancamentoFinanceiro,
    LogEstorno
)
from core.utils import sanitizar_texto_maiusculo

logger = logging.getLogger('apps.financeiro')


def obter_ou_criar_categoria_taxa():
    """Obtém ou cria categoria financeira de DESPESA para taxas de maquininha de cartão."""
    categoria = CategoriaFinanceira.objects.filter(
        tipo='DESPESA',
        nome__icontains='TAXA',
        deleted_at__isnull=True
    ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.filter(
            tipo='DESPESA',
            deleted_at__isnull=True
        ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.create(
            nome='TAXAS DE CARTAO E BANCARIAS',
            tipo='DESPESA'
        )
    return categoria


def obter_ou_criar_categoria_iss_retido():
    """Obtém ou cria categoria financeira de DESPESA / DEDUÇÃO para retenções tributárias (ISS)."""
    categoria = CategoriaFinanceira.objects.filter(
        tipo='DESPESA',
        nome__icontains='ISS',
        deleted_at__isnull=True
    ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.filter(
            tipo='DESPESA',
            nome__icontains='IMPOSTO',
            deleted_at__isnull=True
        ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.create(
            nome='IMPOSTOS E RETENCOES NA FONTE (ISS)',
            tipo='DESPESA'
        )
    return categoria


def obter_ou_criar_categoria_transferencia():
    """Obtém ou cria categoria de TRANSFERÊNCIA (neutra para o DRE)."""
    categoria = CategoriaFinanceira.objects.filter(
        tipo='TRANSFERENCIA',
        deleted_at__isnull=True
    ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.create(
            nome='TRANSFERENCIA INTER-CONTAS (NEUTRA)',
            tipo='TRANSFERENCIA'
        )
    return categoria


@transaction.atomic
def liquidar_lancamento(lancamento, conta_id, meio_pagamento_id=None, data_pagamento=None,
                       valor_pago=None, valor_liquido_recebido=None, valor_iss_retido=None, user=None):
    """
    Realiza a baixa (liquidação) de um título a pagar ou a receber.
    Regras de Negócio e Contábeis:
    1. Apenas títulos em status 'A_VENCER' ou 'VENCIDO' podem ser liquidados.
    2. Validação de Cheque Especial: Para saídas, saldo - valor não pode ultrapassar o limite negativo da conta.
    3. Taxa de Maquininha: Se informado valor_liquido_recebido < valor_pago (e meio permite taxa),
       registra a entrada pelo valor total e cria automaticamente uma linha de saída de taxa vinculada na mesma conta.
    4. Retenção de ISS: Se informado valor_iss_retido > 0, cria uma linha de despesa de dedução tributária de ISS
       e desconta do valor creditado em conta bancária.
    5. Baixa Parcial: Se valor_pago < lancamento.valor, cria um novo lançamento PAGO com o valor liquidado
       e preserva a diferença no lançamento original como A_VENCER.
    6. Cascata de Fatura: Se o título pertence a uma Fatura e todas as parcelas foram quitadas, transita Fatura/Orçamentos para PAGO.
    """
    if lancamento.status_pagamento == 'PAGO':
        raise ValidationError({'status_pagamento': 'Este título já se encontra pago/liquidado.'})
    if lancamento.status_pagamento == 'CANCELADO':
        raise ValidationError({'status_pagamento': 'Não é possível liquidar um título que foi cancelado.'})

    # Blindagem de Cartões: Compras individuais não podem ser liquidadas avulsamente
    if lancamento.fatura_cartao_id and not lancamento.is_fatura_cartao_consolidada:
        raise ValidationError({
            'detail': 'Compras efetuadas pelo cartão de crédito não podem ser baixadas individualmente. A liquidação deve ser realizada exclusivamente através da fatura do cartão.'
        })

    # Se for o título consolidado da fatura de cartão, delega para a liquidação oficial da fatura
    if lancamento.is_fatura_cartao_consolidada and lancamento.fatura_cartao:
        from apps.financeiro.services_cartao import liquidar_fatura_cartao
        liquidar_fatura_cartao(
            fatura=lancamento.fatura_cartao,
            valor_pago=valor_pago or lancamento.valor,
            conta_id=conta_id,
            data_pagamento=data_pagamento,
            user=user
        )
        lancamento.refresh_from_db()
        return lancamento

    conta = ContaBancaria.objects.filter(id=conta_id, deleted_at__isnull=True).first()
    if not conta:
        raise ValidationError({'conta_id': 'Conta bancária informada não encontrada ou inativa.'})

    meio_pagamento = None
    if meio_pagamento_id:
        meio_pagamento = MeioPagamento.objects.filter(id=meio_pagamento_id, ativo=True, deleted_at__isnull=True).first()
        if not meio_pagamento:
            raise ValidationError({'meio_pagamento_id': 'Meio de pagamento informado não encontrado ou inativo.'})
    else:
        meio_pagamento = lancamento.meio_pagamento

    if not data_pagamento:
        data_pagamento = timezone.now()

    valor_total_titulo = lancamento.valor
    if valor_pago is None:
        valor_pago = valor_total_titulo
    else:
        valor_pago = Decimal(str(valor_pago))

    if valor_pago <= Decimal('0.00'):
        raise ValidationError({'valor_pago': 'O valor de liquidação deve ser maior que zero.'})

    if valor_pago > valor_total_titulo:
        raise ValidationError({'valor_pago': f"O valor pago (R$ {valor_pago}) não pode ser maior que o saldo do título (R$ {valor_total_titulo})."})

    # Processamento de Taxa de Maquininha e ISS Retido (apenas em ENTRADA)
    taxa_maquininha = Decimal('0.00')
    if lancamento.tipo_lancamento == 'ENTRADA':
        if valor_liquido_recebido is not None:
            valor_liquido_recebido = Decimal(str(valor_liquido_recebido))
            if valor_liquido_recebido < Decimal('0.00'):
                raise ValidationError({'valor_liquido_recebido': 'O valor líquido recebido não pode ser negativo.'})
            if valor_liquido_recebido > valor_pago:
                raise ValidationError({'valor_liquido_recebido': 'O valor líquido recebido não pode ser maior que o valor bruto pago.'})
            taxa_maquininha = valor_pago - valor_liquido_recebido

        iss_retido = Decimal('0.00')
        if valor_iss_retido is not None:
            iss_retido = Decimal(str(valor_iss_retido))
            if iss_retido < Decimal('0.00'):
                raise ValidationError({'valor_iss_retido': 'O valor do ISS retido não pode ser negativo.'})
            if (taxa_maquininha + iss_retido) > valor_pago:
                raise ValidationError({'valor_iss_retido': 'A soma da taxa de maquininha com o ISS retido não pode superar o valor bruto pago.'})

        # Impacto líquido que efetivamente entra no caixa
        impacto_caixa = valor_pago - taxa_maquininha - iss_retido
    else:
        # SAÍDA (Despesa)
        impacto_caixa = -valor_pago
        iss_retido = Decimal('0.00')

        # Validação de Cheque Especial
        saldo_resultante = conta.saldo + impacto_caixa
        limite_minimo = -conta.limite_credito
        if saldo_resultante < limite_minimo:
            raise ValidationError({
                'conta_id': f"Operação bloqueada por limite de cheque especial. "
                            f"Saldo atual: R$ {conta.saldo}, Limite: R$ {conta.limite_credito}, "
                            f"Saldo resultante seria R$ {saldo_resultante} (Mínimo tolerado: R$ {limite_minimo})."
            })

    # Verifica se a baixa é integral ou parcial
    is_baixa_integral = (valor_pago == valor_total_titulo)

    if is_baixa_integral:
        lancamento_liquidado = lancamento
        lancamento_liquidado.status_pagamento = 'PAGO'
        lancamento_liquidado.data_pagamento = data_pagamento
        lancamento_liquidado.conta = conta
        if meio_pagamento:
            lancamento_liquidado.meio_pagamento = meio_pagamento
        lancamento_liquidado.updated_by_id = getattr(user, 'id', None)
        lancamento_liquidado.save()
    else:
        # Baixa parcial: atualiza o saldo restante no lançamento original e cria um novo para a parte paga
        valor_restante = valor_total_titulo - valor_pago
        lancamento.valor = valor_restante
        lancamento.updated_by_id = getattr(user, 'id', None)
        lancamento.save(update_fields=['valor', 'updated_at', 'updated_by_id'])

        lancamento_liquidado = LancamentoFinanceiro.objects.create(
            origem=lancamento.origem,
            fatura=lancamento.fatura,
            conta=conta,
            meio_pagamento=meio_pagamento,
            cartao_credito=lancamento.cartao_credito,
            fatura_cartao=lancamento.fatura_cartao,
            categoria=lancamento.categoria,
            tipo_lancamento=lancamento.tipo_lancamento,
            descricao=f"{lancamento.descricao or lancamento.categoria.nome} (BAIXA PARCIAL)",
            valor=valor_pago,
            data_vencimento=lancamento.data_vencimento,
            data_pagamento=data_pagamento,
            status_pagamento='PAGO',
            created_by_id=getattr(user, 'id', None)
        )

    # Atualiza saldo real da Conta Bancária
    conta.saldo += impacto_caixa
    conta.save(update_fields=['saldo', 'updated_at'])

    # Criação automática de lançamentos auxiliares de deduções (Taxa e ISS)
    if lancamento.tipo_lancamento == 'ENTRADA':
        if taxa_maquininha > Decimal('0.00'):
            categoria_taxa = obter_ou_criar_categoria_taxa()
            LancamentoFinanceiro.objects.create(
                fatura=lancamento.fatura,
                conta=conta,
                meio_pagamento=meio_pagamento,
                categoria=categoria_taxa,
                tipo_lancamento='SAIDA',
                descricao=f"TAXA DE MAQUININHA / CARTAO - REF. TITULO #{lancamento_liquidado.id}",
                valor=taxa_maquininha,
                data_vencimento=data_pagamento.date() if hasattr(data_pagamento, 'date') else data_pagamento,
                data_pagamento=data_pagamento,
                status_pagamento='PAGO',
                created_by_id=getattr(user, 'id', None)
            )

        if iss_retido > Decimal('0.00'):
            categoria_iss = obter_ou_criar_categoria_iss_retido()
            LancamentoFinanceiro.objects.create(
                fatura=lancamento.fatura,
                conta=conta,
                meio_pagamento=meio_pagamento,
                categoria=categoria_iss,
                tipo_lancamento='SAIDA',
                descricao=f"RETENCAO DE ISS NA FONTE - REF. TITULO #{lancamento_liquidado.id}",
                valor=iss_retido,
                data_vencimento=data_pagamento.date() if hasattr(data_pagamento, 'date') else data_pagamento,
                data_pagamento=data_pagamento,
                status_pagamento='PAGO',
                created_by_id=getattr(user, 'id', None)
            )

    # Cascata de quitação de Fatura
    if lancamento.fatura_id:
        fatura = lancamento.fatura
        pendencias = fatura.lancamentos_financeiros.filter(
            tipo_lancamento='ENTRADA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            deleted_at__isnull=True
        ).exists()

        if not pendencias:
            total_pago = fatura.lancamentos_financeiros.filter(
                tipo_lancamento='ENTRADA',
                status_pagamento='PAGO',
                deleted_at__isnull=True
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

            if total_pago >= fatura.valor_total_faturado:
                fatura.status = 'PAGA'
                fatura.updated_by_id = getattr(user, 'id', None)
                fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])
                fatura.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
                    status_financeiro='PAGO',
                    updated_at=timezone.now()
                )
                logger.info(f"[FATURA QUITADA EM CASCATA] Fatura #{fatura.id} quitada via liquidação de lançamento.")

    logger.info(f"[LANCAMENTO LIQUIDADO] #{lancamento_liquidado.id} ({lancamento.tipo_lancamento}) R$ {valor_pago} na conta '{conta.nome}'.")
    return lancamento_liquidado


@transaction.atomic
def cancelar_lancamento(lancamento, motivo_cancelamento, user=None):
    """
    Cancela um título financeiro pendente (A_VENCER ou VENCIDO).
    Exige justificativa obrigatória com no mínimo 10 caracteres.
    Não altera saldo bancário pois o título não estava pago.
    """
    if lancamento.status_pagamento == 'PAGO':
        raise ValidationError({
            'status_pagamento': 'Não é permitido cancelar diretamente um título já pago. Utilize a função de Estorno.'
        })
    if lancamento.status_pagamento == 'CANCELADO':
        raise ValidationError({'status_pagamento': 'Este título já está cancelado.'})

    motivo = sanitizar_texto_maiusculo(motivo_cancelamento or '')
    if len(motivo) < 10:
        raise ValidationError({'motivo_cancelamento': 'A justificativa de cancelamento deve conter no mínimo 10 caracteres.'})

    lancamento.status_pagamento = 'CANCELADO'
    lancamento.motivo_cancelamento = motivo
    lancamento.updated_by_id = getattr(user, 'id', None)
    lancamento.save(update_fields=['status_pagamento', 'motivo_cancelamento', 'updated_at', 'updated_by_id'])

    logger.info(f"[LANCAMENTO CANCELADO] #{lancamento.id} cancelado por {getattr(user, 'nome', 'Admin')}. Motivo: {motivo}")
    return lancamento


@transaction.atomic
def estornar_lancamento(lancamento, justificativa, user=None):
    """
    Estorna uma baixa de caixa / título PAGO, revertendo seu impacto no saldo bancário.
    Regras:
    1. Apenas títulos 'PAGO' podem ser estornados.
    2. Exige justificativa com no mínimo 10 caracteres.
    3. Reverte o saldo na ContaBancaria:
       - Se ENTRADA: debita da conta (validando se a conta suporta o débito com cheque especial).
       - Se SAIDA: credita de volta na conta.
    4. Anula/estorna automaticamente despesas de Taxa de Maquininha e ISS retido geradas na baixa do título.
    5. Se for Conta Agendada (origem 'AGENDA', 'FATURA', 'CARTAO'):
       - Reverte o status do lançamento para 'A_VENCER', limpa data_pagamento e conta, retornando à agenda financeira.
       - Se vinculado a uma Fatura que estava PAGA, reverte o status da Fatura para FATURADA e orçamentos para FATURADO.
    6. Se for Lançamento Avulso ou Conciliação (origem 'AVULSO', 'CONCILIACAO'):
       - Marca status como 'CANCELADO' com a justificativa informada.
       - Aplica Soft Delete, não gerando conta a pagar em aberto na agenda financeira.
    7. Grava registro perpétuo e imutável na tabela LogEstorno.
    """
    if lancamento.status_pagamento != 'PAGO':
        raise ValidationError({'status_pagamento': f"Apenas lançamentos com status PAGO podem ser estornados. Status atual: {lancamento.get_status_pagamento_display()}."})

    justificativa_sanitizada = sanitizar_texto_maiusculo(justificativa or '')
    if len(justificativa_sanitizada) < 10:
        raise ValidationError({'justificativa': 'A justificativa do estorno deve conter no mínimo 10 caracteres.'})

    if not user or not user.is_authenticated:
        raise ValidationError({'usuario': 'Usuário autenticado obrigatório para efetuar estorno.'})

    conta = lancamento.conta

    # 1. Localiza lançamentos auxiliares de taxa e ISS vinculados a este título
    sub_lancamentos_taxas = LancamentoFinanceiro.objects.filter(
        descricao__icontains=f"REF. TITULO #{lancamento.id}",
        tipo_lancamento='SAIDA',
        status_pagamento='PAGO',
        deleted_at__isnull=True
    )

    total_taxas_a_reverter = Decimal('0.00')
    for sub in sub_lancamentos_taxas:
        total_taxas_a_reverter += sub.valor
        sub.status_pagamento = 'CANCELADO'
        sub.motivo_cancelamento = f"ESTORNO DO TITULO PAI #{lancamento.id} - {justificativa_sanitizada}"
        sub.updated_by_id = user.id
        sub.save()

    # 2. Reversão do impacto no saldo bancário
    if conta:
        if lancamento.tipo_lancamento == 'ENTRADA':
            # Valor que realmente havia entrado líquido na conta
            valor_liquido_entrado = lancamento.valor - total_taxas_a_reverter
            novo_saldo = conta.saldo - valor_liquido_entrado
            limite_minimo = -conta.limite_credito
            if novo_saldo < limite_minimo:
                raise ValidationError({
                    'conta': f"Não é possível estornar a entrada pois o saldo da conta ficaria abaixo do limite de cheque especial. "
                             f"Saldo atual: R$ {conta.saldo}, Débito do estorno: R$ {valor_liquido_entrado}, Limite: R$ {conta.limite_credito}."
                })
            conta.saldo = novo_saldo
            conta.save(update_fields=['saldo', 'updated_at'])
        elif lancamento.tipo_lancamento == 'SAIDA':
            # Devolve o dinheiro gasto para a conta
            conta.saldo += lancamento.valor
            conta.save(update_fields=['saldo', 'updated_at'])
        elif lancamento.tipo_lancamento == 'TRANSFERENCIA':
            # Reverte a transferência inter-contas
            conta_origem = lancamento.conta
            conta_destino = lancamento.conta_destino
            if conta_origem and conta_destino:
                conta_destino.saldo -= lancamento.valor
                conta_origem.saldo += lancamento.valor
                conta_destino.save(update_fields=['saldo', 'updated_at'])
                conta_origem.save(update_fields=['saldo', 'updated_at'])

    # 3. Transição ou Exclusão (Soft Delete) conforme a natureza do lançamento
    eh_conta_agendada = getattr(lancamento, 'eh_conta_agendada', False)
    if not eh_conta_agendada:
        eh_conta_agendada = (
            lancamento.origem in ['AGENDA', 'FATURA', 'CARTAO'] or
            bool(lancamento.fatura_id) or
            bool(lancamento.fatura_cartao_id)
        )

    if eh_conta_agendada:
        # Conta da agenda financeira liquidada por engano: retorna ao estado 'A_VENCER'
        lancamento.status_pagamento = 'A_VENCER'
        lancamento.data_pagamento = None
        lancamento.conta = None
        lancamento.updated_by_id = user.id
        lancamento.save(update_fields=['status_pagamento', 'data_pagamento', 'conta', 'updated_at', 'updated_by_id'])
        tipo_acao = 'RETORNADO_AGENDA'

        # 4. Reversão de Fatura/Orçamentos caso necessário
        if lancamento.fatura_id:
            fatura = lancamento.fatura
            if fatura.status == 'PAGA':
                fatura.status = 'FATURADA'
                fatura.updated_by_id = user.id
                fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])
                fatura.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
                    status_financeiro='FATURADO',
                    updated_at=timezone.now()
                )
                logger.info(f"[FATURA REVERTIDA PARA FATURADA] Fatura #{fatura.id} revertida devido ao estorno do lançamento #{lancamento.id}.")
    else:
        # Lançamento Avulso / Compra Direta / Conciliação: não gera conta a pagar, aplica Soft Delete
        lancamento.status_pagamento = 'CANCELADO'
        lancamento.motivo_cancelamento = f"ESTORNO: {justificativa_sanitizada}"
        lancamento.updated_by_id = user.id
        lancamento.save(update_fields=['status_pagamento', 'motivo_cancelamento', 'updated_at', 'updated_by_id'])
        lancamento.delete(user_id=user.id)
        tipo_acao = 'EXCLUIDO_AVULSO'

    # 5. Gravação perpétua em LogEstorno
    log_estorno = LogEstorno.objects.create(
        lancamento=lancamento,
        usuario=user,
        justificativa=justificativa_sanitizada,
        data_estorno=timezone.now()
    )

    logger.info(f"[ESTORNO CONCLUIDO] Log #{log_estorno.id} ({tipo_acao}) para Lançamento #{lancamento.id} por {getattr(user, 'nome', 'Admin')}.")
    return {
        'lancamento': lancamento,
        'log_estorno': log_estorno,
        'tipo_acao': tipo_acao
    }


@transaction.atomic
def transferir_inter_contas(conta_origem_id, conta_destino_id, valor, descricao=None, data_transferencia=None, comprovante_path=None, nome_arquivo_comprovante=None, user=None):
    """
    Executa uma transferência de fundos entre duas contas bancárias da empresa.
    Operação estritamente atômica e neutra para o DRE.
    1. Validação de contas distintas e ativas.
    2. Checagem de limite de cheque especial na conta de origem.
    3. Débito no saldo de origem e crédito no saldo de destino.
    4. Criação do lançamento financeiro do tipo 'TRANSFERENCIA' com status 'PAGO'.
    """
    if conta_origem_id == conta_destino_id:
        raise ValidationError({'conta_destino_id': 'A conta de destino deve ser diferente da conta de origem.'})

    conta_origem = ContaBancaria.objects.filter(id=conta_origem_id, deleted_at__isnull=True).first()
    if not conta_origem:
        raise ValidationError({'conta_origem_id': 'Conta de origem não encontrada ou inativa.'})

    conta_destino = ContaBancaria.objects.filter(id=conta_destino_id, deleted_at__isnull=True).first()
    if not conta_destino:
        raise ValidationError({'conta_destino_id': 'Conta de destino não encontrada ou inativa.'})

    valor = Decimal(str(valor))
    if valor <= Decimal('0.00'):
        raise ValidationError({'valor': 'O valor da transferência deve ser maior que zero.'})

    # Validação de Cheque Especial na Origem
    saldo_apos_debito = conta_origem.saldo - valor
    limite_tolerado = -conta_origem.limite_credito
    if saldo_apos_debito < limite_tolerado:
        raise ValidationError({
            'conta_origem_id': f"Transferência bloqueada por saldo insuficiente. "
                               f"Saldo disponível na conta de origem: R$ {conta_origem.saldo}, "
                               f"Limite de crédito: R$ {conta_origem.limite_credito}, "
                               f"Tentativa de débito: R$ {valor}."
        })

    if not data_transferencia:
        data_transferencia = timezone.now()

    # 1. Movimentação dos saldos
    conta_origem.saldo -= valor
    conta_destino.saldo += valor
    conta_origem.save(update_fields=['saldo', 'updated_at'])
    conta_destino.save(update_fields=['saldo', 'updated_at'])

    # 2. Criação do registro
    categoria_transf = obter_ou_criar_categoria_transferencia()
    desc = sanitizar_texto_maiusculo(descricao or f"TRANSFERENCIA DE {conta_origem.nome} PARA {conta_destino.nome}")

    lancamento = LancamentoFinanceiro.objects.create(
        conta=conta_origem,
        conta_destino=conta_destino,
        categoria=categoria_transf,
        tipo_lancamento='TRANSFERENCIA',
        descricao=desc,
        valor=valor,
        comprovante=comprovante_path or None,
        nome_arquivo_comprovante=nome_arquivo_comprovante or None,
        data_vencimento=data_transferencia.date() if hasattr(data_transferencia, 'date') else data_transferencia,
        data_pagamento=data_transferencia,
        status_pagamento='PAGO',
        created_by_id=getattr(user, 'id', None)
    )

    logger.info(f"[TRANSFERENCIA CONCLUIDA] R$ {valor} de '{conta_origem.nome}' para '{conta_destino.nome}'. Lançamento #{lancamento.id}.")
    return lancamento


def obter_resumo_financeiro():
    """
    Retorna métricas consolidadas de Tesouraria e Competência:
    - Saldo Total em Contas Bancárias (Caixa Real)
    - Total a Pagar (A Vencer e Vencido)
    - Total a Receber (A Vencer e Vencido)
    - Total Inadimplente / Vencido
    """
    saldo_total_contas = ContaBancaria.objects.filter(
        deleted_at__isnull=True
    ).aggregate(total=Sum('saldo'))['total'] or Decimal('0.00')

    hoje = timezone.localdate()

    # Contas a Pagar
    a_pagar_a_vencer = LancamentoFinanceiro.objects.filter(
        tipo_lancamento='SAIDA',
        status_pagamento='A_VENCER',
        data_vencimento__gte=hoje,
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    a_pagar_vencido = LancamentoFinanceiro.objects.filter(
        tipo_lancamento='SAIDA',
        status_pagamento__in=['A_VENCER', 'VENCIDO'],
        data_vencimento__lt=hoje,
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    # Contas a Receber
    a_receber_a_vencer = LancamentoFinanceiro.objects.filter(
        tipo_lancamento='ENTRADA',
        status_pagamento='A_VENCER',
        data_vencimento__gte=hoje,
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    a_receber_vencido = LancamentoFinanceiro.objects.filter(
        tipo_lancamento='ENTRADA',
        status_pagamento__in=['A_VENCER', 'VENCIDO'],
        data_vencimento__lt=hoje,
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    return {
        'saldo_total_caixa': float(saldo_total_contas),
        'contas_a_pagar': {
            'a_vencer': float(a_pagar_a_vencer),
            'vencido': float(a_pagar_vencido),
            'total': float(a_pagar_a_vencer + a_pagar_vencido)
        },
        'contas_a_receber': {
            'a_vencer': float(a_receber_a_vencer),
            'vencido': float(a_receber_vencido),
            'total': float(a_receber_a_vencer + a_receber_vencido)
        }
    }


import uuid

@transaction.atomic
def registrar_compra_multi_meio(dados_compra=None, matriz_pagamento=None, comprovante_file=None, nome_arquivo_comprovante=None, user=None, **kwargs):
    """
    Registra uma despesa / compra paga com MÚLTIPLAS FORMAS DE PAGAMENTO (Split Payment).
    Regras de Negócio e Integridade:
    1. Valida que a soma de todos os pagamentos da matriz é rigorosamente igual ao valor total da compra.
    2. Gera um grupo_pagamento_id (UUID) unificado vinculando todas as parcelas/lançamentos.
    3. Replica o arquivo de comprovante / NF para todas as transações geradas.
    4. Atualiza o saldo real de contas bancárias e caixa físico imediatamente para pagamentos à vista.
    5. Para pagamentos em cartão, fragmenta nas faturas correspondentes comprometendo limite.
    """
    from apps.financeiro.models import CartaoCredito
    from apps.financeiro.services_cartao import lancar_despesa_cartao

    # Unifica parâmetros flexíveis
    if not isinstance(dados_compra, dict):
        dados_compra = {
            'valor_total': kwargs.get('valor_total') or dados_compra,
            'categoria_id': kwargs.get('categoria_id'),
            'descricao': kwargs.get('descricao', ''),
            'data_compra': kwargs.get('data_compra'),
            'cliente_fornecedor_id': kwargs.get('cliente_fornecedor_id')
        }
    if matriz_pagamento is None:
        matriz_pagamento = kwargs.get('matriz_pagamentos') or kwargs.get('matriz_pagamento')
    if comprovante_file is None:
        comprovante_file = kwargs.get('comprovante') or kwargs.get('comprovante_file')
    if nome_arquivo_comprovante is None:
        nome_arquivo_comprovante = kwargs.get('nome_arquivo_comprovante', '')

    descricao = sanitizar_texto_maiusculo(dados_compra.get('descricao') or 'COMPRA / DESPESA MULTI-MEIO')
    categoria_id = dados_compra.get('categoria_id')
    categoria = CategoriaFinanceira.objects.filter(id=categoria_id, deleted_at__isnull=True).first()
    if not categoria:
        raise ValidationError({'categoria_id': 'Categoria financeira informada não encontrada ou inativa.'})

    valor_total = Decimal(str(dados_compra.get('valor_total', 0)))
    if valor_total <= Decimal('0.00'):
        raise ValidationError({'valor_total': 'O valor total da compra deve ser maior que zero.'})

    if not matriz_pagamento or not isinstance(matriz_pagamento, list):
        raise ValidationError({'matriz_pagamento': 'A matriz de formas de pagamento é obrigatória e deve ser uma lista.'})

    data_compra = dados_compra.get('data_compra')
    if not data_compra:
        data_compra = timezone.localdate()
    elif isinstance(data_compra, str):
        data_compra = timezone.datetime.fromisoformat(data_compra).date() if 'T' in data_compra else timezone.datetime.strptime(data_compra, '%Y-%m-%d').date()

    cliente_fornecedor_id = dados_compra.get('cliente_fornecedor_id')

    # Validação matemática da soma da matriz
    soma_matriz = Decimal('0.00')
    for item in matriz_pagamento:
        v = Decimal(str(item.get('valor', 0)))
        if v <= Decimal('0.00'):
            raise ValidationError({'matriz_pagamento': 'Cada forma de pagamento deve possuir valor maior que zero.'})
        soma_matriz += v

    diferenca = abs(soma_matriz - valor_total)
    if diferenca > Decimal('0.01'):
        raise ValidationError({
            'matriz_pagamento': f"A soma das formas de pagamento (R$ {soma_matriz:.2f}) não coincide com o valor total da compra (R$ {valor_total:.2f}). Diferença: R$ {abs(soma_matriz - valor_total):.2f}."
        })

    grupo_pagamento_id = uuid.uuid4()
    lancamentos_gerados = []

    for idx, item in enumerate(matriz_pagamento, start=1):
        meio_id = item.get('meio_pagamento_id')
        cartao_id = item.get('cartao_credito_id') or item.get('cartao_id')
        tipo_meio = str(item.get('tipo_meio', '')).upper()

        meio = None
        if meio_id:
            meio = MeioPagamento.objects.filter(id=meio_id, ativo=True, deleted_at__isnull=True).first()
            if not meio:
                raise ValidationError({'matriz_pagamento': f"Meio de pagamento #{meio_id} não encontrado ou inativo (item {idx})."})
        elif cartao_id or 'CART' in tipo_meio:
            meio = MeioPagamento.objects.filter(nome__icontains='CARTAO', ativo=True, deleted_at__isnull=True).first() \
                   or MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()
        elif 'PIX' in tipo_meio:
            meio = MeioPagamento.objects.filter(nome__icontains='PIX', ativo=True, deleted_at__isnull=True).first() \
                   or MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()
        elif 'DINHEIRO' in tipo_meio or 'ESPECIE' in tipo_meio:
            meio = MeioPagamento.objects.filter(nome__icontains='DINHEIRO', ativo=True, deleted_at__isnull=True).first() \
                   or MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()
        else:
            meio = MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()

        if not meio:
            nome_default = "CARTAO DE CREDITO" if (cartao_id or 'CART' in tipo_meio) else "OUTROS"
            meio, _ = MeioPagamento.objects.get_or_create(nome=nome_default, defaults={'ativo': True})

        valor_item = Decimal(str(item.get('valor', 0)))

        # Meio Cartão de Crédito
        if cartao_id or (meio and 'CART' in meio.nome.upper() and 'CRED' in meio.nome.upper()) or 'CART' in tipo_meio:
            if not cartao_id:
                raise ValidationError({'matriz_pagamento': f"Para pagamento com cartão de crédito, informe o Cartão Corporativo (item {idx})."})
            cartao = CartaoCredito.objects.filter(id=cartao_id, deleted_at__isnull=True).first()
            if not cartao:
                raise ValidationError({'matriz_pagamento': f"Cartão corporativo #{cartao_id} não encontrado (item {idx})."})

            total_parcelas = int(item.get('total_parcelas') or 1)
            desc_custom = item.get('descricao') or f"PARC. CARTAO {cartao.nome}"
            desc_cartao = f"{descricao} - {desc_custom}"

            res_cartao = lancar_despesa_cartao(
                cartao=cartao,
                valor=valor_item,
                categoria_id=categoria.id,
                descricao=desc_cartao,
                data_compra=data_compra,
                total_parcelas=total_parcelas,
                comprovante=comprovante_file,
                nome_arquivo_comprovante=nome_arquivo_comprovante,
                grupo_pagamento_id=grupo_pagamento_id,
                cliente_fornecedor_id=cliente_fornecedor_id,
                user=user
            )

            if isinstance(res_cartao, list):
                lancamentos_gerados.extend(res_cartao)
            else:
                lancamentos_gerados.append(res_cartao)

        else:
            # Pagamento Direto: Dinheiro, PIX, Débito, Transferência ou Boleto a prazo
            conta_id = item.get('conta_id')
            is_a_prazo = str(item.get('tipo_cobranca', '')).upper() in ['A_PRAZO', 'BOLETO'] or item.get('status_pagamento') == 'A_VENCER'

            conta = None
            if conta_id:
                conta = ContaBancaria.objects.filter(id=conta_id, deleted_at__isnull=True).first()
                if not conta:
                    raise ValidationError({'matriz_pagamento': f"Conta bancária #{conta_id} não encontrada (item {idx})."})

            if not is_a_prazo and not conta:
                # Tenta fallback para a conta preferencial ou caixa físico
                conta = ContaBancaria.objects.filter(deleted_at__isnull=True).order_by('id').first()
                if not conta:
                    raise ValidationError({'matriz_pagamento': f"Informe a Conta Bancária / Caixa de saída para o pagamento em {meio.nome}."})

            data_venc = item.get('data_vencimento') or data_compra
            if isinstance(data_venc, str):
                data_venc = timezone.datetime.fromisoformat(data_venc).date() if 'T' in data_venc else timezone.datetime.strptime(data_venc, '%Y-%m-%d').date()

            status_pagto = 'A_VENCER' if is_a_prazo else 'PAGO'
            data_pagto = None if is_a_prazo else timezone.now()

            # Se for pagamento à vista no caixa/banco, valida limite de cheque especial e debita imediatamente
            if status_pagto == 'PAGO' and conta:
                saldo_resultante = conta.saldo - valor_item
                limite_minimo = -conta.limite_credito
                if saldo_resultante < limite_minimo:
                    raise ValidationError({
                        'matriz_pagamento': f"Operação bloqueada por saldo insuficiente em '{conta.nome}'. "
                                            f"Saldo: R$ {conta.saldo:.2f}, Limite: R$ {conta.limite_credito:.2f}, "
                                            f"Tentativa de débito: R$ {valor_item:.2f}."
                    })
                conta.saldo -= valor_item
                conta.save(update_fields=['saldo', 'updated_at'])

            desc_item = f"{descricao} - {meio.nome}"
            lanc = LancamentoFinanceiro.objects.create(
                origem='AVULSO',
                conta=conta,
                meio_pagamento=meio,
                categoria=categoria,
                tipo_lancamento='SAIDA',
                descricao=desc_item,
                valor=valor_item,
                data_competencia=data_compra,
                data_vencimento=data_venc,
                data_pagamento=data_pagto,
                status_pagamento=status_pagto,
                numero_parcela=idx,
                total_parcelas=len(matriz_pagamento),
                grupo_pagamento_id=grupo_pagamento_id,
                cliente_fornecedor_id=cliente_fornecedor_id,
                comprovante=comprovante_file or None,
                nome_arquivo_comprovante=nome_arquivo_comprovante or None,
                created_by_id=getattr(user, 'id', None)
            )
            lancamentos_gerados.append(lanc)
            logger.info(f"[LANCAMENTO MULTI-MEIO CRIADO] #{lanc.id} ({meio.nome}) R$ {valor_item:.2f} grupo {grupo_pagamento_id}.")

    return {
        'grupo_pagamento_id': str(grupo_pagamento_id),
        'total_lancamentos': len(lancamentos_gerados),
        'valor_total': float(valor_total),
        'lancamentos_ids': [l.id for l in lancamentos_gerados],
        'lancamentos': lancamentos_gerados
    }

