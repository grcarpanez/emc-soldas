"""
Roteamento da API REST para o módulo de Orçamentos Comerciais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 8).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.orcamentos.views import (
    OrcamentoViewSet,
    OrcamentoItemViewSet,
    OrcamentoPropostaPagamentoViewSet
)

app_name = 'orcamentos'

router = DefaultRouter()
router.register(r'orcamentos', OrcamentoViewSet, basename='orcamentos')
router.register(r'orcamento-itens', OrcamentoItemViewSet, basename='orcamento-itens')
router.register(r'orcamento-propostas-pagamento', OrcamentoPropostaPagamentoViewSet, basename='orcamento-propostas-pagamento')

urlpatterns = [
    path('', include(router.urls)),
]
