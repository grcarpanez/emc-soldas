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
    Valida a extensão e os magic bytes / integridade do arquivo enviado (XML, PDF, PNG, JPG).
    Impede uploads de scripts disfarçados (NoExec e proteção contra arquivos maliciosos).
    """
    if not arquivo:
        raise ValidationError("Nenhum arquivo enviado.")

    nome_arquivo = getattr(arquivo, 'name', '')
    extensao = os.path.splitext(nome_arquivo)[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValidationError(
            f"Extensão '{extensao}' não permitida. Extensões aceitas: PDF, XML, PNG, JPG, JPEG."
        )

    # Limite de tamanho: 20MB
    if arquivo.size > 20 * 1024 * 1024:
        raise ValidationError("O tamanho do arquivo excede o limite máximo permitido de 20MB.")

    # Leitura dos primeiros bytes (Magic Number Check)
    arquivo.seek(0)
    cabecalho = arquivo.read(512)
    arquivo.seek(0)

    if extensao in MAGIC_NUMBERS:
        assinaturas = MAGIC_NUMBERS[extensao]
        valido = any(cabecalho.startswith(sig) for sig in assinaturas)
        if not valido:
            raise ValidationError(
                f"O conteúdo do arquivo não corresponde a um formato {extensao.upper().replace('.', '')} válido."
            )

    elif extensao == '.xml':
        # Validação de integridade do documento XML
        try:
            arquivo.seek(0)
            conteudo = arquivo.read(1024 * 1024 * 5) # lê até 5MB para parse
            arquivo.seek(0)
            ET.fromstring(conteudo)
        except Exception:
            raise ValidationError("O arquivo XML enviado é inválido ou está corrompido.")

    return extensao
