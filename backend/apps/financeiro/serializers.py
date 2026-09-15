"""
Serializers do Módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4 e Fase 10).
"""
from decimal import Decimal
from datetime import date
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
    tipo_display = serializers.SerializerMethodField()

    class Meta:
        model = CategoriaFinanceira
        fields = [
            'id',
            'nome',
            'tipo',
            'tipo_display',
            'ativo',
            'categoria_pai',
            'categoria_pai_nome',
            'subcategorias_count',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_subcategorias_count(self, obj):
        return obj.subcategorias.filter(deleted_at__isnull=True).count()

    def get_tipo_display(self, obj):
        mapping = {
            'RECEITA': 'ENTRADA (RECEITA)',
            'DESPESA': 'SAÍDA (DESPESA)',
            'AMBOS': 'AMBOS (ENTRADA E SAÍDA)',
            'TRANSFERENCIA': 'TRANSFERÊNCIA',
        }
        return mapping.get(obj.tipo, obj.tipo)

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome da categoria financeira é obrigatório.")
        return nome_sanitizado

    def validate_tipo(self, value):
        val = sanitizar_texto_maiusculo(value)
        if val in ['ENTRADA', 'RECEITA']:
            return 'RECEITA'
        if val in ['SAIDA', 'SAÍDA', 'DESPESA']:
            return 'DESPESA'
        if val == 'AMBOS':
            return 'AMBOS'
        if val in ['TRANSFERENCIA', 'TRANSFERÊNCIA']:
            return 'TRANSFERENCIA'
        return val

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

        # Matriz de Governança: Restrições de alteração de tipo com lançamentos existentes
        if self.instance and 'tipo' in attrs:
            novo_tipo = attrs['tipo']
            tipo_atual = self.instance.tipo
            if novo_tipo != tipo_atual:
                lancamentos = self.instance.lancamentos.filter(deleted_at__isnull=True)
                if lancamentos.exists():
                    # Bloqueio de inversão direta (RECEITA <-> DESPESA)
                    if (tipo_atual == 'RECEITA' and novo_tipo == 'DESPESA') or (tipo_atual == 'DESPESA' and novo_tipo == 'RECEITA'):
                        raise serializers.ValidationError({
                            "tipo": "Não é possível inverter uma categoria de RECEITA para DESPESA (ou vice-versa) pois existem movimentações financeiras vinculadas a ela."
                        })
                    # Restrição de AMBOS para RECEITA
                    if tipo_atual == 'AMBOS' and novo_tipo == 'RECEITA':
                        if lancamentos.filter(tipo_lancamento='SAIDA').exists():
                            raise serializers.ValidationError({
                                "tipo": "Não é possível restringir esta categoria para RECEITA pois ela possui lançamentos históricos de SAÍDA (DESPESA)."
                            })
                    # Restrição de AMBOS para DESPESA
                    if tipo_atual == 'AMBOS' and novo_tipo == 'DESPESA':
                        if lancamentos.filter(tipo_lancamento='ENTRADA').exists():
                            raise serializers.ValidationError({
                                "tipo": "Não é possível restringir esta categoria para DESPESA pois ela possui lançamentos históricos de ENTRADA (RECEITA)."
                            })

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


class CartaoCreditoSerializer(serializers.ModelSerializer):
    """Serializer para Cartões de Crédito Corporativos."""
    conta_bancaria_nome = serializers.CharField(
        source='conta_bancaria.nome',
        read_only=True,
        allow_null=True
    )
    total_faturas_abertas = serializers.SerializerMethodField()

    class Meta:
        model = CartaoCredito
        fields = [
            'id',
            'nome',
            'dia_vencimento',
            'dia_fechamento_padrao',
            'limite',
            'permite_limite_emergencial',
            'conta_bancaria',
            'conta_bancaria_nome',
            'total_faturas_abertas',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_faturas_abertas(self, obj):
        return obj.faturas.filter(status='ABERTA', deleted_at__isnull=True).count()

    def validate_nome(self, value):
        nome_sanitizado = sanitizar_texto_maiusculo(value)
        if not nome_sanitizado:
            raise serializers.ValidationError("O nome do cartão é obrigatório.")
        return nome_sanitizado

    def validate_dia_vencimento(self, value):
        if value < 1 or value > 31:
            raise serializers.ValidationError("O dia de vencimento deve ser entre 1 e 31.")
        return value

    def validate_dia_fechamento_padrao(self, value):
        if value < 1 or value > 31:
            raise serializers.ValidationError("O dia de fechamento deve ser entre 1 e 31.")
        return value

    def validate_limite(self, value):
        if value < Decimal('0.00'):
            raise serializers.ValidationError("O limite do cartão não pode ser negativo.")
        return value


class LancamentoFinanceiroSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Lançamentos Financeiros (Competência e Caixa Real).
    Suporta Contas a Pagar, Contas a Receber, Extrato e Despesas de Cartão.
    """
    conta_nome = serializers.CharField(source='conta.nome', read_only=True, allow_null=True)
    conta_destino_nome = serializers.CharField(source='conta_destino.nome', read_only=True, allow_null=True)
    meio_pagamento_nome = serializers.CharField(source='meio_pagamento.nome', read_only=True, allow_null=True)
    cartao_credito_nome = serializers.CharField(source='cartao_credito.nome', read_only=True, allow_null=True)
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True)
    categoria_tipo = serializers.CharField(source='categoria.tipo', read_only=True)
    conciliado_por_nome = serializers.CharField(source='conciliado_por.nome', read_only=True, allow_null=True)
    cliente_fornecedor_nome = serializers.CharField(source='cliente_fornecedor.nome_razao', read_only=True, allow_null=True)

    class Meta:
        model = LancamentoFinanceiro
        fields = [
            'id',
            'fatura',
            'cliente_fornecedor',
            'cliente_fornecedor_nome',
            'fitid',
            'conta',
            'conta_nome',
            'conta_destino',
            'conta_destino_nome',
            'meio_pagamento',
            'meio_pagamento_nome',
            'cartao_credito',
            'cartao_credito_nome',
            'fatura_cartao',
            'categoria',
            'categoria_nome',
            'categoria_tipo',
            'tipo_lancamento',
            'descricao',
            'valor',
            'data_vencimento',
            'data_pagamento',
            'status_pagamento',
            'motivo_cancelamento',
            'is_conciliado',
            'data_conciliacao',
            'conciliado_por',
            'conciliado_por_nome',
            'comprovante',
            'nome_arquivo_comprovante',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'is_conciliado',
            'data_conciliacao',
            'conciliado_por',
            'created_at',
            'updated_at'
        ]

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'categoria_id' in data and 'categoria' not in data:
            data['categoria'] = data['categoria_id']
        if 'conta_id' in data and 'conta' not in data:
            data['conta'] = data['conta_id']
        if 'meio_pagamento_id' in data and 'meio_pagamento' not in data:
            data['meio_pagamento'] = data['meio_pagamento_id']
        if 'cartao_credito_id' in data and 'cartao_credito' not in data:
            data['cartao_credito'] = data['cartao_credito_id']
        if 'fatura_cartao_id' in data and 'fatura_cartao' not in data:
            data['fatura_cartao'] = data['fatura_cartao_id']
        return super().to_internal_value(data)

    def validate_descricao(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_valor(self, value):
        if value <= Decimal('0.00'):
            raise serializers.ValidationError("O valor do lançamento deve ser maior que zero.")
        return value

    def validate(self, attrs):
        tipo = attrs.get('tipo_lancamento', getattr(self.instance, 'tipo_lancamento', None))
        status_pagto = attrs.get('status_pagamento', getattr(self.instance, 'status_pagamento', 'A_VENCER'))
        conta = attrs.get('conta', getattr(self.instance, 'conta', None))
        cartao = attrs.get('cartao_credito', getattr(self.instance, 'cartao_credito', None))
        categoria = attrs.get('categoria', getattr(self.instance, 'categoria', None))

        # Validação de compatibilidade da categoria com o tipo de lançamento
        if categoria and tipo:
            if tipo == 'SAIDA' and categoria.tipo == 'RECEITA':
                raise serializers.ValidationError({
                    "categoria": "A categoria selecionada é exclusiva para ENTRADA (RECEITA) e não pode ser usada em um lançamento de SAÍDA."
                })
            if tipo == 'ENTRADA' and categoria.tipo == 'DESPESA':
                raise serializers.ValidationError({
                    "categoria": "A categoria selecionada é exclusiva para SAÍDA (DESPESA) e não pode ser usada em um lançamento de ENTRADA."
                })

        # Se já criado como PAGO, conta bancária é obrigatória (a menos que seja fatura de cartão em aberto)
        if status_pagto == 'PAGO' and not conta and not cartao:
            raise serializers.ValidationError({
                "conta": "A conta bancária é obrigatória para lançamentos com status PAGO."
            })

        return attrs


class FaturaCartaoSerializer(serializers.ModelSerializer):
    """Serializer para Faturas de Cartões de Crédito Corporativos."""
    cartao_nome = serializers.CharField(source='cartao.nome', read_only=True)
    total_despesas = serializers.SerializerMethodField()
    quantidade_itens = serializers.SerializerMethodField()
    despesas_detalhadas = serializers.SerializerMethodField()

    class Meta:
        model = FaturaCartao
        fields = [
            'id',
            'cartao',
            'cartao_nome',
            'mes_referencia',
            'data_fechamento_real',
            'status',
            'total_despesas',
            'quantidade_itens',
            'despesas_detalhadas',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_despesas(self, obj):
        from django.db.models import Sum
        total = obj.despesas_fatura.filter(
            tipo_lancamento='SAIDA',
            deleted_at__isnull=True
        ).exclude(
            descricao__startswith='PAGAMENTO FATURA CARTAO'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0.00')
        return float(total)

    def get_quantidade_itens(self, obj):
        return obj.despesas_fatura.filter(
            tipo_lancamento='SAIDA',
            deleted_at__isnull=True
        ).exclude(
            descricao__startswith='PAGAMENTO FATURA CARTAO'
        ).count()

    def get_despesas_detalhadas(self, obj):
        despesas = obj.despesas_fatura.filter(
            tipo_lancamento='SAIDA',
            deleted_at__isnull=True
        ).exclude(
            descricao__startswith='PAGAMENTO FATURA CARTAO'
        ).order_by('-data_vencimento', '-id')
        return LancamentoFinanceiroSerializer(despesas, many=True).data


# --- Serializers de Ações / Payloads Específicos ---

class LancamentoFinanceiroLiquidarSerializer(serializers.Serializer):
    """Payload para Liquidação / Baixa de Títulos Financeiros."""
    conta_id = serializers.IntegerField(required=True)
    meio_pagamento_id = serializers.IntegerField(required=False, allow_null=True)
    data_pagamento = serializers.DateTimeField(required=False, allow_null=True)
    valor_pago = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    valor_liquido_recebido = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    valor_iss_retido = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)


class LancamentoFinanceiroCancelarSerializer(serializers.Serializer):
    """Payload para Cancelamento de Título a Vencer."""
    motivo_cancelamento = serializers.CharField(min_length=10, max_length=500, required=True)


class LancamentoFinanceiroEstornarSerializer(serializers.Serializer):
    """Payload para Estorno Auditado de Título Pago."""
    justificativa = serializers.CharField(min_length=10, max_length=1000, required=True)


class TransferenciaInterContasSerializer(serializers.Serializer):
    """Payload para Transferência Inter-Contas Atômica."""
    conta_origem_id = serializers.IntegerField(required=True)
    conta_destino_id = serializers.IntegerField(required=True)
    valor = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    descricao = serializers.CharField(max_length=255, required=False, allow_blank=True)
    data_transferencia = serializers.DateTimeField(required=False, allow_null=True)


class RemanejarDespesaCartaoSerializer(serializers.Serializer):
    """Payload para Remanejamento de Despesa entre Faturas de Cartão."""
    nova_fatura_cartao_id = serializers.IntegerField(required=False, allow_null=True)
    novo_mes_referencia = serializers.CharField(max_length=7, required=False, allow_blank=True)


class FaturaCartaoAjustarFechamentoSerializer(serializers.Serializer):
    """Payload para Ajuste de Data de Fechamento Real de Fatura."""
    data_fechamento_real = serializers.DateField(required=True)


class FaturaCartaoLiquidarSerializer(serializers.Serializer):
    """Payload para Pagamento / Liquidação de Fatura de Cartão."""
    valor_pago = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    conta_id = serializers.IntegerField(required=False, allow_null=True)
    data_pagamento = serializers.DateTimeField(required=False, allow_null=True)


class LogEstornoSerializer(serializers.ModelSerializer):
    """Serializer para Consulta e Auditoria Perpétua de Estornos."""
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)
    lancamento_descricao = serializers.CharField(source='lancamento.descricao', read_only=True)
    lancamento_valor = serializers.DecimalField(source='lancamento.valor', max_digits=12, decimal_places=2, read_only=True)
    lancamento_tipo = serializers.CharField(source='lancamento.tipo_lancamento', read_only=True)

    class Meta:
        model = LogEstorno
        fields = [
            'id',
            'lancamento',
            'lancamento_descricao',
            'lancamento_valor',
            'lancamento_tipo',
            'usuario',
            'usuario_nome',
            'justificativa',
            'data_estorno'
        ]
        read_only_fields = fields
