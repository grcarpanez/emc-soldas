"""
Roteamento da API REST para o módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4 e Fase 10).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.financeiro.views import (
    CategoriaFinanceiraViewSet,
    ContaBancariaViewSet,
    MeioPagamentoViewSet,
    RegraPagamentoViewSet,
    CartaoCreditoViewSet,
    FaturaCartaoViewSet,
    LancamentoFinanceiroViewSet,
    LogEstornoViewSet
)

app_name = 'financeiro'

router = DefaultRouter()
router.register(r'categorias-financeiras', CategoriaFinanceiraViewSet, basename='categorias-financeiras')
router.register(r'contas-bancarias', ContaBancariaViewSet, basename='contas-bancarias')
router.register(r'meios-pagamento', MeioPagamentoViewSet, basename='meios-pagamento')
router.register(r'regras-pagamento', RegraPagamentoViewSet, basename='regras-pagamento')
router.register(r'cartoes-credito', CartaoCreditoViewSet, basename='cartoes-credito')
router.register(r'faturas-cartao', FaturaCartaoViewSet, basename='faturas-cartao')
router.register(r'lancamentos-financeiros', LancamentoFinanceiroViewSet, basename='lancamentos-financeiros')
router.register(r'log-estornos', LogEstornoViewSet, basename='log-estornos')

urlpatterns = [
    path('', include(router.urls)),
]
