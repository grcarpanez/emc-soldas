"""
Script utilitário para gerar os 4 relatórios estratégicos em PDF com e sem logomarca institucional.
Gera os arquivos em 'backend/media/exemplos_relatorios/' e na raiz do projeto.
"""
import os
import sys
from decimal import Decimal
import django

# Inicializa o Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.administracao.models import ConfiguracaoGlobal
from apps.cadastros.models import ClienteFornecedor
from apps.relatorios.services import (
    InadimplenciaService, DossieClienteService, CurvaABCService, DREService
)
from core.reports.pdf_generator import (
    gerar_pdf_inadimplencia, gerar_pdf_dossie_cliente,
    gerar_pdf_curva_abc_clientes, gerar_pdf_dre
)
from gerar_logo_exemplo import gerar_logo_generica


def main():
    print("=== Gerador de PDFs Comparativos (Com Logo vs Sem Logo) ===")

    # 1. Garante que a logo exista
    caminho_logo = os.path.join(os.path.dirname(__file__), 'media', 'exemplos', 'logo_generica_emc.png')
    gerar_logo_generica(caminho_logo)
    print(f"[OK] Logomarca confirmada em: {caminho_logo}")

    # 2. Configurações: com logo e sem logo
    try:
        config_real = ConfiguracaoGlobal.get_solo()
    except Exception:
        config_real = ConfiguracaoGlobal()

    config_com_logo = ConfiguracaoGlobal(
        razao_social=config_real.razao_social or 'EMC SOLDAS E MANUTENCAO INDUSTRIAL LTDA',
        cnpj=config_real.cnpj or '12.345.678/0001-90',
        telefone_contato=config_real.telefone_contato or '(11) 98765-4321',
        endereco_oficina=config_real.endereco_oficina or 'RUA INDUSTRIAL DA SOLDA, 500 - GALPAO 2',
        logo_empresa_url=caminho_logo
    )

    config_sem_logo = ConfiguracaoGlobal(
        razao_social=config_real.razao_social or 'EMC SOLDAS E MANUTENCAO INDUSTRIAL LTDA',
        cnpj=config_real.cnpj or '12.345.678/0001-90',
        telefone_contato=config_real.telefone_contato or '(11) 98765-4321',
        endereco_oficina=config_real.endereco_oficina or 'RUA INDUSTRIAL DA SOLDA, 500 - GALPAO 2',
        logo_empresa_url=''
    )

    # 3. Obtém dados reais dos 4 relatórios (com fallback demonstrativo caso banco esteja vazio)
    dados_inadimp = InadimplenciaService.gerar_relatorio()
    if not dados_inadimp.get('itens'):
        dados_inadimp = {
            'posicao_em': '23/08/2026',
            'total_clientes_inadimplentes': 2,
            'total_titulos_atraso': 3,
            'valor_total_inadimplente': Decimal('4850.00'),
            'media_dias_atraso': 18,
            'itens': [
                {
                    'fatura_id': 1042,
                    'cliente_nome': 'MINERACAO VALE DO ACO S/A',
                    'cliente_documento': '33.000.167/0001-01',
                    'cliente_telefone': '(31) 99888-1122',
                    'data_vencimento': '05/08/2026',
                    'dias_atraso': 18,
                    'valor_pendente': Decimal('3200.00')
                },
                {
                    'fatura_id': 1045,
                    'cliente_nome': 'TRANSPORTE E LOGISTICA RAPIDO LTDA',
                    'cliente_documento': '11.222.333/0001-81',
                    'cliente_telefone': '(31) 98777-3344',
                    'data_vencimento': '12/08/2026',
                    'dias_atraso': 11,
                    'valor_pendente': Decimal('1650.00')
                }
            ]
        }

    # Cliente para o dossiê
    cliente = ClienteFornecedor.objects.filter(deleted_at__isnull=True).first()
    cliente_id = cliente.id if cliente else 1
    dados_dossie = DossieClienteService.gerar_dossie(cliente_id)
    if not dados_dossie:
        dados_dossie = {
            'cliente': {
                'id': 1,
                'nome_razao': 'MINERACAO VALE DO ACO S/A',
                'cnpj_cpf': '33.000.167/0001-01',
                'telefone': '(31) 99888-1122',
                'email': 'contato@valedoaco.com.br',
                'logradouro': 'AV INDUSTRIAL',
                'numero': '1500',
                'bairro': 'DISTRITO INDUSTRIAL',
                'cidade': 'BELO HORIZONTE',
                'uf': 'MG'
            },
            'total_orcamentos': 8,
            'total_faturado': Decimal('45800.00'),
            'total_pago': Decimal('41000.00'),
            'total_aberto': Decimal('4800.00'),
            'indice_pontualidade': 92,
            'segregacao_vendas': {
                'produtos': {'quantidade': 14, 'valor_total': Decimal('12500.00'), 'percentual': 27},
                'servicos': {'quantidade': 6, 'valor_total': Decimal('33300.00'), 'percentual': 73}
            },
            'orcamentos': [
                {'numero': 'ORC-2026-089', 'data_geracao': '15/08/2026', 'status_operacional': 'CONCLUIDO', 'status_financeiro': 'FATURADO', 'valor_bruto': Decimal('8500.00'), 'valor_final': Decimal('8000.00')},
                {'numero': 'ORC-2026-074', 'data_geracao': '02/08/2026', 'status_operacional': 'CONCLUIDO', 'status_financeiro': 'PAGO', 'valor_bruto': Decimal('14200.00'), 'valor_final': Decimal('13500.00')},
            ]
        }

    dados_abc = CurvaABCService.calcular_curva_abc_clientes()
    if not dados_abc.get('itens'):
        dados_abc = {
            'data_inicio': '01/08/2026',
            'data_fim': '23/08/2026',
            'faturamento_total_periodo': Decimal('78900.00'),
            'total_clientes_ativos': 3,
            'qtd_classe_a': 1,
            'qtd_classe_b': 1,
            'qtd_classe_c': 1,
            'itens': [
                {'posicao': 1, 'cliente_nome': 'MINERACAO VALE DO ACO S/A', 'cliente_documento': '33.000.167/0001-01', 'faturamento_total': Decimal('52000.00'), 'percentual_participacao': Decimal('65.91'), 'percentual_acumulado': Decimal('65.91'), 'classe_abc': 'A'},
                {'posicao': 2, 'cliente_nome': 'USINA SIDERURGICA CENTRAL LTDA', 'cliente_documento': '22.333.444/0001-55', 'faturamento_total': Decimal('18500.00'), 'percentual_participacao': Decimal('23.45'), 'percentual_acumulado': Decimal('89.36'), 'classe_abc': 'B'},
                {'posicao': 3, 'cliente_nome': 'OFICINA MECANICA EXPRESS EIRELI', 'cliente_documento': '44.555.666/0001-77', 'faturamento_total': Decimal('8400.00'), 'percentual_participacao': Decimal('10.64'), 'percentual_acumulado': Decimal('100.00'), 'classe_abc': 'C'},
            ]
        }

    dados_dre = DREService.gerar_dre_simplificado(regime='competencia')

    # Diretório de saída
    pasta_saida = os.path.join(os.path.dirname(__file__), 'media', 'exemplos_relatorios')
    os.makedirs(pasta_saida, exist_ok=True)
    pasta_raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    relatorios = [
        ("01_inadimplencia", gerar_pdf_inadimplencia, dados_inadimp),
        ("02_dossie_cliente", gerar_pdf_dossie_cliente, dados_dossie),
        ("03_curva_abc_clientes", gerar_pdf_curva_abc_clientes, dados_abc),
        ("04_dre_simplificado", gerar_pdf_dre, dados_dre),
    ]

    for nome_base, func_geradora, dados in relatorios:
        # Versão COM LOGO
        bytes_com_logo = func_geradora(dados, config_override=config_com_logo)
        arq_com_logo_media = os.path.join(pasta_saida, f"{nome_base}_COM_logo.pdf")
        arq_com_logo_raiz = os.path.join(pasta_raiz, f"{nome_base}_COM_logo.pdf")
        with open(arq_com_logo_media, 'wb') as f:
            f.write(bytes_com_logo)
        with open(arq_com_logo_raiz, 'wb') as f:
            f.write(bytes_com_logo)

        # Versão SEM LOGO
        bytes_sem_logo = func_geradora(dados, config_override=config_sem_logo)
        arq_sem_logo_media = os.path.join(pasta_saida, f"{nome_base}_SEM_logo.pdf")
        arq_sem_logo_raiz = os.path.join(pasta_raiz, f"{nome_base}_SEM_logo.pdf")
        with open(arq_sem_logo_media, 'wb') as f:
            f.write(bytes_sem_logo)
        with open(arq_sem_logo_raiz, 'wb') as f:
            f.write(bytes_sem_logo)

        print(f"[OK] Gerados: {nome_base}_COM_logo.pdf  e  {nome_base}_SEM_logo.pdf")

    print("\n=== Todos os 8 PDFs foram gerados com sucesso na raiz do projeto e em backend/media/exemplos_relatorios/ ===")


if __name__ == '__main__':
    main()
