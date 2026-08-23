"""
Serviço de geração de PDF profissional para Faturas e Pré-Faturas (Espelho).
Utiliza ReportLab com layout e paleta alinhados ao Design System Industrial Integrity (docs/DESIGN.md).
Contempla suporte duplo:
- Pré-Fatura (Rascunho): Espelho de negociação comercial com simulação de propostas e supressão de descontos nulos.
- Fatura Final (Faturada/Paga): Consolidação oficial com parcelas, títulos a vencer/pagos e dados de quitação.
"""
import io
import os
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from apps.administracao.models import ConfiguracaoGlobal
from apps.faturamento.services import simular_propostas_fatura


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
COLOR_SUCCESS_GREEN = colors.HexColor('#2E7D32')
COLOR_WARNING_ORANGE = colors.HexColor('#E65100')
COLOR_ALERT_RED = colors.HexColor('#C62828')


class NumberedCanvas(canvas.Canvas):
    """
    Canvas em dois passos para computar o total exato de páginas (Página X de Y)
    e renderizar o rodapé institucional em todas as páginas da fatura.
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
        texto_esquerda = f"EMC Soldas ERP • Documento Financeiro emitido eletronicamente em {data_hora_emissao}"
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


def gerar_pdf_fatura(fatura):
    """
    Gera o arquivo PDF binário de uma Fatura ou Pré-Fatura no padrão Industrial Integrity.
    Retorna uma instância de io.BytesIO pronta para FileResponse ou persistência em disco.
    """
    buffer = io.BytesIO()

    # Margens técnicas: 14mm esquerda/direita, 14mm superior, 16mm inferior
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"Fatura_{fatura.id}_{fatura.cliente.nome_razao[:15]}",
        author="EMC Soldas - Sistema Integrado"
    )

    # Estilos Tipográficos
    styles = getSampleStyleSheet()

    style_company_title = ParagraphStyle(
        'DocCompanyTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=COLOR_DARK_IRON,
        alignment=TA_LEFT
    )

    style_company_meta = ParagraphStyle(
        'DocCompanyMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10.5,
        textColor=COLOR_TEXT_MUTED,
        alignment=TA_LEFT
    )

    style_badge_title = ParagraphStyle(
        'DocBadgeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.white,
        alignment=TA_RIGHT
    )

    style_badge_num = ParagraphStyle(
        'DocBadgeNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        textColor=COLOR_DARK_IRON,
        alignment=TA_RIGHT
    )

    style_section_heading = ParagraphStyle(
        'DocSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=COLOR_DARK_IRON,
        spaceAfter=3,
        alignment=TA_LEFT
    )

    style_cell_text = ParagraphStyle(
        'DocCellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=COLOR_TEXT_MAIN
    )

    style_cell_text_bold = ParagraphStyle(
        'DocCellTextBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=COLOR_TEXT_MAIN
    )

    style_cell_text_right = ParagraphStyle(
        'DocCellTextRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_RIGHT
    )

    style_cell_text_right_bold = ParagraphStyle(
        'DocCellTextRightBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_RIGHT
    )

    style_th = ParagraphStyle(
        'DocTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=TA_LEFT
    )

    style_th_right = ParagraphStyle(
        'DocTHRight',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=TA_RIGHT
    )

    style_provisional_alert = ParagraphStyle(
        'DocProvisionalAlert',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=COLOR_ALERT_RED,
        alignment=TA_CENTER
    )

    story = []
    largura_util = 182 * mm  # 210 - 28

    # 1. Configurações Globais da Oficina
    config = ConfiguracaoGlobal.get_solo()
    nome_empresa = config.razao_social or "EMC SOLDAS E USINAGEM INDUSTRIAL"
    cnpj_empresa = f"CNPJ: {config.cnpj}" if config.cnpj else "CNPJ: 00.000.000/0001-00"
    telefone_empresa = f"TEL: {config.telefone_contato}" if config.telefone_contato else "TEL: (31) 3000-0000"
    email_empresa = "E-MAIL: comercial@emcsoldas.com.br"
    endereco_empresa = config.endereco_oficina or "RUA INDUSTRIAL, 1000 - DISTRITO INDUSTRIAL"

    # Logo
    logo_flowable = None
    if config.logo_empresa_url:
        logo_path = os.path.join(settings.MEDIA_ROOT, config.logo_empresa_url.replace('/media/', ''))
        if os.path.exists(logo_path):
            try:
                with PILImage.open(logo_path) as pil_img:
                    orig_w, orig_h = pil_img.size
                    max_w = 42 * mm
                    max_h = 22 * mm
                    ratio = min(max_w / orig_w, max_h / orig_h)
                    logo_flowable = Image(logo_path, width=orig_w * ratio, height=orig_h * ratio)
            except Exception:
                logo_flowable = None

    # Título do Documento de acordo com o status
    is_rascunho = (fatura.status == 'RASCUNHO')
    is_paga = (fatura.status == 'PAGA')
    is_cancelada = (fatura.status == 'CANCELADA')

    if is_rascunho:
        titulo_doc = "PRÉ-FATURA • ESPELHO COMERCIAL"
        cor_badge = COLOR_STEEL_GRAY
    elif is_paga:
        titulo_doc = "FATURA COMERCIAL QUITADA"
        cor_badge = COLOR_SUCCESS_GREEN
    elif is_cancelada:
        titulo_doc = "FATURA CANCELADA"
        cor_badge = COLOR_ALERT_RED
    else:
        titulo_doc = "FATURA COMERCIAL FINAL"
        cor_badge = COLOR_RUST_ORANGE

    col_empresa_w = 110 * mm
    col_badge_w = 72 * mm

    dados_empresa_html = f"""
    <b>{nome_empresa}</b><br/>
    {cnpj_empresa} • {telefone_empresa}<br/>
    {endereco_empresa}<br/>
    {email_empresa}
    """

    if logo_flowable:
        bloco_empresa = Table(
            [[logo_flowable, Paragraph(dados_empresa_html, style_company_meta)]],
            colWidths=[44 * mm, col_empresa_w - 44 * mm]
        )
        bloco_empresa.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        bloco_empresa = Paragraph(
            f"<b>{nome_empresa}</b><br/><font size='7.5' color='{COLOR_TEXT_MUTED.hexval()}'>{cnpj_empresa} • {telefone_empresa}<br/>{endereco_empresa}<br/>{email_empresa}</font>",
            style_company_title
        )

    badge_table = Table(
        [
            [Paragraph(titulo_doc, style_badge_title)],
            [Paragraph(f"FATURA Nº #{fatura.id:05d}", style_badge_num)]
        ],
        colWidths=[col_badge_w]
    )
    badge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), cor_badge),
        ('BACKGROUND', (0, 1), (0, 1), COLOR_LIGHT_SURFACE),
        ('BOX', (0, 0), (0, 1), 1, COLOR_DARK_IRON),
        ('INNERGRID', (0, 0), (0, 1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ]))

    header_table = Table(
        [[bloco_empresa, badge_table]],
        colWidths=[col_empresa_w, col_badge_w]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_DARK_IRON, spaceBefore=0, spaceAfter=3 * mm))

    # Aviso se for rascunho
    if is_rascunho:
        aviso_rascunho = Table(
            [[Paragraph("ATENÇÃO: ESTE DOCUMENTO É UMA PRÉ-FATURA (RASCUNHO / ESPELHO) PARA CONFERÊNCIA COMERCIAL E DEFINIÇÃO DE CONDIÇÃO DE PAGAMENTO. NÃO CONSTITUI QUITAÇÃO OU TÍTULO DEFINITIVO.", style_provisional_alert)]],
            colWidths=[largura_util]
        )
        aviso_rascunho.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFEBEE')),
            ('BOX', (0, 0), (-1, -1), 1, COLOR_ALERT_RED),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(aviso_rascunho)
        story.append(Spacer(1, 3 * mm))

    # 2. Dados do Cliente e Metadados da Fatura
    cliente = fatura.cliente
    data_emissao_str = fatura.data_emissao.strftime('%d/%m/%Y') if fatura.data_emissao else timezone.localdate().strftime('%d/%m/%Y')
    data_fechamento_str = fatura.data_fechamento.strftime('%d/%m/%Y') if fatura.data_fechamento else "EM ABERTO (RASCUNHO)"
    status_label = fatura.get_status_display()

    info_cliente_html = f"""
    <b>CLIENTE / RAZÃO SOCIAL:</b> {cliente.nome_razao}<br/>
    <b>CNPJ / CPF:</b> {cliente.cnpj_cpf or 'NÃO INFORMADO'}<br/>
    <b>CONTATO / TELEFONE:</b> {cliente.telefone or 'NÃO INFORMADO'} • {cliente.email or ''}<br/>
    <b>ENDEREÇO:</b> {cliente.logradouro or 'NÃO INFORMADO'}, {cliente.numero or 'S/N'} {cliente.cidade or ''}-{cliente.uf or ''}
    """

    info_fatura_html = f"""
    <b>DATA DE EMISSÃO:</b> {data_emissao_str}<br/>
    <b>DATA DE FECHAMENTO:</b> {data_fechamento_str}<br/>
    <b>STATUS DA FATURA:</b> {status_label}<br/>
    <b>NF-E DE SERVIÇO/VENDA:</b> {fatura.numero_nfe_venda or 'NÃO EMITIDA'}
    """

    cliente_meta_table = Table(
        [
            [
                Paragraph("<b>DADOS DO CLIENTE / TOMADOR</b>", style_section_heading),
                Paragraph("<b>CONTROLE E DATAS DA FATURA</b>", style_section_heading)
            ],
            [
                Paragraph(info_cliente_html, style_cell_text),
                Paragraph(info_fatura_html, style_cell_text)
            ]
        ],
        colWidths=[105 * mm, 77 * mm]
    )
    cliente_meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), COLOR_LIGHT_SURFACE),
        ('BACKGROUND', (1, 0), (1, 0), COLOR_LIGHT_SURFACE),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(cliente_meta_table)
    story.append(Spacer(1, 4 * mm))

    # 3. Tabela de Orçamentos Agrupados
    story.append(Paragraph("<b>ORÇAMENTOS CONSOLIDADOS NESTA FATURA</b>", style_section_heading))

    orcamentos = fatura.orcamentos_agrupados.filter(
        deleted_at__isnull=True
    ).select_related('equipamento').prefetch_related('itens_orcamento').order_by('id')

    tabela_orc_data = [
        [
            Paragraph("ORÇAMENTO", style_th),
            Paragraph("DATA", style_th),
            Paragraph("EQUIPAMENTO / VEÍCULO", style_th),
            Paragraph("RESUMO DOS ITENS / SERVIÇOS", style_th),
            Paragraph("VALOR BRUTO", style_th_right),
            Paragraph("VALOR LÍQUIDO", style_th_right),
        ]
    ]

    col_orc_widths = [22 * mm, 18 * mm, 38 * mm, 54 * mm, 25 * mm, 25 * mm]

    total_bruto_calculado = Decimal('0.00')

    for idx, orc in enumerate(orcamentos):
        data_orc_str = orc.data_geracao.strftime('%d/%m/%Y') if orc.data_geracao else "-"
        equip_str = f"{orc.equipamento.placa} ({orc.equipamento.descricao})" if orc.equipamento else "OFICINA / BANCADA"

        # Resumo dos itens
        itens_resumo = []
        for it in orc.itens_orcamento.all()[:3]:
            itens_resumo.append(it.nome_exibicao)
        if orc.itens_orcamento.count() > 3:
            itens_resumo.append(f"... (+{orc.itens_orcamento.count() - 3} itens)")
        resumo_str = ", ".join(itens_resumo) if itens_resumo else "SERVIÇOS DE SOLDA E MANUTENÇÃO"

        valor_bruto_orc = orc.valor_bruto or Decimal('0.00')
        valor_desc_orc = orc.valor_desconto_aplicado or Decimal('0.00')
        valor_liq_orc = max(Decimal('0.00'), valor_bruto_orc - valor_desc_orc)
        total_bruto_calculado += valor_liq_orc

        tabela_orc_data.append([
            Paragraph(f"<b>#{orc.id}</b>", style_cell_text_bold),
            Paragraph(data_orc_str, style_cell_text),
            Paragraph(equip_str, style_cell_text),
            Paragraph(resumo_str, style_cell_text),
            Paragraph(formatar_moeda(valor_bruto_orc), style_cell_text_right),
            Paragraph(formatar_moeda(valor_liq_orc), style_cell_text_right_bold),
        ])

    tabela_orc = Table(tabela_orc_data, colWidths=col_orc_widths, repeatRows=1)
    estilo_tabela_orc = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    for r in range(1, len(tabela_orc_data)):
        if r % 2 == 0:
            estilo_tabela_orc.append(('BACKGROUND', (0, r), (-1, r), COLOR_ALT_ROW))

    tabela_orc.setStyle(TableStyle(estilo_tabela_orc))
    story.append(tabela_orc)
    story.append(Spacer(1, 3 * mm))

    # 4. Bloco de Totais Consolidados da Fatura
    linhas_totais = []

    # Subtotal Bruto dos Orçamentos
    linhas_totais.append([
        Paragraph("<b>SUBTOTAL CONSOLIDADO DOS ORÇAMENTOS:</b>", style_cell_text_right),
        Paragraph(formatar_moeda(fatura.valor_bruto), style_cell_text_right_bold)
    ])

    # Desconto Comercial Global (Oculto se for zerado conforme FSD)
    if fatura.desconto_global and fatura.desconto_global > Decimal('0.00'):
        linhas_totais.append([
            Paragraph("<b>DESCONTO COMERCIAL DA FATURA:</b>", style_cell_text_right),
            Paragraph(f"- {formatar_moeda(fatura.desconto_global)}", style_cell_text_right_bold)
        ])

    # Total Final Faturado
    linhas_totais.append([
        Paragraph("<font size='9'><b>VALOR TOTAL FATURADO:</b></font>", style_cell_text_right),
        Paragraph(f"<font size='10' color='{COLOR_RUST_ORANGE.hexval()}'><b>{formatar_moeda(fatura.valor_total_faturado)}</b></font>", style_cell_text_right_bold)
    ])

    tabela_totais = Table(linhas_totais, colWidths=[130 * mm, 52 * mm])
    tabela_totais.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_SURFACE),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FFF3E0') if not is_paga else colors.HexColor('#E8F5E9')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    totais_wrapper = Table(
        [[Paragraph("", style_cell_text), tabela_totais]],
        colWidths=[0 * mm, largura_util]
    )
    totais_wrapper.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(totais_wrapper)
    story.append(Spacer(1, 4 * mm))

    # 5. Condições de Pagamento e Parcelamento
    if is_rascunho:
        # Se for Rascunho: Simulação de Propostas Sugeridas
        propostas_simuladas = simular_propostas_fatura(fatura)
        if propostas_simuladas:
            story.append(Paragraph("<b>OPÇÕES DE PAGAMENTO SUGERIDAS PARA ESTA PRÉ-FATURA</b>", style_section_heading))

            tabela_prop_data = [
                [
                    Paragraph("CONDIÇÃO COMERCIAL", style_th),
                    Paragraph("MEIO", style_th),
                    Paragraph("DESC. %", style_th_right),
                    Paragraph("PARCELAS", style_th),
                    Paragraph("VALOR FINAL LÍQUIDO", style_th_right),
                ]
            ]

            col_prop_widths = [55 * mm, 32 * mm, 20 * mm, 40 * mm, 35 * mm]

            for prop in propostas_simuladas:
                parc_detalhe = f"{prop['numero_parcelas']}x de {formatar_moeda(prop['valor_parcela'])}" if prop['numero_parcelas'] > 1 else "À VISTA"
                desc_str = f"{prop['desconto_percentual']:.1f}%" if prop['desconto_percentual'] > 0 else "0%"

                tabela_prop_data.append([
                    Paragraph(f"<b>{prop['regra_nome']}</b>", style_cell_text),
                    Paragraph(prop['meio_pagamento_nome'], style_cell_text),
                    Paragraph(desc_str, style_cell_text_right),
                    Paragraph(parc_detalhe, style_cell_text),
                    Paragraph(formatar_moeda(prop['valor_final']), style_cell_text_right_bold),
                ])

            tabela_prop = Table(tabela_prop_data, colWidths=col_prop_widths)
            estilo_prop = [
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
                ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            for r in range(1, len(tabela_prop_data)):
                if r % 2 == 0:
                    estilo_prop.append(('BACKGROUND', (0, r), (-1, r), COLOR_ALT_ROW))

            tabela_prop.setStyle(TableStyle(estilo_prop))
            story.append(tabela_prop)
            story.append(Spacer(1, 4 * mm))
    else:
        # Se for Faturada ou Paga: Condição Comercial Definitiva e Parcelas
        regra = fatura.regra_pagamento
        regra_nome = regra.nome if regra else "CONDIÇÃO COMERCIAL PADRÃO"
        meio_nome = regra.meio_pagamento.nome if regra and regra.meio_pagamento else "A DEFINIR"

        story.append(Paragraph(f"<b>CONDIÇÃO COMERCIAL DEFINIDA: {regra_nome} ({meio_nome})</b>", style_section_heading))

        parcelas = fatura.lancamentos_financeiros.filter(
            tipo_lancamento='ENTRADA',
            deleted_at__isnull=True
        ).order_by('data_vencimento', 'id')

        if parcelas.exists():
            tabela_parc_data = [
                [
                    Paragraph("PARCELA / TÍTULO", style_th),
                    Paragraph("DATA DE VENCIMENTO", style_th),
                    Paragraph("MEIO DE PAGAMENTO", style_th),
                    Paragraph("VALOR (R$)", style_th_right),
                    Paragraph("SITUAÇÃO / STATUS", style_th_right),
                ]
            ]
            col_parc_widths = [50 * mm, 35 * mm, 37 * mm, 30 * mm, 30 * mm]

            for idx_p, p in enumerate(parcelas):
                dt_venc = p.data_vencimento.strftime('%d/%m/%Y') if p.data_vencimento else "-"
                meio_parc = p.meio_pagamento.nome if p.meio_pagamento else meio_nome
                st_pag = p.get_status_pagamento_display()

                if p.status_pagamento == 'PAGO':
                    st_html = f"<font color='{COLOR_SUCCESS_GREEN.hexval()}'><b>PAGO</b></font>"
                elif p.status_pagamento == 'VENCIDO':
                    st_html = f"<font color='{COLOR_ALERT_RED.hexval()}'><b>VENCIDO</b></font>"
                elif p.status_pagamento == 'CANCELADO':
                    st_html = f"<font color='{COLOR_TEXT_MUTED.hexval()}'>CANCELADO</font>"
                else:
                    st_html = f"<font color='{COLOR_WARNING_ORANGE.hexval()}'><b>A VENCER</b></font>"

                tabela_parc_data.append([
                    Paragraph(f"<b>{p.descricao or f'PARCELA {idx_p + 1}'}</b>", style_cell_text),
                    Paragraph(dt_venc, style_cell_text),
                    Paragraph(meio_parc, style_cell_text),
                    Paragraph(formatar_moeda(p.valor), style_cell_text_right_bold),
                    Paragraph(st_html, style_cell_text_right),
                ])

            tabela_parc = Table(tabela_parc_data, colWidths=col_parc_widths)
            estilo_parc = [
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
                ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
            for r in range(1, len(tabela_parc_data)):
                if r % 2 == 0:
                    estilo_parc.append(('BACKGROUND', (0, r), (-1, r), COLOR_ALT_ROW))

            tabela_parc.setStyle(TableStyle(estilo_parc))
            story.append(tabela_parc)
            story.append(Spacer(1, 4 * mm))

    # 6. Dados para Pagamento Bancário / Pix e Assinaturas
    dados_bancarios_html = f"""
    <b>DADOS PARA PAGAMENTO / TRANSFERÊNCIA BANCÁRIA:</b><br/>
    • <b>Favorecido:</b> {nome_empresa} • {cnpj_empresa}<br/>
    • <b>Chave PIX:</b> {config.cnpj or 'comercial@emcsoldas.com.br'}<br/>
    • <b>Instruções:</b> Envie o comprovante de liquidação para financeiro@emcsoldas.com.br.
    """

    bloco_pagto = Table([[Paragraph(dados_bancarios_html, style_cell_text)]], colWidths=[largura_util])
    bloco_pagto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_SURFACE),
        ('BOX', (0, 0), (-1, -1), 0.75, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether([
        bloco_pagto,
        Spacer(1, 6 * mm),
        Table(
            [
                [
                    Paragraph("________________________________________<br/><b>EMC SOLDAS - DEPARTAMENTO FINANCEIRO</b>", style_cell_text),
                    Paragraph("________________________________________<br/><b>CLIENTE / TOMADOR DO SERVIÇO</b>", style_cell_text_right)
                ]
            ],
            colWidths=[91 * mm, 91 * mm]
        )
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
