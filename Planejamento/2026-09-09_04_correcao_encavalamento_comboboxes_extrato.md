# Registro de Planejamento: Correção do Espaçamento e Eliminação de Encavalamento nas Comboboxes da Aba Extrato Real (Tesouraria)

- **Identificador:** `Planejamento/2026-09-09_04_correcao_encavalamento_comboboxes_extrato.md`
- **Data:** 2026-09-09
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-09T17:12:41-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação (`The user has approved this document`).

---

## 1. Contexto e Objetivos
1. Corrigir o encavalamento visual entre a combobox de Contas Bancárias (`#filtro-extrato-conta`) e o seletor de Tipos (`#filtro-extrato-tipo`) na aba Extrato Real (Caixa) da tela de Tesouraria (`/#tesouraria`).
2. Blindar o componente `.emc-multiselect` no Design System (`industrial-integrity.css`) para comportar-se como `display: block; width: 100%; box-sizing: border-box;`, prevenindo que ultrapasse o wrapper pai.
3. Calibrar as larguras dos controles na barra de filtros do Extrato em `financeiro-view.js` para garantir o espaçamento de 10px (`gap: 10px`) sem quebra indesejada.
4. Elevar a versão do PWA para `v4.5` com atualização de `sw.js`, `index.html` e `docs/STATUS.md`.
5. Executar os testes automatizados do Django e realizar o commit semântico obrigatório (Regra Mandatória 13 do `AGENTS.md`).

---

## 2. Decisões Técnicas e Arquiteturais
- **Design System CSS (`industrial-integrity.css`):**
  - Ajustar `.emc-multiselect` para `display: block; width: 100%; box-sizing: border-box;`.
  - Garantir que `.emc-multiselect-trigger` e `.emc-multiselect-dropdown` respeitem as restrições dimensionais do container.
- **View JS (`financeiro-view.js`):**
  - Redimensionar `#wrapper-extrato-conta` para `width: 220px; min-width: 180px; flex-shrink: 0;`.
  - Ajustar `#filtro-extrato-tipo` para `width: 160px; min-width: 150px; flex-shrink: 0;`.
- **Utils JS (`utils.js`):**
  - Reforçar ocultação do elemento nativo via `targetEl.style.setProperty('display', 'none', 'important')`.
- **Versionamento PWA:**
  - `frontend/sw.js`: `CACHE_NAME = 'emc-soldas-v4.5'`.
  - `frontend/index.html`: `?v=4.5`.

---

## 3. Arquivos Afetados
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/financeiro-view.js`
- `frontend/assets/js/utils.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `Planejamento/2026-09-09_04_correcao_encavalamento_comboboxes_extrato.md`
