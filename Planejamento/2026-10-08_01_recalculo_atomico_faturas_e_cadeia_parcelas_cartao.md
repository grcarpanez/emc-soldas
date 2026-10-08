# Plano de Implementação - Recálculo Atômico de Faturas, Deslocamento em Cadeia de Parcelas e Governança de Faturas Fechadas/Pagas

- **Data:** 08/10/2026
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Usuário autorizou em 08/10/2026 às 16:40 ("Proceed").

---

## 1. Contexto e Objetivos

Corrigir a lógica de recálculo de faturas de Cartão Corporativo (`recalcular_faturas_cartao` e `ajustar_fechamento_fatura` em `backend/apps/financeiro/services_cartao.py`) para que:
1. Ao alterar o dia de fechamento padrão do cartão ou ajustar a data de fechamento de uma fatura, qualquer compra afetada (à vista ou parcelada em N vezes) tenha **todas as suas parcelas recalculadas e redistribuídas em cadeia sequencial**, eliminando o acúmulo de múltiplas parcelas da mesma compra em uma única fatura e prevenindo lacunas de meses vazios.
2. Compras fora da faixa de alteração da data de fechamento (ex: compras anteriores ao novo corte ou posteriores ao corte anterior) sejam estritamente preservadas em suas faturas correspondentes.
3. No frontend (`frontend/assets/js/views/financeiro-view.js`), a opção *"A partir de uma competência específica..."* permita escolher livremente qualquer mês e ano passado ou futuro através de um seletor nativo `<input type="month">`, sem se restringir às faturas abertas existentes.
4. Caso a competência inicial de recálculo atinja faturas já **FECHADAS** ou **PAGAS**, o sistema apresente um alerta de impacto ao usuário antes de gravar, detalhando as consequências contábeis (recalculo de títulos de Contas a Pagar e possível divergência de extrato já liquidado), permitindo ao usuário decidir conscientemente entre cancelar ou prosseguir (`confirmar_retroativo_fechadas=True`).

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Identificação e Reposicionamento em Cadeia de Parcelas
* **`grupo_pagamento_id` Garantido:** Em `lancar_despesa_cartao`, se `grupo_pagamento_id` não for informado, gerar automaticamente `uuid.uuid4()` para vincular todas as parcelas da compra (tanto para 1x quanto para Nx).
* **Resiliência para Legados:** Caso existam compras antigas com `grupo_pagamento_id IS NULL` e `total_parcelas > 1`, agrupá-las por `(cartao_credito, data_competencia, total_parcelas, descricao_base)` e atribuir um UUID comum.
* **Cálculo da Fatura Base:**
  * Compra em data $D$ com fechamento no dia $F$: se $D \le F$ vai para o mês da compra; se $D > F$ vai para o mês seguinte.
* **Deslocamento Atômico de Todas as Parcelas:**
  * Para uma compra em $N$ parcelas, se a Parcela 1 for para o mês $M$, a Parcela 2 irá estritamente para $M+1$, Parcela 3 para $M+2$, etc.
  * Compras fora da faixa (ex: dia 04 ou dia 12 no caso de 5 e 10) mantêm suas faturas originais sem sofrer alteração.

### 2.2 Governança de Faturas Fechadas e Pagas
* **Validação no Backend (`recalcular_faturas_cartao`):**
  * Parâmetro booleano `confirmar_retroativo_fechadas` (default `False`).
  * Se existirem faturas com status `FECHADA` ou `PAGA` no intervalo $\ge$ `competencia_inicial`:
    * Se `confirmar_retroativo_fechadas == False`: bloqueia com `ValidationError` estruturado listando as faturas fechadas/pagas encontradas e solicitando confirmação.
    * Se `confirmar_retroativo_fechadas == True`:
      * Atualiza `data_fechamento_real` de todas as faturas do intervalo.
      * Reposiciona as compras elegíveis entre as faturas.
      * Para cada fatura `FECHADA` afetada, recalcula a soma de despesas e atualiza o valor e vencimento do título em Contas a Pagar (`LancamentoFinanceiro` mestre).
      * Registra em log de auditoria detalhado a intervenção retroativa autorizada pelo usuário.

### 2.3 Frontend: Seletor Mês/Ano e Modal de Alerta
* Em `frontend/assets/js/views/financeiro-view.js` (`abrirModalNovoCartao`):
  * Substituir o `<select>` estático por um campo nativo `<input type="month" id="cartao-mes-especifico" class="form-control mono-text">`, permitindo escolher qualquer mês e ano livremente.
  * Antes de submeter o salvamento, verificar se há faturas `FECHADA` ou `PAGA` $\ge$ à competência escolhida.
  * Se houver, exibir modal de aviso de alto impacto (*Industrial Integrity*):
    * Lista as faturas fechadas/pagas encontradas.
    * Explica os impactos: reajuste de valores no Contas a Pagar e possível divergência com extratos bancários já liquidados.
    * Permite ao usuário cancelar ou clicar em **"CONFIRMAR E RECALCULAR MESMO ASSIM"** (enviando `confirmar_retroativo_fechadas: true`).

---

## 3. Arquivos a Modificar

1. `backend/apps/financeiro/services_cartao.py`
2. `backend/apps/financeiro/views.py`
3. `backend/apps/financeiro/tests.py`
4. `frontend/assets/js/views/financeiro-view.js`
5. `frontend/sw.js` (incremento de cache)
6. `frontend/index.html` (cache-busting query strings)
7. `docs/STATUS.md`

---

## 4. Plano de Verificação e Testes

1. Executar suíte de testes com `python backend/manage.py test apps.financeiro`.
2. Validar recálculo em lote e individual com 3 parcelas de compras em 07/10 entre os dias 5 e 10 (ida e volta).
3. Validar estabilidade de compras em 04/10 e 12/10.
4. Validar comportamento de faturas fechadas com e sem confirmação retroativa.

---

## 5. Relatório de Execução e Evidências

- **Implementação do Backend:**
  - `backend/apps/financeiro/services_cartao.py`: Implementadas as funções `adicionar_meses_competencia`, `determinar_fatura_base_compra`, `agrupar_lancamentos_por_compra` e `reposicionar_compra_cartao`. Atualizadas `lancar_despesa_cartao`, `ajustar_fechamento_fatura` e `recalcular_faturas_cartao` com suporte à cadeia contínua de parcelas, sincronização de Contas a Pagar para faturas fechadas e trava de governança `confirmar_retroativo_fechadas`.
  - `backend/apps/financeiro/views.py`: Adicionado suporte ao parâmetro `confirmar_retroativo_fechadas` nos endpoints de atualização de cartão e na ação `recalcular_faturas`.
- **Implementação do Frontend:**
  - `frontend/assets/js/views/financeiro-view.js`: Substituído seletor de faturas por `<input type="month">` para escolha irrestrita de competência retroativa/futura. Implementado modal de aviso de alto impacto com confirmação explícita para faturas fechadas/pagas.
  - `frontend/sw.js`: Versão de cache elevada para `'emc-soldas-v4.64'`.
  - `frontend/index.html`: Tags de script e stylesheet atualizadas para `?v=4.64`.
- **Validação de Testes Automatizados:**
  - `test_recalculo_em_cadeia_parcelas_cartao_dia_10_para_dia_5_e_volta`: Validada a transição da compra de 07/10 em 3 parcelas de (10/2026, 11/2026, 12/2026) para (11/2026, 12/2026, 01/2027) ao mudar fechamento do dia 10 para o dia 5, e o retorno exato ao alterar de volta para o dia 10. Validada a permanência intacta das compras de 04/10 (10/2026, 11/2026) e 12/10 (11/2026).
  - `test_recalculo_bloqueio_faturas_fechadas_sem_confirmacao_e_sucesso_com_confirmacao`: Validado o bloqueio seguro com código `FATURAS_FECHADAS_NAO_CONFIRMADAS` e o sucesso contábil com recálculo do Contas a Pagar ao enviar confirmação.
  - Suíte `apps.financeiro`: 39 testes executados com 100% de sucesso (`Ran 39 tests in 9.814s - OK`).
