"""
Serializers para validação de filtros e payloads de relatórios e dashboards.
"""
from rest_framework import serializers


class FiltroPeriodoSerializer(serializers.Serializer):
    """Validador para filtros temporais padrão nos relatórios."""
    data_inicio = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d', '%d/%m/%Y'])
    data_fim = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d', '%d/%m/%Y'])
    ano = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
    periodo = serializers.CharField(required=False, allow_blank=True)
    conta_id = serializers.IntegerField(required=False)
    regime = serializers.ChoiceField(choices=['competencia', 'caixa'], required=False, default='competencia')


class DashboardFlipCardsResponseSerializer(serializers.Serializer):
    """Estrutura formal de resposta dos Flip Cards do Dashboard."""
    periodo = serializers.DictField()
    operacao = serializers.DictField()
    faturamento = serializers.DictField()
    receita = serializers.DictField()
    caixa = serializers.DictField()
    alertas = serializers.DictField()
    cards = serializers.DictField(required=False)


class CategoriaItemSerializer(serializers.Serializer):
    """Categoria individual e seu valor acumulado no mês."""
    categoria = serializers.CharField()
    valor = serializers.DecimalField(max_digits=12, decimal_places=2)


class MesGraficoSerializer(serializers.Serializer):
    """Detalhamento mensal com evolução de receitas, despesas e segregação por categorias."""
    mes = serializers.IntegerField()
    mes_nome = serializers.CharField()
    mes_sigla = serializers.CharField()
    receitas = serializers.DecimalField(max_digits=12, decimal_places=2)
    receitas_categorias = CategoriaItemSerializer(many=True, required=False)
    despesas = serializers.DecimalField(max_digits=12, decimal_places=2)
    despesas_categorias = CategoriaItemSerializer(many=True, required=False)
    resultado_liquido = serializers.DecimalField(max_digits=12, decimal_places=2)


class GraficosReceitasDespesasSerializer(serializers.Serializer):
    """Estrutura de resposta do gráfico de evolução de receitas e despesas."""
    ano = serializers.IntegerField()
    meses = MesGraficoSerializer(many=True)
    historico = MesGraficoSerializer(many=True, required=False)
    totais_ano = serializers.DictField()


class FeedAtividadeSerializer(serializers.Serializer):
    """Item individual da linha do tempo de atividades recentes."""
    tipo = serializers.CharField()
    identificador = serializers.CharField()
    titulo = serializers.CharField()
    descricao = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    data_hora = serializers.DateTimeField(required=False)
