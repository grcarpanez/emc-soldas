"""
Serializers do Catálogo Base, Dicionários Centrais, Itens, Insumos e Produtos (Motor BOM).
Em conformidade com docs/FSD.md e docs/PLANO.md (Fases 4 e 6).
"""
from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

from apps.administracao.models import ConfiguracaoGlobal
from apps.catalogo.models import (
    DicionarioUom,
    DicionarioAtributo,
    Item,
    ItemAtributoValor,
    Produto,
    FichaTecnica
)
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

        qs = DicionarioAtributo.objects.filter(nome_atributo__iexact=nome_sanitizado)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"O atributo '{nome_sanitizado}' já está cadastrado.")

        return nome_sanitizado


class ItemAtributoValorSerializer(serializers.ModelSerializer):
    """
    Serializer para valores de atributos técnicos vinculados a um Item.
    Ex: Espessura = 6.35 mm (1/4 pol), Material / Liga = ASTM A36.
    """
    atributo_nome = serializers.CharField(source='atributo.nome_atributo', read_only=True)

    class Meta:
        model = ItemAtributoValor
        fields = ['id', 'item', 'atributo', 'atributo_nome', 'valor']
        read_only_fields = ['id', 'atributo_nome']
        extra_kwargs = {
            'item': {'required': False, 'allow_null': True}
        }
        validators = []

    def validate_valor(self, value):
        valor_sanitizado = sanitizar_texto_maiusculo(value)
        if not valor_sanitizado:
            raise serializers.ValidationError("O valor do atributo técnico é obrigatório.")
        return valor_sanitizado

    def validate(self, attrs):
        item = attrs.get('item') or (self.instance.item if self.instance else None)
        atributo = attrs.get('atributo') or (self.instance.atributo if self.instance else None)

        if item and atributo:
            qs = ItemAtributoValor.objects.filter(item=item, atributo=atributo)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "atributo": f"O atributo '{atributo.nome_atributo}' já está cadastrado para este item."
                })
        return attrs


class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer completo do Catálogo de Itens / Insumos / Matérias-Primas.
    Inclui atributos dinâmicos aninhados, cálculo do custo unitário por unidade de consumo
    e contagem de produtos onde o item é utilizado.
    """
    unidade_compra_sigla = serializers.CharField(source='unidade_compra.sigla', read_only=True)
    unidade_compra_descricao = serializers.CharField(source='unidade_compra.descricao', read_only=True)
    unidade_consumo_sigla = serializers.CharField(source='unidade_consumo.sigla', read_only=True, default=None)
    unidade_consumo_descricao = serializers.CharField(source='unidade_consumo.descricao', read_only=True, default=None)

    custo_unitario_consumo = serializers.SerializerMethodField()
    total_produtos_onde_usado = serializers.SerializerMethodField()
    atributos_valores = ItemAtributoValorSerializer(many=True, required=False)

    class Meta:
        model = Item
        fields = [
            'id',
            'nome',
            'unidade_compra',
            'unidade_compra_sigla',
            'unidade_compra_descricao',
            'unidade_consumo',
            'unidade_consumo_sigla',
            'unidade_consumo_descricao',
            'fator_conversao',
            'ultimo_custo_compra',
            'data_ultima_compra',
            'tipo_uso',
            'custo_unitario_consumo',
            'total_produtos_onde_usado',
            'atributos_valores',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'unidade_compra_sigla',
            'unidade_compra_descricao',
            'unidade_consumo_sigla',
            'unidade_consumo_descricao',
            'custo_unitario_consumo',
            'total_produtos_onde_usado',
            'created_at',
            'updated_at',
        ]

    def get_custo_unitario_consumo(self, obj) -> str:
        """Calcula o custo unitário por unidade de consumo (ultimo_custo_compra / fator_conversao)."""
        ultimo_custo = Decimal(str(obj.ultimo_custo_compra or 0))
        fator = Decimal(str(obj.fator_conversao or 1))
        if fator <= Decimal('0'):
            fator = Decimal('1')
        custo_consumo = (ultimo_custo / fator).quantize(Decimal('0.0001'))
        return f"{custo_consumo:.4f}"

    def get_total_produtos_onde_usado(self, obj) -> int:
        """Retorna o número de produtos ativos que utilizam este item na sua receita BOM."""
        return FichaTecnica.objects.filter(
            item=obj,
            produto__deleted_at__isnull=True
        ).values('produto_id').distinct().count()

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome do item é obrigatório.")
        return nome_sanitizado

    def validate_fator_conversao(self, value):
        if value is None or Decimal(str(value)) <= Decimal('0'):
            raise serializers.ValidationError("O fator de conversão deve ser um número decimal maior que zero.")
        return value

    def validate_ultimo_custo_compra(self, value):
        if value is not None and Decimal(str(value)) < Decimal('0'):
            raise serializers.ValidationError("O último custo de compra não pode ser negativo.")
        return value

    def validate(self, attrs):
        unidade_compra = attrs.get('unidade_compra') or (self.instance.unidade_compra if self.instance else None)
        unidade_consumo = attrs.get('unidade_consumo')
        if not unidade_consumo and not (self.instance and self.instance.unidade_consumo):
            attrs['unidade_consumo'] = unidade_compra

        atributos_data = attrs.get('atributos_valores', [])
        atributos_ids = set()
        for a in atributos_data:
            attr = a.get('atributo')
            attr_id = getattr(attr, 'id', attr)
            if attr_id in atributos_ids:
                raise serializers.ValidationError({
                    "atributos_valores": "O mesmo atributo técnico foi informado mais de uma vez para este item."
                })
            atributos_ids.add(attr_id)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        atributos_data = validated_data.pop('atributos_valores', [])
        item = Item.objects.create(**validated_data)

        # Salva atributos técnicos vinculados
        for attr_item in atributos_data:
            ItemAtributoValor.objects.create(
                item=item,
                atributo=attr_item['atributo'],
                valor=sanitizar_texto_maiusculo(attr_item['valor'])
            )

        return item

    @transaction.atomic
    def update(self, instance, validated_data):
        atributos_data = validated_data.pop('atributos_valores', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Atualização de atributos dinâmicos se enviados
        if atributos_data is not None:
            instance.atributos_valores.all().delete()
            for attr_item in atributos_data:
                ItemAtributoValor.objects.create(
                    item=instance,
                    atributo=attr_item['atributo'],
                    valor=sanitizar_texto_maiusculo(attr_item['valor'])
                )

        return instance


class FichaTecnicaSerializer(serializers.ModelSerializer):
    """
    Serializer para o Motor BOM (Bill of Materials) - Composição da Receita do Produto.
    Calcula o subtotal de custo fracionado por insumo.
    """
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    item_nome = serializers.CharField(source='item.nome', read_only=True)
    item_unidade_consumo_sigla = serializers.SerializerMethodField()
    item_ultimo_custo_compra = serializers.DecimalField(
        source='item.ultimo_custo_compra',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    item_fator_conversao = serializers.DecimalField(
        source='item.fator_conversao',
        max_digits=12,
        decimal_places=4,
        read_only=True
    )
    item_custo_unitario_consumo = serializers.SerializerMethodField()
    subtotal_custo = serializers.SerializerMethodField()

    class Meta:
        model = FichaTecnica
        fields = [
            'id',
            'produto',
            'produto_nome',
            'item',
            'item_nome',
            'item_unidade_consumo_sigla',
            'item_ultimo_custo_compra',
            'item_fator_conversao',
            'item_custo_unitario_consumo',
            'quantidade_utilizada',
            'subtotal_custo',
        ]
        read_only_fields = [
            'id',
            'produto_nome',
            'item_nome',
            'item_unidade_consumo_sigla',
            'item_ultimo_custo_compra',
            'item_fator_conversao',
            'item_custo_unitario_consumo',
            'subtotal_custo',
        ]
        extra_kwargs = {
            'produto': {'required': False, 'allow_null': True}
        }
        validators = []

    def get_item_unidade_consumo_sigla(self, obj) -> str:
        if obj.item and obj.item.unidade_consumo:
            return obj.item.unidade_consumo.sigla
        elif obj.item and obj.item.unidade_compra:
            return obj.item.unidade_compra.sigla
        return ""

    def get_item_custo_unitario_consumo(self, obj) -> str:
        if not obj.item:
            return "0.0000"
        ultimo_custo = Decimal(str(obj.item.ultimo_custo_compra or 0))
        fator = Decimal(str(obj.item.fator_conversao or 1))
        if fator <= Decimal('0'):
            fator = Decimal('1')
        custo_consumo = (ultimo_custo / fator).quantize(Decimal('0.0001'))
        return f"{custo_consumo:.4f}"

    def get_subtotal_custo(self, obj) -> str:
        if not obj.item:
            return "0.00"
        ultimo_custo = Decimal(str(obj.item.ultimo_custo_compra or 0))
        fator = Decimal(str(obj.item.fator_conversao or 1))
        if fator <= Decimal('0'):
            fator = Decimal('1')
        custo_consumo = ultimo_custo / fator
        qtd = Decimal(str(obj.quantidade_utilizada or 0))
        subtotal = (qtd * custo_consumo).quantize(Decimal('0.01'))
        return f"{subtotal:.2f}"

    def validate_quantidade_utilizada(self, value):
        if value is None or Decimal(str(value)) <= Decimal('0'):
            raise serializers.ValidationError("A quantidade utilizada deve ser maior que zero.")
        return value

    def validate(self, attrs):
        produto = attrs.get('produto') or (self.instance.produto if self.instance else None)
        item = attrs.get('item') or (self.instance.item if self.instance else None)

        if produto and item:
            qs = FichaTecnica.objects.filter(produto=produto, item=item)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    "item": f"O item '{item.nome}' já consta na ficha técnica deste produto."
                })
        return attrs


class ProdutoSerializer(serializers.ModelSerializer):
    """
    Serializer completo de Produtos e Receitas de Produção da Oficina.
    Calcula em tempo real:
    - Custo Total de Materiais (somatório dos insumos da Ficha Técnica BOM)
    - Custo de Mão de Obra (Horas estimadas * Taxa horária das Configurações Globais)
    - Preço de Custo Apurado (Total Materiais + Total Mão de Obra)
    """
    unidade_venda_sigla = serializers.CharField(source='unidade_venda.sigla', read_only=True)
    unidade_venda_descricao = serializers.CharField(source='unidade_venda.descricao', read_only=True)

    ficha_tecnica_itens = FichaTecnicaSerializer(many=True, required=False)

    taxa_mao_de_obra_hora_aplicada = serializers.SerializerMethodField()
    custo_total_materiais = serializers.SerializerMethodField()
    custo_mao_de_obra = serializers.SerializerMethodField()
    preco_custo_apurado = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            'id',
            'nome',
            'descricao',
            'unidade_venda',
            'unidade_venda_sigla',
            'unidade_venda_descricao',
            'tempo_estimado_execucao',
            'taxa_mao_de_obra_hora_aplicada',
            'custo_total_materiais',
            'custo_mao_de_obra',
            'preco_custo_apurado',
            'ficha_tecnica_itens',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'unidade_venda_sigla',
            'unidade_venda_descricao',
            'taxa_mao_de_obra_hora_aplicada',
            'custo_total_materiais',
            'custo_mao_de_obra',
            'preco_custo_apurado',
            'created_at',
            'updated_at',
        ]

    def _get_taxa_horaria(self) -> Decimal:
        """Obtém a taxa horária vigente das configurações globais."""
        config = ConfiguracaoGlobal.get_solo()
        return Decimal(str(config.taxa_mao_de_obra_hora or 0))

    def get_taxa_mao_de_obra_hora_aplicada(self, obj) -> str:
        taxa = self._get_taxa_horaria().quantize(Decimal('0.01'))
        return f"{taxa:.2f}"

    def get_custo_total_materiais(self, obj) -> str:
        """Calcula a soma dos custos fracionados de todos os materiais da Ficha Técnica."""
        total_materiais = Decimal('0.00')
        fichas = obj.ficha_tecnica_itens.select_related('item').all()
        for f in fichas:
            if f.item:
                ultimo_custo = Decimal(str(f.item.ultimo_custo_compra or 0))
                fator = Decimal(str(f.item.fator_conversao or 1))
                if fator <= Decimal('0'):
                    fator = Decimal('1')
                custo_consumo = ultimo_custo / fator
                qtd = Decimal(str(f.quantidade_utilizada or 0))
                total_materiais += qtd * custo_consumo

        total_materiais = total_materiais.quantize(Decimal('0.01'))
        return f"{total_materiais:.2f}"

    def get_custo_mao_de_obra(self, obj) -> str:
        """Calcula o custo da mão de obra (tempo_estimado_execucao * taxa_mao_de_obra_hora)."""
        horas = Decimal(str(obj.tempo_estimado_execucao or 0))
        taxa = self._get_taxa_horaria()
        custo_mo = (horas * taxa).quantize(Decimal('0.01'))
        return f"{custo_mo:.2f}"

    def get_preco_custo_apurado(self, obj) -> str:
        """Preço de Custo Apurado = Custo Materiais + Custo Mão de Obra."""
        total_mat = Decimal(self.get_custo_total_materiais(obj))
        total_mo = Decimal(self.get_custo_mao_de_obra(obj))
        total_apurado = (total_mat + total_mo).quantize(Decimal('0.01'))
        return f"{total_apurado:.2f}"

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome do produto / serviço é obrigatório.")
        return nome_sanitizado

    def validate_descricao(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_tempo_estimado_execucao(self, value):
        if value is not None and Decimal(str(value)) < Decimal('0'):
            raise serializers.ValidationError("O tempo estimado de mão de obra não pode ser negativo.")
        return value

    def validate(self, attrs):
        ficha_data = attrs.get('ficha_tecnica_itens', [])
        itens_ids = set()
        for f in ficha_data:
            item = f.get('item')
            item_id = getattr(item, 'id', item)
            if item_id in itens_ids:
                raise serializers.ValidationError({
                    "ficha_tecnica_itens": "O mesmo insumo/item foi informado mais de uma vez na receita deste produto."
                })
            itens_ids.add(item_id)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        ficha_data = validated_data.pop('ficha_tecnica_itens', [])
        produto = Produto.objects.create(**validated_data)

        # Valida e cria itens da Ficha Técnica BOM
        for f_item in ficha_data:
            FichaTecnica.objects.create(
                produto=produto,
                item=f_item['item'],
                quantidade_utilizada=f_item['quantidade_utilizada']
            )

        return produto

    @transaction.atomic
    def update(self, instance, validated_data):
        ficha_data = validated_data.pop('ficha_tecnica_itens', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Atualiza a composição da receita BOM se enviada
        if ficha_data is not None:
            instance.ficha_tecnica_itens.all().delete()
            for f_item in ficha_data:
                FichaTecnica.objects.create(
                    produto=instance,
                    item=f_item['item'],
                    quantidade_utilizada=f_item['quantidade_utilizada']
                )

        return instance


class ProdutoCustoDetalhadoSerializer(serializers.Serializer):
    """
    Serializer de Auditoria e Memória de Cálculo Detalhada do Produto (Motor BOM).
    Exibe a discriminação matemática exata de insumos e mão de obra.
    """
    produto_id = serializers.IntegerField()
    produto_nome = serializers.CharField()
    unidade_venda = serializers.CharField()
    tempo_estimado_horas = serializers.DecimalField(max_digits=8, decimal_places=2)
    taxa_mao_de_obra_hora = serializers.DecimalField(max_digits=10, decimal_places=2)
    custo_mao_de_obra = serializers.DecimalField(max_digits=12, decimal_places=2)
    materiais = serializers.ListField(child=serializers.DictField())
    custo_total_materiais = serializers.DecimalField(max_digits=12, decimal_places=2)
    preco_custo_apurado = serializers.DecimalField(max_digits=12, decimal_places=2)
