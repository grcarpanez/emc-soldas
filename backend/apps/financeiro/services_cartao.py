"""
Serviços e regras de negócio para Cartões de Crédito Corporativos e Faturas de Cartão.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 10).
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from apps.financeiro.models import (
    CartaoCredito,
    FaturaCartao,
    LancamentoFinanceiro,
    ContaBancaria,
    CategoriaFinanceira
)
from apps.financeiro.services import (
    obter_ou_criar_categoria_taxa
)
from core.utils import sanitizar_texto_maiusculo

logger = logging.getLogger('apps.financeiro.cartao')


def obter_ou_criar_categoria_despesa_cartao():
    """Obtém ou cria categoria financeira de DESPESA para pagamentos consolidados de fatura de cartão."""
    categoria = CategoriaFinanceira.objects.filter(
        tipo='DESPESA',
        nome__icontains='CARTAO',
        deleted_at__isnull=True
    ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.filter(
            tipo='DESPESA',
            deleted_at__isnull=True
        ).order_by('id').first()

    if not categoria:
        categoria = CategoriaFinanceira.objects.create(
            nome='DESPESAS DIVERSAS COM CARTAO CORPORATIVO',
            tipo='DESPESA'
        )
    return categoria


def calcular_data_fechamento_padrao(cartao, ano, mes):
    """
    Calcula a data de fechamento real baseada no dia_fechamento_padrao do cartão.
    Trata meses com menos dias (ex: 28 de fevereiro, 30 de abril).
    """
    dia = cartao.dia_fechamento_padrao
    # Ajuste para dias limites do mês
    if mes == 2:
        # Ano bissexto
        is_bissexto = (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0)
        max_dias = 29 if is_bissexto else 28
    elif mes in [4, 6, 9, 11]:
        max_dias = 30
    else:
        max_dias = 31

    dia_real = min(dia, max_dias)
    return date(ano, mes, dia_real)


def calcular_data_vencimento_fatura(cartao, ano, mes):
    """
    Calcula a data de vencimento da fatura do cartão.
    Normalmente no mesmo mês ou mês subsequente dependendo da relação fechamento/vencimento.
    """
    dia_venc = cartao.dia_vencimento
    dia_fech = cartao.dia_fechamento_padrao

    # Se vencimento for menor ou igual ao fechamento, vence no mês seguinte
    if dia_venc <= dia_fech:
        mes_venc = mes + 1
        ano_venc = ano
        if mes_venc > 12:
            mes_venc = 1
            ano_venc += 1
    else:
        mes_venc = mes
        ano_venc = ano

    if mes_venc == 2:
        is_bissexto = (ano_venc % 4 == 0 and ano_venc % 100 != 0) or (ano_venc % 400 == 0)
        max_dias = 29 if is_bissexto else 28
    elif mes_venc in [4, 6, 9, 11]:
        max_dias = 30
    else:
        max_dias = 31

    return date(ano_venc, mes_venc, min(dia_venc, max_dias))


@transaction.atomic
def obter_ou_criar_fatura_aberta(cartao, mes_referencia=None, user=None):
    """
    Obtém ou cria a FaturaCartao ABERTA para o cartão de crédito e mês de referência especificado (YYYY-MM).
    Se não especificado, utiliza o mês atual.
    """
    hoje = timezone.localdate()
    if not mes_referencia:
        mes_referencia = f"{hoje.year:04d}-{hoje.month:02d}"

    fatura = FaturaCartao.objects.filter(
        cartao=cartao,
        mes_referencia=mes_referencia,
        deleted_at__isnull=True
    ).first()

    if not fatura:
        partes = mes_referencia.split('-')
        ano = int(partes[0])
        mes = int(partes[1])
        data_fech = calcular_data_fechamento_padrao(cartao, ano, mes)

        fatura = FaturaCartao.objects.create(
            cartao=cartao,
            mes_referencia=mes_referencia,
            data_fechamento_real=data_fech,
            status='ABERTA',
            created_by_id=getattr(user, 'id', None)
        )
        logger.info(f"[FATURA CARTAO CRIADA] Fatura {mes_referencia} criada para cartão '{cartao.nome}'.")

    return fatura


def calcular_limite_disponivel_cartao(cartao):
    """
    Calcula o limite disponível atual do cartão:
    Limite Cadastrado - Total de Despesas em Faturas Abertas e Fechadas (Não Pagas).
    """
    total_comprometido = LancamentoFinanceiro.objects.filter(
        cartao_credito=cartao,
        tipo_lancamento='SAIDA',
        status_pagamento='A_VENCER',
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    limite_disponivel = cartao.limite - total_comprometido
    return {
        'cartao_id': cartao.id,
        'cartao_nome': cartao.nome,
        'limite_total': float(cartao.limite),
        'total_comprometido': float(total_comprometido),
        'limite_disponivel': float(limite_disponivel),
        'permite_limite_emergencial': cartao.permite_limite_emergencial
    }


@transaction.atomic
def lancar_despesa_cartao(cartao, valor, categoria_id, descricao=None, data_compra=None, fatura_cartao_id=None, user=None):
    """
    Registra uma despesa avulsa em Cartão Corporativo.
    Regra de Ouro: NÃO debita conta bancária de imediato.
    Vincula à FaturaCartao ABERTA correspondente, impactando o limite do cartão.
    """
    valor = Decimal(str(valor))
    if valor <= Decimal('0.00'):
        raise ValidationError({'valor': 'O valor da despesa deve ser maior que zero.'})

    categoria = CategoriaFinanceira.objects.filter(id=categoria_id, deleted_at__isnull=True).first()
    if not categoria:
        raise ValidationError({'categoria_id': 'Categoria financeira informada não encontrada ou inativa.'})

    # Validação de Limite
    info_limite = calcular_limite_disponivel_cartao(cartao)
    limite_disp = Decimal(str(info_limite['limite_disponivel']))
    if valor > limite_disp and not cartao.permite_limite_emergencial:
        raise ValidationError({
            'valor': f"Despesa excede o limite disponível do cartão. "
                     f"Limite disponível: R$ {limite_disp}, Valor da compra: R$ {valor}."
        })

    if not data_compra:
        data_compra = timezone.localdate()
    elif isinstance(data_compra, str):
        data_compra = date.fromisoformat(data_compra)

    # Identifica a fatura aberta
    if fatura_cartao_id:
        fatura = FaturaCartao.objects.filter(id=fatura_cartao_id, cartao=cartao, deleted_at__isnull=True).first()
        if not fatura:
            raise ValidationError({'fatura_cartao_id': 'Fatura de cartão informada não encontrada.'})
        if fatura.status != 'ABERTA':
            raise ValidationError({'fatura_cartao_id': f"Não é possível lançar despesas em fatura com status '{fatura.get_status_display()}'."})
    else:
        # Determina o mês de referência pela data da compra e data de fechamento
        mes_ref = f"{data_compra.year:04d}-{data_compra.month:02d}"
        fatura = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref, user=user)

        # Se a compra for após o fechamento real da fatura desse mês, joga para o próximo mês
        if data_compra > fatura.data_fechamento_real:
            prox_mes = data_compra.month + 1
            prox_ano = data_compra.year
            if prox_mes > 12:
                prox_mes = 1
                prox_ano += 1
            mes_ref_prox = f"{prox_ano:04d}-{prox_mes:02d}"
            fatura = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref_prox, user=user)

    desc = sanitizar_texto_maiusculo(descricao or f"COMPRA CARTAO {cartao.nome} - {categoria.nome}")

    lancamento = LancamentoFinanceiro.objects.create(
        cartao_credito=cartao,
        fatura_cartao=fatura,
        categoria=categoria,
        tipo_lancamento='SAIDA',
        descricao=desc,
        valor=valor,
        data_vencimento=fatura.data_fechamento_real,
        status_pagamento='A_VENCER',
        created_by_id=getattr(user, 'id', None)
    )

    logger.info(f"[DESPESA CARTAO REGISTRADA] #{lancamento.id} R$ {valor} na fatura {fatura.mes_referencia} do cartão '{cartao.nome}'.")
    return lancamento


@transaction.atomic
def remanejar_despesa_cartao(lancamento, nova_fatura_cartao_id=None, novo_mes_referencia=None, user=None):
    """
    Permite alterar a fatura de um lançamento específico de cartão (para corrigir situações
    em que compras feitas tarde da noite ou por feriados devam entrar em outra competência).
    """
    if not lancamento.cartao_credito_id:
        raise ValidationError({'lancamento': 'Este lançamento não pertence a um Cartão Corporativo.'})
    if lancamento.status_pagamento == 'PAGO':
        raise ValidationError({'status_pagamento': 'Não é possível remanejar uma despesa de cartão que já foi liquidada/paga.'})

    cartao = lancamento.cartao_credito

    if nova_fatura_cartao_id:
        nova_fatura = FaturaCartao.objects.filter(id=nova_fatura_cartao_id, cartao=cartao, deleted_at__isnull=True).first()
        if not nova_fatura:
            raise ValidationError({'nova_fatura_cartao_id': 'Fatura de destino não encontrada para este cartão.'})
    elif novo_mes_referencia:
        nova_fatura = obter_ou_criar_fatura_aberta(cartao, mes_referencia=novo_mes_referencia, user=user)
    else:
        raise ValidationError({'nova_fatura': 'Informe a nova fatura ou o novo mês de referência de destino.'})

    fatura_antiga = lancamento.fatura_cartao
    lancamento.fatura_cartao = nova_fatura
    lancamento.data_vencimento = nova_fatura.data_fechamento_real
    lancamento.updated_by_id = getattr(user, 'id', None)
    lancamento.save(update_fields=['fatura_cartao', 'data_vencimento', 'updated_at', 'updated_by_id'])

    logger.info(f"[DESPESA CARTAO REMANEJADA] Lançamento #{lancamento.id} movido de '{getattr(fatura_antiga, 'mes_referencia', 'N/A')}' para '{nova_fatura.mes_referencia}'.")
    return lancamento


@transaction.atomic
def ajustar_fechamento_fatura(fatura, nova_data_fechamento, user=None):
    """
    Ajusta a data de fechamento real de uma fatura específica de cartão.
    Atualiza as datas de vencimento dos lançamentos vinculados que ainda estejam A_VENCER.
    """
    if isinstance(nova_data_fechamento, str):
        nova_data_fechamento = date.fromisoformat(nova_data_fechamento)

    fatura.data_fechamento_real = nova_data_fechamento
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['data_fechamento_real', 'updated_at', 'updated_by_id'])

    # Atualiza lançamentos a vencer
    fatura.despesas_fatura.filter(status_pagamento='A_VENCER', deleted_at__isnull=True).update(
        data_vencimento=nova_data_fechamento,
        updated_at=timezone.now()
    )

    logger.info(f"[FECHAMENTO FATURA AJUSTADO] Fatura #{fatura.id} ({fatura.mes_referencia}) nova data fechamento: {nova_data_fechamento}.")
    return fatura


@transaction.atomic
def fechar_fatura_cartao(fatura, user=None):
    """
    Fecha a fatura do cartão de crédito (transita de ABERTA para FECHADA).
    Efeitos:
    1. Consolida o total de despesas da fatura.
    2. Calcula a data de vencimento do pagamento.
    3. Gera o título de Contas a Pagar consolidado no LancamentoFinanceiro (SAIDA, A_VENCER).
    """
    if fatura.status != 'ABERTA':
        raise ValidationError({'status': f"Apenas faturas em status ABERTA podem ser fechadas. Status atual: {fatura.get_status_display()}."})

    total_despesas = fatura.despesas_fatura.filter(
        tipo_lancamento='SAIDA',
        deleted_at__isnull=True
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    partes = fatura.mes_referencia.split('-')
    ano = int(partes[0])
    mes = int(partes[1])
    data_vencimento = calcular_data_vencimento_fatura(fatura.cartao, ano, mes)

    fatura.status = 'FECHADA'
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])

    # Gera o título mestre no Contas a Pagar se houver valor > 0
    titulo_fatura = None
    if total_despesas > Decimal('0.00'):
        categoria_cartao = obter_ou_criar_categoria_despesa_cartao()
        desc = f"PAGAMENTO FATURA CARTAO {fatura.cartao.nome} - {fatura.mes_referencia}"

        # Verifica se já existia título mestre prévio
        titulo_fatura = LancamentoFinanceiro.objects.filter(
            fatura_cartao=fatura,
            descricao__startswith=f"PAGAMENTO FATURA CARTAO {fatura.cartao.nome}",
            deleted_at__isnull=True
        ).first()

        if not titulo_fatura:
            titulo_fatura = LancamentoFinanceiro.objects.create(
                cartao_credito=fatura.cartao,
                fatura_cartao=fatura,
                conta=fatura.cartao.conta_bancaria,
                categoria=categoria_cartao,
                tipo_lancamento='SAIDA',
                descricao=desc,
                valor=total_despesas,
                data_vencimento=data_vencimento,
                status_pagamento='A_VENCER',
                created_by_id=getattr(user, 'id', None)
            )
        else:
            titulo_fatura.valor = total_despesas
            titulo_fatura.data_vencimento = data_vencimento
            titulo_fatura.save(update_fields=['valor', 'data_vencimento', 'updated_at'])

    logger.info(f"[FATURA CARTAO FECHADA] Fatura #{fatura.id} ({fatura.mes_referencia}) fechada. Total: R$ {total_despesas}. Vencimento: {data_vencimento}.")
    return {
        'fatura': fatura,
        'total_fatura': float(total_despesas),
        'data_vencimento': data_vencimento,
        'titulo_contas_a_pagar_id': titulo_fatura.id if titulo_fatura else None
    }


@transaction.atomic
def liquidar_fatura_cartao(fatura, valor_pago, conta_id=None, data_pagamento=None, user=None):
    """
    Liquida (total ou parcialmente) uma fatura fechada de cartão de crédito.
    Regras:
    1. Debita a conta bancária informada (ou a conta preferencial do cartão), validando cheque especial.
    2. Pagamento Total (valor_pago >= total_fatura):
       - Transita a fatura para 'PAGA'.
       - Transita todas as despesas vinculadas para 'PAGO'.
    3. Pagamento Parcial (valor_pago < total_fatura):
       - Aplica ROLLOVER DE SALDO DEVEDOR: calcula o saldo residual não pago (total - valor_pago).
       - Transita a fatura atual para 'PAGA' (ou liquidada com rollover).
       - Abre/localiza a fatura do mês seguinte para o mesmo cartão.
       - Cria um lançamento de despesa na fatura do mês seguinte: "SALDO ANTERIOR / ROLLOVER FATURA {mes_referencia}".
    """
    if fatura.status != 'FECHADA':
        if fatura.status == 'PAGA':
            raise ValidationError({'status': 'Esta fatura já se encontra quitada/paga.'})
        raise ValidationError({'status': f"Apenas faturas FECHADAS podem ser pagas. Status atual: {fatura.get_status_display()}."})

    valor_pago = Decimal(str(valor_pago))
    if valor_pago <= Decimal('0.00'):
        raise ValidationError({'valor_pago': 'O valor de pagamento deve ser maior que zero.'})

    total_despesas = fatura.despesas_fatura.filter(
        tipo_lancamento='SAIDA',
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith=f"PAGAMENTO FATURA CARTAO"
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    # Conta de pagamento
    if conta_id:
        conta = ContaBancaria.objects.filter(id=conta_id, deleted_at__isnull=True).first()
        if not conta:
            raise ValidationError({'conta_id': 'Conta bancária informada não encontrada.'})
    else:
        conta = fatura.cartao.conta_bancaria
        if not conta:
            raise ValidationError({'conta_id': 'Informe a conta bancária para débito da fatura do cartão.'})

    # Validação de Cheque Especial
    saldo_resultante = conta.saldo - valor_pago
    limite_tolerado = -conta.limite_credito
    if saldo_resultante < limite_tolerado:
        raise ValidationError({
            'conta_id': f"Operação bloqueada por limite de cheque especial. "
                        f"Saldo atual: R$ {conta.saldo}, Limite: R$ {conta.limite_credito}, "
                        f"Saldo após pagamento: R$ {saldo_resultante}."
        })

    if not data_pagamento:
        data_pagamento = timezone.now()

    # 1. Debita a conta bancária
    conta.saldo -= valor_pago
    conta.save(update_fields=['saldo', 'updated_at'])

    # 2. Atualiza despesas da fatura
    fatura.despesas_fatura.filter(deleted_at__isnull=True).update(
        status_pagamento='PAGO',
        data_pagamento=data_pagamento,
        conta=conta,
        updated_at=timezone.now()
    )

    fatura.status = 'PAGA'
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])

    saldo_devedor_remanescente = max(Decimal('0.00'), total_despesas - valor_pago)
    fatura_proxima = None
    lancamento_rollover = None

    # 3. Rollover de Pagamento Parcial
    if saldo_devedor_remanescente > Decimal('0.00'):
        partes = fatura.mes_referencia.split('-')
        ano = int(partes[0])
        mes = int(partes[1])
        prox_mes = mes + 1
        prox_ano = ano
        if prox_mes > 12:
            prox_mes = 1
            prox_ano += 1
        mes_ref_prox = f"{prox_ano:04d}-{prox_mes:02d}"

        fatura_proxima = obter_ou_criar_fatura_aberta(fatura.cartao, mes_referencia=mes_ref_prox, user=user)
        categoria_cartao = obter_ou_criar_categoria_despesa_cartao()

        lancamento_rollover = LancamentoFinanceiro.objects.create(
            cartao_credito=fatura.cartao,
            fatura_cartao=fatura_proxima,
            categoria=categoria_cartao,
            tipo_lancamento='SAIDA',
            descricao=f"SALDO ANTERIOR / ROLLOVER FATURA {fatura.mes_referencia}",
            valor=saldo_devedor_remanescente,
            data_vencimento=fatura_proxima.data_fechamento_real,
            status_pagamento='A_VENCER',
            created_by_id=getattr(user, 'id', None)
        )
        logger.info(f"[ROLLOVER DE CARTAO APLICADO] R$ {saldo_devedor_remanescente} transferido da fatura {fatura.mes_referencia} para {mes_ref_prox}.")

    return {
        'fatura': fatura,
        'valor_pago': float(valor_pago),
        'total_fatura': float(total_despesas),
        'saldo_devedor_remanescente': float(saldo_devedor_remanescente),
        'rollover_aplicado': saldo_devedor_remanescente > Decimal('0.00'),
        'fatura_proxima_id': fatura_proxima.id if fatura_proxima else None,
        'lancamento_rollover_id': lancamento_rollover.id if lancamento_rollover else None
    }
