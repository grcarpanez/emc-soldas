"""
Views e ViewSets do módulo de Cadastros Básicos: Clientes, Fornecedores, Equipamentos, Vínculos e Anexos.
Em conformidade com docs/FSD.md, docs/PLANO.md e regras de segurança.
"""
import os
import mimetypes
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import (
    HasComercialAccess,
    HasComprasAccess,
    IsAdminUserRole
)
from core.utils import (
    sanitizar_texto_maiusculo,
    limpar_apenas_digitos,
    validar_cpf,
    validar_cnpj
)
from apps.cadastros.models import (
    ClienteFornecedor,
    Equipamento,
    ClienteEquipamento,
    AnexoGeralCliente
)
from apps.cadastros.serializers import (
    ClienteFornecedorSerializer,
    EquipamentoSerializer,
    ClienteEquipamentoSerializer,
    AnexoGeralClienteSerializer
)
from apps.cadastros.utils_cnpj import consultar_cnpj_externo


class ConsultaCnpjAPIView(APIView):
    """
    Endpoint Proxy Utilitário para Consulta de CNPJ público com Fallback Gracioso.
    Rota: GET /api/utilitarios/consulta-cnpj/<str:cnpj>/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, cnpj):
        resultado = consultar_cnpj_externo(cnpj)
        
        if resultado.get("status") == "error":
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(resultado, status=status.HTTP_200_OK)


class VerificarDocumentoAPIView(APIView):
    """
    Validação matemática antecipada e checagem de duplicidade de CPF/CNPJ no evento onBlur.
    Rota: GET /api/utilitarios/verificar-documento/
    Query params: ?documento=...&tipo_pessoa=...&exclude_id=...
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        doc = request.query_params.get('documento', '')
        tipo_pessoa = request.query_params.get('tipo_pessoa', 'PJ')
        exclude_id = request.query_params.get('exclude_id', None)

        doc_limpo = limpar_apenas_digitos(doc)

        if not doc_limpo:
            return Response({"valido": True, "duplicado": False, "mensagem": "Documento não informado."})

        # Validação matemática
        valido = False
        if tipo_pessoa == 'PF':
            valido = len(doc_limpo) == 11 and validar_cpf(doc_limpo)
            msg_invalido = "CPF inválido. Os dígitos verificadores não conferem."
        else:
            valido = len(doc_limpo) == 14 and validar_cnpj(doc_limpo)
            msg_invalido = "CNPJ inválido. Os dígitos verificadores não conferem."

        if not valido:
            return Response({
                "valido": False,
                "duplicado": False,
                "mensagem": msg_invalido
            }, status=status.HTTP_200_OK)

        # Checagem de duplicidade
        qs = ClienteFornecedor.objects.filter(cnpj_cpf=doc_limpo, deleted_at__isnull=True)
        if exclude_id:
            try:
                qs = qs.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                pass

        if qs.exists():
            duplicado = qs.first()
            return Response({
                "valido": True,
                "duplicado": True,
                "mensagem": f"Documento já cadastrado para '{duplicado.nome_razao}' (ID #{duplicado.id}).",
                "existente": {
                    "id": duplicado.id,
                    "nome_razao": duplicado.nome_razao,
                    "tipo": duplicado.tipo
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "valido": True,
            "duplicado": False,
            "mensagem": "Documento válido e disponível para cadastro."
        }, status=status.HTTP_200_OK)


class ClienteFornecedorPermission(permissions.BasePermission):
    """
    Permissão RBAC customizada para Clientes e Fornecedores:
    - Admin: Acesso pleno.
    - Operador com acesso_comercial: pode gerenciar clientes e fornecedores.
    - Operador com acesso_compras: pode gerenciar fornecedores.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        role = getattr(request.user, 'role', 'Operador')
        if role == 'Admin' or getattr(request.user, 'is_superuser', False):
            return True

        permissoes = getattr(request.user, 'permissoes', None)
        if not permissoes:
            return False

        # Se tiver acesso comercial ou compras, pode acessar a listagem
        return permissoes.acesso_comercial or permissoes.acesso_compras


class ClienteFornecedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de Clientes e Fornecedores (PF/PJ).
    Suporta filtros avançados, cadastro rápido ágil e Soft Delete.
    """
    serializer_class = ClienteFornecedorSerializer
    permission_classes = [ClienteFornecedorPermission]

    def get_queryset(self):
        # Apenas registros não deletados logicamente
        queryset = ClienteFornecedor.objects.filter(deleted_at__isnull=True)

        # Filtro por tipo (Cliente, Fornecedor, Ambos)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            if tipo == 'Cliente':
                queryset = queryset.filter(Q(tipo='Cliente') | Q(tipo='Ambos'))
            elif tipo == 'Fornecedor':
                queryset = queryset.filter(Q(tipo='Fornecedor') | Q(tipo='Ambos'))
            else:
                queryset = queryset.filter(tipo=tipo)

        # Filtro por tipo de pessoa (PF, PJ)
        tipo_pessoa = self.request.query_params.get('tipo_pessoa')
        if tipo_pessoa:
            queryset = queryset.filter(tipo_pessoa=tipo_pessoa)

        # Busca textual
        search = self.request.query_params.get('search')
        if search:
            search_sanitizado = sanitizar_texto_maiusculo(search)
            search_digitos = limpar_apenas_digitos(search)
            
            filtro = (
                Q(nome_razao__icontains=search_sanitizado) |
                Q(nome_fantasia__icontains=search_sanitizado) |
                Q(cidade__icontains=search_sanitizado) |
                Q(email__icontains=search.lower())
            )
            if search_digitos:
                filtro |= Q(cnpj_cpf__icontains=search_digitos) | Q(telefone__icontains=search_digitos)

            queryset = queryset.filter(filtro)

        return queryset.order_by('nome_razao')

    def perform_destroy(self, instance):
        # Soft Delete mandatório
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['get'])
    def dossie(self, request, pk=None):
        """
        Dossiê Comercial e Financeiro do Cliente / Fornecedor.
        """
        cliente = self.get_object()
        
        # Equipamentos ativos vinculados
        equipamentos_ativos = ClienteEquipamento.objects.filter(
            cliente=cliente,
            is_ativo=True
        ).select_related('equipamento')

        equipamentos_data = [
            {
                "id": vinculo.equipamento.id,
                "placa": vinculo.equipamento.placa,
                "identificacao": vinculo.equipamento.identificacao,
                "descricao": vinculo.equipamento.descricao,
                "data_vinculo": vinculo.data_vinculo
            }
            for vinculo in equipamentos_ativos
        ]

        # Resumo
        resumo = {
            "cliente_id": cliente.id,
            "nome_razao": cliente.nome_razao,
            "nome_fantasia": cliente.nome_fantasia,
            "tipo": cliente.tipo,
            "tipo_pessoa": cliente.tipo_pessoa,
            "cnpj_cpf": cliente.cnpj_cpf,
            "telefone": cliente.telefone,
            "email": cliente.email,
            "cidade_uf": f"{cliente.cidade or ''}/{cliente.uf or ''}".strip('/'),
            "equipamentos_vinculados": equipamentos_data,
            "total_equipamentos_ativos": len(equipamentos_data),
        }

        return Response(resumo, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def equipamentos(self, request, pk=None):
        """Lista os equipamentos vinculados ao cliente."""
        cliente = self.get_object()
        vinculos = ClienteEquipamento.objects.filter(
            cliente=cliente
        ).select_related('equipamento').order_by('-is_ativo', '-data_vinculo')

        dados = [
            {
                "vinculo_id": v.id,
                "equipamento_id": v.equipamento.id,
                "placa": v.equipamento.placa,
                "identificacao": v.equipamento.identificacao,
                "descricao": v.equipamento.descricao,
                "is_ativo": v.is_ativo,
                "data_vinculo": v.data_vinculo
            }
            for v in vinculos
        ]
        return Response(dados, status=status.HTTP_200_OK)


class EquipamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para Equipamentos e Veículos atendidos na oficina.
    Suporta busca, histórico de proprietários e transferências.
    """
    serializer_class = EquipamentoSerializer
    permission_classes = [HasComercialAccess]

    def get_queryset(self):
        queryset = Equipamento.objects.filter(deleted_at__isnull=True)

        search = self.request.query_params.get('search')
        if search:
            search_sanitizado = sanitizar_texto_maiusculo(search)
            placa_busca = search_sanitizado.replace('-', '').replace(' ', '')
            queryset = queryset.filter(
                Q(placa__icontains=placa_busca) |
                Q(identificacao__icontains=search_sanitizado) |
                Q(descricao__icontains=search_sanitizado)
            )

        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(
                historico_clientes__cliente_id=cliente_id,
                historico_clientes__is_ativo=True
            )

        return queryset.order_by('placa', 'identificacao')

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['get'])
    def historico_proprietarios(self, request, pk=None):
        """Retorna o histórico cronológico de todos os proprietários deste equipamento."""
        equipamento = self.get_object()
        vinculos = ClienteEquipamento.objects.filter(
            equipamento=equipamento
        ).select_related('cliente').order_by('-data_vinculo')

        dados = [
            {
                "vinculo_id": v.id,
                "cliente_id": v.cliente.id,
                "nome_razao": v.cliente.nome_razao,
                "telefone": v.cliente.telefone,
                "cnpj_cpf": v.cliente.cnpj_cpf,
                "data_vinculo": v.data_vinculo,
                "is_ativo": v.is_ativo
            }
            for v in vinculos
        ]
        return Response(dados, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def transferir(self, request, pk=None):
        """
        Transfere o equipamento para um novo cliente proprietário.
        Inativa o vínculo ativo anterior e cria um novo vínculo com data_vinculo = NOW().
        Payload: { "cliente_id": 123 }
        """
        equipamento = self.get_object()
        novo_cliente_id = request.data.get('novo_cliente_id') or request.data.get('cliente_id')

        if not novo_cliente_id:
            return Response(
                {"status": "error", "message": "O campo 'novo_cliente_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            novo_cliente = ClienteFornecedor.objects.get(pk=novo_cliente_id, deleted_at__isnull=True)
        except ClienteFornecedor.DoesNotExist:
            return Response(
                {"status": "error", "message": "Novo cliente não encontrado ou inativo."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Inativa vínculos anteriores
        ClienteEquipamento.objects.filter(
            equipamento=equipamento,
            is_ativo=True
        ).update(is_ativo=False)

        # Cria novo vínculo ativo
        novo_vinculo = ClienteEquipamento.objects.create(
            cliente=novo_cliente,
            equipamento=equipamento,
            data_vinculo=timezone.now(),
            is_ativo=True
        )

        return Response({
            "status": "success",
            "message": f"Equipamento transferido com sucesso para '{novo_cliente.nome_razao}'.",
            "vinculo": {
                "id": novo_vinculo.id,
                "cliente_id": novo_cliente.id,
                "cliente_nome": novo_cliente.nome_razao,
                "equipamento_id": equipamento.id,
                "data_vinculo": novo_vinculo.data_vinculo,
                "is_ativo": True
            }
        }, status=status.HTTP_200_OK)


class ClienteEquipamentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestão dos Vínculos entre Clientes e Equipamentos.
    """
    serializer_class = ClienteEquipamentoSerializer
    permission_classes = [HasComercialAccess]

    def get_queryset(self):
        queryset = ClienteEquipamento.objects.select_related('cliente', 'equipamento')
        
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)

        equipamento_id = self.request.query_params.get('equipamento_id')
        if equipamento_id:
            queryset = queryset.filter(equipamento_id=equipamento_id)

        is_ativo = self.request.query_params.get('is_ativo')
        if is_ativo is not None:
            queryset = queryset.filter(is_ativo=is_ativo.lower() in ['true', '1'])

        return queryset.order_by('-data_vinculo')

    @action(detail=True, methods=['post'])
    def inativar(self, request, pk=None):
        """Inativa um vínculo existente."""
        vinculo = self.get_object()
        vinculo.is_ativo = False
        vinculo.save(update_fields=['is_ativo'])
        return Response({"status": "success", "message": "Vínculo inativado com sucesso."})


class AnexoGeralClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para upload e gestão segura de anexos gerais de clientes.
    """
    serializer_class = AnexoGeralClienteSerializer
    permission_classes = [HasComercialAccess]

    # Extensões permitidas com MIME types seguros
    EXTENSOES_PERMITIDAS = {'.pdf', '.png', '.jpg', '.jpeg', '.xml', '.csv'}

    def get_queryset(self):
        queryset = AnexoGeralCliente.objects.select_related('cliente')
        cliente_id = self.request.query_params.get('cliente_id')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        arquivo = request.FILES.get('arquivo')
        cliente_id = request.data.get('cliente') or request.data.get('cliente_id')
        nome_documento = request.data.get('nome_documento')

        if not cliente_id:
            return Response({"cliente": ["O campo cliente é obrigatório."]}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cliente = ClienteFornecedor.objects.get(pk=cliente_id, deleted_at__isnull=True)
        except ClienteFornecedor.DoesNotExist:
            return Response({"cliente": ["Cliente não encontrado."]}, status=status.HTTP_404_NOT_FOUND)

        if not arquivo:
            return Response({"arquivo": ["Nenhum arquivo enviado."]}, status=status.HTTP_400_BAD_REQUEST)

        # Validação de extensão
        extensao = os.path.splitext(arquivo.name)[1].lower()
        if extensao not in self.EXTENSOES_PERMITIDAS:
            return Response({
                "arquivo": [f"Extensão '{extensao}' não permitida. Extensões aceitas: PDF, PNG, JPG, JPEG, XML, CSV."]
            }, status=status.HTTP_400_BAD_REQUEST)

        # Nome do documento padronizado
        if not nome_documento:
            nome_documento = os.path.splitext(arquivo.name)[0]
        nome_documento_sanitizado = sanitizar_texto_maiusculo(nome_documento)

        # Armazenamento seguro em pasta protegida
        pasta_destino = os.path.join(settings.MEDIA_ROOT, 'anexos_clientes', str(cliente.id))
        os.makedirs(pasta_destino, exist_ok=True)

        nome_arquivo_seguro = f"anexo_{int(timezone.now().timestamp())}_{arquivo.name.replace(' ', '_')}"
        caminho_completo = os.path.join(pasta_destino, nome_arquivo_seguro)

        with open(caminho_completo, 'wb+') as destino:
            for chunk in arquivo.chunks():
                destino.write(chunk)

        # Caminho relativo para armazenamento no BD
        caminho_relativo = os.path.join('anexos_clientes', str(cliente.id), nome_arquivo_seguro).replace('\\', '/')

        anexo = AnexoGeralCliente.objects.create(
            cliente=cliente,
            nome_documento=nome_documento_sanitizado,
            caminho_arquivo=caminho_relativo
        )

        serializer = self.get_serializer(anexo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download seguro forçando Content-Disposition: attachment e NoExec.
        """
        anexo = self.get_object()
        caminho_absoluto = os.path.join(settings.MEDIA_ROOT, anexo.caminho_arquivo)

        if not os.path.exists(caminho_absoluto):
            raise Http404("Arquivo físico não encontrado no servidor.")

        mime_type, _ = mimetypes.guess_type(caminho_absoluto)
        if not mime_type:
            mime_type = 'application/octet-stream'

        nome_download = f"{anexo.nome_documento}{os.path.splitext(anexo.caminho_arquivo)[1]}"
        response = FileResponse(open(caminho_absoluto, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = f'attachment; filename="{nome_download}"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
