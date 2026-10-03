"""
Serviços e regras de negócio para o Módulo de Faturamento Agregado.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 9).
"""
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError

from apps.cadastros.models import ClienteFornecedor
from apps.orcamentos.models import Orcamento
from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.financeiro.models import (
    LancamentoFinanceiro,
    ContaBancaria,
    MeioPagamento,
    RegraPagamento,
    CategoriaFinanceira
)
from core.utils import sanitizar_texto_maiusculo

logger = logging.getLogger('apps.faturamento')


def obter_categoria_receita_padrao():
    """
    Obtém ou cria uma categoria financeira de RECEITA padrão para lançamentos de faturamento.
    """
    categoria = CategoriaFinanceira.objects.filter(
        tipo='RECEITA',
        deleted_at__isnull=True
    ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.create(
            nome='RECEITA DE PRESTACAO DE SERVICOS',
            tipo='RECEITA'
        )
    return categoria


def obter_categoria_despesa_taxa():
    """
    Obtém ou cria uma categoria financeira de DESPESA para taxas de maquininha de cartão.
    """
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


def listar_conta_corrente_cliente(cliente_id=None):
    """
    Lista os orçamentos prontos e faturáveis para a Conta Corrente de Clientes.
    Critérios:
    - deleted_at is NULL
    - status_financeiro = 'A_FATURAR'
    - fatura is NULL
    - status_operacional em ['CONCLUIDO', 'EM_EXECUCAO', 'APROVADO']
    """
    queryset = Orcamento.objects.filter(
        deleted_at__isnull=True,
        status_financeiro='A_FATURAR',
        fatura__isnull=True,
        status_operacional__in=['CONCLUIDO', 'EM_EXECUCAO', 'APROVADO']
    ).select_related(
        'cliente',
        'equipamento'
    ).prefetch_related(
        'itens_orcamento'
    ).order_by('-data_geracao', '-id')

    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)

    return queryset


@transaction.atomic
def criar_pre_fatura(cliente_id, orcamento_ids, propostas_pagamento=None, desconto_global=Decimal('0.00'), user=None):
    """
    Cria uma nova Pré-Fatura (Rascunho) agregando N orçamentos de um mesmo cliente.
    Regra estrita: Não gera títulos no Contas a Receber nesta fase.
    """
    if not orcamento_ids:
        raise ValidationError({'orcamentos': 'Selecione pelo menos um orçamento para gerar a pré-fatura.'})

    cliente = ClienteFornecedor.objects.filter(id=cliente_id, deleted_at__isnull=True).first()
    if not cliente:
        raise ValidationError({'cliente': 'Cliente não encontrado ou inativo.'})

    orcamentos = list(Orcamento.objects.filter(
        id__in=orcamento_ids,
        deleted_at__isnull=True
    ).select_related('cliente'))

    if len(orcamentos) != len(set(orcamento_ids)):
        raise ValidationError({'orcamentos': 'Um ou mais orçamentos selecionados não foram encontrados ou estão inativos.'})

    for orc in orcamentos:
        if orc.cliente_id != cliente.id:
            raise ValidationError({
                'orcamentos': f"O orçamento #{orc.id} pertence a outro cliente ({orc.cliente.nome_razao}). Todos os orçamentos devem pertencer ao mesmo cliente."
            })
        if orc.fatura_id is not None:
            raise ValidationError({
                'orcamentos': f"O orçamento #{orc.id} já está vinculado à Fatura #{orc.fatura_id}."
            })
        if orc.status_financeiro != 'A_FATURAR':
            raise ValidationError({
                'orcamentos': f"O orçamento #{orc.id} não está disponível para faturamento (Status: {orc.get_status_financeiro_display()})."
            })

    # Calcula valor bruto consolidado dos orçamentos (soma dos valores líquidos de cada um)
    valor_bruto_total = Decimal('0.00')
    for orc in orcamentos:
        valor_liq_orc = max(Decimal('0.00'), (orc.valor_bruto or Decimal('0.00')) - (orc.valor_desconto_aplicado or Decimal('0.00')))
        valor_bruto_total += valor_liq_orc

    desconto_global = Decimal(str(desconto_global or '0.00'))
    if desconto_global < Decimal('0.00'):
        raise ValidationError({'desconto_global': 'O desconto global não pode ser negativo.'})

    valor_total_faturado = max(Decimal('0.00'), valor_bruto_total - desconto_global)

    fatura = Fatura.objects.create(
        cliente=cliente,
        data_emissao=timezone.localdate(),
        status='RASCUNHO',
        valor_bruto=valor_bruto_total,
        desconto_global=desconto_global,
        valor_total_faturado=valor_total_faturado,
        created_by_id=getattr(user, 'id', None)
    )

    # Vincula os orçamentos à fatura mantendo status_financeiro 'A_FATURAR'
    for orc in orcamentos:
        orc.fatura = fatura
        orc.save(update_fields=['fatura', 'updated_at'])

    # Cria propostas sugeridas se fornecidas
    if propostas_pagamento:
        regras_vistas = set()
        for prop in propostas_pagamento:
            regra_val = prop.get('regra_pagamento') or prop.get('regra_pagamento_id')
            if not regra_val:
                continue

            if isinstance(regra_val, RegraPagamento):
                regra = regra_val
                regra_id = regra.id
            else:
                regra_id = regra_val
                regra = RegraPagamento.objects.filter(id=regra_id, ativo=True, deleted_at__isnull=True).first()

            if not regra or regra_id in regras_vistas:
                continue
            regras_vistas.add(regra_id)

            desconto_prop = prop.get('desconto_personalizado')
            if desconto_prop is not None:
                desconto_prop = Decimal(str(desconto_prop))
            else:
                desconto_prop = regra.desconto_concedido_padrao

            FaturaPropostaPagamento.objects.create(
                fatura=fatura,
                regra_pagamento=regra,
                desconto_personalizado=desconto_prop
            )

    logger.info(f"[FATURA RASCUNHO CRIADA] Fatura #{fatura.id} criada para {cliente.nome_razao} com {len(orcamentos)} orçamento(s).")
    return fatura


@transaction.atomic
def atualizar_pre_fatura(fatura, orcamento_ids=None, propostas_pagamento=None, desconto_global=None, user=None):
    """
    Atualiza uma Pré-Fatura em status RASCUNHO.
    Permite adicionar/remover orçamentos, recalcular valores e redefinir propostas sugeridas.
    """
    if fatura.status != 'RASCUNHO':
        raise ValidationError({'status': 'Apenas faturas em status RASCUNHO podem ser editadas.'})

    if orcamento_ids is not None:
        if not orcamento_ids:
            raise ValidationError({'orcamentos': 'A fatura deve conter pelo menos um orçamento.'})

        # Desvincula orçamentos removidos
        orcamentos_antigos = fatura.orcamentos_agrupados.filter(deleted_at__isnull=True)
        for orc in orcamentos_antigos:
            if orc.id not in orcamento_ids:
                orc.fatura = None
                orc.save(update_fields=['fatura', 'updated_at'])

        # Busca novos orçamentos
        novos_orcamentos = list(Orcamento.objects.filter(
            id__in=orcamento_ids,
            deleted_at__isnull=True
        ).select_related('cliente'))

        if len(novos_orcamentos) != len(set(orcamento_ids)):
            raise ValidationError({'orcamentos': 'Um ou mais orçamentos selecionados não foram encontrados ou estão inativos.'})

        valor_bruto_total = Decimal('0.00')
        for orc in novos_orcamentos:
            if orc.cliente_id != fatura.cliente_id:
                raise ValidationError({
                    'orcamentos': f"O orçamento #{orc.id} pertence a outro cliente ({orc.cliente.nome_razao})."
                })
            if orc.fatura_id is not None and orc.fatura_id != fatura.id:
                raise ValidationError({
                    'orcamentos': f"O orçamento #{orc.id} já está vinculado à Fatura #{orc.fatura_id}."
                })
            if orc.status_financeiro != 'A_FATURAR':
                raise ValidationError({
                    'orcamentos': f"O orçamento #{orc.id} não está em status A FATURAR."
                })

            orc.fatura = fatura
            orc.save(update_fields=['fatura', 'updated_at'])

            valor_liq_orc = max(Decimal('0.00'), (orc.valor_bruto or Decimal('0.00')) - (orc.valor_desconto_aplicado or Decimal('0.00')))
            valor_bruto_total += valor_liq_orc

        fatura.valor_bruto = valor_bruto_total

    if desconto_global is not None:
        fatura.desconto_global = Decimal(str(desconto_global))

    fatura.valor_total_faturado = max(Decimal('0.00'), fatura.valor_bruto - fatura.desconto_global)
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save()

    # Atualiza propostas de pagamento se fornecido
    if propostas_pagamento is not None:
        fatura.propostas_pagamento.all().delete()
        regras_vistas = set()
        for prop in propostas_pagamento:
            regra_val = prop.get('regra_pagamento') or prop.get('regra_pagamento_id')
            if not regra_val:
                continue

            if isinstance(regra_val, RegraPagamento):
                regra = regra_val
                regra_id = regra.id
            else:
                regra_id = regra_val
                regra = RegraPagamento.objects.filter(id=regra_id, ativo=True, deleted_at__isnull=True).first()

            if not regra or regra_id in regras_vistas:
                continue
            regras_vistas.add(regra_id)

            desconto_prop = prop.get('desconto_personalizado')
            if desconto_prop is not None:
                desconto_prop = Decimal(str(desconto_prop))
            else:
                desconto_prop = regra.desconto_concedido_padrao

            FaturaPropostaPagamento.objects.create(
                fatura=fatura,
                regra_pagamento=regra,
                desconto_personalizado=desconto_prop
            )

    return fatura


@transaction.atomic
def faturar_rascunho(fatura, regra_pagamento_id, desconto_global=None, numero_nfe_venda=None, user=None):
    """
    Converte uma Pré-Fatura (Rascunho) em Fatura Final (FATURADA).
    Efeitos em cascata:
    1. Vincula a Regra de Pagamento definitiva.
    2. Ajusta desconto final e recalcula valor_total_faturado.
    3. Status da fatura transita para 'FATURADA' com data_fechamento = hoje.
    4. Todos os orçamentos vinculados transitam para status_financeiro = 'FATURADO'.
    5. Gera automaticamente as parcelas em LancamentoFinanceiro (Contas a Receber) com status 'A_VENCER'.
    """
    if fatura.status != 'RASCUNHO':
        raise ValidationError({'status': f"Apenas faturas em status RASCUNHO podem ser faturadas. Status atual: {fatura.get_status_display()}."})

    orcamentos = fatura.orcamentos_agrupados.filter(deleted_at__isnull=True)
    if not orcamentos.exists():
        raise ValidationError({'orcamentos': 'A fatura não possui nenhum orçamento vinculado.'})

    regra = RegraPagamento.objects.filter(id=regra_pagamento_id, ativo=True, deleted_at__isnull=True).select_related('meio_pagamento').first()
    if not regra:
        raise ValidationError({'regra_pagamento': 'Condição comercial / Regra de pagamento não encontrada ou inativa.'})

    if desconto_global is not None:
        fatura.desconto_global = Decimal(str(desconto_global))

    fatura.valor_total_faturado = max(Decimal('0.00'), fatura.valor_bruto - fatura.desconto_global)
    fatura.regra_pagamento = regra
    fatura.status = 'FATURADA'
    fatura.data_fechamento = timezone.localdate()
    if numero_nfe_venda:
        fatura.numero_nfe_venda = sanitizar_texto_maiusculo(numero_nfe_venda)
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save()

    # 1. Transição em cascata dos orçamentos
    orcamentos.update(status_financeiro='FATURADO', updated_at=timezone.now())

    # 2. Geração automática das parcelas a receber no Contas a Receber (LancamentoFinanceiro)
    # Remove eventuais lançamentos prévios da fatura a vencer (caso houvesse algo)
    fatura.lancamentos_financeiros.filter(status_pagamento='A_VENCER').delete()

    categoria_receita = obter_categoria_receita_padrao()
    valor_total = fatura.valor_total_faturado
    num_parcelas = max(1, regra.numero_parcelas)
    prazo_1 = regra.prazo_primeira_parcela_dias or 0
    intervalo = regra.intervalo_parcelas_dias or 30
    data_base = fatura.data_fechamento

    if valor_total > Decimal('0.00'):
        # Cálculo de parcelas com ajuste de centavos na primeira parcela
        valor_base = (valor_total / num_parcelas).quantize(Decimal('0.01'))
        diferenca_centavos = valor_total - (valor_base * num_parcelas)

        for i in range(1, num_parcelas + 1):
            if i == 1:
                vencimento = data_base + timedelta(days=prazo_1)
                valor_parcela = valor_base + diferenca_centavos
            else:
                vencimento = data_base + timedelta(days=prazo_1 + (i - 1) * intervalo)
                valor_parcela = valor_base

            LancamentoFinanceiro.objects.create(
                origem='FATURA',
                fatura=fatura,
                tipo_lancamento='ENTRADA',
                status_pagamento='A_VENCER',
                meio_pagamento=regra.meio_pagamento,
                categoria=categoria_receita,
                descricao=f"FATURA #{fatura.id} - PARCELA {i}/{num_parcelas} - {fatura.cliente.nome_razao}",
                valor=valor_parcela,
                data_vencimento=vencimento,
                created_by_id=getattr(user, 'id', None)
            )

    logger.info(f"[FATURA CONCLUIDA] Fatura #{fatura.id} FATURADA em {num_parcelas}x com Regra '{regra.nome}'.")
    return fatura


@transaction.atomic
def receber_pagamento_fatura(fatura, valor, conta_id=None, meio_pagamento_id=None, data_pagamento=None, valor_liquido=None, user=None):
    """
    Registra um recebimento (baixa total ou parcial) em uma Fatura Final (FATURADA).
    Efeitos:
    1. Amortiza as parcelas de LancamentoFinanceiro da fatura que estejam 'A_VENCER' ou 'VENCIDO'.
    2. Impacta o saldo da ContaBancaria imediatamente (Regime de Caixa Real).
    3. Se houver taxa de maquininha (valor_liquido < valor), debita despesa automática de taxa.
    4. Se o somatório de baixas atingir 100% do valor da fatura:
       - Transita fatura para 'PAGA'
       - Transita orçamentos vinculados para status_financeiro = 'PAGO'
    """
    if fatura.status != 'FATURADA':
        if fatura.status == 'PAGA':
            raise ValidationError({'status': 'Esta fatura já está totalmente quitada.'})
        raise ValidationError({'status': f"Não é possível receber pagamento de fatura em status {fatura.get_status_display()}."})

    valor = Decimal(str(valor))
    if valor <= Decimal('0.00'):
        raise ValidationError({'valor': 'O valor de pagamento deve ser maior que zero.'})

    conta = None
    if conta_id:
        conta = ContaBancaria.objects.filter(id=conta_id, deleted_at__isnull=True).first()
        if not conta:
            raise ValidationError({'conta': 'Conta bancária informada não encontrada ou inativa.'})

    meio_pagamento = None
    if meio_pagamento_id:
        meio_pagamento = MeioPagamento.objects.filter(id=meio_pagamento_id, ativo=True, deleted_at__isnull=True).first()
    elif fatura.regra_pagamento:
        meio_pagamento = fatura.regra_pagamento.meio_pagamento

    if not data_pagamento:
        data_pagamento = timezone.now()

    # Busca parcelas pendentes da fatura em ordem de vencimento
    parcelas_pendentes = list(fatura.lancamentos_financeiros.filter(
        tipo_lancamento='ENTRADA',
        status_pagamento__in=['A_VENCER', 'VENCIDO'],
        deleted_at__isnull=True
    ).order_by('data_vencimento', 'id'))

    valor_restante = valor
    categoria_receita = obter_categoria_receita_padrao()

    for parcela in parcelas_pendentes:
        if valor_restante <= Decimal('0.00'):
            break

        if valor_restante >= parcela.valor:
            # Baixa integral da parcela
            valor_restante -= parcela.valor
            parcela.status_pagamento = 'PAGO'
            parcela.data_pagamento = data_pagamento
            parcela.conta = conta
            if meio_pagamento:
                parcela.meio_pagamento = meio_pagamento
            parcela.updated_by_id = getattr(user, 'id', None)
            parcela.save()
        else:
            # Baixa parcial da parcela: divide em uma parcela paga e mantém o saldo na pendente
            valor_pago = valor_restante
            parcela.valor -= valor_pago
            parcela.save(update_fields=['valor', 'updated_at'])

            LancamentoFinanceiro.objects.create(
                origem='FATURA',
                fatura=fatura,
                tipo_lancamento='ENTRADA',
                status_pagamento='PAGO',
                data_pagamento=data_pagamento,
                data_vencimento=parcela.data_vencimento,
                conta=conta,
                meio_pagamento=meio_pagamento or parcela.meio_pagamento,
                categoria=parcela.categoria,
                descricao=f"{parcela.descricao} (PARCIAL)",
                valor=valor_pago,
                created_by_id=getattr(user, 'id', None)
            )
            valor_restante = Decimal('0.00')

    # Se sobrou valor além das parcelas existentes (ex: adiantamento ou fatura sem parcelas)
    if valor_restante > Decimal('0.00'):
        LancamentoFinanceiro.objects.create(
            origem='FATURA',
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='PAGO',
            data_pagamento=data_pagamento,
            data_vencimento=data_pagamento.date(),
            conta=conta,
            meio_pagamento=meio_pagamento,
            categoria=categoria_receita,
            descricao=f"FATURA #{fatura.id} - RECEBIMENTO COMPLEMENTAR - {fatura.cliente.nome_razao}",
            valor=valor_restante,
            created_by_id=getattr(user, 'id', None)
        )

    # Impacto no Saldo Real da Conta Bancária
    if conta:
        if valor_liquido is not None:
            valor_liquido = Decimal(str(valor_liquido))
            taxa = valor - valor_liquido
            if taxa > Decimal('0.00'):
                conta.saldo += valor_liquido
                conta.save(update_fields=['saldo', 'updated_at'])

                # Registra a despesa de taxa de maquininha para o DRE
                categoria_taxa = obter_categoria_despesa_taxa()
                LancamentoFinanceiro.objects.create(
                    origem='FATURA',
                    fatura=fatura,
                    tipo_lancamento='SAIDA',
                    status_pagamento='PAGO',
                    data_pagamento=data_pagamento,
                    data_vencimento=data_pagamento.date(),
                    conta=conta,
                    meio_pagamento=meio_pagamento,
                    categoria=categoria_taxa,
                    descricao=f"TAXA DE CARTAO / MAQUININHA - FATURA #{fatura.id}",
                    valor=taxa,
                    created_by_id=getattr(user, 'id', None)
                )
            else:
                conta.saldo += valor
                conta.save(update_fields=['saldo', 'updated_at'])
        else:
            conta.saldo += valor
            conta.save(update_fields=['saldo', 'updated_at'])

    # Verificação de Quitação 100%
    total_recebido = fatura.lancamentos_financeiros.filter(
        tipo_lancamento='ENTRADA',
        status_pagamento='PAGO',
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    quitada = False
    if total_recebido >= fatura.valor_total_faturado:
        fatura.status = 'PAGA'
        fatura.updated_by_id = getattr(user, 'id', None)
        fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])
        fatura.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
            status_financeiro='PAGO',
            updated_at=timezone.now()
        )
        quitada = True
        logger.info(f"[FATURA QUITADA] Fatura #{fatura.id} 100% PAGA. Total: R$ {total_recebido}.")

    return {
        'fatura': fatura,
        'valor_recebido': float(valor),
        'total_recebido': float(total_recebido),
        'saldo_restante': max(0.0, float(fatura.valor_total_faturado - total_recebido)),
        'quitada': quitada
    }


@transaction.atomic
def quitar_cortesia_fatura(fatura, motivo_justificativa, user=None):
    """
    Aplica quitação por Cortesia (100% de desconto) em uma fatura.
    Efeitos:
    1. Ajusta desconto_global = valor_bruto e valor_total_faturado = 0.00.
    2. Status transita para 'PAGA' com data_fechamento = hoje.
    3. Cancela quaisquer títulos pendentes no Contas a Receber.
    4. Não lança entradas no caixa real bancário.
    5. Transita todos os orçamentos vinculados para status_financeiro = 'PAGO'.
    """
    if fatura.status not in ['RASCUNHO', 'FATURADA']:
        raise ValidationError({'status': f"Apenas faturas em status RASCUNHO ou FATURADA podem ser quitadas em cortesia. Status atual: {fatura.get_status_display()}."})

    motivo = sanitizar_texto_maiusculo(motivo_justificativa or '')
    if len(motivo) < 10:
        raise ValidationError({'motivo': 'A justificativa da cortesia deve conter no mínimo 10 caracteres.'})

    fatura.desconto_global = fatura.valor_bruto
    fatura.valor_total_faturado = Decimal('0.00')
    fatura.status = 'PAGA'
    fatura.data_fechamento = timezone.localdate()
    fatura.motivo_cancelamento = f"[CORTESIA 100%] {motivo}"
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save()

    # Cancela lançamentos a vencer
    fatura.lancamentos_financeiros.filter(
        status_pagamento='A_VENCER',
        deleted_at__isnull=True
    ).update(
        status_pagamento='CANCELADO',
        motivo_cancelamento=f"QUITACAO EM CORTESIA (100% DESCONTO) - {motivo}"
    )

    # Transita orçamentos para PAGO
    fatura.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
        status_financeiro='PAGO',
        updated_at=timezone.now()
    )

    logger.info(f"[CORTESIA APLICADA] Fatura #{fatura.id} quitada em CORTESIA por {getattr(user, 'nome', 'Admin')}.")
    return fatura


@transaction.atomic
def cancelar_fatura(fatura, motivo_cancelamento, user=None):
    """
    Cancela uma Fatura e executa a desvinculação em cascata.
    Efeitos:
    1. Exige justificativa com no mínimo 10 caracteres.
    2. Bloqueia cancelamento se já houver recebimentos liquidados no Caixa Real.
    3. Define status da fatura como 'CANCELADA' e grava motivo_cancelamento.
    4. Desvincula todos os orçamentos e reverte para status_financeiro = 'A_FATURAR'.
    5. Cancela todos os lançamentos a vencer no Contas a Receber.
    """
    if fatura.status == 'CANCELADA':
        raise ValidationError({'status': 'Esta fatura já se encontra cancelada.'})

    motivo = sanitizar_texto_maiusculo(motivo_cancelamento or '')
    if len(motivo) < 10:
        raise ValidationError({'motivo_cancelamento': 'A justificativa de cancelamento deve conter no mínimo 10 caracteres.'})

    # Validação de recebimentos já realizados
    tem_pagamentos = fatura.lancamentos_financeiros.filter(
        tipo_lancamento='ENTRADA',
        status_pagamento='PAGO',
        deleted_at__isnull=True
    ).exists()

    if tem_pagamentos:
        raise ValidationError({
            'motivo_cancelamento': 'Não é permitido cancelar uma fatura que já possui recebimentos liquidados no caixa. É necessário estornar as baixas antes de cancelar a fatura.'
        })

    fatura.status = 'CANCELADA'
    fatura.motivo_cancelamento = motivo
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['status', 'motivo_cancelamento', 'updated_at', 'updated_by_id'])

    # 1. Desvinculação em cascata e reversão dos orçamentos para 'A_FATURAR'
    fatura.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
        fatura=None,
        status_financeiro='A_FATURAR',
        updated_at=timezone.now()
    )

    # 2. Cancelamento dos lançamentos no Contas a Receber
    fatura.lancamentos_financeiros.filter(
        status_pagamento='A_VENCER',
        deleted_at__isnull=True
    ).update(
        status_pagamento='CANCELADO',
        motivo_cancelamento=f"CANCELAMENTO DA FATURA #{fatura.id} - {motivo}"
    )

    logger.info(f"[FATURA CANCELADA] Fatura #{fatura.id} CANCELADA por {getattr(user, 'nome', 'Admin')}. Motivo: {motivo}")
    return fatura


def simular_propostas_fatura(fatura):
    """
    Calcula os valores simulados para cada proposta sugerida vinculada à pré-fatura.
    Retorna lista de opções com desconto, valor líquido e detalhes das parcelas.
    """
    propostas = fatura.propostas_pagamento.select_related(
        'regra_pagamento',
        'regra_pagamento__meio_pagamento'
    ).all()

    valor_base_fatura = fatura.valor_bruto or Decimal('0.00')
    resultados = []

    for prop in propostas:
        regra = prop.regra_pagamento
        desconto_pct = prop.desconto_personalizado if prop.desconto_personalizado is not None else regra.desconto_concedido_padrao
        desconto_pct = Decimal(str(desconto_pct or '0.00'))

        valor_desconto = (valor_base_fatura * (desconto_pct / Decimal('100.00'))).quantize(Decimal('0.01'))
        valor_final = max(Decimal('0.00'), valor_base_fatura - valor_desconto)

        num_parc = max(1, regra.numero_parcelas)
        valor_parcela = (valor_final / num_parc).quantize(Decimal('0.01'))

        resultados.append({
            'proposta_id': prop.id,
            'regra_id': regra.id,
            'regra_nome': regra.nome,
            'meio_pagamento_nome': regra.meio_pagamento.nome,
            'tipo_cobranca': regra.tipo_cobranca,
            'desconto_percentual': float(desconto_pct),
            'valor_desconto': float(valor_desconto),
            'valor_final': float(valor_final),
            'numero_parcelas': num_parc,
            'valor_parcela': float(valor_parcela),
            'prazo_primeira_parcela_dias': regra.prazo_primeira_parcela_dias,
            'intervalo_parcelas_dias': regra.intervalo_parcelas_dias,
        })

    return resultados
