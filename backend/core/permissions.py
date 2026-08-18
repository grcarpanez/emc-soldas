"""
Classes de permissão RBAC (Role-Based Access Control) dinâmicas.
Valida os 10 toggles dinâmicos no backend conforme a especificação do FSD.
"""
from rest_framework import permissions


class IsAdminUserRole(permissions.BasePermission):
    """Permite acesso apenas a usuários autenticados com papel de Administrador."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Compatibilidade com o campo role do modelo customizado ou is_superuser
        role = getattr(request.user, 'role', 'Operador')
        return role == 'Admin' or getattr(request.user, 'is_superuser', False)


class HasPermissionToggle(permissions.BasePermission):
    """
    Permissão base que verifica se o usuário é Administrador ou se possui
    o toggle de permissão ativo no seu perfil.
    """
    required_toggle = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Administrador possui acesso total irrestrito por padrão
        role = getattr(request.user, 'role', 'Operador')
        if role == 'Admin' or getattr(request.user, 'is_superuser', False):
            return True

        if not self.required_toggle:
            return True

        # Verifica na relação 1:1 de Permissoes
        permissoes = getattr(request.user, 'permissoes', None)
        if permissoes:
            return getattr(permissoes, self.required_toggle, False)

        return False


class HasComercialAccess(HasPermissionToggle):
    required_toggle = 'acesso_comercial'


class HasTesourariaAccess(HasPermissionToggle):
    required_toggle = 'acesso_tesouraria'


class HasComprasAccess(HasPermissionToggle):
    required_toggle = 'acesso_compras'


class HasCatalogoAccess(HasPermissionToggle):
    required_toggle = 'gestao_catalogo'


class HasRelatoriosAccess(HasPermissionToggle):
    required_toggle = 'visao_relatorios'


class HasCadastrosFinanceirosAccess(HasPermissionToggle):
    required_toggle = 'cadastros_financeiros'


class HasDicionarioUomAccess(HasPermissionToggle):
    required_toggle = 'gestao_dicionario_uom'


class HasConfiguracoesGlobaisAccess(HasPermissionToggle):
    required_toggle = 'configuracoes_globais'


class HasGestaoEquipeAccess(HasPermissionToggle):
    required_toggle = 'gestao_equipe'


class HasAuditoriaLogsAccess(HasPermissionToggle):
    required_toggle = 'auditoria_logs_recovery'
