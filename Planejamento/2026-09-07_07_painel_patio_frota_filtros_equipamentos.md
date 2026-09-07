# Registro de Planejamento: Painel Operacional de Frota e Pátio (Filtro por Proprietário e Flag 'No Pátio') - PWA v3.2

- **Identificador:** `Planejamento/2026-09-07_07_painel_patio_frota_filtros_equipamentos.md`
- **Data:** 2026-09-07
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-07T15:42:38-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Objetivos
Aprimorar a aba de Equipamentos & Veículos (`/#cadastros`) transformando-a em um painel operacional completo de gestão de frotas e pátio da oficina.
Substituir a barra anterior desproporcional por um layout balanceado de 4 elementos integrados:
1. Caixa de busca textual expansiva com `flex: 1; min-width: 220px;`.
2. Combobox dinâmica de Proprietários (com `TODOS OS PROPRIETÁRIOS`, `NÃO VINCULADOS` e lista alfabética de clientes).
3. Toggle/checkbox industrial `NO PÁTIO` para filtrar veículos com ordens/orçamentos ativos em execução.
4. Botão `+ NOVO EQUIPAMENTO / MÁQUINA`.
5. Exibição de badge semântico `[NO PÁTIO - ORÇ #12]` na tabela.

---

## 2. Decisões Técnicas e Arquiteturais
- **Backend:**
  - No `EquipamentoViewSet.get_queryset`:
    - Suporte a `cliente_id` numérico ou `'sem_proprietario'` / `'nao_vinculado'` (excluindo registros com vínculos ativos).
    - Suporte a `no_patio=true`, consultando orçamentos ativos (`status_operacional__in=['APROVADO', 'EM_EXECUCAO']` e não deletados) e filtrando `id__in=ids_no_patio`.
  - No `EquipamentoSerializer`: campos computados `em_patio` (booleano) e `orcamento_em_execucao` (`id` e `status_operacional`).
  - Em `apps/cadastros/tests.py`: inclusão de testes unitários automatizados validando ambos os filtros e a serialização de pátio.
- **Frontend:**
  - Barra balanceada com `flex: 1`, combobox de proprietários ordenada alfabeticamente, checkbox `NO PÁTIO` estilizado (*Industrial Integrity*) e botão primário.
  - Carregamento dinâmico via `carregarSelectProprietariosEquip()` e filtragem reativa disparada por eventos `input` e `change`.
  - Badge visual `[NO PÁTIO (#X)]` na coluna de Proprietário da tabela.
- **PWA & Versionamento (Regra Mandatória 12):**
  - Elevação para `CACHE_NAME = 'emc-soldas-v3.2'` em `frontend/sw.js`.
  - Atualização dos scripts e folhas de estilo em `frontend/index.html` para `?v=3.2`.

---

## 3. Arquivos Modificados
- `backend/apps/cadastros/views.py`: aprimoramento de `get_queryset` em `EquipamentoViewSet`.
- `backend/apps/cadastros/serializers.py`: inclusão dos campos `em_patio` e `orcamento_em_execucao`.
- `backend/apps/cadastros/tests.py`: inclusão de `test_filtro_equipamentos_por_proprietario_e_nao_vinculados` e `test_filtro_equipamentos_no_patio_com_orcamento_em_execucao`.
- `frontend/assets/js/views/cadastros-view.js`: nova barra, carregamento de proprietários, filtragem e badges.
- `frontend/sw.js`: versão `emc-soldas-v3.2`.
- `frontend/index.html`: query strings `?v=3.2`.
- `docs/STATUS.md`: documentação viva atualizada.

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes do Módulo `cadastros`:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test apps.cadastros`
   - Resultado: 19 testes executados com 100% de aprovação (`OK`).
2. **Suíte Global do Backend:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test backend/`
   - Resultado: 160 testes executados com 100% de aprovação (`OK`), confirmando regressão zero.
