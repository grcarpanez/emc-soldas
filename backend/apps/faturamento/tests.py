"""
Testes automatizados completos para o Módulo de Faturamento Agregado (Fase 9).
Em conformidade com docs/FSD.md e docs/PLANO.md.
"""
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario, Permissao
from apps.cadastros.models import ClienteFornecedor, Equipamento
from apps.catalogo.models import DicionarioUom, Item, Produto, FichaTecnica
from apps.orcamentos.models import Orcamento, OrcamentoItem
from apps.financeiro.models import (
    ContaBancaria,
    MeioPagamento,
    RegraPagamento,
    CategoriaFinanceira,
    LancamentoFinanceiro
)
from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.administracao.models import ConfiguracaoGlobal


class FaturamentoAgregadoTestCase(TestCase):
    """
    Suíte de testes cobrindo todo o ciclo operacional e financeiro de faturamento:
    Conta Corrente, Pré-Fatura, Fatura Final, Parcelas, Baixas, Quitação 100%,
    Cortesia, Cancelamento em Cascata, PDF e RBAC.
    """

    def setUp(self):
        self.client = APIClient()

        # Configurações Globais da Oficina
        self.config_global = ConfiguracaoGlobal.get_solo()
        self.config_global.razao_social = "EMC SOLDAS TESTES LTDA"
        self.config_global.taxa_mao_de_obra_hora = Decimal('100.00')
        self.config_global.save()

        # 1. Usuários e Permissões
        self.admin = Usuario.objects.create(
            nome="ADMINISTRADOR MASTER",
            email="admin@emcsoldas.com.br",
            role="Admin"
        )
        self.admin.set_password("Admin@123456")
        self.admin.save()
        Permissao.objects.create(usuario=self.admin)

        self.operador_comercial = Usuario.objects.create(
            nome="OPERADOR COMERCIAL",
            email="comercial@emcsoldas.com.br",
            role="Operador"
        )
        self.operador_comercial.set_password("Operador@123456")
        self.operador_comercial.save()
        self.perm_comercial = Permissao.objects.create(
            usuario=self.operador_comercial,
            acesso_comercial=True
        )

        self.operador_sem_comercial = Usuario.objects.create(
            nome="OPERADOR SEM COMERCIAL",
            email="sem.comercial@emcsoldas.com.br",
            role="Operador"
        )
        self.operador_sem_comercial.set_password("SemComercial@123456")
        self.operador_sem_comercial.save()
        Permissao.objects.create(
            usuario=self.operador_sem_comercial,
            acesso_comercial=False
        )

        # 2. Estrutura Financeira (Meios, Regras, Categorias, Contas)
        self.meio_pix = MeioPagamento.objects.create(nome="PIX", permite_taxa_maquininha=False)
        self.meio_boleto = MeioPagamento.objects.create(nome="BOLETO BANCARIO", permite_taxa_maquininha=False)
        self.meio_cartao = MeioPagamento.objects.create(nome="CARTAO DE CREDITO", permite_taxa_maquininha=True)

        self.regra_a_vista = RegraPagamento.objects.create(
            nome="A VISTA NO PIX (5% DESC.)",
            meio_pagamento=self.meio_pix,
            tipo_cobranca="A_VISTA",
            numero_parcelas=1,
            prazo_primeira_parcela_dias=0,
            intervalo_parcelas_dias=0,
            desconto_concedido_padrao=Decimal('5.00')
        )

        self.regra_boleto_3x = RegraPagamento.objects.create(
            nome="BOLETO 30/60/90 DIAS",
            meio_pagamento=self.meio_boleto,
            tipo_cobranca="PARCELADO",
            numero_parcelas=3,
            prazo_primeira_parcela_dias=30,
            intervalo_parcelas_dias=30,
            desconto_concedido_padrao=Decimal('0.00')
        )

        self.regra_cartao_2x = RegraPagamento.objects.create(
            nome="CARTAO 2X",
            meio_pagamento=self.meio_cartao,
            tipo_cobranca="PARCELADO",
            numero_parcelas=2,
            prazo_primeira_parcela_dias=30,
            intervalo_parcelas_dias=30,
            desconto_concedido_padrao=Decimal('0.00')
        )

        self.cat_receita = CategoriaFinanceira.objects.create(
            nome="RECEITA DE SERVICOS (MAO DE OBRA)",
            tipo="RECEITA"
        )
        self.cat_taxa = CategoriaFinanceira.objects.create(
            nome="TAXAS DE CARTAO E BANCARIAS",
            tipo="DESPESA"
        )

        self.conta_bancaria = ContaBancaria.objects.create(
            nome="CONTA BANCARIA PRINCIPAL",
            saldo=Decimal('1000.00'),
            limite_credito=Decimal('500.00')
        )

        # 3. Clientes e Equipamentos
        self.cliente_a = ClienteFornecedor.objects.create(
            tipo="Cliente",
            tipo_pessoa="PJ",
            nome_razao="TRANSPORTADORA VELOZ LTDA",
            cnpj_cpf="33000167000101",
            telefone="31988887777",
            email="financeiro@veloz.com.br"
        )

        self.cliente_b = ClienteFornecedor.objects.create(
            tipo="Cliente",
            tipo_pessoa="PF",
            nome_razao="JOAO SILVA MECANICA",
            cnpj_cpf="12345678909",
            telefone="31977776666"
        )

        self.equipamento_1 = Equipamento.objects.create(
            placa="ABC1234",
            descricao="CAMINHAO VOLVO FH 540"
        )

        self.equipamento_2 = Equipamento.objects.create(
            placa="XYZ9876",
            descricao="CARRETA BASCULANTE RANDON"
        )

        # 4. Orçamentos de Teste para o Cliente A
        # Orçamento 1: Concluído / A Faturar (Bruto: 1000.00, Desconto: 100.00 -> Líquido: 900.00)
        self.orcamento_1 = Orcamento.objects.create(
            cliente=self.cliente_a,
            equipamento=self.equipamento_1,
            data_geracao=timezone.localdate(),
            data_validade=timezone.localdate() + timedelta(days=15),
            status_operacional='CONCLUIDO',
            status_financeiro='A_FATURAR',
            valor_bruto=Decimal('1000.00'),
            valor_desconto_aplicado=Decimal('100.00')
        )
        OrcamentoItem.objects.create(
            orcamento=self.orcamento_1,
            descricao_livre="SOLDA REFORÇO DE CHASSI",
            quantidade=Decimal('1.0000'),
            custo_snapshot=Decimal('300.00'),
            valor_venda_snapshot=Decimal('1000.00')
        )

        # Orçamento 2: Em Execução / A Faturar (Bruto: 600.00, Desconto: 0.00 -> Líquido: 600.00)
        self.orcamento_2 = Orcamento.objects.create(
            cliente=self.cliente_a,
            equipamento=self.equipamento_2,
            data_geracao=timezone.localdate(),
            data_validade=timezone.localdate() + timedelta(days=15),
            status_operacional='EM_EXECUCAO',
            status_financeiro='A_FATURAR',
            valor_bruto=Decimal('600.00'),
            valor_desconto_aplicado=Decimal('0.00')
        )
        OrcamentoItem.objects.create(
            orcamento=self.orcamento_2,
            descricao_livre="RECUPERAÇÃO DE PINO DE ENGATE",
            quantidade=Decimal('1.0000'),
            custo_snapshot=Decimal('150.00'),
            valor_venda_snapshot=Decimal('600.00')
        )

        # Orçamento 3: Do Cliente B (para validar isolamento de cliente)
        self.orcamento_b = Orcamento.objects.create(
            cliente=self.cliente_b,
            data_geracao=timezone.localdate(),
            data_validade=timezone.localdate() + timedelta(days=15),
            status_operacional='CONCLUIDO',
            status_financeiro='A_FATURAR',
            valor_bruto=Decimal('400.00'),
            valor_desconto_aplicado=Decimal('0.00')
        )

    def test_01_conta_corrente_listagem_orçamentos_faturaveis(self):
        """Testa listagem da Conta Corrente de clientes via endpoint."""
        self.client.force_authenticate(user=self.operador_comercial)

        # 1. Consulta geral da conta corrente
        response = self.client.get('/api/faturas/conta-corrente/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dados = response.data
        self.assertGreaterEqual(len(dados), 3)

        # 2. Consulta filtrando pelo Cliente A
        response_a = self.client.get(f'/api/faturas/conta-corrente/?cliente_id={self.cliente_a.id}')
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        ids_a = [item['id'] for item in response_a.data]
        self.assertIn(self.orcamento_1.id, ids_a)
        self.assertIn(self.orcamento_2.id, ids_a)
        self.assertNotIn(self.orcamento_b.id, ids_a)

    def test_02_criacao_pre_fatura_rascunho(self):
        """Testa a criação de uma Pré-Fatura (Rascunho) agregando orçamentos."""
        self.client.force_authenticate(user=self.operador_comercial)

        payload = {
            'cliente': self.cliente_a.id,
            'orcamento_ids': [self.orcamento_1.id, self.orcamento_2.id],
            'desconto_global': '50.00',
            'propostas_pagamento': [
                {
                    'regra_pagamento': self.regra_a_vista.id,
                    'desconto_personalizado': '5.00'
                },
                {
                    'regra_pagamento': self.regra_boleto_3x.id,
                    'desconto_personalizado': '0.00'
                }
            ]
        }

        response = self.client.post('/api/faturas/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        fatura_id = response.data['id']

        # Validações da Fatura criada
        fatura = Fatura.objects.get(id=fatura_id)
        self.assertEqual(fatura.status, 'RASCUNHO')
        self.assertIsNone(fatura.data_fechamento)
        # Valor bruto = 900.00 (orc 1) + 600.00 (orc 2) = 1500.00
        self.assertEqual(fatura.valor_bruto, Decimal('1500.00'))
        self.assertEqual(fatura.desconto_global, Decimal('50.00'))
        self.assertEqual(fatura.valor_total_faturado, Decimal('1450.00'))

        # Valida orçamentos vinculados (mantendo status A_FATURAR)
        self.orcamento_1.refresh_from_db()
        self.orcamento_2.refresh_from_db()
        self.assertEqual(self.orcamento_1.fatura_id, fatura.id)
        self.assertEqual(self.orcamento_1.status_financeiro, 'A_FATURAR')
        self.assertEqual(self.orcamento_2.fatura_id, fatura.id)
        self.assertEqual(self.orcamento_2.status_financeiro, 'A_FATURAR')

        # Regra Estrita: Não deve ter gerado nenhum lançamento no Contas a Receber
        self.assertEqual(fatura.lancamentos_financeiros.count(), 0)

        # Valida propostas sugeridas criadas
        self.assertEqual(fatura.propostas_pagamento.count(), 2)

    def test_03_bloqueio_agrupamento_orcamentos_clientes_diferentes(self):
        """Testa bloqueio ao tentar criar fatura com orçamentos de clientes diferentes."""
        self.client.force_authenticate(user=self.operador_comercial)

        payload = {
            'cliente': self.cliente_a.id,
            'orcamento_ids': [self.orcamento_1.id, self.orcamento_b.id]  # orcamento_b pertence ao cliente_b
        }

        response = self.client.post('/api/faturas/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        detalhes = response.data.get('details', response.data)
        self.assertIn('orcamentos', detalhes)

    def test_04_conversao_fatura_final_e_geracao_parcelas(self):
        """Testa conversão de Rascunho para FATURADA e geração automática de parcelas."""
        self.client.force_authenticate(user=self.operador_comercial)

        # 1. Cria Pré-Fatura
        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='RASCUNHO',
            valor_bruto=Decimal('1500.00'),
            desconto_global=Decimal('0.00'),
            valor_total_faturado=Decimal('1500.00')
        )
        self.orcamento_1.fatura = fatura
        self.orcamento_1.save()
        self.orcamento_2.fatura = fatura
        self.orcamento_2.save()

        # 2. Executa fechamento/faturamento com Regra Boleto 3x (30/60/90) e desconto final de 0.00
        payload_faturar = {
            'regra_pagamento_id': self.regra_boleto_3x.id,
            'desconto_global': '0.00',
            'numero_nfe_venda': 'NFE-12345'
        }

        response = self.client.post(f'/api/faturas/{fatura.id}/faturar/', payload_faturar, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3. Validações da Fatura
        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'FATURADA')
        self.assertEqual(fatura.data_fechamento, timezone.localdate())
        self.assertEqual(fatura.numero_nfe_venda, 'NFE-12345')
        self.assertEqual(fatura.regra_pagamento_id, self.regra_boleto_3x.id)

        # 4. Valida transição em cascata dos orçamentos
        self.orcamento_1.refresh_from_db()
        self.orcamento_2.refresh_from_db()
        self.assertEqual(self.orcamento_1.status_financeiro, 'FATURADO')
        self.assertEqual(self.orcamento_2.status_financeiro, 'FATURADO')

        # 5. Valida parcelas geradas em LancamentoFinanceiro (Contas a Receber)
        parcelas = LancamentoFinanceiro.objects.filter(fatura=fatura).order_by('data_vencimento')
        self.assertEqual(parcelas.count(), 3)

        hoje = timezone.localdate()
        for idx, p in enumerate(parcelas):
            self.assertEqual(p.tipo_lancamento, 'ENTRADA')
            self.assertEqual(p.status_pagamento, 'A_VENCER')
            self.assertEqual(p.valor, Decimal('500.00'))  # 1500 / 3 = 500.00
            self.assertEqual(p.meio_pagamento_id, self.meio_boleto.id)
            # Vencimentos calculados: 30, 60 e 90 dias
            esperado_venc = hoje + timedelta(days=30 * (idx + 1))
            self.assertEqual(p.data_vencimento, esperado_venc)

    def test_05_recebimento_parcial_e_quitacao_total_100_porcento(self):
        """Testa recebimento parcial seguido de quitação integral (100%) com transição para PAGA/PAGO."""
        self.client.force_authenticate(user=self.operador_comercial)

        # Cria fatura faturada com 2 parcelas de R$ 500,00 (Total R$ 1000,00)
        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='FATURADA',
            data_fechamento=timezone.localdate(),
            valor_bruto=Decimal('1000.00'),
            desconto_global=Decimal('0.00'),
            valor_total_faturado=Decimal('1000.00'),
            regra_pagamento=self.regra_cartao_2x
        )
        self.orcamento_1.fatura = fatura
        self.orcamento_1.status_financeiro = 'FATURADO'
        self.orcamento_1.save()

        p1 = LancamentoFinanceiro.objects.create(
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='A_VENCER',
            valor=Decimal('500.00'),
            data_vencimento=timezone.localdate() + timedelta(days=30),
            categoria=self.cat_receita
        )
        p2 = LancamentoFinanceiro.objects.create(
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='A_VENCER',
            valor=Decimal('500.00'),
            data_vencimento=timezone.localdate() + timedelta(days=60),
            categoria=self.cat_receita
        )

        saldo_inicial_conta = self.conta_bancaria.saldo

        # 1. Recebimento parcial de R$ 500,00
        payload_receber_1 = {
            'valor': '500.00',
            'conta_id': self.conta_bancaria.id,
            'meio_pagamento_id': self.meio_pix.id
        }
        res_1 = self.client.post(f'/api/faturas/{fatura.id}/receber/', payload_receber_1, format='json')
        self.assertEqual(res_1.status_code, status.HTTP_200_OK)
        self.assertFalse(res_1.data['quitada'])

        # Saldo bancário aumentou em 500.00
        self.conta_bancaria.refresh_from_db()
        self.assertEqual(self.conta_bancaria.saldo, saldo_inicial_conta + Decimal('500.00'))

        # Fatura continua FATURADA e orçamento continua FATURADO
        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'FATURADA')
        self.orcamento_1.refresh_from_db()
        self.assertEqual(self.orcamento_1.status_financeiro, 'FATURADO')

        # 2. Recebimento final de R$ 500,00 (Totalizando 1000.00)
        payload_receber_2 = {
            'valor': '500.00',
            'conta_id': self.conta_bancaria.id,
            'meio_pagamento_id': self.meio_pix.id
        }
        res_2 = self.client.post(f'/api/faturas/{fatura.id}/receber/', payload_receber_2, format='json')
        self.assertEqual(res_2.status_code, status.HTTP_200_OK)
        self.assertTrue(res_2.data['quitada'])

        # Fatura transitou para PAGA e orçamento para PAGO
        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'PAGA')
        self.orcamento_1.refresh_from_db()
        self.assertEqual(self.orcamento_1.status_financeiro, 'PAGO')

    def test_06_recebimento_com_taxa_de_maquininha(self):
        """Testa baixa com desconto de taxa de maquininha de cartão."""
        self.client.force_authenticate(user=self.operador_comercial)

        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='FATURADA',
            data_fechamento=timezone.localdate(),
            valor_bruto=Decimal('1000.00'),
            valor_total_faturado=Decimal('1000.00')
        )
        LancamentoFinanceiro.objects.create(
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='A_VENCER',
            valor=Decimal('1000.00'),
            data_vencimento=timezone.localdate(),
            categoria=self.cat_receita
        )

        saldo_inicial = self.conta_bancaria.saldo

        # Pagamento de 1000.00 bruto com 970.00 líquido (Taxa de 30.00)
        payload = {
            'valor': '1000.00',
            'valor_liquido': '970.00',
            'conta_id': self.conta_bancaria.id,
            'meio_pagamento_id': self.meio_cartao.id
        }

        response = self.client.post(f'/api/faturas/{fatura.id}/receber/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Saldo bancário deve ter aumentado em exatamente 970.00
        self.conta_bancaria.refresh_from_db()
        self.assertEqual(self.conta_bancaria.saldo, saldo_inicial + Decimal('970.00'))

        # Verifica despesa de taxa registrada
        despesa_taxa = LancamentoFinanceiro.objects.filter(
            fatura=fatura,
            tipo_lancamento='SAIDA',
            status_pagamento='PAGO'
        ).first()
        self.assertIsNotNone(despesa_taxa)
        self.assertEqual(despesa_taxa.valor, Decimal('30.00'))

    def test_07_quitacao_em_cortesia_sem_afetar_caixa_real(self):
        """Testa quitação por cortesia (100% de desconto) sem movimentação de caixa."""
        self.client.force_authenticate(user=self.operador_comercial)

        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='FATURADA',
            data_fechamento=timezone.localdate(),
            valor_bruto=Decimal('900.00'),
            valor_total_faturado=Decimal('900.00')
        )
        self.orcamento_1.fatura = fatura
        self.orcamento_1.status_financeiro = 'FATURADO'
        self.orcamento_1.save()

        LancamentoFinanceiro.objects.create(
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='A_VENCER',
            valor=Decimal('900.00'),
            data_vencimento=timezone.localdate(),
            categoria=self.cat_receita
        )

        saldo_inicial_banco = self.conta_bancaria.saldo

        payload = {
            'motivo': 'CORTESIA INSTITUCIONAL CONCEDIDA PELA DIRETORIA PARA PARCEIRO ESTRATÉGICO.'
        }

        response = self.client.post(f'/api/faturas/{fatura.id}/cortesia/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validações da Fatura e Orçamento
        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'PAGA')
        self.assertEqual(fatura.valor_total_faturado, Decimal('0.00'))
        self.assertEqual(fatura.desconto_global, Decimal('900.00'))

        self.orcamento_1.refresh_from_db()
        self.assertEqual(self.orcamento_1.status_financeiro, 'PAGO')

        # Saldo bancário permaneceu idêntico (cortesia não injeta dinheiro real)
        self.conta_bancaria.refresh_from_db()
        self.assertEqual(self.conta_bancaria.saldo, saldo_inicial_banco)

        # Lançamentos a vencer cancelados
        self.assertTrue(LancamentoFinanceiro.objects.filter(fatura=fatura, status_pagamento='CANCELADO').exists())

    def test_08_cancelamento_fatura_com_desvinculacao_em_cascata(self):
        """Testa o cancelamento justificado de fatura e reversão dos orçamentos para A_FATURAR."""
        self.client.force_authenticate(user=self.operador_comercial)

        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='FATURADA',
            data_fechamento=timezone.localdate(),
            valor_bruto=Decimal('900.00'),
            valor_total_faturado=Decimal('900.00')
        )
        self.orcamento_1.fatura = fatura
        self.orcamento_1.status_financeiro = 'FATURADO'
        self.orcamento_1.save()

        LancamentoFinanceiro.objects.create(
            fatura=fatura,
            tipo_lancamento='ENTRADA',
            status_pagamento='A_VENCER',
            valor=Decimal('900.00'),
            data_vencimento=timezone.localdate(),
            categoria=self.cat_receita
        )

        # 1. Rejeição com justificativa curta (< 10 caracteres)
        payload_curto = {'motivo_cancelamento': 'CURTO'}
        res_curto = self.client.post(f'/api/faturas/{fatura.id}/cancelar/', payload_curto, format='json')
        self.assertEqual(res_curto.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Cancelamento válido
        payload_valido = {
            'motivo_cancelamento': 'CANCELAMENTO SOLICITADO PELO CLIENTE PARA REEMISSÃO EM NOME DE OUTRA FILIAL.'
        }
        res_valido = self.client.post(f'/api/faturas/{fatura.id}/cancelar/', payload_valido, format='json')
        self.assertEqual(res_valido.status_code, status.HTTP_200_OK)

        # Fatura CANCELADA
        fatura.refresh_from_db()
        self.assertEqual(fatura.status, 'CANCELADA')
        self.assertIsNotNone(fatura.motivo_cancelamento)

        # Orçamento desvinculado e revertido para A_FATURAR
        self.orcamento_1.refresh_from_db()
        self.assertIsNone(self.orcamento_1.fatura)
        self.assertEqual(self.orcamento_1.status_financeiro, 'A_FATURAR')

        # Lançamento a vencer cancelado
        lancamento = LancamentoFinanceiro.objects.filter(fatura=fatura).first()
        self.assertEqual(lancamento.status_pagamento, 'CANCELADO')

    def test_09_geracao_e_download_pdf_fatura(self):
        """Testa a geração e download do PDF no padrão Industrial Integrity."""
        self.client.force_authenticate(user=self.operador_comercial)

        fatura = Fatura.objects.create(
            cliente=self.cliente_a,
            status='RASCUNHO',
            valor_bruto=Decimal('1500.00'),
            desconto_global=Decimal('0.00'),
            valor_total_faturado=Decimal('1500.00')
        )
        self.orcamento_1.fatura = fatura
        self.orcamento_1.save()

        FaturaPropostaPagamento.objects.create(
            fatura=fatura,
            regra_pagamento=self.regra_a_vista,
            desconto_personalizado=Decimal('5.00')
        )

        response = self.client.get(f'/api/faturas/{fatura.id}/gerar-pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.getvalue()), 1000)

    def test_10_controle_de_acesso_rbac_toggle_comercial(self):
        """Testa se operador sem o toggle acesso_comercial recebe 403 Forbidden."""
        self.client.force_authenticate(user=self.operador_sem_comercial)

        response_list = self.client.get('/api/faturas/')
        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN)

        response_cc = self.client.get('/api/faturas/conta-corrente/')
        self.assertEqual(response_cc.status_code, status.HTTP_403_FORBIDDEN)
