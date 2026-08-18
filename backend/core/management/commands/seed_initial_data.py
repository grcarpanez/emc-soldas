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

        # 1. Dicionário UOM
        uoms = [
            ("UN", "Unidade"),
            ("m", "Metro"),
            ("m²", "Metro Quadrado"),
            ("cm²", "Centímetro Quadrado"),
            ("mm", "Milímetro"),
            ("kg", "Quilograma"),
            ("g", "Grama"),
            ("L", "Litro"),
            ("mL", "Mililitro"),
            ("CX", "Caixa"),
            ("BARRA", "Barra"),
            ("PCT", "Pacote"),
            ("H", "Hora"),
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

        # 2. Dicionário de Atributos Técnicos
        atributos = [
            "Espessura",
            "Diâmetro",
            "Material / Liga",
            "Rosca",
            "Comprimento",
            "Marca / Fabricante",
            "Acabamento",
        ]
        attr_count = 0
        for nome_attr in atributos:
            _, created = DicionarioAtributo.objects.get_or_create(
                nome_atributo=nome_attr
            )
            if created:
                attr_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Dicionario de Atributos populado ({attr_count} novos atributos)."))

        # 3. Meios de Pagamento
        meios = [
            ("PIX", False),
            ("Dinheiro", False),
            ("Boleto Bancário", False),
            ("Cartão de Crédito", True),
            ("Cartão de Débito", True),
            ("Transferência TED/DOC", False),
            ("Depósito Bancário", False),
            ("Cheque", False),
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

        # 4. Regras de Pagamento / Condições Comerciais
        regras = [
            ("À Vista no Pix (5% Desc.)", "PIX", "A_VISTA", 1, 0, 0, 5.00),
            ("À Vista em Dinheiro", "Dinheiro", "A_VISTA", 1, 0, 0, 0.00),
            ("Boleto 28 Dias", "Boleto Bancário", "A_PRAZO", 1, 28, 0, 0.00),
            ("Boleto 30/60 Dias", "Boleto Bancário", "PARCELADO", 2, 30, 30, 0.00),
            ("Boleto 30/60/90 Dias", "Boleto Bancário", "PARCELADO", 3, 30, 30, 0.00),
            ("Cartão de Débito", "Cartão de Débito", "A_VISTA", 1, 0, 0, 0.00),
            ("Cartão de Crédito à Vista", "Cartão de Crédito", "A_VISTA", 1, 30, 0, 0.00),
            ("Cartão de Crédito 3x", "Cartão de Crédito", "PARCELADO", 3, 30, 30, 0.00),
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

        # 5. Categorias Financeiras
        categorias = [
            ("Receita de Venda de Produtos", "Receita", None),
            ("Receita de Serviços e Reformas", "Receita", None),
            ("Outras Receitas Operacionais", "Receita", None),
            ("Insumos e Matérias-Primas", "Despesa", None),
            ("Folha de Pagamento e Pró-Labore", "Despesa", None),
            ("Tarifas e Maquininhas", "Despesa", None),
            ("Impostos e Tributos", "Despesa", None),
            ("Manutenção e Ferramental", "Despesa", None),
            ("Água, Luz e Internet", "Despesa", None),
            ("Outras Despesas Operacionais", "Despesa", None),
            ("Transferência Inter-Contas", "Transferência", None),
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

        # 6. Contas Bancárias Iniciais
        contas = [
            ("Caixa Físico Oficina", 0.00, 0.00),
            ("Conta Corrente Principal", 0.00, 1000.00),
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

        # 7. Configuração Global (Singleton id=1)
        config, created = ConfiguracaoGlobal.objects.get_or_create(
            id=1,
            defaults={
                'validade_orcamento_dias': 15,
                'taxa_mao_de_obra_hora': 80.00,
                'razao_social': 'EMC Soldas e Manutenção Industrial LTDA',
                'cnpj': '12.345.678/0001-90',
                'telefone_contato': '(11) 98765-4321',
                'endereco_oficina': 'Rua Industrial da Solda, 500 - Galpão 2 - São Paulo/SP',
                'tempo_ociosidade_minutos': 30,
                'tempo_expiracao_sessao_dias': 15,
                'retencao_logs_dias': 30,
                'smtp_host': 'localhost',
                'smtp_port': 587,
                'smtp_use_tls': True,
                'email_remetente_nome': 'EMC Soldas',
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Configuracoes Globais (id=1) inicializadas."))

        # 8. Usuário Administrador Inicial e Permissões Plenas
        admin_email = "admin@emcsoldas.com.br"
        admin_user, created_user = Usuario.objects.get_or_create(
            email=admin_email,
            defaults={
                'nome': 'Administrador Geral',
                'role': 'Admin',
                'password_hash': make_password('Admin@123456'),
                'pin_hash': make_password('123456'),
                'is_ativo': True,
            }
        )

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
