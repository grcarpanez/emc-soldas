"""
Utilitário de consulta pública e integração de dados de CEP (BrasilAPI e ViaCEP).
Em conformidade com docs/FSD.md - Busca e Autocomplete de CEP com Fallback Gracioso.
"""
import logging
import urllib.request
import urllib.error
import json
import ssl
from core.utils import sanitizar_texto_maiusculo, limpar_apenas_digitos

logger = logging.getLogger(__name__)


def consultar_cep_externo(cep: str) -> dict:
    """
    Consulta dados de logradouro, bairro, cidade e UF via API pública.
    Estratégia de alta disponibilidade:
    1. Tentativa primária: BrasilAPI (https://brasilapi.com.br/api/cep/v1/{cep})
    2. Fallback secundário: ViaCEP (https://viacep.com.br/ws/{cep}/json/)
    Retorna dicionário padronizado com campos sanitizados em maiúsculas sem acento.
    """
    cep_limpo = limpar_apenas_digitos(cep)

    if not cep_limpo or len(cep_limpo) != 8:
        return {
            "status": "error",
            "message": "CEP inválido. O CEP deve conter exatamente 8 dígitos numéricos.",
            "data": None
        }

    # Contexto SSL para requisições seguras
    ssl_context = ssl.create_default_context()

    # 1. Tentativa primária: BrasilAPI
    try:
        url_brasilapi = f"https://brasilapi.com.br/api/cep/v1/{cep_limpo}"
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
                
                logradouro = payload.get("street", "") or ""
                bairro = payload.get("neighborhood", "") or ""
                cidade = payload.get("city", "") or ""
                uf = payload.get("state", "") or ""

                return {
                    "status": "success",
                    "data": {
                        "cep": cep_limpo,
                        "logradouro": sanitizar_texto_maiusculo(logradouro),
                        "bairro": sanitizar_texto_maiusculo(bairro),
                        "cidade": sanitizar_texto_maiusculo(cidade),
                        "uf": (uf or "").strip().upper()[:2],
                        "origem": "BrasilAPI"
                    }
                }
    except Exception as ex_brasilapi:
        logger.warning(
            f"[Consulta CEP] Falha na tentativa primária via BrasilAPI para CEP {cep_limpo}: {str(ex_brasilapi)}. "
            f"Acionando fallback para ViaCEP..."
        )

    # 2. Fallback secundário: ViaCEP
    try:
        url_viacep = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        req = urllib.request.Request(
            url_viacep,
            headers={
                "User-Agent": "EMCSoldas-ERP/2.0 (sistema-interno-oficina)",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode('utf-8'))

                # Se a resposta do ViaCEP retornar { "erro": true }
                if payload.get("erro"):
                    return {
                        "status": "error",
                        "message": "CEP não encontrado nas bases oficiais.",
                        "data": None
                    }

                logradouro = payload.get("logradouro", "") or ""
                bairro = payload.get("bairro", "") or ""
                cidade = payload.get("localidade", "") or ""
                uf = payload.get("uf", "") or ""

                return {
                    "status": "success",
                    "data": {
                        "cep": cep_limpo,
                        "logradouro": sanitizar_texto_maiusculo(logradouro),
                        "bairro": sanitizar_texto_maiusculo(bairro),
                        "cidade": sanitizar_texto_maiusculo(cidade),
                        "uf": (uf or "").strip().upper()[:2],
                        "origem": "ViaCEP"
                    }
                }
    except Exception as ex_viacep:
        logger.error(
            f"[Consulta CEP] Falha no fallback secundário via ViaCEP para CEP {cep_limpo}: {str(ex_viacep)}."
        )

    return {
        "status": "error",
        "message": "Não foi possível consultar os dados do CEP nos serviços públicos (BrasilAPI / ViaCEP). Verifique a conexão ou insira os dados manualmente.",
        "data": None
    }
