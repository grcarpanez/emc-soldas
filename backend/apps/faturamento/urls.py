"""
Roteamento da API REST para o módulo de Faturamento Agregado.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 9).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.faturamento.views import (
    FaturaViewSet,
    FaturaPropostaPagamentoViewSet
)

app_name = 'faturamento'

router = DefaultRouter()
router.register(r'faturas', FaturaViewSet, basename='faturas')
router.register(r'fatura-propostas-pagamento', FaturaPropostaPagamentoViewSet, basename='fatura-propostas-pagamento')

urlpatterns = [
    path('', include(router.urls)),
]
