"""
Views e ViewSets do Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos).
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 7).
"""
import os
import re
import mimetypes
from decimal import Decimal
from django.conf import settings
from django.db.models import Q, Avg, Min, Max
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.catalogo.models import Item
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem
from apps.compras.serializers import (
    DocumentoFiscalCompraSerializer,
    NotaCompraItemSerializer,
    HistoricoPrecoItemSerializer
)
from apps.compras.services import validar_arquivo_anexo_compra
from core.permissions import HasComprasAccess
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos


class DocumentoFiscalCompraViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para Notas Fiscais de Compra (`DocumentoFiscalCompra`).
    Protegido pelo toggle 'acesso_compras' e governança de Soft Delete.
    Inclui anexação segura de arquivos (XML/PDF) e consulta de histórico de preços por fornecedor.
    """
    serializer_class = DocumentoFiscalCompraSerializer
    permission_classes = [HasComprasAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'num_nota',
        'chave_acesso',
        'fornecedor__nome_razao',
        'fornecedor__nome_fantasia',
        'fornecedor__cnpj_cpf'
    ]
    ordering_fields = ['data_compra', 'num_nota', 'valor_total', 'created_at']
    ordering = ['-data_compra', '-id']

    def get_queryset(self):
        queryset = DocumentoFiscalCompra.objects.filter(
            deleted_at__isnull=True
        ).select_related(
            'fornecedor'
        ).prefetch_related(
            'itens_comprados__item__unidade_compra'
        )

        # Filtro por Fornecedor
        fornecedor_id = self.request.query_params.get('fornecedor_id')
        if fornecedor_id:
            queryset = queryset.filter(fornecedor_id=fornecedor_id)

        # Filtro por intervalo de datas
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            queryset = queryset.filter(data_compra__gte=data_inicio)

        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            queryset = queryset.filter(data_compra__lte=data_fim)

        # Filtro por item contido na nota
        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(itens_comprados__item_id=item_id).distinct()

        # Busca textual personalizada com suporte a digitos (chave/CNPJ)
        search = self.request.query_params.get('search')
        if search:
            search_sanitizado = sanitizar_texto_maiusculo(search)
            search_digitos = limpar_apenas_digitos(search)

            filtro = (
                Q(num_nota__icontains=search_sanitizado) |
                Q(fornecedor__nome_razao__icontains=search_sanitizado) |
                Q(fornecedor__nome_fantasia__icontains=search_sanitizado)
            )
            if search_digitos:
                filtro |= (
                    Q(chave_acesso__icontains=search_digitos) |
                    Q(fornecedor__cnpj_cpf__icontains=search_digitos)
                )

            queryset = queryset.filter(filtro)

        return queryset

    def perform_destroy(self, instance):
        # Soft Delete mandatório
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['get'])
    def itens(self, request, pk=None):
        """Retorna os itens de uma nota fiscal específica."""
        doc = self.get_object()
        serializer = NotaCompraItemSerializer(doc.itens_comprados.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='historico-precos')
    def historico_precos(self, request):
        """
        Retorna o histórico cronológico de preços pagos por fornecedor para um item específico.
        Suporta filtro opcional por 'fornecedor_id'.
        """
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {"error": "O parâmetro 'item_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = Item.objects.get(pk=item_id, deleted_at__isnull=True)
        except Item.DoesNotExist:
            return Response(
                {"error": "Item não encontrado ou inativado no catálogo."},
                status=status.HTTP_404_NOT_FOUND
            )

        compras_itens = NotaCompraItem.objects.filter(
            item=item,
            documento_fiscal__deleted_at__isnull=True
        ).select_related(
            'documento_fiscal__fornecedor',
            'item__unidade_compra'
        )

        fornecedor_id = request.query_params.get('fornecedor_id')
        if fornecedor_id:
            compras_itens = compras_itens.filter(documento_fiscal__fornecedor_id=fornecedor_id)

        compras_itens = compras_itens.order_by('-documento_fiscal__data_compra', '-id')

        # Estatísticas de preço
        agregados = compras_itens.aggregate(
            preco_medio=Avg('valor_unitario'),
            menor_preco=Min('valor_unitario'),
            maior_preco=Max('valor_unitario')
        )

        lista_historico = []
        for nci in compras_itens:
            doc = nci.documento_fiscal
            fornecedor = doc.fornecedor
            subtotal = (Decimal(str(nci.quantidade_comprada)) * Decimal(str(nci.valor_unitario))).quantize(Decimal('0.01'))

            lista_historico.append({
                "documento_fiscal_id": doc.id,
                "num_nota": doc.num_nota,
                "data_compra": doc.data_compra,
                "fornecedor_id": fornecedor.id,
                "fornecedor_nome": fornecedor.nome_razao,
                "fornecedor_cnpj_cpf": fornecedor.cnpj_cpf,
                "quantidade_comprada": nci.quantidade_comprada,
                "unidade_medida": item.unidade_compra.sigla if item.unidade_compra else "UN",
                "valor_unitario": nci.valor_unitario,
                "subtotal": subtotal
            })

        serializer = HistoricoPrecoItemSerializer(lista_historico, many=True)

        return Response({
            "item_id": item.id,
            "item_nome": item.nome,
            "unidade_compra": item.unidade_compra.sigla if item.unidade_compra else "UN",
            "ultimo_custo_atual": item.ultimo_custo_compra,
            "data_ultima_compra": item.data_ultima_compra,
            "preco_medio": agregados['preco_medio'] or item.ultimo_custo_compra,
            "menor_preco": agregados['menor_preco'] or item.ultimo_custo_compra,
            "maior_preco": agregados['maior_preco'] or item.ultimo_custo_compra,
            "total_aquisicoes": len(lista_historico),
            "historico": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='anexar-arquivo')
    def anexar_arquivo(self, request, pk=None):
        """
        Upload seguro de arquivos anexos (XML, PDF, PNG, JPG) da Nota Fiscal.
        Executa validação profunda de MIME types e magic numbers.
        """
        doc = self.get_object()
        arquivo = request.FILES.get('arquivo')

        if not arquivo:
            return Response(
                {"arquivo": ["Nenhum arquivo enviado para anexo."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validação profunda de extensão e integridade
        extensao = validar_arquivo_anexo_compra(arquivo)

        # Diretório seguro NoExec em media/compras/<fornecedor_id>/
        pasta_destino = os.path.join(settings.MEDIA_ROOT, 'compras', str(doc.fornecedor.id))
        os.makedirs(pasta_destino, exist_ok=True)

        nome_limpo = re.sub(r'[^a-zA-Z0-9_.-]', '_', arquivo.name)
        timestamp = int(timezone.now().timestamp())
        nome_arquivo_seguro = f"nf_{doc.id}_{timestamp}_{nome_limpo}"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo_seguro)

        with open(caminho_completo, 'wb+') as destino:
            for chunk in arquivo.chunks():
                destino.write(chunk)

        # Caminho relativo gravado no banco de dados
        caminho_relativo = os.path.join('compras', str(doc.fornecedor.id), nome_arquivo_seguro).replace('\\', '/')
        doc.caminho_arquivo_anexo = caminho_relativo
        doc.save(update_fields=['caminho_arquivo_anexo', 'updated_at', 'updated_by_id'])

        return Response({
            "status": "success",
            "message": "Arquivo anexo gravado com sucesso.",
            "caminho_arquivo_anexo": caminho_relativo
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='download-anexo')
    def download_anexo(self, request, pk=None):
        """
        Download seguro do anexo da Nota Fiscal forçando Content-Disposition e NoExec.
        """
        doc = self.get_object()
        if not doc.caminho_arquivo_anexo:
            raise Http404("Esta nota fiscal não possui arquivo anexo.")

        caminho_absoluto = os.path.join(settings.MEDIA_ROOT, doc.caminho_arquivo_anexo)
        if not os.path.exists(caminho_absoluto):
            raise Http404("Arquivo físico não encontrado no servidor.")

        mime_type, _ = mimetypes.guess_type(caminho_absoluto)
        if not mime_type:
            mime_type = 'application/octet-stream'

        nome_download = f"NF_{doc.num_nota}_{doc.fornecedor.nome_razao[:20].strip()}{os.path.splitext(doc.caminho_arquivo_anexo)[1]}"
        nome_download_limpo = re.sub(r'[^a-zA-Z0-9_.-]', '_', nome_download)

        response = FileResponse(open(caminho_absoluto, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{nome_download_limpo}"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class NotaCompraItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestão dos itens individuais de compras (`NotaCompraItem`).
    Ao criar ou editar uma linha de item, dispara a retroalimentação automática de custos no Item.
    """
    queryset = NotaCompraItem.objects.filter(
        documento_fiscal__deleted_at__isnull=True
    ).select_related(
        'documento_fiscal__fornecedor',
        'item__unidade_compra'
    )
    serializer_class = NotaCompraItemSerializer
    permission_classes = [HasComprasAccess]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-id']

    def get_queryset(self):
        queryset = super().get_queryset()
        doc_id = self.request.query_params.get('documento_fiscal_id')
        if doc_id:
            queryset = queryset.filter(documento_fiscal_id=doc_id)

        item_id = self.request.query_params.get('item_id')
        if item_id:
            queryset = queryset.filter(item_id=item_id)

        return queryset
