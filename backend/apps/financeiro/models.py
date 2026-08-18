"""
Modelos de Tesouraria, Contas a Pagar/Receber, Caixa Real, Cartões Corporativos e Estornos.
Em conformidade com docs/FSD.md - Entidades ContaBancaria, CartaoCredito, FaturaCartao,
CategoriaFinanceira, MeioPagamento, RegraPagamento, LancamentoFinanceiro e LogEstorno.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class ContaBancaria(BaseModel):
    """
    Contas Bancárias e Caixas Físicos da oficina.
    Suporta limite de crédito (cheque especial) para tolerância de saldo negativo.
    """
    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da Conta / Caixa"
    )
    saldo = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Saldo Atual (R$)"
    )
    limite_credito = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Limite de Cheque Especial (R$)"
    )

    class Meta:
        db_table = 'contas_bancarias'
        verbose_name = 'Conta Bancária'
        verbose_name_plural = 'Contas Bancárias'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (Saldo: R$ {self.saldo})"


class CartaoCredito(BaseModel):
    """
    Cartões de Crédito Corporativos da empresa.
    Despesas vinculadas não debitam saldo bancário até a liquidação da fatura.
    """
    nome = models.CharField(
        max_length=100,
        verbose_name="Identificação do Cartão"
    )
    dia_vencimento = models.IntegerField(
        verbose_name="Dia de Vencimento"
    )
    dia_fechamento_padrao = models.IntegerField(
        verbose_name="Dia de Fechamento Padrão"
    )
    limite = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Limite do Cartão (R$)"
    )
    permite_limite_emergencial = models.BooleanField(
        default=False,
        verbose_name="Permite Limite Emergencial"
    )
    conta_bancaria = models.ForeignKey(
        ContaBancaria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cartoes_credito',
        db_column='conta_bancaria_id',
        verbose_name="Conta Preferencial de Pagamento"
    )

    class Meta:
        db_table = 'cartoes_credito'
        verbose_name = 'Cartão de Crédito Corporativo'
        verbose_name_plural = 'Cartões de Crédito Corporativos'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} (Limite: R$ {self.limite})"


class FaturaCartao(BaseModel):
    """
    Faturas Mensais dos Cartões de Crédito Corporativos.
    Acumulam gastos avulsos e suportam rollover de pagamentos parciais.
    """
    STATUS_CHOICES = [
        ('Aberta', 'Aberta'),
        ('Fechada', 'Fechada'),
        ('Paga', 'Paga'),
    ]

    cartao = models.ForeignKey(
        CartaoCredito,
        on_delete=models.PROTECT,
        related_name='faturas',
        db_column='cartao_id',
        verbose_name="Cartão de Crédito"
    )
    mes_referencia = models.CharField(
        max_length=7,
        verbose_name="Mês de Referência (YYYY-MM)"
    )
    data_fechamento_real = models.DateField(
        verbose_name="Data de Fechamento Real"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Aberta',
        verbose_name="Status da Fatura do Cartão"
    )

    class Meta:
        db_table = 'faturas_cartao'
        verbose_name = 'Fatura de Cartão de Crédito'
        verbose_name_plural = 'Faturas de Cartão de Crédito'
        ordering = ['-mes_referencia']
        constraints = [
            models.UniqueConstraint(
                fields=['cartao', 'mes_referencia'],
                name='unique_cartao_mes_referencia'
            )
        ]

    def __str__(self):
        return f"{self.cartao.nome} - {self.mes_referencia} ({self.status})"


class CategoriaFinanceira(BaseModel):
    """
    Árvore Hierárquica de Categorias e Subcategorias para DRE e Classificação Financeira.
    """
    TIPO_CHOICES = [
        ('Receita', 'Receita'),
        ('Despesa', 'Despesa'),
        ('Transferência', 'Transferência (Neutra pro DRE)'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da Categoria"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='Receita',
        verbose_name="Tipo de Categoria"
    )
    categoria_pai = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategorias',
        db_column='categoria_pai_id',
        verbose_name="Categoria Pai"
    )

    class Meta:
        db_table = 'categorias_financeiras'
        verbose_name = 'Categoria Financeira'
        verbose_name_plural = 'Categorias Financeiras'
        ordering = ['nome']

    def __str__(self):
        if self.categoria_pai:
            return f"{self.categoria_pai.nome} > {self.nome} ({self.tipo})"
        return f"{self.nome} ({self.tipo})"


class MeioPagamento(BaseModel):
    """
    Dicionário Central de Instrumentos Financeiros Físicos.
    Exemplos: PIX, Dinheiro, Boleto Bancário, Cartão de Crédito, Cartão de Débito, TED, Cheque.
    """
    nome = models.CharField(
        max_length=50,
        verbose_name="Nome do Meio de Pagamento"
    )
    permite_taxa_maquininha = models.BooleanField(
        default=False,
        verbose_name="Permite Desconto de Taxa de Maquininha"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Meio Ativo"
    )

    class Meta:
        db_table = 'meios_pagamento'
        verbose_name = 'Meio de Pagamento'
        verbose_name_plural = 'Meios de Pagamento'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class RegraPagamento(BaseModel):
    """
    Matriz de Prazos, Parcelamentos e Condições Comerciais.
    Exemplos: 'Boleto 30/60/90 Dias', 'Pix à Vista com 5%', 'Boleto 28 Dias'.
    """
    TIPO_COBRANCA_CHOICES = [
        ('A_VISTA', 'À Vista'),
        ('A_PRAZO', 'A Prazo'),
        ('PARCELADO', 'Parcelado'),
    ]

    nome = models.CharField(
        max_length=100,
        verbose_name="Nome da Condição Comercial"
    )
    meio_pagamento = models.ForeignKey(
        MeioPagamento,
        on_delete=models.PROTECT,
        related_name='regras_pagamento',
        db_column='meio_pagamento_id',
        verbose_name="Meio de Pagamento Vinculado"
    )
    tipo_cobranca = models.CharField(
        max_length=20,
        choices=TIPO_COBRANCA_CHOICES,
        default='A_VISTA',
        verbose_name="Tipo de Cobrança"
    )
    numero_parcelas = models.IntegerField(
        default=1,
        verbose_name="Número de Parcelas"
    )
    prazo_primeira_parcela_dias = models.IntegerField(
        default=0,
        verbose_name="Prazo da 1ª Parcela (Dias)"
    )
    intervalo_parcelas_dias = models.IntegerField(
        default=0,
        verbose_name="Intervalo entre Parcelas (Dias)"
    )
    desconto_concedido_padrao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Desconto Padrão Sugerido (%)"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Regra Ativa"
    )

    class Meta:
        db_table = 'regras_pagamento'
        verbose_name = 'Regra de Pagamento / Condição Comercial'
        verbose_name_plural = 'Regras de Pagamento / Condições Comerciais'
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.meio_pagamento.nome})"


class LancamentoFinanceiro(BaseModel):
    """
    Movimentações Financeiras de Competência (Contas a Pagar/Receber) e Caixa Real (Extrato).
    Separa estritamente previsões ('A Vencer') de liquidações reais ('Pago').
    """
    TIPO_LANCAMENTO_CHOICES = [
        ('Entrada', 'Entrada (Receita)'),
        ('Saída', 'Saída (Despesa)'),
        ('Transferência', 'Transferência Inter-Contas'),
    ]

    STATUS_PAGAMENTO_CHOICES = [
        ('A Vencer', 'A Vencer'),
        ('Vencido', 'Vencido'),
        ('Pago', 'Pago'),
        ('Cancelado', 'Cancelado'),
    ]

    fatura = models.ForeignKey(
        'faturamento.Fatura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_financeiros',
        db_column='fatura_id',
        verbose_name="Fatura Vinculada"
    )
    conta = models.ForeignKey(
        ContaBancaria,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos_origem',
        db_column='conta_id',
        verbose_name="Conta Bancária / Caixa de Origem"
    )
    conta_destino = models.ForeignKey(
        ContaBancaria,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos_destino',
        db_column='conta_destino_id',
        verbose_name="Conta Bancária de Destino (Transferência)"
    )
    meio_pagamento = models.ForeignKey(
        MeioPagamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos',
        db_column='meio_pagamento_id',
        verbose_name="Meio de Pagamento"
    )
    cartao_credito = models.ForeignKey(
        CartaoCredito,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lancamentos',
        db_column='cartao_credito_id',
        verbose_name="Cartão Corporativo Utilizado"
    )
    fatura_cartao = models.ForeignKey(
        FaturaCartao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='despesas_fatura',
        db_column='fatura_cartao_id',
        verbose_name="Fatura do Cartão"
    )
    categoria = models.ForeignKey(
        CategoriaFinanceira,
        on_delete=models.PROTECT,
        related_name='lancamentos',
        db_column='categoria_id',
        verbose_name="Categoria Financeira"
    )
    tipo_lancamento = models.CharField(
        max_length=20,
        choices=TIPO_LANCAMENTO_CHOICES,
        verbose_name="Tipo de Lançamento"
    )
    descricao = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Descrição / Histórico"
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor (R$)"
    )
    data_vencimento = models.DateField(
        db_index=True,
        verbose_name="Data de Vencimento"
    )
    data_pagamento = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Data/Hora da Baixa ou Pagamento Real"
    )
    status_pagamento = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default='A Vencer',
        db_index=True,
        verbose_name="Status do Pagamento"
    )
    motivo_cancelamento = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Motivo do Cancelamento"
    )
    is_conciliado = models.BooleanField(
        default=False,
        verbose_name="Conciliado com Extrato Bancário"
    )
    data_conciliacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Conciliação"
    )
    conciliado_por = models.ForeignKey(
        'authentication.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lancamentos_conciliados',
        db_column='conciliado_por_id',
        verbose_name="Conciliado por"
    )

    class Meta:
        db_table = 'lancamentos_financeiros'
        verbose_name = 'Lançamento Financeiro'
        verbose_name_plural = 'Lançamentos Financeiros'
        ordering = ['-data_vencimento', '-id']
        indexes = [
            models.Index(fields=['data_vencimento'], name='idx_lanc_vencimento'),
            models.Index(fields=['data_pagamento'], name='idx_lanc_pagamento'),
            models.Index(fields=['status_pagamento'], name='idx_lanc_status_pagto'),
        ]

    def __str__(self):
        return f"[{self.tipo_lancamento}] {self.descricao or self.categoria.nome} - R$ {self.valor} ({self.status_pagamento})"


class LogEstorno(models.Model):
    """
    Rastro Perpétuo e Imutável de Estornos Financeiros.
    Audita baixas de caixa canceladas com preenchimento obrigatório de justificativa.
    """
    id = models.BigAutoField(primary_key=True)
    lancamento = models.ForeignKey(
        LancamentoFinanceiro,
        on_delete=models.PROTECT,
        related_name='estornos',
        db_column='lancamento_id',
        verbose_name="Lançamento Estornado"
    )
    usuario = models.ForeignKey(
        'authentication.Usuario',
        on_delete=models.PROTECT,
        related_name='estornos_realizados',
        db_column='usuario_id',
        verbose_name="Usuário Responsável pelo Estorno"
    )
    justificativa = models.TextField(
        verbose_name="Justificativa Obrigatória do Estorno"
    )
    data_estorno = models.DateTimeField(
        default=timezone.now,
        verbose_name="Data/Hora do Estorno"
    )

    class Meta:
        db_table = 'log_estornos'
        verbose_name = 'Log de Estorno'
        verbose_name_plural = 'Logs de Estornos'
        ordering = ['-data_estorno']

    def __str__(self):
        return f"Estorno #{self.id} - Lançamento #{self.lancamento_id} por {self.usuario.nome}"
