"""
Serializers para o módulo de Cadastros Básicos: Clientes, Fornecedores, Equipamentos, Vínculos e Anexos.
Em conformidade com docs/FSD.md, docs/PLANO.md e regras de segurança.
"""
from rest_framework import serializers
from core.utils import (
    sanitizar_texto_maiusculo,
    limpar_apenas_digitos,
    validar_cpf,
    validar_cnpj,
    validar_placa
)
from apps.cadastros.models import (
    ClienteFornecedor,
    ClienteContato,
    Equipamento,
    ClienteEquipamento,
    AnexoGeralCliente
)


class ClienteContatoSerializer(serializers.ModelSerializer):
    """
    Serializer para contatos e telefones vinculados ao Cliente/Fornecedor.
    """
    class Meta:
        model = ClienteContato
        fields = [
            'id',
            'nome_contato',
            'telefone',
            'is_whatsapp',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_nome_contato(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError("O Nome do Contato é obrigatório.")
        return sanitizar_texto_maiusculo(value)

    def validate_telefone(self, value):
        if not value:
            raise serializers.ValidationError("O Telefone é obrigatório.")
        tel_limpo = limpar_apenas_digitos(value)
        if len(tel_limpo) < 8 or len(tel_limpo) > 12:
            raise serializers.ValidationError("Telefone inválido. Informe o DDD e os dígitos (10 ou 11 dígitos).")
        return tel_limpo


class ClienteFornecedorSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Clientes e Fornecedores com contatos aninhados, validações e sanitização universal.
    """
    quantidade_equipamentos_ativos = serializers.SerializerMethodField()
    contatos = ClienteContatoSerializer(many=True, required=False)

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
            'iss_retido',
            'contatos',
            'quantidade_equipamentos_ativos',
            'created_at',
            'updated_at',
            'created_by_id',
            'updated_by_id',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_id', 'updated_by_id']

    def get_quantidade_equipamentos_ativos(self, obj):
        return obj.equipamentos_vinculados.filter(is_ativo=True).count()

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # Normaliza tipo case-insensitive (CLIENTE -> Cliente, FORNECEDOR -> Fornecedor, AMBOS -> Ambos)
        if 'tipo' in data and isinstance(data['tipo'], str):
            tipo_upper = data['tipo'].upper().strip()
            if tipo_upper == 'CLIENTE':
                data['tipo'] = 'Cliente'
            elif tipo_upper == 'FORNECEDOR':
                data['tipo'] = 'Fornecedor'
            elif tipo_upper in ('AMBOS', 'CLIENTE/FORNECEDOR'):
                data['tipo'] = 'Ambos'

        # Normaliza tipo_pessoa (PF / PJ)
        if 'tipo_pessoa' in data and isinstance(data['tipo_pessoa'], str):
            data['tipo_pessoa'] = data['tipo_pessoa'].upper().strip()

        # Normaliza email vazio para None
        if 'email' in data and (data['email'] is None or not str(data['email']).strip()):
            data['email'] = None

        return super().to_internal_value(data)

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
        if value:
            tel_limpo = limpar_apenas_digitos(value)
            if len(tel_limpo) < 8 or len(tel_limpo) > 12:
                raise serializers.ValidationError("Telefone inválido. Informe o DDD e os dígitos (10 ou 11 dígitos).")
            return tel_limpo
        return value

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

    def create(self, validated_data):
        contatos_data = validated_data.pop('contatos', [])
        
        # Se telefone principal não informado mas houver contatos, usa o 1º telefone
        if not validated_data.get('telefone') and contatos_data:
            validated_data['telefone'] = contatos_data[0].get('telefone')
            
        cliente = ClienteFornecedor.objects.create(**validated_data)
        
        for c_data in contatos_data:
            ClienteContato.objects.create(cliente=cliente, **c_data)
            
        return cliente

    def update(self, instance, validated_data):
        contatos_data = validated_data.pop('contatos', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if contatos_data is not None:
            instance.contatos.all().delete()
            for c_data in contatos_data:
                ClienteContato.objects.create(cliente=instance, **c_data)
                
            if not instance.telefone and contatos_data:
                instance.telefone = contatos_data[0].get('telefone')
                
        instance.save()
        return instance


class EquipamentoSerializer(serializers.ModelSerializer):
    """
    Serializer para Equipamentos e Veículos atendidos na oficina com vínculo de proprietário.
    """
    cliente_atual = serializers.SerializerMethodField()
    cliente_atual_nome = serializers.SerializerMethodField()
    cliente_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    em_patio = serializers.SerializerMethodField()
    orcamento_em_execucao = serializers.SerializerMethodField()

    class Meta:
        model = Equipamento
        fields = [
            'id',
            'placa',
            'identificacao',
            'descricao',
            'cliente_atual',
            'cliente_atual_nome',
            'cliente_id',
            'em_patio',
            'orcamento_em_execucao',
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

    def get_cliente_atual_nome(self, obj):
        vinculo_ativo = obj.historico_clientes.filter(is_ativo=True).select_related('cliente').first()
        return vinculo_ativo.cliente.nome_razao if vinculo_ativo else None

    def get_em_patio(self, obj):
        return obj.orcamentos.filter(
            status_operacional__in=['APROVADO', 'EM_EXECUCAO'],
            deleted_at__isnull=True
        ).exists()

    def get_orcamento_em_execucao(self, obj):
        orc = obj.orcamentos.filter(
            status_operacional__in=['APROVADO', 'EM_EXECUCAO'],
            deleted_at__isnull=True
        ).order_by('-id').first()
        if orc:
            return {
                "id": orc.id,
                "status_operacional": orc.status_operacional
            }
        return None

    def validate_placa(self, value):
        if value:
            placa_limpa = sanitizar_texto_maiusculo(value).replace("-", "").replace(" ", "")
            if not validar_placa(placa_limpa):
                raise serializers.ValidationError(
                    "Placa inválida. Deve seguir o padrão antigo (ex: ABC-1234) ou Mercosul (ex: ABC-1D23): "
                    "3 letras iniciais, 4º dígito numérico, 5º dígito letra ou número e 2 dígitos finais numéricos."
                )
            return f"{placa_limpa[:3]}-{placa_limpa[3:]}"
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

    def create(self, validated_data):
        cliente_id = validated_data.pop('cliente_id', None)
        equipamento = super().create(validated_data)
        if cliente_id:
            ClienteEquipamento.objects.create(
                cliente_id=cliente_id,
                equipamento=equipamento,
                is_ativo=True
            )
        return equipamento

    def update(self, instance, validated_data):
        cliente_id = validated_data.pop('cliente_id', None)
        equipamento = super().update(instance, validated_data)
        
        if cliente_id is not None:
            vinculo_atual = instance.historico_clientes.filter(is_ativo=True).first()
            id_atual = vinculo_atual.cliente_id if vinculo_atual else None
            
            if id_atual != cliente_id:
                if vinculo_atual:
                    vinculo_atual.is_ativo = False
                    vinculo_atual.save()
                if cliente_id:
                    ClienteEquipamento.objects.create(
                        cliente_id=cliente_id,
                        equipamento=instance,
                        is_ativo=True
                    )
        return equipamento


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
