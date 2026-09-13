# Planejamento: Implementação da Busca e Preenchimento Automático por CEP no Cadastro de Clientes/Fornecedores (PWA v4.25)

## 1. Metadados
- **Data:** 2026-09-13
- **Autor:** Antigravity AI & EMC Soldas Team
- **Status:** Concluído
- **Registro do Proceed:** Aprovado pelo usuário em 2026-09-13 20:15:01 BRT.

---

## 2. Contexto e Objetivos
Ao cadastrar ou editar um cliente/fornecedor (`frontend/assets/js/views/cadastros-view.js`), o sistema atualmente já realizava a consulta automática via CNPJ (Receita Federal) ao digitar 14 dígitos e sair do campo (`blur`). No entanto, para cadastros onde o CEP é inserido manualmente (ou para Pessoas Físicas com CPF), o evento de saída (`blur` / `exit`) do campo de CEP (`#comp-cep`) não realizava a busca de endereço nem preenchia os campos de logradouro, bairro, cidade e UF.

O objetivo foi:
1. Criar o utilitário backend `apps/cadastros/utils_cep.py` com integração pública defensiva: consulta primária via **BrasilAPI** com fallback secundário automático para o **ViaCEP**, sanitização em maiúsculas sem acento e tratamento de erros de rede/timeout.
2. Criar o endpoint REST autenticado `GET /api/utilitarios/consulta-cep/<cep>/` (`ConsultaCepAPIView`).
3. Integrar a rota no `urls.py` de cadastros e registrá-la em `frontend/assets/js/config.js`.
4. No frontend (`cadastros-view.js`), adicionar o spinner visual (`#cep-spinner`), aviso contextual e o listener assíncrono `handleAutoConsultaCep` no evento `blur` do campo `#comp-cep`, preenchendo automaticamente `logradouro`, `bairro`, `cidade`, `uf` e posicionando o foco diretamente no campo `#comp-numero`.
5. Adicionar testes unitários automatizados para a consulta de CEP em `backend/apps/cadastros/tests.py`.
6. Cumprir a **Regra 12 de Versionamento PWA** elevando o cache do Service Worker (`frontend/sw.js`) e as tags de script no `frontend/index.html` para **`v4.25`**.

---

## 3. Decisões Técnicas e Arquiteturais
- **Backend (`apps/cadastros/utils_cep.py`):** Sanitização com `limpar_apenas_digitos`, checagem de exatamente 8 dígitos. Chamada primária para BrasilAPI (`https://brasilapi.com.br/api/cep/v1/{cep}`) com timeout de 5 segundos. Em caso de erro ou resposta diferente de 200, fallback gracioso para ViaCEP (`https://viacep.com.br/ws/{cep}/json/`) com timeout de 5 segundos. Sanitização dos campos para maiúsculo sem acento (`sanitizar_texto_maiusculo`).
- **Endpoint (`ConsultaCepAPIView`):** `GET /api/utilitarios/consulta-cep/<cep>/` com permissão `permissions.IsAuthenticated`.
- **Frontend (`cadastros-view.js`):** Spinner `#cep-spinner` posicionado relativamente no container do input. Listener `handleAutoConsultaCep` ativado no `blur`. Preenchimento de logradouro, bairro, cidade e uf, seguido de foco em `#comp-numero` e toast informativo.

---

## 4. Arquivos Modificados / Criados
- `backend/apps/cadastros/utils_cep.py` [CRIADO]
- `backend/apps/cadastros/views.py` [MODIFICADO]
- `backend/apps/cadastros/urls.py` [MODIFICADO]
- `backend/apps/cadastros/tests.py` [MODIFICADO]
- `frontend/assets/js/config.js` [MODIFICADO]
- `frontend/assets/js/views/cadastros-view.js` [MODIFICADO]
- `frontend/sw.js` [MODIFICADO]
- `frontend/index.html` [MODIFICADO]
- `docs/STATUS.md` [MODIFICADO]

---

## 5. Relatório de Execução e Verificação
- **Suíte de Cadastros:** 23 testes executados e aprovados com 100% de sucesso (`OK`). Cobre sucesso via BrasilAPI, fallback para ViaCEP sob falha da BrasilAPI, validação de formato e bloqueio de acesso não autenticado.
- **Suíte Completa do Sistema:** 181 testes executados e aprovados com 100% de sucesso (`OK`), garantindo zero regressões em todos os módulos.
- **Versionamento PWA:** Cache do Service Worker e tags de assets elevados de `v4.24` para `v4.25`.
