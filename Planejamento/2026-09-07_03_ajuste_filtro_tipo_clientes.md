# Plano de Implementação: Ajuste da Combobox de Filtro de Clientes e Layout (v2.9)

- **Data de Elaboração:** 2026-09-07
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluído
- **Proceed do Usuário:** Aprovado em 2026-09-07 ("Temos uma combobox de filtro na tela de cadastro de clientes, com as opções, TODOS OS TIPOS, CLIENTES, FORNECEDORES, AMBOS. Temos duas opções redundantes. Precisamos ajustar o TODOS OS TIPOS para apenas TODOS e excluir o AMBOS, além de reduzir a textbox de busca, para conseguir aumentar um pouco a combobox, porque a opção FORNECEDORES não está cabendo...")

---

## 1. Contexto e Objetivos

Na tela de Cadastros de Clientes & Fornecedores:
1. A combobox de filtro por tipo continha opções redundantes: `TODOS OS TIPOS` e `AMBOS`.
2. A opção `FORNECEDORES` excedia a largura visual da combobox de `160px`, ficando cortada como `"FORNECEDORE"`.
3. A textbox de busca ocupava espaço excessivo, limitando o crescimento da combobox.

### Decisão de Refinamento
- Renomear `TODOS OS TIPOS` para `TODOS` (com valor vazio `""`).
- Excluir a opção redundante `AMBOS`.
- Definir largura confortável de `180px` (`width: 180px; min-width: 180px;`) para o `<select id="filtro-cliente-tipo">`, permitindo visualização completa de `FORNECEDORES`.
- Limitar a textbox de busca `#filtro-cliente-busca` com `max-width: 380px`.
- Elevar a versão do sistema e do Service Worker para `v2.9` com cache-busting nos scripts e CSS (`?v=2.9`).

---

## 2. Decisões Técnicas Implementadas

1. **Frontend (`frontend/assets/js/views/cadastros-view.js`):**
   - Alterado HTML do filtro de tipo para conter apenas:
     - `<option value="">TODOS</option>`
     - `<option value="CLIENTE">CLIENTES</option>`
     - `<option value="FORNECEDOR">FORNECEDORES</option>`
   - Aplicado `width: 180px; min-width: 180px;` na combobox.
   - Aplicado `max-width: 380px` na textbox de busca.
2. **Versionamento PWA (Regra 12 de `AGENTS.md`):**
   - `frontend/sw.js`: `CACHE_NAME` atualizado para `'emc-soldas-v2.9'`.
   - `frontend/index.html`: Todas as tags `<script>` e `<link rel="stylesheet">` atualizadas para `?v=2.9`.
3. **Atualização nos Arquivos Vivos:**
   - `docs/STATUS.md` atualizado na Fase 14.5.

---

## 3. Arquivos Modificados

- `frontend/assets/js/views/cadastros-view.js` (Ajuste das opções e dimensões da combobox e busca)
- `frontend/sw.js` (Incremento para versão `v2.9`)
- `frontend/index.html` (Sufixo `?v=2.9` em CSS e scripts)
- `Planejamento/2026-09-07_03_ajuste_filtro_tipo_clientes.md` (Este documento)
- `docs/STATUS.md` (Registro na Fase 14.5)

---

## 4. Verificação e Resultados

- [x] Testes unitários do Django executados: 16 testes de cadastros aprovados com 100% de sucesso (`OK`).
- [x] Combobox exibe `TODOS`, `CLIENTES` e `FORNECEDORES` sem cortes.
- [x] Busca harmoniosa com `max-width: 380px`.
