"""
Roteador de URLs do módulo de Conciliação Bancária Inteligente Split-Screen.
"""
from django.urls import path
from apps.conciliacao.views import (
    UploadExtratoView,
    ConfirmarConciliacaoView,
    DesconciliarView,
    LancamentoRapidoView,
    TrocarContaView,
    DivergenciasView,
    ImportacaoLoteView
)

app_name = 'conciliacao'

urlpatterns = [
    path('upload-extrato/', UploadExtratoView.as_view(), name='upload-extrato'),
    path('confirmar/', ConfirmarConciliacaoView.as_view(), name='confirmar'),
    path('desconciliar/', DesconciliarView.as_view(), name='desconciliar'),
    path('lancamento-rapido/', LancamentoRapidoView.as_view(), name='lancamento-rapido'),
    path('trocar-conta/', TrocarContaView.as_view(), name='trocar-conta'),
    path('divergencias/', DivergenciasView.as_view(), name='divergencias'),
    path('importacao-lote/', ImportacaoLoteView.as_view(), name='importacao-lote'),
]
