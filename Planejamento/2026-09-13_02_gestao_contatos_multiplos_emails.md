# Planejamento: Gestão de Contatos Corporativos e Múltiplos E-mails (PWA v4.27)

## 1. Metadados
- **Data:** 2026-09-13
- **Autor:** Antigravity AI & EMC Soldas Team
- **Status:** Concluído
- **Registro do Proceed:** Aprovado pelo usuário em 2026-09-13 21:14:52 BRT.

---

## 2. Contexto e Objetivos
Permitir que o cadastro de clientes e fornecedores opere com contatos flexíveis no estilo "agenda de smartphone" e suporte a múltiplos e-mails:
1. O contato corporativo passa a representar uma pessoa ou setor (ex: `JOÃO - COMPRAS`), tendo como único campo obrigatório o nome do responsável. Telefone, WhatsApp e e-mail tornam-se opcionais.
2. Suporte a múltiplos e-mails separados por ponto-e-vírgula (`;`) ou vírgula (`,`) tanto no e-mail corporativo principal quanto nos contatos individuais, com validação matemática individual de cada endereço.
3. Preparar a base estrutural para o futuro modal de disparo de e-mails comerciais e fiscais (com seleção de contatos e e-mails).
4. Cumprir a Regra 12 de Versionamento PWA elevando a versão do Service Worker e do shell SPA para `v4.27`.

---

## 3. Decisões Técnicas e Arquiteturais
- **Backend (`apps/cadastros/models.py`):**
  - `ClienteFornecedor.email`: alterado de `EmailField` para `CharField(max_length=255, null=True, blank=True)`.
  - `ClienteContato`: `telefone` alterado para `CharField(max_length=100, null=True, blank=True)`; inclusão do campo `email = CharField(max_length=255, null=True, blank=True)`.
- **Validação (`apps/cadastros/serializers.py`):**
  - Função utilitária `validar_multiplos_emails(value)` que faz split por `;` e `,`, valida cada e-mail via `django.core.validators.EmailValidator` e normaliza para minúsculas unificadas por `; `.
- **Frontend (`cadastros-view.js`):**
  - Campo `#comp-email` com `type="text"`, placeholder explicativo e hint.
  - Tabela de contatos com nova coluna E-MAIL(S), inputs estilizados e remoção da trava de telefone obrigatório.
- **Governança:**
  - Migrations aplicadas no MySQL (`0005_clientecontato_email_alter_clientecontato_telefone_and_more.py`).
  - Versão `v4.27` sincronizada no `sw.js` e `index.html`.

---

## 4. Arquivos Modificados / Criados
- `backend/apps/cadastros/models.py` [MODIFICADO]
- `backend/apps/cadastros/migrations/0005_clientecontato_email_alter_clientecontato_telefone_and_more.py` [CRIADO]
- `backend/apps/cadastros/serializers.py` [MODIFICADO]
- `backend/apps/cadastros/tests.py` [MODIFICADO]
- `backend/apps/orcamentos/tests.py` [MODIFICADO]
- `frontend/assets/js/views/cadastros-view.js` [MODIFICADO]
- `frontend/sw.js` [MODIFICADO]
- `frontend/index.html` [MODIFICADO]
- `docs/STATUS.md` [MODIFICADO]

---

## 5. Relatório de Execução e Verificação
- **Suíte de Cadastros:** 26 testes executados e aprovados com 100% de sucesso (`OK`). Cobre múltiplos e-mails por `;`, contatos apenas com nome, contatos com múltiplos telefones/e-mails, rejeição de e-mail malformado na lista e cadastro sem contatos.
- **Suíte Completa do Sistema:** 184 testes executados e aprovados com 100% de sucesso (`OK`), garantindo zero regressões.
- **Versionamento PWA:** Cache do Service Worker e tags de assets elevados de `v4.26` para `v4.27`.
