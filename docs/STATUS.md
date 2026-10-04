# STATUS DO PROJETO - EMC SOLDAS

Este documento Ã© um arquivo vivo que registra o estado atual do desenvolvimento, o progresso por fase, o checklist de tarefas e o prÃ³ximo passo recomendado.

**Ãšltima AtualizaÃ§Ã£o:** 2026-10-03 (CorreÃ§Ã£o da Chamada de SanitizaÃ§Ã£o no Cadastro RÃ¡pido de Insumo - PWA v4.44)  
**Fase Atual:** Fase 14.5 - Refinamentos de UX, Mobile e Conectividade Operacional (Compras com EdiÃ§Ã£o, Cancelamento e Cadastro RÃ¡pido de Insumos, Dashboard, ConciliaÃ§Ã£o e Guias)  
**PrÃ³xima Fase:** Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de ConclusÃ£o e Deploy (Pendente - com checklist de rollback do tÃºnel registrado)  

---

## VisÃ£o Geral do Progresso

| Fase | TÃ­tulo | Status | ConclusÃ£o |
| :--- | :--- | :--- | :--- |
| **Fase 0** | Mapeamento Integral dos Campos do Banco de Dados e Matriz de MÃ¡scaras/SanitizaÃ§Ã£o | **ConcluÃ­da** | 100% |
| **Fase 1** | Infraestrutura, Base do Projeto e GovernanÃ§a de ConfiguraÃ§Ã£o | **ConcluÃ­da** | 100% |
| **Fase 2** | Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria | **ConcluÃ­da** | 100% |
| **Fase 3** | AutenticaÃ§Ã£o, SessÃ£o (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC) | **ConcluÃ­da** | 100% |
| **Fase 3.5** | AdequaÃ§Ã£o de SanitizaÃ§Ã£o Universal (Uppercase/Sem Acentos) e UtilitÃ¡rios de MÃ¡scaras | **ConcluÃ­da** | 100% |
| **Fase 4** | Cadastros Estruturais e DicionÃ¡rios Centrais | **ConcluÃ­da** | 100% |
| **Fase 5** | MÃ³dulo de Clientes, Fornecedores e Equipamentos | **ConcluÃ­da** | 100% |
| **Fase 6** | CatÃ¡logo Base, Materiais, Insumos e Produtos (Motor BOM) | **ConcluÃ­da** | 100% |
| **Fase 7** | MÃ³dulo de Compras (Notas Fiscais de Entrada e RetroalimentaÃ§Ã£o de Custos) | **ConcluÃ­da** | 100% |
| **Fase 8** | OrÃ§amentos Comerciais (Snapshot de Custos, Validade e GeraÃ§Ã£o PDF) | **ConcluÃ­da** | 100% |
| **Fase 9** | Faturamento Agregado (Conta Corrente, PrÃ©-Fatura, Fatura Final e QuitaÃ§Ã£o) | **ConcluÃ­da** | 100% |
| **Fase 10** | Tesouraria, Contas a Pagar/Receber, Caixa Real e CartÃµes Corporativos | **ConcluÃ­da** | 100% |
| **Fase 11** | ConciliaÃ§Ã£o BancÃ¡ria Inteligente Split-Screen (OFX/CSV) | **ConcluÃ­da** | 100% |
| **Fase 12** | Central Administrativa, ConfiguraÃ§Ãµes Globais, SMTP e Lixeira (Soft Delete) | **ConcluÃ­da** | 100% |
| **Fase 13** | Dashboards, RelatÃ³rios EstratÃ©gicos e ExportaÃ§Ãµes (PDF/CSV) | **ConcluÃ­da** | 100% |
| **Fase 14** | Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*) | **ConcluÃ­da** | 100% |
| **Fase 15** | Bateria de Testes Integrados, Hardening, Pentest de ConclusÃ£o e Deploy | Pendente | 0% |

---

## Detalhamento do Checklist por Fase

### Fase 0 - Mapeamento Integral dos Campos do Banco de Dados e Matriz de MÃ¡scaras/SanitizaÃ§Ã£o
- [x] Mapear todas as 29 entidades e campos de dados do sistema no `docs/PLANO.md`.
- [x] Definir regra de sanitizaÃ§Ã£o para 100% dos campos de texto (MaiÃºsculas sem Acento - ASCII Puro).
- [x] Definir especificaÃ§Ãµes de mÃ¡scaras: MÃ¡scara ATM de Moeda (`R$ 0,00`), CPF/CNPJ HÃ­brido, Telefone HÃ­brido, CEP, Placas e Horas.

### Fase 1 - Infraestrutura, Base do Projeto e GovernanÃ§a de ConfiguraÃ§Ã£o
- [x] Estruturar pastas desacopladas do projeto (`backend/`, `frontend/`, `docs/`, `tools/`).
- [x] Criar arquivo de dependÃªncias Python (`backend/requirements.txt`).
- [x] Configurar projeto Django com isolamento seguro e leitura via `os.environ` (`backend/config/settings.py`, `urls.py`, `wsgi.py`, `asgi.py`).
- [x] Implementar classes abstratas base de auditoria e soft delete (`backend/core/models.py`).
- [x] Implementar handlers de exceÃ§Ã£o segura e utilitÃ¡rios criptogrÃ¡ficos (`backend/core/`).
- [x] Criar estrutura de aplicativos Django modulares em `backend/apps/`.
- [x] Configurar diretÃ³rio de logs fÃ­sicos com rotaÃ§Ã£o diÃ¡ria (`backend/logs/`) e controle NoExec em mÃ­dia (`backend/media/`).
- [x] Criar casca base do Frontend PWA (`frontend/index.html`, `manifest.json`, `sw.js`).
- [x] Implementar tokens de design system e layout base (*Industrial Integrity* em `frontend/assets/css/`).
- [x] Criar arquivos de governanÃ§a e contexto (`AGENTS.md`, `docs/PLANO.md`, `docs/STATUS.md`, `docs/ERROS.md`).
- [x] Configurar controle de versÃ£o Git (`.gitignore`, `.gitattributes`, `.env.example`).
- [x] Executar primeiro commit blindado de seguranÃ§a (`main`).
- [x] Conectar repositÃ³rio remoto no GitHub (`https://github.com/grcarpanez/emc-soldas.git`) e efetuar primeiro push com sucesso.

### Fase 2 - Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria
- [x] Implementar classe base `SoftDeleteModel` e `AuditableModel` (`backend/core/models.py`).
- [x] Modelar entidades de UsuÃ¡rios e PermissÃµes (`Usuario`, `Permissao` em `apps/authentication`).
- [x] Modelar entidades de Clientes, Fornecedores e Equipamentos (`ClienteFornecedor`, `Equipamento`, `ClienteEquipamento`, `AnexoGeralCliente` em `apps/cadastros`).
- [x] Modelar entidades de DicionÃ¡rio e CatÃ¡logo (`DicionarioUom`, `DicionarioAtributo`, `Item`, `ItemAtributoValor`, `Produto`, `FichaTecnica` em `apps/catalogo`).
- [x] Modelar entidades de OrÃ§amentos e Propostas (`Orcamento`, `OrcamentoItem`, `OrcamentoPropostaPagamento` em `apps/orcamentos`).
- [x] Modelar entidades de Faturas e Propostas (`Fatura`, `FaturaPropostaPagamento` em `apps/faturamento`).
- [x] Modelar entidades de Tesouraria e Estruturas Financeiras (`LancamentoFinanceiro`, `ContaBancaria`, `CartaoCredito`, `FaturaCartao`, `CategoriaFinanceira`, `MeioPagamento`, `RegraPagamento`, `LogEstorno` em `apps/financeiro`).
- [x] Modelar entidades de Compras e Entradas (`DocumentoFiscalCompra`, `NotaCompraItem` em `apps/compras`).
- [x] Modelar entidades de GovernanÃ§a (`ConfiguracaoGlobal`, `ControleArquivoLog` em `apps/administracao`).
- [x] Configurar as 7 `UniqueConstraints` mandatÃ³rias e matriz estratÃ©gica de Ã­ndices B-Tree.
- [x] Gerar migrations versionadas do Django para todos os mÃ³dulos (`python backend/manage.py makemigrations`).
- [x] Criar comando de seeders para dados estruturais padrÃ£o (`python backend/manage.py seed_initial_data`).
- [x] Criar e executar bateria de testes automatizados (`python backend/manage.py test core`) com 100% de sucesso.

### Fase 3 - AutenticaÃ§Ã£o, SessÃ£o (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC)
- [x] Implementar autenticaÃ§Ã£o customizada com suporte a hash PBKDF2 e PIN de 6 dÃ­gitos (`apps/authentication/models.py`).
- [x] Configurar classe customizada de autenticaÃ§Ã£o JWT via Cookie de SessÃ£o HttpOnly (`CookieJWTAuthentication`) com `SameSite=Strict`.
- [x] Criar endpoints de Login, Logout, Me, Soft Lock (PIN de 6 dÃ­gitos), Hard Lock (3 erros) e RecuperaÃ§Ã£o de Senha por cÃ³digo de 8 dÃ­gitos.
- [x] Implementar Onboarding de colaboradores com envio de convite por e-mail e link seguro de ativaÃ§Ã£o (`POST /api/usuarios/convidar/` e `POST /api/auth/activate-account/`).
- [x] Implementar bloqueio temporÃ¡rio anti-bruteforce (5 tentativas falhas em 15 min = 1h de bloqueio) e endpoint de desbloqueio pelo Admin (`POST /api/usuarios/{id}/desbloquear/`).
- [x] Criar e validar classes de permissÃ£o RBAC com os 10 toggles dinÃ¢micos no backend retornando `403 Forbidden` (`core/permissions.py`).
- [x] Implementar injeÃ§Ã£o automÃ¡tica de contexto de autoria nos models a partir de `AuditUserMiddleware`.
- [x] Criar e executar suÃ­te de testes automatizados com 100% de aprovaÃ§Ã£o (21 testes).

### Fase 3.5 - AdequaÃ§Ã£o de SanitizaÃ§Ã£o Universal (Uppercase/Sem Acentos) e UtilitÃ¡rios de MÃ¡scaras
- [x] Criar funÃ§Ã£o utilitÃ¡ria de sanitizaÃ§Ã£o universal `sanitizar_texto_maiusculo` no backend (`backend/core/utils.py`).
- [x] Atualizar dados padrÃ£o do seeder inicial (`backend/core/management/commands/seed_initial_data.py`) convertendo 100% dos textos para maiÃºsculas sem acento e enums em UPPERCASE.
- [x] Criar biblioteca de utilitÃ¡rios no frontend (`frontend/assets/js/utils.js`) com conversÃ£o em tempo real (`input`/`paste`), MÃ¡scara ATM de Moeda (`R$ 0,00`), CPF/CNPJ, Telefone, CEP, Placas, Chave NFe e Linha DigitÃ¡vel.
- [x] Criar e validar testes automatizados de sanitizaÃ§Ã£o de strings no backend com 100% de sucesso.

### Fase 4 - Cadastros Estruturais e DicionÃ¡rios Centrais
- [x] Implementar CRUD de `DicionarioUom` (`/api/dicionario-uom/`) com sanitizaÃ§Ã£o e proteÃ§Ã£o contra deleÃ§Ã£o de UOMs em uso.
- [x] Implementar CRUD de `DicionarioAtributo` (`/api/dicionario-atributos/`) com sanitizaÃ§Ã£o e proteÃ§Ã£o contra deleÃ§Ã£o de atributos em uso.
- [x] Implementar CRUD hierÃ¡rquico de `CategoriaFinanceira` (`/api/categorias-financeiras/`) com validaÃ§Ã£o anti-ciclos e bloqueio de exclusÃ£o com subcategorias ativas.
- [x] Implementar CRUD de `ContaBancaria` (`/api/contas-bancarias/`) com validaÃ§Ã£o de limite de cheque especial e bloqueio com lanÃ§amentos ativos.
- [x] Implementar CRUD de `MeioPagamento` (`/api/meios-pagamento/`) com toggle `permite_taxa_maquininha` e validaÃ§Ã£o de regras ativas.
- [x] Implementar CRUD de `RegraPagamento` (`/api/regras-pagamento/`) com suporte a Ã  vista, a prazo e parcelado, com validaÃ§Ãµes de prazos, intervalos e descontos sugeridos.
- [x] Proteger todos os endpoints via RBAC dinÃ¢mico (`HasDicionarioUomAccess` e `HasCadastrosFinanceirosAccess`).
- [x] Criar e executar suÃ­te de testes automatizados com 100% de sucesso (33 testes).

### Fase 5 - MÃ³dulo de Clientes, Fornecedores e Equipamentos
- [x] Criar endpoint proxy para consulta de CNPJ pÃºblica (BrasilAPI/ReceitaWS) com fallback gracioso (`/api/utilitarios/consulta-cnpj/<cnpj>/`).
- [x] Criar endpoint proxy para consulta de CEP pÃºblica com fallback gracioso BrasilAPI / ViaCEP (`/api/utilitarios/consulta-cep/<cep>/`) e preenchimento automÃ¡tico no evento `blur`/`exit`.
- [x] Implementar validaÃ§Ã£o matemÃ¡tica de CPF (mÃ³dulo 11), CNPJ e checagem antecipada de duplicidade no `onBlur` (`/api/utilitarios/verificar-documento/`).
- [x] Implementar CRUD de `ClienteFornecedor` com suporte a PF/PJ, cadastro rÃ¡pido Ã¡gil (apenas Nome + Telefone), dossiÃª comercial e soft delete.
- [x] Implementar CRUD de `Equipamento` com suporte a placas antigas/Mercosul, identificaÃ§Ã£o tÃ©cnica e soft delete.
- [x] Implementar CRUD de `ClienteEquipamento` com transferÃªncia segura (desativaÃ§Ã£o do vÃ­nculo anterior e ativaÃ§Ã£o do novo) preservando o histÃ³rico para nÃ£o quebrar orÃ§amentos passados.
- [x] Implementar gestÃ£o e download seguro de anexos de clientes (`AnexoGeralCliente`) com validaÃ§Ã£o de extensÃµes permitidas e cabeÃ§alhos forÃ§ados.
- [x] Implementar gestÃ£o de contatos flexÃ­veis (estilo agenda de smartphone) com suporte a mÃºltiplos telefones e e-mails separados por ponto-e-vÃ­rgula (;) e validaÃ§Ã£o individual RFC.
- [x] Criar e executar suÃ­te completa de testes automatizados da Fase 5 com 100% de sucesso (26 testes dedicados em cadastros, 184 testes no acumulado do sistema).

### Fase 6 - CatÃ¡logo Base, Materiais, Insumos e Produtos (Motor BOM)
- [x] Implementar cadastro de Itens com atributos tÃ©cnicos dinÃ¢micos (`ItemAtributoValor`), fator de conversÃ£o de unidades e cÃ¡lculo de custo fracionado de consumo (`/api/itens/`).
- [x] Implementar cadastro de Produtos com tempo estimado de mÃ£o de obra (`tempo_estimado_execucao`) e sub-grid de Ficha TÃ©cnica BOM (`/api/produtos/`).
- [x] Implementar cÃ¡lculo em tempo real do `PreÃ§o de Custo Apurado` (Custo Total Materiais + Custo MÃ£o de Obra via taxa horÃ¡ria de `ConfiguracaoGlobal`).
- [x] Implementar travas de integridade referencial para impedir soft delete de itens em uso na Ficha TÃ©cnica de produtos ativos.
- [x] Implementar endpoints auxiliares: `/api/itens/{id}/onde-usado/`, `/api/produtos/{id}/custo-detalhado/` e `/api/produtos/{id}/atualizar-ficha-tecnica/`.
- [x] Proteger todos os endpoints do CatÃ¡logo via RBAC com o toggle `gestao_catalogo` (`HasCatalogoAccess`).
- [x] Criar e executar suÃ­te de testes automatizados com 100% de sucesso (50 testes no total acumulado do projeto).

### Fase 7 - MÃ³dulo de Compras (Notas Fiscais de Entrada e RetroalimentaÃ§Ã£o de Custos)
- [x] Implementar registro de Notas Fiscais de Entrada (`DocumentoFiscalCompra` e `NotaCompraItem` via `/api/documentos-fiscais-compra/` e `/api/nota-compra-itens/`).
- [x] Implementar rotina de retroalimentaÃ§Ã£o automÃ¡tica de custos no CatÃ¡logo de Itens (`ultimo_custo_compra` e `data_ultima_compra`).
- [x] Configurar upload seguro de XML/PDF com validaÃ§Ã£o de MIME-Type profundo, magic numbers e NoExec (`/api/documentos-fiscais-compra/{id}/anexar-arquivo/` e `download-anexo/`).
- [x] Implementar consulta de histÃ³rico de compras e preÃ§os por fornecedor (`/api/documentos-fiscais-compra/historico-precos/`).
- [x] Implementar modal de cadastro rÃ¡pido de insumos (`Item`) no formulÃ¡rio de notas fiscais com seleÃ§Ã£o imediata e foco automÃ¡tico sem perda de estado da compra.
- [x] Implementar fluxo completo de ediÃ§Ã£o de notas fiscais de compra (`PUT`/`PATCH` em `/api/documentos-fiscais-compra/{id}/`) com suporte a alteraÃ§Ã£o de cabeÃ§alho, itens e anexo.
- [x] Implementar cancelamento de compras com confirmaÃ§Ã£o visual e recÃ¡lculo inteligente e automÃ¡tico do Ãºltimo custo dos insumos para a compra anterior vÃ¡lida.
- [x] Proteger todos os endpoints do mÃ³dulo via RBAC dinÃ¢mico com o toggle `acesso_compras` (`HasComprasAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (28 testes dedicados em compras, 343 testes no acumulado do sistema).

### Fase 8 - OrÃ§amentos Comerciais (Snapshot de Custos, Validade e GeraÃ§Ã£o PDF)
- [x] Implementar criaÃ§Ã£o Ã¡gil de OrÃ§amentos com 3 tipos de itens (Produtos, Itens e LanÃ§amentos Livres).
- [x] Implementar persistÃªncia imutÃ¡vel de Snapshots de custos e valores de venda.
- [x] Implementar mÃ¡quina de estados duplo (Status Operacional vs Status Financeiro).
- [x] Implementar renovaÃ§Ã£o de orÃ§amentos com alerta visual de inflaÃ§Ã£o de insumos/mÃ£o de obra e opÃ§Ã£o de re-precificaÃ§Ã£o.
- [x] Implementar cancelamento justificado obrigatÃ³rio (mÃ­nimo 10 caracteres) com gravaÃ§Ã£o de log e auditoria.
- [x] Implementar detecÃ§Ã£o preventiva de inadimplÃªncia em tempo real com consulta a tÃ­tulos vencidos.
- [x] Implementar serviÃ§o de geraÃ§Ã£o de PDF comercial via ReportLab (*Industrial Integrity*) com desconto oculto quando zerado.
- [x] Gerar arquivo PDF de exemplo fictÃ­cio (`backend/media/exemplos/orcamento_exemplo.pdf`) para aprovaÃ§Ã£o visual do usuÃ¡rio.
- [x] Proteger todos os endpoints do mÃ³dulo via RBAC dinÃ¢mico com o toggle `acesso_comercial` (`HasComercialAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (87 testes no total acumulado do projeto).

### Fase 9 - Faturamento Agregado (Conta Corrente, PrÃ©-Fatura, Fatura Final e QuitaÃ§Ã£o)
- [x] Implementar listagem da Conta Corrente de orÃ§amentos 'A Faturar' (`/api/faturas/conta-corrente/`).
- [x] Implementar fluxo de PrÃ©-Fatura (Rascunho) com simulaÃ§Ã£o de opÃ§Ãµes de pagamento (`FaturaPropostaPagamento`) e PDF Espelho.
- [x] Implementar conversÃ£o em Fatura Final (`FATURADA` via `/api/faturas/{id}/faturar/`), transiÃ§Ã£o em cascata de orÃ§amentos e geraÃ§Ã£o de parcelas no Contas a Receber.
- [x] Implementar quitaÃ§Ã£o total (100% de baixa transitando fatura e orÃ§amentos para `PAGA`/`PAGO` via `/api/faturas/{id}/receber/`).
- [x] Implementar cancelamento de faturas com justificativa obrigatÃ³ria e desvinculaÃ§Ã£o em cascata (reversÃ£o para `A FATURAR` e anulaÃ§Ã£o de parcelas a vencer via `/api/faturas/{id}/cancelar/`).
- [x] Implementar quitaÃ§Ã£o em Cortesia (100% de desconto) sem afetar caixa real (`/api/faturas/{id}/cortesia/`).
- [x] Implementar gerador de PDF profissional para Faturas e PrÃ©-Faturas no padrÃ£o *Industrial Integrity* (`/api/faturas/{id}/gerar-pdf/`).
- [x] Proteger todos os endpoints do mÃ³dulo via RBAC dinÃ¢mico com o toggle `acesso_comercial` (`HasComercialAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (88 testes no total acumulado do projeto).

### Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real e CartÃµes Corporativos
- [x] Implementar Contas a Pagar e Contas a Receber (Regime de CompetÃªncia) sem impactar saldo imediato.
- [x] Implementar Extrato de Caixa Real (Regime de Caixa) com impacto imediato no saldo da conta bancÃ¡ria.
- [x] Implementar Modal Universal de LiquidaÃ§Ã£o com cÃ¡lculo automÃ¡tico de Taxa de Maquininha e RetenÃ§Ã£o de ISS na fonte (Receita Bruta - DeduÃ§Ãµes = Saldo LÃ­quido Real).
- [x] Implementar Bloqueio por Limite de Cheque Especial em saÃ­das bancÃ¡rias.
- [x] Implementar TransferÃªncias Inter-Contas atÃ´micas e neutras para o DRE.
- [x] Implementar gestÃ£o de CartÃµes Corporativos com acumulaÃ§Ã£o de despesas em fatura aberta, alteraÃ§Ã£o de fechamento, remanejamento entre faturas e rollover de saldo devedor.
- [x] Implementar fluxo de Estorno de tÃ­tulos pagos com reversÃ£o de saldo bancÃ¡rio, cancelamento de taxas atreladas e gravaÃ§Ã£o perpÃ©tua em `LogEstorno`.
- [x] Proteger todos os endpoints do mÃ³dulo via RBAC dinÃ¢mico com o toggle `acesso_tesouraria` (`HasTesourariaAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (108 testes no total acumulado do projeto).

### Fase 11 - ConciliaÃ§Ã£o BancÃ¡ria Inteligente Split-Screen (OFX/CSV)
- [x] Implementar serviÃ§o de upload e parsing seguro de extratos OFX e CSV.
- [x] Implementar algoritmo de Match AutomÃ¡tico 1:1 e Match MÃºltiplo (1:N).
- [x] Implementar endpoint de `LanÃ§amento RÃ¡pido no Ato` para tarifas bancÃ¡rias/rendimentos.
- [x] Implementar confirmaÃ§Ã£o de conciliaÃ§Ã£o com gravaÃ§Ã£o de `is_conciliado = True`, data e operador.
- [x] Implementar dados analÃ­ticos para RelatÃ³rio de DivergÃªncias de ConciliaÃ§Ã£o.
- [x] Proteger todos os endpoints do mÃ³dulo via RBAC dinÃ¢mico com o toggle `acesso_tesouraria` (`HasTesourariaAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (118 testes no total acumulado do projeto).

### Fase 12 - Central Administrativa, ConfiguraÃ§Ãµes Globais, SMTP e Lixeira (Soft Delete)
- [x] Implementar ParÃ¢metros Globais com criptografia simÃ©trica AES-256 da senha SMTP, presets rÃ¡pidos e teste de disparo em tempo real.
- [x] Implementar blindagem de nÃ£o-retroatividade para taxa horÃ¡ria e validade de orÃ§amentos sobre orÃ§amentos passados.
- [x] Implementar rotina de expurgo de logs via manifesto TTL (`ControleArquivoLog`), com envio de backup por e-mail dos arquivos expirados antes da exclusÃ£o fÃ­sica.
- [x] Implementar comando CLI agendÃ¡vel `python manage.py expurgar_logs --enviar-backup`.
- [x] Implementar Log Viewer seguro do servidor para visualizaÃ§Ã£o estruturada de falhas pelo Administrador, com blindagem rigorosa contra Path Traversal.
- [x] Implementar GestÃ£o de Equipe com os 10 toggles dinÃ¢micos por usuÃ¡rio, onboarding por e-mail e desbloqueio manual de contas travadas por Anti-Bruteforce.
- [x] Implementar Painel de Lixeira e RestauraÃ§Ã£o LÃ³gica mapeando 16 entidades com isolamento de visÃ£o (Lixeira Global para Admin e Minha Lixeira para Operador).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (133 testes no total acumulado do projeto).

### Fase 13 - Dashboards, RelatÃ³rios EstratÃ©gicos e ExportaÃ§Ãµes (PDF/CSV)
- [x] Implementar agregador do Dashboard Principal com os 5 Flip Cards interativos (OperaÃ§Ã£o, Faturamento, Receita, Caixa e Alertas) e filtros temporais (`/api/dashboard/flip-cards/`).
- [x] Implementar evoluÃ§Ã£o mensal de Receitas vs Despesas (`/api/dashboard/graficos/`) e Feed de Atividades Recentes (`/api/dashboard/feed/`).
- [x] Implementar RelatÃ³rio de InadimplÃªncia com auditoria de faturas vencidas, cÃ¡lculo de dias de atraso e contato de clientes (`/api/relatorios/inadimplencia/`).
- [x] Implementar DossiÃª do Cliente com segregaÃ§Ã£o de produtos (materiais) vs serviÃ§os (reformas), funil de orÃ§amentos e Ã­ndice de pontualidade (`/api/relatorios/dossie-cliente/<id>/`).
- [x] Implementar Curva ABC de Clientes (`/api/relatorios/curva-abc-clientes/`) e Curva ABC de Consumo de Itens (`/api/relatorios/curva-abc-itens/`) com matriz 80/15/5%.
- [x] Implementar DRE Simplificado nos regimes de competÃªncia e caixa com apuraÃ§Ã£o de receitas, deduÃ§Ãµes, custos variÃ¡veis e despesas operacionais (`/api/relatorios/dre/`).
- [x] Implementar RelatÃ³rio de DivergÃªncias de ConciliaÃ§Ã£o BancÃ¡ria em duas abas analÃ­ticas (`/api/relatorios/divergencias-conciliacao/`).
- [x] Implementar geradores de PDF via ReportLab no padrÃ£o *Industrial Integrity* e geradores de CSV com encoding UTF-8 com BOM para todos os relatÃ³rios estratÃ©gicos.
- [x] Aplicar Rate Limiting restritivo de 5 requisiÃ§Ãµes/minuto (`throttle_scope = 'heavy_reports'`) nos endpoints de exportaÃ§Ã£o de relatÃ³rios pesados.
- [x] Proteger todos os endpoints via RBAC dinÃ¢mico com o toggle `visao_relatorios` (`HasRelatoriosAccess`).
- [x] Criar e executar suÃ­te completa de testes automatizados com 100% de sucesso (146 testes no total acumulado do projeto).

### Fase 14 - Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*)
- [x] Implementar roteador client-side SPA (`router.js`), Service Worker (`sw.js`) e cache de assets estÃ¡ticos offline.
- [x] Implementar Telas de Acesso (`auth-view.js`: Login, PIN de 6 dÃ­gitos, RecuperaÃ§Ã£o de Senha e AtivaÃ§Ã£o de Conta).
- [x] Implementar Dashboard Principal (`dashboard-view.js`: 5 Flip Cards 3D com mÃ©tricas em tempo real, filtros temporais e feed de eventos).
- [x] Implementar telas operacionais de Cadastros (`cadastros-view.js`: Clientes com consulta de CNPJ e validaÃ§Ã£o CPF MÃ³dulo 11, Fornecedores, Equipamentos e DicionÃ¡rios UOM/Atributos).
- [x] Implementar CatÃ¡logo de Insumos e Motor BOM (`catalogo-view.js`: Itens, conversÃ£o de unidades, Produtos e Ficha TÃ©cnica BOM calculando Custo Apurado em tempo real).
- [x] Implementar MÃ³dulo de Compras (`compras-view.js`: Notas de Entrada com mÃ¡scara de chave NFe 44 dÃ­gitos, itens e histÃ³rico).
- [x] Implementar OrÃ§amentos Comerciais (`orcamentos-view.js`: ElaboraÃ§Ã£o Ã¡gil com 3 tipos de itens, snapshots imutÃ¡veis, renovaÃ§Ã£o com alerta de inflaÃ§Ã£o, cancelamento justificado e geraÃ§Ã£o de PDF).
- [x] Implementar Faturamento Agregado (`faturamento-view.js`: Conta Corrente, PrÃ©-Faturas, Faturas Finais, Baixas com taxa de maquininha, Cortesias 100% e cancelamento em cascata).
- [x] Implementar Tesouraria & Caixa Real (`financeiro-view.js`: Contas a Pagar/Receber por competÃªncia, Extrato de Caixa Real, CartÃµes Corporativos com rollover e Estorno com justificativa perpÃ©tua).
- [x] Implementar ConciliaÃ§Ã£o BancÃ¡ria Inteligente (`conciliacao-view.js`: Layout Split-Screen de 2 colunas, importaÃ§Ã£o OFX/CSV, Match 1:1, Match MÃºltiplo e LanÃ§amento RÃ¡pido no Ato).
- [x] Implementar Central do Administrador (`administracao-view.js`: ParÃ¢metros Globais, teste SMTP em tempo real, GestÃ£o de Equipe com 10 toggles dinÃ¢micos e desbloqueio anti-bruteforce, Log Viewer com expurgo TTL e Lixeira com restauraÃ§Ã£o lÃ³gica em 1 clique).
- [x] Implementar Central AnalÃ­tica (`relatorios-view.js`: InadimplÃªncia, DossiÃª do Cliente, Curvas ABC de Clientes/Itens, DRE Simplificado e DivergÃªncias de ConciliaÃ§Ã£o com exportaÃ§Ã£o PDF/CSV).
- [x] Integrar 100% dos componentes e formulÃ¡rios ao Design System *Industrial Integrity* (0px border-radius, tipografia tÃ©cnica, paleta Dark Iron, Steel Gray e Rust Orange, mÃ¡scaras e toasts).

### Fase 14.5 - Refinamentos de UX, Mobile e Conectividade Operacional (ConcluÃ­da)
- [x] **Comboboxes PesquisÃ¡veis com Autocomplete:** ImplementaÃ§Ã£o do componente universal `window.EMCUtils.initSearchableSelect` no padrÃ£o *Industrial Integrity* (0px border-radius, tema dark, busca instantÃ¢nea e navegaÃ§Ã£o por teclado).
- [x] **SegregaÃ§Ã£o de Frota e Clientes:** ExclusÃ£o estrita de fornecedores puros (`tipo === 'FORNECEDOR'`) da seleÃ§Ã£o de proprietÃ¡rios de veÃ­culos e da exibiÃ§Ã£o do botÃ£o `FROTA` na tabela.
- [x] **Filtragem DinÃ¢mica no OrÃ§amento:** Combobox de equipamentos re-filtrada em tempo real ao selecionar o cliente no modal de orÃ§amento.
- [x] **Modal de HistÃ³rico CronolÃ³gico de VÃ­nculos:** Endpoint `@action(detail=True, url_path='historico-proprietarios')` e modal frontend exibindo histÃ³rico de titularidade com precisÃ£o de timestamp (`DD/MM/AAAA Ã s HH:MM:SS`), status atual/anterior e telefone de contato.
- [x] **VinculaÃ§Ã£o Inteligente de Frota:** Modal de frota com busca de equipamentos existentes, autopreenchimento de campos e confirmaÃ§Ã£o assistida de transferÃªncia de titularidade entre clientes.
- [x] **Escala Compacta e Alta Densidade Mobile:** CalibraÃ§Ã£o CSS (`industrial-integrity.css` e `layout.css`) com tipografia compacta (`13.5px` / `12.5px`), botÃµes proporcionais (`min-height: 32px`), grids de formulÃ¡rios colapsando em coluna Ãºnica e modais fluidos (`96vw`).
- [x] **Servidor Unificado no Django:** Roteamento de assets estÃ¡ticos e SPA no `backend/config/urls.py`, permitindo execuÃ§Ã£o unificada via `python backend/manage.py runserver 0.0.0.0:8000` (eliminando dependÃªncia do Live Server na porta 5500).
- [x] **Conectividade Wi-Fi e Firewall:** ConfiguraÃ§Ã£o de `ALLOWED_HOSTS = ['*']` e `CSRF_TRUSTED_ORIGINS` para IPs de rede local (`192.168.2.104:8000`) e documentaÃ§Ã£o da regra do Windows Firewall (`netsh advfirewall firewall add rule name="EMC_Soldas_8000" dir=in action=allow protocol=TCP localport=8000`).
- [x] **Assets PWA e Favicon:** GeraÃ§Ã£o dos arquivos fÃ­sicos `favicon.ico`, `icon-192.png` e `icon-512.png` eliminando requisiÃ§Ãµes 404.
- [x] **DinamizaÃ§Ã£o Reativa CPF/CNPJ no Modal de Cadastro:** InicializaÃ§Ã£o do modal como Pessoa FÃ­sica ("NOME COMPLETO *" e campo "NOME FANTASIA" oculto com grid de 1 coluna), transiÃ§Ã£o em tempo real para Pessoa JurÃ­dica ("RAZÃƒO SOCIAL *", reexibiÃ§Ã£o de "NOME FANTASIA" e grid de 2 colunas) ao ultrapassar 11 dÃ­gitos, e reversÃ£o completa ao apagar dÃ­gitos.
- [x] **ExclusÃ£o e DesativaÃ§Ã£o (Soft Delete) com Blindagem de Integridade HistÃ³rica:** ImplementaÃ§Ã£o de botÃµes `EXCLUIR` e modais industriais de confirmaÃ§Ã£o para Clientes, Fornecedores e Equipamentos (`cadastros-view.js`), configuraÃ§Ã£o de `base_manager_name = 'all_objects'` no nÃºcleo ORM (`core/models.py`), inativaÃ§Ã£o de vÃ­nculos ativos de frota sem quebrar orÃ§amentos, faturas, tÃ­tulos, relatÃ³rios analÃ­ticos ou geraÃ§Ã£o de PDFs de registros passados, com segregaÃ§Ã£o de inativos exclusivamente em novos lanÃ§amentos e restauraÃ§Ã£o Ã¡gil via Lixeira.
- [x] **Aprimoramento do Painel de Lixeira & RestauraÃ§Ã£o:** CorreÃ§Ã£o no parser de resposta de itens da Lixeira, suporte Ã  opÃ§Ã£o de nÃ£o filtrar com exibiÃ§Ã£o unificada de todo o histÃ³rico cronolÃ³gico de exclusÃµes por padrÃ£o (`TODAS AS ENTIDADES`), adiÃ§Ã£o de Equipamentos e todas as 16 entidades na combobox, coluna de tipo/entidade na tabela e campo de busca textual em tempo real (150 testes automatizados aprovados com 100% de sucesso).
- [x] **Log Viewer do Servidor, Contagem Real de Eventos e Auditoria Universal de Soft Delete:** ImplementaÃ§Ã£o do handler `DailyDateFileHandler` em `backend/core/logging_handlers.py` gravando diretamente nos arquivos imutÃ¡veis `app-YYYY-MM-DD.log` (eliminando bloqueios de arquivo `PermissionError WinError 32` no Windows), adiÃ§Ã£o dos campos computados `total_eventos`, `quantidade_linhas` e `data_log` no `ControleArquivoLogSerializer`, correÃ§Ã£o de rotas (`/controle-arquivos-log/visualizar/`), modal do Log Viewer enriquecido com destaque semÃ¢ntico de severidade (*Industrial Integrity* com tags `[AUDIT]`, `ERROR`, `WARNING`, `INFO`), filtros em tempo real, sincronizaÃ§Ã£o manual de manifesto e rastreamento perpÃ©tuo de exclusÃµes e restauraÃ§Ãµes em log fÃ­sico (150 testes automatizados aprovados com 100% de sucesso).
- [x] **GestÃ£o de Equipe (RBAC), PermissÃµes DinÃ¢micas, PromoÃ§Ã£o/Rebaixamento, AtivaÃ§Ã£o/DesativaÃ§Ã£o e Auditoria Universal:**
  - CorreÃ§Ã£o dos endpoints REST de permissÃµes (`/api/usuarios/{id}/permissoes/`) com suporte completo aos mÃ©todos `GET`, `PATCH` e `PUT`.
  - ImplementaÃ§Ã£o de aÃ§Ãµes semÃ¢nticas de ativaÃ§Ã£o/desativaÃ§Ã£o (`/api/usuarios/{id}/alternar-status/`, `desativar/`, `ativar/`) com **blindagem de seguranÃ§a contra auto-desativaÃ§Ã£o** (`request.user.id == usuario.id`) e **proteÃ§Ã£o de Ãºltimo Administrador ativo** do sistema.
  - ImplementaÃ§Ã£o de promoÃ§Ã£o e rebaixamento de colaboradores (`/api/usuarios/{id}/alterar-perfil/`) com atribuiÃ§Ã£o plena de 10 toggles para Admins e proteÃ§Ã£o contra rebaixamento do Ãºnico Administrador ativo.
  - Sobrescrita com resposta protegida para auto-exclusÃ£o lÃ³gica no `UsuarioViewSet`.
  - Registro perpÃ©tuo em log fÃ­sico imutÃ¡vel com marcadores de auditoria `[AUDIT]` para promoÃ§Ãµes, rebaixamentos, ativaÃ§Ãµes, desativaÃ§Ãµes, diffs de permissÃµes RBAC, desbloqueios e convites.
  - Interface do frontend PWA atualizada na aba GestÃ£o de Equipe com modal unificado de perfil e matriz de 10 toggles dinÃ¢micos, botÃµes diretos de ativaÃ§Ã£o/desativaÃ§Ã£o e tag de auto-identificaÃ§Ã£o `[VOCÃŠ]` com botÃ£o desabilitado para o usuÃ¡rio da sessÃ£o (157 testes automatizados aprovados com 100% de sucesso).
  - **SincronizaÃ§Ã£o em Tempo Real, Parser Estruturado e SegregaÃ§Ã£o Estrita no Log Viewer:** Auto-sincronizaÃ§Ã£o do manifesto no mÃ©todo `list` de `ControleArquivoLogViewSet` garantindo exibiÃ§Ã£o instantÃ¢nea do arquivo do dia atual no topo da tabela, implementaÃ§Ã£o de parser semÃ¢ntico estruturado em `backend/apps/administracao/services.py` com classificaÃ§Ã£o primÃ¡ria definitiva (`AUDIT`, `SEGURANCA`, `ERROR`, `WARNING`, `HTTP`, `INFO`, `DEBUG`), eliminaÃ§Ã£o de falsos positivos em badges causados por termos em query strings de URLs, e enriquecimento do modal com seletor completo de 7 categorias e badges semÃ¢nticos (*Industrial Integrity*) precisos (157 testes automatizados aprovados com 100% de sucesso).
  - **Blindagem e Isolamento Estrito de Logs em Testes UnitÃ¡rios (Test Isolation):** RefatoraÃ§Ã£o da suÃ­te de testes de administraÃ§Ã£o para utilizar arquivos isolados com data fictÃ­cia (`app-2099-12-31.log`) e limpeza em bloco `try/finally`, eliminando qualquer risco de sobrescrita ou truncamento do arquivo real de log do dia atual (`app-YYYY-MM-DD.log`) durante execuÃ§Ãµes de testes.
- [x] **ValidaÃ§Ã£o Estrita e MÃ¡scara Universal de Placas (PadrÃµes Antigo e Mercosul com Formato ###-####):**
  - ImplementaÃ§Ã£o de mÃ¡scara universal automÃ¡tica com hÃ­fen `###-####` tanto para o padrÃ£o antigo (`AAA-0000`) quanto Mercosul (`AAA-0A00`): o hÃ­fen Ã© inserido **100% automaticamente** apÃ³s a 3Âª letra sem exigir que o operador digite `-`.
  - Backend: FunÃ§Ã£o utilitÃ¡ria `validar_placa(valor)` em `backend/core/utils.py` com sanitizaÃ§Ã£o e regex rigorosa (`^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`), validaÃ§Ã£o defensiva em `apps/cadastros/serializers.py` (`validate_placa`) normalizando e gravando sempre com hÃ­fen `###-####`, retornando `400 Bad Request` semÃ¢ntico para entradas invÃ¡lidas, e testes unitÃ¡rios automatizados cobrindo placas vÃ¡lidas e invÃ¡lidas (16 testes de cadastros e 157 testes globais aprovados com 100% de sucesso).
  - Frontend: FunÃ§Ã£o utilitÃ¡ria `formatarPlacaVeiculo` com restriÃ§Ã£o dinÃ¢mica caractere a caractere no evento `input` (dÃ­gitos 0-2: letras; dÃ­gito 3: nÃºmero; dÃ­gito 4: letra ou nÃºmero; dÃ­gitos 5-6: nÃºmeros; mÃ¡ximo de 8 caracteres formatados com `-`), validaÃ§Ã£o em tempo real e bloqueio de envio com Toast industrial nos modais de equipamento e frota em `cadastros-view.js`.
- [x] **InstituiÃ§Ã£o da GovernanÃ§a de Planejamento MandatÃ³ria e HistÃ³rico PerpÃ©tuo (`Planejamento/`):**
  - AtualizaÃ§Ã£o do `AGENTS.md` com Regra de Ouro inegociÃ¡vel: proibiÃ§Ã£o terminante de qualquer alteraÃ§Ã£o de cÃ³digo ou configuraÃ§Ã£o sem a prÃ©via elaboraÃ§Ã£o de *Implementation Plan* estruturado e aprovaÃ§Ã£o formal explÃ­cita (`Proceed`) do usuÃ¡rio.
  - CriaÃ§Ã£o da pasta `Planejamento/` na raiz do sistema para versionamento perpÃ©tuo de todos os planos de implementaÃ§Ã£o, contendo contexto, decisÃµes arquiteturais, checklist de arquivos, testes e transcriÃ§Ã£o da aprovaÃ§Ã£o do usuÃ¡rio (`Planejamento/YYYY-MM-DD_NN_nome_da_tarefa.md`).
- [x] **GovernanÃ§a PerpÃ©tua de Cache PWA e Versionamento Sincronizado de Assets (`v2.8`, `v2.9` e `v3.0`):**
  - InstituiÃ§Ã£o da Regra MandatÃ³ria 12 no `AGENTS.md` e registro de liÃ§Ã£o tÃ©cnica em `docs/ERROS.md`: toda e qualquer alteraÃ§Ã£o em JS/CSS obriga a sincronizaÃ§Ã£o do `CACHE_NAME` no `frontend/sw.js` e a atualizaÃ§Ã£o dos sufixos de query string `?v=X.Y` em todas as tags `<script>` e `<link>` do `frontend/index.html`.
  - ExecuÃ§Ã£o imediata da versÃ£o `v2.8`, `v2.9` e `v3.0` em `sw.js` e `index.html`, eliminando retenÃ§Ã£o de cÃ³digo desatualizado por caches stale no navegador do usuÃ¡rio.
- [x] **Refinamento de UX no Filtro de Clientes & Fornecedores (v2.9):**
  - Ajuste na combobox de tipo: renomeaÃ§Ã£o de `TODOS OS TIPOS` para `TODOS`, remoÃ§Ã£o da opÃ§Ã£o redundante `AMBOS` (permanecendo estritamente `TODOS`, `CLIENTES` e `FORNECEDORES`), expansÃ£o da largura para `180px` (eliminando o corte do texto de `FORNECEDORES`) e readequaÃ§Ã£o da textbox de busca para `max-width: 380px`.
- [x] **Alinhamento ContÃ­nuo e Responsividade Anti-Esmagamento da Barra de Clientes (v3.0):**
  - UnificaÃ§Ã£o da barra em container flex Ãºnico com `gap: 10px` contÃ­nuo entre todos os 4 elementos, eliminando o buraco vazio central e fazendo com que a busca expansiva (`flex: 1`) e os demais controles preencham 100% da div.
  - AdiÃ§Ã£o de `flex-shrink: 0; min-width: 175px;` na combobox de tipo, eliminando em definitivo o esmagamento e sobreposiÃ§Ã£o ("engolimento") do select em reduÃ§Ãµes progressivas da janela.
  - Agrupamento dos botÃµes de aÃ§Ã£o com quebra suave e limpa para telas menores sem colisÃ£o visual.
- [x] **InclusÃ£o SemÃ¢ntica do Tipo 'Ambos' nos Filtros de Clientes e Fornecedores (Abordagem Ãgil):**
  - NormalizaÃ§Ã£o no backend (`ClienteFornecedorViewSet.get_queryset` em `apps/cadastros/views.py`) com `.strip().upper()`, tornando o filtro de tipo robusto contra variaÃ§Ãµes maiÃºsculas/minÃºsculas (`CLIENTE`, `CLIENTES`, `Cliente`, `FORNECEDOR`, `FORNECEDORES`, `Fornecedor`).
  - ImplementaÃ§Ã£o semÃ¢ntica no ORM: parceiros cadastrados com o tipo `Ambos` (dupla atribuiÃ§Ã£o) sÃ£o incluÃ­dos automaticamente tanto nas buscas/filtros de Clientes (`tipo__in=['Cliente', 'Ambos']`) quanto de Fornecedores (`tipo__in=['Fornecedor', 'Ambos']`).
  - SuÃ­te de testes automatizados unitÃ¡rios enriquecida (`test_filtro_tipo_clientes_e_fornecedores_inclui_ambos` em `cadastros/tests.py`), alcanÃ§ando 17 testes especÃ­ficos e 158 testes globais aprovados com 100% de sucesso.
- [x] **CorreÃ§Ã£o da SeleÃ§Ã£o do Tipo de Cadastro na EdiÃ§Ã£o de Clientes/Fornecedores e Versionamento PWA v3.1:**
  - DiagnÃ³stico e correÃ§Ã£o no modal de ediÃ§Ã£o (`abrirModalCadastroCompleto` em `cadastros-view.js`): resoluÃ§Ã£o de incompatibilidade de casing entre API (`'Cliente'`, `'Fornecedor'`, `'Ambos'`) e atributos HTML dos options, garantindo prÃ©-seleÃ§Ã£o correta do tipo real ao editar e eliminando o risco de sobrescrever fornecedores como clientes por engano.
  - NormalizaÃ§Ã£o preventiva em badges de listagem, botÃ£o de frota e filtros de clientes para orÃ§amentos e frotas (`orcamentos-view.js`).
  - Cumprimento rigoroso da Regra 12 de Versionamento PWA: incremento do `CACHE_NAME` para `'emc-soldas-v3.1'` em `frontend/sw.js` e atualizaÃ§Ã£o dos sufixos de cache-busting `?v=3.1` em todas as tags `<script>` e `<link>` do `frontend/index.html`.
- [x] **Painel Operacional de Frota e PÃ¡tio (Filtro por ProprietÃ¡rio, Flag 'No PÃ¡tio' e PWA v3.2):**
  - TransformaÃ§Ã£o da aba de Equipamentos em um painel completo de controle de frota e oficina, com barra integrada de 4 elementos: busca textual expansiva (`flex: 1; min-width: 220px;`), combobox dinÃ¢mica de proprietÃ¡rios (ordenada alfabeticamente com opÃ§Ã£o de nÃ£o vinculados), toggle industrial `NO PÃTIO` e botÃ£o de novo cadastro.
  - Backend (`EquipamentoViewSet` e `EquipamentoSerializer`): suporte a `cliente_id` (com `sem_proprietario`), filtro `no_patio` cruzando com orÃ§amentos ativos (`status_operacional__in=['APROVADO', 'EM_EXECUCAO']`), e campos computados `em_patio` e `orcamento_em_execucao`.
  - Frontend: badge visual de destaque `[NO PÃTIO (#X)]` na coluna de ProprietÃ¡rio da tabela.
  - Testes unitÃ¡rios dedicados em `apps/cadastros/tests.py` (19 testes de cadastros e 160 testes globais aprovados com 100% de sucesso).
  - Versionamento PWA: cache sincronizado para `emc-soldas-v3.2` em `frontend/sw.js` e tags atualizadas com `?v=3.2` em `frontend/index.html`.
- [x] **Temporizador Visual de Inatividade na Topbar & Alerta Fixo aos 30s (PWA v3.6):**
  - Componente de Topbar em Tempo Real: InclusÃ£o do chip monospace `<span class="status-chip secondary mono-text" id="session-timer-chip">â± MM:SS</span>` na barra superior ao lado do indicador de conectividade (`ONLINE`).
  - Alerta Visual MandatÃ³rio aos 30s: Contagem regressiva contÃ­nua baseada em tempo real que transiciona para estilo de alerta (`status-chip warning` - tom Ã¢mbar/laranja industrial) quando o tempo restante for `<= 30 segundos`, avisando o operador antes do bloqueio automÃ¡tico.
  - Reset DinÃ¢mico por UtilizaÃ§Ã£o Efetiva: O cronÃ´metro reinicia de volta ao tempo total configurado imediatamente ao ocorrer qualquer clique no sistema, digitaÃ§Ã£o, seleÃ§Ã£o ou chamada de API (mantendo o critÃ©rio de que mexer o mouse sem clicar ou usar outros aplicativos no Windows nÃ£o reseta a ociosidade da sessÃ£o).
  - Versionamento PWA: Cache sincronizado para `emc-soldas-v3.6` em `frontend/sw.js` e sufixos de cache-busting `?v=3.6` em `frontend/index.html`.
  - SuÃ­te de Testes Automatizados: 36 testes executados e 100% aprovados (`apps.authentication` e `apps.administracao`).
- [x] **RestriÃ§Ã£o de Valores MÃ­nimos em ParÃ¢metros Globais & Bloqueio Anti-Negativo (PWA v3.7):**
  - Travamento FÃ­sico de MÃ­nimos no Frontend: ConfiguraÃ§Ã£o de `min="1"` e `step="1"` para Validade do OrÃ§amento (`cfg-validade`) e Tempo Soft Lock (`cfg-ociosidade`), e `min="0"` e `step="1"` para RetenÃ§Ã£o de Logs (`cfg-retencao-logs`), impedindo navegaÃ§Ã£o para valores negativos atravÃ©s das setinhas do stepper.
  - SanitizaÃ§Ã£o Ativa de Entrada: Ouvintes reativos nos eventos `input` e `change` que corrigem imediatamente digitaÃ§Ã£o ou colagem manual de nÃºmeros inferiores ao piso permitido (bloqueando sinais de menos ou valores negativos).
  - Blindagem MandatÃ³ria no Backend DRF: ValidaÃ§Ãµes no `ConfiguracaoGlobalSerializer` rejeitando com `400 Bad Request` qualquer payload com `validade_orcamento_dias < 1`, `tempo_ociosidade_minutos < 1` ou `retencao_logs_dias < 0`.
  - Versionamento PWA: Cache elevado para `emc-soldas-v3.7` em `frontend/sw.js` e sufixos de cache-busting `?v=3.7` em `frontend/index.html`.
  - SuÃ­te de Testes Automatizados: 37 testes executados e 100% aprovados (`apps.authentication` e `apps.administracao`).
- [x] **Disparo Real de Teste SMTP via ConexÃ£o Direta, Presets de E-mail e DiagnÃ³stico (PWA v3.8):**
  - ConexÃ£o SMTP Real Direta: EliminaÃ§Ã£o do interceptador de console local na funÃ§Ã£o `testar_conexao_smtp()` em `apps/administracao/services.py`, forÃ§ando conexÃ£o por socket TCP direto com o host e porta indicados (ex: `smtp.gmail.com:587`) com timeout seguro de 15 segundos.
  - SincronizaÃ§Ã£o de ParÃ¢metros e Dados da Tela: Suporte ao alias `email_destino` no `TesteSmtpSerializer` e envio dinÃ¢mico dos dados digitados na tela na hora pelo frontend (inclusive nova senha de app digitada sem precisar salvar antes no banco).
  - Presets RÃ¡pidos de Provedores: InclusÃ£o de botÃµes rÃ¡pidos `[GOOGLE GMAIL]` e `[MICROSOFT OUTLOOK]` no cabeÃ§alho do formulÃ¡rio que preenchem automaticamente o host (`smtp.gmail.com` / `smtp.office365.com`) e porta (`587`) com 1 clique.
  - Versionamento PWA: Cache elevado para `emc-soldas-v3.8` em `frontend/sw.js` e sufixos de cache-busting `?v=3.8` em `frontend/index.html`.
  - SuÃ­te de Testes Automatizados: 17 testes executados e 100% aprovados (`apps.administracao`).
- [x] **GestÃ£o de Formas & Regras Comerciais de Pagamento e CRUD Completo de DicionÃ¡rios Mestres (PWA v3.9):**
  - **Aba de Formas & Regras de Pagamento:** CriaÃ§Ã£o da aba dedicada na Central do Administrador (`#/administracao`) estruturada em duas tabelas no padrÃ£o *Industrial Integrity*:
    - **Meios de Pagamento (`MeioPagamento`):** Listagem com ID, Nome, badge de Taxa de Maquininha (sim/nÃ£o), Status e botÃµes de `EDITAR` e `EXCLUIR` (soft delete seguro com bloqueio automÃ¡tico pelo backend caso haja regras ativas ou movimentaÃ§Ãµes vinculadas).
    - **Regras Comerciais (`RegraPagamento`):** Listagem com Meio vinculado, Tipo de CobranÃ§a (`Ã€ VISTA`, `A PRAZO`, `PARCELADO`), nÃºmero de parcelas, intervalos e prazos de vencimento em dias, percentual de desconto sugerido, Status e botÃµes de `EDITAR` e `EXCLUIR` (soft delete seguro com bloqueio automÃ¡tico pelo backend caso haja propostas ou faturas vinculadas).
    - Modais industriais para criaÃ§Ã£o e ediÃ§Ã£o com validaÃ§Ãµes reativas e atualizaÃ§Ã£o em tempo real.
  - **CRUD Completo em DicionÃ¡rios Mestres (UOM & Atributos TÃ©cnicos):**
    - AdiÃ§Ã£o de coluna `AÃ‡Ã•ES` com botÃµes `EDITAR` e `EXCLUIR` nas tabelas de Unidades de Medida (`DicionarioUom`) e Atributos TÃ©cnicos (`DicionarioAtributo`).
    - Modais dedicados de ediÃ§Ã£o com suporte a `PUT` nas rotas da API.
    - ExclusÃ£o lÃ³gica com confirmaÃ§Ã£o e tratamento gracioso das proteÃ§Ãµes do backend (impedindo exclusÃ£o de UOMs ou atributos em uso por itens/produtos no catÃ¡logo).
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v3.9` em `frontend/sw.js` e sufixos de cache-busting `?v=3.9` em `frontend/index.html`.
  - **SuÃ­te de Testes Automatizados:** 49 testes executados e 100% aprovados (`apps.financeiro`, `apps.catalogo`, `apps.administracao`).
- [x] **ReestruturaÃ§Ã£o e Empilhamento Vertical de Formas & Regras Comerciais de Pagamento (PWA v4.0):**
  - **Empilhamento Vertical 100%:** TransiÃ§Ã£o do layout de 2 colunas paralelas apertadas (`5fr` / `7fr`) para disposiÃ§Ã£o empilhada (um card abaixo do outro com largura total), eliminando esmagamentos de texto, truncamento no cabeÃ§alho e cortes horizontais na tabela de regras.
  - **Card Superior (Meios de Pagamento):** Largura completa com visual arejado e tabela densa (`ID`, `NOME DO MEIO`, `TAXA MAQUININHA`, `STATUS`, `AÃ‡Ã•ES`), botÃ£o `+ NOVO MEIO DE PAGAMENTO`.
  - **Card Inferior (Regras Comerciais):** Largura completa acomodando com total folga e legibilidade as 9 colunas (`ID`, `NOME DA REGRA`, `MEIO VINCULADO`, `TIPO COBRANÃ‡A`, `PARCELAS`, `PRAZOS / INTERVALO`, `DESCONTO (%)`, `STATUS`, `AÃ‡Ã•ES`), botÃ£o `+ NOVA REGRA COMERCIAL` com rÃ³tulo completo e botÃµes de aÃ§Ã£o folgados.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.0` em `frontend/sw.js` e sufixos de cache-busting `?v=4.0` em `frontend/index.html`.
  - **SuÃ­te de Testes Automatizados:** 34 testes executados e 100% aprovados (`apps.administracao`, `apps.financeiro`).
- [x] **Fluidez Vertical e EliminaÃ§Ã£o de Scroll Horizontal em Modais Mobile (PWA v4.1):**
  - **Blindagem Global Anti-Scroll Horizontal:** ConfiguraÃ§Ã£o de `overflow-x: hidden;` e `box-sizing: border-box;` em `.modal-card` e `.modal-body` no `industrial-integrity.css`, eliminando barras de rolagem horizontais em qualquer modal da aplicaÃ§Ã£o.
  - **Classes UtilitÃ¡rias de Grids Responsivos:** ImplementaÃ§Ã£o de `.form-grid-2` e `.form-grid-3` e ampliaÃ§Ã£o do seletor responsivo (`.modal-body div[style*="grid-template-columns"]`, `.modal-body div[style*="display: grid"]`, `.form-grid-2`, `.form-grid-3`), forÃ§ando colapso automÃ¡tico para 1 coluna (`grid-template-columns: 1fr !important;`) em telas `<= 768px` (smartphones em modo retrato e paisagem).
  - **ReestruturaÃ§Ã£o do Modal de Regras de Pagamento:** EliminaÃ§Ã£o de grids inline rÃ­gidos, garantindo que parcelas, prazos e descontos quebrem suavemente em linhas individuais no celular, rolando com fluidez natural exclusivamente na vertical.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.1` em `frontend/sw.js` e sufixos de cache-busting `?v=4.1` em `frontend/index.html`.
  - **SuÃ­te de Testes Automatizados:** 34 testes executados e 100% aprovados (`apps.administracao`, `apps.financeiro`).
- [x] **Combobox PesquisÃ¡vel com Autocomplete para Insumos na Ficha TÃ©cnica BOM (PWA v4.2):**
  - **Campo de Busca e DigitaÃ§Ã£o em Tempo Real:** ConversÃ£o do seletor nativo `<select id="add-ficha-item-id">` no modal de Ficha TÃ©cnica (BOM) em componente dinÃ¢mico `window.EMCUtils.initSearchableSelect`, idÃªntico ao de veÃ­culos e orÃ§amentos, permitindo digitar trechos de insumos e matÃ©rias-primas e filtrar instantaneamente.
  - **OrdenaÃ§Ã£o AlfabÃ©tica PrÃ©via:** OrdenaÃ§Ã£o automÃ¡tica alfabÃ©tica por nome (`localeCompare`) dos itens retornados da API antes da montagem das opÃ§Ãµes.
  - **NavegaÃ§Ã£o Completa por Teclado:** Suporte total a navegaÃ§Ã£o com setas cima/baixo, Enter para selecionar e Esc para fechar, mantendo o valor selecionado no select nativo e submissÃ£o 100% compatÃ­vel com a API REST.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.2` em `frontend/sw.js` e sufixos de cache-busting `?v=4.2` em `frontend/index.html`.
- [x] **ReestruturaÃ§Ã£o Universal das Barras de Filtros e Comboboxes com Flags Multiselect (PWA v4.3):**
  - **EliminaÃ§Ã£o de EspaÃ§os Vazios e Larguras Fixas:** RemoÃ§Ã£o de travas de `max-width: 380px`, adotando campos de pesquisa elÃ¡sticos (`flex: 1; min-width: 240px;`), chips contadores em tempo real (`status-chip secondary`) e botÃµes primÃ¡rios integrados Ã  barra em todas as telas principais do sistema.
  - **CatÃ¡logo & Motor BOM (`/#catalogo`):** Ambas as abas (Insumos e Produtos) reformuladas com busca elÃ¡stica, chip totalizador e botÃ£o primÃ¡rio, respeitando a diretriz de nÃ£o utilizar filtro de unidade de medida.
  - **Compras & Entradas (`/#compras`):** Barra unificada com busca elÃ¡stica por NFe, combobox pesquisÃ¡vel de fornecedores, chip totalizador e botÃ£o `+ LANÃ‡AR NOTA DE COMPRA`.
  - **Tesouraria & Caixa (`/#tesouraria`):**
    - *Aba Extrato:* Busca elÃ¡stica, combobox multiselect com flags para Contas BancÃ¡rias (seleÃ§Ã£o de 1 ou N contas com botÃµes rÃ¡pidos `[âœ“ TODOS]` e `[âœ• LIMPAR]`), filtro de tipo e botÃ£o de lanÃ§amento.
    - *Aba Contas a Pagar:* Busca elÃ¡stica, combobox multiselect com flags para Status (`PENDENTE`, `PAGO`, `PARCIAL`, `CANCELADO`), chip totalizador e botÃ£o de despesa rÃ¡pida.
    - *Aba Contas a Receber:* Busca elÃ¡stica, combobox multiselect com flags para Status, chip totalizador e botÃ£o de receita rÃ¡pida.
  - **Faturamento (`/#faturamento`):** Busca elÃ¡stica por cliente/fatura, combobox multiselect com flags para Status (`FATURADO`, `PAGO`, `PARCIAL`, `CANCELADO`), chip totalizador e atalho para Conta Corrente.
  - **OrÃ§amentos (`/#orcamentos`):** Busca elÃ¡stica por cliente/equipamento/nÃºmero, combobox multiselect com flags para Status Operacional, filtro de status financeiro, chip totalizador e botÃ£o `+ NOVO ORÃ‡AMENTO` integrado.
  - **Backend com Suporte a Filtros MÃºltiplos Separados por VÃ­rgula:** Suporte a filtros `status__in`, `conta_id__in`, `status_operacional__in` e `status_financeiro__in` via DRF Queryset em `LancamentoFinanceiroViewSet`, `FaturaViewSet` e `OrcamentoViewSet`.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.3` em `frontend/sw.js` e sufixos de cache-busting `?v=4.3` em `frontend/index.html`.
- [x] **PadronizaÃ§Ã£o Visual Universal de Controles (42px), CorreÃ§Ã£o de Tela e GovernanÃ§a de Commits (PWA v4.4):**
  - **CorreÃ§Ã£o de Runtime na Tela de Compras (`/#compras`):** ConversÃ£o de `render(container)` para mÃ©todo assÃ­ncrono `async render(container)` em `compras-view.js`, eliminando o erro de sintaxe `SyntaxError: await is only valid in async functions` que causava `Cannot read properties of undefined (reading 'render')`.
  - **Altura CanÃ´nica Universal de 42px para Controles Interativos:** FixaÃ§Ã£o estrita de `height: 42px; box-sizing: border-box !important;` em `.form-control`, `select.form-control`, `.btn`, `.emc-combobox-trigger` e `.emc-multiselect-trigger` no `industrial-integrity.css`, eliminando qualquer desnÃ­vel de pixels entre textboxes, comboboxes e botÃµes nas barras de ferramentas.
  - **HarmonizaÃ§Ã£o CromÃ¡tica e PrevenÃ§Ã£o de Encavalamento:** DeclaraÃ§Ã£o de `--color-rust-orange-bright: #ff6b35;` no `:root`, correÃ§Ã£o de contraste em textos selecionados e padding de foco compensado (`0 13px`) para preservar a altura total exata de 42px com borda de 2px.
  - **Norma Documental de Layout em `docs/DESIGN.md`:** Registro da seÃ§Ã£o normativa "Interactive Controls & Dimensional Consistency" definindo alturas (42px padrÃ£o, 32px small), tipografia tÃ©cnica (`Inter` para dados, `JetBrains Mono` para botÃµes e cÃ³digos) e alinhamento em flex containers.
  - **GovernanÃ§a de Commits SemÃ¢nticos em `AGENTS.md` e `docs/FSD.md`:** InclusÃ£o da Regra MandatÃ³ria 13 no `AGENTS.md` exigindo commits formais apÃ³s cada Implementation Plan aprovado e inclusÃ£o da SeÃ§Ã£o 30 no `docs/FSD.md` com a tabela e convenÃ§Ãµes completas do Conventional Commits.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.4` em `frontend/sw.js` e sufixos de cache-busting `?v=4.4` em `frontend/index.html`.
- [x] **CorreÃ§Ã£o de EspaÃ§amento e EliminaÃ§Ã£o de Encavalamento nas Comboboxes da Aba Extrato (PWA v4.5):**
  - **Blindagem do Componente `.emc-multiselect`:** ConfiguraÃ§Ã£o mandatÃ³ria de `display: block; width: 100%; box-sizing: border-box;` no Design System (`industrial-integrity.css`), impedindo que o container multi-seleÃ§Ã£o vaze horizontalmente para alÃ©m do seu wrapper e cause fusÃ£o visual de bordas com seletores adjacentes.
  - **CalibraÃ§Ã£o Dimensional da Barra de Filtros do Extrato:** Redimensionamento de `#wrapper-extrato-conta` para `220px` (min-width `180px`) e `#filtro-extrato-tipo` para `160px` (min-width `150px`) em `financeiro-view.js`, preservando folga elÃ¡stica e espaÃ§amento fÃ­sico nÃ­tido de `gap: 10px` entre todos os controles interativos.
  - **OcultaÃ§Ã£o Estrita do Select Nativo:** ReforÃ§o com `display: none !important` via JavaScript em `utils.js` para garantir que nÃ³s nativos nÃ£o ocupem fluxo de layout residual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.5` em `frontend/sw.js` e sufixos de cache-busting `?v=4.5` em `frontend/index.html`.
- [x] **Ajuste de Responsividade e ContenÃ§Ã£o dos Flip Cards do Dashboard no Mobile (PWA v4.6):**
  - **PrevenÃ§Ã£o de Transbordamento Vertical:** ElevaÃ§Ã£o da altura de `.flip-card-wrapper` na media query `@media (max-width: 480px)` de `155px` para `195px` em `layout.css` e `industrial-integrity.css`, comportando perfeitamente a quebra de 2 linhas do tÃ­tulo "OPERAÃ‡ÃƒO DE OFICINA" com o selo "GIRE â†»" e o subtÃ­tulo descritivo em colunas de smartphone.
  - **ContenÃ§Ã£o e Blindagem de Faces:** AplicaÃ§Ã£o de `overflow: hidden;` nas faces `.flip-card-front` e `.flip-card-back` com padding de `10px 8px`.
  - **OtimizaÃ§Ã£o de Fontes e EspaÃ§amentos:** CalibraÃ§Ã£o de `flip-card-title` (10px), `flip-card-sub` (11px, line-height 1.2), `flip-card-footer` (padding 6px/margin 4px), `flip-card-btn-detail` (10.5px) e versos dos cards (font 11px, line-height 1.4) para garantir estÃ©tica industrial equilibrada e eliminaÃ§Ã£o completa de vazamento.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.6` em `frontend/sw.js` e sufixos de cache-busting `?v=4.6` em `frontend/index.html`.
- [x] **Combobox Autocomplete PesquisÃ¡vel e Modal de Cadastro de Fornecedor em Compras (PWA v4.7):**
  - **Combobox com Busca em Tempo Real e Autocomplete:** ConversÃ£o do `<select id="nota-fornecedor">` e `<select id="sub-item-id">` no modal de Compras (`LANÃ‡AR NOTA FISCAL DE ENTRADA`) em comboboxes pesquisÃ¡veis industriais (`initSearchableSelect`), eliminando o seletor nativo do mobile e permitindo filtrar por nome/razÃ£o social em tempo real.
  - **Suporte Arquitetural a Modais Empilhados (*Stacked Modals*):** RefatoraÃ§Ã£o de `openModal` e `closeModal` em `utils.js` para gerenciamento dinÃ¢mico via pilha (`modalStack`) com *z-index* incremental, possibilitando abrir o modal de cadastro de fornecedor sobre o modal de compras sem fechÃ¡-lo ou destruir os dados digitados na nota.
  - **AÃ§Ã£o Integrada "+ NOVO FORNECEDOR":** DisponibilizaÃ§Ã£o de atalho visual no cabeÃ§alho do campo e botÃ£o de aÃ§Ã£o integrado dentro do dropdown pesquisÃ¡vel da combobox (`.emc-combobox-action`).
  - **RetroalimentaÃ§Ã£o e SeleÃ§Ã£o AutomÃ¡tica:** Ao concluir o cadastro no modal secundÃ¡rio, a combobox de compras Ã© atualizada dinamicamente com as opÃ§Ãµes ordenadas e o novo fornecedor jÃ¡ selecionado, sem perda de contexto ou recarregamento de pÃ¡gina.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.7` em `frontend/sw.js` e sufixos de cache-busting `?v=4.7` em `frontend/index.html`.
- [x] **CorreÃ§Ã£o de Fechamento de Bloco JSDoc em `utils.js` e Blindagem de Abertura de Compras (PWA v4.8):**
  - **CorreÃ§Ã£o CrÃ­tica de Runtime em `openModal`:** Fechamento do bloco JSDoc da SeÃ§Ã£o 6 de `frontend/assets/js/utils.js` com `*/` antes de `const modalStack = [];`, resolvendo `ReferenceError: modalStack is not defined` que impedia a abertura do modal de compras e de outros modais do sistema.
  - **Blindagem Defensiva em `compras-view.js`:** Envolvimento do mÃ©todo `abrirModalCompra()` em bloco `try ... catch` com feedback claro via Toast notification caso haja falhas de carregamento ou rede.
  - **HomologaÃ§Ã£o da Bateria de Testes Backend:** ExecuÃ§Ã£o de 161 testes do Django com 100% de aprovaÃ§Ã£o (0 erros, 0 falhas).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.8` em `frontend/sw.js` e sufixos de cache-busting `?v=4.8` em `frontend/index.html`.
- [x] **Auto-CÃ¡lculo de Valor Total e Upload/Download Seguro de DANFE/XML em Compras (PWA v4.9):**
  - **Blindagem do Valor Total:** O frontend passa a calcular a soma dos subtotais dos itens e injetar `valor_total` no payload JSON. O serializer do backend torna o campo opcional e calcula automaticamente caso omitido, eliminando o erro de validaÃ§Ã£o `"valor_total Ã© obrigatÃ³rio"`.
  - **Hardening e ValidaÃ§Ã£o Rigorosa de Arquivos (Headers/Magic Bytes):** Implementada checagem binÃ¡ria dos primeiros bytes do arquivo (`%PDF`, `\x89PNG`, `\xff\xd8\xff`), proteÃ§Ã£o estrita contra Path Traversal e Null Bytes no nome do arquivo, e proteÃ§Ã£o anti-XXE com bloqueio de DTD e entidades externas em arquivos XML.
  - **Upload e GestÃ£o da DANFE no Frontend:** Campo de arquivo no modal de compras (`accept=".pdf,.xml"`), upload automÃ¡tico em `FormData` apÃ³s registro da nota, botÃ£o `ðŸ“„ DANFE` na listagem de notas e opÃ§Ã£o de download seguro no modal de detalhes via Blob com Content-Disposition forÃ§ado.
  - **HomologaÃ§Ã£o da Bateria de Testes:** ExecuÃ§Ã£o de 163 testes automatizados do Django com 100% de aprovaÃ§Ã£o (OK em 65.1s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.9` em `frontend/sw.js` e sufixos de cache-busting `?v=4.9` em `frontend/index.html`.
- [x] **Alinhamento Horizontal, Enquadramento Proporcional e EstilizaÃ§Ã£o Usinada do Modal de Compras (PWA v4.10):**
  - **Combobox ElÃ¡stica de Fornecedor & NÃºmero de Nota Compacto:** Redefinido o grid superior do modal para `grid-template-columns: minmax(0, 1fr) 180px 160px; gap: 12px;`, permitindo que o seletor de fornecedor expanda organicamente para preencher o espaÃ§o remanescente, enquanto o nÃºmero da nota assume largura compacta (180px) com o rÃ³tulo conciso `"NÂº Nota (NF-e/Recibo) *"`, eliminando qualquer quebra de linha.
  - **Enquadramento Perfeito da Data de EmissÃ£o:** A coluna de data de emissÃ£o foi ajustada para 160px com `width: 100%; box-sizing: border-box;`, resolvendo o transbordamento lateral e mantendo o campo 100% contido dentro da borda direita do modal.
  - **EqualizaÃ§Ã£o Vertical dos Inputs:** Padronizada a altura dos contÃªineres de rÃ³tulos (`min-height: 22px; display: flex; align-items: center; margin-bottom: 4px;`) em todos os `.form-group` da linha, garantindo alinhamento horizontal milimÃ©trico dos campos.
  - **EstilizaÃ§Ã£o Usinada de `input[type="file"]`:** Criada regra no Design System (`industrial-integrity.css`) para `<input type="file"].form-control` e `::file-selector-button` sem cantos arredondados, com altura padronizada de 42px.
  - **HomologaÃ§Ã£o:** 163 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 82.6s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.10` em `frontend/sw.js` e sufixos de cache-busting `?v=4.10` em `frontend/index.html`.
- [x] **ImportaÃ§Ã£o Inteligente de Documento Fiscal (DANFE/XML) com PrÃ©-Preenchimento e Cruzamento Cadastral em Compras (PWA v4.11):**
  - **Posicionamento no Topo do Modal:** O campo de upload da DANFE (PDF) ou XML da NF-e foi elevado para a primeira posiÃ§Ã£o com destaque visual e feedback em tempo real de status da anÃ¡lise (`ANALISANDO DOCUMENTO...` -> `DADOS EXTRAÃDOS COM SUCESSO`).
  - **ExtraÃ§Ã£o DeterminÃ­stica sem Dados Fantasma:** Implementadas rotinas em `apps/compras/services.py` (`extrair_dados_xml_nfe` e `extrair_dados_pdf_danfe` com `pypdf>=4.0.0`) com validaÃ§Ã£o MÃ³dulo 11 da chave de 44 dÃ­gitos da NF-e e extraÃ§Ã£o estrita dos campos existentes no formulÃ¡rio (CNPJ emitente, nÃºmero da nota, data de emissÃ£o, chave e valor total).
  - **Cruzamento Cadastral por DÃ­gitos Limpos:** Endpoint `POST /api/documentos-fiscais-compra/analisar-documento/` cruza o CNPJ do emitente contra a base higienizando pontuaÃ§Ãµes.
  - **Fluxo com Modais Empilhados (*Stacked Modals*):**
    - Se for **Fornecedor** (ou *Ambos*): seleciona automaticamente na combobox e preenche nÃºmero, data e chave.
    - Se for apenas **Cliente**: exibe modal de confirmaÃ§Ã£o para habilitar como fornecedor (tipo *Ambos*) via `POST /api/clientes-fornecedores/{id}/habilitar-fornecedor/` sem duplicar registro; em caso afirmativo, atualiza, seleciona e preenche.
    - Se for **Novo Emitente**: abre o modal de cadastro de fornecedor empilhado com CNPJ e RazÃ£o Social prÃ©-preenchidos e consulta pÃºblica automÃ¡tica da Receita Federal; ao salvar, seleciona o novo fornecedor e fecha o modal secundÃ¡rio.
    - Em caso de recusa: o arquivo permanece anexado e o formulÃ¡rio Ã© liberado para ediÃ§Ã£o livre.
- [x] **DetecÃ§Ã£o de Boletos, Chaves NF-e/NFS-e e Card Enriquecido de Fornecedor (PWA v4.13):**
  - **Bloqueio Impeditivo de Boletos BancÃ¡rios:** Implementada classificaÃ§Ã£o prÃ©via de documentos em `apps/compras/services.py` (`classificar_documento_fiscal_pdf`). Boletos de cobranÃ§a e fichas de compensaÃ§Ã£o sÃ£o detectados e barrados de imediato com aviso orientativo para registro no mÃ³dulo Financeiro (Contas a Pagar), impedindo o cadastro indevido de pagadores como fornecedores.
  - **ExtraÃ§Ã£o Robusta de Chaves de 44 e 50 DÃ­gitos:**
    - Suporte formal Ã  Chave de Acesso Nacional da NFS-e (DANFSe v2.0 com 50 dÃ­gitos numÃ©ricos).
    - ExtraÃ§Ã£o Ã  prova de falhas em DANFE NF-e 55 com busca direta pelos 11 blocos de 4 dÃ­gitos formatados, evitando colisÃµes com nÃºmeros vizinhos (CNPJ/protocolos).
    - Suporte Ã  Nota Fiscal de ComunicaÃ§Ã£o EletrÃ´nica (NFCom modelo 62) presente em faturas de telecomunicaÃ§Ãµes.
  - **SegregaÃ§Ã£o Estrita Prestador vs. Tomador:** No processamento de PDFs, o extrator prioriza os blocos de `PRESTADOR / FORNECEDOR` e `EMITENTE`, descartando estritamente os dados do `TOMADOR / ADQUIRENTE` para evitar inversÃ£o cadastral.
  - **Card Enriquecido de Fornecedor NÃ£o Encontrado:** Ao analisar um documento cujo fornecedor ainda nÃ£o existe no sistema, o backend consulta a Receita Federal em tempo real (`consultar_cnpj_externo`), e o modal *"FORNECEDOR NÃƒO ENCONTRADO"* exibe a RazÃ£o Social completa, Nome Fantasia, CNPJ formatado e Localidade (Cidade/UF) para conferÃªncia segura.
  - **MÃ¡scara Especializada da Chave NFS-e (50 dÃ­gitos):** A funÃ§Ã£o `formatarChaveAcessoNfe` em `utils.js` agora aplica a mÃ¡scara canÃ´nica da NFS-e Nacional (`9999999 9 99999999999999 99999 999999999999999 9999999 9`) quando o documento possui 50 dÃ­gitos, e preserva o padrÃ£o de 11 grupos de 4 dÃ­gitos para as chaves com 44 dÃ­gitos (NF-e, NFCom).
  - **HomologaÃ§Ã£o da Bateria de Testes:** SuÃ­te completa com 168 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 67.6s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.14` em `frontend/sw.js` e sufixos de cache-busting `?v=4.14` em `frontend/index.html`.
- [x] **NormatizaÃ§Ã£o de EspaÃ§os, CÃ¡lculo de Altura e Responsividade MandatÃ³ria de Modais (PWA v4.17):**
  - **Engenharia de Layout e Teto Vertical MandatÃ³rio em `docs/DESIGN.md`:** InstituiÃ§Ã£o da SeÃ§Ã£o 5 ("Engenharia e CÃ¡lculo de EspaÃ§os para Modais e FormulÃ¡rios - Modal Spatial Budget") e regra de responsividade universal mandatÃ³ria em 100% dos componentes e modais do sistema.
  - **Regra do Teto Vertical (88vh / 94vh):** `.modal-card` com `max-height: 88vh; min-height: 0; overflow: hidden;`, cabeÃ§alho fixo (52px), rodapÃ© de aÃ§Ãµes fixo (60px, `flex-shrink: 0`) e corpo do modal com rolagem suave autocontida (`flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden;`).
  - **Densidade e CompactaÃ§Ã£o de FormulÃ¡rios em Modais:** Em `.modal-body`, o `.form-group` adota `margin-bottom: 10px; gap: 4px;` e eliminaÃ§Ã£o de `margin-top` redundantes inline.
  - **BotÃ£o de Fechar Usinado (`.modal-close-btn`):** DimensÃµes compactas (32x32px, 0px border-radius), perfeitamente centralizado com Ã­cone `âœ•` sem colidir nas bordas da moldura do cabeÃ§alho.
  - **ReestruturaÃ§Ã£o Funcional do Modal de LanÃ§amento no Extrato (`financeiro-view.js`):** Modal reconfigurado para `size: 'lg'`, banner de aviso compacto, grid `1fr 160px` para Categoria + Data de Pagamento (garantindo espaÃ§o amplo para nomes longos) e `1.2fr 1fr` para Conta BancÃ¡ria + Meio de Pagamento, mantendo 100% dos botÃµes visÃ­veis sem transbordo.
  - **CorreÃ§Ã£o Responsiva na Media Query 768px:** SubstituiÃ§Ã£o de classe legada por `.modal-card` com `width: 96vw; max-width: 96vw; max-height: 92vh; margin: auto;` e colapso automÃ¡tico de todos os grids para coluna Ãºnica (`1fr !important; gap: 10px !important;`).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.17` em `frontend/sw.js` e sufixos de cache-busting `?v=4.17` em `frontend/index.html`.
- [x] **UnificaÃ§Ã£o de AÃ§Ãµes de LanÃ§amento e ExpansÃ£o das Comboboxes de Filtro no Extrato Real (PWA v4.18):**
  - **EliminaÃ§Ã£o de RedundÃ¢ncia Operacional:** RemoÃ§Ã£o do botÃ£o secundÃ¡rio duplicado `+ LANÃ‡AMENTO AVULSO` da barra de filtros do Extrato Real em `financeiro-view.js`.
  - **CentralizaÃ§Ã£o Limpa no Topo:** PreservaÃ§Ã£o estrita dos dois botÃµes canÃ´nicos no topo da view (`+ TRANSFERÃŠNCIA INTER-CONTAS` e `+ NOVO LANÃ‡AMENTO`), com detecÃ§Ã£o inteligente de contexto ativando automaticamente o modo de Caixa Real quando a aba ativa for o Extrato.
  - **ExpansÃ£o Dimensional das Comboboxes de Filtro:**
    - Seletor de Contas BancÃ¡rias (`#wrapper-extrato-conta`): ampliado de `220px` para `270px` (min-width `240px`), eliminando reticÃªncias e exibindo `"TODAS AS CONTAS BANCÃRIAS"` por extenso com folga.
    - Seletor de Tipo de MovimentaÃ§Ã£o (`#filtro-extrato-tipo`): ampliado de `160px` para `190px` (min-width `175px`), acomodando com folga `"TODOS OS TIPOS"`, `"RECEITAS (+)"` e `"DESPESAS (-)"`.
    - Campo de Busca Textual (`#filtro-extrato-busca`): expansivo (`flex: 1; min-width: 200px;`) preenchendo o espaÃ§o remanescente com equilÃ­brio visual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.18` em `frontend/sw.js` e sufixos de cache-busting `?v=4.18` em `frontend/index.html`.
- [x] **ConciliaÃ§Ã£o BancÃ¡ria Visual com Linhas de Match BÃ©zier e OperaÃ§Ã£o Dual-Mode (PWA v4.19):**
  - **Motor SVG Nativo de ConexÃµes Curvas (BÃ©zier CÃºbicas):** ImplementaÃ§Ã£o de overlay responsivo com cÃ¡lculo dinÃ¢mico via `getBoundingClientRect()` conectando nÃ³s industriais das transaÃ§Ãµes do extrato aos cards correspondentes do ERP.
  - **Feedback SemÃ¢ntico Visual:** Linhas verdes contÃ­nuas para correspondÃªncias confirmadas, linhas Ã¢mbar tracejadas para sugestÃµes provÃ¡veis e realce instantÃ¢neo no hover/foco. OcultaÃ§Ã£o automÃ¡tica em telas menores (<900px) para ergonomia mobile.
  - **OperaÃ§Ã£o Dual-Mode (Modo Duplo):**
    - *Modo 1 (ConferÃªncia & Match):* ConciliaÃ§Ã£o de lanÃ§amentos jÃ¡ existentes no ERP, com suporte a Auto-Match 1:1, seleÃ§Ã£o manual, desconciliaÃ§Ã£o e criaÃ§Ã£o de lanÃ§amento rÃ¡pido no ato para sobras do extrato.
    - *Modo 2 (ImportaÃ§Ã£o Total & Lote):* Espelhamento automÃ¡tico de todas as linhas do extrato como prÃ©-lanÃ§amentos do ERP com linhas conectivas, permitindo ajuste inline da descriÃ§Ã£o e Categoria DRE, descarte individual com botÃ£o `âœ•` (e restauraÃ§Ã£o `â†©`), e geraÃ§Ã£o em lote com 1 clique.
  - **Endpoint e Atomicidade no Backend:** CriaÃ§Ã£o da rota `POST /api/conciliacao/importacao-lote/` com `ImportacaoLoteSerializer`, validaÃ§Ã£o contra o limite de cheque especial da conta bancÃ¡ria, execuÃ§Ã£o atÃ´mica via `transaction.atomic()`, quitaÃ§Ã£o imediata (`status_pagamento='PAGO'`), marcaÃ§Ã£o `is_conciliado=True` e auditoria perpÃ©tua.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.19` em `frontend/sw.js` e sufixos de cache-busting `?v=4.19` em `frontend/index.html`.
- [x] **Alinhamento dos NÃ³s Ã‚ncora e Luz Neon nas Linhas BÃ©zier da ConciliaÃ§Ã£o (PWA v4.20):**
  - **CoerÃªncia Visual Ponto a Ponto (NÃ³ a NÃ³):** UniversalizaÃ§Ã£o do seletor `.anchor-node` no CSS e adiÃ§Ã£o da classe `.split-item` ao container `.pre-lancamento-card`, posicionando o boton verde perfeitamente na borda esquerda (`left: -5px; top: 50%; transform: translateY(-50%)`) com sombra circular idÃªntica ao boton de saÃ­da da borda direita.
  - **Luz Neon Acelerada por GPU nas Linhas Vetoriais:** AplicaÃ§Ã£o de `filter: drop-shadow(...)` de camada dupla em `.svg-path-match` e `.svg-path-suggestion`, produzindo uma iluminaÃ§Ã£o neon nÃ­tida que acompanha perfeitamente o traÃ§ado curvilÃ­neo sem borrÃµes no DOM ou perda de performance.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.20` em `frontend/sw.js` e sufixos de cache-busting `?v=4.20` em `frontend/index.html`.
- [x] **Alinhamento do BotÃ£o de Descarte e Categoria DRE ObrigatÃ³ria em Branco (PWA v4.21):**
  - **ReestruturaÃ§Ã£o Vertical do PrÃ©-LanÃ§amento:** EliminaÃ§Ã£o do esmagamento horizontal com `display: flex !important; flex-direction: column !important; gap: 8px !important;` no `.pre-lancamento-card`, organizando o card em cabeÃ§alho superior (tÃ­tulo na esquerda, valor e botÃ£o `âœ•` de 26x24px alinhados no centro Ã  direita) e grid de ediÃ§Ã£o inferior (descriÃ§Ã£o e select).
  - **Categoria DRE Inicial em Branco:** InicializaÃ§Ã£o de `categoria_id: null` com a opÃ§Ã£o `-- SELECIONE A CATEGORIA DRE * --` no topo do select e destaque de aviso sutil (`.select-categoria-pendente`).
- [x] **InteligÃªncia na ConciliaÃ§Ã£o BancÃ¡ria, PrevenÃ§Ã£o de Duplicidade, Reconhecimento de Parceiros, RetenÃ§Ã£o de ISS e Carga HistÃ³rica (PWA v4.22):**
  - **PrevenÃ§Ã£o Robusta de Duplicidades:** Algoritmo defensivo checando se as transaÃ§Ãµes do extrato jÃ¡ existem no ERP (por FITID bancÃ¡rio Ãºnico ou por combinaÃ§Ã£o de valor idÃªntico e proximidade de Â±2 dias jÃ¡ conciliada na conta), sinalizando visualmente com badge `[ðŸ”’ JÃ NO ERP]` e descartando compulsoriamente por padrÃ£o na mesa de triagem para impedir duplicaÃ§Ãµes de saldo.
  - **Reconhecimento AutomÃ¡tico de Parceiros por CNPJ/CPF:** Parser com extraÃ§Ã£o regex de documentos na descriÃ§Ã£o da transaÃ§Ã£o (ex: `02.329.307/0001-66 - PETRA MG`), cruzando instantaneamente com `ClienteFornecedor` e exibindo badge semÃ¢ntico `[ðŸ¢ PARCEIRO IDENTIFICADO]`.
  - **Cruzamento Inteligente com Faturas em Aberto & RetenÃ§Ã£o de ISS:**
    - Flag `iss_retido` no modelo `ClienteFornecedor` com checkbox no modal de cadastro completo.
    - ParÃ¢metros Fiscais em `ConfiguracaoGlobal`: campos editÃ¡veis `aliquota_iss` (padrÃ£o 3.00%) e `aliquota_simples_nacional` (informativo, padrÃ£o 8.50%) na aba de AdministraÃ§Ã£o.
    - Cruzamento com faturas do cliente (`status='FATURADA'`): se o cliente possui retenÃ§Ã£o de ISS, o sistema calcula o valor lÃ­quido esperado (`valor_fatura - (valor_fatura * aliquota_iss / 100)`) e compara com a transaÃ§Ã£o bancÃ¡ria considerando **tolerÃ¢ncia de atÃ© 5 centavos (R$ 0,05)** para variaÃ§Ãµes de arredondamento bancÃ¡rio.
    - SugestÃ£o automÃ¡tica e baixa imediata de faturas na importaÃ§Ã£o via `receber_pagamento_fatura`, sem duplicar crÃ©dito de saldo e carimbando FITID e conciliaÃ§Ã£o nos tÃ­tulos.
  - **Carga HistÃ³rica sem OrÃ§amentos/Faturas Retroativas:** AdiÃ§Ã£o das colunas `cliente_fornecedor_id` e `fitid` em `LancamentoFinanceiro`, permitindo que receitas e despesas de perÃ­odos anteriores sejam associadas diretamente aos clientes/fornecedores reais sem exigir orÃ§amentos fictÃ­cios, alimentando perfeitamente o DRE e o DossiÃª do Cliente.
  - **ClassificaÃ§Ã£o HeurÃ­stica de Categorias DRE:** SugestÃ£o automÃ¡tica de categorias contÃ¡beis para Tarifas BancÃ¡rias (`TAR`, `IOF`, `DOC/TED`, etc.), Tributos/Guias (`DAS`, `GPS`, `FGTS`, `DARF`, etc.) e Receitas Operacionais para clientes identificados.
  - **Testes Automatizados:** SuÃ­te de conciliaÃ§Ã£o enriquecida (`test_reconhecimento_parceiro_fatura_iss_retido_e_duplicidade`) com 100% de aprovaÃ§Ã£o (72 testes automatizados acumulados em conciliaÃ§Ã£o, cadastros, administraÃ§Ã£o e financeiro).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.22` em `frontend/sw.js` e sufixos de cache-busting `?v=4.22` em `frontend/index.html`.
- [x] **PadronizaÃ§Ã£o e Contraste Industrial Escuro nas Comboboxes de Categoria DRE (PWA v4.23):**
  - **EliminaÃ§Ã£o do Fundo Branco:** RefatoraÃ§Ã£o de `.select-categoria-pendente` e `select.form-control option` para assegurar fundo escuro industrial (`var(--color-surface-container-low)` / `#1b1c1c`) e tipografia clara com legibilidade nÃ­tida em qualquer estado (selecionado ou pendente).
  - **SinalizaÃ§Ã£o Sutil de PendÃªncia:** A pendÃªncia de seleÃ§Ã£o de categoria agora Ã© indicada exclusivamente pela borda Ã¢mbar (`border-color: var(--color-warning)`), sem alterar a tonalidade de fundo nem comprometer o contraste no desktop ou mobile.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.23` em `frontend/sw.js` e sufixos de cache-busting `?v=4.23` em `frontend/index.html`.
- [x] **Rolagem SimultÃ¢nea e Sincronizada das Colunas na ConciliaÃ§Ã£o BancÃ¡ria (PWA v4.24):**
  - **Controle Visual na Barra de Ferramentas:** AdiÃ§Ã£o do toggle/checkbox `[x] ROLAGEM SIMULTÃ‚NEA` na barra de controle da tela de conciliaÃ§Ã£o com persistÃªncia em tempo real.
  - **Mecanismo de Scroll Proporcional Bidirecional:** SincronizaÃ§Ã£o inteligente baseada no ratio de deslocamento (`scrollTop / (scrollHeight - clientHeight)`) entre o Extrato BancÃ¡rio e a Mesa de Triagem/ERP, mantendo os cards equivalentes sempre alinhados lado a lado.
  - **PrevenÃ§Ã£o de Loop de Eventos:** Bloqueio atravÃ©s de flag de concorrÃªncia (`isSyncingScroll`) e renderizaÃ§Ã£o em `requestAnimationFrame`, mantendo o redesenho dinÃ¢mico das linhas BÃ©zier cÃºbicas sem travamento de tela.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.24` em `frontend/sw.js` e sufixos de cache-busting `?v=4.24` em `frontend/index.html`.
- [x] **Expurgo Operacional e Limpeza do Banco de Dados para InÃ­cio de Carga Real (ProduÃ§Ã£o):**
  - **Limpeza Segura de Dados Transacionais e Cadastrais de Teste:** ExecuÃ§Ã£o atÃ´mica via comando de management `reset_banco_para_producao --confirmar` com exclusÃ£o em ordem referencial de FKs (`LancamentoFinanceiro`, `Fatura`, `Orcamento`, `DocumentoFiscalCompra`, `Produto`, `Item`, `Equipamento`, `ClienteFornecedor`, cartÃµes corporativos e contas bancÃ¡rias extras).
  - **Reset de Contadores AUTO_INCREMENT para 1:** InstruÃ§Ã£o nativa `ALTER TABLE ... AUTO_INCREMENT = 1` aplicada a todas as tabelas operacionais esvaziadas, garantindo que o primeiro cliente, orÃ§amento, fatura, documento e cartÃµes comecem estritamente no ID #1.
  - **Ajuste de Sequencial de Contas BancÃ¡rias (PrÃ³ximo ID = 3):** Reset de `contas_bancarias` com `AUTO_INCREMENT = 1`, instruindo o MySQL a recalcular `max(id) + 1 = 3`, eliminando saltos nos IDs apÃ³s expurgo de contas de teste.
  - **PreservaÃ§Ã£o RÃ­gida de Tabelas Mestras e DomÃ­nio:** DicionÃ¡rios Centrais (`UOM` e `Atributos`), Categorias ContÃ¡beis DRE (13 categorias), Meios e Regras Comerciais de Pagamento, ConfiguraÃ§Ãµes Globais e usuÃ¡rio Administrador Master (`admin@emcsoldas.com.br`) com seus 10 toggles dinÃ¢micos.
  - **Contas BancÃ¡rias Zeradas:** As contas padrÃ£o estruturais (`CAIXA FISICO DA OFICINA` e `CONTA BANCARIA PRINCIPAL`) foram preservadas e inicializadas com saldo exato de `R$ 0,00`, prontas para receber os extratos bancÃ¡rios de 02/2025.
- [x] **SeleÃ§Ã£o ObrigatÃ³ria de Conta BancÃ¡ria na ConciliaÃ§Ã£o e DetecÃ§Ã£o HeurÃ­stica de Meios de Pagamento (PWA v4.28):**
  - **SeleÃ§Ã£o Ativa MandatÃ³ria de Conta:** A tela de conciliaÃ§Ã£o bancÃ¡ria (`#/conciliacao`) agora inicializa estritamente com `-- SELECIONE A CONTA BANCÃRIA * --` sem prÃ©-selecionar nenhuma conta por padrÃ£o. O botÃ£o de upload e a anÃ¡lise ficam bloqueados atÃ© que o operador selecione conscientemente a conta de destino, eliminando conciliaÃ§Ãµes por engano.
  - **Classificador HeurÃ­stico Inteligente de Meios de Pagamento:** ImplementaÃ§Ã£o de motor em `apps/conciliacao/services.py` (`detectar_meio_pagamento_transacao`) com anÃ¡lise de padrÃµes no `<MEMO>`, `<NAME>` e `<TRNTYPE>` do OFX, categorizando com precisÃ£o: `PIX` (transferÃªncias, chaves, QR codes), `CARTÃƒO DE DÃ‰BITO`, `CARTÃƒO DE CRÃ‰DITO`, `TRANSFERÃŠNCIA (TED/DOC)`, `BOLETO BANCÃRIO` e `DEPÃ“SITO BANCÃRIO / DINHEIRO`.
  - **Mesa de Triagem Enriquecida (Modo 2):** Cada card de transaÃ§Ã£o na esteira de importaÃ§Ã£o passa a exibir uma combobox pesquisÃ¡vel de Meio de Pagamento prÃ©-preenchida com a sugestÃ£o inteligente, permitindo ao operador alterar manualmente antes de confirmar a importaÃ§Ã£o em lote.
  - **PersistÃªncia Fiel no Backend:** O endpoint de importaÃ§Ã£o em lote (`executar_importacao_lote`) agora lÃª o `meio_pagamento_id` real enviado em cada transaÃ§Ã£o, eliminando o fallback genÃ©rico que gravava tudo como boleto bancÃ¡rio.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.28` em `frontend/sw.js` e sufixos de cache-busting `?v=4.28` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** SuÃ­te completa com 184 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 74s).
- [x] **ReestruturaÃ§Ã£o das Categorias DRE, Purga de Testes (C1) e Blindagem de Credenciais do Seeder:**
  - **ReestruturaÃ§Ã£o Oficial das 20 Categorias:** ReformulaÃ§Ã£o do catÃ¡logo de categorias contÃ¡beis no `seed_initial_data.py` e no banco de dados. RemoÃ§Ã£o de `(MAO DE OBRA)` de receitas, criaÃ§Ã£o de `AQUISIÃ‡ÃƒO DE MÃQUINAS E EQUIPAMENTOS` (Investimento CAPEX) segregada de `MANUTENÃ‡ÃƒO DE MÃQUINAS E INSTALAÃ‡Ã•ES` (OPEX), e separaÃ§Ã£o clara entre `FOLHA DE PAGAMENTO (SALARIOS E BENEFICIOS)`, `ENCARGOS TRABALHISTAS (FGTS E INSS)`, `PRO-LABORE DOS SOCIOS`, `IMPOSTOS E TRIBUTOS (SIMPLES NACIONAL / ISS / TAXAS)` e `RETIRADA DE SOCIOS / DISTRIBUICAO DE LUCRO`.
  - **Purga Definitiva de Registros de Teste:** ExclusÃ£o automÃ¡tica de categorias residuais de teste (`C1`) e migraÃ§Ã£o atÃ´mica sem duplicidade de IDs para categorias prÃ©-existentes.
  - **Blindagem de Credenciais no Seeder:** SubstituiÃ§Ã£o de senhas/PINs hardcoded em `seed_initial_data.py` por leitura dinÃ¢mica via variÃ¡veis de ambiente (`INITIAL_ADMIN_PASSWORD` e `INITIAL_ADMIN_PIN`) com fallback transparente para o ambiente de desenvolvimento local.
  - **Enriquecimento do Classificador HeurÃ­stico do Extrato:** AtualizaÃ§Ã£o do motor de detecÃ§Ã£o em `apps/conciliacao/services.py` para mapear extratos automaticamente para as novas categorias oficiais (tarifas, tributos, encargos, combustÃ­vel, energia/Ã¡gua/internet, salÃ¡rios e receitas).
  - **HomologaÃ§Ã£o:** SuÃ­te completa de 184 testes automatizados do Django executada e aprovada com 100% de sucesso (OK em 79.9s).
- [x] **Blindagem de Saldos de Contas BancÃ¡rias no Seeder, RestauraÃ§Ã£o e AÃ§Ã£o de RecÃ¡lculo AutomÃ¡tico (PWA v4.29):**
  - **Blindagem Definitiva do Seeder:** AtualizaÃ§Ã£o da SeÃ§Ã£o 6 em `seed_initial_data.py` com checagem `ContaBancaria.all_objects.exists()`, eliminando o risco de o seeder sobrescrever saldos reais de contas bancÃ¡rias ativas durante sincronizaÃ§Ãµes de dados mestres.
  - **Endpoint de RecÃ¡lculo de Saldo (`POST /api/contas-bancarias/{id}/recalcular-saldo/`):** ImplementaÃ§Ã£o de motor de conciliaÃ§Ã£o no `ContaBancariaViewSet` que audita e soma todas as entradas pagas, subtrai saÃ­das pagas e aplica transferÃªncias inter-contas ativas, sincronizando o saldo com as movimentaÃ§Ãµes reais.
  - **RestauraÃ§Ã£o da Conta NUBANK:** Saldo da conta #2 restabelecido com precisÃ£o contÃ¡bil para **R$ 2.100,39** (R$ 10.898,20 de entradas - R$ 8.797,81 de saÃ­das).
  - **BotÃ£o 'RECALCULAR' no Frontend:** AÃ§Ã£o direta na tabela de Contas BancÃ¡rias (`financeiro-view.js`) permitindo ao operador auditar e re-sincronizar o saldo da conta a qualquer momento em 1 clique com feedback visual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.29` em `frontend/sw.js` e sufixos de cache-busting `?v=4.29` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** SuÃ­te completa com 185 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 71.5s).
- [x] **Responsividade Mobile da Barra de Ferramentas de ConciliaÃ§Ã£o BancÃ¡ria (PWA v4.30):**
  - **EliminaÃ§Ã£o do Transbordamento Horizontal:** SubstituiÃ§Ã£o de estilos rÃ­gidos inline por classes semÃ¢nticas (`.conciliacao-toolbar-content`, `.conciliacao-conta-group`, `.conciliacao-modos-group`, `.conciliacao-sync-group`, `.conciliacao-acoes-group`) em `industrial-integrity.css` e `conciliacao-view.js`.
  - **Layout Fluido em Duas Linhas no Mobile (`<= 768px`):**
    - Seletor de conta e botÃµes de alternÃ¢ncia de modo passam a ocupar 100% da largura em blocos ergonÃ´micos para toque.
    - Os botÃµes secundÃ¡rios contextuais (`âš¡ AUTO-MATCH` e `+ LANÃ‡AMENTO RÃPIDO`) dividem a primeira linha com largura igual (`calc(50% - 4px)`).
    - O botÃ£o primÃ¡rio de aÃ§Ã£o (`CONFIRMAR CONCILIAÃ‡ÃƒO` no Modo 1 ou `âš¡ GERAR E CONCILIAR EM LOTE` no Modo 2) ocupa a segunda linha isolada com largura total de 100% (`flex: 1 1 100%`), eliminando o truncamento de texto (`CONFIRMA...`) e impedindo estouro de tela.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.30` em `frontend/sw.js` e sufixos de cache-busting `?v=4.30` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** SuÃ­te completa com 185 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 76.1s).
- [x] **Blindagem do Service Worker para Uploads e OperaÃ§Ãµes de MutaÃ§Ã£o no Celular (PWA v4.31):**
  - **Bypass de MÃ©todos de MutaÃ§Ã£o no Service Worker:** ImplementaÃ§Ã£o de clÃ¡usula de escape imediato `if (event.request.method !== 'GET') return;` no listener de `fetch` em `frontend/sw.js`.
  - **EliminaÃ§Ã£o de Falsos Positivos de DesconexÃ£o Offline:** Uploads multipart de extratos bancÃ¡rios (OFX/CSV), documentos de compras e anexos passam a trafegar diretamente pela pilha de rede nativa do navegador mÃ³vel (Android/iOS), contornando limitaÃ§Ãµes de streaming do worker thread em redes 4G/5G remotas.
  - **PreservaÃ§Ã£o Integral de SeguranÃ§a e Cache:** Cookies HttpOnly, cabeÃ§alhos CSRF e tokens continuam sendo transmitidos diretamente pelo navegador, mantendo o cache e a inicializaÃ§Ã£o instantÃ¢nea para pÃ¡ginas e assets estÃ¡ticos.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.31` em `frontend/sw.js` e sufixos de cache-busting `?v=4.31` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** SuÃ­te completa com 185 testes automatizados do Django executados com 100% de aprovaÃ§Ã£o (OK em 80.1s).
- [x] **Anexo de Comprovantes/NFs e Redesign Ultra-Denso da Mesa de Triagem (PWA v4.32):**
  - **Anexo Inline de Documentos na ConciliaÃ§Ã£o:** AdiÃ§Ã£o de suporte ao upload de Notas Fiscais (em Recebimentos) e Comprovantes de Pagamento (em SaÃ­das) diretamente na Mesa de Triagem (`Modo ImportaÃ§Ã£o em Lote`). BotÃ£o micro-inline `[ðŸ“Ž + NF]` ou `[ðŸ“Ž + RECIBO]` que se converte dinamicamente em badge verde neon `[ðŸ“Ž NF_123.pdf âœ•]`, permitindo vincular arquivos PDF, PNG, JPG ou XML a cada transaÃ§Ã£o prÃ©-lanÃ§ada.
  - **Redesign Arquitetural Ultra-Denso (EliminaÃ§Ã£o do Descompasso de Altura):** ReorganizaÃ§Ã£o dos cards da mesa de triagem em **2 linhas horizontais densas (~72px de altura)**:
    - Linha 1: TÃ­tulo e Data, Valor Formatado (`+ / - R$`), BotÃ£o/Badge Inline de Anexo e BotÃ£o `âœ•` de Descarte.
    - Linha 2: Grid horizontal de 3 colunas (`DescriÃ§Ã£o`, `Meio de Pagamento`, `Categoria DRE`), eliminando o empilhamento vertical e reduzindo a altura do card em mais de 50%, eliminando a discrepÃ¢ncia com a coluna do extrato.
  - **Backend & PersistÃªncia:** Campos `comprovante` (`FileField`) e `nome_arquivo_comprovante` adicionados a `LancamentoFinanceiro` (Migration `financeiro.0005`), com endpoint `POST /api/conciliacao/upload-comprovante/` e integraÃ§Ã£o no serviÃ§o `executar_importacao_lote`.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.32` em `frontend/sw.js` e sufixos de cache-busting `?v=4.32` em `frontend/index.html`.
- [x] **Anexo Universal de Comprovantes na Tesouraria e Modais (PWA v4.33):**
  - **Coluna ANEXO na Tabela do Extrato Real:** AdiÃ§Ã£o da coluna `ANEXO` na listagem do Caixa Real (`financeiro-view.js`). Para movimentaÃ§Ãµes com anexo, exibe badge verde `[ðŸ“Ž NomeArquivo]` que abre/baixa o comprovante diretamente em nova aba; para lanÃ§amentos sem anexo, exibe o botÃ£o `[ðŸ“Ž + ANEXO]` para upload instantÃ¢neo diretamente da linha.
  - **Modais de LanÃ§amento Avulso e EdiÃ§Ã£o:** Campo de seleÃ§Ã£o de arquivos `<input type="file">` adicionado em `abrirModalNovoLancamento` e `abrirModalEditarLancamento`, efetuando o upload prÃ©vio e integrando os caminhos aos payloads de criaÃ§Ã£o (`POST`) e atualizaÃ§Ã£o (`PATCH`).
  - **Modal de TransferÃªncia Inter-Contas:** Atualizados `TransferenciaInterContasSerializer`, `transferir_inter_contas` e o modal `abrirModalTransferencia`, registrando o comprovante da operaÃ§Ã£o no lanÃ§amento de transferÃªncia gerado.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.33` em `frontend/sw.js` e sufixos de cache-busting `?v=4.33` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 38 testes automatizados do Django executados com 100% de sucesso.
- [x] **CorreÃ§Ã£o da SerializaÃ§Ã£o de Comprovantes em LanÃ§amentos Financeiros:**
  - **DiagnÃ³stico:** O DRF `ModelSerializer` padrÃ£o rejeitava strings de caminhos relativos salvas previamente pelo endpoint de upload (`comprovantes/...`) nos mÃ©todos `POST` e `PATCH` de `/api/lancamentos-financeiros/`, disparando o erro *"O dado submetido nÃ£o era um arquivo. Cheque o tipo de codificaÃ§Ã£o no formulÃ¡rio"*.
  - **SoluÃ§Ã£o Arquitetural:** ImplementaÃ§Ã£o do campo hÃ­brido `ComprovanteFileOrCharField(serializers.FileField)` em `backend/apps/financeiro/serializers.py`, aceitando perfeitamente caminhos relativos de arquivos jÃ¡ armazenados no servidor, URLs sanitizadas, arquivos diretos (`UploadedFile`) e valores nulos (desvinculaÃ§Ã£o/remoÃ§Ã£o de anexo).
- [x] **DetecÃ§Ã£o de CorrespondÃªncia e ConferÃªncia Anti-Duplicidade na ImportaÃ§Ã£o de Extratos BancÃ¡rios (PWA v4.34):**
  - **IdentificaÃ§Ã£o AutomÃ¡tica de LanÃ§amentos Manuais PrÃ©-Existentes:** No backend (`backend/apps/conciliacao/services.py`), o motor de enriquecimento passa a identificar lanÃ§amentos manuais pendentes de conciliaÃ§Ã£o (`is_conciliado=False`) que possuam mesma conta bancÃ¡ria, mesma direÃ§Ã£o (`ENTRADA`/`SAIDA`), valor idÃªntico ($\pm$ R$ 0,05) e data prÃ³xima ($\pm$ 3 dias), ignorando diferenÃ§as de texto/descriÃ§Ã£o entre o extrato bancÃ¡rio e o lanÃ§amento manual, anexando o objeto `lancamento_correspondente`.
  - **PrevenÃ§Ã£o AtÃ´mica de Saldo Duplo (`executar_importacao_lote`):** Ao receber `lancamento_existente_id` com aÃ§Ã£o `VINCULAR`, o sistema carimba o FITID bancÃ¡rio e concilia o registro existente sem criar um segundo lanÃ§amento no MySQL. Caso o lanÃ§amento manual jÃ¡ estivesse liquidado como `PAGO` na conta, o backend deduz o valor do recÃ¡lculo de saldo da importaÃ§Ã£o, impedindo que o saldo seja creditado/debitado duas vezes no Caixa Real.
  - **Modal Industrial de ConferÃªncia Anti-Duplicidade:** Abertura automÃ¡tica ao importar extratos com correspondÃªncias (ou via botÃ£o `âš ï¸ CONFERÃŠNCIA` na barra de aÃ§Ãµes), exibindo tabela comparativa lado a lado (Extrato vs LanÃ§amento no ERP) com opÃ§Ãµes de rÃ¡dio: `[ðŸ”˜ VINCULAR E CONCILIAR (Recomendado)]`, `[âšª CRIAR NOVO LANÃ‡AMENTO]` e `[âšª DESCARTAR DO EXTRATO]`.
  - **Mesa de Triagem com AÃ§Ã£o Contextual:** Cards com correspondÃªncia identificada recebem destaque Ã¢mbar/verde no padrÃ£o *Industrial Integrity*, opÃ§Ãµes de rÃ¡dio para alternÃ¢ncia Ã¡gil de aÃ§Ã£o e atualizaÃ§Ã£o automÃ¡tica do texto do botÃ£o `âš¡ IMPORTAR EM LOTE (X: Y VINCULADOS)`.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.34` em `frontend/sw.js` e sufixos de cache-busting `?v=4.34` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 15 testes de `apps.conciliacao`, 27 testes de `apps.financeiro` e 100% dos testes globais aprovados com sucesso.
- [x] **PaginaÃ§Ã£o Industrial do Extrato Real (Caixa Real) e PadronizaÃ§Ã£o na Tesouraria (PWA v4.35):**
  - **Backend - PaginaÃ§Ã£o Customizada (`backend/core/pagination.py` & `settings.py`):** CriaÃ§Ã£o da classe `StandardResultsSetPagination` baseada em `PageNumberPagination`, habilitando `page_size_query_param = 'page_size'` com `max_page_size = 1000` e padrÃ£o de 25 itens. Resolvida a limitaÃ§Ã£o do DRF que ignorava limites de itens por pÃ¡gina na API.
  - **Frontend - UtilitÃ¡rio Centralizado de PaginaÃ§Ã£o (`frontend/assets/js/utils.js`):** Implementada a funÃ§Ã£o `renderPagination` no `window.EMCUtils` com design system *Industrial Integrity* (0px border-radius, tipografia tÃ©cnica `JetBrains Mono` em nÃºmeros e contadores, janelamento inteligente de pÃ¡ginas com elipses `1 ... 4 [5] 6 ... 12`, botÃµes direcionais `Â«`, `â€¹`, `â€º`, `Â»`, bloqueio seguro nas extremidades, seletor dinÃ¢mico de linhas por pÃ¡gina de 25, 50 e 100 itens, e responsividade fluida para mobile).
  - **MÃ³dulo Financeiro (`frontend/assets/js/views/financeiro-view.js`):** Implementada a paginaÃ§Ã£o na aba **Extrato Real (Caixa Real)** com ordenaÃ§Ã£o cronolÃ³gica decrescente estrita por data de liquidaÃ§Ã£o (`ordering=-data_pagamento,-id`), contagem real no badge de total (`res.count`), reset para pÃ¡gina 1 em filtros e buscas, e manutenÃ§Ã£o da pÃ¡gina corrente em operaÃ§Ãµes de adiÃ§Ã£o, ediÃ§Ã£o, estorno ou anexo de comprovantes.
  - **PadronizaÃ§Ã£o em Contas a Pagar e Receber:** A mesma mecÃ¢nica de paginaÃ§Ã£o foi estendida Ã s abas **Contas a Pagar** e **Contas a Receber**, eliminando o limite rÃ­gido de 25 registros em toda a Tesouraria.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.35` em `frontend/sw.js` e sufixos de cache-busting `?v=4.35` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 37 testes de `core` e `apps.financeiro` e 192 testes da suÃ­te global executados com 100% de aprovaÃ§Ã£o (OK em 76.7s).
- [x] **GovernanÃ§a de Commits SemÃ¢nticos MandatÃ³rios por Implementation Plan (AGENTS.md & FSD SeÃ§Ã£o 30):**
  - **Obrigatoriedade InegociÃ¡vel no Ciclo Operacional:** AtualizaÃ§Ã£o da subseÃ§Ã£o `7.3 Ciclo de Trabalho Operacional (Passo a Passo)` do `AGENTS.md`, consolidando que todo ciclo derivado de um Implementation Plan exige, como critÃ©rio inegociÃ¡vel de conclusÃ£o, a realizaÃ§Ã£o de um commit semÃ¢ntico atÃ´mico no Git local.
  - **ProibiÃ§Ã£o de AglutinaÃ§Ã£o de Planos:** VedaÃ§Ã£o expressa ao acÃºmulo de mÃºltiplos planos ou tarefas em um Ãºnico commit genÃ©rico.
  - **PadronizaÃ§Ã£o Estrita com FSD SeÃ§Ã£o 30:** NormatizaÃ§Ã£o do formato canÃ´nico `<tipo>[escopo]: <descriÃ§Ã£o no imperativo e em pt-BR>`, tabela resumida de prefixos vÃ¡lidos (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`), as 7 regras de ouro da mensagem (50-72 caracteres, minÃºsculas, sem ponto final, imperativo em pt-BR) e proibiÃ§Ã£o absoluta de versionar credenciais/segredos.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_04_governanca_commits_ciclo_trabalho_agents.md`.
- [x] **CorreÃ§Ã£o Integral do Dashboard: 5 Flip Cards 3D, GrÃ¡fico SARGable, Feed e Filtros (PWA v4.36):**
  - **Contrato Universal nos 5 Flip Cards:** ResoluÃ§Ã£o da divergÃªncia de payload entre backend e frontend. O endpoint `/api/dashboard/flip-cards/` passa a fornecer tanto a raiz plana quanto a chave espelho `cards: { ... }`, enriquecendo as entidades com todos os aliases esperados pelo frontend (`aprovados`, `em_execucao`, `concluidos`, `cancelados`, `rascunhos`, `faturadas`, `pagas`, `faturamento_real`, `saldo_bancario_real`, `vencidas`), e o frontend adota extraÃ§Ã£o defensiva `res.cards || res || {}` com fallbacks seguros (`?? 0`).
  - **GrÃ¡fico Mensal SARGable e ResoluÃ§Ã£o de `CONVERT_TZ` no MySQL:** SubstituiÃ§Ã£o de filtros `__year` e `__month` por faixas SARGable `data_pagamento__gte=dt_ini, data_pagamento__lt=dt_fim` com timezone-aware datetimes. Isso elimina a dependÃªncia das tabelas de fuso horÃ¡rio do MySQL no Windows/XAMPP (onde `CONVERT_TZ` retornava `NULL`), permitindo que dados reais apareÃ§am de imediato. Implementada determinaÃ§Ã£o inteligente de ano (adotando o ano do Ãºltimo lanÃ§amento caso o ano corrente ainda nÃ£o possua movimentaÃ§Ãµes) e sincronizaÃ§Ã£o de chaves (`meses` e `historico`, `mes_nome` e `mes_sigla`), alÃ©m da exibiÃ§Ã£o do ano real consultado no cabeÃ§alho do card (`RECEITAS X DESPESAS (ANO)`).
  - **Feed de Atividades Recentes em Tempo Real:** InclusÃ£o dos campos `data_hora` e `timestamp` em cada atividade (orÃ§amentos, faturas, baixas de caixa e estornos) e tratamento resiliente no frontend aceitando tanto listas diretas `[...]` quanto payloads encapsulados.
  - **Filtros Temporais Ãgeis:** Implementado suporte nativo ao parÃ¢metro `?periodo=hoje`, `?periodo=mes` e `?periodo=ano` em `FiltroPeriodoSerializer`, `DashboardFlipCardsView` e `DashboardService`, calculando automaticamente as janelas temporais de agregaÃ§Ã£o.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.36` em `frontend/sw.js` e sufixos de cache-busting `?v=4.36` em `frontend/index.html`.
- [x] **DiferenciaÃ§Ã£o no Estorno: Contas a Pagar vs LanÃ§amentos Avulsos e Saneamento do LanÃ§amento #63 (PWA v4.37):**
  - **Rastreamento de Origem no Modelo:** InclusÃ£o do campo `origem` (`AGENDA`, `AVULSO`, `CONCILIACAO`, `FATURA`, `CARTAO`) em `LancamentoFinanceiro` e na serializaÃ§Ã£o, com inferÃªncia inteligente e migration retroativa para os registros existentes.
  - **LÃ³gica de Estorno Inteligente (`estornar_lancamento`):**
    - Se for **Conta Agendada (`AGENDA`, `FATURA`, `CARTAO`)**: estorno reverte o saldo na conta bancÃ¡ria e retorna o tÃ­tulo ao status `'A_VENCER'` ("nÃ£o pago") na agenda financeira, limpando conta e data de pagamento.
    - Se for **LanÃ§amento Avulso / Compra Efetivada (`AVULSO`, `CONCILIACAO`)**: estorno reverte o impacto no saldo bancÃ¡rio, transita status para `'CANCELADO'` com justificativa e aplica **Soft Delete** (`deleted_at = timezone.now()`), **nÃ£o gerando conta a pagar pendente**.
    - Ambos os fluxos mantÃªm a trilha perpÃ©tua e imutÃ¡vel de auditoria na tabela `log_estornos`.
  - **Saneamento do LanÃ§amento #63:** LanÃ§amento de teste duplicado de 02/06/2025 que havia sido estornado e permanecido indevidamente como conta a pagar em aberto teve sua origem classificada como `AVULSO`, status como `CANCELADO` e sofreu Soft Delete via data migration, zerando pendÃªncias indevidas no Contas a Pagar.
  - **ExperiÃªncia Visual (Frontend PWA):** Modal de confirmaÃ§Ã£o de estorno inspeciona a natureza do tÃ­tulo e apresenta alerta explicativo contextual (informando se o tÃ­tulo voltarÃ¡ para o Contas a Pagar ou se serÃ¡ excluÃ­do como compra avulsa).
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.37` em `sw.js` e `?v=4.37` em `index.html`.
  - **HomologaÃ§Ã£o:** 29 testes de `apps.financeiro` e 184 testes da suÃ­te global executados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_06_diferenciacao_estorno_contas_pagar_vs_avulsos.md`.
- [x] **DetecÃ§Ã£o HeurÃ­stica Universal de Meios de Pagamento, GestÃ£o de Guias da Receita Federal e Bloqueio Visual de PendÃªncias no Extrato (PWA v4.38):**
  - **Motor HeurÃ­stico Universal (`apps.conciliacao.services.detectar_meio_pagamento_transacao`):**
    - SanitizaÃ§Ã£o ASCII maiÃºscula sem acentos eliminando falhas por acentuaÃ§Ã£o (`dÃ©bito` vira `DEBITO`).
    - Mapeamento universal cobrindo padrÃµes Febraban/OFX de bancos como Nubank (`Compra no dÃ©bito`), Bradesco (`COMPRA CARTAO DEBITO`, `PAGTO COBRANCA`, `TARIFA REGISTRO COBRANCA`), ItaÃº (`COMPRA A DEBITO`, `RSHOP`), Banco do Brasil, Santander, Caixa, Inter, C6 e adquirentes POS.
    - **Fim dos Chutes Cegos:** RemoÃ§Ã£o do fallback cego que forÃ§ava `PIX` ou `meio_padrao`. Caso a transaÃ§Ã£o nÃ£o seja identificada com convicÃ§Ã£o absoluta, retorna `None`, atribuindo a decisÃ£o consciente ao operador.
  - **ClassificaÃ§Ã£o ContÃ¡bil DRE e ProteÃ§Ã£o da Empresa (`enriquecer_transacao_inteligencia`):**
    - Regex de palavra inteira `\b(DAS|DARF|IPTU|IPVA)\b` impedindo que a razÃ£o social `EMC SOLDAS` seja falsamente classificada como tributo fiscal.
    - IdentificaÃ§Ã£o de rendimentos bancÃ¡rios e aplicaÃ§Ãµes (`RENTAB.INVEST FACILCRED*`) classificados como `OUTRAS RECEITAS OPERACIONAIS E RENDIMENTOS`.
    - **Guias da Receita Federal Sem Chute:** TransaÃ§Ãµes genÃ©ricas da Receita Federal via Pix QR Code deixam a Categoria DRE em aberto (`None`) com alerta contextual `alerta_receita_federal = True`, sem chutar entre DAS ou GPS.
  - **Frontend PWA e Design System *Industrial Integrity* (`conciliacao-view.js` & `industrial-integrity.css`):**
    - **Cards de AtenÃ§Ã£o com Destaque Chamativo:** TransaÃ§Ãµes com lacunas pendentes (Categoria ou Meio ausentes) ganham borda de aviso industrial `#f5a623`, fundo sutil e badge no topo: `âš ï¸ ATENÃ‡ÃƒO: DEFINA O MEIO E/OU CATEGORIA DRE`.
    - **Aviso Contextual da Receita Federal:** ExibiÃ§Ã£o do badge `"âš ï¸ GUIA RECEITA FEDERAL"` solicitando a escolha contÃ¡bil exata pelo usuÃ¡rio.
    - **Reatividade em Tempo Real:** Conforme o operador seleciona os campos nos cards, o mÃ©todo `atualizarEstadoCard(idx)` reavalia o status e remove a borda de alerta e os badges instantaneamente.
    - **Bloqueio Duplo de Lacunas:** Bloqueio preventivo no frontend com contador de pendÃªncias no botÃ£o `btn-gerar-lote` e aviso Toast industrial caso haja campos em branco, alÃ©m de validaÃ§Ã£o estrita no backend (`ValidationError 400 Bad Request` em `executar_importacao_lote`).
- [x] **Tooltips Informativos nas Barras do GrÃ¡fico com SegregaÃ§Ã£o por Categoria (PWA v4.39):**
  - **Backend de AgregaÃ§Ã£o SARGable (`apps.relatorios.services.obter_graficos_receitas_despesas`):**
    - Agrupamento mensal de `LancamentoFinanceiro` por `categoria__nome` preservando compatibilidade SARGable sem `CONVERT_TZ`.
    - Cada mÃªs retorna o detalhamento de `receitas_categorias` e `despesas_categorias` ordenados por valor decrescente.
    - SerializaÃ§Ã£o tipada em `apps.relatorios.serializers` com `CategoriaItemSerializer` e `MesGraficoSerializer`.
  - **Frontend PWA e Design System Industrial Integrity (`dashboard-view.js` & `industrial-integrity.css`):**
    - Componente flutuante `.chart-tooltip` estritamente reto (0px border-radius), fundo escuro `#141414`, borda em cinza aÃ§o `#71797E` e sombra profunda `rgba(0, 0, 0, 0.85)`.
    - RÃ³tulo de cabeÃ§alho com indicador verde (receitas) ou vermelho (despesas), mÃªs/ano e valor total destacado.
    - Lista discriminada de categorias com valor monetÃ¡rio em `JetBrains Mono` e percentual de participaÃ§Ã£o no mÃªs (`X.X%`).
    - Posicionamento dinÃ¢mico relativo Ã  barra com clamps de seguranÃ§a para nÃ£o ultrapassar as extremidades do card.
    - Suporte a Desktop (hover) e Mobile/Tablet (toque/tap).
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.39` em `frontend/sw.js` e sufixos de cache-busting `?v=4.39` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 14 testes de `apps.relatorios` e 197 testes globais aprovados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_08_tooltips_grafico_categorias.md`.
- [x] **Interatividade, Rolagem e Suporte Mobile no Tooltip do GrÃ¡fico (PWA v4.40):**
  - **Acesso ao Ponteiro e Rolagem Interna no CSS (`industrial-integrity.css`):**
    - ConfiguraÃ§Ã£o de `pointer-events: auto;` em `.chart-tooltip.visible`, habilitando alcance e foco do cursor do mouse e toques de tela.
    - Isolamento de cadeia de rolagem na lista interna `.chart-tooltip-list` via `overscroll-behavior: contain;`, aceleraÃ§Ã£o inercial `-webkit-overflow-scrolling: touch;` e captura vertical `touch-action: pan-y;`, impedindo que a rolagem interna movimente a tela principal no celular.
    - InclusÃ£o do botÃ£o de fechamento tÃ©cnico `.chart-tooltip-close` `[âœ•]` (0px border-radius, tipografia mono).
  - **Ponte de TolerÃ¢ncia no Desktop e Touch no Mobile (`dashboard-view.js`):**
    - Temporizador de saÃ­da com tolerÃ¢ncia (*hover grace period*) de 250ms no `mouseleave` da barra, permitindo deslocar o mouse suavemente atÃ© o tooltip.
    - Escuta de `mouseenter` e `mouseleave` no prÃ³prio `#dashboard-chart-tooltip`, cancelando o timer e mantendo o tooltip fixo enquanto o usuÃ¡rio navega e rola a lista com a rodinha do mouse.
    - Tratamento de `e.stopPropagation()` no toque do tooltip no mobile, permitindo rolar com o dedo sem disparar o fechamento por clique fora.
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.40` em `frontend/sw.js` e sufixos de cache-busting `?v=4.40` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 14 testes de `apps.relatorios` aprovados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_09_fix_tooltip_interatividade_scroll_mobile.md`.
- [x] **Responsividade Mobile do GrÃ¡fico e Feed de Atividades do Dashboard (PWA v4.41):**
  - **Grid Inferior com 1 Coluna no Mobile (`layout.css`):**
    - CriaÃ§Ã£o da classe `.dashboard-lower-grid` que aplica `grid-template-columns: 2fr 1fr; gap: 20px;` no Desktop (>900px) e colapsa para `grid-template-columns: 1fr; gap: 16px;` no Mobile/Tablet (<=900px).
    - Empilhamento automÃ¡tico: o card do grÃ¡fico ocupa 100% da largura (alinhado com os Flip Cards de cima) e o card de "ATIVIDADES RECENTES" aparece logo abaixo dele, ocupando 100% da largura com exato alinhamento Ã  esquerda e Ã  direita.
  - **Empilhamento Vertical e Fluidez das Barras (`dashboard-view.js`):**
    - CorreÃ§Ã£o do container `#dashboard-chart-container` para `display: flex; flex-direction: column; width: 100%;`, impedindo que a legenda seja posicionada ao lado das barras.
    - CentralizaÃ§Ã£o da legenda abaixo das barras com `flex-wrap: wrap; gap: 16px; margin-top: 14px;`.
    - Ajuste de `min-width: 0;` em cada coluna de mÃªs e espaÃ§amento fluido `gap: clamp(2px, 0.8vw, 8px)`, permitindo que as 12 colunas se adaptem sem provocar estouro horizontal em qualquer smartphone.
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.41` em `frontend/sw.js` e sufixos de cache-busting `?v=4.41` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 14 testes de `apps.relatorios` aprovados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_10_responsividade_mobile_grafico_feed_dashboard.md`.
- [x] **Cadastro RÃ¡pido de Insumos, EdiÃ§Ã£o e Cancelamento de Compras com RecÃ¡lculo de Custos (PWA v4.42):**
  - **RecÃ¡lculo AutomÃ¡tico de Custos (`compras.services.recalcular_custo_item_apos_alteracao`):**
    - Ao editar itens ou cancelar uma nota de compra (`perform_destroy` com soft delete), o sistema busca a nota fiscal de compra ativa mais recente do insumo e restaura seu `ultimo_custo_compra` no catÃ¡logo.
  - **EdiÃ§Ã£o e Cancelamento na Interface (`compras-view.js`):**
    - AÃ§Ãµes de "EDITAR" e "CANCELAR" inseridas na listagem e na visualizaÃ§Ã£o detalhada da nota de compra.
    - Modal de confirmaÃ§Ã£o seguro com auditoria completa.
  - **Modal de Cadastro RÃ¡pido de Insumos (`dispararCadastroNovoInsumo`):**
    - Permite cadastrar um novo insumo diretamente na digitaÃ§Ã£o da nota de compra sem perder os dados jÃ¡ preenchidos.
  - **Versionamento PWA:** Atualizado para `v4.42`.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_11_cadastro_rapido_insumo_edicao_e_cancelamento_compras.md`.
- [x] **CorreÃ§Ã£o da Rota de DicionÃ¡rio UOM no Modal de Cadastro RÃ¡pido de Insumo (PWA v4.43):**
  - **ResoluÃ§Ã£o de Rota e Fallback Defensivo (`compras-view.js` & `config.js`):**
    - Adicionados os aliases `UOM` e `DICIONARIO_UOM` em `window.CONFIG.ENDPOINTS.CATALOGO` apontando para `/dicionario-uom/`.
    - ResoluÃ§Ã£o defensiva da URL do endpoint de unidades de medida com fallback em cascata (`CATALOGO.UOM` -> `CADASTROS.DICIONARIO_UOM` -> `'/dicionario-uom/'`) e captura de erro (`.catch(() => [])`).
    - Fallback estÃ¡tico com unidades universais (`UN`, `KG`, `M`, `M2`, `BARRA`) caso a API esteja temporariamente inacessÃ­vel, impedindo que o modal trave.
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.43` em `frontend/sw.js` e sufixos de cache-busting `?v=4.43` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 28 testes de `apps.compras` e 15 testes de `apps.catalogo` aprovados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-03_12_correcao_endpoint_dicionario_uom_cadastro_insumo.md`.
- [x] **CorreÃ§Ã£o da Chamada de SanitizaÃ§Ã£o no Cadastro RÃ¡pido de Insumos (PWA v4.44):**
  - **Uso da FunÃ§Ã£o CanÃ´nica do Frontend (`compras-view.js`):**
    - CorreÃ§Ã£o do mÃ©todo chamado na linha 741 para utilizar a funÃ§Ã£o oficial padrÃ£o de todo o frontend: `window.EMCUtils.sanitizarTextoEmTempoReal(nome)`.
    - PreservaÃ§Ã£o integral e estabilidade do mÃ³dulo `utils.js` sem alteraÃ§Ãµes desnecessÃ¡rias.
  - **Versionamento PWA:** SincronizaÃ§Ã£o do cache para `emc-soldas-v4.44` em `frontend/sw.js` e sufixos de cache-busting `?v=4.44` em `frontend/index.html`.
  - **HomologaÃ§Ã£o:** 28 testes de `apps.compras` aprovados com 100% de sucesso.
- [x] **Correção da Adição Sequencial de Insumos na Ficha Técnica BOM (PWA v4.49):**
  - **Single Modal Lifecycle & Reatividade In-Modal (`catalogo-view.js`):**
    - Eliminação do empilhamento recursivo de modais (`openModal`) que gerava sobreposição de overlays no DOM e deixava os botões de ação sem listeners de clique.
    - Implementação da rotina reativa `_atualizarFichaModal`: atualização dinâmica de linhas na tabela `#ficha-tecnica-tbody`, recálculo em tempo real de materiais, mão de obra e preço apurado, limpeza de campos de entrada e sincronização da listagem de catálogo em background.
    - Atualização dinâmica da combobox de insumos (`updateOptions`) filtrando itens já presentes na receita.
    - Suporte à tecla `Enter` no input de quantidade e debounce no botão `+ ADICIONAR`.
  - **Versionamento PWA:** Sincronização do cache para `emc-soldas-v4.49` em `frontend/sw.js` e query strings `?v=4.49` em `frontend/index.html`.
  - **Homologação:** 200 testes automatizados de backend executados e aprovados com 100% de sucesso.
  - **Registro de Planejamento:** Arquivado formalmente em `Planejamento/2026-10-04_01_correcao_adicao_multiplos_insumos_ficha_tecnica_bom.md`.







### Mapeamento de Funcionalidades do Backend com Views/Telas Pendentes no Frontend
Abaixo estÃ£o registradas as entidades que jÃ¡ possuem modelos ORM, validaÃ§Ãµes e rotas de API REST prontas e blindadas no backend, mas que ainda nÃ£o contam com tela/painel de gestÃ£o visual dedicado no frontend (aparecendo atualmente apenas como comboboxes ou subitens):
- [x] **GestÃ£o de Contas BancÃ¡rias Corporativas (`apps/financeiro` - `/api/contas-bancarias/`):**
  - *SituaÃ§Ã£o:* **ConcluÃ­da**. Implementada aba dedicada "CONTAS BANCÃRIAS" no mÃ³dulo Tesouraria & Caixa (`financeiro-view.js`), com cards de KPI (Saldo Total, Limite Cheque Especial, DisponÃ­vel Real), listagem de contas, modal de cadastro e ediÃ§Ã£o de saldos/limites, e inativaÃ§Ã£o por soft delete.
- [x] **GestÃ£o de Categorias Financeiras DRE na AdministraÃ§Ã£o (`apps/financeiro` - `/api/categorias-financeiras/`):**
  - *SituaÃ§Ã£o:* **ConcluÃ­da**. Implementada aba dedicada "CATEGORIAS FINANCEIRAS (DRE)" na Central Administrativa (`administracao-view.js`) com suporte a tipos `RECEITA`, `DESPESA`, `AMBOS` (cadastral) e `TRANSFERENCIA`, status Ativo/Inativo, seleÃ§Ã£o de categoria pai, modal com aviso de governanÃ§a contÃ¡bil, e exclusÃ£o protegida com bloqueio se houver lanÃ§amentos ou subcategorias ativas.
  - *Extrato Real & Tesouraria:* CorreÃ§Ã£o do modal de lanÃ§amento avulso no Extrato Real (`status_pagamento='PAGO'`, conta obrigatÃ³ria e atualizaÃ§Ã£o imediata de saldo), resoluÃ§Ã£o da ingestÃ£o de chaves `_id` no DRF, filtro dinÃ¢mico de categorias em tempo real de acordo com a operaÃ§Ã£o (`SAIDA` -> despesa/ambos; `ENTRADA` -> receita/ambos), coluna de categoria na tabela, busca por categoria e modal de reclassificaÃ§Ã£o/ediÃ§Ã£o de lanÃ§amentos.
  - *PermissÃ£o:* AcessÃ­vel por administradores ou colaboradores com permissÃ£o `cadastros_financeiros` (leitura liberada para tesouraria).
- [ ] **GestÃ£o de CartÃµes de CrÃ©dito Corporativos & Fechamento de Faturas (`apps/financeiro` - `/api/cartoes/` e `/api/faturas-cartao/`):**
  - *SituaÃ§Ã£o atual:* Tabelas 19 e 20 do FSD. CartÃµes e faturas mensais modelados no backend, mas geridos hoje apenas via modal auxiliar no lanÃ§amento de despesas.
  - *Local sugerido:* Aba dedicada na Tesouraria.
- [ ] **Editor Dedicado de Ficha TÃ©cnica / Estrutura de Insumos BOM (`apps/catalogo` - `/api/fichas-tecnicas/`):**
  - *SituaÃ§Ã£o atual:* O cadastro de produtos permite definir itens no modal, mas uma visualizaÃ§Ã£o em Ã¡rvore de composiÃ§Ã£o detalhada e ajuste em lote da receita ainda pode ser expandida.

### Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de ConclusÃ£o e Deploy
- [ ] Executar suÃ­te de testes automatizados unitÃ¡rios e de integraÃ§Ã£o (`python manage.py test`).
- [ ] Executar Pentest MandatÃ³rio de ConclusÃ£o (6 testes: RBAC/IDOR, Brute-force, SQLi/XSS, Uploads, SessÃ£o HttpOnly, Criptografia/Tracebacks).
- [ ] **RemoÃ§Ã£o MandatÃ³ria de ConfiguraÃ§Ãµes TemporÃ¡rias de TÃºnel Externo:** Auditar e remover a liberaÃ§Ã£o de CSRF para o wildcard `https://*.trycloudflare.com` em `backend/config/settings.py` antes do deploy definitivo em produÃ§Ã£o.
- [ ] Disponibilizar script gerador de chaves criptogrÃ¡ficas de 64 caracteres (`tools/generate_keys.py`).
- [ ] Elaborar guia de implantaÃ§Ã£o em produÃ§Ã£o Cloud PaaS.

---

## PrÃ³ximo Passo Recomendado

Acompanhar e apoiar as verificaÃ§Ãµes e validaÃ§Ãµes do usuÃ¡rio no Frontend PWA. Quando o usuÃ¡rio concluir as verificaÃ§Ãµes visuais e operacionais e solicitar o inÃ­cio da Fase 15, executaremos do zero e formalmente a **Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de ConclusÃ£o e Deploy**.





