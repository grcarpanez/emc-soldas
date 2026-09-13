# Planejamento: Unificação de Ações de Lançamento e Expansão das Comboboxes de Filtro no Extrato Real

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed do Usuário:** Aprovado em 13/09/2026 12:34:32 (Aprovação formal do documento implementation_plan.md).

---

## 1. Contexto e Objetivos

1. **Problema Reportado:** Duplicidade de botões de lançamento no módulo Tesouraria & Caixa (botão "+ NOVO LANÇAMENTO" no topo e botão "+ LANÇAMENTO AVULSO" na barra de filtros da tabela do Extrato Real). O botão da barra de filtros ocupava espaço excessivo, forçando as comboboxes de filtro de contas bancárias e tipo a ficarem estreitas, cortando os textos com reticências ("TODAS AS CONTAS BA...", "TODOS OS TIPOS").
2. **Diretriz do Usuário:** Remover o botão duplicado da barra de filtros, expandir a largura das comboboxes para evitar cortes de texto e manter exclusivamente no topo os botões "+ TRANSFERÊNCIA INTER-CONTAS" e "+ NOVO LANÇAMENTO".
3. **Escopo da Entrega:**
   - Remoção do botão "+ LANÇAMENTO AVULSO" e seu listener em `frontend/assets/js/views/financeiro-view.js`.
   - Expansão de `#wrapper-extrato-conta` de 220px para 270px (min-width 240px).
   - Expansão de `#filtro-extrato-tipo` de 160px para 190px (min-width 175px).
   - Versionamento de cache PWA (`sw.js` para `v4.18` e `index.html` para `?v=4.18`).
   - Execução de testes automatizados e atualização de `docs/STATUS.md`.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Inteligência de Contexto do Botão Superior:**
   - O botão do topo `btn-novo-lancamento` já possui lógica de detecção de aba ativa:
     ```javascript
     const tipo = this.currentTab === 'receber' ? 'ENTRADA' : 'SAIDA';
     const modo = this.currentTab === 'extrato' ? 'extrato' : 'competencia';
     this.abrirModalNovoLancamento(tipo, modo);
     ```
     Desta forma, na aba `EXTRATO REAL (CAIXA)`, o botão do topo abre nativamente o modal de lançamento já liquidado com débito/crédito em conta bancária imediato.
2. **Distribuição Harmônica da Barra de Filtros:**
   - `filtro-extrato-busca`: `flex: 1; min-width: 220px;`.
   - `wrapper-extrato-conta`: `width: 270px; min-width: 240px; flex-shrink: 0;`.
   - `filtro-extrato-tipo`: `width: 190px; min-width: 175px; flex-shrink: 0;`.
   - `total-extrato-badge`: `padding: 7px 14px; flex-shrink: 0;`.

---

## 3. Arquivos Modificados

- `frontend/assets/js/views/financeiro-view.js` [MODIFY]
- `frontend/sw.js` [MODIFY]
- `frontend/index.html` [MODIFY]
- `docs/STATUS.md` [MODIFY]

---

## 4. Relatório de Execução e Evidências

1. **Interface Frontend (PWA):**
   - Removido o botão secundário `+ LANÇAMENTO AVULSO` da barra de filtros em `financeiro-view.js`.
   - Ampliada a largura da combobox de Contas Bancárias (`#wrapper-extrato-conta`) para 270px (min-width: 240px), acomodando `"TODAS AS CONTAS BANCÁRIAS"` sem cortes ou reticências.
   - Ampliada a largura da combobox de Tipo de Movimentação (`#filtro-extrato-tipo`) para 190px (min-width: 175px), acomodando com folga `"TODOS OS TIPOS"`, `"RECEITAS (+)"` e `"DESPESAS (-)"`.
   - Preservados os botões superiores `+ TRANSFERÊNCIA INTER-CONTAS` e `+ NOVO LANÇAMENTO`.
2. **Testes Automatizados:**
   - Suíte de 175 testes do projeto Django executada com 100% de sucesso.
3. **Versionamento e Cache:**
   - Cache do Service Worker incrementado para `emc-soldas-v4.18`.
   - Cache-busting em `index.html` atualizado para `?v=4.18`.
4. **Governança:**
   - `docs/STATUS.md` atualizado com a entrega da Fase 14.5.
