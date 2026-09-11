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


def validar_digito_chave_nfe(chave_44: str) -> bool:
    """
    Valida o dígito verificador (DV) da Chave de Acesso da NF-e (44 dígitos)
    utilizando o algoritmo Módulo 11 com pesos de 2 a 9 (SEFAZ).
    """
    if not chave_44 or len(chave_44) != 44 or not chave_44.isdigit():
        return False

    base = chave_44[:43]
    dv_informado = int(chave_44[43])

    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    idx_peso = 0

    for digito in reversed(base):
        soma += int(digito) * pesos[idx_peso]
        idx_peso = (idx_peso + 1) % len(pesos)

    resto = soma % 11
    dv_calculado = 0 if resto in (0, 1) else 11 - resto

    return dv_calculado == dv_informado


def extrair_dados_xml_nfe(arquivo) -> dict:
    """
    Extrai deterministicamente os dados da NF-e a partir de arquivo XML.
    Retorna apenas os campos existentes no formulário de compras:
    - cnpj_emitente (14 dígitos limpos)
    - razao_social_emitente (apenas para caso de novo cadastro)
    - num_nota
    - data_compra (YYYY-MM-DD)
    - chave_acesso (44 dígitos)
    - valor_total (Decimal formatado)
    """
    arquivo.seek(0)
    conteudo = arquivo.read()
    arquivo.seek(0)

    try:
        root = ET.fromstring(conteudo)
    except Exception as e:
        raise ValidationError(f"Erro ao processar estrutura XML: {str(e)}")

    # Trata namespace se presente: ex {http://www.portalfiscal.inf.br/nfe}
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'

    # 1. Chave de Acesso
    chave_acesso = ''
    inf_nfe = root.find(f".//{ns}infNFe")
    if inf_nfe is not None and 'Id' in inf_nfe.attrib:
        chave_raw = inf_nfe.attrib['Id']
        # Remove prefixo 'NFe'
        chave_raw = re.sub(r'\D', '', chave_raw)
        if len(chave_raw) == 44:
            chave_acesso = chave_raw

    # 2. Dados do Emitente
    cnpj_emitente = ''
    razao_social = ''
    emit = root.find(f".//{ns}emit")
    if emit is not None:
        cnpj_el = emit.find(f"{ns}CNPJ")
        if cnpj_el is not None and cnpj_el.text:
            cnpj_emitente = re.sub(r'\D', '', cnpj_el.text.strip())
        nome_el = emit.find(f"{ns}xNome")
        if nome_el is not None and nome_el.text:
            razao_social = nome_el.text.strip().upper()

    # 3. Dados de Identificação da Nota
    num_nota = ''
    data_compra = ''
    ide = root.find(f".//{ns}ide")
    if ide is not None:
        nnf_el = ide.find(f"{ns}nNF")
        if nnf_el is not None and nnf_el.text:
            num_nota = str(int(re.sub(r'\D', '', nnf_el.text.strip())))
        
        # Data de emissão (dhEmi ou dEmi)
        dhemi_el = ide.find(f"{ns}dhEmi")
        demi_el = ide.find(f"{ns}dEmi")
        data_raw = ''
        if dhemi_el is not None and dhemi_el.text:
            data_raw = dhemi_el.text.strip()
        elif demi_el is not None and demi_el.text:
            data_raw = demi_el.text.strip()

        if data_raw:
            # Formato ISO: '2026-09-10T14:30:00-03:00' ou '2026-09-10'
            data_compra = data_raw[:10]

    # 4. Total da Nota
    valor_total = None
    total_icms = root.find(f".//{ns}total/{ns}ICMSTot")
    if total_icms is not None:
        vnf_el = total_icms.find(f"{ns}vNF")
        if vnf_el is not None and vnf_el.text:
            try:
                valor_total = str(Decimal(vnf_el.text.strip()))
            except Exception:
                pass

    return {
        "cnpj_emitente": cnpj_emitente,
        "razao_social_emitente": razao_social,
        "num_nota": num_nota,
        "data_compra": data_compra,
        "chave_acesso": chave_acesso,
        "valor_total": valor_total
    }


def classificar_documento_fiscal_pdf(texto: str) -> tuple:
    """
    Classifica se o PDF representa uma Nota Fiscal hábil (DANFE, NFS-e, NFCom)
    ou se é um Boleto Bancário / Ficha de Compensação / Documento Não Fiscal.
    Retorna: (is_fiscal: bool, tipo_detectado: str, mensagem: str)
    """
    texto_lower = texto.lower()

    termos_fiscais = [
        'danfe', 'nfs-e', 'danfse', 'nf-e', 'nfcom',
        'documento auxiliar da nota fiscal',
        'documento auxiliar da nfs-e',
        'documento auxiliar da nota fiscal de fatura',
        'nota fiscal eletronica', 'nota fiscal eletrônica',
        'nota fiscal de servico', 'nota fiscal de serviço',
        'nota fiscal de faturamento', 'nota fiscal consumidor',
        'chave de acesso da nfs-e', 'chave de acesso',
        'protocolo de autorizacao de uso', 'protocolo de autorização de uso',
        'dados do produto / servicos', 'dados do produto / serviços',
        'tributacao municipal', 'tributação municipal'
    ]

    termos_boleto = [
        'ficha de compensacao', 'ficha de compensação',
        'bloqueto', 'boleto bancario', 'boleto bancário', 'detalhamento do boleto',
        'autenticacao mecanica', 'autenticação mecânica',
        'nosso numero', 'nosso número',
        'agencia/codigo beneficiario', 'agência/código beneficiário',
        'sacador avalista', 'pagavel em qualquer banco', 'pagável em qualquer banco'
    ]

    tem_fiscal = any(t in texto_lower for t in termos_fiscais)
    tem_boleto = any(t in texto_lower for t in termos_boleto)

    # Se contém fortes termos de boleto e não tem indicadores formais de nota fiscal
    if tem_boleto and not tem_fiscal:
        return False, "BOLETO", (
            "O arquivo enviado é um Boleto Bancário ou Ficha de Compensação, e não uma Nota Fiscal. "
            "Boletos representam cobrança e não comprovam entrada fiscal nem alimentam estoque de insumos. "
            "Para registrar este pagamento, utilize o módulo Financeiro (Contas a Pagar) ou anexe a Nota Fiscal emitida pelo fornecedor."
        )

    # Se não tem nenhum termo fiscal inequívoco
    if not tem_fiscal:
        return False, "NAO_FISCAL", (
            "O arquivo enviado não foi reconhecido como um documento fiscal válido (DANFE, NFS-e ou NFCom). "
            "Por favor, anexe uma Nota Fiscal emitida pelo fornecedor."
        )

    return True, "FISCAL", ""


def extrair_dados_pdf_danfe(arquivo) -> dict:
    """
    Extrai deterministicamente os dados da NF-e / NFS-e / NFCom a partir do PDF.
    1. Classifica previamente se o arquivo é documento fiscal hábil ou boleto/não-fiscal;
    2. Extrai a Chave de Acesso suportando NF-e/NFCom (44 dígitos) e NFS-e Nacional (50 dígitos);
    3. Segrega estritamente dados do Prestador/Emitente vs Tomador/Cliente;
    4. Extrai Número da Nota, Data de Emissão e Valor Total.
    """
    import io
    from pypdf import PdfReader

    arquivo.seek(0)
    buffer = io.BytesIO(arquivo.read())
    arquivo.seek(0)

    try:
        reader = PdfReader(buffer)
        texto_completo = ""
        for pagina in reader.pages:
            texto_pagina = pagina.extract_text() or ""
            texto_completo += " " + texto_pagina
    except Exception as e:
        raise ValidationError(f"Não foi possível ler o texto do documento PDF: {str(e)}")

    # 1. Classificação prévia do documento
    is_fiscal, tipo_doc, msg_bloqueio = classificar_documento_fiscal_pdf(texto_completo)
    if not is_fiscal:
        return {
            "is_documento_fiscal": False,
            "tipo_documento": tipo_doc,
            "mensagem": msg_bloqueio,
            "cnpj_emitente": "",
            "razao_social_emitente": "",
            "num_nota": "",
            "data_compra": "",
            "chave_acesso": "",
            "valor_total": None
        }

    # 2. Busca Chave de Acesso
    chave_encontrada = ""
    tipo_chave = ""

    # 2.1 - Chave da NFS-e Nacional (50 dígitos contínuos)
    matches_50 = re.findall(r'\b\d{50}\b', texto_completo)
    if matches_50:
        chave_encontrada = matches_50[0]
        tipo_chave = "NFSE_50"

    # 2.2 - Chave em 11 blocos de 4 dígitos (44 dígitos: DANFE NF-e modelo 55, NFCom modelo 62, NFC-e 65)
    if not chave_encontrada:
        matches_blocos = re.findall(r'\b(?:\d{4}[\s.-]+){10}\d{4}\b', texto_completo)
        for mb in matches_blocos:
            limpo = re.sub(r'\D', '', mb)
            if len(limpo) == 44 and validar_digito_chave_nfe(limpo):
                chave_encontrada = limpo
                tipo_chave = "NFE_44"
                break

    # 2.3 - 44 dígitos contínuos com validação de DV
    if not chave_encontrada:
        digitos_somente = re.findall(r'\b\d{44}\b', texto_completo)
        for cand in digitos_somente:
            if validar_digito_chave_nfe(cand):
                chave_encontrada = cand
                tipo_chave = "NFE_44"
                break

    # 2.4 - Rótulo específico no texto (ex: "CHAVE DE ACESSO DA NFS-e" ou "CHAVE DE ACESSO")
    if not chave_encontrada:
        match_rotulo = re.search(
            r'CHAVE(?:\s+DE)?\s+ACESSO(?:\s+DA\s+NFS-?E)?[\s\S]{0,50}?([0-9\s.-]{44,70})',
            texto_completo,
            re.IGNORECASE
        )
        if match_rotulo:
            limpo_rot = re.sub(r'\D', '', match_rotulo.group(1))
            if len(limpo_rot) >= 50:
                chave_encontrada = limpo_rot[:50]
                tipo_chave = "NFSE_50"
            elif len(limpo_rot) >= 44 and validar_digito_chave_nfe(limpo_rot[:44]):
                chave_encontrada = limpo_rot[:44]
                tipo_chave = "NFE_44"

    # 3. Dados do Emitente e Identificação da Nota
    cnpj_emitente = ""
    razao_social_emitente = ""
    num_nota = ""
    ano_mes = ""

    # Se chave de 44 dígitos, decodifica posições canônicas da NF-e
    if chave_encontrada and tipo_chave == "NFE_44":
        ano_mes = chave_encontrada[2:6]
        cnpj_emitente = chave_encontrada[6:20]
        num_nota_str = chave_encontrada[25:34]
        try:
            num_nota = str(int(num_nota_str))
        except ValueError:
            num_nota = num_nota_str.lstrip('0')

    # Para NFS-e (DANFSe) ou fallback, busca focando no PRESTADOR / EMITENTE
    if not cnpj_emitente:
        # Padrão DANFSe Nacional: "PRESTADOR / FORNECEDOR" seguido de CNPJ
        match_prestador = re.search(
            r'(?:PRESTADOR\s*(?:/\s*FORNECEDOR)?|IDENTIFICA[ÇC][ÃA]O\s+DO\s+EMITENTE|EMITENTE\s+DA\s+NFS-?E|CNPJ\s*Emitente)[\s\S]{0,150}?(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
            texto_completo,
            re.IGNORECASE
        )
        if match_prestador:
            cnpj_emitente = re.sub(r'\D', '', match_prestador.group(1))

            # Tenta capturar a Razão Social do prestador logo após o rótulo
            match_nome = re.search(
                r'PRESTADOR[\s\S]{0,150}?Nome\s*(?:/\s*Nome\s*Empresarial)?\s*[\n\r]+\s*([^\n\r]+)',
                texto_completo,
                re.IGNORECASE
            )
            if match_nome:
                razao_social_emitente = match_nome.group(1).strip().upper()

    # Fallback segregado: busca CNPJs antes do bloco TOMADOR / DESTINATÁRIO (nunca pegar o cliente)
    if not cnpj_emitente:
        partes = re.split(r'(?:TOMADOR|DESTINAT[ÁA]RIO)', texto_completo, maxsplit=1, flags=re.IGNORECASE)
        texto_prestador = partes[0] if partes else texto_completo
        cnpjs_prestador = re.findall(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', texto_prestador)
        if cnpjs_prestador:
            cnpj_emitente = re.sub(r'\D', '', cnpjs_prestador[0])

    # 4. Número da Nota
    if not num_nota:
        # Procura padrões como "NÚMERO DA NFS-e", "NFCOM 1513144", "NFS-e Nº 10", "NF-e Nº 10"
        match_num = re.search(
            r'(?:N[ÚU]MERO\s+DA\s+NFS-?E|Nº?\s*NFCOM|NFS-?E\s*N[º°\.\s]*|NF-?E\s*N[º°\.\s]*|N[ÚU]MERO\s*(?:DA\s*NOTA)?\s*[:º°\.\s]*|NOTA\s+FISCAL[^\d\n\r]{0,30}N[º°\.\s]*)\s*(\d{1,9})\b',
            texto_completo,
            re.IGNORECASE
        )
        if match_num:
            try:
                num_nota = str(int(match_num.group(1)))
            except ValueError:
                num_nota = match_num.group(1).lstrip('0')

    # Fallback no nome do arquivo (ex.: "NFSe 10 Associação.pdf")
    if not num_nota:
        nome_arquivo = getattr(arquivo, 'name', '') or ''
        match_nome = re.search(
            r'(?:NFS-?e?|NF-?e?|Nota|DANFE)[\s_.-]*(\d{1,9})\b',
            nome_arquivo,
            re.IGNORECASE
        )
        if match_nome:
            try:
                num_nota = str(int(match_nome.group(1)))
            except ValueError:
                num_nota = match_nome.group(1).lstrip('0')

    # 5. Data de Emissão
    data_compra = ""
    # Busca por "DATA E HORA DA EMISSÃO DA NFS-e" ou "DATA DA EMISSÃO"
    match_data_rotulo = re.search(
        r'(?:DATA\s*(?:E\s+HORA)?\s*(?:DA)?\s*EMISS[ÃA]O)[\s\S]{0,50}?(\d{2})/(\d{2})/(\d{4})',
        texto_completo,
        re.IGNORECASE
    )
    if match_data_rotulo:
        d, m, y = match_data_rotulo.groups()
        data_compra = f"{y}-{m}-{d}"
    else:
        datas_encontradas = re.findall(r'\b(\d{2})/(\d{2})/(\d{4})\b', texto_completo)
        if datas_encontradas:
            for d, m, y in datas_encontradas:
                if ano_mes and y[2:] == ano_mes[:2] and m == ano_mes[2:]:
                    data_compra = f"{y}-{m}-{d}"
                    break
            if not data_compra:
                d, m, y = datas_encontradas[0]
                data_compra = f"{y}-{m}-{d}"

    # 6. Valor Total
    valor_total = None
    match_valor = re.search(
        r'(?:VALOR\s+TOTAL\s+DA\s+NFS-?E|VALOR\s+L[ÍI]QUIDO\s+DA\s+NFS-?E|VALOR\s+TOTAL\s+DA\s+NOTA|VALOR\s+TOTAL\s+DOS\s+PRODUTOS|TOTAL\s+A\s+PAGAR)[\s\S]{0,80}?(?:R\$\s*)?([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})',
        texto_completo,
        re.IGNORECASE
    )
    if match_valor:
        val_str = match_valor.group(1).replace('.', '').replace(',', '.')
        try:
            valor_total = str(Decimal(val_str))
        except Exception:
            pass

    return {
        "is_documento_fiscal": True,
        "tipo_documento": "FISCAL",
        "cnpj_emitente": cnpj_emitente,
        "razao_social_emitente": razao_social_emitente,
        "num_nota": num_nota,
        "data_compra": data_compra,
        "chave_acesso": chave_encontrada,
        "valor_total": valor_total
    }

