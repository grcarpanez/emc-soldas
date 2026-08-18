"""
Modelos de Orçamentos Comerciais, Itens com Snapshot e Propostas de Pagamento.
Em conformidade com docs/FSD.md - Entidades Orcamento, OrcamentoItem e OrcamentoPropostaPagamento.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class Orcamento(BaseModel):
    """
    Orçamentos Comerciais da oficina.
    Possui duplo acompanhamento (Status Operacional vs Status Financeiro),
    snapshots de custos, validade com proteção de margem e cancelamento justificado.
    """
    STATUS_OPERACIONAL_CHOICES = [
        ('Gerado', 'Gerado'),
        ('Enviado', 'Enviado'),
        ('Aprovado', 'Aprovado'),
        ('Em Execução', 'Em Execução'),
        ('Concluído', 'Concluído'),
        ('Cancelado', 'Cancelado'),
    ]

    STATUS_FINANCEIRO_CHOICES = [
        ('A Faturar', 'A Faturar'),
        ('Faturado', 'Faturado'),
        ('Pago', 'Pago'),
        ('Cancelado', 'Cancelado'),
    ]

    cliente = models.ForeignKey(
        'cadastros.ClienteFornecedor',
        on_delete=models.PROTECT,
        related_name='orcamentos',
        db_column='cliente_id',
        verbose_name="Cliente"
    )
    equipamento = models.ForeignKey(
        'cadastros.Equipamento',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='orcamentos',
        db_column='equipamento_id',
        verbose_name="Equipamento / Veículo"
    )
    fatura = models.ForeignKey(
        'faturamento.Fatura',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamentos_agrupados',
        db_column='fatura_id',
        verbose_name="Fatura Vinculada"
    )
    data_geracao = models.DateField(
        default=timezone.now,
        db_index=True,
        verbose_name="Data de Geração"
    )
    data_validade = models.DateField(
        verbose_name="Data de Validade da Proposta"
    )
    status_operacional = models.CharField(
        max_length=20,
        choices=STATUS_OPERACIONAL_CHOICES,
        default='Gerado',
        db_index=True,
        verbose_name="Status Operacional / Produtivo"
    )
    status_financeiro = models.CharField(
        max_length=20,
        choices=STATUS_FINANCEIRO_CHOICES,
        default='A Faturar',
        db_index=True,
        verbose_name="Status Financeiro"
    )
    valor_bruto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Bruto Total (R$)"
    )
    valor_desconto_aplicado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor de Desconto Aplicado (R$)"
    )
    motivo_cancelamento = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Motivo do Cancelamento"
    )

    class Meta:
        db_table = 'orcamentos'
        verbose_name = 'Orçamento Comercial'
        verbose_name_plural = 'Orçamentos Comerciais'
        ordering = ['-data_geracao', '-id']
        indexes = [
            models.Index(fields=['data_geracao'], name='idx_orc_data_geracao'),
            models.Index(fields=['status_operacional'], name='idx_orc_status_oper'),
            models.Index(fields=['status_financeiro'], name='idx_orc_status_fin'),
        ]

    def __str__(self):
        return f"Orçamento #{self.id} - {self.cliente.nome_razao} (R$ {self.valor_liquido})"

    @property
    def valor_liquido(self):
        """Retorna o valor líquido após desconto."""
        return max(self.valor_bruto - self.valor_desconto_aplicado, 0.0)


class OrcamentoItem(models.Model):
    """
    Linhas do Orçamento: suporta Produtos Compostos, Itens Simples ou Lançamentos Manuais Livres.
    Armazena snapshot imutável do custo e do valor de venda no momento da inserção.
    """
    id = models.BigAutoField(primary_key=True)
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='itens_orcamento',
        db_column='orcamento_id',
        verbose_name="Orçamento Pai"
    )
    produto = models.ForeignKey(
        'catalogo.Produto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamento_itens',
        db_column='produto_id',
        verbose_name="Produto Composto (BOM)"
    )
    item = models.ForeignKey(
        'catalogo.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orcamento_itens',
        db_column='item_id',
        verbose_name="Item / Insumo Simples"
    )
    descricao_livre = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Descrição Livre (Lançamento Manual)"
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1.0000,
        verbose_name="Quantidade"
    )
    custo_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Custo Unitário Snapshot (R$)"
    )
    valor_venda_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor de Venda Unitário Snapshot (R$)"
    )

    class Meta:
        db_table = 'orcamento_itens'
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'

    def __str__(self):
        nome = self.descricao_livre or (self.produto.nome if self.produto else (self.item.nome if self.item else "Item Avulso"))
        return f"{self.quantidade} x {nome} (R$ {self.valor_venda_snapshot})"


class OrcamentoPropostaPagamento(models.Model):
    """
    Opções de Pagamento sugeridas na visualização/PDF do Orçamento.
    Garante que a mesma regra não se repita no mesmo orçamento.
    """
    id = models.BigAutoField(primary_key=True)
    orcamento = models.ForeignKey(
        Orcamento,
        on_delete=models.CASCADE,
        related_name='propostas_pagamento',
        db_column='orcamento_id',
        verbose_name="Orçamento"
    )
    regra_pagamento = models.ForeignKey(
        'financeiro.RegraPagamento',
        on_delete=models.PROTECT,
        related_name='orcamento_propostas',
        db_column='regra_pagamento_id',
        verbose_name="Condição Comercial / Regra de Pagamento"
    )
    desconto_personalizado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Desconto Personalizado (%)"
    )

    class Meta:
        db_table = 'orcamento_propostas_pagamento'
        verbose_name = 'Proposta de Pagamento do Orçamento'
        verbose_name_plural = 'Propostas de Pagamento dos Orçamentos'
        constraints = [
            models.UniqueConstraint(
                fields=['orcamento', 'regra_pagamento'],
                name='unique_orcamento_regra_pgto'
            )
        ]

    def __str__(self):
        return f"Orçamento #{self.orcamento_id} - {self.regra_pagamento.nome}"
