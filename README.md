# EMC Soldas - Gestão Industrial, Orçamentos e Tesouraria

Sistema integrado para gestão técnica e financeira especializada em caldeiraria, soldagem industrial, corte, conformação e usinagem. O sistema gerencia o fluxo operacional de ponta a ponta: cadastros corporativos, catálogo com explosão de materiais (BOM), compras com importação de documentos fiscais (XML/DANFE), orçamentos com snapshots de custo, faturamento com conta corrente, tesouraria em tempo real e conciliação bancária inteligente via OFX e CSV.

---

## 🛠️ Stack Tecnológica e Arquitetura

O sistema adota uma **arquitetura estritamente desacoplada**:

- **Backend:** Python 3 (3.10+), Django 5.x e Django REST Framework (DRF).
- **Banco de Dados:** MySQL 8.x (InnoDB com 29 entidades relacionais, B-Tree indexes e 100% Soft Delete).
- **Frontend:** Progressive Web App (PWA) client-side desenvolvido em HTML5 semântico, Vanilla JavaScript moderno (ES6+) e CSS3 puro, sem frameworks pesados (sem Bootstrap, Tailwind ou React).
- **Design System:** *Industrial Integrity* (cantos estritamente retos `0px border-radius`, tipografia técnica monoespaçada/sans e paleta industrial: Dark Iron `#131313`, Steel Gray `#71797E`, Rust Orange `#B7410E`).
- **Segurança:** Autenticação JWT armazenada em Cookie HttpOnly (`SameSite=Strict`), Soft Lock (inatividade de 30 minutos com PIN de 6 dígitos), RBAC granular com 10 toggles dinâmicos, criptografia AES-256 (Fernet) para credenciais sensíveis e proteção contra SQLi/XSS/CSRF.

---

## 📋 Pré-requisitos de Instalação

Antes de iniciar, certifique-se de ter instalado em seu ambiente:

1. **Python 3.10 ou superior** ([Download Python](https://www.python.org/downloads/))
2. **Git** ([Download Git](https://git-scm.com/))
3. **Servidor MySQL 8.0+** ou **XAMPP / MariaDB** rodando localmente na porta padrão `3306`.
4. Um navegador moderno (Google Chrome, Microsoft Edge, Mozilla Firefox).

---

## 🚀 Guia Passo a Passo: Execução Local para Testes

### 1. Clonar o Repositório
Abra o terminal (PowerShell, CMD ou Bash) e clone o projeto:
```bash
git clone https://github.com/grcarpanez/emc-soldas.git
cd emc-soldas
```

---

### 2. Configurar o Ambiente Virtual Python
Crie um ambiente virtual isolado para as dependências do backend:

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Instalar as Dependências
Com o ambiente virtual ativado, instale os pacotes necessários:
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

---

### 4. Configurar as Variáveis de Ambiente
Crie o arquivo `.env` na raiz do projeto com base no modelo fornecido:

**No Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**No Linux / macOS:**
```bash
cp .env.example .env
```

Abra o arquivo `.env` e confirme os dados de conexão com o seu MySQL local:
```env
DEBUG=True
SECRET_KEY=django-insecure-emc-soldas-dev-key-industrial-integrity-2026-secure-token-998877
ENCRYPTION_KEY=emc_soldas_aes256_master_key_local_dev_only_32_bytes_len=
ALLOWED_HOSTS=127.0.0.1,localhost

DB_ENGINE=django.db.backends.mysql
DB_NAME=emc_soldas
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500
```
> **Nota:** Em ambiente de desenvolvimento local, o envio de e-mails usa `console.EmailBackend`, imprimindo códigos e links de recuperação diretamente no terminal.

---

### 5. Preparar o Banco de Dados MySQL
Certifique-se de que o serviço do MySQL está em execução (ex: serviço local ou MySQL ativado no Painel de Controle do XAMPP).

Crie a base de dados no MySQL:
```sql
CREATE DATABASE emc_soldas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 6. Aplicar Migrations e Carregar Dados Iniciais
Aplique as migrações estruturais do Django ORM:
```bash
python backend/manage.py migrate
```

Carregue a carga inicial de dados estruturais (dicionários UOM, atributos industriais, contas padrão, meios e regras de pagamento, parâmetros globais):
```bash
python backend/manage.py seed_initial_data
```

---

### 7. Criar o Usuário Administrador
Crie um superusuário para ter acesso total ao sistema e ao painel:
```bash
python backend/manage.py createsuperuser
```
Informe nome de usuário, e-mail e senha conforme solicitado no terminal.

---

### 8. Iniciar o Servidor de Desenvolvimento (Backend)
Inicie o servidor HTTP do Django REST Framework:
```bash
python backend/manage.py runserver
```
O backend estará disponível em: **`http://127.0.0.1:8000/`**  
A raiz da API REST responde em: **`http://127.0.0.1:8000/api/`**

---

### 9. Executar o Frontend (Client-Side PWA)
O frontend é uma Single Page Application / PWA estática que se comunica via API REST. Você pode executá-lo de duas formas:

#### Opção A: Servidor HTTP Local com Python (Recomendado)
Abra um novo terminal, navegue até a pasta `frontend/` e inicie um servidor rápido na porta `5500`:
```bash
cd frontend
python -m http.server 5500
```
Acesse no seu navegador: **`http://127.0.0.1:5500`**

#### Opção B: Extensão Live Server (VS Code)
1. Abra o repositório no VS Code.
2. Clique com o botão direito sobre o arquivo `frontend/index.html`.
3. Selecione **Open with Live Server** (porta padrão `5500`).

---

## 🧪 Execução de Testes Automatizados

O sistema conta com suíte de testes automatizados cobrindo autenticação, sanitização universal, modelos ORM, regras de pagamento e integridade financeira:

```bash
# Executar todos os testes
python backend/manage.py test backend/

# Executar testes específicos por módulo
python backend/manage.py test core
python backend/manage.py test apps.authentication
python backend/manage.py test apps.catalogo
python backend/manage.py test apps.financeiro
```

---

## 📁 Estrutura de Pastas do Repositório

```text
/ (raiz do projeto)
├── README.md                  # Este guia rápido de introdução e testes locais
├── AGENTS.md                  # Protocolos mandatórios de governança e regras para IA/Devs
├── .gitignore                 # Arquivos ignorados pelo Git
├── .env.example               # Modelo de variáveis de ambiente
├── Planejamento/              # Planos de implementação e registros de aprovação (Proceed)
├── docs/                      # Arquivos vivos de especificação técnica e progresso
│   ├── FSD.md                 # Especificação Funcional Completa (30 seções)
│   ├── DESIGN.md              # Guia do Design System Industrial Integrity
│   ├── INSUMOS.md             # Inventário de insumos técnicos
│   ├── PLANO.md               # Plano construtivo master em 15 fases
│   ├── STATUS.md              # Registro vivo de status e progresso do projeto
│   └── ERROS.md               # Histórico vivo de prevenção de incidentes e erros
├── backend/                   # Backend Django REST Framework (API)
│   ├── manage.py              # CLI do Django
│   ├── requirements.txt       # Dependências Python
│   ├── config/                # Configurações do projeto Django (settings, urls, wsgi)
│   ├── core/                  # Classes base, auditoria, RBAC, middlewares e utils
│   ├── apps/                  # Módulos de negócio (authentication, cadastros, compras, etc.)
│   ├── logs/                  # Logs diários com rotação física
│   └── media/                 # Armazenamento protegido de anexos e documentos fiscais
├── frontend/                  # Aplicação Frontend PWA (Client-Side)
│   ├── index.html             # Shell principal da SPA
│   ├── manifest.json          # Manifesto do PWA
│   ├── sw.js                  # Service Worker com cache offline
│   └── assets/                # Folhas de estilo (CSS) e scripts de componentes (JS)
└── tools/                     # Scripts utilitários de suporte operacional
    └── generate_keys.py       # Gerador de chaves criptográficas de 64 caracteres
```

---

## 🛡️ Governança e Boas Práticas

- **Regra de Ouro (Implementation Plan):** Toda e qualquer alteração de código ou banco de dados exige um plano prévio aprovado e registrado na pasta `Planejamento/` antes de sua execução (consulte `AGENTS.md`).
- **Commits Semânticos Obrigatórios:** Commits seguem o padrão *Conventional Commits* em português (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `security`), conforme definido na Seção 30 do `docs/FSD.md`.
- **Versionamento de Assets Frontend (PWA):** Modificações em JS/CSS exigem incremento de versão no `frontend/sw.js` (`CACHE_NAME`) e no `frontend/index.html` (`?v=X.Y`), seguidas de recarregamento forçado no navegador (`Ctrl + Shift + R`).
