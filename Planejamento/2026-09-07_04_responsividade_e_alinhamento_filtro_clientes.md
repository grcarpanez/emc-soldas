# Plano de Implementação: Alinhamento Contínuo e Responsividade da Barra de Clientes (v3.0)

- **Data de Elaboração:** 2026-09-07
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluído
- **Proceed do Usuário:** Aprovado em 2026-09-07 ("Tava mais bonito antes com a textbox maior. ela deveria reduzir só um pouco, pra caber o aumento da combobox. antes estava a combobox junto com os outros botoes, tendo apenas o espaçamento entre os 4 elementos, igual. ajuste a textbox pra que os 4 elementos cubram o espaço da div que estão inserdos. Estou mandando também 3 prints com redução progressiva da janela pra que observe a responsividade. em certo ponto (imagem do meio), a combobox é engolida...")

---

## 1. Contexto e Diagnóstico

Com base nas 4 capturas de tela fornecidas pelo usuário:
1. **Espaço Vazio no Meio (Print 1):** O `max-width: 380px` com `justify-content: space-between` impedia o crescimento orgânico da caixa de busca, deixando um vazio incômodo entre o filtro de tipo e os botões à direita.
2. **Achatamento da Combobox (Prints 2 e 3):** Em janelas intermediárias, o sub-bloco flex esquerdo era comprimido contra o bloco direito. Como a combobox não possuía `flex-shrink: 0`, ela era espremida e engolida, truncando o texto para `"FORNEC"` e colidindo com os botões.
3. **Expectativa Visual do Usuário:** Os 4 elementos (Busca, Combobox, Cadastro Rápido e Novo Cadastro) devem cobrir 100% da largura da div em fluxo contínuo, com espaçamento idêntico (`gap: 10px`) entre cada um deles e sem que a combobox seja engolida nas reduções de tela.

---

## 2. Decisões Técnicas Implementadas

1. **Estrutura Flex Unificada em `cadastros-view.js`:**
   - Eliminada a divisão de dois blocos com `justify-content: space-between`.
   - Container único: `display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;`.
   - Espaçamento homogêneo de `10px` entre todos os 4 elementos.
2. **Preenchimento Total da Div (Sem Buracos):**
   - Caixa de busca com `flex: 1; min-width: 200px;` (sem limite artificial de largura máxima), preenchendo automaticamente toda a extensão da div até encostar na combobox.
3. **Blindagem Anti-Esmagamento da Combobox:**
   - `<select id="filtro-cliente-tipo">` configurado com `width: 175px; min-width: 175px; flex-shrink: 0;`.
   - Com `flex-shrink: 0`, a combobox é protegida contra qualquer compressão pelo navegador, mantendo o texto `"FORNECEDORES"` sempre 100% nítido.
4. **Quebra Responsiva Suave:**
   - Botões agrupados com `display: flex; gap: 10px; flex-shrink: 0; white-space: nowrap;`.
   - Ao reduzir a janela, quando não houver espaço suficiente para os 4 itens na mesma linha, os dois botões quebram suavemente em bloco para a linha inferior sem nunca sobrepor a combobox.
5. **Governança de Assets PWA (Regra 12 de `AGENTS.md`):**
   - `frontend/sw.js`: Versão elevada para `emc-soldas-v3.0`.
   - `frontend/index.html`: Sufixos atualizados para `?v=3.0` em todos os scripts e folhas de estilo CSS.
6. **Atualização nos Arquivos Vivos:**
   - `docs/STATUS.md` atualizado na Fase 14.5.

---

## 3. Arquivos Modificados

- `frontend/assets/js/views/cadastros-view.js` (Layout flex unificado, gap 10px, busca flex: 1, combobox flex-shrink: 0)
- `frontend/sw.js` (Versão `v3.0`)
- `frontend/index.html` (Sufixos `?v=3.0`)
- `Planejamento/2026-09-07_04_responsividade_e_alinhamento_filtro_clientes.md` (Este documento)
- `docs/STATUS.md` (Registro de avanço na Fase 14.5)

---

## 4. Verificação e Resultados

- [x] Testes unitários de cadastros: 16 testes aprovados com 100% de sucesso (`OK`).
- [x] Em janelas largas: 4 elementos cobrem 100% da div com gap homogêneo de 10px entre si.
- [x] Em janelas intermediárias: a combobox não é engolida nem sobreposta; os botões quebram juntos com suavidade.
