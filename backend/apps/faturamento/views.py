"""
Views e ViewSets do Módulo de Faturamento Agregado.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 9).
"""
import io
from decimal import Decimal
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.faturamento.serializers import (
    FaturaSerializer,
    FaturaDetailSerializer,
    FaturaPropostaPagamentoSerializer,
    FaturarFaturaSerializer,
    ReceberFaturaSerializer,
    CortesiaFaturaSerializer,
    CancelarFaturaSerializer,
    ContaCorrenteOrcamentoSerializer
)
from apps.faturamento.services import (
    listar_conta_corrente_cliente,
    faturar_rascunho,
    receber_pagamento_fatura,
    quitar_cortesia_fatura,
    cancelar_fatura
)
from apps.faturamento.pdf_service import gerar_pdf_fatura
from core.permissions import HasComercialAccess


class FaturaViewSet(viewsets.ModelViewSet):
    """
    CRUD e gestão operacional completa de Faturas e Pré-Faturas (`Fatura`).
    Protegido pelo toggle 'acesso_comercial' e governança estrita de Soft Delete.
    Inclui Conta Corrente, conversão em Fatura Final, liquidação, cortesia, cancelamento em cascata e geração de PDF.
    """
    permission_classes = [HasComercialAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'id',
        'cliente__nome_razao',
        'cliente__nome_fantasia',
        'cliente__cnpj_cpf',
        'numero_nfe_venda',
        'linha_digitavel_boleto'
    ]
    ordering_fields = ['data_emissao', 'data_fechamento', 'valor_total_faturado', 'id', 'created_at']
    ordering = ['-data_emissao', '-id']

    def get_queryset(self):
        queryset = Fatura.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'cliente',
            'regra_pagamento',
            'regra_pagamento__meio_pagamento'
        ).prefetch_related(
            'orcamentos_agrupados__equipamento',
            'orcamentos_agrupados__itens_orcamento',
            'propostas_pagamento__regra_pagamento__meio_pagamento',
            'lancamentos_financeiros__meio_pagamento',
            'lancamentos_financeiros__conta'
        )

        # Filtro por Cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        # Filtro por Status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())

        # Filtro por Intervalo de Datas de Emissão
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(data_emissao__gte=data_inicio)

        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(data_emissao__lte=data_fim)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FaturaDetailSerializer
        return FaturaSerializer

    def perform_destroy(self, instance):
        """Soft delete seguro da fatura com liberação dos orçamentos se for rascunho."""
        if instance.status == 'FATURADA' or instance.status == 'PAGA':
            raise ValidationError({'status': 'Não é permitido excluir uma fatura emitida ou paga. Utilize o cancelamento de fatura ou estorno.'})

        # Desvincula orçamentos vinculados
        instance.orcamentos_agrupados.filter(deleted_at__isnull=True).update(
            fatura=None,
            status_financeiro='A_FATURAR',
            updated_at=timezone.now()
        )
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='conta-corrente')
    def conta_corrente(self, request):
        """
        Lista os orçamentos da Conta Corrente de Clientes disponíveis para agrupamento em Pré-Fatura.
        Suporta filtro opcional por `cliente_id`.
        """
        cliente_id = request.query_params.get('cliente_id')
        orcamentos = listar_conta_corrente_cliente(cliente_id=cliente_id)
        serializer = ContaCorrenteOrcamentoSerializer(orcamentos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='faturar')
    def faturar(self, request, pk=None):
        """
        Converte uma Pré-Fatura (Rascunho) em Fatura Final (FATURADA).
        Define a regra de pagamento, transita os orçamentos para FATURADO e gera parcelas no Contas a Receber.
        """
        fatura = self.get_object()
        serializer = FaturarFaturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fatura_atualizada = faturar_rascunho(
            fatura=fatura,
            regra_pagamento_id=serializer.validated_data['regra_pagamento_id'],
            desconto_global=serializer.validated_data.get('desconto_global'),
            numero_nfe_venda=serializer.validated_data.get('numero_nfe_venda'),
            user=request.user
        )

        response_serializer = FaturaDetailSerializer(fatura_atualizada, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='receber')
    def receber(self, request, pk=None):
        """
        Registra baixa / liquidação de pagamento (total ou parcial) em uma Fatura Final.
        Impacta o saldo de caixa real e transita para PAGA quando atingir 100% de quitação.
        """
        fatura = self.get_object()
        serializer = ReceberFaturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = receber_pagamento_fatura(
            fatura=fatura,
            valor=serializer.validated_data['valor'],
            conta_id=serializer.validated_data.get('conta_id'),
            meio_pagamento_id=serializer.validated_data.get('meio_pagamento_id'),
            data_pagamento=serializer.validated_data.get('data_pagamento'),
            valor_liquido=serializer.validated_data.get('valor_liquido'),
            user=request.user
        )

        fatura_data = FaturaDetailSerializer(resultado['fatura'], context={'request': request}).data
        resultado['fatura'] = fatura_data

        return Response(resultado, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cortesia')
    def cortesia(self, request, pk=None):
        """
        Aplica quitação por Cortesia (100% de desconto) na fatura com justificativa obrigatória.
        """
        fatura = self.get_object()
        serializer = CortesiaFaturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fatura_atualizada = quitar_cortesia_fatura(
            fatura=fatura,
            motivo_justificativa=serializer.validated_data['motivo'],
            user=request.user
        )

        response_serializer = FaturaDetailSerializer(fatura_atualizada, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """
        Cancela a fatura com justificativa obrigatória (mínimo 10 caracteres).
        Libera os orçamentos contidos revertendo para 'A_FATURAR' e cancela parcelas a vencer.
        """
        fatura = self.get_object()
        serializer = CancelarFaturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fatura_cancelada = cancelar_fatura(
            fatura=fatura,
            motivo_cancelamento=serializer.validated_data['motivo_cancelamento'],
            user=request.user
        )

        response_serializer = FaturaDetailSerializer(fatura_cancelada, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='gerar-pdf')
    def gerar_pdf(self, request, pk=None):
        """
        Gera e faz o streaming do PDF da Fatura / Pré-Fatura no padrão Industrial Integrity.
        """
        fatura = self.get_object()
        pdf_buffer = gerar_pdf_fatura(fatura)

        nome_arquivo = f"Fatura_{fatura.id:05d}_{fatura.cliente.nome_razao[:20].strip().replace(' ', '_')}.pdf"
        return FileResponse(
            pdf_buffer,
            as_attachment=False,
            content_type='application/pdf',
            filename=nome_arquivo
        )


class FaturaPropostaPagamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD para gerenciar as propostas de pagamento simuladas na Pré-Fatura.
    Protegido pelo toggle 'acesso_comercial'.
    """
    permission_classes = [HasComercialAccess]
    serializer_class = FaturaPropostaPagamentoSerializer
    queryset = FaturaPropostaPagamento.objects.select_related(
        'fatura',
        'regra_pagamento__meio_pagamento'
    ).all()
    filter_backends = [filters.OrderingFilter]
    ordering = ['id']

    def get_queryset(self):
        qs = super().get_queryset()
        fatura_id = self.request.query_params.get('fatura_id')
        if fatura_id:
            qs = qs.filter(fatura_id=fatura_id)
        return qs
