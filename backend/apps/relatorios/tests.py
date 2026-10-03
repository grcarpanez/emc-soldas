"""
Suíte completa de testes automatizados para a Central de Relatórios e Dashboard do ERP EMC Soldas.
Cobre cálculos matemáticos, agregações relacionais, filtros temporais, exportações em PDF e CSV,
controle de acesso RBAC (visao_relatorios) e Rate Limiting (heavy_reports).
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario, Permissao
from apps.cadastros.models import ClienteFornecedor, Equipamento, ClienteEquipamento
from apps.catalogo.models import DicionarioUom, Item, Produto, FichaTecnica
from apps.orcamentos.models import Orcamento, OrcamentoItem
from apps.faturamento.models import Fatura
from apps.financeiro.models import (
    ContaBancaria, CategoriaFinanceira, MeioPagamento, RegraPagamento,
    LancamentoFinanceiro, LogEstorno
)
from apps.administracao.models import ConfiguracaoGlobal


class RelatoriosBaseTestCase(TestCase):
    """Cenário base compartilhado com dados populados para testes da Central Analítica."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.hoje = timezone.localdate()

        # Configuração Global
        self.config = ConfiguracaoGlobal.get_solo()
        self.config.razao_social = "EMC SOLDAS TESTE"
        self.config.taxa_mao_de_obra_hora = Decimal('100.00')
        self.config.save()

        # Usuários e Permissões
        self.admin = Usuario.objects.create_user(
            email='admin@emcsoldas.com.br',
            password='Password123!',
            role='Admin',
            nome='Administrador Master'
        )
        self.admin.permissoes.visao_relatorios = True
        self.admin.permissoes.acesso_comercial = True
        self.admin.permissoes.acesso_tesouraria = True
        self.admin.permissoes.save()

        self.operador_com_permissao = Usuario.objects.create_user(
            email='operador.relatorios@emcsoldas.com.br',
            password='Password123!',
            role='Operador',
            nome='Operador Analista'
        )
        self.operador_com_permissao.permissoes.visao_relatorios = True
        self.operador_com_permissao.permissoes.save()

        self.operador_sem_permissao = Usuario.objects.create_user(
            email='operador.bloqueado@emcsoldas.com.br',
            password='Password123!',
            role='Operador',
            nome='Operador Bloqueado'
        )
        self.operador_sem_permissao.permissoes.visao_relatorios = False
        self.operador_sem_permissao.permissoes.save()

        # Estrutura Básica
        self.uom_un = DicionarioUom.objects.create(sigla='UN', descricao='UNIDADE')
        self.uom_kg = DicionarioUom.objects.create(sigla='KG', descricao='QUILOGRAMA')

        self.cat_receita = CategoriaFinanceira.objects.create(nome='VENDAS E SERVICOS', tipo='RECEITA')
        self.cat_despesa = CategoriaFinanceira.objects.create(nome='DESPESAS OPERACIONAIS', tipo='DESPESA')
        self.cat_taxa = CategoriaFinanceira.objects.create(nome='TAXAS E TARIFAS', tipo='DESPESA')

        self.conta = ContaBancaria.objects.create(nome='BANCO PRINCIPAL', saldo=Decimal('5000.00'), limite_credito=Decimal('1000.00'))
        self.meio_pix = MeioPagamento.objects.create(nome='PIX')
        self.meio_cartao = MeioPagamento.objects.create(nome='CARTAO DE CREDITO', permite_taxa_maquininha=True)
        self.regra_vista = RegraPagamento.objects.create(nome='A VISTA', meio_pagamento=self.meio_pix, tipo_cobranca='A_VISTA')

        # Clientes
        self.cliente_a = ClienteFornecedor.objects.create(
            nome_razao='CLIENTE GRANDE S/A',
            tipo_pessoa='PJ',
            cnpj_cpf='33000167000101',
            telefone='31999990001',
            cidade='BELO HORIZONTE',
            uf='MG'
        )
        self.cliente_b = ClienteFornecedor.objects.create(
            nome_razao='OFICINA DO ZE LTDA',
            tipo_pessoa='PJ',
            cnpj_cpf='11222333000181',
            telefone='31999990002',
            cidade='CONTAGEM',
            uf='MG'
        )

        # Itens e Produtos
        self.item_arame = Item.objects.create(
            nome='ARAME MIG 1.2MM',
            unidade_compra=self.uom_kg,
            ultimo_custo_compra=Decimal('20.00'),
            tipo_uso='INSUMO_PRODUTIVO'
        )
        self.produto_reforma = Produto.objects.create(
            nome='REFORMA DE CACAMBA',
            unidade_venda=self.uom_un,
            tempo_estimado_execucao=Decimal('2.00')
        )
        FichaTecnica.objects.create(produto=self.produto_reforma, item=self.item_arame, quantidade_utilizada=Decimal('5.0000'))

        # Orçamentos
        self.orc1 = Orcamento.objects.create(
            cliente=self.cliente_a,
            data_geracao=self.hoje,
            data_validade=self.hoje + timedelta(days=15),
            status_operacional='CONCLUIDO',
            status_financeiro='FATURADO',
            valor_bruto=Decimal('1000.00'),
            valor_desconto_aplicado=Decimal('0.00')
        )
        OrcamentoItem.objects.create(
            orcamento=self.orc1,
            produto=self.produto_reforma,
            quantidade=Decimal('1.0000'),
            custo_snapshot=Decimal('300.00'),
            valor_venda_snapshot=Decimal('1000.00')
        )

        self.orc2 = Orcamento.objects.create(
            cliente=self.cliente_b,
            data_geracao=self.hoje,
            data_validade=self.hoje + timedelta(days=15),
            status_operacional='CONCLUIDO',
            status_financeiro='FATURADO',
            valor_bruto=Decimal('500.00'),
            valor_desconto_aplicado=Decimal('50.00')
        )
        OrcamentoItem.objects.create(
            orcamento=self.orc2,
            item=self.item_arame,
            quantidade=Decimal('10.0000'),
            custo_snapshot=Decimal('20.00'),
            valor_venda_snapshot=Decimal('50.00')
        )

        # Faturas
        self.fat1 = Fatura.objects.create(
            cliente=self.cliente_a,
            data_emissao=self.hoje,
            data_fechamento=self.hoje,
            status='FATURADA',
            valor_bruto=Decimal('1000.00'),
            desconto_global=Decimal('0.00'),
            valor_total_faturado=Decimal('1000.00')
        )
        self.orc1.fatura = self.fat1
        self.orc1.save()

        self.fat2 = Fatura.objects.create(
            cliente=self.cliente_b,
            data_emissao=self.hoje,
            data_fechamento=self.hoje,
            status='PAGA',
            valor_bruto=Decimal('500.00'),
            desconto_global=Decimal('50.00'),
            valor_total_faturado=Decimal('450.00')
        )
        self.orc2.fatura = self.fat2
        self.orc2.save()

        # Lançamentos Financeiros
        # 1. Parcela em atraso (Inadimplência da Fat 1)
        self.lanc_atrasado = LancamentoFinanceiro.objects.create(
            fatura=self.fat1,
            conta=self.conta,
            categoria=self.cat_receita,
            tipo_lancamento='ENTRADA',
            descricao='FATURA 1 - PARCELA 1/1',
            valor=Decimal('1000.00'),
            data_vencimento=self.hoje - timedelta(days=10),
            status_pagamento='A_VENCER'
        )

        # 2. Recebimento quitado (Fat 2)
        self.lanc_pago = LancamentoFinanceiro.objects.create(
            fatura=self.fat2,
            conta=self.conta,
            categoria=self.cat_receita,
            tipo_lancamento='ENTRADA',
            descricao='RECEBIMENTO FATURA 2',
            valor=Decimal('450.00'),
            data_vencimento=self.hoje,
            data_pagamento=timezone.now(),
            status_pagamento='PAGO',
            is_conciliado=False
        )

        # 3. Despesa Paga
        self.lanc_despesa_paga = LancamentoFinanceiro.objects.create(
            conta=self.conta,
            categoria=self.cat_despesa,
            tipo_lancamento='SAIDA',
            descricao='ENERGIA ELETRICA OFICINA',
            valor=Decimal('200.00'),
            data_vencimento=self.hoje,
            data_pagamento=timezone.now(),
            status_pagamento='PAGO',
            is_conciliado=True
        )

        # 4. Despesa a Pagar nos próximos 3 dias
        self.lanc_despesa_futura = LancamentoFinanceiro.objects.create(
            conta=self.conta,
            categoria=self.cat_despesa,
            tipo_lancamento='SAIDA',
            descricao='INTERNET E TELEFONIA',
            valor=Decimal('150.00'),
            data_vencimento=self.hoje + timedelta(days=3),
            status_pagamento='A_VENCER'
        )


class DashboardViewsTestCase(RelatoriosBaseTestCase):
    """Testes dos endpoints do Dashboard Principal."""

    def test_dashboard_flip_cards_sucesso(self):
        """Valida agregação de dados e métricas dos 5 Flip Cards."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/dashboard/flip-cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dados = response.json()
        self.assertIn('operacao', dados)
        self.assertIn('faturamento', dados)
        self.assertIn('receita', dados)
        self.assertIn('caixa', dados)
        self.assertIn('alertas', dados)

        # Operação
        self.assertEqual(dados['operacao']['total_orcamentos'], 2)
        self.assertEqual(dados['operacao']['orcamentos_concluidos'], 2)
        self.assertEqual(Decimal(str(dados['operacao']['valor_total_orcado'])), Decimal('1500.00'))

        # Faturamento
        self.assertEqual(dados['faturamento']['total_faturas'], 2)
        self.assertEqual(dados['faturamento']['faturas_pagas'], 1)
        self.assertEqual(Decimal(str(dados['faturamento']['valor_liquido_faturado'])), Decimal('1450.00'))

        # Caixa Real Consolidado
        self.assertEqual(Decimal(str(dados['caixa']['saldo_real_consolidado'])), Decimal('5000.00'))

        # Alertas
        self.assertGreaterEqual(dados['alertas']['contas_a_receber_vencidas_qtd'], 1)
        self.assertEqual(dados['alertas']['proximos_7_dias_qtd'], 1)
        self.assertIn('cards', dados)
        self.assertEqual(dados['cards']['caixa']['saldo_bancario_real'], dados['caixa']['saldo_real_consolidado'])
        self.assertGreaterEqual(dados['cards']['alertas']['vencidas'], 1)

    def test_dashboard_flip_cards_filtro_periodo(self):
        """Valida que os filtros de período hoje, mes e ano ajustam data_inicio e data_fim."""
        self.client.force_authenticate(user=self.admin)

        for p in ['hoje', 'mes', 'ano']:
            res = self.client.get(f'/api/dashboard/flip-cards/?periodo={p}')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            d = res.json()
            self.assertIn('periodo', d)
            self.assertIn('data_inicio', d['periodo'])
            self.assertIn('data_fim', d['periodo'])

    def test_dashboard_graficos_receitas_despesas(self):
        """Valida retorno do gráfico mensal de receitas vs despesas."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(f'/api/dashboard/graficos/?ano={self.hoje.year}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dados = response.json()
        self.assertEqual(dados['ano'], self.hoje.year)
        self.assertEqual(len(dados['meses']), 12)
        self.assertIn('historico', dados)
        self.assertEqual(len(dados['historico']), 12)
        self.assertIn('mes_sigla', dados['meses'][0])
        self.assertIn('totais_ano', dados)

    def test_dashboard_feed_atividades(self):
        """Valida listagem da linha do tempo de atividades recentes."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/dashboard/feed/?limite=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dados = response.json()
        self.assertIsInstance(dados, list)
        self.assertGreaterEqual(len(dados), 2)
        self.assertIn('data_hora', dados[0])
        self.assertIn('timestamp', dados[0])


class RelatoriosEstrategicosTestCase(RelatoriosBaseTestCase):
    """Testes dos 6 Relatórios Estratégicos e Exportações."""

    def test_relatorio_inadimplencia_json_e_exportacoes(self):
        """Valida listagem analítica e exportação em PDF/CSV de inadimplência."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON em tela
        res_json = self.client.get('/api/relatorios/inadimplencia/')
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        dados = res_json.json()
        self.assertEqual(dados['total_clientes_inadimplentes'], 1)
        self.assertEqual(dados['total_titulos_atraso'], 1)
        self.assertEqual(Decimal(str(dados['valor_total_inadimplente'])), Decimal('1000.00'))
        self.assertEqual(dados['itens'][0]['dias_atraso'], 10)

        # 2. Exportação PDF
        cache.clear()
        res_pdf = self.client.get('/api/relatorios/inadimplencia/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pdf['Content-Type'], 'application/pdf')
        self.assertTrue(len(res_pdf.content) > 100)

        # 3. Exportação CSV
        cache.clear()
        res_csv = self.client.get('/api/relatorios/inadimplencia/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', res_csv['Content-Type'])
        self.assertTrue(len(res_csv.content) > 50)

    def test_dossie_cliente_json_e_exportacoes(self):
        """Valida Dossiê Completo do Cliente com segregação de produtos e serviços."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON
        res_json = self.client.get(f'/api/relatorios/dossie-cliente/{self.cliente_a.id}/')
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        dados = res_json.json()
        self.assertEqual(dados['cliente']['nome_razao'], 'CLIENTE GRANDE S/A')
        self.assertEqual(dados['total_orcamentos'], 1)
        self.assertEqual(Decimal(str(dados['total_faturado'])), Decimal('1000.00'))
        self.assertIn('segregacao_vendas', dados)

        # 2. Exportação PDF
        cache.clear()
        res_pdf = self.client.get(f'/api/relatorios/dossie-cliente/{self.cliente_a.id}/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pdf['Content-Type'], 'application/pdf')

        # 3. Exportação CSV
        cache.clear()
        res_csv = self.client.get(f'/api/relatorios/dossie-cliente/{self.cliente_a.id}/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', res_csv['Content-Type'])

    def test_curva_abc_clientes(self):
        """Valida classificação ABC de clientes (80/15/5%)."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON
        res_json = self.client.get('/api/relatorios/curva-abc-clientes/')
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        dados = res_json.json()
        self.assertEqual(dados['total_clientes_ativos'], 2)
        self.assertEqual(Decimal(str(dados['faturamento_total_periodo'])), Decimal('1450.00'))
        self.assertEqual(dados['itens'][0]['classe_abc'], 'A')

        # 2. PDF e CSV
        cache.clear()
        res_pdf = self.client.get('/api/relatorios/curva-abc-clientes/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        cache.clear()
        res_csv = self.client.get('/api/relatorios/curva-abc-clientes/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)

    def test_curva_abc_itens(self):
        """Valida Curva ABC de consumo de itens/insumos."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON
        res_json = self.client.get('/api/relatorios/curva-abc-itens/')
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        dados = res_json.json()
        self.assertGreaterEqual(dados['total_itens_consumidos'], 1)

        # 2. PDF e CSV
        cache.clear()
        res_pdf = self.client.get('/api/relatorios/curva-abc-itens/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        cache.clear()
        res_csv = self.client.get('/api/relatorios/curva-abc-itens/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)

    def test_dre_simplificado(self):
        """Valida cálculo de Receitas, Deduções, Custos e Margem Líquida no DRE."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON Regime Competência
        res_comp = self.client.get('/api/relatorios/dre/?regime=competencia')
        self.assertEqual(res_comp.status_code, status.HTTP_200_OK)
        dados_comp = res_comp.json()
        self.assertEqual(dados_comp['regime'], 'COMPETENCIA')
        self.assertGreaterEqual(Decimal(str(dados_comp['receita_bruta'])), Decimal('1500.00'))
        self.assertIn('linhas', dados_comp)

        # 2. JSON Regime Caixa
        res_caixa = self.client.get('/api/relatorios/dre/?regime=caixa')
        self.assertEqual(res_caixa.status_code, status.HTTP_200_OK)

        # 3. PDF e CSV
        cache.clear()
        res_pdf = self.client.get('/api/relatorios/dre/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        cache.clear()
        res_csv = self.client.get('/api/relatorios/dre/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)

    def test_divergencias_conciliacao(self):
        """Valida identificação de sobras do ERP sem conciliação confirmada."""
        self.client.force_authenticate(user=self.admin)

        # 1. JSON
        res_json = self.client.get('/api/relatorios/divergencias-conciliacao/')
        self.assertEqual(res_json.status_code, status.HTTP_200_OK)
        dados = res_json.json()
        self.assertEqual(dados['total_sobras_erp'], 1)  # self.lanc_pago tem is_conciliado=False
        self.assertEqual(dados['sobras_erp'][0]['descricao'], 'RECEBIMENTO FATURA 2')

        # 2. PDF e CSV
        cache.clear()
        res_pdf = self.client.get('/api/relatorios/divergencias-conciliacao/exportar-pdf/')
        self.assertEqual(res_pdf.status_code, status.HTTP_200_OK)
        cache.clear()
        res_csv = self.client.get('/api/relatorios/divergencias-conciliacao/exportar-csv/')
        self.assertEqual(res_csv.status_code, status.HTTP_200_OK)

    def test_throttling_heavy_reports_bloqueia_apos_limite(self):
        """Valida que o ScopedRateThrottle bloqueia a 6ª requisição pesada consecutiva com 429."""
        self.client.force_authenticate(user=self.admin)
        cache.clear()

        # Dispara 5 requisições permitidas (taxa: 5/minute)
        for _ in range(5):
            res = self.client.get('/api/relatorios/inadimplencia/exportar-csv/')
            self.assertEqual(res.status_code, status.HTTP_200_OK)

        # A 6ª requisição dentro do mesmo minuto deve receber 429 Too Many Requests
        res_bloqueada = self.client.get('/api/relatorios/inadimplencia/exportar-csv/')
        self.assertEqual(res_bloqueada.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class RelatoriosSegurancaRBACTestCase(RelatoriosBaseTestCase):
    """Testes de Controle de Acesso RBAC (visao_relatorios) e autenticação."""

    def test_operador_com_permissao_acessa_com_sucesso(self):
        """Operador com toggle visao_relatorios=True acessa os relatórios normalmente."""
        self.client.force_authenticate(user=self.operador_com_permissao)
        response = self.client.get('/api/dashboard/flip-cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_operador_sem_permissao_bloqueado_com_403(self):
        """Operador com toggle visao_relatorios=False recebe sumariamente 403 Forbidden."""
        self.client.force_authenticate(user=self.operador_sem_permissao)

        endpoints = [
            '/api/dashboard/flip-cards/',
            '/api/dashboard/graficos/',
            '/api/dashboard/feed/',
            '/api/relatorios/inadimplencia/',
            '/api/relatorios/inadimplencia/exportar-pdf/',
            '/api/relatorios/inadimplencia/exportar-csv/',
            f'/api/relatorios/dossie-cliente/{self.cliente_a.id}/',
            '/api/relatorios/curva-abc-clientes/',
            '/api/relatorios/curva-abc-itens/',
            '/api/relatorios/dre/',
            '/api/relatorios/divergencias-conciliacao/',
        ]

        for url in endpoints:
            cache.clear()
            res = self.client.get(url)
            self.assertEqual(
                res.status_code, status.HTTP_403_FORBIDDEN,
                f"Falha de segurança: operador sem permissão acessou {url}"
            )

    def test_usuario_anonimo_bloqueado(self):
        """Acesso não autenticado é rejeitado com 401 Unauthorized / 403 Forbidden."""
        response = self.client.get('/api/dashboard/flip-cards/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
