"""
Tratamento global e seguro de exceções da API REST.
Impede vazamento de Tracebacks técnicos para o frontend e grava detalhes em logs diários.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('emc_soldas')


def custom_exception_handler(exc, context):
    """
    Handler de exceções customizado do Django REST Framework.
    Formata respostas em padrão consistente e seguro.
    """
    response = exception_handler(exc, context)

    # Erro interno não tratado pelo DRF (HTTP 500)
    if response is None:
        view_name = context.get('view', '__unknown_view__')
        logger.exception(f"[ERRO CRÍTICO 500] Exceção não tratada na view {view_name}: {str(exc)}")

        return Response(
            {
                "status": "error",
                "message": "Ocorreu um erro interno no servidor. Nossa equipe foi notificada.",
                "code": "internal_server_error"
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Formata respostas padrão do DRF para manter consistência
    custom_data = {
        "status": "error",
        "code": getattr(exc, 'default_code', 'api_error'),
        "message": "Falha na validação da requisição.",
        "details": response.data
    }

    if isinstance(response.data, dict) and 'detail' in response.data:
        custom_data['message'] = str(response.data['detail'])

    response.data = custom_data
    return response
