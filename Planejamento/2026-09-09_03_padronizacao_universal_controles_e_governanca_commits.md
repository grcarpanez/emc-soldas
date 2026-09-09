# Registro de Planejamento: Padronização Visual Universal de Controles e Resolução de Erros de Tela (PWA v4.4)

- **Identificador:** `Planejamento/2026-09-09_03_padronizacao_universal_controles_e_governanca_commits.md`
- **Data:** 2026-09-09
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-09T16:22:07-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação ("Plano Aprovado!"). Também determinou a inclusão da regra mandatória de commits semânticos por etapa aprovada no `AGENTS.md` e a replicação integral do guia de boas práticas e convenções de commit como seção no `docs/FSD.md`.

---

## 1. Contexto e Objetivos
1. Corrigir o erro de runtime `Cannot read properties of undefined (reading 'render')` na tela de Compras (`/#compras`).
2. Eliminar o desnível de altura entre comboboxes (`.emc-combobox`, `.emc-multiselect`) e os demais controles de formulário (`.form-control`, `.btn`), padronizando a altura canônica para **42px**.
3. Eliminar divergências cromáticas de texto e risco de encavalamento visual nas comboboxes.
4. Documentar minuciosamente no `docs/DESIGN.md` a seção normativa de Controles Interativos e Consistência Dimensional (42px padrão, fontes, cores de superfícies e bordas).
5. Estabelecer e registrar a regra mandatória de commits atômicos semânticos (Conventional Commits) no `AGENTS.md` e como seção oficial no `docs/FSD.md`.
6. Elevar a versão do PWA para `v4.4` com cache-busting sincronizado.

---

## 2. Decisões Técnicas e Arquiteturais
- **Backend:** Mantido estável (todos os 73 testes aprovados).
- **Frontend CSS (`industrial-integrity.css`):**
  - Adição da variável `--color-rust-orange-bright: #ff6b35;` no `:root`.
  - Fixação de `height: 42px; box-sizing: border-box !important;` em `.form-control`, `select.form-control`, `.btn`, `.emc-combobox-trigger` e `.emc-multiselect-trigger`.
  - Padronização de alinhamento vertical flex e `line-height: normal` para os rótulos internos.
- **Frontend JS (`compras-view.js`):**
  - Adicionar `async` na declaração de `render(container)`.
- **Governança (`AGENTS.md` e `docs/FSD.md`):**
  - Criação da Regra Mandatória 13 no `AGENTS.md` exigindo commit formal do Git a cada etapa de Implementation Plan concluída, seguindo o padrão Conventional Commits.
  - Inclusão da Seção 30 no `docs/FSD.md` reproduzindo integralmente o Guia de Boas Práticas, Convenções e Prefixos do Git.
- **Versionamento PWA:**
  - `frontend/sw.js`: `CACHE_NAME = 'emc-soldas-v4.4';`
  - `frontend/index.html`: `?v=4.4` em todos os scripts e styles.

---

## 3. Arquivos Afetados
- `frontend/assets/js/views/compras-view.js`
- `frontend/assets/css/industrial-integrity.css`
- `docs/DESIGN.md`
- `AGENTS.md`
- `docs/FSD.md`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
