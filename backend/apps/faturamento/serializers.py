"""
Serializers para o Módulo de Faturamento Agregado.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 9).
"""
from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.cadastros.models import ClienteFornecedor
from apps.orcamentos.models import Orcamento
from apps.financeiro.models import RegraPagamento, MeioPagamento, ContaBancaria, LancamentoFinanceiro
from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.faturamento.services import (
    criar_pre_fatura,
    atualizar_pre_fatura,
    simular_propostas_fatura
)
from core.utils import sanitizar_texto_maiusculo


class FaturaPropostaPagamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para simulação de opções de pagamento na Pré-Fatura.
    """
    regra_pagamento_nome = serializers.CharField(source='regra_pagamento.nome', read_only=True)
    meio_pagamento_nome = serializers.CharField(source='regra_pagamento.meio_pagamento.nome', read_only=True)
    tipo_cobranca = serializers.CharField(source='regra_pagamento.tipo_cobranca', read_only=True)
    numero_parcelas = serializers.IntegerField(source='regra_pagamento.numero_parcelas', read_only=True)
    prazo_primeira_parcela_dias = serializers.IntegerField(source='regra_pagamento.prazo_primeira_parcela_dias', read_only=True)
    intervalo_parcelas_dias = serializers.IntegerField(source='regra_pagamento.intervalo_parcelas_dias', read_only=True)

    fatura = serializers.PrimaryKeyRelatedField(read_only=True)
    regra_pagamento = serializers.PrimaryKeyRelatedField(
        queryset=RegraPagamento.objects.filter(deleted_at__isnull=True, ativo=True)
    )

    class Meta:
        model = FaturaPropostaPagamento
        fields = [
            'id',
            'fatura',
            'regra_pagamento',
            'regra_pagamento_nome',
            'meio_pagamento_nome',
            'tipo_cobranca',
            'numero_parcelas',
            'prazo_primeira_parcela_dias',
            'intervalo_parcelas_dias',
            'desconto_personalizado'
        ]
        # Evita falha de UniqueTogetherValidator automático em nested writes
        validators = []


class OrcamentoResumoFaturaSerializer(serializers.ModelSerializer):
    """
    Serializer resumo de orçamentos vinculados a uma fatura.
    """
    equipamento_placa = serializers.CharField(source='equipamento.placa', read_only=True, default=None)
    equipamento_descricao = serializers.CharField(source='equipamento.descricao', read_only=True, default=None)
    valor_liquido = serializers.SerializerMethodField()
    resumo_itens = serializers.SerializerMethodField()

    class Meta:
        model = Orcamento
        fields = [
            'id',
            'cliente_id',
            'equipamento_id',
            'equipamento_placa',
            'equipamento_descricao',
            'data_geracao',
            'data_validade',
            'status_operacional',
            'status_financeiro',
            'valor_bruto',
            'valor_desconto_aplicado',
            'valor_liquido',
            'resumo_itens'
        ]

    def get_valor_liquido(self, obj):
        vb = obj.valor_bruto or Decimal('0.00')
        vd = obj.valor_desconto_aplicado or Decimal('0.00')
        return float(max(Decimal('0.00'), vb - vd))

    def get_resumo_itens(self, obj):
        itens = []
        for it in obj.itens_orcamento.all()[:3]:
            itens.append(it.nome_exibicao)
        if obj.itens_orcamento.count() > 3:
            itens.append(f"+{obj.itens_orcamento.count() - 3} itens")
        return ", ".join(itens) if itens else "SERVIÇOS DE SOLDA"


class LancamentoFaturaResumoSerializer(serializers.ModelSerializer):
    """
    Serializer resumo de parcelas no Contas a Receber geradas pela Fatura.
    """
    meio_pagamento_nome = serializers.CharField(source='meio_pagamento.nome', read_only=True, default=None)
    conta_nome = serializers.CharField(source='conta.nome', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_pagamento_display', read_only=True)

    class Meta:
        model = LancamentoFinanceiro
        fields = [
            'id',
            'tipo_lancamento',
            'status_pagamento',
            'status_display',
            'meio_pagamento',
            'meio_pagamento_nome',
            'conta',
            'conta_nome',
            'descricao',
            'valor',
            'data_vencimento',
            'data_pagamento',
            'is_conciliado'
        ]


class FaturaSerializer(serializers.ModelSerializer):
    """
    Serializer principal para listagem, criação e edição de Faturas / Pré-Faturas.
    """
    cliente_nome = serializers.CharField(source='cliente.nome_razao', read_only=True)
    cliente_cnpj_cpf = serializers.CharField(source='cliente.cnpj_cpf', read_only=True)
    regra_pagamento_nome = serializers.CharField(source='regra_pagamento.nome', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    orcamento_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    propostas_pagamento = FaturaPropostaPagamentoSerializer(many=True, required=False)
    orcamentos_agrupados = OrcamentoResumoFaturaSerializer(many=True, read_only=True)
    total_orcamentos = serializers.SerializerMethodField()
    total_recebido = serializers.SerializerMethodField()
    saldo_devedor = serializers.SerializerMethodField()

    cliente = serializers.PrimaryKeyRelatedField(
        queryset=ClienteFornecedor.objects.filter(deleted_at__isnull=True)
    )

    class Meta:
        model = Fatura
        fields = [
            'id',
            'cliente',
            'cliente_nome',
            'cliente_cnpj_cpf',
            'data_emissao',
            'data_fechamento',
            'status',
            'status_display',
            'valor_bruto',
            'desconto_global',
            'valor_total_faturado',
            'regra_pagamento',
            'regra_pagamento_nome',
            'numero_nfe_venda',
            'caminho_nfe_pdf',
            'caminho_boleto_pdf',
            'linha_digitavel_boleto',
            'caminho_comprovante_pagamento',
            'motivo_cancelamento',
            'orcamento_ids',
            'orcamentos_agrupados',
            'propostas_pagamento',
            'total_orcamentos',
            'total_recebido',
            'saldo_devedor',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'data_emissao',
            'data_fechamento',
            'status',
            'valor_bruto',
            'valor_total_faturado',
            'created_at',
            'updated_at'
        ]

    def get_total_orcamentos(self, obj):
        return obj.orcamentos_agrupados.filter(deleted_at__isnull=True).count()

    def get_total_recebido(self, obj):
        total = obj.lancamentos_financeiros.filter(
            tipo_lancamento='ENTRADA',
            status_pagamento='PAGO',
            deleted_at__isnull=True
        ).values_list('valor', flat=True)
        return float(sum(total))

    def get_saldo_devedor(self, obj):
        total_rec = self.get_total_recebido(obj)
        vf = float(obj.valor_total_faturado or 0.0)
        return max(0.0, round(vf - total_rec, 2))

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if self.instance is None:
            # Criação de nova Pré-Fatura
            orcamento_ids = attrs.get('orcamento_ids')
            if not orcamento_ids:
                raise ValidationError({'orcamento_ids': 'Informe ao menos um ID de orçamento para gerar a fatura.'})
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        cliente = validated_data.pop('cliente')
        orcamento_ids = validated_data.pop('orcamento_ids', [])
        propostas_data = validated_data.pop('propostas_pagamento', [])
        desconto_global = validated_data.get('desconto_global', Decimal('0.00'))

        fatura = criar_pre_fatura(
            cliente_id=cliente.id,
            orcamento_ids=orcamento_ids,
            propostas_pagamento=propostas_data,
            desconto_global=desconto_global,
            user=user
        )
        return fatura

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        orcamento_ids = validated_data.pop('orcamento_ids', None)
        propostas_data = validated_data.pop('propostas_pagamento', None)
        desconto_global = validated_data.get('desconto_global', None)

        fatura = atualizar_pre_fatura(
            fatura=instance,
            orcamento_ids=orcamento_ids,
            propostas_pagamento=propostas_data,
            desconto_global=desconto_global,
            user=user
        )
        return fatura


class FaturaDetailSerializer(FaturaSerializer):
    """
    Serializer detalhado para exibição completa de uma Fatura.
    Inclui parcelas a receber geradas e simulação completa de propostas.
    """
    parcelas = serializers.SerializerMethodField()
    propostas_simuladas = serializers.SerializerMethodField()

    class Meta(FaturaSerializer.Meta):
        fields = FaturaSerializer.Meta.fields + ['parcelas', 'propostas_simuladas']

    def get_parcelas(self, obj):
        parcelas = obj.lancamentos_financeiros.filter(
            tipo_lancamento='ENTRADA',
            deleted_at__isnull=True
        ).order_by('data_vencimento', 'id')
        return LancamentoFaturaResumoSerializer(parcelas, many=True).data

    def get_propostas_simuladas(self, obj):
        return simular_propostas_fatura(obj)


class FaturarFaturaSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de fechamento da Pré-Fatura (Conversão em FATURADA).
    """
    regra_pagamento_id = serializers.IntegerField(
        required=True,
        help_text="ID da Condição Comercial / Regra de Pagamento definitiva."
    )
    desconto_global = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=None,
        help_text="Desconto comercial global ajustado na negociação final (R$)."
    )
    numero_nfe_venda = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Número da NF-e emitida para os serviços."
    )

    def validate_regra_pagamento_id(self, value):
        if not RegraPagamento.objects.filter(id=value, ativo=True, deleted_at__isnull=True).exists():
            raise ValidationError("Regra de pagamento informada não existe ou está inativa.")
        return value


class ReceberFaturaSerializer(serializers.Serializer):
    """
    Serializer para registrar baixa / recebimento de pagamento na Fatura.
    """
    valor = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=True,
        help_text="Valor bruto amortizado/recebido (R$)."
    )
    conta_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID da Conta Bancária ou Caixa onde o valor foi creditado."
    )
    meio_pagamento_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID do Meio de Pagamento utilizado na liquidação."
    )
    data_pagamento = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Data/Hora da liquidação efetiva (default: agora)."
    )
    valor_liquido = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Valor líquido recebido (caso haja desconto de taxa de maquininha)."
    )

    def validate_valor(self, value):
        if value <= Decimal('0.00'):
            raise ValidationError("O valor do recebimento deve ser maior que zero.")
        return value

    def validate_conta_id(self, value):
        if value and not ContaBancaria.objects.filter(id=value, deleted_at__isnull=True).exists():
            raise ValidationError("Conta bancária informada não existe ou está inativa.")
        return value

    def validate_meio_pagamento_id(self, value):
        if value and not MeioPagamento.objects.filter(id=value, ativo=True, deleted_at__isnull=True).exists():
            raise ValidationError("Meio de pagamento informado não existe ou está inativo.")
        return value


class CortesiaFaturaSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de quitação por cortesia (100% de desconto).
    """
    motivo = serializers.CharField(
        min_length=10,
        max_length=500,
        required=True,
        help_text="Justificativa da concessão de cortesia comercial (mínimo 10 caracteres)."
    )


class CancelarFaturaSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de cancelamento de fatura com justificativa.
    """
    motivo_cancelamento = serializers.CharField(
        min_length=10,
        max_length=500,
        required=True,
        help_text="Motivo de cancelamento obrigatório (mínimo 10 caracteres)."
    )


class ContaCorrenteOrcamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para a listagem da Conta Corrente de Clientes (orçamentos faturáveis).
    """
    cliente_nome = serializers.CharField(source='cliente.nome_razao', read_only=True)
    cliente_cnpj_cpf = serializers.CharField(source='cliente.cnpj_cpf', read_only=True)
    equipamento_placa = serializers.CharField(source='equipamento.placa', read_only=True, default=None)
    equipamento_descricao = serializers.CharField(source='equipamento.descricao', read_only=True, default=None)
    valor_liquido = serializers.SerializerMethodField()
    total_itens = serializers.SerializerMethodField()
    resumo_itens = serializers.SerializerMethodField()

    class Meta:
        model = Orcamento
        fields = [
            'id',
            'cliente_id',
            'cliente_nome',
            'cliente_cnpj_cpf',
            'equipamento_id',
            'equipamento_placa',
            'equipamento_descricao',
            'data_geracao',
            'data_validade',
            'status_operacional',
            'status_financeiro',
            'valor_bruto',
            'valor_desconto_aplicado',
            'valor_liquido',
            'total_itens',
            'resumo_itens'
        ]

    def get_valor_liquido(self, obj):
        vb = obj.valor_bruto or Decimal('0.00')
        vd = obj.valor_desconto_aplicado or Decimal('0.00')
        return float(max(Decimal('0.00'), vb - vd))

    def get_total_itens(self, obj):
        return obj.itens_orcamento.count()

    def get_resumo_itens(self, obj):
        itens = []
        for it in obj.itens_orcamento.all()[:3]:
            itens.append(it.nome_exibicao)
        if obj.itens_orcamento.count() > 3:
            itens.append(f"+{obj.itens_orcamento.count() - 3} itens")
        return ", ".join(itens) if itens else "SERVIÇOS DE SOLDA"
