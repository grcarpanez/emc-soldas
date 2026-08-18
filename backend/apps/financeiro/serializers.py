"""
Serializers do Módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4).
"""
from decimal import Decimal
from rest_framework import serializers
from apps.financeiro.models import (
    CategoriaFinanceira,
    ContaBancaria,
    MeioPagamento,
    RegraPagamento,
    CartaoCredito,
    FaturaCartao,
    LancamentoFinanceiro,
    LogEstorno
)
from core.utils import sanitizar_texto_maiusculo


class CategoriaFinanceiraSerializer(serializers.ModelSerializer):
    """Serializer para a Árvore Hierárquica de Categorias Financeiras (DRE)."""
    categoria_pai_nome = serializers.CharField(
        source='categoria_pai.nome',
        read_only=True,
        allow_null=True
    )
    subcategorias_count = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaFinanceira
        fields = [
            'id',
            'nome',
            'tipo',
            'categoria_pai',
            'categoria_pai_nome',
            'subcategorias_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_subcategorias_count(self, obj):
        return obj.subcategorias.filter(deleted_at__isnull=True).count()

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome da categoria financeira é obrigatório.")
        return nome_sanitizado

    def validate(self, attrs):
        categoria_pai = attrs.get('categoria_pai')
        
        # Prevenção de auto-referência direta
        if self.instance and categoria_pai:
            if categoria_pai.id == self.instance.id:
                raise serializers.ValidationError({
                    "categoria_pai": "Uma categoria não pode ser subcategoria de si mesma."
                })

            # Prevenção de ciclos recursivos (A -> B -> A)
            pai_atual = categoria_pai
            while pai_atual is not None:
                if pai_atual.id == self.instance.id:
                    raise serializers.ValidationError({
                        "categoria_pai": "Esta seleção geraria um ciclo hierárquico inválido."
                    })
                pai_atual = pai_atual.categoria_pai

        return attrs


class ContaBancariaSerializer(serializers.ModelSerializer):
    """Serializer para Contas Bancárias e Caixas Físicos (com Cheque Especial)."""

    class Meta:
        model = ContaBancaria
        fields = [
            'id',
            'nome',
            'saldo',
            'limite_credito',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome da conta bancária é obrigatório.")
        return nome_sanitizado

    def validate_limite_credito(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("O limite de cheque especial não pode ser negativo.")
        return value


class MeioPagamentoSerializer(serializers.ModelSerializer):
    """Serializer para Instrumentos Financeiros Físicos (PIX, Dinheiro, Boleto, etc.)."""

    class Meta:
        model = MeioPagamento
        fields = [
            'id',
            'nome',
            'permite_taxa_maquininha',
            'ativo',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome do meio de pagamento é obrigatório.")

        qs = MeioPagamento.objects.filter(nome__iexact=nome_sanitizado)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"O meio de pagamento '{nome_sanitizado}' já está cadastrado.")

        return nome_sanitizado


class RegraPagamentoSerializer(serializers.ModelSerializer):
    """Serializer para Matriz de Prazos, Parcelamentos e Condições Comerciais."""
    meio_pagamento_nome = serializers.CharField(
        source='meio_pagamento.nome',
        read_only=True
    )
    permite_taxa_maquininha = serializers.BooleanField(
        source='meio_pagamento.permite_taxa_maquininha',
        read_only=True
    )

    class Meta:
        model = RegraPagamento
        fields = [
            'id',
            'nome',
            'meio_pagamento',
            'meio_pagamento_nome',
            'permite_taxa_maquininha',
            'tipo_cobranca',
            'numero_parcelas',
            'prazo_primeira_parcela_dias',
            'intervalo_parcelas_dias',
            'desconto_concedido_padrao',
            'ativo',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome da condição comercial é obrigatório.")
        return nome_sanitizado

    def validate_numero_parcelas(self, value):
        if value < 1:
            raise serializers.ValidationError("O número de parcelas deve ser no mínimo 1.")
        return value

    def validate_prazo_primeira_parcela_dias(self, value):
        if value < 0:
            raise serializers.ValidationError("O prazo da primeira parcela não pode ser negativo.")
        return value

    def validate_intervalo_parcelas_dias(self, value):
        if value < 0:
            raise serializers.ValidationError("O intervalo entre parcelas não pode ser negativo.")
        return value

    def validate_desconto_concedido_padrao(self, value):
        if value < Decimal('0.00') or value > Decimal('100.00'):
            raise serializers.ValidationError("O desconto sugerido deve estar entre 0% e 100%.")
        return value

    def validate(self, attrs):
        tipo_cobranca = attrs.get('tipo_cobranca', getattr(self.instance, 'tipo_cobranca', 'A_VISTA'))
        numero_parcelas = attrs.get('numero_parcelas', getattr(self.instance, 'numero_parcelas', 1))

        if tipo_cobranca == 'A_VISTA' and numero_parcelas > 1:
            raise serializers.ValidationError({
                "numero_parcelas": "Condições do tipo 'À Vista' devem ter exatamente 1 parcela."
            })

        return attrs
