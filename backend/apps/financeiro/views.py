"""
Views e ViewSets do Módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4).
"""
from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.financeiro.models import (
    CategoriaFinanceira,
    ContaBancaria,
    MeioPagamento,
    RegraPagamento,
    LancamentoFinanceiro
)
from apps.financeiro.serializers import (
    CategoriaFinanceiraSerializer,
    ContaBancariaSerializer,
    MeioPagamentoSerializer,
    RegraPagamentoSerializer
)
from core.permissions import HasCadastrosFinanceirosAccess


class CategoriaFinanceiraViewSet(viewsets.ModelViewSet):
    """
    CRUD completo da Árvore de Categorias Financeiras.
    Protegido pelo toggle 'cadastros_financeiros' e governança de Soft Delete.
    """
    queryset = CategoriaFinanceira.objects.all().select_related('categoria_pai')
    serializer_class = CategoriaFinanceiraSerializer
    permission_classes = [HasCadastrosFinanceirosAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'tipo', 'id', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo.upper())

        categoria_pai = self.request.query_params.get('categoria_pai')
        if categoria_pai:
            if categoria_pai.lower() == 'null' or categoria_pai == '0':
                qs = qs.filter(categoria_pai__isnull=True)
            else:
                qs = qs.filter(categoria_pai_id=categoria_pai)

        return qs

    def perform_destroy(self, instance):
        # Bloqueia exclusão se houver subcategorias ativas
        if instance.subcategorias.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar esta Categoria Financeira pois existem subcategorias ativas vinculadas a ela."
            )

        # Bloqueia exclusão se houver lançamentos financeiros ativos
        if instance.lancamentos.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar esta Categoria Financeira pois ela possui lançamentos financeiros associados."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class ContaBancariaViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Contas Bancárias e Caixas Físicos.
    Protegido pelo toggle 'cadastros_financeiros' e governança de Soft Delete.
    """
    queryset = ContaBancaria.objects.all()
    serializer_class = ContaBancariaSerializer
    permission_classes = [HasCadastrosFinanceirosAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'saldo', 'limite_credito', 'id', 'created_at']
    ordering = ['nome']

    def perform_destroy(self, instance):
        # Bloqueia exclusão se houver lançamentos financeiros ativos
        tem_origem = instance.lancamentos_origem.filter(deleted_at__isnull=True).exists()
        tem_destino = instance.lancamentos_destino.filter(deleted_at__isnull=True).exists()

        if tem_origem or tem_destino:
            raise ValidationError(
                "Não é possível inativar esta Conta Bancária pois existem movimentações financeiras vinculadas a ela."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class MeioPagamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Dicionário de Meios de Pagamento.
    Protegido pelo toggle 'cadastros_financeiros' e governança de Soft Delete.
    """
    queryset = MeioPagamento.objects.all()
    serializer_class = MeioPagamentoSerializer
    permission_classes = [HasCadastrosFinanceirosAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'ativo', 'id', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            is_active = ativo.lower() in ['true', '1', 't']
            qs = qs.filter(ativo=is_active)

        taxa = self.request.query_params.get('permite_taxa_maquininha')
        if taxa is not None:
            has_taxa = taxa.lower() in ['true', '1', 't']
            qs = qs.filter(permite_taxa_maquininha=has_taxa)

        return qs

    def perform_destroy(self, instance):
        # Bloqueia exclusão se houver regras de pagamento ativas vinculadas
        if instance.regras_pagamento.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar este Meio de Pagamento pois existem regras de pagamento comerciais vinculadas."
            )

        # Bloqueia exclusão se houver lançamentos financeiros ativos
        if instance.lancamentos.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar este Meio de Pagamento pois ele está vinculado a movimentações financeiras."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class RegraPagamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo da Matriz de Regras e Condições Comerciais de Pagamento.
    Protegido pelo toggle 'cadastros_financeiros' e governança de Soft Delete.
    """
    queryset = RegraPagamento.objects.all().select_related('meio_pagamento')
    serializer_class = RegraPagamentoSerializer
    permission_classes = [HasCadastrosFinanceirosAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'meio_pagamento__nome']
    ordering_fields = ['nome', 'tipo_cobranca', 'numero_parcelas', 'id', 'created_at']
    ordering = ['nome']

    def get_queryset(self):
        qs = super().get_queryset()
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            is_active = ativo.lower() in ['true', '1', 't']
            qs = qs.filter(ativo=is_active)

        tipo_cobranca = self.request.query_params.get('tipo_cobranca')
        if tipo_cobranca:
            qs = qs.filter(tipo_cobranca=tipo_cobranca.upper())

        meio_pagamento = self.request.query_params.get('meio_pagamento')
        if meio_pagamento:
            qs = qs.filter(meio_pagamento_id=meio_pagamento)

        return qs

    def perform_destroy(self, instance):
        # Bloqueia exclusão se houver propostas vinculadas em orçamentos ou faturas ativas
        tem_orcamentos = instance.propostas_orcamentos.exists() if hasattr(instance, 'propostas_orcamentos') else False
        tem_faturas = instance.propostas_faturas.exists() if hasattr(instance, 'propostas_faturas') else False

        if tem_orcamentos or tem_faturas:
            raise ValidationError(
                "Não é possível inativar esta Regra de Pagamento pois ela está vinculada a propostas de orçamentos ou faturas."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)
