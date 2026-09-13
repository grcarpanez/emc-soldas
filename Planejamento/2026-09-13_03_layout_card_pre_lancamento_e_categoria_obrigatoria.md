# Plano de Implementação: Alinhamento do Botão ✕ e Categoria DRE Obrigatória em Branco

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed:** Aprovado formalmente pelo usuário em 2026-09-13 13:24:09 ("Aprovado. Execute, por favor").

---

## 1. Contexto e Objetivos
O usuário solicitou dois ajustes cruciais na experiência do Modo Importação Total da Conciliação Bancária:
1. **Correção de Alinhamento do Botão `✕` e Layout do Card:** O card de pré-lançamento herdou acidentalmente `display: flex; flex-direction: row;` da classe `.split-item`, o que espremeu todos os elementos em uma única linha horizontal deformada (título, valor, botão ✕, campo de descrição e select). Devemos reestruturar o card em duas linhas limpas e bem espaçadas:
   - **Linha 1 (Cabeçalho):** Identificador/Data na esquerda e Valor formatado com Botão `✕` perfeitamente alinhados na direita.
   - **Linha 2 (Edição):** Grid proporcional com campo de Descrição (editável) e Select de Categoria DRE.
2. **Categoria DRE Inicial em Branco e Obrigatória:**
   - Atualmente o sistema pré-selecionava a primeira categoria encontrada (ex: "ENERGIA ELÉTRICA E ÁGUA"), o que induz a erro contábil caso o usuário não perceba.
   - O select deve inicializar em branco (`value=""`, `-- SELECIONE A CATEGORIA DRE * --`).
   - O botão mestre de importação em lote deve permanecer bloqueado enquanto houver itens ativos sem categoria selecionada, exibindo `⚡ SELECIONE AS CATEGORIAS (N PENDENTES)`.

---

## 2. Decisões Técnicas e Arquiteturais
- **Layout Vertical Forçado no Card:**
  Adicionar regras explícitas em `industrial-integrity.css` para que `.pre-lancamento-card` tenha `display: flex !important; flex-direction: column !important; gap: 8px !important;`, mantendo o botão circular de conexão `.anchor-node.left` na borda esquerda intacto.
- **Botão `✕` Padronizado:** Definir dimensões industriais de 26x24px, 0px border-radius e centralização flex, posicionado de forma limpa ao lado do valor numérico no topo direito.
- **Validação de Categorias em Tempo Real:**
  - Inicialização com `categoria_id: null`.
  - Opção vazia obrigatória no topo do select.
  - O botão de importação em lote reflete dinamicamente a contagem de categorias pendentes de preenchimento (`⚡ SELECIONE AS CATEGORIAS (N PENDENTES)`), liberando o clique apenas quando 100% dos lançamentos ativos estiverem devidamente classificados.
- **Versionamento PWA:** Elevação para `v4.21` no `sw.js` e `index.html`.

---

## 3. Arquivos Afetados
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/conciliacao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `walkthrough.md`
