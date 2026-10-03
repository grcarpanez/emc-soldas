# Plano de Implementação - Paginação do Extrato Real (Caixa Real) e Padronização na Tesouraria

**Data:** 2026-10-03  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação (Proceed):** Aprovado pelo usuário em 2026-10-03 01:16:32 com a mensagem: *"Execute o plano, por favor"*  

---

## 1. Contexto e Objetivos

### 1.1 Contexto da Demanda
O usuário relatou que a visualização do **Extrato Real (Caixa Real)** na tela de Tesouraria (`/financeiro/`) possui um limite rígido de itens e não permite visualizar todo o histórico de movimentações financeiras liquidadas (`PAGO`).

O usuário destacou dois requisitos essenciais:
1. **Não carregar todos os lançamentos de uma só vez**, preservando o desempenho de carregamento da página e consumo de rede;
2. **Implementar Paginação explícita** como abordagem preferida (em vez de rolagem infinita/carga progressiva), garantindo conferência auditável com extratos bancários, controle de páginas e estabilidade no scroll ao interagir com modais de edição, estorno e comprovantes.

### 1.2 Diagnóstico Técnico
1. **Backend:** No Django REST Framework (DRF), `REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS']` está definido como `rest_framework.pagination.PageNumberPagination` com `PAGE_SIZE = 25`. Por padrão no DRF, `page_size_query_param` é `None`, o que ignora qualquer tentativa do cliente de especificar a quantidade de itens por página (`?page_size=50`).
2. **Frontend:** No arquivo `frontend/assets/js/views/financeiro-view.js`:
   - A função `carregarListaExtrato()` faz uma requisição simples sem o parâmetro `page`;
   - O array consumido é limitado aos 25 primeiros itens (`res.results`);
   - O contador de total no badge (`#total-extrato-badge`) é preenchido com `lista.length` (máximo 25) em vez do total real retornado pelo backend (`res.count`);
   - Não há controles visuais de paginação (botões de anterior, próxima, números de página, seletor de linhas por página);
   - A ordenação não estava explicitamente fixada em ordem cronológica de liquidação decrescente (`-data_pagamento, -id`).
3. **Consistência do Módulo de Tesouraria:** As abas adjacentes **Contas a Pagar** e **Contas a Receber** sofrem da mesma limitação de estarem travadas nos 25 primeiros registros da primeira página.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend: Paginação Padrão com `page_size` Configurável (`backend/core/pagination.py`)
Criar uma classe centralizada de paginação no módulo `core`:
```python
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000
```
- **Configuração no Django Settings (`backend/config/settings.py`):**
  Definir `REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'] = 'core.pagination.StandardResultsSetPagination'`.
- **Benefícios:**
  - Suporte completo a `?page=N` e `?page_size=N` em todas as rotas paginadas;
  - Limite seguro de `max_page_size = 1000`, viabilizando chamadas já existentes em outros módulos (ex: seletores de clientes/produtos em orçamentos) sem quebrar o teto operacional;
  - Resposta padrão do DRF contendo `count`, `next`, `previous` e `results`.

### 2.2 Frontend: Utilitário Centralizado de Paginação Industrial (`frontend/assets/js/utils.js`)
Criar o helper global `window.EMCUtils.renderPagination` para padronizar controles de paginação em toda a SPA:
- **Assinatura:**
  ```javascript
  window.EMCUtils.renderPagination({
    container,          // HTMLElement ou seletor
    currentPage,        // Página atual (base 1)
    pageSize,           // Itens por página (padrão 25)
    totalCount,         // Contagem total de registros filtrados (res.count)
    pageSizeOptions,    // Ex: [25, 50, 100]
    onPageChange,       // Callback(novaPagina)
    onPageSizeChange    // Callback(novoPageSize)
  });
  ```
- **Padrão Visual Industrial Integrity (DESIGN.md):**
  - Cantos retos obrigatórios (`0px border-radius`);
  - Tipografia técnica `JetBrains Mono` nos contadores numéricos e botões;
  - Cores funcionais: *Dark Iron* (`#131313` / `#2B2B2B`), *Steel Gray* (`#71797E`), *Rust Orange* (`#B7410E`) para a página ativa;
  - Alinhamento em flexbox responsivo com altura compacta de controles (`height: 32px; box-sizing: border-box;`);
  - Janelamento numérico inteligente com elipses (ex: `1 ... 4 [5] 6 ... 12`), desabilitando botões de borda (`« Primeira`, `‹ Anterior`, `Próxima ›`, `Última »`) quando nos extremos;
  - Leitura contextual: `"EXIBINDO X A Y DE Z LANÇAMENTOS"`.

### 2.3 Gestão de Estado e Navegação no Módulo Financeiro (`frontend/assets/js/views/financeiro-view.js`)
1. **Estado:**
   - `extratoCurrentPage`: 1
   - `extratoPageSize`: 25
   - `extratoTotalCount`: 0
   - `extratoTotalPages`: 1
2. **Renderização do Layout:**
   - Adicionar o container `#extrato-pagination-container` posicionado imediatamente abaixo de `.table-container` do Extrato Real.
3. **Consulta de Dados (`carregarListaExtrato`):**
   - Construir parâmetros: `page`, `page_size`, `status_pagamento=PAGO`, `ordering=-data_pagamento,-id` além dos filtros de busca, conta e tipo;
   - Extrair `res.count` e atualizar o badge `#total-extrato-badge` com o número total verídico;
   - Renderizar as linhas da página retornada;
   - Chamar `EMCUtils.renderPagination` passando os callbacks de troca de página e troca de tamanho de página;
   - Em caso de troca de página, realizar rolagem suave para o início da tabela.
4. **Resets de Filtros e Manutenção de Contexto:**
   - Ao alterar texto de busca, conta bancária ou tipo: resetar para `page = 1`;
   - Ao cadastrar novo lançamento, editar, estornar ou anexar comprovante: recarregar a mesma página ativa (`this.extratoCurrentPage`), mantendo o operador no seu contexto de trabalho.
5. **Extensão para Contas a Pagar e Contas a Receber:**
   - Aplicar a mesma governança de paginação nas abas de Contas a Pagar e Contas a Receber, eliminando o limite fantasma de 25 itens em todo o módulo de Tesouraria.

### 2.4 Estilos CSS Industriais (`frontend/assets/css/industrial-integrity.css`)
- Implementar as classes `.emc-pagination`, `.emc-pagination-info`, `.emc-pagination-controls`, `.emc-pagination-btn` e `.emc-pagination-size-select` com responsividade mobile (colapso para coluna única ou wrap fluído em telas `<= 768px`).

---

## 3. Arquivos a Modificar / Criar

| Arquivo | Status | Descrição da Intervenção |
| :--- | :--- | :--- |
| `Planejamento/2026-10-03_03_paginacao_extrato_real_tesouraria.md` | Criar | Este plano de implementação com metadados e registro de aprovação. |
| `backend/core/pagination.py` | Criar | Classe `StandardResultsSetPagination` estendendo `PageNumberPagination`. |
| `backend/config/settings.py` | Modificar | Registrar `core.pagination.StandardResultsSetPagination` no `REST_FRAMEWORK`. |
| `frontend/assets/css/industrial-integrity.css` | Modificar | Estilos industriais da barra de paginação e botões compactos 32px. |
| `frontend/assets/js/utils.js` | Modificar | Implementação do utilitário reutilizável `window.EMCUtils.renderPagination`. |
| `frontend/assets/js/views/financeiro-view.js` | Modificar | Integração da paginação nas abas de Extrato Real, Contas a Pagar e Contas a Receber. |
| `frontend/sw.js` | Modificar | Atualização de `CACHE_NAME` para `'emc-soldas-v4.35'`. |
| `frontend/index.html` | Modificar | Atualização do cache-busting de scripts e links para `?v=4.35`. |
| `docs/STATUS.md` | Modificar | Atualização viva de status na Fase 14.5. |

---

## 4. Plano de Verificação e Testes

### 4.1 Testes Automatizados de Backend
1. Executar bateria de testes do núcleo e financeiro:
   ```powershell
   .\venv\Scripts\python.exe backend/manage.py test core apps.financeiro
   ```
2. Executar suíte completa de testes do sistema (garantir 100% dos 190+ testes aprovados):
   ```powershell
   .\venv\Scripts\python.exe backend/manage.py test backend/
   ```

### 4.2 Testes Funcionais e de Interface
1. **Navegação de Páginas:**
   - Clicar nos botões numéricos (1, 2, 3...) e direcionais (‹ Anterior, Próxima ›, « Primeira, Última ») e verificar transição fluida de registros;
   - Verificar estado desabilitado de botões nos limites (primeira e última página).
2. **Seletor de Quantidade por Página:**
   - Alternar entre 25, 50 e 100 itens por página; verificar atualização imediata da tabela e recálculo da quantidade total de páginas.
3. **Sincronia com Filtros e Busca:**
   - Realizar buscas por descrição, filtro por conta ou tipo; verificar se a página reseta para a página 1 e os contadores refletem o subtotal filtrado.
4. **Persistência de Página em Ações:**
   - Efetuar uma edição ou estorno em um lançamento na página 2; verificar se a lista recarrega permanecendo na página 2.
5. **Responsividade e Design System:**
   - Testar em resolução desktop (1920x1080) e mobile (375x667);
   - Verificar cantos 100% retos (`0px border-radius`), tipografia técnica e ausência de overflow horizontal.

---

## 5. Relatório de Execução (Pós-conclusão)

1. **Backend - Paginação Customizada (`backend/core/pagination.py` & `settings.py`):**
   - Criada a classe `StandardResultsSetPagination` baseada em `PageNumberPagination`, com `page_size = 25`, `page_size_query_param = 'page_size'`, `max_page_size = 1000` e `page_query_param = 'page'`.
   - Atualizado `REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'] = 'core.pagination.StandardResultsSetPagination'` em `settings.py`.
   - Adicionados testes automatizados unitários no `core/tests.py` validando paginação padrão (25 itens), paginação customizada (`page=2&page_size=10`) e contrato da resposta JSON (`count`, `next`, `previous`, `results`).
   - Adicionado teste na API de `apps.financeiro` validando requisição paginada ao endpoint `/api/lancamentos-financeiros/`.

2. **Frontend - Utilitário Centralizado de Paginação (`frontend/assets/js/utils.js`):**
   - Implementada a função `renderPagination` no `window.EMCUtils` com janelamento inteligente de páginas com elipses (`1 ... 4 [5] 6 ... 12`), botões direcionais (`«`, `‹`, `›`, `»`), bloqueio seguro nas extremidades, seletor de linhas por página (`25`, `50`, `100`), contadores de registros exibidos (`X a Y de Z`) e tipografia monoespelhada `JetBrains Mono`.

3. **Frontend - Módulo Financeiro (`frontend/assets/js/views/financeiro-view.js`):**
   - Implementado estado reativo de paginação (`extratoCurrentPage`, `extratoPageSize`, `extratoTotalCount`, etc.).
   - Atualizada a consulta do **Extrato Real (Caixa Real)** para enviar `page`, `page_size`, `status_pagamento=PAGO` e ordenação cronológica estrita por pagamento decrescente (`ordering=-data_pagamento,-id`).
   - Corrigido o badge de total (`#total-extrato-badge`) para exibir o número real vindo do banco (`res.count`).
   - Implementada barra de paginação abaixo da tabela com transição fluida e auto-scroll para o topo da lista.
   - Sincronizados os filtros de busca, conta bancária e tipo para resetar à página 1 a cada modificação.
   - Preservação da página corrente nas operações de inclusão, edição, estorno e upload de comprovantes.
   - Estendida a mesma mecânica de paginação para as abas **Contas a Pagar** e **Contas a Receber**.

4. **Design System & PWA (`industrial-integrity.css`, `sw.js`, `index.html`):**
   - Implementadas as classes `.emc-pagination`, `.emc-pagination-info`, `.emc-pagination-controls`, `.emc-pagination-btn`, `.emc-pagination-size-select` com cantos retos (`0px border-radius`) e responsividade universal mobile (`max-width: 768px`).
   - Atualizada a versão do Service Worker para `CACHE_NAME = 'emc-soldas-v4.35'`.
   - Atualizados os sufixos de cache-busting para `?v=4.35` em todos os scripts e folhas de estilo do `index.html`.

5. **Verificação Automatizada:**
   - `python backend/manage.py test core apps.financeiro`: 37 testes executados e 100% aprovados.
   - `python backend/manage.py test backend/`: Suíte completa com 192 testes executados e 100% aprovados (OK em 76.7s).

