"""
Serviços de segurança, geração de tokens JWT, disparo de e-mails de recuperação/onboarding
e manipulação de cookies HttpOnly com SameSite=Strict.
"""
import secrets
import string
import logging
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Usuario, Permissao, TokenSeguranca

logger = logging.getLogger('emc_soldas')


def gerar_tokens_usuario(usuario: Usuario) -> dict:
    """
    Gera par de tokens JWT (Access Token e Refresh Token) codificando o ID do usuário.
    """
    refresh = RefreshToken()
    refresh['user_id'] = usuario.id
    refresh['email'] = usuario.email
    refresh['role'] = usuario.role

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def set_auth_cookies(response, access_token: str, refresh_token: str = None):
    """
    Injeta os tokens JWT em cookies de sessão HttpOnly com SameSite=Strict.
    Garante 'Morte Súbita' da sessão ao fechar o navegador e proteção anti-XSS.
    """
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
    cookie_name = jwt_settings.get('AUTH_COOKIE', 'emc_access_token')
    refresh_cookie_name = jwt_settings.get('AUTH_COOKIE_REFRESH', 'emc_refresh_token')
    secure = jwt_settings.get('AUTH_COOKIE_SECURE', not settings.DEBUG)
    samesite = jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Strict')
    path = jwt_settings.get('AUTH_COOKIE_PATH', '/')

    # Cookie de Sessão HttpOnly para o Access Token (expira ao fechar navegador)
    response.set_cookie(
        key=cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path=path
    )

    if refresh_token:
        # Refresh token também em Cookie HttpOnly com vida útil de 15 dias
        max_age = int(jwt_settings.get('REFRESH_TOKEN_LIFETIME', timedelta(days=15)).total_seconds())
        response.set_cookie(
            key=refresh_cookie_name,
            value=refresh_token,
            max_age=max_age,
            httponly=True,
            secure=secure,
            samesite=samesite,
            path=path
        )


def clear_auth_cookies(response):
    """
    Remove os cookies de autenticação do cliente no momento do logout.
    """
    jwt_settings = getattr(settings, 'SIMPLE_JWT', {})
    cookie_name = jwt_settings.get('AUTH_COOKIE', 'emc_access_token')
    refresh_cookie_name = jwt_settings.get('AUTH_COOKIE_REFRESH', 'emc_refresh_token')
    path = jwt_settings.get('AUTH_COOKIE_PATH', '/')

    response.delete_cookie(cookie_name, path=path)
    response.delete_cookie(refresh_cookie_name, path=path)


def gerar_codigo_recuperacao(usuario: Usuario) -> str:
    """
    Gera código numérico de 8 dígitos criptograficamente seguro para recuperação de senha,
    com validade de 30 minutos, invalidando códigos anteriores do mesmo tipo.
    """
    # Invalida tokens anteriores não utilizados
    TokenSeguranca.objects.filter(
        usuario=usuario,
        tipo='RECOVERY',
        utilizado=False
    ).update(utilizado=True)

    # Gera código aleatório de 8 dígitos
    caracteres = string.digits
    codigo = ''.join(secrets.choice(caracteres) for _ in range(8))

    expira_em = timezone.now() + timedelta(minutes=30)
    TokenSeguranca.objects.create(
        usuario=usuario,
        token=codigo,
        tipo='RECOVERY',
        expira_em=expira_em,
        utilizado=False
    )

    return codigo


def enviar_email_recuperacao_senha(usuario: Usuario, codigo: str) -> bool:
    """
    Dispara e-mail com o código de 8 dígitos de recuperação de senha.
    Em desenvolvimento, o envio é direcionado com segurança para o console.
    """
    assunto = "[EMC Soldas] Código de Recuperação de Senha"
    mensagem = (
        f"Olá, {usuario.nome}!\n\n"
        f"Você solicitou a recuperação da sua senha de acesso ao sistema EMC Soldas.\n\n"
        f"Seu código de verificação é:\n"
        f"{codigo}\n\n"
        f"Este código é de uso único e expira em 30 minutos.\n"
        f"Se você não solicitou esta redefinição, desconsidere este e-mail.\n\n"
        f"Atenciosamente,\n"
        f"Equipe de Segurança EMC Soldas"
    )

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail de recuperação para {usuario.email}: {e}")
        return False


def gerar_token_convite_onboarding(usuario: Usuario) -> str:
    """
    Gera token criptográfico seguro de 32 bytes (URL-safe) para convite de onboarding,
    com validade de 48 horas.
    """
    # Invalida convites anteriores pendentes
    TokenSeguranca.objects.filter(
        usuario=usuario,
        tipo='INVITE',
        utilizado=False
    ).update(utilizado=True)

    token = secrets.token_urlsafe(32)
    expira_em = timezone.now() + timedelta(hours=48)

    TokenSeguranca.objects.create(
        usuario=usuario,
        token=token,
        tipo='INVITE',
        expira_em=expira_em,
        utilizado=False
    )

    return token


def enviar_email_convite_colaborador(usuario: Usuario, token: str) -> bool:
    """
    Dispara e-mail de convite para novo colaborador cadastrar sua senha de acesso.
    """
    assunto = "[EMC Soldas] Convite de Acesso ao Sistema"
    mensagem = (
        f"Olá, {usuario.nome}!\n\n"
        f"Você foi cadastrado como colaborador no sistema de gestão EMC Soldas ({usuario.role}).\n\n"
        f"Para ativar sua conta e definir sua senha de acesso, utilize o token abaixo:\n"
        f"{token}\n\n"
        f"Este convite é válido por 48 horas.\n\n"
        f"Atenciosamente,\n"
        f"Administração EMC Soldas"
    )

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail de convite para {usuario.email}: {e}")
        return False
