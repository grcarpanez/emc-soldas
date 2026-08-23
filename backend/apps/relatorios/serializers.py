"""
Serializers para validação de filtros e payloads de relatórios e dashboards.
"""
from rest_framework import serializers


class FiltroPeriodoSerializer(serializers.Serializer):
    """Validador para filtros temporais padrão nos relatórios."""
    data_inicio = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d', '%d/%m/%Y'])
    data_fim = serializers.DateField(required=False, format='%Y-%m-%d', input_formats=['%Y-%m-%d', '%d/%m/%Y'])
    ano = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
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


class GraficosReceitasDespesasSerializer(serializers.Serializer):
    """Estrutura de resposta do gráfico de evolução de receitas e despesas."""
    ano = serializers.IntegerField()
    meses = serializers.ListField(child=serializers.DictField())
    totais_ano = serializers.DictField()


class FeedAtividadeSerializer(serializers.Serializer):
    """Item individual da linha do tempo de atividades recentes."""
    tipo = serializers.CharField()
    identificador = serializers.CharField()
    titulo = serializers.CharField()
    descricao = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
