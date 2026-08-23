"""
Roteador de URLs para a Central de Relatórios e Dashboard do sistema EMC Soldas.
Rotas padronizadas em kebab-case conforme o FSD.
"""
from django.urls import path
from apps.relatorios.views import (
    DashboardFlipCardsView, DashboardGraficosView, DashboardFeedView,
    RelatorioInadimplenciaView, RelatorioInadimplenciaExportPDFView, RelatorioInadimplenciaExportCSVView,
    DossieClienteView, DossieClienteExportPDFView, DossieClienteExportCSVView,
    CurvaABCClientesView, CurvaABCClientesExportPDFView, CurvaABCClientesExportCSVView,
    CurvaABCItensView, CurvaABCItensExportPDFView, CurvaABCItensExportCSVView,
    DRESimplificadoView, DRESimplificadoExportPDFView, DRESimplificadoExportCSVView,
    DivergenciasConciliacaoView, DivergenciasConciliacaoExportPDFView, DivergenciasConciliacaoExportCSVView
)

app_name = 'relatorios'

urlpatterns = [
    # 1. Dashboard Principal
    path('dashboard/flip-cards/', DashboardFlipCardsView.as_view(), name='dashboard-flip-cards'),
    path('dashboard/graficos/', DashboardGraficosView.as_view(), name='dashboard-graficos'),
    path('dashboard/feed/', DashboardFeedView.as_view(), name='dashboard-feed'),

    # 2. Relatório de Inadimplência
    path('relatorios/inadimplencia/', RelatorioInadimplenciaView.as_view(), name='relatorio-inadimplencia'),
    path('relatorios/inadimplencia/exportar-pdf/', RelatorioInadimplenciaExportPDFView.as_view(), name='relatorio-inadimplencia-pdf'),
    path('relatorios/inadimplencia/exportar-csv/', RelatorioInadimplenciaExportCSVView.as_view(), name='relatorio-inadimplencia-csv'),

    # 3. Dossiê do Cliente
    path('relatorios/dossie-cliente/<int:cliente_id>/', DossieClienteView.as_view(), name='dossie-cliente'),
    path('relatorios/dossie-cliente/<int:cliente_id>/exportar-pdf/', DossieClienteExportPDFView.as_view(), name='dossie-cliente-pdf'),
    path('relatorios/dossie-cliente/<int:cliente_id>/exportar-csv/', DossieClienteExportCSVView.as_view(), name='dossie-cliente-csv'),

    # 4. Curva ABC de Clientes
    path('relatorios/curva-abc-clientes/', CurvaABCClientesView.as_view(), name='curva-abc-clientes'),
    path('relatorios/curva-abc-clientes/exportar-pdf/', CurvaABCClientesExportPDFView.as_view(), name='curva-abc-clientes-pdf'),
    path('relatorios/curva-abc-clientes/exportar-csv/', CurvaABCClientesExportCSVView.as_view(), name='curva-abc-clientes-csv'),

    # 5. Curva ABC de Consumo de Itens
    path('relatorios/curva-abc-itens/', CurvaABCItensView.as_view(), name='curva-abc-itens'),
    path('relatorios/curva-abc-itens/exportar-pdf/', CurvaABCItensExportPDFView.as_view(), name='curva-abc-itens-pdf'),
    path('relatorios/curva-abc-itens/exportar-csv/', CurvaABCItensExportCSVView.as_view(), name='curva-abc-itens-csv'),

    # 6. DRE Simplificado
    path('relatorios/dre/', DRESimplificadoView.as_view(), name='dre-simplificado'),
    path('relatorios/dre/exportar-pdf/', DRESimplificadoExportPDFView.as_view(), name='dre-simplificado-pdf'),
    path('relatorios/dre/exportar-csv/', DRESimplificadoExportCSVView.as_view(), name='dre-simplificado-csv'),

    # 7. Divergências de Conciliação Bancária
    path('relatorios/divergencias-conciliacao/', DivergenciasConciliacaoView.as_view(), name='divergencias-conciliacao'),
    path('relatorios/divergencias-conciliacao/exportar-pdf/', DivergenciasConciliacaoExportPDFView.as_view(), name='divergencias-conciliacao-pdf'),
    path('relatorios/divergencias-conciliacao/exportar-csv/', DivergenciasConciliacaoExportCSVView.as_view(), name='divergencias-conciliacao-csv'),
]
