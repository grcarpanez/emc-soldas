"""
Parsers seguros e resilientes para extratos bancários nos formatos OFX e CSV.
Converte arquivos bancários heterogêneos para uma estrutura padronizada em Python/Django.
"""
import re
import csv
import io
import hashlib
import unicodedata
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


def normalizar_termo_cabecalho(texto: Any) -> str:
    """
    Normaliza termos de cabeçalho removendo acentuações, caracteres especiais e espaços extras.
    Exemplo: 'Descrição / Histórico (R$)' -> 'descricao historico r'
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto).strip().lower())
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    limpo = re.sub(r'[^a-z0-9\s]', ' ', sem_acento)
    return " ".join(limpo.split())


def tentar_parsear_data(valor_str: str) -> Optional[date]:
    """Tenta converter strings em date considerando múltiplos formatos brasileiros e internacionais."""
    if not valor_str:
        return None
    limpo = str(valor_str).strip().split('T')[0].split(' ')[0]
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%Y', '%d.%m.%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(limpo, fmt).date()
        except ValueError:
            continue
    return None


def parse_csv_content(content: str) -> Dict[str, Any]:
    """
    Realiza o parsing de extratos bancários em formato CSV com motor universal em 3 camadas:
    1. Dicionário amplo de sinônimos com normalização fonética e sem acentos de todos os bancos brasileiros.
    2. Detecção heurística de tipos de dados por amostragem das linhas (Inspection by Sampling).
    3. Filtro automático de ruídos e linhas administrativas (saldo anterior, totalizadores).
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
    elif primeiras_linhas.count('\t') > primeiras_linhas.count(';') and primeiras_linhas.count('\t') > primeiras_linhas.count(','):
        delimitador = '\t'

    f = io.StringIO(content)
    reader = csv.reader(f, delimiter=delimitador)

    linhas = [list(r) for r in reader if any(field.strip() for field in r)]
    if not linhas:
        return {
            'formato': 'CSV',
            'meta': meta,
            'transacoes': [],
            'total_transacoes': 0,
        }

    idx_cabecalho = -1
    col_data = -1
    col_descricao = -1
    col_valor = -1
    col_debito = -1
    col_credito = -1
    col_doc = -1
    col_tipo = -1

    # Dicionário Amplo de Sinônimos (Normalizados sem acento)
    keywords_data = ['data', 'dt', 'data lancamento', 'data movimento', 'data mov', 'date', 'data transacao', 'dia']
    keywords_desc = ['historico', 'descricao', 'detalhes', 'memo', 'lancamento', 'historico descricao', 'description', 'transacao', 'complemento', 'narrativa', 'identificacao', 'movimentacao']
    keywords_valor = ['valor', 'amount', 'val', 'valor r', 'valor rs', 'valor bruto', 'valor liquido']
    keywords_debito = ['debito', 'debitos', 'saida', 'saidas', 'valor debito', 'debito r', 'debito rs']
    keywords_credito = ['credito', 'creditos', 'entrada', 'entradas', 'valor credito', 'credito r', 'credito rs']
    keywords_doc = ['documento', 'docto', 'doc', 'num doc', 'n documento', 'numero documento', 'identificador', 'id', 'uuid', 'fitid', 'transacao id', 'codigo', 'n doc']
    keywords_tipo = ['tipo', 'natureza', 'd c', 'dc', 'operacao', 'debito credito']

    # 1. Varredura do Cabeçalho
    for idx, row in enumerate(linhas[:15]):
        norm_row = [normalizar_termo_cabecalho(c) for c in row]
        c_data = -1
        c_desc = -1
        c_val = -1
        c_deb = -1
        c_cred = -1
        c_doc = -1
        c_tipo = -1

        for col_idx, col_norm in enumerate(norm_row):
            if not col_norm:
                continue
            if c_data == -1 and any(k == col_norm or k in col_norm for k in keywords_data):
                c_data = col_idx
            elif c_desc == -1 and any(k == col_norm or k in col_norm for k in keywords_desc):
                c_desc = col_idx
            elif c_deb == -1 and any(k == col_norm or k in col_norm for k in keywords_debito):
                c_deb = col_idx
            elif c_cred == -1 and any(k == col_norm or k in col_norm for k in keywords_credito):
                c_cred = col_idx
            elif c_val == -1 and any(k == col_norm or k in col_norm for k in keywords_valor):
                c_val = col_idx
            elif c_doc == -1 and any(k == col_norm or k in col_norm for k in keywords_doc):
                c_doc = col_idx
            elif c_tipo == -1 and any(k == col_norm or k in col_norm for k in keywords_tipo):
                c_tipo = col_idx

        # Considera linha de cabeçalho válida se encontrou Data e (Valor ou Débito/Crédito)
        if c_data != -1 and (c_val != -1 or (c_deb != -1 and c_cred != -1) or c_desc != -1):
            idx_cabecalho = idx
            col_data = c_data
            col_descricao = c_desc
            col_valor = c_val
            col_debito = c_deb
            col_credito = c_cred
            col_doc = c_doc
            col_tipo = c_tipo
            break

    linhas_dados = linhas[idx_cabecalho + 1:] if idx_cabecalho != -1 else linhas

    # 2. Heurística por Amostragem de Dados (Inspection by Sampling) se faltou alguma coluna vital
    if col_data == -1 or (col_valor == -1 and col_debito == -1) or col_descricao == -1:
        amostra = linhas_dados[:10]
        if amostra:
            num_cols = max(len(r) for r in amostra)
            colunas_usadas = {col_data, col_valor, col_debito, col_credito, col_descricao, col_doc, col_tipo} - {-1}

            # Tenta descobrir Data se não achou
            if col_data == -1:
                for c_idx in range(num_cols):
                    if c_idx in colunas_usadas:
                        continue
                    datas_validas = sum(1 for r in amostra if len(r) > c_idx and tentar_parsear_data(r[c_idx]) is not None)
                    if datas_validas >= len(amostra) * 0.6:
                        col_data = c_idx
                        colunas_usadas.add(c_idx)
                        break

            # Tenta descobrir Valor se não achou
            if col_valor == -1 and col_debito == -1:
                for c_idx in range(num_cols):
                    if c_idx in colunas_usadas:
                        continue
                    valores_validos = 0
                    for r in amostra:
                        if len(r) > c_idx:
                            try:
                                v = converter_valor_decimal(r[c_idx])
                                if v != Decimal('0.00'):
                                    valores_validos += 1
                            except Exception:
                                pass
                    if valores_validos >= len(amostra) * 0.6:
                        col_valor = c_idx
                        colunas_usadas.add(c_idx)
                        break

            # Tenta descobrir Descrição entre as colunas remanescentes (coluna com maior texto)
            if col_descricao == -1:
                melhor_c = -1
                maior_len_medio = 0
                for c_idx in range(num_cols):
                    if c_idx in colunas_usadas:
                        continue
                    lens = [len(str(r[c_idx]).strip()) for r in amostra if len(r) > c_idx]
                    if lens:
                        media = sum(lens) / len(lens)
                        if media > maior_len_medio:
                            maior_len_medio = media
                            melhor_c = c_idx
                if melhor_c != -1:
                    col_descricao = melhor_c
                    colunas_usadas.add(melhor_c)

    # Termos de Ruído e Linhas Administrativas para Ignorar
    TERMOS_IGNORAR = [
        'saldo anterior', 'saldo do dia', 'saldo final', 'saldo atual',
        'saldo disponivel', 'saldo contabil', 'total de lancamentos',
        'total lancamentos', 'totalizador', 'saldo transportado',
        'total creditos', 'total debitos', 'saldo bloqueado', 'saldo em conta'
    ]

    for idx, row in enumerate(linhas_dados):
        if not row:
            continue
        if col_data != -1 and len(row) <= col_data:
            continue

        raw_date = row[col_data].strip() if col_data != -1 and len(row) > col_data else ""
        dt_obj = tentar_parsear_data(raw_date)
        if not dt_obj:
            continue

        descricao_raw = row[col_descricao].strip() if col_descricao != -1 and len(row) > col_descricao else ""
        documento = row[col_doc].strip() if col_doc != -1 and len(row) > col_doc else ""

        # Filtro de linhas administrativas (ex: Saldo Anterior)
        desc_lower = normalizar_termo_cabecalho(descricao_raw)
        if any(t in desc_lower for t in TERMOS_IGNORAR):
            continue

        # Determinação do valor financeiro
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
                if col_tipo != -1 and len(row) > col_tipo:
                    tipo_char = row[col_tipo].strip().upper()
                    if tipo_char in ('D', 'DEBITO') and valor > 0:
                        valor = -valor
                    elif tipo_char in ('C', 'CREDITO') and valor < 0:
                        valor = abs(valor)

        if valor == Decimal('0.00'):
            continue

        tipo = 'ENTRADA' if valor > 0 else 'SAIDA'
        descricao = sanitizar_texto_maiusculo(descricao_raw) if descricao_raw else "TRANSACAO BANCARIA CSV"

        # Captura ou gera FITID determinístico
        if documento and len(documento) >= 8 and not re.search(r'\s', documento):
            fitid = documento
        else:
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
