"""
Roteamento da API REST para o módulo de Compras, Notas Fiscais de Entrada e Retroalimentação de Custos.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 7).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.compras.views import DocumentoFiscalCompraViewSet, NotaCompraItemViewSet

app_name = 'compras'

router = DefaultRouter()
router.register(r'documentos-fiscais-compra', DocumentoFiscalCompraViewSet, basename='documentos-fiscais-compra')
router.register(r'nota-compra-itens', NotaCompraItemViewSet, basename='nota-compra-itens')

urlpatterns = [
    path('', include(router.urls)),
]
