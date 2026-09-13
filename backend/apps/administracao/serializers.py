"""
Serializers para o Módulo de Administração, Parâmetros Globais, SMTP,
Manifesto de Logs, Log Viewer e Painel de Lixeira (Soft Delete).
Em conformidade com docs/FSD.md - Seções 5.10, 8, 14, 16, 18, 19 e 20.
"""
from rest_framework import serializers
from django.utils import timezone
from core.utils import sanitizar_texto_maiusculo, CryptoManager
from .models import ConfiguracaoGlobal, ControleArquivoLog


class ConfiguracaoGlobalSerializer(serializers.ModelSerializer):
    """
    Serializer para o Singleton de Configurações Globais da Empresa.
    Protege a senha SMTP com criptografia AES-256 e omite a senha real nas leituras.
    """
    smtp_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Nova senha SMTP para criptografar (não retornada nas consultas)"
    )
    smtp_has_password = serializers.SerializerMethodField(
        read_only=True,
        help_text="Indica se há uma senha SMTP configurada e criptografada no banco"
    )
    aplicar_retroativo_expurgo = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
        help_text="Se True, aplica redução de prazo de retenção de logs retroativamente"
    )

    class Meta:
        model = ConfiguracaoGlobal
        fields = [
            'id',
            'razao_social',
            'cnpj',
            'telefone_contato',
            'endereco_oficina',
            'logo_empresa_url',
            'taxa_mao_de_obra_hora',
            'aliquota_iss',
            'aliquota_simples_nacional',
            'validade_orcamento_dias',
            'tempo_ociosidade_minutos',
            'tempo_expiracao_sessao_dias',
            'retencao_logs_dias',
            'smtp_host',
            'smtp_port',
            'smtp_user',
            'smtp_password',
            'smtp_has_password',
            'smtp_use_tls',
            'smtp_use_ssl',
            'email_remetente_nome',
            'aplicar_retroativo_expurgo',
            'updated_at',
            'updated_by_id',
        ]
        read_only_fields = ['id', 'updated_at', 'updated_by_id']

    def get_smtp_has_password(self, obj) -> bool:
        """Verifica se há senha SMTP gravada e não-vazia."""
        return bool(obj.smtp_password_encrypted and obj.smtp_password_encrypted.strip())

    def validate_razao_social(self, value):
        return sanitizar_texto_maiusculo(value)

    def validate_endereco_oficina(self, value):
        return sanitizar_texto_maiusculo(value)

    def validate_email_remetente_nome(self, value):
        return sanitizar_texto_maiusculo(value)

    def validate_taxa_mao_de_obra_hora(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("A taxa de mão de obra não pode ser negativa.")
        return value

    def validate_validade_orcamento_dias(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("A validade do orçamento deve ser de pelo menos 1 dia.")
        return value

    def validate_tempo_ociosidade_minutos(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("O tempo de ociosidade para soft lock deve ser de pelo menos 1 minuto.")
        return value

    def validate_retencao_logs_dias(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("O prazo de retenção de logs não pode ser negativo (mínimo 0 dias).")
        return value

    def update(self, instance, validated_data):
        # Trata criptografia da senha SMTP se informada
        smtp_password = validated_data.pop('smtp_password', None)
        if smtp_password is not None:
            if smtp_password.strip() == '':
                instance.smtp_password_encrypted = None
            else:
                instance.smtp_password_encrypted = CryptoManager.encrypt(smtp_password)

        aplicar_retroativo = validated_data.pop('aplicar_retroativo_expurgo', False)
        novo_prazo_retencao = validated_data.get('retencao_logs_dias')

        # Se houve alteração no prazo de retenção de logs, aciona o serviço
        prazo_anterior = instance.retencao_logs_dias
        instancia_atualizada = super().update(instance, validated_data)

        if novo_prazo_retencao is not None and novo_prazo_retencao != prazo_anterior:
            from .services import atualizar_retencao_logs
            atualizar_retencao_logs(
                novo_prazo_dias=novo_prazo_retencao,
                prazo_anterior_dias=prazo_anterior,
                aplicar_retroativo=aplicar_retroativo,
                usuario_id=self.context.get('request').user.id if self.context.get('request') else None
            )

        return instancia_atualizada


class TesteSmtpSerializer(serializers.Serializer):
    """Serializer para validação dos dados de teste de disparo SMTP em tempo real."""
    destinatario = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="E-mail destinatário para o envio de teste. Se omitido, usa o usuário SMTP ou Admin"
    )
    email_destino = serializers.EmailField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Alias para destinatario"
    )
    smtp_host = serializers.CharField(required=False, allow_blank=True)
    smtp_port = serializers.IntegerField(required=False)
    smtp_user = serializers.CharField(required=False, allow_blank=True)
    smtp_password = serializers.CharField(required=False, allow_blank=True, write_only=True)
    smtp_use_tls = serializers.BooleanField(required=False)
    smtp_use_ssl = serializers.BooleanField(required=False)
    email_remetente_nome = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs.get('destinatario') and attrs.get('email_destino'):
            attrs['destinatario'] = attrs['email_destino']
        return attrs


class ControleArquivoLogSerializer(serializers.ModelSerializer):
    """Serializer para visualização e auditoria do Manifesto de Logs Rotativos."""
    data_log = serializers.SerializerMethodField(read_only=True)
    total_eventos = serializers.SerializerMethodField(read_only=True)
    quantidade_linhas = serializers.SerializerMethodField(read_only=True)
    dias_restantes = serializers.SerializerMethodField(read_only=True)
    tamanho_bytes = serializers.SerializerMethodField(read_only=True)
    tamanho_formatado = serializers.SerializerMethodField(read_only=True)
    is_expirado = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ControleArquivoLog
        fields = [
            'id',
            'caminho_arquivo_fisico',
            'data_criacao',
            'data_log',
            'total_eventos',
            'quantidade_linhas',
            'data_expurgo_planejada',
            'dias_restantes',
            'tamanho_bytes',
            'tamanho_formatado',
            'is_expirado',
            'created_at',
        ]
        read_only_fields = fields

    def get_data_log(self, obj) -> str:
        return obj.data_criacao.strftime('%Y-%m-%d') if obj.data_criacao else ''

    def get_total_eventos(self, obj) -> int:
        import os
        from django.conf import settings
        caminho_completo = os.path.join(settings.BASE_DIR, obj.caminho_arquivo_fisico)
        if not os.path.exists(caminho_completo):
            logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
            caminho_completo = os.path.join(logs_dir, os.path.basename(obj.caminho_arquivo_fisico))
        if os.path.exists(caminho_completo):
            try:
                with open(caminho_completo, 'r', encoding='utf-8', errors='replace') as f:
                    return sum(1 for line in f if line.strip())
            except Exception:
                return 0
        return 0

    def get_quantidade_linhas(self, obj) -> int:
        return self.get_total_eventos(obj)

    def get_dias_restantes(self, obj) -> int:
        hoje = timezone.localdate()
        return (obj.data_expurgo_planejada - hoje).days

    def get_is_expirado(self, obj) -> bool:
        hoje = timezone.localdate()
        return obj.data_expurgo_planejada <= hoje

    def get_tamanho_bytes(self, obj) -> int:
        import os
        from django.conf import settings
        caminho_completo = os.path.join(settings.BASE_DIR, obj.caminho_arquivo_fisico)
        if not os.path.exists(caminho_completo):
            logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
            caminho_completo = os.path.join(logs_dir, os.path.basename(obj.caminho_arquivo_fisico))
        if os.path.exists(caminho_completo):
            return os.path.getsize(caminho_completo)
        return 0

    def get_tamanho_formatado(self, obj) -> str:
        bytes_size = self.get_tamanho_bytes(obj)
        if bytes_size < 1024:
            return f"{bytes_size} B"
        elif bytes_size < 1024 * 1024:
            return f"{bytes_size / 1024:.1f} KB"
        else:
            return f"{bytes_size / (1024 * 1024):.2f} MB"


class LogViewerFilterSerializer(serializers.Serializer):
    """Validador de filtros para a leitura segura do Log Viewer."""
    arquivo = serializers.CharField(
        required=False,
        default='hoje',
        help_text="Nome do arquivo (ex: app-2026-08-23.log) ou data YYYY-MM-DD ou 'hoje'"
    )
    data = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Data do log no formato YYYY-MM-DD"
    )
    nivel = serializers.CharField(
        required=False,
        default='TODOS',
        allow_blank=True,
        help_text="Nível de severidade ou categoria (TODOS, AUDIT, SEGURANCA, ERROR, WARNING, INFO, DEBUG, CRITICAL)"
    )
    busca = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(default=100, min_value=1, max_value=1000, required=False)
    offset = serializers.IntegerField(default=0, min_value=0, required=False)

    def validate_nivel(self, value):
        if not value:
            return 'TODOS'
        return value.strip().upper()


class LixeiraItemSerializer(serializers.Serializer):
    """Serializer universal de representação de registros na Lixeira."""
    entidade = serializers.CharField(help_text="Código da entidade (ex: orcamentos, faturas, clientes)")
    entidade_nome = serializers.CharField(help_text="Nome amigável da entidade (ex: Orçamento)")
    id = serializers.IntegerField(help_text="ID da chave primária do registro")
    identificador = serializers.CharField(help_text="Identificador principal (ex: Nº Orçamento, Razão Social, Nome)")
    detalhes = serializers.CharField(help_text="Informações adicionais / resumo do registro")
    deleted_at = serializers.DateTimeField(help_text="Data e hora da exclusão lógica")
    deleted_by_id = serializers.IntegerField(allow_null=True, help_text="ID do usuário que inativou")
    deleted_by_nome = serializers.CharField(allow_null=True, help_text="Nome do usuário que inativou")
    pode_restaurar = serializers.BooleanField(help_text="Indica se o usuário logado tem permissão para restaurar")


class ExpurgoLogRequestSerializer(serializers.Serializer):
    """Validador do endpoint de disparo do expurgo manual/agendado."""
    enviar_email_backup = serializers.BooleanField(
        default=True,
        required=False,
        help_text="Se True, envia backup por e-mail dos logs antes do expurgo físico"
    )
    data_corte = serializers.DateField(
        required=False,
        allow_null=True,
        help_text="Data limite para expurgo. Padrão é a data atual (hoje)"
    )
