"""
Modelos de Usuários, Autenticação e Permissões Dinâmicas (RBAC).
Em conformidade com docs/FSD.md - Entidades Usuario e Permissao.
"""
from django.db import models
from core.models import BaseModel


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
