"""
Testes automatizados completos para o módulo de Catálogo, Dicionários Centrais, Itens, Produtos e Motor BOM (Fases 4 e 6).
Valida CRUD, RBAC, Sanitização Universal, Soft Delete, Integridade Referencial, Fator de Conversão e Cálculo do Preço de Custo Apurado.
"""
from decimal import Decimal
from django.test import TestCase
from django.db import transaction
from rest_framework.test import APIClient
from rest_framework import status

from apps.administracao.models import ConfiguracaoGlobal
from apps.authentication.models import Usuario, Permissao
from apps.catalogo.models import (
    DicionarioUom,
    DicionarioAtributo,
    Item,
    ItemAtributoValor,
    Produto,
    FichaTecnica
)


class CatalogoModuleTestCase(TestCase):
    """Suíte completa de testes para Catálogo, Itens, Produtos e Motor BOM."""

    def setUp(self):
        self.client = APIClient()

        # Garante configuração global padrão (taxa de mão de obra R$ 80,00/h)
        self.config = ConfiguracaoGlobal.get_solo()
        self.config.taxa_mao_de_obra_hora = Decimal('80.00')
        self.config.save()

        # 1. Usuário Administrador Master
        self.admin = Usuario.objects.create_user(
            email="admin@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        # 2. Usuário Operador sem permissões
        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        # 3. Usuário Operador com permissão de Dicionário UOM
        self.operador_uom = Usuario.objects.create_user(
            email="operador.uom@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_uom.permissoes.gestao_dicionario_uom = True
        self.operador_uom.permissoes.save()

        # 4. Usuário Operador com permissão de Catálogo (Itens, Produtos e BOM)
        self.operador_catalogo = Usuario.objects.create_user(
            email="operador.catalogo@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_catalogo.permissoes.gestao_catalogo = True
        self.operador_catalogo.permissoes.save()

        # Dados estruturais de apoio
        self.uom_un = DicionarioUom.objects.create(sigla="UN", descricao="UNIDADE")
        self.uom_barra = DicionarioUom.objects.create(sigla="BARRA", descricao="BARRA DE 6 METROS")
        self.uom_metro = DicionarioUom.objects.create(sigla="M", descricao="METRO LINEAR")
        self.uom_cx = DicionarioUom.objects.create(sigla="CX", descricao="CAIXA")
        self.uom_kg = DicionarioUom.objects.create(sigla="KG", descricao="QUILOGRAMA")

        self.attr_espessura = DicionarioAtributo.objects.create(nome_atributo="ESPESSURA")
        self.attr_material = DicionarioAtributo.objects.create(nome_atributo="MATERIAL / LIGA")

    # =========================================================================
    # 1. TESTES DE DICIONÁRIOS (UOM E ATRIBUTOS)
    # =========================================================================

    def test_uom_unauthenticated_access_denied(self):
        """Usuário não autenticado deve receber 401."""
        response = self.client.get('/api/dicionario-uom/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_uom_operador_sem_permissao_access_forbidden(self):
        """Operador sem toggle 'gestao_dicionario_uom' deve receber 403."""
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/dicionario-uom/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_uom_crud_and_sanitization(self):
        """Valida criação com sanitização para maiúsculas sem acento, listagem, edição e soft delete."""
        self.client.force_authenticate(user=self.operador_uom)

        payload = {
            "sigla": "m²",
            "descricao": "Metro Quadrado para Chapas de Aço"
        }
        response = self.client.post('/api/dicionario-uom/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sigla'], "M2")
        self.assertEqual(response.data['descricao'], "METRO QUADRADO PARA CHAPAS DE ACO")

        uom_id = response.data['id']

        # Duplicidade
        response_dup = self.client.post('/api/dicionario-uom/', payload, format='json')
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # Atualização
        patch_payload = {"descricao": "Metro Quadrado Atualizado"}
        response_patch = self.client.patch(f'/api/dicionario-uom/{uom_id}/', patch_payload, format='json')
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(response_patch.data['descricao'], "METRO QUADRADO ATUALIZADO")

        # Soft Delete
        response_delete = self.client.delete(f'/api/dicionario-uom/{uom_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        uom_db = DicionarioUom.all_objects.get(id=uom_id)
        self.assertIsNotNone(uom_db.deleted_at)
        self.assertEqual(uom_db.deleted_by_id, self.operador_uom.id)

    def test_uom_delete_blocked_when_in_use(self):
        """Valida que UOM em uso por Item não pode sofrer soft delete."""
        self.client.force_authenticate(user=self.admin)
        uom = DicionarioUom.objects.create(sigla="LATA", descricao="LATA 18L")
        Item.objects.create(
            nome="TINTA PRIMER",
            unidade_compra=uom,
            unidade_consumo=uom,
            fator_conversao=1.0000,
            ultimo_custo_compra=120.00
        )
        response = self.client.delete(f'/api/dicionario-uom/{uom.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("em uso", str(response.data))

    def test_atributo_crud_and_sanitization(self):
        """Valida CRUD e sanitização de DicionarioAtributo."""
        self.client.force_authenticate(user=self.admin)
        payload = {"nome_atributo": "Rosca / Diâmetro Externo"}
        response = self.client.post('/api/dicionario-atributos/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome_atributo'], "ROSCA / DIAMETRO EXTERNO")

        attr_id = response.data['id']
        response_delete = self.client.delete(f'/api/dicionario-atributos/{attr_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

    # =========================================================================
    # 2. TESTES DE ITENS E ATRIBUTOS TÉCNICOS DINÂMICOS
    # =========================================================================

    def test_item_unauthenticated_access_denied(self):
        """Acesso anônimo a itens deve retornar 401."""
        response = self.client.get('/api/itens/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_item_operador_sem_permissao_access_forbidden(self):
        """Operador sem toggle 'gestao_catalogo' deve receber 403."""
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/itens/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_item_crud_with_nested_attributes_and_sanitization(self):
        """
        Valida criação de Item com sanitização de texto, cálculo de custo unitário de consumo
        e persistência de atributos técnicos dinâmicos aninhados.
        """
        self.client.force_authenticate(user=self.operador_catalogo)

        # Compra: Barra 6m por R$ 60,00 | Consumo: Metro (m) | Fator: 6.0000 -> Custo consumo: R$ 10,0000/m
        payload = {
            "nome": "tubo de aço quadrado 50x50",
            "unidade_compra": self.uom_barra.id,
            "unidade_consumo": self.uom_metro.id,
            "fator_conversao": "6.0000",
            "ultimo_custo_compra": "60.00",
            "tipo_uso": "INSUMO_PRODUTIVO",
            "atributos_valores": [
                {
                    "atributo": self.attr_espessura.id,
                    "valor": "2.0 mm (chapa 14)"
                },
                {
                    "atributo": self.attr_material.id,
                    "valor": "aço carbono sae 1020"
                }
            ]
        }
        response = self.client.post('/api/itens/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], "TUBO DE ACO QUADRADO 50X50")
        self.assertEqual(response.data['unidade_compra_sigla'], "BARRA")
        self.assertEqual(response.data['unidade_consumo_sigla'], "M")
        self.assertEqual(response.data['custo_unitario_consumo'], "10.0000")
        self.assertEqual(response.data['total_produtos_onde_usado'], 0)

        # Valida atributos salvos e sanitizados
        atributos = response.data['atributos_valores']
        self.assertEqual(len(atributos), 2)
        self.assertEqual(atributos[0]['valor'], "2.0 MM (CHAPA 14)")
        self.assertEqual(atributos[1]['valor'], "ACO CARBONO SAE 1020")

        item_id = response.data['id']

        # Atualização (PATCH) alterando preço de compra e atributos
        patch_payload = {
            "ultimo_custo_compra": "90.00",  # R$ 90,00 / 6 = R$ 15,0000/m
            "atributos_valores": [
                {
                    "atributo": self.attr_espessura.id,
                    "valor": "2.25 mm (reforçado)"
                }
            ]
        }
        response_patch = self.client.patch(f'/api/itens/{item_id}/', patch_payload, format='json')
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(response_patch.data['custo_unitario_consumo'], "15.0000")
        self.assertEqual(len(response_patch.data['atributos_valores']), 1)
        self.assertEqual(response_patch.data['atributos_valores'][0]['valor'], "2.25 MM (REFORCADO)")

    def test_item_fator_conversao_invalido(self):
        """Fator de conversão menor ou igual a zero deve ser rejeitado."""
        self.client.force_authenticate(user=self.operador_catalogo)
        payload = {
            "nome": "ARAME MIG ER70S-6",
            "unidade_compra": self.uom_kg.id,
            "fator_conversao": "0.0000",
            "ultimo_custo_compra": "25.00"
        }
        response = self.client.post('/api/itens/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fator_conversao", str(response.data))

    def test_item_ultimo_custo_compra_negativo(self):
        """Custo de compra negativo deve ser rejeitado."""
        self.client.force_authenticate(user=self.operador_catalogo)
        payload = {
            "nome": "DISCO DE CORTE 4.5 POL",
            "unidade_compra": self.uom_un.id,
            "ultimo_custo_compra": "-10.00"
        }
        response = self.client.post('/api/itens/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ultimo_custo_compra", str(response.data))

    # =========================================================================
    # 3. TESTES DE PRODUTOS E MOTOR DE CUSTOS BOM (BILL OF MATERIALS)
    # =========================================================================

    def test_produto_unauthenticated_access_denied(self):
        """Acesso anônimo a produtos deve retornar 401."""
        response = self.client.get('/api/produtos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_produto_operador_sem_permissao_access_forbidden(self):
        """Operador sem toggle 'gestao_catalogo' deve receber 403."""
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/produtos/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_produto_crud_and_motor_bom_calculation(self):
        """
        Valida a matemática precisa do Motor BOM:
        Item 1 (Tubo): Compra Barra 6m = R$ 60,00 | Consumo Metro (m) | Fator = 6 -> R$ 10,00/m. Qtd: 2.5m = R$ 25,00
        Item 2 (Parafuso): Compra Caixa 100 = R$ 50,00 | Consumo UN | Fator = 100 -> R$ 0,50/un. Qtd: 10 un = R$ 5,00
        Custo Total Materiais = R$ 25,00 + R$ 5,00 = R$ 30,00
        Mão de Obra: 1.5 horas * R$ 80,00/h = R$ 120,00
        Preço de Custo Apurado = R$ 30,00 + R$ 120,00 = R$ 150,00
        """
        self.client.force_authenticate(user=self.operador_catalogo)

        item_tubo = Item.objects.create(
            nome="TUBO QUADRADO 50X50",
            unidade_compra=self.uom_barra,
            unidade_consumo=self.uom_metro,
            fator_conversao=Decimal('6.0000'),
            ultimo_custo_compra=Decimal('60.00')
        )
        item_parafuso = Item.objects.create(
            nome="PARAFUSO SEXTAVADO M10",
            unidade_compra=self.uom_cx,
            unidade_consumo=self.uom_un,
            fator_conversao=Decimal('100.0000'),
            ultimo_custo_compra=Decimal('50.00')
        )

        payload_produto = {
            "nome": "grade de proteção para esteira",
            "descricao": "grade metálica sob medida com reforço",
            "unidade_venda": self.uom_un.id,
            "tempo_estimado_execucao": "1.50",
            "ficha_tecnica_itens": [
                {
                    "item": item_tubo.id,
                    "quantidade_utilizada": "2.5000"
                },
                {
                    "item": item_parafuso.id,
                    "quantidade_utilizada": "10.0000"
                }
            ]
        }

        response = self.client.post('/api/produtos/', payload_produto, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome'], "GRADE DE PROTECAO PARA ESTEIRA")
        self.assertEqual(response.data['descricao'], "GRADE METALICA SOB MEDIDA COM REFORCO")
        self.assertEqual(response.data['taxa_mao_de_obra_hora_aplicada'], "80.00")
        self.assertEqual(response.data['custo_total_materiais'], "30.00")
        self.assertEqual(response.data['custo_mao_de_obra'], "120.00")
        self.assertEqual(response.data['preco_custo_apurado'], "150.00")

        produto_id = response.data['id']

        # Testa endpoint de Custo Detalhado (Memória de cálculo auditável)
        response_detalhe = self.client.get(f'/api/produtos/{produto_id}/custo-detalhado/')
        self.assertEqual(response_detalhe.status_code, status.HTTP_200_OK)
        self.assertEqual(response_detalhe.data['tempo_estimado_horas'], "1.50")
        self.assertEqual(response_detalhe.data['taxa_mao_de_obra_hora'], "80.00")
        self.assertEqual(response_detalhe.data['custo_mao_de_obra'], "120.00")
        self.assertEqual(response_detalhe.data['custo_total_materiais'], "30.00")
        self.assertEqual(response_detalhe.data['preco_custo_apurado'], "150.00")
        self.assertEqual(len(response_detalhe.data['materiais']), 2)

        # Testa action de atualizar ficha técnica
        payload_nova_ficha = {
            "itens": [
                {
                    "item": item_tubo.id,
                    "quantidade_utilizada": "4.0000"  # 4 * 10 = R$ 40,00
                }
            ]
        }
        response_update_ficha = self.client.post(
            f'/api/produtos/{produto_id}/atualizar-ficha-tecnica/',
            payload_nova_ficha,
            format='json'
        )
        self.assertEqual(response_update_ficha.status_code, status.HTTP_200_OK)
        self.assertEqual(response_update_ficha.data['custo_total_materiais'], "40.00")
        self.assertEqual(response_update_ficha.data['preco_custo_apurado'], "160.00")  # 40 + 120

    # =========================================================================
    # 4. TESTES DE INTEGRIDADE REFERENCIAL E TRAVAS DE SOFT DELETE
    # =========================================================================

    def test_item_delete_blocked_when_in_active_produto_bom(self):
        """
        Regra Mandatória: Não é permitido excluir (soft delete) um Item caso ele
        conste na Ficha Técnica de um Produto ativo.
        """
        self.client.force_authenticate(user=self.operador_catalogo)

        item = Item.objects.create(
            nome="CHAPA DE ACO INOX 304",
            unidade_compra=self.uom_un,
            fator_conversao=Decimal('1.0000'),
            ultimo_custo_compra=Decimal('200.00')
        )
        produto = Produto.objects.create(
            nome="MESA DE INSPECAO INOX",
            unidade_venda=self.uom_un,
            tempo_estimado_execucao=Decimal('3.00')
        )
        FichaTecnica.objects.create(
            produto=produto,
            item=item,
            quantidade_utilizada=Decimal('2.0000')
        )

        # 1. Verifica no endpoint 'onde-usado'
        response_onde = self.client.get(f'/api/itens/{item.id}/onde-usado/')
        self.assertEqual(response_onde.status_code, status.HTTP_200_OK)
        self.assertEqual(response_onde.data['total_produtos'], 1)
        self.assertEqual(response_onde.data['produtos'][0]['produto_id'], produto.id)

        # 2. Tenta deletar o item -> Deve ser BLOQUEADO com 400 Bad Request
        response_delete = self.client.delete(f'/api/itens/{item.id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("MESA DE INSPECAO INOX", str(response_delete.data))

        # 3. Inativa o produto (soft delete do Produto)
        produto.delete(user_id=self.operador_catalogo.id)

        # 4. Tenta deletar o item novamente -> Agora deve PERMITIR com 204 No Content
        response_delete_ok = self.client.delete(f'/api/itens/{item.id}/')
        self.assertEqual(response_delete_ok.status_code, status.HTTP_204_NO_CONTENT)

        item_db = Item.all_objects.get(id=item.id)
        self.assertIsNotNone(item_db.deleted_at)
        self.assertEqual(item_db.deleted_by_id, self.operador_catalogo.id)

    def test_ficha_tecnica_item_duplicado_bloqueado(self):
        """Não permite cadastrar o mesmo item duas vezes na ficha técnica do mesmo produto."""
        self.client.force_authenticate(user=self.operador_catalogo)

        item = Item.objects.create(
            nome="ELETRODO E7018",
            unidade_compra=self.uom_kg,
            ultimo_custo_compra=Decimal('30.00')
        )
        produto = Produto.objects.create(
            nome="ESTRUTURA METALICA",
            unidade_venda=self.uom_un
        )

        payload_duplicado = {
            "produto": produto.id,
            "item": item.id,
            "quantidade_utilizada": "1.0000"
        }
        res1 = self.client.post('/api/fichas-tecnicas/', payload_duplicado, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post('/api/fichas-tecnicas/', payload_duplicado, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
