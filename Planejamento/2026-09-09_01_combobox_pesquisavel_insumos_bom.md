# Registro de Planejamento: Combobox Pesquisável com Autocomplete para Insumos na Ficha Técnica (BOM) (PWA v4.2)

- **Identificador:** `Planejamento/2026-09-09_01_combobox_pesquisavel_insumos_bom.md`
- **Data:** 2026-09-09
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-09T15:21:03-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Objetivos
Aprimorar a experiência de uso da seleção de insumos na Ficha Técnica (BOM) em `/#catalogo`, transformando o elemento `<select>` nativo estático em um componente pesquisável com digitação e autocomplete em tempo real (`window.EMCUtils.initSearchableSelect`), idêntico ao componente já utilizado no cadastro de frota/veículos e em orçamentos. A mudança resolve a limitação da rolagem manual conforme o número de matérias-primas e insumos cadastrados cresce.

---

## 2. Decisões Técnicas e Arquiteturais
- **Frontend (`catalogo-view.js`):**
  - Ordenar alfabeticamente a lista de itens do catálogo recuperada da API (`listaItens.sort(...)`).
  - Após a abertura do modal (`window.EMCUtils.openModal`), instanciar `window.EMCUtils.initSearchableSelect` no elemento `#add-ficha-item-id`.
  - Configurar placeholder amigável `'SELECIONE OU BUSQUE UM INSUMO...'`.
- **Governança PWA (Regra Mandatória 12 do AGENTS.md):**
  - Elevação da constante `CACHE_NAME` para `'emc-soldas-v4.2'` em `frontend/sw.js`.
  - Atualização dos sufixos de script e estilo para `?v=4.2` em `frontend/index.html`.
- **Documentação e Auditoria:**
  - Atualização viva de `docs/STATUS.md`.

---

## 3. Arquivos Modificados
- `frontend/assets/js/views/catalogo-view.js`: ordenação alfabética e inicialização de `initSearchableSelect` em `gerenciarFichaTecnica`.
- `frontend/sw.js`: atualização do cache para `emc-soldas-v4.2`.
- `frontend/index.html`: cache-busting `?v=4.2` em todos os assets.
- `docs/STATUS.md`: documentação viva atualizada.

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes Automatizados:**
   - Teste de backend do app catálogo (`apps.catalogo`).
2. **Versionamento PWA:**
   - Bundles sincronizados para `v4.2` em `sw.js` e `index.html`.
