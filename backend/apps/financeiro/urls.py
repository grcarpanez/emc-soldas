"""
Roteamento da API REST para o módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.financeiro.views import (
    CategoriaFinanceiraViewSet,
    ContaBancariaViewSet,
    MeioPagamentoViewSet,
    RegraPagamentoViewSet
)

app_name = 'financeiro'

router = DefaultRouter()
router.register(r'categorias-financeiras', CategoriaFinanceiraViewSet, basename='categorias-financeiras')
router.register(r'contas-bancarias', ContaBancariaViewSet, basename='contas-bancarias')
router.register(r'meios-pagamento', MeioPagamentoViewSet, basename='meios-pagamento')
router.register(r'regras-pagamento', RegraPagamentoViewSet, basename='regras-pagamento')

urlpatterns = [
    path('', include(router.urls)),
]
