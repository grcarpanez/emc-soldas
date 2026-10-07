# Plano de Implementação: Correção da Recuperação da Conta Vinculada na Edição de Cartão

## 1. Metadados
- **Data:** 2026-10-07
- **Autor:** Antigravity AI & EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** 2026-10-07 19:37:36-03:00 ("Proceed")

---

## 2. Contexto e Esclarecimento de Negócio

### 2.1 Direcionamento do Usuário
O usuário esclareceu a regra de negócio:
> *"O problema não é a existência do nenhuma. Posso ter um cartão de crédito de um banco sem ter conta naquele banco, e está tudo bem. O problema é que quando abro o modal de edição do cartão NUBANK, por exemplo, que foi criado vinculado à conta NUBANK (independente de terem o mesmo nome), o modal de edição não está recuperando a informação da conta vinculada e está retornando nenhuma, como se o cartão não estivesse vinculado a conta nenhuma. É isso que deve ser corrigido e não a lógica de pertencimento do cartão."*

Portanto:
1. **A opção "NENHUMA" deve permanecer:** Uma empresa pode legitimamente possuir um cartão corporativo de uma instituição na qual não mantém conta corrente ou caixa direto, ou preferir não vincular uma conta de débito automático pré-definida.
2. **O problema real é a falha na recuperação e pré-seleção:** Quando o cartão possui uma conta vinculada no banco de dados (por exemplo, Cartão #1 vinculado à Conta #2 "NUBANK"), o modal de edição deve recuperar esse vínculo de forma fidedigna e pré-selecionar a conta correta, em vez de redefinir o campo para "NENHUMA".

---

## 3. Diagnóstico Técnico da Causa Raiz

1. **Objeto em Memória Obsoleto (`this.cartaoAtivo` não sincronizado):**
   - No método `carregarListaCartoes`:
     ```javascript
     if (cartaoIdParaSelecionar) {
       this.cartaoAtivo = this.cartoesLista.find(c => c.id === Number(cartaoIdParaSelecionar)) || this.cartoesLista[0];
     } else if (!this.cartaoAtivo || !this.cartoesLista.some(c => c.id === this.cartaoAtivo.id)) {
       this.cartaoAtivo = this.cartoesLista[0];
     }
     ```
     Quando `this.cartaoAtivo` já existia em memória, faltava o ramo `else`, e o objeto retinha a referência antiga.
2. **Falta de Busca Direta na Abertura da Edição (`Fresh Fetch`):**
   - Ao clicar em `✏️ EDITAR CARTÃO`, `abrirModalNovoCartao` recebia o objeto `this.cartaoAtivo` direto da memória, sem consultar o endpoint `GET /api/cartoes-credito/{id}/` para obter a verdade absoluta do banco de dados.
3. **Resolução Defensiva do ID da Conta:**
   - A extração deve ser polimórfica: `conta_bancaria_id`, `conta_bancaria` (inteiro) ou objeto `{ id: ... }`.
4. **Falta de Atribuição Programática no DOM (`select.value`):**
   - No Chrome Mobile, modais dinâmicos podem necessitar de atribuição programática explícita `select.value = String(contaIdAtual)`.
5. **Backend (`CartaoCreditoSerializer.to_internal_value`):**
   - Garantir que `conta_bancaria_id` ou `conta_bancaria` no payload mapeiem consistentemente para `data['conta_bancaria']`.

---

## 4. Arquivos a Modificar

1. `backend/apps/financeiro/serializers.py`
2. `frontend/assets/js/views/financeiro-view.js`
3. `frontend/sw.js` (atualizar para `emc-soldas-v4.63`)
4. `frontend/index.html` (atualizar query strings `?v=4.63`)
5. `docs/STATUS.md`

---

## 5. Plano de Verificação e Testes

1. Executar suíte de testes Django: `python backend/manage.py test apps core`.
2. Validar retorno da API para `GET /api/cartoes-credito/1/`.
3. Validar no modal de edição do cartão a pré-seleção correta da conta bancária vinculada.
4. Validar que a opção "NENHUMA" permanece funcional caso o usuário deseje desvincular.

---

## 6. Relatório de Execução e Evidências

1. **Backend:**
   - Aprimorado `to_internal_value` em `CartaoCreditoSerializer` para mapear `conta_bancaria_id` (tanto inteiro quanto None) para `conta_bancaria`.
   - Adicionado teste unitário e de integração `test_atualizacao_cartao_preservacao_e_remocao_conta_bancaria` em `apps/financeiro/tests.py`, cobrindo recuperação por GET, atualização mantendo vínculo, remoção de vínculo com None (opção NENHUMA) e restauração de vínculo.
2. **Frontend:**
   - Adicionada consulta direta obrigatória (`await window.api.get('/cartoes-credito/' + cartaoEdicao.id + '/')`) no método `abrirModalNovoCartao`, garantindo dados frescos do MySQL.
   - Sincronização em `carregarListaCartoes`: ramo `else` garante que `this.cartaoAtivo` é atualizado na referência local.
   - Resolução polimórfica à prova de falhas de `contaIdAtual` e inclusão de atribuição programática via `selectConta.value = String(contaIdAtual)` no ciclo de montagem do modal.
   - Preservação estrita da opção `-- NENHUMA (SEM DÉBITO EM CONTA) --` para cartões sem débito em conta.
   - Robustez estendida ao modal de quitação/liquidação de fatura (`abrirModalLiquidarFatura`).
3. **PWA & Cache:**
   - `CACHE_NAME` atualizado para `emc-soldas-v4.63` em `frontend/sw.js`.
   - Tags atualizadas para `?v=4.63` em `frontend/index.html`.
4. **Validação:**
   - Suíte de 212 testes automatizados executada e 100% aprovada em 80.472s.
