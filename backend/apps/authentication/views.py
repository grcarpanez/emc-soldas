"""
Views e ViewSets para Autenticação, Gestão de PIN/Soft Lock, Onboarding e RBAC.
Em conformidade com docs/FSD.md - Seções 6, 8, 8.1, 8.2 e 11.
"""
import logging
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from core.permissions import IsAdminUserRole, HasGestaoEquipeAccess
from .models import Usuario, Permissao, TokenSeguranca
from .serializers import (
    UsuarioSerializer,
    LoginSerializer,
    SetPinSerializer,
    UnlockPinSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ConvidarUsuarioSerializer,
    ActivateAccountSerializer,
    AtualizarPermissoesSerializer,
)
from .services import (
    gerar_tokens_usuario,
    set_auth_cookies,
    clear_auth_cookies,
    gerar_codigo_recuperacao,
    enviar_email_recuperacao_senha,
    gerar_token_convite_onboarding,
    enviar_email_convite_colaborador,
)

logger = logging.getLogger('emc_soldas')


class LoginView(APIView):
    """
    Endpoint de Login com proteção Anti-Bruteforce e injeção de Cookie HttpOnly.
    Bloqueio automático de 1 hora após 5 falhas consecutivas.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de login inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower().strip()
        password = serializer.validated_data['password']

        usuario = Usuario.objects.filter(email__iexact=email, deleted_at__isnull=True).first()

        if not usuario:
            # Defesa contra timing attack simulando verificação de hash
            check_password(password, 'pbkdf2_sha256$260000$dummy$dummyhash')
            return Response({
                'status': 'error',
                'message': 'E-mail ou senha incorretos.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Checagem de bloqueio por Anti-Bruteforce
        if usuario.is_locked():
            return Response({
                'status': 'error',
                'message': 'Conta temporariamente bloqueada por excesso de tentativas de login falhas. Tente novamente mais tarde.',
                'bloqueado_ate': usuario.bloqueado_ate
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Checagem de conta inativa
        if not usuario.is_ativo:
            return Response({
                'status': 'error',
                'message': 'Esta conta de usuário está desativada. Contate o Administrador.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Verificação da Senha
        if not usuario.check_password(password):
            usuario.registrar_falha_login(max_tentativas=5, minutos_bloqueio=60)
            if usuario.is_locked():
                return Response({
                    'status': 'error',
                    'message': 'Conta bloqueada por 1 hora devido a 5 tentativas consecutivas de login incorretas.',
                    'bloqueado_ate': usuario.bloqueado_ate
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            tentativas_restantes = max(0, 5 - usuario.tentativas_login_falhas)
            return Response({
                'status': 'error',
                'message': f'E-mail ou senha incorretos. {tentativas_restantes} tentativa(s) restante(s) antes do bloqueio.',
                'tentativas_restantes': tentativas_restantes
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Login bem-sucedido: reseta falhas e atualiza last_login
        usuario.resetar_falhas_login()
        tokens = gerar_tokens_usuario(usuario)

        user_data = UsuarioSerializer(usuario).data

        response = Response({
            'status': 'success',
            'message': 'Login realizado com sucesso.',
            'user': user_data,
            'access': tokens['access'],
        }, status=status.HTTP_200_OK)

        # Injeta tokens em Cookies HttpOnly com SameSite=Strict
        set_auth_cookies(response, tokens['access'], tokens['refresh'])
        return response


class LogoutView(APIView):
    """
    Endpoint de Logout para destruição de sessão no servidor e limpeza dos Cookies HttpOnly.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({
            'status': 'success',
            'message': 'Sessão encerrada com sucesso.'
        }, status=status.HTTP_200_OK)

        clear_auth_cookies(response)
        return response


class MeView(APIView):
    """
    Retorna os dados do colaborador autenticado e sua matriz de 10 toggles dinâmicos.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response({
            'status': 'success',
            'user': serializer.data
        }, status=status.HTTP_200_OK)


class SetPinView(APIView):
    """
    Cadastro ou alteração do PIN de segurança de 6 dígitos para o Soft Lock.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetPinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de PIN inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        pin = serializer.validated_data['pin']
        request.user.set_pin(pin)
        request.user.save(update_fields=['pin_hash', 'updated_at'])

        return Response({
            'status': 'success',
            'message': 'PIN de segurança de 6 dígitos cadastrado com sucesso.'
        }, status=status.HTTP_200_OK)


class UnlockPinView(APIView):
    """
    Destravamento ágil da tela travada por Soft Lock (30 minutos de ociosidade).
    Com trava de segurança: 3 erros consecutivos de PIN acionam o Hard Lock imediato.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UnlockPinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'PIN deve conter exatamente 6 dígitos numéricos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        pin = serializer.validated_data['pin']
        
        # Obtém erros acumulados na sessão ativa
        pin_errors = getattr(request.user, '_pin_errors', 0)
        session_errors = request.session.get('pin_errors', 0)

        if not request.user.has_pin:
            return Response({
                'status': 'error',
                'message': 'Nenhum PIN cadastrado para este usuário. Use sua senha completa.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if request.user.check_pin(pin):
            request.session['pin_errors'] = 0
            return Response({
                'status': 'success',
                'message': 'Sessão destravada com sucesso.'
            }, status=status.HTTP_200_OK)
        else:
            session_errors += 1
            request.session['pin_errors'] = session_errors

            if session_errors >= 3:
                # Dispara Hard Lock: destrói a sessão e exige login completo
                request.session['pin_errors'] = 0
                response = Response({
                    'status': 'error',
                    'message': 'Limite de 3 tentativas incorretas de PIN excedido. Sessão encerrada por segurança (Hard Lock). Faça login com e-mail e senha.',
                    'hard_lock': True
                }, status=status.HTTP_401_UNAUTHORIZED)
                clear_auth_cookies(response)
                return response

            tentativas_restantes = 3 - session_errors
            return Response({
                'status': 'error',
                'message': f'PIN incorreto. Você tem mais {tentativas_restantes} tentativa(s) antes do bloqueio da sessão (Hard Lock).',
                'tentativas_restantes': tentativas_restantes,
                'hard_lock': False
            }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """
    Solicitação de recuperação de senha: gera código de 8 dígitos e envia por e-mail.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'E-mail inválido.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower().strip()
        usuario = Usuario.objects.filter(email__iexact=email, deleted_at__isnull=True).first()

        if usuario and usuario.is_ativo:
            codigo = gerar_codigo_recuperacao(usuario)
            enviar_email_recuperacao_senha(usuario, codigo)

        # Mensagem genérica para prevenir enumeração de contas
        return Response({
            'status': 'success',
            'message': 'Se o e-mail informado estiver cadastrado em nosso sistema, um código de verificação de 8 dígitos foi enviado.'
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    Redefinição de senha utilizando o código de 8 dígitos recebido por e-mail.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de redefinição inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower().strip()
        code = serializer.validated_data['code'].strip()
        new_password = serializer.validated_data['new_password']

        usuario = Usuario.objects.filter(email__iexact=email, deleted_at__isnull=True).first()
        if not usuario:
            return Response({
                'status': 'error',
                'message': 'Código de verificação inválido ou expirado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        token_obj = TokenSeguranca.objects.filter(
            usuario=usuario,
            token=code,
            tipo='RECOVERY',
            utilizado=False
        ).first()

        if not token_obj or not token_obj.is_valido:
            return Response({
                'status': 'error',
                'message': 'Código de verificação inválido ou expirado. Solicite um novo código.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Atualiza a senha e invalida o token
        usuario.set_password(new_password)
        usuario.resetar_falhas_login()
        usuario.save(update_fields=['password_hash', 'tentativas_login_falhas', 'bloqueado_ate', 'updated_at'])

        token_obj.utilizado = True
        token_obj.save(update_fields=['utilizado'])

        return Response({
            'status': 'success',
            'message': 'Senha redefinida com sucesso. Você já pode fazer login com suas novas credenciais.'
        }, status=status.HTTP_200_OK)


class ActivateAccountView(APIView):
    """
    Ativação de conta e cadastro de senha para colaboradores convidados via onboarding.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ActivateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de ativação inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token'].strip()
        password = serializer.validated_data['password']

        token_obj = TokenSeguranca.objects.filter(
            token=token,
            tipo='INVITE',
            utilizado=False
        ).select_related('usuario').first()

        if not token_obj or not token_obj.is_valido:
            return Response({
                'status': 'error',
                'message': 'Link de convite inválido ou expirado. Solicite um novo convite ao Administrador.'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = token_obj.usuario
        usuario.set_password(password)
        usuario.is_ativo = True
        usuario.resetar_falhas_login()
        usuario.save(update_fields=['password_hash', 'is_ativo', 'tentativas_login_falhas', 'bloqueado_ate', 'updated_at'])

        token_obj.utilizado = True
        token_obj.save(update_fields=['utilizado'])

        # Gera tokens para login imediato
        tokens = gerar_tokens_usuario(usuario)
        user_data = UsuarioSerializer(usuario).data

        response = Response({
            'status': 'success',
            'message': 'Conta ativada com sucesso! Bem-vindo(a) ao sistema EMC Soldas.',
            'user': user_data,
            'access': tokens['access']
        }, status=status.HTTP_200_OK)

        set_auth_cookies(response, tokens['access'], tokens['refresh'])
        return response


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Gestão de Colaboradores e Equipe.
    Permissões: Administrador ou Usuário com permissão `gestao_equipe`.
    """
    queryset = Usuario.objects.select_related('permissoes').filter(deleted_at__isnull=True).order_by('nome')
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, HasGestaoEquipeAccess]

    @action(detail=False, methods=['post'], url_path='convidar')
    def convidar(self, request):
        """
        Onboarding de colaboradores: cadastra o usuário com senha pendente
        e envia convite seguro por e-mail.
        """
        serializer = ConvidarUsuarioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de convite inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        nome = serializer.validated_data['nome'].strip()
        email = serializer.validated_data['email']
        role = serializer.validated_data.get('role', 'Operador')
        permissoes_data = serializer.validated_data.get('permissoes', {})

        # Cria o colaborador com is_ativo=False aguardando ativação
        usuario = Usuario.objects.create(
            nome=nome,
            email=email,
            role=role,
            is_ativo=False,
            created_by_id=request.user.id
        )

        # Cria a matriz de permissões 1:1
        if role == 'Admin':
            # Administrador recebe todos os toggles ativos por padrão
            Permissao.objects.create(
                usuario=usuario,
                acesso_comercial=True,
                acesso_tesouraria=True,
                acesso_compras=True,
                gestao_catalogo=True,
                visao_relatorios=True,
                cadastros_financeiros=True,
                gestao_dicionario_uom=True,
                configuracoes_globais=True,
                gestao_equipe=True,
                auditoria_logs_recovery=True,
            )
        else:
            Permissao.objects.create(
                usuario=usuario,
                acesso_comercial=permissoes_data.get('acesso_comercial', False),
                acesso_tesouraria=permissoes_data.get('acesso_tesouraria', False),
                acesso_compras=permissoes_data.get('acesso_compras', False),
                gestao_catalogo=permissoes_data.get('gestao_catalogo', False),
                visao_relatorios=permissoes_data.get('visao_relatorios', True),
                cadastros_financeiros=permissoes_data.get('cadastros_financeiros', False),
                gestao_dicionario_uom=permissoes_data.get('gestao_dicionario_uom', False),
                configuracoes_globais=permissoes_data.get('configuracoes_globais', False),
                gestao_equipe=permissoes_data.get('gestao_equipe', False),
                auditoria_logs_recovery=permissoes_data.get('auditoria_logs_recovery', False),
            )

        # Gera token de convite e envia e-mail
        token = gerar_token_convite_onboarding(usuario)
        enviar_email_convite_colaborador(usuario, token)

        return Response({
            'status': 'success',
            'message': f'Convite enviado com sucesso para {usuario.email}.',
            'user': UsuarioSerializer(usuario).data,
            'invite_token': token
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='desbloquear')
    def desbloquear(self, request, pk=None):
        """
        Desbloqueio manual de conta travada por Anti-Bruteforce.
        """
        usuario = self.get_object()
        usuario.resetar_falhas_login()
        return Response({
            'status': 'success',
            'message': f'Usuário {usuario.nome} ({usuario.email}) foi desbloqueado com sucesso.'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'put'], url_path='permissoes')
    def atualizar_permissoes(self, request, pk=None):
        """
        Atualiza os 10 toggles dinâmicos da permissão do colaborador.
        """
        usuario = self.get_object()
        permissoes, _ = Permissao.objects.get_or_create(usuario=usuario)

        serializer = AtualizarPermissoesSerializer(permissoes, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Dados de permissão inválidos.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            'status': 'success',
            'message': f'Permissões de {usuario.nome} atualizadas com sucesso.',
            'permissoes': serializer.data
        }, status=status.HTTP_200_OK)
