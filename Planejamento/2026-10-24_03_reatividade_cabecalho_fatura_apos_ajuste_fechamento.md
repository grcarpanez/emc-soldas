# Plano de Implementação: Reatividade Instantânea do Cabeçalho e Totais da Fatura após Ajuste de Fechamento

- **Data:** 24/10/2026
- **Autor:** Antigravity (Pair Programming com Usuário)
- **Status:** Concluído (Validado com Sucesso)
- **Registro do Proceed:** Aprovado pelo usuário em 24/10/2026 às 23:47 via mensagem "Proceed".

---

## 1. Contexto e Diagnóstico do Problema

### 1.1 Relato do Usuário
> *"Agora só precisamos ajustar uma coisa. Quando altero o fechamento da fatura, o recálculo estaá correto, os lançamentos da fatura são atualizados, o valor da fatura é atualizado no backend, mas na view, o valor da fatura não é atualizado, nem a data de fechamento da fatura, só depois que aperto F5"*

### 1.2 Diagnóstico Técnico e Causa Raiz
Na visualização de Cartões Corporativos (`frontend/assets/js/views/financeiro-view.js`):
1. Ao confirmar o modal de ajuste de fechamento (`abrirModalAjustarFechamento`), a função dispara `POST /api/faturas-cartao/{id}/ajustar-fechamento/` e, em seguida, invoca `await this.carregarMetricasEFaturasCartao()`.
2. Em `carregarMetricasEFaturasCartao`:
   - A lista de faturas é recarregada da API (`this.faturasLista = resFaturas.results || ...`), trazendo novas instâncias de objetos com `data_fechamento_real`, `total_despesas` e `data_vencimento_calculada` devidamente recalculados.
   - **Porém**, a seleção da fatura ativa no código estava escrita como:
     ```javascript
     if (!this.faturaAtiva || !this.faturasLista.some(f => f.id === this.faturaAtiva.id)) {
       const aberta = this.faturasLista.find(f => f.status === 'ABERTA');
       this.faturaAtiva = aberta || this.faturasLista[0];
     }
     ```
   - Como `this.faturaAtiva` já estava populado com a fatura selecionada, a condição `this.faturasLista.some(f => f.id === this.faturaAtiva.id)` avaliava como `true`, fazendo com que o `if` fosse ignorado.
   - Dessa forma, `this.faturaAtiva` **continuava apontando para o objeto JavaScript em memória antigo**, que ainda continha a data de fechamento antiga e o total desatualizado.
3. Quando `carregarDetalhesFaturaAtiva()` era executado logo após:
   - A chamada para `/itens/` buscava os novos itens da fatura na API e renderizava a tabela com as compras atualizadas (conforme evidenciado na imagem enviada pelo usuário, exibindo apenas o item #149 de R$ 1,00).
   - **Porém**, o cabeçalho superior lia `f = this.faturaAtiva`, renderizando `f.total_despesas` e `f.data_fechamento_real` a partir da referência de memória antiga (exibindo ainda `10/10/2026` e `R$ 303,00`).
4. Ao pressionar `F5`, a SPA era recarregada com `this.faturaAtiva = null`, forçando a leitura da nova instância da fatura a partir de `this.faturasLista[0]`, motivo pelo qual o F5 resolvia o problema.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Re-sincronização do Objeto da Fatura Ativa (`financeiro-view.js`):**
   - Em `carregarMetricasEFaturasCartao()`, reassociar a referência de `this.faturaAtiva` para a instância atualizada correspondente dentro de `this.faturasLista`:
     ```javascript
     if (this.faturaAtiva) {
       this.faturaAtiva = this.faturasLista.find(f => f.id === this.faturaAtiva.id) || null;
     }
     if (!this.faturaAtiva) {
       const aberta = this.faturasLista.find(f => f.status === 'ABERTA');
       this.faturaAtiva = aberta || this.faturasLista[0];
     }
     ```
   - Essa correção garante reatividade instantânea não apenas no ajuste de fechamento, mas também em lançamentos de despesas, fechamentos de fatura, liquidações e remanejamentos.
2. **Atualização Imediata e Reativa no Callback de Ajuste de Fechamento:**
   - Como o endpoint de ajuste de fechamento já devolve a fatura atualizada em `res.dados.fatura`, atualizaremos preventivamente `this.faturaAtiva = dados.fatura` antes de chamar `carregarMetricasEFaturasCartao()`, proporcionando uma atualização fluida e livre de estados stale.
3. **Versionamento e Governança PWA:**
   - Atualizar a constante `CACHE_NAME` em `frontend/sw.js` para `'emc-soldas-v4.67'`.
   - Atualizar as query strings de versão em todas as tags `<script>` e `<link>` em `frontend/index.html` para `?v=4.67`.

---

## 3. Arquivos a Modificar

| Arquivo | Ação | Descrição |
|---|---|---|
| `frontend/assets/js/views/financeiro-view.js` | Modificar | Reassociar `this.faturaAtiva` ao recarregar faturas e sincronizar dados no ajuste de fechamento |
| `frontend/sw.js` | Modificar | Atualizar `CACHE_NAME` para `emc-soldas-v4.67` |
| `frontend/index.html` | Modificar | Atualizar query string para `?v=4.67` |
| `docs/STATUS.md` | Modificar | Atualizar data e checklist com a melhoria de reatividade |
| `docs/ERROS.md` | Modificar | Documentar retenção de referência de objeto em memória no frontend |

---

## 4. Plano de Verificação e Testes

1. **Verificação no Navegador:**
   - Recarregar a página com `Ctrl + Shift + R` para ativar o Service Worker `v4.67`.
   - Acessar **Financeiro** > aba **Cartões Corporativos**.
   - Clicar em `AJUSTAR FECHAMENTO REAL` na fatura `2026-10` e alterar a data (ex: antecipar para dia 05 ou retornar para dia 10).
   - Verificar se o **Corte / Fechamento Real** e o **TOTAL DA FATURA** no cabeçalho superior mudam instantaneamente no ato da confirmação do modal, sem necessidade de recarregar a página (`F5`).
2. **Suíte de Testes Automatizados:**
   - Executar `python backend/manage.py test backend/` para confirmar 100% de integridade em todos os testes.

---

## 5. Relatório de Execução e Evidências de Validação

- **Data de Conclusão:** 24/10/2026
- **Status Final:** Concluído com Sucesso

### 5.1 O que foi Executado
1. **Re-sincronização de Estado no Frontend (`frontend/assets/js/views/financeiro-view.js`):**
   - Em `carregarMetricasEFaturasCartao()`, implementada a re-associação do objeto ativo:
     `this.faturaAtiva = this.faturasLista.find(f => f.id === this.faturaAtiva.id) || null;`
     Garantindo que a referência em memória seja atualizada com a nova instância recebida da API (`total_despesas`, `data_fechamento_real`, `status`, etc.).
   - Em `abrirModalAjustarFechamento`, adicionada a atribuição proativa `this.faturaAtiva = dados.fatura` antes de invocar `carregarMetricasEFaturasCartao()`.
   - Agora, ao alterar a data de fechamento real, o cabeçalho superior (Corte / Fechamento Real e Total da Fatura) e os itens da tabela são atualizados instantaneamente sem necessidade de recarregar a página (`F5`).
2. **Versionamento e Governança PWA:**
   - Atualizado o Service Worker `frontend/sw.js` para a versão `emc-soldas-v4.67`.
   - Atualizadas todas as 19 query strings de assets no `frontend/index.html` para `?v=4.67`.
3. **Validação de Testes:**
   - 43 testes automatizados de `apps.financeiro` executados e 100% aprovados.
