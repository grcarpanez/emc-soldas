"""
Utilitários de segurança, validação matemática e criptografia simétrica (AES-256 Fernet).
"""
import base64
import re
import unicodedata
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def sanitizar_texto_maiusculo(texto: str) -> str:
    """
    Remove acentos, caracteres diacríticos e converte para MAIÚSCULAS (ASCII puro).
    Preserva caracteres especiais válidos (como vírgulas, pontos, hífens, barras, números e símbolos).
    Exemplo: 'Av. São João, 120 - Apto 3 (Oficina Nº 2)' -> 'AV. SAO JOAO, 120 - APTO 3 (OFICINA NO 2)'
    """
    if not texto or not isinstance(texto, str):
        return texto

    # Substitui caracteres específicos antes da decomposição se necessário (ex: º, ª)
    texto_ajustado = texto.replace('º', 'O').replace('ª', 'A').replace('°', 'O')
    
    # Decomposição NFD separa letras de seus diacríticos/acentos
    texto_nfd = unicodedata.normalize('NFKD', texto_ajustado)
    
    # Remove apenas os caracteres de combinação (acentos, til, cedilha combinada)
    texto_sem_acento = "".join(c for c in texto_nfd if not unicodedata.combining(c))
    
    return texto_sem_acento.upper().strip()


def limpar_apenas_digitos(valor: str) -> str:
    """Extrai estritamente os dígitos numéricos de uma string."""
    if not valor:
        return ""
    return re.sub(r'\D', '', str(valor))



class CryptoManager:
    """Gerenciador de criptografia simétrica AES-256 para dados sensíveis (senhas SMTP)."""

    @classmethod
    def _get_fernet(cls) -> Fernet:
        """Gera chave Fernet derivada da chave mestra do sistema."""
        raw_key = getattr(settings, 'ENCRYPTION_KEY', 'emc_default_key_32_bytes_len_1234')
        # Deriva chave de 32 bytes compatível com Fernet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'emc_soldas_salt_fixed_2026',
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(raw_key.encode()))
        return Fernet(derived_key)

    @classmethod
    def encrypt(cls, plain_text: str) -> str:
        """Criptografa texto plano retornando string base64 segura."""
        if not plain_text:
            return ""
        f = cls._get_fernet()
        return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')

    @classmethod
    def decrypt(cls, cipher_text: str) -> str:
        """Descriptografa texto cifrado."""
        if not cipher_text:
            return ""
        try:
            f = cls._get_fernet()
            return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
        except Exception:
            return ""


def validar_cpf(cpf: str) -> bool:
    """
    Validação algorítmica matemática dos 2 dígitos verificadores do CPF (módulo 11).
    Rejeita sequências repetidas e cálculos inválidos.
    """
    if not cpf:
        return False

    # Remove caracteres não numéricos
    numeros = re.sub(r'\D', '', str(cpf))

    if len(numeros) != 11:
        return False

    # Rejeita CPFs com todos os dígitos iguais (ex: 111.111.111-11)
    if numeros == numeros[0] * 11:
        return False

    # Validação do primeiro dígito verificador
    soma = sum(int(numeros[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito_1 = 0 if resto < 2 else 11 - resto

    if int(numeros[9]) != digito_1:
        return False

    # Validação do segundo dígito verificador
    soma = sum(int(numeros[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito_2 = 0 if resto < 2 else 11 - resto

    if int(numeros[10]) != digito_2:
        return False

    return True


def validar_cnpj(cnpj: str) -> bool:
    """
    Validação algorítmica matemática dos 2 dígitos verificadores do CNPJ (módulo 11).
    """
    if not cnpj:
        return False

    numeros = re.sub(r'\D', '', str(cnpj))

    if len(numeros) != 14:
        return False

    if numeros == numeros[0] * 14:
        return False

    # Primeiro dígito
    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(numeros[i]) * pesos_1[i] for i in range(12))
    resto = soma % 11
    digito_1 = 0 if resto < 2 else 11 - resto

    if int(numeros[12]) != digito_1:
        return False

    # Segundo dígito
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(numeros[i]) * pesos_2[i] for i in range(13))
    resto = soma % 11
    digito_2 = 0 if resto < 2 else 11 - resto

    if int(numeros[13]) != digito_2:
        return False

    return True


def formatar_moeda(valor: float) -> str:
    """Formata valor numérico como moeda brasileira (BRL)."""
    try:
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"
