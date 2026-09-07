# Registro de Planejamento: Combobox Pesquisável com Autocomplete Industrial para Proprietários de Equipamentos (PWA v3.3)

- **Identificador:** `Planejamento/2026-09-07_08_combobox_pesquisavel_proprietario_equipamentos.md`
- **Data:** 2026-09-07
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-07T15:53:54-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Objetivos
Aprimorar a experiência de uso da combobox de proprietários na aba de Equipamentos & Veículos (`/#cadastros`), transformando o select estático em um componente pesquisável com digitação e autocomplete em tempo real (`window.EMCUtils.initSearchableSelect`), idêntico ao componente utilizado no modal de vinculação de equipamentos e em orçamentos.

---

## 2. Decisões Técnicas e Arquiteturais
- **Frontend (`cadastros-view.js`):**
  - Envolver o select `#filtro-equip-proprietario` em um wrapper estilizado de `270px` (`min-width: 230px; flex-shrink: 0;`).
  - Após carregar e ordenar a lista alfabética de clientes, invocar `window.EMCUtils.initSearchableSelect(select, { placeholder: 'TODOS OS PROPRIETÁRIOS' })`.
  - Ao selecionar qualquer opção (ou usar o teclado), o evento `change` dispara automaticamente `carregarListaEquipamentos()`.
- **Governança PWA (Regra Mandatória 12):**
  - Elevação de `CACHE_NAME` para `'emc-soldas-v3.3'` em `frontend/sw.js`.
  - Atualização dos sufixos de script e estilo para `?v=3.3` em `frontend/index.html`.

---

## 3. Arquivos Modificados
- `frontend/assets/js/views/cadastros-view.js`: wrapper e integração de `initSearchableSelect` em `renderEquipamentos` e `carregarSelectProprietariosEquip`.
- `frontend/sw.js`: versão `emc-soldas-v3.3`.
- `frontend/index.html`: query strings `?v=3.3`.
- `docs/STATUS.md`: documentação viva atualizada.

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes Automatizados:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test apps.cadastros`
   - Resultado: 19 testes executados com 100% de aprovação (`OK`).
2. **Versionamento PWA:**
   - Bundles sincronizados para `v3.3` em `sw.js` e `index.html`.
