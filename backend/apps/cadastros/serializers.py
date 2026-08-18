"""
Serializers para o módulo de Cadastros Básicos: Clientes, Fornecedores, Equipamentos, Vínculos e Anexos.
Em conformidade com docs/FSD.md, docs/PLANO.md e regras de segurança.
"""
from rest_framework import serializers
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


class ClienteFornecedorSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Clientes e Fornecedores com validações matemáticas e sanitização universal.
    """
    quantidade_equipamentos_ativos = serializers.SerializerMethodField()

    class Meta:
        model = ClienteFornecedor
        fields = [
            'id',
            'tipo',
            'tipo_pessoa',
            'nome_razao',
            'nome_fantasia',
            'cnpj_cpf',
            'inscricao_estadual',
            'isento_ie',
            'email',
            'telefone',
            'cep',
            'logradouro',
            'numero',
            'complemento',
            'bairro',
            'cidade',
            'uf',
            'quantidade_equipamentos_ativos',
            'created_at',
            'updated_at',
            'created_by_id',
            'updated_by_id',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_id', 'updated_by_id']

    def get_quantidade_equipamentos_ativos(self, obj):
        return obj.equipamentos_vinculados.filter(is_ativo=True).count()

    def validate_nome_razao(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("O Nome / Razão Social é de preenchimento obrigatório.")
        return sanitizar_texto_maiusculo(value)

    def validate_nome_fantasia(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_inscricao_estadual(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_logradouro(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_numero(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_complemento(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_bairro(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_cidade(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_uf(self, value):
        if value:
            uf_limpa = sanitizar_texto_maiusculo(value)
            if len(uf_limpa) != 2:
                raise serializers.ValidationError("A UF deve conter exatamente 2 caracteres (ex: SP, MG, RJ).")
            return uf_limpa
        return value

    def validate_email(self, value):
        if value:
            return str(value).lower().strip()
        return value

    def validate_telefone(self, value):
        if not value:
            raise serializers.ValidationError("O Telefone de contato é obrigatório.")
        tel_limpo = limpar_apenas_digitos(value)
        if len(tel_limpo) < 8 or len(tel_limpo) > 12:
            raise serializers.ValidationError("Telefone inválido. Informe o DDD e os dígitos (10 ou 11 dígitos).")
        return tel_limpo

    def validate_cep(self, value):
        if value:
            cep_limpo = limpar_apenas_digitos(value)
            if len(cep_limpo) != 8:
                raise serializers.ValidationError("CEP inválido. O CEP deve conter 8 dígitos numéricos.")
            return cep_limpo
        return value

    def validate(self, attrs):
        tipo_pessoa = attrs.get('tipo_pessoa', getattr(self.instance, 'tipo_pessoa', 'PJ'))
        cnpj_cpf = attrs.get('cnpj_cpf', getattr(self.instance, 'cnpj_cpf', None))

        if cnpj_cpf:
            doc_limpo = limpar_apenas_digitos(cnpj_cpf)
            
            # Validação matemática por tipo de pessoa
            if tipo_pessoa == 'PF':
                if len(doc_limpo) != 11:
                    raise serializers.ValidationError({"cnpj_cpf": "O CPF deve conter exatamente 11 dígitos numéricos."})
                if not validar_cpf(doc_limpo):
                    raise serializers.ValidationError({"cnpj_cpf": "CPF inválido. Os dígitos verificadores não conferem matematicamente."})
            elif tipo_pessoa == 'PJ':
                if len(doc_limpo) != 14:
                    raise serializers.ValidationError({"cnpj_cpf": "O CNPJ deve conter exatamente 14 dígitos numéricos."})
                if not validar_cnpj(doc_limpo):
                    raise serializers.ValidationError({"cnpj_cpf": "CNPJ inválido. Os dígitos verificadores não conferem matematicamente."})

            # Blindagem Anti-Duplicação (excluindo registros que sofreram soft delete)
            qs = ClienteFornecedor.objects.filter(cnpj_cpf=doc_limpo, deleted_at__isnull=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                duplicado = qs.first()
                raise serializers.ValidationError({
                    "cnpj_cpf": f"Este CPF/CNPJ já está cadastrado no sistema para '{duplicado.nome_razao}' (ID #{duplicado.id})."
                })

            attrs['cnpj_cpf'] = doc_limpo

        return attrs


class EquipamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para Equipamentos e Veículos atendidos na oficina.
    """
    cliente_atual = serializers.SerializerMethodField()

    class Meta:
        model = Equipamento
        fields = [
            'id',
            'placa',
            'identificacao',
            'descricao',
            'cliente_atual',
            'created_at',
            'updated_at',
            'created_by_id',
            'updated_by_id',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_id', 'updated_by_id']

    def get_cliente_atual(self, obj):
        vinculo_ativo = obj.historico_clientes.filter(is_ativo=True).select_related('cliente').first()
        if vinculo_ativo:
            return {
                "id": vinculo_ativo.cliente.id,
                "nome_razao": vinculo_ativo.cliente.nome_razao,
                "telefone": vinculo_ativo.cliente.telefone,
                "data_vinculo": vinculo_ativo.data_vinculo,
            }
        return None

    def validate_placa(self, value):
        if value:
            placa_limpa = sanitizar_texto_maiusculo(value).replace("-", "").replace(" ", "")
            if len(placa_limpa) != 7:
                raise serializers.ValidationError("Placa inválida. Deve conter 7 caracteres alfanuméricos (ex: ABC-1234 ou ABC1D23).")
            return placa_limpa
        return value

    def validate_identificacao(self, value):
        if value:
            return sanitizar_texto_maiusculo(value)
        return value

    def validate_descricao(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("A descrição do equipamento é de preenchimento obrigatório.")
        return sanitizar_texto_maiusculo(value)

    def validate(self, attrs):
        placa = attrs.get('placa', getattr(self.instance, 'placa', None))
        identificacao = attrs.get('identificacao', getattr(self.instance, 'identificacao', None))
        
        if not placa and not identificacao:
            raise serializers.ValidationError({
                "identificacao": "Informe ao menos a Placa ou a Identificação Técnica (Frota/Chassi/Código Interno)."
            })
        return attrs


class ClienteEquipamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para o histórico de vínculos entre Clientes e Equipamentos.
    Ao vincular como ativo, desativa automaticamente o vínculo anterior do equipamento.
    """
    cliente_detalhes = serializers.SerializerMethodField(read_only=True)
    equipamento_detalhes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClienteEquipamento
        fields = [
            'id',
            'cliente',
            'equipamento',
            'cliente_detalhes',
            'equipamento_detalhes',
            'data_vinculo',
            'is_ativo',
        ]
        read_only_fields = ['id']

    def get_cliente_detalhes(self, obj):
        return {
            "id": obj.cliente.id,
            "nome_razao": obj.cliente.nome_razao,
            "telefone": obj.cliente.telefone,
            "cnpj_cpf": obj.cliente.cnpj_cpf
        }

    def get_equipamento_detalhes(self, obj):
        return {
            "id": obj.equipamento.id,
            "placa": obj.equipamento.placa,
            "identificacao": obj.equipamento.identificacao,
            "descricao": obj.equipamento.descricao
        }

    def create(self, validated_data):
        is_ativo = validated_data.get('is_ativo', True)
        equipamento = validated_data.get('equipamento')

        # Se for um novo vínculo ativo, desativa com segurança os vínculos anteriores deste equipamento
        if is_ativo and equipamento:
            ClienteEquipamento.objects.filter(
                equipamento=equipamento,
                is_ativo=True
            ).update(is_ativo=False)

        return super().create(validated_data)


class AnexoGeralClienteSerializer(serializers.ModelSerializer):
    """
    Serializer para anexos de clientes.
    """
    class Meta:
        model = AnexoGeralCliente
        fields = [
            'id',
            'cliente',
            'nome_documento',
            'caminho_arquivo',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_nome_documento(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("O nome do documento é obrigatório.")
        return sanitizar_texto_maiusculo(value)
