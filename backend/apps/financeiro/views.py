"""
Views e ViewSets do Módulo Financeiro e Tesouraria.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 4 e Fase 10).
"""
from datetime import date
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

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
from apps.financeiro.serializers import (
    CategoriaFinanceiraSerializer,
    ContaBancariaSerializer,
    MeioPagamentoSerializer,
    RegraPagamentoSerializer,
    CartaoCreditoSerializer,
    FaturaCartaoSerializer,
    FaturaCartaoAjustarFechamentoSerializer,
    FaturaCartaoLiquidarSerializer,
    LancamentoFinanceiroSerializer,
    LancamentoFinanceiroLiquidarSerializer,
    LancamentoFinanceiroCancelarSerializer,
    LancamentoFinanceiroEstornarSerializer,
    TransferenciaInterContasSerializer,
    RemanejarDespesaCartaoSerializer,
    LogEstornoSerializer
)
from apps.financeiro.services import (
    liquidar_lancamento,
    cancelar_lancamento,
    estornar_lancamento,
    transferir_inter_contas,
    obter_resumo_financeiro
)
from apps.financeiro.services_cartao import (
    obter_ou_criar_fatura_aberta,
    calcular_limite_disponivel_cartao,
    lancar_despesa_cartao,
    remanejar_despesa_cartao,
    ajustar_fechamento_fatura,
    fechar_fatura_cartao,
    liquidar_fatura_cartao
)
from core.permissions import (
    HasCadastrosFinanceirosAccess,
    HasTesourariaAccess
)


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
        if instance.subcategorias.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar esta Categoria Financeira pois existem subcategorias ativas vinculadas a ela."
            )

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
        if instance.regras_pagamento.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                "Não é possível inativar este Meio de Pagamento pois existem regras de pagamento comerciais vinculadas."
            )

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
        tem_orcamentos = instance.propostas_orcamentos.exists() if hasattr(instance, 'propostas_orcamentos') else False
        tem_faturas = instance.propostas_faturas.exists() if hasattr(instance, 'propostas_faturas') else False

        if tem_orcamentos or tem_faturas:
            raise ValidationError(
                "Não é possível inativar esta Regra de Pagamento pois ela está vinculada a propostas de orçamentos ou faturas."
            )

        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class CartaoCreditoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Cartões de Crédito Corporativos.
    Protegido pelo toggle 'acesso_tesouraria'.
    """
    queryset = CartaoCredito.objects.all().select_related('conta_bancaria')
    serializer_class = CartaoCreditoSerializer
    permission_classes = [HasTesourariaAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome']
    ordering_fields = ['nome', 'limite', 'dia_vencimento', 'id', 'created_at']
    ordering = ['nome']

    @action(detail=True, methods=['get'], url_path='fatura-atual')
    def fatura_atual(self, request, pk=None):
        """Retorna ou inicializa a fatura aberta do mês atual para o cartão."""
        cartao = self.get_object()
        mes_referencia = request.query_params.get('mes_referencia')
        fatura = obter_ou_criar_fatura_aberta(cartao, mes_referencia=mes_referencia, user=request.user)
        serializer = FaturaCartaoSerializer(fatura)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='limite-disponivel')
    def limite_disponivel(self, request, pk=None):
        """Calcula o limite total, comprometido e disponível do cartão."""
        cartao = self.get_object()
        info = calcular_limite_disponivel_cartao(cartao)
        return Response(info, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.faturas.filter(deleted_at__isnull=True).exists():
            raise ValidationError("Não é possível excluir um cartão de crédito que possui faturas registradas.")
        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        instance.delete(user_id=user_id)


class FaturaCartaoViewSet(viewsets.ModelViewSet):
    """
    Gestão de Faturas de Cartões de Crédito Corporativos.
    Protegido pelo toggle 'acesso_tesouraria'.
    """
    queryset = FaturaCartao.objects.all().select_related('cartao')
    serializer_class = FaturaCartaoSerializer
    permission_classes = [HasTesourariaAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['cartao__nome', 'mes_referencia']
    ordering_fields = ['mes_referencia', 'status', 'id', 'created_at']
    ordering = ['-mes_referencia']

    def get_queryset(self):
        qs = super().get_queryset()
        cartao_id = self.request.query_params.get('cartao_id')
        if cartao_id:
            qs = qs.filter(cartao_id=cartao_id)

        status_fatura = self.request.query_params.get('status')
        if status_fatura:
            qs = qs.filter(status=status_fatura.upper())

        mes_ref = self.request.query_params.get('mes_referencia')
        if mes_ref:
            qs = qs.filter(mes_referencia=mes_ref)

        return qs

    @action(detail=True, methods=['post'], url_path='fechar')
    def fechar(self, request, pk=None):
        """Fecha a fatura do cartão e gera o título a pagar no Contas a Pagar."""
        fatura = self.get_object()
        resultado = fechar_fatura_cartao(fatura, user=request.user)
        resultado['fatura'] = FaturaCartaoSerializer(resultado['fatura']).data
        return Response({
            'status': 'success',
            'message': f"Fatura {fatura.mes_referencia} fechada com sucesso.",
            'dados': resultado
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='liquidar')
    def liquidar(self, request, pk=None):
        """Liquida a fatura do cartão com suporte a pagamento parcial e rollover."""
        fatura = self.get_object()
        serializer = FaturaCartaoLiquidarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = liquidar_fatura_cartao(
            fatura=fatura,
            valor_pago=serializer.validated_data['valor_pago'],
            conta_id=serializer.validated_data.get('conta_id'),
            data_pagamento=serializer.validated_data.get('data_pagamento'),
            user=request.user
        )
        resultado['fatura'] = FaturaCartaoSerializer(resultado['fatura']).data
        return Response({
            'status': 'success',
            'message': 'Fatura liquidada com sucesso.',
            'dados': resultado
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='ajustar-fechamento')
    def ajustar_fechamento(self, request, pk=None):
        """Ajusta a data de fechamento real de uma fatura específica."""
        fatura = self.get_object()
        serializer = FaturaCartaoAjustarFechamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fatura_atualizada = ajustar_fechamento_fatura(
            fatura=fatura,
            nova_data_fechamento=serializer.validated_data['data_fechamento_real'],
            user=request.user
        )
        return Response(FaturaCartaoSerializer(fatura_atualizada).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='lancar-despesa')
    def lancar_despesa(self, request, pk=None):
        """Atalho para registrar despesa vinculada diretamente a esta fatura."""
        fatura = self.get_object()
        valor = request.data.get('valor')
        categoria_id = request.data.get('categoria_id')
        descricao = request.data.get('descricao')
        data_compra = request.data.get('data_compra')

        if not valor or not categoria_id:
            raise ValidationError({'detail': 'Campos valor e categoria_id são obrigatórios.'})

        lancamento = lancar_despesa_cartao(
            cartao=fatura.cartao,
            valor=valor,
            categoria_id=categoria_id,
            descricao=descricao,
            data_compra=data_compra,
            fatura_cartao_id=fatura.id,
            user=request.user
        )
        return Response(LancamentoFinanceiroSerializer(lancamento).data, status=status.HTTP_201_CREATED)


class LancamentoFinanceiroViewSet(viewsets.ModelViewSet):
    """
    CRUD e Central de Operações de Lançamentos Financeiros (Competência e Caixa Real).
    Protegido pelo toggle 'acesso_tesouraria'.
    """
    queryset = LancamentoFinanceiro.objects.all().select_related(
        'fatura',
        'conta',
        'conta_destino',
        'meio_pagamento',
        'cartao_credito',
        'fatura_cartao',
        'categoria',
        'conciliado_por'
    )
    serializer_class = LancamentoFinanceiroSerializer
    permission_classes = [HasTesourariaAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'categoria__nome', 'conta__nome', 'motivo_cancelamento']
    ordering_fields = ['data_vencimento', 'data_pagamento', 'valor', 'status_pagamento', 'id', 'created_at']
    ordering = ['-data_vencimento', '-id']

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # Filtro por tipo de lançamento (ENTRADA, SAIDA, TRANSFERENCIA)
        tipo = params.get('tipo_lancamento')
        if tipo:
            qs = qs.filter(tipo_lancamento=tipo.upper())

        # Filtro por status de pagamento (suporta múltiplos separados por vírgula: ex 'A_VENCER,VENCIDO')
        status_pagto = params.get('status_pagamento')
        if status_pagto:
            status_list = [s.strip().upper() for s in status_pagto.split(',') if s.strip()]
            if len(status_list) == 1:
                qs = qs.filter(status_pagamento=status_list[0])
            elif len(status_list) > 1:
                qs = qs.filter(status_pagamento__in=status_list)

        # Filtro por Regime (competencia vs caixa)
        regime = params.get('regime')
        if regime:
            if regime.lower() == 'caixa':
                qs = qs.filter(status_pagamento='PAGO')
            elif regime.lower() == 'competencia':
                qs = qs.filter(status_pagamento__in=['A_VENCER', 'VENCIDO'])

        # Filtro por Conta Bancária (suporta múltiplos IDs separados por vírgula: ex '1,2')
        conta_id = params.get('conta_id') or params.get('conta')
        if conta_id:
            contas_list = [c.strip() for c in str(conta_id).split(',') if c.strip().isdigit()]
            if len(contas_list) == 1:
                qs = qs.filter(conta_id=contas_list[0])
            elif len(contas_list) > 1:
                qs = qs.filter(conta_id__in=contas_list)

        # Filtro por Categoria
        categoria_id = params.get('categoria_id') or params.get('categoria')
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)

        # Filtro por Cartão de Crédito
        cartao_id = params.get('cartao_credito_id') or params.get('cartao_credito')
        if cartao_id:
            qs = qs.filter(cartao_credito_id=cartao_id)

        # Filtro por Fatura de Cartão
        fatura_cartao_id = params.get('fatura_cartao_id') or params.get('fatura_cartao')
        if fatura_cartao_id:
            qs = qs.filter(fatura_cartao_id=fatura_cartao_id)

        # Filtro por Fatura de Venda
        fatura_id = params.get('fatura_id') or params.get('fatura')
        if fatura_id:
            qs = qs.filter(fatura_id=fatura_id)

        # Filtro por Conciliação
        is_conciliado = params.get('is_conciliado')
        if is_conciliado is not None:
            is_conc = is_conciliado.lower() in ['true', '1', 't']
            qs = qs.filter(is_conciliado=is_conc)

        # Range de Vencimento
        venc_ini = params.get('data_vencimento_inicio')
        venc_fim = params.get('data_vencimento_fim')
        if venc_ini:
            qs = qs.filter(data_vencimento__gte=venc_ini)
        if venc_fim:
            qs = qs.filter(data_vencimento__lte=venc_fim)

        # Range de Pagamento
        pagto_ini = params.get('data_pagamento_inicio')
        pagto_fim = params.get('data_pagamento_fim')
        if pagto_ini:
            qs = qs.filter(data_pagamento__date__gte=pagto_ini)
        if pagto_fim:
            qs = qs.filter(data_pagamento__date__lte=pagto_fim)

        return qs

    def perform_create(self, serializer):
        user_id = self.request.user.id if self.request.user and self.request.user.is_authenticated else None
        lancamento = serializer.save(created_by_id=user_id)

        # Se vinculado a cartão de crédito mas sem fatura_cartao especificada, vincula à fatura aberta
        if lancamento.cartao_credito and not lancamento.fatura_cartao:
            data_base = lancamento.data_vencimento or timezone.localdate()
            mes_ref = f"{data_base.year:04d}-{data_base.month:02d}"
            fatura = obter_ou_criar_fatura_aberta(lancamento.cartao_credito, mes_referencia=mes_ref, user=self.request.user)
            if data_base > fatura.data_fechamento_real:
                prox_mes = data_base.month + 1
                prox_ano = data_base.year
                if prox_mes > 12:
                    prox_mes = 1
                    prox_ano += 1
                mes_ref_prox = f"{prox_ano:04d}-{prox_mes:02d}"
                fatura = obter_ou_criar_fatura_aberta(lancamento.cartao_credito, mes_referencia=mes_ref_prox, user=self.request.user)
            lancamento.fatura_cartao = fatura
            lancamento.save(update_fields=['fatura_cartao', 'updated_at'])

        # Se já foi criado como PAGO e conta informada, atualiza o saldo bancário
        if lancamento.status_pagamento == 'PAGO' and lancamento.conta:
            conta = lancamento.conta
            if lancamento.tipo_lancamento == 'ENTRADA':
                conta.saldo += lancamento.valor
                conta.save(update_fields=['saldo', 'updated_at'])
            elif lancamento.tipo_lancamento == 'SAIDA':
                novo_saldo = conta.saldo - lancamento.valor
                if novo_saldo < -conta.limite_credito:
                    raise ValidationError({'conta': 'Lançamento excede o limite de cheque especial da conta bancária.'})
                conta.saldo = novo_saldo
                conta.save(update_fields=['saldo', 'updated_at'])

    @action(detail=True, methods=['post'], url_path='liquidar')
    def liquidar(self, request, pk=None):
        """Baixa / Liquidação de título a pagar ou a receber com suporte a taxas e retenções."""
        lancamento = self.get_object()
        serializer = LancamentoFinanceiroLiquidarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_liquidado = liquidar_lancamento(
            lancamento=lancamento,
            conta_id=serializer.validated_data['conta_id'],
            meio_pagamento_id=serializer.validated_data.get('meio_pagamento_id'),
            data_pagamento=serializer.validated_data.get('data_pagamento'),
            valor_pago=serializer.validated_data.get('valor_pago'),
            valor_liquido_recebido=serializer.validated_data.get('valor_liquido_recebido'),
            valor_iss_retido=serializer.validated_data.get('valor_iss_retido'),
            user=request.user
        )
        return Response(LancamentoFinanceiroSerializer(lancamento_liquidado).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        """Cancelamento justificado de título pendente (A Vencer ou Vencido)."""
        lancamento = self.get_object()
        serializer = LancamentoFinanceiroCancelarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_cancelado = cancelar_lancamento(
            lancamento=lancamento,
            motivo_cancelamento=serializer.validated_data['motivo_cancelamento'],
            user=request.user
        )
        return Response(LancamentoFinanceiroSerializer(lancamento_cancelado).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='estornar')
    def estornar(self, request, pk=None):
        """Estorno auditado de título PAGO com reversão de saldo bancário e gravação perpétua em LogEstorno."""
        lancamento = self.get_object()
        serializer = LancamentoFinanceiroEstornarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resultado = estornar_lancamento(
            lancamento=lancamento,
            justificativa=serializer.validated_data['justificativa'],
            user=request.user
        )
        return Response({
            'status': 'success',
            'message': 'Título estornado com sucesso e rastro perpétuo gravado.',
            'lancamento': LancamentoFinanceiroSerializer(resultado['lancamento']).data,
            'log_estorno': LogEstornoSerializer(resultado['log_estorno']).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='alterar-fatura-cartao')
    def alterar_fatura_cartao(self, request, pk=None):
        """Remaneja uma despesa de cartão para outra competência/fatura."""
        lancamento = self.get_object()
        serializer = RemanejarDespesaCartaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento_atualizado = remanejar_despesa_cartao(
            lancamento=lancamento,
            nova_fatura_cartao_id=serializer.validated_data.get('nova_fatura_cartao_id'),
            novo_mes_referencia=serializer.validated_data.get('novo_mes_referencia'),
            user=request.user
        )
        return Response(LancamentoFinanceiroSerializer(lancamento_atualizado).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='transferir')
    def transferir(self, request):
        """Transferência inter-contas atômica e neutra para o DRE."""
        serializer = TransferenciaInterContasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lancamento = transferir_inter_contas(
            conta_origem_id=serializer.validated_data['conta_origem_id'],
            conta_destino_id=serializer.validated_data['conta_destino_id'],
            valor=serializer.validated_data['valor'],
            descricao=serializer.validated_data.get('descricao'),
            data_transferencia=serializer.validated_data.get('data_transferencia'),
            user=request.user
        )
        return Response(LancamentoFinanceiroSerializer(lancamento).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        """Retorna métricas consolidadas de Tesouraria e Competência."""
        dados = obter_resumo_financeiro()
        return Response(dados, status=status.HTTP_200_OK)


class LogEstornoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Trilha de Auditoria Perpétua e Imutável de Estornos.
    Protegido pelo toggle 'acesso_tesouraria'.
    """
    queryset = LogEstorno.objects.all().select_related('lancamento', 'usuario')
    serializer_class = LogEstornoSerializer
    permission_classes = [HasTesourariaAccess]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['justificativa', 'usuario__nome', 'lancamento__descricao']
    ordering_fields = ['data_estorno', 'id']
    ordering = ['-data_estorno']

    def get_queryset(self):
        qs = super().get_queryset()
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            qs = qs.filter(usuario_id=usuario_id)

        lancamento_id = self.request.query_params.get('lancamento_id')
        if lancamento_id:
            qs = qs.filter(lancamento_id=lancamento_id)

        return qs
