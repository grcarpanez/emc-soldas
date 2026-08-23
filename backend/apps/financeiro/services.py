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
    5. Reverte o status do lançamento para 'A_VENCER' (ou cancela se foi gerado em baixa parcial), limpa data_pagamento e conta.
    6. Se vinculado a uma Fatura que estava PAGA, reverte o status da Fatura para FATURADA e orçamentos para FATURADO.
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

    # 3. Transição do lançamento estornado
    lancamento.status_pagamento = 'A_VENCER'
    lancamento.data_pagamento = None
    lancamento.conta = None
    lancamento.updated_by_id = user.id
    lancamento.save(update_fields=['status_pagamento', 'data_pagamento', 'conta', 'updated_at', 'updated_by_id'])

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

    # 5. Gravação perpétua em LogEstorno
    log_estorno = LogEstorno.objects.create(
        lancamento=lancamento,
        usuario=user,
        justificativa=justificativa_sanitizada,
        data_estorno=timezone.now()
    )

    logger.info(f"[ESTORNO CONCLUIDO] Log #{log_estorno.id} para Lançamento #{lancamento.id} por {user.nome}.")
    return {
        'lancamento': lancamento,
        'log_estorno': log_estorno
    }


@transaction.atomic
def transferir_inter_contas(conta_origem_id, conta_destino_id, valor, descricao=None, data_transferencia=None, user=None):
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
