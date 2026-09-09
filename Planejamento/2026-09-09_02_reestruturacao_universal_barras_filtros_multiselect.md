# Registro de Planejamento: Reestruturação Universal das Barras de Filtro e Ação (PWA v4.3)

- **Identificador:** `Planejamento/2026-09-09_02_reestruturacao_universal_barras_filtros_multiselect.md`
- **Data:** 2026-09-09
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-09T16:00:21-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Objetivos
Harmonização universal das barras de controle e filtros no padrão *Industrial Integrity* para eliminar espaços em branco ociosos e comboboxes espremidas em 5 módulos essenciais: **Catálogo**, **Compras**, **Tesouraria**, **Faturamento** e **Orçamentos**, introduzindo o componente universal de **Combobox Multi-Seleção com Flags** (`1 ou N opções simultâneas`).

---

## 2. Decisões Técnicas e Arquiteturais
- **Backend (DRF ViewSets):**
  - `LancamentoFinanceiroViewSet`: suporte a múltiplos status de pagamento e múltiplas contas bancárias separadas por vírgula (`status_pagamento__in`, `conta_id__in`).
  - `FaturaViewSet`: suporte a múltiplos status de faturas separados por vírgula (`status__in`).
  - `OrcamentoViewSet`: suporte a múltiplos status operacionais e múltiplos status financeiros separados por vírgula (`status_operacional__in`, `status_financeiro__in`).
- **Frontend (Design System e Utilitários):**
  - `industrial-integrity.css`: estilos de `.emc-multiselect`, gatilho de trigger, dropdown com flags/checkboxes e botões de cabeçalho `[✓ TODOS]` e `[✕ LIMPAR]`.
  - `utils.js`: implementação da função utilitária `window.EMCUtils.initMultiSelectCombobox`.
- **Frontend (Views):**
  - `catalogo-view.js`: busca elástica, contadores dinâmicos e botões primários integrados em ambas as abas (sem filtros de UOM, conforme diretriz do usuário).
  - `compras-view.js`: busca elástica, combobox pesquisável de fornecedores, chip de total de notas e botão `+ LANÇAR NOTA DE COMPRA` integrado na barra.
  - `financeiro-view.js`:
    - Aba Extrato: busca elástica, multiselect com flags para Contas Bancárias (1 ou N), combobox de Tipo de Lançamento (`TODOS`, `RECEITAS`, `DESPESAS`), totalizador e botão `+ LANÇAMENTO AVULSO`.
    - Aba Contas a Pagar: busca elástica, multiselect com flags para Status (`A VENCER`, `VENCIDAS`, `PAGAS`), totalizador e botão `+ NOVA DESPESA / TÍTULO`.
    - Aba Contas a Receber: busca elástica, multiselect com flags para Status (`A VENCER`, `VENCIDAS`, `RECEBIDAS`), totalizador e botão `+ NOVO TÍTULO AVULSO`.
  - `faturamento-view.js`: busca elástica, multiselect com flags para Status (`RASCUNHO`, `FATURADA`, `PAGA`, `CANCELADA`), chip totalizador e botão de atalho para Conta Corrente.
  - `orcamentos-view.js`: busca elástica, multiselect com flags para Status Operacional (`GERADO`, `ENVIADO`, `APROVADO`, `EM EXECUÇÃO`, `CONCLUÍDO`, `CANCELADO`), combobox de Status Financeiro (`TODOS`, `PENDENTE`, `FATURADO`, `QUITADO`), chip totalizador e botão `+ NOVO ORÇAMENTO` integrado na barra.
- **Governança PWA (Regra Mandatória 12 do AGENTS.md):**
  - Elevação da constante `CACHE_NAME` para `'emc-soldas-v4.3'` em `frontend/sw.js`.
  - Atualização dos sufixos de script e estilo para `?v=4.3` em `frontend/index.html`.
- **Documentação e Auditoria:**
  - Atualização viva de `docs/STATUS.md`.

---

## 3. Arquivos Modificados
- `backend/apps/financeiro/views.py`
- `backend/apps/faturamento/views.py`
- `backend/apps/orcamentos/views.py`
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/utils.js`
- `frontend/assets/js/views/catalogo-view.js`
- `frontend/assets/js/views/compras-view.js`
- `frontend/assets/js/views/financeiro-view.js`
- `frontend/assets/js/views/faturamento-view.js`
- `frontend/assets/js/views/orcamentos-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes Automatizados Backend:**
   - Execução de testes de `financeiro`, `faturamento`, `orcamentos`, `compras` e `catalogo`.
2. **Versionamento PWA:**
   - Bundles sincronizados para `v4.3` em `sw.js` e `index.html`.
