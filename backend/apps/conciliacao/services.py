"""
Serviços de negócio da Conciliação Bancária Inteligente Split-Screen.
Contempla algoritmo de matching 1:1 e 1:N, liquidação com impacto em saldo,
lançamento rápido no ato, troca de contas e relatório de divergências.
"""
from datetime import date, timedelta, datetime
from decimal import Decimal
from itertools import combinations
from typing import Dict, List, Any, Optional

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

from apps.financeiro.models import LancamentoFinanceiro, ContaBancaria, CategoriaFinanceira, MeioPagamento
from apps.conciliacao.parsers import parse_extrato_arquivo
from core.utils import sanitizar_texto_maiusculo


def processar_extrato_split_screen(
    arquivo,
    conta_id: Optional[int] = None,
    data_inicio_str: Optional[str] = None,
    data_fim_str: Optional[str] = None,
    user=None
) -> Dict[str, Any]:
    """
    Processa upload de extrato bancário (OFX ou CSV) e executa o algoritmo
    de correspondência inteligente com os lançamentos do ERP para renderização Split-Screen.
    """
    dados_extrato = parse_extrato_arquivo(arquivo)
    transacoes_extrato = dados_extrato.get('transacoes', [])
    meta = dados_extrato.get('meta', {})

    conta_obj = None
    if conta_id:
        try:
            conta_obj = ContaBancaria.objects.get(id=conta_id, deleted_at__isnull=True)
            meta['conta_id_selecionada'] = conta_obj.id
            meta['conta_nome_selecionada'] = conta_obj.nome
            meta['conta_saldo_atual'] = float(conta_obj.saldo)
        except ContaBancaria.DoesNotExist:
            raise NotFound("Conta bancária informada não foi encontrada ou está inativa.")

    # Determinação do intervalo de busca no ERP
    dt_inicio: Optional[date] = None
    dt_fim: Optional[date] = None

    if data_inicio_str:
        try:
            dt_inicio = date.fromisoformat(data_inicio_str)
        except ValueError:
            pass
    if data_fim_str:
        try:
            dt_fim = date.fromisoformat(data_fim_str)
        except ValueError:
            pass

    if not dt_inicio and transacoes_extrato:
        datas = [t['data_obj'] for t in transacoes_extrato]
        dt_inicio = min(datas) - timedelta(days=3)
    elif not dt_inicio:
        dt_inicio = timezone.localdate() - timedelta(days=30)

    if not dt_fim and transacoes_extrato:
        datas = [t['data_obj'] for t in transacoes_extrato]
        dt_fim = max(datas) + timedelta(days=3)
    elif not dt_fim:
        dt_fim = timezone.localdate() + timedelta(days=5)

    # Busca lançamentos do ERP no período
    qs_erp = LancamentoFinanceiro.objects.filter(
        deleted_at__isnull=True
    ).exclude(
        status_pagamento='CANCELADO'
    )

    if conta_id:
        # Lançamentos da conta ou lançamentos ainda sem conta atribuída (ex: gerados em faturas)
        qs_erp = qs_erp.filter(Q(conta_id=conta_id) | Q(conta__isnull=True))

    qs_erp = qs_erp.filter(
        Q(data_pagamento__date__range=[dt_inicio, dt_fim]) |
        Q(data_vencimento__range=[dt_inicio, dt_fim])
    ).select_related('conta', 'categoria', 'meio_pagamento', 'conciliado_por')

    lancamentos_erp = list(qs_erp)

    # Mapeamento para matching
    # Estruturas de controle
    transacoes_processadas = []
    lancamentos_usados_ids = set()
    lancamentos_status_map = {}

    # Inicializa todos os lançamentos como PENDENTE ou CONCILIADO
    for lanc in lancamentos_erp:
        if lanc.is_conciliado:
            lancamentos_status_map[lanc.id] = {
                'status_conciliacao': 'CONCILIADO',
                'sugestao_fitid': None,
                'detalhe': 'CONCILIADO PREVIAMENTE'
            }
        else:
            lancamentos_status_map[lanc.id] = {
                'status_conciliacao': 'SOBRA_ERP',
                'sugestao_fitid': None,
                'detalhe': 'NAO LOCALIZADO NO EXTRATO'
            }

    # Executa algoritmo de matching para cada transação do extrato
    for trn in transacoes_extrato:
        trn_valor = trn['valor_decimal']
        trn_valor_abs = abs(trn_valor)
        trn_tipo = trn['tipo'] # 'ENTRADA' ou 'SAIDA'
        trn_data = trn['data_obj']
        fitid = trn['fitid']

        match_encontrado = False
        match_tipo = 'NAO_CONCILIADO'
        lancamentos_sugeridos = []

        # 1. Match Automático 1:1
        for lanc in lancamentos_erp:
            if lanc.id in lancamentos_usados_ids:
                continue

            # Checa correspondência de tipo e valor exato
            if lanc.tipo_lancamento == trn_tipo and lanc.valor == trn_valor_abs:
                # Proximidade de data (±3 dias)
                ref_date = lanc.data_pagamento.date() if lanc.data_pagamento else lanc.data_vencimento
                diff_dias = abs((ref_date - trn_data).days)
                if diff_dias <= 3:
                    match_encontrado = True
                    lancamentos_usados_ids.add(lanc.id)
                    lancamentos_sugeridos.append(lanc.id)

                    if lanc.is_conciliado:
                        match_tipo = 'CONCILIADO'
                        lancamentos_status_map[lanc.id] = {
                            'status_conciliacao': 'CONCILIADO',
                            'sugestao_fitid': fitid,
                            'detalhe': 'CONCILIADO COM ESTA TRANSACAO'
                        }
                    else:
                        match_tipo = 'SUGESTAO_1_1'
                        lancamentos_status_map[lanc.id] = {
                            'status_conciliacao': 'SUGESTAO_MATCH',
                            'sugestao_fitid': fitid,
                            'detalhe': f'MATCH 1:1 SUGERIDO (DIFERENCA DE {diff_dias} DIA(S))'
                        }
                    break

        # 2. Match Múltiplo (1:N) se não encontrou 1:1
        if not match_encontrado:
            candidatos = [
                l for l in lancamentos_erp
                if l.id not in lancamentos_usados_ids
                and l.tipo_lancamento == trn_tipo
                and not l.is_conciliado
                and abs(((l.data_pagamento.date() if l.data_pagamento else l.data_vencimento) - trn_data).days) <= 3
            ]

            # Testa combinações de 2 a 4 títulos cuja soma dê o valor da transação
            for k in range(2, min(len(candidatos) + 1, 5)):
                for combo in combinations(candidatos, k):
                    soma_combo = sum(c.valor for c in combo)
                    if soma_combo == trn_valor_abs:
                        match_encontrado = True
                        match_tipo = 'SUGESTAO_MULTIPLO'
                        combo_ids = [c.id for c in combo]
                        lancamentos_sugeridos.extend(combo_ids)
                        for c in combo:
                            lancamentos_usados_ids.add(c.id)
                            lancamentos_status_map[c.id] = {
                                'status_conciliacao': 'SUGESTAO_MATCH',
                                'sugestao_fitid': fitid,
                                'detalhe': f'MATCH MULTIPLO (1:{k})'
                            }
                        break
                if match_encontrado:
                    break

        transacoes_processadas.append({
            'fitid': fitid,
            'data': trn['data'],
            'valor': trn['valor'],
            'valor_absoluto': trn['valor_absoluto'],
            'tipo': trn_tipo,
            'descricao': trn['descricao'],
            'documento': trn['documento'],
            'status_match': match_tipo,
            'lancamentos_sugeridos_ids': lancamentos_sugeridos,
        })

    # Formata lista de lançamentos do ERP
    erp_processados = []
    for lanc in lancamentos_erp:
        st_info = lancamentos_status_map.get(lanc.id, {
            'status_conciliacao': 'SOBRA_ERP',
            'sugestao_fitid': None,
            'detalhe': 'NAO LOCALIZADO NO EXTRATO'
        })
        erp_processados.append({
            'id': lanc.id,
            'descricao': lanc.descricao or 'SEM DESCRICAO',
            'valor': float(lanc.valor),
            'tipo_lancamento': lanc.tipo_lancamento,
            'data_vencimento': lanc.data_vencimento.isoformat() if lanc.data_vencimento else None,
            'data_pagamento': lanc.data_pagamento.isoformat() if lanc.data_pagamento else None,
            'status_pagamento': lanc.status_pagamento,
            'is_conciliado': lanc.is_conciliado,
            'data_conciliacao': lanc.data_conciliacao.isoformat() if lanc.data_conciliacao else None,
            'conciliado_por_nome': lanc.conciliado_por.nome if lanc.conciliado_por else None,
            'conta_id': lanc.conta_id,
            'conta_nome': lanc.conta.nome if lanc.conta else 'SEM CONTA DEFINIDA',
            'categoria_nome': lanc.categoria.nome if lanc.categoria else 'SEM CATEGORIA',
            'fatura_id': lanc.fatura_id,
            'status_conciliacao': st_info['status_conciliacao'],
            'sugestao_fitid': st_info['sugestao_fitid'],
            'detalhe_match': st_info['detalhe'],
        })

    # Consolidação do Resumo
    total_extrato = len(transacoes_processadas)
    total_erp = len(erp_processados)
    total_conciliados = sum(1 for t in transacoes_processadas if t['status_match'] == 'CONCILIADO')
    total_sugestoes = sum(1 for t in transacoes_processadas if t['status_match'].startswith('SUGESTAO'))
    total_sobras_extrato = sum(1 for t in transacoes_processadas if t['status_match'] == 'NAO_CONCILIADO')
    total_sobras_erp = sum(1 for e in erp_processados if e['status_conciliacao'] == 'SOBRA_ERP')

    return {
        'formato': dados_extrato.get('formato', 'OFX'),
        'meta': meta,
        'periodo': {
            'data_inicio': dt_inicio.isoformat() if dt_inicio else None,
            'data_fim': dt_fim.isoformat() if dt_fim else None,
        },
        'resumo': {
            'total_transacoes_extrato': total_extrato,
            'total_lancamentos_erp': total_erp,
            'total_conciliados': total_conciliados,
            'total_sugestoes': total_sugestoes,
            'total_sobras_extrato': total_sobras_extrato,
            'total_sobras_erp': total_sobras_erp,
        },
        'extrato': transacoes_processadas,
        'transacoes': transacoes_processadas,
        'erp': erp_processados,
    }


def confirmar_conciliacao(
    lancamento_ids: List[int],
    conta_id: int,
    data_conciliacao: Optional[Any] = None,
    user=None
) -> List[LancamentoFinanceiro]:
    """
    Confirma a conciliação de 1 ou N lançamentos financeiros.
    Se o título estiver em 'A_VENCER' ou 'VENCIDO', realiza a liquidação imediata como 'PAGO'
    com impacto no saldo da conta bancária.
    Grava compulsoriamente is_conciliado = True, data_conciliacao e conciliado_por_id.
    """
    if not lancamento_ids:
        raise ValidationError({"lancamento_ids": "Informe ao menos um ID de lançamento financeiro para conciliar."})

    try:
        conta = ContaBancaria.objects.get(id=conta_id, deleted_at__isnull=True)
    except ContaBancaria.DoesNotExist:
        raise NotFound("Conta bancária informada não foi encontrada ou está inativa.")

    dt_conciliacao = data_conciliacao or timezone.now()
    lancamentos_atualizados = []

    with transaction.atomic():
        lancamentos = LancamentoFinanceiro.objects.filter(
            id__in=lancamento_ids,
            deleted_at__isnull=True
        ).exclude(status_pagamento='CANCELADO')

        if not lancamentos.exists():
            raise NotFound("Nenhum lançamento válido encontrado para os IDs informados.")

        for lanc in lancamentos:
            # 1. Se estava pendente, efetua a liquidação real no Regime de Caixa
            if lanc.status_pagamento in ('A_VENCER', 'VENCIDO'):
                lanc.status_pagamento = 'PAGO'
                lanc.data_pagamento = dt_conciliacao
                lanc.conta = conta

                # Impacto em saldo
                if lanc.tipo_lancamento == 'ENTRADA':
                    conta.saldo += lanc.valor
                elif lanc.tipo_lancamento == 'SAIDA':
                    saldo_resultante = conta.saldo - lanc.valor
                    limite_disponivel = -conta.limite_credito
                    if saldo_resultante < limite_disponivel:
                        raise ValidationError(
                            f"Saldo insuficiente na conta '{conta.nome}' para liquidar o lançamento '{lanc.id}'. "
                            f"Saldo: R$ {conta.saldo}, Limite: R$ {conta.limite_credito}, Valor: R$ {lanc.valor}."
                        )
                    conta.saldo -= lanc.valor
                
                conta.updated_by_id = getattr(user, 'id', None)
                conta.save()

            # 2. Se já estava PAGO mas em conta diferente, ajusta a conta
            elif lanc.status_pagamento == 'PAGO' and lanc.conta_id != conta.id:
                conta_antiga = lanc.conta
                if conta_antiga:
                    # Estorna da antiga
                    if lanc.tipo_lancamento == 'ENTRADA':
                        conta_antiga.saldo -= lanc.valor
                    elif lanc.tipo_lancamento == 'SAIDA':
                        conta_antiga.saldo += lanc.valor
                    conta_antiga.updated_by_id = getattr(user, 'id', None)
                    conta_antiga.save()

                # Aplica na nova
                if lanc.tipo_lancamento == 'ENTRADA':
                    conta.saldo += lanc.valor
                elif lanc.tipo_lancamento == 'SAIDA':
                    saldo_resultante = conta.saldo - lanc.valor
                    limite_disponivel = -conta.limite_credito
                    if saldo_resultante < limite_disponivel:
                        raise ValidationError(
                            f"Saldo insuficiente na conta '{conta.nome}' para realocar o lançamento '{lanc.id}'."
                        )
                    conta.saldo -= lanc.valor
                
                conta.updated_by_id = getattr(user, 'id', None)
                conta.save()
                lanc.conta = conta

            # 3. Gravação perpétua de conciliação
            lanc.is_conciliado = True
            lanc.data_conciliacao = dt_conciliacao
            lanc.conciliado_por_id = getattr(user, 'id', None)
            lanc.updated_by_id = getattr(user, 'id', None)
            lanc.save()

            lancamentos_atualizados.append(lanc)

    return lancamentos_atualizados


def desconciliar_lancamento(lancamento_id: int, user=None) -> LancamentoFinanceiro:
    """
    Reverte a marcação de conciliação bancária de um lançamento.
    Não desfaz o pagamento (para manter o regime de caixa), apenas limpa os dados de auditoria do extrato.
    """
    try:
        lanc = LancamentoFinanceiro.objects.get(id=lancamento_id, deleted_at__isnull=True)
    except LancamentoFinanceiro.DoesNotExist:
        raise NotFound("Lançamento financeiro não encontrado.")

    lanc.is_conciliado = False
    lanc.data_conciliacao = None
    lanc.conciliado_por = None
    lanc.updated_by_id = getattr(user, 'id', None)
    lanc.save(update_fields=['is_conciliado', 'data_conciliacao', 'conciliado_por', 'updated_at', 'updated_by_id'])

    return lanc


def realizar_lancamento_rapido(dados: Dict[str, Any], user=None) -> LancamentoFinanceiro:
    """
    Cria instantaneamente um lançamento financeiro liquidado (PAGO) e já marcado como conciliado
    a partir de uma linha do extrato bancário (ex: tarifas, rendimentos, juros, IOF).
    """
    tipo_lancamento = dados.get('tipo_lancamento', 'SAIDA').upper()
    descricao = sanitizar_texto_maiusculo(dados.get('descricao', ''))
    valor = Decimal(str(dados.get('valor', '0.00')))
    conta_id = dados.get('conta_id')
    categoria_id = dados.get('categoria_id')
    meio_pagamento_id = dados.get('meio_pagamento_id')
    data_pagamento = dados.get('data_pagamento') or timezone.now()

    if not descricao:
        raise ValidationError({"descricao": "A descrição do lançamento é obrigatória."})
    if valor <= 0:
        raise ValidationError({"valor": "O valor do lançamento deve ser maior que zero."})
    if not conta_id:
        raise ValidationError({"conta_id": "Informe a conta bancária vinculada."})
    if not categoria_id:
        raise ValidationError({"categoria_id": "Informe a categoria financeira para o DRE."})

    try:
        conta = ContaBancaria.objects.get(id=conta_id, deleted_at__isnull=True)
    except ContaBancaria.DoesNotExist:
        raise NotFound("Conta bancária informada não foi encontrada.")

    try:
        categoria = CategoriaFinanceira.objects.get(id=categoria_id, deleted_at__isnull=True)
    except CategoriaFinanceira.DoesNotExist:
        raise NotFound("Categoria financeira informada não foi encontrada.")

    meio_pagamento = None
    if meio_pagamento_id:
        try:
            meio_pagamento = MeioPagamento.objects.get(id=meio_pagamento_id, deleted_at__isnull=True)
        except MeioPagamento.DoesNotExist:
            pass
    
    if not meio_pagamento:
        # Fallback para o primeiro meio de pagamento ativo
        meio_pagamento = MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()

    with transaction.atomic():
        # Impacto no saldo real
        if tipo_lancamento == 'ENTRADA':
            conta.saldo += valor
        else:
            saldo_resultante = conta.saldo - valor
            limite_disponivel = -conta.limite_credito
            if saldo_resultante < limite_disponivel:
                raise ValidationError(
                    f"Saldo insuficiente na conta '{conta.nome}' para realizar a saída de R$ {valor}."
                )
            conta.saldo -= valor

        conta.updated_by_id = getattr(user, 'id', None)
        conta.save()

        dt_venc = data_pagamento.date() if isinstance(data_pagamento, datetime) else data_pagamento
        if isinstance(dt_venc, str):
            dt_venc = date.fromisoformat(dt_venc.split('T')[0])

        lancamento = LancamentoFinanceiro.objects.create(
            tipo_lancamento=tipo_lancamento,
            descricao=descricao,
            valor=valor,
            data_vencimento=dt_venc,
            data_pagamento=data_pagamento,
            status_pagamento='PAGO',
            conta=conta,
            categoria=categoria,
            meio_pagamento=meio_pagamento,
            is_conciliado=True,
            data_conciliacao=timezone.now(),
            conciliado_por_id=getattr(user, 'id', None),
            created_by_id=getattr(user, 'id', None),
            updated_by_id=getattr(user, 'id', None),
        )

    return lancamento


def trocar_conta_lancamento(lancamento_id: int, nova_conta_id: int, user=None) -> LancamentoFinanceiro:
    """
    Troca em 1 clique a conta bancária de um lançamento financeiro do ERP,
    remanejando o saldo caso o lançamento já esteja em status PAGO.
    """
    try:
        lanc = LancamentoFinanceiro.objects.get(id=lancamento_id, deleted_at__isnull=True)
    except LancamentoFinanceiro.DoesNotExist:
        raise NotFound("Lançamento financeiro não encontrado.")

    try:
        nova_conta = ContaBancaria.objects.get(id=nova_conta_id, deleted_at__isnull=True)
    except ContaBancaria.DoesNotExist:
        raise NotFound("Nova conta bancária não encontrada.")

    if lanc.conta_id == nova_conta.id:
        return lanc

    with transaction.atomic():
        if lanc.status_pagamento == 'PAGO':
            # Estorna da conta antiga
            conta_antiga = lanc.conta
            if conta_antiga:
                if lanc.tipo_lancamento == 'ENTRADA':
                    conta_antiga.saldo -= lanc.valor
                elif lanc.tipo_lancamento == 'SAIDA':
                    conta_antiga.saldo += lanc.valor
                conta_antiga.updated_by_id = getattr(user, 'id', None)
                conta_antiga.save()

            # Debita/Credita na nova conta
            if lanc.tipo_lancamento == 'ENTRADA':
                nova_conta.saldo += lanc.valor
            elif lanc.tipo_lancamento == 'SAIDA':
                saldo_resultante = nova_conta.saldo - lanc.valor
                limite_disponivel = -nova_conta.limite_credito
                if saldo_resultante < limite_disponivel:
                    raise ValidationError(
                        f"Saldo insuficiente na nova conta '{nova_conta.nome}' para transferir o lançamento."
                    )
                nova_conta.saldo -= lanc.valor

            nova_conta.updated_by_id = getattr(user, 'id', None)
            nova_conta.save()

        lanc.conta = nova_conta
        lanc.updated_by_id = getattr(user, 'id', None)
        lanc.save(update_fields=['conta', 'updated_at', 'updated_by_id'])

    return lanc


def obter_relatorio_divergencias(
    conta_id: Optional[int] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
    transacoes_extrato: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Gera dados estruturados para o Relatório de Divergências de Conciliação em 2 abas:
    - Aba 1: Sobras do Extrato Bancário (Transações no banco sem correspondência no ERP).
    - Aba 2: Sobras do ERP (Lançamentos manuais realizados/pendentes no ERP não localizados no banco).
    """
    dt_inicio = data_inicio or (timezone.localdate() - timedelta(days=30))
    dt_fim = data_fim or timezone.localdate()

    # Busca Sobras do ERP (não conciliados no período)
    qs_erp = LancamentoFinanceiro.objects.filter(
        deleted_at__isnull=True,
        is_conciliado=False
    ).exclude(
        status_pagamento='CANCELADO'
    ).filter(
        Q(data_pagamento__date__range=[dt_inicio, dt_fim]) |
        Q(data_vencimento__range=[dt_inicio, dt_fim])
    ).select_related('conta', 'categoria', 'meio_pagamento')

    if conta_id:
        qs_erp = qs_erp.filter(Q(conta_id=conta_id) | Q(conta__isnull=True))

    sobras_erp = []
    total_valor_sobras_erp_entrada = Decimal('0.00')
    total_valor_sobras_erp_saida = Decimal('0.00')

    for lanc in qs_erp:
        if lanc.tipo_lancamento == 'ENTRADA':
            total_valor_sobras_erp_entrada += lanc.valor
        else:
            total_valor_sobras_erp_saida += lanc.valor

        sobras_erp.append({
            'id': lanc.id,
            'descricao': lanc.descricao or 'SEM DESCRICAO',
            'valor': float(lanc.valor),
            'tipo_lancamento': lanc.tipo_lancamento,
            'data_vencimento': lanc.data_vencimento.isoformat() if lanc.data_vencimento else None,
            'data_pagamento': lanc.data_pagamento.isoformat() if lanc.data_pagamento else None,
            'status_pagamento': lanc.status_pagamento,
            'conta_id': lanc.conta_id,
            'conta_nome': lanc.conta.nome if lanc.conta else 'SEM CONTA DEFINIDA',
            'categoria_nome': lanc.categoria.nome if lanc.categoria else 'SEM CATEGORIA',
            'acoes_disponiveis': ['TROCAR_CONTA', 'ESTORNAR', 'MANTER_PENDENTE'],
        })

    # Sobras do Extrato
    sobras_extrato = []
    total_valor_sobras_extrato_entrada = Decimal('0.00')
    total_valor_sobras_extrato_saida = Decimal('0.00')

    if transacoes_extrato:
        for trn in transacoes_extrato:
            if trn.get('status_match') == 'NAO_CONCILIADO':
                val = Decimal(str(trn.get('valor_absoluto', 0.00)))
                if trn.get('tipo') == 'ENTRADA':
                    total_valor_sobras_extrato_entrada += val
                else:
                    total_valor_sobras_extrato_saida += val

                sobras_extrato.append({
                    'fitid': trn.get('fitid'),
                    'data': trn.get('data'),
                    'valor': trn.get('valor'),
                    'valor_absoluto': trn.get('valor_absoluto'),
                    'tipo': trn.get('tipo'),
                    'descricao': trn.get('descricao'),
                    'documento': trn.get('documento'),
                    'acoes_disponiveis': ['LANCAMENTO_RAPIDO', 'IGNORAR'],
                })

    return {
        'periodo': {
            'data_inicio': dt_inicio.isoformat(),
            'data_fim': dt_fim.isoformat(),
        },
        'conta_id_filtro': conta_id,
        'aba_1_sobras_extrato': {
            'titulo': 'SOBRAS DO EXTRATO BANCARIO (CONSTA NO BANCO, FALTA NO ERP)',
            'total_registros': len(sobras_extrato),
            'total_entradas': float(total_valor_sobras_extrato_entrada),
            'total_saidas': float(total_valor_sobras_extrato_saida),
            'itens': sobras_extrato,
        },
        'aba_2_sobras_erp': {
            'titulo': 'SOBRAS DO ERP (CONSTA NO ERP, FALTA NO EXTRATO BANCARIO)',
            'total_registros': len(sobras_erp),
            'total_entradas': float(total_valor_sobras_erp_entrada),
            'total_saidas': float(total_valor_sobras_erp_saida),
            'itens': sobras_erp,
        },
    }
