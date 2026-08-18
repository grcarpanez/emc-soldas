"""
Roteamento da API REST para o módulo de Catálogo, Dicionários Centrais, Itens, Produtos e Motor BOM.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fases 4 e 6).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalogo.views import (
    DicionarioUomViewSet,
    DicionarioAtributoViewSet,
    ItemViewSet,
    ItemAtributoValorViewSet,
    ProdutoViewSet,
    FichaTecnicaViewSet
)

app_name = 'catalogo'

router = DefaultRouter()
router.register(r'dicionario-uom', DicionarioUomViewSet, basename='dicionario-uom')
router.register(r'dicionario-atributos', DicionarioAtributoViewSet, basename='dicionario-atributos')
router.register(r'itens', ItemViewSet, basename='itens')
router.register(r'item-atributos-valores', ItemAtributoValorViewSet, basename='item-atributos-valores')
router.register(r'produtos', ProdutoViewSet, basename='produtos')
router.register(r'fichas-tecnicas', FichaTecnicaViewSet, basename='fichas-tecnicas')

urlpatterns = [
    path('', include(router.urls)),
]
