"""
Testes automatizados completos para o módulo de Compras, Notas Fiscais de Entrada e Retroalimentação de Custos (Fase 7).
Valida CRUD, RBAC, Sanitização Universal, Validação de Chave NFe, Retroalimentação de Custos no Catálogo,
Upload/Download Seguro de XML/PDF e Histórico de Preços por Fornecedor.
"""
import io
import os
import shutil
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction, IntegrityError
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario
from apps.cadastros.models import ClienteFornecedor
from apps.catalogo.models import DicionarioUom, Item
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem


class ComprasModuleTestCase(TestCase):
    """Suíte completa de testes para Compras, Notas Fiscais de Entrada e Retroalimentação de Custos."""

    def setUp(self):
        self.client = APIClient()

        # 1. Usuário Administrador Master
        self.admin = Usuario.objects.create_user(
            email="admin.compras@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        # 2. Usuário Operador sem permissões
        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem.compras@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        # 3. Usuário Operador com permissão de Compras
        self.operador_compras = Usuario.objects.create_user(
            email="operador.compras@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_compras.permissoes.acesso_compras = True
        self.operador_compras.permissoes.save()

        # 4. Dados cadastrais de apoio
        self.fornecedor_acos = ClienteFornecedor.objects.create(
            tipo="Fornecedor",
            tipo_pessoa="PJ",
            nome_razao="ACOS BRASIL DISTRIBUIDORA LTDA",
            cnpj_cpf="33000167000101",
            telefone="1133334444"
        )

        self.fornecedor_gases = ClienteFornecedor.objects.create(
            tipo="Ambos",
            tipo_pessoa="PJ",
            nome_razao="OXIGENIO E GASES INDUSTRIAIS SA",
            cnpj_cpf="00000000000191",
            telefone="1133335555"
        )

        self.cliente_apenas = ClienteFornecedor.objects.create(
            tipo="Cliente",
            tipo_pessoa="PJ",
            nome_razao="TRANSPORTADORA VELOZ LTDA",
            cnpj_cpf="11222333000144",
            telefone="1199998888"
        )

        # Unidades de medida
        self.uom_un = DicionarioUom.objects.create(sigla="UN", descricao="UNIDADE")
        self.uom_barra = DicionarioUom.objects.create(sigla="BARRA", descricao="BARRA DE 6 METROS")
        self.uom_metro = DicionarioUom.objects.create(sigla="M", descricao="METRO LINEAR")
        self.uom_kg = DicionarioUom.objects.create(sigla="KG", descricao="QUILOGRAMA")

        # Itens do catálogo
        self.item_tubo = Item.objects.create(
            nome="TUBO DE ACO CARBONO 2 POLEGADAS",
            unidade_compra=self.uom_barra,
            unidade_consumo=self.uom_metro,
            fator_conversao=Decimal('6.0000'),
            ultimo_custo_compra=Decimal('100.00'),
            tipo_uso="INSUMO_PRODUTIVO"
        )

        self.item_arame = Item.objects.create(
            nome="ARAME DE SOLDA MIG ER70S-6 1.2MM",
            unidade_compra=self.uom_kg,
            unidade_consumo=self.uom_kg,
            fator_conversao=Decimal('1.0000'),
            ultimo_custo_compra=Decimal('25.00'),
            tipo_uso="INSUMO_PRODUTIVO"
        )

    def tearDown(self):
        # Limpa eventuais arquivos criados em media/compras durante os testes
        pasta_compras = os.path.join(settings.MEDIA_ROOT, 'compras')
        if os.path.exists(pasta_compras):
            shutil.rmtree(pasta_compras, ignore_errors=True)

    # =========================================================================
    # 1. TESTES DE AUTENTICAÇÃO E RBAC
    # =========================================================================

    def test_compras_unauthenticated_access_denied(self):
        """Usuário não autenticado deve receber 401."""
        response = self.client.get('/api/documentos-fiscais-compra/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_compras_operador_sem_permissao_forbidden(self):
        """Operador sem o toggle 'acesso_compras' deve receber 403."""
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/documentos-fiscais-compra/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_compras_operador_com_permissao_allowed(self):
        """Operador com toggle 'acesso_compras' pode listar notas."""
        self.client.force_authenticate(user=self.operador_compras)
        response = self.client.get('/api/documentos-fiscais-compra/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_compras_admin_allowed(self):
        """Administrador tem acesso irrestrito."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/documentos-fiscais-compra/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # =========================================================================
    # 2. TESTES DE CRUD E SANITIZAÇÃO DE NOTAS DE COMPRA
    # =========================================================================

    def test_criar_nota_compra_com_itens_e_sanitizacao(self):
        """Cria nota de compra com itens aninhados, sanitizando o número da nota."""
        self.client.force_authenticate(user=self.operador_compras)

        chave_44 = "35260833000167550010000123451234567890123456"
        payload = {
            "num_nota": "nf-e nº 45.890-a",
            "chave_acesso": f" {chave_44[:4]} {chave_44[4:8]}-{chave_44[8:]} ",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-15",
            "valor_total": "1250.00",
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "10.0000",
                    "valor_unitario": "110.0000"
                },
                {
                    "item_id": self.item_arame.id,
                    "quantidade_comprada": "5.0000",
                    "valor_unitario": "30.0000"
                }
            ]
        }

        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['num_nota'], "NF-E NO 45.890-A")
        self.assertEqual(response.data['chave_acesso'], chave_44)
        self.assertEqual(response.data['total_itens'], 2)

        # Verifica persistência no banco
        doc = DocumentoFiscalCompra.objects.get(pk=response.data['id'])
        self.assertEqual(doc.itens_comprados.count(), 2)

    def test_validacao_chave_acesso_invalida(self):
        """Chave de acesso com quantidade incorreta de dígitos deve ser rejeitada."""
        self.client.force_authenticate(user=self.operador_compras)

        payload = {
            "num_nota": "NF 123",
            "chave_acesso": "1234567890",  # Menos de 44 dígitos
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-15",
            "valor_total": "500.00"
        }
        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("chave_acesso", str(response.data))

    def test_validacao_fornecedor_apenas_cliente_rejeitado(self):
        """Parceiro cadastrado apenas como 'Cliente' não pode ser usado em notas de compra."""
        self.client.force_authenticate(user=self.operador_compras)

        payload = {
            "num_nota": "NF 1234",
            "fornecedor_id": self.cliente_apenas.id,
            "data_compra": "2026-08-15",
            "valor_total": "300.00"
        }
        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fornecedor", str(response.data))

    def test_validacao_item_duplicado_na_mesma_nota(self):
        """O mesmo item não pode ser inserido duas vezes na mesma nota fiscal."""
        self.client.force_authenticate(user=self.operador_compras)

        payload = {
            "num_nota": "NF 999",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-15",
            "valor_total": "200.00",
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "1.0000",
                    "valor_unitario": "100.0000"
                },
                {
                    "item_id": self.item_tubo.id,  # Duplicado
                    "quantidade_comprada": "2.0000",
                    "valor_unitario": "100.0000"
                }
            ]
        }
        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("itens_comprados", str(response.data))

    # =========================================================================
    # 3. TESTES DE RETROALIMENTAÇÃO AUTOMÁTICA DE CUSTOS NO CATÁLOGO
    # =========================================================================

    def test_retroalimentacao_automatica_custos(self):
        """Ao cadastrar nota de compra, o último custo do Item é atualizado automaticamente."""
        self.client.force_authenticate(user=self.operador_compras)

        # Custo anterior do tubo era 100.00
        self.assertEqual(self.item_tubo.ultimo_custo_compra, Decimal('100.00'))

        payload = {
            "num_nota": "NF 5000",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-18",
            "valor_total": "1350.00",
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "10.0000",
                    "valor_unitario": "135.0000"  # Novo custo unitário
                }
            ]
        }

        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifica se o Item no banco foi retroalimentado
        self.item_tubo.refresh_from_db()
        self.assertEqual(self.item_tubo.ultimo_custo_compra, Decimal('135.00'))
        self.assertIsNotNone(self.item_tubo.data_ultima_compra)

    def test_retroalimentacao_via_item_avulso_viewset(self):
        """Inclusão de item avulso via /api/nota-compra-itens/ também atualiza o custo."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 888",
            fornecedor=self.fornecedor_gases,
            data_compra=date(2026, 8, 17),
            valor_total=Decimal('500.00')
        )

        payload = {
            "documento_fiscal": doc.id,
            "item_id": self.item_arame.id,
            "quantidade_comprada": "10.0000",
            "valor_unitario": "32.5000"
        }

        response = self.client.post('/api/nota-compra-itens/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.item_arame.refresh_from_db()
        self.assertEqual(self.item_arame.ultimo_custo_compra, Decimal('32.50'))

    # =========================================================================
    # 4. TESTES DE UPLOAD E DOWNLOAD SEGURO DE ANEXOS (XML/PDF)
    # =========================================================================

    def test_upload_pdf_seguro(self):
        """Upload de arquivo PDF com cabeçalho %PDF válido."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 100",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('100.00')
        )

        conteudo_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        arquivo_pdf = SimpleUploadedFile("danfe_nota_100.pdf", conteudo_pdf, content_type="application/pdf")

        response = self.client.post(
            f'/api/documentos-fiscais-compra/{doc.id}/anexar-arquivo/',
            {'arquivo': arquivo_pdf},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('caminho_arquivo_anexo', response.data)

        # Testa download seguro do anexo
        response_dl = self.client.get(f'/api/documentos-fiscais-compra/{doc.id}/download-anexo/')
        self.assertEqual(response_dl.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', response_dl['Content-Disposition'])
        self.assertEqual(response_dl['X-Content-Type-Options'], 'nosniff')

    def test_upload_xml_seguro(self):
        """Upload de arquivo XML NFe válido."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 200",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('200.00')
        )

        conteudo_xml = b'<?xml version="1.0" encoding="UTF-8"?><nfeProc><NFe><infNFe><total><vNF>200.00</vNF></total></infNFe></NFe></nfeProc>'
        arquivo_xml = SimpleUploadedFile("nfe_200.xml", conteudo_xml, content_type="application/xml")

        response = self.client.post(
            f'/api/documentos-fiscais-compra/{doc.id}/anexar-arquivo/',
            {'arquivo': arquivo_xml},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_upload_arquivo_extensao_proibida_rejeitado(self):
        """Arquivos executáveis ou scripts (.exe, .py, .sh) devem ser sumariamente bloqueados."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 300",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('300.00')
        )

        arquivo_malicioso = SimpleUploadedFile("script.py", b"print('hacked')", content_type="text/x-python")

        response = self.client.post(
            f'/api/documentos-fiscais-compra/{doc.id}/anexar-arquivo/',
            {'arquivo': arquivo_malicioso},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Extensão '.py' não permitida", str(response.data))

    def test_upload_pdf_falso_magic_bytes_rejeitado(self):
        """Arquivo com extensão .pdf mas sem magic bytes válidos (%PDF) deve ser rejeitado."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 400",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('400.00')
        )

        conteudo_falso = b"ISSO NAO EH UM PDF DE VERDADE"
        arquivo_falso = SimpleUploadedFile("falso.pdf", conteudo_falso, content_type="application/pdf")

        response = self.client.post(
            f'/api/documentos-fiscais-compra/{doc.id}/anexar-arquivo/',
            {'arquivo': arquivo_falso},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cabeçalho inválido", str(response.data))

    def test_upload_xml_xxe_rejeitado(self):
        """Arquivo XML com entidade maliciosa/DOCTYPE deve ser rejeitado por segurança."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 450",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('450.00')
        )

        xml_malicioso = b'<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>'
        arquivo_xxe = SimpleUploadedFile("malicioso.xml", xml_malicioso, content_type="application/xml")

        response = self.client.post(
            f'/api/documentos-fiscais-compra/{doc.id}/anexar-arquivo/',
            {'arquivo': arquivo_xxe},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("proteção contra XXE", str(response.data))

    def test_criar_nota_compra_calcula_valor_total_automatico(self):
        """Se valor_total for omitido no payload, o serializer calcula automaticamente a soma dos itens."""
        self.client.force_authenticate(user=self.operador_compras)

        payload = {
            "num_nota": "NF 9999",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-20",
            # valor_total omitido intencionalmente
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "2.0000",
                    "valor_unitario": "50.0000"
                },
                {
                    "item_id": self.item_arame.id,
                    "quantidade_comprada": "4.0000",
                    "valor_unitario": "25.0000"
                }
            ]
        }

        response = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 2 * 50 + 4 * 25 = 200.00
        self.assertEqual(Decimal(str(response.data['valor_total'])), Decimal('200.00'))

    # =========================================================================
    # 5. TESTES DE HISTÓRICO DE PREÇOS E CONSULTAS
    # =========================================================================

    def test_historico_precos_por_item(self):
        """Consulta do histórico de preços pagos em compras passadas por item."""
        self.client.force_authenticate(user=self.operador_compras)

        # Cria 2 notas em datas distintas para o item_tubo
        doc1 = DocumentoFiscalCompra.objects.create(
            num_nota="NF 1001",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 7, 10),
            valor_total=Decimal('1000.00')
        )
        NotaCompraItem.objects.create(
            documento_fiscal=doc1,
            item=self.item_tubo,
            quantidade_comprada=Decimal('10.0000'),
            valor_unitario=Decimal('100.0000')
        )

        doc2 = DocumentoFiscalCompra.objects.create(
            num_nota="NF 1002",
            fornecedor=self.fornecedor_gases,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('1200.00')
        )
        NotaCompraItem.objects.create(
            documento_fiscal=doc2,
            item=self.item_tubo,
            quantidade_comprada=Decimal('10.0000'),
            valor_unitario=Decimal('120.0000')
        )

        # Consulta endpoint de histórico
        response = self.client.get(f'/api/documentos-fiscais-compra/historico-precos/?item_id={self.item_tubo.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['item_id'], self.item_tubo.id)
        self.assertEqual(response.data['total_aquisicoes'], 2)
        self.assertEqual(Decimal(str(response.data['menor_preco'])), Decimal('100.00'))
        self.assertEqual(Decimal(str(response.data['maior_preco'])), Decimal('120.00'))
        self.assertEqual(Decimal(str(response.data['preco_medio'])), Decimal('110.00'))
        self.assertEqual(len(response.data['historico']), 2)

    def test_historico_precos_sem_item_id_erro(self):
        """Consulta sem item_id deve retornar 400 Bad Request."""
        self.client.force_authenticate(user=self.operador_compras)
        response = self.client.get('/api/documentos-fiscais-compra/historico-precos/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filtros_notas_compra(self):
        """Filtros por fornecedor_id, intervalo de datas e item_id."""
        self.client.force_authenticate(user=self.operador_compras)

        doc1 = DocumentoFiscalCompra.objects.create(
            num_nota="NF 10",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 1),
            valor_total=Decimal('500.00')
        )
        NotaCompraItem.objects.create(
            documento_fiscal=doc1,
            item=self.item_tubo,
            quantidade_comprada=Decimal('5.0000'),
            valor_unitario=Decimal('100.0000')
        )

        doc2 = DocumentoFiscalCompra.objects.create(
            num_nota="NF 20",
            fornecedor=self.fornecedor_gases,
            data_compra=date(2026, 8, 15),
            valor_total=Decimal('300.00')
        )
        NotaCompraItem.objects.create(
            documento_fiscal=doc2,
            item=self.item_arame,
            quantidade_comprada=Decimal('10.0000'),
            valor_unitario=Decimal('30.0000')
        )

        # Filtro por fornecedor
        resp_forn = self.client.get(f'/api/documentos-fiscais-compra/?fornecedor_id={self.fornecedor_acos.id}')
        self.assertEqual(resp_forn.status_code, status.HTTP_200_OK)
        results = resp_forn.data.get('results', resp_forn.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['num_nota'], "NF 10")

        # Filtro por item
        resp_item = self.client.get(f'/api/documentos-fiscais-compra/?item_id={self.item_arame.id}')
        self.assertEqual(resp_item.status_code, status.HTTP_200_OK)
        results_item = resp_item.data.get('results', resp_item.data)
        self.assertEqual(len(results_item), 1)
        self.assertEqual(results_item[0]['num_nota'], "NF 20")

    # =========================================================================
    # 6. TESTES DE SOFT DELETE
    # =========================================================================

    def test_soft_delete_documento_fiscal_compra(self):
        """Exclusão de Nota Fiscal aplica Soft Delete sem remover registro físico."""
        self.client.force_authenticate(user=self.operador_compras)

        doc = DocumentoFiscalCompra.objects.create(
            num_nota="NF 9999",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 10),
            valor_total=Decimal('1000.00')
        )

        response = self.client.delete(f'/api/documentos-fiscais-compra/{doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verifica soft delete no banco
        doc.refresh_from_db()
        self.assertIsNotNone(doc.deleted_at)
        self.assertEqual(doc.deleted_by_id, self.operador_compras.id)

        # Não aparece na listagem ativa
        list_resp = self.client.get('/api/documentos-fiscais-compra/')
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        results = list_resp.data.get('results', list_resp.data)
        self.assertEqual(len(results), 0)

    # =========================================================================
    # 7. TESTES DE ANÁLISE PRÉVIA E CRUZAMENTO DE CNPJ (XML / PDF)
    # =========================================================================

    def test_analisar_documento_xml_fornecedor_existente(self):
        """Envio de XML extrai dados e identifica fornecedor existente pelo CNPJ."""
        self.client.force_authenticate(user=self.operador_compras)

        xml_conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe Id="NFe35260933000167000101550010001234561000000018">
                    <ide>
                        <nNF>123456</nNF>
                        <dhEmi>2026-09-10T10:00:00-03:00</dhEmi>
                    </ide>
                    <emit>
                        <CNPJ>33000167000101</CNPJ>
                        <xNome>ACOS BRASIL DISTRIBUIDORA LTDA</xNome>
                    </emit>
                    <total>
                        <ICMSTot>
                            <vNF>1500.50</vNF>
                        </ICMSTot>
                    </total>
                </infNFe>
            </NFe>
        </nfeProc>
        """.encode('utf-8')

        arquivo_xml = SimpleUploadedFile("nfe_teste.xml", xml_conteudo, content_type="text/xml")
        resp = self.client.post(
            '/api/documentos-fiscais-compra/analisar-documento/',
            {'arquivo': arquivo_xml},
            format='multipart'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        dados = resp.data.get('dados_extraidos', {})
        self.assertEqual(dados.get('cnpj_emitente'), '33000167000101')
        self.assertEqual(dados.get('num_nota'), '123456')
        self.assertEqual(dados.get('data_compra'), '2026-09-10')
        self.assertEqual(dados.get('valor_total'), '1500.50')
        self.assertEqual(dados.get('chave_acesso'), '35260933000167000101550010001234561000000018')

        parceiro = resp.data.get('parceiro_existente')
        self.assertIsNotNone(parceiro)
        self.assertEqual(parceiro['id'], self.fornecedor_acos.id)
        self.assertEqual(parceiro['tipo'], 'Fornecedor')

    def test_analisar_documento_cliente_a_habilitar(self):
        """Identifica quando o emitente existe no banco mas com tipo 'Cliente'."""
        self.client.force_authenticate(user=self.operador_compras)

        xml_conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe Id="NFe35260988888888000188550010000009991000000017">
                    <ide>
                        <nNF>999</nNF>
                        <dhEmi>2026-09-10T10:00:00-03:00</dhEmi>
                    </ide>
                    <emit>
                        <CNPJ>11222333000144</CNPJ>
                        <xNome>TRANSPORTADORA VELOZ LTDA</xNome>
                    </emit>
                    <total>
                        <ICMSTot>
                            <vNF>850.00</vNF>
                        </ICMSTot>
                    </total>
                </infNFe>
            </NFe>
        </nfeProc>
        """.encode('utf-8')

        arquivo_xml = SimpleUploadedFile("nfe_cliente.xml", xml_conteudo, content_type="text/xml")
        resp = self.client.post(
            '/api/documentos-fiscais-compra/analisar-documento/',
            {'arquivo': arquivo_xml},
            format='multipart'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        parceiro = resp.data.get('parceiro_existente')
        self.assertIsNotNone(parceiro)
        self.assertEqual(parceiro['tipo'], 'Cliente')

        # Agora testa a ação de habilitar fornecedor
        resp_hab = self.client.post(f'/api/clientes-fornecedores/{parceiro["id"]}/habilitar-fornecedor/')
        self.assertEqual(resp_hab.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_hab.data['parceiro']['tipo'], 'Ambos')

        # Recarrega do banco
        self.cliente_apenas.refresh_from_db()
        self.assertEqual(self.cliente_apenas.tipo, 'Ambos')

    def test_analisar_documento_boleto_bancario_bloqueado(self):
        """Documentos de cobrança bancária (boletos) devem ser bloqueados na entrada de compras."""
        self.client.force_authenticate(user=self.operador_compras)

        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 750, "Autenticacao Mecanica - Ficha de Compensacao")
        p.drawString(100, 730, "Beneficiario: NOVUS CONTABILIDADE LTDA CNPJ: 38.536.678/0001-66")
        p.drawString(100, 710, "Pagador: ABBAC JF CENTRO CNPJ: 07.030.719/0001-14")
        p.drawString(100, 690, "Detalhamento do Boleto - Nosso Numero: 0042698-3")
        p.showPage()
        p.save()
        buffer.seek(0)

        arquivo_pdf = SimpleUploadedFile("boleto_sicoob.pdf", buffer.getvalue(), content_type="application/pdf")
        resp = self.client.post(
            '/api/documentos-fiscais-compra/analisar-documento/',
            {'arquivo': arquivo_pdf},
            format='multipart'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data.get('is_documento_fiscal'))
        self.assertEqual(resp.data.get('tipo_documento'), 'BOLETO')
        self.assertIn('Boleto Bancário', resp.data.get('message', ''))

    def test_analisar_documento_danfse_50_digitos(self):
        """DANFSe v2.0 com chave nacional de 50 dígitos deve extrair chave, prestador e número da nota."""
        self.client.force_authenticate(user=self.operador_compras)

        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 770, "DANFSe v2.0 Documento Auxiliar da NFS-e")
        p.drawString(100, 750, "CHAVE DE ACESSO DA NFS-e")
        p.drawString(100, 735, "31367022225805557000120000000000001026090640797349")
        p.drawString(100, 715, "NUMERO DA NFS-e: 10")
        p.drawString(100, 695, "DATA E HORA DA EMISSAO DA NFS-e: 09/09/2026")
        p.drawString(100, 675, "PRESTADOR / FORNECEDOR CNPJ / CPF / NIF: 25.805.557/0001-20")
        p.drawString(100, 655, "Nome / Nome Empresarial: MULTIPRINTERS COMERCIO E SERVICOS LTDA")
        p.drawString(100, 635, "TOMADOR / ADQUIRENTE CNPJ: 07.030.719/0001-14")
        p.drawString(100, 615, "VALOR TOTAL DA NFS-e: R$ 319,00")
        p.showPage()
        p.save()
        buffer.seek(0)

        arquivo_pdf = SimpleUploadedFile("nfse_10.pdf", buffer.getvalue(), content_type="application/pdf")
        resp = self.client.post(
            '/api/documentos-fiscais-compra/analisar-documento/',
            {'arquivo': arquivo_pdf},
            format='multipart'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get('is_documento_fiscal'))
        dados = resp.data.get('dados_extraidos', {})
        self.assertEqual(dados.get('chave_acesso'), '31367022225805557000120000000000001026090640797349')
        self.assertEqual(dados.get('cnpj_emitente'), '25805557000120')
        self.assertEqual(dados.get('num_nota'), '10')
        self.assertEqual(dados.get('data_compra'), '2026-09-09')
        self.assertEqual(dados.get('valor_total'), '319.00')

    def test_analisar_documento_danfe_blocos_4_digitos(self):
        """DANFE com chave impressa em 11 blocos de 4 dígitos precedida por CNPJ e protocolo."""
        self.client.force_authenticate(user=self.operador_compras)

        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.drawString(100, 770, "DANFE DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRONICA")
        p.drawString(100, 750, "PROTOCOLO DE AUTORIZACAO 131267812554004 12/08/2026")
        p.drawString(100, 730, "CNPJ / CPF 17.851.981/0001-83")
        p.drawString(100, 710, "CHAVE DE ACESSO")
        p.drawString(100, 690, "3126 0817 8519 8100 0183 5500 3000 1573 8315 8090 8986")
        p.drawString(100, 670, "DESTINATARIO / REMETENTE CNPJ 07.030.719/0002-03")
        p.drawString(100, 650, "DATA DA EMISSAO: 12/08/2026")
        p.drawString(100, 630, "VALOR TOTAL DA NOTA: 19,80")
        p.showPage()
        p.save()
        buffer.seek(0)

        arquivo_pdf = SimpleUploadedFile("danfe_rivelli.pdf", buffer.getvalue(), content_type="application/pdf")
        resp = self.client.post(
            '/api/documentos-fiscais-compra/analisar-documento/',
            {'arquivo': arquivo_pdf},
            format='multipart'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get('is_documento_fiscal'))
        dados = resp.data.get('dados_extraidos', {})
        self.assertEqual(dados.get('chave_acesso'), '31260817851981000183550030001573831580908986')
        self.assertEqual(dados.get('cnpj_emitente'), '17851981000183')
        self.assertEqual(dados.get('num_nota'), '157383')
        self.assertEqual(dados.get('data_compra'), '2026-08-12')
        self.assertEqual(dados.get('valor_total'), '19.80')

    # =========================================================================
    # 8. TESTES DE CANCELAMENTO E EDIÇÃO COM RECÁLCULO DE CUSTOS
    # =========================================================================

    def test_cancelar_nota_compra_recalcula_custo_item_para_compra_anterior(self):
        """Ao cancelar uma nota fiscal (Soft Delete), o custo do item é recalculado para a compra anterior."""
        self.client.force_authenticate(user=self.operador_compras)

        # Compra 1: Tubo por R$ 80,00 em 01/08/2026
        doc1 = DocumentoFiscalCompra.objects.create(
            num_nota="NF 101",
            fornecedor=self.fornecedor_acos,
            data_compra=date(2026, 8, 1),
            valor_total=Decimal('80.00')
        )
        NotaCompraItem.objects.create(
            documento_fiscal=doc1,
            item=self.item_tubo,
            quantidade_comprada=Decimal('1.0000'),
            valor_unitario=Decimal('80.0000')
        )

        # Compra 2: Tubo por R$ 120,00 em 15/08/2026 (atualiza último custo para 120)
        payload2 = {
            "num_nota": "NF 102",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-15",
            "valor_total": "120.00",
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "1.0000",
                    "valor_unitario": "120.0000"
                }
            ]
        }
        res2 = self.client.post('/api/documentos-fiscais-compra/', payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        doc2_id = res2.data['id']

        self.item_tubo.refresh_from_db()
        self.assertEqual(self.item_tubo.ultimo_custo_compra, Decimal('120.00'))

        # Cancela (Soft Delete) a Compra 2
        del_res = self.client.delete(f'/api/documentos-fiscais-compra/{doc2_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        # O item deve voltar a ter o custo da Compra 1 (R$ 80,00)
        self.item_tubo.refresh_from_db()
        self.assertEqual(self.item_tubo.ultimo_custo_compra, Decimal('80.00'))
        self.assertEqual(self.item_tubo.data_ultima_compra.date(), date(2026, 8, 1))

    def test_cancelar_unica_compra_zera_data_ultima_compra(self):
        """Ao cancelar a única compra de um insumo, a data da última compra é limpa."""
        self.client.force_authenticate(user=self.operador_compras)

        payload = {
            "num_nota": "NF 777",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-25",
            "valor_total": "95.00",
            "itens_comprados": [
                {
                    "item_id": self.item_arame.id,
                    "quantidade_comprada": "1.0000",
                    "valor_unitario": "95.0000"
                }
            ]
        }
        res = self.client.post('/api/documentos-fiscais-compra/', payload, format='json')
        doc_id = res.data['id']

        del_res = self.client.delete(f'/api/documentos-fiscais-compra/{doc_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        self.item_arame.refresh_from_db()
        self.assertIsNone(self.item_arame.data_ultima_compra)

    def test_editar_nota_compra_recalcula_custo(self):
        """Edição completa de nota de compra via PUT atualiza cabeçalho, itens e recalcula custos."""
        self.client.force_authenticate(user=self.operador_compras)

        payload_original = {
            "num_nota": "NF 555",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-10",
            "valor_total": "100.00",
            "itens_comprados": [
                {
                    "item_id": self.item_tubo.id,
                    "quantidade_comprada": "1.0000",
                    "valor_unitario": "100.0000"
                }
            ]
        }
        res = self.client.post('/api/documentos-fiscais-compra/', payload_original, format='json')
        doc_id = res.data['id']

        # Altera a nota: troca o item para arame e altera número da nota
        payload_edit = {
            "num_nota": "NF 555-EDITADA",
            "fornecedor_id": self.fornecedor_acos.id,
            "data_compra": "2026-08-12",
            "valor_total": "45.00",
            "itens_comprados": [
                {
                    "item_id": self.item_arame.id,
                    "quantidade_comprada": "1.0000",
                    "valor_unitario": "45.0000"
                }
            ]
        }
        res_edit = self.client.put(f'/api/documentos-fiscais-compra/{doc_id}/', payload_edit, format='json')
        self.assertEqual(res_edit.status_code, status.HTTP_200_OK)
        self.assertEqual(res_edit.data['num_nota'], "NF 555-EDITADA")

        # Verifica arame atualizado para 45.00
        self.item_arame.refresh_from_db()
        self.assertEqual(self.item_arame.ultimo_custo_compra, Decimal('45.00'))
        self.assertEqual(self.item_arame.data_ultima_compra.date(), date(2026, 8, 12))

        # Tubo que saiu da nota não tem mais compras ativas, sua data é limpa
        self.item_tubo.refresh_from_db()
        self.assertIsNone(self.item_tubo.data_ultima_compra)


