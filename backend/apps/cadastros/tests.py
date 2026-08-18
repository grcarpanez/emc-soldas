"""
Suíte de testes automatizados do módulo de Cadastros Básicos (Fase 5).
Cobre: Clientes, Fornecedores, Equipamentos, Vínculos com Transferência Histórica, Anexos e Utilitários de CNPJ/CPF.
"""
import io
import json
from unittest.mock import patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import Usuario, Permissao
from apps.cadastros.models import (
    ClienteFornecedor,
    Equipamento,
    ClienteEquipamento,
    AnexoGeralCliente
)


class CadastrosBaseTestCase(TestCase):
    """Configuração base com usuários Admin, Operador com permissão e Operador sem permissão."""

    def setUp(self):
        self.client = APIClient()

        # Usuário Administrador Master
        self.admin = Usuario.objects.create(
            email='admin.cadastros@emcsoldas.com.br',
            role='Admin',
            is_ativo=True
        )
        self.admin.set_password('AdminSenha123!')
        self.admin.set_pin('123456')
        self.admin.save()
        Permissao.objects.create(
            usuario=self.admin,
            acesso_comercial=True,
            acesso_compras=True,
            gestao_catalogo=True,
            visao_relatorios=True,
            cadastros_financeiros=True,
            gestao_dicionario_uom=True,
            configuracoes_globais=True,
            gestao_equipe=True,
            auditoria_logs_recovery=True
        )

        # Operador com Acesso Comercial
        self.operador_comercial = Usuario.objects.create(
            email='operador.comercial@emcsoldas.com.br',
            role='Operador',
            is_ativo=True
        )
        self.operador_comercial.set_password('OperadorSenha123!')
        self.operador_comercial.save()
        Permissao.objects.create(
            usuario=self.operador_comercial,
            acesso_comercial=True,
            acesso_compras=False
        )

        # Operador com Acesso Compras (sem Comercial)
        self.operador_compras = Usuario.objects.create(
            email='operador.compras@emcsoldas.com.br',
            role='Operador',
            is_ativo=True
        )
        self.operador_compras.set_password('OperadorSenha123!')
        self.operador_compras.save()
        Permissao.objects.create(
            usuario=self.operador_compras,
            acesso_comercial=False,
            acesso_compras=True
        )

        # Operador sem Permissões
        self.operador_sem_permissao = Usuario.objects.create(
            email='operador.sem.acesso@emcsoldas.com.br',
            role='Operador',
            is_ativo=True
        )
        self.operador_sem_permissao.set_password('OperadorSenha123!')
        self.operador_sem_permissao.save()
        Permissao.objects.create(
            usuario=self.operador_sem_permissao,
            acesso_comercial=False,
            acesso_compras=False
        )


class ClienteFornecedorAPITestCase(CadastrosBaseTestCase):
    """Testes de CRUD, validações matemáticas de CPF/CNPJ, cadastro rápido e Soft Delete."""

    def test_criar_cliente_pj_com_cnpj_valido(self):
        """Valida criação de Cliente PJ com CNPJ válido e sanitização para maiúsculas sem acento."""
        self.client.force_authenticate(user=self.operador_comercial)
        
        # CNPJ válido de teste (Petrobras matriz: 33.000.167/0001-01)
        payload = {
            "tipo": "Cliente",
            "tipo_pessoa": "PJ",
            "nome_razao": "Indústria Metalúrgica São João Ltda",
            "nome_fantasia": "Metalúrgica São João",
            "cnpj_cpf": "33.000.167/0001-01",
            "telefone": "(11) 98765-4321",
            "email": "Contato@SaoJoao.com.br",
            "cep": "01310-100",
            "logradouro": "Av. Paulista, 1000 - Conjunto 42 (Galpão 3)",
            "cidade": "São Paulo",
            "uf": "sp"
        }

        response = self.client.post('/api/clientes-fornecedores/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Conferência da sanitização universal
        self.assertEqual(response.data['nome_razao'], 'INDUSTRIA METALURGICA SAO JOAO LTDA')
        self.assertEqual(response.data['nome_fantasia'], 'METALURGICA SAO JOAO')
        self.assertEqual(response.data['cnpj_cpf'], '33000167000101')
        self.assertEqual(response.data['telefone'], '11987654321')
        self.assertEqual(response.data['email'], 'contato@saojoao.com.br')
        self.assertEqual(response.data['uf'], 'SP')
        self.assertIn('GALPAO 3', response.data['logradouro'])

    def test_criar_cliente_pf_com_cpf_valido(self):
        """Valida criação de Cliente PF com algoritmo módulo 11 válido."""
        self.client.force_authenticate(user=self.operador_comercial)
        
        # CPF válido conhecido (ex: 529.982.247-25)
        payload = {
            "tipo": "Cliente",
            "tipo_pessoa": "PF",
            "nome_razao": "Carlos Eduardo da Silva",
            "cnpj_cpf": "529.982.247-25",
            "telefone": "(19) 99887-1122"
        }

        response = self.client.post('/api/clientes-fornecedores/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome_razao'], 'CARLOS EDUARDO DA SILVA')
        self.assertEqual(response.data['cnpj_cpf'], '52998224725')

    def test_rejeitar_cpf_invalido_e_digitos_repetidos(self):
        """Testa rejeição estrita de CPF matematicamente incorreto ou com dígitos repetidos."""
        self.client.force_authenticate(user=self.operador_comercial)

        # 1. Dígitos repetidos
        payload_repetido = {
            "tipo": "Cliente",
            "tipo_pessoa": "PF",
            "nome_razao": "Teste Invalido",
            "cnpj_cpf": "111.111.111-11",
            "telefone": "(11) 98888-7777"
        }
        res_rep = self.client.post('/api/clientes-fornecedores/', payload_repetido, format='json')
        self.assertEqual(res_rep.status_code, status.HTTP_400_BAD_REQUEST)
        detalhes_rep = res_rep.data.get('details', res_rep.data)
        self.assertIn('cnpj_cpf', detalhes_rep)

        # 2. Dígito verificador errado
        payload_errado = {
            "tipo": "Cliente",
            "tipo_pessoa": "PF",
            "nome_razao": "Teste Invalido 2",
            "cnpj_cpf": "529.982.247-99",
            "telefone": "(11) 98888-7777"
        }
        res_err = self.client.post('/api/clientes-fornecedores/', payload_errado, format='json')
        self.assertEqual(res_err.status_code, status.HTTP_400_BAD_REQUEST)
        detalhes_err = res_err.data.get('details', res_err.data)
        self.assertIn('cnpj_cpf', detalhes_err)

    def test_cadastro_rapido_agil_apenas_nome_e_telefone(self):
        """Valida que clientes avulsos de balcão podem ser cadastrados apenas com Nome e Telefone."""
        self.client.force_authenticate(user=self.operador_comercial)

        payload_rapido = {
            "tipo": "Cliente",
            "tipo_pessoa": "PF",
            "nome_razao": "João do Caminhão Avulso",
            "telefone": "(11) 97766-5544"
        }
        response = self.client.post('/api/clientes-fornecedores/', payload_rapido, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nome_razao'], 'JOAO DO CAMINHAO AVULSO')
        self.assertIsNone(response.data['cnpj_cpf'])

    def test_blindagem_anti_duplicacao_cpf_cnpj(self):
        """Garante que o sistema impeça cadastrar o mesmo CPF/CNPJ em duplicidade."""
        self.client.force_authenticate(user=self.operador_comercial)

        # Cadastro do primeiro cliente
        payload_1 = {
            "tipo": "Cliente",
            "tipo_pessoa": "PJ",
            "nome_razao": "Empresa Primária Ltda",
            "cnpj_cpf": "33.000.167/0001-01",
            "telefone": "(11) 98888-1111"
        }
        res_1 = self.client.post('/api/clientes-fornecedores/', payload_1, format='json')
        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)

        # Tentativa de cadastro do segundo cliente com o mesmo CNPJ
        payload_2 = {
            "tipo": "Cliente",
            "tipo_pessoa": "PJ",
            "nome_razao": "Outra Empresa Duplicada",
            "cnpj_cpf": "33.000.167/0001-01",
            "telefone": "(11) 99999-2222"
        }
        res_2 = self.client.post('/api/clientes-fornecedores/', payload_2, format='json')
        self.assertEqual(res_2.status_code, status.HTTP_400_BAD_REQUEST)
        detalhes_2 = res_2.data.get('details', res_2.data)
        self.assertIn('cnpj_cpf', detalhes_2)
        self.assertIn('já está cadastrado', str(detalhes_2['cnpj_cpf'][0]))

    def test_soft_delete_cliente(self):
        """Verifica que o soft delete inativa o cliente sem apagar fisicamente do banco de dados."""
        self.client.force_authenticate(user=self.operador_comercial)

        cliente = ClienteFornecedor.objects.create(
            nome_razao='CLIENTE PARA SOFT DELETE',
            telefone='11999999999',
            tipo='Cliente'
        )

        response = self.client.delete(f'/api/clientes-fornecedores/{cliente.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Registro ainda existe no banco com deleted_at preenchido
        cliente = ClienteFornecedor.all_objects.get(pk=cliente.id)
        self.assertIsNotNone(cliente.deleted_at)

        # Não deve constar na listagem da API
        res_list = self.client.get('/api/clientes-fornecedores/')
        self.assertEqual(res_list.data['count'], 0)

    def test_rbac_permissoes_comercial_e_compras(self):
        """Testa o controle de acesso dinâmico RBAC para clientes e fornecedores."""
        # 1. Usuário sem permissão recebe 403
        self.client.force_authenticate(user=self.operador_sem_permissao)
        res_sem = self.client.get('/api/clientes-fornecedores/')
        self.assertEqual(res_sem.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Operador de compras acessa listagem
        self.client.force_authenticate(user=self.operador_compras)
        res_compras = self.client.get('/api/clientes-fornecedores/?tipo=Fornecedor')
        self.assertEqual(res_compras.status_code, status.HTTP_200_OK)


class EquipamentoEVinculosAPITestCase(CadastrosBaseTestCase):
    """Testes de Equipamentos e Transferência Histórica de Vínculos com Clientes."""

    def test_criar_equipamento_com_placa_e_identificacao(self):
        """Valida criação de equipamento com máscara de placa antiga e Mercosul."""
        self.client.force_authenticate(user=self.operador_comercial)

        # Placa antiga
        payload_1 = {
            "placa": "ABC-1234",
            "identificacao": "Caminhão Pipa Mercedes 1620",
            "descricao": "Reforma geral da caçamba e solda do chassi"
        }
        res_1 = self.client.post('/api/equipamentos/', payload_1, format='json')
        self.assertEqual(res_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_1.data['placa'], 'ABC1234')
        self.assertEqual(res_1.data['identificacao'], 'CAMINHAO PIPA MERCEDES 1620')

        # Placa Mercosul
        payload_2 = {
            "placa": "BRA2E19",
            "identificacao": "Cavalo Mecânico Scania R450",
            "descricao": "Solda de quinta roda"
        }
        res_2 = self.client.post('/api/equipamentos/', payload_2, format='json')
        self.assertEqual(res_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_2.data['placa'], 'BRA2E19')

    def test_transferencia_historica_de_equipamento(self):
        """
        Valida que a transferência de um equipamento para um novo cliente desativa o vínculo
        anterior mantendo a linha do tempo histórica íntegra para não quebrar orçamentos passados.
        """
        self.client.force_authenticate(user=self.operador_comercial)

        # Clientes
        cliente_a = ClienteFornecedor.objects.create(
            nome_razao="TRANSPORTADORA ALFA LTDA",
            telefone="11911111111"
        )
        cliente_b = ClienteFornecedor.objects.create(
            nome_razao="LOGISTICA BETA S/A",
            telefone="11922222222"
        )

        # Equipamento
        equipamento = Equipamento.objects.create(
            placa="XYZ9876",
            identificacao="Carreta Randon 3 Eixos",
            descricao="Reforma de assoalho"
        )

        # 1. Vinculação inicial ao Cliente A
        vinculo_1 = ClienteEquipamento.objects.create(
            cliente=cliente_a,
            equipamento=equipamento,
            is_ativo=True
        )

        # Checa cliente atual
        res_eq = self.client.get(f'/api/equipamentos/{equipamento.id}/')
        self.assertEqual(res_eq.data['cliente_atual']['id'], cliente_a.id)

        # 2. Transferência para o Cliente B via endpoint de transferência
        payload_transf = {"novo_cliente_id": cliente_b.id}
        res_transf = self.client.post(f'/api/equipamentos/{equipamento.id}/transferir/', payload_transf, format='json')
        self.assertEqual(res_transf.status_code, status.HTTP_200_OK)

        # 3. Verifica que o vínculo anterior foi inativado e o novo está ativo
        vinculo_1.refresh_from_db()
        self.assertFalse(vinculo_1.is_ativo)

        res_eq_novo = self.client.get(f'/api/equipamentos/{equipamento.id}/')
        self.assertEqual(res_eq_novo.data['cliente_atual']['id'], cliente_b.id)

        # 4. Histórico completo de proprietários contém 2 registros
        res_hist = self.client.get(f'/api/equipamentos/{equipamento.id}/historico_proprietarios/')
        self.assertEqual(res_hist.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_hist.data), 2)
        self.assertEqual(res_hist.data[0]['cliente_id'], cliente_b.id)
        self.assertTrue(res_hist.data[0]['is_ativo'])
        self.assertEqual(res_hist.data[1]['cliente_id'], cliente_a.id)
        self.assertFalse(res_hist.data[1]['is_ativo'])


class AnexoGeralClienteAPITestCase(CadastrosBaseTestCase):
    """Testes de Upload e Download Seguro de Anexos de Clientes."""

    def test_upload_e_download_anexo_seguro(self):
        """Valida o envio de arquivo PDF e download com headers forçados."""
        self.client.force_authenticate(user=self.operador_comercial)

        cliente = ClienteFornecedor.objects.create(
            nome_razao="CLIENTE COM ANEXOS",
            telefone="11988887777"
        )

        arquivo_conteudo = b"%PDF-1.4 Mock de Contrato Social da Empresa em PDF"
        arquivo = SimpleUploadedFile("contrato_social.pdf", arquivo_conteudo, content_type="application/pdf")

        # Upload
        res_upload = self.client.post(
            '/api/anexos-gerais-clientes/',
            {
                "cliente": cliente.id,
                "nome_documento": "Contrato Social Registrado na Junta",
                "arquivo": arquivo
            },
            format='multipart'
        )
        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        anexo_id = res_upload.data['id']
        self.assertEqual(res_upload.data['nome_documento'], 'CONTRATO SOCIAL REGISTRADO NA JUNTA')

        # Download seguro
        res_download = self.client.get(f'/api/anexos-gerais-clientes/{anexo_id}/download/')
        self.assertEqual(res_download.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', res_download['Content-Disposition'])
        self.assertEqual(res_download['X-Content-Type-Options'], 'nosniff')

    def test_rejeitar_extensao_proibida(self):
        """Valida bloqueio de scripts executáveis (.exe, .sh, .py)."""
        self.client.force_authenticate(user=self.operador_comercial)

        cliente = ClienteFornecedor.objects.create(
            nome_razao="CLIENTE COM SCRIPT",
            telefone="11988887777"
        )

        arquivo = SimpleUploadedFile("malware.exe", b"MZ Mock executavel", content_type="application/x-dosexec")

        res_upload = self.client.post(
            '/api/anexos-gerais-clientes/',
            {
                "cliente": cliente.id,
                "nome_documento": "Executável Inválido",
                "arquivo": arquivo
            },
            format='multipart'
        )
        self.assertEqual(res_upload.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('não permitida', str(res_upload.data))


class UtilitariosConsultaAPITestCase(CadastrosBaseTestCase):
    """Testes dos endpoints utilitários de validação antecipada e consulta pública de CNPJ."""

    def test_verificar_documento_on_blur(self):
        """Valida a checagem antecipada de CPF e detecção de duplicidade."""
        self.client.force_authenticate(user=self.operador_comercial)

        # 1. CPF Válido e não cadastrado
        res_valido = self.client.get('/api/utilitarios/verificar-documento/?documento=529.982.247-25&tipo_pessoa=PF')
        self.assertEqual(res_valido.status_code, status.HTTP_200_OK)
        self.assertTrue(res_valido.data['valido'])
        self.assertFalse(res_valido.data['duplicado'])

        # 2. CPF Inválido
        res_inv = self.client.get('/api/utilitarios/verificar-documento/?documento=111.111.111-11&tipo_pessoa=PF')
        self.assertEqual(res_inv.status_code, status.HTTP_200_OK)
        self.assertFalse(res_inv.data['valido'])

        # 3. Cadastra cliente com o CPF válido
        ClienteFornecedor.objects.create(
            nome_razao="MARIA SILVA",
            cnpj_cpf="52998224725",
            telefone="11999998888",
            tipo_pessoa="PF"
        )

        # 4. Checa novamente o mesmo CPF -> deve acusar duplicidade
        res_dup = self.client.get('/api/utilitarios/verificar-documento/?documento=529.982.247-25&tipo_pessoa=PF')
        self.assertEqual(res_dup.status_code, status.HTTP_200_OK)
        self.assertTrue(res_dup.data['valido'])
        self.assertTrue(res_dup.data['duplicado'])
        self.assertEqual(res_dup.data['existente']['nome_razao'], 'MARIA SILVA')

    @patch('apps.cadastros.utils_cnpj.urllib.request.urlopen')
    def test_consulta_cnpj_proxy_mock(self, mock_urlopen):
        """Valida o endpoint proxy de consulta de CNPJ com resposta simulada da BrasilAPI."""
        self.client.force_authenticate(user=self.operador_comercial)

        # Mock da resposta JSON da BrasilAPI
        mock_response_data = {
            "razao_social": "EMPRESA DE TESTE MOCK LTDA",
            "nome_fantasia": "MOCK SOLDAS",
            "cnpj": "33000167000101",
            "cep": "01310100",
            "descricao_tipo_de_logradouro": "AVENIDA",
            "logradouro": "PAULISTA",
            "numero": "1000",
            "bairro": "BELA VISTA",
            "municipio": "SAO PAULO",
            "uf": "SP",
            "ddd_telefone_1": "1133334444",
            "email": "contato@mock.com.br"
        }
        
        mock_cm = mock_urlopen.return_value.__enter__.return_value
        mock_cm.status = 200
        mock_cm.read.return_value = json.dumps(mock_response_data).encode('utf-8')

        response = self.client.get('/api/utilitarios/consulta-cnpj/33.000.167/0001-01/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['data']['nome_razao'], 'EMPRESA DE TESTE MOCK LTDA')
        self.assertEqual(response.data['data']['cidade'], 'SAO PAULO')
        self.assertEqual(response.data['data']['uf'], 'SP')
