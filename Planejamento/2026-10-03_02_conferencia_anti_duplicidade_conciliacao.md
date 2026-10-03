# Plano de Implementação - Detecção de Lançamentos Correspondentes e Conferência Anti-Duplicidade na Importação de Extratos

**Data:** 2026-10-03  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação (Proceed):** Aprovado pelo usuário em 2026-10-03 00:51:43 com a mensagem: *"Aprovado. Execute, por favor"*

---

## 1. Contexto e Objetivos

O usuário realizou um lançamento manual no Caixa Real no dia 02/06/2025. Ao importar o extrato bancário correspondente daquele mês, o sistema gerou um segundo lançamento idêntico no mesmo dia, duplicando a movimentação e o saldo. O usuário solicitou que a importação verifique se já existem lançamentos iguais no ERP comparando valores e datas (pois os nomes/descrições no extrato bancário e no lançamento manual são diferentes) e abra uma conferência com o usuário para evitar duplicações.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Critério de Busca de Correspondência (Ignorando Descrição)
A correspondência com lançamentos pendentes no ERP (`is_conciliado = False`) é baseada estritamente em:
- **Conta Bancária:** Mesma conta do extrato (ou lançamento pendente sem conta associada);
- **Tipo de Movimentação:** `ENTRADA` (crédito) ou `SAIDA` (débito);
- **Valor:** Tolerância de até R$ 0,05 (`abs(valor_extrato - valor_erp) <= Decimal('0.05')`), cobrindo valores exatos ou eventuais centavos de arredondamento;
- **Janela Temporal:** Tolerância de até **±3 dias** entre a data da transação no extrato e a data informada no lançamento manual (`data_pagamento` ou `data_vencimento`);
- **Status:** Não cancelado (`deleted_at__isnull=True` e `status_pagamento != 'CANCELADO'`).

### 2.2 Enriquecimento de Dados no Backend (`backend/apps/conciliacao/services.py`)
- Ao processar o extrato, se encontrar um lançamento no ERP (`is_conciliado=False`) que atenda aos critérios acima, o backend anexa à transação o objeto `lancamento_correspondente`:
  ```json
  {
    "id": 123,
    "descricao": "SERVICO DE SOLDA",
    "valor": 6770.00,
    "data": "2025-06-02",
    "status_pagamento": "PAGO",
    "categoria_id": 4,
    "categoria_nome": "RECEITA DE SERVICOS",
    "dias_diferenca": 0
  }
  ```
- O resumo de metadados (`meta`) incluirá a contagem `total_correspondencias_pendentes`.

### 2.3 Modal de Conferência de Importação no Frontend (`frontend/assets/js/views/conciliacao-view.js`)
Logo após o upload do extrato (ou ao alternar para a importação):
- Se `total_correspondencias_pendentes > 0`, o sistema abre automaticamente o **Modal de Conferência de Lançamentos**:
  - Exibe tabela comparativa:
    - **Extrato:** Data | Descrição do Banco | Valor
    - **ERP:** ID | Data | Descrição Manual | Categoria DRE | Valor
    - **Ação por Item (com opção recomendada pré-selecionada):**
      - `[🔘 VINCULAR E CONCILIAR (Recomendado)]` -> Reutiliza o lançamento manual, concilia e **NÃO DUPLICA**!
      - `[⚪ CRIAR NOVO LANÇAMENTO]` -> Trata como movimentação avulsa e cria um novo.
      - `[⚪ DESCARTAR DO EXTRATO]` -> Ignora a linha do extrato.
  - Botão de confirmação: **APLICAR DECISÕES E CONTINUAR**.

### 2.4 Destaque Visual na Mesa de Triagem (Modo 2)
- Nos cards da Mesa de Triagem que possuírem lançamento correspondente:
  - Borda e badge em tom âmbar (*Industrial Integrity*): `⚠️ CONFERÊNCIA: Lançamento manual encontrado no ERP (#123 - R$ Valor)`.
  - A categoria DRE já vem preenchida automaticamente com a categoria do lançamento existente.
  - O seletor de ação (Vincular / Criar Novo / Descartar) fica visível no próprio card para alteração ágil.

### 2.5 Execução Atômica Anti-Duplicidade de Saldo (`executar_importacao_lote`)
Ao receber `lancamento_existente_id` com ação `VINCULAR`:
1. Atualiza o lançamento existente: `is_conciliado = True`, `fitid = trn.fitid`, `data_conciliacao = now`, `conciliado_por = user`.
2. Se anexou comprovante/NF na triagem, anexa ao lançamento existente.
3. Se o lançamento estava `A_VENCER`, liquida para `PAGO` e debita/credita o saldo da conta normalmente.
4. **Proteção de Saldo Duplo:** Se o lançamento manual já havia sido lançado como `PAGO` na mesma conta (no Caixa Real), o saldo dessa conta **já havia sido computado no momento do lançamento manual**. Portanto, o sistema **NÃO altera o saldo novamente**, impedindo duplicidade financeira no Caixa Real!
5. **Nenhum registro novo é criado no MySQL**, garantindo unicidade perfeita.

---

## 3. Arquivos Afetados

- `backend/apps/conciliacao/services.py`
- `backend/apps/conciliacao/serializers.py`
- `backend/apps/conciliacao/tests.py`
- `frontend/assets/js/views/conciliacao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `Planejamento/2026-10-03_02_conferencia_anti_duplicidade_conciliacao.md`
- `docs/STATUS.md`
- `docs/ERROS.md`

---

## 4. Plano de Verificação e Testes

1. Testes automatizados do app conciliação:
   `python backend/manage.py test apps.conciliacao`
2. Testes automatizados do app financeiro:
   `python backend/manage.py test apps.financeiro`
3. Execução completa dos testes:
   `python backend/manage.py test apps/`

---

## 5. Relatório de Execução

1. **Backend - Serializers e Serviços (`apps/conciliacao`):**
   - Atualizado `ItemImportacaoLoteSerializer` para aceitar `lancamento_existente_id` e tornar `categoria_id` opcional na vinculação.
   - Atualizado `enriquecer_transacao_inteligencia` para buscar lançamentos pendentes no ERP (`is_conciliado=False`) compatíveis por conta, direção, valor ($\pm$ R$ 0,05) e janela temporal ($\pm$ 3 dias), ignorando diferenças de texto do banco.
   - Atualizado `processar_extrato_split_screen` para anexar `lancamento_correspondente` e computar `total_correspondencias_pendentes` nos metadados.
   - Atualizado `executar_importacao_lote` para suportar `lancamento_existente_id`. Quando vinculado, carimba o FITID no lançamento manual existente, concilia e verifica se o lançamento já estava `PAGO` na mesma conta (`ja_impactou_saldo`), não recalculando nem duplicando o saldo real da conta.
2. **Frontend - Mesa de Triagem e Modal de Conferência (`conciliacao-view.js`):**
   - Implementado método `abrirModalConferenciaCorrespondentes(itens)` exibindo tabela comparativa (Extrato vs Lançamento Manual no ERP) com seletores de ação (`VINCULAR E CONCILIAR (Recomendado)`, `CRIAR NOVO`, `DESCARTAR DO EXTRATO`).
   - Abertura automática ao carregar extrato com correspondências ou via botão `⚠️ CONFERÊNCIA` na barra de ações.
   - Implementado método `definirAcaoCorrespondente(idx, acao)` sincronizado com os rádios nos cards da Mesa de Triagem e conexões SVG.
   - Cards com correspondência identificada exibem faixa contextual âmbar/verde com opção de alternância ágil de ação.
   - Atualizado `executarImportacaoLote` para enviar `lancamento_existente_id` e exibir resumo de lançamentos a vincular vs novos a criar.
3. **PWA e Cache-Busting:**
   - Atualizado `CACHE_NAME = 'emc-soldas-v4.34'` em `frontend/sw.js`.
   - Atualizados todos os sufixos de cache-busting `?v=4.34` em `frontend/index.html`.
4. **Verificação Automatizada:**
   - `python backend/manage.py test apps.conciliacao`: 15 testes executados e 100% aprovados (OK em 4.3s).
   - `python backend/manage.py test apps.financeiro`: 27 testes executados e 100% aprovados (OK em 7.8s).

