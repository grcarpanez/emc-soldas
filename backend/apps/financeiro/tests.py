"""
Testes automatizados para os cadastros estruturais do Módulo Financeiro (Fase 4).
Valida CRUD, RBAC, Sanitização Universal, Soft Delete e Integridade Referencial.
"""
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario
from apps.financeiro.models import (
    CategoriaFinanceira,
    ContaBancaria,
    MeioPagamento,
    RegraPagamento
)


class CadastrosEstruturaisFinanceiroTestCase(TestCase):
    """Bateria de testes para CategoriaFinanceira, ContaBancaria, MeioPagamento e RegraPagamento."""

    def setUp(self):
        self.client = APIClient()

        # Criação de Usuário Administrador
        self.admin = Usuario.objects.create_user(
            email="admin.fin@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        # Criação de Usuário Operador sem permissão
        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem.fin@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        # Criação de Usuário Operador com permissão de Cadastros Financeiros
        self.operador_com_permissao = Usuario.objects.create_user(
            email="operador.fin@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_com_permissao.permissoes.cadastros_financeiros = True
        self.operador_com_permissao.permissoes.save()

    # ==================== CATEGORIAS FINANCEIRAS ====================

    def test_categoria_unauthenticated_and_forbidden(self):
        """Valida 401 para anônimo e 403 para operador sem toggle."""
        response = self.client.get('/api/categorias-financeiras/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/categorias-financeiras/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_categoria_crud_sanitization_and_hierarchy(self):
        """Valida criação, sanitização e hierarquia de CategoriaFinanceira."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        # 1. Criação de Categoria Pai
        payload_pai = {
            "nome": "Despesas Operacionais e Produção",
            "tipo": "DESPESA"
        }
        response_pai = self.client.post('/api/categorias-financeiras/', payload_pai, format='json')
        self.assertEqual(response_pai.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_pai.data['nome'], "DESPESAS OPERACIONAIS E PRODUCAO")
        pai_id = response_pai.data['id']

        # 2. Criação de Subcategoria
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

        # 3. Bloqueio de exclusão do Pai pois possui subcategoria ativa
        response_del_pai = self.client.delete(f'/api/categorias-financeiras/{pai_id}/')
        self.assertEqual(response_del_pai.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("subcategorias", str(response_del_pai.data))

        # 4. Soft Delete da Filha
        response_del_filha = self.client.delete(f'/api/categorias-financeiras/{filha_id}/')
        self.assertEqual(response_del_filha.status_code, status.HTTP_204_NO_CONTENT)

        # 5. Agora o Pai pode ser excluído logicamente
        response_del_pai_ok = self.client.delete(f'/api/categorias-financeiras/{pai_id}/')
        self.assertEqual(response_del_pai_ok.status_code, status.HTTP_204_NO_CONTENT)

        # Verifica soft delete no banco
        cat_db = CategoriaFinanceira.all_objects.get(id=pai_id)
        self.assertIsNotNone(cat_db.deleted_at)
        self.assertEqual(cat_db.deleted_by_id, self.operador_com_permissao.id)

    def test_categoria_anti_cycle_validation(self):
        """Valida que uma categoria não pode ser pai de si mesma."""
        self.client.force_authenticate(user=self.admin)

        cat = CategoriaFinanceira.objects.create(
            nome="RECEITA DE SERVICOS",
            tipo="RECEITA"
        )

        response = self.client.patch(
            f'/api/categorias-financeiras/{cat.id}/',
            {"categoria_pai": cat.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ==================== CONTAS BANCÁRIAS ====================

    def test_conta_bancaria_crud_and_validations(self):
        """Valida criação, sanitização e regras de cheque especial em ContaBancaria."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        # 1. Criação com limite de cheque especial
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

        # 2. Rejeição de limite negativo
        response_neg = self.client.patch(
            f'/api/contas-bancarias/{conta_id}/',
            {"limite_credito": "-500.00"},
            format='json'
        )
        self.assertEqual(response_neg.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Soft Delete
        response_delete = self.client.delete(f'/api/contas-bancarias/{conta_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        conta_db = ContaBancaria.all_objects.get(id=conta_id)
        self.assertIsNotNone(conta_db.deleted_at)

    # ==================== MEIOS DE PAGAMENTO ====================

    def test_meio_pagamento_crud_and_uniqueness(self):
        """Valida CRUD e unicidade de MeioPagamento."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        payload = {
            "nome": "Cartão de Crédito - Maquininha Stone",
            "permite_taxa_maquininha": True,
            "ativo": True
        }
        response = self.client.post('/api/meios-pagamento/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], "CARTAO DE CREDITO - MAQUININHA STONE")
        self.assertTrue(response.data['permite_taxa_maquininha'])
        meio_id = response.data['id']

        # Duplicidade
        response_dup = self.client.post('/api/meios-pagamento/', payload, format='json')
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # Soft delete
        response_delete = self.client.delete(f'/api/meios-pagamento/{meio_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

    # ==================== REGRAS DE PAGAMENTO ====================

    def test_regra_pagamento_crud_and_business_rules(self):
        """Valida criação e regras comerciais de RegraPagamento."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        meio = MeioPagamento.objects.create(
            nome="BOLETO BANCARIO",
            permite_taxa_maquininha=False
        )

        # 1. Criação de Regra Parcelada
        payload_parcelado = {
            "nome": "Boleto 30 / 60 / 90 Dias (3x)",
            "meio_pagamento": meio.id,
            "tipo_cobranca": "PARCELADO",
            "numero_parcelas": 3,
            "prazo_primeira_parcela_dias": 30,
            "intervalo_parcelas_dias": 30,
            "desconto_concedido_padrao": "0.00",
            "ativo": True
        }
        response_parc = self.client.post('/api/regras-pagamento/', payload_parcelado, format='json')
        self.assertEqual(response_parc.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_parc.data['nome'], "BOLETO 30 / 60 / 90 DIAS (3X)")
        self.assertEqual(response_parc.data['numero_parcelas'], 3)
        regra_id = response_parc.data['id']

        # 2. Rejeição de regra À Vista com mais de 1 parcela
        payload_invalido = {
            "nome": "Pix com Parcelas Invalidas",
            "meio_pagamento": meio.id,
            "tipo_cobranca": "A_VISTA",
            "numero_parcelas": 2,
            "desconto_concedido_padrao": "5.00"
        }
        response_inv = self.client.post('/api/regras-pagamento/', payload_invalido, format='json')
        self.assertEqual(response_inv.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Rejeição de desconto fora do intervalo (ex: 150%)
        payload_desc_inv = {
            "nome": "Desconto Impossivel",
            "meio_pagamento": meio.id,
            "tipo_cobranca": "A_VISTA",
            "numero_parcelas": 1,
            "desconto_concedido_padrao": "150.00"
        }
        response_desc = self.client.post('/api/regras-pagamento/', payload_desc_inv, format='json')
        self.assertEqual(response_desc.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Bloqueio de exclusão do Meio de Pagamento que possui regra ativa
        response_del_meio = self.client.delete(f'/api/meios-pagamento/{meio.id}/')
        self.assertEqual(response_del_meio.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Soft Delete da Regra
        response_del_regra = self.client.delete(f'/api/regras-pagamento/{regra_id}/')
        self.assertEqual(response_del_regra.status_code, status.HTTP_204_NO_CONTENT)
