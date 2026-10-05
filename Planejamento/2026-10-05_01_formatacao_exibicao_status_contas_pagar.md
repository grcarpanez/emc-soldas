# Plano de Implementação - Formatação Amigável de Status em Contas a Pagar e Receber

- **Data de Criação:** 05/10/2026
- **Autor:** Antigravity AI & Gustavo
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 05/10/2026 às 11:24:45 (Horário de Brasília)
  - **Transcrição da Aprovação do Usuário:** *"Proceed"*

---

## 1. Contexto e Diagnóstico

### 1.1 Sintoma
Na tela **Tesouraria & Fluxo de Caixa** (aba **Contas a Pagar**), a coluna de **STATUS** exibia a tag/chip com o valor interno do banco contendo *underscore* (`A_VENCER`), conforme registrado em evidência, em vez da exibição formatada com espaço (`A VENCER`).

### 1.2 Causa Raiz
1. **Frontend (`financeiro-view.js`):** Na renderização da tabela de Contas a Pagar (linha 387) e Contas a Receber (linha 530), bem como no modal de edição/reclassificação (linha 1128), a interpolação injetava diretamente o valor cru do backend:
   ```javascript
   <td><span class="status-chip ${badge}">${l.status_pagamento}</span></td>
   ```
   Como o valor gravado na coluna MySQL é `A_VENCER`, ele era desenhado no DOM sem formatação amigável.
2. **Backend (`backend/apps/financeiro/serializers.py`):** O serializer `LancamentoFinanceiroSerializer` expõe `origem_display`, mas não expunha explicitamente o campo `status_pagamento_display` gerado pelo método nativo do Django ORM `get_status_pagamento_display()`.
3. **Ausência de Helper Unificado:** Não havia um helper centralizado no `EMCUtils` para higienização e exibição padronizada de códigos de status que possam conter underscores (`_`).

---

## 2. Decisões Técnicas e Arquiteturais

1. **Utilitário Global de Interface (`frontend/assets/js/utils.js`):**
   - Implementar a função `formatarStatus(status)` no `window.EMCUtils`:
     ```javascript
     function formatarStatus(status) {
       if (!status || typeof status !== 'string') return '';
       return status.replace(/_/g, ' ').trim();
     }
     ```
   - Essa função substitui com segurança todos os caracteres `_` por espaços, garantindo que `A_VENCER` seja renderizado como `A VENCER`.

2. **Ajuste nas Telas de Tesouraria e Faturamento:**
   - **`frontend/assets/js/views/financeiro-view.js`:**
     - Linha 387 (Contas a Pagar): Aplicar `window.EMCUtils.formatarStatus(l.status_pagamento)`.
     - Linha 530 (Contas a Receber): Aplicar `window.EMCUtils.formatarStatus(l.status_pagamento)`.
     - Linha 1128 (Modal de Edição): Aplicar `window.EMCUtils.formatarStatus(lancamento.status_pagamento)`.
   - **`frontend/assets/js/views/conciliacao-view.js`** e **`frontend/assets/js/views/faturamento-view.js`:**
     - Aplicar o mesmo helper nas listagens de parcelas/lançamentos para consistência visual em todo o fluxo financeiro.

3. **Enriquecimento no Backend (`backend/apps/financeiro/serializers.py`):**
   - Incluir no `LancamentoFinanceiroSerializer`:
     ```python
     status_pagamento_display = serializers.CharField(source='get_status_pagamento_display', read_only=True)
     ```
   - Adicionar `status_pagamento_display` à lista de `fields`.

4. **Governança de Versão PWA e Cache Busting:**
   - Incrementar `CACHE_NAME` no `frontend/sw.js` de `'emc-soldas-v4.49'` para `'emc-soldas-v4.50'`.
   - Atualizar a query string `?v=4.50` em `frontend/index.html`.
   - Orientar o recarregamento forçado via `Ctrl + Shift + R`.

---

## 3. Arquivos Afetados

- `frontend/assets/js/utils.js`
- `frontend/assets/js/views/financeiro-view.js`
- `frontend/assets/js/views/faturamento-view.js`
- `frontend/assets/js/views/conciliacao-view.js`
- `backend/apps/financeiro/serializers.py`
- `backend/apps/financeiro/tests.py`
- `frontend/sw.js`
- `frontend/index.html`
- `Planejamento/2026-10-05_01_formatacao_exibicao_status_contas_pagar.md`
- `docs/STATUS.md`

---

## 4. Plano de Verificação e Testes

1. Executar suíte de testes de backend: `.\venv\Scripts\python backend/manage.py test backend/apps/financeiro/` garantindo 100% de sucesso.
2. Validar no frontend a exibição das tags de status com espaço em vez de `_`.

---

## 5. Relatório de Execução e Homologação

- **Data de Conclusão:** 05/10/2026
- **Execução Realizada:**
  1. `frontend/assets/js/utils.js`: Implementada a função `formatarStatus(status)` e exportada em `window.EMCUtils`.
  2. `frontend/assets/js/views/financeiro-view.js`: Aplicado `window.EMCUtils.formatarStatus()` nas tabelas de Contas a Pagar e Contas a Receber e no modal de edição de lançamentos.
  3. `frontend/assets/js/views/faturamento-view.js` e `conciliacao-view.js`: Aplicado `formatarStatus()` na renderização de status de lançamentos/parcelas.
  4. `backend/apps/financeiro/serializers.py`: Incluído o campo `status_pagamento_display` (leitura via `get_status_pagamento_display`).
  5. `backend/apps/financeiro/tests.py`: Criado teste `test_status_pagamento_display_serializer` validando que `status_pagamento_display` retorna `'A VENCER'`.
  6. Sincronização do cache PWA: Atualizado `CACHE_NAME` para `'emc-soldas-v4.50'` em `sw.js` e query strings de scripts/estilos em `index.html` para `?v=4.50`.
  7. Bateria completa de testes automatizados (`python backend/manage.py test backend`): 201 testes aprovados (100% OK em 85.2s).

