"""
Serviços de negócio do Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos).
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 7).
"""
import os
import re
import xml.etree.ElementTree as ET
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalogo.models import Item


def retroalimentar_custo_item(item, valor_unitario: Decimal, data_compra=None, usuario=None):
    """
    Atualiza o último custo de compra e a data da última compra do Item no catálogo,
    retroalimentando o motor de custos BOM de forma atômica e segura.
    """
    if not isinstance(item, Item):
        item = Item.objects.get(pk=item)

    item.ultimo_custo_compra = Decimal(str(valor_unitario))
    
    if data_compra:
        if isinstance(data_compra, str):
            # Se for string date YYYY-MM-DD
            from datetime import datetime
            try:
                dt = datetime.strptime(data_compra, '%Y-%m-%d')
                item.data_ultima_compra = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except ValueError:
                item.data_ultima_compra = timezone.now()
        else:
            from datetime import datetime, date
            if isinstance(data_compra, date) and not isinstance(data_compra, datetime):
                item.data_ultima_compra = timezone.make_aware(datetime.combine(data_compra, datetime.min.time()))
            else:
                item.data_ultima_compra = data_compra
    else:
        item.data_ultima_compra = timezone.now()

    if usuario and getattr(usuario, 'id', None):
        item.updated_by_id = usuario.id

    item.save(update_fields=['ultimo_custo_compra', 'data_ultima_compra', 'updated_at', 'updated_by_id'])
    return item


# Extensões e Magic Bytes seguros permitidos para notas fiscais de entrada
EXTENSOES_PERMITIDAS = {'.pdf', '.xml', '.png', '.jpg', '.jpeg'}

MAGIC_NUMBERS = {
    '.pdf': [b'%PDF'],
    '.png': [b'\x89PNG\r\n\x1a\n'],
    '.jpg': [b'\xff\xd8\xff'],
    '.jpeg': [b'\xff\xd8\xff'],
}


def validar_arquivo_anexo_compra(arquivo):
    """
    Valida a extensão, o cabeçalho (magic bytes) e a integridade de segurança do arquivo enviado.
    Aplica verificações rigorosas:
    1. Rejeição de nomes com Path Traversal (../) ou Null Bytes (\x00).
    2. Validação de extensão permitida (PDF, XML, PNG, JPG).
    3. Limite estrito de tamanho (20MB).
    4. Inspeção dos bytes de cabeçalho (Magic Bytes) para garantir que o tipo real confere com o anunciado.
    5. Proteção contra ataques XXE (XML External Entity) e expansão recursiva de entidades (Billion Laughs) para XMLs.
    """
    if not arquivo:
        raise ValidationError("Nenhum arquivo enviado.")

    nome_arquivo = getattr(arquivo, 'name', '')
    if not nome_arquivo:
        raise ValidationError("Nome de arquivo ausente.")

    # Proteção contra Path Traversal e Null Byte
    if '\x00' in nome_arquivo or '..' in nome_arquivo or '/' in nome_arquivo or '\\' in nome_arquivo:
        raise ValidationError("Nome de arquivo contém caracteres ou padrões de caminho não permitidos.")

    extensao = os.path.splitext(nome_arquivo)[1].lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValidationError(
            f"Extensão '{extensao}' não permitida. Extensões aceitas: PDF, XML, PNG, JPG, JPEG."
        )

    # Limite de tamanho: 20MB
    if arquivo.size > 20 * 1024 * 1024:
        raise ValidationError("O tamanho do arquivo excede o limite máximo permitido de 20MB.")

    if arquivo.size == 0:
        raise ValidationError("O arquivo enviado está vazio (0 bytes).")

    # Leitura e inspeção do cabeçalho binário (Magic Bytes Check)
    arquivo.seek(0)
    cabecalho = arquivo.read(512)
    arquivo.seek(0)

    if extensao in MAGIC_NUMBERS:
        assinaturas = MAGIC_NUMBERS[extensao]
        valido = any(cabecalho.startswith(sig) for sig in assinaturas)
        if not valido:
            raise ValidationError(
                f"Cabeçalho inválido: o conteúdo real do arquivo não corresponde a um arquivo {extensao.upper().replace('.', '')} legítimo."
            )

    elif extensao == '.xml':
        # Validação do cabeçalho de XML
        cabecalho_texto = cabecalho.decode('utf-8', errors='ignore').strip()
        # Arquivos XML começam com <?xml ou com uma tag <raiz
        if not (cabecalho_texto.startswith('<?xml') or cabecalho_texto.startswith('<')):
            raise ValidationError("Cabeçalho inválido: o arquivo XML não inicia com declaração ou tag XML válida.")

        # Proteção contra XXE e DTD Malicioso
        arquivo.seek(0)
        conteudo = arquivo.read(1024 * 1024 * 5)  # lê até 5MB para análise de segurança
        arquivo.seek(0)

        conteudo_str = conteudo.decode('utf-8', errors='ignore')
        # Bloqueia compulsoriamente <!DOCTYPE e <!ENTITY para blindar contra XXE e Billion Laughs
        if '<!DOCTYPE' in conteudo_str.upper() or '<!ENTITY' in conteudo_str.upper() or 'SYSTEM' in conteudo_str.upper():
            raise ValidationError("Arquivo XML rejeitado por conter declarações DTD ou entidades externas não seguras (proteção contra XXE).")

        try:
            ET.fromstring(conteudo)
        except Exception:
            raise ValidationError("O arquivo XML enviado é inválido ou está corrompido.")

    return extensao
