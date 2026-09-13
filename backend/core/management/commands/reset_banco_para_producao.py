from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction, connection

from apps.financeiro.models import LancamentoFinanceiro, ContaBancaria
from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem
from apps.catalogo.models import Produto, Item, FichaTecnica, ItemAtributoValor
from apps.cadastros.models import ClienteFornecedor, ClienteContato, Equipamento, ClienteEquipamento


class Command(BaseCommand):
    help = "Reseta os dados operacionais e transacionais para início de produção com dados reais."

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão definitiva dos dados transacionais e de teste.',
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.ERROR(
                    "ATENCAO: Este comando apagara todos os dados transacionais e cadastrais de teste.\n"
                    "Execute com --confirmar para prosseguir."
                )
            )
            return

        self.stdout.write(self.style.WARNING("Iniciando limpeza dos dados operacionais..."))

        with transaction.atomic():
            # 1. Financeiro transacional
            total_lanc = LancamentoFinanceiro.all_objects.all().delete()[0]
            self.stdout.write(f"- LancamentoFinanceiro removidos: {total_lanc}")

            # 2. Faturamento
            total_prop = FaturaPropostaPagamento.objects.all().delete()[0]
            total_fat = Fatura.all_objects.all().delete()[0]
            self.stdout.write(f"- Faturas removidas: {total_fat}, Propostas: {total_prop}")

            # 3. Orcamentos
            total_orc_itens = OrcamentoItem.objects.all().delete()[0]
            total_orc_prop = OrcamentoPropostaPagamento.objects.all().delete()[0]
            total_orc = Orcamento.all_objects.all().delete()[0]
            self.stdout.write(f"- Orcamentos removidos: {total_orc} (Itens: {total_orc_itens}, Propostas: {total_orc_prop})")

            # 4. Compras / NFe
            total_nfe_itens = NotaCompraItem.objects.all().delete()[0]
            total_nfe = DocumentoFiscalCompra.all_objects.all().delete()[0]
            self.stdout.write(f"- Documentos de Compra removidos: {total_nfe} (Itens: {total_nfe_itens})")

            # 5. Catalogo (Produtos e Itens/Insumos)
            total_ficha = FichaTecnica.objects.all().delete()[0]
            total_prod = Produto.all_objects.all().delete()[0]
            total_item_attr = ItemAtributoValor.objects.all().delete()[0]
            total_item = Item.all_objects.all().delete()[0]
            self.stdout.write(f"- Catalogo limpo (Produtos: {total_prod}, Itens: {total_item}, Fichas: {total_ficha}, Atrib: {total_item_attr})")

            # 6. Equipamentos e Contatos
            total_cli_eq = ClienteEquipamento.objects.all().delete()[0]
            total_eq = Equipamento.all_objects.all().delete()[0]
            total_cont = ClienteContato.objects.all().delete()[0]
            self.stdout.write(f"- Equipamentos removidos: {total_eq}, Vinculos: {total_cli_eq}, Contatos: {total_cont}")

            # 7. Clientes e Fornecedores
            total_cli_forn = ClienteFornecedor.all_objects.all().delete()[0]
            self.stdout.write(f"- Clientes e Fornecedores removidos: {total_cli_forn}")

            # 8. Contas Bancarias (manter apenas as estruturais com saldo 0)
            contas_padrao = ['CAIXA FISICO DA OFICINA', 'CONTA BANCARIA PRINCIPAL']
            total_contas_extras = ContaBancaria.all_objects.exclude(nome__in=contas_padrao).delete()[0]
            self.stdout.write(f"- Contas bancarias extras removidas: {total_contas_extras}")

            for conta in ContaBancaria.all_objects.all():
                conta.saldo = 0.00
                conta.deleted_at = None
                conta.save(update_fields=['saldo', 'deleted_at'])
            self.stdout.write("- Contas bancarias padrao preservadas e saldo zerado para R$ 0,00.")

            # 9. Reset dos contadores de ID (AUTO_INCREMENT = 1) nas tabelas operacionais esvaziadas
            tabelas_reset_id = [
                'clientes_fornecedores',
                'clientes_contatos',
                'equipamentos',
                'cliente_equipamento',
                'itens',
                'item_atributos_valores',
                'produtos',
                'ficha_tecnica',
                'orcamentos',
                'orcamento_itens',
                'orcamento_propostas_pagamento',
                'faturas',
                'fatura_propostas_pagamento',
                'lancamentos_financeiros',
                'documentos_fiscais_compra',
                'nota_compra_itens',
            ]
            with connection.cursor() as cursor:
                for tabela in tabelas_reset_id:
                    try:
                        cursor.execute(f"ALTER TABLE `{tabela}` AUTO_INCREMENT = 1;")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Aviso ao resetar AUTO_INCREMENT de {tabela}: {e}"))
            self.stdout.write(self.style.SUCCESS("- Contadores AUTO_INCREMENT das tabelas operacionais reiniciados em 1."))

        self.stdout.write(self.style.SUCCESS("Dados transacionais expurgados com sucesso!"))
        self.stdout.write("Garantindo integridade dos dados mestres com seed_initial_data...")
        call_command('seed_initial_data')
        self.stdout.write(self.style.SUCCESS("Ambiente preparado para dados reais com sucesso!"))
