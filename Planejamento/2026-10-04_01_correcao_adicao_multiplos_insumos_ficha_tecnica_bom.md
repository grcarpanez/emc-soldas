# Plano de Implementação - Correção da Adição de Múltiplos Insumos na Ficha Técnica (BOM)

- **Data de Criação:** 04/10/2026
- **Autor:** Antigravity AI & Gustavo
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 04/10/2026 às 11:34:57 (Horário de Brasília)
  - **Transcrição da Aprovação do Usuário:** *"Verdade. Testei aqui e ele vai sobreponto varios modais. Pode executar o plano, por favor."*

---

## 1. Contexto e Diagnóstico

### 1.1 Sintoma
Ao tentar adicionar itens à Ficha Técnica de um produto (BOM), o usuário conseguia adicionar com sucesso apenas o primeiro item (geralmente uma das chapas, primeiros itens na ordenação alfabética). Ao tentar adicionar insumos seguintes como `OXIGENIO`, `PARAFUSO` ou `PREGO`, o clique no botão `+ ADICIONAR` ficava completamente inerte, sem requisições HTTP e sem erros.

### 1.2 Causa Raiz
No arquivo `frontend/assets/js/views/catalogo-view.js`:
1. `gerenciarFichaTecnica(produtoId)` abria o modal chamando `window.EMCUtils.openModal(...)`.
2. Após o `POST /api/fichas-tecnicas/` ou `DELETE`, a rotina chamava recursivamente `this.gerenciarFichaTecnica(produtoId)` para recarregar.
3. `openModal` inseria uma nova overlay no topo sem fechar nem atualizar o modal existente.
4. Os elementos com os mesmos IDs (`#btn-add-item-ficha`, `#add-ficha-item-id`, `#add-ficha-qtd`) passavam a existir duplicados no DOM.
5. `document.getElementById` capturava sempre os elementos do primeiro modal (invisível, que ficou embaixo).
6. O botão do modal do topo ficava sem listener de eventos, inoperante.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Ciclo de Vida Único de Modal (Single Modal Lifecycle):**
   - O modal da Ficha Técnica é instanciado uma única vez.
   - Criada a rotina interna `_atualizarFichaModal(pId)` que:
     - Busca o produto atualizado com seus itens de ficha técnica via `GET /api/produtos/{id}/`.
     - Renderiza dinamicamente as linhas em `#ficha-tecnica-tbody`.
     - Atualiza os valores da memória de cálculo em tempo real (`#bom-custo-materiais`, `#bom-custo-mo`, `#bom-preco-apurado`).
     - Limpa o campo `#add-ficha-qtd`.
     - Reseta a combobox pesquisável (`selItemFicha._emcCombobox.setValue('')`).
     - Atualiza as opções da combobox para exibir apenas os insumos ainda não inclusos na receita do produto.
     - Sincroniza a tabela de listagem do catálogo em background (`this.carregarListaProdutos()`).

2. **Aprimoramento de UX e Usabilidade:**
   - Desabilitar temporariamente o botão durante a requisição de adição para evitar duplicações por múltiplos cliques rápidos.
   - Permitir adicionar teclando `Enter` no campo de quantidade.
   - Tratar a exclusão (`removerItemFicha`) também atualizando o mesmo modal sem reabrir janelas.

3. **Governança de Versão e Cache PWA:**
   - Incrementar `CACHE_NAME` de `emc-soldas-v4.48` para `emc-soldas-v4.49` em `frontend/sw.js`.
   - Atualizar a query string `?v=4.49` em `frontend/index.html`.

---

## 3. Arquivos Afetados

- `frontend/assets/js/views/catalogo-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `docs/ERROS.md`
- `Planejamento/2026-10-04_01_correcao_adicao_multiplos_insumos_ficha_tecnica_bom.md`

---

## 4. Plano de Verificação e Testes

1. Executar suíte de testes de backend: `python backend/manage.py test apps.catalogo` e testes globais.
2. Validar no navegador:
   - Adicionar o 1º insumo (Chapa).
   - Adicionar o 2º insumo (Oxigênio).
   - Adicionar o 3º insumo (Parafuso).
   - Adicionar o 4º insumo (Prego).
   - Remover um insumo e verificar a reatividade.
   - Fechar o modal e verificar que nenhum modal extra ficou na tela.

---

## 5. Relatório de Execução e Homologação

- **Data de Conclusão:** 04/10/2026
- **Execução Realizada:**
  1. `catalogo-view.js`: Implementado Single Modal Lifecycle em `gerenciarFichaTecnica` e `removerItemFicha` com a rotina reativa `_atualizarFichaModal`. A adição e remoção agora atualizam o DOM diretamente no modal aberto, sem sobreposição de overlays.
  2. Suporte ao `Enter` no campo de quantidade e debounce no botão `+ ADICIONAR`.
  3. Atualização automática da combobox de insumos (`updateOptions`) filtrando itens já presentes na receita.
  4. Sincronização do cache PWA: `v4.48` -> `v4.49` em `sw.js` e `index.html`.
  5. Atualizados os arquivos vivos `docs/STATUS.md` e `docs/ERROS.md`.
  6. Suíte de testes automatizados do Django (`python backend/manage.py test backend/`) executada com sucesso absoluto: 200 testes aprovados (100% OK em 81.8s).
