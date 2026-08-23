"""
Script utilitário para gerar uma logomarca genérica industrial em PNG da 'EMC SOLDAS'.
Salva o arquivo em 'backend/media/exemplos/logo_generica_emc.png'.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def gerar_logo_generica(caminho_destino):
    os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)

    # Dimensões da logo (alta resolução)
    width, height = 480, 200
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Cores Industrial Integrity
    color_rust = (183, 65, 14, 255)       # #B7410E
    color_dark_iron = (43, 43, 43, 255)   # #2B2B2B
    color_steel = (113, 121, 126, 255)    # #71797E

    # Elemento Gráfico: Símbolo geométrico angular de Solda/Arco
    draw.polygon([(20, 40), (80, 40), (100, 100), (40, 100)], fill=color_rust)
    draw.polygon([(50, 105), (110, 105), (90, 165), (30, 165)], fill=color_dark_iron)
    # Centelha / Faísca de solda
    draw.polygon([(75, 80), (125, 95), (95, 110), (105, 125), (65, 115)], fill=(255, 180, 0, 255))

    # Tenta carregar fonte do sistema ou desenha texto
    try:
        font_large = ImageFont.truetype("arialbd.ttf", 60)
        font_sub = ImageFont.truetype("arialbd.ttf", 17)
        font_tag = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Tipografia Institucional
    draw.text((140, 36), "EMC", fill=color_dark_iron, font=font_large)
    draw.text((290, 36), "SOLDAS", fill=color_rust, font=font_large)
    draw.text((142, 110), "SOLUÇÕES EM SOLDAGEM E USINAGEM", fill=color_steel, font=font_sub)
    draw.text((142, 138), "ENGENHARIA E CALDEIRARIA PESADA", fill=color_dark_iron, font=font_tag)

    # Linha divisória industrial
    draw.line([(140, 102), (460, 102)], fill=color_rust, width=3)

    img.save(caminho_destino, 'PNG')
    return caminho_destino

if __name__ == '__main__':
    caminho = os.path.join(os.path.dirname(__file__), 'media', 'exemplos', 'logo_generica_emc.png')
    gerar_logo_generica(caminho)
    print(f"[OK] Logo gerada com sucesso em: {caminho}")
