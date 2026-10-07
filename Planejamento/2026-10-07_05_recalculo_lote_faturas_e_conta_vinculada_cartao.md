# Plano de Implementação - Preservação da Conta Vinculada do Cartão e Recálculo em Lote de Faturas Abertas por Competência

**Data:** 2026-10-07  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação do Usuário:**
- Mensagem: "Proceed"
- Feedback/Ajuste: "Não precisa da opção NENHUMA. Não faz sentido." (Removida a opção NENHUMA, mantendo ATUAL, PROXIMA e ESPECIFICA)
- Timestamp: 2026-10-07T19:04:15-03:00

---

## 1. Contexto e Diagnóstico dos Problemas

Com base nos testes do usuário na gestão de cartões corporativos, foram identificadas duas necessidades operacionais críticas:

### 1.1 Problema 1: Conta Vinculada Resetada para "Nenhuma" no Modal de Edição do Cartão
- **Causa Raiz Identificada:**
  1. No frontend (`frontend/assets/js/views/financeiro-view.js:959`), a renderização das opções de contas bancárias verificava:
     ```javascript
     cartaoEdicao?.conta_bancaria_id === c.id
     ```
     No entanto, o backend (`CartaoCreditoSerializer`) expunha a chave como `conta_bancaria` (o ID inteiro da ForeignKey), deixando `cartaoEdicao.conta_bancaria_id` como `undefined`. Logo, a condição era sempre falsa e o combobox selecionava o primeiro `<option value="">-- NENHUMA (DEFINIR DEPOIS) --</option>`.
  2. No momento de salvar (`onConfirm`), o frontend enviava `conta_bancaria_id`, mas `CartaoCreditoSerializer` esperava `conta_bancaria` e não possuía mapeamento de alias em `to_internal_value`, sobrescrevendo o vínculo com nulo caso não recebesse o campo com o nome exato do modelo.
- **Impacto:** Toda vez que o operador abria o modal para ajustar qualquer parâmetro do cartão, a conta bancária de débito preferencial era desvinculada.

### 1.2 Problema 2: Ausência de Recálculo em Lote das Faturas ao Alterar a Configuração Mestre do Cartão
- **Causa Raiz Identificada:**
  - O endpoint `POST /api/faturas-cartao/{id}/ajustar-fechamento/` já implementa recálculo pontual para uma única fatura específica com remanejamento automático de compras.
  - Porém, ao editar as configurações gerais do **Cartão** (`dia_fechamento_padrao` e `dia_vencimento` via `PUT /api/cartoes/{id}/`), a operação apenas alterava a tabela `cartoes_credito`, sem atualizar as faturas abertas existentes (`FaturaCartao` com status `ABERTA`).
  - O usuário precisa de controle operacional sobre o escopo de aplicação da mudança:
    1. **A partir da competência atual** (ex: `2026-10`) e futuras abertas (padrão recomendado).
    2. **A partir da próxima competência** (ex: `2026-11`) e futuras abertas (mantendo o corte do mês atual inalterado).
    3. **A partir de uma competência aberta específica** selecionada pelo operador (ex: `2026-12`).

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend - Suporte Bidirecional a `conta_bancaria` / `conta_bancaria_id` no Serializer
- Em `backend/apps/financeiro/serializers.py` (`CartaoCreditoSerializer`):
  - Adicionar `to_internal_value`: mapear `conta_bancaria_id` -> `conta_bancaria` se presente.
  - Adicionar campo serializado `conta_bancaria_id = serializers.IntegerField(source='conta_bancaria.id', read_only=True, allow_null=True)` garantindo que o JSON de saída contenha tanto `conta_bancaria` quanto `conta_bancaria_id`.
  - Garantir que tanto criação quanto atualização preservem a integridade da chave estrangeira.

### 2.2 Backend - Serviço Atômico de Recálculo em Lote (`services_cartao.py`)
- Criar a função `@transaction.atomic def recalcular_faturas_cartao(cartao, competencia_inicial, user=None)`:
  - Recupera todas as faturas do cartão com `status='ABERTA'`, `mes_referencia >= competencia_inicial` e `deleted_at__isnull=True`, ordenadas em ordem cronológica crescente (`order_by('mes_referencia')`).
  - Para cada fatura da sequência:
    1. Calcula a nova data de fechamento real baseada no novo `cartao.dia_fechamento_padrao`:
       `nova_data = calcular_data_fechamento_padrao(cartao, ano, mes)`.
    2. Se `nova_data != fatura.data_fechamento_real`:
       Invoca `ajustar_fechamento_fatura(fatura, nova_data, user=user)`.
    3. Proteção para parcelamentos: em `ajustar_fechamento_fatura`, garantir que despesas puxadas de volta da fatura subsequente apliquem-se apenas a compras à vista ou à 1ª parcela (`Q(numero_parcela=1) | Q(total_parcelas=1) | Q(numero_parcela__isnull=True)`), evitando que a parcela 2 ou 3 de uma compra anterior seja erroneamente agrupada na fatura do mês anterior.
  - Retorna relatório atômico:
    ```python
    {
        'cartao_id': cartao.id,
        'competencia_inicial': competencia_inicial,
        'faturas_recalculadas': total_faturas,
        'itens_movidos_adiante': total_adiante,
        'itens_puxados_de_volta': total_volta
    }
    ```

### 2.3 Backend - Atualização do Cartão com Recálculo Integrado (`views.py`)
- Em `CartaoCreditoViewSet`:
  - Sobrescrever `update`:
    - Atualiza os campos do cartão (`nome`, `dia_fechamento_padrao`, `dia_vencimento`, `limite`, `conta_bancaria`, etc.).
    - Recebe os parâmetros adicionais `recalcular_faturas` (booleano) e `competencia_inicial_recalculo` (string `'YYYY-MM'`).
    - Se `recalcular_faturas=True` e `competencia_inicial_recalculo` fornecida, executa `recalcular_faturas_cartao` na mesma transação atômica.
    - Devolve no JSON de resposta a chave `'recalculo'` com o sumário de faturas e itens atualizados.
  - Adicionar `@action(detail=True, methods=['post'], url_path='recalcular-faturas')` permitindo disparar o recálculo em lote isoladamente via API REST a qualquer momento.

### 2.4 Frontend - UX Industrial Integrity no Modal de Cartão (`financeiro-view.js`)
- **Preservação da Conta Vinculada:**
  - Extração robusta: `const contaIdAtual = cartaoEdicao?.conta_bancaria_id || cartaoEdicao?.conta_bancaria || null;`
  - Seleção exata: `${String(c.id) === String(contaIdAtual) ? 'selected' : ''}`
  - Envio no payload tanto de `conta_bancaria` quanto de `conta_bancaria_id`.
- **Painel de Recálculo em Lote (exibido apenas no modo de edição `isEdicao`):**
  - Bloco visual técnico com borda Rust Orange:
    - Campo `Escopo de Repercussão nas Faturas`:
      - `[ATUAL]` A partir da competência atual (`YYYY-MM`) e futuras (padrão)
      - `[PROXIMA]` A partir da próxima competência (`YYYY-MM`) e futuras
      - `[ESPECIFICA]` A partir de uma competência específica...
    - Se o operador selecionar `[ESPECIFICA]`, exibe combobox preenchido com as faturas abertas do cartão para seleção direta.
  - No salvamento:
    - Envia `recalcular_faturas: true` e a `competencia_inicial_recalculo` correspondente (`ATUAL`, `PROXIMA` ou `ESPECIFICA`).
    - Exibe toast com o resumo (ex: *"Cartão atualizado com sucesso! 2 fatura(s) recalculada(s) a partir de 2026-10."*).
    - Recarrega imediatamente as métricas, os cartões e a linha do tempo das faturas.

### 2.5 Governança de PWA e Cache
- Atualizar Service Worker (`frontend/sw.js`): versão `emc-soldas-v4.62`.
- Atualizar cache-busting em `frontend/index.html`: sufixos `?v=4.62`.

---

## 3. Arquivos a Serem Modificados

| Arquivo | Natureza da Alteração |
| :--- | :--- |
| `backend/apps/financeiro/serializers.py` | `to_internal_value` para mapear `conta_bancaria_id`, e campo `conta_bancaria_id` explícito em `CartaoCreditoSerializer`. |
| `backend/apps/financeiro/services_cartao.py` | Implementação de `recalcular_faturas_cartao` e proteção de parcelas em `ajustar_fechamento_fatura`. |
| `backend/apps/financeiro/views.py` | `update` customizado em `CartaoCreditoViewSet` com suporte a recálculo em lote e action `recalcular-faturas`. |
| `backend/apps/financeiro/tests.py` | Testes automatizados para vínculo de conta, recálculo em lote a partir da competência atual e próxima, e proteção de parcelas. |
| `frontend/assets/js/views/financeiro-view.js` | Resolução do combobox de conta vinculada, seletor de escopo de recálculo (atual, próxima, específica, nenhuma) e envio de parâmetros. |
| `frontend/sw.js` | Incremento de versão para `emc-soldas-v4.62`. |
| `frontend/index.html` | Cache-busting atualizado para `?v=4.62`. |
| `docs/STATUS.md` | Atualização do checklist vivo da Fase 14.5. |
| `Planejamento/2026-10-07_05_recalculo_lote_faturas_e_conta_vinculada_cartao.md` | Salvamento permanente deste plano após aprovação. |

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados de Backend:**
   - Executar `python backend/manage.py test apps.financeiro`.
   - Executar a suíte completa de testes do sistema (`python backend/manage.py test apps core`) garantindo aprovação de 100% dos testes.
2. **Teste Manual no Frontend (Navegador):**
   - Abrir **Financeiro > CARTÕES CORPORATIVOS**.
   - Clicar em **EDITAR CARTÃO**: verificar que a Conta Bancária vinculada (ex: Banco do Brasil) aparece pré-selecionada corretamente no combobox (não mais "NENHUMA").
   - Salvar sem alterar a conta e reabrir: certificar-se de que a conta permaneceu vinculada.
   - Alterar o `Dia de Fechamento Padrão` (ex: de 20 para 15):
     - Selecionar "A partir da competência atual (2026-10)".
     - Confirmar a gravação: verificar que a fatura `2026-10` teve seu fechamento ajustado para o dia 15 e as compras posteriores foram remanejadas para `2026-11`.
   - Testar também o recálculo "A partir da próxima competência (2026-11)", verificando que a fatura `2026-10` mantém seu fechamento e a de `2026-11` passa para a nova data.

---

## 5. Relatório de Execução (Pós-conclusão)

Todas as ações foram concluídas com êxito:

1. **Preservação da Conta Bancária Vinculada:**
   - `CartaoCreditoSerializer` atualizado com `to_internal_value` para mapear `conta_bancaria_id` para `conta_bancaria` e campos serializados `conta_bancaria` e `conta_bancaria_id`.
   - `financeiro-view.js` corrigido para extrair resilientemente `cartaoEdicao?.conta_bancaria_id || cartaoEdicao?.conta_bancaria` e realizar matching de tipos com `String(c.id) === String(contaIdAtual)`.
   - Validado nos testes automatizados que salvar e reabrir o cartão mantém a conta bancária vinculada intacta.

2. **Recálculo em Lote de Faturas Abertas:**
   - Criado serviço atômico `recalcular_faturas_cartao(cartao, competencia_inicial, user)` em `services_cartao.py`.
   - Blindagem em `ajustar_fechamento_fatura` com filtro `Q(numero_parcela=1) | Q(total_parcelas=1) | Q(numero_parcela__isnull=True)` para impedir que parcelas subsequentes de compras a prazo sejam agrupadas na competência anterior.
   - `CartaoCreditoViewSet.update` e action `@action(detail=True, methods=['post'], url_path='recalcular-faturas')` integrados com atomicidade transacional e retorno de sumário (`recalculo`).

3. **Interface e UX no Modal de Edição:**
   - Adicionado painel técnico "REPERCUSSÃO NAS FATURAS ABERTAS EXISTENTES" no modal de edição com as opções:
     - `ATUAL`: A partir da competência atual (`YYYY-MM`) e futuras
     - `PROXIMA`: A partir da próxima competência (`YYYY-MM`) e futuras
     - `ESPECIFICA`: A partir de uma competência específica (dropdown com faturas abertas)
   - Notificação toast informativa reportando o total de faturas recalculadas.

4. **Bateria de Testes:**
   - Adicionados testes `test_cartao_serializer_preservacao_conta_bancaria` e `test_recalcular_faturas_cartao_em_lote_atual_e_proxima`.
   - Suíte completa executada: **211/211 testes aprovados (100% de sucesso em 78.6s)**.

5. **Versionamento PWA:**
   - `CACHE_NAME` atualizado para `emc-soldas-v4.62` em `sw.js`.
   - Cache-busting atualizado para `?v=4.62` em `index.html`.

