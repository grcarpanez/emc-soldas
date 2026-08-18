"""
Views e ViewSets do Catálogo Base, Dicionários Centrais, Itens, Insumos e Produtos (Motor BOM).
Em conformidade com docs/FSD.md e docs/PLANO.md (Fases 4 e 6).
"""
from decimal import Decimal
from django.db import transaction
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.administracao.models import ConfiguracaoGlobal
from apps.catalogo.models import (
    DicionarioUom,
    DicionarioAtributo,
    Item,
    ItemAtributoValor,
    Produto,
    FichaTecnica
)
from apps.catalogo.serializers import (
    DicionarioUomSerializer,
    DicionarioAtributoSerializer,
    ItemSerializer,
    ItemAtributoValorSerializer,
    ProdutoSerializer,
    FichaTecnicaSerializer
)
from core.permissions import HasDicionarioUomAccess, HasCatalogoAccess


class DicionarioUomViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Dicionário Central de Unidades de Medida (UOM).
    Protegido pelo toggle 'gestao_dicionario_uom' e governança de Soft Delete.
    """
    queryset = DicionarioUom.objects.all()
    serializer_class = DicionarioUomSerializer
    permission_classes = [HasDicionarioUomAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sigla', 'descricao']
    ordering_fields = ['sigla', 'descricao', 'id', 'created_at']
    ordering = ['sigla']

    def perform_destroy(self, instance):
        # Valida se a unidade está vinculada a itens ou produtos ativos
        itens_compra = Item.objects.filter(unidade_compra=instance).exists()
        itens_consumo = Item.objects.filter(unidade_consumo=instance).exists()
        produtos_venda = Produto.objects.filter(unidade_venda=instance).exists()

        if itens_compra or itens_consumo or produtos_venda:
            raise ValidationError(
                "Não é possível inativar esta Unidade de Medida pois ela está em uso por itens ou produtos do catálogo."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class DicionarioAtributoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Catálogo Central de Atributos Técnicos.
    Protegido pelo toggle 'gestao_dicionario_uom' e governança de Soft Delete.
    """
    queryset = DicionarioAtributo.objects.all()
    serializer_class = DicionarioAtributoSerializer
    permission_classes = [HasDicionarioUomAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome_atributo']
    ordering_fields = ['nome_atributo', 'id', 'created_at']
    ordering = ['nome_atributo']

    def perform_destroy(self, instance):
        # Valida se o atributo está em uso em itens ativos
        if ItemAtributoValor.objects.filter(atributo=instance).exists():
            raise ValidationError(
                "Não é possível inativar este Atributo Técnico pois ele está vinculado a especificações de itens existentes."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class ItemViewSet(viewsets.ModelViewSet):
    """
    CRUD completo do Catálogo de Itens, Insumos e Matérias-Primas.
    Protegido pelo toggle 'gestao_catalogo' e governança de Soft Delete.
    Implementa trava de integridade para impedir exclusão lógica de itens em uso no Motor BOM.
    """
    queryset = Item.objects.select_related(
        'unidade_compra',
        'unidade_consumo'
    ).prefetch_related(
        'atributos_valores__atributo'
    ).all()
    serializer_class = ItemSerializer
    permission_classes = [HasCatalogoAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        'nome',
        'tipo_uso',
        'unidade_compra__sigla',
        'unidade_consumo__sigla',
        'atributos_valores__valor'
    ]
    ordering_fields = [
        'nome',
        'ultimo_custo_compra',
        'data_ultima_compra',
        'tipo_uso',
        'id',
        'created_at'
    ]
    ordering = ['nome']

    def perform_destroy(self, instance):
        # Trava de integridade mandatória: Bloqueia soft delete se o item constar na receita de Produtos ativos
        produtos_dependentes = FichaTecnica.objects.filter(
            item=instance,
            produto__deleted_at__isnull=True
        ).select_related('produto')

        if produtos_dependentes.exists():
            nomes_produtos = ", ".join(sorted(set(f.produto.nome for f in produtos_dependentes)))
            raise ValidationError(
                f"Não é possível excluir o item '{instance.nome}' pois ele está em uso na Ficha Técnica dos seguintes produtos ativos: {nomes_produtos}. Remova o item das receitas antes de inativá-lo."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)

    @action(detail=True, methods=['get'], url_path='onde-usado')
    def onde_usado(self, request, pk=None):
        """
        Retorna a lista de produtos ativos que utilizam este insumo em suas Fichas Técnicas BOM.
        """
        item = self.get_object()
        fichas = FichaTecnica.objects.filter(
            item=item,
            produto__deleted_at__isnull=True
        ).select_related('produto', 'produto__unidade_venda')

        resultados = []
        for f in fichas:
            unidade_sigla = item.unidade_consumo.sigla if item.unidade_consumo else item.unidade_compra.sigla
            resultados.append({
                "produto_id": f.produto.id,
                "produto_nome": f.produto.nome,
                "produto_unidade_venda": f.produto.unidade_venda.sigla,
                "quantidade_utilizada": str(f.quantidade_utilizada),
                "unidade_consumo": unidade_sigla
            })

        return Response({
            "item_id": item.id,
            "item_nome": item.nome,
            "total_produtos": len(resultados),
            "produtos": resultados
        }, status=status.HTTP_200_OK)


class ItemAtributoValorViewSet(viewsets.ModelViewSet):
    """
    CRUD dos Valores de Atributos Técnicos vinculados a Itens do Catálogo.
    Protegido pelo toggle 'gestao_catalogo'.
    """
    queryset = ItemAtributoValor.objects.select_related('item', 'atributo').all()
    serializer_class = ItemAtributoValorSerializer
    permission_classes = [HasCatalogoAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['item__nome', 'atributo__nome_atributo', 'valor']
    ordering_fields = ['item__nome', 'atributo__nome_atributo', 'id']
    ordering = ['item__nome']


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Produtos e Receitas de Produção da Oficina (Motor BOM).
    Protegido pelo toggle 'gestao_catalogo' e governança de Soft Delete.
    Calcula Preço de Custo Apurado em tempo real integrando insumos e mão de obra.
    """
    queryset = Produto.objects.select_related(
        'unidade_venda'
    ).prefetch_related(
        'ficha_tecnica_itens__item__unidade_compra',
        'ficha_tecnica_itens__item__unidade_consumo'
    ).all()
    serializer_class = ProdutoSerializer
    permission_classes = [HasCatalogoAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'descricao', 'unidade_venda__sigla']
    ordering_fields = ['nome', 'tempo_estimado_execucao', 'id', 'created_at']
    ordering = ['nome']

    def perform_destroy(self, instance):
        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)

    @action(detail=True, methods=['get'], url_path='custo-detalhado')
    def custo_detalhado(self, request, pk=None):
        """
        Retorna a memória de cálculo completa e discriminada do Preço de Custo Apurado.
        Detalha item a item da receita BOM (quantidades, custos fracionados e subtotais)
        e a composição do custo da mão de obra baseada na taxa horária global vigente.
        """
        produto = self.get_object()
        config = ConfiguracaoGlobal.get_solo()
        taxa_horaria = Decimal(str(config.taxa_mao_de_obra_hora or 0))
        horas_mo = Decimal(str(produto.tempo_estimado_execucao or 0))
        custo_mo = (horas_mo * taxa_horaria).quantize(Decimal('0.01'))

        materiais_detalhados = []
        total_materiais = Decimal('0.00')

        fichas = produto.ficha_tecnica_itens.select_related(
            'item',
            'item__unidade_compra',
            'item__unidade_consumo'
        ).all()

        for f in fichas:
            item = f.item
            if item:
                ultimo_custo = Decimal(str(item.ultimo_custo_compra or 0))
                fator = Decimal(str(item.fator_conversao or 1))
                if fator <= Decimal('0'):
                    fator = Decimal('1')
                custo_unit_consumo = (ultimo_custo / fator).quantize(Decimal('0.0001'))
                qtd = Decimal(str(f.quantidade_utilizada or 0))
                subtotal = (qtd * (ultimo_custo / fator)).quantize(Decimal('0.01'))
                total_materiais += subtotal

                unidade_consumo_sigla = item.unidade_consumo.sigla if item.unidade_consumo else item.unidade_compra.sigla

                materiais_detalhados.append({
                    "item_id": item.id,
                    "item_nome": item.nome,
                    "unidade_compra": item.unidade_compra.sigla,
                    "unidade_consumo": unidade_consumo_sigla,
                    "fator_conversao": str(item.fator_conversao),
                    "ultimo_custo_compra": f"{ultimo_custo:.2f}",
                    "custo_unitario_consumo": f"{custo_unit_consumo:.4f}",
                    "quantidade_utilizada": str(f.quantidade_utilizada),
                    "subtotal_custo": f"{subtotal:.2f}"
                })

        total_materiais = total_materiais.quantize(Decimal('0.01'))
        preco_custo_apurado = (total_materiais + custo_mo).quantize(Decimal('0.01'))

        return Response({
            "produto_id": produto.id,
            "produto_nome": produto.nome,
            "unidade_venda": produto.unidade_venda.sigla,
            "tempo_estimado_horas": f"{horas_mo:.2f}",
            "taxa_mao_de_obra_hora": f"{taxa_horaria:.2f}",
            "custo_mao_de_obra": f"{custo_mo:.2f}",
            "materiais": materiais_detalhados,
            "custo_total_materiais": f"{total_materiais:.2f}",
            "preco_custo_apurado": f"{preco_custo_apurado:.2f}"
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='atualizar-ficha-tecnica')
    @transaction.atomic
    def atualizar_ficha_tecnica(self, request, pk=None):
        """
        Endpoint dedicado para redefinir a composição da Ficha Técnica BOM do produto em lote.
        Payload esperado: { "itens": [ { "item": <id>, "quantidade_utilizada": <dec> }, ... ] }
        """
        produto = self.get_object()
        itens_data = request.data.get('itens', [])

        if not isinstance(itens_data, list):
            raise ValidationError({"itens": "O campo 'itens' deve ser uma lista de objetos."})

        # Valida integridade e duplicações
        itens_ids = set()
        novos_itens = []
        for i, raw_item in enumerate(itens_data):
            item_id = raw_item.get('item')
            qtd = raw_item.get('quantidade_utilizada')

            if not item_id:
                raise ValidationError({"itens": f"Item na posição {i} não possui 'item' (ID) informado."})
            if qtd is None or Decimal(str(qtd)) <= Decimal('0'):
                raise ValidationError({"itens": f"Quantidade utilizada na posição {i} deve ser maior que zero."})

            if item_id in itens_ids:
                raise ValidationError({"itens": f"Item ID {item_id} informado em duplicidade na ficha técnica."})
            itens_ids.add(item_id)

            try:
                item_obj = Item.objects.get(id=item_id)
            except Item.DoesNotExist:
                raise ValidationError({"itens": f"Item com ID {item_id} não encontrado ou inativo."})

            novos_itens.append((item_obj, qtd))

        # Substitui os itens de forma transacional atômica
        produto.ficha_tecnica_itens.all().delete()
        for item_obj, qtd in novos_itens:
            FichaTecnica.objects.create(
                produto=produto,
                item=item_obj,
                quantidade_utilizada=qtd
            )

        serializer = self.get_serializer(produto)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FichaTecnicaViewSet(viewsets.ModelViewSet):
    """
    CRUD dos Itens de Composição da Ficha Técnica BOM.
    Protegido pelo toggle 'gestao_catalogo'.
    """
    queryset = FichaTecnica.objects.select_related(
        'produto',
        'item',
        'item__unidade_compra',
        'item__unidade_consumo'
    ).all()
    serializer_class = FichaTecnicaSerializer
    permission_classes = [HasCatalogoAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['produto__nome', 'item__nome']
    ordering_fields = ['produto__nome', 'item__nome', 'id']
    ordering = ['produto__nome', 'item__nome']
