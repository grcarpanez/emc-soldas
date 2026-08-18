"""
Testes automatizados para o módulo de Catálogo e Dicionários Centrais (Fase 4).
Valida CRUD, RBAC, Sanitização Universal, Soft Delete e Integridade Referencial.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario, Permissao
from apps.catalogo.models import (
    DicionarioUom,
    DicionarioAtributo,
    Item,
    ItemAtributoValor
)


class DicionariosCatalogoTestCase(TestCase):
    """Bateria de testes para DicionarioUom e DicionarioAtributo."""

    def setUp(self):
        self.client = APIClient()

        # Criação de Usuário Administrador
        self.admin = Usuario.objects.create_user(
            email="admin@emcsoldas.com.br",
            password="adminpassword123",
            role="Admin"
        )

        # Criação de Usuário Operador sem permissão
        self.operador_sem_permissao = Usuario.objects.create_user(
            email="operador.sem@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )

        # Criação de Usuário Operador com permissão de Dicionário UOM
        self.operador_com_permissao = Usuario.objects.create_user(
            email="operador.uom@emcsoldas.com.br",
            password="operadorpassword123",
            role="Operador"
        )
        self.operador_com_permissao.permissoes.gestao_dicionario_uom = True
        self.operador_com_permissao.permissoes.save()

    def test_uom_unauthenticated_access_denied(self):
        """Usuário não autenticado deve receber 401."""
        response = self.client.get('/api/dicionario-uom/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_uom_operador_sem_permissao_access_forbidden(self):
        """Operador sem o toggle 'gestao_dicionario_uom' deve receber 403."""
        self.client.force_authenticate(user=self.operador_sem_permissao)
        response = self.client.get('/api/dicionario-uom/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_uom_crud_and_sanitization(self):
        """Valida criação com sanitização para maiúsculas sem acento, listagem, edição e soft delete."""
        self.client.force_authenticate(user=self.operador_com_permissao)

        # 1. Criação com caracteres minúsculos e acentuados
        payload = {
            "sigla": "m²",
            "descricao": "Metro Quadrado para Chapas de Aço"
        }
        response = self.client.post('/api/dicionario-uom/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sigla'], "M2")
        self.assertEqual(response.data['descricao'], "METRO QUADRADO PARA CHAPAS DE ACO")

        uom_id = response.data['id']

        # 2. Validação de Unicidade
        response_dup = self.client.post('/api/dicionario-uom/', payload, format='json')
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Atualização (PATCH)
        patch_payload = {"descricao": "Metro Quadrado Atualizado"}
        response_patch = self.client.patch(f'/api/dicionario-uom/{uom_id}/', patch_payload, format='json')
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(response_patch.data['descricao'], "METRO QUADRADO ATUALIZADO")

        # 4. Soft Delete
        response_delete = self.client.delete(f'/api/dicionario-uom/{uom_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        # 5. Verifica se não aparece mais na listagem ativa
        response_list = self.client.get('/api/dicionario-uom/')
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response_list.data['results']] if 'results' in response_list.data else [item['id'] for item in response_list.data]
        self.assertNotIn(uom_id, ids)

        # 6. Verifica persistência no banco com soft delete
        uom_db = DicionarioUom.all_objects.get(id=uom_id)
        self.assertIsNotNone(uom_db.deleted_at)
        self.assertEqual(uom_db.deleted_by_id, self.operador_com_permissao.id)

    def test_uom_delete_blocked_when_in_use(self):
        """Valida que uma UOM em uso por Item não pode sofrer soft delete."""
        self.client.force_authenticate(user=self.admin)

        uom = DicionarioUom.objects.create(sigla="KG", descricao="QUILOGRAMA")
        item = Item.objects.create(
            nome="ARAME DE SOLDA MIG",
            unidade_compra=uom,
            unidade_consumo=uom,
            fator_conversao=1.0000,
            ultimo_custo_compra=45.00
        )

        response = self.client.delete(f'/api/dicionario-uom/{uom.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("em uso", str(response.data))

    def test_atributo_crud_and_sanitization(self):
        """Valida CRUD e sanitização de DicionarioAtributo."""
        self.client.force_authenticate(user=self.admin)

        # 1. Criação
        payload = {"nome_atributo": "Espessura da Chapa (Polegadas / mm)"}
        response = self.client.post('/api/dicionario-atributos/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome_atributo'], "ESPESSURA DA CHAPA (POLEGADAS / MM)")

        attr_id = response.data['id']

        # 2. Unicidade
        response_dup = self.client.post('/api/dicionario-atributos/', payload, format='json')
        self.assertEqual(response_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Soft Delete
        response_delete = self.client.delete(f'/api/dicionario-atributos/{attr_id}/')
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        attr_db = DicionarioAtributo.all_objects.get(id=attr_id)
        self.assertIsNotNone(attr_db.deleted_at)
