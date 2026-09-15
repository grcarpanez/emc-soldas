# STATUS DO PROJETO - EMC SOLDAS

Este documento é um arquivo vivo que registra o estado atual do desenvolvimento, o progresso por fase, o checklist de tarefas e o próximo passo recomendado.

**Última Atualização:** 2026-09-14 (Blindagem do Service Worker para Uploads e Operações de Mutação no Celular, PWA v4.31)  
**Fase Atual:** Fase 14.5 - Refinamentos de UX, Mobile e Conectividade Operacional (Modais Empilhados, Comboboxes Pesquisáveis, CEP Automático, Máscaras Flexíveis, Conciliação Mobile, Bypass SW e Governança)  
**Próxima Fase:** Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy (Pendente - com checklist de rollback do túnel registrado)  

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
| **Fase 11** | Conciliação Bancária Inteligente Split-Screen (OFX/CSV) | **Concluída** | 100% |
| **Fase 12** | Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete) | **Concluída** | 100% |
| **Fase 13** | Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV) | **Concluída** | 100% |
| **Fase 14** | Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*) | **Concluída** | 100% |
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
- [x] Criar biblioteca de utilitários no frontend (`frontend/assets/js/utils.js`) com conversão em tempo real (`input`/`paste`), Máscara ATM de Moeda (`R$ 0,00`), CPF/CNPJ, Telefone, CEP, Placas, Chave NFe e Linha Digitável.
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
- [x] Criar endpoint proxy para consulta de CEP pública com fallback gracioso BrasilAPI / ViaCEP (`/api/utilitarios/consulta-cep/<cep>/`) e preenchimento automático no evento `blur`/`exit`.
- [x] Implementar validação matemática de CPF (módulo 11), CNPJ e checagem antecipada de duplicidade no `onBlur` (`/api/utilitarios/verificar-documento/`).
- [x] Implementar CRUD de `ClienteFornecedor` com suporte a PF/PJ, cadastro rápido ágil (apenas Nome + Telefone), dossiê comercial e soft delete.
- [x] Implementar CRUD de `Equipamento` com suporte a placas antigas/Mercosul, identificação técnica e soft delete.
- [x] Implementar CRUD de `ClienteEquipamento` com transferência segura (desativação do vínculo anterior e ativação do novo) preservando o histórico para não quebrar orçamentos passados.
- [x] Implementar gestão e download seguro de anexos de clientes (`AnexoGeralCliente`) com validação de extensões permitidas e cabeçalhos forçados.
- [x] Implementar gestão de contatos flexíveis (estilo agenda de smartphone) com suporte a múltiplos telefones e e-mails separados por ponto-e-vírgula (;) e validação individual RFC.
- [x] Criar e executar suíte completa de testes automatizados da Fase 5 com 100% de sucesso (26 testes dedicados em cadastros, 184 testes no acumulado do sistema).

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
- [x] Implementar serviço de upload e parsing seguro de extratos OFX e CSV.
- [x] Implementar algoritmo de Match Automático 1:1 e Match Múltiplo (1:N).
- [x] Implementar endpoint de `Lançamento Rápido no Ato` para tarifas bancárias/rendimentos.
- [x] Implementar confirmação de conciliação com gravação de `is_conciliado = True`, data e operador.
- [x] Implementar dados analíticos para Relatório de Divergências de Conciliação.
- [x] Proteger todos os endpoints do módulo via RBAC dinâmico com o toggle `acesso_tesouraria` (`HasTesourariaAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (118 testes no total acumulado do projeto).

### Fase 12 - Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete)
- [x] Implementar Parâmetros Globais com criptografia simétrica AES-256 da senha SMTP, presets rápidos e teste de disparo em tempo real.
- [x] Implementar blindagem de não-retroatividade para taxa horária e validade de orçamentos sobre orçamentos passados.
- [x] Implementar rotina de expurgo de logs via manifesto TTL (`ControleArquivoLog`), com envio de backup por e-mail dos arquivos expirados antes da exclusão física.
- [x] Implementar comando CLI agendável `python manage.py expurgar_logs --enviar-backup`.
- [x] Implementar Log Viewer seguro do servidor para visualização estruturada de falhas pelo Administrador, com blindagem rigorosa contra Path Traversal.
- [x] Implementar Gestão de Equipe com os 10 toggles dinâmicos por usuário, onboarding por e-mail e desbloqueio manual de contas travadas por Anti-Bruteforce.
- [x] Implementar Painel de Lixeira e Restauração Lógica mapeando 16 entidades com isolamento de visão (Lixeira Global para Admin e Minha Lixeira para Operador).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (133 testes no total acumulado do projeto).

### Fase 13 - Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV)
- [x] Implementar agregador do Dashboard Principal com os 5 Flip Cards interativos (Operação, Faturamento, Receita, Caixa e Alertas) e filtros temporais (`/api/dashboard/flip-cards/`).
- [x] Implementar evolução mensal de Receitas vs Despesas (`/api/dashboard/graficos/`) e Feed de Atividades Recentes (`/api/dashboard/feed/`).
- [x] Implementar Relatório de Inadimplência com auditoria de faturas vencidas, cálculo de dias de atraso e contato de clientes (`/api/relatorios/inadimplencia/`).
- [x] Implementar Dossiê do Cliente com segregação de produtos (materiais) vs serviços (reformas), funil de orçamentos e índice de pontualidade (`/api/relatorios/dossie-cliente/<id>/`).
- [x] Implementar Curva ABC de Clientes (`/api/relatorios/curva-abc-clientes/`) e Curva ABC de Consumo de Itens (`/api/relatorios/curva-abc-itens/`) com matriz 80/15/5%.
- [x] Implementar DRE Simplificado nos regimes de competência e caixa com apuração de receitas, deduções, custos variáveis e despesas operacionais (`/api/relatorios/dre/`).
- [x] Implementar Relatório de Divergências de Conciliação Bancária em duas abas analíticas (`/api/relatorios/divergencias-conciliacao/`).
- [x] Implementar geradores de PDF via ReportLab no padrão *Industrial Integrity* e geradores de CSV com encoding UTF-8 com BOM para todos os relatórios estratégicos.
- [x] Aplicar Rate Limiting restritivo de 5 requisições/minuto (`throttle_scope = 'heavy_reports'`) nos endpoints de exportação de relatórios pesados.
- [x] Proteger todos os endpoints via RBAC dinâmico com o toggle `visao_relatorios` (`HasRelatoriosAccess`).
- [x] Criar e executar suíte completa de testes automatizados com 100% de sucesso (146 testes no total acumulado do projeto).

### Fase 14 - Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*)
- [x] Implementar roteador client-side SPA (`router.js`), Service Worker (`sw.js`) e cache de assets estáticos offline.
- [x] Implementar Telas de Acesso (`auth-view.js`: Login, PIN de 6 dígitos, Recuperação de Senha e Ativação de Conta).
- [x] Implementar Dashboard Principal (`dashboard-view.js`: 5 Flip Cards 3D com métricas em tempo real, filtros temporais e feed de eventos).
- [x] Implementar telas operacionais de Cadastros (`cadastros-view.js`: Clientes com consulta de CNPJ e validação CPF Módulo 11, Fornecedores, Equipamentos e Dicionários UOM/Atributos).
- [x] Implementar Catálogo de Insumos e Motor BOM (`catalogo-view.js`: Itens, conversão de unidades, Produtos e Ficha Técnica BOM calculando Custo Apurado em tempo real).
- [x] Implementar Módulo de Compras (`compras-view.js`: Notas de Entrada com máscara de chave NFe 44 dígitos, itens e histórico).
- [x] Implementar Orçamentos Comerciais (`orcamentos-view.js`: Elaboração ágil com 3 tipos de itens, snapshots imutáveis, renovação com alerta de inflação, cancelamento justificado e geração de PDF).
- [x] Implementar Faturamento Agregado (`faturamento-view.js`: Conta Corrente, Pré-Faturas, Faturas Finais, Baixas com taxa de maquininha, Cortesias 100% e cancelamento em cascata).
- [x] Implementar Tesouraria & Caixa Real (`financeiro-view.js`: Contas a Pagar/Receber por competência, Extrato de Caixa Real, Cartões Corporativos com rollover e Estorno com justificativa perpétua).
- [x] Implementar Conciliação Bancária Inteligente (`conciliacao-view.js`: Layout Split-Screen de 2 colunas, importação OFX/CSV, Match 1:1, Match Múltiplo e Lançamento Rápido no Ato).
- [x] Implementar Central do Administrador (`administracao-view.js`: Parâmetros Globais, teste SMTP em tempo real, Gestão de Equipe com 10 toggles dinâmicos e desbloqueio anti-bruteforce, Log Viewer com expurgo TTL e Lixeira com restauração lógica em 1 clique).
- [x] Implementar Central Analítica (`relatorios-view.js`: Inadimplência, Dossiê do Cliente, Curvas ABC de Clientes/Itens, DRE Simplificado e Divergências de Conciliação com exportação PDF/CSV).
- [x] Integrar 100% dos componentes e formulários ao Design System *Industrial Integrity* (0px border-radius, tipografia técnica, paleta Dark Iron, Steel Gray e Rust Orange, máscaras e toasts).

### Fase 14.5 - Refinamentos de UX, Mobile e Conectividade Operacional (Concluída)
- [x] **Comboboxes Pesquisáveis com Autocomplete:** Implementação do componente universal `window.EMCUtils.initSearchableSelect` no padrão *Industrial Integrity* (0px border-radius, tema dark, busca instantânea e navegação por teclado).
- [x] **Segregação de Frota e Clientes:** Exclusão estrita de fornecedores puros (`tipo === 'FORNECEDOR'`) da seleção de proprietários de veículos e da exibição do botão `FROTA` na tabela.
- [x] **Filtragem Dinâmica no Orçamento:** Combobox de equipamentos re-filtrada em tempo real ao selecionar o cliente no modal de orçamento.
- [x] **Modal de Histórico Cronológico de Vínculos:** Endpoint `@action(detail=True, url_path='historico-proprietarios')` e modal frontend exibindo histórico de titularidade com precisão de timestamp (`DD/MM/AAAA às HH:MM:SS`), status atual/anterior e telefone de contato.
- [x] **Vinculação Inteligente de Frota:** Modal de frota com busca de equipamentos existentes, autopreenchimento de campos e confirmação assistida de transferência de titularidade entre clientes.
- [x] **Escala Compacta e Alta Densidade Mobile:** Calibração CSS (`industrial-integrity.css` e `layout.css`) com tipografia compacta (`13.5px` / `12.5px`), botões proporcionais (`min-height: 32px`), grids de formulários colapsando em coluna única e modais fluidos (`96vw`).
- [x] **Servidor Unificado no Django:** Roteamento de assets estáticos e SPA no `backend/config/urls.py`, permitindo execução unificada via `python backend/manage.py runserver 0.0.0.0:8000` (eliminando dependência do Live Server na porta 5500).
- [x] **Conectividade Wi-Fi e Firewall:** Configuração de `ALLOWED_HOSTS = ['*']` e `CSRF_TRUSTED_ORIGINS` para IPs de rede local (`192.168.2.104:8000`) e documentação da regra do Windows Firewall (`netsh advfirewall firewall add rule name="EMC_Soldas_8000" dir=in action=allow protocol=TCP localport=8000`).
- [x] **Assets PWA e Favicon:** Geração dos arquivos físicos `favicon.ico`, `icon-192.png` e `icon-512.png` eliminando requisições 404.
- [x] **Dinamização Reativa CPF/CNPJ no Modal de Cadastro:** Inicialização do modal como Pessoa Física ("NOME COMPLETO *" e campo "NOME FANTASIA" oculto com grid de 1 coluna), transição em tempo real para Pessoa Jurídica ("RAZÃO SOCIAL *", reexibição de "NOME FANTASIA" e grid de 2 colunas) ao ultrapassar 11 dígitos, e reversão completa ao apagar dígitos.
- [x] **Exclusão e Desativação (Soft Delete) com Blindagem de Integridade Histórica:** Implementação de botões `EXCLUIR` e modais industriais de confirmação para Clientes, Fornecedores e Equipamentos (`cadastros-view.js`), configuração de `base_manager_name = 'all_objects'` no núcleo ORM (`core/models.py`), inativação de vínculos ativos de frota sem quebrar orçamentos, faturas, títulos, relatórios analíticos ou geração de PDFs de registros passados, com segregação de inativos exclusivamente em novos lançamentos e restauração ágil via Lixeira.
- [x] **Aprimoramento do Painel de Lixeira & Restauração:** Correção no parser de resposta de itens da Lixeira, suporte à opção de não filtrar com exibição unificada de todo o histórico cronológico de exclusões por padrão (`TODAS AS ENTIDADES`), adição de Equipamentos e todas as 16 entidades na combobox, coluna de tipo/entidade na tabela e campo de busca textual em tempo real (150 testes automatizados aprovados com 100% de sucesso).
- [x] **Log Viewer do Servidor, Contagem Real de Eventos e Auditoria Universal de Soft Delete:** Implementação do handler `DailyDateFileHandler` em `backend/core/logging_handlers.py` gravando diretamente nos arquivos imutáveis `app-YYYY-MM-DD.log` (eliminando bloqueios de arquivo `PermissionError WinError 32` no Windows), adição dos campos computados `total_eventos`, `quantidade_linhas` e `data_log` no `ControleArquivoLogSerializer`, correção de rotas (`/controle-arquivos-log/visualizar/`), modal do Log Viewer enriquecido com destaque semântico de severidade (*Industrial Integrity* com tags `[AUDIT]`, `ERROR`, `WARNING`, `INFO`), filtros em tempo real, sincronização manual de manifesto e rastreamento perpétuo de exclusões e restaurações em log físico (150 testes automatizados aprovados com 100% de sucesso).
- [x] **Gestão de Equipe (RBAC), Permissões Dinâmicas, Promoção/Rebaixamento, Ativação/Desativação e Auditoria Universal:**
  - Correção dos endpoints REST de permissões (`/api/usuarios/{id}/permissoes/`) com suporte completo aos métodos `GET`, `PATCH` e `PUT`.
  - Implementação de ações semânticas de ativação/desativação (`/api/usuarios/{id}/alternar-status/`, `desativar/`, `ativar/`) com **blindagem de segurança contra auto-desativação** (`request.user.id == usuario.id`) e **proteção de último Administrador ativo** do sistema.
  - Implementação de promoção e rebaixamento de colaboradores (`/api/usuarios/{id}/alterar-perfil/`) com atribuição plena de 10 toggles para Admins e proteção contra rebaixamento do único Administrador ativo.
  - Sobrescrita com resposta protegida para auto-exclusão lógica no `UsuarioViewSet`.
  - Registro perpétuo em log físico imutável com marcadores de auditoria `[AUDIT]` para promoções, rebaixamentos, ativações, desativações, diffs de permissões RBAC, desbloqueios e convites.
  - Interface do frontend PWA atualizada na aba Gestão de Equipe com modal unificado de perfil e matriz de 10 toggles dinâmicos, botões diretos de ativação/desativação e tag de auto-identificação `[VOCÊ]` com botão desabilitado para o usuário da sessão (157 testes automatizados aprovados com 100% de sucesso).
  - **Sincronização em Tempo Real, Parser Estruturado e Segregação Estrita no Log Viewer:** Auto-sincronização do manifesto no método `list` de `ControleArquivoLogViewSet` garantindo exibição instantânea do arquivo do dia atual no topo da tabela, implementação de parser semântico estruturado em `backend/apps/administracao/services.py` com classificação primária definitiva (`AUDIT`, `SEGURANCA`, `ERROR`, `WARNING`, `HTTP`, `INFO`, `DEBUG`), eliminação de falsos positivos em badges causados por termos em query strings de URLs, e enriquecimento do modal com seletor completo de 7 categorias e badges semânticos (*Industrial Integrity*) precisos (157 testes automatizados aprovados com 100% de sucesso).
  - **Blindagem e Isolamento Estrito de Logs em Testes Unitários (Test Isolation):** Refatoração da suíte de testes de administração para utilizar arquivos isolados com data fictícia (`app-2099-12-31.log`) e limpeza em bloco `try/finally`, eliminando qualquer risco de sobrescrita ou truncamento do arquivo real de log do dia atual (`app-YYYY-MM-DD.log`) durante execuções de testes.
- [x] **Validação Estrita e Máscara Universal de Placas (Padrões Antigo e Mercosul com Formato ###-####):**
  - Implementação de máscara universal automática com hífen `###-####` tanto para o padrão antigo (`AAA-0000`) quanto Mercosul (`AAA-0A00`): o hífen é inserido **100% automaticamente** após a 3ª letra sem exigir que o operador digite `-`.
  - Backend: Função utilitária `validar_placa(valor)` em `backend/core/utils.py` com sanitização e regex rigorosa (`^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`), validação defensiva em `apps/cadastros/serializers.py` (`validate_placa`) normalizando e gravando sempre com hífen `###-####`, retornando `400 Bad Request` semântico para entradas inválidas, e testes unitários automatizados cobrindo placas válidas e inválidas (16 testes de cadastros e 157 testes globais aprovados com 100% de sucesso).
  - Frontend: Função utilitária `formatarPlacaVeiculo` com restrição dinâmica caractere a caractere no evento `input` (dígitos 0-2: letras; dígito 3: número; dígito 4: letra ou número; dígitos 5-6: números; máximo de 8 caracteres formatados com `-`), validação em tempo real e bloqueio de envio com Toast industrial nos modais de equipamento e frota em `cadastros-view.js`.
- [x] **Instituição da Governança de Planejamento Mandatória e Histórico Perpétuo (`Planejamento/`):**
  - Atualização do `AGENTS.md` com Regra de Ouro inegociável: proibição terminante de qualquer alteração de código ou configuração sem a prévia elaboração de *Implementation Plan* estruturado e aprovação formal explícita (`Proceed`) do usuário.
  - Criação da pasta `Planejamento/` na raiz do sistema para versionamento perpétuo de todos os planos de implementação, contendo contexto, decisões arquiteturais, checklist de arquivos, testes e transcrição da aprovação do usuário (`Planejamento/YYYY-MM-DD_NN_nome_da_tarefa.md`).
- [x] **Governança Perpétua de Cache PWA e Versionamento Sincronizado de Assets (`v2.8`, `v2.9` e `v3.0`):**
  - Instituição da Regra Mandatória 12 no `AGENTS.md` e registro de lição técnica em `docs/ERROS.md`: toda e qualquer alteração em JS/CSS obriga a sincronização do `CACHE_NAME` no `frontend/sw.js` e a atualização dos sufixos de query string `?v=X.Y` em todas as tags `<script>` e `<link>` do `frontend/index.html`.
  - Execução imediata da versão `v2.8`, `v2.9` e `v3.0` em `sw.js` e `index.html`, eliminando retenção de código desatualizado por caches stale no navegador do usuário.
- [x] **Refinamento de UX no Filtro de Clientes & Fornecedores (v2.9):**
  - Ajuste na combobox de tipo: renomeação de `TODOS OS TIPOS` para `TODOS`, remoção da opção redundante `AMBOS` (permanecendo estritamente `TODOS`, `CLIENTES` e `FORNECEDORES`), expansão da largura para `180px` (eliminando o corte do texto de `FORNECEDORES`) e readequação da textbox de busca para `max-width: 380px`.
- [x] **Alinhamento Contínuo e Responsividade Anti-Esmagamento da Barra de Clientes (v3.0):**
  - Unificação da barra em container flex único com `gap: 10px` contínuo entre todos os 4 elementos, eliminando o buraco vazio central e fazendo com que a busca expansiva (`flex: 1`) e os demais controles preencham 100% da div.
  - Adição de `flex-shrink: 0; min-width: 175px;` na combobox de tipo, eliminando em definitivo o esmagamento e sobreposição ("engolimento") do select em reduções progressivas da janela.
  - Agrupamento dos botões de ação com quebra suave e limpa para telas menores sem colisão visual.
- [x] **Inclusão Semântica do Tipo 'Ambos' nos Filtros de Clientes e Fornecedores (Abordagem Ágil):**
  - Normalização no backend (`ClienteFornecedorViewSet.get_queryset` em `apps/cadastros/views.py`) com `.strip().upper()`, tornando o filtro de tipo robusto contra variações maiúsculas/minúsculas (`CLIENTE`, `CLIENTES`, `Cliente`, `FORNECEDOR`, `FORNECEDORES`, `Fornecedor`).
  - Implementação semântica no ORM: parceiros cadastrados com o tipo `Ambos` (dupla atribuição) são incluídos automaticamente tanto nas buscas/filtros de Clientes (`tipo__in=['Cliente', 'Ambos']`) quanto de Fornecedores (`tipo__in=['Fornecedor', 'Ambos']`).
  - Suíte de testes automatizados unitários enriquecida (`test_filtro_tipo_clientes_e_fornecedores_inclui_ambos` em `cadastros/tests.py`), alcançando 17 testes específicos e 158 testes globais aprovados com 100% de sucesso.
- [x] **Correção da Seleção do Tipo de Cadastro na Edição de Clientes/Fornecedores e Versionamento PWA v3.1:**
  - Diagnóstico e correção no modal de edição (`abrirModalCadastroCompleto` em `cadastros-view.js`): resolução de incompatibilidade de casing entre API (`'Cliente'`, `'Fornecedor'`, `'Ambos'`) e atributos HTML dos options, garantindo pré-seleção correta do tipo real ao editar e eliminando o risco de sobrescrever fornecedores como clientes por engano.
  - Normalização preventiva em badges de listagem, botão de frota e filtros de clientes para orçamentos e frotas (`orcamentos-view.js`).
  - Cumprimento rigoroso da Regra 12 de Versionamento PWA: incremento do `CACHE_NAME` para `'emc-soldas-v3.1'` em `frontend/sw.js` e atualização dos sufixos de cache-busting `?v=3.1` em todas as tags `<script>` e `<link>` do `frontend/index.html`.
- [x] **Painel Operacional de Frota e Pátio (Filtro por Proprietário, Flag 'No Pátio' e PWA v3.2):**
  - Transformação da aba de Equipamentos em um painel completo de controle de frota e oficina, com barra integrada de 4 elementos: busca textual expansiva (`flex: 1; min-width: 220px;`), combobox dinâmica de proprietários (ordenada alfabeticamente com opção de não vinculados), toggle industrial `NO PÁTIO` e botão de novo cadastro.
  - Backend (`EquipamentoViewSet` e `EquipamentoSerializer`): suporte a `cliente_id` (com `sem_proprietario`), filtro `no_patio` cruzando com orçamentos ativos (`status_operacional__in=['APROVADO', 'EM_EXECUCAO']`), e campos computados `em_patio` e `orcamento_em_execucao`.
  - Frontend: badge visual de destaque `[NO PÁTIO (#X)]` na coluna de Proprietário da tabela.
  - Testes unitários dedicados em `apps/cadastros/tests.py` (19 testes de cadastros e 160 testes globais aprovados com 100% de sucesso).
  - Versionamento PWA: cache sincronizado para `emc-soldas-v3.2` em `frontend/sw.js` e tags atualizadas com `?v=3.2` em `frontend/index.html`.
- [x] **Temporizador Visual de Inatividade na Topbar & Alerta Fixo aos 30s (PWA v3.6):**
  - Componente de Topbar em Tempo Real: Inclusão do chip monospace `<span class="status-chip secondary mono-text" id="session-timer-chip">⏱ MM:SS</span>` na barra superior ao lado do indicador de conectividade (`ONLINE`).
  - Alerta Visual Mandatório aos 30s: Contagem regressiva contínua baseada em tempo real que transiciona para estilo de alerta (`status-chip warning` - tom âmbar/laranja industrial) quando o tempo restante for `<= 30 segundos`, avisando o operador antes do bloqueio automático.
  - Reset Dinâmico por Utilização Efetiva: O cronômetro reinicia de volta ao tempo total configurado imediatamente ao ocorrer qualquer clique no sistema, digitação, seleção ou chamada de API (mantendo o critério de que mexer o mouse sem clicar ou usar outros aplicativos no Windows não reseta a ociosidade da sessão).
  - Versionamento PWA: Cache sincronizado para `emc-soldas-v3.6` em `frontend/sw.js` e sufixos de cache-busting `?v=3.6` em `frontend/index.html`.
  - Suíte de Testes Automatizados: 36 testes executados e 100% aprovados (`apps.authentication` e `apps.administracao`).
- [x] **Restrição de Valores Mínimos em Parâmetros Globais & Bloqueio Anti-Negativo (PWA v3.7):**
  - Travamento Físico de Mínimos no Frontend: Configuração de `min="1"` e `step="1"` para Validade do Orçamento (`cfg-validade`) e Tempo Soft Lock (`cfg-ociosidade`), e `min="0"` e `step="1"` para Retenção de Logs (`cfg-retencao-logs`), impedindo navegação para valores negativos através das setinhas do stepper.
  - Sanitização Ativa de Entrada: Ouvintes reativos nos eventos `input` e `change` que corrigem imediatamente digitação ou colagem manual de números inferiores ao piso permitido (bloqueando sinais de menos ou valores negativos).
  - Blindagem Mandatória no Backend DRF: Validações no `ConfiguracaoGlobalSerializer` rejeitando com `400 Bad Request` qualquer payload com `validade_orcamento_dias < 1`, `tempo_ociosidade_minutos < 1` ou `retencao_logs_dias < 0`.
  - Versionamento PWA: Cache elevado para `emc-soldas-v3.7` em `frontend/sw.js` e sufixos de cache-busting `?v=3.7` em `frontend/index.html`.
  - Suíte de Testes Automatizados: 37 testes executados e 100% aprovados (`apps.authentication` e `apps.administracao`).
- [x] **Disparo Real de Teste SMTP via Conexão Direta, Presets de E-mail e Diagnóstico (PWA v3.8):**
  - Conexão SMTP Real Direta: Eliminação do interceptador de console local na função `testar_conexao_smtp()` em `apps/administracao/services.py`, forçando conexão por socket TCP direto com o host e porta indicados (ex: `smtp.gmail.com:587`) com timeout seguro de 15 segundos.
  - Sincronização de Parâmetros e Dados da Tela: Suporte ao alias `email_destino` no `TesteSmtpSerializer` e envio dinâmico dos dados digitados na tela na hora pelo frontend (inclusive nova senha de app digitada sem precisar salvar antes no banco).
  - Presets Rápidos de Provedores: Inclusão de botões rápidos `[GOOGLE GMAIL]` e `[MICROSOFT OUTLOOK]` no cabeçalho do formulário que preenchem automaticamente o host (`smtp.gmail.com` / `smtp.office365.com`) e porta (`587`) com 1 clique.
  - Versionamento PWA: Cache elevado para `emc-soldas-v3.8` em `frontend/sw.js` e sufixos de cache-busting `?v=3.8` em `frontend/index.html`.
  - Suíte de Testes Automatizados: 17 testes executados e 100% aprovados (`apps.administracao`).
- [x] **Gestão de Formas & Regras Comerciais de Pagamento e CRUD Completo de Dicionários Mestres (PWA v3.9):**
  - **Aba de Formas & Regras de Pagamento:** Criação da aba dedicada na Central do Administrador (`#/administracao`) estruturada em duas tabelas no padrão *Industrial Integrity*:
    - **Meios de Pagamento (`MeioPagamento`):** Listagem com ID, Nome, badge de Taxa de Maquininha (sim/não), Status e botões de `EDITAR` e `EXCLUIR` (soft delete seguro com bloqueio automático pelo backend caso haja regras ativas ou movimentações vinculadas).
    - **Regras Comerciais (`RegraPagamento`):** Listagem com Meio vinculado, Tipo de Cobrança (`À VISTA`, `A PRAZO`, `PARCELADO`), número de parcelas, intervalos e prazos de vencimento em dias, percentual de desconto sugerido, Status e botões de `EDITAR` e `EXCLUIR` (soft delete seguro com bloqueio automático pelo backend caso haja propostas ou faturas vinculadas).
    - Modais industriais para criação e edição com validações reativas e atualização em tempo real.
  - **CRUD Completo em Dicionários Mestres (UOM & Atributos Técnicos):**
    - Adição de coluna `AÇÕES` com botões `EDITAR` e `EXCLUIR` nas tabelas de Unidades de Medida (`DicionarioUom`) e Atributos Técnicos (`DicionarioAtributo`).
    - Modais dedicados de edição com suporte a `PUT` nas rotas da API.
    - Exclusão lógica com confirmação e tratamento gracioso das proteções do backend (impedindo exclusão de UOMs ou atributos em uso por itens/produtos no catálogo).
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v3.9` em `frontend/sw.js` e sufixos de cache-busting `?v=3.9` em `frontend/index.html`.
  - **Suíte de Testes Automatizados:** 49 testes executados e 100% aprovados (`apps.financeiro`, `apps.catalogo`, `apps.administracao`).
- [x] **Reestruturação e Empilhamento Vertical de Formas & Regras Comerciais de Pagamento (PWA v4.0):**
  - **Empilhamento Vertical 100%:** Transição do layout de 2 colunas paralelas apertadas (`5fr` / `7fr`) para disposição empilhada (um card abaixo do outro com largura total), eliminando esmagamentos de texto, truncamento no cabeçalho e cortes horizontais na tabela de regras.
  - **Card Superior (Meios de Pagamento):** Largura completa com visual arejado e tabela densa (`ID`, `NOME DO MEIO`, `TAXA MAQUININHA`, `STATUS`, `AÇÕES`), botão `+ NOVO MEIO DE PAGAMENTO`.
  - **Card Inferior (Regras Comerciais):** Largura completa acomodando com total folga e legibilidade as 9 colunas (`ID`, `NOME DA REGRA`, `MEIO VINCULADO`, `TIPO COBRANÇA`, `PARCELAS`, `PRAZOS / INTERVALO`, `DESCONTO (%)`, `STATUS`, `AÇÕES`), botão `+ NOVA REGRA COMERCIAL` com rótulo completo e botões de ação folgados.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.0` em `frontend/sw.js` e sufixos de cache-busting `?v=4.0` em `frontend/index.html`.
  - **Suíte de Testes Automatizados:** 34 testes executados e 100% aprovados (`apps.administracao`, `apps.financeiro`).
- [x] **Fluidez Vertical e Eliminação de Scroll Horizontal em Modais Mobile (PWA v4.1):**
  - **Blindagem Global Anti-Scroll Horizontal:** Configuração de `overflow-x: hidden;` e `box-sizing: border-box;` em `.modal-card` e `.modal-body` no `industrial-integrity.css`, eliminando barras de rolagem horizontais em qualquer modal da aplicação.
  - **Classes Utilitárias de Grids Responsivos:** Implementação de `.form-grid-2` e `.form-grid-3` e ampliação do seletor responsivo (`.modal-body div[style*="grid-template-columns"]`, `.modal-body div[style*="display: grid"]`, `.form-grid-2`, `.form-grid-3`), forçando colapso automático para 1 coluna (`grid-template-columns: 1fr !important;`) em telas `<= 768px` (smartphones em modo retrato e paisagem).
  - **Reestruturação do Modal de Regras de Pagamento:** Eliminação de grids inline rígidos, garantindo que parcelas, prazos e descontos quebrem suavemente em linhas individuais no celular, rolando com fluidez natural exclusivamente na vertical.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.1` em `frontend/sw.js` e sufixos de cache-busting `?v=4.1` em `frontend/index.html`.
  - **Suíte de Testes Automatizados:** 34 testes executados e 100% aprovados (`apps.administracao`, `apps.financeiro`).
- [x] **Combobox Pesquisável com Autocomplete para Insumos na Ficha Técnica BOM (PWA v4.2):**
  - **Campo de Busca e Digitação em Tempo Real:** Conversão do seletor nativo `<select id="add-ficha-item-id">` no modal de Ficha Técnica (BOM) em componente dinâmico `window.EMCUtils.initSearchableSelect`, idêntico ao de veículos e orçamentos, permitindo digitar trechos de insumos e matérias-primas e filtrar instantaneamente.
  - **Ordenação Alfabética Prévia:** Ordenação automática alfabética por nome (`localeCompare`) dos itens retornados da API antes da montagem das opções.
  - **Navegação Completa por Teclado:** Suporte total a navegação com setas cima/baixo, Enter para selecionar e Esc para fechar, mantendo o valor selecionado no select nativo e submissão 100% compatível com a API REST.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.2` em `frontend/sw.js` e sufixos de cache-busting `?v=4.2` em `frontend/index.html`.
- [x] **Reestruturação Universal das Barras de Filtros e Comboboxes com Flags Multiselect (PWA v4.3):**
  - **Eliminação de Espaços Vazios e Larguras Fixas:** Remoção de travas de `max-width: 380px`, adotando campos de pesquisa elásticos (`flex: 1; min-width: 240px;`), chips contadores em tempo real (`status-chip secondary`) e botões primários integrados à barra em todas as telas principais do sistema.
  - **Catálogo & Motor BOM (`/#catalogo`):** Ambas as abas (Insumos e Produtos) reformuladas com busca elástica, chip totalizador e botão primário, respeitando a diretriz de não utilizar filtro de unidade de medida.
  - **Compras & Entradas (`/#compras`):** Barra unificada com busca elástica por NFe, combobox pesquisável de fornecedores, chip totalizador e botão `+ LANÇAR NOTA DE COMPRA`.
  - **Tesouraria & Caixa (`/#tesouraria`):**
    - *Aba Extrato:* Busca elástica, combobox multiselect com flags para Contas Bancárias (seleção de 1 ou N contas com botões rápidos `[✓ TODOS]` e `[✕ LIMPAR]`), filtro de tipo e botão de lançamento.
    - *Aba Contas a Pagar:* Busca elástica, combobox multiselect com flags para Status (`PENDENTE`, `PAGO`, `PARCIAL`, `CANCELADO`), chip totalizador e botão de despesa rápida.
    - *Aba Contas a Receber:* Busca elástica, combobox multiselect com flags para Status, chip totalizador e botão de receita rápida.
  - **Faturamento (`/#faturamento`):** Busca elástica por cliente/fatura, combobox multiselect com flags para Status (`FATURADO`, `PAGO`, `PARCIAL`, `CANCELADO`), chip totalizador e atalho para Conta Corrente.
  - **Orçamentos (`/#orcamentos`):** Busca elástica por cliente/equipamento/número, combobox multiselect com flags para Status Operacional, filtro de status financeiro, chip totalizador e botão `+ NOVO ORÇAMENTO` integrado.
  - **Backend com Suporte a Filtros Múltiplos Separados por Vírgula:** Suporte a filtros `status__in`, `conta_id__in`, `status_operacional__in` e `status_financeiro__in` via DRF Queryset em `LancamentoFinanceiroViewSet`, `FaturaViewSet` e `OrcamentoViewSet`.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.3` em `frontend/sw.js` e sufixos de cache-busting `?v=4.3` em `frontend/index.html`.
- [x] **Padronização Visual Universal de Controles (42px), Correção de Tela e Governança de Commits (PWA v4.4):**
  - **Correção de Runtime na Tela de Compras (`/#compras`):** Conversão de `render(container)` para método assíncrono `async render(container)` em `compras-view.js`, eliminando o erro de sintaxe `SyntaxError: await is only valid in async functions` que causava `Cannot read properties of undefined (reading 'render')`.
  - **Altura Canônica Universal de 42px para Controles Interativos:** Fixação estrita de `height: 42px; box-sizing: border-box !important;` em `.form-control`, `select.form-control`, `.btn`, `.emc-combobox-trigger` e `.emc-multiselect-trigger` no `industrial-integrity.css`, eliminando qualquer desnível de pixels entre textboxes, comboboxes e botões nas barras de ferramentas.
  - **Harmonização Cromática e Prevenção de Encavalamento:** Declaração de `--color-rust-orange-bright: #ff6b35;` no `:root`, correção de contraste em textos selecionados e padding de foco compensado (`0 13px`) para preservar a altura total exata de 42px com borda de 2px.
  - **Norma Documental de Layout em `docs/DESIGN.md`:** Registro da seção normativa "Interactive Controls & Dimensional Consistency" definindo alturas (42px padrão, 32px small), tipografia técnica (`Inter` para dados, `JetBrains Mono` para botões e códigos) e alinhamento em flex containers.
  - **Governança de Commits Semânticos em `AGENTS.md` e `docs/FSD.md`:** Inclusão da Regra Mandatória 13 no `AGENTS.md` exigindo commits formais após cada Implementation Plan aprovado e inclusão da Seção 30 no `docs/FSD.md` com a tabela e convenções completas do Conventional Commits.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.4` em `frontend/sw.js` e sufixos de cache-busting `?v=4.4` em `frontend/index.html`.
- [x] **Correção de Espaçamento e Eliminação de Encavalamento nas Comboboxes da Aba Extrato (PWA v4.5):**
  - **Blindagem do Componente `.emc-multiselect`:** Configuração mandatória de `display: block; width: 100%; box-sizing: border-box;` no Design System (`industrial-integrity.css`), impedindo que o container multi-seleção vaze horizontalmente para além do seu wrapper e cause fusão visual de bordas com seletores adjacentes.
  - **Calibração Dimensional da Barra de Filtros do Extrato:** Redimensionamento de `#wrapper-extrato-conta` para `220px` (min-width `180px`) e `#filtro-extrato-tipo` para `160px` (min-width `150px`) em `financeiro-view.js`, preservando folga elástica e espaçamento físico nítido de `gap: 10px` entre todos os controles interativos.
  - **Ocultação Estrita do Select Nativo:** Reforço com `display: none !important` via JavaScript em `utils.js` para garantir que nós nativos não ocupem fluxo de layout residual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.5` em `frontend/sw.js` e sufixos de cache-busting `?v=4.5` em `frontend/index.html`.
- [x] **Ajuste de Responsividade e Contenção dos Flip Cards do Dashboard no Mobile (PWA v4.6):**
  - **Prevenção de Transbordamento Vertical:** Elevação da altura de `.flip-card-wrapper` na media query `@media (max-width: 480px)` de `155px` para `195px` em `layout.css` e `industrial-integrity.css`, comportando perfeitamente a quebra de 2 linhas do título "OPERAÇÃO DE OFICINA" com o selo "GIRE ↻" e o subtítulo descritivo em colunas de smartphone.
  - **Contenção e Blindagem de Faces:** Aplicação de `overflow: hidden;` nas faces `.flip-card-front` e `.flip-card-back` com padding de `10px 8px`.
  - **Otimização de Fontes e Espaçamentos:** Calibração de `flip-card-title` (10px), `flip-card-sub` (11px, line-height 1.2), `flip-card-footer` (padding 6px/margin 4px), `flip-card-btn-detail` (10.5px) e versos dos cards (font 11px, line-height 1.4) para garantir estética industrial equilibrada e eliminação completa de vazamento.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.6` em `frontend/sw.js` e sufixos de cache-busting `?v=4.6` em `frontend/index.html`.
- [x] **Combobox Autocomplete Pesquisável e Modal de Cadastro de Fornecedor em Compras (PWA v4.7):**
  - **Combobox com Busca em Tempo Real e Autocomplete:** Conversão do `<select id="nota-fornecedor">` e `<select id="sub-item-id">` no modal de Compras (`LANÇAR NOTA FISCAL DE ENTRADA`) em comboboxes pesquisáveis industriais (`initSearchableSelect`), eliminando o seletor nativo do mobile e permitindo filtrar por nome/razão social em tempo real.
  - **Suporte Arquitetural a Modais Empilhados (*Stacked Modals*):** Refatoração de `openModal` e `closeModal` em `utils.js` para gerenciamento dinâmico via pilha (`modalStack`) com *z-index* incremental, possibilitando abrir o modal de cadastro de fornecedor sobre o modal de compras sem fechá-lo ou destruir os dados digitados na nota.
  - **Ação Integrada "+ NOVO FORNECEDOR":** Disponibilização de atalho visual no cabeçalho do campo e botão de ação integrado dentro do dropdown pesquisável da combobox (`.emc-combobox-action`).
  - **Retroalimentação e Seleção Automática:** Ao concluir o cadastro no modal secundário, a combobox de compras é atualizada dinamicamente com as opções ordenadas e o novo fornecedor já selecionado, sem perda de contexto ou recarregamento de página.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.7` em `frontend/sw.js` e sufixos de cache-busting `?v=4.7` em `frontend/index.html`.
- [x] **Correção de Fechamento de Bloco JSDoc em `utils.js` e Blindagem de Abertura de Compras (PWA v4.8):**
  - **Correção Crítica de Runtime em `openModal`:** Fechamento do bloco JSDoc da Seção 6 de `frontend/assets/js/utils.js` com `*/` antes de `const modalStack = [];`, resolvendo `ReferenceError: modalStack is not defined` que impedia a abertura do modal de compras e de outros modais do sistema.
  - **Blindagem Defensiva em `compras-view.js`:** Envolvimento do método `abrirModalCompra()` em bloco `try ... catch` com feedback claro via Toast notification caso haja falhas de carregamento ou rede.
  - **Homologação da Bateria de Testes Backend:** Execução de 161 testes do Django com 100% de aprovação (0 erros, 0 falhas).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.8` em `frontend/sw.js` e sufixos de cache-busting `?v=4.8` em `frontend/index.html`.
- [x] **Auto-Cálculo de Valor Total e Upload/Download Seguro de DANFE/XML em Compras (PWA v4.9):**
  - **Blindagem do Valor Total:** O frontend passa a calcular a soma dos subtotais dos itens e injetar `valor_total` no payload JSON. O serializer do backend torna o campo opcional e calcula automaticamente caso omitido, eliminando o erro de validação `"valor_total é obrigatório"`.
  - **Hardening e Validação Rigorosa de Arquivos (Headers/Magic Bytes):** Implementada checagem binária dos primeiros bytes do arquivo (`%PDF`, `\x89PNG`, `\xff\xd8\xff`), proteção estrita contra Path Traversal e Null Bytes no nome do arquivo, e proteção anti-XXE com bloqueio de DTD e entidades externas em arquivos XML.
  - **Upload e Gestão da DANFE no Frontend:** Campo de arquivo no modal de compras (`accept=".pdf,.xml"`), upload automático em `FormData` após registro da nota, botão `📄 DANFE` na listagem de notas e opção de download seguro no modal de detalhes via Blob com Content-Disposition forçado.
  - **Homologação da Bateria de Testes:** Execução de 163 testes automatizados do Django com 100% de aprovação (OK em 65.1s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.9` em `frontend/sw.js` e sufixos de cache-busting `?v=4.9` em `frontend/index.html`.
- [x] **Alinhamento Horizontal, Enquadramento Proporcional e Estilização Usinada do Modal de Compras (PWA v4.10):**
  - **Combobox Elástica de Fornecedor & Número de Nota Compacto:** Redefinido o grid superior do modal para `grid-template-columns: minmax(0, 1fr) 180px 160px; gap: 12px;`, permitindo que o seletor de fornecedor expanda organicamente para preencher o espaço remanescente, enquanto o número da nota assume largura compacta (180px) com o rótulo conciso `"Nº Nota (NF-e/Recibo) *"`, eliminando qualquer quebra de linha.
  - **Enquadramento Perfeito da Data de Emissão:** A coluna de data de emissão foi ajustada para 160px com `width: 100%; box-sizing: border-box;`, resolvendo o transbordamento lateral e mantendo o campo 100% contido dentro da borda direita do modal.
  - **Equalização Vertical dos Inputs:** Padronizada a altura dos contêineres de rótulos (`min-height: 22px; display: flex; align-items: center; margin-bottom: 4px;`) em todos os `.form-group` da linha, garantindo alinhamento horizontal milimétrico dos campos.
  - **Estilização Usinada de `input[type="file"]`:** Criada regra no Design System (`industrial-integrity.css`) para `<input type="file"].form-control` e `::file-selector-button` sem cantos arredondados, com altura padronizada de 42px.
  - **Homologação:** 163 testes automatizados do Django executados com 100% de aprovação (OK em 82.6s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.10` em `frontend/sw.js` e sufixos de cache-busting `?v=4.10` em `frontend/index.html`.
- [x] **Importação Inteligente de Documento Fiscal (DANFE/XML) com Pré-Preenchimento e Cruzamento Cadastral em Compras (PWA v4.11):**
  - **Posicionamento no Topo do Modal:** O campo de upload da DANFE (PDF) ou XML da NF-e foi elevado para a primeira posição com destaque visual e feedback em tempo real de status da análise (`ANALISANDO DOCUMENTO...` -> `DADOS EXTRAÍDOS COM SUCESSO`).
  - **Extração Determinística sem Dados Fantasma:** Implementadas rotinas em `apps/compras/services.py` (`extrair_dados_xml_nfe` e `extrair_dados_pdf_danfe` com `pypdf>=4.0.0`) com validação Módulo 11 da chave de 44 dígitos da NF-e e extração estrita dos campos existentes no formulário (CNPJ emitente, número da nota, data de emissão, chave e valor total).
  - **Cruzamento Cadastral por Dígitos Limpos:** Endpoint `POST /api/documentos-fiscais-compra/analisar-documento/` cruza o CNPJ do emitente contra a base higienizando pontuações.
  - **Fluxo com Modais Empilhados (*Stacked Modals*):**
    - Se for **Fornecedor** (ou *Ambos*): seleciona automaticamente na combobox e preenche número, data e chave.
    - Se for apenas **Cliente**: exibe modal de confirmação para habilitar como fornecedor (tipo *Ambos*) via `POST /api/clientes-fornecedores/{id}/habilitar-fornecedor/` sem duplicar registro; em caso afirmativo, atualiza, seleciona e preenche.
    - Se for **Novo Emitente**: abre o modal de cadastro de fornecedor empilhado com CNPJ e Razão Social pré-preenchidos e consulta pública automática da Receita Federal; ao salvar, seleciona o novo fornecedor e fecha o modal secundário.
    - Em caso de recusa: o arquivo permanece anexado e o formulário é liberado para edição livre.
- [x] **Detecção de Boletos, Chaves NF-e/NFS-e e Card Enriquecido de Fornecedor (PWA v4.13):**
  - **Bloqueio Impeditivo de Boletos Bancários:** Implementada classificação prévia de documentos em `apps/compras/services.py` (`classificar_documento_fiscal_pdf`). Boletos de cobrança e fichas de compensação são detectados e barrados de imediato com aviso orientativo para registro no módulo Financeiro (Contas a Pagar), impedindo o cadastro indevido de pagadores como fornecedores.
  - **Extração Robusta de Chaves de 44 e 50 Dígitos:**
    - Suporte formal à Chave de Acesso Nacional da NFS-e (DANFSe v2.0 com 50 dígitos numéricos).
    - Extração à prova de falhas em DANFE NF-e 55 com busca direta pelos 11 blocos de 4 dígitos formatados, evitando colisões com números vizinhos (CNPJ/protocolos).
    - Suporte à Nota Fiscal de Comunicação Eletrônica (NFCom modelo 62) presente em faturas de telecomunicações.
  - **Segregação Estrita Prestador vs. Tomador:** No processamento de PDFs, o extrator prioriza os blocos de `PRESTADOR / FORNECEDOR` e `EMITENTE`, descartando estritamente os dados do `TOMADOR / ADQUIRENTE` para evitar inversão cadastral.
  - **Card Enriquecido de Fornecedor Não Encontrado:** Ao analisar um documento cujo fornecedor ainda não existe no sistema, o backend consulta a Receita Federal em tempo real (`consultar_cnpj_externo`), e o modal *"FORNECEDOR NÃO ENCONTRADO"* exibe a Razão Social completa, Nome Fantasia, CNPJ formatado e Localidade (Cidade/UF) para conferência segura.
  - **Máscara Especializada da Chave NFS-e (50 dígitos):** A função `formatarChaveAcessoNfe` em `utils.js` agora aplica a máscara canônica da NFS-e Nacional (`9999999 9 99999999999999 99999 999999999999999 9999999 9`) quando o documento possui 50 dígitos, e preserva o padrão de 11 grupos de 4 dígitos para as chaves com 44 dígitos (NF-e, NFCom).
  - **Homologação da Bateria de Testes:** Suíte completa com 168 testes automatizados do Django executados com 100% de aprovação (OK em 67.6s).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.14` em `frontend/sw.js` e sufixos de cache-busting `?v=4.14` em `frontend/index.html`.
- [x] **Normatização de Espaços, Cálculo de Altura e Responsividade Mandatória de Modais (PWA v4.17):**
  - **Engenharia de Layout e Teto Vertical Mandatório em `docs/DESIGN.md`:** Instituição da Seção 5 ("Engenharia e Cálculo de Espaços para Modais e Formulários - Modal Spatial Budget") e regra de responsividade universal mandatória em 100% dos componentes e modais do sistema.
  - **Regra do Teto Vertical (88vh / 94vh):** `.modal-card` com `max-height: 88vh; min-height: 0; overflow: hidden;`, cabeçalho fixo (52px), rodapé de ações fixo (60px, `flex-shrink: 0`) e corpo do modal com rolagem suave autocontida (`flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden;`).
  - **Densidade e Compactação de Formulários em Modais:** Em `.modal-body`, o `.form-group` adota `margin-bottom: 10px; gap: 4px;` e eliminação de `margin-top` redundantes inline.
  - **Botão de Fechar Usinado (`.modal-close-btn`):** Dimensões compactas (32x32px, 0px border-radius), perfeitamente centralizado com ícone `✕` sem colidir nas bordas da moldura do cabeçalho.
  - **Reestruturação Funcional do Modal de Lançamento no Extrato (`financeiro-view.js`):** Modal reconfigurado para `size: 'lg'`, banner de aviso compacto, grid `1fr 160px` para Categoria + Data de Pagamento (garantindo espaço amplo para nomes longos) e `1.2fr 1fr` para Conta Bancária + Meio de Pagamento, mantendo 100% dos botões visíveis sem transbordo.
  - **Correção Responsiva na Media Query 768px:** Substituição de classe legada por `.modal-card` com `width: 96vw; max-width: 96vw; max-height: 92vh; margin: auto;` e colapso automático de todos os grids para coluna única (`1fr !important; gap: 10px !important;`).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.17` em `frontend/sw.js` e sufixos de cache-busting `?v=4.17` em `frontend/index.html`.
- [x] **Unificação de Ações de Lançamento e Expansão das Comboboxes de Filtro no Extrato Real (PWA v4.18):**
  - **Eliminação de Redundância Operacional:** Remoção do botão secundário duplicado `+ LANÇAMENTO AVULSO` da barra de filtros do Extrato Real em `financeiro-view.js`.
  - **Centralização Limpa no Topo:** Preservação estrita dos dois botões canônicos no topo da view (`+ TRANSFERÊNCIA INTER-CONTAS` e `+ NOVO LANÇAMENTO`), com detecção inteligente de contexto ativando automaticamente o modo de Caixa Real quando a aba ativa for o Extrato.
  - **Expansão Dimensional das Comboboxes de Filtro:**
    - Seletor de Contas Bancárias (`#wrapper-extrato-conta`): ampliado de `220px` para `270px` (min-width `240px`), eliminando reticências e exibindo `"TODAS AS CONTAS BANCÁRIAS"` por extenso com folga.
    - Seletor de Tipo de Movimentação (`#filtro-extrato-tipo`): ampliado de `160px` para `190px` (min-width `175px`), acomodando com folga `"TODOS OS TIPOS"`, `"RECEITAS (+)"` e `"DESPESAS (-)"`.
    - Campo de Busca Textual (`#filtro-extrato-busca`): expansivo (`flex: 1; min-width: 200px;`) preenchendo o espaço remanescente com equilíbrio visual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.18` em `frontend/sw.js` e sufixos de cache-busting `?v=4.18` em `frontend/index.html`.
- [x] **Conciliação Bancária Visual com Linhas de Match Bézier e Operação Dual-Mode (PWA v4.19):**
  - **Motor SVG Nativo de Conexões Curvas (Bézier Cúbicas):** Implementação de overlay responsivo com cálculo dinâmico via `getBoundingClientRect()` conectando nós industriais das transações do extrato aos cards correspondentes do ERP.
  - **Feedback Semântico Visual:** Linhas verdes contínuas para correspondências confirmadas, linhas âmbar tracejadas para sugestões prováveis e realce instantâneo no hover/foco. Ocultação automática em telas menores (<900px) para ergonomia mobile.
  - **Operação Dual-Mode (Modo Duplo):**
    - *Modo 1 (Conferência & Match):* Conciliação de lançamentos já existentes no ERP, com suporte a Auto-Match 1:1, seleção manual, desconciliação e criação de lançamento rápido no ato para sobras do extrato.
    - *Modo 2 (Importação Total & Lote):* Espelhamento automático de todas as linhas do extrato como pré-lançamentos do ERP com linhas conectivas, permitindo ajuste inline da descrição e Categoria DRE, descarte individual com botão `✕` (e restauração `↩`), e geração em lote com 1 clique.
  - **Endpoint e Atomicidade no Backend:** Criação da rota `POST /api/conciliacao/importacao-lote/` com `ImportacaoLoteSerializer`, validação contra o limite de cheque especial da conta bancária, execução atômica via `transaction.atomic()`, quitação imediata (`status_pagamento='PAGO'`), marcação `is_conciliado=True` e auditoria perpétua.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.19` em `frontend/sw.js` e sufixos de cache-busting `?v=4.19` em `frontend/index.html`.
- [x] **Alinhamento dos Nós Âncora e Luz Neon nas Linhas Bézier da Conciliação (PWA v4.20):**
  - **Coerência Visual Ponto a Ponto (Nó a Nó):** Universalização do seletor `.anchor-node` no CSS e adição da classe `.split-item` ao container `.pre-lancamento-card`, posicionando o boton verde perfeitamente na borda esquerda (`left: -5px; top: 50%; transform: translateY(-50%)`) com sombra circular idêntica ao boton de saída da borda direita.
  - **Luz Neon Acelerada por GPU nas Linhas Vetoriais:** Aplicação de `filter: drop-shadow(...)` de camada dupla em `.svg-path-match` e `.svg-path-suggestion`, produzindo uma iluminação neon nítida que acompanha perfeitamente o traçado curvilíneo sem borrões no DOM ou perda de performance.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.20` em `frontend/sw.js` e sufixos de cache-busting `?v=4.20` em `frontend/index.html`.
- [x] **Alinhamento do Botão de Descarte e Categoria DRE Obrigatória em Branco (PWA v4.21):**
  - **Reestruturação Vertical do Pré-Lançamento:** Eliminação do esmagamento horizontal com `display: flex !important; flex-direction: column !important; gap: 8px !important;` no `.pre-lancamento-card`, organizando o card em cabeçalho superior (título na esquerda, valor e botão `✕` de 26x24px alinhados no centro à direita) e grid de edição inferior (descrição e select).
  - **Categoria DRE Inicial em Branco:** Inicialização de `categoria_id: null` com a opção `-- SELECIONE A CATEGORIA DRE * --` no topo do select e destaque de aviso sutil (`.select-categoria-pendente`).
- [x] **Inteligência na Conciliação Bancária, Prevenção de Duplicidade, Reconhecimento de Parceiros, Retenção de ISS e Carga Histórica (PWA v4.22):**
  - **Prevenção Robusta de Duplicidades:** Algoritmo defensivo checando se as transações do extrato já existem no ERP (por FITID bancário único ou por combinação de valor idêntico e proximidade de ±2 dias já conciliada na conta), sinalizando visualmente com badge `[🔒 JÁ NO ERP]` e descartando compulsoriamente por padrão na mesa de triagem para impedir duplicações de saldo.
  - **Reconhecimento Automático de Parceiros por CNPJ/CPF:** Parser com extração regex de documentos na descrição da transação (ex: `02.329.307/0001-66 - PETRA MG`), cruzando instantaneamente com `ClienteFornecedor` e exibindo badge semântico `[🏢 PARCEIRO IDENTIFICADO]`.
  - **Cruzamento Inteligente com Faturas em Aberto & Retenção de ISS:**
    - Flag `iss_retido` no modelo `ClienteFornecedor` com checkbox no modal de cadastro completo.
    - Parâmetros Fiscais em `ConfiguracaoGlobal`: campos editáveis `aliquota_iss` (padrão 3.00%) e `aliquota_simples_nacional` (informativo, padrão 8.50%) na aba de Administração.
    - Cruzamento com faturas do cliente (`status='FATURADA'`): se o cliente possui retenção de ISS, o sistema calcula o valor líquido esperado (`valor_fatura - (valor_fatura * aliquota_iss / 100)`) e compara com a transação bancária considerando **tolerância de até 5 centavos (R$ 0,05)** para variações de arredondamento bancário.
    - Sugestão automática e baixa imediata de faturas na importação via `receber_pagamento_fatura`, sem duplicar crédito de saldo e carimbando FITID e conciliação nos títulos.
  - **Carga Histórica sem Orçamentos/Faturas Retroativas:** Adição das colunas `cliente_fornecedor_id` e `fitid` em `LancamentoFinanceiro`, permitindo que receitas e despesas de períodos anteriores sejam associadas diretamente aos clientes/fornecedores reais sem exigir orçamentos fictícios, alimentando perfeitamente o DRE e o Dossiê do Cliente.
  - **Classificação Heurística de Categorias DRE:** Sugestão automática de categorias contábeis para Tarifas Bancárias (`TAR`, `IOF`, `DOC/TED`, etc.), Tributos/Guias (`DAS`, `GPS`, `FGTS`, `DARF`, etc.) e Receitas Operacionais para clientes identificados.
  - **Testes Automatizados:** Suíte de conciliação enriquecida (`test_reconhecimento_parceiro_fatura_iss_retido_e_duplicidade`) com 100% de aprovação (72 testes automatizados acumulados em conciliação, cadastros, administração e financeiro).
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.22` em `frontend/sw.js` e sufixos de cache-busting `?v=4.22` em `frontend/index.html`.
- [x] **Padronização e Contraste Industrial Escuro nas Comboboxes de Categoria DRE (PWA v4.23):**
  - **Eliminação do Fundo Branco:** Refatoração de `.select-categoria-pendente` e `select.form-control option` para assegurar fundo escuro industrial (`var(--color-surface-container-low)` / `#1b1c1c`) e tipografia clara com legibilidade nítida em qualquer estado (selecionado ou pendente).
  - **Sinalização Sutil de Pendência:** A pendência de seleção de categoria agora é indicada exclusivamente pela borda âmbar (`border-color: var(--color-warning)`), sem alterar a tonalidade de fundo nem comprometer o contraste no desktop ou mobile.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.23` em `frontend/sw.js` e sufixos de cache-busting `?v=4.23` em `frontend/index.html`.
- [x] **Rolagem Simultânea e Sincronizada das Colunas na Conciliação Bancária (PWA v4.24):**
  - **Controle Visual na Barra de Ferramentas:** Adição do toggle/checkbox `[x] ROLAGEM SIMULTÂNEA` na barra de controle da tela de conciliação com persistência em tempo real.
  - **Mecanismo de Scroll Proporcional Bidirecional:** Sincronização inteligente baseada no ratio de deslocamento (`scrollTop / (scrollHeight - clientHeight)`) entre o Extrato Bancário e a Mesa de Triagem/ERP, mantendo os cards equivalentes sempre alinhados lado a lado.
  - **Prevenção de Loop de Eventos:** Bloqueio através de flag de concorrência (`isSyncingScroll`) e renderização em `requestAnimationFrame`, mantendo o redesenho dinâmico das linhas Bézier cúbicas sem travamento de tela.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.24` em `frontend/sw.js` e sufixos de cache-busting `?v=4.24` em `frontend/index.html`.
- [x] **Expurgo Operacional e Limpeza do Banco de Dados para Início de Carga Real (Produção):**
  - **Limpeza Segura de Dados Transacionais e Cadastrais de Teste:** Execução atômica via comando de management `reset_banco_para_producao --confirmar` com exclusão em ordem referencial de FKs (`LancamentoFinanceiro`, `Fatura`, `Orcamento`, `DocumentoFiscalCompra`, `Produto`, `Item`, `Equipamento`, `ClienteFornecedor`, cartões corporativos e contas bancárias extras).
  - **Reset de Contadores AUTO_INCREMENT para 1:** Instrução nativa `ALTER TABLE ... AUTO_INCREMENT = 1` aplicada a todas as tabelas operacionais esvaziadas, garantindo que o primeiro cliente, orçamento, fatura, documento e cartões comecem estritamente no ID #1.
  - **Ajuste de Sequencial de Contas Bancárias (Próximo ID = 3):** Reset de `contas_bancarias` com `AUTO_INCREMENT = 1`, instruindo o MySQL a recalcular `max(id) + 1 = 3`, eliminando saltos nos IDs após expurgo de contas de teste.
  - **Preservação Rígida de Tabelas Mestras e Domínio:** Dicionários Centrais (`UOM` e `Atributos`), Categorias Contábeis DRE (13 categorias), Meios e Regras Comerciais de Pagamento, Configurações Globais e usuário Administrador Master (`admin@emcsoldas.com.br`) com seus 10 toggles dinâmicos.
  - **Contas Bancárias Zeradas:** As contas padrão estruturais (`CAIXA FISICO DA OFICINA` e `CONTA BANCARIA PRINCIPAL`) foram preservadas e inicializadas com saldo exato de `R$ 0,00`, prontas para receber os extratos bancários de 02/2025.
- [x] **Seleção Obrigatória de Conta Bancária na Conciliação e Detecção Heurística de Meios de Pagamento (PWA v4.28):**
  - **Seleção Ativa Mandatória de Conta:** A tela de conciliação bancária (`#/conciliacao`) agora inicializa estritamente com `-- SELECIONE A CONTA BANCÁRIA * --` sem pré-selecionar nenhuma conta por padrão. O botão de upload e a análise ficam bloqueados até que o operador selecione conscientemente a conta de destino, eliminando conciliações por engano.
  - **Classificador Heurístico Inteligente de Meios de Pagamento:** Implementação de motor em `apps/conciliacao/services.py` (`detectar_meio_pagamento_transacao`) com análise de padrões no `<MEMO>`, `<NAME>` e `<TRNTYPE>` do OFX, categorizando com precisão: `PIX` (transferências, chaves, QR codes), `CARTÃO DE DÉBITO`, `CARTÃO DE CRÉDITO`, `TRANSFERÊNCIA (TED/DOC)`, `BOLETO BANCÁRIO` e `DEPÓSITO BANCÁRIO / DINHEIRO`.
  - **Mesa de Triagem Enriquecida (Modo 2):** Cada card de transação na esteira de importação passa a exibir uma combobox pesquisável de Meio de Pagamento pré-preenchida com a sugestão inteligente, permitindo ao operador alterar manualmente antes de confirmar a importação em lote.
  - **Persistência Fiel no Backend:** O endpoint de importação em lote (`executar_importacao_lote`) agora lê o `meio_pagamento_id` real enviado em cada transação, eliminando o fallback genérico que gravava tudo como boleto bancário.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.28` em `frontend/sw.js` e sufixos de cache-busting `?v=4.28` em `frontend/index.html`.
  - **Homologação:** Suíte completa com 184 testes automatizados do Django executados com 100% de aprovação (OK em 74s).
- [x] **Reestruturação das Categorias DRE, Purga de Testes (C1) e Blindagem de Credenciais do Seeder:**
  - **Reestruturação Oficial das 20 Categorias:** Reformulação do catálogo de categorias contábeis no `seed_initial_data.py` e no banco de dados. Remoção de `(MAO DE OBRA)` de receitas, criação de `AQUISIÇÃO DE MÁQUINAS E EQUIPAMENTOS` (Investimento CAPEX) segregada de `MANUTENÇÃO DE MÁQUINAS E INSTALAÇÕES` (OPEX), e separação clara entre `FOLHA DE PAGAMENTO (SALARIOS E BENEFICIOS)`, `ENCARGOS TRABALHISTAS (FGTS E INSS)`, `PRO-LABORE DOS SOCIOS`, `IMPOSTOS E TRIBUTOS (SIMPLES NACIONAL / ISS / TAXAS)` e `RETIRADA DE SOCIOS / DISTRIBUICAO DE LUCRO`.
  - **Purga Definitiva de Registros de Teste:** Exclusão automática de categorias residuais de teste (`C1`) e migração atômica sem duplicidade de IDs para categorias pré-existentes.
  - **Blindagem de Credenciais no Seeder:** Substituição de senhas/PINs hardcoded em `seed_initial_data.py` por leitura dinâmica via variáveis de ambiente (`INITIAL_ADMIN_PASSWORD` e `INITIAL_ADMIN_PIN`) com fallback transparente para o ambiente de desenvolvimento local.
  - **Enriquecimento do Classificador Heurístico do Extrato:** Atualização do motor de detecção em `apps/conciliacao/services.py` para mapear extratos automaticamente para as novas categorias oficiais (tarifas, tributos, encargos, combustível, energia/água/internet, salários e receitas).
  - **Homologação:** Suíte completa de 184 testes automatizados do Django executada e aprovada com 100% de sucesso (OK em 79.9s).
- [x] **Blindagem de Saldos de Contas Bancárias no Seeder, Restauração e Ação de Recálculo Automático (PWA v4.29):**
  - **Blindagem Definitiva do Seeder:** Atualização da Seção 6 em `seed_initial_data.py` com checagem `ContaBancaria.all_objects.exists()`, eliminando o risco de o seeder sobrescrever saldos reais de contas bancárias ativas durante sincronizações de dados mestres.
  - **Endpoint de Recálculo de Saldo (`POST /api/contas-bancarias/{id}/recalcular-saldo/`):** Implementação de motor de conciliação no `ContaBancariaViewSet` que audita e soma todas as entradas pagas, subtrai saídas pagas e aplica transferências inter-contas ativas, sincronizando o saldo com as movimentações reais.
  - **Restauração da Conta NUBANK:** Saldo da conta #2 restabelecido com precisão contábil para **R$ 2.100,39** (R$ 10.898,20 de entradas - R$ 8.797,81 de saídas).
  - **Botão 'RECALCULAR' no Frontend:** Ação direta na tabela de Contas Bancárias (`financeiro-view.js`) permitindo ao operador auditar e re-sincronizar o saldo da conta a qualquer momento em 1 clique com feedback visual.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.29` em `frontend/sw.js` e sufixos de cache-busting `?v=4.29` em `frontend/index.html`.
  - **Homologação:** Suíte completa com 185 testes automatizados do Django executados com 100% de aprovação (OK em 71.5s).
- [x] **Responsividade Mobile da Barra de Ferramentas de Conciliação Bancária (PWA v4.30):**
  - **Eliminação do Transbordamento Horizontal:** Substituição de estilos rígidos inline por classes semânticas (`.conciliacao-toolbar-content`, `.conciliacao-conta-group`, `.conciliacao-modos-group`, `.conciliacao-sync-group`, `.conciliacao-acoes-group`) em `industrial-integrity.css` e `conciliacao-view.js`.
  - **Layout Fluido em Duas Linhas no Mobile (`<= 768px`):**
    - Seletor de conta e botões de alternância de modo passam a ocupar 100% da largura em blocos ergonômicos para toque.
    - Os botões secundários contextuais (`⚡ AUTO-MATCH` e `+ LANÇAMENTO RÁPIDO`) dividem a primeira linha com largura igual (`calc(50% - 4px)`).
    - O botão primário de ação (`CONFIRMAR CONCILIAÇÃO` no Modo 1 ou `⚡ GERAR E CONCILIAR EM LOTE` no Modo 2) ocupa a segunda linha isolada com largura total de 100% (`flex: 1 1 100%`), eliminando o truncamento de texto (`CONFIRMA...`) e impedindo estouro de tela.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.30` em `frontend/sw.js` e sufixos de cache-busting `?v=4.30` em `frontend/index.html`.
  - **Homologação:** Suíte completa com 185 testes automatizados do Django executados com 100% de aprovação (OK em 76.1s).
- [x] **Blindagem do Service Worker para Uploads e Operações de Mutação no Celular (PWA v4.31):**
  - **Bypass de Métodos de Mutação no Service Worker:** Implementação de cláusula de escape imediato `if (event.request.method !== 'GET') return;` no listener de `fetch` em `frontend/sw.js`.
  - **Eliminação de Falsos Positivos de Desconexão Offline:** Uploads multipart de extratos bancários (OFX/CSV), documentos de compras e anexos passam a trafegar diretamente pela pilha de rede nativa do navegador móvel (Android/iOS), contornando limitações de streaming do worker thread em redes 4G/5G remotas.
  - **Preservação Integral de Segurança e Cache:** Cookies HttpOnly, cabeçalhos CSRF e tokens continuam sendo transmitidos diretamente pelo navegador, mantendo o cache e a inicialização instantânea para páginas e assets estáticos.
  - **Versionamento PWA:** Cache elevado para `emc-soldas-v4.31` em `frontend/sw.js` e sufixos de cache-busting `?v=4.31` em `frontend/index.html`.
  - **Homologação:** Suíte completa com 185 testes automatizados do Django executados com 100% de aprovação (OK em 80.1s).
- [x] **Anexo de Comprovantes/NFs e Redesign Ultra-Denso da Mesa de Triagem (PWA v4.32):**
  - **Anexo Inline de Documentos na Conciliação:** Adição de suporte ao upload de Notas Fiscais (em Recebimentos) e Comprovantes de Pagamento (em Saídas) diretamente na Mesa de Triagem (`Modo Importação em Lote`). Botão micro-inline `[📎 + NF]` ou `[📎 + RECIBO]` que se converte dinamicamente em badge verde neon `[📎 NF_123.pdf ✕]`, permitindo vincular arquivos PDF, PNG, JPG ou XML a cada transação pré-lançada.
  - **Redesign Arquitetural Ultra-Denso (Eliminação do Descompasso de Altura):** Reorganização dos cards da mesa de triagem em **2 linhas horizontais densas (~72px de altura)**:
    - Linha 1: Título e Data, Valor Formatado (`+ / - R$`), Botão/Badge Inline de Anexo e Botão `✕` de Descarte.
    - Linha 2: Grid horizontal de 3 colunas (`Descrição`, `Meio de Pagamento`, `Categoria DRE`), eliminando o empilhamento vertical e reduzindo a altura do card em mais de 50%, eliminando a discrepância com a coluna do extrato.
  - **Backend & Persistência:** Campos `comprovante` (`FileField`) e `nome_arquivo_comprovante` adicionados a `LancamentoFinanceiro` (Migration `financeiro.0005`), com endpoint `POST /api/conciliacao/upload-comprovante/` e integração no serviço `executar_importacao_lote`.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.32` em `frontend/sw.js` e sufixos de cache-busting `?v=4.32` em `frontend/index.html`.
- [x] **Anexo Universal de Comprovantes na Tesouraria e Modais (PWA v4.33):**
  - **Coluna ANEXO na Tabela do Extrato Real:** Adição da coluna `ANEXO` na listagem do Caixa Real (`financeiro-view.js`). Para movimentações com anexo, exibe badge verde `[📎 NomeArquivo]` que abre/baixa o comprovante diretamente em nova aba; para lançamentos sem anexo, exibe o botão `[📎 + ANEXO]` para upload instantâneo diretamente da linha.
  - **Modais de Lançamento Avulso e Edição:** Campo de seleção de arquivos `<input type="file">` adicionado em `abrirModalNovoLancamento` e `abrirModalEditarLancamento`, efetuando o upload prévio e integrando os caminhos aos payloads de criação (`POST`) e atualização (`PATCH`).
  - **Modal de Transferência Inter-Contas:** Atualizados `TransferenciaInterContasSerializer`, `transferir_inter_contas` e o modal `abrirModalTransferencia`, registrando o comprovante da operação no lançamento de transferência gerado.
  - **Versionamento PWA:** Cache sincronizado para `emc-soldas-v4.33` em `frontend/sw.js` e sufixos de cache-busting `?v=4.33` em `frontend/index.html`.
  - **Homologação:** 38 testes automatizados do Django executados com 100% de sucesso.




### Mapeamento de Funcionalidades do Backend com Views/Telas Pendentes no Frontend
Abaixo estão registradas as entidades que já possuem modelos ORM, validações e rotas de API REST prontas e blindadas no backend, mas que ainda não contam com tela/painel de gestão visual dedicado no frontend (aparecendo atualmente apenas como comboboxes ou subitens):
- [x] **Gestão de Contas Bancárias Corporativas (`apps/financeiro` - `/api/contas-bancarias/`):**
  - *Situação:* **Concluída**. Implementada aba dedicada "CONTAS BANCÁRIAS" no módulo Tesouraria & Caixa (`financeiro-view.js`), com cards de KPI (Saldo Total, Limite Cheque Especial, Disponível Real), listagem de contas, modal de cadastro e edição de saldos/limites, e inativação por soft delete.
- [x] **Gestão de Categorias Financeiras DRE na Administração (`apps/financeiro` - `/api/categorias-financeiras/`):**
  - *Situação:* **Concluída**. Implementada aba dedicada "CATEGORIAS FINANCEIRAS (DRE)" na Central Administrativa (`administracao-view.js`) com suporte a tipos `RECEITA`, `DESPESA`, `AMBOS` (cadastral) e `TRANSFERENCIA`, status Ativo/Inativo, seleção de categoria pai, modal com aviso de governança contábil, e exclusão protegida com bloqueio se houver lançamentos ou subcategorias ativas.
  - *Extrato Real & Tesouraria:* Correção do modal de lançamento avulso no Extrato Real (`status_pagamento='PAGO'`, conta obrigatória e atualização imediata de saldo), resolução da ingestão de chaves `_id` no DRF, filtro dinâmico de categorias em tempo real de acordo com a operação (`SAIDA` -> despesa/ambos; `ENTRADA` -> receita/ambos), coluna de categoria na tabela, busca por categoria e modal de reclassificação/edição de lançamentos.
  - *Permissão:* Acessível por administradores ou colaboradores com permissão `cadastros_financeiros` (leitura liberada para tesouraria).
- [ ] **Gestão de Cartões de Crédito Corporativos & Fechamento de Faturas (`apps/financeiro` - `/api/cartoes/` e `/api/faturas-cartao/`):**
  - *Situação atual:* Tabelas 19 e 20 do FSD. Cartões e faturas mensais modelados no backend, mas geridos hoje apenas via modal auxiliar no lançamento de despesas.
  - *Local sugerido:* Aba dedicada na Tesouraria.
- [ ] **Editor Dedicado de Ficha Técnica / Estrutura de Insumos BOM (`apps/catalogo` - `/api/fichas-tecnicas/`):**
  - *Situação atual:* O cadastro de produtos permite definir itens no modal, mas uma visualização em árvore de composição detalhada e ajuste em lote da receita ainda pode ser expandida.

### Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy
- [ ] Executar suíte de testes automatizados unitários e de integração (`python manage.py test`).
- [ ] Executar Pentest Mandatório de Conclusão (6 testes: RBAC/IDOR, Brute-force, SQLi/XSS, Uploads, Sessão HttpOnly, Criptografia/Tracebacks).
- [ ] **Remoção Mandatória de Configurações Temporárias de Túnel Externo:** Auditar e remover a liberação de CSRF para o wildcard `https://*.trycloudflare.com` em `backend/config/settings.py` antes do deploy definitivo em produção.
- [ ] Disponibilizar script gerador de chaves criptográficas de 64 caracteres (`tools/generate_keys.py`).
- [ ] Elaborar guia de implantação em produção Cloud PaaS.

---

## Próximo Passo Recomendado

Acompanhar e apoiar as verificações e validações do usuário no Frontend PWA. Quando o usuário concluir as verificações visuais e operacionais e solicitar o início da Fase 15, executaremos do zero e formalmente a **Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy**.




