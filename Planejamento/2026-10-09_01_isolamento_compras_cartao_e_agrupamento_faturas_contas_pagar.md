# Plano de Implementação: Isolamento de Compras com Cartão e Agrupamento de Faturas no Contas a Pagar

- **Data:** 09/10/2026
- **Autor:** Antigravity (Pair Programming com Usuário)
- **Status:** Concluído (Aprovado e Validado com 100% dos Testes)
- **Registro do Proceed:** Aprovado pelo usuário em 24/10/2026 via mensagem "Proceed", com comentários de governança sobre impacto na alteração de fechamento e recálculo em cadeia das faturas adjacentes.

---

## 1. Contexto e Motivação do Negócio

Atualmente, todas as compras efetuadas com Cartões de Crédito Corporativos (sejam compras à vista ou compras parceladas em até 10x) geram registros na tabela `lancamentos_financeiros` com `tipo_lancamento = 'SAIDA'` e `status_pagamento = 'A_VENCER'`.

Na tela de **Contas a Pagar**, o filtro busca todos os lançamentos com `tipo_lancamento = 'SAIDA'`. Como consequência:
1. **Poluição e Mistura Indevida:** Todas as compras individuais do cartão (parcelas avulsas, despesas com peças, combustíveis, etc.) aparecem listadas na tabela geral de Contas a Pagar.
2. **Risco Crítico de Liquidação Avulsa Inválida:** Cada compra individual no cartão exibe a ação `PAGAR (BAIXA)`, permitindo que o operador liquide individualmente uma compra de cartão direto contra o saldo bancário, o que é conceitual e contabilmente incorreto, pois as compras de cartão só são liquidadas no pagamento da fatura consolidada.
3. **Ausência da Fatura Aberta e Duplicação no Fechamento:** Enquanto a fatura está ABERTA, não há lançamento agrupado de previsão de saída no Contas a Pagar; e quando a fatura é FECHADA, gera-se um título `PAGAMENTO FATURA CARTAO...`, fazendo com que tanto o título mestre quanto as compras individuais apareçam simultaneamente, duplicando o valor da dívida no Contas a Pagar.

### Requisito Solicitado pelo Usuário
> *"Precisamos alterar a listagem de contas a pagar. lá não devem ser exibidas as compras feitas com cartão, pra não misturar. As compras do cartão são listadas apenas nas faturas do cartão. Mesmo porque, eu não posso ter a possibilidade de um botão PAGAR (BAIXA) em uma conta do cartão. As compras efetuadas pelo cartão de crédito devem ser liquidadas exclusivamente pela liquidação da fatura do cartão. O que deve aparecer nas contas a pagar, são apenas as faturas dos cartões, e da maneira que está hoje, está listando todas as compras do cartão. Precisamos exibir apenas um lançamento agrupado da fatura. Entendeu?"*

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Modelo de Dados (`LancamentoFinanceiro`)
- Adicionar o campo booleano `is_fatura_cartao_consolidada`:
  ```python
  is_fatura_cartao_consolidada = models.BooleanField(
      default=False,
      db_index=True,
      verbose_name="Título Consolidado da Fatura de Cartão"
  )
  ```
- **Semântica:**
  - `is_fatura_cartao_consolidada = False` + `fatura_cartao_id != null`: **Item / Compra individual da fatura de cartão**. Exibido estritamente na visualização de faturas (`GET /api/faturas-cartao/{id}/itens/`), **nunca no Contas a Pagar**.
  - `is_fatura_cartao_consolidada = True`: **Título consolidado da fatura de cartão**. Representa o valor total acumulado e a previsão de vencimento da fatura perante o banco. **Exibido no Contas a Pagar**.
  - `fatura_cartao_id is null`: Contas a pagar/receber normais (boletos, transferências, fornecedores). Exibidos no Contas a Pagar normalmente.

### 2.2 Sincronização Automática Contínua (`sincronizar_titulo_fatura_cartao`)
- Criar a função centralizadora `sincronizar_titulo_fatura_cartao(fatura, user=None)` em `services_cartao.py`:
  1. Soma o valor total de compras ativas não consolidadas da fatura (`tipo_lancamento='SAIDA'`, `is_fatura_cartao_consolidada=False`, `deleted_at__isnull=True`).
  2. Calcula a data de vencimento da fatura com base no dia de fechamento/vencimento do cartão.
  3. Se `total > 0`:
     - Localiza ou cria o `LancamentoFinanceiro` consolidado (`is_fatura_cartao_consolidada = True`, `fatura_cartao = fatura`, `descricao = f"FATURA CARTAO {cartao.nome} - {fatura.mes_referencia}"`).
     - Sincroniza `valor = total`, `data_vencimento = vencimento`, `data_competencia = fatura.data_fechamento_real`, `status_pagamento = 'PAGO' if fatura.status == 'PAGA' else 'A_VENCER'`, `conta = fatura.cartao.conta_bancaria`.
  4. Se `total == 0`:
     - Se existir título consolidado pendente, ajusta para `0.00` ou remove se não houver compras.
- **Tratamento de Alteração de Fechamento e Recálculo em Cadeia (Apontamento do Usuário):**
  - Ao alterar a data de fechamento (`ajustar_fechamento_fatura` ou `recalcular_faturas_cartao`):
    - O motor de redistribuição de compras deve filtrar **estritamente compras reais** (`is_fatura_cartao_consolidada = False`), impedindo que o título consolidado seja inadvertidamente movido como se fosse um item de compra.
    - Sincronizar compulsoriamente a fatura em alteração e as **faturas adjacentes (anterior e posterior)** que tiveram despesas movimentadas, puxadas ou empurradas.
    - Tratamento de transição de status: se uma fatura sofrer alteração de fechamento que justifique reabertura ou fechamento forçado, atualizar o status da fatura e sincronizar o status do título financeiro correspondente em Contas a Pagar.
- Integrar a chamada de sincronização em:
  - `lancar_despesa_cartao`
  - `remanejar_despesa_cartao`
  - `ajustar_fechamento_fatura` (fatura atual e adjacentes)
  - `recalcular_faturas_cartao` (todas as faturas da cadeia)
  - `fechar_fatura_cartao`
  - `liquidar_fatura_cartao`
- Executar migração de dados para sincronizar todas as faturas pré-existentes no banco de dados.

### 2.3 Blindagem da API REST e Governança
1. **Filtro no ViewSet (`LancamentoFinanceiroViewSet.get_queryset`):**
   - Por padrão, excluir da listagem geral de lançamentos qualquer registro onde `fatura_cartao_id` esteja preenchido e `is_fatura_cartao_consolidada = False`.
   - Adicionar parâmetro explícito `incluir_itens_cartao=true` apenas para rotas que exigem auditoria individual.
2. **Blindagem contra Baixa Indevida (`services.liquidar_lancamento`):**
   - Lançar `ValidationError` caso tente liquidar diretamente uma compra individual de cartão (`fatura_cartao_id is not null and is_fatura_cartao_consolidada == False`).
   - Se tentar liquidar o título consolidado, encaminhar para a rotina oficial de liquidação da fatura (`liquidar_fatura_cartao`), garantindo verificação de cheque especial, conta debitada e rollover de pagamento parcial.
3. **Endpoint de Itens da Fatura (`FaturaCartaoViewSet.itens`):**
   - Garantir que retorne estritamente compras individuais (`is_fatura_cartao_consolidada = False`), evitando duplicar o título consolidado dentro dos itens da fatura.

### 2.4 Interface e Experiência no Frontend (PWA)
1. **Listagem de Contas a Pagar (`financeiro-view.js`):**
   - A tabela lista as contas a pagar convencionais e os títulos consolidados das faturas de cartão.
   - **Identificador Visual:** Exibir chip distintivo `FATURA CARTÃO` ao lado do nome do cartão.
   - **Coluna Ações:**
     - Se fatura **FECHADA**: botão verde `💰 LIQUIDAR FATURA`, abrindo o modal oficial de liquidação da fatura do cartão (`abrirModalLiquidarFatura`).
     - Se fatura **ABERTA**: botão `🔍 CONFERIR FATURA (ABERTA)`, com navegação direta para a aba de Cartões Corporativos na fatura correspondente.
     - Se fatura **PAGA**: tag textual `FATURA QUITADA`.
     - Nenhum botão `PAGAR (BAIXA)` avulso é exibido para compras de cartão.
2. **Versionamento e Cache:**
   - Incrementar versão do Service Worker (`sw.js`: `v2.8` -> `v2.9`).
   - Atualizar sufixo `?v=2.9` em `index.html`.

---

## 3. Arquivos a Criar e Modificar

| Arquivo | Ação | Descrição |
|---|---|---|
| `backend/apps/financeiro/models.py` | Modificar | Adicionar campo `is_fatura_cartao_consolidada` em `LancamentoFinanceiro` |
| `backend/apps/financeiro/migrations/0009_lancamentofinanceiro_is_fatura_cartao_consolidada.py` | Criar | Migration do campo e migração de dados para faturas existentes |
| `backend/apps/financeiro/services_cartao.py` | Modificar | Criar `sincronizar_titulo_fatura_cartao` e integrar aos fluxos de compra, remanejamento, fechamento e liquidação |
| `backend/apps/financeiro/services.py` | Modificar | Blindar `liquidar_lancamento` contra baixa de itens individuais de cartão |
| `backend/apps/financeiro/serializers.py` | Modificar | Expor `is_fatura_cartao_consolidada`, `fatura_cartao_status`, `fatura_cartao_mes` no serializer |
| `backend/apps/financeiro/views.py` | Modificar | Filtrar itens individuais de cartão no `get_queryset` do `LancamentoFinanceiroViewSet` e refinar `itens` no `FaturaCartaoViewSet` |
| `frontend/assets/js/views/financeiro-view.js` | Modificar | Ajustar renderização da tabela de Contas a Pagar para tratar faturas consolidadas e direcionar para liquidação/conferência |
| `frontend/sw.js` | Modificar | Atualizar `CACHE_NAME` para `v2.9` |
| `frontend/index.html` | Modificar | Cache-busting com query string `?v=2.9` |
| `backend/apps/financeiro/tests.py` | Modificar | Novos testes unitários e de integração cobrindo a sincronização e blindagem |

---

## 4. Plano de Verificação e Testes

1. **Testes Unitários Backend:**
   - Testar que `lancar_despesa_cartao` cria o item individual e sincroniza/cria o título consolidado da fatura com `is_fatura_cartao_consolidada=True`.
   - Testar que a listagem de `tipo_lancamento='SAIDA'` no endpoint `/api/lancamentos-financeiros/` retorna apenas o título consolidado e não as compras individuais.
   - Testar que `/api/faturas-cartao/{id}/itens/` retorna as compras individuais e não o título consolidado.
   - Testar que chamar `/api/lancamentos-financeiros/{id}/liquidar/` em uma compra individual retorna erro `400 Bad Request` com mensagem explicativa.
   - Testar que a liquidação da fatura transita tanto o título consolidado quanto os itens da fatura para status `PAGO`.
2. **Suíte Completa:**
   - Rodar `python backend/manage.py test backend/` e garantir 100% de sucesso em todos os testes.
3. **Validação Manual no Frontend:**
   - Abrir a tela de Contas a Pagar.
   - Verificar que as compras individuais do Nubank (IDs 149 a 159) não poluem a lista.
   - Verificar que a fatura consolidada aparece como um único título agrupado com seu total correto e vencimento.
   - Verificar que a coluna de ações exibe as opções adequadas para a fatura do cartão.

---

## 5. Relatório de Execução e Evidências de Validação

- **Data de Conclusão:** 24/10/2026
- **Status Final:** Concluído com Sucesso

### 5.1 O que foi Executado
1. **Modelagem e Migrations:**
   - Adicionado campo `is_fatura_cartao_consolidada = models.BooleanField(default=False, db_index=True)` no modelo `LancamentoFinanceiro` (`backend/apps/financeiro/models.py`).
   - Gerada e aplicada com sucesso a migração `backend/apps/financeiro/migrations/0009_lancamentofinanceiro_is_fatura_cartao_consolidada.py`.
2. **Sincronizador Automatizado de Faturas (`services_cartao.py`):**
   - Implementada a função `sincronizar_titulo_fatura_cartao(fatura, user=None)`, garantindo a criação, atualização contínua e sincronização de status de títulos consolidados de faturas de cartão em Contas a Pagar.
   - Integrada a sincronização automática em todos os eventos do ciclo de vida: compra avulsa/parcelada (`lancar_despesa_cartao`), remanejamento entre faturas (`remanejar_despesa_cartao`), alteração de fechamento com recálculo em cadeia de faturas adjacentes (`ajustar_fechamento_fatura`), recálculo atômico global (`recalcular_faturas_cartao`), fechamento formal (`fechar_fatura_cartao`) e liquidação total/parcial (`liquidar_fatura_cartao`).
   - Ajustadas as rotinas de cálculo de limite disponível e redistribuição para ignorar títulos consolidados (`is_fatura_cartao_consolidada=False`), evitando duplicação contábil.
   - Sincronizadas todas as faturas pré-existentes na base de dados com seus respectivos títulos consolidados.
3. **Blindagem e Governança na API REST (`services.py`, `serializers.py`, `views.py`):**
   - `services.py`: implementada rejeição estrita com `ValidationError` ao tentar liquidar despesas avulsas de cartão via endpoint padrão `liquidar_lancamento`. Ao liquidar o título consolidado, encaminha com segurança para `liquidar_fatura_cartao`.
   - `serializers.py`: expostos os campos `is_fatura_cartao_consolidada`, `fatura_cartao_status` e `fatura_cartao_mes`.
   - `views.py`: o queryset de `LancamentoFinanceiroViewSet` filtra e oculta itens avulsos de cartão especificamente em listagens (`self.action == 'list'`), preservando o acesso direto por ID para rotas de detalhe (`alterar-fatura-cartao`, etc.). `FaturaCartaoViewSet.itens` filtra estritamente `is_fatura_cartao_consolidada=False`.
4. **Interface e Experiência do Usuário (Frontend SPA / PWA):**
   - `frontend/assets/js/views/financeiro-view.js`:
     - Tabela de Contas a Pagar exibe chip temático `FATURA CARTÃO` ao lado do cartão.
     - Botão `PAGAR (BAIXA)` avulso suprimido para despesas de cartão.
     - Botão `💰 LIQUIDAR FATURA` para faturas fechadas abrindo o modal oficial de liquidação.
     - Botão `🔍 CONFERIR FATURA (ABERTA)` para faturas abertas direcionando para a aba de cartões corporativos.
     - Tag informativa `FATURA QUITADA` para faturas pagas.
     - Recarregamento automático de Contas a Pagar após a liquidação da fatura.
5. **Versionamento e Cache PWA:**
   - Atualizado `CACHE_NAME` para `'emc-soldas-v4.66'` no `frontend/sw.js`.
   - Atualizadas todas as query strings de CSS e JS para `?v=4.66` no `frontend/index.html`.

### 5.2 Evidências de Testes
- **Testes Unitários e Integrados do Módulo Financeiro:**
  - `python backend/manage.py test apps.financeiro`: 42 testes executados e 100% aprovados.
  - Testes específicos adicionados:
    - `test_contas_a_pagar_exibe_apenas_fatura_consolidada_e_oculta_compras_avulsas`
    - `test_bloqueio_baixa_avulsa_compra_cartao_e_sucesso_na_liquidacao_fatura`
    - `test_sincronizacao_titulo_consolidado_ao_alterar_fechamento_e_recadear`
- **Suíte Completa de Testes do Sistema:**
  - `python backend/manage.py test backend/`: 217 testes executados e 100% aprovados em 66.4s sem falhas ou regressões.
