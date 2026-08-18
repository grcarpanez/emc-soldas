# AGENTS.md - Contexto Operacional para IA e Desenvolvedores

Este arquivo estabelece o contexto arquitetural, regras de segurança, padrões de codificação e protocolos de governança para qualquer IA ou desenvolvedor atuando no sistema **EMC Soldas**.

---

## 1. Idioma e Comunicação

- Responder e documentar **sempre em português do Brasil** (`pt-BR`).
- Comentários no código, mensagens de commit, documentações e saídas de log devem ser em português do Brasil.

---

## 2. Stack Tecnológica e Arquitetura

- **Linguagem Backend:** Python 3 (versão 3.10+)
- **Framework Backend:** Django + Django REST Framework (DRF)
- **Banco de Dados:** MySQL (InnoDB, 29 entidades com integridade referencial)
- **Frontend:** Progressive Web App (PWA) client-side com HTML5 semântico, Vanilla JavaScript moderno (ES6+) e CSS3 puro.
- **Design System:** *Industrial Integrity* (especificado em `docs/DESIGN.md`) com 0px border-radius (cantos estritamente retos), tipografia técnica (IBM Plex Sans, Inter, JetBrains Mono) e paleta industrial (Dark Iron `#131313`, Steel Gray `#71797E`, Brushed Metal `#A5A9B4`, Rust Orange `#B7410E`). Sem frameworks como Tailwind ou Bootstrap.
- **Service Workers:** Suporte a cache de assets e resiliência offline (`sw.js`).
- **Arquitetura:** Estritamente desacoplada. O backend opera exclusivamente como API REST (JSON). Toda a regra de negócio, validações, persistência e auditoria residem no servidor. O frontend é uma aplicação client-side isolada que consome a API via Fetch/AJAX.
- **Proibição de Pastas Legadas:** Não utilizar termos ou dependências de servidores legados como `public_html`, `public`, `htdocs` ou `www` na arquitetura da aplicação.

---

## 3. Ambientes do Projeto

- **Ambiente de Desenvolvimento Local:**
  - Banco de Dados MySQL local (via XAMPP ou serviço MySQL local na porta 3306).
  - Servidor de desenvolvimento Django nativo (`python manage.py runserver`).
  - Frontend servido estaticamente.
  - Fallback automático para `console.EmailBackend` em desenvolvimento local.
- **Ambiente de Produção:**
  - Cloud PaaS (ex: Render, PythonAnywhere, com compatibilidade arquitetural para AWS).
  - Variáveis de ambiente sensíveis (`SECRET_KEY`, `ENCRYPTION_KEY`, dados do banco) injetadas diretamente na memória do processo via `os.environ`.
  - Servidor WSGI/ASGI de alta performance (Gunicorn / Uvicorn).

---

## 4. Estrutura de Pastas do Repositório

```text
/ (raiz do projeto)
├── AGENTS.md                  # Contexto operacional e protocolo para IA
├── .gitignore                 # Arquivos e pastas ignorados pelo controle de versão
├── docs/                      # Documentação de especificação e arquivos vivos
│   ├── FSD.md                 # Documento de Especificação Funcional completo
│   ├── DESIGN.md              # Guia do Design System (Industrial Integrity)
│   ├── INSUMOS.md             # Inventário de insumos do projeto
│   ├── PLANO.md               # Plano de construção master em 15 fases
│   ├── STATUS.md              # Arquivo vivo de status e progresso
│   └── ERROS.md               # Arquivo vivo de registro e prevenção de erros
├── backend/                   # Aplicação Backend (Django REST Framework)
│   ├── manage.py              # Utilitário de linha de comando do Django
│   ├── requirements.txt       # Dependências Python do projeto
│   ├── config/                # Configurações do projeto Django
│   │   ├── __init__.py
│   │   ├── settings.py        # Configurações com leitura via os.environ
│   │   ├── urls.py            # Roteamento central da API REST
│   │   ├── wsgi.py            # Ponto de entrada WSGI
│   │   └── asgi.py            # Ponto de entrada ASGI
│   ├── core/                  # Núcleo compartilhado (Base Models, Permissões, Middlewares)
│   │   ├── __init__.py
│   │   ├── models.py          # SoftDeleteModel e AuditableModel
│   │   ├── permissions.py     # Classes de permissão RBAC (10 toggles)
│   │   ├── middleware.py      # Middlewares de segurança e auditoria
│   │   ├── exceptions.py      # Tratamento global de erros (sem vazar tracebacks)
│   │   └── utils.py           # Utilitários (AES-256 Fernet, Validação CPF Módulo 11)
│   ├── apps/                  # Módulos da aplicação (Django Apps)
│   │   ├── authentication/    # Usuários, Sessão, Soft Lock, Hard Lock, JWT
│   │   ├── cadastros/         # Clientes, Fornecedores, Equipamentos, Vínculos
│   │   ├── catalogo/          # Dicionários UOM/Atributos, Itens, Produtos, BOM
│   │   ├── compras/           # Notas Fiscais de Entrada e Retroalimentação de Custos
│   │   ├── orcamentos/        # Orçamentos, Snapshots, Validade e Propostas
│   │   ├── faturamento/       # Pré-Faturas, Faturas Finais e Conta Corrente
│   │   ├── financeiro/        # Contas a Pagar/Receber, Caixa Real, Cartões, Estornos
│   │   ├── conciliacao/       # Conciliação Bancária Split-Screen (OFX/CSV)
│   │   ├── administracao/     # Configurações Globais, SMTP, Expurgo de Logs, Lixeira
│   │   └── relatorios/        # Dashboards, Central Analítica, DRE, Exportações
│   ├── logs/                  # Arquivos físicos diários de log (rotativos)
│   └── media/                 # Uploads protegidos de arquivos (PDF/XML/CSV)
├── frontend/                  # Aplicação Frontend PWA (Client-Side)
│   ├── index.html             # Shell da SPA / PWA
│   ├── manifest.json          # Manifesto do PWA
│   ├── sw.js                  # Service Worker com cache e resiliência offline
│   └── assets/
│       ├── css/
│       │   ├── industrial-integrity.css # Tokens, tipografia, componentes (DESIGN.md)
│       │   └── layout.css               # Grid 12/4 colunas, sidebar, topbar, cards
│       ├── js/
│       │   ├── config.js      # URLs base da API e configurações globais
│       │   ├── api.js         # Cliente HTTP Fetch com CSRF, JWT e tratamento de erros
│       │   └── app.js         # Inicialização da SPA, roteamento e eventos de UI
│       └── icons/             # Ícones do PWA
└── tools/                     # Scripts de apoio operacional
    └── generate_keys.py       # Gerador de chaves criptográficas de 64 caracteres
```

---

## 5. Comandos Principais

- **Criar ambiente virtual:** `python -m venv venv`
- **Ativar ambiente virtual (Windows):** `.\venv\Scripts\activate`
- **Ativar ambiente virtual (Linux/Mac):** `source venv/bin/activate`
- **Instalar dependências:** `pip install -r backend/requirements.txt`
- **Gerar migrations:** `python backend/manage.py makemigrations`
- **Aplicar migrations:** `python backend/manage.py migrate`
- **Criar superusuário inicial:** `python backend/manage.py createsuperuser`
- **Popular dados iniciais (Seeders):** `python backend/manage.py seed_initial_data`
- **Executar servidor de desenvolvimento:** `python backend/manage.py runserver`
- **Executar testes automatizados:** `python backend/manage.py test backend/`
- **Gerar chaves criptográficas seguras:** `python tools/generate_keys.py`

---

## 6. Regras de Segurança e Blindagem Técnica

1. **Proteção contra SQL Injection (SQLi):**
   - Proibição absoluta do uso de queries SQL cruas (`.raw()`, `cursor.execute()`).
   - Uso exclusivo e obrigatório do Django ORM para todas as interações com o banco de dados.
2. **Proteção contra Cross-Site Scripting (XSS):**
   - Sanitização e escape automático de todo dado renderizado no DOM pelo Vanilla JS (`textContent`, templates parametrizados).
   - Proibição de inserção direta de HTML não sanitizado (`innerHTML`) com dados de entrada de usuários.
3. **Proteção contra Cross-Site Request Forgery (CSRF):**
   - Cookies HttpOnly configurados com flag `SameSite=Strict`.
   - Exigência mandatória do cabeçalho `X-CSRFToken` em todas as requisições de mutação (POST, PUT, PATCH, DELETE).
4. **Autenticação e Gestão de Sessão (JWT via Cookie HttpOnly):**
   - O token JWT é armazenado estritamente como Cookie de Sessão HttpOnly, garantindo "Morte Súbita" da sessão ao fechar o navegador, reiniciar o sistema ou sofrer queda de energia.
   - Inacessível via JavaScript (`document.cookie`), impedindo roubo de credenciais via XSS.
5. **Soft Lock (30 minutos de ociosidade) e Hard Lock:**
   - Soft Lock automático após 30 minutos sem interação do usuário.
   - Destravamento ágil via PIN de 6 dígitos numéricos (ou WebAuthn).
   - Hard Lock com invalidação de sessão após 3 erros consecutivos no PIN ou ao término da validade mestre do token.
6. **Proteção Anti-Bruteforce e Rate Limiting (Throttling):**
   - Bloqueio automático de 1 hora para contas/IPs que registrarem 5 falhas consecutivas de login em 15 minutos (`429 Too Many Requests`). Desbloqueio manual exclusivo pelo Administrador.
   - Throttle global padrão: 100 requisições/minuto por usuário/IP.
   - Throttle restritivo para relatórios e PDFs pesados (`heavy_reports`): 5 requisições/minuto.
7. **Controle de Acesso Baseado em Papéis (RBAC com 10 Toggles Dinâmicos):**
   - Validação mandatória no backend através de classes de permissão do DRF (`HasPermissionToggle`) em cada endpoint.
   - Retorno estrito de `403 Forbidden` quando o colaborador não tiver o toggle correspondente ativo.
   - Tratamento visual no frontend: ocultação total de abas/menus restritos e exibição de cadeado `[🔒]` com tooltip explicativo em cards de métricas.
8. **Proibição Absoluta de Hard Delete (100% Soft Delete na V1):**
   - Nenhuma rota de API ou operação de negócio realiza comandos `DELETE` físicos no MySQL.
   - Exclusões gravam `deleted_at = NOW()` e `deleted_by_id = request.user.id`.
   - Lixeira com visão segregada: Administrador acessa Lixeira Global (audita e restaura qualquer registro); Operador acessa Minha Lixeira (`deleted_by_id = request.user.id`).
9. **Criptografia Simétrica de Dados Sensíveis (AES-256 / Fernet):**
   - Senhas de SMTP configuradas no painel administrativo são armazenadas no banco cifradas via AES-256 (chave `ENCRYPTION_KEY` lida via `os.environ`).
   - A API nunca devolve a senha real em texto puro nas respostas JSON.
10. **Segurança de Uploads e Diretório NoExec:**
    - Validação profunda de MIME-Type real e magic bytes (não confiar apenas na extensão informada).
    - Remoção de metadados EXIF em imagens para prevenir esteganografia.
    - Diretório de mídia (`backend/media/`) configurado sem permissão de execução de scripts (NoExec).
    - Cabeçalhos estritos `Content-Disposition: attachment` e `Content-Type` forçados no download.
11. **Logs Físicos Seguros e Não-Vazamento de Tracebacks:**
    - Erros e falhas graves são gravados exclusivamente em arquivos físicos diários (`backend/logs/app-YYYY-MM-DD.log`), gerenciados pela tabela de manifesto `ControleArquivoLog`.
    - Respostas de erro 500 da API REST devolvem apenas JSON amigável e padronizado (`{ "status": "error", "message": "Ocorreu um erro interno. Tente novamente." }`), sem vazar o Traceback técnico do Python para o cliente.

---

## 7. Protocolo dos Arquivos Vivos

Todo trabalho neste repositório deve seguir rigorosamente o seguinte ciclo:

### Antes de iniciar qualquer trabalho:
1. Ler `docs/FSD.md`.
2. Ler `docs/DESIGN.md`.
3. Ler `docs/INSUMOS.md`.
4. Ler `docs/PLANO.md`.
5. Ler `docs/STATUS.md`.
6. Ler `docs/ERROS.md`.

> **Atenção:** Use sempre caminhos relativos à raiz do projeto. Não transformar estes caminhos em links absolutos. Não usar links `file:///`. Não registrar caminhos locais da máquina atual dentro do `AGENTS.md` ou nos arquivos de documentação.

### Ao terminar qualquer trabalho:
1. Atualizar `docs/STATUS.md` com o progresso real da fase e checklist.
2. Registrar erros encontrados e soluções aplicadas em `docs/ERROS.md`, se houver.
3. Informar ao usuário detalhadamente o que foi construído.
4. Informar como testar ou validar a entrega com comandos claros e roteiro prático.

---

## 8. Boas Práticas de Engenharia e Código

- **Simplicidade e Clareza:** Código legível, modular e autoexplicativo.
- **Funções Pequenas e Focadas:** Métodos com responsabilidade única (Single Responsibility Principle).
- **Nomes Descritivos:** Variáveis, funções e classes com nomes claros em português ou inglês padronizado, respeitando a convenção do FSD.
- **Convenção de Nomes Mandatória:**
  - Classes Django ORM: PascalCase singular (`LancamentoFinanceiro`, `OrcamentoItem`).
  - Tabelas MySQL (`db_table`): snake_case plural (`lancamentos_financeiros`, `orcamento_itens`).
  - Atributos e colunas: snake_case (`data_pagamento`, `conciliado_por_id`).
  - Rotas REST: kebab-case plural (`/api/lancamentos-financeiros/`, `/api/orcamentos/`).
- **Sem Escopo Fantasma:** Não inventar funcionalidades fora do escopo definido no `docs/FSD.md`.
- **Tratamento de Exceções:** Tratar casos de borda e falhas de rede/banco com respostas graciosas e seguras.
- **Design System Fiel:** Seguir `docs/DESIGN.md` em 100% dos componentes visuais, respeitando a estética industrial, tipografia, ausência de cantos arredondados e contrastes adequados.
