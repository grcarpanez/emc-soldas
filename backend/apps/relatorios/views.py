"""
Views e ViewSets da Central de Relatórios Estratégicos e Dashboard do sistema EMC Soldas.
Aplica controle de acesso RBAC (HasRelatoriosAccess), Rate Limiting para relatórios pesados (heavy_reports)
e entrega respostas analíticas em JSON, PDF profissional e planilhas CSV estruturadas.
"""
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from core.permissions import HasRelatoriosAccess
from apps.relatorios.services import (
    DashboardService, InadimplenciaService, DossieClienteService,
    CurvaABCService, DREService, DivergenciasConciliacaoService
)
from apps.relatorios.serializers import FiltroPeriodoSerializer
from core.reports.pdf_generator import (
    gerar_pdf_inadimplencia, gerar_pdf_dossie_cliente,
    gerar_pdf_curva_abc_clientes, gerar_pdf_curva_abc_itens,
    gerar_pdf_dre, gerar_pdf_divergencias_conciliacao
)
from core.reports.csv_generator import (
    gerar_csv_inadimplencia, gerar_csv_dossie_cliente,
    gerar_csv_curva_abc_clientes, gerar_csv_curva_abc_itens,
    gerar_csv_dre, gerar_csv_divergencias_conciliacao
)


class BaseExportAPIView(APIView):
    """View base para exportações de relatórios com throttling restritivo e RBAC."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'heavy_reports'


# ==============================================================================
# 1. DASHBOARD PRINCIPAL (FLIP CARDS, GRÁFICOS E FEED)
# ==============================================================================

class DashboardFlipCardsView(APIView):
    """Retorna os dados analíticos consolidados dos 5 Flip Cards interativos."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = DashboardService.obter_flip_cards(data_inicio, data_fim)
        return Response(dados, status=status.HTTP_200_OK)


class DashboardGraficosView(APIView):
    """Retorna a evolução de Receitas vs Despesas (12 meses do ano)."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        ano = request.query_params.get('ano')
        dados = DashboardService.obter_graficos_receitas_despesas(ano)
        return Response(dados, status=status.HTTP_200_OK)


class DashboardFeedView(APIView):
    """Retorna a linha do tempo cronológica com atividades recentes da oficina."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        limite = int(request.query_params.get('limite', 20))
        dados = DashboardService.obter_feed_atividades(limite)
        return Response(dados, status=status.HTTP_200_OK)


# ==============================================================================
# 2. RELATÓRIO DE INADIMPLÊNCIA
# ==============================================================================

class RelatorioInadimplenciaView(APIView):
    """Painel analítico em tela de faturas e títulos vencidos em aberto."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        dados = InadimplenciaService.gerar_relatorio()
        return Response(dados, status=status.HTTP_200_OK)


class RelatorioInadimplenciaExportPDFView(BaseExportAPIView):
    """Exportação do Relatório de Inadimplência em PDF."""

    def get(self, request):
        dados = InadimplenciaService.gerar_relatorio()
        pdf_bytes = gerar_pdf_inadimplencia(dados)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_inadimplencia.pdf"'
        return response


class RelatorioInadimplenciaExportCSVView(BaseExportAPIView):
    """Exportação do Relatório de Inadimplência em CSV."""

    def get(self, request):
        dados = InadimplenciaService.gerar_relatorio()
        csv_bytes = gerar_csv_inadimplencia(dados)

        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="relatorio_inadimplencia.csv"'
        return response


# ==============================================================================
# 3. DOSSIÊ DO CLIENTE
# ==============================================================================

class DossieClienteView(APIView):
    """Visão analítica completa do cliente com segregação de produtos e serviços."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request, cliente_id):
        dados = DossieClienteService.gerar_dossie(cliente_id)
        if not dados:
            return Response(
                {'status': 'error', 'message': 'Cliente não localizado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(dados, status=status.HTTP_200_OK)


class DossieClienteExportPDFView(BaseExportAPIView):
    """Exportação do Dossiê do Cliente em PDF."""

    def get(self, request, cliente_id):
        dados = DossieClienteService.gerar_dossie(cliente_id)
        if not dados:
            return Response(
                {'status': 'error', 'message': 'Cliente não localizado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        pdf_bytes = gerar_pdf_dossie_cliente(dados)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="dossie_cliente_{cliente_id}.pdf"'
        return response


class DossieClienteExportCSVView(BaseExportAPIView):
    """Exportação do Dossiê do Cliente em CSV."""

    def get(self, request, cliente_id):
        dados = DossieClienteService.gerar_dossie(cliente_id)
        if not dados:
            return Response(
                {'status': 'error', 'message': 'Cliente não localizado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        csv_bytes = gerar_csv_dossie_cliente(dados)
        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="dossie_cliente_{cliente_id}.csv"'
        return response


# ==============================================================================
# 4. CURVA ABC DE CLIENTES
# ==============================================================================

class CurvaABCClientesView(APIView):
    """Classificação de clientes por relevância de faturamento (80/15/5%)."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_clientes(data_inicio, data_fim)
        return Response(dados, status=status.HTTP_200_OK)


class CurvaABCClientesExportPDFView(BaseExportAPIView):
    """Exportação da Curva ABC de Clientes em PDF."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_clientes(data_inicio, data_fim)
        pdf_bytes = gerar_pdf_curva_abc_clientes(dados)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="curva_abc_clientes.pdf"'
        return response


class CurvaABCClientesExportCSVView(BaseExportAPIView):
    """Exportação da Curva ABC de Clientes em CSV."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_clientes(data_inicio, data_fim)
        csv_bytes = gerar_csv_curva_abc_clientes(dados)

        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="curva_abc_clientes.csv"'
        return response


# ==============================================================================
# 5. CURVA ABC DE CONSUMO DE ITENS
# ==============================================================================

class CurvaABCItensView(APIView):
    """Classificação de consumo de insumos/materiais por custo acumulado."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_itens(data_inicio, data_fim)
        return Response(dados, status=status.HTTP_200_OK)


class CurvaABCItensExportPDFView(BaseExportAPIView):
    """Exportação da Curva ABC de Consumo de Itens em PDF."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_itens(data_inicio, data_fim)
        pdf_bytes = gerar_pdf_curva_abc_itens(dados)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="curva_abc_itens.pdf"'
        return response


class CurvaABCItensExportCSVView(BaseExportAPIView):
    """Exportação da Curva ABC de Consumo de Itens em CSV."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        dados = CurvaABCService.calcular_curva_abc_itens(data_inicio, data_fim)
        csv_bytes = gerar_csv_curva_abc_itens(dados)

        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="curva_abc_itens.csv"'
        return response


# ==============================================================================
# 6. DRE SIMPLIFICADO
# ==============================================================================

class DRESimplificadoView(APIView):
    """Demonstrativo de Resultados do Exercício agrupado por Categoria."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        regime = serializer.validated_data.get('regime', 'competencia')

        dados = DREService.gerar_dre_simplificado(data_inicio, data_fim, regime)
        return Response(dados, status=status.HTTP_200_OK)


class DRESimplificadoExportPDFView(BaseExportAPIView):
    """Exportação do DRE em PDF."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        regime = serializer.validated_data.get('regime', 'competencia')

        dados = DREService.gerar_dre_simplificado(data_inicio, data_fim, regime)
        pdf_bytes = gerar_pdf_dre(dados)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="dre_simplificado.pdf"'
        return response


class DRESimplificadoExportCSVView(BaseExportAPIView):
    """Exportação do DRE em CSV."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        regime = serializer.validated_data.get('regime', 'competencia')

        dados = DREService.gerar_dre_simplificado(data_inicio, data_fim, regime)
        csv_bytes = gerar_csv_dre(dados)

        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="dre_simplificado.csv"'
        return response


# ==============================================================================
# 7. DIVERGÊNCIAS DE CONCILIAÇÃO BANCÁRIA
# ==============================================================================

class DivergenciasConciliacaoView(APIView):
    """Painel de auditoria de sobras do extrato e sobras do ERP."""
    permission_classes = [IsAuthenticated, HasRelatoriosAccess]

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        conta_id = serializer.validated_data.get('conta_id')

        dados = DivergenciasConciliacaoService.gerar_relatorio(conta_id, data_inicio, data_fim)
        return Response(dados, status=status.HTTP_200_OK)


class DivergenciasConciliacaoExportPDFView(BaseExportAPIView):
    """Exportação do Relatório de Divergências de Conciliação em PDF."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        conta_id = serializer.validated_data.get('conta_id')

        dados = DivergenciasConciliacaoService.gerar_relatorio(conta_id, data_inicio, data_fim)
        pdf_bytes = gerar_pdf_divergencias_conciliacao(dados)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="divergencias_conciliacao.pdf"'
        return response


class DivergenciasConciliacaoExportCSVView(BaseExportAPIView):
    """Exportação do Relatório de Divergências de Conciliação em CSV."""

    def get(self, request):
        serializer = FiltroPeriodoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')
        conta_id = serializer.validated_data.get('conta_id')

        dados = DivergenciasConciliacaoService.gerar_relatorio(conta_id, data_inicio, data_fim)
        csv_bytes = gerar_csv_divergencias_conciliacao(dados)

        response = HttpResponse(csv_bytes, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="divergencias_conciliacao.csv"'
        return response
