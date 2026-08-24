"""
Camada de Serviços do Módulo de Administração.
Contempla:
- Gestão de SMTP, Presets e Disparo de Teste em Tempo Real.
- Sincronização do Manifesto TTL e Rotina de Expurgo com Backup por E-mail.
- Leitura Segura de Logs do Servidor (Blindagem contra Path Traversal).
- Motor de Lixeira Unificada e Restauração Lógica (16 Entidades) com segregação de visões.
"""
import os
import glob
import logging
from datetime import timedelta
from typing import Dict, List, Any, Optional

from django.conf import settings
from django.utils import timezone
from django.core.mail import get_connection, EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.db import transaction

from core.utils import CryptoManager
from .models import ConfiguracaoGlobal, ControleArquivoLog

logger = logging.getLogger('emc_soldas')


# ==============================================================================
# 1. SERVIÇOS DE SMTP E TESTE EM TEMPO REAL
# ==============================================================================

def obter_presets_smtp() -> List[Dict[str, Any]]:
    """Retorna presets rápidos para configuração simplificada de provedores SMTP."""
    return [
        {
            "id": "gmail",
            "nome": "Google Gmail (com Senha de App)",
            "host": "smtp.gmail.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "instrucoes": "Utilize seu e-mail do Gmail e gere uma 'Senha de App' de 16 letras na sua Conta Google (Segurança > Verificação em 2 etapas > Senhas de app)."
        },
        {
            "id": "outlook",
            "nome": "Microsoft Outlook / Office 365",
            "host": "smtp.office365.com",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "instrucoes": "Utilize seu e-mail corporativo Microsoft ou conta Outlook com autenticação moderna / SMTP habilitado."
        },
        {
            "id": "custom",
            "nome": "Servidor SMTP Personalizado",
            "host": "",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "instrucoes": "Insira os dados fornecidos pelo seu provedor de hospedagem de e-mails (Host, Porta, Usuário e Senha)."
        }
    ]


def testar_conexao_smtp(dados_teste: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Testa a conectividade com o servidor SMTP e envia um e-mail de teste em tempo real.
    Se dados_teste for omitido ou parcial, utiliza a configuração gravada no banco.
    """
    config = ConfiguracaoGlobal.get_solo()
    
    dados = dados_teste or {}
    host = dados.get('smtp_host') or config.smtp_host or 'localhost'
    port = dados.get('smtp_port') or config.smtp_port or 587
    user = dados.get('smtp_user') if 'smtp_user' in dados else config.smtp_user
    use_tls = dados.get('smtp_use_tls') if 'smtp_use_tls' in dados else config.smtp_use_tls
    use_ssl = dados.get('smtp_use_ssl') if 'smtp_use_ssl' in dados else config.smtp_use_ssl
    nome_remetente = dados.get('email_remetente_nome') or config.email_remetente_nome or 'EMC Soldas'

    # Senha: se informada no payload usa ela; senão descriptografa do banco
    if 'smtp_password' in dados and dados['smtp_password']:
        password = dados['smtp_password']
    else:
        password = CryptoManager.decrypt(config.smtp_password_encrypted) if config.smtp_password_encrypted else ''

    destinatario = dados.get('destinatario')
    if not destinatario:
        destinatario = user if (user and '@' in user) else 'admin@emcsoldas.com.br'

    remetente_formatado = f"{nome_remetente} <{user or 'nao-responda@emcsoldas.com.br'}>"

    # Em ambiente de testes (locmem) ou console, utiliza a conexão configurada
    backend_configurado = getattr(settings, 'EMAIL_BACKEND', '')
    try:
        if 'locmem' in backend_configurado or 'console' in backend_configurado:
            conexao = get_connection()
        else:
            conexao = EmailBackend(
                host=host,
                port=port,
                username=user,
                password=password,
                use_tls=use_tls,
                use_ssl=use_ssl,
                timeout=10
            )

        assunto = "[EMC SOLDAS] Teste de Disparo de E-mail (SMTP)"
        corpo = (
            f"Prezado(a) Administrador(a),\n\n"
            f"Este é um e-mail de teste disparado com sucesso pela Central Administrativa do sistema EMC Soldas.\n\n"
            f"Configurações testadas:\n"
            f"- Servidor (Host): {host}:{port}\n"
            f"- Usuário SMTP: {user or 'Não configurado'}\n"
            f"- Criptografia: {'TLS' if use_tls else ('SSL' if use_ssl else 'Nenhuma')}\n"
            f"- Data/Hora do Teste: {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            f"Se você recebeu esta mensagem, o serviço de envio de e-mails está 100% operacional.\n\n"
            f"Atenciosamente,\n"
            f"EMC Soldas - Gestão e Governança"
        )

        email = EmailMessage(
            subject=assunto,
            body=corpo,
            from_email=remetente_formatado,
            to=[destinatario],
            connection=conexao
        )
        email.send(fail_silently=False)

        return {
            "sucesso": True,
            "mensagem": f"E-mail de teste enviado com sucesso para {destinatario}.",
            "detalhes": {
                "host": host,
                "port": port,
                "destinatario": destinatario,
                "remetente": remetente_formatado,
                "timestamp": timezone.localtime().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"[SMTP TEST FAIL] Falha no teste de e-mail: {str(e)}")
        return {
            "sucesso": False,
            "erro": f"Falha na comunicação com o servidor SMTP: {str(e)}",
            "detalhes": {
                "host": host,
                "port": port,
                "destinatario": destinatario
            }
        }


# ==============================================================================
# 2. MANIFESTO TTL, EXPURGO E BACKUP DE LOGS
# ==============================================================================

def sincronizar_manifesto_logs() -> Dict[str, Any]:
    """
    Varre a pasta física backend/logs/ e registra no manifesto qualquer
    arquivo físico app-YYYY-MM-DD.log que ainda não conste no banco.
    """
    config = ConfiguracaoGlobal.get_solo()
    retencao_dias = config.retencao_logs_dias or 30

    logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    padrao_arquivos = os.path.join(logs_dir, 'app-*.log')
    arquivos_encontrados = glob.glob(padrao_arquivos)

    novos_registros = 0
    for caminho_completo in arquivos_encontrados:
        nome_arquivo = os.path.basename(caminho_completo)
        caminho_relativo = os.path.join('logs', nome_arquivo).replace('\\', '/')

        # Extrai data do nome do arquivo: app-YYYY-MM-DD.log
        try:
            data_str = nome_arquivo.replace('app-', '').replace('.log', '')
            ano, mes, dia = map(int, data_str.split('-'))
            import datetime
            data_criacao = datetime.date(ano, mes, dia)
        except Exception:
            data_criacao = timezone.localdate()

        data_expurgo = data_criacao + timedelta(days=retencao_dias)

        manifesto, created = ControleArquivoLog.objects.get_or_create(
            caminho_arquivo_fisico=caminho_relativo,
            defaults={
                'data_criacao': data_criacao,
                'data_expurgo_planejada': data_expurgo
            }
        )
        if created:
            novos_registros += 1

    return {
        "sucesso": True,
        "total_arquivos": len(arquivos_encontrados),
        "novos_indexados": novos_registros
    }


def atualizar_retencao_logs(novo_prazo_dias: int, prazo_anterior_dias: int,
                            aplicar_retroativo: bool = False, usuario_id: int = None) -> Dict[str, Any]:
    """
    Atualiza as datas de expurgo do manifesto após alteração do prazo global.
    - Se prazo aumentou: recalcula todas as datas futuras.
    - Se prazo diminuiu e aplicar_retroativo=True: recalcula e expurga os vencidos.
    - Se prazo diminuiu e aplicar_retroativo=False: mantém os existentes e aplica aos futuros.
    """
    sincronizar_manifesto_logs()

    if novo_prazo_dias > prazo_anterior_dias or aplicar_retroativo:
        manifestos = ControleArquivoLog.objects.all()
        for item in manifestos:
            item.data_expurgo_planejada = item.data_criacao + timedelta(days=novo_prazo_dias)
            item.save(update_fields=['data_expurgo_planejada'])

        if aplicar_retroativo and novo_prazo_dias < prazo_anterior_dias:
            # Dispara expurgo imediato para os que ficaram fora do prazo
            return expurgar_arquivos_log(enviar_email_backup=True)

    return {"sucesso": True, "novo_prazo_dias": novo_prazo_dias}


def expurgar_arquivos_log(enviar_email_backup: bool = True, data_corte=None) -> Dict[str, Any]:
    """
    Rotina de expurgo de logs por decurso de prazo (TTL):
    1. Localiza registros no manifesto com data_expurgo_planejada <= data_corte (hoje).
    2. Se enviar_email_backup=True, envia e-mail com os arquivos .log em anexo.
    3. Exclui com segurança os arquivos físicos em disco e remove as linhas do manifesto.
    """
    sincronizar_manifesto_logs()

    hoje = data_corte or timezone.localdate()
    manifestos_expirados = ControleArquivoLog.objects.filter(data_expurgo_planejada__lte=hoje)

    if not manifestos_expirados.exists():
        return {
            "sucesso": True,
            "mensagem": "Nenhum arquivo de log atingiu a data de expurgo planejada.",
            "total_expurgados": 0,
            "arquivos": []
        }

    config = ConfiguracaoGlobal.get_solo()
    logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))

    arquivos_para_deletar = []
    arquivos_anexos = []

    for item in manifestos_expirados:
        nome_arquivo = os.path.basename(item.caminho_arquivo_fisico)
        caminho_real = os.path.join(logs_dir, nome_arquivo)
        if os.path.exists(caminho_real):
            arquivos_para_deletar.append((item, caminho_real, nome_arquivo))
            arquivos_anexos.append(caminho_real)
        else:
            # Arquivo físico já não existe, apenas baixa no manifesto
            arquivos_para_deletar.append((item, None, nome_arquivo))

    email_enviado = False
    if enviar_email_backup and arquivos_anexos:
        try:
            destinatario = config.smtp_user if (config.smtp_user and '@' in config.smtp_user) else 'admin@emcsoldas.com.br'
            remetente_formatado = f"{config.email_remetente_nome} <{config.smtp_user or 'nao-responda@emcsoldas.com.br'}>"

            backend_configurado = getattr(settings, 'EMAIL_BACKEND', '')
            if 'locmem' in backend_configurado or 'console' in backend_configurado:
                conexao = get_connection()
            else:
                conexao = EmailBackend(
                    host=config.smtp_host or 'localhost',
                    port=config.smtp_port or 587,
                    username=config.smtp_user,
                    password=CryptoManager.decrypt(config.smtp_password_encrypted) if config.smtp_password_encrypted else '',
                    use_tls=config.smtp_use_tls,
                    use_ssl=config.smtp_use_ssl,
                    timeout=15
                )

            assunto = f"[EMC SOLDAS - BACKUP DE AUDITORIA] Arquivo(s) de Log Expirado(s) em {hoje.strftime('%d/%m/%Y')}"
            
            lista_nomes = "\n".join(f"- {os.path.basename(arq)} ({os.path.getsize(arq)} bytes)" for arq in arquivos_anexos)
            corpo = (
                f"Prezado(a) Administrador(a),\n\n"
                f"Informamos que a rotina de expurgo automático por decurso de prazo (TTL) foi executada em {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')}.\n\n"
                f"Os seguintes arquivos físicos de log atingiram o prazo de retenção ({config.retencao_logs_dias} dias) e estão anexados a esta mensagem como backup permanente antes da exclusão física do servidor:\n\n"
                f"{lista_nomes}\n\n"
                f"Após a confirmação deste envio, os arquivos foram excluídos com segurança do disco.\n\n"
                f"Atenciosamente,\n"
                f"EMC Soldas - Governança e Auditoria"
            )

            msg = EmailMessage(
                subject=assunto,
                body=corpo,
                from_email=remetente_formatado,
                to=[destinatario],
                connection=conexao
            )

            for caminho_arq in arquivos_anexos:
                msg.attach_file(caminho_arq)

            msg.send(fail_silently=False)
            email_enviado = True
            logger.info(f"[EXPURGO BACKUP] Backup de {len(arquivos_anexos)} arquivo(s) de log enviado para {destinatario}.")
        except Exception as e:
            logger.error(f"[EXPURGO BACKUP FAIL] Falha ao enviar e-mail de backup dos logs: {str(e)}")
            # Em caso de falha de e-mail em produção, podemos logar e prosseguir ou abortar conforme criticidade

    # Exclusão física e remoção no manifesto
    total_deletados = 0
    nomes_deletados = []
    with transaction.atomic():
        for item, caminho_real, nome_arquivo in arquivos_para_deletar:
            if caminho_real and os.path.exists(caminho_real):
                try:
                    os.remove(caminho_real)
                except Exception as e:
                    logger.error(f"[EXPURGO FILE ERROR] Não foi possível remover o arquivo {caminho_real}: {str(e)}")
            item.delete()
            total_deletados += 1
            nomes_deletados.append(nome_arquivo)

    logger.info(f"[EXPURGO LOGS] {total_deletados} arquivo(s) de log expurgado(s) com sucesso: {', '.join(nomes_deletados)}")

    return {
        "sucesso": True,
        "mensagem": f"{total_deletados} arquivo(s) de log expurgado(s) com sucesso.",
        "total_expurgados": total_deletados,
        "arquivos": nomes_deletados,
        "email_backup_enviado": email_enviado
    }


# ==============================================================================
# 3. LOG VIEWER SEGURO DO SERVIDOR (BLINDAGEM ANTI-PATH TRAVERSAL)
# ==============================================================================

def ler_arquivo_log_seguro(identificador_arquivo: str = 'hoje', nivel: str = 'TODOS',
                           busca: str = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Leitura segura e paginada dos arquivos de log físicos diários.
    Blindagem absoluta contra Path Traversal (../, /, \\, arquivos fora de logs/).
    """
    logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)

    # Resolve o nome do arquivo seguro
    ident = str(identificador_arquivo).strip() if identificador_arquivo else ''
    if not ident or ident in ('hoje', 'undefined', 'null'):
        nome_arquivo = f"app-{timezone.localdate().strftime('%Y-%m-%d')}.log"
    elif ident.startswith('app-') and ident.endswith('.log'):
        nome_arquivo = os.path.basename(ident)
    elif len(ident) == 10 and ident.count('-') == 2:
        # Formato YYYY-MM-DD
        nome_arquivo = f"app-{ident}.log"
    else:
        nome_arquivo = os.path.basename(ident)
        if not nome_arquivo.endswith('.log'):
            nome_arquivo = f"{nome_arquivo}.log"

    # Blindagem estrita: proíbe caracteres de navegação e garante que está na pasta logs
    nome_seguro = os.path.basename(nome_arquivo)
    caminho_absoluto = os.path.abspath(os.path.join(logs_dir, nome_seguro))
    logs_dir_absoluto = os.path.abspath(logs_dir)

    if not caminho_absoluto.startswith(logs_dir_absoluto) or not nome_seguro.endswith('.log'):
        raise PermissionError("Acesso negado: Tentativa de navegação não autorizada fora do diretório de logs.")

    if not os.path.exists(caminho_absoluto):
        return {
            "arquivo": nome_seguro,
            "existe": False,
            "conteudo": "Arquivo de log ainda não possui registros.",
            "total_linhas": 0,
            "total_linhas_arquivo": 0,
            "total_linhas_filtradas": 0,
            "linhas": [],
            "arquivos_disponiveis": listar_arquivos_log_disponiveis()
        }

    # Leitura das linhas do arquivo
    with open(caminho_absoluto, 'r', encoding='utf-8', errors='replace') as f:
        todas_linhas = f.readlines()

    # Aplica filtros de nível e busca
    linhas_processadas = []
    nivel_filtro = nivel.upper() if nivel else 'TODOS'
    termo_busca = busca.strip().lower() if busca and busca.strip() else None

    for i, linha in enumerate(reversed(todas_linhas)):
        texto = linha.strip()
        if not texto:
            continue

        # Filtro de Nível
        if nivel_filtro != 'TODOS':
            if f"[{nivel_filtro}]" not in texto and f" {nivel_filtro} " not in texto:
                continue

        # Filtro de Busca Textual
        if termo_busca:
            if termo_busca not in texto.lower():
                continue

        linhas_processadas.append({
            "linha_numero": len(todas_linhas) - i,
            "conteudo": texto,
            "is_error": "ERROR" in texto or "CRITICAL" in texto,
            "is_warning": "WARNING" in texto,
            "is_audit": "[AUDIT]" in texto
        })

    total_filtradas = len(linhas_processadas)
    linhas_paginadas = linhas_processadas[offset: offset + limit]
    conteudo_texto = "\n".join(item["conteudo"] for item in linhas_paginadas)

    return {
        "arquivo": nome_seguro,
        "existe": True,
        "tamanho_bytes": os.path.getsize(caminho_absoluto),
        "total_linhas_arquivo": len(todas_linhas),
        "total_linhas_filtradas": total_filtradas,
        "limit": limit,
        "offset": offset,
        "conteudo": conteudo_texto or "Nenhum evento registrado com os filtros informados.",
        "linhas": linhas_paginadas,
        "arquivos_disponiveis": listar_arquivos_log_disponiveis()
    }


def listar_arquivos_log_disponiveis() -> List[Dict[str, Any]]:
    """Lista todos os arquivos .log existentes na pasta de logs."""
    logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
    if not os.path.exists(logs_dir):
        return []

    arquivos = glob.glob(os.path.join(logs_dir, 'app-*.log'))
    resultado = []
    for caminho in sorted(arquivos, reverse=True):
        nome = os.path.basename(caminho)
        data_str = nome.replace('app-', '').replace('.log', '')
        resultado.append({
            "nome": nome,
            "data": data_str,
            "tamanho_bytes": os.path.getsize(caminho)
        })
    return resultado


# ==============================================================================
# 4. MOTOR DA LIXEIRA UNIFICADA E RESTAURAÇÃO LÓGICA (16 ENTIDADES)
# ==============================================================================

class LixeiraService:
    """
    Serviço centralizado para gerenciar a Lixeira e Restauração Lógica das 16 entidades
    com Soft Delete do sistema EMC Soldas, com segregação de visões entre Admin e Operador.
    """

    # Mapeamento dinâmico das 16 entidades elegíveis para Soft Delete
    ENTIDADES_CONFIG = {
        'orcamentos': {
            'nome_singular': 'Orçamento',
            'app': 'orcamentos',
            'model_name': 'Orcamento',
            'campo_identificador': lambda obj: f"ORÇAMENTO #{obj.id} - {getattr(obj.cliente, 'nome_razao', 'CLIENTE N/A')}",
            'campo_detalhes': lambda obj: f"VALOR: R$ {obj.valor_bruto} | STATUS OP: {obj.status_operacional} | STATUS FIN: {obj.status_financeiro}"
        },
        'faturas': {
            'nome_singular': 'Fatura',
            'app': 'faturamento',
            'model_name': 'Fatura',
            'campo_identificador': lambda obj: f"FATURA #{obj.id} - {getattr(obj.cliente, 'nome_razao', 'CLIENTE N/A')}",
            'campo_detalhes': lambda obj: f"VALOR: R$ {obj.valor_total_faturado} | STATUS: {obj.status}"
        },
        'clientes': {
            'nome_singular': 'Cliente / Fornecedor',
            'app': 'cadastros',
            'model_name': 'ClienteFornecedor',
            'campo_identificador': lambda obj: f"{obj.nome_razao} ({obj.tipo})",
            'campo_detalhes': lambda obj: f"DOC: {obj.cnpj_cpf or 'SEM DOCUMENTO'} | TEL: {obj.telefone or 'SEM TELEFONE'}"
        },
        'equipamentos': {
            'nome_singular': 'Equipamento / Veículo',
            'app': 'cadastros',
            'model_name': 'Equipamento',
            'campo_identificador': lambda obj: f"PLACA: {obj.placa or 'S/ PLACA'} - {obj.identificacao}",
            'campo_detalhes': lambda obj: f"DESCRIÇÃO: {obj.descricao or 'N/A'}"
        },
        'itens': {
            'nome_singular': 'Item / Matéria-Prima',
            'app': 'catalogo',
            'model_name': 'Item',
            'campo_identificador': lambda obj: f"{obj.nome}",
            'campo_detalhes': lambda obj: f"TIPO USO: {obj.tipo_uso} | ÚLTIMO CUSTO: R$ {obj.ultimo_custo_compra}"
        },
        'produtos': {
            'nome_singular': 'Produto / Receita BOM',
            'app': 'catalogo',
            'model_name': 'Produto',
            'campo_identificador': lambda obj: f"{obj.nome}",
            'campo_detalhes': lambda obj: f"TEMPO ESTIMADO: {obj.tempo_estimado_execucao}h"
        },
        'lancamentos': {
            'nome_singular': 'Lançamento Financeiro',
            'app': 'financeiro',
            'model_name': 'LancamentoFinanceiro',
            'campo_identificador': lambda obj: f"#{obj.id} - {obj.descricao}",
            'campo_detalhes': lambda obj: f"TIPO: {obj.tipo_lancamento} | VALOR: R$ {obj.valor} | STATUS: {obj.status_pagamento}"
        },
        'contas_bancarias': {
            'nome_singular': 'Conta Bancária',
            'app': 'financeiro',
            'model_name': 'ContaBancaria',
            'campo_identificador': lambda obj: f"{obj.nome}",
            'campo_detalhes': lambda obj: f"SALDO ATUAL: R$ {obj.saldo} | CHEQUE ESPECIAL: R$ {obj.limite_credito}"
        },
        'cartoes': {
            'nome_singular': 'Cartão Corporativo',
            'app': 'financeiro',
            'model_name': 'CartaoCredito',
            'campo_identificador': lambda obj: f"{obj.nome}",
            'campo_detalhes': lambda obj: f"LIMITE: R$ {obj.limite} | DIA VENC: {obj.dia_vencimento}"
        },
        'documentos_compra': {
            'nome_singular': 'Nota Fiscal de Compra',
            'app': 'compras',
            'model_name': 'DocumentoFiscalCompra',
            'campo_identificador': lambda obj: f"NF #{obj.num_nota} - {getattr(obj.fornecedor, 'nome_razao', 'FORNECEDOR N/A')}",
            'campo_detalhes': lambda obj: f"DATA: {obj.data_compra} | TOTAL: R$ {obj.valor_total}"
        },
        'dicionario_uom': {
            'nome_singular': 'Unidade de Medida (UOM)',
            'app': 'catalogo',
            'model_name': 'DicionarioUom',
            'campo_identificador': lambda obj: f"{obj.sigla} - {obj.descricao}",
            'campo_detalhes': lambda obj: f"UOM OFICIAL"
        },
        'dicionario_atributos': {
            'nome_singular': 'Atributo Técnico',
            'app': 'catalogo',
            'model_name': 'DicionarioAtributo',
            'campo_identificador': lambda obj: f"{obj.nome_atributo}",
            'campo_detalhes': lambda obj: f"ATRIBUTO DINÂMICO"
        },
        'categorias_financeiras': {
            'nome_singular': 'Categoria Financeira',
            'app': 'financeiro',
            'model_name': 'CategoriaFinanceira',
            'campo_identificador': lambda obj: f"{obj.nome} ({obj.tipo})",
            'campo_detalhes': lambda obj: f"CATEGORIA DRE"
        },
        'meios_pagamento': {
            'nome_singular': 'Meio de Pagamento',
            'app': 'financeiro',
            'model_name': 'MeioPagamento',
            'campo_identificador': lambda obj: f"{obj.nome}",
            'campo_detalhes': lambda obj: f"TAXA MAQUININHA: {'SIM' if obj.permite_taxa_maquininha else 'NÃO'}"
        },
        'regras_pagamento': {
            'nome_singular': 'Regra de Pagamento',
            'app': 'financeiro',
            'model_name': 'RegraPagamento',
            'campo_identificador': lambda obj: f"{obj.nome} ({obj.tipo_cobranca})",
            'campo_detalhes': lambda obj: f"PARCELAS: {obj.numero_parcelas} | DESCONTO: {obj.desconto_concedido_padrao}%"
        },
        'usuarios': {
            'nome_singular': 'Colaborador / Usuário',
            'app': 'authentication',
            'model_name': 'Usuario',
            'campo_identificador': lambda obj: f"{obj.nome} ({obj.email})",
            'campo_detalhes': lambda obj: f"PAPEL: {obj.role} | STATUS: {'ATIVO' if obj.is_ativo else 'INATIVO'}"
        }
    }

    @classmethod
    def _obter_model_class(cls, entidade_key: str):
        """Importa dinamicamente a classe do Model a partir da chave configurada."""
        conf = cls.ENTIDADES_CONFIG.get(entidade_key)
        if not conf:
            return None
        from django.apps import apps
        return apps.get_model(conf['app'], conf['model_name'])

    @classmethod
    def listar_itens(cls, user, entidade: str = None, data_inicio=None,
                     data_fim=None, busca: str = None, autor_id: int = None) -> List[Dict[str, Any]]:
        """
        Lista registros inativados logicamente aplicando as regras de segregação:
        - Admin ou permissão `auditoria_logs_recovery`: Acesso à Lixeira Global (tudo).
        - Operador comum: Acesso estrito a Minha Lixeira (`deleted_by_id = user.id`).
        """
        is_admin = getattr(user, 'role', 'Operador') == 'Admin' or getattr(user, 'is_superuser', False)
        permissoes = getattr(user, 'permissoes', None)
        tem_recovery_access = is_admin or (permissoes and getattr(permissoes, 'auditoria_logs_recovery', False))

        entidades_para_consultar = [entidade] if (entidade and entidade in cls.ENTIDADES_CONFIG) else list(cls.ENTIDADES_CONFIG.keys())

        # Mapeamento para nomes de usuários autores
        from apps.authentication.models import Usuario
        usuarios_map = {u.id: u.nome for u in Usuario.objects.all()}

        resultado_geral = []

        for ent_key in entidades_para_consultar:
            model_cls = cls._obter_model_class(ent_key)
            if not model_cls:
                continue

            conf = cls.ENTIDADES_CONFIG[ent_key]

            # Consulta registros com deleted_at preenchido
            if hasattr(model_cls, 'all_objects'):
                qs = model_cls.all_objects.filter(deleted_at__isnull=False)
            else:
                qs = model_cls.objects.filter(deleted_at__isnull=False)

            # Segregação mandatória de visão
            if not tem_recovery_access:
                # Operador enxerga exclusivamente registros inativados por si mesmo
                qs = qs.filter(deleted_by_id=user.id)
            elif autor_id:
                qs = qs.filter(deleted_by_id=autor_id)

            if data_inicio:
                qs = qs.filter(deleted_at__date__gte=data_inicio)
            if data_fim:
                qs = qs.filter(deleted_at__date__lte=data_fim)

            for item in qs.order_by('-deleted_at')[:100]:
                try:
                    identificador = conf['campo_identificador'](item)
                    detalhes = conf['campo_detalhes'](item)
                except Exception:
                    identificador = f"#{item.id}"
                    detalhes = "REGISTRO INATIVADO"

                if busca and busca.strip():
                    termo = busca.strip().lower()
                    if termo not in identificador.lower() and termo not in detalhes.lower():
                        continue

                autor_nome = usuarios_map.get(item.deleted_by_id, f"Usuário #{item.deleted_by_id}") if item.deleted_by_id else "Sistema"
                pode_restaurar = tem_recovery_access or (item.deleted_by_id == user.id)

                resultado_geral.append({
                    "entidade": ent_key,
                    "entidade_nome": conf['nome_singular'],
                    "id": item.id,
                    "identificador": identificador,
                    "detalhes": detalhes,
                    "deleted_at": item.deleted_at,
                    "deleted_by_id": item.deleted_by_id,
                    "deleted_by_nome": autor_nome,
                    "pode_restaurar": pode_restaurar
                })

        # Ordena consolidado por data de exclusão decrescente
        resultado_geral.sort(key=lambda x: x['deleted_at'] or timezone.now(), reverse=True)
        return resultado_geral

    @classmethod
    def restaurar_item(cls, user, entidade: str, item_id: int) -> Dict[str, Any]:
        """
        Restaura o registro inativado logicamente (revertendo deleted_at = NULL).
        Aplica validação de permissão: Operador só pode restaurar se foi ele quem excluiu.
        """
        if entidade not in cls.ENTIDADES_CONFIG:
            raise ValueError(f"Entidade '{entidade}' não é reconhecida pela Lixeira.")

        model_cls = cls._obter_model_class(entidade)
        if not model_cls:
            raise ValueError(f"Modelo para '{entidade}' não foi localizado.")

        conf = cls.ENTIDADES_CONFIG[entidade]

        # Busca o item deletado
        if hasattr(model_cls, 'all_objects'):
            item = model_cls.all_objects.filter(id=item_id, deleted_at__isnull=False).first()
        else:
            item = model_cls.objects.filter(id=item_id, deleted_at__isnull=False).first()

        if not item:
            raise ValueError(f"{conf['nome_singular']} #{item_id} não encontrado na Lixeira ou já se encontra ativo.")

        is_admin = getattr(user, 'role', 'Admin') == 'Admin' or getattr(user, 'is_superuser', False)
        permissoes = getattr(user, 'permissoes', None)
        tem_recovery_access = is_admin or (permissoes and getattr(permissoes, 'auditoria_logs_recovery', False))

        if not tem_recovery_access and item.deleted_by_id != user.id:
            raise PermissionError("Você não tem permissão para restaurar registros excluídos por outros colaboradores.")

        # Executa a restauração lógica
        with transaction.atomic():
            if hasattr(item, 'restore'):
                item.restore()
            else:
                item.deleted_at = None
                item.deleted_by_id = None
                item.save(update_fields=['deleted_at', 'deleted_by_id'])

        identificador = conf['campo_identificador'](item)
        logger.info(f"[AUDIT] [RESTAURACAO_LIXEIRA] Usuário: {user.email} (ID: {user.id}) | Entidade: {conf['nome_singular']} #{item.id} - {identificador} | Data/Hora: {timezone.localtime().strftime('%d/%m/%Y %H:%M:%S')}")

        return {
            "sucesso": True,
            "mensagem": f"{conf['nome_singular']} '{identificador}' foi restaurado(a) com sucesso.",
            "entidade": entidade,
            "id": item.id
        }
