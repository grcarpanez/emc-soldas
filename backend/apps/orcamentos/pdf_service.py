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

from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, Image
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


class NumberedCanvas(canvas.Canvas):
    """
    Canvas em dois passos para computar o total exato de páginas (Página X de Y)
    e renderizar o rodapé institucional em todas as páginas do orçamento.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(COLOR_TEXT_MUTED)

        # Linha técnica de rodapé
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(14 * mm, 12 * mm, 210 * mm - 14 * mm, 12 * mm)

        # Identificação técnica à esquerda
        data_hora_emissao = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
        texto_esquerda = f"EMC Soldas ERP • Proposta Comercial gerada eletronicamente em {data_hora_emissao}"
        self.drawString(14 * mm, 7.5 * mm, texto_esquerda)

        # Numeração de páginas à direita
        texto_direita = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(210 * mm - 14 * mm, 7.5 * mm, texto_direita)
        self.restoreState()


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


def gerar_pdf_orcamento(orcamento, buffer=None, config_override=None):
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
        bottomMargin=18 * mm
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

    style_cell_header_center = ParagraphStyle(
        'CellHeaderCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
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

    style_cell_center = ParagraphStyle(
        'CellCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_CENTER
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
    if config_override is not None:
        config = config_override
    else:
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

    # Verificação e carregamento seguro da Logo da Empresa com Bounding Box Fit
    logo_flowable = None
    logo_path = getattr(config, 'logo_empresa_url', None)
    if logo_path and isinstance(logo_path, str) and logo_path.strip():
        candidatos = [
            logo_path,
            os.path.join(getattr(settings, 'BASE_DIR', ''), logo_path.lstrip('/\\')),
            os.path.join(getattr(settings, 'MEDIA_ROOT', ''), logo_path.lstrip('/\\')),
            os.path.join(os.path.dirname(__file__), '..', '..', logo_path.lstrip('/\\')),
        ]
        for cand in candidatos:
            if os.path.isfile(cand):
                try:
                    with PILImage.open(cand) as pil_img:
                        img_w, img_h = pil_img.size
                    if img_w > 0 and img_h > 0:
                        # Bounding Box máxima permitida para a logomarca no cabeçalho
                        max_w = 46 * mm
                        max_h = 22 * mm
                        scale = min(max_w / float(img_w), max_h / float(img_h))
                        final_w = float(img_w) * scale
                        final_h = float(img_h) * scale
                        logo_flowable = Image(cand, width=final_w, height=final_h)
                        break
                except Exception:
                    logo_flowable = None

    if logo_flowable:
        # Se tem logo cadastrada: compõe logo à esquerda e dados cadastrais ao lado
        empresa_dados_html = f"""
        <b>{config.razao_social.upper()}</b><br/>
        CNPJ: {config.cnpj}<br/>
        Fone: {config.telefone_contato}<br/>
        {config.endereco_oficina}
        """
        col_esquerda_conteudo = Table(
            [[logo_flowable, Paragraph(empresa_dados_html, style_empresa_dados)]],
            colWidths=[48 * mm, 62 * mm]
        )
        col_esquerda_conteudo.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 4),
        ]))
    else:
        # Se NÃO tem logo: ocupa os 110mm com tipografia institucional limpa
        empresa_texto = f"""
        <b>{config.razao_social.upper()}</b><br/>
        CNPJ: {config.cnpj} | Fone: {config.telefone_contato}<br/>
        {config.endereco_oficina}
        """
        col_esquerda_conteudo = Paragraph(empresa_texto, style_empresa_dados)

    dt_geracao_str = orcamento.data_geracao.strftime('%d/%m/%Y') if orcamento.data_geracao else timezone.now().strftime('%d/%m/%Y')
    dt_validade_str = orcamento.data_validade.strftime('%d/%m/%Y') if orcamento.data_validade else "NÃO INFORMADA"

    orc_meta_texto = f"""
    <b>PROPOSTA COMERCIAL #{orcamento.id:04d}</b><br/>
    Emissão: <b>{dt_geracao_str}</b><br/>
    Validade da Proposta: <b>{dt_validade_str}</b><br/>
    Status: <b>{orcamento.get_status_operacional_display()}</b>
    """

    header_data = [
        [col_esquerda_conteudo, Paragraph(orc_meta_texto, style_orc_meta)]
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
        Paragraph("#", style_cell_header_center),
        Paragraph("DESCRIÇÃO DO ITEM / SERVIÇO", style_cell_header),
        Paragraph("QTD", style_cell_header_center),
        Paragraph("UN", style_cell_header_center),
        Paragraph("PREÇO UNIT.", style_cell_header_center),
        Paragraph("SUBTOTAL", style_cell_header_center),
    ]

    itens_rows = [itens_header]
    col_w_idx = 8 * mm
    col_w_desc = 90 * mm
    col_w_qtd = 16 * mm
    col_w_un = 14 * mm
    col_w_unit = 27 * mm
    col_w_sub = 27 * mm

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
            Paragraph(f"{idx:02d}", style_cell_center),
            Paragraph(nome_item.upper(), style_cell_text),
            Paragraph(qtd_str, style_cell_center),
            Paragraph(unidade.upper(), style_cell_center),
            Paragraph(unit_str, style_cell_right),
            Paragraph(subtotal_str, style_cell_right_bold),
        ])

    itens_table = Table(
        itens_rows,
        colWidths=[col_w_idx, col_w_desc, col_w_qtd, col_w_un, col_w_unit, col_w_sub],
        repeatRows=1
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
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer


def salvar_pdf_exemplo(caminho_arquivo, com_logo=True, total_itens=25):
    """
    Gera um PDF de demonstração com dados fictícios completos e salva no caminho especificado.
    Suporta geração com logo ou sem logo para validação do cabeçalho institucional.
    """
    from apps.cadastros.models import ClienteFornecedor, Equipamento
    from apps.catalogo.models import Item, Produto, DicionarioUom
    from apps.financeiro.models import RegraPagamento, MeioPagamento
    from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento

    uom_un = DicionarioUom(id=1, sigla='UN', descricao='UNIDADE')
    uom_kg = DicionarioUom(id=2, sigla='KG', descricao='QUILOGRAMA')
    uom_m = DicionarioUom(id=3, sigla='M', descricao='METRO')
    uom_cj = DicionarioUom(id=4, sigla='CJ', descricao='CONJUNTO')
    uom_h = DicionarioUom(id=5, sigla='H', descricao='HORA')

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
        identificacao='MAQUINA SOLDA MIG/MAG ESAB 400A / CARRETA PRANCHA',
        descricao='CHASSI REFORCADO, SISTEMA DE SUSPENSAO PESADA E ESTRUTURA METÁLICA DE TRANSPORTE'
    )

    # Insumos / Materiais
    item_eletrodo = Item(id=1, nome='ELETRODO REVESTIDO AWS E7018 3.25MM', unidade_compra=uom_kg, ultimo_custo_compra=Decimal('28.50'))
    item_chapa_aco = Item(id=2, nome='CHAPA ACO CARBONO ASTM A36 1/2 POL (12.7MM)', unidade_compra=uom_kg, ultimo_custo_compra=Decimal('8.90'))
    item_arame_mig = Item(id=3, nome='ARAME TUBULAR MIG/MAG E71T-1 1.2MM (ROLO 15KG)', unidade_compra=uom_kg, ultimo_custo_compra=Decimal('22.40'))
    item_viga_w = Item(id=4, nome='VIGA METALICA PERFIL W 200X26.6 ASTM A572 GR50', unidade_compra=uom_m, ultimo_custo_compra=Decimal('185.00'))
    item_disco_corte = Item(id=5, nome='DISCO DE CORTE INDUSTRIAL 7X1/8 NORTON', unidade_compra=uom_un, ultimo_custo_compra=Decimal('14.20'))
    item_tinta_epoxi = Item(id=6, nome='TINTA EPOXI PRIMER BI-COMPONENTE ALTA ESPESSURA', unidade_compra=uom_un, ultimo_custo_compra=Decimal('160.00'))

    # Produtos / Serviços Compostos
    prod_recup_chassi = Produto(id=1, nome='RECUPERACAO E ALINHAMENTO ESTRUTURAL DE CHASSI PESADO', unidade_venda=uom_cj, tempo_estimado_execucao=Decimal('8.00'))
    prod_solda_tig = Produto(id=2, nome='SOLDA TIG ESPECIAL EM TUBULACOES E ACESSORIOS DE INOX', unidade_venda=uom_m, tempo_estimado_execucao=Decimal('3.50'))
    prod_fabric_suporte = Produto(id=3, nome='FABRICACAO E MONTAGEM DE SUPORTES REFORCADOS DE FIXACAO', unidade_venda=uom_un, tempo_estimado_execucao=Decimal('4.00'))

    # Meios e Regras de Pagamento
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
        nome='BOLETO 30/60/90 DIAS',
        meio_pagamento=meio_boleto,
        tipo_cobranca='PARCELADO',
        numero_parcelas=3,
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

    # Banco de 25 Itens Detalhados
    todos_itens = [
        OrcamentoItem(id=1, produto=prod_recup_chassi, quantidade=Decimal('1.0000'), custo_snapshot=Decimal('1250.00'), valor_venda_snapshot=Decimal('3400.00')),
        OrcamentoItem(id=2, item=item_viga_w, quantidade=Decimal('6.0000'), custo_snapshot=Decimal('185.00'), valor_venda_snapshot=Decimal('320.00')),
        OrcamentoItem(id=3, item=item_chapa_aco, quantidade=Decimal('85.0000'), custo_snapshot=Decimal('8.90'), valor_venda_snapshot=Decimal('16.50')),
        OrcamentoItem(id=4, produto=prod_fabric_suporte, quantidade=Decimal('4.0000'), custo_snapshot=Decimal('320.00'), valor_venda_snapshot=Decimal('650.00')),
        OrcamentoItem(id=5, item=item_arame_mig, quantidade=Decimal('30.0000'), custo_snapshot=Decimal('22.40'), valor_venda_snapshot=Decimal('38.00')),
        OrcamentoItem(id=6, item=item_eletrodo, quantidade=Decimal('15.0000'), custo_snapshot=Decimal('28.50'), valor_venda_snapshot=Decimal('48.00')),
        OrcamentoItem(id=7, produto=prod_solda_tig, quantidade=Decimal('5.5000'), custo_snapshot=Decimal('210.00'), valor_venda_snapshot=Decimal('420.00')),
        OrcamentoItem(id=8, item=item_disco_corte, quantidade=Decimal('20.0000'), custo_snapshot=Decimal('14.20'), valor_venda_snapshot=Decimal('25.00')),
        OrcamentoItem(id=9, descricao_livre='CORTE PLASMA CNC E CHANFRO DE BORDAS PARA SOLDA PENETRACAO TOTAL', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('180.00'), valor_venda_snapshot=Decimal('450.00')),
        OrcamentoItem(id=10, descricao_livre='USINAGEM DE BUCHAS E PINOS EM ACO SAE 1045 TRATADO TERMICAMENTE', quantidade=Decimal('8.0000'), custo_snapshot=Decimal('65.00'), valor_venda_snapshot=Decimal('140.00')),
        OrcamentoItem(id=11, descricao_livre='JATEAMENTO ABRASIVO COM GRANALHA DE ACO PADRAO SA 2.5', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('350.00'), valor_venda_snapshot=Decimal('850.00')),
        OrcamentoItem(id=12, item=item_tinta_epoxi, quantidade=Decimal('3.0000'), custo_snapshot=Decimal('160.00'), valor_venda_snapshot=Decimal('290.00')),
        OrcamentoItem(id=13, descricao_livre='ENSAIO NAO DESTRUTIVO (END) POR LIQUIDO PENETRANTE E ULTRA-SOM', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('200.00'), valor_venda_snapshot=Decimal('600.00')),
        OrcamentoItem(id=14, descricao_livre='EMISSAO DE LAUDO TECNICO COM ART (ANOTACAO DE RESPONSABILIDADE TECNICA)', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('150.00'), valor_venda_snapshot=Decimal('400.00')),
        OrcamentoItem(id=15, descricao_livre='PARAFUSO SEXTAVADO GRAU 8.8 M16X60 COM PORCA E ARRUELA DE PRESSAO', quantidade=Decimal('32.0000'), custo_snapshot=Decimal('6.50'), valor_venda_snapshot=Decimal('14.00')),
        OrcamentoItem(id=16, descricao_livre='CHAPA DE DESGASTE HARDOX 450 3/8 POL PARA REVESTIMENTO DE CACAMBA', quantidade=Decimal('45.0000'), custo_snapshot=Decimal('24.00'), valor_venda_snapshot=Decimal('48.00')),
        OrcamentoItem(id=17, descricao_livre='SOLDA POR ELETRODO REVESTIDO DE REVESTIMENTO DURO (ANTI-ABRASAO)', quantidade=Decimal('6.0000'), custo_snapshot=Decimal('85.00'), valor_venda_snapshot=Decimal('190.00')),
        OrcamentoItem(id=18, descricao_livre='VALVULA ESFERA TRIPARTIDA INOX 316 CLASSE 300 2 POL', quantidade=Decimal('2.0000'), custo_snapshot=Decimal('340.00'), valor_venda_snapshot=Decimal('680.00')),
        OrcamentoItem(id=19, descricao_livre='TUBO INDUSTRIAL SCHEDULE 40 ACO CARBONO SEM COSTURA 3 POL', quantidade=Decimal('12.0000'), custo_snapshot=Decimal('78.00'), valor_venda_snapshot=Decimal('155.00')),
        OrcamentoItem(id=20, descricao_livre='CONEXOES E CURVAS 90 GRAUS RAIO LONGO SCHEDULE 40 PARA TUBULACAO', quantidade=Decimal('8.0000'), custo_snapshot=Decimal('45.00'), valor_venda_snapshot=Decimal('98.00')),
        OrcamentoItem(id=21, descricao_livre='TESTE DE PRESSAO HIDROSTATICO EM TUBULACOES ATE 150 PSI', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('220.00'), valor_venda_snapshot=Decimal('520.00')),
        OrcamentoItem(id=22, descricao_livre='TRATAMENTO TERMICO DE ALIVIO DE TENSOES POS-SOLDAGEM (PWHT)', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('480.00'), valor_venda_snapshot=Decimal('1100.00')),
        OrcamentoItem(id=23, descricao_livre='SERVICO DE GUINDASTE E MOVIMENTACAO DE CARGA PESADA (4 HORAS)', quantidade=Decimal('4.0000'), custo_snapshot=Decimal('180.00'), valor_venda_snapshot=Decimal('350.00')),
        OrcamentoItem(id=24, descricao_livre='PINTURA DE ACABAMENTO POLIURETANO INDUSTRIAL (PU) COR CINZA MUNSELL', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('280.00'), valor_venda_snapshot=Decimal('720.00')),
        OrcamentoItem(id=25, descricao_livre='MONTAGEM FINAL, TESTE OPERACIONAL DE CARGA E LIBERACAO TECNICA', quantidade=Decimal('1.0000'), custo_snapshot=Decimal('300.00'), valor_venda_snapshot=Decimal('750.00')),
    ]

    itens_mock = todos_itens[:total_itens]
    valor_bruto_total = sum(i.quantidade * i.valor_venda_snapshot for i in itens_mock)
    desconto_aplicado = Decimal('500.00')

    prop1 = OrcamentoPropostaPagamento(id=1, regra_pagamento=regra_pix, desconto_personalizado=Decimal('5.00'))
    prop2 = OrcamentoPropostaPagamento(id=2, regra_pagamento=regra_boleto, desconto_personalizado=Decimal('0.00'))

    orcamento = MockOrcamento(
        id=1089,
        cliente=cliente,
        equipamento=equipamento,
        data_geracao=hoje,
        data_validade=hoje + timezone.timedelta(days=15),
        status_operacional='APROVADO',
        status_financeiro='A_FATURAR',
        valor_bruto=valor_bruto_total,
        valor_desconto_aplicado=desconto_aplicado,
        itens=itens_mock,
        propostas=[prop1, prop2]
    )

    # Configuração customizada da empresa (com ou sem logo)
    logo_path = None
    if com_logo:
        logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'exemplos', 'logo_generica_emc.png')
        if not os.path.exists(logo_path):
            from gerar_logo_exemplo import gerar_logo_generica
            gerar_logo_generica(logo_path)

    config_mock = ConfiguracaoGlobal(
        razao_social='EMC SOLDAS LTDA',
        cnpj='00.000.000/0001-00',
        telefone_contato='(11) 99999-9999',
        endereco_oficina='RUA INDUSTRIAL, 100 - OFICINA',
        logo_empresa_url=logo_path
    )

    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    try:
        with open(caminho_arquivo, 'wb') as f:
            gerar_pdf_orcamento(orcamento, buffer=f, config_override=config_mock)
    except PermissionError:
        caminho_arquivo = caminho_arquivo.replace('.pdf', '_v2.pdf')
        with open(caminho_arquivo, 'wb') as f:
            gerar_pdf_orcamento(orcamento, buffer=f, config_override=config_mock)

    return caminho_arquivo
