#!/usr/bin/env python
"""
Utilitário para geração de chaves criptográficas seguras de 64 caracteres.
Utilizado para parametrização de SECRET_KEY e ENCRYPTION_KEY em ambiente Cloud PaaS.
"""
import secrets


def generate_secure_key(length: int = 64) -> str:
    """Gera chave criptograficamente segura com caracteres alfanuméricos e símbolos."""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for _ in range(length))


if __name__ == '__main__':
    print("=" * 70)
    print("EMC SOLDAS - GERADOR DE CHAVES CRIPTOGRÁFICAS SEGURAS")
    print("=" * 70)
    print(f"\nSECRET_KEY recomendada (64 caracteres):\n{generate_secure_key(64)}\n")
    print(f"ENCRYPTION_KEY recomendada (64 caracteres):\n{generate_secure_key(64)}\n")
    print("=" * 70)
    print("ATENÇÃO: Cadastre estas variáveis no painel da sua hospedagem Cloud PaaS")
    print("(Render, PythonAnywhere, AWS, etc.) e nunca as comite no Git.")
    print("=" * 70)
