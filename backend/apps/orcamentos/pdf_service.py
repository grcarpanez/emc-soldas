"""
Serviço de geração de PDF profissional para Orçamentos Comerciais.
Utiliza ReportLab com layout e paleta alinhados ao Design System Industrial Integrity (docs/DESIGN.md).
Contempla supressão de descontos nulos/zerados e formatação industrial técnica.
"""
import io
import os
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from apps.administracao.models import ConfiguracaoGlobal


# Paleta Industrial Integrity (docs/DESIGN.md)
COLOR_DARK_IRON = colors.HexColor('#2B2B2B')
COLOR_STEEL_GRAY = colors.HexColor('#71797E')
COLOR_BRUSHED_METAL = colors.HexColor('#A5A9B4')
COLOR_RUST_ORANGE = colors.HexColor('#B7410E')
COLOR_LIGHT_SURFACE = colors.HexColor('#F8F9FA')
COLOR_ALT_ROW = colors.HexColor('#F1F3F5')
COLOR_BORDER = colors.HexColor('#D1D5DB')
COLOR_TEXT_MAIN = colors.HexColor('#131313')
COLOR_TEXT_MUTED = colors.HexColor('#555555')


def formatar_moeda(valor):
    """Formata decimal para padrão monetário brasileiro R$ 0,00."""
    if valor is None:
        valor = Decimal('0.00')
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_quantidade(valor):
    """Formata quantidade removendo zeros desnecessários após a vírgula."""
    if valor is None:
        return "0"
    if not isinstance(valor, Decimal):
        valor = Decimal(str(valor))
    # Se for inteiro, exibe sem decimais
    if valor == valor.to_integral():
        return f"{int(valor)}"
    return f"{valor:.4f}".rstrip('0').rstrip('.').replace('.', ',')


def gerar_pdf_orcamento(orcamento, buffer=None):
    """
    Gera o PDF transacional do orçamento comercial.
    Retorna o buffer BytesIO contendo os bytes do PDF.
    """
    if buffer is None:
        buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm
    )

    styles = getSampleStyleSheet()

    # Estilos customizados Industrial Integrity
    style_empresa_titulo = ParagraphStyle(
        'EmpresaTitulo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=COLOR_RUST_ORANGE
    )

    style_empresa_dados = ParagraphStyle(
        'EmpresaDados',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_MUTED
    )

    style_orc_numero = ParagraphStyle(
        'OrcNumero',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        alignment=TA_RIGHT,
        textColor=COLOR_DARK_IRON
    )

    style_orc_meta = ParagraphStyle(
        'OrcMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=COLOR_TEXT_MUTED
    )

    style_secao_titulo = ParagraphStyle(
        'SecaoTitulo',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.white
    )

    style_cell_header = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    style_cell_header_right = ParagraphStyle(
        'CellHeaderRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=TA_RIGHT
    )

    style_cell_text = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_MAIN
    )

    style_cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_MAIN
    )

    style_cell_right = ParagraphStyle(
        'CellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_RIGHT,
        textColor=COLOR_TEXT_MAIN
    )

    style_cell_right_bold = ParagraphStyle(
        'CellRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=TA_RIGHT,
        textColor=COLOR_TEXT_MAIN
    )

    style_total_label = ParagraphStyle(
        'TotalLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
        textColor=COLOR_DARK_IRON
    )

    style_total_val = ParagraphStyle(
        'TotalVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        alignment=TA_RIGHT,
        textColor=COLOR_DARK_IRON
    )

    style_total_destaque = ParagraphStyle(
        'TotalDestaque',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_RIGHT,
        textColor=COLOR_RUST_ORANGE
    )

    style_termo = ParagraphStyle(
        'TermoTexto',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=TA_JUSTIFY,
        textColor=COLOR_TEXT_MUTED
    )

    elements = []
    try:
        config = ConfiguracaoGlobal.get_solo()
    except Exception:
        config = ConfiguracaoGlobal(
            razao_social='EMC SOLDAS LTDA',
            cnpj='00.000.000/0001-00',
            telefone_contato='(11) 99999-9999',
            endereco_oficina='RUA INDUSTRIAL, 100 - OFICINA'
        )

    # 1. CABEÇALHO INSTITUCIONAL & IDENTIFICAÇÃO DO ORÇAMENTO
    col_width_left = 110 * mm
    col_width_right = 72 * mm

    empresa_texto = f"""
    <b>{config.razao_social.upper()}</b><br/>
    CNPJ: {config.cnpj} | Fone: {config.telefone_contato}<br/>
    {config.endereco_oficina}
    """

    dt_geracao_str = orcamento.data_geracao.strftime('%d/%m/%Y') if orcamento.data_geracao else timezone.now().strftime('%d/%m/%Y')
    dt_validade_str = orcamento.data_validade.strftime('%d/%m/%Y') if orcamento.data_validade else "NÃO INFORMADA"

    orc_meta_texto = f"""
    <b>PROPOSTA COMERCIAL #{orcamento.id:04d}</b><br/>
    Emissão: <b>{dt_geracao_str}</b><br/>
    Validade da Proposta: <b>{dt_validade_str}</b><br/>
    Status: <b>{orcamento.get_status_operacional_display()}</b>
    """

    header_data = [
        [Paragraph(empresa_texto, style_empresa_dados), Paragraph(orc_meta_texto, style_orc_meta)]
    ]
    header_table = Table(header_data, colWidths=[col_width_left, col_width_right])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_RUST_ORANGE, spaceBefore=2, spaceAfter=8))

    # 2. DADOS DO CLIENTE E EQUIPAMENTO
    cliente = orcamento.cliente
    equipamento = orcamento.equipamento

    doc_cliente = cliente.cnpj_cpf or "NÃO INFORMADO"
    tipo_doc = "CNPJ" if len(doc_cliente.replace('.', '').replace('-', '').replace('/', '')) > 11 else "CPF"
    fone_cliente = cliente.telefone or "NÃO INFORMADO"
    end_cliente = f"{cliente.logradouro or ''}, {cliente.numero or ''} - {cliente.bairro or ''} - {cliente.cidade or ''}/{cliente.uf or ''}".strip(" ,-/")
    if not end_cliente:
        end_cliente = "NÃO INFORMADO"

    cliente_info_html = f"""
    <b>Cliente:</b> {cliente.nome_razao.upper()}<br/>
    <b>{tipo_doc}:</b> {doc_cliente} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Telefone:</b> {fone_cliente}<br/>
    <b>Endereço:</b> {end_cliente}
    """

    equip_info_html = ""
    if equipamento:
        placa_str = f"<b>Placa:</b> {equipamento.placa} &nbsp;|&nbsp; " if equipamento.placa else ""
        ident_str = f"<b>Identificação:</b> {equipamento.identificacao} &nbsp;|&nbsp; " if equipamento.identificacao else ""
        equip_info_html = f"""
        <b>Equipamento / Veículo:</b><br/>
        {placa_str}{ident_str}<b>Descrição:</b> {equipamento.descricao.upper()}
        """
    else:
        equip_info_html = "<b>Equipamento / Veículo:</b><br/>NÃO VINCULADO"

    info_box_data = [
        [
            Paragraph("<b>DADOS DO CLIENTE</b>", style_cell_bold),
            Paragraph("<b>DADOS DO EQUIPAMENTO / SERVIÇO</b>", style_cell_bold)
        ],
        [
            Paragraph(cliente_info_html, style_cell_text),
            Paragraph(equip_info_html, style_cell_text)
        ]
    ]
    info_table = Table(info_box_data, colWidths=[col_width_left, col_width_right])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_SURFACE),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 1, COLOR_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8))

    # 3. TABELA DE ITENS E SERVIÇOS
    itens_header = [
        Paragraph("#", style_cell_header),
        Paragraph("DESCRIÇÃO DO ITEM / SERVIÇO", style_cell_header),
        Paragraph("QTD", style_cell_header_right),
        Paragraph("UN", style_cell_header),
        Paragraph("PREÇO UNIT.", style_cell_header_right),
        Paragraph("SUBTOTAL", style_cell_header_right),
    ]

    itens_rows = [itens_header]
    col_w_idx = 8 * mm
    col_w_desc = 94 * mm
    col_w_qtd = 16 * mm
    col_w_un = 14 * mm
    col_w_unit = 25 * mm
    col_w_sub = 25 * mm

    itens_orcamento = orcamento.itens_orcamento.select_related(
        'produto', 'item', 'produto__unidade_venda', 'item__unidade_compra'
    ).all()

    for idx, item_orc in enumerate(itens_orcamento, start=1):
        # Determina nome e unidade
        if item_orc.produto:
            nome_item = f"[PRODUTO] {item_orc.produto.nome}"
            unidade = item_orc.produto.unidade_venda.sigla if item_orc.produto.unidade_venda else "UN"
        elif item_orc.item:
            nome_item = f"[INSUMO] {item_orc.item.nome}"
            unidade = item_orc.item.unidade_compra.sigla if item_orc.item.unidade_compra else "UN"
        else:
            nome_item = item_orc.descricao_livre or "ITEM AVULSO"
            unidade = "UN"

        qtd_str = formatar_quantidade(item_orc.quantidade)
        unit_str = formatar_moeda(item_orc.valor_venda_snapshot)
        subtotal_val = (item_orc.quantidade or Decimal('1.00')) * (item_orc.valor_venda_snapshot or Decimal('0.00'))
        subtotal_str = formatar_moeda(subtotal_val)

        itens_rows.append([
            Paragraph(f"{idx:02d}", style_cell_text),
            Paragraph(nome_item.upper(), style_cell_text),
            Paragraph(qtd_str, style_cell_right),
            Paragraph(unidade.upper(), style_cell_text),
            Paragraph(unit_str, style_cell_right),
            Paragraph(subtotal_str, style_cell_right_bold),
        ])

    itens_table = Table(
        itens_rows,
        colWidths=[col_w_idx, col_w_desc, col_w_qtd, col_w_un, col_w_unit, col_w_sub]
    )

    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]

    # Linhas zebradas
    for r in range(1, len(itens_rows)):
        if r % 2 == 0:
            t_style.append(('BACKGROUND', (0, r), (-1, r), COLOR_ALT_ROW))

    itens_table.setStyle(TableStyle(t_style))
    elements.append(itens_table)
    elements.append(Spacer(1, 6))

    # 4. QUADRO DE TOTAIS (COM SUPRESSÃO DE DESCONTO SE ZERADO)
    tem_desconto = orcamento.valor_desconto_aplicado and orcamento.valor_desconto_aplicado > Decimal('0.00')

    totais_rows = []
    if tem_desconto:
        totais_rows.append([
            Paragraph("VALOR BRUTO TOTAL:", style_total_label),
            Paragraph(formatar_moeda(orcamento.valor_bruto), style_total_val)
        ])
        totais_rows.append([
            Paragraph("DESCONTO CONCEDIDO (-):", style_total_label),
            Paragraph(f"- {formatar_moeda(orcamento.valor_desconto_aplicado)}", style_total_val)
        ])
        totais_rows.append([
            Paragraph("VALOR LÍQUIDO TOTAL:", style_total_label),
            Paragraph(formatar_moeda(orcamento.valor_liquido), style_total_destaque)
        ])
    else:
        # Quando o desconto for zero ou nulo, suprime a linha de desconto completamente
        totais_rows.append([
            Paragraph("VALOR TOTAL DA PROPOSTA:", style_total_label),
            Paragraph(formatar_moeda(orcamento.valor_liquido), style_total_destaque)
        ])

    totais_table = Table(totais_rows, colWidths=[132 * mm, 50 * mm])
    totais_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_SURFACE),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
    ]))

    elements.append(totais_table)
    elements.append(Spacer(1, 8))

    # 5. OPÇÕES DE PAGAMENTO / PROPOSTAS COMERCIAIS
    propostas = orcamento.propostas_pagamento.select_related('regra_pagamento', 'regra_pagamento__meio_pagamento').all()
    tem_propostas = propostas.exists() if hasattr(propostas, 'exists') else bool(propostas)
    if tem_propostas:
        pgto_header = [
            Paragraph("CONDIÇÃO COMERCIAL / FORMA DE PAGAMENTO", style_cell_header),
            Paragraph("PARCELAMENTO / PRAZOS", style_cell_header),
            Paragraph("VALOR FINAL ESTIMADO", style_cell_header_right)
        ]
        pgto_rows = [pgto_header]

        valor_base = orcamento.valor_liquido
        for prop in propostas:
            regra = prop.regra_pagamento
            desc_aplicado = prop.desconto_personalizado if prop.desconto_personalizado is not None else (regra.desconto_concedido_padrao or Decimal('0.00'))

            if desc_aplicado > Decimal('0.00'):
                valor_com_desc = valor_base * (Decimal('1.00') - (desc_aplicado / Decimal('100.00')))
                desc_str = f" ({desc_aplicado:.1f}% desc.)"
            else:
                valor_com_desc = valor_base
                desc_str = ""

            num_parc = max(regra.numero_parcelas or 1, 1)
            valor_parcela = valor_com_desc / Decimal(num_parc)

            if num_parc == 1:
                if regra.prazo_primeira_parcela_dias > 0:
                    prazo_info = f"À Vista para {regra.prazo_primeira_parcela_dias} dias"
                else:
                    prazo_info = "À Vista no ato"
            else:
                prazo_info = f"{num_parc}x de {formatar_moeda(valor_parcela)} (intervalo {regra.intervalo_parcelas_dias}d)"

            nome_regra = f"{regra.nome.upper()} [{regra.meio_pagamento.nome.upper()}]{desc_str}"

            pgto_rows.append([
                Paragraph(nome_regra, style_cell_text),
                Paragraph(prazo_info, style_cell_text),
                Paragraph(formatar_moeda(valor_com_desc), style_cell_right_bold)
            ])

        pgto_table = Table(pgto_rows, colWidths=[90 * mm, 52 * mm, 40 * mm])
        pgto_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ]))

        bloco_pgto = [
            Paragraph("<b>CONDIÇÕES DE PAGAMENTO SUGERIDAS</b>", style_cell_bold),
            Spacer(1, 3),
            pgto_table
        ]
        elements.append(KeepTogether(bloco_pgto))
        elements.append(Spacer(1, 8))

    # 6. TERMO DE VALIDADE E ASSINATURAS
    termo_texto = (
        f"Esta proposta comercial possui validade impreterível até o dia <b>{dt_validade_str}</b>. "
        "Após este período, os valores e custos unitários de matéria-prima e mão de obra poderão sofrer "
        "reajustes conforme tabela vigente de mercado. A aprovação deste orçamento autoriza o início da execução "
        "dos serviços e reserva de insumos conforme as especificações acima descritas."
    )

    assinatura_data = [
        [
            Paragraph(f"<b>{config.razao_social.upper()}</b><br/>EMC Soldas - Departamento Comercial", style_cell_text),
            Paragraph("<b>DE ACORDO DO CLIENTE</b><br/>Assinatura / Carimbo", style_cell_text)
        ],
        [
            Spacer(1, 14 * mm),
            Spacer(1, 14 * mm)
        ],
        [
            Paragraph("__________________________________________", style_cell_text),
            Paragraph("__________________________________________", style_cell_text)
        ]
    ]

    assinatura_table = Table(assinatura_data, colWidths=[91 * mm, 91 * mm])
    assinatura_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 0),
    ]))

    bloco_final = [
        Paragraph(termo_texto, style_termo),
        Spacer(1, 6),
        assinatura_table
    ]
    elements.append(KeepTogether(bloco_final))

    # Constrói o documento
    doc.build(elements)
    buffer.seek(0)
    return buffer


def salvar_pdf_exemplo(caminho_arquivo):
    """
    Gera um PDF de demonstração com dados fictícios completos e salva no caminho especificado.
    Útil para validação visual e aprovação do usuário.
    """
    from apps.cadastros.models import ClienteFornecedor, Equipamento
    from apps.catalogo.models import Item, Produto, DicionarioUom
    from apps.financeiro.models import RegraPagamento, MeioPagamento
    from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento

    uom_un = DicionarioUom(id=1, sigla='UN', descricao='UNIDADE')
    uom_kg = DicionarioUom(id=2, sigla='KG', descricao='QUILOGRAMA')

    cliente = ClienteFornecedor(
        id=1,
        tipo='CLIENTE',
        tipo_pessoa='PJ',
        nome_razao='PETROBRAS TRANSPORTE S.A. - TRANSPETRO',
        cnpj_cpf='33.000.167/0001-01',
        telefone='(21) 3211-9000',
        logradouro='AVENIDA PRESIDENTE VARGAS',
        numero='328',
        bairro='CENTRO',
        cidade='RIO DE JANEIRO',
        uf='RJ'
    )

    equipamento = Equipamento(
        id=1,
        placa='EMC-2026',
        identificacao='MAQUINA SOLDA MIG/MAG ESAB 400A',
        descricao='CABECOTE REFORCADO E SISTEMA DE REFRIGERACAO INDUSTRIAL'
    )

    item_eletrodo = Item(
        id=1,
        nome='ELETRODO REVESTIDO E7018 3.25MM',
        unidade_compra=uom_kg,
        fator_conversao=Decimal('1.0000'),
        ultimo_custo_compra=Decimal('28.50'),
        tipo_uso='INSUMO_PRODUTIVO'
    )

    produto_reforma = Produto(
        id=1,
        nome='REFORMA ESTRUTURAL DE CHASSI E SOLDA TIG ALTA PRECISAO',
        unidade_venda=uom_un,
        descricao='RECUPERACAO COMPLETA DE VIGAS DE SUSTENTACAO E REFAZIMENTO DE JUNTAS SOLDADAS',
        tempo_estimado_execucao=Decimal('4.50')
    )

    meio_pix = MeioPagamento(id=1, nome='PIX', ativo=True)
    meio_boleto = MeioPagamento(id=2, nome='BOLETO BANCARIO', ativo=True)

    regra_pix = RegraPagamento(
        id=1,
        nome='PIX A VISTA (5% DESCONTO)',
        meio_pagamento=meio_pix,
        tipo_cobranca='A_VISTA',
        numero_parcelas=1,
        desconto_concedido_padrao=Decimal('5.00')
    )

    regra_boleto = RegraPagamento(
        id=2,
        nome='BOLETO 30/60 DIAS',
        meio_pagamento=meio_boleto,
        tipo_cobranca='PARCELADO',
        numero_parcelas=2,
        prazo_primeira_parcela_dias=30,
        intervalo_parcelas_dias=30,
        desconto_concedido_padrao=Decimal('0.00')
    )

    class MockRelatedManager:
        def __init__(self, items):
            self._items = items
        def all(self):
            return self._items
        def select_related(self, *args, **kwargs):
            return self
        def exists(self):
            return len(self._items) > 0
        def __iter__(self):
            return iter(self._items)

    class MockOrcamento:
        def __init__(self, id, cliente, equipamento, data_geracao, data_validade, status_operacional, status_financeiro, valor_bruto, valor_desconto_aplicado, itens, propostas):
            self.id = id
            self.cliente = cliente
            self.equipamento = equipamento
            self.data_geracao = data_geracao
            self.data_validade = data_validade
            self.status_operacional = status_operacional
            self.status_financeiro = status_financeiro
            self.valor_bruto = valor_bruto
            self.valor_desconto_aplicado = valor_desconto_aplicado
            self.itens_orcamento = MockRelatedManager(itens)
            self.propostas_pagamento = MockRelatedManager(propostas)
            self.motivo_cancelamento = None

        @property
        def valor_liquido(self):
            return max(self.valor_bruto - self.valor_desconto_aplicado, Decimal('0.00'))

        def get_status_operacional_display(self):
            return "APROVADO"

    hoje = timezone.now().date()

    # Cria itens mock em memória para renderização
    item1 = OrcamentoItem(
        id=1,
        produto=produto_reforma,
        quantidade=Decimal('1.0000'),
        custo_snapshot=Decimal('488.25'),
        valor_venda_snapshot=Decimal('1450.00')
    )
    item2 = OrcamentoItem(
        id=2,
        item=item_eletrodo,
        quantidade=Decimal('5.0000'),
        custo_snapshot=Decimal('28.50'),
        valor_venda_snapshot=Decimal('50.00')
    )
    item3 = OrcamentoItem(
        id=3,
        descricao_livre='TESTE HIDROSTATICO E LAUDO TECNICO DE ENSAIO NAO DESTRUTIVO (END)',
        quantidade=Decimal('1.0000'),
        custo_snapshot=Decimal('50.00'),
        valor_venda_snapshot=Decimal('150.00')
    )

    prop1 = OrcamentoPropostaPagamento(
        id=1,
        regra_pagamento=regra_pix,
        desconto_personalizado=Decimal('5.00')
    )
    prop2 = OrcamentoPropostaPagamento(
        id=2,
        regra_pagamento=regra_boleto,
        desconto_personalizado=Decimal('0.00')
    )

    orcamento = MockOrcamento(
        id=1089,
        cliente=cliente,
        equipamento=equipamento,
        data_geracao=hoje,
        data_validade=hoje + timezone.timedelta(days=15),
        status_operacional='APROVADO',
        status_financeiro='A_FATURAR',
        valor_bruto=Decimal('1850.00'),
        valor_desconto_aplicado=Decimal('100.00'),
        itens=[item1, item2, item3],
        propostas=[prop1, prop2]
    )

    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, 'wb') as f:
        gerar_pdf_orcamento(orcamento, buffer=f)

    return caminho_arquivo
