"""
Middlewares do núcleo para injeção de contexto de auditoria e logging de segurança.
"""
import logging
import threading

logger = logging.getLogger('audit')
security_logger = logging.getLogger('django')

# Thread local para armazenar o usuário atual da requisição
_thread_locals = threading.local()


def get_current_user():
    """Retorna o usuário associado à thread atual da requisição."""
    return getattr(_thread_locals, 'user', None)


class AuditUserMiddleware:
    """
    Middleware que captura o usuário autenticado da requisição e armazena
    no thread local para alimentar campos de autoria em models.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        _thread_locals.user = None
        return response


class SecurityLoggingMiddleware:
    """
    Middleware que registra tentativas de acesso não autorizado (401/403)
    e rastreia anomalias de segurança com IP e rota.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code in (401, 403):
            ip = self._get_client_ip(request)
            user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else 'Anon'
            security_logger.warning(
                f"[SEGURANÇA] Acesso não autorizado ({response.status_code}) - IP: {ip} | "
                f"Usuário: {user} | Método: {request.method} | Rota: {request.path}"
            )

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
