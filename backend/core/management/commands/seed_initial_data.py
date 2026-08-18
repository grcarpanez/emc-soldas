"""
Comando de Management do Django para popular a base de dados com sementes essenciais.
Executado via: python backend/manage.py seed_initial_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.authentication.models import Usuario, Permissao
from apps.catalogo.models import DicionarioUom, DicionarioAtributo
from apps.financeiro.models import (
    MeioPagamento,
    RegraPagamento,
    CategoriaFinanceira,
    ContaBancaria,
)
from apps.administracao.models import ConfiguracaoGlobal


class Command(BaseCommand):
    help = "Popula o banco de dados com dados estruturais iniciais (UOM, Atributos, Meios, Regras, Categorias, Configuração Global e Admin Inicial)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando povoamento de dados estruturais (Seeders)..."))

        # 1. Dicionário UOM (100% Maiúsculas sem Acento)
        uoms = [
            ("UN", "UNIDADE"),
            ("M", "METRO"),
            ("M2", "METRO QUADRADO"),
            ("CM2", "CENTIMETRO QUADRADO"),
            ("MM", "MILIMETRO"),
            ("KG", "QUILOGRAMA"),
            ("G", "GRAMA"),
            ("L", "LITRO"),
            ("ML", "MILILITRO"),
            ("CX", "CAIXA"),
            ("BARRA", "BARRA"),
            ("PCT", "PACOTE"),
            ("H", "HORA"),
        ]
        uom_count = 0
        for sigla, desc in uoms:
            _, created = DicionarioUom.objects.get_or_create(
                sigla=sigla,
                defaults={'descricao': desc}
            )
            if created:
                uom_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Dicionario UOM populado ({uom_count} novas unidades)."))

        # 2. Dicionário de Atributos Técnicos (100% Maiúsculas sem Acento)
        atributos = [
            "ESPESSURA",
            "DIAMETRO",
            "MATERIAL / LIGA",
            "ROSCA",
            "COMPRIMENTO",
            "MARCA / FABRICANTE",
            "ACABAMENTO",
        ]
        attr_count = 0
        for nome_attr in atributos:
            _, created = DicionarioAtributo.objects.get_or_create(
                nome_atributo=nome_attr
            )
            if created:
                attr_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Dicionario de Atributos populado ({attr_count} novos atributos)."))

        # 3. Meios de Pagamento (100% Maiúsculas sem Acento)
        meios = [
            ("PIX", False),
            ("DINHEIRO", False),
            ("BOLETO BANCARIO", False),
            ("CARTAO DE CREDITO", True),
            ("CARTAO DE DEBITO", True),
            ("TRANSFERENCIA TED/DOC", False),
            ("DEPOSITO BANCARIO", False),
            ("CHEQUE", False),
        ]
        meios_dict = {}
        meio_count = 0
        for nome_meio, permite_taxa in meios:
            meio, created = MeioPagamento.objects.get_or_create(
                nome=nome_meio,
                defaults={'permite_taxa_maquininha': permite_taxa, 'ativo': True}
            )
            meios_dict[nome_meio] = meio
            if created:
                meio_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Meios de Pagamento populados ({meio_count} novos meios)."))

        # 4. Regras de Pagamento / Condições Comerciais (100% Maiúsculas sem Acento)
        regras = [
            ("A VISTA NO PIX (5% DESC.)", "PIX", "A_VISTA", 1, 0, 0, 5.00),
            ("A VISTA EM DINHEIRO", "DINHEIRO", "A_VISTA", 1, 0, 0, 0.00),
            ("BOLETO 28 DIAS", "BOLETO BANCARIO", "A_PRAZO", 1, 28, 0, 0.00),
            ("BOLETO 30/60 DIAS", "BOLETO BANCARIO", "PARCELADO", 2, 30, 30, 0.00),
            ("BOLETO 30/60/90 DIAS", "BOLETO BANCARIO", "PARCELADO", 3, 30, 30, 0.00),
            ("CARTAO DE DEBITO", "CARTAO DE DEBITO", "A_VISTA", 1, 0, 0, 0.00),
            ("CARTAO DE CREDITO A VISTA", "CARTAO DE CREDITO", "A_VISTA", 1, 30, 0, 0.00),
            ("CARTAO DE CREDITO 3X", "CARTAO DE CREDITO", "PARCELADO", 3, 30, 30, 0.00),
        ]
        regra_count = 0
        for nome_regra, meio_nome, tipo_cobr, num_parc, prazo_1, interv, desc_padrao in regras:
            if meio_nome in meios_dict:
                _, created = RegraPagamento.objects.get_or_create(
                    nome=nome_regra,
                    defaults={
                        'meio_pagamento': meios_dict[meio_nome],
                        'tipo_cobranca': tipo_cobr,
                        'numero_parcelas': num_parc,
                        'prazo_primeira_parcela_dias': prazo_1,
                        'intervalo_parcelas_dias': interv,
                        'desconto_concedido_padrao': desc_padrao,
                        'ativo': True
                    }
                )
                if created:
                    regra_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Regras de Pagamento populadas ({regra_count} novas regras)."))

        # 5. Categorias Financeiras (100% Maiúsculas sem Acento e Enum UPPERCASE)
        categorias = [
            ("RECEITA DE VENDA DE PRODUTOS", "RECEITA", None),
            ("RECEITA DE SERVICOS E REFORMAS", "RECEITA", None),
            ("OUTRAS RECEITAS OPERACIONAIS", "RECEITA", None),
            ("INSUMOS E MATERIAS-PRIMAS", "DESPESA", None),
            ("FOLHA DE PAGAMENTO E PRO-LABORE", "DESPESA", None),
            ("TARIFAS E MAQUININHAS", "DESPESA", None),
            ("IMPOSTOS E TRIBUTOS", "DESPESA", None),
            ("MANUTENCAO E FERRAMENTAL", "DESPESA", None),
            ("AGUA, LUZ E INTERNET", "DESPESA", None),
            ("OUTRAS DESPESAS OPERACIONAIS", "DESPESA", None),
            ("TRANSFERENCIA INTER-CONTAS", "TRANSFERENCIA", None),
        ]
        cat_count = 0
        for nome_cat, tipo_cat, _ in categorias:
            _, created = CategoriaFinanceira.objects.get_or_create(
                nome=nome_cat,
                defaults={'tipo': tipo_cat}
            )
            if created:
                cat_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Categorias Financeiras populadas ({cat_count} novas categorias)."))

        # 6. Contas Bancárias Iniciais (100% Maiúsculas sem Acento)
        contas = [
            ("CAIXA FISICO OFICINA", 0.00, 0.00),
            ("CONTA CORRENTE PRINCIPAL", 0.00, 1000.00),
        ]
        conta_count = 0
        for nome_conta, saldo, limite in contas:
            _, created = ContaBancaria.objects.get_or_create(
                nome=nome_conta,
                defaults={'saldo': saldo, 'limite_credito': limite}
            )
            if created:
                conta_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Contas Bancarias populadas ({conta_count} novas contas)."))

        # 7. Configuração Global (Singleton id=1 - 100% Maiúsculas sem Acento)
        config, created = ConfiguracaoGlobal.objects.get_or_create(
            id=1,
            defaults={
                'validade_orcamento_dias': 15,
                'taxa_mao_de_obra_hora': 80.00,
                'razao_social': 'EMC SOLDAS E MANUTENCAO INDUSTRIAL LTDA',
                'cnpj': '12.345.678/0001-90',
                'telefone_contato': '(11) 98765-4321',
                'endereco_oficina': 'RUA INDUSTRIAL DA SOLDA, 500 - GALPAO 2 - SAO PAULO/SP',
                'tempo_ociosidade_minutos': 30,
                'tempo_expiracao_sessao_dias': 15,
                'retencao_logs_dias': 30,
                'smtp_host': 'localhost',
                'smtp_port': 587,
                'smtp_use_tls': True,
                'email_remetente_nome': 'EMC SOLDAS',
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Configuracoes Globais (id=1) inicializadas."))

        # 8. Usuário Administrador Inicial e Permissões Plenas
        admin_email = "admin@emcsoldas.com.br"
        admin_user, created_user = Usuario.objects.get_or_create(
            email=admin_email,
            defaults={
                'nome': 'ADMINISTRADOR GERAL',
                'role': 'Admin',
                'password_hash': make_password('AdminMaster2026!'),
                'pin_hash': make_password('123456'),
                'is_ativo': True,
            }
        )
        if not created_user:
            admin_user.nome = 'ADMINISTRADOR GERAL'
            admin_user.set_password('AdminMaster2026!')
            admin_user.set_pin('123456')
            admin_user.resetar_falhas_login()
            admin_user.save()

        Permissao.objects.get_or_create(
            usuario=admin_user,
            defaults={
                'acesso_comercial': True,
                'acesso_tesouraria': True,
                'acesso_compras': True,
                'gestao_catalogo': True,
                'visao_relatorios': True,
                'cadastros_financeiros': True,
                'gestao_dicionario_uom': True,
                'configuracoes_globais': True,
                'gestao_equipe': True,
                'auditoria_logs_recovery': True,
            }
        )
        if created_user:
            self.stdout.write(self.style.SUCCESS(f"[OK] Usuario Administrador Master criado ({admin_email} / PIN: 123456)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"[OK] Usuario Administrador Master verificado ({admin_email})."))

        self.stdout.write(self.style.SUCCESS("=== Semeamento de dados iniciais concluido com sucesso! ==="))
