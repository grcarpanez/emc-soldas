# Plano de Implementação - Botão e Modal Sobreposto para Cadastro Rápido de Equipamento no Orçamento

- **Data de Criação:** 05/10/2026
- **Autor:** Antigravity AI & Gustavo
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 05/10/2026 às 12:35:27 (Horário de Brasília)
  - **Transcrição da Aprovação do Usuário:** *"Proceed"*

---

## 1. Contexto e Diagnóstico

### 1.1 Motivação
Na elaboração ágil de um orçamento comercial (`orcamentos-view.js`), ao selecionar um cliente, a combobox de **Equipamento / Máquina** filtra os veículos daquele cliente. Caso o cliente ainda não tenha o veículo/máquina cadastrado no sistema (ou seja um equipamento novo), o operador atualmente precisaria cancelar ou sair da tela de orçamentos, navegar até o módulo de **Cadastros**, registrar o equipamento e retornar para começar o orçamento do zero.

Para garantir a máxima agilidade operacional adotada no restante do sistema (como já implementado para fornecedores e insumos no módulo de compras), o usuário solicitou um botão direto para criar o equipamento ali mesmo, abrindo um modal sobreposto (stacked modal) sem perda do contexto ou dos dados já preenchidos no orçamento.

### 1.2 Atenção Especial à Hierarquia de Camadas (`z-index`)
O usuário destacou que **nenhuma camada ou modal sobreposto pode ter `z-index` superior ao das notificações** (toasts do sistema).

Auditoria da escala de `z-index` no Design System (*Industrial Integrity*):
```text
┌────────────────────────────────────────────────────────┐
│ 1. Notificações / Toasts (#toast-container)            │  z-index: 999999  (NÍVEL MÁXIMO ABSOLUTO)
├────────────────────────────────────────────────────────┤
│ 2. Dropdowns de Combobox (.emc-combobox-dropdown)      │  z-index: 999998
├────────────────────────────────────────────────────────┤
│ 3. Modal Sobreposto / Nível 2 (Cadastrar Equipamento)  │  z-index: 100020
├────────────────────────────────────────────────────────┤
│ 4. Modal Base / Nível 1 (Elaboração de Orçamento)      │  z-index: 100000
└────────────────────────────────────────────────────────┘
```
**Conclusão da auditoria:** O sistema de modais empilhados do `EMCUtils.openModal` opera na faixa de `100000 + (stack * 20)` (`100000`, `100020`, etc.). As notificações (`.toast-container`) estão fixadas no teto absoluto de `999999`. Portanto, qualquer toast de sucesso (*"Equipamento criado com sucesso!"*) ou erro continuará aparecendo **estritamente acima de ambos os modais e de qualquer dropdown**, sem qualquer risco de sobreposição indevida.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Habilitação de Callback `onSuccess` em `cadastros-view.js`:**
   - Atualizar a assinatura do método existente `abrirModalEquipamento(equip = null, preSelectClienteId = null, opts = {})`.
   - Apoiar o recebimento de `opts.onSuccess(novoEquip)`.
   - Ao concluir a criação com sucesso via `POST /api/equipamentos/`, disparar `await opts.onSuccess(resEquip)`, permitindo que telas consumidoras recebam o objeto do equipamento criado e atualizem suas interfaces reativamente.
   - Proteger chamadas internas (`this.carregarListaEquipamentos()`) para que operem com segurança mesmo quando o modal for instanciado fora da aba de Cadastros.

2. **Integração Dupla no Formulário de Orçamento (`orcamentos-view.js`):**
   - **No Cabeçalho do Campo:** Inserir o botão `+ NOVO EQUIPAMENTO` na barra superior do rótulo do campo `Equipamento / Máquina`, com estilo padronizado `btn-ghost btn-sm` (cor `var(--color-rust-orange)`), idêntico ao já existente no módulo de Compras para fornecedores e insumos.
   - **Alinhamento Perfeito das Linhas:** Padronizar a altura dos cabeçalhos dos 3 campos do grid (`Cliente *`, `Equipamento / Máquina` e `Validade (Dias)`) com `min-height: 22px; margin-bottom: 4px;`, garantindo que os inputs e comboboxes fiquem perfeitamente alinhados na mesma linha horizontal.
   - **Na Ação da Combobox:** Configurar o parâmetro `action: { label: '+ CADASTRAR NOVO EQUIPAMENTO', onClick: () => dispararCadastroNovoEquipamento() }` na inicialização do `initSearchableSelect` de equipamentos.
   - **Disparador `dispararCadastroNovoEquipamento`:**
     - Identifica o cliente atualmente selecionado no orçamento (`selCli.value`).
     - Abre o modal de cadastro via `window.CadastrosView.abrirModalEquipamento(null, clienteId, { onSuccess: ... })`.
     - No `onSuccess`:
       - Busca a lista atualizada de equipamentos via API REST.
       - Atualiza dinamicamente as opções da combobox (`selEq._emcCombobox.updateOptions(...)`).
       - Pré-seleciona imediatamente o novo equipamento criado.
       - Caso o orçamento estivesse sem cliente selecionado e o operador associou um cliente no cadastro do equipamento, auto-seleciona esse cliente também no orçamento.

3. **Governança de Versão PWA e Cache Busting:**
   - Incrementar `CACHE_NAME` para `'emc-soldas-v4.52'` em `frontend/sw.js`.
   - Atualizar a query string para `?v=4.52` em `frontend/index.html`.

---

## 3. Arquivos Afetados

- `frontend/assets/js/views/cadastros-view.js`
- `frontend/assets/js/views/orcamentos-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `Planejamento/2026-10-05_03_cadastro_rapido_equipamento_modal_orcamento.md`
- `docs/STATUS.md`

---

## 4. Plano de Verificação e Testes

1. Testar o fluxo completo de criação de equipamento a partir do modal de orçamento.
2. Validar que apenas o modal de equipamento fecha ao confirmar e que o orçamento permanece aberto com o novo equipamento selecionado.
3. Certificar que as notificações toast aparecem no topo com `z-index: 999999`.
4. Executar suíte de testes automatizados: `python backend/manage.py test backend/`.

---

## 5. Relatório de Execução e Homologação

- **Data de Conclusão:** 05/10/2026
- **Execução Realizada:**
  1. `frontend/assets/js/views/cadastros-view.js`:
     - Assinatura de `abrirModalEquipamento(equip = null, preSelectClienteId = null, opts = {})` expandida para aceitar opções flexíveis.
     - Capturado o objeto `resEquip` retornado pelo POST/PUT e disparado o callback assíncrono `await opts.onSuccess(resEquip)`.
     - Blindadas as chamadas a `this.carregarListaEquipamentos()` e `this.carregarListaClientes()` com verificação de tipo funcional para evitar quebras em contextos externos.
  2. `frontend/assets/js/views/orcamentos-view.js`:
     - Adicionado o botão `+ NOVO EQUIPAMENTO` (`btn-ghost btn-sm`) na barra de título do campo `Equipamento / Máquina`.
     - Homogeneizada a altura dos cabeçalhos dos campos do grid (`Cliente *`, `Equipamento / Máquina` e `Validade (Dias)`) com `min-height: 22px; margin-bottom: 4px;` para alinhamento estético uniforme.
     - Integrada a ação `action: { label: '+ CADASTRAR NOVO EQUIPAMENTO', onClick: () => dispararCadastroNovoEquipamento() }` na combobox de equipamentos, acessível mesmo na ausência de opções prévias.
     - Implementado o método `dispararCadastroNovoEquipamento()` com pré-seleção do cliente atual e callback `onSuccess` que recarrega a lista de equipamentos, atualiza a combobox via `selEq._emcCombobox.updateOptions()` e auto-seleciona o novo equipamento criado.
  3. Conformidade Rigorosa de `z-index`:
     - O modal sobreposto opera em camada `z-index: 100020`.
     - As notificações (toasts) permanecem no topo absoluto da aplicação com `z-index: 999999` (`#toast-container`), garantindo visibilidade total sem oclusão.
  4. Governança de Cache PWA:
     - Atualizado `CACHE_NAME` para `'emc-soldas-v4.52'` em `frontend/sw.js`.
     - Atualizadas as query strings de estilos e scripts para `?v=4.52` em `frontend/index.html`.
  5. Bateria de Testes Automatizados:
     - Executado `python backend/manage.py test backend/`: 201 testes executados e aprovados com 100% de sucesso (81.4s).
