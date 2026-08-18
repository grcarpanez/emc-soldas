"""
Roteamento da API REST para o módulo de Cadastros Básicos e Utilitários.
Em conformidade com docs/FSD.md e docs/PLANO.md.
"""
from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from apps.cadastros.views import (
    ClienteFornecedorViewSet,
    EquipamentoViewSet,
    ClienteEquipamentoViewSet,
    AnexoGeralClienteViewSet,
    ConsultaCnpjAPIView,
    VerificarDocumentoAPIView
)

app_name = 'cadastros'

router = DefaultRouter()
router.register(r'clientes-fornecedores', ClienteFornecedorViewSet, basename='clientes-fornecedores')
router.register(r'equipamentos', EquipamentoViewSet, basename='equipamentos')
router.register(r'cliente-equipamentos', ClienteEquipamentoViewSet, basename='cliente-equipamentos')
router.register(r'anexos-gerais-clientes', AnexoGeralClienteViewSet, basename='anexos-gerais-clientes')

urlpatterns = [
    # Rotas dos ViewSets principais
    path('', include(router.urls)),

    # Rotas utilitárias de validação e consultas públicas
    re_path(r'^utilitarios/consulta-cnpj/(?P<cnpj>.+?)/?$', ConsultaCnpjAPIView.as_view(), name='consulta-cnpj'),
    path('utilitarios/verificar-documento/', VerificarDocumentoAPIView.as_view(), name='verificar-documento'),
]
