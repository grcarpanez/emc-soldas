"""
Modelos de Administração, Parâmetros Globais, SMTP e Manifesto de Retenção de Logs.
Em conformidade com docs/FSD.md - Entidades ConfiguracaoGlobal e ControleArquivoLog.
"""
from django.db import models
from django.utils import timezone


class ConfiguracaoGlobal(models.Model):
    """
    Parâmetros Universais do Sistema (Registro Único - Singleton id=1).
    Armazena dados da empresa, taxa horária, validade de orçamentos,
    políticas de sessão e credenciais SMTP protegidas por criptografia AES-256.
    """
    id = models.BigAutoField(primary_key=True)
    validade_orcamento_dias = models.IntegerField(
        default=15,
        verbose_name="Validade Padrão de Orçamentos (Dias)"
    )
    taxa_mao_de_obra_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=80.00,
        verbose_name="Taxa de Mão de Obra por Hora (R$)"
    )
    razao_social = models.CharField(
        max_length=255,
        default='EMC Soldas LTDA',
        verbose_name="Razão Social da Oficina"
    )
    cnpj = models.CharField(
        max_length=20,
        default='00.000.000/0001-00',
        verbose_name="CNPJ da Oficina"
    )
    telefone_contato = models.CharField(
        max_length=20,
        default='(11) 99999-9999',
        verbose_name="Telefone de Contato"
    )
    endereco_oficina = models.CharField(
        max_length=255,
        default='Rua Industrial, 100 - Oficina',
        verbose_name="Endereço Completo"
    )
    logo_empresa_url = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Caminho / URL da Logomarca"
    )
    tempo_ociosidade_minutos = models.IntegerField(
        default=30,
        verbose_name="Tempo de Ociosidade para Soft Lock (Minutos)"
    )
    tempo_expiracao_sessao_dias = models.IntegerField(
        default=15,
        verbose_name="Validade Mestre da Sessão (Dias)"
    )
    retencao_logs_dias = models.IntegerField(
        default=30,
        verbose_name="Retenção de Arquivos de Log (Dias)"
    )
    smtp_host = models.CharField(
        max_length=255,
        default='localhost',
        verbose_name="Servidor SMTP (Host)"
    )
    smtp_port = models.IntegerField(
        default=587,
        verbose_name="Porta SMTP"
    )
    smtp_user = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Usuário SMTP"
    )
    smtp_password_encrypted = models.TextField(
        null=True,
        blank=True,
        verbose_name="Senha SMTP Criptografada (AES-256)"
    )
    smtp_use_tls = models.BooleanField(
        default=True,
        verbose_name="Utilizar TLS"
    )
    smtp_use_ssl = models.BooleanField(
        default=False,
        verbose_name="Utilizar SSL"
    )
    email_remetente_nome = models.CharField(
        max_length=150,
        default='EMC Soldas',
        verbose_name="Nome do Remetente nos Disparos"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data da Última Alteração"
    )
    updated_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Atualizado por (ID do Usuário)"
    )

    class Meta:
        db_table = 'configuracoes_globais'
        verbose_name = 'Configuração Global'
        verbose_name_plural = 'Configurações Globais'

    def __str__(self):
        return f"Configurações Globais - {self.razao_social}"

    @classmethod
    def get_solo(cls):
        """Retorna ou cria a instância única (Singleton id=1) de configurações globais."""
        instancia, _ = cls.objects.get_or_create(id=1)
        return instancia

    def save(self, *args, **kwargs):
        # Garante que sempre exista apenas o registro id=1 (Singleton)
        self.id = 1
        super().save(*args, **kwargs)


class ControleArquivoLog(models.Model):
    """
    Manifesto de Arquivos Físicos de Log Rotativo do Servidor.
    Gerencia a matemática de TTL e data de expurgo sem necessidade de renomear arquivos no disco.
    """
    id = models.BigAutoField(primary_key=True)
    caminho_arquivo_fisico = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="Caminho Físico do Arquivo (.log)"
    )
    data_criacao = models.DateField(
        default=timezone.now,
        verbose_name="Data de Criação do Log"
    )
    data_expurgo_planejada = models.DateField(
        verbose_name="Data Planejada de Expurgo (TTL)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Registro no Manifesto"
    )

    class Meta:
        db_table = 'controle_arquivos_log'
        verbose_name = 'Manifesto de Arquivo de Log'
        verbose_name_plural = 'Manifestos de Arquivos de Log'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"{self.caminho_arquivo_fisico} (Expurgo: {self.data_expurgo_planejada})"
