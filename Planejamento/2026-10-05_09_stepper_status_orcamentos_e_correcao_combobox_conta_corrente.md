# Implementation Plan - Stepper de Transição de Status em Orçamentos e Correção da Combobox na Conta Corrente

- **Data:** 2026-10-05
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Concluído
- **Arquivo de Registro:** `Planejamento/2026-10-05_09_stepper_status_orcamentos_e_correcao_combobox_conta_corrente.md`

---

## 1. Contexto e Diagnóstico

### 1.1 Sintomas Reportados pelo Usuário
1. **Modal de Detalhes não atualiza após mudança de status:**
   > *"Quando clico no botão de alteração de status, preciso fechar o modal e abrir de novo pra ele atualizar. ele deveria atualizar já na hora que eu clico."*
2. **Necessidade de Avançar e Regredir Status Livremente (Tratamento de Erros de Clique):**
   > *"e deveriam ser dois botões, um para avançar o status e um para regredir o status, caso eu clique por engano. Ou então, uma combobox pra eu selecionar em que status ele dewve ficar, ou botões de todos os status e quando clico em um, ele fica ativo e os outros inativos"*
3. **Seleção de Cliente na Conta Corrente não carrega orçamentos:**
   > *"E mesmo assim, selecionando o David, que ele exibe que tem dois orçamentos a faturar, ele me manda selecionar um cliente que tenha ao menos um orçamento a consolidr"*
4. **Alinhamento dos Dois Momentos de Faturamento:**
   > *"na verdade teremos dois momentos de fatura. quando seleciono os orçamenros, devo gerar uma pré fatura, com as opções de pagamento que vou oferecer ao cliente. envio ao cliente. assim que ele me retornar com a resposta da forma de pagamento que escolheu, eu vou na listagem de faturas emitidas, que deve mostrar as faturas emitidas e também as pré faturas emitidas. Seleciono essa pre fatura, defino o valor final (caso combine algum desconto na negociação da pre fatura), defino a forma de pagamento escolhida e só aí, connverto a pre fatura em fatura, e é nesse momento, de finalização da fatura, que é gerada a conta a reeber, em nome desse cliente, vinculada a essa fatura, que agrega os orçamentos que escolhi. Tenho também, na pre fatura a opção de cancelá-la, liberando todos os orçamentos que ela agrupava pra que entrem em outra fatura."*

---

## 2. Objetivos da Solução

1. **Correção do Callback `onChange` em `initSearchableSelect`:**
   Garantir que a seleção de qualquer item no `initSearchableSelect` invoque `opts.onChange(val, item)` e dispare o evento `change`, garantindo que ao selecionar o cliente **DAVID**, os 2 orçamentos sejam imediatamente carregados na tabela com suas caixas de seleção.
2. **Stepper / Barra de Status com Botões Ativos/Inativos:**
   Implementar no modal de detalhes do orçamento uma barra técnica de botões para os 5 status operacionais:
   `[ GERADO ]` `[ ENVIADO ]` `[ APROVADO ]` `[ EM EXECUÇÃO ]` `[ CONCLUÍDO ]`
   - O status atual fica **ativo e destacado** (estilo visual Dark Iron / Rust Orange / Green).
   - Os outros status ficam **clicáveis** para transição direta (permitindo tanto avançar quanto regredir livremente em caso de engano).
   - Adicionar botões auxiliares `◀ VOLTAR STATUS` e `AVANÇAR STATUS ▶` para transição sequencial rápida.
3. **Atualização Instantânea do Modal em Tempo Real:**
   Atualizar o DOM do modal na hora do clique (fechando o anterior via `closeModal()` e reabrindo via `verDetalhes(orcId)` com verificação de `.modal-overlay`), eliminando qualquer necessidade de fechar e reabrir manualmente.
4. **Endpoint Genérico e Regras de Regressão no Backend:**
   - Adicionar endpoint `@action(detail=True, methods=['post'], url_path='alterar-status-operacional')` no `OrcamentoViewSet`.
   - Permitir avanço e regressão livre entre qualquer status operacional (`GERADO`, `ENVIADO`, `APROVADO`, `EM_EXECUCAO`, `CONCLUIDO`) desde que o orçamento não esteja faturado (`status_financeiro == 'A_FATURAR'`).
   - Se já estiver faturado ou pago, o status operacional fica travado.
5. **Implementação do Fluxo em Dois Momentos de Faturamento:**
   - **Momento 1 (Conta Corrente -> Nova Pré-Fatura em Rascunho):**
     - Seleção do cliente e listagem com checkboxes individuais e seleção master.
     - Resumo em tempo real: contador de orçamentos e somatório do valor líquido consolidado.
     - Modal de consolidação de Pré-Fatura: permite definir desconto da proposta e marcar quais opções de regras de pagamento ativas serão oferecidas no PDF espelho (com desconto padrão ajustável por regra).
     - Geração em `RASCUNHO`, sem criar títulos no Contas a Receber e mantendo orçamentos em `A_FATURAR`.
     - Emissão do PDF Espelho da Pré-Fatura para envio ao cliente via WhatsApp ou e-mail.
     - Botão de cancelamento que liberta os orçamentos de volta para a Conta Corrente.
   - **Momento 2 (Listagem de Faturas -> Fechamento Definitivo):**
     - Identificação visual `RASCUNHO (PRÉ-FATURA)` na lista e no modal de detalhes.
     - Exibição das opções de propostas ofertadas no espelho.
     - Painel de fechamento definitivo: seleção da regra acordada com o cliente, ajuste de desconto final negociado e inclusão opcional de número da NF-e.
     - Faturamento definitivo: transita para `FATURADA`, orçamentos para `FATURADO` e gera compulsoriamente os títulos a receber no Contas a Receber.
6. **Versionamento e Testes:**
   - Incrementar versão PWA para `v4.58` em `sw.js` e `index.html`.
   - 100% de aprovação na suíte de testes (203 testes passando).

---

## 3. Decisões Arquiteturais e Técnicas

### 3.1 Frontend (`frontend/assets/js/utils.js`)
Em `initSearchableSelect`:
```javascript
  const onChangeCallback = typeof opts.onChange === 'function' ? opts.onChange : null;
  ...
  function selecionarItem(val) {
    selectEl.value = val;
    extrairOpcoes();
    atualizarTriggerText();
    fecharDropdown();
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
    if (onChangeCallback) {
      onChangeCallback(val, selectEl.options[selectEl.selectedIndex]);
    }
  }
```

### 3.2 Frontend (`frontend/assets/js/views/faturamento-view.js`)
- Implementação de `atualizarResumoSelecao()` para contagem e valor acumulado ao vivo.
- Implementação de `abrirModalNovaPreFatura()` com seleção de propostas de pagamento ativas e desconto da proposta.
- Refinamento de `verDetalhesFatura()` com suporte completo às duas fases (Rascunho com propostas simuladas x Faturamento Definitivo).

### 3.3 Backend (`backend/apps/orcamentos/services.py` e `views.py`)
- Em `services.py`:
  Substituir a trava rígida de `CONCLUIDO` por:
  ```python
  if orcamento.status_financeiro in ['FATURADO', 'PAGO'] and novo_status != orcamento.status_operacional:
      raise ValidationError({
          'status_operacional': f"Orçamento faturado ({orcamento.get_status_financeiro_display()}) não pode ter seu status operacional alterado."
      })
  ```
- Em `views.py`:
  Implementar `@action(detail=True, methods=['post'], url_path='alterar-status-operacional')` usando `AlterarStatusOperacionalSerializer`.

### 3.4 Frontend (`frontend/assets/js/views/orcamentos-view.js`)
- Mapear o Stepper com os 5 status e botões de `◀ VOLTAR` e `AVANÇAR ▶`.
- Método `mudarStatusOperacional(orcId, novoStatus)` chamando `/api/orcamentos/{id}/alterar-status-operacional/` com payload `{ "novo_status": novoStatus }`.
- Atualizar a tela imediatamente fechando o modal atual (`closeModal()`) e reabrindo com `verDetalhes(orcId)`.

---

## 4. Arquivos Modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `Planejamento/2026-10-05_09_stepper_status_orcamentos_e_correcao_combobox_conta_corrente.md` | Criar/Atualizar | Plano de implementação, governança e relatório de execução |
| `frontend/assets/js/utils.js` | Modificar | Adicionar suporte a `opts.onChange` no `initSearchableSelect` |
| `frontend/assets/js/views/faturamento-view.js` | Modificar | Fluxo completo em 2 momentos (Pré-Fatura com propostas + Fechamento final) |
| `backend/apps/orcamentos/services.py` | Modificar | Flexibilizar regressão de status operacional para orçamentos a faturar |
| `backend/apps/orcamentos/views.py` | Modificar | Adicionar action `alterar-status-operacional` |
| `frontend/assets/js/config.js` | Modificar | Registrar endpoint `ALTERAR_STATUS_OPERACIONAL` |
| `frontend/assets/js/views/orcamentos-view.js` | Modificar | Stepper visual com botões ativos/inativos e atualização instantânea |
| `frontend/sw.js` | Modificar | Incremento de versão para `emc-soldas-v4.58` |
| `frontend/index.html` | Modificar | Cache-busting para `?v=4.58` |
| `docs/STATUS.md` | Modificar | Atualização de status e versionamento |

---

## 5. Plano de Verificação e Testes

1. **Testes de Backend:**
   - `python manage.py test apps.orcamentos apps.faturamento` (24 testes OK)
   - `python manage.py test` (203 testes OK - 100% de sucesso)
2. **Validação da Seleção do Cliente na Conta Corrente:**
   - Acessar **Faturamento & Conta Corrente** -> **Conta Corrente**.
   - Selecionar **DAVID**: a tabela carrega os 2 orçamentos com valores e checkboxes.
   - Selecionar os orçamentos: o resumo atualiza o contador e a soma total em tempo real.
   - Clicar em `+ CONSOLIDAR EM PRÉ-FATURA` -> Abre modal do Momento 1 com opções de regras de pagamento para o PDF espelho e desconto inicial.
   - Confirmar: gera pré-fatura em `RASCUNHO`, sem contas a receber, e abre os detalhes com botão de baixar PDF espelho.
3. **Validação do Stepper de Status:**
   - Abrir os detalhes de um orçamento.
   - Clicar nos botões do stepper ou em `◀ VOLTAR` / `AVANÇAR ▶`.
   - O status transita e o modal atualiza instantaneamente.

---

## 6. Registro de Aprovação (Proceed)

- **Status:** Concluído (Aprovado pelo usuário)
- **Data/Hora da Aprovação:** 2026-10-05 16:04:54
- **Mensagem do Usuário:** "Proceed"

---

## 7. Relatório de Execução Técnica

1. **Combobox Pesquisável (`initSearchableSelect` em `utils.js`):**
   - Corrigido para disparar `onChangeCallback(val, selOpt)` imediatamente ao selecionar qualquer opção.
   - Destravou o carregamento automático da tabela da Conta Corrente de clientes.
2. **Stepper e Regressão de Status em Orçamentos:**
   - Criada action `@action(detail=True, methods=['post'], url_path='alterar-status-operacional')` no `OrcamentoViewSet`.
   - Removida trava de `CONCLUIDO` em `services.py`, permitindo avançar e regredir livremente entre qualquer um dos 5 status operacionais enquanto o orçamento estiver `A_FATURAR`.
   - No modal de detalhes (`orcamentos-view.js`), implementado stepper com 5 botões de status (com badge `● ATUAL` no ativo e os demais clicáveis) e botões rápidos de `◀ VOLTAR` e `AVANÇAR ▶`.
   - Atualização em tempo real do modal sem necessidade de fechar/reabrir manualmente.
3. **Fluxo de Faturamento em Dois Momentos:**
   - **Momento 1:** Na Conta Corrente, a seleção de cliente carrega os orçamentos aptos com checkboxes. Ao clicar em consolidar, abre modal permitindo definir desconto da pré-fatura e selecionar quais condições comerciais ativas serão ofertadas ao cliente no PDF espelho. Cria a Pré-Fatura em status `RASCUNHO`, mantendo os orçamentos em `A_FATURAR` e sem gerar contas a receber.
   - **Momento 2:** Na listagem de faturas, a pré-fatura aparece identificada como `RASCUNHO (PRÉ-FATURA)`. No modal de detalhes, são exibidas as opções ofertadas e o painel de conversão em fatura definitiva (seleção da forma de pagamento aprovada pelo cliente, desconto final acordado e NF-e). Ao faturar definitivo, transita para `FATURADA`, orçamentos para `FATURADO` e cria os títulos no Contas a Receber.
   - **Cancelamento:** Pré-Faturas podem ser canceladas com justificativa, desvinculando os orçamentos de volta para `A_FATURAR` na Conta Corrente.
4. **Validação de Testes:**
   - Suíte de 203 testes automatizados executada e aprovada com 100% de sucesso.
5. **Versionamento PWA:**
   - `CACHE_NAME` atualizado para `emc-soldas-v4.58` em `sw.js` e tags com `?v=4.58` em `index.html`.
