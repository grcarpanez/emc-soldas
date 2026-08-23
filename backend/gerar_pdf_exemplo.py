"""
Script utilitário para geração de PDF de demonstração transacional de Orçamento.
Salva o arquivo em 'backend/media/exemplos/orcamento_exemplo.pdf' para visualização do usuário.
"""
import os
import sys
import django

# Configura o ambiente Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.orcamentos.pdf_service import salvar_pdf_exemplo

if __name__ == '__main__':
    caminho_destino = os.path.join(os.path.dirname(__file__), 'media', 'exemplos', 'orcamento_exemplo_25itens.pdf')
    arquivo_gerado = salvar_pdf_exemplo(caminho_destino)
    print(f"[OK] PDF com 25 itens gerado com sucesso em: {arquivo_gerado}")
