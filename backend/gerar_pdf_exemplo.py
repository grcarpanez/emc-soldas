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
    exemplos_dir = os.path.join(os.path.dirname(__file__), 'media', 'exemplos')
    os.makedirs(exemplos_dir, exist_ok=True)

    # Modelo 1: Orçamento com Logo Genérica (25 Itens / 2 Páginas)
    path_com_logo = os.path.join(exemplos_dir, 'orcamento_com_logo.pdf')
    pdf_com_logo = salvar_pdf_exemplo(path_com_logo, com_logo=True, total_itens=25)
    print(f"[OK] Modelo 1 (COM LOGO) gerado em: {pdf_com_logo}")

    # Modelo 2: Orçamento SEM Logo (25 Itens / 2 Páginas)
    path_sem_logo = os.path.join(exemplos_dir, 'orcamento_sem_logo.pdf')
    pdf_sem_logo = salvar_pdf_exemplo(path_sem_logo, com_logo=False, total_itens=25)
    print(f"[OK] Modelo 2 (SEM LOGO) gerado em: {pdf_sem_logo}")
