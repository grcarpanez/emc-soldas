# Plano de Implementação - Ajustes de Linha do Tempo de Faturas, Estilo de Botões, Seleção de Cartão no Lançamento e Meios na Matriz de Pagamentos

**Data:** 2026-10-07  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação do Usuário:**
- Mensagem: "Proceed"
- Timestamp: 2026-10-07T17:18:21-03:00

---

## 1. Contexto e Objetivos

Com base nos testes e no feedback com capturas de tela fornecidas pelo usuário:
1. **Ordenação Cronológica das Faturas:** As faturas de cartão de crédito estão sendo exibidas em ordem decrescente (`2026-12`, `2026-11`, `2026-10`). Devem ser listadas estritamente em **ordem crescente** (`2026-10`, `2026-11`, `2026-12`), facilitando a navegação temporal da fatura atual para as futuras.
2. **Design System & Contraste dos Botões de Fatura (*Industrial Integrity*):**
   - Os botões de faturas não selecionadas estão sendo renderizados com fundo branco (estilo padrão de botão do navegador), quebrando o padrão dark da aplicação.
   - O botão da fatura selecionada possui fundo escuro, porém o texto do mês (`2026-10`) está preto/escuro, tornando a leitura impossível.
   - É necessário criar um componente mecânico dedicado (`.fatura-timeline-btn`), com 0px border-radius, fundo dark uniforme (`#1e1e1e`), bordas ferrosas e, no estado ativo, fundo sutilmente avermelhado/ferroso (`#241610`), borda Rust Orange (`#B7410E`) e **texto estritamente branco/luminoso (`#FFFFFF !important`)**.
3. **Seleção de Cartão Corporativo no Modal de Novos Lançamentos:**
   - No modal de *Nova Despesa / Novo Lançamento*, deve haver um seletor específico para os cartões de crédito corporativos cadastrados.
   - **Regra de acoplamento reativo:**
     - Se o usuário selecionar um cartão na combobox de cartões corporativos, o campo *Meio de Pagamento* é automaticamente selecionado para `"CARTÃO DE CRÉDITO"` e fica bloqueado (`disabled`). O seletor de Conta Bancária de saída imediata é ocultado ou desabilitado, e o seletor de parcelas (1x a 12x) é exibido.
     - Se o usuário selecionar qualquer outro meio de pagamento (ex: PIX, Dinheiro, Boleto, Transferência), o campo de cartão de crédito **não deve ser exibido** (`display: none`), mantendo a seleção da Conta Bancária / Caixa ativa.
     - Se o usuário selecionar o meio de pagamento `"CARTÃO DE CRÉDITO"`, o seletor de cartões corporativos é exibido e focado.
4. **Escolha Explícita do Meio de Pagamento na Matriz de Distribuição (Caixa de Mercado):**
   - Atualmente, as linhas da matriz apenas alternavam entre `"CONTA / CAIXA"` e `"CARTÃO CRÉDITO"` de forma genérica, sem que o operador pudesse especificar qual o meio físico real utilizado naquela conta (ex: se na conta Nubank foi pago via **PIX**, **DÉBITO**, **TRANSFERÊNCIA** ou se no Caixa da Oficina foi pago em **DINHEIRO**).
   - Cada linha da matriz passará a ter um seletor explícito de **Meio de Pagamento** (Dinheiro, PIX, Cartão de Crédito, Débito, Transferência, Boleto, etc.).
   - Se o meio for *Cartão de Crédito*, a linha exibe o seletor de Cartão Corporativo + Parcelas ($N$x).
   - Se o meio for qualquer outro, a linha exibe o seletor de Conta Bancária / Caixa.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Ordenação e Componente Visual das Faturas (`financeiro-view.js` e `industrial-integrity.css`)
- **Ordenação:**
  ```javascript
  this.faturasLista.sort((a, b) => a.mes_referencia.localeCompare(b.mes_referencia));
  ```
- **CSS Especializado (*Industrial Integrity*):**
  - Criação da classe `.fatura-timeline-btn` com:
    - `background-color: var(--color-surface-container, #1e1e1e)`
    - `color: var(--color-on-surface, #e1e2e8)`
    - `border: 1px solid var(--color-outline-variant, #44474e)`
    - `border-radius: 0 !important`
  - Estado `.fatura-timeline-btn.active`:
    - `background-color: #241610 !important`
    - `border: 2px solid var(--color-rust-orange, #b7410e) !important`
    - `color: #ffffff !important`
    - `.fatura-mes { color: #ffffff !important; font-weight: 700; }`

### 2.2 Sincronização Reativa no Modal de Novo Lançamento (`financeiro-view.js`)
- Estruturação dos campos sob `#container-pagamento-simples`:
  - `Meio de Pagamento` (`#nl-meio`)
  - `Conta Bancária / Caixa` (`#wrapper-nl-conta`)
  - `Cartão Corporativo` (`#wrapper-nl-cartao`)
  - `Parcelamento Cartão` (`#wrapper-nl-parcelas`)
- **Event Listeners reativos:**
  - `#nl-cartao change`: se selecionado cartão, `#nl-meio` vai para ID de Cartão de Crédito e fica `disabled=true`; `#wrapper-nl-conta` é ocultado; `#wrapper-nl-parcelas` é exibido. Se desmarcado, `#nl-meio` é desbloqueado e `#wrapper-nl-conta` reexibido.
  - `#nl-meio change`: se selecionado outro meio (PIX, Dinheiro, etc.), `#wrapper-nl-cartao` fica `display: none` e `#wrapper-nl-parcelas` oculto; se selecionado Cartão de Crédito, `#wrapper-nl-cartao` é exibido e `#wrapper-nl-conta` ocultado.
  - `#nl-tipo change`: se mudar para `ENTRADA`, cartão corporativo é ocultado (cartões corporativos são exclusivos para despesas/saídas).
- **Submissão unificada:**
  - Se cartão estiver selecionado, envia via `POST /api/lancamentos-financeiros/lancar-multi-meio/` (com 1 item de cartão e parcelamento configurado) ou action direta de despesa, garantindo criação/vínculo automático na fatura aberta, ajuste de centavos e limite comprometido.
  - Se outro meio estiver selecionado, envia como lançamento financeiro tradicional para `/api/lancamentos-financeiros/`.

### 2.3 Matriz de Pagamentos Multi-Meio com Seleção de Meio (`financeiro-view.js`)
- Em cada linha da matriz (`.matriz-pagto-row`):
  - Coluna 1: `<select class="matriz-meio-id">` preenchido dinamicamente com todos os meios ativos de `listaMeios`.
  - Coluna 2: Container dinâmico `.matriz-alvo-container`:
    - Se o meio selecionado tiver "CART" e "CRED" no nome:
      - `<select class="matriz-cartao-id">` (Cartões existentes) + `<select class="matriz-parcelas">` (1x a 12x).
    - Para qualquer outro meio:
      - `<select class="matriz-conta-id">` (Contas bancárias / caixas com saldo atualizado).
  - Coluna 3: `<input class="matriz-row-valor" data-mask="moeda-atm">`.
  - Coluna 4: Botão remover `✕`.
- No envio, o objeto enviado no array `matriz_pagamentos` inclui:
  `{ meio_pagamento_id, tipo_meio, conta_id, cartao_id, total_parcelas, valor, descricao }`.

### 2.4 Compatibilidade no Serializer Backend (`serializers.py`)
- Em `LancamentoFinanceiroSerializer.to_internal_value`:
  - Adicionar suporte a `cartao_id` como alias de `cartao_credito` (além de `cartao_credito_id`), tornando a API flexível e uniforme.

### 2.5 Governança de PWA e Assets
- `frontend/sw.js`: incrementar versão de cache de `emc-soldas-v4.60` para `emc-soldas-v4.61`.
- `frontend/index.html`: atualizar sufixos de cache-busting de `?v=4.60` para `?v=4.61`.

---

## 3. Arquivos Afetados

| Arquivo | Natureza da Alteração |
| :--- | :--- |
| `frontend/assets/css/industrial-integrity.css` | Criação das regras `.fatura-timeline-btn`, `.fatura-timeline-btn.active` e `.fatura-mes` com contraste e paleta industrial. |
| `frontend/assets/js/views/financeiro-view.js` | Ordenação crescente de faturas, aplicação das novas classes de botões, dinâmica de seleção de cartão/meio no modal simples e seletor de meios na matriz multi-meio. |
| `backend/apps/financeiro/serializers.py` | Suporte a `cartao_id` no `to_internal_value` de `LancamentoFinanceiroSerializer`. |
| `frontend/sw.js` | Atualização do `CACHE_NAME` para `emc-soldas-v4.61`. |
| `frontend/index.html` | Atualização das tags `<script>` e `<link>` para `?v=4.61`. |
| `docs/STATUS.md` | Registro dos refinamentos de UX da Tesouraria e Cartões. |
| `Planejamento/2026-10-07_04_ajustes_faturas_crescentes_botoes_cartao_e_matriz_meios.md` | Salvamento permanente do plano aprovado. |

---

## 4. Plano de Verificação e Testes

1. **Testes Visuais no Frontend:**
   - Navegar até **Financeiro > CARTÕES CORPORATIVOS**.
   - Conferir se as faturas aparecem em ordem crescente (`2026-10`, `2026-11`, `2026-12`).
   - Conferir se os botões não selecionados possuem fundo escuro uniforme (sem botões brancos no dark theme).
   - Clicar nas faturas e verificar que o botão ativo possui borda Rust Orange e texto `YYYY-MM` estritamente branco (`#FFFFFF`) e perfeitamente legível.
2. **Teste de Seleção de Cartão no Modal Simples:**
   - Clicar em `+ NOVO LANÇAMENTO` (Despesa a Pagar).
   - Selecionar um cartão na combobox de cartões: verificar que Meio de Pagamento muda para "CARTÃO DE CRÉDITO" e bloqueia (`disabled`), Conta Bancária é ocultada e Parcelas é exibida.
   - Desmarcar o cartão: verificar que Meio de Pagamento desbloqueia e Conta Bancária reaparece.
   - Selecionar "PIX" ou "DINHEIRO" no Meio de Pagamento: verificar que a combobox de cartão desaparece.
   - Selecionar "CARTÃO DE CRÉDITO" no Meio de Pagamento: verificar que a combobox de cartão reaparece.
3. **Teste da Matriz de Pagamentos (Caixa de Mercado):**
   - Ativar o switch de matriz de pagamento.
   - Adicionar formas de pagamento e verificar a presença do seletor de Meio de Pagamento em cada linha.
   - Alterar entre "PIX", "DINHEIRO" e "CARTÃO DE CRÉDITO" e observar a alternância instantânea entre Conta/Caixa e Cartão+Parcelas.
   - Efetuar a gravação de uma compra mista e confirmar a integridade contábil.
4. **Suíte de Testes Automatizados:**
   - Executar `python backend/manage.py test apps core` e garantir que 100% dos testes continuem aprovados (209/209).

---

## 5. Relatório de Execução (Pós-conclusão)

Todas as metas definidas no plano foram integralmente implementadas e verificadas:

1. **Ordenação Cronológica Crescente das Faturas:**
   - Implementado sort determinístico em `carregarMetricasEFaturasCartao` via `(a.mes_referencia || '').localeCompare(b.mes_referencia || '')`.
   - As faturas agora são dispostas linearmente da mais antiga/atual para as futuras (ex: `2026-10`, `2026-11`, `2026-12`).

2. **Design System & Contraste Técnico (*Industrial Integrity*):**
   - Criada a classe `.fatura-timeline-btn` com fundo escuro (`#1e1e1e`), bordas ferrosas (`#44474e`) e cantos retos (0px border-radius). Eliminado o estilo padrão de botão branco do navegador.
   - Estado ativo (`.fatura-timeline-btn.active`) estilizado com fundo escuro ferroso (`#241610`), borda de 2px Rust Orange (`#B7410E`) e texto estritamente branco (`#FFFFFF !important`) com tipografia nítida e legível em alto contraste.

3. **Integração de Cartão Corporativo no Modal de Novos Lançamentos:**
   - Integrado o seletor `#nl-cartao` com lista de cartões corporativos ativos e limites disponíveis.
   - Sincronização reativa bidirecional:
     - Seleção de cartão altera `#nl-meio` para "CARTÃO DE CRÉDITO", trava como `disabled`, oculta seletor de conta bancária e exibe seletor de parcelas (1x a 12x).
     - Seleção de outro meio (PIX, Dinheiro, Boleto, etc.) oculta o seletor de cartão de crédito e reexibe a conta bancária.
     - Seleção de "CARTÃO DE CRÉDITO" diretamente no meio de pagamento reexibe o seletor de cartões.
     - Mudança de tipo para `ENTRADA` oculta qualquer opção de cartão corporativo.
   - Na submissão, se houver cartão selecionado, os dados são despachados de forma atômica para `/api/lancamentos-financeiros/lancar-multi-meio/` com divisão de parcelas e vínculo automático com a fatura aberta do mês.

4. **Meio de Pagamento Explícito em Cada Linha da Matriz ("Caixa de Mercado"):**
   - Cada linha adicionada na matriz de distribuição de pagamentos agora possui um combobox `<select class="matriz-meio-id">` com todos os meios cadastrados (Dinheiro, PIX, Cartão de Crédito, Débito, Transferência, etc.).
   - Se o meio selecionado contiver "CART" e "CRED", a linha exibe o seletor de Cartões Corporativos + Seletor de Parcelas.
   - Para quaisquer outros meios, exibe o seletor de Contas Bancárias / Caixa com saldo em tempo real.
   - A submissão transmite `meio_pagamento_id`, `cartao_id`, `total_parcelas`, `conta_id` e `valor`, garantindo conciliação detalhada e rastreabilidade total.

5. **Serializer Backend:**
   - `LancamentoFinanceiroSerializer.to_internal_value` atualizado para aceitar `cartao_id` como alias direto de `cartao_credito`.

6. **Versionamento e Testes:**
   - Cache de Service Worker incrementado para `emc-soldas-v4.61` em `frontend/sw.js`.
   - Cache-busting atualizado para `?v=4.61` em todas as tags `<link>` e `<script>` de `frontend/index.html`.
   - Suíte de testes automatizados executada: **209/209 testes aprovados (100% de sucesso)**.
