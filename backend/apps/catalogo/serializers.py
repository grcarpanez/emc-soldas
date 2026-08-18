"""
Serializers do Catálogo Base e Dicionários Centrais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4).
"""
from rest_framework import serializers
from apps.catalogo.models import DicionarioUom, DicionarioAtributo
from core.utils import sanitizar_texto_maiusculo


class DicionarioUomSerializer(serializers.ModelSerializer):
    """Serializer para o Dicionário Central de Unidades de Medida (UOM)."""

    class Meta:
        model = DicionarioUom
        fields = ['id', 'sigla', 'descricao', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_sigla(self, value):
        sigla_sanitizada = sanitizar_texto_maiusculo(value)
        if not sigla_sanitizada:
            raise serializers.ValidationError("A sigla da unidade de medida é obrigatória.")

        # Validação de unicidade considerando apenas registros ativos (Soft Delete)
        qs = DicionarioUom.objects.filter(sigla__iexact=sigla_sanitizada)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"A sigla '{sigla_sanitizada}' já está cadastrada.")

        return sigla_sanitizada

    def validate_descricao(self, value):
        descricao_sanitizada = sanitizar_texto_maiusculo(value)
        if not descricao_sanitizada:
            raise serializers.ValidationError("A descrição da unidade de medida é obrigatória.")
        return descricao_sanitizada


class DicionarioAtributoSerializer(serializers.ModelSerializer):
    """Serializer para o Catálogo Central de Atributos Técnicos."""

    class Meta:
        model = DicionarioAtributo
        fields = ['id', 'nome_atributo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_nome_atributo(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome do atributo técnico é obrigatório.")

        # Validação de unicidade considerando apenas registros ativos
        qs = DicionarioAtributo.objects.filter(nome_atributo__iexact=nome_sanitizado)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"O atributo '{nome_sanitizado}' já está cadastrado.")

        return nome_sanitizado
