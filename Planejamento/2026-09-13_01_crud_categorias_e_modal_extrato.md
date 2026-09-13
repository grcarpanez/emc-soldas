# Planejamento: Gestão de Categorias (CRUD) na Administração, Governança de Alteração/Exclusão, Filtro Dinâmico e Edição/Pesquisa no Extrato Real

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed do Usuário:** Aprovado em 13/09/2026 11:33:58 (Aprovação formal do documento implementation_plan.md).

---

## 1. Contexto e Objetivos

1. **Problema Reportado:** Ao tentar registrar um lançamento avulso no módulo **EXTRATO REAL (CAIXA)**, o sistema retornava o erro: `[ERRO] CATEGORIA: Este campo é obrigatório.` mesmo com a categoria preenchida.
2. **Causa Raiz:** O frontend enviava `{ categoria_id, conta_id, meio_pagamento_id }` enquanto o `LancamentoFinanceiroSerializer` do DRF esperava `categoria`, `conta` e `meio_pagamento`, descartando os IDs com sufixo `_id`. Além disso, no regime de caixa (Extrato Real), a movimentação deve ser salva como `PAGO` com conta obrigatória e débito/crédito imediato do saldo bancário.
3. **Necessidades Adicionais:**
   - Criar uma aba completa de CRUD de Categorias na Administração.
   - Adicionar indicação de `AMBOS` estritamente cadastral (a categoria pode ser utilizada tanto para receitas quanto para despesas).
   - Implementar filtro dinâmico no modal de lançamento (se `SAIDA`, exibe despesas e ambos; se `ENTRADA`, exibe receitas e ambos).
   - Estabelecer Matriz de Governança rígida contra exclusão/inversão de categorias que já possuem lançamentos vinculados.
   - Adicionar campo `ativo` em `CategoriaFinanceira` para descontinuação operacional sem afetar histórico.
   - Habilitar pesquisa por categoria no extrato, exibir coluna de categoria na tabela e permitir reclassificação de lançamentos para viabilizar migração/exclusão de categorias.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Modelo `CategoriaFinanceira`:**
   - `TIPO_CHOICES`: `RECEITA`, `DESPESA`, `AMBOS`, `TRANSFERENCIA`.
   - Novo campo `ativo = models.BooleanField(default=True, verbose_name="Categoria Ativa")`.
   - Migration Django `0003_alter_categoriafinanceira_tipo_and_more.py`.
2. **Serializers:**
   - `CategoriaFinanceiraSerializer`: suporte ao campo `ativo`, validação rígida de alteração de tipo impedindo inversão de categorias com lançamentos.
   - `LancamentoFinanceiroSerializer`: mapeamento transparente em `to_internal_value` de `categoria_id` -> `categoria`, `conta_id` -> `conta`, `meio_pagamento_id` -> `meio_pagamento`, `cartao_credito_id` -> `cartao_credito`.
3. **ViewSets:**
   - `CategoriaFinanceiraViewSet`: suporte a filtro por `ativo` e por `aplicacao` / `tipo_lancamento` (`SAIDA` -> `['DESPESA', 'AMBOS']`; `ENTRADA` -> `['RECEITA', 'AMBOS']`).
   - `LancamentoFinanceiroViewSet`: `search_fields = ['=id', 'descricao', 'categoria__nome', 'conta__nome', 'motivo_cancelamento']`.
4. **Frontend:**
   - `administracao-view.js`: nova aba `CATEGORIAS FINANCEIRAS (DRE)` com listagem, busca, filtro de tipo, hierarquia, status ativo/inativo, modais de cadastro e edição com alerta de auditoria, e exclusão com validação.
   - `financeiro-view.js`:
     - Coluna de Categoria na tabela do Extrato Real.
     - Ajuste do placeholder de busca para incluir "CATEGORIA".
     - Filtro dinâmico de categorias no modal de lançamento de acordo com o tipo (`SAIDA` vs `ENTRADA`).
     - Detecção de modo Extrato Real (`status_pagamento='PAGO'`, conta obrigatória, atualização imediata).
     - Modal de edição/reclassificação de lançamentos.
5. **PWA e Cache:**
   - Incremento de versão em `sw.js` para `emc-soldas-v4.16`.
   - Atualização de query strings em `index.html` para `?v=4.16`.

---

## 3. Arquivos Modificados / Criados

- `backend/apps/financeiro/models.py` [MODIFY]
- `backend/apps/financeiro/migrations/0003_alter_cartaocredito_managers_and_more.py` [NEW]
- `backend/apps/financeiro/serializers.py` [MODIFY]
- `backend/apps/financeiro/views.py` [MODIFY]
- `backend/apps/financeiro/tests.py` [MODIFY]
- `backend/core/permissions.py` [MODIFY]
- `frontend/assets/js/views/administracao-view.js` [MODIFY]
- `frontend/assets/js/views/financeiro-view.js` [MODIFY]
- `frontend/sw.js` [MODIFY]
- `frontend/index.html` [MODIFY]
- `docs/STATUS.md` [MODIFY]

---

## 4. Plano de Verificação e Testes

- Execução da suíte de testes Django: `.\venv\Scripts\python backend/manage.py test backend/`.
- Verificação funcional dos fluxos manuais descritos no plano.

---

## 5. Relatório de Execução e Evidências

1. **Model & Migrations:** Campo `ativo` adicionado e `TIPO_CHOICES` ampliado com `AMBOS` em `CategoriaFinanceira`. Migration `0003_alter_cartaocredito_managers_and_more.py` gerada e aplicada com sucesso.
2. **Serializers & Governança Contábil:**
   - Implementado `to_internal_value` universal em `LancamentoFinanceiroSerializer` para aceitar `_id` (`categoria_id`, `conta_id`, etc.).
   - Implementada validação impedindo inversão direta de `RECEITA` para `DESPESA` ou restrição de `AMBOS` quando a categoria já possui lançamentos históricos vinculados.
3. **ViewSets e Permissões:**
   - Permissão `HasCadastrosFinanceirosOuLeituraTesouraria` adicionada em `core/permissions.py` permitindo leitura GET para operadores de tesouraria.
   - Filtros de `aplicacao` e `ativo` configurados em `CategoriaFinanceiraViewSet`.
   - `search_fields` atualizado em `LancamentoFinanceiroViewSet` para contemplar `categoria__nome`.
   - Bloqueio de exclusão em `perform_destroy` com mensagem de erro explicativa caso existam lançamentos vinculados.
4. **Interface Frontend (PWA):**
   - Nova aba de "CATEGORIAS FINANCEIRAS (DRE)" na Administração (`administracao-view.js`) com busca, filtro por tipo, tabela hierárquica, modal de criação/edição e exclusão assistida.
   - Modal de lançamento avulso no Extrato Real (`financeiro-view.js`) reativo: filtro dinâmico ao alternar entre Entrada/Saída, gravação imediata como `PAGO` e atualização do saldo em conta.
   - Tabela do Extrato Real com coluna de categoria dedicada, busca textual por categoria e botão "EDITAR" para reclassificação de lançamentos.
5. **Validação de Testes Automatizados:**
   - Criada classe `CategoriasGovernancaETesourariaTestCase` com 7 testes unitários.
   - Suíte de 175 testes do projeto executada: 100% de aprovação (`Ran 175 tests in 65.420s. OK`).
6. **Versionamento e Cache:**
   - Cache do Service Worker incrementado para `emc-soldas-v4.16`.
   - Cache-busting em `index.html` atualizado para `?v=4.16`.
