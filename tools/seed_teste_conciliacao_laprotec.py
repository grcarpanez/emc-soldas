"""
Script para criação pontual do Orçamento e Fatura de Teste para Conciliação Bancária.
Cliente: LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA (CNPJ 09.027.059/0001-48).
Item: SERVICO DE TESTE (Qtd 1, Custo 170.00, Venda 210.53).
Data: 03/08/2026.
Regra de Pagamento: A VISTA NO PIX (5% DESC.) -> 210.53 - 10.53 = R$ 200.00 líquidos.
"""
import sys
import os
from decimal import Decimal
from datetime import date

# Configura path e settings do Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import transaction
from apps.cadastros.models import ClienteFornecedor
from apps.orcamentos.models import Orcamento, OrcamentoItem
from apps.faturamento.models import Fatura
from apps.faturamento.services import criar_pre_fatura, faturar_rascunho
from apps.financeiro.models import RegraPagamento, LancamentoFinanceiro

@transaction.atomic
def run():
    print("=== INICIANDO CRIAÇÃO DO ORÇAMENTO E FATURA DE TESTE ===")

    # 1. Localiza o cliente Laprotec
    cliente = ClienteFornecedor.objects.filter(cnpj_cpf__icontains='09027059').first()
    if not cliente:
        raise ValueError("Cliente LAPROTEC não encontrado no banco de dados!")
    print(f"[OK] Cliente encontrado: #{cliente.id} - {cliente.nome_razao} (CNPJ: {cliente.cnpj_cpf})")

    # 2. Localiza a regra de pagamento PIX à vista
    regra_pix = RegraPagamento.objects.filter(id=1, deleted_at__isnull=True).first()
    if not regra_pix or 'PIX' not in regra_pix.nome.upper():
        regra_pix = RegraPagamento.objects.filter(nome__icontains='PIX', deleted_at__isnull=True).first()
    print(f"[OK] Regra de Pagamento: #{regra_pix.id} - {regra_pix.nome} (Desconto padrão: {regra_pix.desconto_concedido_padrao}%)")

    # 3. Cria o Orçamento
    data_teste = date(2026, 8, 3)
    data_validade = date(2026, 8, 18)

    orcamento = Orcamento.objects.create(
        cliente=cliente,
        equipamento=None,
        data_geracao=data_teste,
        data_validade=data_validade,
        status_operacional='CONCLUIDO',
        status_financeiro='A_FATURAR',
        valor_bruto=Decimal('210.53'),
        valor_desconto_aplicado=Decimal('0.00')
    )
    print(f"[OK] Orçamento #{orcamento.id} criado com sucesso (Data: {data_teste}, Status: {orcamento.status_operacional})")

    # 4. Cria o Item Avulso do Orçamento
    item = OrcamentoItem.objects.create(
        orcamento=orcamento,
        produto=None,
        item=None,
        descricao_livre='SERVICO DE TESTE',
        quantidade=Decimal('1.0000'),
        custo_snapshot=Decimal('170.00'),
        valor_venda_snapshot=Decimal('210.53')
    )
    print(f"[OK] Item criado: '{item.descricao_livre}' - Qtd: {item.quantidade}, Custo: R$ {item.custo_snapshot}, Venda: R$ {item.valor_venda_snapshot}")

    # 5. Cria a Pré-Fatura (Rascunho)
    fatura_pre = criar_pre_fatura(
        cliente_id=cliente.id,
        orcamento_ids=[orcamento.id],
        propostas_pagamento=[{
            'regra_pagamento': regra_pix,
            'desconto_personalizado': Decimal('5.00')
        }],
        desconto_global=Decimal('10.53')
    )
    # Ajusta data_emissao para 03/08/2026
    fatura_pre.data_emissao = data_teste
    fatura_pre.save(update_fields=['data_emissao'])
    print(f"[OK] Pré-Fatura #{fatura_pre.id} criada em Rascunho.")

    # 6. Converte em Fatura Definitiva (Faturar)
    fatura_final = faturar_rascunho(
        fatura=fatura_pre,
        regra_pagamento_id=regra_pix.id,
        desconto_global=Decimal('10.53')
    )
    # Ajusta data_fechamento e data_emissao para 03/08/2026
    fatura_final.data_emissao = data_teste
    fatura_final.data_fechamento = data_teste
    fatura_final.save(update_fields=['data_emissao', 'data_fechamento'])

    # 7. Ajusta vencimento das parcelas geradas no Contas a Receber para 03/08/2026
    parcelas = fatura_final.lancamentos_financeiros.filter(tipo_lancamento='ENTRADA', deleted_at__isnull=True)
    for p in parcelas:
        p.data_vencimento = data_teste
        p.save(update_fields=['data_vencimento'])
        print(f"[OK] Lançamento a Receber #{p.id} gerado: R$ {p.valor} com vencimento em {p.data_vencimento} (Status: {p.status_pagamento}, Conciliado: {p.is_conciliado})")

    # 8. Atualiza orçamento
    orcamento.refresh_from_db()
    print(f"[OK] Orçamento #{orcamento.id} atualizado: Status Operacional={orcamento.status_operacional}, Status Financeiro={orcamento.status_financeiro}, Fatura=#{orcamento.fatura_id}")
    print(f"[OK] Fatura #{fatura_final.id} finalizada: Valor Total Faturado=R$ {fatura_final.valor_total_faturado}, Status={fatura_final.status}")

    print("\n=== REGISTROS CRIADOS COM SUCESSO! PRONTO PARA TESTE DE CONCILIAÇÃO ===")

if __name__ == '__main__':
    run()
