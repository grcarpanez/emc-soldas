"""
Serializers do Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos).
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 7).
"""
from decimal import Decimal
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.cadastros.models import ClienteFornecedor
from apps.catalogo.models import Item
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem
from apps.compras.services import retroalimentar_custo_item
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos


class NotaCompraItemSerializer(serializers.ModelSerializer):
    """
    Serializer para os itens individuais adquiridos em cada Nota Fiscal de Compra.
    Garante validações numéricas e calcula o subtotal da linha.
    """
    documento_fiscal = serializers.PrimaryKeyRelatedField(
        queryset=DocumentoFiscalCompra.objects.all(),
        required=False,
        allow_null=True
    )
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.filter(deleted_at__isnull=True),
        source='item',
        write_only=True,
        required=True
    )
    item_nome = serializers.CharField(source='item.nome', read_only=True)
    item_unidade_compra_sigla = serializers.CharField(source='item.unidade_compra.sigla', read_only=True)
    item_ultimo_custo_anterior = serializers.DecimalField(
        source='item.ultimo_custo_compra',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotaCompraItem
        fields = [
            'id',
            'documento_fiscal',
            'item',
            'item_id',
            'item_nome',
            'item_unidade_compra_sigla',
            'item_ultimo_custo_anterior',
            'quantidade_comprada',
            'valor_unitario',
            'subtotal'
        ]
        read_only_fields = ['id', 'item', 'item_nome', 'item_unidade_compra_sigla', 'item_ultimo_custo_anterior', 'subtotal']
        validators = []  # Desativa UniqueTogetherValidator automático do DRF para suportar escrita aninhada segura

    def get_subtotal(self, obj) -> str:
        """Calcula a multiplicação da quantidade comprada pelo valor unitário."""
        if obj.quantidade_comprada is not None and obj.valor_unitario is not None:
            sub = Decimal(str(obj.quantidade_comprada)) * Decimal(str(obj.valor_unitario))
            return str(sub.quantize(Decimal('0.01')))
        return "0.00"

    def validate_quantidade_comprada(self, value):
        if value <= Decimal('0'):
            raise ValidationError("A quantidade comprada deve ser estritamente maior que zero.")
        return value

    def validate_valor_unitario(self, value):
        if value < Decimal('0'):
            raise ValidationError("O valor unitário de compra não pode ser negativo.")
        return value

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            # Retroalimenta custo no catálogo
            request = self.context.get('request')
            usuario = getattr(request, 'user', None) if request else None
            retroalimentar_custo_item(
                item=instance.item,
                valor_unitario=instance.valor_unitario,
                data_compra=instance.documento_fiscal.data_compra if instance.documento_fiscal else None,
                usuario=usuario
            )
            return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            # Retroalimenta custo no catálogo
            request = self.context.get('request')
            usuario = getattr(request, 'user', None) if request else None
            retroalimentar_custo_item(
                item=instance.item,
                valor_unitario=instance.valor_unitario,
                data_compra=instance.documento_fiscal.data_compra if instance.documento_fiscal else None,
                usuario=usuario
            )
            return instance


class DocumentoFiscalCompraSerializer(serializers.ModelSerializer):
    """
    Serializer principal para DocumentoFiscalCompra com suporte a itens aninhados,
    sanitização universal de número de nota, validação de 44 dígitos para NFe
    e retroalimentação automática de custos no Catálogo de Itens.
    """
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        queryset=ClienteFornecedor.objects.filter(deleted_at__isnull=True),
        source='fornecedor',
        write_only=True,
        required=True
    )
    fornecedor_nome = serializers.CharField(source='fornecedor.nome_razao', read_only=True)
    fornecedor_cnpj_cpf = serializers.CharField(source='fornecedor.cnpj_cpf', read_only=True)
    chave_acesso = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    itens_comprados = NotaCompraItemSerializer(many=True, required=False)
    total_itens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DocumentoFiscalCompra
        fields = [
            'id',
            'num_nota',
            'chave_acesso',
            'fornecedor',
            'fornecedor_id',
            'fornecedor_nome',
            'fornecedor_cnpj_cpf',
            'data_compra',
            'valor_total',
            'caminho_arquivo_anexo',
            'itens_comprados',
            'total_itens',
            'created_at',
            'updated_at',
            'created_by_id',
            'updated_by_id'
        ]
        read_only_fields = [
            'id',
            'fornecedor',
            'fornecedor_nome',
            'fornecedor_cnpj_cpf',
            'caminho_arquivo_anexo',
            'total_itens',
            'created_at',
            'updated_at',
            'created_by_id',
            'updated_by_id'
        ]

    def get_total_itens(self, obj) -> int:
        return obj.itens_comprados.count()

    def validate_num_nota(self, value):
        if not value or not str(value).strip():
            raise ValidationError("O número da nota fiscal é obrigatório.")
        return sanitizar_texto_maiusculo(str(value).strip())

    def validate_chave_acesso(self, value):
        if not value:
            return None
        digitos = limpar_apenas_digitos(value)
        if not digitos:
            return None
        if len(digitos) != 44:
            raise ValidationError("A chave de acesso da NFe deve conter exatamente 44 dígitos numéricos.")
        return digitos

    def validate_fornecedor_id(self, value):
        if value.tipo not in ['Fornecedor', 'Ambos']:
            raise ValidationError(
                f"O parceiro '{value.nome_razao}' é do tipo '{value.tipo}'. Apenas parceiros do tipo 'Fornecedor' ou 'Ambos' podem ser vinculados a notas de compra."
            )
        return value

    def validate_fornecedor(self, value):
        if value.tipo not in ['Fornecedor', 'Ambos']:
            raise ValidationError(
                f"O parceiro '{value.nome_razao}' é do tipo '{value.tipo}'. Apenas parceiros do tipo 'Fornecedor' ou 'Ambos' podem ser vinculados a notas de compra."
            )
        return value

    def validate_valor_total(self, value):
        if value <= Decimal('0'):
            raise ValidationError("O valor total da nota fiscal deve ser estritamente maior que zero.")
        return value

    def validate(self, attrs):
        # Validação do tipo de parceiro (Fornecedor / Ambos)
        fornecedor = attrs.get('fornecedor')
        if fornecedor and fornecedor.tipo not in ['Fornecedor', 'Ambos']:
            raise ValidationError({
                "fornecedor": f"O parceiro '{fornecedor.nome_razao}' é do tipo '{fornecedor.tipo}'. Apenas parceiros do tipo 'Fornecedor' ou 'Ambos' podem ser vinculados a notas de compra."
            })

        # Validação cruzada de itens se enviados no payload
        itens_data = self.initial_data.get('itens_comprados')
        if itens_data is not None:
            if not isinstance(itens_data, list):
                raise ValidationError({"itens_comprados": "O campo itens_comprados deve ser uma lista de itens."})
            
            # Validação anti-duplicação de item na mesma nota e somatório automático
            item_ids = []
            soma_itens = Decimal('0.00')
            for idx, item_dict in enumerate(itens_data):
                item_id = item_dict.get('item_id') or item_dict.get('item')
                if not item_id:
                    raise ValidationError({f"itens_comprados": f"O ID do item na posição {idx} é obrigatório."})
                if item_id in item_ids:
                    raise ValidationError({
                        "itens_comprados": f"O item ID {item_id} foi adicionado mais de uma vez nesta nota. Cada item deve constar apenas uma vez por nota fiscal."
                    })
                item_ids.append(item_id)

                try:
                    qtd = Decimal(str(item_dict.get('quantidade_comprada', 0)))
                    vlr = Decimal(str(item_dict.get('valor_unitario', 0)))
                    soma_itens += (qtd * vlr)
                except Exception:
                    pass

            # Se valor_total não foi enviado explicitamente, adota a soma calculada dos itens
            if 'valor_total' not in attrs or attrs.get('valor_total') is None:
                if soma_itens <= Decimal('0'):
                    raise ValidationError({"valor_total": "O valor total da nota fiscal deve ser estritamente maior que zero."})
                attrs['valor_total'] = soma_itens.quantize(Decimal('0.01'))
        elif 'valor_total' not in attrs or attrs.get('valor_total') is None:
            raise ValidationError({"valor_total": "O valor total da nota fiscal é obrigatório."})

        return attrs

    def create(self, validated_data):
        itens_data = validated_data.pop('itens_comprados', [])
        request = self.context.get('request')
        usuario = getattr(request, 'user', None) if request else None

        with transaction.atomic():
            doc_compra = DocumentoFiscalCompra.objects.create(**validated_data)

            for item_info in itens_data:
                item_instance = item_info['item']
                qtd = item_info['quantidade_comprada']
                vlr_unit = item_info['valor_unitario']

                NotaCompraItem.objects.create(
                    documento_fiscal=doc_compra,
                    item=item_instance,
                    quantidade_comprada=qtd,
                    valor_unitario=vlr_unit
                )

                # Retroalimenta custo no catálogo
                retroalimentar_custo_item(
                    item=item_instance,
                    valor_unitario=vlr_unit,
                    data_compra=doc_compra.data_compra,
                    usuario=usuario
                )

            return doc_compra

    def update(self, instance, validated_data):
        itens_data = validated_data.pop('itens_comprados', None)
        request = self.context.get('request')
        usuario = getattr(request, 'user', None) if request else None

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if itens_data is not None:
                # Remove itens existentes e recria com os novos dados
                instance.itens_comprados.all().delete()
                for item_info in itens_data:
                    item_instance = item_info['item']
                    qtd = item_info['quantidade_comprada']
                    vlr_unit = item_info['valor_unitario']

                    NotaCompraItem.objects.create(
                        documento_fiscal=instance,
                        item=item_instance,
                        quantidade_comprada=qtd,
                        valor_unitario=vlr_unit
                    )

                    # Retroalimenta custo no catálogo
                    retroalimentar_custo_item(
                        item=item_instance,
                        valor_unitario=vlr_unit,
                        data_compra=instance.data_compra,
                        usuario=usuario
                    )

            return instance


class HistoricoPrecoItemSerializer(serializers.Serializer):
    """
    Serializer para exibição estruturada do histórico de preços pagos por fornecedor.
    """
    documento_fiscal_id = serializers.IntegerField()
    num_nota = serializers.CharField()
    data_compra = serializers.DateField()
    fornecedor_id = serializers.IntegerField()
    fornecedor_nome = serializers.CharField()
    fornecedor_cnpj_cpf = serializers.CharField(allow_null=True)
    quantidade_comprada = serializers.DecimalField(max_digits=12, decimal_places=4)
    unidade_medida = serializers.CharField()
    valor_unitario = serializers.DecimalField(max_digits=12, decimal_places=4)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
