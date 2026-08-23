"""
Serializers para o módulo de Conciliação Bancária Inteligente Split-Screen.
Valida uploads de extrato, confirmações de conciliação, lançamentos rápidos e trocas de conta.
"""
from decimal import Decimal
from rest_framework import serializers


class UploadExtratoSerializer(serializers.Serializer):
    """Valida o payload de upload do arquivo de extrato bancário (OFX ou CSV)."""
    arquivo = serializers.FileField(required=True)
    conta_id = serializers.IntegerField(required=False, allow_null=True)
    data_inicio = serializers.DateField(required=False, allow_null=True)
    data_fim = serializers.DateField(required=False, allow_null=True)

    def validate_arquivo(self, value):
        extensao = value.name.lower().split('.')[-1]
        if extensao not in ('ofx', 'csv', 'txt'):
            raise serializers.ValidationError("Formato de arquivo inválido. Envie um extrato em formato .OFX, .CSV ou .TXT.")
        
        # Limite de tamanho de upload (máximo 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("O tamanho do arquivo de extrato excede o limite máximo permitido de 10MB.")
        return value


class ConfirmarConciliacaoSerializer(serializers.Serializer):
    """Valida a confirmação de conciliação de 1 ou N lançamentos financeiros."""
    lancamento_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="Lista de IDs de lançamentos financeiros do ERP a conciliar."
    )
    conta_id = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="ID da conta bancária onde a conciliação/liquidação será efetivada."
    )
    data_conciliacao = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Data/Hora da efetivação da conciliação (opcional, default NOW)."
    )


class DesconciliarSerializer(serializers.Serializer):
    """Valida a reversão de conciliação de um lançamento financeiro."""
    lancamento_id = serializers.IntegerField(required=True, min_value=1)


class LancamentoRapidoSerializer(serializers.Serializer):
    """Valida a criação imediata de despesa/receita a partir de uma linha do extrato bancário."""
    tipo_lancamento = serializers.ChoiceField(
        choices=['ENTRADA', 'SAIDA'],
        required=True
    )
    descricao = serializers.CharField(
        max_length=255,
        required=True
    )
    valor = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        required=True
    )
    data_pagamento = serializers.DateTimeField(
        required=False,
        allow_null=True
    )
    conta_id = serializers.IntegerField(
        required=True,
        min_value=1
    )
    categoria_id = serializers.IntegerField(
        required=True,
        min_value=1
    )
    meio_pagamento_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )


class TrocarContaSerializer(serializers.Serializer):
    """Valida a alteração rápida de conta bancária de um lançamento financeiro."""
    lancamento_id = serializers.IntegerField(required=True, min_value=1)
    nova_conta_id = serializers.IntegerField(required=True, min_value=1)


class DivergenciasQuerySerializer(serializers.Serializer):
    """Valida os parâmetros de filtro para a consulta de divergências de conciliação."""
    conta_id = serializers.IntegerField(required=False, allow_null=True)
    data_inicio = serializers.DateField(required=False, allow_null=True)
    data_fim = serializers.DateField(required=False, allow_null=True)
