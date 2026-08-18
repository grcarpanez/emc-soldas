"""
Modelos de Usuários, Autenticação e Permissões Dinâmicas (RBAC).
Em conformidade com docs/FSD.md - Entidades Usuario e Permissao.
"""
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
from core.models import BaseModel, SoftDeleteManager


class UsuarioManager(SoftDeleteManager):
    """Manager com suporte a criação facilitada de usuários e permissões 1:1."""

    def create_user(self, email: str, password: str = None, nome: str = None, role: str = 'Operador', **extra_fields):
        email = email.lower().strip()
        nome = nome or email.split('@')[0].upper()
        user = self.create(email=email, nome=nome, role=role, **extra_fields)
        if password:
            user.set_password(password)
            user.save(update_fields=['password_hash'])
        Permissao.objects.get_or_create(usuario=user)
        return user


class Usuario(BaseModel):
    """
    Entidade de Colaboradores e Usuários do sistema.
    Suporta perfil Admin e Operador, PIN de segurança para Soft Lock,
    controle de tentativas falhas (anti-bruteforce) e colunas preparatórias para V2.
    """
    ROLE_CHOICES = [
        ('Admin', 'Administrador'),
        ('Operador', 'Operador'),
    ]

    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="E-mail de Acesso"
    )
    password_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Hash da Senha"
    )
    nome = models.CharField(
        max_length=150,
        verbose_name="Nome Completo"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Operador',
        verbose_name="Perfil de Acesso"
    )
    pin_hash = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Hash do PIN (6 dígitos)"
    )
    tentativas_login_falhas = models.IntegerField(
        default=0,
        verbose_name="Tentativas de Login Falhas"
    )
    bloqueado_ate = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloqueado até (Anti-Bruteforce)"
    )
    auth_provider = models.CharField(
        max_length=20,
        default='LOCAL',
        verbose_name="Provedor de Autenticação"
    )
    is_2fa_enabled = models.BooleanField(
        default=False,
        verbose_name="2FA Ativado"
    )
    is_ativo = models.BooleanField(
        default=True,
        verbose_name="Usuário Ativo"
    )
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Último Login"
    )

    objects = UsuarioManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.email}) - {self.role}"

    @property
    def is_admin(self) -> bool:
        return self.role == 'Admin'

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def has_pin(self) -> bool:
        return bool(self.pin_hash)

    def get_username(self) -> str:
        return self.email

    def set_password(self, raw_password: str):
        """Define o hash seguro da senha utilizando PBKDF2/Argon2 nativo do Django."""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verifica a exatidão da senha com defesa contra timing attacks."""
        if not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)

    def set_pin(self, raw_pin: str):
        """Define o hash do PIN numérico de 6 dígitos para o Soft Lock."""
        self.pin_hash = make_password(str(raw_pin).strip())

    def check_pin(self, raw_pin: str) -> bool:
        """Verifica se o PIN fornecido coincide com o hash gravado."""
        if not self.pin_hash:
            return False
        return check_password(str(raw_pin).strip(), self.pin_hash)

    def is_locked(self) -> bool:
        """Verifica se o usuário está atualmente bloqueado por anti-bruteforce."""
        if self.bloqueado_ate and self.bloqueado_ate > timezone.now():
            return True
        return False

    def registrar_falha_login(self, max_tentativas: int = 5, minutos_bloqueio: int = 60):
        """
        Incrementa contador de tentativas falhas.
        Se atingir max_tentativas (5), aplica bloqueio temporário (1 hora).
        """
        self.tentativas_login_falhas += 1
        if self.tentativas_login_falhas >= max_tentativas:
            self.bloqueado_ate = timezone.now() + timedelta(minutes=minutos_bloqueio)
        self.save(update_fields=['tentativas_login_falhas', 'bloqueado_ate', 'updated_at'])

    def resetar_falhas_login(self):
        """Reseta o contador de falhas e remove o bloqueio após login com sucesso."""
        self.tentativas_login_falhas = 0
        self.bloqueado_ate = None
        self.last_login = timezone.now()
        self.save(update_fields=['tentativas_login_falhas', 'bloqueado_ate', 'last_login', 'updated_at'])


class Permissao(models.Model):
    """
    Matriz de Permissões Granulares com 10 Toggles Dinâmicos por Usuário.
    Relacionamento 1:1 com a entidade Usuario.
    """
    id = models.BigAutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='permissoes',
        db_column='usuario_id',
        verbose_name="Usuário Vinculado"
    )
    acesso_comercial = models.BooleanField(
        default=False,
        verbose_name="1. Acesso Comercial (Orçamentos, Faturas e Clientes)"
    )
    acesso_tesouraria = models.BooleanField(
        default=False,
        verbose_name="2. Acesso à Tesouraria (Caixa, Conciliação e Estornos)"
    )
    acesso_compras = models.BooleanField(
        default=False,
        verbose_name="3. Acesso a Compras (Notas Fiscais de Entrada e Fornecedores)"
    )
    gestao_catalogo = models.BooleanField(
        default=False,
        verbose_name="4. Gestão de Catálogo (Itens, Produtos, BOM e Preços)"
    )
    visao_relatorios = models.BooleanField(
        default=True,
        verbose_name="5. Visualização de Relatórios (Curvas ABC, Inadimplência e DRE)"
    )
    cadastros_financeiros = models.BooleanField(
        default=False,
        verbose_name="6. Cadastros Financeiros (Contas Bancárias, Regras e Categorias)"
    )
    gestao_dicionario_uom = models.BooleanField(
        default=False,
        verbose_name="7. Dicionário Central UOM (Unidades de Medida e Atributos)"
    )
    configuracoes_globais = models.BooleanField(
        default=False,
        verbose_name="8. Configurações Globais (Empresa, Prazos e SMTP)"
    )
    gestao_equipe = models.BooleanField(
        default=False,
        verbose_name="9. Gestão de Equipe (Usuários, Permissões e Desbloqueio)"
    )
    auditoria_logs_recovery = models.BooleanField(
        default=False,
        verbose_name="10. Auditoria e Logs (Logs do Servidor, Expurgo e Lixeira Global)"
    )

    class Meta:
        db_table = 'permissoes'
        verbose_name = 'Permissão'
        verbose_name_plural = 'Permissões'

    def __str__(self):
        return f"Permissões de {self.usuario.nome}"


class TokenSeguranca(models.Model):
    """
    Armazena tokens de uso único para recuperação de senha (código de 8 dígitos)
    e links de convite seguro de onboarding de colaboradores.
    """
    TIPO_CHOICES = [
        ('RECOVERY', 'Recuperação de Senha'),
        ('INVITE', 'Convite de Onboarding'),
    ]

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_seguranca',
        db_column='usuario_id',
        verbose_name="Usuário"
    )
    token = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        verbose_name="Código / Token Criptográfico"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo do Token"
    )
    expira_em = models.DateTimeField(
        verbose_name="Data/Hora de Expiração"
    )
    utilizado = models.BooleanField(
        default=False,
        verbose_name="Token Utilizado"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )

    class Meta:
        db_table = 'tokens_seguranca'
        verbose_name = 'Token de Segurança'
        verbose_name_plural = 'Tokens de Segurança'
        ordering = ['-created_at']

    def __str__(self):
        return f"Token {self.tipo} - {self.usuario.email} (Utilizado: {self.utilizado})"

    @property
    def is_valido(self) -> bool:
        """Verifica se o token ainda não foi utilizado e se está dentro do prazo de validade."""
        return not self.utilizado and self.expira_em > timezone.now()
