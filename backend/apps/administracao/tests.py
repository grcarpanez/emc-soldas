"""
Suíte de Testes Automatizados da Fase 12 - Central Administrativa.
Cobre:
- Singleton de ConfiguracaoGlobal e criptografia AES-256 de senhas SMTP.
- Presets rápidos e Teste de disparo SMTP em tempo real.
- Blindagem de Não-Retroatividade em orçamentos anteriores.
- Sincronização do Manifesto TTL e Rotina de Expurgo com Backup por E-mail.
- Comando CLI manage.py expurgar_logs (--enviar-backup / --sem-backup).
- Log Viewer Seguro do Servidor e Blindagem contra Path Traversal.
- Controle de Acesso RBAC com os 10 Toggles Dinâmicos.
- Painel de Lixeira e Restauração Lógica com Segregação (Lixeira Global vs Minha Lixeira).
"""
import os
import datetime
from decimal import Decimal
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status

from core.utils import CryptoManager
from apps.authentication.models import Usuario, Permissao
from apps.administracao.models import ConfiguracaoGlobal, ControleArquivoLog
from apps.administracao.services import (
    obter_presets_smtp,
    testar_conexao_smtp,
    sincronizar_manifesto_logs,
    expurgar_arquivos_log,
    ler_arquivo_log_seguro,
    LixeiraService
)
from apps.orcamentos.models import Orcamento
from apps.catalogo.models import Item, DicionarioUom
from apps.cadastros.models import ClienteFornecedor
from apps.financeiro.models import LancamentoFinanceiro, ContaBancaria, CategoriaFinanceira, MeioPagamento


class AdministracaoTests(TestCase):
    """Testes completos das funcionalidades administrativas."""

    def setUp(self):
        self.client = APIClient()
        self.logs_dir = getattr(settings, 'LOG_DIR', os.path.join(settings.BASE_DIR, 'logs'))
        os.makedirs(self.logs_dir, exist_ok=True)

        # 1. Configuração Global padrão (Singleton id=1)
        self.config = ConfiguracaoGlobal.objects.create(
            id=1,
            razao_social="EMC SOLDAS LTDA",
            cnpj="00000000000100",
            taxa_mao_de_obra_hora=Decimal('100.00'),
            validade_orcamento_dias=15,
            tempo_ociosidade_minutos=30,
            tempo_expiracao_sessao_dias=15,
            retencao_logs_dias=30,
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="teste@emcsoldas.com.br",
            smtp_use_tls=True,
            smtp_use_ssl=False,
            email_remetente_nome="EMC SOLDAS NOTIFICACOES"
        )

        # 2. Usuário Administrador Master
        self.admin_user = Usuario.objects.create(
            nome="ADMINISTRADOR GESTOR",
            email="admin@emcsoldas.com.br",
            role="Admin",
            is_ativo=True
        )
        self.admin_user.set_password("SenhaAdmin@123")
        self.admin_user.save()
        self.admin_perm = Permissao.objects.create(
            usuario=self.admin_user,
            acesso_comercial=True,
            acesso_tesouraria=True,
            acesso_compras=True,
            gestao_catalogo=True,
            visao_relatorios=True,
            cadastros_financeiros=True,
            gestao_dicionario_uom=True,
            configuracoes_globais=True,
            gestao_equipe=True,
            auditoria_logs_recovery=True
        )

        # 3. Operador Padrão (Sem toggles administrativos)
        self.operador_user = Usuario.objects.create(
            nome="OPERADOR BALCAO",
            email="operador@emcsoldas.com.br",
            role="Operador",
            is_ativo=True
        )
        self.operador_user.set_password("SenhaOp@123")
        self.operador_user.save()
        self.operador_perm = Permissao.objects.create(
            usuario=self.operador_user,
            acesso_comercial=True,
            acesso_tesouraria=True,
            acesso_compras=True,
            gestao_catalogo=True,
            visao_relatorios=True,
            cadastros_financeiros=False,
            gestao_dicionario_uom=False,
            configuracoes_globais=False,
            gestao_equipe=False,
            auditoria_logs_recovery=False
        )

        # 4. Operador com Acesso Específico de Auditoria/Recovery
        self.auditor_user = Usuario.objects.create(
            nome="OPERADOR AUDITOR",
            email="auditor@emcsoldas.com.br",
            role="Operador",
            is_ativo=True
        )
        self.auditor_user.set_password("SenhaAuditor@123")
        self.auditor_user.save()
        self.auditor_perm = Permissao.objects.create(
            usuario=self.auditor_user,
            acesso_comercial=True,
            auditoria_logs_recovery=True,
            configuracoes_globais=True
        )

    # --------------------------------------------------------------------------
    # 1. TESTES DE PARÂMETROS GLOBAIS E CRIPTOGRAFIA AES-256
    # --------------------------------------------------------------------------

    def test_consulta_configuracoes_globais_singleton(self):
        """Valida que a consulta retorna o Singleton com status de senha e sem expor plaintext."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/configuracoes-globais/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['razao_social'], "EMC SOLDAS LTDA")
        self.assertNotIn('smtp_password', data)
        self.assertFalse(data['smtp_has_password'])

    def test_atualizacao_configuracoes_com_criptografia_senha_smtp(self):
        """Valida atualização com sanitização e criptografia simétrica AES-256 na senha SMTP."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "razao_social": "EMC Soldas & Usinagem Especializada",
            "taxa_mao_de_obra_hora": "120.00",
            "smtp_password": "SenhaSuperSecretaApp123",
            "email_remetente_nome": "EMC Soldas - Central Automática"
        }
        response = self.client.patch('/api/configuracoes-globais/1/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.config.refresh_from_db()
        self.assertEqual(self.config.razao_social, "EMC SOLDAS & USINAGEM ESPECIALIZADA")
        self.assertEqual(self.config.email_remetente_nome, "EMC SOLDAS - CENTRAL AUTOMATICA")
        self.assertEqual(self.config.taxa_mao_de_obra_hora, Decimal('120.00'))

        # Confirma que no banco está criptografado e não é plaintext
        self.assertIsNotNone(self.config.smtp_password_encrypted)
        self.assertNotEqual(self.config.smtp_password_encrypted, "SenhaSuperSecretaApp123")
        # Descriptografia deve recuperar o valor exato
        senha_recuperada = CryptoManager.decrypt(self.config.smtp_password_encrypted)
        self.assertEqual(senha_recuperada, "SenhaSuperSecretaApp123")

        # Consulta subsequente indica smtp_has_password = True sem vazar a senha
        res_get = self.client.get('/api/configuracoes-globais/')
        self.assertTrue(res_get.data['smtp_has_password'])
        self.assertNotIn('smtp_password', res_get.data)

    def test_presets_smtp_endpoint(self):
        """Valida o endpoint que fornece presets rápidos para configuração de e-mails."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/configuracoes-globais/presets-smtp/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('presets', response.data)
        presets_ids = [p['id'] for p in response.data['presets']]
        self.assertIn('gmail', presets_ids)
        self.assertIn('outlook', presets_ids)

    def test_disparo_teste_smtp_em_tempo_real(self):
        """Valida endpoint de teste de envio de e-mail SMTP em tempo real."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "destinatario": "destinatario.teste@emcsoldas.com.br",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "teste@emcsoldas.com.br",
            "smtp_use_tls": True
        }
        response = self.client.post('/api/configuracoes-globais/testar-smtp/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['sucesso'])
        # Verifica se o e-mail foi enfileirado na mailbox de teste
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn("destinatario.teste@emcsoldas.com.br", mail.outbox[-1].to)

    # --------------------------------------------------------------------------
    # 2. TESTE DE NÃO-RETROATIVIDADE EM ORÇAMENTOS
    # --------------------------------------------------------------------------

    def test_nao_retroatividade_taxa_horaria_e_validade_em_orcamentos(self):
        """Comprova que alteração global de taxa e validade não afeta orçamentos passados."""
        cliente = ClienteFornecedor.objects.create(
            nome_razao="CLIENTE TESTE RETROATIVIDADE",
            cnpj_cpf="11122233344",
            tipo="Cliente",
            tipo_pessoa="PF"
        )
        uom = DicionarioUom.objects.create(sigla="UN", descricao="UNIDADE")

        data_geracao_passada = timezone.localdate() - datetime.timedelta(days=10)
        data_validade_original = data_geracao_passada + datetime.timedelta(days=15)

        orcamento_antigo = Orcamento.objects.create(
            cliente=cliente,
            data_geracao=data_geracao_passada,
            data_validade=data_validade_original,
            valor_bruto=Decimal('500.00'),
            status_operacional="GERADO",
            status_financeiro="A_FATURAR",
            created_by_id=self.admin_user.id
        )

        # Atualiza a configuração global (taxa de 100 para 200, validade de 15 para 45 dias)
        self.client.force_authenticate(user=self.admin_user)
        self.client.patch('/api/configuracoes-globais/1/', {
            "taxa_mao_de_obra_hora": "200.00",
            "validade_orcamento_dias": 45
        })

        orcamento_antigo.refresh_from_db()
        # Valores e datas originais devem permanecer intactos
        self.assertEqual(orcamento_antigo.valor_bruto, Decimal('500.00'))
        self.assertEqual(orcamento_antigo.data_validade, data_validade_original)

    # --------------------------------------------------------------------------
    # 3. TESTES DE MANIFESTO TTL, EXPURGO E BACKUP DE LOGS
    # --------------------------------------------------------------------------

    def test_sincronizacao_e_listagem_manifesto_logs(self):
        """Valida que arquivos de log físicos em disco são indexados no manifesto."""
        # Cria arquivo de log físico simulado
        data_simulada = timezone.localdate() - datetime.timedelta(days=5)
        nome_arquivo = f"app-{data_simulada.strftime('%Y-%m-%d')}.log"
        caminho_arquivo = os.path.join(self.logs_dir, nome_arquivo)
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write("[2026-08-18 10:00:00] [INFO] Inicialização do sistema.\n")

        self.client.force_authenticate(user=self.admin_user)
        res_sinc = self.client.post('/api/controle-arquivos-log/sincronizar/')
        self.assertEqual(res_sinc.status_code, status.HTTP_200_OK)
        self.assertTrue(res_sinc.data['sucesso'])

        res_list = self.client.get('/api/controle-arquivos-log/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        lista_dados = res_list.data.get('results', res_list.data) if isinstance(res_list.data, dict) else res_list.data
        caminhos = [item['caminho_arquivo_fisico'] for item in lista_dados]
        self.assertTrue(any(nome_arquivo in c for c in caminhos))

        # Limpeza
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)

    def test_rotina_expurgo_com_envio_backup_email_e_exclusao_fisica(self):
        """Valida que logs expirados são enviados por e-mail e excluídos fisicamente."""
        # 1. Cria um arquivo de log com data de 40 dias atrás (expirado para retenção de 30 dias)
        data_antiga = timezone.localdate() - datetime.timedelta(days=40)
        nome_antigo = f"app-{data_antiga.strftime('%Y-%m-%d')}.log"
        caminho_antigo = os.path.join(self.logs_dir, nome_antigo)
        with open(caminho_antigo, 'w', encoding='utf-8') as f:
            f.write("[LOG ANTIGO] [AUDIT] Evento ocorrido ha 40 dias.\n")

        # Indexa no manifesto com data planejada no passado
        manifesto = ControleArquivoLog.objects.create(
            caminho_arquivo_fisico=os.path.join('logs', nome_antigo).replace('\\', '/'),
            data_criacao=data_antiga,
            data_expurgo_planejada=timezone.localdate() - datetime.timedelta(days=10)
        )

        mail.outbox = []
        self.client.force_authenticate(user=self.admin_user)
        res_expurgo = self.client.post('/api/controle-arquivos-log/expurgar/', {
            "enviar_email_backup": True
        })
        self.assertEqual(res_expurgo.status_code, status.HTTP_200_OK)
        self.assertTrue(res_expurgo.data['sucesso'])
        self.assertGreaterEqual(res_expurgo.data['total_expurgados'], 1)

        # 1. Confirma que o e-mail de backup foi enviado com o arquivo em anexo
        self.assertTrue(res_expurgo.data['email_backup_enviado'])
        self.assertGreaterEqual(len(mail.outbox), 1)
        email_backup = mail.outbox[-1]
        self.assertIn("BACKUP DE AUDITORIA", email_backup.subject)
        self.assertGreaterEqual(len(email_backup.attachments), 1)

        # 2. Confirma que o arquivo físico foi excluído do disco
        self.assertFalse(os.path.exists(caminho_antigo))
        # 3. Confirma que o manifesto foi baixado no banco
        self.assertFalse(ControleArquivoLog.objects.filter(id=manifesto.id).exists())

    def test_comando_cli_expurgar_logs(self):
        """Valida a execução do comando de linha de comando `manage.py expurgar_logs`."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('expurgar_logs', '--sem-backup', stdout=out)
        conteudo_saida = out.getvalue()
        self.assertIn("[OK] Sincronizacao concluida", conteudo_saida)

    # --------------------------------------------------------------------------
    # 4. TESTES DO LOG VIEWER SEGURO E BLINDAGEM ANTI-PATH TRAVERSAL
    # --------------------------------------------------------------------------

    def test_log_viewer_leitura_estruturada_e_filtros(self):
        """Valida leitura estruturada com filtros por severidade e busca textual."""
        hoje_str = timezone.localdate().strftime('%Y-%m-%d')
        arquivo_hoje = os.path.join(self.logs_dir, f"app-{hoje_str}.log")
        with open(arquivo_hoje, 'w', encoding='utf-8') as f:
            f.write(f"[{hoje_str} 10:00:00] [INFO] Sistema operando normalmente.\n")
            f.write(f"[{hoje_str} 10:05:00] [WARNING] Tentativa de acesso sem permissao.\n")
            f.write(f"[{hoje_str} 10:10:00] [ERROR] Falha de conexao com gateway.\n")
            f.write(f"[{hoje_str} 10:15:00] [AUDIT] [CANCELAMENTO] Orcamento #99 cancelado.\n")

        self.client.force_authenticate(user=self.admin_user)
        # Consulta com filtro de nível ERROR
        response = self.client.get('/api/logs/', {'arquivo': 'hoje', 'nivel': 'ERROR'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['existe'])
        self.assertEqual(response.data['total_linhas_filtradas'], 1)
        self.assertIn("Falha de conexao", response.data['linhas'][0]['conteudo'])

        # Consulta com busca textual
        res_busca = self.client.get('/api/logs/', {'arquivo': 'hoje', 'busca': 'CANCELAMENTO'})
        self.assertEqual(res_busca.status_code, status.HTTP_200_OK)
        self.assertEqual(res_busca.data['total_linhas_filtradas'], 1)
        self.assertIn("Orcamento #99 cancelado", res_busca.data['linhas'][0]['conteudo'])

    def test_log_viewer_bloqueio_path_traversal(self):
        """Valida que tentativas de navegação fora do diretório de logs são rejeitadas."""
        self.client.force_authenticate(user=self.admin_user)
        # Tentativa de Path Traversal
        response = self.client.get('/api/logs/', {'arquivo': '../../settings.py'})
        # O sistema deve sanitizar com os.path.basename ou retornar erro
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # O arquivo procurado deve ser estritamente basename com .log
        self.assertEqual(response.data['arquivo'], 'settings.py.log')
        self.assertFalse(response.data['existe'])

    # --------------------------------------------------------------------------
    # 5. TESTES DE CONTROLE DE ACESSO RBAC
    # --------------------------------------------------------------------------

    def test_rbac_operador_bloqueado_em_configuracoes_e_logs(self):
        """Valida que operador sem toggles recebe 403 Forbidden nas rotas restritas."""
        self.client.force_authenticate(user=self.operador_user)

        res_config = self.client.get('/api/configuracoes-globais/')
        self.assertEqual(res_config.status_code, status.HTTP_403_FORBIDDEN)

        res_logs = self.client.get('/api/logs/')
        self.assertEqual(res_logs.status_code, status.HTTP_403_FORBIDDEN)

        res_expurgo = self.client.post('/api/controle-arquivos-log/expurgar/')
        self.assertEqual(res_expurgo.status_code, status.HTTP_403_FORBIDDEN)

    def test_rbac_operador_com_toggle_recovery_liberado(self):
        """Valida que operador com auditoria_logs_recovery acessa o Log Viewer."""
        self.client.force_authenticate(user=self.auditor_user)
        res_logs = self.client.get('/api/logs/')
        self.assertEqual(res_logs.status_code, status.HTTP_200_OK)

    # --------------------------------------------------------------------------
    # 6. TESTES DA LIXEIRA UNIFICADA E RESTAURAÇÃO LÓGICA
    # --------------------------------------------------------------------------

    def test_lixeira_segregacao_global_vs_minha_lixeira(self):
        """Valida que o Admin vê a Lixeira Global e o Operador vê apenas Minha Lixeira."""
        # 1. Cria 2 itens e deleta por usuários diferentes
        uom = DicionarioUom.objects.create(sigla="KG", descricao="QUILOGRAMA")
        item_admin = Item.objects.create(
            nome="INSUMO EXCLUIDO PELO ADMIN",
            unidade_compra=uom,
            unidade_consumo=uom,
            created_by_id=self.admin_user.id
        )
        item_admin.delete(user_id=self.admin_user.id)

        item_op = Item.objects.create(
            nome="INSUMO EXCLUIDO PELO OPERADOR",
            unidade_compra=uom,
            unidade_consumo=uom,
            created_by_id=self.operador_user.id
        )
        item_op.delete(user_id=self.operador_user.id)

        # 2. Consulta pelo Operador (Minha Lixeira)
        self.client.force_authenticate(user=self.operador_user)
        res_op = self.client.get('/api/lixeira/', {'entidade': 'itens'})
        self.assertEqual(res_op.status_code, status.HTTP_200_OK)
        ids_op = [i['id'] for i in res_op.data['itens']]
        self.assertIn(item_op.id, ids_op)
        self.assertNotIn(item_admin.id, ids_op)

        # 3. Consulta pelo Admin (Lixeira Global)
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get('/api/lixeira/', {'entidade': 'itens'})
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        ids_admin = [i['id'] for i in res_admin.data['itens']]
        self.assertIn(item_op.id, ids_admin)
        self.assertIn(item_admin.id, ids_admin)

    def test_restauracao_logica_com_sucesso(self):
        """Valida que o endpoint de restauração reativa o registro inativado."""
        cliente = ClienteFornecedor.objects.create(
            nome_razao="CLIENTE INATIVADO TESTE",
            tipo="Cliente",
            tipo_pessoa="PJ",
            created_by_id=self.admin_user.id
        )
        cliente.delete(user_id=self.admin_user.id)
        self.assertIsNotNone(cliente.deleted_at)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/api/lixeira/clientes/{cliente.id}/restaurar/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'], 'success')

        cliente.refresh_from_db()
        self.assertIsNone(cliente.deleted_at)
        self.assertIsNone(cliente.deleted_by_id)

    def test_operador_bloqueado_de_restaurar_item_de_outro_usuario(self):
        """Valida que o operador não pode restaurar registros inativados por outros."""
        uom = DicionarioUom.objects.create(sigla="LT", descricao="LITRO")
        item_admin = Item.objects.create(
            nome="ITEM ADMIN DELETADO",
            unidade_compra=uom,
            unidade_consumo=uom,
            created_by_id=self.admin_user.id
        )
        item_admin.delete(user_id=self.admin_user.id)

        self.client.force_authenticate(user=self.operador_user)
        response = self.client.post(f'/api/lixeira/itens/{item_admin.id}/restaurar/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("permissão", response.data['message'].lower())

    def test_listar_lixeira_sem_filtro_retorna_todas_as_entidades(self):
        """Valida que a consulta na Lixeira sem o parâmetro entidade retorna registros de múltiplos modelos."""
        from apps.cadastros.models import Equipamento

        cliente = ClienteFornecedor.objects.create(
            nome_razao="CLIENTE DELETADO GLOBAL",
            tipo="Cliente",
            tipo_pessoa="PJ",
            created_by_id=self.admin_user.id
        )
        cliente.delete(user_id=self.admin_user.id)

        equip = Equipamento.objects.create(
            placa="DEL-9999",
            identificacao="FROTA DELETADA",
            descricao="CAMINHAO BASCULANTE",
            created_by_id=self.admin_user.id
        )
        equip.delete(user_id=self.admin_user.id)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/lixeira/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('itens', response.data)

        entidades_retornadas = [i['entidade'] for i in response.data['itens']]
        self.assertIn('clientes', entidades_retornadas)
        self.assertIn('equipamentos', entidades_retornadas)
