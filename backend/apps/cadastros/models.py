"""
Modelos de Cadastros Básicos: Clientes, Fornecedores, Equipamentos e Vínculos.
Em conformidade com docs/FSD.md - Entidades ClienteFornecedor, Equipamento, ClienteEquipamento e AnexoGeralCliente.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class ClienteFornecedor(BaseModel):
    """
    Cadastro unificado de Clientes e Fornecedores (PF/PJ).
    Suporta hierarquia top-down, validação matemática de CPF e consulta pública de CNPJ.
    """
    TIPO_CHOICES = [
        ('Cliente', 'Cliente'),
        ('Fornecedor', 'Fornecedor'),
        ('Ambos', 'Ambos'),
    ]

    TIPO_PESSOA_CHOICES = [
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    ]

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='Cliente',
        verbose_name="Tipo de Cadastro"
    )
    tipo_pessoa = models.CharField(
        max_length=2,
        choices=TIPO_PESSOA_CHOICES,
        default='PJ',
        verbose_name="Tipo de Pessoa"
    )
    nome_razao = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nome / Razão Social"
    )
    nome_fantasia = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Nome Fantasia"
    )
    cnpj_cpf = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
        verbose_name="CPF / CNPJ"
    )
    inscricao_estadual = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        verbose_name="Inscrição Estadual"
    )
    isento_ie = models.BooleanField(
        default=False,
        verbose_name="Isento de Inscrição Estadual"
    )
    email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="E-mail"
    )
    telefone = models.CharField(
        max_length=20,
        verbose_name="Telefone de Contato"
    )
    cep = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="CEP"
    )
    logradouro = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Logradouro"
    )
    numero = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Número"
    )
    complemento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Complemento"
    )
    bairro = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Bairro"
    )
    cidade = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Cidade"
    )
    uf = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        verbose_name="UF"
    )

    class Meta:
        db_table = 'clientes_fornecedores'
        verbose_name = 'Cliente / Fornecedor'
        verbose_name_plural = 'Clientes e Fornecedores'
        ordering = ['nome_razao']
        indexes = [
            models.Index(fields=['nome_razao'], name='idx_cli_forn_nome_razao'),
            models.Index(fields=['cnpj_cpf'], name='idx_cli_forn_cnpj_cpf'),
        ]

    def __str__(self):
        return f"{self.nome_razao} ({self.tipo})"


class Equipamento(BaseModel):
    """
    Equipamentos e Veículos atendidos na oficina.
    Possui histórico relacional de vínculos para que trocas de donos não afetem orçamentos passados.
    """
    identificacao_placa = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Identificação / Placa"
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name="Descrição do Equipamento"
    )

    class Meta:
        db_table = 'equipamentos'
        verbose_name = 'Equipamento / Veículo'
        verbose_name_plural = 'Equipamentos e Veículos'
        ordering = ['identificacao_placa']
        indexes = [
            models.Index(fields=['identificacao_placa'], name='idx_equip_ident_placa'),
        ]

    def __str__(self):
        return f"{self.identificacao_placa} - {self.descricao}"


class ClienteEquipamento(models.Model):
    """
    Histórico relacional de Vínculos entre Clientes e Equipamentos.
    Preserva a linha do tempo de transferências de proprietários via flag is_ativo.
    """
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(
        ClienteFornecedor,
        on_delete=models.PROTECT,
        related_name='equipamentos_vinculados',
        db_column='cliente_id',
        verbose_name="Cliente Proprietário"
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,
        related_name='historico_clientes',
        db_column='equipamento_id',
        verbose_name="Equipamento"
    )
    data_vinculo = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data do Vínculo"
    )
    is_ativo = models.BooleanField(
        default=True,
        verbose_name="Vínculo Ativo"
    )

    class Meta:
        db_table = 'cliente_equipamento'
        verbose_name = 'Vínculo Cliente-Equipamento'
        verbose_name_plural = 'Vínculos Cliente-Equipamento'
        ordering = ['-data_vinculo']

    def __str__(self):
        status = "Ativo" if self.is_ativo else "Inativo"
        return f"{self.equipamento.identificacao_placa} -> {self.cliente.nome_razao} ({status})"


class AnexoGeralCliente(models.Model):
    """
    Documentos e anexos vinculados à ficha do cliente.
    """
    id = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(
        ClienteFornecedor,
        on_delete=models.CASCADE,
        related_name='anexos',
        db_column='cliente_id',
        verbose_name="Cliente Vinculado"
    )
    nome_documento = models.CharField(
        max_length=255,
        verbose_name="Nome do Documento"
    )
    caminho_arquivo = models.CharField(
        max_length=500,
        verbose_name="Caminho do Arquivo Físico"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Envio"
    )

    class Meta:
        db_table = 'anexos_gerais_clientes'
        verbose_name = 'Anexo Geral do Cliente'
        verbose_name_plural = 'Anexos Gerais de Clientes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nome_documento} - {self.cliente.nome_razao}"
