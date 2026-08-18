# PLANO DE CONSTRUÇÃO DO SISTEMA - EMC SOLDAS

Este documento define o roteiro incremental de desenvolvimento do sistema **EMC Soldas**, estruturado com base no Documento de Especificação Funcional (`docs/FSD.md`), no Guia de Identidade Visual (`docs/DESIGN.md`) e no Inventário de Insumos (`docs/INSUMOS.md`).

---

## Sumário das Fases

- [Fase 1 - Infraestrutura, Base do Projeto e Governança de Configuração](#fase-1---infraestrutura-base-do-projeto-e-governança-de-configuração)
- [Fase 2 - Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria](#fase-2---banco-de-dados-modelos-orm-29-entidades-migrations-e-auditoria)
- [Fase 3 - Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC)](#fase-3---autenticação-sessão-jwt-httponly-soft-lock-e-controle-de-acesso-rbac)
- [Fase 4 - Cadastros Estruturais e Dicionários Centrais](#fase-4---cadastros-estruturais-e-dicionários-centrais)
- [Fase 5 - Módulo de Clientes, Fornecedores e Equipamentos](#fase-5---módulo-de-clientes-fornecedores-e-equipamentos)
- [Fase 6 - Catálogo Base, Materiais, Insumos e Produtos (Motor BOM)](#fase-6---catálogo-base-materiais-insumos-e-produtos-motor-bom)
- [Fase 7 - Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos)](#fase-7---módulo-de-compras-notas-fiscais-de-entrada-e-retroalimentação-de-custos)
- [Fase 8 - Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF)](#fase-8---orçamentos-comerciais-snapshot-de-custos-validade-e-geração-pdf)
- [Fase 9 - Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação)](#fase-9---faturamento-agregado-conta-corrente-pré-fatura-fatura-final-e-quitação)
- [Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos](#fase-10---tesouraria-contas-a-pagarreceber-caixa-real-e-cartões-corporativos)
- [Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV)](#fase-11---conciliação-bancária-inteligente-split-screen-ofxcsv)
- [Fase 12 - Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete)](#fase-12---central-administrativa-configurações-globais-smtp-e-lixeira-soft-delete)
- [Fase 13 - Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV)](#fase-13---dashboards-relatórios-estratégicos-e-exportações-pdfcsv)
- [Fase 14 - Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*)](#fase-14---frontend-pwa-client-side-e-interface-completa-industrial-integrity)
- [Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy](#fase-15---bateria-de-testes-integrados-hardening-pentest-de-conclusão-e-deploy)

---

## Fase 1 - Infraestrutura, Base do Projeto e Governança de Configuração

### Objetivo da Fase
Preparar o alicerce técnico da aplicação, organizando o repositório em arquitetura desacoplada (Backend Django REST Framework e Frontend PWA estático), definindo o gerenciamento de dependências, a governança de variáveis de ambiente (`os.environ`), a proteção contra acesso indevido a pastas internas, o sistema de logs físicos rotativos diários com manifesto e o design system inicial.

### Checklist de Tarefas
- [x] Criar estrutura de diretórios do projeto (`backend/`, `frontend/`, `docs/`).
- [x] Criar arquivo de dependências Python (`backend/requirements.txt`).
- [x] Configurar projeto Django (`backend/config/settings.py`, `urls.py`, `wsgi.py`, `asgi.py`) com isolamento seguro, suporte a MySQL, CORS, JWT HttpOnly e Rate Limiting.
- [x] Criar módulo de núcleo (`backend/core/`) com classes base abstratas (`BaseModel` com Soft Delete e Auditoria), middlewares de segurança/exceções e utilitários criptográficos (AES-256 Fernet e validação módulo 11 de CPF).
- [x] Criar estrutura de aplicativos modulares (`apps/authentication`, `apps/cadastros`, `apps/catalogo`, `apps/compras`, `apps/orcamentos`, `apps/faturamento`, `apps/financeiro`, `apps/conciliacao`, `apps/administracao`, `apps/relatorios`).
- [x] Configurar diretório de logs físicos com rotação diária (`backend/logs/`) e proteção NoExec em uploads (`backend/media/`).
- [x] Criar base estática do Frontend PWA (`frontend/index.html`, `manifest.json`, `sw.js`).
- [x] Implementar Design System **Industrial Integrity** (`frontend/assets/css/industrial-integrity.css`, `layout.css`) com tokens de cores, tipografia (IBM Plex Sans, Inter, JetBrains Mono) e cantos retos (0px border-radius).
- [x] Criar arquivos vivos e de contexto (`AGENTS.md`, `docs/PLANO.md`, `docs/STATUS.md`, `docs/ERROS.md`).

### Critérios de Pronto
- Estrutura de pastas criada e desacoplada.
- Arquivos de configuração funcionais sem vazamento de credenciais no repositório.
- Design System básico implementado e aderente ao `docs/DESIGN.md`.
- `AGENTS.md` e arquivos vivos devidamente configurados com caminhos relativos e portáveis.

### Arquivos e Áreas Prováveis
- `backend/requirements.txt`
- `backend/manage.py`
- `backend/config/`
- `backend/core/`
- `backend/apps/`
- `backend/logs/`
- `frontend/`
- `AGENTS.md`
- `docs/PLANO.md`
- `docs/STATUS.md`
- `docs/ERROS.md`

### Observações de Dependência
- Fase fundamental para todas as demais fases.

---

## Fase 2 - Banco de Dados, Modelos ORM (29 Entidades), Migrations e Auditoria

### Objetivo da Fase
Modelar as 29 entidades funcionais do sistema no Django ORM seguindo rigorosamente a convenção técnica de nomenclatura (PascalCase singular para classes, snake_case plural para `db_table`, snake_case para colunas e `{entidade}_id` para FKs), com camada de Soft Delete (100% proibido Hard Delete), campos de auditoria perpétua, constraints de unicidade e matriz estratégica de índices.

### Checklist de Tarefas
- [ ] Implementar classe base `SoftDeleteModel` e `AuditableModel` com `deleted_at`, `deleted_by_id`, `created_at`, `updated_at`, `created_by_id`, `updated_by_id`.
- [ ] Implementar models de Autenticação e Permissões (`Usuario`, `Permissao`).
- [ ] Implementar models de Cadastros Básicos (`ClienteFornecedor`, `Equipamento`, `ClienteEquipamento`, `AnexoGeralCliente`).
- [ ] Implementar models do Dicionário e Catálogo (`DicionarioUom`, `DicionarioAtributo`, `Item`, `ItemAtributoValor`, `Produto`, `FichaTecnica`).
- [ ] Implementar models de Operação Comercial (`Orcamento`, `OrcamentoItem`, `OrcamentoPropostaPagamento`).
- [ ] Implementar models de Faturamento e Conta Corrente (`Fatura`, `FaturaPropostaPagamento`).
- [ ] Implementar models de Tesouraria e Estrutura Financeira (`LancamentoFinanceiro`, `ContaBancaria`, `CartaoCredito`, `FaturaCartao`, `CategoriaFinanceira`, `MeioPagamento`, `RegraPagamento`, `LogEstorno`).
- [ ] Implementar models de Compras e Entradas (`DocumentoFiscalCompra`, `NotaCompraItem`).
- [ ] Implementar models de Governança e Configurações Globais (`ConfiguracaoGlobal`, `ControleArquivoLog`).
- [ ] Configurar índices adicionais B-Tree sobre campos de identificação única, autocompletes, datas e status.
- [ ] Configurar as 7 `UniqueConstraints` mandatórias (item-atributo, produto-item BOM, nota-item, cartão-mês, orçamento-regra, fatura-regra, etc.).
- [ ] Gerar e versionar migrations iniciais do Django (`python manage.py makemigrations`).
- [ ] Criar seeders/fixtures iniciais para `DicionarioUom`, `DicionarioAtributo`, `MeiosPagamento`, `CategoriasFinanceiras` e `ConfiguracaoGlobal` inicial (id=1).

### Critérios de Pronto
- As 29 entidades mapeadas com fidelidade total aos tipos, colunas e relacionamentos do FSD.
- Migrations geradas e aplicáveis sem erros no MySQL (`python manage.py migrate`).
- Soft delete ativo em todas as entidades elegíveis, bloqueando sumariamente `DELETE` físico.
- Constraints e índices criados no banco.

### Arquivos e Áreas Prováveis
- `backend/core/models.py`
- `backend/apps/*/models.py`
- `backend/apps/*/migrations/`
- `backend/core/management/commands/seed_initial_data.py`

### Observações de Dependência
- Depende da Fase 1.

---

## Fase 3 - Autenticação, Sessão (JWT HttpOnly), Soft Lock e Controle de Acesso (RBAC)

### Objetivo da Fase
Construir o ecossistema de autenticação segura baseado em JWT armazenado em Cookie HttpOnly (`SameSite=Strict`), Soft Lock por ociosidade (30 minutos) com destravamento por PIN de 6 dígitos (ou WebAuthn), Hard Lock por tentativas excessivas/expiração, Onboarding de usuários via convite seguro por e-mail, Recuperação de senha por código de 8 dígitos, Proteção Anti-Bruteforce com bloqueio temporário e Matriz de Permissões com 10 Toggles Dinâmicos aplicados no Backend.

### Checklist de Tarefas
- [ ] Implementar autenticação customizada com suporte a `Usuario` (e-mail, senha com hash PBKDF2/Argon2, PIN de 6 dígitos em `pin_hash`).
- [ ] Implementar emissão e leitura de JWT via Cookie de Sessão HttpOnly com defesa CSRF (`X-CSRFToken`).
- [ ] Criar endpoints de autenticação:
  - `POST /api/auth/login/` (com proteção anti-bruteforce: 5 tentativas falhas = bloqueio de 1 hora).
  - `POST /api/auth/logout/` (invalidação de tokens e destruição do cookie).
  - `POST /api/auth/set-pin/` (cadastro e alteração do PIN de 6 dígitos).
  - `POST /api/auth/unlock-pin/` (destravamento do Soft Lock, com trava de 3 erros levando ao Hard Lock).
  - `POST /api/auth/forgot-password/` (envio de código de 8 dígitos com validade de 30 min via SMTP/console).
  - `POST /api/auth/reset-password/` (redefinição de senha com validação do código).
- [ ] Implementar onboarding de colaboradores (`POST /api/usuarios/convidar/`) gerando link seguro para criação da senha própria.
- [ ] Implementar endpoint de desbloqueio manual pelo Admin (`POST /api/usuarios/{id}/desbloquear/`).
- [ ] Construir classes de permissão do DRF (`HasPermissionToggle`) para validar os 10 toggles dinâmicos no backend.
- [ ] Implementar middleware para capturar o usuário autenticado da sessão e injetar automaticamente em `created_by_id`, `updated_by_id` e `deleted_by_id`.

### Critérios de Pronto
- Login via Cookie HttpOnly funcional.
- Soft Lock com PIN de 6 dígitos operacional e Hard Lock após 3 erros.
- Onboarding e recuperação de senha disparando e-mails (com fallback seguro para console em dev).
- RBAC com 10 toggles validado no backend retornando 403 Forbidden para acessos não autorizados.

### Arquivos e Áreas Prováveis
- `backend/apps/authentication/`
- `backend/core/permissions.py`
- `backend/core/middleware.py`

### Observações de Dependência
- Depende da Fase 2.

---

## Fase 4 - Cadastros Estruturais e Dicionários Centrais

### Objetivo da Fase
Desenvolver os endpoints de CRUD e regras de negócio para os cadastros estruturais da oficina: Dicionário UOM (Unidades de Medida), Dicionário de Atributos Técnicos, Categorias Financeiras (Árvore Hierárquica), Contas Bancárias (com Cheque Especial), Meios de Pagamento (com flag para taxa de maquininha) e Regras de Pagamento (Matriz de Condições Comerciais, Prazos, Parcelamentos e Descontos).

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `DicionarioUom` (`/api/dicionario-uom/`).
- [ ] Criar serializers, viewsets e rotas para `DicionarioAtributo` (`/api/dicionario-atributos/`).
- [ ] Criar serializers, viewsets e rotas para `CategoriaFinanceira` (`/api/categorias-financeiras/`) com suporte a árvore pai/filho e classificação (Receita, Despesa, Transferência).
- [ ] Criar serializers, viewsets e rotas para `ContaBancaria` (`/api/contas-bancarias/`) com saldo e `limite_credito` (cheque especial).
- [ ] Criar serializers, viewsets e rotas para `MeioPagamento` (`/api/meios-pagamento/`) com flag `permite_taxa_maquininha`.
- [ ] Criar serializers, viewsets e rotas para `RegraPagamento` (`/api/regras-pagamento/`) suportando `A_VISTA`, `A_PRAZO`, `PARCELADO`, prazos em dias, intervalo de parcelas e desconto sugerido.
- [ ] Garantir aplicação do Soft Delete e auditoria em todos os cadastros estruturais.
- [ ] Proteger endpoints via toggles de permissão (`gestao_dicionario_uom` e `cadastros_financeiros`).

### Critérios de Pronto
- Endpoints REST operacionais e testados via DRF.
- Seeders populando dados básicos padrão.
- Validações de soft delete e permissões ativas.

### Arquivos e Áreas Prováveis
- `backend/apps/cadastros/`
- `backend/apps/financeiro/`

### Observações de Dependência
- Depende da Fase 3.

---

## Fase 5 - Módulo de Clientes, Fornecedores e Equipamentos

### Objetivo da Fase
Implementar o gerenciamento completo de Clientes e Fornecedores (PF/PJ), com hierarquia visual e validação antecipada de CPF (módulo 11), integração com API pública de CNPJ (BrasilAPI/ReceitaWS) com fallback gracioso, blindagem anti-duplicação de CPF/CNPJ, cadastro rápido simplificado (Nome + Telefone) e gerenciamento de Equipamentos com histórico de transferências de clientes (`ClienteEquipamento`).

### Checklist de Tarefas
- [ ] Criar rota proxy utilitária backend para consulta de CNPJ (`GET /api/utilitarios/consulta-cnpj/{cnpj}/`).
- [ ] Implementar validação matemática de CPF (módulo 11) no backend e checagem de duplicidade no `onBlur`/serializer.
- [ ] Criar serializers, viewsets e rotas para `ClienteFornecedor` (`/api/clientes-fornecedores/`):
  - Suporte a PF e PJ.
  - Cadastro rápido ágil (exigindo apenas `nome_razao` e `telefone`).
  - Histórico de compras para fornecedores e histórico financeiro/inadimplência para clientes.
- [ ] Criar serializers, viewsets e rotas para `Equipamento` (`/api/equipamentos/`) e `ClienteEquipamento` (`/api/cliente-equipamentos/`).
- [ ] Implementar lógica de transferência de equipamentos com registro de `data_vinculo` e flag `is_ativo`, preservando orçamentos passados.
- [ ] Criar endpoints para anexos de clientes (`/api/anexos-gerais-clientes/`) com validação de MIME-type profundo.

### Critérios de Pronto
- CRUD completo de Clientes, Fornecedores e Equipamentos funcional.
- Consulta pública de CNPJ operacional com tratamento de falhas.
- Validação e unicidade estrita de CPF/CNPJ.
- Histórico de transferência de equipamentos preservando vínculos anteriores.

### Arquivos e Áreas Prováveis
- `backend/apps/cadastros/`
- `backend/core/utils.py`

### Observações de Dependência
- Depende da Fase 4.

---

## Fase 6 - Catálogo Base, Materiais, Insumos e Produtos (Motor BOM)

### Objetivo da Fase
Construir o motor de custos e composição de produtos da oficina, abrangendo o cadastro de Itens/Matéria-Prima (com atributos técnicos dinâmicos, fatores de conversão entre unidades de compra e consumo, e registro de último custo de compra) e Produtos (com tempo de mão de obra e Ficha Técnica BOM calculando o Preço de Custo Apurado em tempo real).

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `Item` (`/api/itens/`) com vínculos a `DicionarioUom` (compra e consumo) e `fator_conversao`.
- [ ] Implementar sub-recurso integrado para `ItemAtributoValor` (`/api/item-atributos-valores/`) com `UniqueConstraint(item_id, atributo_id)`.
- [ ] Criar serializers, viewsets e rotas para `Produto` (`/api/produtos/`) com tempo estimado de mão de obra (`tempo_estimado_execucao`).
- [ ] Implementar Ficha Técnica BOM (`FichaTecnica` - `/api/fichas-tecnicas/`) com cálculo dinâmico do `Preço de Custo Apurado` (soma do custo fracionado dos materiais + taxa horária de mão de obra global).
- [ ] Bloquear soft delete de Itens caso constem em receitas de Produtos ativos.
- [ ] Aplicar permissão `gestao_catalogo` sobre os endpoints.

### Critérios de Pronto
- Cadastro de Itens com atributos e fator de conversão operacional.
- Criação de Produtos com Ficha Técnica BOM calculando custo composto com precisão matemática.
- Travas de integridade para exclusão lógica de insumos em uso.

### Arquivos e Áreas Prováveis
- `backend/apps/catalogo/`

### Observações de Dependência
- Depende das Fases 4 e 5.

---

## Fase 7 - Módulo de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos)

### Objetivo da Fase
Implementar o registro de Notas Fiscais de Compra (`DocumentoFiscalCompra` e `NotaCompraItem`), com upload seguro de arquivos físicos (XML/PDF) para arquivamento e mecanismo automático de retroalimentação de custos que atualiza o `ultimo_custo_compra` dos Itens do catálogo e registra a linha do tempo de preços sem gerar títulos automáticos no financeiro (isolamento V1).

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `DocumentoFiscalCompra` (`/api/documentos-fiscais-compra/`).
- [ ] Criar sub-recurso de itens da nota (`NotaCompraItem` - `/api/nota-compra-itens/`).
- [ ] Implementar rotina de retroalimentação automática: ao salvar a nota, atualizar `Item.ultimo_custo_compra` e `Item.data_ultima_compra`.
- [ ] Configurar upload seguro de XML/PDF com validação de extensão e MIME-type real.
- [ ] Implementar consulta do histórico de preços de fornecedores por item.
- [ ] Aplicar permissão `acesso_compras` nas rotas do módulo.

### Critérios de Pronto
- Registro de compras manual com múltiplos itens funcional.
- Retroalimentação automática de custos no Catálogo de Itens comprovada.
- Histórico de aquisições auditável.

### Arquivos e Áreas Prováveis
- `backend/apps/compras/`

### Observações de Dependência
- Depende da Fase 6.

---

## Fase 8 - Orçamentos Comerciais (Snapshot de Custos, Validade e Geração PDF)

### Objetivo da Fase
Desenvolver o núcleo operacional da oficina para criação ágil de Orçamentos com suporte a 3 tipos de linhas (Produtos compostos, Itens simples e Lançamentos manuais livres), persistência de Snapshots de custos e preços de venda, acompanhamento de Status Duplo (Operacional vs Financeiro), controle de Validade com Alerta de Inflação na renovação, proteção contra inadimplência preventiva, cancelamento com justificativa obrigatória (mínimo 10 caracteres) e exportação em PDF profissional com desconto oculto quando zerado.

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `Orcamento` (`/api/orcamentos/`) e `OrcamentoItem` (`/api/orcamento-itens/`).
- [ ] Implementar gravação de Snapshots (`custo_snapshot` e `valor_venda_snapshot`) na inclusão de itens e produtos.
- [ ] Implementar propostas de pagamento do orçamento (`OrcamentoPropostaPagamento`).
- [ ] Implementar máquina de estados operacional (`Gerado`, `Enviado`, `Aprovado`, `Em Execução`, `Concluído`, `Cancelado`) e financeira (`A Faturar`, `Faturado`, `Pago`, `Cancelado`).
- [ ] Implementar alerta visual/preventivo de cliente com títulos em atraso.
- [ ] Implementar motor de Renovação de Orçamento com comparação entre o Snapshot gravado e o custo atual do catálogo (alerta de inflação).
- [ ] Implementar endpoint de cancelamento de orçamento (`POST /api/orcamentos/{id}/cancelar/`) com exigência de justificativa textual (mínimo 10 caracteres) e disparo de log de auditoria.
- [ ] Implementar serviço de geração de PDF do Orçamento, suprimindo menção a descontos quando o valor for zero ou nulo.
- [ ] Aplicar permissão `acesso_comercial` sobre as rotas.

### Critérios de Pronto
- Elaboração de orçamentos com os 3 tipos de itens operacional.
- Snapshots imutáveis gravados com sucesso.
- Renovação com alerta de inflação testada.
- Cancelamento justificado gravado em log e banco.
- Geração de PDF transacional validada.

### Arquivos e Áreas Prováveis
- `backend/apps/orcamentos/`
- `backend/core/reports/`

### Observações de Dependência
- Depende das Fases 6 e 7.

---

## Fase 9 - Faturamento Agregado (Conta Corrente, Pré-Fatura, Fatura Final e Quitação)

### Objetivo da Fase
Implementar o fluxo financeiro de faturamento agregado da oficina através da máquina de estados em cascata: Fase 1 (Pré-Fatura/Rascunho aglutinando orçamentos prontos com simulação de propostas e PDF Espelho sem gerar títulos no Contas a Receber); Fase 2 (Fatura Final com escolha da forma de pagamento, transição automática dos orçamentos para `FATURADO` e geração das parcelas a receber); Fase 3 (Quitação Total com transição para `PAGA` ao atingir 100% de amortização); além de cancelamento de fatura com desvinculação em cascata e suporte a cortesia (100% de desconto).

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `Fatura` (`/api/faturas/`) e `FaturaPropostaPagamento` (`/api/fatura-propostas-pagamento/`).
- [ ] Implementar endpoint para listagem da Conta Corrente do Cliente (orçamentos em status `CONCLUÍDO` / `A FATURAR`).
- [ ] Implementar fluxo de Pré-Fatura (Rascunho): aglutinação de N orçamentos, seleção de opções sugeridas de pagamento e geração do PDF Espelho da Pré-Fatura.
- [ ] Implementar conversão de Pré-Fatura em Fatura Final (`POST /api/faturas/{id}/faturar/`):
  - Vinculação obrigatória da `regra_pagamento_id` e desconto final.
  - Transição de status da fatura para `FATURADA`.
  - Transição em cascata do status financeiro dos orçamentos para `FATURADO`.
  - Geração automática das parcelas em `LancamentoFinanceiro` (Contas a Receber) com datas calculadas pela regra de pagamento.
- [ ] Implementar cancelamento de faturas (`POST /api/faturas/{id}/cancelar/`) com justificativa obrigatória, reversão dos orçamentos para `A FATURAR` e anulação das parcelas a vencer.
- [ ] Implementar verificação de Quitação 100%: transição automática da fatura para `PAGA` e dos orçamentos vinculados para `PAGO` quando a soma das baixas liquidar a dívida total.
- [ ] Implementar suporte a quitação em Cortesia (desconto de 100%) registrando histórico comercial sem afetar o caixa real.

### Critérios de Pronto
- Ciclo completo de faturamento (Rascunho ➔ Faturada ➔ Paga) validado com integridade total.
- Parcelas no Contas a Receber geradas com as datas corretas.
- Cancelamento em cascata revertendo estados de orçamentos perfeitamente.

### Arquivos e Áreas Prováveis
- `backend/apps/faturamento/`
- `backend/apps/financeiro/`

### Observações de Dependência
- Depende da Fase 8.

---

## Fase 10 - Tesouraria, Contas a Pagar/Receber, Caixa Real e Cartões Corporativos

### Objetivo da Fase
Desenvolver o módulo financeiro e de tesouraria da empresa, separando estritamente o Regime de Competência (Contas a Pagar e Contas a Receber com títulos `A Vencer` sem afetar saldo bancário) do Regime de Caixa (Extrato Real com títulos `Pago` impactando imediatamente a `ContaBancaria`), com Modal Universal de Liquidação (incluindo cálculo automático de Taxa de Maquininha), Transferências Inter-Contas, Bloqueio por Limite de Cheque Especial, Cartões Corporativos com Rollover e fluxo de Estorno com gravação perpétua em `LogEstorno`.

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `LancamentoFinanceiro` (`/api/lancamentos-financeiros/`) cobrindo Contas a Pagar, Contas a Receber e Extrato de Caixa.
- [ ] Implementar endpoint universal de liquidação (`POST /api/lancamentos-financeiros/{id}/liquidar/` e `POST /api/faturas/{id}/receber/`):
  - Validação de saldo da conta bancária e bloqueio caso ultrapasse o `limite_credito` (cheque especial).
  - Cálculo automático de Taxa de Maquininha: entrada do valor bruto + saída automática da despesa de taxa na conta, impactando o saldo líquido real.
- [ ] Implementar cancelamento de títulos a vencer (`status_pagamento = 'Cancelado'`) com justificativa obrigatória.
- [ ] Implementar fluxo de Estorno para títulos já pagos (`POST /api/lancamentos-financeiros/{id}/estornar/`):
  - Reversão do saldo bancário.
  - Gravação imutável da justificativa em `LogEstorno` (`/api/log-estornos/`).
- [ ] Implementar Transferência Inter-Contas (`/api/lancamentos-financeiros/transferir/`) sem impacto no DRE.
- [ ] Implementar sub-módulo de Cartões Corporativos (`CartaoCredito` e `FaturaCartao`):
  - Lançamento de despesas na fatura aberta sem debitar conta bancária.
  - Fechamento de fatura e geração de título a pagar.
  - Rollover automático de saldo devedor remanescente para o mês seguinte.
- [ ] Proteger endpoints via permissão `acesso_tesouraria`.

### Critérios de Pronto
- Contas a Pagar, Contas a Receber e Extrato operando com respeito aos regimes de competência e caixa.
- Baixa com taxa de maquininha gerando receita bruta, despesa de taxa e saldo líquido exato.
- Bloqueio por cheque especial e estorno auditado funcionando.
- Gestão de cartões corporativos com rollover validada.

### Arquivos e Áreas Prováveis
- `backend/apps/financeiro/`

### Observações de Dependência
- Depende das Fases 4 e 9.

---

## Fase 11 - Conciliação Bancária Inteligente Split-Screen (OFX/CSV)

### Objetivo da Fase
Implementar o motor e as interfaces de Conciliação Bancária Split-Screen, suportando upload e parsing de arquivos de extrato bancário nos formatos OFX e CSV, matching automático 1:1 por valor e proximidade de data (±3 dias), matching múltiplo (1:N), criação instantânea de despesas não previstas no ato (`[Lançamento Rápido no Ato]`), troca rápida de conta bancária e estornos, gravando compulsoriamente `is_conciliado = True`, data e operador responsável.

### Checklist de Tarefas
- [ ] Criar serviço de parsing seguro para arquivos de extrato bancário em formato OFX e CSV (`/api/conciliacao/upload-extrato/`).
- [ ] Implementar algoritmo de correspondência:
  - Match Automático 1:1 (valor idêntico e data ±3 dias).
  - Match Múltiplo (agrupamento de múltiplos títulos para uma transação bancária).
- [ ] Implementar endpoint de conciliação (`POST /api/conciliacao/confirmar/`) que atualiza `is_conciliado = True`, `data_conciliacao = NOW()` e `conciliado_por_id = request.user.id`.
- [ ] Implementar funcionalidade de `Lançamento Rápido no Ato` (`POST /api/conciliacao/lancamento-rapido/`) para tarifas/rendimentos do extrato com conciliação imediata.
- [ ] Implementar geração de dados para o Relatório de Divergências de Conciliação (Sobras do Extrato vs Sobras do ERP).

### Critérios de Pronto
- Upload e parsing de OFX e CSV funcionando com tratamento de erros.
- Matching 1:1 e múltiplo sugerindo correspondências adequadas.
- Lançamento rápido no ato e confirmação gravando trilha de auditoria completa.

### Arquivos e Áreas Prováveis
- `backend/apps/conciliacao/`

### Observações de Dependência
- Depende da Fase 10.

---

## Fase 12 - Central Administrativa, Configurações Globais, SMTP e Lixeira (Soft Delete)

### Objetivo da Fase
Construir a Central do Administrador contemplando: Parâmetros Globais da Empresa (dados cadastrais, taxa de mão de obra por hora, validade de orçamentos com não-retroatividade), Gestão de Retenção de Logs com manifesto TTL (`ControleArquivoLog`), Serviço Dinâmico de SMTP com credenciais criptografadas (AES-256 Fernet) e teste em tempo real, Gestão de Equipe com os 10 Toggles Dinâmicos de permissão e desbloqueio anti-bruteforce, Log Viewer do servidor e Painel de Lixeira e Restauração (Lixeira Global para o Admin e Minha Lixeira para o Operador).

### Checklist de Tarefas
- [ ] Criar serializers, viewsets e rotas para `ConfiguracaoGlobal` (`/api/configuracoes-globais/`):
  - Criptografia simétrica AES-256 da senha SMTP no banco (`smtp_password_encrypted`).
  - Endpoint de teste de disparo SMTP em tempo real (`POST /api/configuracoes-globais/testar-smtp/`).
  - Não-retroatividade de alterações de taxa horária e validade de orçamentos.
- [ ] Criar rotina de expurgo de logs gerenciada pela tabela `ControleArquivoLog` (`/api/controle-arquivos-log/`).
- [ ] Implementar Log Viewer do servidor para visualização segura de arquivos diários (`logs/app-YYYY-MM-DD.log`) pelo Admin.
- [ ] Implementar gestão de colaboradores e permissões (`/api/usuarios/` e `/api/permissoes/`) com os 10 toggles dinâmicos.
- [ ] Implementar Painel de Lixeira e Restauração (`/api/lixeira/`):
  - Listagem com filtros por entidade, data e usuário autor.
  - Endpoint `POST /api/lixeira/{entidade}/{id}/restaurar/` (revertendo `deleted_at = NULL`).
  - Isolamento de visão: Admin enxerga Lixeira Global; Operador enxerga apenas "Minha Lixeira" (`deleted_by_id = request.user.id`).
- [ ] Aplicar permissões `configuracoes_globais`, `gestao_equipe` e `auditoria_logs_recovery`.

### Critérios de Pronto
- Configurações globais salvas e protegidas no banco com AES-256.
- Teste de SMTP funcionando (com fallback seguro para console).
- Gestão de equipe e controle dos 10 toggles dinâmicos operacional.
- Log Viewer e Lixeira com restauração lógica funcionando para Admin e Operador.

### Arquivos e Áreas Prováveis
- `backend/apps/administracao/`
- `backend/core/utils.py`

### Observações de Dependência
- Depende das Fases 3 e 10.

---

## Fase 13 - Dashboards, Relatórios Estratégicos e Exportações (PDF/CSV)

### Objetivo da Fase
Desenvolver os endpoints de agregação para o Dashboard de Flip Cards (Operação, Faturamento, Receita, Caixa e Alertas), Gráficos de Receitas x Despesas, Feed de Atividades Recentes, e a Central de Relatórios Estratégicos da oficina: Painel de Inadimplência, Dossiê do Cliente, Curva ABC de Clientes, Curva ABC de Consumo de Itens, DRE Simplificado e Relatório de Divergências de Conciliação com exportação em PDF e CSV.

### Checklist de Tarefas
- [ ] Criar endpoint consolidado para o Dashboard (`GET /api/dashboard/flip-cards/` e `/api/dashboard/graficos/`):
  - Cards: Operação, Faturamento, Receita (Real vs Projetado), Caixa (Real vs Projetado) e Alertas (Vencidas, Vencendo Hoje, Próximos 7 dias).
  - Filtros temporais rápidos ("Este Mês", "Mês Passado", "Este Ano").
- [ ] Implementar Relatório de Inadimplência (`/api/relatorios/inadimplencia/`).
- [ ] Implementar Dossiê do Cliente (`/api/relatorios/dossie-cliente/{id}/`) separando materiais de reformas.
- [ ] Implementar Curva ABC de Clientes e Curva ABC de Itens (`/api/relatorios/curva-abc/`).
- [ ] Implementar DRE Simplificado (`/api/relatorios/dre/`) agrupado por Categoria Financeira.
- [ ] Implementar Relatório de Divergências de Conciliação (`/api/relatorios/divergencias-conciliacao/`) em duas abas (sobras de extrato vs sobras de ERP).
- [ ] Implementar geradores de exportação em **PDF** e **CSV** para todos os relatórios estratégicos.
- [ ] Aplicar rate limit preventivo de 5 req/min (`ScopedRateThrottle: heavy_reports`) sobre endpoints pesados de exportação.

### Critérios de Pronto
- Agregações do dashboard retornando números consolidados rápidos via banco indexado.
- Relatórios estratégicos gerando dados higienizados e exportações em PDF e CSV perfeitas.
- Throttle de relatórios ativo e protegendo a infraestrutura.

### Arquivos e Áreas Prováveis
- `backend/apps/relatorios/`
- `backend/core/reports/`

### Observações de Dependência
- Depende das Fases 8, 9, 10 e 11.

---

## Fase 14 - Frontend PWA Client-Side e Interface Completa (*Industrial Integrity*)

### Objetivo da Fase
Construir e integrar a interface de usuário do Frontend PWA completa em Vanilla JS, HTML5 e CSS puro baseado no Design System **Industrial Integrity** (`docs/DESIGN.md`), com navegação por Sidebar retrátil, tabelas com filtros combinados e busca em tempo real nos cabeçalhos, Flip Cards interativos no Dashboard, modais ágeis de cadastro com validação de CPF/CNPJ no topo (`onBlur`), modal universal de liquidação, tela split-screen de conciliação bancária, modais de justificativa obrigatória (mínimo 10 caracteres) para cancelamentos/estornos, tratamento visual híbrido de permissões (ocultação de menus e bloqueio com cadeado `[🔒]` em cards), e Service Worker com cache e resiliência offline.

### Checklist de Tarefas
- [ ] Implementar estrutura SPA/PWA com roteador client-side em Vanilla JS e Service Worker (`sw.js`).
- [ ] Construir layout base: Sidebar retrátil, Topbar, Barra de status de conexão (online/offline) e Container Dinâmico.
- [ ] Desenvolver telas públicas de Acesso: Login, Esqueci minha senha, Criação de Senha e Modal de Desbloqueio por PIN de 6 dígitos (Soft Lock).
- [ ] Desenvolver Dashboard Principal com os 5 Flip Cards interativos (com botões de rodapé `Ver detalhes ➔` de clique isolado), gráficos e atalhos rápidos.
- [ ] Desenvolver telas do Módulo Operacional:
  - Listagem de Orçamentos e Faturas com filtros avançados e buscas inline.
  - Tela de Elaboração de Orçamento com Resumo Lateral Fixo e Modal de Cadastro Rápido de Cliente/Veículo.
  - Formulário de Cliente/Fornecedor com CPF/CNPJ no topo absoluto, validação matemática e botão `[Buscar CNPJ]`.
  - Tela de Faturamento Agregado (Conta Corrente, Pré-Fatura com propostas e Fatura Final com conversão em 1 clique).
  - Modal de Cancelamento com justificativa obrigatória (mínimo 10 caracteres).
- [ ] Desenvolver telas da Tesouraria e Conciliação:
  - Listagens de Contas a Pagar, Contas a Receber e Extrato de Caixa Real.
  - Modal Universal de Liquidação com taxa de maquininha.
  - Tela de Conciliação Bancária Split-Screen (Extrato OFX/CSV à esquerda, ERP à direita, botões de match, lançamento rápido no ato e estorno).
  - Linha do tempo de Cartões Corporativos.
- [ ] Desenvolver telas de Compras e Catálogo:
  - Registro de Notas de Entrada com upload de XML/PDF e itens manuais.
  - Cadastro de Itens com atributos dinâmicos e Produtos com sub-grid de Ficha Técnica BOM.
  - Interface de Equipamentos com histórico de proprietários.
- [ ] Desenvolver Central do Administrador:
  - Telas em abas para Cadastros Financeiros e Dicionário UOM/Atributos.
  - Painel de Configurações Globais (Empresa, Mão de Obra, Prazos e SMTP com teste em tempo real).
  - Gestão de Equipe com os 10 Toggles Dinâmicos e botão de desbloqueio de contas.
  - Log Viewer do servidor e Painel de Lixeira (Lixeira Global vs Minha Lixeira com botão `[Restaurar]`).
- [ ] Desenvolver Central Analítica com visualização e exportação (PDF/CSV) de todos os relatórios estratégicos.
- [ ] Aplicar padrão de cantos retos (0px border-radius), paleta de cores (Dark Iron, Steel Gray, Rust Orange) e tipografia (IBM Plex Sans, Inter, JetBrains Mono) em 100% dos componentes.

### Critérios de Pronto
- Aplicação PWA navegável, responsiva em Desktop e Mobile, consumindo 100% das APIs REST.
- Identidade visual estritamente alinhada ao `docs/DESIGN.md`.
- Soft Lock com PIN destravando a aplicação perfeitamente.
- Todos os fluxos operacionais e transacionais integrados de ponta a ponta.

### Arquivos e Áreas Prováveis
- `frontend/`
- `frontend/assets/css/`
- `frontend/assets/js/`

### Observações de Dependência
- Depende de todas as fases de backend (Fases 1 a 13).

---

## Fase 15 - Bateria de Testes Integrados, Hardening, Pentest de Conclusão e Deploy

### Objetivo da Fase
Executar a bateria completa de testes automatizados locais (unitários, integração e cascatas de estado), validação visual de usabilidade multi-dispositivo, bateria de testes de invasão e segurança (Pentest de Conclusão com 6 testes mandatórios do FSD) e preparação dos scripts de apoio para deploy seguro em ambiente Cloud PaaS (Render, PythonAnywhere, etc.).

### Checklist de Tarefas
- [ ] Executar suíte de testes unitários e de integração no backend (`python manage.py test`).
- [ ] Validar cobertura de máquinas de estado e cascatas financeiras (Orçamentos ➔ Pré-Fatura ➔ Fatura Final ➔ Baixa com Taxa de Maquininha ➔ Quitação 100% ➔ Estorno/Cancelamento).
- [ ] Executar Pentest Mandatório de Conclusão:
  - **Teste 1 (RBAC/IDOR):** Tentar acessar rotas de Admin com token de Operador (verificar 403 Forbidden).
  - **Teste 2 (Anti-Bruteforce & Throttling):** Simular 6 falhas consecutivas de login (verificar bloqueio de 1h) e rajada em relatórios (verificar 429 Too Many Requests).
  - **Teste 3 (SQLi & XSS):** Injetar payloads maliciosos em buscas, autocompletes e justificativas textuais (validar sanitização estrita).
  - **Teste 4 (Uploads Maliciosos):** Tentar upload de executáveis renomeados (verificar bloqueio por MIME-type profundo).
  - **Teste 5 (Sessão & Cookie HttpOnly):** Validar invisibilidade do JWT via JavaScript (`document.cookie`) e Soft Lock após 30 min.
  - **Teste 6 (Criptografia & Logs):** Verificar credenciais SMTP cifradas em AES-256 e não-vazamento de Tracebacks em erros 500.
- [ ] Criar script de apoio gerador de chaves criptográficas de 64 caracteres (`tools/generate_keys.py`) para `SECRET_KEY` e `ENCRYPTION_KEY`.
- [ ] Elaborar guia de deploy assistido para Cloud PaaS sem exposição de segredos.

### Critérios de Pronto
- 100% dos testes automatizados passando com sucesso.
- Pentest com os 6 testes de invasão aprovados sem vulnerabilidades.
- Sistema homologado e pronto para implantação em produção.

### Arquivos e Áreas Prováveis
- `backend/tests/`
- `tools/`
- `docs/STATUS.md`

### Observações de Dependência
- Depende da Fase 14.
