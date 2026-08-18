"""
Serializers para o ecossistema de Autenticação, Usuários, Permissões e Gestão de PIN/Sessão.
"""
import re
from rest_framework import serializers
from .models import Usuario, Permissao, TokenSeguranca


class PermissaoSerializer(serializers.ModelSerializer):
    """Serializer para a matriz de 10 toggles dinâmicos de permissão."""

    class Meta:
        model = Permissao
        fields = [
            'acesso_comercial',
            'acesso_tesouraria',
            'acesso_compras',
            'gestao_catalogo',
            'visao_relatorios',
            'cadastros_financeiros',
            'gestao_dicionario_uom',
            'configuracoes_globais',
            'gestao_equipe',
            'auditoria_logs_recovery',
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para leitura dos dados do colaborador."""
    permissoes = PermissaoSerializer(read_only=True)
    has_pin = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id',
            'nome',
            'email',
            'role',
            'is_ativo',
            'has_pin',
            'is_admin',
            'tentativas_login_falhas',
            'bloqueado_ate',
            'last_login',
            'created_at',
            'updated_at',
            'permissoes',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login', 'tentativas_login_falhas', 'bloqueado_ate']


class LoginSerializer(serializers.Serializer):
    """Validação de credenciais de login."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class SetPinSerializer(serializers.Serializer):
    """Validação de cadastro/alteração do PIN de 6 dígitos numéricos."""
    pin = serializers.CharField(max_length=6, min_length=6, required=True)
    confirm_pin = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_pin(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("O PIN deve conter exatamente 6 dígitos numéricos.")
        return value

    def validate(self, data):
        if data['pin'] != data['confirm_pin']:
            raise serializers.ValidationError({"confirm_pin": "A confirmação do PIN não confere."})
        return data


class UnlockPinSerializer(serializers.Serializer):
    """Validação do PIN para destravamento do Soft Lock."""
    pin = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_pin(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("O PIN deve conter exatamente 6 dígitos numéricos.")
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    """Validação do e-mail para solicitação de recuperação de senha."""
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    """Validação de redefinição de senha com código de 8 dígitos."""
    email = serializers.EmailField(required=True)
    code = serializers.CharField(max_length=8, min_length=8, required=True)
    new_password = serializers.CharField(min_length=8, required=True, write_only=True)

    def validate_code(self, value):
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError("O código de verificação deve conter 8 dígitos numéricos.")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A nova senha deve ter no mínimo 8 caracteres.")
        return value


class ConvidarUsuarioSerializer(serializers.Serializer):
    """Serializer para onboarding de novos colaboradores pelo Administrador."""
    nome = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(choices=Usuario.ROLE_CHOICES, default='Operador')
    permissoes = PermissaoSerializer(required=False)

    def validate_email(self, value):
        if Usuario.objects.filter(email__iexact=value, deleted_at__isnull=True).exists():
            raise serializers.ValidationError("Já existe um colaborador cadastrado com este e-mail.")
        return value.lower().strip()


class ActivateAccountSerializer(serializers.Serializer):
    """Validação da ativação de conta do convite com definição da senha inicial."""
    token = serializers.CharField(required=True)
    password = serializers.CharField(min_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(min_length=8, required=True, write_only=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "A confirmação da senha não confere."})
        return data


class AtualizarPermissoesSerializer(serializers.ModelSerializer):
    """Serializer para alteração direta dos 10 toggles dinâmicos por colaborador."""

    class Meta:
        model = Permissao
        fields = [
            'acesso_comercial',
            'acesso_tesouraria',
            'acesso_compras',
            'gestao_catalogo',
            'visao_relatorios',
            'cadastros_financeiros',
            'gestao_dicionario_uom',
            'configuracoes_globais',
            'gestao_equipe',
            'auditoria_logs_recovery',
        ]
