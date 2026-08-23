"""
Gerador de arquivos CSV para a Central de Relatórios do sistema EMC Soldas.
Gera saídas em formato UTF-8 com BOM (compatibilidade com Microsoft Excel e LibreOffice)
e formatações de data e valores monetários no padrão brasileiro.
"""
import csv
import io
import codecs
from decimal import Decimal


def formatar_moeda_csv(valor):
    """Formata valor decimal para moeda brasileira R$ 0,00 ou 0,00."""
    if valor is None:
        return "0,00"
    if not isinstance(valor, Decimal):
        try:
            valor = Decimal(str(valor))
        except Exception:
            return str(valor)
    return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_numero_csv(valor, casas=2):
    """Formata número decimal com N casas decimais usando vírgula."""
    if valor is None:
        return "0"
    if not isinstance(valor, Decimal):
        try:
            valor = Decimal(str(valor))
        except Exception:
            return str(valor)
    fmt = f"{{:,.{casas}f}}"
    return fmt.format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')


def gerar_csv_estruturado(titulo, cabecalhos, linhas, sumario=None, delimitador=';'):
    """
    Gera um buffer binário de CSV estruturado com cabeçalho institucional,
    tabela de dados e bloco de sumário executivo.
    """
    output = io.StringIO()
    writer = csv.writer(output, delimiter=delimitador, quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho Institucional
    writer.writerow([f"EMC SOLDAS - {titulo.upper()}"])
    writer.writerow([])

    # Cabeçalhos da Tabela
    writer.writerow(cabecalhos)

    # Linhas de Dados
    for linha in linhas:
        writer.writerow(linha)

    # Sumário / Totais
    if sumario:
        writer.writerow([])
        writer.writerow(["--- RESUMO EXECUTIVO ---"])
        for chave, valor in sumario.items():
            writer.writerow([chave, valor])

    # Codifica para bytes com UTF-8 BOM
    conteudo_str = output.getvalue()
    conteudo_bytes = codecs.BOM_UTF8 + conteudo_str.encode('utf-8')
    return conteudo_bytes


def gerar_csv_inadimplencia(dados):
    """Gera CSV do Relatório de Inadimplência."""
    cabecalhos = [
        "ID FATURA", "CLIENTE", "CPF/CNPJ", "TELEFONE", "VALOR ORIGINAL (R$)",
        "VALOR ABERTO (R$)", "DATA VENCIMENTO", "DIAS ATRASO", "STATUS FATURA"
    ]
    linhas = []
    for item in dados.get('itens', []):
        linhas.append([
            item.get('fatura_id', ''),
            item.get('cliente_nome', ''),
            item.get('cliente_documento', ''),
            item.get('cliente_telefone', ''),
            formatar_moeda_csv(item.get('valor_original')),
            formatar_moeda_csv(item.get('valor_pendente')),
            item.get('data_vencimento', ''),
            item.get('dias_atraso', 0),
            item.get('status_fatura', '')
        ])

    sumario = {
        "Total de Clientes Inadimplentes": dados.get('total_clientes_inadimplentes', 0),
        "Total de Títulos em Atraso": dados.get('total_titulos_atraso', 0),
        "Valor Total em Atraso (R$)": formatar_moeda_csv(dados.get('valor_total_inadimplente', Decimal('0.00'))),
        "Média de Dias de Atraso": f"{dados.get('media_dias_atraso', 0)} dias"
    }

    return gerar_csv_estruturado("Relatorio de Inadimplencia", cabecalhos, linhas, sumario)


def gerar_csv_dossie_cliente(dados):
    """Gera CSV do Dossiê Completo do Cliente."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    cliente = dados.get('cliente', {})
    writer.writerow([f"EMC SOLDAS - DOSSIE DO CLIENTE: {cliente.get('nome_razao', '').upper()}"])
    writer.writerow([])
    writer.writerow(["DOCUMENTO", cliente.get('cnpj_cpf', '')])
    writer.writerow(["TELEFONE", cliente.get('telefone', '')])
    writer.writerow(["EMAIL", cliente.get('email', '')])
    writer.writerow(["CIDADE/UF", f"{cliente.get('cidade', '')}/{cliente.get('uf', '')}"])
    writer.writerow([])

    # Resumo Geral
    writer.writerow(["--- RESUMO FINANCEIRO GERAL ---"])
    writer.writerow(["Total de Orcamentos", dados.get('total_orcamentos', 0)])
    writer.writerow(["Total Faturado (R$)", formatar_moeda_csv(dados.get('total_faturado', Decimal('0.00')))])
    writer.writerow(["Total Pago (R$)", formatar_moeda_csv(dados.get('total_pago', Decimal('0.00')))])
    writer.writerow(["Total em Aberto (R$)", formatar_moeda_csv(dados.get('total_aberto', Decimal('0.00')))])
    writer.writerow(["Pontualidade Pagamentos", f"{dados.get('indice_pontualidade', 0)}%"])
    writer.writerow([])

    # Segregação de Vendas: Produtos vs Serviços
    writer.writerow(["--- SEGREGAÇÃO DE VENDAS (PRODUTOS VS SERVIÇOS) ---"])
    writer.writerow(["Categoria", "Qtd Itens/Servicos", "Valor Total (R$)", "% Participacao"])
    seg = dados.get('segregacao_vendas', {})
    prod = seg.get('produtos', {})
    serv = seg.get('servicos', {})
    writer.writerow(["Venda de Produtos (Pecas/Materiais)", prod.get('quantidade', 0), formatar_moeda_csv(prod.get('valor_total')), f"{prod.get('percentual', 0)}%"])
    writer.writerow(["Prestacao de Servicos (Reformas/Soldas)", serv.get('quantidade', 0), formatar_moeda_csv(serv.get('valor_total')), f"{serv.get('percentual', 0)}%"])
    writer.writerow([])

    # Histórico de Orçamentos
    writer.writerow(["--- HISTORICO DE ORÇAMENTOS ---"])
    writer.writerow(["NUMERO", "DATA GERACAO", "STATUS OPERACIONAL", "STATUS FINANCEIRO", "VALOR BRUTO (R$)", "VALOR FINAL (R$)"])
    for orc in dados.get('orcamentos', []):
        writer.writerow([
            orc.get('numero', ''),
            orc.get('data_geracao', ''),
            orc.get('status_operacional', ''),
            orc.get('status_financeiro', ''),
            formatar_moeda_csv(orc.get('valor_bruto')),
            formatar_moeda_csv(orc.get('valor_final'))
        ])

    conteudo_bytes = codecs.BOM_UTF8 + output.getvalue().encode('utf-8')
    return conteudo_bytes


def gerar_csv_curva_abc_clientes(dados):
    """Gera CSV do Relatório de Curva ABC de Clientes."""
    cabecalhos = [
        "POSICAO", "CLIENTE", "CPF/CNPJ", "FATURAMENTO (R$)", "PARTICIPACAO (%)",
        "ACUMULADO (%)", "CLASSIFICACAO ABC", "QTD FATURAS", "TICKET MEDIO (R$)"
    ]
    linhas = []
    for item in dados.get('itens', []):
        linhas.append([
            item.get('posicao', 0),
            item.get('cliente_nome', ''),
            item.get('cliente_documento', ''),
            formatar_moeda_csv(item.get('faturamento_total')),
            f"{formatar_numero_csv(item.get('percentual_participacao'))}%",
            f"{formatar_numero_csv(item.get('percentual_acumulado'))}%",
            item.get('classe_abc', ''),
            item.get('quantidade_faturas', 0),
            formatar_moeda_csv(item.get('ticket_medio'))
        ])

    sumario = {
        "Faturamento Total Analisado (R$)": formatar_moeda_csv(dados.get('faturamento_total_periodo', Decimal('0.00'))),
        "Total de Clientes com Faturamento": dados.get('total_clientes_ativos', 0),
        "Clientes Classe A (80% da receita)": dados.get('qtd_classe_a', 0),
        "Clientes Classe B (15% da receita)": dados.get('qtd_classe_b', 0),
        "Clientes Classe C (5% da receita)": dados.get('qtd_classe_c', 0),
    }

    return gerar_csv_estruturado("Curva ABC de Clientes", cabecalhos, linhas, sumario)


def gerar_csv_curva_abc_itens(dados):
    """Gera CSV do Relatório de Curva ABC de Consumo de Itens."""
    cabecalhos = [
        "POSICAO", "ITEM / INSUMO", "UOM", "TIPO USO", "QUANTIDADE CONSUMIDA",
        "CUSTO TOTAL (R$)", "PARTICIPACAO (%)", "ACUMULADO (%)", "CLASSIFICACAO ABC"
    ]
    linhas = []
    for item in dados.get('itens', []):
        linhas.append([
            item.get('posicao', 0),
            item.get('item_nome', ''),
            item.get('uom_sigla', ''),
            item.get('tipo_uso', ''),
            formatar_numero_csv(item.get('quantidade_consumida'), 4),
            formatar_moeda_csv(item.get('custo_total')),
            f"{formatar_numero_csv(item.get('percentual_participacao'))}%",
            f"{formatar_numero_csv(item.get('percentual_acumulado'))}%",
            item.get('classe_abc', '')
        ])

    sumario = {
        "Custo Total de Consumo Analisado (R$)": formatar_moeda_csv(dados.get('custo_total_periodo', Decimal('0.00'))),
        "Total de Itens Utilizados": dados.get('total_itens_consumidos', 0),
        "Itens Classe A (80% do consumo)": dados.get('qtd_classe_a', 0),
        "Itens Classe B (15% do consumo)": dados.get('qtd_classe_b', 0),
        "Itens Classe C (5% do consumo)": dados.get('qtd_classe_c', 0),
    }

    return gerar_csv_estruturado("Curva ABC de Consumo de Itens", cabecalhos, linhas, sumario)


def gerar_csv_dre(dados):
    """Gera CSV do Demonstrativo de Resultado do Exercício (DRE Simplificado)."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(["EMC SOLDAS - DEMONSTRATIVO DE RESULTADO DO EXERCICIO (DRE SIMPLIFICADO)"])
    writer.writerow(["PERIODO", f"{dados.get('data_inicio', '')} ate {dados.get('data_fim', '')}"])
    writer.writerow(["REGIME", dados.get('regime', 'COMPETENCIA').upper()])
    writer.writerow([])

    writer.writerow(["ESTRUTURA DRE", "VALOR (R$)", "% SOBRE RECEITA BRUTA"])

    linhas_dre = dados.get('linhas', [])
    for linha in linhas_dre:
        descricao = linha.get('descricao', '')
        valor = formatar_moeda_csv(linha.get('valor'))
        percentual = f"{formatar_numero_csv(linha.get('percentual'))}%" if linha.get('percentual') is not None else ""
        writer.writerow([descricao, valor, percentual])

    conteudo_bytes = codecs.BOM_UTF8 + output.getvalue().encode('utf-8')
    return conteudo_bytes


def gerar_csv_divergencias_conciliacao(dados):
    """Gera CSV do Relatório de Divergências de Conciliação Bancária."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(["EMC SOLDAS - RELATORIO DE DIVERGENCIAS DE CONCILIACAO BANCARIA"])
    writer.writerow(["CONTA BANCARIA", dados.get('conta_nome', 'TODAS AS CONTAS')])
    writer.writerow(["PERIODO", f"{dados.get('data_inicio', '')} ate {dados.get('data_fim', '')}"])
    writer.writerow([])

    # Aba 1: Sobras do Extrato
    writer.writerow(["--- ABA 1: TRANSACOES NO EXTRATO BANCARIO SEM LANCAMENTO NO ERP ---"])
    writer.writerow(["DATA BANCO", "DESCRICAO / HISTORICO BANCARIO", "VALOR (R$)", "TIPO", "ARQUIVO ORIGEM"])
    for extrato in dados.get('sobras_extrato', []):
        writer.writerow([
            extrato.get('data', ''),
            extrato.get('historico', ''),
            formatar_moeda_csv(extrato.get('valor')),
            extrato.get('tipo', ''),
            extrato.get('arquivo_origem', '')
        ])
    writer.writerow([])

    # Aba 2: Sobras do ERP
    writer.writerow(["--- ABA 2: LANCAMENTOS DO ERP PAGOS SEM CONCILIACAO CONFIRMADA ---"])
    writer.writerow(["DATA PAGAMENTO", "DESCRICAO ERP", "CATEGORIA", "MEIO PGTO", "VALOR (R$)", "TIPO"])
    for erp in dados.get('sobras_erp', []):
        writer.writerow([
            erp.get('data_pagamento', ''),
            erp.get('descricao', ''),
            erp.get('categoria', ''),
            erp.get('meio_pagamento', ''),
            formatar_moeda_csv(erp.get('valor')),
            erp.get('tipo_lancamento', '')
        ])

    conteudo_bytes = codecs.BOM_UTF8 + output.getvalue().encode('utf-8')
    return conteudo_bytes
