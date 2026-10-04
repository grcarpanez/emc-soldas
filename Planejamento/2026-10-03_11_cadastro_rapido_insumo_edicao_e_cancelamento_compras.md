# Implementation Plan - Cadastro Rápido de Insumos, Edição e Cancelamento de Compras

- **Data:** 2026-10-03
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** Concluído
- **Fase de Referência:** Fase 7 / Fase 14.5 (UX, Compras e Retroalimentação de Custos)
- **Versão do PWA Alvo:** v4.42 (Incremento de v4.41 -> v4.42)
- **Registro de Aprovação:** Aprovado explicitamente pelo usuário via `Proceed` em 2026-10-03 21:14:06-03:00.

---

## 1. Contexto e Objetivos

### 1.1 O Que Motivou a Demanda
Durante o lançamento de compras na oficina, a rotina operacional identificou três necessidades de alto atrito:
1. **Cadastro Rápido de Insumo no Lançamento:** Atualmente, se um insumo comprado ainda não existe no catálogo, o operador é obrigado a fechar o modal de lançamento da nota fiscal, navegar até a aba Catálogo, cadastrar o insumo, retornar para Compras e digitar novamente todos os dados da nota fiscal (fornecedor, número, data, chave, anexo e itens prévios), gerando retrabalho expressivo.
2. **Edição de Notas de Compra:** Se o operador errar o número da nota, fornecedor, data, quantidade ou valor de algum item, a listagem de compras atual não dispõe de um botão "EDITAR", impedindo correções pontuais sem intervenção técnica.
3. **Cancelamento de Compra (com Recálculo de Custos):** Se uma nota fiscal for lançada em duplicidade ou de forma equivocada, a interface não disponibiliza um botão visual de "CANCELAR COMPRA". Além disso, o cancelamento de uma nota fiscal exige o recálculo automático e inteligente do custo do insumo no catálogo, restaurando o último custo de compra para a compra ativa válida anterior.

### 1.2 Objetivos Técnicos e de Negócio
- Permitir o cadastro ágil de novos insumos diretamente no modal de lançamento/edição de nota fiscal, selecionando o insumo recém-criado automaticamente e mantendo todos os dados já digitados na nota sem perda de estado.
- Permitir edição completa (`PUT`/`PATCH`) de notas de compra existentes (cabeçalho, itens e anexo).
- Disponibilizar botão de cancelamento com confirmação segura e Soft Delete mandatório (`deleted_at = NOW()`), recalculando automaticamente `ultimo_custo_compra` e `data_ultima_compra` dos insumos para a compra ativa anterior no histórico.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend (Django REST Framework & MySQL)
1. **Recálculo Inteligente de Custos (`recalcular_custo_item_apos_alteracao` em `apps/compras/services.py`):**
   - Ao cancelar (Soft Delete) ou editar uma nota fiscal, o sistema consultará `NotaCompraItem` filtrando pelo item e apenas notas fiscais ativas (`documento_fiscal__deleted_at__isnull=True`), ordenado por data decrescente (`-documento_fiscal__data_compra`, `-documento_fiscal__id`).
   - Se houver compra ativa remanescente: restaura `ultimo_custo_compra = ultima_compra.valor_unitario` e `data_ultima_compra = ultima_compra.documento_fiscal.data_compra`.
   - Se não houver compras ativas remanescentes: redefine `data_ultima_compra = None`.
2. **Soft Delete Seguro no ViewSet (`perform_destroy` em `DocumentoFiscalCompraViewSet`):**
   - Captura os `item_ids` dos itens pertencentes à nota antes do Soft Delete.
   - Executa `instance.soft_delete(user=self.request.user)`.
   - Dispara `recalcular_custo_item_apos_alteracao` para cada item impactado, garantindo consistência total do catálogo.
3. **Edição Robusta de Notas (`DocumentoFiscalCompraSerializer.update`):**
   - Suporta atualização de campos do cabeçalho (`num_nota`, `fornecedor_id`, `data_compra`, `chave_acesso`, `valor_total`).
   - Se `itens_comprados` for enviado, mapeia os itens antigos, recria a lista com os novos itens e recalcula os custos dos itens antigos e novos com precisão.

### 2.2 Frontend PWA (Vanilla JS & Design System *Industrial Integrity*)
1. **Modal de Cadastro Rápido de Insumo:**
   - Adicionar botão `+ NOVO INSUMO` no cabeçalho do sub-grid de itens da nota fiscal e na opção de ação do combobox pesquisável de insumos (`action: { label: '+ CADASTRAR NOVO INSUMO', onClick: ... }`).
   - Modal secundário via `window.EMCUtils.openModal` que empilha no `modalStack` (z-index superior), sem fechar o modal de compra.
   - Campos essenciais e ágeis:
     - `Nome do Insumo *` (autofocus, conversão automática para maiúsculo sem acento).
     - `Unidade de Compra *` (carregada do dicionário UOM).
     - `Unidade de Consumo` (pré-selecionada igual à de compra).
     - `Fator de Conversão` (padrão `1,0000`).
     - `Tipo de Uso` (padrão `INSUMO PRODUTIVO`).
   - Ao salvar (`POST /api/itens/`):
     - Atualiza as opções do select/combobox de insumos da compra.
     - **Auto-seleciona** o novo item imediatamente.
     - Posiciona o foco no campo "Quantidade Comprada".
     - Fecha apenas o modal rápido, preservando 100% dos dados já digitados na nota.
2. **Botão e Fluxo de Edição de Compra:**
   - Botão `EDITAR` na tabela principal de compras e no modal de detalhes da nota.
   - Reutiliza `abrirModalCompra(notaId)` preenchendo todos os dados existentes: Fornecedor, Nº Nota, Data, Chave de Acesso, indicação de anexo existente e carregando a lista `itensTemp` com os itens já cadastrados.
   - Permite adicionar, remover e modificar itens e valores.
   - Ao submeter, executa `PUT` em `/api/documentos-fiscais-compra/${notaId}/` (e upload de novo anexo se fornecido).
3. **Botão e Fluxo de Cancelamento de Compra:**
   - Botão `CANCELAR` na tabela de compras e no modal de detalhes com estilo de destaque de segurança (`btn-danger btn-sm`).
   - Modal de confirmação seguro (`CANCELAR NOTA FISCAL DE ENTRADA`) informando o número da nota, fornecedor, valor total e advertindo sobre o recálculo dos custos dos insumos.
   - Ao confirmar, envia `DELETE /api/documentos-fiscais-compra/${notaId}/`.
   - Exibe toast de sucesso e recarrega a tabela de notas.

---

## 3. Arquivos a Modificar / Criar

| Arquivo | Ação | Descrição |
| :--- | :--- | :--- |
| `backend/apps/compras/services.py` | Modificar | Adicionar função `recalcular_custo_item_apos_alteracao(item, usuario)` para recompor custos após exclusão/edição. |
| `backend/apps/compras/views.py` | Modificar | Atualizar `perform_destroy` em `DocumentoFiscalCompraViewSet` para recalcular custos após Soft Delete. |
| `backend/apps/compras/serializers.py` | Modificar | Ajustar `DocumentoFiscalCompraSerializer.update` para gerenciar itens substituídos e disparar recálculo dos itens afetados. |
| `backend/apps/compras/tests.py` | Modificar | Adicionar testes unitários/integrados para cancelamento, recálculo de custos após delete e edição completa de notas. |
| `frontend/assets/js/views/compras-view.js` | Modificar | Implementar modal de cadastro rápido de insumo, fluxo de edição (`abrirModalCompra(notaId)`), botões `EDITAR` e `CANCELAR` com modal de confirmação. |
| `frontend/sw.js` | Modificar | Incrementar versão de cache do Service Worker de `v4.41` para `v4.42` (Regra 12). |
| `frontend/index.html` | Modificar | Atualizar sufixos de cache-busting `?v=4.42` em todas as tags `<script>` e `<link>` (Regra 12). |
| `Planejamento/2026-10-03_11_cadastro_rapido_insumo_edicao_e_cancelamento_compras.md` | Criar | Arquivo definitivo de planejamento e relatório de execução arquivado na raiz. |
| `docs/STATUS.md` | Modificar | Registrar a conclusão das funcionalidades e avanço no checklist de compras. |

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados Backend (`python backend/manage.py test apps.compras`):**
   - Teste de cancelamento de nota de compra e verificação de que o custo do insumo volta para o valor da compra anterior.
   - Teste de cancelamento de nota única e verificação de que `data_ultima_compra` volta para `None`.
   - Teste de edição de nota fiscal alterando quantidade/preço de item e recalculando custo.
   - Execução da suíte completa de testes de compras (garantindo 100% de sucesso).
2. **Verificação de Regras de Segurança e Blindagem Técnica:**
   - Proibição de Hard Delete: conferir se a nota cancelada possui `deleted_at` preenchido e não desaparece fisicamente do MySQL.
   - RBAC: conferir que apenas usuários com `acesso_compras` conseguem editar ou cancelar.
   - Não-vazamento de tracebacks e sanitização universal de inputs.
3. **Verificação no Frontend PWA (Client-Side):**
   - Testar o botão `+ NOVO INSUMO` durante o preenchimento de uma nota com itens já inseridos; confirmar que o modal rápido abre, salva o insumo, seleciona-o no select e mantém os dados da nota intactos.
   - Testar o botão `EDITAR` em uma nota existente; confirmar que todos os campos e itens são carregados, modificar um item, salvar e verificar a atualização.
   - Testar o botão `CANCELAR` em uma nota de compra; confirmar modal de confirmação, execução do cancelamento e recarregamento da tabela.
   - Confirmar incremento de versão do Service Worker (`v4.42`) e cache-busting em `index.html`.

---

## 6. Relatório de Execução e Evidências de Validação

- **Status Final:** Concluído com 100% de Sucesso
- **Data de Conclusão:** 2026-10-03
- **Resumo das Entregas:**
  1. **Recálculo Inteligente de Custos no Backend:**
     - Criada função `recalcular_custo_item_apos_alteracao` em `backend/apps/compras/services.py`, restaurando o custo e data para a compra ativa mais recente em `NotaCompraItem` quando uma nota fiscal for cancelada ou editada.
     - Atualizado `DocumentoFiscalCompraViewSet.perform_destroy` em `backend/apps/compras/views.py` para soft-deletar a nota e recalcular automaticamente os custos dos insumos no catálogo.
     - Atualizado `DocumentoFiscalCompraSerializer.update` em `backend/apps/compras/serializers.py` para mapear insumos adicionados/removidos e recalcular custos com consistência atômica.
  2. **Cadastro Rápido de Insumo no Frontend:**
     - Criado método `dispararCadastroNovoInsumo` integrado ao combobox pesquisável de insumos e com botão de atalho `+ NOVO INSUMO` no sub-grid de itens da nota fiscal (`frontend/assets/js/views/compras-view.js`).
     - Abertura de modal sobreposto (empilhado via `modalStack`) que salva o insumo via API, atualiza as opções, auto-seleciona o novo item e move o foco para a quantidade, mantendo todos os dados já digitados na nota sem perda de estado.
  3. **Edição e Cancelamento de Notas Fiscais:**
     - Adicionados botões `EDITAR` e `CANCELAR` na tabela de notas fiscais e no modal de detalhes (`frontend/assets/js/views/compras-view.js`).
     - `abrirModalCompra(notaId)` adaptado para carregar dados da nota, anexo existente e itens em edição, enviando `PUT` para a API.
     - `confirmarCancelamentoNota` implementado com modal seguro de advertência (*Industrial Integrity*) e exclusão lógica via `DELETE`.
  4. **Governança de Cache PWA (Regra 12):**
     - `CACHE_NAME` atualizado para `emc-soldas-v4.42` em `frontend/sw.js`.
     - Tags `<link>` e `<script>` atualizadas com sufixo `?v=4.42` em `frontend/index.html`.
  5. **Bateria de Testes Automatizados:**
     - Criados 3 novos testes em `backend/apps/compras/tests.py`:
       - `test_cancelar_nota_compra_recalcula_custo_item_para_compra_anterior`
       - `test_cancelar_unica_compra_zera_data_ultima_compra`
       - `test_editar_nota_compra_recalcula_custo`
     - Resultado: 28 testes em `apps.compras` (100% OK) e 343 testes em toda a suíte do backend (100% OK em 62.4s).

