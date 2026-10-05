# Plano de Implementação - Correção da Largura Máxima da Combobox de Cliente no Orçamento

- **Data de Criação:** 05/10/2026
- **Autor:** Antigravity AI & Gustavo
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 05/10/2026 às 12:10:15 (Horário de Brasília)
  - **Transcrição da Aprovação do Usuário:** *"Proceed"*

---

## 1. Contexto e Diagnóstico

### 1.1 Sintoma
Ao abrir o modal **"ELABORAÇÃO ÁGIL DE ORÇAMENTO"** e selecionar um cliente com razão social e CNPJ extensos (ex: *"LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA EM RECUPERACAO JUDICIAL (09.027.059/0001-48)"*), o campo de seleção do cliente expande indefinidamente em largura. Isso empurra o campo **"Equipamento / Máquina"** para a direita e comprime/extrapola o campo **"Validade (Dias)"** para fora da área visível do modal (cortado pelo `overflow-x: hidden`).

### 1.2 Causa Raiz Técnica
1. **Ausência de `min-width: 0` no Flex Item do Gatilho da Combobox (`industrial-integrity.css`):**
   - O elemento `.emc-combobox-trigger` é um flex container (`display: flex`) e seu filho `.emc-combobox-trigger-text` possui `flex: 1`, `white-space: nowrap`, `overflow: hidden` e `text-overflow: ellipsis`.
   - Na especificação CSS Flexbox (CSS Flexbox Level 1, §4.5), flex items têm `min-width: auto` por padrão. Com `white-space: nowrap`, o tamanho intrínseco mínimo (`min-content`) do item passa a ser a largura total do texto sem quebras.
   - Sem `min-width: 0;`, o texto recusa o encolhimento, impedindo a atuação do `text-overflow: ellipsis` e forçando a combobox a alargar.
2. **Dimensionamento Mínimo Implícito no CSS Grid (`orcamentos-view.js`):**
   - O cabeçalho do formulário utiliza `grid-template-columns: 2fr 1fr 140px;`.
   - No CSS Grid, trilhas definidas com unidades `fr` possuem dimensão mínima `auto` (`minmax(auto, 2fr)`). Quando o conteúdo interno do grid item (o `.form-group` contendo a combobox) não tem restrição mínima de largura, a trilha inteira se estende para acomodar o texto longo.
3. **Ausência de Tooltip Nativo Informativo (`utils.js`):**
   - Ao truncar um nome longo de cliente com reticências, o operador precisa conseguir conferir o nome completo e o CNPJ passando o mouse sobre o elemento. Atualmente, `initSearchableSelect` não preenche o atributo `title` no gatilho.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Blindagem Global dos Componentes Combobox e Formulários (`frontend/assets/css/industrial-integrity.css`):**
   - Na classe `.form-group`:
     - Adicionar `min-width: 0;` para que qualquer campo de formulário inserido dentro de um Grid ou Flexbox respeite a coluna alocada e permita que seus componentes internos encolham adequadamente.
   - Nas classes `.emc-combobox` e `.emc-combobox-trigger`:
     - Adicionar `min-width: 0;` e `max-width: 100%;`.
   - Na classe `.emc-combobox-trigger-text`:
     - Adicionar `min-width: 0;`, ativando o truncamento com reticências (`text-overflow: ellipsis`) estritamente dentro da largura delimitada pela coluna.
   - Replicar a mesma proteção em `.emc-multiselect`, `.emc-multiselect-trigger` e `.emc-multiselect-trigger-text` para consistência e prevenção de bugs similares em seletores múltiplos.

2. **Calibração das Trilhas de Grid no Modal de Orçamentos (`frontend/assets/js/views/orcamentos-view.js`):**
   - Atualizar a declaração de grid do cabeçalho de orçamento (linha 213):
     - De: `grid-template-columns: 2fr 1fr 140px;`
     - Para: `grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) 140px;`
     - Isso assegura matematicamente que o campo de cliente nasça e se mantenha estritamente na proporção `2fr`, o de equipamento em `1fr` e a validade em `140px`, sem qualquer deslocamento lateral, independentemente do tamanho do nome do cliente.
   - Atualizar também as linhas dos seletores de itens (linhas 248, 268 e 288):
     - De: `grid-template-columns: 2fr 100px 140px 140px auto;`
     - Para: `grid-template-columns: minmax(0, 2fr) 100px 140px 140px auto;`
     - Prevenindo que produtos BOM ou insumos com nomes técnicos extensos empurrem os campos de quantidade, custo e venda.

3. **Melhoria Ergonômica de Tooltip (`frontend/assets/js/utils.js`):**
   - No método `atualizarTriggerText()` de `initSearchableSelect`, atribuir o texto selecionado ao atributo `title` do gatilho (`triggerText.title` e `trigger.title`).
   - Dessa forma, quando o texto for truncado com `...`, o usuário poderá passar o mouse e ler a razão social completa e o CNPJ em um tooltip nativo imediato.

4. **Sincronização Mandatória de Versão PWA e Cache Busting:**
   - Incrementar a versão `CACHE_NAME` no `frontend/sw.js` de `'emc-soldas-v4.50'` para `'emc-soldas-v4.51'`.
   - Atualizar a query string `?v=4.51` em `frontend/index.html` para os arquivos modificados.
   - Orientar o recarregamento via `Ctrl + Shift + R`.

---

## 3. Arquivos Afetados

- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/orcamentos-view.js`
- `frontend/assets/js/utils.js`
- `frontend/sw.js`
- `frontend/index.html`
- `Planejamento/2026-10-05_02_correcao_largura_maxima_combobox_cliente_orcamentos.md`
- `docs/STATUS.md`

---

## 4. Plano de Verificação e Testes

1. Executar suíte de testes automatizados: `python backend/manage.py test backend/`.
2. Validar que a combobox no modal de novo orçamento não deforma e que os campos adjacentes mantêm posicionamento e visibilidade perfeita.

---

## 5. Relatório de Execução e Homologação

- **Data de Conclusão:** 05/10/2026
- **Execução Realizada:**
  1. `frontend/assets/css/industrial-integrity.css`:
     - Adicionado `min-width: 0;` na classe `.form-group`.
     - Adicionado `min-width: 0; max-width: 100%;` em `.emc-combobox` e `.emc-combobox-trigger`.
     - Adicionado `min-width: 0;` em `.emc-combobox-trigger-text`, habilitando o encolhimento e o truncamento por reticências (`text-overflow: ellipsis`).
     - Adicionado `min-width: 0; max-width: 100%;` em `.emc-multiselect`, `.emc-multiselect-trigger` e `min-width: 0;` em `.emc-multiselect-trigger-text`.
  2. `frontend/assets/js/views/orcamentos-view.js`:
     - Atualizadas as trilhas de CSS Grid de cabeçalho e seletores de itens no modal de orçamentos para utilizar `minmax(0, 2fr)`, garantindo que a combobox nunca expanda além de sua cota proporcional inicial e impedindo qualquer deslocamento ou encavalamento de colunas.
  3. `frontend/assets/js/utils.js`:
     - Inserido suporte a tooltip nativo (`title`) em `initSearchableSelect` (`triggerText.title` e `container.title`), permitindo ao operador visualizar o nome completo e dados cadastrais ao passar o mouse sobre o texto truncado.
  4. Governança de Cache PWA:
     - Atualizado `CACHE_NAME` para `'emc-soldas-v4.51'` em `frontend/sw.js`.
     - Atualizadas as query strings de estilos e scripts para `?v=4.51` em `frontend/index.html`.
  5. Bateria de Testes Automatizados:
     - Executado `python backend/manage.py test backend/`: 201 testes executados e aprovados com 100% de sucesso (80.6s).
