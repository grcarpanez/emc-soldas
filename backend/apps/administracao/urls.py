"""
Roteamento das APIs REST do Módulo de Administração.
Em conformidade com docs/FSD.md - Kebab-case plural e endpoints padronizados:
- /api/configuracoes-globais/
- /api/controle-arquivos-log/
- /api/lixeira/
- /api/logs/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ConfiguracaoGlobalViewSet,
    ControleArquivoLogViewSet,
    LogViewerView,
    LixeiraViewSet
)

app_name = 'administracao'

router = DefaultRouter()
router.register(r'configuracoes-globais', ConfiguracaoGlobalViewSet, basename='configuracoes-globais')
router.register(r'controle-arquivos-log', ControleArquivoLogViewSet, basename='controle-arquivos-log')
router.register(r'lixeira', LixeiraViewSet, basename='lixeira')

urlpatterns = [
    path('', include(router.urls)),
    path('logs/', LogViewerView.as_view(), name='log-viewer-direto'),
]
