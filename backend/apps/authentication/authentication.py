"""
Autenticação JWT com suporte a Cookie de Sessão HttpOnly e cabeçalho Bearer.
Em conformidade com docs/FSD.md - Seções 6, 8.1 e 8.2.
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from .models import Usuario


class CookieJWTAuthentication(JWTAuthentication):
    """
    Classe de autenticação customizada para o Django REST Framework.
    
    Tenta obter o token JWT a partir de:
    1. Cabeçalho HTTP Authorization (Bearer <token>)
    2. Cookie de Sessão HttpOnly ('emc_access_token')
    
    Em seguida, localiza e valida a instância do modelo `Usuario`.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = None

        if header is not None:
            raw_token = self.get_raw_token(header)
        else:
            cookie_name = getattr(settings, 'SIMPLE_JWT', {}).get('AUTH_COOKIE', 'emc_access_token')
            raw_token = request.COOKIES.get(cookie_name)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_user(self, validated_token):
        """
        Localiza o usuário no modelo `Usuario` a partir do `user_id` codificado no token JWT.
        """
        user_id = validated_token.get('user_id')
        if not user_id:
            raise InvalidToken("Token inválido: identificador de usuário ausente.")

        try:
            usuario = Usuario.objects.select_related('permissoes').get(id=user_id, deleted_at__isnull=True)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed("Usuário não encontrado ou inativo.", code='user_not_found')

        if not usuario.is_ativo:
            raise AuthenticationFailed("A conta deste usuário está inativada.", code='user_inactive')

        return usuario
