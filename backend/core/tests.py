"""
Bateria de Testes Automatizados para a Fase 2:
Validação dos Modelos ORM (29 Entidades), Soft Delete, Constraints e Seeders.
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.core.management import call_command

from apps.authentication.models import Usuario, Permissao
from apps.cadastros.models import ClienteFornecedor, Equipamento, ClienteEquipamento, AnexoGeralCliente
from apps.catalogo.models import DicionarioUom, DicionarioAtributo, Item, ItemAtributoValor, Produto, FichaTecnica
from apps.compras.models import DocumentoFiscalCompra, NotaCompraItem
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento
from apps.faturamento.models import Fatura, FaturaPropostaPagamento
from apps.financeiro.models import (
    ContaBancaria,
    CartaoCredito,
    FaturaCartao,
    CategoriaFinanceira,
    MeioPagamento,
    RegraPagamento,
    LancamentoFinanceiro,
    LogEstorno,
)
from apps.administracao.models import ConfiguracaoGlobal, ControleArquivoLog


class ModelosFase2TestCase(TestCase):
    """
    Testes de integridade, constraints, soft delete e auditoria para as 29 entidades.
    """

    def setUp(self):
        # Usuário base para auditoria
        self.user = Usuario.objects.create(
            email="test@emcsoldas.com.br",
            nome="Tester Silva",
            role="Admin"
        )
        self.perm = Permissao.objects.create(
            usuario=self.user,
            acesso_comercial=True,
            acesso_tesouraria=True
        )

    def test_01_soft_delete_e_auditoria(self):
        """Valida que soft delete oculta registros da consulta padrão e permite restauração."""
        uom = DicionarioUom.objects.create(sigla="UN", descricao="Unidade")
        self.assertFalse(uom.is_deleted)
        self.assertEqual(DicionarioUom.objects.count(), 1)

        # Aplica soft delete
        uom.delete(user_id=self.user.id)
        self.assertTrue(uom.is_deleted)
        self.assertIsNotNone(uom.deleted_at)
        self.assertEqual(uom.deleted_by_id, self.user.id)

        # Consulta padrão não retorna o item deletado
        self.assertEqual(DicionarioUom.objects.count(), 0)
        # Consulta com with_deleted ou only_deleted encontra
        self.assertEqual(DicionarioUom.objects.with_deleted().count(), 1)
        self.assertEqual(DicionarioUom.objects.only_deleted().count(), 1)

        # Restaura da Lixeira
        uom.restore()
        self.assertFalse(uom.is_deleted)
        self.assertIsNone(uom.deleted_at)
        self.assertEqual(DicionarioUom.objects.count(), 1)

    def test_02_cadastros_cliente_fornecedor_equipamento(self):
        """Valida criação de clientes, equipamentos e histórico relacional de vínculos."""
        cliente = ClienteFornecedor.objects.create(
            tipo="Cliente",
            tipo_pessoa="PJ",
            nome_razao="Oficina Mecânica Alpha LTDA",
            cnpj_cpf="12.345.678/0001-00",
            telefone="(11) 98888-7777"
        )
        self.assertEqual(cliente.nome_razao, "Oficina Mecânica Alpha LTDA")

        equip = Equipamento.objects.create(
            identificacao_placa="ABC-1234",
            descricao="Torno Mecânico Industrial 2000W"
        )
        self.assertEqual(equip.identificacao_placa, "ABC-1234")

        vinculo = ClienteEquipamento.objects.create(
            cliente=cliente,
            equipamento=equip,
            is_ativo=True
        )
        self.assertTrue(vinculo.is_ativo)

        anexo = AnexoGeralCliente.objects.create(
            cliente=cliente,
            nome_documento="Contrato Social",
            caminho_arquivo="/media/anexos/contrato.pdf"
        )
        self.assertEqual(anexo.nome_documento, "Contrato Social")

    def test_03_catalogo_bom_e_constraints(self):
        """Valida catálogo de materiais, sub-grid de atributos, produtos e Ficha Técnica (BOM)."""
        uom_un = DicionarioUom.objects.create(sigla="UN", descricao="Unidade")
        uom_kg = DicionarioUom.objects.create(sigla="kg", descricao="Quilograma")
        attr_esp = DicionarioAtributo.objects.create(nome_atributo="Espessura")

        item = Item.objects.create(
            nome="Chapa de Aço Carbono 1020",
            unidade_compra=uom_un,
            unidade_consumo=uom_kg,
            fator_conversao=Decimal('10.0000'),
            ultimo_custo_compra=Decimal('150.00'),
            tipo_uso="Insumo Produtivo"
        )

        item_attr = ItemAtributoValor.objects.create(
            item=item,
            atributo=attr_esp,
            valor="6.35 mm (1/4 pol)"
        )
        self.assertEqual(item_attr.valor, "6.35 mm (1/4 pol)")

        # Teste de UniqueConstraint em ItemAtributoValor (não pode duplicar o mesmo atributo no mesmo item)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                ItemAtributoValor.objects.create(
                    item=item,
                    atributo=attr_esp,
                    valor="Outro Valor"
                )

        produto = Produto.objects.create(
            nome="Suporte Industrial Soldado Reforçado",
            unidade_venda=uom_un,
            tempo_estimado_execucao=Decimal('2.50')
        )

        ficha = FichaTecnica.objects.create(
            produto=produto,
            item=item,
            quantidade_utilizada=Decimal('3.5000')
        )
        self.assertEqual(ficha.quantidade_utilizada, Decimal('3.5000'))

        # Teste de UniqueConstraint em FichaTecnica (não pode duplicar item no mesmo produto)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                FichaTecnica.objects.create(
                    produto=produto,
                    item=item,
                    quantidade_utilizada=Decimal('1.0000')
                )

    def test_04_compras_e_nota_fiscal(self):
        """Valida notas fiscais de entrada e constraint de itens da nota."""
        fornecedor = ClienteFornecedor.objects.create(
            tipo="Fornecedor",
            tipo_pessoa="PJ",
            nome_razao="Aços & Soldas Distribuidora",
            telefone="(11) 91111-2222"
        )
        uom_un = DicionarioUom.objects.create(sigla="UN", descricao="Unidade")
        item = Item.objects.create(
            nome="Eletrodo OK 48.04",
            unidade_compra=uom_un,
            ultimo_custo_compra=Decimal('45.00')
        )

        nf = DocumentoFiscalCompra.objects.create(
            num_nota="NF-98765",
            fornecedor=fornecedor,
            data_compra=timezone.now().date(),
            valor_total=Decimal('450.00')
        )

        nota_item = NotaCompraItem.objects.create(
            documento_fiscal=nf,
            item=item,
            quantidade_comprada=Decimal('10.0000'),
            valor_unitario=Decimal('45.0000')
        )
        self.assertEqual(nota_item.quantidade_comprada, Decimal('10.0000'))

        # Constraint: mesmo item duplicado na mesma nota deve falhar
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                NotaCompraItem.objects.create(
                    documento_fiscal=nf,
                    item=item,
                    quantidade_comprada=Decimal('5.0000'),
                    valor_unitario=Decimal('45.0000')
                )

    def test_05_financeiro_estruturas_e_lancamentos(self):
        """Valida contas bancárias, cartões, categorias, regras e lançamentos."""
        conta = ContaBancaria.objects.create(
            nome="Banco Itaú CC",
            saldo=Decimal('5000.00'),
            limite_credito=Decimal('1000.00')
        )
        cartao = CartaoCredito.objects.create(
            nome="Nubank PJ",
            dia_vencimento=10,
            dia_fechamento_padrao=3,
            limite=Decimal('8000.00'),
            conta_bancaria=conta
        )
        fatura_cartao = FaturaCartao.objects.create(
            cartao=cartao,
            mes_referencia="2026-08",
            data_fechamento_real=timezone.now().date(),
            status="Aberta"
        )
        # Constraint de fatura de cartão duplicada no mesmo mês
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                FaturaCartao.objects.create(
                    cartao=cartao,
                    mes_referencia="2026-08",
                    data_fechamento_real=timezone.now().date(),
                    status="Aberta"
                )

        cat_rec = CategoriaFinanceira.objects.create(
            nome="Serviços de Solda",
            tipo="Receita"
        )
        meio_pix = MeioPagamento.objects.create(
            nome="PIX",
            permite_taxa_maquininha=False
        )
        regra_pix = RegraPagamento.objects.create(
            nome="Pix 5% Desc.",
            meio_pagamento=meio_pix,
            tipo_cobranca="A_VISTA",
            desconto_concedido_padrao=Decimal('5.00')
        )

        lanc = LancamentoFinanceiro.objects.create(
            conta=conta,
            meio_pagamento=meio_pix,
            categoria=cat_rec,
            tipo_lancamento="Entrada",
            descricao="Recebimento Serviço Solda Chassi",
            valor=Decimal('1200.00'),
            data_vencimento=timezone.now().date(),
            status_pagamento="A Vencer"
        )
        self.assertEqual(lanc.status_pagamento, "A Vencer")

        # Estorno
        estorno = LogEstorno.objects.create(
            lancamento=lanc,
            usuario=self.user,
            justificativa="Estorno por duplicidade de lançamento informada pelo cliente."
        )
        self.assertEqual(estorno.usuario.email, "test@emcsoldas.com.br")

    def test_06_orcamento_faturamento_e_cascata(self):
        """Valida orçamentos, faturamento e propostas de pagamento."""
        cliente = ClienteFornecedor.objects.create(
            tipo="Cliente",
            tipo_pessoa="PF",
            nome_razao="João da Silva",
            telefone="(11) 97777-6666"
        )
        meio_pix = MeioPagamento.objects.create(nome="PIX")
        regra_pix = RegraPagamento.objects.create(
            nome="Pix à Vista",
            meio_pagamento=meio_pix,
            tipo_cobranca="A_VISTA"
        )

        orc = Orcamento.objects.create(
            cliente=cliente,
            data_validade=timezone.now().date() + timezone.timedelta(days=15),
            status_operacional="Gerado",
            status_financeiro="A Faturar",
            valor_bruto=Decimal('850.00'),
            valor_desconto_aplicado=Decimal('50.00')
        )
        self.assertEqual(orc.valor_liquido, Decimal('800.00'))

        item_orc = OrcamentoItem.objects.create(
            orcamento=orc,
            descricao_livre="Soldagem Especial de Estrutura Metálica",
            quantidade=Decimal('1.0000'),
            custo_snapshot=Decimal('200.00'),
            valor_venda_snapshot=Decimal('850.00')
        )
        self.assertEqual(item_orc.custo_snapshot, Decimal('200.00'))

        prop_orc = OrcamentoPropostaPagamento.objects.create(
            orcamento=orc,
            regra_pagamento=regra_pix,
            desconto_personalizado=Decimal('7.00')
        )
        self.assertEqual(prop_orc.desconto_personalizado, Decimal('7.00'))

        # Constraint de proposta duplicada no orçamento
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                OrcamentoPropostaPagamento.objects.create(
                    orcamento=orc,
                    regra_pagamento=regra_pix
                )

        # Fatura
        fatura = Fatura.objects.create(
            cliente=cliente,
            status="Rascunho",
            valor_bruto=Decimal('850.00'),
            desconto_global=Decimal('50.00'),
            valor_total_faturado=Decimal('800.00')
        )
        prop_fat = FaturaPropostaPagamento.objects.create(
            fatura=fatura,
            regra_pagamento=regra_pix
        )
        self.assertEqual(prop_fat.fatura_id, fatura.id)

        # Constraint de proposta duplicada na fatura
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                FaturaPropostaPagamento.objects.create(
                    fatura=fatura,
                    regra_pagamento=regra_pix
                )

    def test_07_administracao_singleton_e_manifesto(self):
        """Valida Singleton de ConfiguracaoGlobal e manifesto de expurgo de logs."""
        config1 = ConfiguracaoGlobal.get_solo()
        config1.razao_social = "EMC Soldas Matriz"
        config1.validade_orcamento_dias = 20
        config1.save()
        self.assertEqual(config1.id, 1)

        # Acesso subsequente ao Singleton retorna a mesma instância
        config2 = ConfiguracaoGlobal.get_solo()
        self.assertEqual(config2.id, 1)
        self.assertEqual(config2.razao_social, "EMC Soldas Matriz")
        self.assertEqual(ConfiguracaoGlobal.objects.count(), 1)

        manifesto = ControleArquivoLog.objects.create(
            caminho_arquivo_fisico="/backend/logs/app-2026-08-18.log",
            data_criacao=timezone.now().date(),
            data_expurgo_planejada=timezone.now().date() + timezone.timedelta(days=30)
        )
        self.assertIn("app-2026-08-18.log", manifesto.caminho_arquivo_fisico)

    def test_08_comando_seeder_initial_data(self):
        """Valida execução completa do comando de management seed_initial_data."""
        call_command('seed_initial_data')
        self.assertGreater(DicionarioUom.objects.count(), 0)
        self.assertGreater(DicionarioAtributo.objects.count(), 0)
        self.assertGreater(MeioPagamento.objects.count(), 0)
        self.assertGreater(RegraPagamento.objects.count(), 0)
        self.assertGreater(CategoriaFinanceira.objects.count(), 0)
        self.assertGreater(ContaBancaria.objects.count(), 0)
        self.assertTrue(ConfiguracaoGlobal.objects.filter(id=1).exists())
        self.assertTrue(Usuario.objects.filter(email="admin@emcsoldas.com.br").exists())
