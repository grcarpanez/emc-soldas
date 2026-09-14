"""
Serviços de negócio da Conciliação Bancária Inteligente Split-Screen.
Contempla algoritmo de matching 1:1 e 1:N, liquidação com impacto em saldo,
lançamento rápido no ato, troca de contas e relatório de divergências.
"""
from datetime import date, timedelta, datetime
from decimal import Decimal
from itertools import combinations
from typing import Dict, List, Any, Optional

import re
import logging
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

from apps.financeiro.models import LancamentoFinanceiro, ContaBancaria, CategoriaFinanceira, MeioPagamento
from apps.cadastros.models import ClienteFornecedor
from apps.administracao.models import ConfiguracaoGlobal
from apps.faturamento.models import Fatura
from apps.faturamento.services import receber_pagamento_fatura
from apps.conciliacao.parsers import parse_extrato_arquivo
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos

logger = logging.getLogger(__name__)


def detectar_meio_pagamento_transacao(
    descricao: str,
    tipo: str,
    tipo_original_ofx: str = '',
    meios_cache: Optional[Dict[str, MeioPagamento]] = None
) -> Optional[Dict[str, Any]]:
    """
    Classifica heuristicamente o Meio de Pagamento (PIX, Cartões, TED, Boleto, Dinheiro)
    a partir da descrição (<MEMO>), canal e tipo original do extrato.
    """
    if not meios_cache:
        meios_cache = {m.nome.upper(): m for m in MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True)}

    desc_upper = (descricao or '').upper()
    trntype_upper = (tipo_original_ofx or '').upper()

    nome_meio_alvo = None

    # 1. PIX
    if any(k in desc_upper for k in ['PIX', 'TRANSF PIX', 'PAGTO PIX', 'LIQ PIX', 'QR CODE', 'CHAVE PIX', 'PIX RECEBIDO', 'PIX ENVIADO']):
        nome_meio_alvo = 'PIX'

    # 2. Cartão de Débito / Crédito
    elif any(k in desc_upper for k in ['CARTAO', 'MAQ', 'POS ', 'CIELO', 'REDE', 'GETNET', 'STONE', 'PAGSEGURO', 'VISA', 'MASTER', 'ELO ']) or trntype_upper == 'POS':
        if any(k in desc_upper for k in ['DEB', 'DEBITO']) or (trntype_upper == 'POS' and tipo == 'SAIDA'):
            nome_meio_alvo = 'CARTAO DE DEBITO'
        else:
            nome_meio_alvo = 'CARTAO DE CREDITO'

    # 3. Transferência Bancária (TED / DOC / TEF / Inter-contas)
    elif any(k in desc_upper for k in ['TED ', 'DOC ', 'TEF ', 'TRANSF ', 'TRANSFERENCIA', 'TRANSF ENTRE CONTAS', 'TRANSF C/C', 'DOC/TED']):
        nome_meio_alvo = 'TRANSFERENCIA TED/DOC'

    # 4. Boleto Bancário / Título / Convênio
    elif any(k in desc_upper for k in ['BOLETO', 'TITULO', 'PAGTO TITULO', 'COBRANCA', 'LIQ TITULO', 'LIQ COBRANCA', 'CONVENIO', 'BLOQUETO']):
        nome_meio_alvo = 'BOLETO BANCARIO'

    # 5. Dinheiro / Depósito / Saque
    elif any(k in desc_upper for k in ['DEPOSITO', 'DEP DINHEIRO', 'SAQUE', 'ESPECIE']):
        nome_meio_alvo = 'DEPOSITO BANCARIO' if tipo == 'ENTRADA' else 'DINHEIRO'

    # 6. Fallback Heurístico Baseado no Fluxo
    if not nome_meio_alvo:
        if tipo == 'ENTRADA':
            # Recebimento sem menção específica costuma ser PIX ou TED
            nome_meio_alvo = 'PIX' if 'PIX' in meios_cache else 'TRANSFERENCIA TED/DOC'
        else:
            # Pagamento avulso genérico costuma ser PIX ou Boleto
            nome_meio_alvo = 'PIX' if 'PIX' in meios_cache else 'BOLETO BANCARIO'

    # Localiza objeto no cache
    meio_obj = meios_cache.get(nome_meio_alvo)
    if not meio_obj and meios_cache:
        meio_obj = list(meios_cache.values())[0]

    if meio_obj:
        return {'id': meio_obj.id, 'nome': meio_obj.nome}
    return None


def enriquecer_transacao_inteligencia(
    trn: Dict[str, Any],
    conta_id: Optional[int],
    config_global: Optional[ConfiguracaoGlobal],
    parceiros_map: Dict[str, ClienteFornecedor],
    categorias_despesa: List[CategoriaFinanceira],
    categorias_receita: List[CategoriaFinanceira],
    meios_cache: Optional[Dict[str, MeioPagamento]] = None
) -> Dict[str, Any]:
    """
    Enriquece uma transação de extrato com inteligência heurística:
    1. Prevenção de duplicidade por FITID ou combinação defensiva;
    2. Identificação de Cliente/Fornecedor por CNPJ/CPF no histórico;
    3. Cruzamento com Faturas em Aberto (com cálculo de ISS Retido e tolerância de 5 centavos);
    4. Sugestão automática de Categorias DRE (Tarifas, Tributos, Receitas);
    5. Detecção automática de Meio de Pagamento (PIX, Cartões, TED, Boleto).
    """
    fitid = trn.get('fitid') or ''
    tipo = trn.get('tipo', 'ENTRADA')
    valor_abs = abs(Decimal(str(trn.get('valor', 0))))
    data_obj = trn.get('data_obj') or date.fromisoformat(trn['data'])
    descricao = trn.get('descricao', '')

    duplicidade = False
    duplicidade_motivo = ''
    lancamento_duplicado_id = None

    # 1. Checagem de Duplicidade
    if fitid:
        lanc_existente = LancamentoFinanceiro.objects.filter(
            fitid=fitid,
            deleted_at__isnull=True
        ).first()
        if lanc_existente:
            duplicidade = True
            duplicidade_motivo = f"Transação com FITID '{fitid}' já registrada no ERP (Lançamento #{lanc_existente.id})"
            lancamento_duplicado_id = lanc_existente.id

    if not duplicidade and conta_id:
        # Checagem defensiva por valor idêntico e data próxima (±2 dias) já conciliado
        lanc_conciliado = LancamentoFinanceiro.objects.filter(
            conta_id=conta_id,
            tipo_lancamento=tipo,
            valor=valor_abs,
            data_pagamento__date__range=[data_obj - timedelta(days=2), data_obj + timedelta(days=2)],
            is_conciliado=True,
            deleted_at__isnull=True
        ).first()
        if lanc_conciliado:
            duplicidade = True
            duplicidade_motivo = f"Lançamento idêntico já conciliado nesta conta (Lançamento #{lanc_conciliado.id})"
            lancamento_duplicado_id = lanc_conciliado.id

    # 2. Reconhecimento de Parceiro por CNPJ/CPF na descrição
    parceiro_identificado = None
    cnpjs_cpfs = re.findall(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b|\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', descricao)

    if cnpjs_cpfs:
        doc_limpo = limpar_apenas_digitos(cnpjs_cpfs[0])
        cli = parceiros_map.get(doc_limpo)
        if not cli:
            cli = ClienteFornecedor.objects.filter(
                Q(cnpj_cpf=doc_limpo) | Q(cnpj_cpf=cnpjs_cpfs[0]),
                deleted_at__isnull=True
            ).first()
            if cli:
                parceiros_map[doc_limpo] = cli

        if cli:
            parceiro_identificado = {
                'id': cli.id,
                'nome_razao': cli.nome_razao,
                'tipo': cli.tipo,
                'cnpj_cpf': cli.cnpj_cpf,
                'iss_retido': getattr(cli, 'iss_retido', False)
            }

    # 3. Cruzamento com Faturas em Aberto (com ISS Retido e tolerância de 5 centavos)
    fatura_sugerida = None
    if tipo == 'ENTRADA' and parceiro_identificado and str(parceiro_identificado['tipo']).upper() in ['CLIENTE', 'AMBOS']:
        faturas_candidatas = Fatura.objects.filter(
            cliente_id=parceiro_identificado['id'],
            status='FATURADA',
            deleted_at__isnull=True
        ).order_by('data_fechamento', 'id')

        aliquota_iss = config_global.aliquota_iss if (config_global and parceiro_identificado.get('iss_retido')) else Decimal('0.00')

        for fatura in faturas_candidatas:
            val_fatura = fatura.valor_total_faturado
            val_iss = (val_fatura * (aliquota_iss / Decimal('100.00'))).quantize(Decimal('0.01'))
            val_liquido = val_fatura - val_iss

            # Tolerância de 5 centavos
            if abs(valor_abs - val_liquido) <= Decimal('0.05'):
                fatura_sugerida = {
                    'id': fatura.id,
                    'numero': fatura.id,
                    'valor_fatura': float(val_fatura),
                    'valor_iss': float(val_iss),
                    'valor_liquido': float(val_liquido),
                    'iss_retido_aplicado': bool(aliquota_iss > Decimal('0.00')),
                    'aliquota_iss': float(aliquota_iss),
                    'detalhe': f"Fatura #{fatura.id} com retenção de ISS ({aliquota_iss}%)"
                }
                break
            elif abs(valor_abs - val_fatura) <= Decimal('0.05'):
                fatura_sugerida = {
                    'id': fatura.id,
                    'numero': fatura.id,
                    'valor_fatura': float(val_fatura),
                    'valor_iss': 0.0,
                    'valor_liquido': float(val_fatura),
                    'iss_retido_aplicado': False,
                    'aliquota_iss': 0.0,
                    'detalhe': f"Fatura #{fatura.id} valor integral"
                }
                break

    # 4. Classificação Heurística de Categorias DRE
    categoria_sugerida = None
    desc_upper = descricao.upper()

    if tipo == 'SAIDA':
        # Tarifas Bancárias
        if any(w in desc_upper for w in ['TAR ', 'TARIFA', 'MANUT', 'IOF', 'DOC/TED', 'TAXA TRANSF', 'TAXA MAQ', 'CESTA BANC']):
            cat = next((c for c in categorias_despesa if any(k in c.nome.upper() for k in ['TARIFA', 'BANCAR', 'DESPESAS FINANCEIRAS'])), None)
            if cat:
                categoria_sugerida = {'id': cat.id, 'nome': cat.nome}
        # Tributos e Encargos
        elif any(w in desc_upper for w in ['DAS ', 'SIMPLES NACIONAL', 'GPS', 'FGTS', 'DARF', 'TRIBUTO', 'ARRECADACAO', 'RECEITA FEDERAL', 'PREFEITURA', 'INSS', 'IPTU', 'IPVA']):
            cat = next((c for c in categorias_despesa if any(k in c.nome.upper() for k in ['TRIBUTO', 'IMPOSTO', 'ENCARGO'])), None)
            if cat:
                categoria_sugerida = {'id': cat.id, 'nome': cat.nome}
    elif tipo == 'ENTRADA':
        if parceiro_identificado or fatura_sugerida:
            cat = next((c for c in categorias_receita if any(k in c.nome.upper() for k in ['SERVICO', 'SOLDA', 'REFORMA', 'RECEITA OPERACIONAL'])), None)
            if not cat and categorias_receita:
                cat = categorias_receita[0]
            if cat:
                categoria_sugerida = {'id': cat.id, 'nome': cat.nome}

    # 5. Detecção Heurística do Meio de Pagamento
    meio_pagamento_sugerido = detectar_meio_pagamento_transacao(
        descricao=descricao,
        tipo=tipo,
        tipo_original_ofx=trn.get('tipo_original_ofx', ''),
        meios_cache=meios_cache
    )

    return {
        'duplicidade': duplicidade,
        'duplicidade_motivo': duplicidade_motivo,
        'lancamento_duplicado_id': lancamento_duplicado_id,
        'parceiro_identificado': parceiro_identificado,
        'fatura_sugerida': fatura_sugerida,
        'categoria_sugerida': categoria_sugerida,
        'meio_pagamento_sugerido': meio_pagamento_sugerido
    }


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

    # Cache de categorias, parceiros, meios de pagamento e configuração global para enriquecimento com inteligência
    config_global = ConfiguracaoGlobal.objects.first()
    parceiros_map = {}
    categorias_despesa = list(CategoriaFinanceira.objects.filter(tipo='DESPESA', deleted_at__isnull=True))
    categorias_receita = list(CategoriaFinanceira.objects.filter(tipo='RECEITA', deleted_at__isnull=True))
    meios_cache = {m.nome.upper(): m for m in MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True)}

    # Executa algoritmo de matching para cada transação do extrato
    for trn in transacoes_extrato:
        trn_valor = trn['valor_decimal']
        trn_valor_abs = abs(trn_valor)
        trn_tipo = trn['tipo'] # 'ENTRADA' ou 'SAIDA'
        trn_data = trn['data_obj']
        fitid = trn['fitid']
        descricao = trn.get('descricao', '')

        # Enriquecimento com inteligência avançada (duplicidade, CNPJ/CPF, ISS retido, faturas, categorias e meio de pagamento)
        info_inteligencia = enriquecer_transacao_inteligencia(
            trn=trn,
            conta_id=conta_id,
            config_global=config_global,
            parceiros_map=parceiros_map,
            categorias_despesa=categorias_despesa,
            categorias_receita=categorias_receita,
            meios_cache=meios_cache
        )

        match_encontrado = False
        match_tipo = 'NAO_CONCILIADO'
        lancamentos_sugeridos = []

        # Se detectou duplicidade direta no ERP
        if info_inteligencia['duplicidade']:
            match_encontrado = True
            match_tipo = 'CONCILIADO' if 'CONCILIADO' in info_inteligencia['duplicidade_motivo'] else 'SUGESTAO_1_1'
            dup_id = info_inteligencia.get('lancamento_duplicado_id')
            if dup_id:
                lancamentos_usados_ids.add(dup_id)
                lancamentos_sugeridos.append(dup_id)
                lancamentos_status_map[dup_id] = {
                    'status_conciliacao': 'CONCILIADO' if match_tipo == 'CONCILIADO' else 'SUGESTAO_MATCH',
                    'sugestao_fitid': fitid,
                    'detalhe': info_inteligencia['duplicidade_motivo']
                }

        # 1. Match Automático 1:1 (caso não tenha sido detectada duplicidade prévia)
        if not match_encontrado:
            for lanc in lancamentos_erp:
                if lanc.id in lancamentos_usados_ids:
                    continue

                # Checa correspondência de tipo e valor exato
                if lanc.tipo_lancamento == trn_tipo and lanc.valor == trn_valor_abs:
                    # Checa proximidade de data (±3 dias de tolerância bancária)
                    dt_lanc = lanc.data_pagamento.date() if lanc.data_pagamento else lanc.data_vencimento
                    dias_diferenca = abs((dt_lanc - trn_data).days)
                    if dias_diferenca <= 3:
                        match_encontrado = True
                        match_tipo = 'SUGESTAO_1_1'
                        lancamentos_usados_ids.add(lanc.id)
                        lancamentos_sugeridos.append(lanc.id)
                        lancamentos_status_map[lanc.id] = {
                            'status_conciliacao': 'SUGESTAO_MATCH',
                            'sugestao_fitid': fitid,
                            'detalhe': f'MATCH 1:1 (DIFERENCA DE {dias_diferenca} DIA(S))'
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
            'descricao': descricao,
            'documento': trn['documento'],
            'status_match': match_tipo,
            'lancamentos_sugeridos_ids': lancamentos_sugeridos,
            'duplicidade': info_inteligencia['duplicidade'],
            'duplicidade_motivo': info_inteligencia['duplicidade_motivo'],
            'parceiro_identificado': info_inteligencia['parceiro_identificado'],
            'fatura_sugerida': info_inteligencia['fatura_sugerida'],
            'categoria_sugerida': info_inteligencia['categoria_sugerida'],
            'meio_pagamento_sugerido': info_inteligencia['meio_pagamento_sugerido'],
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


def executar_importacao_lote(
    conta_id: int,
    lancamentos_dados: List[Dict[str, Any]],
    user=None
) -> Dict[str, Any]:
    """
    Cria, liquida e concilia em lote uma lista de movimentações bancárias geradas
    a partir do extrato (Modo Importação Total & Geração em Lote).
    Opera em transação atômica, atualiza o saldo real da conta bancária e registra
    auditoria perpétua.
    """
    if not lancamentos_dados:
        raise ValidationError({"lancamentos": "Nenhum lançamento informado para importação em lote."})

    try:
        conta = ContaBancaria.objects.get(id=conta_id, deleted_at__isnull=True)
    except ContaBancaria.DoesNotExist:
        raise NotFound("Conta bancária informada não foi encontrada ou está inativa.")

    # Busca categorias válidas em massa
    cat_ids = {item['categoria_id'] for item in lancamentos_dados}
    categorias_map = {
        cat.id: cat for cat in CategoriaFinanceira.objects.filter(id__in=cat_ids, deleted_at__isnull=True)
    }

    # Meio de pagamento padrão se não fornecido
    meio_padrao = MeioPagamento.objects.filter(ativo=True, deleted_at__isnull=True).first()

    now = timezone.now()
    user_id = getattr(user, 'id', None)

    total_entradas = Decimal('0.00')
    total_saidas = Decimal('0.00')
    lancamentos_criados = []

    with transaction.atomic():
        for item in lancamentos_dados:
            cat_id = item['categoria_id']
            if cat_id not in categorias_map:
                raise ValidationError({"categoria_id": f"Categoria financeira #{cat_id} não encontrada ou inativa."})

            categoria = categorias_map[cat_id]
            tipo = item['tipo_lancamento'].upper()
            valor = Decimal(str(item['valor']))
            descricao = sanitizar_texto_maiusculo(item['descricao'])
            dt_pagto = item['data_pagamento']

            if isinstance(dt_pagto, str):
                try:
                    dt_pagto = datetime.fromisoformat(dt_pagto.replace('Z', '+00:00'))
                except ValueError:
                    dt_pagto = now

            dt_venc = dt_pagto.date() if isinstance(dt_pagto, datetime) else dt_pagto

            # Meio de pagamento específico do item ou detectado heuristicamente
            meio = None
            if item.get('meio_pagamento_id'):
                meio = MeioPagamento.objects.filter(id=item['meio_pagamento_id'], deleted_at__isnull=True).first()
            if not meio:
                meio_detectado = detectar_meio_pagamento_transacao(descricao=descricao, tipo=tipo)
                if meio_detectado:
                    meio = MeioPagamento.objects.filter(id=meio_detectado['id'], deleted_at__isnull=True).first()
            if not meio:
                meio = meio_padrao

            # Atualiza totalizadores de saldo
            if tipo == 'ENTRADA':
                total_entradas += valor
            else:
                total_saidas += valor

            # Se for vinculação com Fatura em aberto, executa baixa de fatura
            fatura_id = item.get('fatura_id')
            if fatura_id and tipo == 'ENTRADA':
                try:
                    fatura_obj = Fatura.objects.get(id=fatura_id, status='FATURADA', deleted_at__isnull=True)
                    # Executa baixa via serviço de faturamento
                    receber_pagamento_fatura(
                        fatura=fatura_obj,
                        valor=valor,
                        conta_id=conta.id,
                        meio_pagamento_id=meio.id if meio else None,
                        data_pagamento=dt_pagto,
                        user=user
                    )
                    # Marca os lançamentos da fatura como conciliados e atribui fitid
                    lancs_fatura = fatura_obj.lancamentos_financeiros.filter(
                        status_pagamento='PAGO',
                        is_conciliado=False
                    )
                    for lf in lancs_fatura:
                        lf.is_conciliado = True
                        lf.data_conciliacao = now
                        lf.conciliado_por = user
                        if item.get('fitid'):
                            lf.fitid = item.get('fitid')
                        lf.save(update_fields=['is_conciliado', 'data_conciliacao', 'conciliado_por', 'fitid', 'updated_at'])
                        lancamentos_criados.append(lf)
                    
                    # Como receber_pagamento_fatura já credita conta.saldo, não duplicamos o crédito no final
                    total_entradas -= valor
                    continue
                except Fatura.DoesNotExist:
                    pass

            # Cria lançamento já liquidado e conciliado (Receita/Despesa direta, suportando cliente/fornecedor e fitid)
            cli_forn_id = item.get('cliente_fornecedor_id')
            fitid_val = item.get('fitid') or None

            lanc = LancamentoFinanceiro.objects.create(
                conta=conta,
                categoria=categoria,
                meio_pagamento=meio,
                cliente_fornecedor_id=cli_forn_id,
                fitid=fitid_val,
                tipo_lancamento=tipo,
                descricao=descricao,
                valor=valor,
                data_vencimento=dt_venc,
                data_pagamento=dt_pagto,
                status_pagamento='PAGO',
                is_conciliado=True,
                data_conciliacao=now,
                conciliado_por=user,
                created_by_id=user_id,
                updated_by_id=user_id
            )
            lancamentos_criados.append(lanc)

        # Impacto consolidado no saldo real da conta
        delta_saldo = total_entradas - total_saidas
        novo_saldo = conta.saldo + delta_saldo
        limite_disponivel = -conta.limite_credito

        if novo_saldo < limite_disponivel:
            raise ValidationError(
                f"Saldo insuficiente na conta '{conta.nome}' para processar a importação em lote. "
                f"Saldo Atual: R$ {conta.saldo}, Saídas: R$ {total_saidas}, Entradas: R$ {total_entradas}, "
                f"Limite Especial: R$ {conta.limite_credito}."
            )

        conta.saldo = novo_saldo
        conta.updated_by_id = user_id
        conta.save(update_fields=['saldo', 'updated_at', 'updated_by_id'])

    return {
        'status': 'sucesso',
        'mensagem': f"{len(lancamentos_criados)} lançamento(s) gerado(s) e conciliado(s) em lote com sucesso!",
        'total_processados': len(lancamentos_criados),
        'total_entradas': float(total_entradas),
        'total_saidas': float(total_saidas),
        'novo_saldo_conta': float(conta.saldo),
        'lancamentos_ids': [l.id for l in lancamentos_criados]
    }

