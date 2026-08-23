"""
Serializers para o Módulo de Orçamentos Comerciais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 8).
"""
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.administracao.models import ConfiguracaoGlobal
from apps.cadastros.models import ClienteFornecedor, Equipamento
from apps.catalogo.models import Item, Produto
from apps.financeiro.models import RegraPagamento
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento
from apps.orcamentos.services import (
    calcular_custo_corrente_item,
    verificar_inadimplencia_cliente,
    cancelar_orcamento,
    renovar_validade_orcamento,
    alterar_status_operacional
)
from core.utils import sanitizar_texto_maiusculo


class OrcamentoItemSerializer(serializers.ModelSerializer):
    """
    Serializer para as linhas do orçamento.
    Suporta os 3 tipos exclusivos de itens:
    1. Produto Composto (BOM)
    2. Item / Insumo Simples
    3. Lançamento Manual Livre
    """
    subtotal_venda = serializers.SerializerMethodField()
    subtotal_custo = serializers.SerializerMethodField()
    margem_lucro_unitario = serializers.SerializerMethodField()
    margem_lucro_percentual = serializers.SerializerMethodField()
    nome_exibicao = serializers.SerializerMethodField()
    unidade_medida = serializers.SerializerMethodField()
    tipo_item = serializers.SerializerMethodField()

    produto = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.filter(deleted_at__isnull=True),
        required=False,
        allow_null=True
    )
    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.filter(deleted_at__isnull=True),
        required=False,
        allow_null=True
    )
    descricao_livre = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    quantidade = serializers.DecimalField(
        max_digits=12,
        decimal_places=4,
        required=False,
        default=Decimal('1.0000')
    )
    custo_snapshot = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    valor_venda_snapshot = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    item_nome = serializers.CharField(source='item.nome', read_only=True)

    class Meta:
        model = OrcamentoItem
        fields = [
            'id',
            'orcamento',
            'produto',
            'produto_nome',
            'item',
            'item_nome',
            'descricao_livre',
            'quantidade',
            'custo_snapshot',
            'valor_venda_snapshot',
            'subtotal_venda',
            'subtotal_custo',
            'margem_lucro_unitario',
            'margem_lucro_percentual',
            'nome_exibicao',
            'unidade_medida',
            'tipo_item'
        ]
        read_only_fields = ['id', 'orcamento']
        validators = []

    def get_tipo_item(self, obj):
        if obj.produto_id:
            return 'PRODUTO'
        elif obj.item_id:
            return 'ITEM'
        return 'LIVRE'

    def get_nome_exibicao(self, obj):
        if obj.produto:
            return obj.produto.nome
        elif obj.item:
            return obj.item.nome
        return obj.descricao_livre or "ITEM AVULSO"

    def get_unidade_medida(self, obj):
        if obj.produto and obj.produto.unidade_venda:
            return obj.produto.unidade_venda.sigla
        elif obj.item and obj.item.unidade_compra:
            return obj.item.unidade_compra.sigla
        return "UN"

    def get_subtotal_venda(self, obj):
        qtd = obj.quantidade or Decimal('1.0000')
        venda = obj.valor_venda_snapshot or Decimal('0.00')
        return float((qtd * venda).quantize(Decimal('0.01')))

    def get_subtotal_custo(self, obj):
        qtd = obj.quantidade or Decimal('1.0000')
        custo = obj.custo_snapshot or Decimal('0.00')
        return float((qtd * custo).quantize(Decimal('0.01')))

    def get_margem_lucro_unitario(self, obj):
        venda = obj.valor_venda_snapshot or Decimal('0.00')
        custo = obj.custo_snapshot or Decimal('0.00')
        return float((venda - custo).quantize(Decimal('0.01')))

    def get_margem_lucro_percentual(self, obj):
        venda = obj.valor_venda_snapshot or Decimal('0.00')
        custo = obj.custo_snapshot or Decimal('0.00')
        if venda > 0:
            return float((((venda - custo) / venda) * 100).quantize(Decimal('0.01')))
        return 0.0

    def validate(self, attrs):
        produto = attrs.get('produto') or (self.instance.produto if self.instance else None)
        item = attrs.get('item') or (self.instance.item if self.instance else None)
        descricao_livre = attrs.get('descricao_livre') or (self.instance.descricao_livre if self.instance else None)

        # Regra de Exclusividade: exatamente 1 tipo preenchido
        tipos_preenchidos = sum(1 for val in [produto, item, bool(descricao_livre and str(descricao_livre).strip())] if val)

        if tipos_preenchidos == 0:
            raise ValidationError(
                "A linha do orçamento deve conter um Produto Composto, um Item Simples ou uma Descrição Livre."
            )
        if tipos_preenchidos > 1:
            raise ValidationError(
                "A linha do orçamento não pode misturar tipos. Informe apenas um entre Produto, Item ou Descrição Livre."
            )

        # Sanitização da descrição livre se informada
        if descricao_livre:
            attrs['descricao_livre'] = sanitizar_texto_maiusculo(str(descricao_livre).strip())

        # Validação de quantidade
        quantidade = attrs.get('quantidade') or (self.instance.quantidade if self.instance else Decimal('1.0000'))
        if quantidade <= Decimal('0.0000'):
            raise ValidationError({'quantidade': "A quantidade deve ser maior que zero."})

        # Preenchimento automático de custo_snapshot caso não fornecido
        custo_snapshot = attrs.get('custo_snapshot')
        if custo_snapshot is None:
            if produto:
                attrs['custo_snapshot'] = produto.preco_custo_apurado
            elif item:
                attrs['custo_snapshot'] = item.ultimo_custo_compra or Decimal('0.00')
            else:
                attrs['custo_snapshot'] = Decimal('0.00')

        # Validação do valor de venda
        valor_venda = attrs.get('valor_venda_snapshot')
        if valor_venda is None:
            # Se não informado, sugere pelo menos o custo ou valor zero
            attrs['valor_venda_snapshot'] = attrs.get('custo_snapshot', Decimal('0.00'))

        return attrs


class OrcamentoPropostaPagamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para opções e propostas comerciais de pagamento vinculadas ao orçamento.
    """
    regra_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=RegraPagamento.objects.filter(deleted_at__isnull=True)
    )
    desconto_personalizado = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    nome_regra = serializers.CharField(source='regra_pagamento.nome', read_only=True)
    meio_pagamento_nome = serializers.CharField(source='regra_pagamento.meio_pagamento.nome', read_only=True)
    tipo_cobranca = serializers.CharField(source='regra_pagamento.tipo_cobranca', read_only=True)
    numero_parcelas = serializers.IntegerField(source='regra_pagamento.numero_parcelas', read_only=True)
    prazo_primeira_parcela_dias = serializers.IntegerField(source='regra_pagamento.prazo_primeira_parcela_dias', read_only=True)
    intervalo_parcelas_dias = serializers.IntegerField(source='regra_pagamento.intervalo_parcelas_dias', read_only=True)
    desconto_efetivo_percentual = serializers.SerializerMethodField()
    valor_total_estimado = serializers.SerializerMethodField()
    valor_parcela_estimada = serializers.SerializerMethodField()

    class Meta:
        model = OrcamentoPropostaPagamento
        fields = [
            'id',
            'orcamento',
            'regra_pagamento',
            'nome_regra',
            'meio_pagamento_nome',
            'tipo_cobranca',
            'numero_parcelas',
            'prazo_primeira_parcela_dias',
            'intervalo_parcelas_dias',
            'desconto_personalizado',
            'desconto_efetivo_percentual',
            'valor_total_estimado',
            'valor_parcela_estimada'
        ]
        read_only_fields = ['id', 'orcamento']
        validators = []

    def get_desconto_efetivo_percentual(self, obj):
        if obj.desconto_personalizado is not None:
            return float(obj.desconto_personalizado)
        return float(obj.regra_pagamento.desconto_concedido_padrao or Decimal('0.00'))

    def get_valor_total_estimado(self, obj):
        valor_base = obj.orcamento.valor_liquido if obj.orcamento else Decimal('0.00')
        desc = Decimal(str(self.get_desconto_efetivo_percentual(obj)))
        if desc > Decimal('0.00'):
            total = valor_base * (Decimal('1.00') - (desc / Decimal('100.00')))
        else:
            total = valor_base
        return float(total.quantize(Decimal('0.01')))

    def get_valor_parcela_estimada(self, obj):
        total = Decimal(str(self.get_valor_total_estimado(obj)))
        num_parc = max(obj.regra_pagamento.numero_parcelas or 1, 1)
        return float((total / Decimal(num_parc)).quantize(Decimal('0.01')))

    def validate_desconto_personalizado(self, value):
        if value is not None:
            if value < Decimal('0.00') or value > Decimal('100.00'):
                raise ValidationError("O desconto personalizado deve estar entre 0.00% e 100.00%.")
        return value


class OrcamentoSerializer(serializers.ModelSerializer):
    """
    Serializer padrão para listagem, criação e edição de Orçamentos Comerciais.
    Suporta criação e atualização aninhada de itens e propostas de pagamento.
    """
    itens = OrcamentoItemSerializer(many=True, required=False, source='itens_orcamento')
    propostas_pagamento = OrcamentoPropostaPagamentoSerializer(many=True, required=False)

    cliente_nome = serializers.CharField(source='cliente.nome_razao', read_only=True)
    cliente_cnpj_cpf = serializers.CharField(source='cliente.cnpj_cpf', read_only=True)
    cliente_telefone = serializers.CharField(source='cliente.telefone', read_only=True)
    equipamento_descricao = serializers.CharField(source='equipamento.descricao', read_only=True)
    equipamento_placa = serializers.CharField(source='equipamento.placa', read_only=True)

    data_geracao = serializers.DateField(required=False)
    data_validade = serializers.DateField(required=False)

    valor_liquido = serializers.SerializerMethodField()
    is_expirado = serializers.SerializerMethodField()
    total_itens = serializers.SerializerMethodField()
    cliente_inadimplente = serializers.SerializerMethodField()

    class Meta:
        model = Orcamento
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'cliente_cnpj_cpf',
            'cliente_telefone',
            'equipamento',
            'equipamento_descricao',
            'equipamento_placa',
            'fatura',
            'data_geracao',
            'data_validade',
            'status_operacional',
            'status_financeiro',
            'valor_bruto',
            'valor_desconto_aplicado',
            'valor_liquido',
            'is_expirado',
            'cliente_inadimplente',
            'total_itens',
            'motivo_cancelamento',
            'itens',
            'propostas_pagamento',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'fatura',
            'status_financeiro',
            'motivo_cancelamento',
            'created_at',
            'updated_at'
        ]

    def get_valor_liquido(self, obj):
        return float(obj.valor_liquido)

    def get_is_expirado(self, obj):
        if obj.data_validade:
            return obj.data_validade < timezone.now().date()
        return False

    def get_total_itens(self, obj):
        return obj.itens_orcamento.count()

    def get_cliente_inadimplente(self, obj):
        # Checa status de inadimplência em tempo real
        res = verificar_inadimplencia_cliente(obj.cliente_id)
        return res['inadimplente']

    def validate(self, attrs):
        cliente = attrs.get('cliente') or (self.instance.cliente if self.instance else None)
        if not cliente:
            raise ValidationError({'cliente': "O cliente é obrigatório para a geração do orçamento."})

        # Validação do equipamento se fornecido
        equipamento = attrs.get('equipamento') or (self.instance.equipamento if self.instance else None)

        # Se data_geracao não for informada, define a data de hoje (date puro)
        if not attrs.get('data_geracao') and not (self.instance and self.instance.data_geracao):
            attrs['data_geracao'] = timezone.localdate()

        dt_geracao = attrs.get('data_geracao') or (self.instance.data_geracao if self.instance else timezone.localdate())

        # Se data_validade não for informada na criação, calcula automaticamente
        if not attrs.get('data_validade') and not (self.instance and self.instance.data_validade):
            config = ConfiguracaoGlobal.get_solo()
            dias = config.validade_orcamento_dias or 15
            attrs['data_validade'] = dt_geracao + timedelta(days=dias)

        # Validação do valor de desconto
        valor_desconto = attrs.get('valor_desconto_aplicado', Decimal('0.00'))
        if valor_desconto < Decimal('0.00'):
            raise ValidationError({'valor_desconto_aplicado': "O valor do desconto não pode ser negativo."})

        return attrs

    def create(self, validated_data):
        itens_data = validated_data.pop('itens_orcamento', [])
        propostas_data = validated_data.pop('propostas_pagamento', [])

        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            validated_data['created_by_id'] = user.id
            validated_data['updated_by_id'] = user.id

        with transaction.atomic():
            orcamento = Orcamento.objects.create(**validated_data)

            valor_bruto_acumulado = Decimal('0.00')

            # Criação dos itens do orçamento
            for item_dict in itens_data:
                # Preenche custo_snapshot caso não informado
                if 'custo_snapshot' not in item_dict or item_dict['custo_snapshot'] is None:
                    if item_dict.get('produto'):
                        item_dict['custo_snapshot'] = item_dict['produto'].preco_custo_apurado
                    elif item_dict.get('item'):
                        item_dict['custo_snapshot'] = item_dict['item'].ultimo_custo_compra or Decimal('0.00')
                    else:
                        item_dict['custo_snapshot'] = Decimal('0.00')

                item_obj = OrcamentoItem.objects.create(orcamento=orcamento, **item_dict)
                valor_bruto_acumulado += item_obj.quantidade * item_obj.valor_venda_snapshot

            # Atualiza o valor bruto total
            if valor_bruto_acumulado > Decimal('0.00'):
                orcamento.valor_bruto = valor_bruto_acumulado
                orcamento.save(update_fields=['valor_bruto'])

            # Criação das propostas de pagamento
            for prop_dict in propostas_data:
                OrcamentoPropostaPagamento.objects.create(orcamento=orcamento, **prop_dict)

        return orcamento

    def update(self, instance, validated_data):
        itens_data = validated_data.pop('itens_orcamento', None)
        propostas_data = validated_data.pop('propostas_pagamento', None)

        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            validated_data['updated_by_id'] = user.id

        # Não permite editar orçamentos concluídos ou cancelados
        if instance.status_operacional in ['CONCLUIDO', 'CANCELADO']:
            raise ValidationError({
                'status_operacional': f"Não é permitido editar um orçamento com status '{instance.get_status_operacional_display()}'."
            })

        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Se itens_data foi explicitamente enviado, sincroniza
            if itens_data is not None:
                instance.itens_orcamento.all().delete()
                valor_bruto_acumulado = Decimal('0.00')
                for item_dict in itens_data:
                    if 'custo_snapshot' not in item_dict or item_dict['custo_snapshot'] is None:
                        if item_dict.get('produto'):
                            item_dict['custo_snapshot'] = item_dict['produto'].preco_custo_apurado
                        elif item_dict.get('item'):
                            item_dict['custo_snapshot'] = item_dict['item'].ultimo_custo_compra or Decimal('0.00')
                        else:
                            item_dict['custo_snapshot'] = Decimal('0.00')

                    item_obj = OrcamentoItem.objects.create(orcamento=instance, **item_dict)
                    valor_bruto_acumulado += item_obj.quantidade * item_obj.valor_venda_snapshot

                instance.valor_bruto = valor_bruto_acumulado
                instance.save(update_fields=['valor_bruto'])

            # Se propostas_data foi enviado, sincroniza
            if propostas_data is not None:
                instance.propostas_pagamento.all().delete()
                for prop_dict in propostas_data:
                    OrcamentoPropostaPagamento.objects.create(orcamento=instance, **prop_dict)

        return instance


class OrcamentoDetailSerializer(OrcamentoSerializer):
    """
    Serializer detalhado para visualização completa do Orçamento,
    com métricas consolidadas de custo, margem e alerta de inadimplência.
    """
    total_custo_snapshot = serializers.SerializerMethodField()
    margem_lucro_total = serializers.SerializerMethodField()
    margem_lucro_percentual = serializers.SerializerMethodField()
    alerta_inadimplencia = serializers.SerializerMethodField()

    class Meta(OrcamentoSerializer.Meta):
        fields = OrcamentoSerializer.Meta.fields + [
            'total_custo_snapshot',
            'margem_lucro_total',
            'margem_lucro_percentual',
            'alerta_inadimplencia'
        ]

    def get_total_custo_snapshot(self, obj):
        total = Decimal('0.00')
        for item in obj.itens_orcamento.all():
            total += (item.quantidade or Decimal('1.00')) * (item.custo_snapshot or Decimal('0.00'))
        return float(total.quantize(Decimal('0.01')))

    def get_margem_lucro_total(self, obj):
        venda_liq = obj.valor_liquido
        custo = Decimal(str(self.get_total_custo_snapshot(obj)))
        return float((venda_liq - custo).quantize(Decimal('0.01')))

    def get_margem_lucro_percentual(self, obj):
        venda_liq = obj.valor_liquido
        margem = Decimal(str(self.get_margem_lucro_total(obj)))
        if venda_liq > Decimal('0.00'):
            return float(((margem / venda_liq) * 100).quantize(Decimal('0.01')))
        return 0.0

    def get_alerta_inadimplencia(self, obj):
        res = verificar_inadimplencia_cliente(obj.cliente_id)
        return res


class CancelarOrcamentoSerializer(serializers.Serializer):
    """
    Serializer para a ação de cancelamento justificado obrigatório.
    """
    motivo_cancelamento = serializers.CharField(
        min_length=10,
        max_length=500,
        required=True,
        error_messages={
            'min_length': "O motivo do cancelamento deve conter no mínimo 10 caracteres.",
            'blank': "O motivo do cancelamento é obrigatório."
        }
    )


class RenovarOrcamentoSerializer(serializers.Serializer):
    """
    Serializer para a ação de renovação de validade e re-precificação.
    """
    dias_validade = serializers.IntegerField(
        required=False,
        default=None,
        min_value=1,
        max_value=365
    )
    atualizar_precos = serializers.BooleanField(
        required=False,
        default=False
    )
    novos_precos_itens = serializers.DictField(
        required=False,
        default=dict,
        child=serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    )


class AlterarStatusOperacionalSerializer(serializers.Serializer):
    """
    Serializer para transições da máquina de estados operacional.
    """
    novo_status = serializers.ChoiceField(
        choices=Orcamento.STATUS_OPERACIONAL_CHOICES,
        required=True
    )
