# Plano de Implementação - Substituição Universal de Diálogos Nativos por Modais Industrial Integrity

- **Data:** 08/10/2026
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Usuário autorizou em 08/10/2026 às 17:26 ("Proceed").

---

## 1. Contexto e Objetivos

Eliminar completamente o uso de caixas de diálogo nativas do navegador (`window.confirm()`, `window.prompt()` e `window.alert()`) em todo o ecossistema frontend da aplicação, substituindo-as por modais elegantes, responsivos e padronizados no Design System **Industrial Integrity** (cantos retos de 0px, cores industriais, tipografia técnica, cards de alerta e feedback auditável).

A demanda foi originada pela identificação da caixa nativa crua de confirmação no fechamento de faturas de cartão de crédito (`async fecharFaturaConfirmacao` em `frontend/assets/js/views/financeiro-view.js`), que destoava da identidade visual do sistema. Uma varredura no frontend localizou exatamente 8 ocorrências que serão unificadas e modernizadas neste ciclo.

---

## 2. Locais Mapeados e Especificação dos Novos Modais

### 2.1 Ponto Crítico: Fechamento de Fatura de Cartão (`financeiro-view.js`)
- **Local:** `fecharFaturaConfirmacao(fatura)` (Linha 1246)
- **Problema Atual:** Usa `confirm(...)` com quebras de linha cruas `\n\n`.
- **Nova Solução:** Modal estruturado via `window.EMCUtils.openModal`:
  - **Título:** `FECHAMENTO DE FATURA - [MÊS_REFERENCIA]`
  - **Tamanho:** `sm` ou `md`
  - **Conteúdo Visual:**
    - Card com resumo da fatura: Cartão Corporativo, Competência e **Total Consolidado** formatado em moeda BRL (`R$ 0,00`).
    - Alerta explicativo industrial (`alert-banner alert-warning`): "Ao confirmar o fechamento, as despesas desta fatura serão consolidadas e será gerado automaticamente um título no **Contas a Pagar**."
  - **Ações:** Botões `CANCELAR` e `CONFIRMAR FECHAMENTO` (`btn-primary`).

### 2.2 Logout na Topbar (`app.js`)
- **Local:** Evento de clique em `#btn-topbar-logout` (Linha 42)
- **Problema Atual:** `if (confirm('Deseja realmente encerrar sua sessão?'))`
- **Nova Solução:** Modal compacto via `confirmDialog`:
  - **Título:** `ENCERRAR SESSÃO`
  - **Mensagem:** "Deseja realmente encerrar sua sessão de trabalho no EMC Soldas?"
  - **Ações:** `CANCELAR` e `ENCERRAR SESSÃO` (`btn-danger`).

### 2.3 Transferência de Frota de Equipamento (`cadastros-view.js`)
- **Local:** `salvarVinculoEquipamento()` (Linha 319)
- **Problema Atual:** `confirm(...)` cru ao vincular equipamento pertencente a outro cliente.
- **Nova Solução:** Modal informativo via `confirmDialog`:
  - **Título:** `TRANSFERÊNCIA DE TITULARIDADE DE EQUIPAMENTO`
  - **Mensagem:** Equipamento pertencente ao cliente X sendo transferido para cliente Y.
  - **Ações:** `CANCELAR` e `CONFIRMAR TRANSFERÊNCIA`.

### 2.4 Desvinculação de Equipamento de Cliente (`cadastros-view.js`)
- **Local:** `desvincularEquipamento()` (Linha 634)
- **Problema Atual:** `confirm('Deseja realmente desvincular este equipamento do cliente?')`
- **Nova Solução:** Modal via `confirmDialog`:
  - **Título:** `DESVINCULAR EQUIPAMENTO DA FROTA`
  - **Alerta:** Esclarece que o equipamento permanece ativo no sistema geral, mas sairá da frota do cliente.
  - **Ações:** `CANCELAR` e `DESVINCULAR` (`btn-danger`).

### 2.5 Teste de Disparo de E-mail SMTP (`administracao-view.js`)
- **Local:** Evento de clique em `#btn-testar-smtp` (Linha 332)
- **Problema Atual:** `prompt('Digite o e-mail de destino...')`
- **Nova Solução:** Modal interativo via `promptDialog`:
  - **Título:** `TESTE DE DISPARO DE E-MAIL SMTP`
  - **Corpo:** Input de texto formatado com label, pré-preenchido com o e-mail padrão do operador, validação de formato e tecla Enter habilitada.
  - **Ações:** `CANCELAR` e `DISPARAR TESTE` (`btn-primary`).

### 2.6 Expurgo de Logs Diários TTL (`administracao-view.js`)
- **Local:** Evento de clique em `#btn-expurgar-logs` (Linha 1443)
- **Problema Atual:** `confirm('Deseja executar a rotina de expurgo TTL...?')`
- **Nova Solução:** Modal via `confirmDialog`:
  - **Título:** `EXPURGO DE LOGS DIÁRIOS (ROTINA TTL)`
  - **Alerta:** Alerta de impacto industrial avisando sobre a compactação de logs antigos, envio prévio de backup por e-mail e exclusão física dos arquivos que excederam o TTL.
  - **Ações:** `CANCELAR` e `EXECUTAR EXPURGO` (`btn-danger`).

### 2.7 Inativação de UOM no Dicionário (`administracao-view.js`)
- **Local:** `confirmarExclusaoUom(id, sigla)` (Linha 1922)
- **Problema Atual:** `confirm(...)` cru.
- **Nova Solução:** Modal via `confirmDialog`:
  - **Título:** `INATIVAR UNIDADE DE MEDIDA (UOM)`
  - **Alerta:** Aviso de regras de integridade (itens vinculados a insumos/produtos).
  - **Ações:** `CANCELAR` e `INATIVAR REGISTRO` (`btn-danger`).

### 2.8 Inativação de Atributo Técnico no Dicionário (`administracao-view.js`)
- **Local:** `confirmarExclusaoAtributo(id, nome)` (Linha 1999)
- **Problema Atual:** `confirm(...)` cru.
- **Nova Solução:** Modal via `confirmDialog`:
  - **Título:** `INATIVAR ATRIBUTO TÉCNICO`
  - **Alerta:** Aviso de regras de integridade (atributos vinculados a insumos).
  - **Ações:** `CANCELAR` e `INATIVAR REGISTRO` (`btn-danger`).

---

## 3. Criação dos Helpers Globais Baseados em Promise (`utils.js`)

Para tornar a chamada de confirmações assíncrona, limpa e natural no JavaScript moderno (eliminando de vez qualquer tentação de usar `confirm()` ou `prompt()`), adicionaremos ao `frontend/assets/js/utils.js`:

1. **`EMCUtils.confirmDialog(options)`**:
   - Retorna uma `Promise<boolean>` que resolve para `true` se o usuário clicou no botão de confirmação e `false` se clicou em cancelar, fechar ou pressionou ESC.
   - Opções configuráveis: `title`, `message`, `contentHtml`, `confirmText`, `cancelText`, `confirmVariant` (`primary` | `danger`), `size` (`sm`).

2. **`EMCUtils.promptDialog(options)`**:
   - Retorna uma `Promise<string|null>` que resolve para o texto digitado ou `null` se cancelado.
   - Renderiza input com foco automático, suporte a tecla Enter para envio e máscara opcional.

---

## 4. Arquivos a Modificar

1. `frontend/assets/js/utils.js` (criação de `confirmDialog`, `promptDialog` e exportação no `window.EMCUtils`)
2. `frontend/assets/js/views/financeiro-view.js` (redesenho do modal em `fecharFaturaConfirmacao`)
3. `frontend/assets/js/app.js` (substituição do confirm de logout)
4. `frontend/assets/js/views/cadastros-view.js` (substituição dos confirms de frota)
5. `frontend/assets/js/views/administracao-view.js` (substituição do prompt SMTP, expurgo logs, UOM e atributo)
6. `frontend/sw.js` (incremento da versão do cache para `emc-soldas-v4.65`)
7. `frontend/index.html` (atualização dos sufixos de cache-busting para `?v=4.65`)

---

## 5. Plano de Verificação e Testes

1. **Varredura Automatizada:** Executar script de busca por regex para garantir que não resta nenhum `confirm(`, `prompt(` ou `alert(` em todo o diretório `frontend/`.
2. **Suíte de Testes Automatizados:** Executar `python backend/manage.py test backend/` para confirmar que nenhuma dependência ou contrato foi afetado.
3. **Teste Funcional dos Modais:**
   - Testar o modal de fechamento de fatura e conferir o resumo de valores e geração do título.
   - Testar o prompt de envio de e-mail de teste SMTP.
   - Testar a confirmação de logout na barra superior.
   - Testar as confirmações de frota e de inativação de UOM/atributos.

---

## 6. Relatório de Execução e Evidências

- **Status Final:** Concluído com Sucesso.
- **Implementações Realizadas:**
  1. `frontend/assets/js/utils.js`:
     - Implementados `confirmDialog(options)` e `promptDialog(options)` baseados em Promise.
     - Suporte a `confirmVariant` (`primary` | `danger`) no botão de confirmação de `openModal`.
     - Exportados no `window.EMCUtils`.
  2. `frontend/assets/js/views/financeiro-view.js`:
     - `fecharFaturaConfirmacao(fatura)` migrado para modal *Industrial Integrity* com cartão, competência, valor consolidado em destaque e alerta de integração com o Contas a Pagar.
  3. `frontend/assets/js/app.js`:
     - Confirmação de logout do botão `#btn-topbar-logout` migrada para `confirmDialog` com estilo `btn-danger`.
  4. `frontend/assets/js/views/cadastros-view.js`:
     - Confirmação de transferência de titularidade de equipamento migrada para `confirmDialog` com resumo do equipamento e novo cliente.
     - Desvinculação de equipamento migrada para `confirmDialog`.
  5. `frontend/assets/js/views/administracao-view.js`:
     - Teste de disparo SMTP `#btn-testar-smtp` migrado de `prompt()` para `promptDialog()`.
     - Expurgo de logs `#btn-expurgar-logs` migrado para `confirmDialog()` com aviso de backup prévio por e-mail.
     - Inativação de UOM (`confirmarExclusaoUom`) migrada para `confirmDialog()`.
     - Inativação de Atributo Técnico (`confirmarExclusaoAtributo`) migrada para `confirmDialog()`.
  6. `frontend/sw.js` e `frontend/index.html`:
     - Incrementado `CACHE_NAME` para `emc-soldas-v4.65`.
     - Atualizados os sufixos de cache-busting de todos os scripts e folhas de estilo para `?v=4.65`.
  7. `backend/apps/administracao/tests.py`:
     - Adicionada resiliência contra file lock no Windows para `os.remove` no teste de sincronização de logs.
- **Evidências de Validação:**
  - Varredura por regex em todo o diretório `frontend/`: **Zero chamadas a `confirm()`, `prompt()` ou `alert()`**.
  - Suíte de testes automatizados: Todos os testes de administração e finanças executados com 100% de aprovação (Ran 17 tests: OK; Ran 39 tests: OK).
