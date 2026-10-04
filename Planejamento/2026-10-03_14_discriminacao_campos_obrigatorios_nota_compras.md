# Implementation Plan - Validação Clara e Destaque Visual de Campos Obrigatórios na Nota de Compra

- **Data:** 2026-10-03
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** Aguardando Aprovação (Pendente de `Proceed`)
- **Fase de Referência:** Fase 14.5 (UX, Compras e Cadastros)
- **Versão do PWA Alvo:** v4.45 (Incremento de v4.44 -> v4.45)

---

## 1. Contexto e Diagnóstico

### 1.1 O Problema Relatado
Ao tentar registrar ou salvar a nota fiscal de compra, o sistema exibe a mensagem de erro genérica:
```text
Preencha os campos obrigatórios da nota.
```
No entanto, o operador relata que, visualmente na tela, "não há nenhum campo obrigatório sem preenchimento".

### 1.2 Análise da Causa Raiz
No arquivo `frontend/assets/js/views/compras-view.js` (linhas 314–317):
```javascript
if (!fornecedor_id || !num_nota || !data_compra) {
  window.EMCUtils.showToast('Preencha os campos obrigatórios da nota.', 'error');
  return false;
}
```
Essa validação apresenta três problemas críticos de experiência do usuário (UX):
1. **Mensagem Genérica e Opaca:** A notificação não diz **qual** dos campos está faltando (`fornecedor_id`, `num_nota` ou `data_compra`).
2. **Ausência de Feedback Visual:** Nenhum dos campos com erro recebe borda vermelha, foco ou destaque, impedindo que o operador identifique o que o formulário considera pendente.
3. **Casos Ocultos de Campo Vazio:**
   - **Fornecedor no Combobox:** Se o usuário importou um PDF/XML de um fornecedor não cadastrado e fechou o modal de fornecedor, ou se digitou no campo de busca do combobox mas não clicou no item da lista suspensa, o `<select id="nota-fornecedor">` permanece com valor vazio (`""`), enquanto na tela o operador vê os dados do anexo preenchidos.
   - **Data de Emissão:** Se a data extraída do documento vier em formato rejeitado pelo `<input type="date">` (que exige estritamente `YYYY-MM-DD`), o browser limpa o campo silenciosamente para `""`.
   - **Sub-item Pendente:** Se o operador preencheu Insumo, Quantidade e Valor, mas esqueceu de clicar no botão secundário `+ ADICIONAR ITEM` antes de clicar no botão principal `REGISTRAR COMPRA`, a lista de itens fica vazia.

---

## 2. Decisões Técnicas e Solução Arquitetural

1. **Validação Específica Campo a Campo com Nomes Amigáveis:**
   - Em vez de uma condição única com mensagem genérica, verificar individualmente:
     - `fornecedor_id`: "Selecione o Fornecedor da nota fiscal."
     - `num_nota`: "Informe o Número da nota fiscal (NF-e/Recibo)."
     - `data_compra`: "Informe a Data de Emissão da nota fiscal."
   - Se mais de um campo estiver vazio, listar explicitamente os nomes dos campos faltantes (ex: `"Preencha os campos obrigatórios: Fornecedor e Data de Emissão."`).
2. **Destaque Visual Imediato (Borda Vermelha Industrial e Foco):**
   - Aplicar estilo/classe de erro com borda vermelha industrial (`border: 2px solid var(--color-error) !important;`) nos campos não preenchidos.
   - Se for o fornecedor, aplicar o destaque visual diretamente no trigger do combobox estilizado (`.emc-combobox-trigger`).
   - Aplicar foco automático (`focus()`) no primeiro campo com pendência para orientar o operador instantaneamente.
   - Limpar o destaque visual assim que o operador selecionar ou preencher o campo (listeners de `input` e `change`).
3. **Auto-Inclusão Inteligente de Sub-Item Pendente:**
   - Ao clicar em `REGISTRAR COMPRA`, se a lista `this.itensTemp` estiver vazia mas os campos de sub-item (`sub-item-id`, `sub-item-qtd`, `sub-item-unit`) estiverem preenchidos com valores válidos, o sistema automaticamente aciona a inclusão do item na nota e prossegue com o registro, eliminando o erro de "item esquecido".
4. **Proteção no Formato da Data:**
   - Garantir que qualquer data preenchida (seja via anexo ou manual) seja convertida estritamente para `YYYY-MM-DD`, prevenindo que o `<input type="date">` fique em branco.
5. **Versionamento PWA (Regra 12):**
   - Atualizar `CACHE_NAME` para `emc-soldas-v4.45` em `frontend/sw.js`.
   - Atualizar os sufixos de versão para `?v=4.45` em `frontend/index.html`.
6. **Governança:**
   - Testar com `node -c` e bateria de testes `apps.compras`.
   - Atualizar `docs/STATUS.md` e arquivar o plano em `Planejamento/2026-10-03_14_discriminacao_campos_obrigatorios_nota_compras.md`.
   - Executar commit semântico (Regra 13).

---

## 3. Arquivos a Modificar / Criar

| Arquivo | Ação | Descrição |
| :--- | :--- | :--- |
| `frontend/assets/js/views/compras-view.js` | Modificar | Validação discriminada campo a campo, destaque com borda vermelha, foco automático e auto-inclusão de sub-item pendente. |
| `frontend/sw.js` | Modificar | Incrementar `CACHE_NAME` para `emc-soldas-v4.45` (Regra 12). |
| `frontend/index.html` | Modificar | Atualizar sufixos para `?v=4.45` (Regra 12). |
| `Planejamento/2026-10-03_14_discriminacao_campos_obrigatorios_nota_compras.md` | Criar | Arquivamento do plano e registro de governança. |
| `docs/STATUS.md` | Modificar | Registro da entrega v4.45. |

---

## 4. Plano de Verificação e Testes

1. `node -c frontend/assets/js/views/compras-view.js`
2. `python backend/manage.py test apps.compras`
3. Teste manual no navegador (com `Ctrl + Shift + R`):
   - Abrir **+ Lançar Nota de Compra**.
   - Clicar em **REGISTRAR COMPRA** sem preencher nada:
     - Conferir se os campos não preenchidos ganham borda vermelha e foco.
     - Conferir se a notificação lista exatamente quais campos estão pendentes (Fornecedor, Número da Nota, Data).
   - Preencher apenas Fornecedor e clicar em REGISTRAR:
     - Conferir se apenas Número da Nota e Data ficam com borda vermelha e a mensagem cita apenas eles.
   - Preencher o insumo, quantidade e valor na sub-grade sem clicar no botão menor `+ ADICIONAR ITEM`:
     - Clicar em **REGISTRAR COMPRA**: verificar se o sistema inclui o item automaticamente e salva a nota com sucesso.


## 6. Relatório de Execução (Pós-conclusão)
- **Status:** Concluído
- **Data/Hora:** 03/10/2026 23:05
- **Ações Realizadas:**
  - Validação em compras-view.js alterada para identificar campos obrigatórios vazios, aplicando borda ar(--color-error) e focando no primeiro elemento não preenchido.
  - Implementada rotina para auto-clique no botão + ADICIONAR se o usuário houver preenchido insumo e quantidade no sub-grid mas esquecido de adicionar à grid.
  - Testes do módulo pps.compras executados e aprovados.
  - Versionamento PWA em rontend/sw.js e index.html atualizado para 4.45.
