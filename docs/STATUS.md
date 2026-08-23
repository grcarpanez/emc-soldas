# STATUS DO PROJETO - EMC SOLDAS

Este documento é um arquivo vivo que registra o estado atual do desenvolvimento, o progresso por fase, o checklist de tarefas e o próximo passo recomendado.

**Última Atualização:** 2026-08-23 (Conclusão da Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real, Cartões Corporativos e Estornos)  
**Fase Atual:** Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV) (Pronta para início)  
**Próxima Fase:** Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV)  

---

## Visão Geral do Progresso

| Fase | Título | Status | Conclusão |
| :--- | :--- | :--- | :--- |
| **Fase 0** | Mapeamento Integral dos Campos do Banco de Dados e Matriz de Máscaras/Sanitização | **Concluída** | 100% |
| **Fase 1** | Infraestrutura, Base do Projeto e Governança de Configuração | **Concluída** | 100% |
| **Fase 2** | Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria | **Concluída** | 100% |
| **Fase 3** | Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC) | **Concluída** | 100% |
| **Fase 3.5** | Adequação de Sanitização Universal (Uppercase/Sem Acentos) e Utilitários de Máscaras | **Concluída** | 100% |
| **Fase 4** | Cadastros Estruturais e Dicionários Centrais | **Concluída** | 100% |
| **Fase 5** | Módulo de Clientes, Fornecedores e Equipamentos | **Concluída** | 100% |
| **Fase 6** | Catálogo Base, Materiais, Insumos e Produtos (Motor BOM) | **Concluída** | 100% |
| **Fase 7** | Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos) | **Concluída** | 100% |
| **Fase 8** | Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF) | **Concluída** | 100% |
| **Fase 9** | Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação) | **Concluída** | 100% |
| **Fase 10** | Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos | **Concluída** | 100% |
| **Fase 11** | Conciliação Bancária Inteligente Split-Screen (OFX/CSV) | Pendente | 0% |
| **Fase 12** | Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete) | Pendente | 0% |
| **Fase 13** | Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV) | Pendente | 0% |
| **Fase 14** | Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*) | Pendente | 0% |
| **Fase 15** | Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy | Pendente | 0% |

---

## Detalhamento do Checklist por Fase

### Fase 0 - Mapeamento Integral dos Campos do Banco de Dados e Matriz de Máscaras/Sanitização
- [x] Mapear todas as 29 entidades e campos de dados do sistema no `docs/PLANO.md`.
- [x] Definir regra de sanitização para 100% dos campos de texto (Maiúsculas sem Acento - ASCII Puro).
- [x] Definir especificações de máscaras: Máscara ATM de Moeda (`R$ 0,00`), CPF/CNPJ Híbrido, Telefone Híbrido, CEP, Placas e Horas.

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

### Fase 3.5 - Adequação de Sanitização Universal (Uppercase/Sem Acentos) e Utilitários de Máscaras
- [x] Criar função utilitária de sanitização universal `sanitizar_texto_maiusculo` no backend (`backend/core/utils.py`).
- [x] Atualizar dados padrão do seeder inicial (`backend/core/management/commands/seed_initial_data.py`) convertendo 100% dos textos para maiúsculas sem acento e enums em UPPERCASE.
- [x] Criar biblioteca de utilitários no frontend (`frontend/assets/js/utils.js`) com conversão em tempo real (`input`/`paste`), Máscara ATM de Moeda (`R$ 0,00`), CPF/CNPJ, Telefone, CEP, Placas e Linha Digitável.
- [x] Criar e validar testes automatizados de sanitização de strings no backend com 100% de sucesso.

### Fase 4 - Cadastros Estruturais e Dicionários Centrais
- [x] Implementar CRUD de `DicionarioUom` (`/api/dicionario-uom/`) com sanitização e proteção contra deleção de UOMs em uso.
- [x] Implementar CRUD de `DicionarioAtributo` (`/api/dicionario-atributos/`) com sanitização e proteção contra deleção de atributos em uso.
- [x] Implementar CRUD hierárquico de `CategoriaFinanceira` (`/api/categorias-financeiras/`) com validação anti-ciclos e bloqueio de exclusão com subcategorias ativas.
- [x] Implementar CRUD de `ContaBancaria` (`/api/contas-bancarias/`) com validação de limite de cheque especial e bloqueio com lançamentos ativos.
- [x] Implementar CRUD de `MeioPagamento` (`/api/meios-pagamento/`) com toggle `permite_taxa_maquininha` e validação de regras ativas.
- [x] Implementar CRUD de `RegraPagamento` (`/api/regras-pagamento/`) com suporte a à vista, a prazo e parcelado, com validações de prazos, intervalos e descontos sugeridos.
- [x] Proteger todos os endpoints via RBAC dinâmico (`HasDicionarioUomAccess` e `HasCadastrosFinanceirosAccess`).
- [x] Criar e executar suíte de testes automatizados com 100% de sucesso (33 testes).

### Fase 5 - Módulo de Clientes, Fornecedores e Equipamentos
- [x] Criar endpoint proxy para consulta de CNPJ pública (BrasilAPI/ReceitaWS) com fallback gracioso (`/api/utilitarios/consulta-cnpj/<cnpj>/`).
- [x] Implementar validação matemática de CPF (módulo 11), CNPJ e checagem antecipada de duplicidade no `onBlur` (`/api/utilitarios/verificar-documento/`).
- [x] Implementar CRUD de `ClienteFornecedor` com suporte a PF/PJ, cadastro rápido ágil (apenas Nome + Telefone), dossiê comercial e soft delete.
- [x] Implementar CRUD de `Equipamento` com suporte a placas antigas/Mercosul, identificação técnica e soft delete.
- [x] Implementar CRUD de `ClienteEquipamento` com transferência segura (desativação do vínculo anterior e ativação do novo) preservando o histórico para não quebrar orçamentos passados.
- [x] Implementar gestão e download seguro de anexos de clientes (`AnexoGeralCliente`) com validação de extensões permitidas e cabeçalhos forçados.
- [x] Criar e executar suíte completa de testes automatizados da Fase 5 com 100% de sucesso (46 testes no total acumulado).

### Fase 6 - Catálogo Base, Materiais, Insumos e Produtos (Motor BOM)
- [x] Implementar cadastro de Itens com atributos técnicos dinâmicos (`ItemAtributoValor`), fator de conversão de unidades e cálculo de custo fracionado de consumo (`/api/itens/`).
- [x] Implementar cadastro de Produtos com tempo estimado de mão de obra (`tempo_estimado_execucao`) e sub-grid de Ficha Técnica BOM (`/api/produtos/`).
- [x] Implementar cálculo em tempo real do `Preço de Custo Apurado` (Custo Total Materiais + Custo Mão de Obra via taxa horária de `ConfiguracaoGlobal`).
- [x] Implementar travas de integridade referencial para impedir soft delete de itens em uso na Ficha Técnica de produtos ativos.
- [x] Implementar endpoints auxiliares: `/api/itens/{id}/onde-usado/`, `/api/produtos/{id}/custo-detalhado/` e `/api/produtos/{id}/atualizar-ficha-tecnica/`.
- [x] Proteger todos os endpoints do Catálogo via RBAC com o toggle `gestao_catalogo` (`HasCatalogoAccess`).
- [x] Criar e executar suíte de testes automatizados com 100% de sucesso (50 testes no total acumulado do projeto).

### Fase 7 - Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos)
- [x] Implementar registro de Notas Fiscais de Entrada (`DocumentoFiscalCompra` e `NotaCompraItem` via `/api/documentos-fiscais-compra/` e `/api/nota-compra-itens/`).
- [x] Implementar rotina de retroalimentação automática de custos no Catálogo de Itens (`ultimo_custo_compra` e `data_ultima_compra`).
- [x] Configurar upload seguro de XML/PDF com validação de MIME-Type profundo, magic numbers e NoExec (`/api/documentos-fiscais-compra/{id}/anexar-arquivo/` e `download-anexo/`).
- [x] Implementar consulta de histórico de compras e preços por fornecedor (`/api/documentos-fiscais-compra/historico-precos/`).
- [x] Proteger todos os endpoints do módulo via RBAC dinâmico com o toggle `acesso_compras` (`HasComprasAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (74 testes no total acumulado do projeto).

### Fase 8 - Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF)
- [x] Implementar criação ágil de Orçamentos com 3 tipos de itens (Produtos, Itens e Lançamentos Livres).
- [x] Implementar persistência imutável de Snapshots de custos e valores de venda.
- [x] Implementar máquina de estados duplo (Status Operacional vs Status Financeiro).
- [x] Implementar renovação de orçamentos com alerta visual de inflação de insumos/mão de obra e opção de re-precificação.
- [x] Implementar cancelamento justificado obrigatório (mínimo 10 caracteres) com gravação de log e auditoria.
- [x] Implementar detecção preventiva de inadimplência em tempo real com consulta a títulos vencidos.
- [x] Implementar serviço de geração de PDF comercial via ReportLab (*Industrial Integrity*) com desconto oculto quando zerado.
- [x] Gerar arquivo PDF de exemplo fictício (`backend/media/exemplos/orcamento_exemplo.pdf`) para aprovação visual do usuário.
- [x] Proteger todos os endpoints do módulo via RBAC dinâmico com o toggle `acesso_comercial` (`HasComercialAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (87 testes no total acumulado do projeto).

### Fase 9 - Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação)
- [x] Implementar listagem da Conta Corrente de orçamentos 'A Faturar' (`/api/faturas/conta-corrente/`).
- [x] Implementar fluxo de Pré-Fatura (Rascunho) com simulação de opções de pagamento (`FaturaPropostaPagamento`) e PDF Espelho.
- [x] Implementar conversão em Fatura Final (`FATURADA` via `/api/faturas/{id}/faturar/`), transição em cascata de orçamentos e geração de parcelas no Contas a Receber.
- [x] Implementar quitação total (100% de baixa transitando fatura e orçamentos para `PAGA`/`PAGO` via `/api/faturas/{id}/receber/`).
- [x] Implementar cancelamento de faturas com justificativa obrigatória e desvinculação em cascata (reversão para `A FATURAR` e anulação de parcelas a vencer via `/api/faturas/{id}/cancelar/`).
- [x] Implementar quitação em Cortesia (100% de desconto) sem afetar caixa real (`/api/faturas/{id}/cortesia/`).
- [x] Implementar gerador de PDF profissional para Faturas e Pré-Faturas no padrão *Industrial Integrity* (`/api/faturas/{id}/gerar-pdf/`).
- [x] Proteger todos os endpoints do módulo via RBAC dinâmico com o toggle `acesso_comercial` (`HasComercialAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (88 testes no total acumulado do projeto).

### Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos
- [x] Implementar Contas a Pagar e Contas a Receber (Regime de Competência) sem impactar saldo imediato.
- [x] Implementar Extrato de Caixa Real (Regime de Caixa) com impacto imediato no saldo da conta bancária.
- [x] Implementar Modal Universal de Liquidação com cálculo automático de Taxa de Maquininha e Retenção de ISS na fonte (Receita Bruta - Deduções = Saldo Líquido Real).
- [x] Implementar Bloqueio por Limite de Cheque Especial em saídas bancárias.
- [x] Implementar Transferências Inter-Contas atômicas e neutras para o DRE.
- [x] Implementar gestão de Cartões Corporativos com acumulação de despesas em fatura aberta, alteração de fechamento, remanejamento entre faturas e rollover de saldo devedor.
- [x] Implementar fluxo de Estorno de títulos pagos com reversão de saldo bancário, cancelamento de taxas atreladas e gravação perpétua em `LogEstorno`.
- [x] Proteger todos os endpoints do módulo via RBAC dinâmico com o toggle `acesso_tesouraria` (`HasTesourariaAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (108 testes no total acumulado do projeto).

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

Iniciar a **Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV)**, desenvolvendo a camada de parsing de extratos bancários em formato OFX e CSV (`/api/conciliacao/upload-extrato/`), o algoritmo de correspondência (Match Automático 1:1 e Match Múltiplo 1:N), endpoint de `Lançamento Rápido no Ato` para tarifas/rendimentos com conciliação imediata, e gravação mandatória de auditoria (`is_conciliado = True`, `data_conciliacao` e `conciliado_por_id`), protegido pelo toggle `acesso_tesouraria`.

