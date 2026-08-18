# STATUS DO PROJETO - EMC SOLDAS

Este documento é um arquivo vivo que registra o estado atual do desenvolvimento, o progresso por fase, o checklist de tarefas e o próximo passo recomendado.

**Última Atualização:** 2026-08-18 (Conclusão da Fase 3)  
**Fase Atual:** Fase 3 - Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC) (Concluída)  
**Próxima Fase:** Fase 4 - Cadastros Estruturais e Dicionários Centrais  

---

## Visão Geral do Progresso

| Fase | Título | Status | Conclusão |
| :--- | :--- | :--- | :--- |
| **Fase 1** | Infraestrutura, Base do Projeto e Governança de Configuração | **Concluída** | 100% |
| **Fase 2** | Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria | **Concluída** | 100% |
| **Fase 3** | Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC) | **Concluída** | 100% |
| **Fase 4** | Cadastros Estruturais e Dicionários Centrais | Pendente | 0% |
| **Fase 5** | Módulo de Clientes, Fornecedores e Equipamentos | Pendente | 0% |
| **Fase 6** | Catálogo Base, Materiais, Insumos e Produtos (Motor BOM) | Pendente | 0% |
| **Fase 7** | Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos) | Pendente | 0% |
| **Fase 8** | Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF) | Pendente | 0% |
| **Fase 9** | Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação) | Pendente | 0% |
| **Fase 10** | Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos | Pendente | 0% |
| **Fase 11** | Conciliação Bancária Inteligente Split-Screen (OFX/CSV) | Pendente | 0% |
| **Fase 12** | Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete) | Pendente | 0% |
| **Fase 13** | Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV) | Pendente | 0% |
| **Fase 14** | Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*) | Pendente | 0% |
| **Fase 15** | Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy | Pendente | 0% |

---

## Detalhamento do Checklist por Fase

### Fase 1 - Infraestrutura, Base do Projeto e Governança de Configuração
- [x] Estruturar pastas desacopladas do projeto (`backend/`, `frontend/`, `docs/`, `tools/`).
- [x] Criar arquivo de dependências Python (`backend/requirements.txt`).
- [x] Configurar projeto Django com isolamento seguro e leitura via `os.environ` (`backend/config/settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- [x] Implementar classes abstratas base de auditoria e soft delete (`backend/core/models.py`).
- [x] Implementar handlers de exceção segura e utilitários criptográficos (`backend/core/`).
- [x] Criar estrutura de aplicativos Django modulares em `backend/apps/`.
- [x] Configurar diretório de logs físicos com rotação diária (`backend/logs/`) e controle NoExec em mídia (`backend/media/`).
- [x] Criar casca base do Frontend PWA (`frontend/index.html`, `manifest.json`, `sw.js`).
- [x] Implementar tokens de design system e layout base (*Industrial Integrity* em `frontend/assets/css/`).
- [x] Criar arquivos de governança e contexto (`AGENTS.md`, `docs/PLANO.md`, `docs/STATUS.md`, `docs/ERROS.md`).
- [x] Configurar controle de versão Git (`.gitignore`, `.gitattributes`, `.env.example`).
- [x] Executar primeiro commit blindado de segurança (`main`).
- [x] Conectar repositório remoto no GitHub (`https://github.com/grcarpanez/emc-soldas.git`) e efetuar primeiro push com sucesso.

### Fase 2 - Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria
- [x] Implementar classe base `SoftDeleteModel` e `AuditableModel` (`backend/core/models.py`).
- [x] Modelar entidades de Usuários e Permissões (`Usuario`, `Permissao` em `apps/authentication`).
- [x] Modelar entidades de Clientes, Fornecedores e Equipamentos (`ClienteFornecedor`, `Equipamento`, `ClienteEquipamento`, `AnexoGeralCliente` em `apps/cadastros`).
- [x] Modelar entidades de Dicionário e Catálogo (`DicionarioUom`, `DicionarioAtributo`, `Item`, `ItemAtributoValor`, `Produto`, `FichaTecnica` em `apps/catalogo`).
- [x] Modelar entidades de Orçamentos e Propostas (`Orcamento`, `OrcamentoItem`, `OrcamentoPropostaPagamento` em `apps/orcamentos`).
- [x] Modelar entidades de Faturas e Propostas (`Fatura`, `FaturaPropostaPagamento` em `apps/faturamento`).
- [x] Modelar entidades de Tesouraria e Estruturas Financeiras (`LancamentoFinanceiro`, `ContaBancaria`, `CartaoCredito`, `FaturaCartao`, `CategoriaFinanceira`, `MeioPagamento`, `RegraPagamento`, `LogEstorno` em `apps/financeiro`).
- [x] Modelar entidades de Compras e Entradas (`DocumentoFiscalCompra`, `NotaCompraItem` em `apps/compras`).
- [x] Modelar entidades de Governança (`ConfiguracaoGlobal`, `ControleArquivoLog` em `apps/administracao`).
- [x] Configurar as 7 `UniqueConstraints` mandatórias e matriz estratégica de índices B-Tree.
- [x] Gerar migrations versionadas do Django para todos os módulos (`python backend/manage.py makemigrations`).
- [x] Criar comando de seeders para dados estruturais padrão (`python backend/manage.py seed_initial_data`).
- [x] Criar e executar bateria de testes automatizados (`python backend/manage.py test core`) com 100% de sucesso.

### Fase 3 - Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC)
- [x] Implementar autenticação customizada com suporte a hash PBKDF2 e PIN de 6 dígitos (`apps/authentication/models.py`).
- [x] Configurar classe customizada de autenticação JWT via Cookie de Sessão HttpOnly (`CookieJWTAuthentication`) com `SameSite=Strict`.
- [x] Criar endpoints de Login, Logout, Me, Soft Lock (PIN de 6 dígitos), Hard Lock (3 erros) e Recuperação de Senha por código de 8 dígitos.
- [x] Implementar Onboarding de colaboradores com envio de convite por e-mail e link seguro de ativação (`POST /api/usuarios/convidar/` e `POST /api/auth/activate-account/`).
- [x] Implementar bloqueio temporário anti-bruteforce (5 tentativas falhas em 15 min = 1h de bloqueio) e endpoint de desbloqueio pelo Admin (`POST /api/usuarios/{id}/desbloquear/`).
- [x] Criar e validar classes de permissão RBAC com os 10 toggles dinâmicos no backend retornando `403 Forbidden` (`core/permissions.py`).
- [x] Implementar injeção automática de contexto de autoria nos models a partir de `AuditUserMiddleware`.
- [x] Criar e executar suíte de testes automatizados com 100% de aprovação (21 testes).

### Fase 4 - Cadastros Estruturais e Dicionários Centrais
- [ ] Implementar CRUD de `DicionarioUom` e `DicionarioAtributo`.
- [ ] Implementar CRUD hierárquico de `CategoriaFinanceira`.
- [ ] Implementar CRUD de `ContaBancaria` (com saldo e limite de cheque especial).
- [ ] Implementar CRUD de `MeioPagamento` (com toggle `permite_taxa_maquininha`).
- [ ] Implementar CRUD de `RegraPagamento` (à vista, a prazo, parcelado com prazos e descontos padrão).

### Fase 5 - Módulo de Clientes, Fornecedores e Equipamentos
- [ ] Criar endpoint proxy para consulta de CNPJ pública (BrasilAPI/ReceitaWS) com fallback gracioso.
- [ ] Implementar validação matemática de CPF (módulo 11) e checagem antecipada de unicidade (`onBlur`).
- [ ] Implementar CRUD de `ClienteFornecedor` com suporte a PF/PJ e cadastro rápido ágil (apenas Nome + Telefone).
- [ ] Implementar CRUD de `Equipamento` com histórico relacional de proprietários (`ClienteEquipamento`).
- [ ] Implementar gestão segura de anexos gerais de clientes.

### Fase 6 - Catálogo Base, Materiais, Insumos e Produtos (Motor BOM)
- [ ] Implementar cadastro de Itens com atributos técnicos dinâmicos e fator de conversão de unidades.
- [ ] Implementar cadastro de Produtos com tempo de mão de obra e sub-grid de Ficha Técnica BOM.
- [ ] Implementar cálculo em tempo real do `Preço de Custo Apurado`.
- [ ] Implementar travas de integridade para impedir soft delete de itens em uso na receita de produtos ativos.

### Fase 7 - Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos)
- [ ] Implementar registro de Notas Fiscais de Entrada (`DocumentoFiscalCompra` e `NotaCompraItem`).
- [ ] Implementar rotina de retroalimentação automática de custos no Catálogo de Itens.
- [ ] Configurar upload seguro de XML/PDF com validação de MIME-Type profundo.
- [ ] Implementar histórico de compras e preços por fornecedor.

### Fase 8 - Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF)
- [ ] Implementar criação ágil de Orçamentos com 3 tipos de itens (Produtos, Itens e Lançamentos Livres).
- [ ] Implementar persistência imutável de Snapshots de custos e valores de venda.
- [ ] Implementar máquina de estados duplo (Status Operacional vs Status Financeiro).
- [ ] Implementar renovação de orçamentos com alerta visual de inflação de insumos/mão de obra.
- [ ] Implementar cancelamento justificado obrigatório (mínimo 10 caracteres) com gravação de log.
- [ ] Implementar serviço de geração de PDF com desconto oculto quando zerado.

### Fase 9 - Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação)
- [ ] Implementar listagem da Conta Corrente de orçamentos 'A Faturar'.
- [ ] Implementar fluxo de Pré-Fatura (Rascunho) com simulação de opções de pagamento e PDF Espelho.
- [ ] Implementar conversão em Fatura Final (`FATURADA`), transição em cascata de orçamentos e geração de parcelas no Contas a Receber.
- [ ] Implementar quitação total (100% de baixa transitando fatura e orçamentos para `PAGA`/`PAGO`).
- [ ] Implementar cancelamento de faturas com desvinculação em cascata e reversão para `A FATURAR`.
- [ ] Implementar quitação em Cortesia (100% de desconto) sem afetar caixa real.

### Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos
- [ ] Implementar Contas a Pagar e Contas a Receber (Regime de Competência) sem impactar saldo imediato.
- [ ] Implementar Extrato de Caixa Real (Regime de Caixa) com impacto imediato no saldo da conta bancária.
- [ ] Implementar Modal Universal de Liquidação com cálculo automático de Taxa de Maquininha (Receita Bruta + Despesa de Taxa = Saldo Líquido).
- [ ] Implementar Bloqueio por Limite de Cheque Especial.
- [ ] Implementar Transferências Inter-Contas.
- [ ] Implementar gestão de Cartões Corporativos com acumulação de despesas e rollover de saldo devedor.
- [ ] Implementar fluxo de Estorno de títulos pagos com justificativa obrigatória e gravação perpétua em `LogEstorno`.

### Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV)
- [ ] Implementar serviço de upload e parsing seguro de extratos OFX e CSV.
- [ ] Implementar algoritmo de Match Automático 1:1 e Match Múltiplo (1:N).
- [ ] Implementar endpoint de `Lançamento Rápido no Ato` para tarifas bancárias/rendimentos.
- [ ] Implementar confirmação de conciliação com gravação de `is_conciliado = True`, data e operador.
- [ ] Implementar dados analíticos para Relatório de Divergências de Conciliação.

### Fase 12 - Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete)
- [ ] Implementar Parâmetros Globais com criptografia simétrica AES-256 da senha SMTP e teste de disparo em tempo real.
- [ ] Implementar blindagem de não-retroatividade para taxa horária e validade de orçamentos.
- [ ] Implementar rotina de expurgo de logs via manifesto TTL (`ControleArquivoLog`).
- [ ] Implementar Log Viewer do servidor para o Administrador.
- [ ] Implementar Gestão de Equipe com os 10 toggles dinâmicos por usuário e desbloqueio de contas.
- [ ] Implementar Painel de Lixeira e Restauração (Lixeira Global para Admin e Minha Lixeira para Operador).

### Fase 13 - Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV)
- [ ] Implementar agregação do Dashboard de Flip Cards (Operação, Faturamento, Receita, Caixa e Alertas).
- [ ] Implementar Relatório de Inadimplência, Dossiê do Cliente, Curvas ABC e DRE Simplificado.
- [ ] Implementar Relatório de Divergências de Conciliação (Sobras de Extrato vs Sobras de ERP).
- [ ] Implementar exportações consolidadas em PDF e CSV com throttling protetivo (5 req/min).

### Fase 14 - Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*)
- [ ] Implementar roteador client-side SPA, Service Worker e cache offline.
- [ ] Implementar Telas de Acesso (Login, PIN de 6 dígitos, Recuperação de Senha).
- [ ] Implementar Dashboard de Flip Cards interativos e atalhos rápidos.
- [ ] Implementar telas operacionais de Orçamentos, Faturas, Clientes, Equipamentos, Catálogo e Compras.
- [ ] Implementar telas de Tesouraria, Liquidação, Cartões e Conciliação Split-Screen.
- [ ] Implementar Central do Administrador, Gestão de Permissões, Logs e Lixeira.
- [ ] Integrar todos os formulários com validação visual, feedback em tempo real e Design System 100% fiel ao `docs/DESIGN.md`.

### Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy
- [ ] Executar suíte de testes automatizados unitários e de integração (`python manage.py test`).
- [ ] Executar Pentest Mandatório de Conclusão (6 testes: RBAC/IDOR, Brute-force, SQLi/XSS, Uploads, Sessão HttpOnly, Criptografia/Tracebacks).
- [ ] Disponibilizar script gerador de chaves criptográficas de 64 caracteres (`tools/generate_keys.py`).
- [ ] Elaborar guia de implantação em produção Cloud PaaS.

---

## Próximo Passo Recomendado

Iniciar a **Fase 4 - Cadastros Estruturais e Dicionários Centrais**, implementando os endpoints de CRUD e regras de negócio para Dicionário UOM (`DicionarioUom`), Dicionário de Atributos (`DicionarioAtributo`), Categorias Financeiras (`CategoriaFinanceira`), Contas Bancárias (`ContaBancaria`), Meios de Pagamento (`MeioPagamento`) e Regras de Pagamento (`RegraPagamento`), protegidos pelas permissões RBAC correspondentes.
