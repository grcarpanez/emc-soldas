"""
Serviços e regras de negócio para o Módulo de Orçamentos Comerciais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 8).
"""
import logging
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Sum
from rest_framework.exceptions import ValidationError

from apps.administracao.models import ConfiguracaoGlobal
from apps.catalogo.models import Item, Produto
from apps.financeiro.models import LancamentoFinanceiro
from core.utils import sanitizar_texto_maiusculo

logger = logging.getLogger('apps.orcamentos')


def verificar_inadimplencia_cliente(cliente_id):
    """
    Verifica em tempo real se o cliente possui títulos a receber em atraso ou vencidos.
    Retorna dicionário com status de inadimplência, total em atraso e lista de títulos.
    """
    hoje = timezone.now().date()

    # Busca lançamentos de entrada (receitas/faturas) do cliente que estejam vencidos ou em atraso
    titulos_vencidos = LancamentoFinanceiro.objects.filter(
        deleted_at__isnull=True,
        tipo_lancamento='ENTRADA',
        fatura__cliente_id=cliente_id
    ).filter(
        Q(status_pagamento='VENCIDO') |
        Q(status_pagamento='A_VENCER', data_vencimento__lt=hoje)
    ).select_related('fatura')

    total_vencido = titulos_vencidos.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
    quantidade = titulos_vencidos.count()
    is_inadimplente = quantidade > 0

    detalhes_titulos = []
    for titulo in titulos_vencidos[:10]:  # Limita aos primeiros 10 para payload ágil
        dias_atraso = (hoje - titulo.data_vencimento).days if titulo.data_vencimento else 0
        detalhes_titulos.append({
            'id': titulo.id,
            'fatura_id': titulo.fatura_id,
            'descricao': titulo.descricao,
            'valor': float(titulo.valor),
            'data_vencimento': titulo.data_vencimento.isoformat() if titulo.data_vencimento else None,
            'dias_atraso': max(dias_atraso, 0)
        })

    alerta_mensagem = ""
    if is_inadimplente:
        alerta_mensagem = (
            f"ALERTA DE INADIMPLÊNCIA: O cliente possui {quantidade} título(s) em atraso, "
            f"totalizando R$ {total_vencido:,.2f}."
        )

    return {
        'inadimplente': is_inadimplente,
        'quantidade_titulos_vencidos': quantidade,
        'total_vencido': float(total_vencido),
        'alerta_mensagem': alerta_mensagem,
        'titulos_vencidos': detalhes_titulos
    }


def calcular_custo_corrente_item(orcamento_item):
    """
    Calcula o custo unitário corrente de mercado para uma linha de orçamento
    baseando-se nos dados atuais do catálogo e taxas globais.
    """
    config = ConfiguracaoGlobal.get_solo()
    taxa_hora = config.taxa_mao_de_obra_hora or Decimal('0.00')

    # Caso 1: Produto Composto (BOM)
    if orcamento_item.produto:
        return orcamento_item.produto.preco_custo_apurado

    # Caso 2: Item / Insumo Simples
    elif orcamento_item.item:
        return (orcamento_item.item.ultimo_custo_compra or Decimal('0.00')).quantize(Decimal('0.01'))

    # Caso 3: Lançamento Manual Livre (sem referência de catálogo)
    else:
        return orcamento_item.custo_snapshot or Decimal('0.00')


def analisar_inflacao_orcamento(orcamento):
    """
    Analisa todos os itens de um orçamento, comparando o snapshot de custos original
    com os custos atuais do catálogo de materiais e taxas de mão de obra.
    Retorna relatório completo com alertas de inflação por linha e impacto geral de margem.
    """
    itens = orcamento.itens_orcamento.select_related(
        'produto', 'item', 'item__unidade_compra', 'produto__unidade_venda'
    ).all()

    detalhes_itens = []
    total_custo_snapshot = Decimal('0.00')
    total_custo_corrente = Decimal('0.00')
    total_venda = Decimal('0.00')
    itens_com_inflacao_count = 0

    for item in itens:
        qtd = item.quantidade or Decimal('1.0000')
        custo_snap = item.custo_snapshot or Decimal('0.00')
        venda_snap = item.valor_venda_snapshot or Decimal('0.00')
        custo_corr = calcular_custo_corrente_item(item)

        subtotal_custo_snap = qtd * custo_snap
        subtotal_custo_corr = qtd * custo_corr
        subtotal_venda = qtd * venda_snap

        total_custo_snapshot += subtotal_custo_snap
        total_custo_corrente += subtotal_custo_corr
        total_venda += subtotal_venda

        diff_custo = custo_corr - custo_snap
        variacao_percentual = Decimal('0.00')
        if custo_snap > 0:
            variacao_percentual = ((diff_custo / custo_snap) * 100).quantize(Decimal('0.01'))

        tem_inflacao_linha = diff_custo > Decimal('0.00')
        if tem_inflacao_linha:
            itens_com_inflacao_count += 1

        nome_exibicao = item.descricao_livre or (item.produto.nome if item.produto else (item.item.nome if item.item else "ITEM AVULSO"))

        detalhes_itens.append({
            'item_id': item.id,
            'tipo': 'PRODUTO' if item.produto else ('ITEM' if item.item else 'LIVRE'),
            'nome': nome_exibicao,
            'quantidade': float(qtd),
            'custo_snapshot_unitario': float(custo_snap),
            'custo_corrente_unitario': float(custo_corr),
            'diferenca_custo_unitario': float(diff_custo),
            'variacao_percentual': float(variacao_percentual),
            'tem_inflacao': tem_inflacao_linha,
            'valor_venda_snapshot_unitario': float(venda_snap),
            'subtotal_venda': float(subtotal_venda),
            'subtotal_custo_snapshot': float(subtotal_custo_snap),
            'subtotal_custo_corrente': float(subtotal_custo_corr),
        })

    diferenca_total_custo = total_custo_corrente - total_custo_snapshot
    variacao_geral_percentual = Decimal('0.00')
    if total_custo_snapshot > 0:
        variacao_geral_percentual = ((diferenca_total_custo / total_custo_snapshot) * 100).quantize(Decimal('0.01'))

    margem_original_valor = total_venda - total_custo_snapshot
    margem_original_percentual = Decimal('0.00')
    if total_venda > 0:
        margem_original_percentual = ((margem_original_valor / total_venda) * 100).quantize(Decimal('0.01'))

    margem_projetada_valor = total_venda - total_custo_corrente
    margem_projetada_percentual = Decimal('0.00')
    if total_venda > 0:
        margem_projetada_percentual = ((margem_projetada_valor / total_venda) * 100).quantize(Decimal('0.01'))

    ha_inflacao_geral = diferenca_total_custo > Decimal('0.00')

    return {
        'orcamento_id': orcamento.id,
        'data_geracao': orcamento.data_geracao.isoformat() if orcamento.data_geracao else None,
        'data_validade': orcamento.data_validade.isoformat() if orcamento.data_validade else None,
        'is_expirado': orcamento.data_validade < timezone.now().date() if orcamento.data_validade else False,
        'ha_inflacao': ha_inflacao_geral,
        'itens_com_inflacao_count': itens_com_inflacao_count,
        'total_itens': len(detalhes_itens),
        'total_custo_original': float(total_custo_snapshot),
        'total_custo_atualizado': float(total_custo_corrente),
        'aumento_custo_total': float(diferenca_total_custo),
        'variacao_geral_percentual': float(variacao_geral_percentual),
        'valor_total_venda': float(total_venda),
        'margem_original_valor': float(margem_original_valor),
        'margem_original_percentual': float(margem_original_percentual),
        'margem_projetada_valor': float(margem_projetada_valor),
        'margem_projetada_percentual': float(margem_projetada_percentual),
        'itens': detalhes_itens
    }


def renovar_validade_orcamento(orcamento, dias_validade=None, atualizar_precos=False, novos_precos_itens=None, user=None):
    """
    Renova o prazo de validade do orçamento.
    - Se atualizar_precos == False: estende a data mantendo os custos antigos (honrando preço).
    - Se atualizar_precos == True: atualiza os snapshots de custo com base no catálogo atual e permite
      atualizar os valores de venda informados em novos_precos_itens.
    """
    if orcamento.status_operacional == 'CANCELADO' or orcamento.status_financeiro == 'CANCELADO':
        raise ValidationError({'status': "Não é possível renovar um orçamento cancelado."})

    config = ConfiguracaoGlobal.get_solo()
    dias = dias_validade if dias_validade and int(dias_validade) > 0 else (config.validade_orcamento_dias or 15)

    hoje = timezone.now().date()
    nova_validade = hoje + timedelta(days=int(dias))

    with transaction.atomic():
        orcamento.data_validade = nova_validade

        # Se for para atualizar os custos/preços
        if atualizar_precos:
            itens = orcamento.itens_orcamento.all()
            novos_precos_map = novos_precos_itens or {}

            # Converte chaves de dicionário para inteiros se forem strings
            if isinstance(novos_precos_map, dict):
                novos_precos_map = {int(k): Decimal(str(v)) for k, v in novos_precos_map.items()}

            valor_bruto_recalculado = Decimal('0.00')

            for item in itens:
                # Atualiza snapshot do custo para o valor corrente de mercado
                custo_novo = calcular_custo_corrente_item(item)
                item.custo_snapshot = custo_novo

                # Se foi passado um novo valor de venda para este item, atualiza
                if item.id in novos_precos_map:
                    item.valor_venda_snapshot = Decimal(str(novos_precos_map[item.id]))

                item.save(update_fields=['custo_snapshot', 'valor_venda_snapshot'])
                valor_bruto_recalculado += item.quantidade * item.valor_venda_snapshot

            orcamento.valor_bruto = valor_bruto_recalculado

        orcamento.updated_at = timezone.now()
        if user and user.is_authenticated:
            orcamento.updated_by_id = user.id
        orcamento.save()

    logger.info(
        f"[ORCAMENTO RENOVAÇÃO] Orçamento #{orcamento.id} renovado até {nova_validade} "
        f"(Atualizar preços: {atualizar_precos}) por Usuário: {user}"
    )

    return orcamento


def cancelar_orcamento(orcamento, motivo, user=None):
    """
    Executa o cancelamento justificado do orçamento com validações e disparo de log de auditoria.
    Exige no mínimo 10 caracteres no motivo.
    """
    motivo_sanitizado = sanitizar_texto_maiusculo(motivo or "").strip()

    if len(motivo_sanitizado) < 10:
        raise ValidationError({
            'motivo_cancelamento': "O motivo do cancelamento é obrigatório e deve conter no mínimo 10 caracteres."
        })

    # Validação de regras financeiras e operacionais
    if orcamento.status_operacional == 'CONCLUIDO':
        raise ValidationError({
            'status_operacional': "Orçamento com status 'CONCLUÍDO' não pode ser cancelado diretamente."
        })

    if orcamento.status_financeiro in ['FATURADO', 'PAGO']:
        raise ValidationError({
            'status_financeiro': (
                f"Orçamento com status financeiro '{orcamento.get_status_financeiro_display()}' "
                "não pode ser cancelado sem antes desvincular ou cancelar a fatura correspondente."
            )
        })

    with transaction.atomic():
        orcamento.status_operacional = 'CANCELADO'
        orcamento.status_financeiro = 'CANCELADO'
        orcamento.motivo_cancelamento = motivo_sanitizado
        orcamento.updated_at = timezone.now()
        if user and user.is_authenticated:
            orcamento.updated_by_id = user.id
        orcamento.save(update_fields=[
            'status_operacional', 'status_financeiro', 'motivo_cancelamento',
            'updated_at', 'updated_by_id'
        ])

    logger.warning(
        f"[ORCAMENTO CANCELADO] Orçamento #{orcamento.id} CANCELADO por Usuário: {user} "
        f"| Motivo: {motivo_sanitizado}"
    )

    return orcamento


def alterar_status_operacional(orcamento, novo_status, user=None):
    """
    Aplica as regras de transição da máquina de estados operacional:
    GERADO -> ENVIADO -> APROVADO -> EM_EXECUCAO -> CONCLUIDO
    """
    novo_status = novo_status.upper().strip()
    status_atuais_validos = [choice[0] for choice in orcamento.STATUS_OPERACIONAL_CHOICES]

    if novo_status not in status_atuais_validos:
        raise ValidationError({'status_operacional': f"Status '{novo_status}' inválido."})

    if orcamento.status_operacional == 'CANCELADO':
        raise ValidationError({'status_operacional': "Orçamento cancelado não pode ter seu status alterado."})

    if novo_status == 'CANCELADO':
        raise ValidationError({
            'status_operacional': "Para cancelar um orçamento, utilize o endpoint específico de cancelamento fornecendo a justificativa."
        })

    # Validação de validade expirada ao aprovar
    if novo_status == 'APROVADO':
        if orcamento.data_validade and orcamento.data_validade < timezone.now().date():
            raise ValidationError({
                'data_validade': (
                    f"Orçamento expirado em {orcamento.data_validade.strftime('%d/%m/%Y')}. "
                    "É obrigatório renovar a validade do orçamento antes da aprovação."
                )
            })

    # Não permitir regredir de CONCLUIDO arbitrariamente
    if orcamento.status_operacional == 'CONCLUIDO' and novo_status != 'CONCLUIDO':
        raise ValidationError({
            'status_operacional': "Orçamento já concluído não pode retornar a etapas anteriores."
        })

    orcamento.status_operacional = novo_status
    orcamento.updated_at = timezone.now()
    if user and user.is_authenticated:
        orcamento.updated_by_id = user.id
    orcamento.save(update_fields=['status_operacional', 'updated_at', 'updated_by_id'])

    logger.info(
        f"[ORCAMENTO STATUS] Orçamento #{orcamento.id} transitou para status operacional '{novo_status}' "
        f"por Usuário: {user}"
    )

    return orcamento
