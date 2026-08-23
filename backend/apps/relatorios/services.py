"""
Camada de serviços analíticos e inteligência de negócios para o sistema EMC Soldas.
Implementa agregações para o Dashboard Principal e os 6 Relatórios Estratégicos do ERP.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, F, Avg
from django.utils import timezone

from apps.orcamentos.models import Orcamento, OrcamentoItem
from apps.faturamento.models import Fatura
from apps.financeiro.models import (
    LancamentoFinanceiro, ContaBancaria, CartaoCredito, FaturaCartao,
    CategoriaFinanceira, MeioPagamento, LogEstorno
)
from apps.cadastros.models import ClienteFornecedor, Equipamento, ClienteEquipamento
from apps.catalogo.models import Item, Produto, FichaTecnica
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem
from core.utils import sanitizar_texto_maiusculo


def normalizar_datas(data_inicio=None, data_fim=None):
    """
    Normaliza parâmetros de data. Se não informados, assume o mês corrente.
    Retorna objetos datetime.date.
    """
    hoje = timezone.localdate()
    if not data_inicio:
        data_inicio = hoje.replace(day=1)
    elif isinstance(data_inicio, str):
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
        except ValueError:
            data_inicio = hoje.replace(day=1)

    if not data_fim:
        data_fim = hoje
    elif isinstance(data_fim, str):
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            data_fim = hoje

    return data_inicio, data_fim


class DashboardService:
    """Serviço de agregação e métricas do Dashboard Principal."""

    @staticmethod
    def obter_flip_cards(data_inicio=None, data_fim=None):
        """
        Calcula os indicadores analíticos dos 5 Flip Cards interativos do Dashboard:
        1. Operação (Orçamentos)
        2. Faturamento (Faturas)
        3. Receita (Real vs Projetada)
        4. Caixa (Real vs Projetado)
        5. Alertas Financeiros
        """
        data_inicio, data_fim = normalizar_datas(data_inicio, data_fim)
        hoje = timezone.localdate()

        # ==========================================
        # 1. CARD: OPERAÇÃO (ORÇAMENTOS)
        # ==========================================
        orcamentos_qs = Orcamento.objects.filter(
            deleted_at__isnull=True,
            data_geracao__range=(data_inicio, data_fim)
        )
        total_orcamentos = orcamentos_qs.count()
        orcamentos_aprovados = orcamentos_qs.filter(
            status_operacional__in=['APROVADO', 'EM_EXECUCAO', 'CONCLUIDO']
        ).count()
        orcamentos_concluidos = orcamentos_qs.filter(
            status_operacional='CONCLUIDO'
        ).count()
        orcamentos_gerados = orcamentos_qs.filter(
            status_operacional='GERADO'
        ).count()

        taxa_aprovacao = Decimal('0.00')
        if total_orcamentos > 0:
            taxa_aprovacao = (Decimal(orcamentos_aprovados) / Decimal(total_orcamentos) * Decimal('100.00')).quantize(Decimal('0.01'))

        valor_total_orcado = orcamentos_qs.aggregate(total=Sum('valor_bruto'))['total'] or Decimal('0.00')
        valor_aprovado = orcamentos_qs.filter(
            status_operacional__in=['APROVADO', 'EM_EXECUCAO', 'CONCLUIDO']
        ).aggregate(
            total=Sum(F('valor_bruto') - F('valor_desconto_aplicado'))
        )['total'] or Decimal('0.00')

        card_operacao = {
            'total_orcamentos': total_orcamentos,
            'orcamentos_gerados': orcamentos_gerados,
            'orcamentos_aprovados': orcamentos_aprovados,
            'orcamentos_concluidos': orcamentos_concluidos,
            'taxa_aprovacao_percentual': taxa_aprovacao,
            'valor_total_orcado': valor_total_orcado,
            'valor_total_aprovado': valor_aprovado,
        }

        # ==========================================
        # 2. CARD: FATURAMENTO (FATURAS)
        # ==========================================
        faturas_qs = Fatura.objects.filter(
            deleted_at__isnull=True,
            data_emissao__range=(data_inicio, data_fim)
        )
        total_faturas = faturas_qs.count()
        faturas_rascunho = faturas_qs.filter(status='RASCUNHO').count()
        faturas_faturadas = faturas_qs.filter(status='FATURADA').count()
        faturas_pagas = faturas_qs.filter(status='PAGA').count()

        valor_bruto_faturado = faturas_qs.filter(
            status__in=['FATURADA', 'PAGA']
        ).aggregate(total=Sum('valor_bruto'))['total'] or Decimal('0.00')

        desconto_faturado = faturas_qs.filter(
            status__in=['FATURADA', 'PAGA']
        ).aggregate(total=Sum('desconto_global'))['total'] or Decimal('0.00')

        valor_liquido_faturado = faturas_qs.filter(
            status__in=['FATURADA', 'PAGA']
        ).aggregate(total=Sum('valor_total_faturado'))['total'] or Decimal('0.00')

        card_faturamento = {
            'total_faturas': total_faturas,
            'faturas_rascunho': faturas_rascunho,
            'faturas_faturadas': faturas_faturadas,
            'faturas_pagas': faturas_pagas,
            'valor_bruto_faturado': valor_bruto_faturado,
            'desconto_total_concedido': desconto_faturado,
            'valor_liquido_faturado': valor_liquido_faturado,
        }

        # ==========================================
        # 3. CARD: RECEITA (REAL VS PROJETADO)
        # ==========================================
        # Receita Real: baixas efetivadas de entrada com status PAGO
        receita_real = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='ENTRADA',
            status_pagamento='PAGO',
            data_pagamento__date__range=(data_inicio, data_fim)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # Receita Projetada: todas as previsões a receber com vencimento no período
        receita_projetada = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='ENTRADA',
            status_pagamento__in=['A_VENCER', 'VENCIDO', 'PAGO'],
            data_vencimento__range=(data_inicio, data_fim)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        taxa_realizacao_receita = Decimal('0.00')
        if receita_projetada > 0:
            taxa_realizacao_receita = (receita_real / receita_projetada * Decimal('100.00')).quantize(Decimal('0.01'))

        card_receita = {
            'receita_real': receita_real,
            'receita_projetada': receita_projetada,
            'taxa_realizacao_percentual': taxa_realizacao_receita,
            'diferenca_projetado_real': receita_projetada - receita_real,
        }

        # ==========================================
        # 4. CARD: CAIXA (REAL VS PROJETADO)
        # ==========================================
        saldo_real_consolidado = ContaBancaria.objects.filter(
            deleted_at__isnull=True
        ).aggregate(total=Sum('saldo'))['total'] or Decimal('0.00')

        previsao_entradas_caixa = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='ENTRADA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__range=(data_inicio, data_fim)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        previsao_saidas_caixa = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='SAIDA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__range=(data_inicio, data_fim)
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        saldo_projetado = saldo_real_consolidado + previsao_entradas_caixa - previsao_saidas_caixa

        card_caixa = {
            'saldo_real_consolidado': saldo_real_consolidado,
            'previsao_entradas': previsao_entradas_caixa,
            'previsao_saidas': previsao_saidas_caixa,
            'saldo_projetado': saldo_projetado,
        }

        # ==========================================
        # 5. CARD: ALERTAS FINANCEIROS
        # ==========================================
        limite_7_dias = hoje + timedelta(days=7)

        # Contas a Pagar Atrasadas
        despesas_vencidas_qs = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='SAIDA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__lt=hoje
        )
        contas_vencidas_qtd = despesas_vencidas_qs.count()
        contas_vencidas_valor = despesas_vencidas_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # Contas a Receber Atrasadas
        recebimentos_vencidos_qs = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='ENTRADA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__lt=hoje
        )
        recebimentos_vencidos_qtd = recebimentos_vencidos_qs.count()
        recebimentos_vencidos_valor = recebimentos_vencidos_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # Contas a Pagar Vencendo Hoje
        despesas_hoje_qs = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='SAIDA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento=hoje
        )
        vencendo_hoje_qtd = despesas_hoje_qs.count()
        vencendo_hoje_valor = despesas_hoje_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        # Contas a Pagar nos Próximos 7 Dias
        despesas_7d_qs = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='SAIDA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__gt=hoje,
            data_vencimento__lte=limite_7_dias
        )
        proximos_7d_qtd = despesas_7d_qs.count()
        proximos_7d_valor = despesas_7d_qs.aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        card_alertas = {
            'contas_a_pagar_vencidas_qtd': contas_vencidas_qtd,
            'contas_a_pagar_vencidas_valor': contas_vencidas_valor,
            'contas_a_receber_vencidas_qtd': recebimentos_vencidos_qtd,
            'contas_a_receber_vencidas_valor': recebimentos_vencidos_valor,
            'vencendo_hoje_qtd': vencendo_hoje_qtd,
            'vencendo_hoje_valor': vencendo_hoje_valor,
            'proximos_7_dias_qtd': proximos_7d_qtd,
            'proximos_7_dias_valor': proximos_7d_valor,
        }

        return {
            'periodo': {
                'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                'data_fim': data_fim.strftime('%Y-%m-%d'),
            },
            'operacao': card_operacao,
            'faturamento': card_faturamento,
            'receita': card_receita,
            'caixa': card_caixa,
            'alertas': card_alertas,
        }

    @staticmethod
    def obter_graficos_receitas_despesas(ano=None):
        """
        Retorna a evolução mensal de Receitas Líquidas vs Despesas Pagas (12 meses do ano).
        """
        hoje = timezone.localdate()
        if not ano:
            ano = hoje.year
        else:
            try:
                ano = int(ano)
            except ValueError:
                ano = hoje.year

        nomes_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        meses_dados = []
        total_ano_receitas = Decimal('0.00')
        total_ano_despesas = Decimal('0.00')

        for mes in range(1, 13):
            # Receitas Pagas no Mês
            rec = LancamentoFinanceiro.objects.filter(
                deleted_at__isnull=True,
                tipo_lancamento='ENTRADA',
                status_pagamento='PAGO',
                data_pagamento__year=ano,
                data_pagamento__month=mes
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

            # Despesas Pagas no Mês
            desp = LancamentoFinanceiro.objects.filter(
                deleted_at__isnull=True,
                tipo_lancamento='SAIDA',
                status_pagamento='PAGO',
                data_pagamento__year=ano,
                data_pagamento__month=mes
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

            resultado = rec - desp
            total_ano_receitas += rec
            total_ano_despesas += desp

            meses_dados.append({
                'mes': mes,
                'mes_nome': nomes_meses[mes - 1],
                'receitas': rec,
                'despesas': desp,
                'resultado_liquido': resultado,
            })

        return {
            'ano': ano,
            'meses': meses_dados,
            'totais_ano': {
                'receitas_total': total_ano_receitas,
                'despesas_total': total_ano_despesas,
                'resultado_liquido_total': total_ano_receitas - total_ano_despesas,
            }
        }

    @staticmethod
    def obter_feed_atividades(limite=20):
        """
        Retorna a linha do tempo cronológica com as atividades operacionais e financeiras mais recentes.
        """
        atividades = []

        # 1. Orçamentos recentes
        orcamentos = Orcamento.objects.filter(deleted_at__isnull=True).select_related('cliente').order_by('-created_at')[:limite]
        for orc in orcamentos:
            cliente_nome = orc.cliente.nome_razao if orc.cliente else "CLIENTE NÃO IDENTIFICADO"
            atividades.append({
                'tipo': 'ORCAMENTO',
                'identificador': f"#{orc.id}",
                'titulo': f"Orçamento #{orc.id} - {orc.status_operacional}",
                'descricao': f"Cliente: {cliente_nome} | Valor: R$ {orc.valor_bruto}",
                'status': orc.status_operacional,
                'timestamp': orc.created_at,
            })

        # 2. Faturas recentes
        faturas = Fatura.objects.filter(deleted_at__isnull=True).select_related('cliente').order_by('-created_at')[:limite]
        for fat in faturas:
            cliente_nome = fat.cliente.nome_razao if fat.cliente else "CLIENTE NÃO IDENTIFICADO"
            atividades.append({
                'tipo': 'FATURA',
                'identificador': f"#{fat.id}",
                'titulo': f"Fatura #{fat.id} - {fat.status}",
                'descricao': f"Cliente: {cliente_nome} | Total: R$ {fat.valor_total_faturado}",
                'status': fat.status,
                'timestamp': fat.created_at,
            })

        # 3. Lançamentos Financeiros Pagos recentes
        lancamentos = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            status_pagamento='PAGO'
        ).select_related('categoria', 'conta').order_by('-data_pagamento')[:limite]
        for lanc in lancamentos:
            ts = lanc.data_pagamento or lanc.created_at
            tipo_label = "Recebimento" if lanc.tipo_lancamento == 'ENTRADA' else "Pagamento"
            atividades.append({
                'tipo': 'FINANCEIRO',
                'identificador': f"#{lanc.id}",
                'titulo': f"{tipo_label} Liquidado - R$ {lanc.valor}",
                'descricao': f"{lanc.descricao or 'Sem descrição'} ({lanc.categoria.nome if lanc.categoria else 'Geral'})",
                'status': lanc.tipo_lancamento,
                'timestamp': ts,
            })

        # 4. Estornos recentes
        estornos = LogEstorno.objects.select_related('usuario', 'lancamento').order_by('-data_estorno')[:limite]
        for est in estornos:
            atividades.append({
                'tipo': 'ESTORNO',
                'identificador': f"#{est.id}",
                'titulo': f"Estorno de Lançamento #{est.lancamento_id}",
                'descricao': f"Motivo: {est.justificativa}",
                'status': 'ESTORNADO',
                'timestamp': est.data_estorno,
            })

        # Ordena unificado por timestamp decrescente
        atividades.sort(key=lambda x: x['timestamp'] if x['timestamp'] else timezone.now(), reverse=True)
        return atividades[:limite]


class InadimplenciaService:
    """Serviço de análise de inadimplência e cobrança preventiva."""

    @staticmethod
    def gerar_relatorio():
        """
        Lista e totaliza faturas e títulos a receber vencidos e não quitados,
        calculando dias de atraso e agrupando por cliente.
        """
        hoje = timezone.localdate()

        # Busca lançamentos a receber vencidos
        lancamentos_vencidos = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            tipo_lancamento='ENTRADA',
            status_pagamento__in=['A_VENCER', 'VENCIDO'],
            data_vencimento__lt=hoje
        ).select_related('fatura', 'fatura__cliente')

        itens = []
        clientes_unicos = set()
        total_inadimplente = Decimal('0.00')
        soma_dias_atraso = 0

        for lanc in lancamentos_vencidos:
            dias = (hoje - lanc.data_vencimento).days
            soma_dias_atraso += dias
            total_inadimplente += lanc.valor

            cliente = lanc.fatura.cliente if (lanc.fatura and lanc.fatura.cliente) else None
            cliente_id = cliente.id if cliente else None
            if cliente_id:
                clientes_unicos.add(cliente_id)

            cliente_nome = cliente.nome_razao if cliente else (lanc.descricao or "CLIENTE NÃO IDENTIFICADO")
            cliente_doc = cliente.cnpj_cpf if cliente else "-"
            cliente_tel = cliente.telefone if cliente else "-"
            status_fat = lanc.fatura.status if lanc.fatura else "AVULSO"

            itens.append({
                'lancamento_id': lanc.id,
                'fatura_id': lanc.fatura_id,
                'cliente_id': cliente_id,
                'cliente_nome': cliente_nome,
                'cliente_documento': cliente_doc,
                'cliente_telefone': cliente_tel,
                'valor_original': lanc.valor,
                'valor_pendente': lanc.valor,
                'data_vencimento': lanc.data_vencimento.strftime('%d/%m/%Y'),
                'dias_atraso': dias,
                'status_fatura': status_fat,
            })

        # Ordena do maior atraso para o menor
        itens.sort(key=lambda x: x['dias_atraso'], reverse=True)

        total_titulos = len(itens)
        media_dias = int(soma_dias_atraso / total_titulos) if total_titulos > 0 else 0

        return {
            'posicao_em': hoje.strftime('%d/%m/%Y'),
            'total_clientes_inadimplentes': len(clientes_unicos),
            'total_titulos_atraso': total_titulos,
            'valor_total_inadimplente': total_inadimplente,
            'media_dias_atraso': media_dias,
            'itens': itens,
        }


class DossieClienteService:
    """Serviço para consolidação do Dossiê Histórico e Comercial do Cliente."""

    @staticmethod
    def gerar_dossie(cliente_id):
        """
        Retorna a visão analítica 360 graus do cliente com segregação de produtos e serviços.
        """
        cliente = ClienteFornecedor.objects.filter(id=cliente_id, deleted_at__isnull=True).first()
        if not cliente:
            return None

        # 1. Orçamentos do Cliente
        orcamentos_qs = Orcamento.objects.filter(cliente=cliente, deleted_at__isnull=True).order_by('-data_geracao')
        total_orcamentos = orcamentos_qs.count()

        orcamentos_list = []
        for orc in orcamentos_qs:
            orcamentos_list.append({
                'id': orc.id,
                'numero': orc.id,
                'data_geracao': orc.data_geracao.strftime('%d/%m/%Y'),
                'status_operacional': orc.status_operacional,
                'status_financeiro': orc.status_financeiro,
                'valor_bruto': orc.valor_bruto,
                'valor_final': orc.valor_bruto - orc.valor_desconto_aplicado,
            })

        # 2. Faturamento e Pagamentos
        faturas_qs = Fatura.objects.filter(cliente=cliente, deleted_at__isnull=True).order_by('-data_emissao')
        total_faturado = faturas_qs.filter(
            status__in=['FATURADA', 'PAGA']
        ).aggregate(total=Sum('valor_total_faturado'))['total'] or Decimal('0.00')

        # Baixas reais pagas
        total_pago = LancamentoFinanceiro.objects.filter(
            fatura__cliente=cliente,
            tipo_lancamento='ENTRADA',
            status_pagamento='PAGO',
            deleted_at__isnull=True
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        total_aberto = total_faturado - total_pago if total_faturado > total_pago else Decimal('0.00')

        # 3. Índice de Pontualidade
        lancamentos_pagos = LancamentoFinanceiro.objects.filter(
            fatura__cliente=cliente,
            tipo_lancamento='ENTRADA',
            status_pagamento='PAGO',
            deleted_at__isnull=True
        )
        total_pagos_count = lancamentos_pagos.count()
        pontuais_count = 0
        for l in lancamentos_pagos:
            if l.data_pagamento and l.data_pagamento.date() <= l.data_vencimento:
                pontuais_count += 1
        indice_pontualidade = 100
        if total_pagos_count > 0:
            indice_pontualidade = int((pontuais_count / total_pagos_count) * 100)

        # 4. Segregação de Vendas: Produtos (Materiais) vs Serviços (Reformas)
        itens_orcamento = OrcamentoItem.objects.filter(
            orcamento__cliente=cliente,
            orcamento__deleted_at__isnull=True
        )

        valor_produtos = Decimal('0.00')
        qtd_produtos = Decimal('0.00')
        valor_servicos = Decimal('0.00')
        qtd_servicos = Decimal('0.00')

        for item in itens_orcamento:
            val = item.valor_venda_snapshot * item.quantidade
            if item.produto_id:
                # É um produto composto/serviço da oficina
                valor_servicos += val
                qtd_servicos += item.quantidade
            elif item.item_id:
                # É venda direta de insumo/peça
                valor_produtos += val
                qtd_produtos += item.quantidade
            else:
                # Descrição livre -> conta como serviço avulso
                valor_servicos += val
                qtd_servicos += item.quantidade

        total_consumo = valor_produtos + valor_servicos
        perc_prod = 0
        perc_serv = 0
        if total_consumo > 0:
            perc_prod = int((valor_produtos / total_consumo) * 100)
            perc_serv = 100 - perc_prod

        # 5. Equipamentos vinculados
        vinculos = ClienteEquipamento.objects.filter(cliente=cliente).select_related('equipamento')
        equipamentos_list = []
        for v in vinculos:
            if v.equipamento:
                equipamentos_list.append({
                    'id': v.equipamento.id,
                    'identificacao': v.equipamento.identificacao,
                    'placa': v.equipamento.placa,
                    'descricao': v.equipamento.descricao,
                    'is_ativo': v.is_ativo,
                    'data_vinculo': v.data_vinculo.strftime('%d/%m/%Y') if v.data_vinculo else '-',
                })

        return {
            'cliente': {
                'id': cliente.id,
                'nome_razao': cliente.nome_razao,
                'nome_fantasia': cliente.nome_fantasia,
                'cnpj_cpf': cliente.cnpj_cpf,
                'tipo_pessoa': cliente.tipo_pessoa,
                'telefone': cliente.telefone,
                'email': cliente.email,
                'logradouro': cliente.logradouro,
                'numero': cliente.numero,
                'bairro': cliente.bairro,
                'cidade': cliente.cidade,
                'uf': cliente.uf,
            },
            'total_orcamentos': total_orcamentos,
            'total_faturado': total_faturado,
            'total_pago': total_pago,
            'total_aberto': total_aberto,
            'indice_pontualidade': indice_pontualidade,
            'segregacao_vendas': {
                'produtos': {
                    'quantidade': qtd_produtos,
                    'valor_total': valor_produtos,
                    'percentual': perc_prod,
                },
                'servicos': {
                    'quantidade': qtd_servicos,
                    'valor_total': valor_servicos,
                    'percentual': perc_serv,
                }
            },
            'orcamentos': orcamentos_list,
            'equipamentos': equipamentos_list,
        }


class CurvaABCService:
    """Serviço de cálculo de Curva ABC para Clientes e Consumo de Itens (80/15/5%)."""

    @staticmethod
    def calcular_curva_abc_clientes(data_inicio=None, data_fim=None):
        """
        Ranqueia clientes por volume de faturamento e os classifica em classes A (80%), B (15%) e C (5%).
        """
        data_inicio, data_fim = normalizar_datas(data_inicio, data_fim)

        # Faturamento de Faturas
        faturas = Fatura.objects.filter(
            deleted_at__isnull=True,
            status__in=['FATURADA', 'PAGA'],
            data_emissao__range=(data_inicio, data_fim)
        ).values('cliente_id', 'cliente__nome_razao', 'cliente__cnpj_cpf').annotate(
            total_faturado=Sum('valor_total_faturado'),
            qtd_faturas=Count('id')
        ).order_by('-total_faturado')

        faturamento_total_periodo = sum(item['total_faturado'] for item in faturas) or Decimal('0.00')

        itens = []
        acumulado = Decimal('0.00')
        qtd_a = 0
        qtd_b = 0
        qtd_c = 0

        for pos, item in enumerate(faturas, start=1):
            fat = item['total_faturado']
            qtd_fat = item['qtd_faturas']
            part = Decimal('0.00')
            if faturamento_total_periodo > 0:
                part = (fat / faturamento_total_periodo * Decimal('100.00')).quantize(Decimal('0.01'))

            acumulado += part

            # Classificação ABC
            if acumulado <= Decimal('80.00') or (pos == 1 and acumulado > Decimal('80.00')):
                classe = 'A'
                qtd_a += 1
            elif acumulado <= Decimal('95.00') or (qtd_a > 0 and qtd_b == 0 and acumulado > Decimal('95.00')):
                classe = 'B'
                qtd_b += 1
            else:
                classe = 'C'
                qtd_c += 1

            ticket_medio = (fat / Decimal(qtd_fat)).quantize(Decimal('0.01')) if qtd_fat > 0 else Decimal('0.00')

            itens.append({
                'posicao': pos,
                'cliente_id': item['cliente_id'],
                'cliente_nome': item['cliente__nome_razao'],
                'cliente_documento': item['cliente__cnpj_cpf'],
                'faturamento_total': fat,
                'quantidade_faturas': qtd_fat,
                'ticket_medio': ticket_medio,
                'percentual_participacao': part,
                'percentual_acumulado': min(acumulado, Decimal('100.00')),
                'classe_abc': classe,
            })

        return {
            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
            'data_fim': data_fim.strftime('%d/%m/%Y'),
            'faturamento_total_periodo': faturamento_total_periodo,
            'total_clientes_ativos': len(itens),
            'qtd_classe_a': qtd_a,
            'qtd_classe_b': qtd_b,
            'qtd_classe_c': qtd_c,
            'itens': itens,
        }

    @staticmethod
    def calcular_curva_abc_itens(data_inicio=None, data_fim=None):
        """
        Ranqueia o consumo de insumos e matérias-primas por custo total e classifica em A/B/C.
        """
        data_inicio, data_fim = normalizar_datas(data_inicio, data_fim)

        # Consumo de itens via Orçamentos no período
        orc_itens = OrcamentoItem.objects.filter(
            orcamento__deleted_at__isnull=True,
            orcamento__data_geracao__range=(data_inicio, data_fim),
            orcamento__status_operacional__in=['APROVADO', 'EM_EXECUCAO', 'CONCLUIDO'],
            item__isnull=False
        ).values(
            'item_id', 'item__nome', 'item__unidade_compra__sigla', 'item__tipo_uso'
        ).annotate(
            qtd_consumida=Sum('quantidade'),
            custo_total=Sum(F('custo_snapshot') * F('quantidade'))
        ).order_by('-custo_total')

        custo_total_periodo = sum(item['custo_total'] for item in orc_itens) or Decimal('0.00')

        itens = []
        acumulado = Decimal('0.00')
        qtd_a = 0
        qtd_b = 0
        qtd_c = 0

        for pos, item in enumerate(orc_itens, start=1):
            custo = item['custo_total']
            part = Decimal('0.00')
            if custo_total_periodo > 0:
                part = (custo / custo_total_periodo * Decimal('100.00')).quantize(Decimal('0.01'))

            acumulado += part

            if acumulado <= Decimal('80.00') or (pos == 1 and acumulado > Decimal('80.00')):
                classe = 'A'
                qtd_a += 1
            elif acumulado <= Decimal('95.00') or (qtd_a > 0 and qtd_b == 0 and acumulado > Decimal('95.00')):
                classe = 'B'
                qtd_b += 1
            else:
                classe = 'C'
                qtd_c += 1

            itens.append({
                'posicao': pos,
                'item_id': item['item_id'],
                'item_nome': item['item__nome'],
                'uom_sigla': item['item__unidade_compra__sigla'] or 'UN',
                'tipo_uso': item['item__tipo_uso'],
                'quantidade_consumida': item['qtd_consumida'],
                'custo_total': custo,
                'percentual_participacao': part,
                'percentual_acumulado': min(acumulado, Decimal('100.00')),
                'classe_abc': classe,
            })

        return {
            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
            'data_fim': data_fim.strftime('%d/%m/%Y'),
            'custo_total_periodo': custo_total_periodo,
            'total_itens_consumidos': len(itens),
            'qtd_classe_a': qtd_a,
            'qtd_classe_b': qtd_b,
            'qtd_classe_c': qtd_c,
            'itens': itens,
        }


class DREService:
    """Serviço de apuração do Demonstrativo de Resultado do Exercício (DRE Simplificado)."""

    @staticmethod
    def gerar_dre_simplificado(data_inicio=None, data_fim=None, regime='competencia'):
        """
        Monta a demonstração de resultado com receitas, deduções, custos variáveis e despesas operacionais.
        """
        data_inicio, data_fim = normalizar_datas(data_inicio, data_fim)
        regime = str(regime).lower()

        if regime == 'caixa':
            # Regime de Caixa: baseado em baixas de data_pagamento com status PAGO
            receita_bruta_total = LancamentoFinanceiro.objects.filter(
                deleted_at__isnull=True,
                tipo_lancamento='ENTRADA',
                status_pagamento='PAGO',
                data_pagamento__date__range=(data_inicio, data_fim)
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

            despesas_qs = LancamentoFinanceiro.objects.filter(
                deleted_at__isnull=True,
                tipo_lancamento='SAIDA',
                status_pagamento='PAGO',
                data_pagamento__date__range=(data_inicio, data_fim)
            )
        else:
            # Regime de Competência: baseado em Faturas emitidas e Lançamentos por data_vencimento
            receita_bruta_total = Fatura.objects.filter(
                deleted_at__isnull=True,
                status__in=['FATURADA', 'PAGA'],
                data_emissao__range=(data_inicio, data_fim)
            ).aggregate(total=Sum('valor_bruto'))['total'] or Decimal('0.00')

            # Se não houver faturas, fallback para lançamentos a receber no período
            if receita_bruta_total == Decimal('0.00'):
                receita_bruta_total = LancamentoFinanceiro.objects.filter(
                    deleted_at__isnull=True,
                    tipo_lancamento='ENTRADA',
                    status_pagamento__in=['A_VENCER', 'VENCIDO', 'PAGO'],
                    data_vencimento__range=(data_inicio, data_fim)
                ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

            despesas_qs = LancamentoFinanceiro.objects.filter(
                deleted_at__isnull=True,
                tipo_lancamento='SAIDA',
                status_pagamento__in=['A_VENCER', 'VENCIDO', 'PAGO'],
                data_vencimento__range=(data_inicio, data_fim)
            )

        # Deduções da Receita: Descontos comerciais e taxas de maquininhas
        descontos_concedidos = Fatura.objects.filter(
            deleted_at__isnull=True,
            status__in=['FATURADA', 'PAGA'],
            data_emissao__range=(data_inicio, data_fim)
        ).aggregate(total=Sum('desconto_global'))['total'] or Decimal('0.00')

        taxas_maquininhas = despesas_qs.filter(
            Q(categoria__nome__icontains='TAXA') | Q(categoria__nome__icontains='MAQUININHA') | Q(categoria__nome__icontains='TARIFA')
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')

        deducoes_totais = descontos_concedidos + taxas_maquininhas
        receita_liquida = receita_bruta_total - deducoes_totais

        # Custos Operacionais / Insumos
        custos_insumos = OrcamentoItem.objects.filter(
            orcamento__deleted_at__isnull=True,
            orcamento__data_geracao__range=(data_inicio, data_fim),
            orcamento__status_operacional__in=['APROVADO', 'EM_EXECUCAO', 'CONCLUIDO']
        ).aggregate(
            total=Sum(F('custo_snapshot') * F('quantidade'))
        )['total'] or Decimal('0.00')

        margem_contribuicao = receita_liquida - custos_insumos

        # Despesas Operacionais Agrupadas por Categoria (excluindo taxas de maquininha já deduzidas)
        despesas_operacionais_qs = despesas_qs.exclude(
            Q(categoria__nome__icontains='TAXA') | Q(categoria__nome__icontains='MAQUININHA') | Q(categoria__nome__icontains='TARIFA')
        ).values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')

        total_despesas_operacionais = sum(item['total'] for item in despesas_operacionais_qs) or Decimal('0.00')

        resultado_liquido = margem_contribuicao - total_despesas_operacionais

        def calc_perc(valor):
            if receita_bruta_total > 0:
                return (valor / receita_bruta_total * Decimal('100.00')).quantize(Decimal('0.01'))
            return Decimal('0.00')

        linhas_dre = [
            {'descricao': '(+) 1. RECEITA BRUTA OPERACIONAL', 'valor': receita_bruta_total, 'percentual': Decimal('100.00'), 'is_destaque': True, 'is_total': False},
            {'descricao': '(-) 2. DEDUCOES DA RECEITA BRUTA', 'valor': deducoes_totais, 'percentual': calc_perc(deducoes_totais), 'is_destaque': False, 'is_total': False},
            {'descricao': '     - DESCONTOS COMERCIAIS CONCEDIDOS', 'valor': descontos_concedidos, 'percentual': calc_perc(descontos_concedidos), 'is_destaque': False, 'is_total': False},
            {'descricao': '     - TARIFAS BANCARIAS E TAXAS DE MAQUININHA', 'valor': taxas_maquininhas, 'percentual': calc_perc(taxas_maquininhas), 'is_destaque': False, 'is_total': False},
            {'descricao': '(=) 3. RECEITA OPERACIONAL LIQUIDA', 'valor': receita_liquida, 'percentual': calc_perc(receita_liquida), 'is_destaque': True, 'is_total': False},
            {'descricao': '(-) 4. CUSTOS OPERACIONAIS (MATERIA-PRIMA E INSUMOS)', 'valor': custos_insumos, 'percentual': calc_perc(custos_insumos), 'is_destaque': False, 'is_total': False},
            {'descricao': '(=) 5. MARGEM DE CONTRIBUICAO BRUTA', 'valor': margem_contribuicao, 'percentual': calc_perc(margem_contribuicao), 'is_destaque': True, 'is_total': False},
            {'descricao': '(-) 6. DESPESAS OPERACIONAIS E ADMINISTRATIVAS', 'valor': total_despesas_operacionais, 'percentual': calc_perc(total_despesas_operacionais), 'is_destaque': False, 'is_total': False},
        ]

        for item in despesas_operacionais_qs:
            nome_cat = sanitizar_texto_maiusculo(item['categoria__nome'] or 'DESPESAS GERAIS')
            linhas_dre.append({
                'descricao': f'     - {nome_cat}',
                'valor': item['total'],
                'percentual': calc_perc(item['total']),
                'is_destaque': False,
                'is_total': False,
            })

        linhas_dre.append({
            'descricao': '(=) 7. RESULTADO OPERACIONAL LIQUIDO DO EXERCICIO',
            'valor': resultado_liquido,
            'percentual': calc_perc(resultado_liquido),
            'is_destaque': True,
            'is_total': True,
        })

        return {
            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
            'data_fim': data_fim.strftime('%d/%m/%Y'),
            'regime': regime.upper(),
            'receita_bruta': receita_bruta_total,
            'receita_liquida': receita_liquida,
            'custos_insumos': custos_insumos,
            'margem_contribuicao': margem_contribuicao,
            'total_despesas_operacionais': total_despesas_operacionais,
            'resultado_liquido': resultado_liquido,
            'margem_liquida_percentual': calc_perc(resultado_liquido),
            'linhas': linhas_dre,
        }


class DivergenciasConciliacaoService:
    """Serviço de auditoria e cruzamento de divergências de conciliação bancária."""

    @staticmethod
    def gerar_relatorio(conta_id=None, data_inicio=None, data_fim=None):
        """
        Retorna divergências em duas abas:
        - Aba 1: Sobras do Extrato (Transações bancárias sem lançamento ERP)
        - Aba 2: Sobras do ERP (Lançamentos com status PAGO não conciliados)
        """
        data_inicio, data_fim = normalizar_datas(data_inicio, data_fim)

        conta_nome = "TODAS AS CONTAS"
        erp_qs = LancamentoFinanceiro.objects.filter(
            deleted_at__isnull=True,
            status_pagamento='PAGO',
            is_conciliado=False,
            data_pagamento__date__range=(data_inicio, data_fim)
        ).select_related('conta', 'categoria', 'meio_pagamento')

        if conta_id:
            conta = ContaBancaria.objects.filter(id=conta_id).first()
            if conta:
                conta_nome = conta.nome
                erp_qs = erp_qs.filter(conta_id=conta_id)

        sobras_erp = []
        for lanc in erp_qs:
            sobras_erp.append({
                'id': lanc.id,
                'data_pagamento': lanc.data_pagamento.strftime('%d/%m/%Y %H:%M') if lanc.data_pagamento else '-',
                'descricao': lanc.descricao or 'SEM DESCRIÇÃO',
                'categoria': lanc.categoria.nome if lanc.categoria else 'GERAL',
                'meio_pagamento': lanc.meio_pagamento.nome if lanc.meio_pagamento else '-',
                'tipo_lancamento': lanc.tipo_lancamento,
                'valor': lanc.valor,
                'conta_nome': lanc.conta.nome if lanc.conta else '-',
            })

        # Sobras de Extrato (Em produção, lidas da tabela/sessão de extratos não conciliados)
        sobras_extrato = []

        return {
            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
            'data_fim': data_fim.strftime('%d/%m/%Y'),
            'conta_id': conta_id,
            'conta_nome': conta_nome,
            'total_sobras_erp': len(sobras_erp),
            'total_sobras_extrato': len(sobras_extrato),
            'sobras_erp': sobras_erp,
            'sobras_extrato': sobras_extrato,
        }
