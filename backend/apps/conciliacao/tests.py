"""
Suíte de testes automatizados para a Fase 11 - Conciliação Bancária Inteligente Split-Screen.
Cobre parsers OFX/CSV, motor de matching 1:1 e 1:N, liquidação com impacto em saldo,
lançamento rápido no ato, desconciliação, troca de conta, divergências e segurança RBAC.
"""
from decimal import Decimal
from datetime import date, timedelta
import io

from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario, Permissao
from apps.financeiro.models import ContaBancaria, CategoriaFinanceira, MeioPagamento, LancamentoFinanceiro
from apps.conciliacao.parsers import parse_ofx_content, parse_csv_content, converter_valor_decimal


class ConciliacaoParsersTestCase(TestCase):
    """Testes unitários para os parsers de OFX e CSV."""

    def test_converter_valor_decimal_formatos(self):
        self.assertEqual(converter_valor_decimal("1.250,50"), Decimal("1250.50"))
        self.assertEqual(converter_valor_decimal("-1.250,50"), Decimal("-1250.50"))
        self.assertEqual(converter_valor_decimal("150,00 D"), Decimal("-150.00"))
        self.assertEqual(converter_valor_decimal("(300.75)"), Decimal("-300.75"))
        self.assertEqual(converter_valor_decimal("5000.00"), Decimal("5000.00"))

    def test_parser_ofx_valido(self):
        ofx_conteudo = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <CURDEF>BRL
        <BANKACCTFROM>
          <BANKID>001
          <BRANCHID>1234
          <ACCTID>98765-4
          <ACCTTYPE>CHECKING
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20260801120000[-3:BRT]
          <DTEND>20260831120000[-3:BRT]
          <STMTTRN>
            <TRNTYPE>DEBIT
            <DTPOSTED>20260810120000[-3:BRT]
            <TRNAMT>-85.50
            <FITID>OFX2026081001
            <MEMO>TAR CONTA CORRENTE SERVIÇOS
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT
            <DTPOSTED>20260812120000[-3:BRT]
            <TRNAMT>1500.00
            <FITID>OFX2026081202
            <NAME>PIX RECEBIDO CLIENTE JOAO
          </STMTTRN>
        </BANKTRANLIST>
        <LEDGERBAL>
          <BALAMT>15000.00
          <DTASOF>20260831120000
        </LEDGERBAL>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""
        resultado = parse_ofx_content(ofx_conteudo)
        self.assertEqual(resultado['formato'], 'OFX')
        self.assertEqual(resultado['meta']['banco_codigo'], '001')
        self.assertEqual(resultado['meta']['agencia'], '1234')
        self.assertEqual(resultado['meta']['conta'], '98765-4')
        self.assertEqual(resultado['total_transacoes'], 2)

        t1 = resultado['transacoes'][0]
        self.assertEqual(t1['fitid'], 'OFX2026081001')
        self.assertEqual(t1['data'], '2026-08-10')
        self.assertEqual(t1['valor'], -85.50)
        self.assertEqual(t1['tipo'], 'SAIDA')
        self.assertEqual(t1['descricao'], 'TAR CONTA CORRENTE SERVICOS') # Sem acento

        t2 = resultado['transacoes'][1]
        self.assertEqual(t2['fitid'], 'OFX2026081202')
        self.assertEqual(t2['data'], '2026-08-12')
        self.assertEqual(t2['valor'], 1500.00)
        self.assertEqual(t2['tipo'], 'ENTRADA')
        self.assertEqual(t2['descricao'], 'PIX RECEBIDO CLIENTE JOAO')

    def test_parser_csv_valido(self):
        csv_conteudo = """Data;Historico;Documento;Valor
15/08/2026;PAGAMENTO FORNECEDOR ACO;DOC123;-450,00
16/08/2026;RECEBIMENTO CARTAO CREDITO;DOC456;1200,00
"""
        resultado = parse_csv_content(csv_conteudo)
        self.assertEqual(resultado['formato'], 'CSV')
        self.assertEqual(resultado['total_transacoes'], 2)

        t1 = resultado['transacoes'][0]
        self.assertEqual(t1['data'], '2026-08-15')
        self.assertEqual(t1['valor'], -450.00)
        self.assertEqual(t1['tipo'], 'SAIDA')
        self.assertEqual(t1['descricao'], 'PAGAMENTO FORNECEDOR ACO')

        t2 = resultado['transacoes'][1]
        self.assertEqual(t2['data'], '2026-08-16')
        self.assertEqual(t2['valor'], 1200.00)
        self.assertEqual(t2['tipo'], 'ENTRADA')


class ConciliacaoAPITestCase(TestCase):
    """Testes de integração das APIs de Conciliação Bancária."""

    def setUp(self):
        self.client = APIClient()

        # Usuário Admin
        self.admin = Usuario.objects.create_user(
            email='admin@emcsoldas.com.br',
            nome='ADMINISTRADOR MASTER',
            role='Admin',
            password='Password123!'
        )

        # Usuário Operador com Acesso à Tesouraria
        self.operador_tesouraria = Usuario.objects.create_user(
            email='tesouraria@emcsoldas.com.br',
            nome='OPERADOR TESOURARIA',
            role='Operador',
            password='Password123!'
        )
        self.operador_tesouraria.permissoes.acesso_tesouraria = True
        self.operador_tesouraria.permissoes.save()

        # Usuário Operador sem Acesso à Tesouraria
        self.operador_bloqueado = Usuario.objects.create_user(
            email='bloqueado@emcsoldas.com.br',
            nome='OPERADOR SEM ACESSO',
            role='Operador',
            password='Password123!'
        )
        self.operador_bloqueado.permissoes.acesso_tesouraria = False
        self.operador_bloqueado.permissoes.save()

        # Estruturas financeiras
        self.conta = ContaBancaria.objects.create(
            nome='BANCO DO BRASIL - CC PRINCIPAL',
            saldo=Decimal('10000.00'),
            limite_credito=Decimal('5000.00')
        )
        self.conta_secundaria = ContaBancaria.objects.create(
            nome='ITAU - CC OPERACIONAL',
            saldo=Decimal('3000.00'),
            limite_credito=Decimal('1000.00')
        )

        self.categoria_receita = CategoriaFinanceira.objects.create(
            nome='SERVICOS DE SOLDA E FABRICACAO',
            tipo='RECEITA'
        )
        self.categoria_despesa = CategoriaFinanceira.objects.create(
            nome='TARIFAS E DESPESAS BANCARIAS',
            tipo='DESPESA'
        )
        self.categoria_insumos = CategoriaFinanceira.objects.create(
            nome='AQUISICAO DE MATERIA-PRIMA',
            tipo='DESPESA'
        )

        self.meio_pix = MeioPagamento.objects.create(
            nome='PIX',
            ativo=True
        )

    def test_upload_extrato_split_screen_match_1_1(self):
        """Testa o processamento Split-Screen com sugestão de Match Automático 1:1."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        hoje = timezone.localdate()

        # Cria lançamento no ERP a vencer
        lanc = LancamentoFinanceiro.objects.create(
            tipo_lancamento='ENTRADA',
            descricao='FATURA 101 - CLIENTE TESTE',
            valor=Decimal('1500.00'),
            data_vencimento=hoje,
            status_pagamento='A_VENCER',
            categoria=self.categoria_receita,
            conta=self.conta
        )

        ofx_content = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>CREDIT
            <DTPOSTED>{hoje.strftime('%Y%m%d')}120000
            <TRNAMT>1500.00
            <FITID>FIT1500
            <MEMO>PIX FATURA 101
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""

        arquivo = SimpleUploadedFile("extrato.ofx", ofx_content.encode('utf-8'), content_type="text/plain")

        response = self.client.post(
            '/api/conciliacao/upload-extrato/',
            {'arquivo': arquivo, 'conta_id': self.conta.id},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dados = response.json()
        self.assertEqual(dados['resumo']['total_transacoes_extrato'], 1)
        self.assertEqual(dados['resumo']['total_sugestoes'], 1)

        transacao = dados['extrato'][0]
        self.assertEqual(transacao['status_match'], 'SUGESTAO_1_1')
        self.assertIn(lanc.id, transacao['lancamentos_sugeridos_ids'])

    def test_confirmar_conciliacao_liquida_titulo_pendente(self):
        """Testa a conciliação efetiva liquidando um título a vencer e alterando saldo bancário."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        lanc = LancamentoFinanceiro.objects.create(
            tipo_lancamento='ENTRADA',
            descricao='RECEBIMENTO SERVICO',
            valor=Decimal('2000.00'),
            data_vencimento=timezone.localdate(),
            status_pagamento='A_VENCER',
            categoria=self.categoria_receita
        )

        saldo_anterior = self.conta.saldo

        response = self.client.post('/api/conciliacao/confirmar/', {
            'lancamento_ids': [lanc.id],
            'conta_id': self.conta.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lanc.refresh_from_db()
        self.conta.refresh_from_db()

        self.assertTrue(lanc.is_conciliado)
        self.assertEqual(lanc.status_pagamento, 'PAGO')
        self.assertIsNotNone(lanc.data_conciliacao)
        self.assertEqual(lanc.conciliado_por_id, self.operador_tesouraria.id)
        self.assertEqual(lanc.conta_id, self.conta.id)

        # Saldo bancário deve ter aumentado em R$ 2.000,00
        self.assertEqual(self.conta.saldo, saldo_anterior + Decimal('2000.00'))

    def test_desconciliar_lancamento(self):
        """Testa a reversão da marcação de conciliação."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        lanc = LancamentoFinanceiro.objects.create(
            tipo_lancamento='ENTRADA',
            descricao='RECEBIMENTO CONCILIADO',
            valor=Decimal('1000.00'),
            data_vencimento=timezone.localdate(),
            data_pagamento=timezone.now(),
            status_pagamento='PAGO',
            is_conciliado=True,
            data_conciliacao=timezone.now(),
            conciliado_por=self.operador_tesouraria,
            categoria=self.categoria_receita,
            conta=self.conta
        )

        response = self.client.post('/api/conciliacao/desconciliar/', {
            'lancamento_id': lanc.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lanc.refresh_from_db()

        self.assertFalse(lanc.is_conciliado)
        self.assertIsNone(lanc.data_conciliacao)
        self.assertIsNone(lanc.conciliado_por)
        # Permanece como PAGO
        self.assertEqual(lanc.status_pagamento, 'PAGO')

    def test_lancamento_rapido_no_ato(self):
        """Testa a criação instantânea de tarifa bancária a partir da linha do extrato."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        saldo_anterior = self.conta.saldo

        payload = {
            'tipo_lancamento': 'SAIDA',
            'descricao': 'TARIFA MANUTENCAO DE CONTA',
            'valor': '45.90',
            'conta_id': self.conta.id,
            'categoria_id': self.categoria_despesa.id,
            'meio_pagamento_id': self.meio_pix.id
        }

        response = self.client.post('/api/conciliacao/lancamento-rapido/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        dados = response.json()['lancamento']
        self.assertTrue(dados['is_conciliado'])
        self.assertEqual(dados['status_pagamento'], 'PAGO')
        self.assertEqual(dados['descricao'], 'TARIFA MANUTENCAO DE CONTA')

        self.conta.refresh_from_db()
        self.assertEqual(self.conta.saldo, saldo_anterior - Decimal('45.90'))

    def test_trocar_conta_lancamento_remaneja_saldo(self):
        """Testa a troca de conta bancária com estorno da antiga e débito na nova."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        # Lançamento pago que foi baixado na conta 1
        lanc = LancamentoFinanceiro.objects.create(
            tipo_lancamento='SAIDA',
            descricao='PAGAMENTO DE PECAS',
            valor=Decimal('500.00'),
            data_vencimento=timezone.localdate(),
            data_pagamento=timezone.now(),
            status_pagamento='PAGO',
            conta=self.conta,
            categoria=self.categoria_insumos
        )

        saldo_conta1_inicial = self.conta.saldo
        saldo_conta2_inicial = self.conta_secundaria.saldo

        response = self.client.post('/api/conciliacao/trocar-conta/', {
            'lancamento_id': lanc.id,
            'nova_conta_id': self.conta_secundaria.id
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.conta.refresh_from_db()
        self.conta_secundaria.refresh_from_db()
        lanc.refresh_from_db()

        self.assertEqual(lanc.conta_id, self.conta_secundaria.id)
        # Conta 1 recebe de volta R$ 500
        self.assertEqual(self.conta.saldo, saldo_conta1_inicial + Decimal('500.00'))
        # Conta 2 é debitada em R$ 500
        self.assertEqual(self.conta_secundaria.saldo, saldo_conta2_inicial - Decimal('500.00'))

    def test_divergencias_conciliacao(self):
        """Testa o endpoint de consulta do Relatório de Divergências."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        # Cria lançamento no ERP não conciliado
        LancamentoFinanceiro.objects.create(
            tipo_lancamento='SAIDA',
            descricao='DESPESA DIVERGENTE NAO CONCILIADA',
            valor=Decimal('320.00'),
            data_vencimento=timezone.localdate(),
            status_pagamento='PAGO',
            conta=self.conta,
            categoria=self.categoria_insumos,
            is_conciliado=False
        )

        response = self.client.get('/api/conciliacao/divergencias/', {'conta_id': self.conta.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        dados = response.json()
        self.assertIn('aba_1_sobras_extrato', dados)
        self.assertIn('aba_2_sobras_erp', dados)
        self.assertGreaterEqual(dados['aba_2_sobras_erp']['total_registros'], 1)

    def test_rbac_bloqueio_sem_acesso_tesouraria(self):
        """Testa se colaborador sem o toggle 'acesso_tesouraria' recebe 403 Forbidden."""
        self.client.force_authenticate(user=self.operador_bloqueado)

        response = self.client.get('/api/conciliacao/divergencias/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post('/api/conciliacao/confirmar/', {'lancamento_ids': [1], 'conta_id': 1})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_importacao_lote_com_sucesso(self):
        """Testa a geração em lote de lançamentos a partir do extrato com conciliação automática."""
        self.client.force_authenticate(user=self.operador_tesouraria)
        saldo_inicial = self.conta.saldo

        payload = {
            'conta_id': self.conta.id,
            'lancamentos': [
                {
                    'fitid': 'LOTE_TEST_001',
                    'data_pagamento': '2026-08-20T12:00:00Z',
                    'descricao': 'TARIFA BANCARIA LOTE',
                    'valor': '45.00',
                    'tipo_lancamento': 'SAIDA',
                    'categoria_id': self.categoria_insumos.id,
                    'documento': 'DOCLOTE1'
                },
                {
                    'fitid': 'LOTE_TEST_002',
                    'data_pagamento': '2026-08-21T14:30:00Z',
                    'descricao': 'DEPOSITO CLIENTE LOTE',
                    'valor': '2500.00',
                    'tipo_lancamento': 'ENTRADA',
                    'categoria_id': self.categoria_receita.id,
                    'documento': 'DOCLOTE2'
                }
            ]
        }

        response = self.client.post('/api/conciliacao/importacao-lote/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        dados = response.json()
        self.assertEqual(dados['status'], 'sucesso')
        self.assertEqual(dados['total_processados'], 2)

        self.conta.refresh_from_db()
        # Saldo inicial + (-45.00) + (+2500.00) = Saldo inicial + 2455.00
        self.assertEqual(self.conta.saldo, saldo_inicial + Decimal('2455.00'))

        # Verifica se os lançamentos foram criados como PAGO e is_conciliado=True
        l1 = LancamentoFinanceiro.objects.get(descricao='TARIFA BANCARIA LOTE')
        self.assertEqual(l1.status_pagamento, 'PAGO')
        self.assertTrue(l1.is_conciliado)
        self.assertEqual(l1.valor, Decimal('45.00'))
        self.assertEqual(l1.tipo_lancamento, 'SAIDA')

        l2 = LancamentoFinanceiro.objects.get(descricao='DEPOSITO CLIENTE LOTE')
        self.assertEqual(l2.status_pagamento, 'PAGO')
        self.assertTrue(l2.is_conciliado)
        self.assertEqual(l2.valor, Decimal('2500.00'))
        self.assertEqual(l2.tipo_lancamento, 'ENTRADA')

    def test_reconhecimento_parceiro_fatura_iss_retido_e_duplicidade(self):
        """Testa enriquecimento com CNPJ, fatura com retenção de ISS (tolerância R$ 0,05) e bloqueio de duplicidade."""
        from apps.cadastros.models import ClienteFornecedor
        from apps.faturamento.models import Fatura
        from apps.administracao.models import ConfiguracaoGlobal

        self.client.force_authenticate(user=self.operador_tesouraria)

        # Configura Alíquota de ISS Global em 3.00%
        cfg, _ = ConfiguracaoGlobal.objects.get_or_create(id=1)
        cfg.aliquota_iss = Decimal('3.00')
        cfg.save()

        # Cadastra cliente com retenção de ISS
        cliente = ClienteFornecedor.objects.create(
            nome_razao='PETRA MINERACAO LTDA',
            cnpj_cpf='02329307000166',
            tipo='CLIENTE',
            tipo_pessoa='PJ',
            iss_retido=True
        )

        # Fatura de R$ 10.000,00 -> ISS 3% = R$ 300,00 -> Líquido esperado = R$ 9.700,00
        fatura = Fatura.objects.create(
            cliente=cliente,
            status='FATURADA',
            valor_bruto=Decimal('10000.00'),
            valor_total_faturado=Decimal('10000.00'),
            data_fechamento=timezone.localdate()
        )

        # Simula extrato com recebimento de R$ 9.700,03 (dentro da margem de 5 centavos)
        hoje = timezone.localdate()
        ofx_content = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
<OFX>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <BANKTRANLIST>
          <STMTTRN>
            <TRNTYPE>CREDIT
            <DTPOSTED>{hoje.strftime('%Y%m%d')}120000
            <TRNAMT>9700.03
            <FITID>PETRA_PIX_01
            <MEMO>02.329.307/0001-66 - PETRA MINERACAO LTDA
          </STMTTRN>
        </BANKTRANLIST>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""
        arquivo = SimpleUploadedFile("extrato_petra.ofx", ofx_content.encode('utf-8'), content_type="text/plain")

        response = self.client.post(
            '/api/conciliacao/upload-extrato/',
            {'arquivo': arquivo, 'conta_id': self.conta.id},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dados = response.json()
        trn = dados['extrato'][0]

        # Valida parceiro identificado
        self.assertIsNotNone(trn['parceiro_identificado'])
        self.assertEqual(trn['parceiro_identificado']['id'], cliente.id)
        self.assertTrue(trn['parceiro_identificado']['iss_retido'])

        # Valida fatura sugerida com cálculo de ISS retido
        self.assertIsNotNone(trn['fatura_sugerida'])
        self.assertEqual(trn['fatura_sugerida']['id'], fatura.id)
        self.assertTrue(trn['fatura_sugerida']['iss_retido_aplicado'])
        self.assertEqual(trn['fatura_sugerida']['valor_iss'], 300.0)

        # Importa em lote com vinculação à fatura e parceiro
        payload_lote = {
            'conta_id': self.conta.id,
            'lancamentos': [
                {
                    'fitid': 'PETRA_PIX_01',
                    'data_pagamento': hoje.isoformat(),
                    'descricao': 'FATURA #1 - PETRA MINERACAO LTDA',
                    'valor': '9700.03',
                    'tipo_lancamento': 'ENTRADA',
                    'categoria_id': self.categoria_receita.id,
                    'cliente_fornecedor_id': cliente.id,
                    'fatura_id': fatura.id
                }
            ]
        }
        res_lote = self.client.post('/api/conciliacao/importacao-lote/', payload_lote, format='json')
        self.assertEqual(res_lote.status_code, status.HTTP_201_CREATED)

        # Testa que se re-enviarmos o mesmo extrato, o FITID dispara DUPLICIDADE
        arquivo_dup = SimpleUploadedFile("extrato_petra_dup.ofx", ofx_content.encode('utf-8'), content_type="text/plain")
        res_dup = self.client.post(
            '/api/conciliacao/upload-extrato/',
            {'arquivo': arquivo_dup, 'conta_id': self.conta.id},
            format='multipart'
        )
        self.assertEqual(res_dup.status_code, status.HTTP_200_OK)
        trn_dup = res_dup.json()['extrato'][0]
        self.assertTrue(trn_dup['duplicidade'])
        self.assertIn('PETRA_PIX_01', trn_dup['duplicidade_motivo'])

    def test_upload_comprovante_e_importacao_lote_com_anexo(self):
        """Testa o endpoint upload-comprovante e a gravação de comprovante no LancamentoFinanceiro."""
        self.client.force_authenticate(user=self.operador_tesouraria)

        dummy_pdf = SimpleUploadedFile("nota_fiscal_servico.pdf", b"%PDF-1.4 Mock PDF content", content_type="application/pdf")
        response_upload = self.client.post(
            '/api/conciliacao/upload-comprovante/',
            {'arquivo': dummy_pdf},
            format='multipart'
        )

        self.assertEqual(response_upload.status_code, status.HTTP_201_CREATED)
        dados_upload = response_upload.json()
        self.assertEqual(dados_upload['status'], 'sucesso')
        self.assertIn('comprovantes/', dados_upload['comprovante_path'])
        self.assertEqual(dados_upload['nome_arquivo_comprovante'], 'nota_fiscal_servico.pdf')

        caminho_salvo = dados_upload['comprovante_path']

        # Efetua importação em lote incluindo o comprovante no payload
        payload_lote = {
            'conta_id': self.conta.id,
            'lancamentos': [
                {
                    'fitid': 'PIX_COM_ANEXO_001',
                    'data_pagamento': '2026-09-15T10:00:00Z',
                    'descricao': 'RECEBIMENTO SERVICO SOLDA COM NF',
                    'valor': '1500.00',
                    'tipo_lancamento': 'ENTRADA',
                    'categoria_id': self.categoria_receita.id,
                    'comprovante_path': caminho_salvo,
                    'nome_arquivo_comprovante': 'nota_fiscal_servico.pdf'
                }
            ]
        }

        res_lote = self.client.post('/api/conciliacao/importacao-lote/', payload_lote, format='json')
        self.assertEqual(res_lote.status_code, status.HTTP_201_CREATED)

        lanc = LancamentoFinanceiro.objects.get(fitid='PIX_COM_ANEXO_001')
        self.assertEqual(lanc.nome_arquivo_comprovante, 'nota_fiscal_servico.pdf')
        self.assertTrue(lanc.comprovante.name.endswith('.pdf'))


