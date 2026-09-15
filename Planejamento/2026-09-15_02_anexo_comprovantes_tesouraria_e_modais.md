# Implementation Plan: Anexo de Comprovantes no Caixa Real e Modais da Tesouraria

**Data:** 2026-09-15  
**Autor:** Antigravity AI  
**Status:** Concluído  
**Proceed do Usuário:** Aprovado explicitamente via comando "Execute o plano." (15/09/2026).

---

## 1. Contexto e Objetivos

Garantir a padronização e consistência no gerenciamento de comprovantes em todo o módulo de Tesouraria & Caixa Real, complementando a funcionalidade entregue na conciliação bancária:
1. **Listagem do Extrato Real (Caixa):** Tabela exibe botão/badge de anexo `[📎 Ver Anexo]` ou botão `[📎 + Anexo]` para anexar documento diretamente em qualquer movimentação existente.
2. **Modal "Novo Lançamento Avulso":** Campo obrigatório/opcional de upload de comprovante (Nota Fiscal/Recibo).
3. **Modal "Editar / Reclassificar Lançamento":** Exibe comprovante cadastrado e permite anexar/substituir o arquivo.
4. **Modal "Nova Transferência Inter-contas":** Campo para anexo do comprovante da operação de transferência entre contas bancárias.

---

## 2. Decisões Técnicas e Arquiteturais

- **Backend:**
  - `TransferenciaInterContasSerializer`: inclusão de `comprovante_path` e `nome_arquivo_comprovante`.
  - `transferir_inter_contas()`: repasse dos campos para `LancamentoFinanceiro.objects.create`.
- **Frontend:**
  - `financeiro-view.js`: adição de coluna de anexo na tabela do extrato real e inclusão dos campos de upload nos 3 modais.
  - Upload prévio de mídias via `/api/conciliacao/upload-comprovante/`.
- **Versionamento PWA:** `CACHE_NAME` elevado para `'emc-soldas-v4.33'` em `sw.js` e `?v=4.33` em `index.html`.

---

## 3. Arquivos Afetados

- `backend/apps/financeiro/serializers.py`
- `backend/apps/financeiro/services.py`
- `backend/apps/financeiro/views.py`
- `backend/apps/financeiro/tests.py`
- `frontend/assets/js/views/financeiro-view.js`
- `frontend/sw.js`
- `frontend/index.html`

---

## 4. Relatório de Execução Pós-Conclusão

1. **Tabela do Extrato Real:** Adicionada coluna `ANEXO` na listagem do caixa real (`financeiro-view.js`), renderizando badge verde `[📎 NomeArquivo]` para lançamentos com anexo ou botão `[📎 + ANEXO]` para upload instantâneo.
2. **Modais de Lançamento e Edição:** Incluídos campos de upload em `abrirModalNovoLancamento` e `abrirModalEditarLancamento`, efetuando upload prévio e integrando as URIs nos payloads.
3. **Modal de Transferência Inter-Contas:** Atualizados serializer, view e serviço no backend, bem como o modal no frontend (`abrirModalTransferencia`), registrando o comprovante no lançamento do tipo `TRANSFERENCIA`.
4. **Versionamento PWA (Regra 12):** `CACHE_NAME` incrementado para `'emc-soldas-v4.33'` em `sw.js` e `?v=4.33` em `index.html`.
5. **Testes Backend:** 38 testes executados e 100% aprovados (`apps.financeiro` e `apps.conciliacao`).

