"""
Modelos de Compras e Entradas: Notas Fiscais e Itens Comprados.
Em conformidade com docs/FSD.md - Entidades DocumentoFiscalCompra e NotaCompraItem.
"""
from django.db import models
from core.models import BaseModel


class DocumentoFiscalCompra(BaseModel):
    """
    Notas Fiscais de Entrada / Aquisição de Materiais e Insumos.
    Alimenta o motor de custos BOM e registra histórico de compras.
    """
    num_nota = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Número da Nota Fiscal"
    )
    chave_acesso = models.CharField(
        max_length=44,
        null=True,
        blank=True,
        verbose_name="Chave de Acesso NFe (44 dígitos)"
    )
    fornecedor = models.ForeignKey(
        'cadastros.ClienteFornecedor',
        on_delete=models.PROTECT,
        related_name='documentos_fiscais_compra',
        db_column='fornecedor_id',
        verbose_name="Fornecedor"
    )
    data_compra = models.DateField(
        db_index=True,
        verbose_name="Data da Compra"
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Total da Nota (R$)"
    )
    caminho_arquivo_anexo = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Caminho do Anexo (PDF/XML)"
    )

    class Meta:
        db_table = 'documentos_fiscais_compra'
        verbose_name = 'Nota Fiscal de Entrada'
        verbose_name_plural = 'Notas Fiscais de Entrada'
        ordering = ['-data_compra']
        indexes = [
            models.Index(fields=['num_nota'], name='idx_compra_num_nota'),
            models.Index(fields=['data_compra'], name='idx_compra_data'),
        ]

    def __str__(self):
        return f"NF {self.num_nota} - {self.fornecedor.nome_razao} ({self.data_compra})"


class NotaCompraItem(models.Model):
    """
    Itens adquiridos em cada Nota Fiscal de Compra.
    Garante que cada item apareça apenas uma vez por nota.
    """
    id = models.BigAutoField(primary_key=True)
    documento_fiscal = models.ForeignKey(
        DocumentoFiscalCompra,
        on_delete=models.CASCADE,
        related_name='itens_comprados',
        db_column='documento_fiscal_id',
        verbose_name="Nota Fiscal Pai"
    )
    item = models.ForeignKey(
        'catalogo.Item',
        on_delete=models.PROTECT,
        related_name='historico_compras',
        db_column='item_id',
        verbose_name="Item / Insumo Comprado"
    )
    quantidade_comprada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Comprada"
    )
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Valor Unitário de Compra (R$)"
    )

    class Meta:
        db_table = 'nota_compra_itens'
        verbose_name = 'Item da Nota de Compra'
        verbose_name_plural = 'Itens das Notas de Compra'
        constraints = [
            models.UniqueConstraint(
                fields=['documento_fiscal', 'item'],
                name='unique_nota_item'
            )
        ]

    def __str__(self):
        return f"{self.item.nome} - {self.quantidade_comprada} un x R$ {self.valor_unitario}"
