"""
Roteamento da API REST para o módulo de Catálogo e Dicionários Centrais.
Em conformidade com docs/FSD.md e docs/PLANO.md.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.catalogo.views import (
    DicionarioUomViewSet,
    DicionarioAtributoViewSet
)

app_name = 'catalogo'

router = DefaultRouter()
router.register(r'dicionario-uom', DicionarioUomViewSet, basename='dicionario-uom')
router.register(r'dicionario-atributos', DicionarioAtributoViewSet, basename='dicionario-atributos')

urlpatterns = [
    path('', include(router.urls)),
]
