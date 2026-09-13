"""
Testes automatizados para o Módulo Financeiro e Tesouraria.
Cobre Cadastros Estruturais (Fase 4), Lançamentos Financeiros, Modal Universal de Liquidação
com Taxa de Maquininha e ISS Retido, Estorno Auditado, Cheque Especial, Transferências Inter-Contas
e Sub-módulo de Cartões Corporativos com Rollover (Fase 10).
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario
from apps.financeiro.models import (
    CategoriaFinanceira,
    ContaBancaria,
    MeioPagamento,
    RegraPagamento,
    CartaoCredito,
    FaturaCartao,
    LancamentoFinanceiro,
    LogEstorno
)


class CadastrosEstruturaisFinanceiroTestCase(TestCase):
    """Bateria de testes para CategoriaFinanceira, ContaBancaria, MeioPagamento e RegraPagamento (Fase 4)."""

    def setUp(self):
        self.client = APIClient()

        self.admin = Usuario.objects.create_user(
            email="admin.fin@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem.fin@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        self.operador_com_permissao = Usuario.objects.create_user(
            email="operador.fin@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_com_permissao.permissoes.cadastros_financeiros = True
        self.operador_com_permissao.permissoes.save()

    def test_categoria_unauthenticated_and_forbidden(self):
        response = self.client.get('/api/categorias-financeiras/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/categorias-financeiras/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_categoria_crud_sanitization_and_hierarchy(self):
        self.client.force_authenticate(user=self.operador_com_permissao)

        payload_pai = {
            "nome": "Despesas Operacionais e Produção",
            "tipo": "DESPESA"
        }
        response_pai = self.client.post('/api/categorias-financeiras/', payload_pai, format='json')
        self.assertEqual(response_pai.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_pai.data['nome'], "DESPESAS OPERACIONAIS E PRODUCAO")
        pai_id = response_pai.data['id']

        payload_filha = {
            "nome": "Gás de Proteção e Consumíveis de Solda",
            "tipo": "DESPESA",
            "categoria_pai": pai_id
        }
        response_filha = self.client.post('/api/categorias-financeiras/', payload_filha, format='json')
        self.assertEqual(response_filha.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_filha.data['nome'], "GAS DE PROTECAO E CONSUMIVEIS DE SOLDA")
        self.assertEqual(response_filha.data['categoria_pai'], pai_id)
        filha_id = response_filha.data['id']

        response_del_pai = self.client.delete(f'/api/categorias-financeiras/{pai_id}/')
        self.assertEqual(response_del_pai.status_code, status.HTTP_400_BAD_REQUEST)

        response_del_filha = self.client.delete(f'/api/categorias-financeiras/{filha_id}/')
        self.assertEqual(response_del_filha.status_code, status.HTTP_204_NO_CONTENT)

        response_del_pai_ok = self.client.delete(f'/api/categorias-financeiras/{pai_id}/')
        self.assertEqual(response_del_pai_ok.status_code, status.HTTP_204_NO_CONTENT)

    def test_conta_bancaria_crud_and_validations(self):
        self.client.force_authenticate(user=self.operador_com_permissao)

        payload = {
            "nome": "Banco Itaú - Conta Corrente Principal",
            "saldo": "15000.50",
            "limite_credito": "10000.00"
        }
        response = self.client.post('/api/contas-bancarias/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], "BANCO ITAU - CONTA CORRENTE PRINCIPAL")
        self.assertEqual(response.data['saldo'], "15000.50")
        self.assertEqual(response.data['limite_credito'], "10000.00")
        conta_id = response.data['id']

        response_neg = self.client.patch(
            f'/api/contas-bancarias/{conta_id}/',
            {"limite_credito": "-500.00"},
            format='json'
        )
        self.assertEqual(response_neg.status_code, status.HTTP_400_BAD_REQUEST)


class TesourariaLancamentosTestCase(TestCase):
    """Bateria de testes para Lançamentos Financeiros, Liquidações, Estornos e Cheque Especial (Fase 10)."""

    def setUp(self):
        self.client = APIClient()

        self.admin = Usuario.objects.create_user(
            email="admin.tesouraria@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem.tes@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        self.operador_com_permissao = Usuario.objects.create_user(
            email="operador.tes@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_com_permissao.permissoes.acesso_tesouraria = True
        self.operador_com_permissao.permissoes.save()

        # Estruturas auxiliares
        self.categoria_receita = CategoriaFinanceira.objects.create(
            nome="RECEITA DE SERVICOS DE SOLDA",
            tipo="RECEITA"
        )
        self.categoria_despesa = CategoriaFinanceira.objects.create(
            nome="DESPESAS DE MANUTENCAO",
            tipo="DESPESA"
        )
        self.conta_principal = ContaBancaria.objects.create(
            nome="BANCO DO BRASIL - CONTA EMPRESA",
            saldo=Decimal("5000.00"),
            limite_credito=Decimal("2000.00")
        )
        self.conta_secundaria = ContaBancaria.objects.create(
            nome="CAIXA FISICO DA OFICINA",
            saldo=Decimal("500.00"),
            limite_credito=Decimal("0.00")
        )
        self.meio_maquininha = MeioPagamento.objects.create(
            nome="CARTAO DE CREDITO / MAQUININHA",
            permite_taxa_maquininha=True
        )
        self.meio_pix = MeioPagamento.objects.create(
            nome="PIX",
            permite_taxa_maquininha=False
        )

    def test_rbac_lancamento_financeiro(self):
        """Valida proteção RBAC nos endpoints de lançamentos financeiros."""
        # 1. Não autenticado
        response = self.client.get('/api/lancamentos-financeiros/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Operador sem toggle acesso_tesouraria
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/lancamentos-financeiros/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Operador com toggle acesso_tesouraria
        self.client.force_authenticate(user=self.operador_com_permissao)
        response = self.client.get('/api/lancamentos-financeiros/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_criar_titulo_competencia_vs_caixa(self):
        """Valida que títulos A Vencer não afetam o saldo bancário, enquanto títulos Pagos afetam de imediato."""
        self.client.force_authenticate(user=self.operador_com_permissao)
        saldo_inicial = self.conta_principal.saldo

        # 1. Título A Vencer (Competência)
        payload_a_vencer = {
            "categoria": self.categoria_despesa.id,
            "tipo_lancamento": "SAIDA",
            "descricao": "Compra de Eletrodos a Prazo",
            "valor": "1200.00",
            "data_vencimento": (timezone.localdate() + timedelta(days=30)).isoformat(),
            "status_pagamento": "A_VENCER"
        }
        res_vencer = self.client.post('/api/lancamentos-financeiros/', payload_a_vencer, format='json')
        self.assertEqual(res_vencer.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_vencer.data['descricao'], "COMPRA DE ELETRODOS A PRAZO")

        # Saldo bancário permanece inalterado
        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_inicial)

        # 2. Título Pago no Ato (Regime de Caixa)
        payload_pago = {
            "conta": self.conta_principal.id,
            "categoria": self.categoria_despesa.id,
            "tipo_lancamento": "SAIDA",
            "descricao": "Troca de Oleo do Compressor",
            "valor": "300.00",
            "data_vencimento": timezone.localdate().isoformat(),
            "status_pagamento": "PAGO"
        }
        res_pago = self.client.post('/api/lancamentos-financeiros/', payload_pago, format='json')
        self.assertEqual(res_pago.status_code, status.HTTP_201_CREATED)

        # Saldo bancário debitado em R$ 300,00
        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_inicial - Decimal("300.00"))

    def test_liquidacao_universal_taxa_maquininha(self):
        """Valida liquidação de receita com dedução de taxa de maquininha e impacto líquido no caixa."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        # Cria título a receber no valor de R$ 1.000,00
        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_receita,
            tipo_lancamento="ENTRADA",
            descricao="SERVICO DE SOLDA ESTRUTURAL",
            valor=Decimal("1000.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        saldo_anterior = self.conta_principal.saldo  # R$ 5.000,00

        # Liquida com Valor Bruto R$ 1.000,00 e Valor Líquido R$ 970,00 (Taxa = R$ 30,00)
        payload_liquidar = {
            "conta_id": self.conta_principal.id,
            "meio_pagamento_id": self.meio_maquininha.id,
            "valor_pago": "1000.00",
            "valor_liquido_recebido": "970.00"
        }
        response = self.client.post(f'/api/lancamentos-financeiros/{titulo.id}/liquidar/', payload_liquidar, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status_pagamento'], 'PAGO')

        # Verifica saldo na conta: deve aumentar exatamente R$ 970,00
        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_anterior + Decimal("970.00"))

        # Verifica geração automática da despesa de taxa de maquininha
        taxa_lanc = LancamentoFinanceiro.objects.filter(
            tipo_lancamento='SAIDA',
            descricao__icontains=f"REF. TITULO #{titulo.id}",
            status_pagamento='PAGO'
        ).first()
        self.assertIsNotNone(taxa_lanc)
        self.assertEqual(taxa_lanc.valor, Decimal("30.00"))
        self.assertEqual(taxa_lanc.conta_id, self.conta_principal.id)

    def test_liquidacao_universal_iss_retido(self):
        """Valida liquidação de receita com dedução de ISS retido na fonte."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_receita,
            tipo_lancamento="ENTRADA",
            descricao="CONTRATO INDUSTRIAL USINAGEM",
            valor=Decimal("2000.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        saldo_anterior = self.conta_principal.saldo

        # Liquida R$ 2.000,00 com R$ 100,00 de ISS retido (Líquido = R$ 1.900,00)
        payload = {
            "conta_id": self.conta_principal.id,
            "meio_pagamento_id": self.meio_pix.id,
            "valor_pago": "2000.00",
            "valor_iss_retido": "100.00"
        }
        response = self.client.post(f'/api/lancamentos-financeiros/{titulo.id}/liquidar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_anterior + Decimal("1900.00"))

        # Verifica geração da despesa de ISS retido
        iss_lanc = LancamentoFinanceiro.objects.filter(
            tipo_lancamento='SAIDA',
            descricao__icontains=f"RETENCAO DE ISS NA FONTE - REF. TITULO #{titulo.id}",
            status_pagamento='PAGO'
        ).first()
        self.assertIsNotNone(iss_lanc)
        self.assertEqual(iss_lanc.valor, Decimal("100.00"))

    def test_liquidacao_parcial_com_desdobramento(self):
        """Valida baixa parcial desmembrando o título em linha Paga e mantendo o saldo A Vencer."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_receita,
            tipo_lancamento="ENTRADA",
            descricao="RECUPERACAO DE CACAMBA COMPLETA",
            valor=Decimal("1500.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        # Baixa parcial de R$ 600,00
        payload = {
            "conta_id": self.conta_principal.id,
            "valor_pago": "600.00"
        }
        response = self.client.post(f'/api/lancamentos-financeiros/{titulo.id}/liquidar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status_pagamento'], 'PAGO')
        self.assertEqual(Decimal(str(response.data['valor'])), Decimal("600.00"))

        # Título original teve seu valor reduzido para R$ 900,00 e permaneceu A_VENCER
        titulo.refresh_from_db()
        self.assertEqual(titulo.valor, Decimal("900.00"))
        self.assertEqual(titulo.status_pagamento, 'A_VENCER')

    def test_bloqueio_cheque_especial_saida(self):
        """Valida que saídas que ultrapassem o saldo + limite de cheque especial são bloqueadas."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        # Conta secundária tem saldo 500.00 e limite 0.00
        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_despesa,
            tipo_lancamento="SAIDA",
            descricao="MANUTENCAO MAQUINA DE CORTE",
            valor=Decimal("800.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        payload = {
            "conta_id": self.conta_secundaria.id,
            "valor_pago": "800.00"
        }
        response = self.client.post(f'/api/lancamentos-financeiros/{titulo.id}/liquidar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cheque especial", str(response.data).lower())

        # Saldo permanece inalterado
        self.conta_secundaria.refresh_from_db()
        self.assertEqual(self.conta_secundaria.saldo, Decimal("500.00"))

    def test_cancelamento_titulo_a_vencer(self):
        """Valida cancelamento de título pendente com justificativa >= 10 caracteres."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_despesa,
            tipo_lancamento="SAIDA",
            descricao="SERVICO CANCELADO PELO FORNECEDOR",
            valor=Decimal("450.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        # 1. Justificativa curta (erro)
        res_curto = self.client.post(
            f'/api/lancamentos-financeiros/{titulo.id}/cancelar/',
            {"motivo_cancelamento": "curto"},
            format='json'
        )
        self.assertEqual(res_curto.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Justificativa válida
        res_ok = self.client.post(
            f'/api/lancamentos-financeiros/{titulo.id}/cancelar/',
            {"motivo_cancelamento": "FORNECEDOR NAO ENTREGOU O SERVICO CONTRATADO"},
            format='json'
        )
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(res_ok.data['status_pagamento'], 'CANCELADO')

    def test_estorno_titulo_pago_com_anulacao_taxas_e_log(self):
        """Valida estorno de título pago, reversão do saldo bancário, cancelamento de taxas e gravação perpétua em LogEstorno."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        saldo_inicial = self.conta_principal.saldo

        # 1. Cria e liquida um título com taxa de maquininha
        titulo = LancamentoFinanceiro.objects.create(
            categoria=self.categoria_receita,
            tipo_lancamento="ENTRADA",
            descricao="VENDA DE PECA SOLDADA",
            valor=Decimal("1000.00"),
            data_vencimento=timezone.localdate(),
            status_pagamento="A_VENCER"
        )

        self.client.post(
            f'/api/lancamentos-financeiros/{titulo.id}/liquidar/',
            {
                "conta_id": self.conta_principal.id,
                "meio_pagamento_id": self.meio_maquininha.id,
                "valor_pago": "1000.00",
                "valor_liquido_recebido": "970.00"
            },
            format='json'
        )

        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_inicial + Decimal("970.00"))

        # 2. Executa Estorno da baixa
        payload_estorno = {
            "justificativa": "CLIENTE DESISTIU DO PEDIDO E TEVE ESTORNO NO CARTAO"
        }
        res_estorno = self.client.post(
            f'/api/lancamentos-financeiros/{titulo.id}/estornar/',
            payload_estorno,
            format='json'
        )
        self.assertEqual(res_estorno.status_code, status.HTTP_200_OK)
        self.assertEqual(res_estorno.data['lancamento']['status_pagamento'], 'A_VENCER')

        # 3. Saldo bancário volta exatamente ao saldo inicial
        self.conta_principal.refresh_from_db()
        self.assertEqual(self.conta_principal.saldo, saldo_inicial)

        # 4. Taxa de maquininha correspondente foi cancelada
        taxa = LancamentoFinanceiro.objects.filter(
            descricao__icontains=f"REF. TITULO #{titulo.id}"
        ).first()
        self.assertIsNotNone(taxa)
        self.assertEqual(taxa.status_pagamento, 'CANCELADO')

        # 5. Log perpétuo gravado
        log = LogEstorno.objects.filter(lancamento=titulo).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.usuario_id, self.operador_com_permissao.id)
        self.assertIn("CLIENTE DESISTIU", log.justificativa)

    def test_transferencia_inter_contas_atomica(self):
        """Valida transferência entre contas bancárias com integridade matemática e neutra para DRE."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        saldo_origem_ini = self.conta_principal.saldo   # 5000.00
        saldo_destino_ini = self.conta_secundaria.saldo # 500.00

        payload = {
            "conta_origem_id": self.conta_principal.id,
            "conta_destino_id": self.conta_secundaria.id,
            "valor": "1000.00",
            "descricao": "SUPRIMENTO DE CAIXA OFICINA"
        }
        response = self.client.post('/api/lancamentos-financeiros/transferir/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tipo_lancamento'], 'TRANSFERENCIA')
        self.assertEqual(response.data['status_pagamento'], 'PAGO')

        self.conta_principal.refresh_from_db()
        self.conta_secundaria.refresh_from_db()

        self.assertEqual(self.conta_principal.saldo, saldo_origem_ini - Decimal("1000.00"))
        self.assertEqual(self.conta_secundaria.saldo, saldo_destino_ini + Decimal("1000.00"))

    def test_resumo_financeiro_endpoint(self):
        """Valida agregação de métricas no endpoint /resumo/."""
        self.client.force_authenticate(user=self.operador_com_permissao)
        response = self.client.get('/api/lancamentos-financeiros/resumo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('saldo_total_caixa', response.data)
        self.assertIn('contas_a_pagar', response.data)
        self.assertIn('contas_a_receber', response.data)


class CartoesCorporativosTestCase(TestCase):
    """Bateria de testes para Cartões de Crédito Corporativos, Faturas e Rollover (Fase 10)."""

    def setUp(self):
        self.client = APIClient()

        self.operador = Usuario.objects.create_user(
            email="operador.cartao@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador.permissoes.acesso_tesouraria = True
        self.operador.permissoes.save()

        self.conta = ContaBancaria.objects.create(
            nome="CONTA CORRENTE ITAU",
            saldo=Decimal("10000.00"),
            limite_credito=Decimal("5000.00")
        )

        self.categoria = CategoriaFinanceira.objects.create(
            nome="COMBUSTIVEL E FRETES",
            tipo="DESPESA"
        )

        self.cartao = CartaoCredito.objects.create(
            nome="CARTAO NUBANK CORPORATIVO",
            dia_vencimento=10,
            dia_fechamento_padrao=3,
            limite=Decimal("3000.00"),
            permite_limite_emergencial=False,
            conta_bancaria=self.conta
        )

    def test_despesa_cartao_em_fatura_aberta_sem_debito_bancario(self):
        """Valida que compra com cartão cai na fatura aberta sem debitar a conta bancária de imediato."""
        self.client.force_authenticate(user=self.operador)
        saldo_inicial = self.conta.saldo

        # Lança despesa de R$ 500,00 no cartão
        payload = {
            "cartao_credito": self.cartao.id,
            "categoria": self.categoria.id,
            "tipo_lancamento": "SAIDA",
            "descricao": "ABASTECIMENTO CAMINHONETE OFICINA",
            "valor": "500.00",
            "data_vencimento": timezone.localdate().isoformat(),
            "status_pagamento": "A_VENCER"
        }
        response = self.client.post('/api/lancamentos-financeiros/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Conta bancária não deve ser debitada
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, saldo_inicial)

        # Fatura aberta foi gerada/associada
        lanc = LancamentoFinanceiro.objects.get(id=response.data['id'])
        self.assertIsNotNone(lanc.fatura_cartao)
        self.assertEqual(lanc.fatura_cartao.status, 'ABERTA')

    def test_remanejar_despesa_entre_faturas_cartao(self):
        """Valida que uma despesa pode ser remanejada de uma fatura para outra competência."""
        self.client.force_authenticate(user=self.operador)

        fatura_ago = FaturaCartao.objects.create(
            cartao=self.cartao,
            mes_referencia="2026-08",
            data_fechamento_real=date(2026, 8, 3),
            status="ABERTA"
        )
        fatura_set = FaturaCartao.objects.create(
            cartao=self.cartao,
            mes_referencia="2026-09",
            data_fechamento_real=date(2026, 9, 3),
            status="ABERTA"
        )

        lanc = LancamentoFinanceiro.objects.create(
            cartao_credito=self.cartao,
            fatura_cartao=fatura_ago,
            categoria=self.categoria,
            tipo_lancamento="SAIDA",
            descricao="COMPRA NOTURNA TINTA",
            valor=Decimal("250.00"),
            data_vencimento=fatura_ago.data_fechamento_real,
            status_pagamento="A_VENCER"
        )

        # Move a compra para a fatura de Setembro
        response = self.client.post(
            f'/api/lancamentos-financeiros/{lanc.id}/alterar-fatura-cartao/',
            {"nova_fatura_cartao_id": fatura_set.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        lanc.refresh_from_db()
        self.assertEqual(lanc.fatura_cartao_id, fatura_set.id)
        self.assertEqual(lanc.data_vencimento, fatura_set.data_fechamento_real)

    def test_fechar_fatura_cartao_gerando_contas_a_pagar(self):
        """Valida que fechar fatura gera título no Contas a Pagar."""
        self.client.force_authenticate(user=self.operador)

        fatura = FaturaCartao.objects.create(
            cartao=self.cartao,
            mes_referencia="2026-08",
            data_fechamento_real=date(2026, 8, 3),
            status="ABERTA"
        )

        LancamentoFinanceiro.objects.create(
            cartao_credito=self.cartao,
            fatura_cartao=fatura,
            categoria=self.categoria,
            tipo_lancamento="SAIDA",
            descricao="GASOLINA",
            valor=Decimal("400.00"),
            data_vencimento=fatura.data_fechamento_real,
            status_pagamento="A_VENCER"
        )
        LancamentoFinanceiro.objects.create(
            cartao_credito=self.cartao,
            fatura_cartao=fatura,
            categoria=self.categoria,
            tipo_lancamento="SAIDA",
            descricao="ALMOCO EQUIPE",
            valor=Decimal("200.00"),
            data_vencimento=fatura.data_fechamento_real,
            status_pagamento="A_VENCER"
        )

        # Fecha a fatura
        response = self.client.post(f'/api/faturas-cartao/{fatura.id}/fechar/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dados']['total_fatura'], 600.00)

        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'FECHADA')

        # Título a pagar gerado
        titulo_pagar = LancamentoFinanceiro.objects.filter(
            fatura_cartao=fatura,
            descricao__startswith=f"PAGAMENTO FATURA CARTAO {self.cartao.nome}"
        ).first()
        self.assertIsNotNone(titulo_pagar)
        self.assertEqual(titulo_pagar.valor, Decimal("600.00"))
        self.assertEqual(titulo_pagar.status_pagamento, 'A_VENCER')

    def test_liquidacao_parcial_fatura_cartao_com_rollover(self):
        """Valida que pagamento parcial de fatura fechada transfere o saldo restante para o mês seguinte via Rollover."""
        self.client.force_authenticate(user=self.operador)

        fatura = FaturaCartao.objects.create(
            cartao=self.cartao,
            mes_referencia="2026-08",
            data_fechamento_real=date(2026, 8, 3),
            status="FECHADA"
        )

        LancamentoFinanceiro.objects.create(
            cartao_credito=self.cartao,
            fatura_cartao=fatura,
            categoria=self.categoria,
            tipo_lancamento="SAIDA",
            descricao="COMPRA PECAS MAQUINA",
            valor=Decimal("1000.00"),
            data_vencimento=fatura.data_fechamento_real,
            status_pagamento="A_VENCER"
        )

        saldo_bancario_ini = self.conta.saldo # 10000.00

        # Paga apenas R$ 400,00 da fatura de R$ 1.000,00 (Saldo residual R$ 600,00 para Rollover)
        payload = {
            "valor_pago": "400.00",
            "conta_id": self.conta.id
        }
        response = self.client.post(f'/api/faturas-cartao/{fatura.id}/liquidar/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['dados']['rollover_aplicado'])
        self.assertEqual(response.data['dados']['saldo_devedor_remanescente'], 600.00)

        # Saldo bancário debitado em R$ 400,00
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, saldo_bancario_ini - Decimal("400.00"))

        # Fatura de Setembro recebeu a linha de Rollover de R$ 600,00
        fatura_set = FaturaCartao.objects.filter(cartao=self.cartao, mes_referencia="2026-09").first()
        self.assertIsNotNone(fatura_set)
        rollover_lanc = LancamentoFinanceiro.objects.filter(
            fatura_cartao=fatura_set,
            descricao__icontains="SALDO ANTERIOR / ROLLOVER FATURA 2026-08"
        ).first()
        self.assertIsNotNone(rollover_lanc)
        self.assertEqual(rollover_lanc.valor, Decimal("600.00"))
        self.assertEqual(rollover_lanc.status_pagamento, 'A_VENCER')


class CategoriasGovernancaETesourariaTestCase(TestCase):
    """Bateria de testes para a Matriz de Governança de Categorias, indicação AMBOS e Lançamento no Extrato."""

    def setUp(self):
        self.client = APIClient()
        self.admin = Usuario.objects.create_user(
            email="admin.cat@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )
        self.operador_tesouraria = Usuario.objects.create_user(
            email="operador.tes@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_tesouraria.permissoes.acesso_tesouraria = True
        self.operador_tesouraria.permissoes.save()

        self.conta = ContaBancaria.objects.create(
            nome="ITAU PRINCIPAL",
            saldo=Decimal("5000.00"),
            limite_credito=Decimal("2000.00")
        )
        self.meio = MeioPagamento.objects.create(nome="PIX", ativo=True)

        self.cat_receita = CategoriaFinanceira.objects.create(
            nome="RECEITA DE SERVICOS",
            tipo="RECEITA"
        )
        self.cat_despesa = CategoriaFinanceira.objects.create(
            nome="DESPESA COM ENERGIA",
            tipo="DESPESA"
        )
        self.cat_ambos = CategoriaFinanceira.objects.create(
            nome="AJUSTE DE CAIXA",
            tipo="AMBOS"
        )

    def test_operador_tesouraria_pode_ler_categorias_mas_nao_modificar(self):
        self.client.force_authenticate(user=self.operador_tesouraria)
        # Leitura permitida
        response = self.client.get('/api/categorias-financeiras/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Mutação proibida (precisa de cadastros_financeiros ou Admin)
        response = self.client.post('/api/categorias-financeiras/', {
            "nome": "NOVA CATEGORIA TESTE",
            "tipo": "DESPESA"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_criacao_categoria_com_ambos_e_ativo(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post('/api/categorias-financeiras/', {
            "nome": "RECLASSIFICACAO DIVERSA",
            "tipo": "AMBOS",
            "ativo": True
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tipo'], 'AMBOS')
        self.assertEqual(response.data['tipo_display'], 'AMBOS (ENTRADA E SAÍDA)')
        self.assertTrue(response.data['ativo'])

    def test_filtro_dinamico_por_aplicacao(self):
        self.client.force_authenticate(user=self.admin)

        # Filtro SAIDA deve trazer DESPESA e AMBOS (não traz RECEITA)
        resp_saida = self.client.get('/api/categorias-financeiras/?aplicacao=SAIDA')
        self.assertEqual(resp_saida.status_code, status.HTTP_200_OK)
        nomes_saida = [c['nome'] for c in resp_saida.data.get('results', resp_saida.data)]
        self.assertIn("DESPESA COM ENERGIA", nomes_saida)
        self.assertIn("AJUSTE DE CAIXA", nomes_saida)
        self.assertNotIn("RECEITA DE SERVICOS", nomes_saida)

        # Filtro ENTRADA deve trazer RECEITA e AMBOS (não traz DESPESA)
        resp_entrada = self.client.get('/api/categorias-financeiras/?aplicacao=ENTRADA')
        self.assertEqual(resp_entrada.status_code, status.HTTP_200_OK)
        nomes_entrada = [c['nome'] for c in resp_entrada.data.get('results', resp_entrada.data)]
        self.assertIn("RECEITA DE SERVICOS", nomes_entrada)
        self.assertIn("AJUSTE DE CAIXA", nomes_entrada)
        self.assertNotIn("DESPESA COM ENERGIA", nomes_entrada)

    def test_bloqueio_inversao_tipo_categoria_com_lancamentos(self):
        self.client.force_authenticate(user=self.admin)

        # Cria lançamento vinculado à categoria de receita
        LancamentoFinanceiro.objects.create(
            tipo_lancamento="ENTRADA",
            descricao="RECEBIMENTO CLIENTE TESTE",
            valor=Decimal("300.00"),
            categoria=self.cat_receita,
            conta=self.conta,
            data_vencimento=timezone.localdate(),
            status_pagamento="PAGO"
        )

        # Tentar alterar cat_receita para DESPESA deve ser bloqueado
        response = self.client.patch(f'/api/categorias-financeiras/{self.cat_receita.id}/', {
            "tipo": "DESPESA"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Não é possível inverter uma categoria de RECEITA para DESPESA", str(response.data))

        # Mas expandir para AMBOS deve ser permitido
        response_ambos = self.client.patch(f'/api/categorias-financeiras/{self.cat_receita.id}/', {
            "tipo": "AMBOS"
        })
        self.assertEqual(response_ambos.status_code, status.HTTP_200_OK)
        self.assertEqual(response_ambos.data['tipo'], 'AMBOS')

    def test_bloqueio_exclusao_categoria_com_lancamentos(self):
        self.client.force_authenticate(user=self.admin)

        LancamentoFinanceiro.objects.create(
            tipo_lancamento="SAIDA",
            descricao="PAGAMENTO ENERGIA",
            valor=Decimal("150.00"),
            categoria=self.cat_despesa,
            conta=self.conta,
            data_vencimento=timezone.localdate(),
            status_pagamento="PAGO"
        )

        # Tentar deletar categoria vinculada deve retornar erro 400
        response = self.client.delete(f'/api/categorias-financeiras/{self.cat_despesa.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("possui 1 lançamento(s) financeiro(s) associado(s)", str(response.data))

        # Categoria não usada (cat_ambos) pode ser excluída via soft delete
        response_del = self.client.delete(f'/api/categorias-financeiras/{self.cat_ambos.id}/')
        self.assertEqual(response_del.status_code, status.HTTP_204_NO_CONTENT)

    def test_criacao_lancamento_via_categoria_id_e_modo_extrato(self):
        self.client.force_authenticate(user=self.operador_tesouraria)

        saldo_anterior = self.conta.saldo # 5000.00
        valor_despesa = Decimal("250.00")

        # Frontend submete com chaves terminadas em _id (categoria_id, conta_id, meio_pagamento_id)
        payload = {
            "tipo_lancamento": "SAIDA",
            "descricao": "TAXA CARTORIO TESTE",
            "valor": str(valor_despesa),
            "categoria_id": self.cat_despesa.id,
            "conta_id": self.conta.id,
            "meio_pagamento_id": self.meio.id,
            "data_vencimento": str(timezone.localdate()),
            "status_pagamento": "PAGO"
        }

        response = self.client.post('/api/lancamentos-financeiros/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['categoria'], self.cat_despesa.id)
        self.assertEqual(response.data['conta'], self.conta.id)
        self.assertEqual(response.data['status_pagamento'], 'PAGO')

        # Verifica débito imediato no saldo da conta bancária
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, saldo_anterior - valor_despesa)

    def test_busca_no_extrato_por_nome_de_categoria_e_reclassificacao(self):
        self.client.force_authenticate(user=self.operador_tesouraria)

        lanc = LancamentoFinanceiro.objects.create(
            tipo_lancamento="SAIDA",
            descricao="GASTO DIVERSO",
            valor=Decimal("120.00"),
            categoria=self.cat_despesa,
            conta=self.conta,
            data_vencimento=timezone.localdate(),
            status_pagamento="PAGO"
        )

        # Busca por nome da categoria na rota de lançamentos
        response_busca = self.client.get(f'/api/lancamentos-financeiros/?search={self.cat_despesa.nome}')
        self.assertEqual(response_busca.status_code, status.HTTP_200_OK)
        ids_encontrados = [l['id'] for l in response_busca.data.get('results', response_busca.data)]
        self.assertIn(lanc.id, ids_encontrados)

        # Reclassifica o lançamento para a categoria AMBOS
        response_patch = self.client.patch(f'/api/lancamentos-financeiros/{lanc.id}/', {
            "categoria_id": self.cat_ambos.id,
            "descricao": "GASTO RECLASSIFICADO"
        }, format='json')
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(response_patch.data['categoria'], self.cat_ambos.id)
        self.assertEqual(response_patch.data['descricao'], "GASTO RECLASSIFICADO")

