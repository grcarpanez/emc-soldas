"""
Suíte de Testes Automatizados da Fase 3 - Autenticação, Sessão, Soft Lock e RBAC.
Em conformidade com docs/FSD.md e docs/PLANO.md.
"""
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import Usuario, Permissao, TokenSeguranca
from apps.authentication.services import gerar_tokens_usuario


class AuthenticationPhase3Tests(APITestCase):
    """
    Testes unitários e de integração para todo o fluxo de Autenticação,
    Gestão de Sessão HttpOnly, Soft Lock com PIN, Hard Lock, Anti-Bruteforce,
    Onboarding e Matriz de Permissões RBAC (10 Toggles).
    """

    def setUp(self):
        # Cria Usuário Administrador Master
        self.admin = Usuario.objects.create(
            nome="Administrador Master",
            email="admin@emcsoldas.com.br",
            role="Admin",
            is_ativo=True
        )
        self.admin.set_password("SenhaAdminSegura123!")
        self.admin.set_pin("123456")
        self.admin.save()

        self.admin_perm = Permissao.objects.create(
            usuario=self.admin,
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

        # Cria Usuário Operador Padrão
        self.operador = Usuario.objects.create(
            nome="Operador Oficina",
            email="operador@emcsoldas.com.br",
            role="Operador",
            is_ativo=True
        )
        self.operador.set_password("SenhaOperadorSegura123!")
        self.operador.set_pin("654321")
        self.operador.save()

        self.operador_perm = Permissao.objects.create(
            usuario=self.operador,
            acesso_comercial=True,
            acesso_tesouraria=False,
            acesso_compras=False,
            gestao_catalogo=False,
            visao_relatorios=True,
            cadastros_financeiros=False,
            gestao_dicionario_uom=False,
            configuracoes_globais=False,
            gestao_equipe=False,
            auditoria_logs_recovery=False,
        )

    # -------------------------------------------------------------------------
    # 1. Testes de Login, Logout e Cookies HttpOnly
    # -------------------------------------------------------------------------

    def test_login_sucesso_com_cookies_httponly(self):
        """Valida login com credenciais corretas e injeção do Cookie HttpOnly SameSite=Strict."""
        url = reverse('authentication:login')
        payload = {
            'email': 'admin@emcsoldas.com.br',
            'password': 'SenhaAdminSegura123!'
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['user']['email'], 'admin@emcsoldas.com.br')
        self.assertTrue(response.data['user']['is_admin'])
        self.assertTrue(response.data['user']['has_pin'])

        # Verifica injeção dos cookies HttpOnly
        self.assertIn('emc_access_token', response.cookies)
        self.assertTrue(response.cookies['emc_access_token']['httponly'])
        self.assertEqual(response.cookies['emc_access_token']['samesite'], 'Strict')

    def test_login_senha_incorreta_e_tentativas_restantes(self):
        """Valida que senha incorreta retorna 401 e decrementa contador de tentativas."""
        url = reverse('authentication:login')
        payload = {
            'email': 'operador@emcsoldas.com.br',
            'password': 'SenhaErrada123'
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['tentativas_restantes'], 4)

        # Checa no banco se incrementou
        self.operador.refresh_from_db()
        self.assertEqual(self.operador.tentativas_login_falhas, 1)

    def test_anti_bruteforce_bloqueio_apos_5_tentativas(self):
        """Valida que 5 falhas consecutivas bloqueiam a conta por 1 hora com status 429."""
        url = reverse('authentication:login')
        payload = {
            'email': 'operador@emcsoldas.com.br',
            'password': 'SenhaIncorreta'
        }

        # 4 tentativas incorretas
        for i in range(4):
            resp = self.client.post(url, payload, format='json')
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # 5ª tentativa dispara o bloqueio
        resp_5 = self.client.post(url, payload, format='json')
        self.assertEqual(resp_5.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('bloqueada por 1 hora', resp_5.data['message'])

        self.operador.refresh_from_db()
        self.assertTrue(self.operador.is_locked())
        self.assertIsNotNone(self.operador.bloqueado_ate)

        # Tentativa subsequente é barrada imediatamente pelo lock
        resp_6 = self.client.post(url, payload, format='json')
        self.assertEqual(resp_6.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_desbloqueio_manual_pelo_admin(self):
        """Valida que o Admin pode desbloquear uma conta travada por anti-bruteforce."""
        # Trava o operador
        self.operador.bloqueado_ate = timezone.now() + timedelta(hours=1)
        self.operador.tentativas_login_falhas = 5
        self.operador.save()

        # Autentica como Admin
        tokens = gerar_tokens_usuario(self.admin)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = f'/api/usuarios/{self.operador.id}/desbloquear/'
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        self.operador.refresh_from_db()
        self.assertFalse(self.operador.is_locked())
        self.assertEqual(self.operador.tentativas_login_falhas, 0)

    def test_logout_limpa_cookies(self):
        """Valida que o endpoint de logout limpa os cookies de sessão."""
        tokens = gerar_tokens_usuario(self.admin)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = reverse('authentication:logout')
        response = self.client.post(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Confirma limpeza do cookie
        self.assertEqual(response.cookies['emc_access_token'].value, '')

    def test_me_endpoint(self):
        """Valida consulta dos dados do usuário logado e matriz de 10 toggles."""
        tokens = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = reverse('authentication:me')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.operador.email)
        self.assertTrue(response.data['user']['permissoes']['acesso_comercial'])
        self.assertFalse(response.data['user']['permissoes']['acesso_tesouraria'])

    # -------------------------------------------------------------------------
    # 2. Testes de Soft Lock e Hard Lock (PIN de 6 dígitos)
    # -------------------------------------------------------------------------

    def test_set_pin_configuracao(self):
        """Valida cadastro de novo PIN de 6 dígitos com confirmação."""
        tokens = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = reverse('authentication:set-pin')
        payload = {
            'pin': '987654',
            'confirm_pin': '987654'
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.operador.refresh_from_db()
        self.assertTrue(self.operador.check_pin('987654'))

    def test_unlock_pin_sucesso(self):
        """Valida destravamento com sucesso do Soft Lock pelo PIN correto."""
        tokens = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = reverse('authentication:unlock-pin')
        payload = {'pin': '654321'}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

    def test_unlock_pin_hard_lock_apos_3_erros(self):
        """Valida que 3 erros consecutivos no PIN acionam Hard Lock e limpam a sessão."""
        tokens = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = reverse('authentication:unlock-pin')
        payload_errado = {'pin': '000000'}

        # 1º erro
        resp1 = self.client.post(url, payload_errado, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp1.data['tentativas_restantes'], 2)
        self.assertFalse(resp1.data['hard_lock'])

        # 2º erro
        resp2 = self.client.post(url, payload_errado, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp2.data['tentativas_restantes'], 1)

        # 3º erro -> Hard Lock!
        resp3 = self.client.post(url, payload_errado, format='json')
        self.assertEqual(resp3.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(resp3.data['hard_lock'])
        self.assertIn('Hard Lock', resp3.data['message'])

    # -------------------------------------------------------------------------
    # 3. Testes de Recuperação de Senha (Código 8 Dígitos)
    # -------------------------------------------------------------------------

    def test_fluxo_recuperacao_senha_completo(self):
        """Valida fluxo de esqueci minha senha com código de 8 dígitos e redefinição."""
        # 1. Solicita recuperação
        forgot_url = reverse('authentication:forgot-password')
        resp_forgot = self.client.post(forgot_url, {'email': 'operador@emcsoldas.com.br'}, format='json')
        self.assertEqual(resp_forgot.status_code, status.HTTP_200_OK)

        # Obtém o token de 8 dígitos gerado
        token_obj = TokenSeguranca.objects.filter(
            usuario=self.operador,
            tipo='RECOVERY',
            utilizado=False
        ).first()
        self.assertIsNotNone(token_obj)
        self.assertEqual(len(token_obj.token), 8)
        self.assertTrue(token_obj.token.isdigit())

        # 2. Redefine a senha com o código
        reset_url = reverse('authentication:reset-password')
        payload_reset = {
            'email': 'operador@emcsoldas.com.br',
            'code': token_obj.token,
            'new_password': 'NovaSenhaSegura9988#'
        }
        resp_reset = self.client.post(reset_url, payload_reset, format='json')
        self.assertEqual(resp_reset.status_code, status.HTTP_200_OK)

        # 3. Valida login com a nova senha
        login_url = reverse('authentication:login')
        resp_login = self.client.post(login_url, {
            'email': 'operador@emcsoldas.com.br',
            'password': 'NovaSenhaSegura9988#'
        }, format='json')
        self.assertEqual(resp_login.status_code, status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 4. Testes de Onboarding e Convite de Colaboradores
    # -------------------------------------------------------------------------

    def test_onboarding_convite_e_ativacao_conta(self):
        """Valida convite de novo colaborador pelo Admin e ativação com definição de senha."""
        tokens = gerar_tokens_usuario(self.admin)
        self.client.cookies['emc_access_token'] = tokens['access']

        convidar_url = '/api/usuarios/convidar/'
        payload_convite = {
            'nome': 'Carlos Soldador',
            'email': 'carlos@emcsoldas.com.br',
            'role': 'Operador',
            'permissoes': {
                'acesso_comercial': True,
                'gestao_catalogo': True,
            }
        }
        resp_convite = self.client.post(convidar_url, payload_convite, format='json')
        self.assertEqual(resp_convite.status_code, status.HTTP_201_CREATED)

        invite_token = resp_convite.data['invite_token']
        self.assertIsNotNone(invite_token)

        # Colaborador criado inativo aguardando ativação
        novo_user = Usuario.objects.get(email='carlos@emcsoldas.com.br')
        self.assertFalse(novo_user.is_ativo)
        self.assertTrue(novo_user.permissoes.gestao_catalogo)
        self.assertFalse(novo_user.permissoes.acesso_tesouraria)

        # Ativa a conta com senha
        activate_url = reverse('authentication:activate-account')
        payload_activate = {
            'token': invite_token,
            'password': 'MinhaNovaSenhaForte123!',
            'confirm_password': 'MinhaNovaSenhaForte123!'
        }
        resp_activate = self.client.post(activate_url, payload_activate, format='json')
        self.assertEqual(resp_activate.status_code, status.HTTP_200_OK)

        novo_user.refresh_from_db()
        self.assertTrue(novo_user.is_ativo)
        self.assertTrue(novo_user.check_password('MinhaNovaSenhaForte123!'))

    # -------------------------------------------------------------------------
    # 5. Testes de RBAC com 10 Toggles Dinâmicos (403 Forbidden)
    # -------------------------------------------------------------------------

    def test_rbac_bloqueio_403_para_operador_sem_gestao_equipe(self):
        """Valida que colaborador sem o toggle gestao_equipe recebe 403 Forbidden ao acessar /api/usuarios/."""
        tokens = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens['access']

        url = '/api/usuarios/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rbac_liberacao_apos_atualizacao_de_toggle(self):
        """Valida que conceder o toggle gestao_equipe ao operador libera o acesso."""
        # Admin atualiza as permissões do operador
        tokens_admin = gerar_tokens_usuario(self.admin)
        self.client.cookies['emc_access_token'] = tokens_admin['access']

        patch_url = f'/api/usuarios/{self.operador.id}/permissoes/'
        resp_patch = self.client.patch(patch_url, {'gestao_equipe': True}, format='json')
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_patch.data['permissoes']['gestao_equipe'])

        # Agora o operador acessa /api/usuarios/ com sucesso
        tokens_operador = gerar_tokens_usuario(self.operador)
        self.client.cookies['emc_access_token'] = tokens_operador['access']

        url = '/api/usuarios/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
