"""
Views e ViewSets da Central Administrativa.
Contempla:
- ConfiguracaoGlobalViewSet (Singleton, Presets SMTP, Teste em Tempo Real)
- ControleArquivoLogViewSet (Manifesto, Sincronização, Expurgo com Backup por E-mail)
- LogViewerView (Visualizador Seguro de Logs com anti-path traversal)
- LixeiraViewSet (Lixeira Unificada com Segregação e Restauração Lógica)
"""
import logging
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from core.permissions import (
    HasConfiguracoesGlobaisAccess,
    HasAuditoriaLogsAccess,
    HasGestaoEquipeAccess,
    IsAdminUserRole
)
from .models import ConfiguracaoGlobal, ControleArquivoLog
from .serializers import (
    ConfiguracaoGlobalSerializer,
    TesteSmtpSerializer,
    ControleArquivoLogSerializer,
    LogViewerFilterSerializer,
    LixeiraItemSerializer,
    ExpurgoLogRequestSerializer
)
from .services import (
    obter_presets_smtp,
    testar_conexao_smtp,
    sincronizar_manifesto_logs,
    expurgar_arquivos_log,
    ler_arquivo_log_seguro,
    listar_arquivos_log_disponiveis,
    LixeiraService
)

logger = logging.getLogger('emc_soldas')


class ConfiguracaoGlobalViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar os Parâmetros Universais do Sistema (Singleton id=1).
    Permissão: `configuracoes_globais` (ou Administrador).
    """
    queryset = ConfiguracaoGlobal.objects.all()
    serializer_class = ConfiguracaoGlobalSerializer
    permission_classes = [IsAuthenticated, HasConfiguracoesGlobaisAccess]
    http_method_names = ['get', 'put', 'patch', 'post', 'head', 'options']

    def get_object(self):
        """Retorna sempre a instância única Singleton (id=1)."""
        return ConfiguracaoGlobal.get_solo()

    def list(self, request, *args, **kwargs):
        """Retorna o objeto único de configurações."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='presets-smtp')
    def presets_smtp(self, request):
        """Retorna os presets rápidos de provedores SMTP."""
        presets = obter_presets_smtp()
        return Response({
            "status": "success",
            "presets": presets
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='testar-smtp')
    def testar_smtp(self, request):
        """
        Dispara um e-mail de teste em tempo real com as configurações informadas ou salvas.
        """
        serializer = TesteSmtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Dados de teste SMTP inválidos.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        resultado = testar_conexao_smtp(serializer.validated_data)
        http_code = status.HTTP_200_OK if resultado.get("sucesso") else status.HTTP_400_BAD_REQUEST

        return Response(resultado, status=http_code)


class ControleArquivoLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para Auditoria e Gestão do Manifesto TTL de Logs Físicos.
    Permissão: `auditoria_logs_recovery` (ou Administrador).
    """
    queryset = ControleArquivoLog.objects.all().order_by('-data_criacao')
    serializer_class = ControleArquivoLogSerializer
    permission_classes = [IsAuthenticated, HasAuditoriaLogsAccess]

    @action(detail=False, methods=['post'], url_path='sincronizar')
    def sincronizar(self, request):
        """Varre a pasta de logs e indexa arquivos físicos novos no manifesto."""
        resultado = sincronizar_manifesto_logs()
        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='expurgar')
    def expurgar(self, request):
        """
        Executa a rotina de expurgo de logs por decurso de prazo:
        Envia backup por e-mail e exclui arquivos físicos expirados.
        """
        serializer = ExpurgoLogRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Parâmetros de expurgo inválidos.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        enviar_backup = serializer.validated_data.get('enviar_email_backup', True)
        data_corte = serializer.validated_data.get('data_corte')

        resultado = expurgar_arquivos_log(enviar_email_backup=enviar_backup, data_corte=data_corte)
        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='visualizar')
    def visualizar(self, request):
        """
        Log Viewer Seguro: lê o conteúdo dos arquivos diários com anti-path traversal.
        """
        serializer = LogViewerFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Parâmetros de consulta do Log Viewer inválidos.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = serializer.validated_data
        try:
            resultado = ler_arquivo_log_seguro(
                identificador_arquivo=params.get('arquivo', 'hoje'),
                nivel=params.get('nivel', 'TODOS'),
                busca=params.get('busca'),
                limit=params.get('limit', 100),
                offset=params.get('offset', 0)
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"[LOG VIEWER ERROR] {str(e)}")
            return Response({
                "status": "error",
                "message": "Não foi possível ler o arquivo de log solicitado."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogViewerView(APIView):
    """
    Endpoint direto /api/logs/ para visualização segura de logs.
    Permissão: `auditoria_logs_recovery` (ou Administrador).
    """
    permission_classes = [IsAuthenticated, HasAuditoriaLogsAccess]

    def get(self, request):
        serializer = LogViewerFilterSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "message": "Parâmetros inválidos.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        params = serializer.validated_data
        try:
            resultado = ler_arquivo_log_seguro(
                identificador_arquivo=params.get('arquivo', 'hoje'),
                nivel=params.get('nivel', 'TODOS'),
                busca=params.get('busca'),
                limit=params.get('limit', 100),
                offset=params.get('offset', 0)
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "Erro ao carregar logs do servidor."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LixeiraViewSet(viewsets.ViewSet):
    """
    Painel Centralizado de Lixeira e Restauração Lógica (100% Soft Delete).
    Segregação de Visão:
    - Administrador ou toggle `auditoria_logs_recovery`: Lixeira Global.
    - Operador comum: Minha Lixeira (`deleted_by_id = request.user.id`).
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Lista os registros inativados logicamente."""
        entidade = request.query_params.get('entidade')
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        busca = request.query_params.get('busca')
        autor_id = request.query_params.get('autor_id')

        autor_id_int = int(autor_id) if (autor_id and autor_id.isdigit()) else None

        itens = LixeiraService.listar_itens(
            user=request.user,
            entidade=entidade,
            data_inicio=data_inicio,
            data_fim=data_fim,
            busca=busca,
            autor_id=autor_id_int
        )

        serializer = LixeiraItemSerializer(itens, many=True)
        return Response({
            "status": "success",
            "total": len(itens),
            "itens": serializer.data,
            "entidades_suportadas": list(LixeiraService.ENTIDADES_CONFIG.keys())
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='entidades')
    def entidades(self, request):
        """Retorna lista de entidades e nomes amigáveis mapeados na Lixeira."""
        lista = [
            {"codigo": k, "nome": v['nome_singular']}
            for k, v in LixeiraService.ENTIDADES_CONFIG.items()
        ]
        return Response({
            "status": "success",
            "entidades": lista
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path=r'(?P<entidade>[^/.]+)/(?P<item_id>\d+)/restaurar')
    def restaurar(self, request, entidade=None, item_id=None):
        """
        Restaura um registro inativado da Lixeira.
        Operador só restaura se deleted_by_id for seu próprio ID.
        """
        if not entidade or not item_id:
            return Response({
                "status": "error",
                "message": "Entidade e ID são obrigatórios para restauração."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            resultado = LixeiraService.restaurar_item(
                user=request.user,
                entidade=entidade,
                item_id=int(item_id)
            )
            return Response({
                "status": "success",
                "message": resultado['mensagem'],
                "resultado": resultado
            }, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"[RESTAURACAO ERROR] Falha ao restaurar {entidade} #{item_id}: {str(e)}")
            return Response({
                "status": "error",
                "message": "Ocorreu um erro interno ao restaurar o registro."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
