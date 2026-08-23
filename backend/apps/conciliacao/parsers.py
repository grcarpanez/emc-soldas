"""
Parsers seguros e resilientes para extratos bancários nos formatos OFX e CSV.
Converte arquivos bancários heterogêneos para uma estrutura padronizada em Python/Django.
"""
import re
import csv
import io
import hashlib
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Any, Optional

from core.utils import sanitizar_texto_maiusculo


class ExtratoParserException(Exception):
    """Exceção lançada quando ocorre falha crítica no parsing do extrato."""
    pass


def extrair_data_ofx(raw_date: str) -> Optional[date]:
    """
    Extrai objeto date de formatos de data típicos do padrão OFX.
    Exemplos: '20260810120000[-3:BRT]', '20260810', '20260810120000'.
    """
    if not raw_date:
        return None
    
    # Extrai os primeiros 8 dígitos (YYYYMMDD)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', raw_date)
    if match:
        ano, mes, dia = int(match.group(1)), int(match.group(2)), int(match.group(3))
        try:
            return date(ano, mes, dia)
        except ValueError:
            return None
    return None


def converter_valor_decimal(valor_str: Any) -> Decimal:
    """
    Converte com segurança strings numéricas em Decimal.
    Trata formatos brasileiros ('1.250,50', '-1.250,50', '1.250,50 D') e internacionais ('1250.50').
    """
    if isinstance(valor_str, (int, float, Decimal)):
        return Decimal(str(valor_str))
    
    if not valor_str:
        return Decimal('0.00')

    texto = str(valor_str).strip()
    
    # Identifica sinal negativo explícito ou notação contábil (ex: '(150.00)' ou '150,00 D')
    is_negativo = False
    if texto.startswith('-') or texto.endswith('-') or (texto.startswith('(') and texto.endswith(')')):
        is_negativo = True
    if re.search(r'\b[Dd]\b', texto):
        is_negativo = True

    # Remove parênteses, caracteres D/C e outros símbolos não numéricos, exceto pontos e vírgulas
    limpo = re.sub(r'[^\d,\.-]', '', texto)

    if not limpo:
        return Decimal('0.00')

    # Trata formatos com vírgula decimal (brasileiro) vs ponto decimal
    if ',' in limpo and '.' in limpo:
        if limpo.rfind(',') > limpo.rfind('.'):
            # Formato brasileiro: 1.500,50 -> 1500.50
            limpo = limpo.replace('.', '').replace(',', '.')
        else:
            # Formato americano: 1,500.50 -> 1500.50
            limpo = limpo.replace(',', '')
    elif ',' in limpo:
        # Apenas vírgula: 1500,50 -> 1500.50
        limpo = limpo.replace(',', '.')

    # Remove qualquer sinal remanescente antes da conversão final
    limpo = limpo.replace('-', '')

    try:
        resultado = Decimal(limpo)
        if is_negativo:
            resultado = -resultado
        return resultado
    except InvalidOperation:
        raise ExtratoParserException(f"Valor numérico inválido encontrado: '{valor_str}'")


def parse_ofx_content(content: str) -> Dict[str, Any]:
    """
    Realiza o parsing de conteúdo OFX (SGML 1.x ou XML 2.x).
    Extrai metadados bancários e lista de transações com sanitização.
    """
    meta: Dict[str, Any] = {
        'banco_codigo': '',
        'agencia': '',
        'conta': '',
        'data_inicio': None,
        'data_fim': None,
        'saldo_final': None,
    }
    transacoes: List[Dict[str, Any]] = []

    # Extração de Metadados via Regex flexível (suporta tags abertas SGML e fechadas XML)
    bank_id_match = re.search(r'<BANKID>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if bank_id_match:
        meta['banco_codigo'] = bank_id_match.group(1).strip()

    branch_id_match = re.search(r'<BRANCHID>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if branch_id_match:
        meta['agencia'] = branch_id_match.group(1).strip()

    acct_id_match = re.search(r'<ACCTID>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if acct_id_match:
        meta['conta'] = acct_id_match.group(1).strip()

    dt_start_match = re.search(r'<DTSTART>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if dt_start_match:
        meta['data_inicio'] = extrair_data_ofx(dt_start_match.group(1).strip())

    dt_end_match = re.search(r'<DTEND>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if dt_end_match:
        meta['data_fim'] = extrair_data_ofx(dt_end_match.group(1).strip())

    bal_amt_match = re.search(r'<BALAMT>\s*([^<\r\n]+)', content, re.IGNORECASE)
    if bal_amt_match:
        try:
            meta['saldo_final'] = converter_valor_decimal(bal_amt_match.group(1).strip())
        except Exception:
            meta['saldo_final'] = None

    # Extração de cada bloco <STMTTRN> ... </STMTTRN> (ou até o próximo <STMTTRN> ou </BANKTRANLIST>)
    stmttrn_blocks = re.findall(r'<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|(?=</BANKTRANLIST>))', content, re.IGNORECASE | re.DOTALL)

    for idx, block in enumerate(stmttrn_blocks):
        trntype_match = re.search(r'<TRNTYPE>\s*([^<\r\n]+)', block, re.IGNORECASE)
        dtposted_match = re.search(r'<DTPOSTED>\s*([^<\r\n]+)', block, re.IGNORECASE)
        trnamt_match = re.search(r'<TRNAMT>\s*([^<\r\n]+)', block, re.IGNORECASE)
        fitid_match = re.search(r'<FITID>\s*([^<\r\n]+)', block, re.IGNORECASE)
        checknum_match = re.search(r'<CHECKNUM>\s*([^<\r\n]+)', block, re.IGNORECASE)
        memo_match = re.search(r'<MEMO>\s*([^<\r\n]+)', block, re.IGNORECASE)
        name_match = re.search(r'<NAME>\s*([^<\r\n]+)', block, re.IGNORECASE)

        if not dtposted_match or not trnamt_match:
            continue

        dt_posted = extrair_data_ofx(dtposted_match.group(1).strip())
        if not dt_posted:
            continue

        valor = converter_valor_decimal(trnamt_match.group(1).strip())
        fitid = fitid_match.group(1).strip() if fitid_match else f"OFX-{dt_posted.isoformat()}-{idx}-{abs(valor)}"
        documento = checknum_match.group(1).strip() if checknum_match else ""

        # Descrição prioriza MEMO, depois NAME
        descricao_raw = ""
        if memo_match:
            descricao_raw = memo_match.group(1).strip()
        elif name_match:
            descricao_raw = name_match.group(1).strip()
        
        descricao = sanitizar_texto_maiusculo(descricao_raw) if descricao_raw else "TRANSACAO BANCARIA"

        # Define tipo ENTRADA / SAIDA baseado no sinal do valor
        tipo = 'ENTRADA' if valor > 0 else 'SAIDA'

        transacoes.append({
            'fitid': fitid,
            'data': dt_posted.isoformat(),
            'data_obj': dt_posted,
            'valor': float(valor),
            'valor_decimal': valor,
            'valor_absoluto': float(abs(valor)),
            'valor_absoluto_decimal': abs(valor),
            'tipo': tipo,
            'descricao': descricao,
            'documento': documento,
            'tipo_original_ofx': trntype_match.group(1).strip() if trntype_match else '',
        })

    # Atualiza data_inicio e data_fim a partir das transações se não vierem no cabeçalho
    if transacoes:
        datas = [t['data_obj'] for t in transacoes]
        if not meta['data_inicio']:
            meta['data_inicio'] = min(datas)
        if not meta['data_fim']:
            meta['data_fim'] = max(datas)

    if meta['data_inicio'] and isinstance(meta['data_inicio'], date):
        meta['data_inicio'] = meta['data_inicio'].isoformat()
    if meta['data_fim'] and isinstance(meta['data_fim'], date):
        meta['data_fim'] = meta['data_fim'].isoformat()
    if meta['saldo_final'] is not None:
        meta['saldo_final'] = float(meta['saldo_final'])

    return {
        'formato': 'OFX',
        'meta': meta,
        'transacoes': transacoes,
        'total_transacoes': len(transacoes),
    }


def parse_csv_content(content: str) -> Dict[str, Any]:
    """
    Realiza o parsing de extratos bancários em formato CSV com detecção inteligente de colunas.
    Suporta exportações comuns de bancos brasileiros (Data, Histórico, Documento, Valor, Saldo).
    """
    meta: Dict[str, Any] = {
        'banco_codigo': '',
        'agencia': '',
        'conta': '',
        'data_inicio': None,
        'data_fim': None,
        'saldo_final': None,
    }
    transacoes: List[Dict[str, Any]] = []

    # Identifica delimitador (; ou , ou \t)
    primeiras_linhas = "\n".join(content.splitlines()[:10])
    delimitador = ';'
    if primeiras_linhas.count(';') < primeiras_linhas.count(',') and primeiras_linhas.count(',') > 0:
        delimitador = ','
    elif primeiras_linhas.count('\t') > primeiras_linhas.count(';'):
        delimitador = '\t'

    f = io.StringIO(content)
    reader = csv.reader(f, delimiter=delimitador)

    linhas = list(reader)
    if not linhas:
        return {
            'formato': 'CSV',
            'meta': meta,
            'transacoes': [],
            'total_transacoes': 0,
        }

    # Busca a linha de cabeçalho
    idx_cabecalho = -1
    col_data = -1
    col_descricao = -1
    col_valor = -1
    col_debito = -1
    col_credito = -1
    col_doc = -1
    col_tipo = -1

    keywords_data = ['data', 'dt', 'data lancamento', 'data movimento', 'data_lancamento', 'date']
    keywords_desc = ['historico', 'descricao', 'detalhes', 'memo', 'lancamento', 'historico / descricao', 'description']
    keywords_valor = ['valor', 'valor (r$)', 'valor r$', 'amount', 'val']
    keywords_debito = ['debito', 'saida', 'debito (r$)', 'saidas']
    keywords_credito = ['credito', 'entrada', 'credito (r$)', 'entradas']
    keywords_doc = ['documento', 'docto', 'doc', 'num doc', 'n documento', 'numero documento']
    keywords_tipo = ['tipo', 'd/c', 'd_c', 'natureza']

    for idx, row in enumerate(linhas[:15]):
        row_lower = [str(c).strip().lower() for c in row]
        for col_idx, col_name in enumerate(row_lower):
            if any(k == col_name or k in col_name for k in keywords_data) and col_data == -1:
                col_data = col_idx
            if any(k == col_name or k in col_name for k in keywords_desc) and col_descricao == -1:
                col_descricao = col_idx
            if any(k == col_name or k in col_name for k in keywords_valor) and col_valor == -1:
                col_valor = col_idx
            if any(k == col_name or k in col_name for k in keywords_debito) and col_debito == -1:
                col_debito = col_idx
            if any(k == col_name or k in col_name for k in keywords_credito) and col_credito == -1:
                col_credito = col_idx
            if any(k == col_name or k in col_name for k in keywords_doc) and col_doc == -1:
                col_doc = col_idx
            if any(k == col_name or k in col_name for k in keywords_tipo) and col_tipo == -1:
                col_tipo = col_idx

        # Se encontrou ao menos data e (valor ou débito/crédito)
        if col_data != -1 and (col_valor != -1 or (col_debito != -1 and col_credito != -1)):
            idx_cabecalho = idx
            break

    # Fallback caso não tenha cabeçalho explícito: assume colunas 0=data, 1=descrição, 2=valor
    linhas_dados = linhas[idx_cabecalho + 1:] if idx_cabecalho != -1 else linhas
    if col_data == -1:
        col_data = 0
    if col_descricao == -1 and len(linhas_dados) > 0 and len(linhas_dados[0]) > 1:
        col_descricao = 1
    if col_valor == -1 and col_debito == -1 and len(linhas_dados) > 0 and len(linhas_dados[0]) > 2:
        col_valor = 2

    for idx, row in enumerate(linhas_dados):
        if not row or len(row) <= col_data:
            continue

        raw_date = row[col_data].strip()
        dt_obj: Optional[date] = None

        # Tenta formatos comuns de data
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%Y', '%d.%m.%Y'):
            try:
                dt_obj = datetime.strptime(raw_date, fmt).date()
                break
            except ValueError:
                continue

        if not dt_obj:
            continue

        descricao_raw = row[col_descricao].strip() if col_descricao != -1 and len(row) > col_descricao else ""
        documento = row[col_doc].strip() if col_doc != -1 and len(row) > col_doc else ""

        # Determinação do valor
        valor = Decimal('0.00')
        if col_debito != -1 and col_credito != -1 and len(row) > max(col_debito, col_credito):
            val_deb = row[col_debito].strip()
            val_cred = row[col_credito].strip()
            if val_deb:
                valor = -abs(converter_valor_decimal(val_deb))
            elif val_cred:
                valor = abs(converter_valor_decimal(val_cred))
        elif col_valor != -1 and len(row) > col_valor:
            val_str = row[col_valor].strip()
            if val_str:
                valor = converter_valor_decimal(val_str)
                # Verifica coluna de tipo D/C se houver
                if col_tipo != -1 and len(row) > col_tipo:
                    tipo_char = row[col_tipo].strip().upper()
                    if tipo_char == 'D' and valor > 0:
                        valor = -valor
                    elif tipo_char == 'C' and valor < 0:
                        valor = abs(valor)

        if valor == Decimal('0.00'):
            continue

        tipo = 'ENTRADA' if valor > 0 else 'SAIDA'
        descricao = sanitizar_texto_maiusculo(descricao_raw) if descricao_raw else "TRANSACAO BANCARIA CSV"
        
        # Gera FITID hash determinístico para o CSV
        hash_seed = f"CSV-{dt_obj.isoformat()}-{idx}-{valor}-{descricao_raw}"
        fitid = hashlib.md5(hash_seed.encode('utf-8')).hexdigest()[:16].upper()

        transacoes.append({
            'fitid': fitid,
            'data': dt_obj.isoformat(),
            'data_obj': dt_obj,
            'valor': float(valor),
            'valor_decimal': valor,
            'valor_absoluto': float(abs(valor)),
            'valor_absoluto_decimal': abs(valor),
            'tipo': tipo,
            'descricao': descricao,
            'documento': documento,
            'tipo_original_ofx': '',
        })

    if transacoes:
        datas = [t['data_obj'] for t in transacoes]
        meta['data_inicio'] = min(datas).isoformat()
        meta['data_fim'] = max(datas).isoformat()

    return {
        'formato': 'CSV',
        'meta': meta,
        'transacoes': transacoes,
        'total_transacoes': len(transacoes),
    }


def parse_extrato_arquivo(uploaded_file) -> Dict[str, Any]:
    """
    Ponto de entrada unificado para leitura e parsing de extratos bancários (OFX ou CSV).
    Lê o buffer de bytes com fallback inteligente de encoding (utf-8, latin-1/cp1252).
    """
    raw_bytes = uploaded_file.read()
    
    # Decodificação com fallback resiliente
    content = ""
    for enc in ('utf-8', 'latin-1', 'cp1252', 'iso-8859-1'):
        try:
            content = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if not content:
        raise ExtratoParserException("Não foi possível decodificar o arquivo de extrato. Encoding incompatível.")

    # Detecção automática entre OFX e CSV
    if '<OFX>' in content.upper() or 'OFXHEADER' in content.upper() or '<STMTTRN>' in content.upper():
        return parse_ofx_content(content)
    else:
        return parse_csv_content(content)
