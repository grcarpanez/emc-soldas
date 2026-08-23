"""
Views e ViewSets do Módulo de Orçamentos Comerciais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 8).
"""
import io
from decimal import Decimal
from django.db.models import Q
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.cadastros.models import ClienteFornecedor
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento
from apps.orcamentos.serializers import (
    OrcamentoSerializer,
    OrcamentoDetailSerializer,
    OrcamentoItemSerializer,
    OrcamentoPropostaPagamentoSerializer,
    CancelarOrcamentoSerializer,
    RenovarOrcamentoSerializer,
    AlterarStatusOperacionalSerializer
)
from apps.orcamentos.services import (
    verificar_inadimplencia_cliente,
    analisar_inflacao_orcamento,
    renovar_validade_orcamento,
    cancelar_orcamento,
    alterar_status_operacional
)
from apps.orcamentos.pdf_service import gerar_pdf_orcamento
from core.permissions import HasComercialAccess
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos


class OrcamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD e gestão operacional completa de Orçamentos Comerciais (`Orcamento`).
    Protegido pelo toggle 'acesso_comercial' e governança estrita de Soft Delete.
    Inclui máquina de estados, snapshots, inflação, inadimplência e geração de PDF.
    """
    permission_classes = [HasComercialAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'id',
        'cliente__nome_razao',
        'cliente__nome_fantasia',
        'cliente__cnpj_cpf',
        'equipamento__placa',
        'equipamento__descricao',
        'itens_orcamento__descricao_livre',
        'itens_orcamento__produto__nome',
        'itens_orcamento__item__nome'
    ]
    ordering_fields = ['data_geracao', 'data_validade', 'valor_bruto', 'id', 'created_at']
    ordering = ['-data_geracao', '-id']

    def get_queryset(self):
        queryset = Orcamento.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'cliente',
            'equipamento',
            'fatura'
        ).prefetch_related(
            'itens_orcamento__produto__unidade_venda',
            'itens_orcamento__item__unidade_compra',
            'propostas_pagamento__regra_pagamento__meio_pagamento'
        )

        # Filtro por Cliente
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        # Filtro por Equipamento
        equipamento_id = self.request.query_params.get('equipamento_id')
        if equipamento_id:
            queryset = queryset.filter(equipamento_id=equipamento_id)

        # Filtro por Status Operacional
        status_op = self.request.query_params.get('status_operacional')
        if status_op:
            queryset = queryset.filter(status_operacional=status_op.upper())

        # Filtro por Status Financeiro
        status_fin = self.request.query_params.get('status_financeiro')
        if status_fin:
            queryset = queryset.filter(status_financeiro=status_fin.upper())

        # Filtro por Intervalo de Datas
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(data_geracao__gte=data_inicio)

        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(data_geracao__lte=data_fim)

        # Filtro por Orçamentos Expirados
        is_expirado = self.request.query_params.get('expirado')
        if is_expirado is not None:
            hoje = timezone.now().date()
            if is_expirado.lower() in ['true', '1']:
                queryset = queryset.filter(data_validade__lt=hoje)
            elif is_expirado.lower() in ['false', '0']:
                queryset = queryset.filter(data_validade__gte=hoje)

        # Busca textual personalizada com suporte a dígitos (CPF/CNPJ/ID)
        search = self.request.query_params.get('search')
        if search:
            search_sanitizado = sanitizar_texto_maiusculo(search)
            search_digitos = limpar_apenas_digitos(search)

            filtro = (
                Q(cliente__nome_razao__icontains=search_sanitizado) |
                Q(cliente__nome_fantasia__icontains=search_sanitizado) |
                Q(equipamento__placa__icontains=search_sanitizado) |
                Q(equipamento__descricao__icontains=search_sanitizado) |
                Q(itens_orcamento__descricao_livre__icontains=search_sanitizado) |
                Q(itens_orcamento__produto__nome__icontains=search_sanitizado) |
                Q(itens_orcamento__item__nome__icontains=search_sanitizado)
            )
            if search_digitos:
                filtro |= Q(cliente__cnpj_cpf__icontains=search_digitos)
                if search_digitos.isdigit():
                    filtro |= Q(id=int(search_digitos))

            queryset = queryset.filter(filtro).distinct()

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrcamentoDetailSerializer
        elif self.action == 'cancelar':
            return CancelarOrcamentoSerializer
        elif self.action == 'renovar':
            return RenovarOrcamentoSerializer
        elif self.action in ['enviar', 'aprovar', 'iniciar_execucao', 'concluir']:
            return AlterarStatusOperacionalSerializer
        return OrcamentoSerializer

    def perform_destroy(self, instance):
        # Validação antes do Soft Delete
        if instance.status_financeiro in ['FATURADO', 'PAGO']:
            raise ValidationError({
                'status_financeiro': "Não é permitido excluir um orçamento já faturado ou pago."
            })
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """
        Cancela o orçamento com exigência mandatória de justificativa (mínimo 10 caracteres).
        """
        orcamento = self.get_object()
        serializer = CancelarOrcamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        motivo = serializer.validated_data['motivo_cancelamento']
        orcamento_atualizado = cancelar_orcamento(orcamento, motivo=motivo, user=request.user)

        return Response(
            OrcamentoDetailSerializer(orcamento_atualizado).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='verificar-inflacao')
    def verificar_inflacao(self, request, pk=None):
        """
        Compara o snapshot de custos gravado com os custos atuais de mercado do catálogo.
        Retorna relatório detalhado com variações de margem e insumos que subiram de preço.
        """
        orcamento = self.get_object()
        relatorio = analisar_inflacao_orcamento(orcamento)
        return Response(relatorio, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='renovar')
    def renovar(self, request, pk=None):
        """
        Renova a data de validade do orçamento.
        Suporta estender a data mantendo os preços antigos ou re-precificar atualizando custos.
        """
        orcamento = self.get_object()
        serializer = RenovarOrcamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dias = serializer.validated_data.get('dias_validade')
        atualizar_precos = serializer.validated_data.get('atualizar_precos', False)
        novos_precos = serializer.validated_data.get('novos_precos_itens', {})

        orcamento_renovado = renovar_validade_orcamento(
            orcamento,
            dias_validade=dias,
            atualizar_precos=atualizar_precos,
            novos_precos_itens=novos_precos,
            user=request.user
        )

        return Response(
            OrcamentoDetailSerializer(orcamento_renovado).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='gerar-pdf')
    def gerar_pdf(self, request, pk=None):
        """
        Gera e retorna o PDF transacional do orçamento formatado no padrão Industrial Integrity.
        Suprime o campo de desconto caso seja zero/nulo.
        """
        orcamento = self.get_object()
        buffer = io.BytesIO()
        gerar_pdf_orcamento(orcamento, buffer=buffer)

        nome_arquivo = f"orcamento_{orcamento.id:04d}.pdf"
        return FileResponse(
            buffer,
            as_attachment=False,
            content_type='application/pdf',
            filename=nome_arquivo
        )

    @action(detail=True, methods=['post'], url_path='enviar')
    def enviar(self, request, pk=None):
        """Transita status operacional para ENVIADO."""
        orcamento = self.get_object()
        orcamento = alterar_status_operacional(orcamento, 'ENVIADO', user=request.user)
        return Response(OrcamentoDetailSerializer(orcamento).data)

    @action(detail=True, methods=['post'], url_path='aprovar')
    def aprovar(self, request, pk=None):
        """Transita status operacional para APROVADO (valida se a proposta não está expirada)."""
        orcamento = self.get_object()
        orcamento = alterar_status_operacional(orcamento, 'APROVADO', user=request.user)
        return Response(OrcamentoDetailSerializer(orcamento).data)

    @action(detail=True, methods=['post'], url_path='iniciar-execucao')
    def iniciar_execucao(self, request, pk=None):
        """Transita status operacional para EM_EXECUCAO."""
        orcamento = self.get_object()
        orcamento = alterar_status_operacional(orcamento, 'EM_EXECUCAO', user=request.user)
        return Response(OrcamentoDetailSerializer(orcamento).data)

    @action(detail=True, methods=['post'], url_path='concluir')
    def concluir(self, request, pk=None):
        """Transita status operacional para CONCLUIDO."""
        orcamento = self.get_object()
        orcamento = alterar_status_operacional(orcamento, 'CONCLUIDO', user=request.user)
        return Response(OrcamentoDetailSerializer(orcamento).data)

    @action(detail=False, methods=['get'], url_path='verificar-inadimplencia')
    def verificar_inadimplencia(self, request):
        """
        Consulta preventiva de inadimplência para um cliente específico via query param `cliente_id`.
        """
        cliente_id = request.query_params.get('cliente_id')
        if not cliente_id:
            raise ValidationError({'cliente_id': "O parâmetro 'cliente_id' é obrigatório."})

        try:
            cliente = ClienteFornecedor.objects.get(id=cliente_id, deleted_at__isnull=True)
        except ClienteFornecedor.DoesNotExist:
            raise Http404("Cliente não encontrado.")

        resultado = verificar_inadimplencia_cliente(cliente.id)
        return Response(resultado, status=status.HTTP_200_OK)


class OrcamentoItemViewSet(viewsets.ModelViewSet):
    """
    CRUD para itens avulsos de orçamentos (`OrcamentoItem`).
    Protegido pelo toggle 'acesso_comercial'.
    """
    queryset = OrcamentoItem.objects.select_related(
        'orcamento', 'produto', 'item', 'produto__unidade_venda', 'item__unidade_compra'
    ).all()
    serializer_class = OrcamentoItemSerializer
    permission_classes = [HasComercialAccess]

    def get_queryset(self):
        queryset = super().get_queryset()
        orcamento_id = self.request.query_params.get('orcamento_id')
        if orcamento_id:
            queryset = queryset.filter(orcamento_id=orcamento_id)
        return queryset


class OrcamentoPropostaPagamentoViewSet(viewsets.ModelViewSet):
    """
    CRUD para propostas de pagamento vinculadas ao orçamento (`OrcamentoPropostaPagamento`).
    Protegido pelo toggle 'acesso_comercial'.
    """
    queryset = OrcamentoPropostaPagamento.objects.select_related(
        'orcamento', 'regra_pagamento', 'regra_pagamento__meio_pagamento'
    ).all()
    serializer_class = OrcamentoPropostaPagamentoSerializer
    permission_classes = [HasComercialAccess]

    def get_queryset(self):
        queryset = super().get_queryset()
        orcamento_id = self.request.query_params.get('orcamento_id')
        if orcamento_id:
            queryset = queryset.filter(orcamento_id=orcamento_id)
        return queryset
