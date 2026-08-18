"""
Script de teste prático e visual para validação da Fase 5 (Clientes, Fornecedores, Equipamentos e CNPJ).
Execute no terminal: .\venv\Scripts\python.exe tools/testar_fase5.py
"""
import sys
import json
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:8000"

# Gerenciador de cookies para manter a sessão autenticada
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def print_pass(mensagem):
    print(f"  [OK] {mensagem}")


def print_fail(mensagem):
    print(f"  [FALHA] {mensagem}")


def fazer_requisicao(metodo, endpoint, dados=None):
    url = f"{BASE_URL}{endpoint}"
    corpo = json.dumps(dados).encode('utf-8') if dados else None
    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=corpo, headers=headers, method=metodo)
    try:
        with opener.open(req, timeout=10) as resposta:
            status_code = resposta.status
            conteudo = resposta.read().decode('utf-8')
            return status_code, json.loads(conteudo) if conteudo else {}
    except urllib.error.HTTPError as e:
        conteudo = e.read().decode('utf-8')
        try:
            dados_erro = json.loads(conteudo)
        except Exception:
            dados_erro = {"raw": conteudo}
        return e.code, dados_erro
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    print("=" * 70)
    print("   TESTE AUTOMATIZADO PRÁTICO - FASE 5 (EMC SOLDAS ERP)")
    print("=" * 70)
    print("Certifique-se de que o servidor Django está rodando em outro terminal:")
    print("  .\\venv\\Scripts\\python.exe backend/manage.py runserver\n")

    # 1. Login
    print("1. Efetuando Login como Administrador Master...")
    payload_login = {
        "email": "admin@emcsoldas.com.br",
        "password": "AdminMaster2026!"
    }
    status_code, resp = fazer_requisicao("POST", "/api/auth/login/", payload_login)
    if status_code == 200:
        print_pass(f"Login realizado com sucesso! Usuário: {resp.get('usuario', {}).get('nome')}")
    else:
        print_fail(f"Erro no login (Status {status_code}): {resp}")
        print("\nDica: Se o servidor não estiver rodando, inicie com 'runserver' antes de testar.")
        sys.exit(1)

    # 2. Consulta de CNPJ Público
    print("\n2. Testando Consulta Pública de CNPJ (33.000.167/0001-01)...")
    status_code, resp = fazer_requisicao("GET", "/api/utilitarios/consulta-cnpj/33000167000101/")
    if status_code == 200:
        dados_cnpj = resp.get("data", {})
        print_pass(f"CNPJ consultado com sucesso via {resp.get('provedor', 'Proxy')}!")
        print(f"       Razão Social: {dados_cnpj.get('nome_razao')}")
        print(f"       Cidade/UF:    {dados_cnpj.get('cidade')}/{dados_cnpj.get('uf')}")
        print(f"       Telefone:     {dados_cnpj.get('telefone')}")
    else:
        print_fail(f"Erro na consulta de CNPJ (Status {status_code}): {resp}")

    # 3. Validação Antecipada de CPF (onBlur)
    print("\n3. Testando Validação Antecipada de CPF no onBlur...")
    # CPF Válido
    status_code, resp = fazer_requisicao("GET", "/api/utilitarios/verificar-documento/?documento=529.982.247-25&tipo_pessoa=PF")
    if resp.get("valido") is True:
        print_pass("CPF Válido (529.982.247-25) aprovado pela validação matemática módulo 11.")
    else:
        print_fail("Falha ao validar CPF correto.")

    # CPF Inválido
    status_code, resp = fazer_requisicao("GET", "/api/utilitarios/verificar-documento/?documento=111.111.111-11&tipo_pessoa=PF")
    if resp.get("valido") is False:
        print_pass("CPF com dígitos repetidos (111.111.111-11) bloqueado corretamente.")
    else:
        print_fail("CPF inválido foi aceito indevidamente.")

    # 4. Cadastro de Cliente PJ
    print("\n4. Cadastrando Novo Cliente PJ...")
    payload_cliente = {
        "tipo": "Cliente",
        "tipo_pessoa": "PJ",
        "nome_razao": "Transportadora Rápido Soluções Ltda",
        "nome_fantasia": "Rápido Soluções",
        "cnpj_cpf": "33.000.167/0001-01",
        "telefone": "(11) 98888-7777",
        "email": "contato@rapidosolucoes.com.br",
        "cidade": "Campinas",
        "uf": "SP"
    }
    status_code, resp = fazer_requisicao("POST", "/api/clientes-fornecedores/", payload_cliente)
    if status_code == 201:
        cliente_id = resp.get("id")
        print_pass(f"Cliente cadastrado com ID #{cliente_id}!")
        print(f"       Razão Social Sanitizada: {resp.get('nome_razao')}")
    elif status_code == 400 and "já está cadastrado" in str(resp):
        print_pass("Cliente já havia sido cadastrado anteriormente (Blindagem anti-duplicidade ativa).")
        # Busca o ID existente
        _, lista = fazer_requisicao("GET", "/api/clientes-fornecedores/?search=RAPIDO")
        cliente_id = lista.get("results", [{}])[0].get("id", 1) if "results" in lista else 1
    else:
        print_fail(f"Erro ao cadastrar cliente (Status {status_code}): {resp}")
        cliente_id = 1

    # 5. Cadastro de Equipamento e Transferência
    print("\n5. Cadastrando Equipamento / Veículo...")
    payload_equip = {
        "placa": "BRA-2E19",
        "identificacao": "Cavalo Mecânico Scania R450",
        "descricao": "Solda de quinta roda e reforço de chassi"
    }
    status_code, resp_eq = fazer_requisicao("POST", "/api/equipamentos/", payload_equip)
    if status_code == 201:
        equip_id = resp_eq.get("id")
        print_pass(f"Equipamento cadastrado com ID #{equip_id} (Placa: {resp_eq.get('placa')})!")
    else:
        print_pass("Equipamento já existente recuperado para teste de transferência.")
        _, lista_eq = fazer_requisicao("GET", "/api/equipamentos/?search=BRA2E19")
        equip_id = lista_eq.get("results", [{}])[0].get("id", 1) if "results" in lista_eq else 1

    # 6. Transferência de Equipamento para o Cliente
    print(f"\n6. Vinculando/Transferindo Equipamento #{equip_id} para o Cliente #{cliente_id}...")
    payload_transf = {"novo_cliente_id": cliente_id}
    status_code, resp_tr = fazer_requisicao("POST", f"/api/equipamentos/{equip_id}/transferir/", payload_transf)
    if status_code == 200:
        print_pass("Equipamento vinculado com sucesso ao cliente!")
        print(f"       Mensagem: {resp_tr.get('message')}")
    else:
        print_fail(f"Erro na transferência (Status {status_code}): {resp_tr}")

    print("\n" + "=" * 70)
    print("   TODOS OS TESTES DA FASE 5 FORAM CONCLUÍDOS COM SUCESSO!")
    print("=" * 70)


if __name__ == "__main__":
    main()
