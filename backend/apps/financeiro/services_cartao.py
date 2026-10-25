"""
Serviços e regras de negócio para Cartões de Crédito Corporativos e Faturas de Cartão.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 10).
"""
import logging
import uuid
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q
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


def adicionar_meses_competencia(mes_referencia, delta_meses):
    """
    Adiciona delta_meses (positivo ou negativo) a uma competência YYYY-MM e retorna o novo YYYY-MM.
    """
    partes = mes_referencia.split('-')
    ano = int(partes[0])
    mes = int(partes[1]) + delta_meses
    while mes > 12:
        mes -= 12
        ano += 1
    while mes < 1:
        mes += 12
        ano -= 1
    return f"{ano:04d}-{mes:02d}"


def determinar_fatura_base_compra(cartao, data_compra, user=None):
    """
    Determina a FaturaCartao ABERTA correspondente à primeira parcela de uma compra realizada em data_compra.
    Regra de Negócio:
    1. Obtém ou cria a fatura do mês em que a compra ocorreu (YYYY-MM).
    2. Se data_compra <= fatura_mes.data_fechamento_real:
       A 1ª parcela pertence à fatura desse mês.
    3. Se data_compra > fatura_mes.data_fechamento_real:
       A 1ª parcela é transferida para o mês subsequente (+1 mês).
    """
    if isinstance(data_compra, str):
        data_compra = date.fromisoformat(data_compra)

    mes_ref = f"{data_compra.year:04d}-{data_compra.month:02d}"
    fatura_mes = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref, user=user)

    if data_compra > fatura_mes.data_fechamento_real:
        mes_ref_prox = adicionar_meses_competencia(mes_ref, 1)
        return obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref_prox, user=user)

    return fatura_mes


def calcular_limite_disponivel_cartao(cartao):
    """
    Calcula o limite disponível atual do cartão:
    Limite Cadastrado - Total de Despesas em Faturas Abertas e Fechadas (Não Pagas).
    Não contabiliza os títulos consolidados de fatura para evitar dupla contagem.
    """
    total_comprometido = LancamentoFinanceiro.objects.filter(
        cartao_credito=cartao,
        tipo_lancamento='SAIDA',
        status_pagamento='A_VENCER',
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
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


def sincronizar_titulo_fatura_cartao(fatura, user=None):
    """
    Sincroniza atomicamente o título consolidado da Fatura de Cartão no Contas a Pagar.
    Garante que:
    1. Apenas compras individuais (is_fatura_cartao_consolidada=False) componham o total da fatura.
    2. Exista exatamente 1 lançamento financeiro consolidado no Contas a Pagar com is_fatura_cartao_consolidada=True.
    3. A data de vencimento e valor estejam estritamente alinhados com o fechamento e competência da fatura.
    4. Se a fatura estiver PAGA, o título consolidado esteja PAGO; caso contrário, A_VENCER (ou VENCIDO se data_vencimento < hoje).
    """
    total_despesas = fatura.despesas_fatura.filter(
        tipo_lancamento='SAIDA',
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).exclude(
        descricao__startswith="FATURA CARTAO"
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    partes = fatura.mes_referencia.split('-')
    ano = int(partes[0])
    mes = int(partes[1])
    data_vencimento = calcular_data_vencimento_fatura(fatura.cartao, ano, mes)

    desc = f"PAGAMENTO FATURA CARTAO {fatura.cartao.nome} - {fatura.mes_referencia}"

    # Localiza título consolidado prévio (ou legado com prefixo PAGAMENTO FATURA CARTAO)
    titulo_fatura = LancamentoFinanceiro.objects.filter(
        fatura_cartao=fatura,
        is_fatura_cartao_consolidada=True,
        deleted_at__isnull=True
    ).first()

    if not titulo_fatura:
        titulo_fatura = LancamentoFinanceiro.objects.filter(
            fatura_cartao=fatura,
            descricao__startswith=f"PAGAMENTO FATURA CARTAO {fatura.cartao.nome}",
            deleted_at__isnull=True
        ).first()

    if total_despesas > Decimal('0.00'):
        categoria_cartao = obter_ou_criar_categoria_despesa_cartao()
        status_pagto = 'PAGO' if fatura.status == 'PAGA' else 'A_VENCER'

        if not titulo_fatura:
            titulo_fatura = LancamentoFinanceiro.objects.create(
                origem='CARTAO',
                cartao_credito=fatura.cartao,
                fatura_cartao=fatura,
                conta=fatura.cartao.conta_bancaria,
                categoria=categoria_cartao,
                tipo_lancamento='SAIDA',
                descricao=desc,
                valor=total_despesas,
                data_competencia=fatura.data_fechamento_real,
                data_vencimento=data_vencimento,
                status_pagamento=status_pagto,
                is_fatura_cartao_consolidada=True,
                created_by_id=getattr(user, 'id', None)
            )
            logger.info(f"[TITULO CONSOLIDADO CRIADO] Fatura #{fatura.id} ({fatura.mes_referencia}) - R$ {total_despesas}.")
        else:
            campos_update = ['valor', 'data_vencimento', 'data_competencia', 'is_fatura_cartao_consolidada', 'updated_at']
            titulo_fatura.valor = total_despesas
            titulo_fatura.data_vencimento = data_vencimento
            titulo_fatura.data_competencia = fatura.data_fechamento_real
            titulo_fatura.is_fatura_cartao_consolidada = True
            if fatura.cartao.conta_bancaria and not titulo_fatura.conta:
                titulo_fatura.conta = fatura.cartao.conta_bancaria
                campos_update.append('conta')
            if fatura.status == 'PAGA' and titulo_fatura.status_pagamento != 'PAGO':
                titulo_fatura.status_pagamento = 'PAGO'
                campos_update.append('status_pagamento')
            elif fatura.status in ('ABERTA', 'FECHADA') and titulo_fatura.status_pagamento == 'PAGO':
                titulo_fatura.status_pagamento = 'A_VENCER'
                campos_update.append('status_pagamento')
            titulo_fatura.save(update_fields=campos_update)
            logger.info(f"[TITULO CONSOLIDADO ATUALIZADO] Fatura #{fatura.id} ({fatura.mes_referencia}) - R$ {total_despesas}.")
    else:
        # Se total é zero e existe título não pago, atualiza para zero
        if titulo_fatura and titulo_fatura.status_pagamento != 'PAGO':
            titulo_fatura.valor = Decimal('0.00')
            titulo_fatura.data_vencimento = data_vencimento
            titulo_fatura.is_fatura_cartao_consolidada = True
            titulo_fatura.save(update_fields=['valor', 'data_vencimento', 'is_fatura_cartao_consolidada', 'updated_at'])

    return titulo_fatura


@transaction.atomic
def lancar_despesa_cartao(cartao, valor, categoria_id, descricao=None, data_compra=None, fatura_cartao_id=None,
                         total_parcelas=1, comprovante=None, nome_arquivo_comprovante=None,
                         grupo_pagamento_id=None, cliente_fornecedor_id=None, user=None):
    """
    Registra uma despesa avulsa ou parcelada em Cartão Corporativo.
    Regras:
    1. NÃO debita conta bancária de imediato.
    2. Valida o limite total da compra contra o limite disponível do cartão.
    3. Se total_parcelas == 1: vincula à fatura aberta correspondente.
    4. Se total_parcelas > 1: divide o valor em N parcelas (ajustando centavos na 1ª parcela),
       identifica/cria as N faturas consecutivas e cria os N lançamentos vinculados.
    5. Grava data_competencia com a data real da compra.
    """
    valor = Decimal(str(valor))
    if valor <= Decimal('0.00'):
        raise ValidationError({'valor': 'O valor da despesa deve ser maior que zero.'})

    total_parcelas = max(1, int(total_parcelas or 1))

    categoria = CategoriaFinanceira.objects.filter(id=categoria_id, deleted_at__isnull=True).first()
    if not categoria:
        raise ValidationError({'categoria_id': 'Categoria financeira informada não encontrada ou inativa.'})

    # Validação de Limite Total
    info_limite = calcular_limite_disponivel_cartao(cartao)
    limite_disp = Decimal(str(info_limite['limite_disponivel']))
    if valor > limite_disp and not cartao.permite_limite_emergencial:
        raise ValidationError({
            'valor': f"Despesa excede o limite disponível do cartão. "
                     f"Limite disponível: R$ {limite_disp:.2f}, Valor total da compra: R$ {valor:.2f}."
        })

    if not data_compra:
        data_compra = timezone.localdate()
    elif isinstance(data_compra, str):
        data_compra = date.fromisoformat(data_compra)

    desc_base = sanitizar_texto_maiusculo(descricao or f"COMPRA CARTAO {cartao.nome} - {categoria.nome}")

    if not grupo_pagamento_id:
        grupo_pagamento_id = uuid.uuid4()

    # Determinação da primeira fatura
    if fatura_cartao_id and total_parcelas == 1:
        fatura_inicial = FaturaCartao.objects.filter(id=fatura_cartao_id, cartao=cartao, deleted_at__isnull=True).first()
        if not fatura_inicial:
            raise ValidationError({'fatura_cartao_id': 'Fatura de cartão informada não encontrada.'})
        if fatura_inicial.status != 'ABERTA':
            raise ValidationError({'fatura_cartao_id': f"Não é possível lançar despesas em fatura com status '{fatura_inicial.get_status_display()}'."})
    else:
        fatura_inicial = determinar_fatura_base_compra(cartao, data_compra, user=user)

    # Cálculo da divisão de parcelas
    parcela_base = (valor / total_parcelas).quantize(Decimal('0.01'))
    centavos_excedentes = valor - (parcela_base * total_parcelas)

    lancamentos_criados = []

    for i in range(1, total_parcelas + 1):
        mes_ref_i = adicionar_meses_competencia(fatura_inicial.mes_referencia, i - 1)
        if i == 1:
            fatura_i = fatura_inicial
        else:
            fatura_i = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref_i, user=user)

        # Valor da parcela
        valor_parcela = parcela_base + (centavos_excedentes if i == 1 else Decimal('0.00'))

        # Descrição com identificador de parcelas se total_parcelas > 1
        if total_parcelas > 1:
            desc_parcela = f"{desc_base} ({i}/{total_parcelas})"
        else:
            desc_parcela = desc_base

        lanc = LancamentoFinanceiro.objects.create(
            origem='CARTAO',
            cartao_credito=cartao,
            fatura_cartao=fatura_i,
            categoria=categoria,
            tipo_lancamento='SAIDA',
            descricao=desc_parcela,
            valor=valor_parcela,
            data_competencia=data_compra,
            data_vencimento=fatura_i.data_fechamento_real,
            status_pagamento='A_VENCER',
            numero_parcela=i,
            total_parcelas=total_parcelas,
            grupo_pagamento_id=grupo_pagamento_id,
            cliente_fornecedor_id=cliente_fornecedor_id,
            comprovante=comprovante or None,
            nome_arquivo_comprovante=nome_arquivo_comprovante or None,
            is_fatura_cartao_consolidada=False,
            created_by_id=getattr(user, 'id', None)
        )
        lancamentos_criados.append(lanc)
        logger.info(f"[DESPESA CARTAO REGISTRADA] #{lanc.id} R$ {valor_parcela} na fatura {fatura_i.mes_referencia} ({i}/{total_parcelas}) do cartão '{cartao.nome}'.")
        sincronizar_titulo_fatura_cartao(fatura_i, user=user)

    if total_parcelas == 1:
        primeiro = lancamentos_criados[0]
        primeiro.lancamentos_parcelas = lancamentos_criados
        return primeiro

    return lancamentos_criados


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

    # Sincroniza os títulos consolidados das duas faturas envolvidas
    if fatura_antiga:
        sincronizar_titulo_fatura_cartao(fatura_antiga, user=user)
    sincronizar_titulo_fatura_cartao(nova_fatura, user=user)

    logger.info(f"[DESPESA CARTAO REMANEJADA] Lançamento #{lancamento.id} movido de '{getattr(fatura_antiga, 'mes_referencia', 'N/A')}' para '{nova_fatura.mes_referencia}'.")
    return lancamento


def agrupar_lancamentos_por_compra(lancamentos_qs):
    """
    Agrupa uma lista/queryset de LancamentoFinanceiro em compras atômicas.
    1. Lançamentos com grupo_pagamento_id preenchido são agrupados pelo UUID.
    2. Lançamentos legados com total_parcelas > 1 e grupo_pagamento_id nulo são agrupados por
       (cartao_credito_id, data_competencia, total_parcelas, descricao_base) e recebem um UUID gerado.
    3. Lançamentos unitários (total_parcelas == 1) sem grupo_pagamento_id formam grupos de 1 item.
    """
    grupos = {}
    grupos_legados = {}

    for lanc in lancamentos_qs:
        if lanc.grupo_pagamento_id:
            gid = str(lanc.grupo_pagamento_id)
            if gid not in grupos:
                grupos[gid] = []
            grupos[gid].append(lanc)
        elif (lanc.total_parcelas or 1) > 1:
            desc_limpa = (lanc.descricao or '').split('(')[0].strip()
            chave_legada = (
                lanc.cartao_credito_id,
                lanc.data_competencia,
                lanc.total_parcelas,
                desc_limpa
            )
            if chave_legada not in grupos_legados:
                grupos_legados[chave_legada] = []
            grupos_legados[chave_legada].append(lanc)
        else:
            grupos[f"single_{lanc.id}"] = [lanc]

    for chave, itens in grupos_legados.items():
        novo_gid = uuid.uuid4()
        ids_para_atualizar = [item.id for item in itens]
        LancamentoFinanceiro.objects.filter(id__in=ids_para_atualizar).update(
            grupo_pagamento_id=novo_gid
        )
        for item in itens:
            item.grupo_pagamento_id = novo_gid
        grupos[str(novo_gid)] = itens

    return list(grupos.values())


def reposicionar_compra_cartao(cartao, itens_compra, user=None):
    """
    Reposiciona atomicamente toda a cadeia de parcelas de uma compra de cartão.
    Garante que:
    1. A 1ª parcela caia na fatura correta conforme a data da compra e o fechamento do cartão.
    2. As parcelas subsequentes (2..N) caiam estritamente nos meses consecutivos (+1, +2, etc.).
    3. O vencimento de cada parcela seja sincronizado com o data_fechamento_real da respectiva fatura.
    Retorna o número de itens que tiveram sua fatura alterada.
    """
    if not itens_compra:
        return 0

    itens_ordenados = sorted(itens_compra, key=lambda x: (x.numero_parcela or 1))
    primeiro_item = itens_ordenados[0]
    data_compra = primeiro_item.data_competencia or (primeiro_item.created_at.date() if primeiro_item.created_at else timezone.localdate())

    fatura_base = determinar_fatura_base_compra(cartao, data_compra, user=user)
    mes_ref_base = fatura_base.mes_referencia

    itens_movidos = 0

    for item in itens_ordenados:
        num_parcela = item.numero_parcela or 1
        delta_mes = num_parcela - 1
        mes_ref_target = adicionar_meses_competencia(mes_ref_base, delta_mes)

        if delta_mes == 0:
            fatura_target = fatura_base
        else:
            fatura_target = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_ref_target, user=user)

        mudou_fatura = (item.fatura_cartao_id != fatura_target.id)
        mudou_venc = (item.data_vencimento != fatura_target.data_fechamento_real)

        if mudou_fatura or mudou_venc:
            item.fatura_cartao = fatura_target
            item.data_vencimento = fatura_target.data_fechamento_real
            item.updated_at = timezone.now()
            item.updated_by_id = getattr(user, 'id', None)
            item.save(update_fields=['fatura_cartao', 'data_vencimento', 'updated_at', 'updated_by_id'])
            if mudou_fatura:
                itens_movidos += 1

    return itens_movidos


@transaction.atomic
def ajustar_fechamento_fatura(fatura, nova_data_fechamento, user=None):
    """
    Ajusta a data de fechamento real de uma fatura específica de cartão.
    Regras de Recálculo Dinâmico em Cadeia e Governança de Faturas:
    1. Faturas com status PAGA não podem ter a data de fechamento alterada.
    2. Se a fatura estiver FECHADA e a nova data de fechamento for ajustada, a fatura é reaberta
       para permitir que compras sejam redistribuídas ou reavaliadas dinamicamente.
    3. Se nova_data_fechamento < data_antiga (antecipação do fechamento):
       - As compras já efetuadas após o novo corte (data_competencia > nova_data_fechamento)
         são redistribuídas automaticamente para o mês subsequente COM TODAS AS SUAS PARCELAS EM CADEIA.
    4. Se nova_data_fechamento > data_antiga (adiamento do fechamento):
       - As compras da fatura do mês subsequente que ocorreram até a nova data de corte
         (data_competencia <= nova_data_fechamento) são puxadas de volta COM TODAS AS SUAS PARCELAS EM CADEIA.
    5. O título consolidado da fatura (is_fatura_cartao_consolidada=True) NUNCA é movido como compra.
    6. Sincroniza compulsoriamente os títulos consolidados em Contas a Pagar da fatura atual e das adjacentes
       (fatura anterior e fatura posterior).
    """
    if fatura.status == 'PAGA':
        raise ValidationError({
            'status': "Faturas já liquidadas/pagas não podem ter a data de fechamento ajustada."
        })

    if isinstance(nova_data_fechamento, str):
        nova_data_fechamento = date.fromisoformat(nova_data_fechamento)

    data_antiga = fatura.data_fechamento_real
    fatura.data_fechamento_real = nova_data_fechamento

    # Se a fatura estava FECHADA, reabre para acomodar as possíveis reclassificações de compras
    campos_salvar = ['data_fechamento_real', 'updated_at', 'updated_by_id']
    if fatura.status == 'FECHADA':
        fatura.status = 'ABERTA'
        campos_salvar.append('status')

    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=campos_salvar)

    mes_ref_prox = adicionar_meses_competencia(fatura.mes_referencia, 1)
    mes_ref_ant = adicionar_meses_competencia(fatura.mes_referencia, -1)
    itens_movidos_adiante = 0
    itens_puxados_de_volta = 0

    if nova_data_fechamento < data_antiga:
        # Antecipação do corte: compras reais com data_competencia > nova_data_fechamento na fatura atual
        despesas_afetadas = fatura.despesas_fatura.filter(
            status_pagamento='A_VENCER',
            is_fatura_cartao_consolidada=False,
            deleted_at__isnull=True
        ).exclude(
            descricao__startswith="PAGAMENTO FATURA CARTAO"
        ).filter(
            Q(data_competencia__gt=nova_data_fechamento) |
            (Q(data_competencia__isnull=True) & Q(data_vencimento__gt=nova_data_fechamento))
        )

        grupos = agrupar_lancamentos_por_compra(despesas_afetadas)
        for itens_compra in grupos:
            primeiro = itens_compra[0]
            if primeiro.grupo_pagamento_id:
                todas_parcelas = list(LancamentoFinanceiro.objects.filter(
                    grupo_pagamento_id=primeiro.grupo_pagamento_id,
                    status_pagamento='A_VENCER',
                    is_fatura_cartao_consolidada=False,
                    deleted_at__isnull=True
                ).exclude(descricao__startswith="PAGAMENTO FATURA CARTAO"))
            else:
                todas_parcelas = itens_compra

            movidos = reposicionar_compra_cartao(fatura.cartao, todas_parcelas, user=user)
            itens_movidos_adiante += movidos

    elif nova_data_fechamento > data_antiga:
        # Adiamento do corte: se a fatura seguinte tem compras com data_competencia <= nova_data_fechamento
        fatura_prox = FaturaCartao.objects.filter(
            cartao=fatura.cartao,
            mes_referencia=mes_ref_prox,
            deleted_at__isnull=True
        ).first()

        if fatura_prox:
            despesas_a_puxar = fatura_prox.despesas_fatura.filter(
                status_pagamento='A_VENCER',
                is_fatura_cartao_consolidada=False,
                deleted_at__isnull=True
            ).exclude(
                descricao__startswith="PAGAMENTO FATURA CARTAO"
            ).filter(
                Q(numero_parcela=1) | Q(total_parcelas=1) | Q(numero_parcela__isnull=True)
            ).filter(
                Q(data_competencia__lte=nova_data_fechamento) |
                (Q(data_competencia__isnull=True) & Q(created_at__date__lte=nova_data_fechamento))
            )

            grupos = agrupar_lancamentos_por_compra(despesas_a_puxar)
            for itens_compra in grupos:
                primeiro = itens_compra[0]
                if primeiro.grupo_pagamento_id:
                    todas_parcelas = list(LancamentoFinanceiro.objects.filter(
                        grupo_pagamento_id=primeiro.grupo_pagamento_id,
                        status_pagamento='A_VENCER',
                        is_fatura_cartao_consolidada=False,
                        deleted_at__isnull=True
                    ).exclude(descricao__startswith="PAGAMENTO FATURA CARTAO"))
                else:
                    todas_parcelas = itens_compra

                movidos = reposicionar_compra_cartao(fatura.cartao, todas_parcelas, user=user)
                itens_puxados_de_volta += movidos

    # Sincroniza vencimento dos lançamentos individuais que permaneceram nesta fatura
    fatura.despesas_fatura.filter(
        status_pagamento='A_VENCER',
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).exclude(
        descricao__startswith="FATURA CARTAO"
    ).update(
        data_vencimento=nova_data_fechamento,
        updated_at=timezone.now()
    )

    # Sincronização em cadeia dos títulos consolidados: fatura atual e adjacentes (anterior e posterior)
    sincronizar_titulo_fatura_cartao(fatura, user=user)

    fatura_prox_obj = FaturaCartao.objects.filter(cartao=fatura.cartao, mes_referencia=mes_ref_prox, deleted_at__isnull=True).first()
    if fatura_prox_obj:
        sincronizar_titulo_fatura_cartao(fatura_prox_obj, user=user)

    fatura_ant_obj = FaturaCartao.objects.filter(cartao=fatura.cartao, mes_referencia=mes_ref_ant, deleted_at__isnull=True).first()
    if fatura_ant_obj:
        sincronizar_titulo_fatura_cartao(fatura_ant_obj, user=user)

    logger.info(
        f"[FECHAMENTO FATURA AJUSTADO] Fatura #{fatura.id} ({fatura.mes_referencia}) fechamento: {nova_data_fechamento}. "
        f"Itens movidos adiante: {itens_movidos_adiante}, Itens puxados de volta: {itens_puxados_de_volta}."
    )
    return {
        'fatura': fatura,
        'nova_data_fechamento': nova_data_fechamento,
        'itens_movidos_adiante': itens_movidos_adiante,
        'itens_puxados_de_volta': itens_puxados_de_volta
    }
    return {
        'fatura': fatura,
        'nova_data_fechamento': nova_data_fechamento,
        'itens_movidos_adiante': itens_movidos_adiante,
        'itens_puxados_de_volta': itens_puxados_de_volta
    }


@transaction.atomic
def recalcular_faturas_cartao(cartao, competencia_inicial, user=None, confirmar_retroativo_fechadas=False):
    """
    Recalcula as faturas do cartão de crédito a partir da competência inicial informada (YYYY-MM).
    Regras de Negócio e Governança Contábil:
    1. Valida o formato da competência inicial (YYYY-MM).
    2. Identifica todas as faturas cadastradas a partir dessa competência.
    3. Se houver faturas com status FECHADA ou PAGA:
       - Se confirmar_retroativo_fechadas for False: gera ValidationError alertando o usuário e listando as faturas.
       - Se confirmar_retroativo_fechadas for True: autoriza o recálculo e ajusta os títulos consolidados em Contas a Pagar.
    4. Atualiza a data_fechamento_real de cada fatura baseada no dia_fechamento_padrao do cartão.
    5. Coleta todas as despesas abertas no intervalo e reposiciona atomicamente cada compra inteira
       (com todas as suas parcelas em cadeia sequencial).
    6. Atualiza os títulos consolidados de Contas a Pagar para faturas fechadas que sofreram alteração.
    Retorna o sumário completo de faturas recalculadas, compras avaliadas e parcelas remanejadas.
    """
    if not competencia_inicial or not isinstance(competencia_inicial, str) or len(competencia_inicial) != 7:
        raise ValidationError({'competencia_inicial': 'Competência inicial inválida. Formato esperado: YYYY-MM.'})

    faturas_qs = FaturaCartao.objects.filter(
        cartao=cartao,
        mes_referencia__gte=competencia_inicial,
        deleted_at__isnull=True
    ).order_by('mes_referencia')

    faturas_fechadas_ou_pagas = [f for f in faturas_qs if f.status in ('FECHADA', 'PAGA')]
    if faturas_fechadas_ou_pagas and not confirmar_retroativo_fechadas:
        detalhes = [
            {
                'id': f.id,
                'mes_referencia': f.mes_referencia,
                'status': f.status,
                'data_fechamento_real': str(f.data_fechamento_real),
            }
            for f in faturas_fechadas_ou_pagas
        ]
        raise ValidationError({
            'alerta_faturas_fechadas': True,
            'faturas_afetadas': detalhes,
            'detail': (
                f"Existem {len(detalhes)} fatura(s) com status FECHADA ou PAGA no período selecionado a partir de {competencia_inicial}. "
                f"O recálculo retroativo pode alterar valores de títulos no Contas a Pagar e gerar divergência com extratos bancários já quitados. "
                f"Confirmação explícita do operador é necessária."
            )
        })

    # Atualiza data_fechamento_real de todas as faturas do período
    total_faturas_recalculadas = 0
    for fatura in faturas_qs:
        partes = fatura.mes_referencia.split('-')
        ano = int(partes[0])
        mes = int(partes[1])
        nova_data_fech = calcular_data_fechamento_padrao(cartao, ano, mes)

        if fatura.data_fechamento_real != nova_data_fech:
            fatura.data_fechamento_real = nova_data_fech
            fatura.updated_at = timezone.now()
            fatura.updated_by_id = getattr(user, 'id', None)
            fatura.save(update_fields=['data_fechamento_real', 'updated_at', 'updated_by_id'])
            total_faturas_recalculadas += 1

    # Coleta todas as despesas vinculadas a este cartão no período
    despesas_qs = LancamentoFinanceiro.objects.filter(
        origem='CARTAO',
        cartao_credito=cartao,
        status_pagamento='A_VENCER',
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).filter(
        fatura_cartao__mes_referencia__gte=competencia_inicial
    ).select_related('fatura_cartao')

    # Agrupa por compra inteira
    grupos_compras = agrupar_lancamentos_por_compra(despesas_qs)
    total_compras = len(grupos_compras)
    total_parcelas_remanejadas = 0

    for itens_compra in grupos_compras:
        primeiro = itens_compra[0]
        if primeiro.grupo_pagamento_id:
            todas_parcelas = list(LancamentoFinanceiro.objects.filter(
                grupo_pagamento_id=primeiro.grupo_pagamento_id,
                status_pagamento='A_VENCER',
                is_fatura_cartao_consolidada=False,
                deleted_at__isnull=True
            ).exclude(descricao__startswith="PAGAMENTO FATURA CARTAO"))
        else:
            todas_parcelas = itens_compra

        movidos = reposicionar_compra_cartao(cartao, todas_parcelas, user=user)
        total_parcelas_remanejadas += movidos

    # Sincroniza títulos de Contas a Pagar de todas as faturas do período
    for fatura in faturas_qs:
        # Sincroniza vencimento dos lançamentos da fatura
        fatura.despesas_fatura.filter(
            status_pagamento='A_VENCER',
            is_fatura_cartao_consolidada=False,
            deleted_at__isnull=True
        ).exclude(
            descricao__startswith="PAGAMENTO FATURA CARTAO"
        ).exclude(
            descricao__startswith="FATURA CARTAO"
        ).update(
            data_vencimento=fatura.data_fechamento_real,
            updated_at=timezone.now()
        )
        sincronizar_titulo_fatura_cartao(fatura, user=user)

    logger.info(
        f"[RECALCULO FATURAS CARTAO] Cartão '{cartao.nome}' a partir de {competencia_inicial}: "
        f"{total_faturas_recalculadas} fatura(s) com data ajustada, {total_compras} compra(s) avaliada(s), "
        f"{total_parcelas_remanejadas} parcela(s) remanejada(s)."
    )
    return {
        'cartao_id': cartao.id,
        'competencia_inicial': competencia_inicial,
        'faturas_recalculadas': total_faturas_recalculadas,
        'compras_recalculadas': total_compras,
        'itens_movidos_adiante': total_parcelas_remanejadas,
        'itens_puxados_de_volta': 0,
        'parcelas_remanejadas': total_parcelas_remanejadas
    }


@transaction.atomic
def fechar_fatura_cartao(fatura, user=None):
    """
    Fecha a fatura do cartão de crédito (transita de ABERTA para FECHADA).
    Efeitos:
    1. Consolida o total de despesas da fatura.
    2. Calcula a data de vencimento do pagamento.
    3. Atualiza/gera o título de Contas a Pagar consolidado no LancamentoFinanceiro (SAIDA, A_VENCER).
    """
    if fatura.status != 'ABERTA':
        raise ValidationError({'status': f"Apenas faturas em status ABERTA podem ser fechadas. Status atual: {fatura.get_status_display()}."})

    total_despesas = fatura.despesas_fatura.filter(
        tipo_lancamento='SAIDA',
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).exclude(
        descricao__startswith="FATURA CARTAO"
    ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

    partes = fatura.mes_referencia.split('-')
    ano = int(partes[0])
    mes = int(partes[1])
    data_vencimento = calcular_data_vencimento_fatura(fatura.cartao, ano, mes)

    fatura.status = 'FECHADA'
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])

    # Sincroniza o título mestre consolidado no Contas a Pagar
    titulo_fatura = sincronizar_titulo_fatura_cartao(fatura, user=user)

    logger.info(f"[FATURA CARTAO FECHADA] Fatura #{fatura.id} ({fatura.mes_referencia}) fechada. Total: R$ {total_despesas}. Vencimento: {data_vencimento}.")
    return {
        'fatura': fatura,
        'total_fatura': float(total_despesas),
        'data_vencimento': data_vencimento,
        'titulo_contas_a_pagar_id': titulo_fatura.id if titulo_fatura else None
    }


@transaction.atomic
def liquidar_fatura_cartao(fatura, valor_pago, conta_id=None, data_pagamento=None, comprovante=None, nome_arquivo_comprovante=None, user=None):
    """
    Liquida (total ou parcialmente) uma fatura fechada de cartão de crédito.
    Regras:
    1. Debita a conta bancária informada (ou a conta preferencial do cartão), validando cheque especial.
    2. Pagamento Total (valor_pago >= total_fatura):
       - Transita a fatura para 'PAGA'.
       - Transita todas as despesas vinculadas para 'PAGO'.
       - Quita o título mestre consolidado no Contas a Pagar.
    3. Pagamento Parcial (valor_pago < total_fatura):
       - Aplica ROLLOVER DE SALDO DEVEDOR: calcula o saldo residual não pago (total - valor_pago).
       - Transita a fatura atual para 'PAGA'.
       - Abre/localiza a fatura do mês seguinte para o mesmo cartão.
       - Cria um lançamento de despesa na fatura do mês seguinte: "SALDO ANTERIOR / ROLLOVER FATURA {mes_referencia}".
       - Sincroniza o título consolidado da fatura seguinte.
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
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).exclude(
        descricao__startswith="FATURA CARTAO"
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
                        f"Saldo atual: R$ {conta.saldo:.2f}, Limite: R$ {conta.limite_credito:.2f}, "
                        f"Saldo após pagamento: R$ {saldo_resultante:.2f}."
        })

    if not data_pagamento:
        data_pagamento = timezone.now()

    # 1. Debita a conta bancária
    conta.saldo -= valor_pago
    conta.save(update_fields=['saldo', 'updated_at'])

    # 2. Atualiza despesas individuais da fatura
    fatura.despesas_fatura.filter(
        is_fatura_cartao_consolidada=False,
        deleted_at__isnull=True
    ).exclude(
        descricao__startswith="PAGAMENTO FATURA CARTAO"
    ).exclude(
        descricao__startswith="FATURA CARTAO"
    ).update(
        status_pagamento='PAGO',
        data_pagamento=data_pagamento,
        conta=conta,
        updated_at=timezone.now()
    )

    # 3. Transita a fatura para PAGA
    fatura.status = 'PAGA'
    fatura.updated_by_id = getattr(user, 'id', None)
    fatura.save(update_fields=['status', 'updated_at', 'updated_by_id'])

    # 4. Sincroniza e quita o título consolidado em Contas a Pagar
    titulo_fatura = sincronizar_titulo_fatura_cartao(fatura, user=user)
    if titulo_fatura:
        titulo_fatura.status_pagamento = 'PAGO'
        titulo_fatura.data_pagamento = data_pagamento
        titulo_fatura.conta = conta
        titulo_fatura.valor = valor_pago
        if comprovante:
            titulo_fatura.comprovante = comprovante
            titulo_fatura.nome_arquivo_comprovante = nome_arquivo_comprovante
        titulo_fatura.save()

    saldo_devedor_remanescente = max(Decimal('0.00'), total_despesas - valor_pago)
    fatura_proxima = None
    lancamento_rollover = None

    # 5. Rollover de Pagamento Parcial
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
            origem='CARTAO',
            cartao_credito=fatura.cartao,
            fatura_cartao=fatura_proxima,
            categoria=categoria_cartao,
            tipo_lancamento='SAIDA',
            descricao=f"SALDO ANTERIOR / ROLLOVER FATURA {fatura.mes_referencia}",
            valor=saldo_devedor_remanescente,
            data_competencia=timezone.localdate(),
            data_vencimento=fatura_proxima.data_fechamento_real,
            status_pagamento='A_VENCER',
            is_fatura_cartao_consolidada=False,
            created_by_id=getattr(user, 'id', None)
        )
        logger.info(f"[ROLLOVER DE CARTAO APLICADO] R$ {saldo_devedor_remanescente} transferido da fatura {fatura.mes_referencia} para {mes_ref_prox}.")
        # Sincroniza o título consolidado da fatura seguinte
        sincronizar_titulo_fatura_cartao(fatura_proxima, user=user)

    return {
        'fatura': fatura,
        'valor_pago': float(valor_pago),
        'total_fatura': float(total_despesas),
        'saldo_devedor_remanescente': float(saldo_devedor_remanescente),
        'rollover_aplicado': saldo_devedor_remanescente > Decimal('0.00'),
        'fatura_proxima_id': fatura_proxima.id if fatura_proxima else None,
        'lancamento_rollover_id': lancamento_rollover.id if lancamento_rollover else None
    }
