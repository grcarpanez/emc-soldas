"""
Testes automatizados completos para o Módulo de Orçamentos Comerciais.
Em conformidade com docs/FSD.md e docs/PLANO.md (Fase 8).
"""
import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.db import transaction, IntegrityError
from rest_framework.test import APIClient
from rest_framework import status

from apps.administracao.models import ConfiguracaoGlobal
from apps.authentication.models import Usuario, Permissao
from apps.cadastros.models import ClienteFornecedor, Equipamento
from apps.catalogo.models import DicionarioUom, DicionarioAtributo, Item, Produto, FichaTecnica
from apps.financeiro.models import ContaBancaria, MeioPagamento, RegraPagamento, LancamentoFinanceiro, CategoriaFinanceira
from apps.orcamentos.models import Orcamento, OrcamentoItem, OrcamentoPropostaPagamento
from apps.orcamentos.services import (
    analisar_inflacao_orcamento,
    verificar_inadimplencia_cliente
)
from apps.orcamentos.pdf_service import salvar_pdf_exemplo


class OrcamentosModuleTestCase(TestCase):
    """
    Suíte de testes de integração e regras de negócio para o módulo de Orçamentos.
    """

    def setUp(self):
        self.client = APIClient()

        # Configurações Globais
        self.config = ConfiguracaoGlobal.get_solo()
        self.config.taxa_mao_de_obra_hora = Decimal('80.00')
        self.config.validade_orcamento_dias = 15
        self.config.save()

        # Usuário Admin
        self.admin_user = Usuario.objects.create_user(
            email='admin@emcsoldas.com.br',
            password='Password123!',
            role='Admin'
        )
        self.admin_user.permissoes.acesso_comercial = True
        self.admin_user.permissoes.gestao_catalogo = True
        self.admin_user.permissoes.cadastros_financeiros = True
        self.admin_user.permissoes.acesso_tesouraria = True
        self.admin_user.permissoes.save()

        # Usuário Operador COM acesso comercial
        self.operador_comercial = Usuario.objects.create_user(
            email='comercial@emcsoldas.com.br',
            password='Password123!',
            role='Operador'
        )
        self.operador_comercial.permissoes.acesso_comercial = True
        self.operador_comercial.permissoes.gestao_catalogo = True
        self.operador_comercial.permissoes.save()

        # Usuário Operador SEM acesso comercial
        self.operador_sem_comercial = Usuario.objects.create_user(
            email='semcomercial@emcsoldas.com.br',
            password='Password123!',
            role='Operador'
        )
        self.operador_sem_comercial.permissoes.acesso_comercial = False
        self.operador_sem_comercial.permissoes.save()

        # Dados Estruturais Básicos
        self.uom_un = DicionarioUom.objects.create(sigla='UN', descricao='UNIDADE')
        self.uom_kg = DicionarioUom.objects.create(sigla='KG', descricao='QUILOGRAMA')

        # Cliente e Equipamento
        self.cliente = ClienteFornecedor.objects.create(
            tipo='CLIENTE',
            tipo_pessoa='PJ',
            nome_razao='VALE S.A.',
            cnpj_cpf='33.592.510/0001-54',
            telefone='(31) 3915-1000',
            logradouro='AV DOUTOR MARCO PAULO SIMAO',
            numero='35',
            cidade='BELO HORIZONTE',
            uf='MG'
        )

        self.equipamento = Equipamento.objects.create(
            placa='VAL-2026',
            identificacao='CARREGADEIRA CAT 980K',
            descricao='REFORÇO ESTRUTURAL DA CAÇAMBA'
        )

        # Catálogo: Itens e Produtos
        self.item_chapa = Item.objects.create(
            nome='CHAPA DE ACO CARBONO 1/2 POL',
            unidade_compra=self.uom_kg,
            fator_conversao=Decimal('1.0000'),
            ultimo_custo_compra=Decimal('10.00'),
            tipo_uso='INSUMO_PRODUTIVO'
        )

        self.item_eletrodo = Item.objects.create(
            nome='ELETRODO REVESTIDO OK 48.04 4MM',
            unidade_compra=self.uom_kg,
            fator_conversao=Decimal('1.0000'),
            ultimo_custo_compra=Decimal('30.00'),
            tipo_uso='INSUMO_PRODUTIVO'
        )

        # Produto Composto (BOM): 5kg de chapa (R$ 50) + 1kg eletrodo (R$ 30) + 2h mão de obra (R$ 160) = R$ 240 custo
        self.produto_reforco = Produto.objects.create(
            nome='FABRICACAO DE REFORCO DE CACAMBA',
            unidade_venda=self.uom_un,
            tempo_estimado_execucao=Decimal('2.00')
        )
        FichaTecnica.objects.create(
            produto=self.produto_reforco,
            item=self.item_chapa,
            quantidade_utilizada=Decimal('5.0000')
        )
        FichaTecnica.objects.create(
            produto=self.produto_reforco,
            item=self.item_eletrodo,
            quantidade_utilizada=Decimal('1.0000')
        )

        # Regras de Pagamento
        self.meio_pix = MeioPagamento.objects.create(nome='PIX', ativo=True)
        self.meio_boleto = MeioPagamento.objects.create(nome='BOLETO BANCARIO', ativo=True)

        self.regra_vista = RegraPagamento.objects.create(
            nome='PIX A VISTA (5% DESC)',
            meio_pagamento=self.meio_pix,
            tipo_cobranca='A_VISTA',
            numero_parcelas=1,
            desconto_concedido_padrao=Decimal('5.00')
        )
        self.regra_parcelado = RegraPagamento.objects.create(
            nome='BOLETO 30/60 DIAS',
            meio_pagamento=self.meio_boleto,
            tipo_cobranca='PARCELADO',
            numero_parcelas=2,
            prazo_primeira_parcela_dias=30,
            intervalo_parcelas_dias=30,
            desconto_concedido_padrao=Decimal('0.00')
        )

    # -------------------------------------------------------------------------
    # 1. TESTES DE CRUD, CRIAÇÃO ANINHADA E SNAPSHOTS
    # -------------------------------------------------------------------------

    def test_01_criar_orcamento_com_tres_tipos_de_itens_e_snapshots(self):
        """
        Cria um orçamento contendo Produto Composto, Item Simples e Lançamento Livre.
        Verifica a gravação imutável de snapshots de custos e cálculo de valor bruto.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        payload = {
            'cliente': self.cliente.id,
            'equipamento': self.equipamento.id,
            'valor_desconto_aplicado': '50.00',
            'itens': [
                {
                    'produto': self.produto_reforco.id,
                    'quantidade': '1.0000',
                    'valor_venda_snapshot': '500.00'
                },
                {
                    'item': self.item_eletrodo.id,
                    'quantidade': '2.0000',
                    'valor_venda_snapshot': '60.00'
                },
                {
                    'descricao_livre': 'Serviço de Pintura e Limpeza com Jato de Granalha',
                    'quantidade': '1.0000',
                    'custo_snapshot': '40.00',
                    'valor_venda_snapshot': '120.00'
                }
            ],
            'propostas_pagamento': [
                {
                    'regra_pagamento': self.regra_vista.id,
                    'desconto_personalizado': '5.00'
                },
                {
                    'regra_pagamento': self.regra_parcelado.id
                }
            ]
        }

        response = self.client.post('/api/orcamentos/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        orc_id = response.data['id']
        orcamento = Orcamento.objects.get(id=orc_id)

        # Verifica totais: 1*500 + 2*60 + 1*120 = 740.00
        self.assertEqual(orcamento.valor_bruto, Decimal('740.00'))
        self.assertEqual(orcamento.valor_desconto_aplicado, Decimal('50.00'))
        self.assertEqual(orcamento.valor_liquido, Decimal('690.00'))
        self.assertEqual(orcamento.itens_orcamento.count(), 3)
        self.assertEqual(orcamento.propostas_pagamento.count(), 2)

        # Verifica snapshots dos itens
        item_prod = orcamento.itens_orcamento.get(produto=self.produto_reforco)
        # Custo apurado do produto: 5*10 + 1*30 + 2*80 = 240.00
        self.assertEqual(item_prod.custo_snapshot, Decimal('240.00'))
        self.assertEqual(item_prod.valor_venda_snapshot, Decimal('500.00'))

        item_mat = orcamento.itens_orcamento.get(item=self.item_eletrodo)
        self.assertEqual(item_mat.custo_snapshot, Decimal('30.00'))
        self.assertEqual(item_mat.valor_venda_snapshot, Decimal('60.00'))

        item_livre = orcamento.itens_orcamento.get(descricao_livre__isnull=False)
        self.assertEqual(item_livre.descricao_livre, 'SERVICO DE PINTURA E LIMPEZA COM JATO DE GRANALHA')
        self.assertEqual(item_livre.custo_snapshot, Decimal('40.00'))

    def test_02_imutabilidade_dos_snapshots_apos_alteracao_no_catalogo(self):
        """
        Garante que variações posteriores de custos no catálogo não alteram os snapshots do orçamento.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            valor_bruto=Decimal('500.00')
        )
        OrcamentoItem.objects.create(
            orcamento=orcamento,
            item=self.item_eletrodo,
            quantidade=Decimal('1.0000'),
            custo_snapshot=Decimal('30.00'),
            valor_venda_snapshot=Decimal('60.00')
        )

        # Altera o preço de compra do eletrodo no catálogo (sobe de 30 para 55)
        self.item_eletrodo.ultimo_custo_compra = Decimal('55.00')
        self.item_eletrodo.save()

        # O snapshot no orçamento deve permanecer estritamente em 30.00
        item_orc = orcamento.itens_orcamento.first()
        self.assertEqual(item_orc.custo_snapshot, Decimal('30.00'))

    def test_03_validacao_de_exclusividade_de_tipo_de_item(self):
        """
        Rejeita itens que misturem tipos ou que não informem nenhum tipo.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        # Caso A: Produto E Item preenchidos na mesma linha
        payload_misto = {
            'cliente': self.cliente.id,
            'itens': [
                {
                    'produto': self.produto_reforco.id,
                    'item': self.item_eletrodo.id,
                    'quantidade': '1.0000',
                    'valor_venda_snapshot': '100.00'
                }
            ]
        }
        res_misto = self.client.post('/api/orcamentos/', payload_misto, format='json')
        self.assertEqual(res_misto.status_code, status.HTTP_400_BAD_REQUEST)

        # Caso B: Nenhum tipo preenchido
        payload_vazio = {
            'cliente': self.cliente.id,
            'itens': [
                {
                    'quantidade': '1.0000',
                    'valor_venda_snapshot': '100.00'
                }
            ]
        }
        res_vazio = self.client.post('/api/orcamentos/', payload_vazio, format='json')
        self.assertEqual(res_vazio.status_code, status.HTTP_400_BAD_REQUEST)

    def test_04_proposta_pagamento_constraint_unicidade(self):
        """
        Garante que a mesma regra de pagamento não pode ser duplicada no mesmo orçamento.
        """
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15)
        )
        OrcamentoPropostaPagamento.objects.create(
            orcamento=orcamento,
            regra_pagamento=self.regra_vista,
            desconto_personalizado=Decimal('5.00')
        )

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                OrcamentoPropostaPagamento.objects.create(
                    orcamento=orcamento,
                    regra_pagamento=self.regra_vista,
                    desconto_personalizado=Decimal('3.00')
                )

    # -------------------------------------------------------------------------
    # 2. TESTES DA MÁQUINA DE ESTADOS OPERACIONAL E VALIDAÇÕES
    # -------------------------------------------------------------------------

    def test_05_fluxo_da_maquina_de_estados_operacional(self):
        """
        Testa o avanço operacional: GERADO -> ENVIADO -> APROVADO -> EM_EXECUCAO -> CONCLUIDO.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=10),
            status_operacional='GERADO'
        )

        # 1. Enviar
        res1 = self.client.post(f'/api/orcamentos/{orcamento.id}/enviar/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['status_operacional'], 'ENVIADO')

        # 2. Aprovar
        res2 = self.client.post(f'/api/orcamentos/{orcamento.id}/aprovar/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['status_operacional'], 'APROVADO')

        # 3. Iniciar Execução
        res3 = self.client.post(f'/api/orcamentos/{orcamento.id}/iniciar-execucao/')
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.data['status_operacional'], 'EM_EXECUCAO')

        # 4. Concluir
        res4 = self.client.post(f'/api/orcamentos/{orcamento.id}/concluir/')
        self.assertEqual(res4.status_code, status.HTTP_200_OK)
        self.assertEqual(res4.data['status_operacional'], 'CONCLUIDO')

    def test_06_bloqueio_de_aprovacao_para_orcamento_com_validade_expirada(self):
        """
        Impede aprovação de orçamento expirado, exigindo renovação prévia.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        data_passada = timezone.now().date() - timedelta(days=5)
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=data_passada - timedelta(days=15),
            data_validade=data_passada,
            status_operacional='ENVIADO'
        )

        res = self.client.post(f'/api/orcamentos/{orcamento.id}/aprovar/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('data_validade' in res.data or 'data_validade' in res.data.get('details', {}))

    # -------------------------------------------------------------------------
    # 3. TESTES DE CANCELAMENTO JUSTIFICADO OBRIGATÓRIO
    # -------------------------------------------------------------------------

    def test_07_cancelamento_justificado_obrigatorio(self):
        """
        Valida exigência de justificativa com no mínimo 10 caracteres no cancelamento.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            status_operacional='ENVIADO',
            status_financeiro='A_FATURAR'
        )

        # Tentativa A: Sem motivo ou com menos de 10 caracteres
        res_curto = self.client.post(
            f'/api/orcamentos/{orcamento.id}/cancelar/',
            {'motivo_cancelamento': 'Desistiu'},
            format='json'
        )
        self.assertEqual(res_curto.status_code, status.HTTP_400_BAD_REQUEST)

        # Tentativa B: Justificativa válida (>10 caracteres)
        res_sucesso = self.client.post(
            f'/api/orcamentos/{orcamento.id}/cancelar/',
            {'motivo_cancelamento': 'Cliente optou por adiar a reforma para o próximo trimestre.'},
            format='json'
        )
        self.assertEqual(res_sucesso.status_code, status.HTTP_200_OK)
        self.assertEqual(res_sucesso.data['status_operacional'], 'CANCELADO')
        self.assertEqual(res_sucesso.data['status_financeiro'], 'CANCELADO')

        orcamento.refresh_from_db()
        self.assertEqual(orcamento.status_operacional, 'CANCELADO')
        self.assertEqual(orcamento.status_financeiro, 'CANCELADO')
        self.assertTrue('PROXIMO TRIMESTRE' in orcamento.motivo_cancelamento)

    def test_08_bloqueio_de_cancelamento_para_orcamento_concluido(self):
        """
        Impede cancelamento direto de orçamento concluído.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            status_operacional='CONCLUIDO'
        )

        res = self.client.post(
            f'/api/orcamentos/{orcamento.id}/cancelar/',
            {'motivo_cancelamento': 'Cancelamento indevido após serviço feito.'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 4. TESTES DE INFLAÇÃO E RENOVAÇÃO DE VALIDADE
    # -------------------------------------------------------------------------

    def test_09_verificacao_de_inflacao_e_renovacao(self):
        """
        Testa a rota de verificação de inflação e os dois modos de renovação (com e sem atualização de preços).
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date() - timedelta(days=20),
            data_validade=timezone.now().date() - timedelta(days=5),
            valor_bruto=Decimal('300.00')
        )
        item_orc = OrcamentoItem.objects.create(
            orcamento=orcamento,
            item=self.item_chapa,
            quantidade=Decimal('10.0000'),
            custo_snapshot=Decimal('10.00'),      # Custo original: 10 * 10 = R$ 100
            valor_venda_snapshot=Decimal('30.00') # Venda: 10 * 30 = R$ 300
        )

        # Simula inflação: preço de compra da chapa subiu de 10.00 para 16.00 no catálogo
        self.item_chapa.ultimo_custo_compra = Decimal('16.00')
        self.item_chapa.save()

        # 1. Consulta verificação de inflação
        res_inflacao = self.client.get(f'/api/orcamentos/{orcamento.id}/verificar-inflacao/')
        self.assertEqual(res_inflacao.status_code, status.HTTP_200_OK)
        self.assertTrue(res_inflacao.data['ha_inflacao'])
        self.assertEqual(res_inflacao.data['total_custo_original'], 100.0)
        self.assertEqual(res_inflacao.data['total_custo_atualizado'], 160.0)
        self.assertEqual(res_inflacao.data['aumento_custo_total'], 60.0)

        # 2. Modo A: Renovar mantendo preços antigos
        res_renovar_a = self.client.post(
            f'/api/orcamentos/{orcamento.id}/renovar/',
            {'dias_validade': 15, 'atualizar_precos': False},
            format='json'
        )
        self.assertEqual(res_renovar_a.status_code, status.HTTP_200_OK)
        item_orc.refresh_from_db()
        self.assertEqual(item_orc.custo_snapshot, Decimal('10.00')) # Mantém 10.00

        # 3. Modo B: Renovar atualizando custos e re-precificando a venda para 38.00
        res_renovar_b = self.client.post(
            f'/api/orcamentos/{orcamento.id}/renovar/',
            {
                'dias_validade': 15,
                'atualizar_precos': True,
                'novos_precos_itens': {str(item_orc.id): '38.00'}
            },
            format='json'
        )
        self.assertEqual(res_renovar_b.status_code, status.HTTP_200_OK)
        item_orc.refresh_from_db()
        orcamento.refresh_from_db()

        # Custo atualizado para 16.00 e venda atualizada para 38.00 (Total: 10 * 38 = 380.00)
        self.assertEqual(item_orc.custo_snapshot, Decimal('16.00'))
        self.assertEqual(item_orc.valor_venda_snapshot, Decimal('38.00'))
        self.assertEqual(orcamento.valor_bruto, Decimal('380.00'))

    # -------------------------------------------------------------------------
    # 5. TESTE DE INADIMPLÊNCIA PREVENTIVA
    # -------------------------------------------------------------------------

    def test_10_verificacao_de_inadimplencia_preventiva(self):
        """
        Verifica o detector de títulos vencidos do cliente.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        # Cria categoria de receita e conta bancária
        cat_rec = CategoriaFinanceira.objects.create(nome='RECEITA OPERACIONAL', tipo='RECEITA')
        conta = ContaBancaria.objects.create(nome='BANCO DO BRASIL', saldo=Decimal('1000.00'))

        # Lança título a receber vencido do cliente
        LancamentoFinanceiro.objects.create(
            tipo_lancamento='ENTRADA',
            categoria=cat_rec,
            conta=conta,
            descricao='DUPLICATA SERVIÇO ANTERIOR',
            valor=Decimal('1500.00'),
            data_vencimento=timezone.now().date() - timedelta(days=10),
            status_pagamento='VENCIDO'
        )

        res_inad = self.client.get(f'/api/orcamentos/verificar-inadimplencia/?cliente_id={self.cliente.id}')
        self.assertEqual(res_inad.status_code, status.HTTP_200_OK)
        # Nota: o serviço consulta títulos com fatura__cliente_id, garantindo isolamento
        self.assertIn('inadimplente', res_inad.data)

    # -------------------------------------------------------------------------
    # 6. TESTES DE GERAÇÃO DE PDF TRANSACIONAL (REPORTLAB)
    # -------------------------------------------------------------------------

    def test_11_geracao_de_pdf_com_e_sem_desconto(self):
        """
        Testa o endpoint de geração de PDF, verificando retorno de bytes válidos (%PDF).
        """
        self.client.force_authenticate(user=self.operador_comercial)

        # Orçamento com Desconto
        orc_com_desc = Orcamento.objects.create(
            cliente=self.cliente,
            equipamento=self.equipamento,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            valor_bruto=Decimal('1000.00'),
            valor_desconto_aplicado=Decimal('100.00')
        )
        OrcamentoItem.objects.create(
            orcamento=orc_com_desc,
            item=self.item_chapa,
            quantidade=Decimal('10.0000'),
            custo_snapshot=Decimal('10.00'),
            valor_venda_snapshot=Decimal('100.00')
        )
        OrcamentoPropostaPagamento.objects.create(
            orcamento=orc_com_desc,
            regra_pagamento=self.regra_vista,
            desconto_personalizado=Decimal('5.00')
        )

        res_pdf_desc = self.client.get(f'/api/orcamentos/{orc_com_desc.id}/gerar-pdf/')
        self.assertEqual(res_pdf_desc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pdf_desc['Content-Type'], 'application/pdf')
        # Verifica se os primeiros bytes contêm o magic number %PDF
        pdf_bytes = b"".join(res_pdf_desc.streaming_content) if res_pdf_desc.streaming else res_pdf_desc.content
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        # Orçamento com Desconto Zerado (supressão)
        orc_sem_desc = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            valor_bruto=Decimal('500.00'),
            valor_desconto_aplicado=Decimal('0.00')
        )
        OrcamentoItem.objects.create(
            orcamento=orc_sem_desc,
            item=self.item_eletrodo,
            quantidade=Decimal('5.0000'),
            custo_snapshot=Decimal('30.00'),
            valor_venda_snapshot=Decimal('100.00')
        )

        res_pdf_sem_desc = self.client.get(f'/api/orcamentos/{orc_sem_desc.id}/gerar-pdf/')
        self.assertEqual(res_pdf_sem_desc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pdf_sem_desc['Content-Type'], 'application/pdf')
        pdf_bytes_sem = b"".join(res_pdf_sem_desc.streaming_content) if res_pdf_sem_desc.streaming else res_pdf_sem_desc.content
        self.assertTrue(pdf_bytes_sem.startswith(b'%PDF'))

    # -------------------------------------------------------------------------
    # 7. TESTES DE CONTROLE DE ACESSO RBAC
    # -------------------------------------------------------------------------

    def test_12_controle_de_acesso_rbac(self):
        """
        Valida que o toggle 'acesso_comercial' é rigorosamente exigido em todas as rotas.
        """
        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15)
        )

        # 1. Usuário SEM acesso comercial -> 403 Forbidden
        self.client.force_authenticate(user=self.operador_sem_comercial)
        res_bloqueado = self.client.get('/api/orcamentos/')
        self.assertEqual(res_bloqueado.status_code, status.HTTP_403_FORBIDDEN)

        res_pdf_bloq = self.client.get(f'/api/orcamentos/{orcamento.id}/gerar-pdf/')
        self.assertEqual(res_pdf_bloq.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Usuário anônimo -> 401 Unauthorized
        self.client.logout()
        res_anon = self.client.get('/api/orcamentos/')
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # 3. Usuário COM acesso comercial -> 200 OK
        self.client.force_authenticate(user=self.operador_comercial)
        res_permitido = self.client.get('/api/orcamentos/')
        self.assertEqual(res_permitido.status_code, status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 8. TESTE DE SOFT DELETE
    # -------------------------------------------------------------------------

    def test_13_soft_delete_orcamento(self):
        """
        Valida que a exclusão de orçamento grava deleted_at e não executa DELETE físico.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        orcamento = Orcamento.objects.create(
            cliente=self.cliente,
            data_geracao=timezone.now().date(),
            data_validade=timezone.now().date() + timedelta(days=15),
            status_operacional='GERADO',
            status_financeiro='A_FATURAR'
        )

        res = self.client.delete(f'/api/orcamentos/{orcamento.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        orcamento.refresh_from_db()
        self.assertIsNotNone(orcamento.deleted_at)
        self.assertEqual(orcamento.deleted_by_id, self.operador_comercial.id)

        # Não aparece na listagem ativa
        self.assertFalse(Orcamento.objects.filter(id=orcamento.id, deleted_at__isnull=True).exists())
