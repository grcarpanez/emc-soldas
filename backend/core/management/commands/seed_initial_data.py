"""
Comando de Management do Django para popular e sincronizar a base de dados com sementes estruturais.
Garante 100% de sanitização (Maiúsculas sem Acento - ASCII puro) em registros novos e pré-existentes.
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
from core.utils import sanitizar_texto_maiusculo


class Command(BaseCommand):
    help = "Popula e sanitiza o banco de dados com dados estruturais padrão (100% Maiúsculas sem Acento)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando sincronização e sanitização universal dos dados estruturais..."))

        # 0. Sanitização retroativa de registros existentes no banco
        self.stdout.write("Higienizando registros pré-existentes no banco...")
        
        for u in DicionarioUom.all_objects.all():
            u.sigla = sanitizar_texto_maiusculo(u.sigla)
            u.descricao = sanitizar_texto_maiusculo(u.descricao)
            u.save(update_fields=['sigla', 'descricao'])

        for a in DicionarioAtributo.all_objects.all():
            a.nome_atributo = sanitizar_texto_maiusculo(a.nome_atributo)
            a.save(update_fields=['nome_atributo'])

        for m in MeioPagamento.all_objects.all():
            m.nome = sanitizar_texto_maiusculo(m.nome)
            m.save(update_fields=['nome'])

        for r in RegraPagamento.all_objects.all():
            r.nome = sanitizar_texto_maiusculo(r.nome)
            r.save(update_fields=['nome'])

        for c in CategoriaFinanceira.all_objects.all():
            c.nome = sanitizar_texto_maiusculo(c.nome)
            c.tipo = c.tipo.upper()
            c.save(update_fields=['nome', 'tipo'])

        for b in ContaBancaria.all_objects.all():
            b.nome = sanitizar_texto_maiusculo(b.nome)
            b.save(update_fields=['nome'])

        self.stdout.write(self.style.SUCCESS("[OK] Registros existentes higienizados para Maiúsculas sem Acento."))

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
            sigla_san = sanitizar_texto_maiusculo(sigla)
            desc_san = sanitizar_texto_maiusculo(desc)
            obj, created = DicionarioUom.objects.update_or_create(
                sigla=sigla_san,
                defaults={'descricao': desc_san, 'deleted_at': None}
            )
            if created:
                uom_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Dicionario UOM sincronizado ({uom_count} novas unidades)."))

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
            attr_san = sanitizar_texto_maiusculo(nome_attr)
            obj, created = DicionarioAtributo.objects.update_or_create(
                nome_atributo=attr_san,
                defaults={'deleted_at': None}
            )
            if created:
                attr_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Dicionario de Atributos sincronizado ({attr_count} novos atributos)."))

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
            ("CORTESIA", False),
        ]
        meios_dict = {}
        meio_count = 0
        for nome_meio, permite_taxa in meios:
            meio_san = sanitizar_texto_maiusculo(nome_meio)
            meio, created = MeioPagamento.objects.update_or_create(
                nome=meio_san,
                defaults={'permite_taxa_maquininha': permite_taxa, 'ativo': True, 'deleted_at': None}
            )
            meios_dict[meio_san] = meio
            if created:
                meio_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Meios de Pagamento sincronizados ({meio_count} novos meios)."))

        # 4. Regras de Pagamento / Condições Comerciais (100% Maiúsculas sem Acento)
        regras = [
            ("A VISTA NO PIX (5% DESC.)", "PIX", "A_VISTA", 1, 0, 0, 5.00),
            ("A VISTA EM DINHEIRO", "DINHEIRO", "A_VISTA", 1, 0, 0, 0.00),
            ("BOLETO 28 DIAS", "BOLETO BANCARIO", "A_PRAZO", 1, 28, 0, 0.00),
            ("BOLETO 30/60 DIAS", "BOLETO BANCARIO", "PARCELADO", 2, 30, 30, 0.00),
            ("BOLETO 30/60/90 DIAS", "BOLETO BANCARIO", "PARCELADO", 3, 30, 30, 0.00),
            ("CARTAO DE DEBITO A VISTA", "CARTAO DE DEBITO", "A_VISTA", 1, 0, 0, 0.00),
            ("CARTAO DE CREDITO A VISTA", "CARTAO DE CREDITO", "A_VISTA", 1, 30, 0, 0.00),
            ("CARTAO DE CREDITO 3X SEM JUROS", "CARTAO DE CREDITO", "PARCELADO", 3, 30, 30, 0.00),
            ("CORTESIA (100% DESCONTO)", "CORTESIA", "A_VISTA", 1, 0, 0, 100.00),
        ]
        regra_count = 0
        for nome_regra, meio_nome, tipo_cobr, num_parc, prazo_1, interv, desc_padrao in regras:
            meio_san = sanitizar_texto_maiusculo(meio_nome)
            regra_san = sanitizar_texto_maiusculo(nome_regra)
            if meio_san in meios_dict:
                obj, created = RegraPagamento.objects.update_or_create(
                    nome=regra_san,
                    defaults={
                        'meio_pagamento': meios_dict[meio_san],
                        'tipo_cobranca': tipo_cobr,
                        'numero_parcelas': num_parc,
                        'prazo_primeira_parcela_dias': prazo_1,
                        'intervalo_parcelas_dias': interv,
                        'desconto_concedido_padrao': desc_padrao,
                        'ativo': True,
                        'deleted_at': None
                    }
                )
                if created:
                    regra_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Regras de Pagamento sincronizadas ({regra_count} novas regras)."))

        # 5. Categorias Financeiras (100% Maiúsculas sem Acento e Enum UPPERCASE)
        categorias = [
            ("RECEITA DE SERVICOS (MAO DE OBRA)", "RECEITA", None),
            ("RECEITA DE VENDA DE PRODUTOS E MATERIAIS", "RECEITA", None),
            ("OUTRAS RECEITAS OPERACIONAIS", "RECEITA", None),
            ("INSUMOS PRODUTIVOS E MATERIA-PRIMA", "DESPESA", None),
            ("ENERGIA ELETRICA E AGUA", "DESPESA", None),
            ("MANUTENCAO DE MAQUINAS", "DESPESA", None),
            ("IMPOSTOS E TRIBUTOS", "DESPESA", None),
            ("SALARIOS E ENCARGOS", "DESPESA", None),
            ("TAXAS DE CARTAO E BANCARIAS", "DESPESA", None),
            ("OUTRAS DESPESAS OPERACIONAIS", "DESPESA", None),
            ("TRANSFERENCIA INTER-CONTAS", "TRANSFERENCIA", None),
        ]
        cat_count = 0
        for nome_cat, tipo_cat, _ in categorias:
            nome_san = sanitizar_texto_maiusculo(nome_cat)
            obj, created = CategoriaFinanceira.objects.update_or_create(
                nome=nome_san,
                defaults={'tipo': tipo_cat.upper(), 'deleted_at': None}
            )
            if created:
                cat_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Categorias Financeiras sincronizadas ({cat_count} novas categorias)."))

        # 6. Contas Bancárias Iniciais (100% Maiúsculas sem Acento)
        contas = [
            ("CAIXA FISICO DA OFICINA", 0.00, 0.00),
            ("CONTA BANCARIA PRINCIPAL", 0.00, 1000.00),
        ]
        conta_count = 0
        for nome_conta, saldo, limite in contas:
            nome_san = sanitizar_texto_maiusculo(nome_conta)
            obj, created = ContaBancaria.objects.update_or_create(
                nome=nome_san,
                defaults={'saldo': saldo, 'limite_credito': limite, 'deleted_at': None}
            )
            if created:
                conta_count += 1
        self.stdout.write(self.style.SUCCESS(f"[OK] Contas Bancarias sincronizadas ({conta_count} novas contas)."))

        # 7. Configuração Global (Singleton id=1 - 100% Maiúsculas sem Acento)
        config, created = ConfiguracaoGlobal.objects.update_or_create(
            id=1,
            defaults={
                'validade_orcamento_dias': 15,
                'taxa_mao_de_obra_hora': 80.00,
                'razao_social': sanitizar_texto_maiusculo('EMC SOLDAS E MANUTENCAO INDUSTRIAL LTDA'),
                'cnpj': '12.345.678/0001-90',
                'telefone_contato': '(11) 98765-4321',
                'endereco_oficina': sanitizar_texto_maiusculo('RUA INDUSTRIAL DA SOLDA, 500 - GALPAO 2 - SAO PAULO/SP'),
                'tempo_ociosidade_minutos': 30,
                'tempo_expiracao_sessao_dias': 15,
                'retencao_logs_dias': 30,
                'smtp_host': 'localhost',
                'smtp_port': 587,
                'smtp_use_tls': True,
                'email_remetente_nome': sanitizar_texto_maiusculo('EMC SOLDAS'),
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Configuracoes Globais (id=1) sincronizadas."))

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

        self.stdout.write(self.style.SUCCESS("=== Semeamento e sincronizacao de dados estruturais concluidos com sucesso! ==="))
