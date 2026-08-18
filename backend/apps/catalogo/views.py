"""
Views e ViewSets do Catálogo Base e Dicionários Centrais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4).
"""
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.catalogo.models import (
    DicionarioUom,
    DicionarioAtributo,
    Item,
    Produto,
    ItemAtributoValor
)
from apps.catalogo.serializers import (
    DicionarioUomSerializer,
    DicionarioAtributoSerializer
)
from core.permissions import HasDicionarioUomAccess


class DicionarioUomViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Dicionário Central de Unidades de Medida (UOM).
    Protegido pelo toggle 'gestao_dicionario_uom' e governança de Soft Delete.
    """
    queryset = DicionarioUom.objects.all()
    serializer_class = DicionarioUomSerializer
    permission_classes = [HasDicionarioUomAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sigla', 'descricao']
    ordering_fields = ['sigla', 'descricao', 'id', 'created_at']
    ordering = ['sigla']

    def perform_destroy(self, instance):
        # Valida se a unidade está vinculada a itens ou produtos ativos
        itens_compra = Item.objects.filter(unidade_compra=instance).exists()
        itens_consumo = Item.objects.filter(unidade_consumo=instance).exists()
        produtos_venda = Produto.objects.filter(unidade_venda=instance).exists()

        if itens_compra or itens_consumo or produtos_venda:
            raise ValidationError(
                "Não é possível inativar esta Unidade de Medida pois ela está em uso por itens ou produtos do catálogo."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class DicionarioAtributoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Catálogo Central de Atributos Técnicos.
    Protegido pelo toggle 'gestao_dicionario_uom' e governança de Soft Delete.
    """
    queryset = DicionarioAtributo.objects.all()
    serializer_class = DicionarioAtributoSerializer
    permission_classes = [HasDicionarioUomAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome_atributo']
    ordering_fields = ['nome_atributo', 'id', 'created_at']
    ordering = ['nome_atributo']

    def perform_destroy(self, instance):
        # Valida se o atributo está em uso em itens ativos
        if ItemAtributoValor.objects.filter(atributo=instance).exists():
            raise ValidationError(
                "Não é possível inativar este Atributo Técnico pois ele está vinculado a especificações de itens existentes."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)
