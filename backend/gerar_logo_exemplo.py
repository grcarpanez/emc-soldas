"""
Script utilitário para gerar uma logomarca genérica industrial em PNG da 'EMC SOLDAS'.
Salva o arquivo em 'backend/media/exemplos/logo_generica_emc.png'.
"""
import os
from PIL import Image, ImageDraw, ImageFont

def gerar_logo_generica(caminho_destino):
    os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)

    # Dimensões da logo com margens seguras (Canvas 600 x 180)
    width, height = 600, 180
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Cores Industrial Integrity
    color_rust = (183, 65, 14, 255)       # #B7410E (Rust Orange)
    color_dark_iron = (43, 43, 43, 255)   # #2B2B2B (Dark Iron)
    color_steel = (113, 121, 126, 255)    # #71797E (Steel Gray)

    # Símbolo Geométrico Industrial (Solda / Arco Elétrico)
    draw.polygon([(15, 30), (70, 30), (90, 85), (35, 85)], fill=color_rust)
    draw.polygon([(45, 90), (100, 90), (80, 145), (25, 145)], fill=color_dark_iron)
    # Centelha / Faísca de solda
    draw.polygon([(68, 70), (112, 82), (86, 95), (96, 110), (58, 100)], fill=(255, 185, 15, 255))

    # Carrega fontes com fallback
    try:
        font_emc = ImageFont.truetype("arialbd.ttf", 54)
        font_sub = ImageFont.truetype("arialbd.ttf", 16)
        font_tag = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_emc = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_tag = ImageFont.load_default()

    # Tipografia Institucional bem espaçada
    draw.text((125, 26), "EMC", fill=color_dark_iron, font=font_emc)
    draw.text((255, 26), "SOLDAS", fill=color_rust, font=font_emc)
    
    # Linha divisória industrial
    draw.line([(125, 92), (580, 92)], fill=color_rust, width=3)
    
    draw.text((126, 102), "SOLUÇÕES EM SOLDAGEM E USINAGEM", fill=color_steel, font=font_sub)
    draw.text((126, 128), "ENGENHARIA E CALDEIRARIA PESADA", fill=color_dark_iron, font=font_tag)

    img.save(caminho_destino, 'PNG')
    return caminho_destino

if __name__ == '__main__':
    caminho = os.path.join(os.path.dirname(__file__), 'media', 'exemplos', 'logo_generica_emc.png')
    gerar_logo_generica(caminho)
    print(f"[OK] Logo gerada com sucesso em: {caminho}")
