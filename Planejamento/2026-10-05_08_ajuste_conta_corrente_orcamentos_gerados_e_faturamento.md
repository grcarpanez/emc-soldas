# Implementation Plan - Workflow de Status de Orçamentos e Faturamento na Conta Corrente

- **Data:** 2026-10-05
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Pendente (Aguardando aprovação - Proceed)
- **Arquivo de Registro:** `Planejamento/2026-10-05_08_ajuste_conta_corrente_orcamentos_gerados_e_faturamento.md`

---

## 1. Contexto e Diagnóstico

### 1.1 Cenário e Decisão de Negócio Alinhada com o Usuário
O usuário esclareceu:
> *"Foi um erro meu. Realmente o orçamento deve estar no mínimo aprovado para que seja faturado. Mas precisamos realmente dos botões para alterar o status deles"*

### 1.2 Análise Técnica do Estado Atual
1. **Regra de Faturamento e Conta Corrente:**
   A regra em `apps/faturamento/services.py` (`listar_conta_corrente_cliente`) exige `status_operacional__in=['CONCLUIDO', 'EM_EXECUCAO', 'APROVADO']`.
   Esta regra está **correta e alinhada com as diretrizes do FSD e confirmada pelo usuário**. Orçamentos em `GERADO` ou `ENVIADO` não devem aparecer para faturar até serem formalmente aprovados.
2. **Gargalo de Usabilidade na Interface de Orçamentos (`orcamentos-view.js`):**
   No modal de detalhes do orçamento (`verDetalhes`), existiam apenas os botões `BAIXAR PDF`, `RENOVAR VALIDADE` e `CANCELAR ORÇAMENTO`.
   **Não existiam botões para o operador transitar o status operacional** (`Aprovar`, `Iniciar Execução`, `Concluir`), impedindo que o operador avance o orçamento de `GERADO` para `APROVADO`.
   Os endpoints de backend já existem no `OrcamentoViewSet` (`/enviar/`, `/aprovar/`, `/iniciar-execucao/`, `/concluir/`), faltando apenas a camada de interação e ações na interface.
3. **Divergência de Parâmetros de Payload no Faturamento (`faturamento-view.js`):**
   No método `gerarPreFatura()`, o payload enviado no POST era `{ cliente_id, orcamentos_ids }`, enquanto o `FaturaSerializer` espera `{ cliente, orcamento_ids }`. Se disparado, gerava erro 400.
4. **Ausência da Combobox Pesquisável na Conta Corrente (Regra 14 do AGENTS.md):**
   O seletor de clientes na aba de Conta Corrente usava `<select>` puro e não indicava quantos orçamentos faturáveis cada cliente possui.

---

## 2. Objetivos da Solução

1. **Botões de Transição de Status no Modal de Detalhes (`orcamentos-view.js`):**
   - Implementar botões contextuais claros no modal de detalhes do orçamento:
     - Se `GERADO`: botão `[MARCAR COMO ENVIADO]` e botão de destaque `[APROVAR ORÇAMENTO]`.
     - Se `ENVIADO`: botão de destaque `[APROVAR ORÇAMENTO]`.
     - Se `APROVADO`: botão `[INICIAR EXECUÇÃO]`.
     - Se `EM_EXECUCAO`: botão `[CONCLUIR SERVIÇO]`.
     - Se `CONCLUIDO`: indicador `[✓ SERVIÇO CONCLUÍDO - PRONTO PARA FATURAMENTO]`.
   - Adicionar método `transitarStatusOperacional(orcId, acao)` com chamadas à API, tratamento de validação (ex: orçamento expirado) e toasts de sucesso com recarregamento em tempo real.
2. **Atalho Rápido na Tabela de Orçamentos (Opcional & Ágil):**
   - Na coluna de Ações da listagem de orçamentos, exibir botão rápido `APROVAR` quando o orçamento estiver em `GERADO` ou `ENVIADO`, permitindo aprovação em 1 clique direto da tabela com confirmação rápida.
3. **Mapeamento de Endpoints no Frontend (`config.js`):**
   - Registrar no objeto `CONFIG.ENDPOINTS.ORCAMENTOS` os endpoints `/enviar/`, `/aprovar/`, `/iniciar-execucao/` e `/concluir/`.
4. **Resiliência e Combobox Pesquisável no Faturamento (`faturamento-view.js` e `serializers.py`):**
   - Corrigir o payload em `gerarPreFatura()` para `{ cliente: clienteId, orcamento_ids: selecionados }`.
   - No `FaturaSerializer`, adicionar suporte a `cliente_id` e `orcamentos_ids` como aliases defensivos.
   - Implementar Combobox Pesquisável (`initSearchableSelect`) no seletor de cliente da Conta Corrente, indicando a quantidade de orçamentos faturáveis (ex: `DAVID (2 orçamentos faturáveis)`).
   - Ajustar as cores dos chips de status na tabela da Conta Corrente (`APROVADO` -> success, `EM_EXECUCAO` -> warning, `CONCLUIDO` -> success).
5. **Versionamento e Testes:**
   - Incrementar versão do Service Worker para `emc-soldas-v4.57` e cache-busting no `index.html`.
   - Garantir 100% de aprovação na suíte de testes do backend.

---

## 3. Decisões Arquiteturais e Técnicas

### 3.1 Frontend `frontend/assets/js/config.js`
Adicionar em `CONFIG.ENDPOINTS.ORCAMENTOS`:
```javascript
ENVIAR: '/orcamentos/{id}/enviar/',
APROVAR: '/orcamentos/{id}/aprovar/',
INICIAR_EXECUCAO: '/orcamentos/{id}/iniciar-execucao/',
CONCLUIR: '/orcamentos/{id}/concluir/',
```

### 3.2 Frontend `frontend/assets/js/views/orcamentos-view.js`
- Adicionar função `transitarStatus(orcId, novoStatus, endpointUrl)`:
  - Dispara POST para o endpoint correspondente.
  - Exibe toast informativo (`Orçamento aprovado com sucesso!`, `Execução iniciada!`, `Serviço concluído!`).
  - Recarrega a tabela e atualiza os detalhes.
- No modal `verDetalhes`:
  - Renderizar no rodapé o bloco de botões de workflow operacional.
  - Para orçamentos expirados, o backend já bloqueia a aprovação exigindo renovação; o frontend capturará e exibirá o toast explicativo.

### 3.3 Backend `backend/apps/faturamento/serializers.py`
- Em `FaturaSerializer`:
  - Tratar aliases no `to_internal_value` ou validação: se vier `cliente_id`, preenche `cliente`; se vier `orcamentos_ids`, preenche `orcamento_ids`.

### 3.4 Frontend `frontend/assets/js/views/faturamento-view.js`
- Inicializar `cc-filtro-cliente` com `window.EMCUtils.initSearchableSelect`.
- Consultar `/api/faturas/conta-corrente/` para contar orçamentos por cliente e destacar no texto do select.
- Garantir envio correto de `cliente` e `orcamento_ids` no POST de pré-fatura.

---

## 4. Arquivos a Modificar

| Arquivo | Ação | Descrição |
|---|---|---|
| `Planejamento/2026-10-05_08_ajuste_conta_corrente_orcamentos_gerados_e_faturamento.md` | Modificar | Plano de implementação com escopo revisado |
| `frontend/assets/js/config.js` | Modificar | Adicionar endpoints de transição de status operacional |
| `frontend/assets/js/views/orcamentos-view.js` | Modificar | Botões de workflow operacional no modal de detalhes e atalho na tabela |
| `backend/apps/faturamento/serializers.py` | Modificar | Suporte defensivo a aliases no payload de faturas |
| `frontend/assets/js/views/faturamento-view.js` | Modificar | Combobox pesquisável de clientes, payload correto e chips dinâmicos |
| `frontend/sw.js` | Modificar | Bump para `emc-soldas-v4.57` |
| `frontend/index.html` | Modificar | Cache-busting para `?v=4.57` |
| `docs/STATUS.md` | Modificar | Atualização de status e versionamento |

---

## 5. Plano de Verificação e Testes

1. **Testes de Backend:**
   - `..\venv\Scripts\python.exe manage.py test apps.orcamentos apps.faturamento`
   - Suíte global (`python manage.py test`)
2. **Validação do Fluxo Operacional:**
   - Acessar a listagem de Orçamentos.
   - Abrir os detalhes do Orçamento #1 ou #2 do cliente DAVID (que está `GERADO`).
   - Clicar no botão `[APROVAR ORÇAMENTO]`: o status transita para `APROVADO`.
   - Opcionalmente avançar para `[INICIAR EXECUÇÃO]` ou `[CONCLUIR SERVIÇO]`.
3. **Validação na Conta Corrente:**
   - Acessar **Faturamento & Conta Corrente** -> **Conta Corrente (Orçamentos a Faturar)**.
   - O cliente DAVID agora exibe seus orçamentos aprovados/concluídos na tabela!
   - Selecionar os orçamentos e clicar em `+ CONSOLIDAR EM PRÉ-FATURA`.
   - A Pré-Fatura em Rascunho é criada com sucesso!

---

## 6. Registro de Aprovação (Proceed)

- **Status:** Concluído (Aprovado e executado com sucesso)
- **Data/Hora da Aprovação:** 2026-10-05 15:34:09
- **Mensagem do Usuário:** "Proceed"

---

## 7. Relatório de Execução e Evidências

### 7.1 Modificações Realizadas
1. **Frontend (`frontend/assets/js/config.js`):**
   - Mapeados os endpoints `/orcamentos/{id}/enviar/`, `/orcamentos/{id}/aprovar/`, `/orcamentos/{id}/iniciar-execucao/` e `/orcamentos/{id}/concluir/` em `CONFIG.ENDPOINTS.ORCAMENTOS`.
2. **Frontend (`frontend/assets/js/views/orcamentos-view.js`):**
   - Modal de Detalhes (`verDetalhes`): Inserido painel de ações de transição operacional no padrão *Industrial Integrity*, exibindo botões contextuais (`MARCAR COMO ENVIADO`, `✓ APROVAR ORÇAMENTO`, `▶ INICIAR EXECUÇÃO`, `✓ CONCLUIR SERVIÇO`) e badges informativos de elegibilidade para faturamento.
   - Tabela de Orçamentos: Incluído botão rápido `APROVAR` diretamente na coluna de ações para orçamentos em estado `GERADO` ou `ENVIADO`.
   - Método `transitarStatus(orcId, acao, nomeLegivel)` implementado com integração aos endpoints REST, atualização da tabela e recarga dinâmica do modal de detalhes.
3. **Backend (`backend/apps/faturamento/serializers.py`):**
   - Implementado `to_internal_value` no `FaturaSerializer` para dar suporte resiliente aos aliases `cliente_id` (para `cliente`) e `orcamentos_ids` (para `orcamento_ids`).
4. **Frontend (`frontend/assets/js/views/faturamento-view.js`):**
   - Implementada a Combobox Pesquisável (`initSearchableSelect`) no seletor de clientes da Conta Corrente (Regra 14 do AGENTS.md), exibindo a quantidade de orçamentos pendentes por cliente (ex: `DAVID [2 orçamentos a faturar]`).
   - Calibradas as cores dos chips de status operacional na tabela da Conta Corrente.
   - Corrigido o payload em `gerarPreFatura()` enviando `cliente` e `orcamento_ids`.
5. **Versionamento PWA:**
   - Atualizado `CACHE_NAME = 'emc-soldas-v4.57'` em `frontend/sw.js`.
   - Atualizados sufixos de cache-busting para `?v=4.57` em `frontend/index.html`.
6. **Documentação Viva:**
   - Atualizado `docs/STATUS.md` com a tarefa concluída e PWA `v4.57`.

### 7.2 Resultados dos Testes Automatizados
- Testes de Orçamentos e Faturamento: 24 testes executados com 100% de sucesso.
- Suíte Global do Sistema (`task-1232`): **203 testes executados com 100% de sucesso** (`Ran 203 tests in 81.310s - OK`).

