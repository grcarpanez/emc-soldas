"""
Gerador de relatórios executivos em PDF para a Central Analítica do sistema EMC Soldas.
Utiliza ReportLab com layout profissional baseado no Design System Industrial Integrity (docs/DESIGN.md).
Contempla NumberedCanvas (Página X de Y), inserção inteligente da logomarca institucional,
tabelas técnicas zebradas, cabeçalhos centralizados vertical e horizontalmente, sumários executivos e cantos retos (0px).
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
COLOR_SUCCESS = colors.HexColor('#2E7D32')
COLOR_DANGER = colors.HexColor('#C62828')
COLOR_WARNING = colors.HexColor('#EF6C00')


class NumberedCanvas(canvas.Canvas):
    """
    Canvas em dois passos para computar o total exato de páginas (Página X de Y)
    e renderizar o rodapé institucional em todas as páginas do relatório.
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
        texto_esquerda = f"EMC Soldas ERP • Central Analítica • Relatório emitido em {data_hora_emissao}"
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
        try:
            valor = Decimal(str(valor))
        except Exception:
            return str(valor)
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_numero(valor, casas=2):
    """Formata decimal com N casas."""
    if valor is None:
        return "0"
    if not isinstance(valor, Decimal):
        try:
            valor = Decimal(str(valor))
        except Exception:
            return str(valor)
    fmt = f"{{:,.{casas}f}}"
    return fmt.format(valor).replace(',', 'X').replace('.', ',').replace('X', '.')


def obter_estilos_base():
    """Retorna folha de estilos padronizada Industrial Integrity."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='IndustrialTitle',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=COLOR_DARK_IRON,
        alignment=TA_RIGHT
    ))

    styles.add(ParagraphStyle(
        name='IndustrialSubtitle',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_TEXT_MUTED,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=COLOR_DARK_IRON,
        spaceBefore=7,
        spaceAfter=3
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='TableHeaderCenter',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_LEFT
    ))

    styles.add(ParagraphStyle(
        name='TableCellCenter',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='TableCellRight',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_RIGHT
    ))

    styles.add(ParagraphStyle(
        name='TableCellBoldRight',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=COLOR_TEXT_MAIN,
        alignment=TA_RIGHT
    ))

    styles.add(ParagraphStyle(
        name='SummaryLabel',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_DARK_IRON
    ))

    styles.add(ParagraphStyle(
        name='SummaryValue',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=COLOR_RUST_ORANGE,
        alignment=TA_RIGHT
    ))

    return styles


def criar_cabecalho_institucional(titulo_relatorio, subtitulo="", styles=None, config_override=None):
    """
    Monta o cabeçalho executivo padrão do sistema com suporte inteligente à logomarca
    institucional (respeitando aspect ratio e bounding box fit) e dados da oficina.
    """
    if not styles:
        styles = obter_estilos_base()

    if config_override is not None:
        config = config_override
    else:
        try:
            config = ConfiguracaoGlobal.get_solo()
        except Exception:
            config = ConfiguracaoGlobal(
                razao_social='EMC SOLDAS & MANUTENÇÃO INDUSTRIAL',
                cnpj='12.345.678/0001-90',
                telefone_contato='(11) 98765-4321',
                endereco_oficina='RUA INDUSTRIAL DA SOLDA, 500 - GALPÃO 2'
            )

    razao = config.razao_social or "EMC SOLDAS & MANUTENÇÃO INDUSTRIAL"
    cnpj = config.cnpj or ""
    telefone = config.telefone_contato or ""
    endereco = config.endereco_oficina or ""

    # 1. Carregamento e Bounding Box Fit inteligente da Logomarca
    logo_flowable = None
    logo_path = getattr(config, 'logo_empresa_url', None)
    if logo_path and isinstance(logo_path, str) and logo_path.strip():
        candidatos = [
            logo_path,
            os.path.join(getattr(settings, 'BASE_DIR', ''), logo_path.lstrip('/\\')),
            os.path.join(getattr(settings, 'MEDIA_ROOT', ''), logo_path.lstrip('/\\')),
            os.path.join(os.path.dirname(__file__), '..', '..', logo_path.lstrip('/\\')),
            os.path.join(getattr(settings, 'BASE_DIR', ''), 'media', 'exemplos', 'logo_generica_emc.png'),
        ]
        for cand in candidatos:
            if os.path.isfile(cand):
                try:
                    with PILImage.open(cand) as pil_img:
                        img_w, img_h = pil_img.size
                    if img_w > 0 and img_h > 0:
                        max_w = 46 * mm
                        max_h = 22 * mm
                        scale = min(max_w / float(img_w), max_h / float(img_h))
                        final_w = float(img_w) * scale
                        final_h = float(img_h) * scale
                        logo_flowable = Image(cand, width=final_w, height=final_h)
                        break
                except Exception:
                    logo_flowable = None

    # 2. Dados textuais da empresa
    empresa_dados_html = f"<b>{razao.upper()}</b><br/>"
    if cnpj:
        empresa_dados_html += f"CNPJ: {cnpj}<br/>"
    if telefone:
        empresa_dados_html += f"Tel: {telefone}<br/>"
    if endereco:
        empresa_dados_html += f"{endereco}"

    if logo_flowable:
        col_esquerda = Table(
            [[logo_flowable, Paragraph(empresa_dados_html, styles['IndustrialSubtitle'])]],
            colWidths=[48 * mm, 60 * mm]
        )
        col_esquerda.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 4),
        ]))
    else:
        col_esquerda = Paragraph(empresa_dados_html, styles['IndustrialSubtitle'])

    # 3. Lado direito com Título do Relatório e Subtítulo
    titulo_html = f"<b>{titulo_relatorio.upper()}</b><br/><font color='#71797E' size='8'>{subtitulo}</font>"
    col_direita = Paragraph(titulo_html, styles['IndustrialTitle'])

    cabecalho_data = [[col_esquerda, col_direita]]
    tabela_cabecalho = Table(cabecalho_data, colWidths=[108 * mm, 74 * mm])
    tabela_cabecalho.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elementos = [
        tabela_cabecalho,
        Spacer(1, 2 * mm),
        HRFlowable(width="100%", thickness=1.5, color=COLOR_RUST_ORANGE, spaceBefore=1, spaceAfter=5),
    ]
    return elementos


def gerar_pdf_inadimplencia(dados, config_override=None):
    """Gera o PDF do Relatório de Inadimplência com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    # Cabeçalho
    subtitulo = f"Posição em {timezone.localtime(timezone.now()).strftime('%d/%m/%Y')} • Cobrança Preventiva"
    elementos.extend(criar_cabecalho_institucional("Painel de Inadimplência", subtitulo, styles, config_override=config_override))

    # Cards de Resumo Executivo
    total_inadimplente = dados.get('valor_total_inadimplente', Decimal('0.00'))
    total_clientes = dados.get('total_clientes_inadimplentes', 0)
    total_titulos = dados.get('total_titulos_atraso', 0)
    media_dias = dados.get('media_dias_atraso', 0)

    resumo_data = [
        [
            Paragraph("<b>TOTAL EM ATRASO</b>", styles['TableCellCenter']),
            Paragraph("<b>CLIENTES EM ATRASO</b>", styles['TableCellCenter']),
            Paragraph("<b>TÍTULOS VENCIDOS</b>", styles['TableCellCenter']),
            Paragraph("<b>MÉDIA DE ATRASO</b>", styles['TableCellCenter']),
        ],
        [
            Paragraph(f"<font color='#C62828' size='11'><b>{formatar_moeda(total_inadimplente)}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<font color='#2B2B2B' size='11'><b>{total_clientes}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<font color='#2B2B2B' size='11'><b>{total_titulos}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<font color='#EF6C00' size='11'><b>{media_dias} dias</b></font>", styles['TableCellCenter']),
        ]
    ]

    tabela_resumo = Table(resumo_data, colWidths=[45.5 * mm, 45.5 * mm, 45.5 * mm, 45.5 * mm])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_LIGHT_SURFACE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 4 * mm))

    # Tabela de Títulos Vencidos com Cabeçalhos Centralizados Vertical e Horizontalmente
    elementos.append(Paragraph("<b>Detalhamento de Faturas e Títulos Vencidos</b>", styles['SectionHeader']))

    headers = [
        Paragraph("<b>FATURA</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CLIENTE / CONTATO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>DOC / TELEFONE</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VENCIMENTO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>ATRASO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR ABERTO</b>", styles['TableHeaderCenter']),
    ]
    tabela_linhas = [headers]

    for item in dados.get('itens', []):
        dias = item.get('dias_atraso', 0)
        cor_dias = '#C62828' if dias > 30 else ('#EF6C00' if dias > 7 else '#131313')
        tabela_linhas.append([
            Paragraph(f"<b>#{item.get('fatura_id', '')}</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{item.get('cliente_nome', '')}</b>", styles['TableCell']),
            Paragraph(f"{item.get('cliente_documento', '')}<br/>{item.get('cliente_telefone', '')}", styles['TableCell']),
            Paragraph(str(item.get('data_vencimento', '')), styles['TableCellCenter']),
            Paragraph(f"<font color='{cor_dias}'><b>{dias} d</b></font>", styles['TableCellCenter']),
            Paragraph(f"<b>{formatar_moeda(item.get('valor_pendente'))}</b>", styles['TableCellBoldRight']),
        ])

    if len(tabela_linhas) == 1:
        tabela_linhas.append([
            Paragraph("Nenhuma fatura em atraso localizada no período.", styles['TableCellCenter']),
            "", "", "", "", ""
        ])

    tabela_titulos = Table(tabela_linhas, colWidths=[20 * mm, 52 * mm, 40 * mm, 24 * mm, 18 * mm, 28 * mm], repeatRows=1)
    tabela_titulos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    elementos.append(tabela_titulos)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def gerar_pdf_dossie_cliente(dados, config_override=None):
    """Gera o PDF do Dossiê Completo do Cliente com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    cliente = dados.get('cliente', {})
    subtitulo = f"Dossiê Histórico e Comercial • Cliente #{cliente.get('id', '')}"
    elementos.extend(criar_cabecalho_institucional(f"Dossiê: {cliente.get('nome_razao', '')}", subtitulo, styles, config_override=config_override))

    # Bloco de Informações Cadastrais
    info_cliente_data = [
        [
            Paragraph(f"<b>Razão Social / Nome:</b> {cliente.get('nome_razao', '')}", styles['TableCell']),
            Paragraph(f"<b>CPF/CNPJ:</b> {cliente.get('cnpj_cpf', '') or 'NÃO INFORMADO'}", styles['TableCell']),
        ],
        [
            Paragraph(f"<b>Telefone:</b> {cliente.get('telefone', '') or '-'}", styles['TableCell']),
            Paragraph(f"<b>E-mail:</b> {cliente.get('email', '') or '-'}", styles['TableCell']),
        ],
        [
            Paragraph(f"<b>Endereço:</b> {cliente.get('logradouro', '') or ''}, {cliente.get('numero', '') or ''} - {cliente.get('bairro', '') or ''}", styles['TableCell']),
            Paragraph(f"<b>Cidade/UF:</b> {cliente.get('cidade', '') or ''}/{cliente.get('uf', '') or ''}", styles['TableCell']),
        ]
    ]
    tabela_info = Table(info_cliente_data, colWidths=[91 * mm, 91 * mm])
    tabela_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_SURFACE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_info)
    elementos.append(Spacer(1, 4 * mm))

    # Indicadores Financeiros do Cliente
    indicadores_data = [
        [
            Paragraph("<b>TOTAL ORÇAMENTOS</b>", styles['TableCellCenter']),
            Paragraph("<b>FATURAMENTO TOTAL</b>", styles['TableCellCenter']),
            Paragraph("<b>VALOR PAGO</b>", styles['TableCellCenter']),
            Paragraph("<b>SALDO EM ABERTO</b>", styles['TableCellCenter']),
            Paragraph("<b>PONTUALIDADE</b>", styles['TableCellCenter']),
        ],
        [
            Paragraph(f"<b>{dados.get('total_orcamentos', 0)}</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{formatar_moeda(dados.get('total_faturado'))}</b>", styles['TableCellCenter']),
            Paragraph(f"<font color='#2E7D32'><b>{formatar_moeda(dados.get('total_pago'))}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<font color='#C62828'><b>{formatar_moeda(dados.get('total_aberto'))}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('indice_pontualidade', 0)}%</b>", styles['TableCellCenter']),
        ]
    ]
    tabela_ind = Table(indicadores_data, colWidths=[36.4 * mm, 36.4 * mm, 36.4 * mm, 36.4 * mm, 36.4 * mm])
    tabela_ind.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_LIGHT_SURFACE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    elementos.append(tabela_ind)
    elementos.append(Spacer(1, 4 * mm))

    # Segregação de Vendas: Produtos vs Serviços (Cabeçalhos Centralizados)
    elementos.append(Paragraph("<b>Segregação de Consumo: Produtos (Peças) vs Serviços (Reformas)</b>", styles['SectionHeader']))
    seg = dados.get('segregacao_vendas', {})
    prod = seg.get('produtos', {})
    serv = seg.get('servicos', {})

    seg_data = [
        [
            Paragraph("<b>CATEGORIA</b>", styles['TableHeaderCenter']),
            Paragraph("<b>QUANTIDADE</b>", styles['TableHeaderCenter']),
            Paragraph("<b>VALOR TOTAL (R$)</b>", styles['TableHeaderCenter']),
            Paragraph("<b>PARTICIPAÇÃO (%)</b>", styles['TableHeaderCenter']),
        ],
        [
            Paragraph("<b>Venda Direta de Produtos / Materiais</b>", styles['TableCell']),
            Paragraph(str(prod.get('quantidade', 0)), styles['TableCellCenter']),
            Paragraph(formatar_moeda(prod.get('valor_total')), styles['TableCellBoldRight']),
            Paragraph(f"{prod.get('percentual', 0)}%", styles['TableCellCenter']),
        ],
        [
            Paragraph("<b>Prestação de Serviços / Reformas e Soldas</b>", styles['TableCell']),
            Paragraph(str(serv.get('quantidade', 0)), styles['TableCellCenter']),
            Paragraph(formatar_moeda(serv.get('valor_total')), styles['TableCellBoldRight']),
            Paragraph(f"{serv.get('percentual', 0)}%", styles['TableCellCenter']),
        ]
    ]
    tabela_seg = Table(seg_data, colWidths=[72 * mm, 30 * mm, 45 * mm, 35 * mm])
    tabela_seg.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_seg)
    elementos.append(Spacer(1, 4 * mm))

    # Histórico Recente de Orçamentos (Cabeçalhos Centralizados)
    elementos.append(Paragraph("<b>Histórico de Orçamentos</b>", styles['SectionHeader']))
    orc_headers = [
        Paragraph("<b>NÚMERO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>DATA</b>", styles['TableHeaderCenter']),
        Paragraph("<b>STATUS OPERACIONAL</b>", styles['TableHeaderCenter']),
        Paragraph("<b>STATUS FINANCEIRO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR BRUTO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR FINAL</b>", styles['TableHeaderCenter']),
    ]
    orc_rows = [orc_headers]
    for orc in dados.get('orcamentos', [])[:20]:
        orc_rows.append([
            Paragraph(f"<b>#{orc.get('numero', '')}</b>", styles['TableCellCenter']),
            Paragraph(str(orc.get('data_geracao', '')), styles['TableCellCenter']),
            Paragraph(str(orc.get('status_operacional', '')), styles['TableCell']),
            Paragraph(str(orc.get('status_financeiro', '')), styles['TableCell']),
            Paragraph(formatar_moeda(orc.get('valor_bruto')), styles['TableCellRight']),
            Paragraph(f"<b>{formatar_moeda(orc.get('valor_final'))}</b>", styles['TableCellBoldRight']),
        ])
    if len(orc_rows) == 1:
        orc_rows.append([Paragraph("Nenhum orçamento registrado para este cliente.", styles['TableCellCenter']), "", "", "", "", ""])

    tabela_orc = Table(orc_rows, colWidths=[20 * mm, 24 * mm, 40 * mm, 38 * mm, 30 * mm, 30 * mm], repeatRows=1)
    tabela_orc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_orc)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def gerar_pdf_curva_abc_clientes(dados, config_override=None):
    """Gera o PDF da Curva ABC de Clientes com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    subtitulo = f"Período: {dados.get('data_inicio', '')} até {dados.get('data_fim', '')} • Matriz 80/15/5%"
    elementos.extend(criar_cabecalho_institucional("Curva ABC de Clientes", subtitulo, styles, config_override=config_override))

    # Resumo das Classes A, B e C
    resumo_abc = [
        [
            Paragraph("<b>FATURAMENTO TOTAL</b>", styles['TableCellCenter']),
            Paragraph("<b>CLASSE A (80%)</b>", styles['TableCellCenter']),
            Paragraph("<b>CLASSE B (15%)</b>", styles['TableCellCenter']),
            Paragraph("<b>CLASSE C (5%)</b>", styles['TableCellCenter']),
        ],
        [
            Paragraph(f"<font color='#B7410E' size='10.5'><b>{formatar_moeda(dados.get('faturamento_total_periodo'))}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_a', 0)} clientes</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_b', 0)} clientes</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_c', 0)} clientes</b>", styles['TableCellCenter']),
        ]
    ]
    tabela_resumo = Table(resumo_abc, colWidths=[45.5 * mm, 45.5 * mm, 45.5 * mm, 45.5 * mm])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_LIGHT_SURFACE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 4 * mm))

    # Listagem Ranqueada com Cabeçalhos Centralizados Vertical e Horizontalmente
    headers = [
        Paragraph("<b>POS</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CLIENTE</b>", styles['TableHeaderCenter']),
        Paragraph("<b>DOC</b>", styles['TableHeaderCenter']),
        Paragraph("<b>FATURAMENTO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>PART. (%)</b>", styles['TableHeaderCenter']),
        Paragraph("<b>ACUM. (%)</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CLASSE</b>", styles['TableHeaderCenter']),
    ]
    linhas = [headers]

    for item in dados.get('itens', []):
        classe = item.get('classe_abc', '')
        cor_classe = '#2E7D32' if classe == 'A' else ('#EF6C00' if classe == 'B' else '#71797E')
        linhas.append([
            Paragraph(f"<b>#{item.get('posicao', 0)}</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{item.get('cliente_nome', '')}</b>", styles['TableCell']),
            Paragraph(str(item.get('cliente_documento', '') or '-'), styles['TableCell']),
            Paragraph(formatar_moeda(item.get('faturamento_total')), styles['TableCellBoldRight']),
            Paragraph(f"{formatar_numero(item.get('percentual_participacao'))}%", styles['TableCellCenter']),
            Paragraph(f"{formatar_numero(item.get('percentual_acumulado'))}%", styles['TableCellCenter']),
            Paragraph(f"<font color='{cor_classe}'><b>CLASSE {classe}</b></font>", styles['TableCellCenter']),
        ])

    if len(linhas) == 1:
        linhas.append([Paragraph("Nenhum cliente com faturamento no período.", styles['TableCellCenter']), "", "", "", "", "", ""])

    tabela_dados = Table(linhas, colWidths=[14 * mm, 62 * mm, 32 * mm, 30 * mm, 18 * mm, 18 * mm, 18 * mm], repeatRows=1)
    tabela_dados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_dados)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def gerar_pdf_curva_abc_itens(dados, config_override=None):
    """Gera o PDF da Curva ABC de Consumo de Itens com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    subtitulo = f"Período: {dados.get('data_inicio', '')} até {dados.get('data_fim', '')} • Consumo de Insumos"
    elementos.extend(criar_cabecalho_institucional("Curva ABC de Consumo de Itens", subtitulo, styles, config_override=config_override))

    # Resumo
    resumo_abc = [
        [
            Paragraph("<b>CUSTO TOTAL CONSUMO</b>", styles['TableCellCenter']),
            Paragraph("<b>ITENS CLASSE A (80%)</b>", styles['TableCellCenter']),
            Paragraph("<b>ITENS CLASSE B (15%)</b>", styles['TableCellCenter']),
            Paragraph("<b>ITENS CLASSE C (5%)</b>", styles['TableCellCenter']),
        ],
        [
            Paragraph(f"<font color='#B7410E' size='10.5'><b>{formatar_moeda(dados.get('custo_total_periodo'))}</b></font>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_a', 0)} itens</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_b', 0)} itens</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{dados.get('qtd_classe_c', 0)} itens</b>", styles['TableCellCenter']),
        ]
    ]
    tabela_resumo = Table(resumo_abc, colWidths=[45.5 * mm, 45.5 * mm, 45.5 * mm, 45.5 * mm])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_STEEL_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_LIGHT_SURFACE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 4 * mm))

    headers = [
        Paragraph("<b>POS</b>", styles['TableHeaderCenter']),
        Paragraph("<b>ITEM / INSUMO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>UOM</b>", styles['TableHeaderCenter']),
        Paragraph("<b>QTD CONSUMIDA</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CUSTO TOTAL</b>", styles['TableHeaderCenter']),
        Paragraph("<b>PART. (%)</b>", styles['TableHeaderCenter']),
        Paragraph("<b>ACUM. (%)</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CLASSE</b>", styles['TableHeaderCenter']),
    ]
    linhas = [headers]

    for item in dados.get('itens', []):
        classe = item.get('classe_abc', '')
        cor_classe = '#2E7D32' if classe == 'A' else ('#EF6C00' if classe == 'B' else '#71797E')
        linhas.append([
            Paragraph(f"<b>#{item.get('posicao', 0)}</b>", styles['TableCellCenter']),
            Paragraph(f"<b>{item.get('item_nome', '')}</b>", styles['TableCell']),
            Paragraph(str(item.get('uom_sigla', '')), styles['TableCellCenter']),
            Paragraph(formatar_numero(item.get('quantidade_consumida'), 3), styles['TableCellRight']),
            Paragraph(formatar_moeda(item.get('custo_total')), styles['TableCellBoldRight']),
            Paragraph(f"{formatar_numero(item.get('percentual_participacao'))}%", styles['TableCellCenter']),
            Paragraph(f"{formatar_numero(item.get('percentual_acumulado'))}%", styles['TableCellCenter']),
            Paragraph(f"<font color='{cor_classe}'><b>CLASSE {classe}</b></font>", styles['TableCellCenter']),
        ])

    if len(linhas) == 1:
        linhas.append([Paragraph("Nenhum item consumido no período.", styles['TableCellCenter']), "", "", "", "", "", "", ""])

    tabela_dados = Table(linhas, colWidths=[12 * mm, 56 * mm, 14 * mm, 24 * mm, 28 * mm, 16 * mm, 16 * mm, 16 * mm], repeatRows=1)
    tabela_dados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabela_dados)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def gerar_pdf_dre(dados, config_override=None):
    """Gera o PDF do DRE Simplificado com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    subtitulo = f"Período: {dados.get('data_inicio', '')} até {dados.get('data_fim', '')} • Regime: {dados.get('regime', 'COMPETENCIA').upper()}"
    elementos.extend(criar_cabecalho_institucional("Demonstrativo de Resultado (DRE)", subtitulo, styles, config_override=config_override))

    headers = [
        Paragraph("<b>ESTRUTURA DRE</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR (R$)</b>", styles['TableHeaderCenter']),
        Paragraph("<b>% RECEITA BRUTA</b>", styles['TableHeaderCenter']),
    ]
    linhas = [headers]

    for linha in dados.get('linhas', []):
        is_destaque = linha.get('is_destaque', False)
        is_total = linha.get('is_total', False)
        descricao = linha.get('descricao', '')
        valor_str = formatar_moeda(linha.get('valor'))
        perc = f"{formatar_numero(linha.get('percentual'))}%" if linha.get('percentual') is not None else "-"

        if is_total:
            cor_val = '#2E7D32' if Decimal(str(linha.get('valor', 0))) >= 0 else '#C62828'
            desc_p = Paragraph(f"<b><font size='9'>{descricao}</font></b>", styles['TableCell'])
            val_p = Paragraph(f"<b><font size='9' color='{cor_val}'>{valor_str}</font></b>", styles['TableCellBoldRight'])
            perc_p = Paragraph(f"<b><font size='9'>{perc}</font></b>", styles['TableCellCenter'])
        elif is_destaque:
            desc_p = Paragraph(f"<b>{descricao}</b>", styles['TableCell'])
            val_p = Paragraph(f"<b>{valor_str}</b>", styles['TableCellBoldRight'])
            perc_p = Paragraph(f"<b>{perc}</b>", styles['TableCellCenter'])
        else:
            desc_p = Paragraph(f"&nbsp;&nbsp;{descricao}", styles['TableCell'])
            val_p = Paragraph(valor_str, styles['TableCellRight'])
            perc_p = Paragraph(perc, styles['TableCellCenter'])

        linhas.append([desc_p, val_p, perc_p])

    tabela_dre = Table(linhas, colWidths=[112 * mm, 40 * mm, 30 * mm])
    tabela_dre.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))

    # Aplicar backgrounds condicionais nas linhas de destaque
    for i, linha in enumerate(dados.get('linhas', []), start=1):
        if linha.get('is_total'):
            tabela_dre.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), COLOR_LIGHT_SURFACE)]))
        elif linha.get('is_destaque'):
            tabela_dre.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), COLOR_ALT_ROW)]))

    elementos.append(tabela_dre)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()


def gerar_pdf_divergencias_conciliacao(dados, config_override=None):
    """Gera o PDF do Relatório de Divergências de Conciliação Bancária com cabeçalhos centralizados vertical e horizontalmente."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=18 * mm
    )

    styles = obter_estilos_base()
    elementos = []

    subtitulo = f"Conta: {dados.get('conta_nome', 'TODAS')} • Período: {dados.get('data_inicio', '')} até {dados.get('data_fim', '')}"
    elementos.extend(criar_cabecalho_institucional("Divergências de Conciliação Bancária", subtitulo, styles, config_override=config_override))

    # Aba 1: Sobras do Extrato
    elementos.append(Paragraph("<b>1. Transações no Extrato Bancário sem Vínculo no ERP</b>", styles['SectionHeader']))
    headers1 = [
        Paragraph("<b>DATA BANCO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>HISTÓRICO BANCÁRIO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>TIPO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>ARQUIVO ORIGEM</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR</b>", styles['TableHeaderCenter']),
    ]
    linhas1 = [headers1]
    for ext in dados.get('sobras_extrato', []):
        linhas1.append([
            Paragraph(str(ext.get('data', '')), styles['TableCellCenter']),
            Paragraph(str(ext.get('historico', '')), styles['TableCell']),
            Paragraph(str(ext.get('tipo', '')), styles['TableCellCenter']),
            Paragraph(str(ext.get('arquivo_origem', '') or '-'), styles['TableCell']),
            Paragraph(f"<b>{formatar_moeda(ext.get('valor'))}</b>", styles['TableCellBoldRight']),
        ])
    if len(linhas1) == 1:
        linhas1.append([Paragraph("Nenhuma transação pendente no extrato bancário.", styles['TableCellCenter']), "", "", "", ""])

    tab1 = Table(linhas1, colWidths=[24 * mm, 74 * mm, 20 * mm, 34 * mm, 30 * mm])
    tab1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tab1)
    elementos.append(Spacer(1, 5 * mm))

    # Aba 2: Sobras do ERP
    elementos.append(Paragraph("<b>2. Lançamentos do ERP com Status Pago sem Conciliação Confirmada</b>", styles['SectionHeader']))
    headers2 = [
        Paragraph("<b>DATA PGTO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>DESCRIÇÃO ERP</b>", styles['TableHeaderCenter']),
        Paragraph("<b>CATEGORIA</b>", styles['TableHeaderCenter']),
        Paragraph("<b>MEIO PGTO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>TIPO</b>", styles['TableHeaderCenter']),
        Paragraph("<b>VALOR</b>", styles['TableHeaderCenter']),
    ]
    linhas2 = [headers2]
    for erp in dados.get('sobras_erp', []):
        linhas2.append([
            Paragraph(str(erp.get('data_pagamento', '')), styles['TableCellCenter']),
            Paragraph(str(erp.get('descricao', '')), styles['TableCell']),
            Paragraph(str(erp.get('categoria', '')), styles['TableCell']),
            Paragraph(str(erp.get('meio_pagamento', '') or '-'), styles['TableCellCenter']),
            Paragraph(str(erp.get('tipo_lancamento', '')), styles['TableCellCenter']),
            Paragraph(f"<b>{formatar_moeda(erp.get('valor'))}</b>", styles['TableCellBoldRight']),
        ])
    if len(linhas2) == 1:
        linhas2.append([Paragraph("Nenhum lançamento pendente de conciliação no ERP.", styles['TableCellCenter']), "", "", "", "", ""])

    tab2 = Table(linhas2, colWidths=[22 * mm, 56 * mm, 36 * mm, 24 * mm, 16 * mm, 28 * mm])
    tab2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_DARK_IRON),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_ALT_ROW]),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tab2)

    doc.build(elementos, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
