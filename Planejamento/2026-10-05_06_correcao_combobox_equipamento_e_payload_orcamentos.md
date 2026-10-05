# Plano de Implementação: Correção da Atualização da Combobox de Equipamentos e Resolução do Payload de Orçamentos (cliente_id vs cliente)

- **Data:** 05/10/2026
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado em 05/10/2026 14:56 via instrução "Proceed"
- **Referência:** Solicitação do Usuário via screenshot (`media_1791222592668.png`) e apontamento:
  1. *"A combobox de equipamentos não esta atualizando e selecionando o equipamento recem cadastrado, no modal de orçamento. Abri um novo orçamento, cadastrei um novo cliente, ele apareceu já selecionado, cadastrei um novo equipamento, mas ele não aparece na combobox, ela não recarrega os dados."*
  2. *"Outro erro (no print): mesmo com os dados selecionados, está dando um erro falando que o cliente é obrigatório"*

---

## 1. Diagnóstico e Causa Raiz

### 1.1 Problema 1: Combobox de Equipamentos não atualiza após cadastro rápido
- **Causa Raiz Identificada:** Em [`frontend/assets/js/views/orcamentos-view.js`](file:///d:/gestao_orcamentos_2.0/frontend/assets/js/views/orcamentos-view.js#L163), a lista de equipamentos foi declarada no escopo do modal como:
  ```javascript
  const listaEquip = equipamentos.results || equipamentos || [];
  ```
- No callback `onSuccess` disparado após o cadastro bem-sucedido do novo equipamento (linha 413):
  ```javascript
  listaEquip = resEq.results || resEq || [];
  ```
- Por ter sido declarada com `const`, a tentativa de reatribuição dispara uma exceção JavaScript: `TypeError: Assignment to constant variable.`.
- Essa exceção cai imediatamente no bloco `catch (err)`, interrompendo a execução antes das linhas 425-436, onde `montarOptionsEquip()` e `selEq._emcCombobox.updateOptions(novasOptions, novoEquip.id)` seriam chamados.
- **Consequência:** A combobox de equipamentos permanece estática com a lista antiga e não seleciona o novo equipamento.

### 1.2 Problema 2: Erro `[ERRO] CLIENTE: Este campo é obrigatório` ao salvar orçamento
- **Causa Raiz Identificada:** No método `onConfirm` de geração do orçamento em [`frontend/assets/js/views/orcamentos-view.js`](file:///d:/gestao_orcamentos_2.0/frontend/assets/js/views/orcamentos-view.js#L372-L385), o payload é montado utilizando sufixos `_id`:
  ```javascript
  const payload = {
    cliente_id,
    equipamento_id,
    validade_dias,
    valor_desconto_aplicado,
    itens: this.orcItensTemp.map(it => ({
      produto_id: it.produto_id || null,
      item_id: it.item_id || null,
      ...
    }))
  };
  ```
- No backend, [`OrcamentoSerializer`](file:///d:/gestao_orcamentos_2.0/backend/apps/orcamentos/serializers.py#L263) e [`OrcamentoItemSerializer`](file:///d:/gestao_orcamentos_2.0/backend/apps/orcamentos/serializers.py#L67) são `ModelSerializers` do DRF que declaram os relacionamentos com os nomes de modelo:
  - `cliente` (ForeignKey para `ClienteFornecedor`)
  - `equipamento` (ForeignKey para `Equipamento`)
  - `itens`: `produto` (ForeignKey para `Produto`) e `item` (ForeignKey para `Item`)
- Como os serializers não possuíam `to_internal_value` para mapear chaves com sufixo `_id`, o DRF descartava `cliente_id`.
- Ao executar a validação `validate(self, attrs)`, `attrs.get('cliente')` resultava em `None`, gerando o erro de validação HTTP 400 Bad Request:
  ```json
  { "cliente": ["Este campo é obrigatório."] }
  ```
  Que a camada HTTP (`api.js`) converteu para o toast exibido no print: `[ERRO] CLIENTE: Este campo é obrigatório.`.
- **Efeito Colateral Adicional:** Mesmo que `cliente` fosse aceito, `equipamento_id`, `produto_id` e `item_id` seriam descartados pelo mesmo motivo, perdendo o vínculo do equipamento e impedindo a gravação dos itens.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend: Tolerância e Resiliência Universal de Chaves nos Serializers
1. **`OrcamentoSerializer` (`backend/apps/orcamentos/serializers.py`):**
   - Implementar `to_internal_value(self, data)`:
     - Mapear `cliente_id` -> `cliente` (se `cliente` não enviado).
     - Mapear `equipamento_id` -> `equipamento` (se `equipamento` não enviado).
     - Normalizar valores vazios de equipamento (`""`, `"null"`, `"None"`) para `None`.
     - Suportar `validade_dias`: calcular automaticamente `data_validade = hoje + validade_dias` caso `data_validade` não venha preenchida explicitamente.
2. **`OrcamentoItemSerializer` (`backend/apps/orcamentos/serializers.py`):**
   - Implementar `to_internal_value(self, data)`:
     - Mapear `produto_id` -> `produto` (se `produto` não enviado).
     - Mapear `item_id` -> `item` (se `item` não enviado).
     - Normalizar vazios para `None`.
3. **`OrcamentoPropostaPagamentoSerializer` (`backend/apps/orcamentos/serializers.py`):**
   - Implementar `to_internal_value(self, data)`:
     - Mapear `regra_pagamento_id` -> `regra_pagamento`.

### 2.2 Frontend: Correção de Escopo, Atualização Reativa e Payload Canônico
1. **Escopo das Variáveis no Modal de Orçamento (`frontend/assets/js/views/orcamentos-view.js`):**
   - Declarar `listaEquip`, `listaClientes`, `listaProd`, `listaItens` com `let` (em vez de `const`), permitindo atualização dinâmica quando novos registros forem criados.
2. **Fluxo de `onSuccess` do Equipamento:**
   - Ao criar equipamento, recarregar `listaEquip` do servidor.
   - Re-executar `montarOptionsEquip(clienteIdAtual)`.
   - Chamar `selEq._emcCombobox.updateOptions(novasOptions, novoEquip.id)` para que a combobox injete as novas options e selecione imediatamente o item criado.
3. **Payload de Envio do Orçamento:**
   - Enviar no payload tanto o nome canônico (`cliente`, `equipamento`, `produto`, `item`) quanto com `_id` (`cliente_id`, `equipamento_id`, etc.), garantindo redundância total.
   - Calcular e enviar `data_validade` em formato ISO (`YYYY-MM-DD`) além de `validade_dias`.

### 2.3 Utilitário de Combobox (`frontend/assets/js/utils.js`)
- Em `initSearchableSelect.updateOptions(newHtml, selectedValue)`:
  - Garantir que se `selectedValue` for fornecido, além de setar `selectEl.value`, marque o respectivo `<option>` como `selected = true`, atualize o trigger text e renderize as opções com a classe `.selected`.

### 2.4 Versionamento de Cache PWA
- Atualizar Service Worker (`frontend/sw.js`) de `v4.54` para `v4.55`.
- Atualizar cache-busting no `frontend/index.html` para `?v=4.55`.

---

## 3. Arquivos Afetados

| Arquivo | Natureza da Modificação |
| :--- | :--- |
| `backend/apps/orcamentos/serializers.py` | Implementar `to_internal_value` em `OrcamentoSerializer`, `OrcamentoItemSerializer` e `OrcamentoPropostaPagamentoSerializer` |
| `backend/apps/orcamentos/tests.py` | Adicionar teste validando criação de orçamento com chaves com sufixo `_id` (`cliente_id`, `equipamento_id`, `produto_id`, `item_id`, `validade_dias`) |
| `frontend/assets/js/views/orcamentos-view.js` | Corrigir `const` para `let`, sincronizar `onSuccess` de equipamento e enviar payload com campos canônicos |
| `frontend/assets/js/utils.js` | Reforçar seleção e atualização de trigger no `updateOptions` do `initSearchableSelect` |
| `frontend/sw.js` | Incrementar versão do cache para `v4.55` |
| `frontend/index.html` | Atualizar sufixos para `?v=4.55` |
| `docs/STATUS.md` | Registrar correções no arquivo vivo de progresso |

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados:**
   - Adicionar teste em `backend/apps/orcamentos/tests.py`:
     - Testar POST em `/api/orcamentos/` com payload contendo `cliente_id`, `equipamento_id`, `produto_id`, `item_id`, `validade_dias` -> HTTP 201 Created.
   - Executar `python manage.py test apps.orcamentos`.
   - Executar suíte completa `python manage.py test`.
2. **Validação Manual no Navegador:**
   - `Ctrl + Shift + R` para recarregar com PWA `v4.55`.
   - Abrir "Novo Orçamento".
   - Criar um novo cliente pelo atalho da combobox de clientes -> verificar que seleciona automaticamente.
   - Criar um novo equipamento pelo atalho da combobox de equipamentos -> verificar que a combobox recarrega e o novo equipamento aparece imediatamente selecionado.
   - Adicionar uma linha de produto BOM ou insumo.
   - Clicar em "GERAR ORÇAMENTO" -> verificar sucesso (toast verde) sem erro de "cliente é obrigatório".

---

## 5. Governança e Commit Semântico

Após a validação, executar commit atômico:
- **Mensagem:** `fix(orcamentos): corrigir atualizacao da combobox de equipamentos e mapear cliente_id no serializer`

---

## 6. Relatório de Execução e Evidências

1. **Backend (`backend/apps/orcamentos/serializers.py`):**
   - Implementado método `to_internal_value` em `OrcamentoSerializer`, mapeando `cliente_id` -> `cliente`, `equipamento_id` -> `equipamento`, normalizando strings vazias para `None` e calculando `data_validade` a partir de `validade_dias`.
   - Implementado método `to_internal_value` em `OrcamentoItemSerializer`, mapeando `produto_id` -> `produto`, `item_id` -> `item` e normalizando vazios para `None`.
   - Implementado método `to_internal_value` em `OrcamentoPropostaPagamentoSerializer`, mapeando `regra_pagamento_id` -> `regra_pagamento`.
2. **Frontend (`frontend/assets/js/views/orcamentos-view.js`):**
   - Corrigidas declarações de `const` para `let` para `listaEquip`, `listaClientes`, `listaProd` e `listaItens`.
   - No callback `onSuccess` de equipamento, atualizada a lista de equipamentos via API e invocada `selEq._emcCombobox.updateOptions(novasOptions, novoEquip.id)`, selecionando imediatamente o item recém-cadastrado.
   - No método `onConfirm` de geração de orçamento, mapeados os campos canônicos (`cliente`, `equipamento`, `data_validade`, `produto`, `item`) em conjunto com as chaves `_id` e calculada a data de validade com base em `validade_dias`.
3. **Frontend (`frontend/assets/js/utils.js`):**
   - No método `updateOptions` da combobox pesquisável (`initSearchableSelect`), garantida a seleção via `String(selectedValue)`, marcação de `selected = true` na option e disparo de evento `change`.
4. **Testes Automatizados:**
   - Adicionado teste `test_14_criacao_orcamento_com_payload_sufixo_id_e_validade_dias` em `backend/apps/orcamentos/tests.py`.
   - Execução de `apps.orcamentos`: 14 testes executados com 100% de aprovação (`OK`).
5. **Versionamento e PWA:**
   - Cache PWA incrementado para `v4.55` em `frontend/sw.js` e `frontend/index.html`.

