"""
Modelos do Catálogo Base, Dicionários Centrais, Itens, Insumos e Produtos (Motor BOM).
Em conformidade com docs/FSD.md - Entidades DicionarioUom, DicionarioAtributo, Item, ItemAtributoValor, Produto e FichaTecnica.
"""
from django.db import models
from core.models import BaseModel


class DicionarioUom(BaseModel):
    """
    Dicionário Central de Unidades de Medida Oficiais (UOM).
    Exemplos: m², cm², L, mL, kg, g, m, UN, CX, BARRA.
    """
    sigla = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Sigla da Unidade (ex: kg, m, UN)"
    )
    descricao = models.CharField(
        max_length=50,
        verbose_name="Descrição da Unidade"
    )

    class Meta:
        db_table = 'dicionario_uom'
        verbose_name = 'Unidade de Medida (UOM)'
        verbose_name_plural = 'Unidades de Medida (UOM)'
        ordering = ['sigla']

    def __str__(self):
        return f"{self.sigla} - {self.descricao}"


class DicionarioAtributo(BaseModel):
    """
    Catálogo Central de Atributos Descritivos Técnicos.
    Exemplos: Espessura, Diâmetro, Material / Liga, Rosca, Marca / Fabricante.
    """
    nome_atributo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nome do Atributo Técnico"
    )

    class Meta:
        db_table = 'dicionario_atributos'
        verbose_name = 'Atributo Descritivo'
        verbose_name_plural = 'Atributos Descritivos'
        ordering = ['nome_atributo']

    def __str__(self):
        return self.nome_atributo


class Item(BaseModel):
    """
    Catálogo de Materiais, Insumos, Ferramental e EPIs.
    Controla proporção matemática de compra para consumo e armazena último custo apurado.
    """
    TIPO_USO_CHOICES = [
        ('INSUMO_PRODUTIVO', 'INSUMO PRODUTIVO'),
        ('MATERIAL_CONSUMO', 'MATERIAL DE CONSUMO'),
        ('EPI', 'EPI'),
        ('FERRAMENTAL', 'FERRAMENTAL'),
    ]

    nome = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nome do Item / Insumo"
    )
    unidade_compra = models.ForeignKey(
        DicionarioUom,
        on_delete=models.PROTECT,
        related_name='itens_unidade_compra',
        db_column='unidade_compra_id',
        verbose_name="Unidade de Compra"
    )
    unidade_consumo = models.ForeignKey(
        DicionarioUom,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='itens_unidade_consumo',
        db_column='unidade_consumo_id',
        verbose_name="Unidade de Consumo / Fracionamento"
    )
    fator_conversao = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1.0000,
        verbose_name="Fator de Conversão (Compra -> Consumo)"
    )
    ultimo_custo_compra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Último Custo de Compra (R$)"
    )
    data_ultima_compra = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Última Compra"
    )
    tipo_uso = models.CharField(
        max_length=30,
        choices=TIPO_USO_CHOICES,
        default='INSUMO_PRODUTIVO',
        verbose_name="Tipo de Uso"
    )

    class Meta:
        db_table = 'itens'
        verbose_name = 'Item / Insumo'
        verbose_name_plural = 'Itens e Insumos'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome'], name='idx_item_nome'),
        ]

    def __str__(self):
        return f"{self.nome} ({self.unidade_compra.sigla})"


class ItemAtributoValor(models.Model):
    """
    Valores de atributos técnicos vinculados a um Item específico (Sub-grid do Item).
    Garante que o mesmo atributo técnico não se repita para o mesmo item.
    """
    id = models.BigAutoField(primary_key=True)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='atributos_valores',
        db_column='item_id',
        verbose_name="Item"
    )
    atributo = models.ForeignKey(
        DicionarioAtributo,
        on_delete=models.PROTECT,
        related_name='itens_valores',
        db_column='atributo_id',
        verbose_name="Atributo Técnico"
    )
    valor = models.CharField(
        max_length=255,
        verbose_name="Valor do Atributo"
    )

    class Meta:
        db_table = 'item_atributos_valores'
        verbose_name = 'Valor de Atributo do Item'
        verbose_name_plural = 'Valores de Atributos dos Itens'
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'atributo'],
                name='unique_item_atributo'
            )
        ]

    def __str__(self):
        return f"{self.item.nome} - {self.atributo.nome_atributo}: {self.valor}"


class Produto(BaseModel):
    """
    Produtos e Receitas de Serviços fabricados ou executados pela oficina.
    Possui tempo estimado de mão de obra e composição BOM via Ficha Técnica.
    """
    nome = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Nome do Produto / Serviço Composto"
    )
    descricao = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descrição / Especificação Técnica"
    )
    unidade_venda = models.ForeignKey(
        DicionarioUom,
        on_delete=models.PROTECT,
        related_name='produtos_unidade_venda',
        db_column='unidade_venda_id',
        verbose_name="Unidade de Venda"
    )
    tempo_estimado_execucao = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        verbose_name="Tempo Estimado de Mão de Obra (Horas)"
    )

    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto / Receita'
        verbose_name_plural = 'Produtos e Receitas'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome'], name='idx_produto_nome'),
        ]

    def __str__(self):
        return f"{self.nome} ({self.unidade_venda.sigla})"


class FichaTecnica(models.Model):
    """
    Motor de Custos BOM (Bill of Materials) - Composição do Produto.
    Vincula os insumos e frações consumidas na fabricação do produto.
    """
    id = models.BigAutoField(primary_key=True)
    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name='ficha_tecnica_itens',
        db_column='produto_id',
        verbose_name="Produto Pai"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='fichas_tecnicas_onde_usado',
        db_column='item_id',
        verbose_name="Item / Matéria-Prima Utilizada"
    )
    quantidade_utilizada = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Quantidade Utilizada (na Unidade de Consumo)"
    )

    class Meta:
        db_table = 'ficha_tecnica'
        verbose_name = 'Item da Ficha Técnica (BOM)'
        verbose_name_plural = 'Itens das Fichas Técnicas (BOM)'
        constraints = [
            models.UniqueConstraint(
                fields=['produto', 'item'],
                name='unique_produto_item_ficha'
            )
        ]

    def __str__(self):
        return f"{self.produto.nome} -> {self.quantidade_utilizada} x {self.item.nome}"
