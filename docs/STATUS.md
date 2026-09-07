# STATUS DO PROJETO - EMC SOLDAS

Este documento é um arquivo vivo que registra o estado atual do desenvolvimento, o progresso por fase, o checklist de tarefas e o próximo passo recomendado.

**Última Atualização:** 2026-09-07 (Validações de Usabilidade, Validação Estrita de Placas e Governança de Planejamento)  
**Fase Atual:** Fase 14.5 - Refinamentos de UX, Mobile e Conectividade Operacional (Verificações em andamento no frontend)  
**Próxima Fase:** Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy (Pendente - pronta para início após validações do frontend)  

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

### Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy
- [ ] Executar suíte de testes automatizados unitários e de integração (`python manage.py test`).
- [ ] Executar Pentest Mandatório de Conclusão (6 testes: RBAC/IDOR, Brute-force, SQLi/XSS, Uploads, Sessão HttpOnly, Criptografia/Tracebacks).
- [ ] Disponibilizar script gerador de chaves criptográficas de 64 caracteres (`tools/generate_keys.py`).
- [ ] Elaborar guia de implantação em produção Cloud PaaS.

---

## Próximo Passo Recomendado

Acompanhar e apoiar as verificações e validações do usuário no Frontend PWA. Quando o usuário concluir as verificações visuais e operacionais e solicitar o início da Fase 15, executaremos do zero e formalmente a **Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy**.




