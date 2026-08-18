"""
Utilitário de consulta pública e integração de dados de CNPJ (BrasilAPI e ReceitaWS).
Em conformidade com docs/FSD.md - Motor de Busca e Autocomplete de CNPJ com Fallback Gracioso.
"""
import logging
import urllib.request
import urllib.error
import json
import ssl
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos, validar_cnpj

logger = logging.getLogger(__name__)


def consultar_cnpj_externo(cnpj: str) -> dict:
    """
    Consulta dados cadastrais de uma empresa via API pública (BrasilAPI com fallback para ReceitaWS).
    Retorna dicionário padronizado e devidamente sanitizado em maiúsculas sem acento.
    """
    cnpj_limpo = limpar_apenas_digitos(cnpj)

    if not cnpj_limpo or len(cnpj_limpo) != 14:
        return {
            "status": "error",
            "message": "CNPJ inválido. O documento deve conter exatamente 14 dígitos numéricos.",
            "data": None
        }

    if not validar_cnpj(cnpj_limpo):
        return {
            "status": "error",
            "message": "Dígitos verificadores do CNPJ são inválidos matematicamente.",
            "data": None
        }

    # Contexto SSL para requisições seguras
    ssl_context = ssl.create_default_context()

    # 1. Tentativa primária: BrasilAPI
    try:
        url_brasilapi = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        req = urllib.request.Request(
            url_brasilapi,
            headers={
                "User-Agent": "EMCSoldas-ERP/2.0 (sistema-interno-oficina)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode('utf-8'))
                
                # Monta logradouro completo se houver descrição de tipo
                tipo_logr = payload.get("descricao_tipo_de_logradouro", "")
                logr = payload.get("logradouro", "")
                logradouro_completo = f"{tipo_logr} {logr}".strip() if tipo_logr else logr

                # Monta telefone
                ddd = payload.get("ddd_telefone_1", "")
                telefone_limpo = limpar_apenas_digitos(ddd)

                dados_normalizados = {
                    "tipo_pessoa": "PJ",
                    "nome_razao": sanitizar_texto_maiusculo(payload.get("razao_social", "")),
                    "nome_fantasia": sanitizar_texto_maiusculo(payload.get("nome_fantasia", "") or payload.get("razao_social", "")),
                    "cnpj_cpf": cnpj_limpo,
                    "email": (payload.get("email") or "").lower().strip(),
                    "telefone": telefone_limpo,
                    "cep": limpar_apenas_digitos(payload.get("cep", "")),
                    "logradouro": sanitizar_texto_maiusculo(logradouro_completo),
                    "numero": sanitizar_texto_maiusculo(str(payload.get("numero", ""))),
                    "complemento": sanitizar_texto_maiusculo(payload.get("complemento", "")),
                    "bairro": sanitizar_texto_maiusculo(payload.get("bairro", "")),
                    "cidade": sanitizar_texto_maiusculo(payload.get("municipio", "")),
                    "uf": sanitizar_texto_maiusculo(payload.get("uf", "")),
                    "inscricao_estadual": "",
                    "isento_ie": False,
                }

                return {
                    "status": "success",
                    "provedor": "BrasilAPI",
                    "message": "Dados do CNPJ localizados com sucesso.",
                    "data": dados_normalizados
                }
    except Exception as exc:
        logger.warning(f"[CNPJ-PROXY] Falha na consulta BrasilAPI para {cnpj_limpo}: {str(exc)}. Tentando fallback ReceitaWS...")

    # 2. Tentativa secundária (Fallback): ReceitaWS
    try:
        url_receitaws = f"https://receitaws.com.br/v1/cnpj/{cnpj_limpo}"
        req = urllib.request.Request(
            url_receitaws,
            headers={
                "User-Agent": "EMCSoldas-ERP/2.0 (sistema-interno-oficina)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode('utf-8'))
                
                if payload.get("status") == "ERROR":
                    return {
                        "status": "error",
                        "message": payload.get("message", "CNPJ não localizado na base da Receita Federal."),
                        "data": None
                    }

                dados_normalizados = {
                    "tipo_pessoa": "PJ",
                    "nome_razao": sanitizar_texto_maiusculo(payload.get("nome", "")),
                    "nome_fantasia": sanitizar_texto_maiusculo(payload.get("fantasia", "") or payload.get("nome", "")),
                    "cnpj_cpf": cnpj_limpo,
                    "email": (payload.get("email") or "").lower().strip(),
                    "telefone": limpar_apenas_digitos(payload.get("telefone", "")),
                    "cep": limpar_apenas_digitos(payload.get("cep", "")),
                    "logradouro": sanitizar_texto_maiusculo(payload.get("logradouro", "")),
                    "numero": sanitizar_texto_maiusculo(str(payload.get("numero", ""))),
                    "complemento": sanitizar_texto_maiusculo(payload.get("complemento", "")),
                    "bairro": sanitizar_texto_maiusculo(payload.get("bairro", "")),
                    "cidade": sanitizar_texto_maiusculo(payload.get("municipio", "")),
                    "uf": sanitizar_texto_maiusculo(payload.get("uf", "")),
                    "inscricao_estadual": "",
                    "isento_ie": False,
                }

                return {
                    "status": "success",
                    "provedor": "ReceitaWS",
                    "message": "Dados do CNPJ localizados com sucesso (via ReceitaWS).",
                    "data": dados_normalizados
                }
    except Exception as exc:
        logger.warning(f"[CNPJ-PROXY] Falha no fallback ReceitaWS para {cnpj_limpo}: {str(exc)}")

    # 3. Fallback gracioso caso ambos os serviços públicos estejam indisponíveis
    return {
        "status": "warning",
        "message": "Consulta pública indisponível no momento. Preencha os dados cadastrais manualmente.",
        "data": {
            "tipo_pessoa": "PJ",
            "cnpj_cpf": cnpj_limpo,
            "nome_razao": "",
            "nome_fantasia": "",
            "email": "",
            "telefone": "",
            "cep": "",
            "logradouro": "",
            "numero": "",
            "complemento": "",
            "bairro": "",
            "cidade": "",
            "uf": "",
            "inscricao_estadual": "",
            "isento_ie": False,
        }
    }
