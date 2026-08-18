"""
Modelos de Faturamento Agregado, Conta Corrente de Clientes e Propostas da Pré-Fatura.
Em conformidade com docs/FSD.md - Entidades Fatura e FaturaPropostaPagamento.
"""
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class Fatura(BaseModel):
    """
    Título Financeiro Mestre Aglutinador de Orçamentos da Oficina.
    Comanda o Faturamento Agregado em Cascata (Rascunho -> Faturada -> Paga).
    """
    STATUS_CHOICES = [
        ('RASCUNHO', 'RASCUNHO (PRÉ-FATURA)'),
        ('FATURADA', 'FATURADA (FATURA FINAL)'),
        ('PAGA', 'PAGA (QUITADA)'),
        ('CANCELADA', 'CANCELADA'),
    ]

    cliente = models.ForeignKey(
        'cadastros.ClienteFornecedor',
        on_delete=models.PROTECT,
        related_name='faturas',
        db_column='cliente_id',
        verbose_name="Cliente"
    )
    data_emissao = models.DateField(
        default=timezone.now,
        verbose_name="Data de Emissão / Criação do Rascunho"
    )
    data_fechamento = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Data de Fechamento / Faturamento Final"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='RASCUNHO',
        db_index=True,
        verbose_name="Status da Fatura"
    )
    valor_bruto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Bruto Consolidado (R$)"
    )
    desconto_global = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Desconto Comercial Global (R$)"
    )
    valor_total_faturado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Valor Total Líquido Faturado (R$)"
    )
    regra_pagamento = models.ForeignKey(
        'financeiro.RegraPagamento',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='faturas',
        db_column='regra_pagamento_id',
        verbose_name="Condição Comercial Definitiva"
    )
    numero_nfe_venda = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Número da NF-e de Venda/Serviço"
    )
    caminho_nfe_pdf = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Caminho do PDF da DANFE"
    )
    caminho_boleto_pdf = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Caminho do PDF do Boleto"
    )
    linha_digitavel_boleto = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Linha Digitável do Boleto"
    )
    caminho_comprovante_pagamento = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Caminho do Comprovante de Pagamento"
    )
    motivo_cancelamento = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Motivo do Cancelamento"
    )

    class Meta:
        db_table = 'faturas'
        verbose_name = 'Fatura de Cliente'
        verbose_name_plural = 'Faturas de Clientes'
        ordering = ['-id']
        indexes = [
            models.Index(fields=['data_fechamento'], name='idx_fat_data_fechamento'),
            models.Index(fields=['status'], name='idx_fat_status'),
        ]

    def __str__(self):
        return f"Fatura #{self.id} - {self.cliente.nome_razao} (R$ {self.valor_total_faturado}) [{self.status}]"


class FaturaPropostaPagamento(models.Model):
    """
    Opções de Pagamento sugeridas na Pré-Fatura (Espelho enviado ao cliente).
    Permite simular diferentes prazos e personalizar descontos por opção.
    """
    id = models.BigAutoField(primary_key=True)
    fatura = models.ForeignKey(
        Fatura,
        on_delete=models.CASCADE,
        related_name='propostas_pagamento',
        db_column='fatura_id',
        verbose_name="Fatura / Pré-Fatura"
    )
    regra_pagamento = models.ForeignKey(
        'financeiro.RegraPagamento',
        on_delete=models.PROTECT,
        related_name='fatura_propostas',
        db_column='regra_pagamento_id',
        verbose_name="Condição Comercial Sugerida"
    )
    desconto_personalizado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Desconto Personalizado para a Opção (%)"
    )

    class Meta:
        db_table = 'fatura_propostas_pagamento'
        verbose_name = 'Proposta de Pagamento da Fatura'
        verbose_name_plural = 'Propostas de Pagamento das Faturas'
        constraints = [
            models.UniqueConstraint(
                fields=['fatura', 'regra_pagamento'],
                name='unique_fatura_regra_pgto'
            )
        ]

    def __str__(self):
        return f"Pré-Fatura #{self.fatura_id} - Opção: {self.regra_pagamento.nome}"
