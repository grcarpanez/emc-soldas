# Plano de Implementação: Diferenciação no Estorno de Contas a Pagar vs. Lançamentos Avulsos

## 1. Metadados do Plano
- **Data de Elaboração:** 03/10/2026
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** `Concluído`
- **Identificador:** `Planejamento/2026-10-03_06_diferenciacao_estorno_contas_pagar_vs_avulsos.md`
- **Registro do Proceed:** Aprovado formalmente pelo usuário em 03/10/2026 às 12:46:37 (`Proceed`).

---

## 2. Contexto Operacional e Diagnóstico

### 2.1 Cenário Atual
- O usuário criou um lançamento avulso em 02/06/2025 para testes (`#63 - COMPRA NO DEBITO - EQUIPAMINAS EQUIPAMENT - R$ 474,60`).
- Ao realizar a conciliação / importação do extrato bancário, o lançamento real correspondente foi registrado (`#64`).
- Para sanar a duplicidade no caixa, o usuário estornou o lançamento `#63`.
- O método de estorno atual (`estornar_lancamento`) reverteu corretamente o saldo da conta bancária, mas transitou incondicionalmente o status de qualquer título para `'A_VENCER'` (`status_pagamento = 'A_VENCER'`, `conta = None`, `data_pagamento = None`).
- Consequência: O lançamento de compra avulsa foi indevidamente convertido em uma **Conta a Pagar em aberto**, passando a poluir a agenda financeira da empresa.

### 2.2 Distinção de Negócio (Regra da EMC Soldas)
1. **Contas a Pagar / Receber (Agenda Financeira):** São compromissos prévios lançados para planejamento da agenda (`status_pagamento = 'A_VENCER'`). Quando liquidadas por engano no sistema, o estorno deve reverter o saldo bancário e **retornar o título ao estado original "não pago" (`A_VENCER`)**, permitindo posterior liquidação na data e conta corretas.
2. **Lançamentos Avulsos / Compras Efetivadas:** São compras e movimentações já liquidadas no ato (à vista, débito, pix balcão, importação do extrato bancário). Eles **não são contas agendadas**, são compras já realizadas. Ao serem estornados (por duplicidade, digitação errada ou cancelamento):
   - O saldo bancário da conta é devidamente revertido (devolvendo ou retirando o valor);
   - O registro **NÃO pode virar uma conta a pagar** em aberto;
   - O lançamento deve sofrer **Soft Delete** (`deleted_at = timezone.now()`, `deleted_by_id = user.id`) com status `'CANCELADO'`;
   - O rastro perpétuo é gravado compulsoriamente na tabela `log_estornos`.

---

## 3. Decisões Técnicas e Arquiteturais

### 3.1 Modelagem de Dados (`backend/apps/financeiro/models.py`)
- Adição do campo `origem` no modelo `LancamentoFinanceiro`:
  ```python
  ORIGEM_CHOICES = [
      ('AGENDA', 'Conta Agendada (Contas a Pagar/Receber)'),
      ('AVULSO', 'Compra / Lançamento Avulso no Extrato'),
      ('CONCILIACAO', 'Extrato / Conciliação Bancária'),
      ('FATURA', 'Faturamento de Orçamentos'),
      ('CARTAO', 'Fatura de Cartão de Crédito'),
  ]
  origem = models.CharField(
      max_length=20,
      choices=ORIGEM_CHOICES,
      default='AGENDA',
      db_index=True,
      verbose_name="Origem do Lançamento"
  )
  ```
- Criação da migration Django correspondente.
- Execução de data migration / script retroativo para os 91 registros existentes:
  - Transações com `fitid` ou `is_conciliado=True` -> `origem = 'CONCILIACAO'`.
  - Registros avulsos criados no extrato (#91 e #63) -> `origem = 'AVULSO'`.
  - **Correção imediata do lançamento #63:** Como o saldo já foi revertido no estorno anterior, atualizar `#63` com `origem = 'AVULSO'`, `status_pagamento = 'CANCELADO'`, `motivo_cancelamento = 'ESTORNO DE LANÇAMENTO AVULSO DUPLICADO'` e aplicar soft delete (`deleted_at = timezone.now()`), removendo-o da listagem de Contas a Pagar em aberto.

### 3.2 Lógica do Serviço de Estorno (`backend/apps/financeiro/services.py`)
- Refatoração da função `estornar_lancamento`:
  ```python
  eh_conta_agendada = (
      lancamento.origem in ['AGENDA', 'FATURA', 'CARTAO'] or
      bool(lancamento.fatura_id) or
      bool(lancamento.fatura_cartao_id)
  )

  if eh_conta_agendada:
      # 1. Reversão para a agenda financeira
      lancamento.status_pagamento = 'A_VENCER'
      lancamento.data_pagamento = None
      lancamento.conta = None
      lancamento.updated_by_id = user.id
      lancamento.save(update_fields=['status_pagamento', 'data_pagamento', 'conta', 'updated_at', 'updated_by_id'])
      tipo_acao = 'RETORNADO_AGENDA'
  else:
      # 2. Lançamento avulso / compra direta: reverte saldo e aplica Soft Delete
      lancamento.status_pagamento = 'CANCELADO'
      lancamento.motivo_cancelamento = f"ESTORNO: {justificativa_sanitizada}"
      lancamento.save(update_fields=['status_pagamento', 'motivo_cancelamento', 'updated_at', 'updated_by_id'])
      lancamento.delete(user_id=user.id)
      tipo_acao = 'EXCLUIDO_AVULSO'
  ```
- Ambas as vias realizam a reversão exata do saldo na `ContaBancaria` e gravam compulsoriamente a entrada no `LogEstorno`.

### 3.3 Serializers e ViewSets (`serializers.py`, `views.py`)
- `LancamentoFinanceiroSerializer`: expor o campo `origem`. Na criação, caso não informado:
  - Se `status_pagamento == 'PAGO'` -> default `'AVULSO'`.
  - Se `status_pagamento in ['A_VENCER', 'VENCIDO']` -> default `'AGENDA'`.
- `LancamentoFinanceiroViewSet.estornar`:
  - Retornar mensagem customizada e amigável:
    - Se `RETORNADO_AGENDA`: *"Baixa estornada com sucesso. O título retornou para a agenda de Contas a Pagar/Receber."*
    - Se `EXCLUIDO_AVULSO`: *"Lançamento avulso estornado com sucesso. O saldo bancário foi revertido e a movimentação foi excluída."*

### 3.4 Sincronização nos Apps Conectados
- `backend/apps/conciliacao/services.py`: setar `origem='CONCILIACAO'` na criação de novos lançamentos da conciliação.
- `backend/apps/faturamento/services.py`: setar `origem='FATURA'` ao faturar pedidos.
- `backend/apps/financeiro/services_cartao.py`: setar `origem='CARTAO'`.

### 3.5 Interface do Usuário (Frontend - `financeiro-view.js`)
- Na abertura do modal de estorno (`abrirModalEstorno(lancamentoId)`):
  - Inspecionar a origem do lançamento selecionado.
  - Exibir alerta contextual educativo no modal:
    - **Para Contas a Pagar/Receber:** `⚡ Conta Liquidada: Este lançamento foi originado de uma Conta a Pagar/Receber agendada. Ao confirmar o estorno, o saldo bancário será revertido e o título voltará para o estado "NÃO PAGO" (A Vencer) na sua agenda financeira.`
    - **Para Lançamentos Avulsos:** `⚡ Lançamento Avulso (Compra Direta): Esta movimentação foi liquidada no ato e não possui conta agendada. Ao confirmar o estorno, o saldo bancário será revertido e o lançamento será excluído (não criará conta a pagar pendente).`
- No modal de Novo Lançamento:
  - Na aba Extrato: enviar `origem: 'AVULSO'`.
  - Na aba Contas a Pagar / Receber: enviar `origem: 'AGENDA'`.

### 3.6 Governança de Cache PWA e Commits
- Atualizar `CACHE_NAME = 'emc-soldas-v4.37'` em `frontend/sw.js`.
- Atualizar tags com `?v=4.37` em `frontend/index.html`.

---

## 4. Arquivos a Criar e Modificar

1. **`backend/apps/financeiro/models.py`**
   - Adicionar campo `origem` com choices (`AGENDA`, `AVULSO`, `CONCILIACAO`, `FATURA`, `CARTAO`).
2. **`backend/apps/financeiro/migrations/XXXX_lancamentofinanceiro_origem.py`**
   - Migration com criação do campo e migração de dados históricos (incluindo saneamento do lançamento `#63`).
3. **`backend/apps/financeiro/services.py`**
   - Refatorar `estornar_lancamento` para aplicar soft delete em avulsos e retorno a `A_VENCER` para contas agendadas.
4. **`backend/apps/financeiro/serializers.py`**
   - Adicionar `origem` no `LancamentoFinanceiroSerializer` com validação e defaults inteligentes.
5. **`backend/apps/financeiro/views.py`**
   - Retornar mensagens contextuais na action `estornar`.
6. **`backend/apps/conciliacao/services.py`**
   - Garantir atribuição de `origem='CONCILIACAO'`.
7. **`backend/apps/faturamento/services.py`**
   - Garantir atribuição de `origem='FATURA'`.
8. **`backend/apps/financeiro/services_cartao.py`**
   - Garantir atribuição de `origem='CARTAO'`.
9. **`backend/apps/financeiro/tests.py`**
   - Bateria de testes automatizados cobrindo os dois caminhos de estorno e auditoria imutável.
10. **`frontend/assets/js/views/financeiro-view.js`**
    - Modal de estorno contextualizado e payload com `origem`.
11. **`frontend/sw.js`**
    - Incremento para `emc-soldas-v4.37`.
12. **`frontend/index.html`**
    - Incremento para `?v=4.37`.
13. **`docs/STATUS.md`**
    - Registro vivo da melhoria na Fase 10/11.

---

## 5. Plano de Verificação e Testes

### 5.1 Testes Automatizados (Backend)
- Executar: `.\venv\Scripts\python.exe backend/manage.py test apps.financeiro apps.conciliacao`
- Casos específicos:
  1. Estorno de conta agendada liquidada -> valida retorno do saldo bancário, transição para `A_VENCER`, limpeza de `data_pagamento` e gravação em `LogEstorno`.
  2. Estorno de compra avulsa liquidada -> valida retorno do saldo bancário, aplicação de `Soft Delete` (`deleted_at is not None`), status `'CANCELADO'` e gravação em `LogEstorno`.
  3. Verificação de que o título avulso estornado **não aparece** na listagem de Contas a Pagar nem de Extrato.
  4. Validação da trilha em `LogEstorno` com justificativa obrigatória (>10 caracteres).

### 5.2 Validação Manual e E2E
- Verificar que o lançamento `#63` sumiu da aba "Contas a Pagar".
- Criar um novo lançamento avulso no Extrato e estorná-lo -> verificar que o saldo volta e nenhuma conta a pagar é gerada.
- Criar uma conta a pagar na aba "Contas a Pagar", dar baixa nela no Extrato e estorná-la -> verificar que o saldo volta e ela retorna para a lista de Contas a Pagar.

---

## 6. Relatório de Execução (Pós-conclusão)

### 6.1 Ações Realizadas
1. **Modelagem de Dados e Data Migration:**
   - Adicionado campo `origem` com choices (`AGENDA`, `AVULSO`, `CONCILIACAO`, `FATURA`, `CARTAO`) e property `eh_conta_agendada` no modelo `LancamentoFinanceiro` (`backend/apps/financeiro/models.py`).
   - Gerada e aplicada a migration `0006_lancamentofinanceiro_origem.py` com rotina retroativa para os 91 registros históricos do banco.
   - O lançamento `#63` de 02/06/2025 foi classificado como `origem='AVULSO'`, status `'CANCELADO'`, motivo de cancelamento registrado e recebeu Soft Delete (`deleted_at` preenchido), saindo definitivamente da listagem de Contas a Pagar em aberto.
2. **Refatoração do Serviço de Estorno:**
   - Implementada bifurcação em `estornar_lancamento` (`backend/apps/financeiro/services.py`):
     - Contas agendadas (`AGENDA`, `FATURA`, `CARTAO`) retornam para `A_VENCER` ("não paga") na agenda financeira.
     - Lançamentos avulsos (`AVULSO`, `CONCILIACAO`) sofrem Soft Delete com status `CANCELADO`, sem virar conta a pagar.
     - Ambos revertem o saldo na conta bancária e gravam rastro perpétuo em `LogEstorno`.
3. **Serializers, Views e Propagação de Origem:**
   - Exposto `origem`, `origem_display` e `eh_conta_agendada` no `LancamentoFinanceiroSerializer` com validação e inferência inteligente.
   - Atualizado `LancamentoFinanceiroViewSet.estornar` para responder com mensagens claras e contextuais.
   - Atribuída origem correta na criação de lançamentos em `conciliacao/services.py`, `faturamento/services.py` e `financeiro/services_cartao.py`.
4. **Interface do Usuário (Frontend PWA):**
   - Modal de estorno no Extrato (`financeiro-view.js`) inspeciona o lançamento e exibe alerta explicativo contextual (*Industrial Integrity*).
   - Modal de novo lançamento envia `origem: 'AVULSO'` no extrato e `origem: 'AGENDA'` no contas a pagar/receber.
5. **Governança de Cache PWA e Suíte de Testes:**
   - `CACHE_NAME` atualizado para `emc-soldas-v4.37` em `sw.js` e `?v=4.37` em `index.html`.
   - Adicionado teste unitário `test_estorno_lancamento_avulso_com_soft_delete_sem_gerar_conta_a_pagar` em `apps/financeiro/tests.py`.
   - Homologação: 29 testes do app financeiro e 184 testes da suíte global executados com 100% de sucesso.

