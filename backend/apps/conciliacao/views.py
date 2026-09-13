"""
Views e endpoints REST para Conciliação Bancária Inteligente Split-Screen (OFX/CSV).
Protegidos por autenticação JWT e pelo toggle RBAC 'acesso_tesouraria'.
"""
from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from core.permissions import HasTesourariaAccess
from apps.financeiro.serializers import LancamentoFinanceiroSerializer
from apps.conciliacao.serializers import (
    UploadExtratoSerializer,
    ConfirmarConciliacaoSerializer,
    DesconciliarSerializer,
    LancamentoRapidoSerializer,
    TrocarContaSerializer,
    DivergenciasQuerySerializer,
    ImportacaoLoteSerializer
)
from apps.conciliacao.services import (
    processar_extrato_split_screen,
    confirmar_conciliacao,
    desconciliar_lancamento,
    realizar_lancamento_rapido,
    trocar_conta_lancamento,
    obter_relatorio_divergencias,
    executar_importacao_lote
)
from apps.conciliacao.parsers import ExtratoParserException


class UploadExtratoView(views.APIView):
    """
    POST /api/conciliacao/upload-extrato/
    Processa o upload do arquivo de extrato bancário (OFX ou CSV) e retorna
    a visão Split-Screen com os lançamentos do ERP e sugestões de matching.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = UploadExtratoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        arquivo = serializer.validated_data['arquivo']
        conta_id = serializer.validated_data.get('conta_id')
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        data_ini_str = data_inicio.isoformat() if data_inicio else None
        data_fim_str = data_fim.isoformat() if data_fim else None

        try:
            resultado = processar_extrato_split_screen(
                arquivo=arquivo,
                conta_id=conta_id,
                data_inicio_str=data_ini_str,
                data_fim_str=data_fim_str,
                user=request.user
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ExtratoParserException as e:
            return Response(
                {"detail": f"Erro ao processar o arquivo de extrato: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ConfirmarConciliacaoView(views.APIView):
    """
    POST /api/conciliacao/confirmar/
    Efetiva a conciliação de 1 ou N lançamentos financeiros, liquidando títulos
    pendentes no Regime de Caixa e gravando a auditoria perpétua.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = ConfirmarConciliacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_ids = serializer.validated_data['lancamento_ids']
        conta_id = serializer.validated_data['conta_id']
        data_conciliacao = serializer.validated_data.get('data_conciliacao')

        lancamentos = confirmar_conciliacao(
            lancamento_ids=lancamento_ids,
            conta_id=conta_id,
            data_conciliacao=data_conciliacao,
            user=request.user
        )

        dados_serializados = LancamentoFinanceiroSerializer(lancamentos, many=True).data
        return Response({
            "status": "sucesso",
            "mensagem": f"{len(lancamentos)} lançamento(s) conciliado(s) com sucesso.",
            "lancamentos_conciliados": dados_serializados
        }, status=status.HTTP_200_OK)


class DesconciliarView(views.APIView):
    """
    POST /api/conciliacao/desconciliar/
    Reverte a flag e dados de conciliação bancária de um lançamento financeiro.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = DesconciliarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_id = serializer.validated_data['lancamento_id']
        lancamento = desconciliar_lancamento(
            lancamento_id=lancamento_id,
            user=request.user
        )

        dados_serializados = LancamentoFinanceiroSerializer(lancamento).data
        return Response({
            "status": "sucesso",
            "mensagem": "Conciliação do lançamento desfeita com sucesso.",
            "lancamento": dados_serializados
        }, status=status.HTTP_200_OK)


class LancamentoRapidoView(views.APIView):
    """
    POST /api/conciliacao/lancamento-rapido/
    Cria e liquida imediatamente uma despesa ou receita direto de uma linha do extrato bancário
    (ex: tarifas bancárias, rendimentos), marcando-a automaticamente como conciliada.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = LancamentoRapidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento = realizar_lancamento_rapido(
            dados=serializer.validated_data,
            user=request.user
        )

        dados_serializados = LancamentoFinanceiroSerializer(lancamento).data
        return Response({
            "status": "sucesso",
            "mensagem": "Lançamento rápido criado, liquidado e conciliado com sucesso.",
            "lancamento": dados_serializados
        }, status=status.HTTP_201_CREATED)


class TrocarContaView(views.APIView):
    """
    POST /api/conciliacao/trocar-conta/
    Altera em 1 clique a conta bancária de um lançamento financeiro do ERP,
    remanejando saldos caso o título já esteja em status PAGO.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = TrocarContaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_id = serializer.validated_data['lancamento_id']
        nova_conta_id = serializer.validated_data['nova_conta_id']

        lancamento = trocar_conta_lancamento(
            lancamento_id=lancamento_id,
            nova_conta_id=nova_conta_id,
            user=request.user
        )

        dados_serializados = LancamentoFinanceiroSerializer(lancamento).data
        return Response({
            "status": "sucesso",
            "mensagem": "Conta bancária do lançamento alterada com sucesso.",
            "lancamento": dados_serializados
        }, status=status.HTTP_200_OK)


class DivergenciasView(views.APIView):
    """
    GET /api/conciliacao/divergencias/
    Retorna os dados estruturados para as duas abas do Relatório de Divergências de Conciliação:
    - Aba 1: Sobras do Extrato Bancário.
    - Aba 2: Sobras do ERP (Lançamentos manuais não localizados no banco).
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]

    def get(self, request, *args, **kwargs):
        serializer = DivergenciasQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        conta_id = serializer.validated_data.get('conta_id')
        data_inicio = serializer.validated_data.get('data_inicio')
        data_fim = serializer.validated_data.get('data_fim')

        resultado = obter_relatorio_divergencias(
            conta_id=conta_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        return Response(resultado, status=status.HTTP_200_OK)


class ImportacaoLoteView(views.APIView):
    """
    POST /api/conciliacao/importacao-lote/
    Efetiva a importação em lote a partir do extrato bancário, criando e conciliando
    todos os lançamentos financeiros no ERP de forma atômica e atualizando o saldo bancário.
    """
    permission_classes = [permissions.IsAuthenticated, HasTesourariaAccess]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        serializer = ImportacaoLoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        conta_id = serializer.validated_data['conta_id']
        lancamentos_dados = serializer.validated_data['lancamentos']

        resultado = executar_importacao_lote(
            conta_id=conta_id,
            lancamentos_dados=lancamentos_dados,
            user=request.user
        )
        return Response(resultado, status=status.HTTP_201_CREATED)

