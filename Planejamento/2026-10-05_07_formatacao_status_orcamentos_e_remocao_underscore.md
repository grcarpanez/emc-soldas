# Plano de Implementação: Formatação de Status em Orçamentos e Eliminação de Underscore (_)

- **Data:** 05/10/2026
- **Autor:** Antigravity (Pair Programming AI) & Gustavo
- **Status:** Concluído
- **Registro do Proceed:** Aprovado em 05/10/2026 15:13 via instrução "Proceed"
- **Referência:** Imagem `media_1791223627914.png` e solicitação: *"Precisamos ajustar aqui o status e tratar o _"*

---

## 1. Contexto e Diagnóstico

### 1.1 Sintomas Observados
1. **Exibição de Underscore (`_`) no Status:**
   - Na tabela de **Orçamentos Comerciais**, a coluna **STATUS FINANCEIRO** exibe a tag/badge com o valor cru do banco de dados contendo *underscore*: `A_FATURAR`, em vez da grafia legível `A FATURAR`.
   - Se o status operacional for `EM_EXECUCAO`, ele também é renderizado como `EM_EXECUCAO` em vez de `EM EXECUÇÃO` (ou `EM EXECUCAO`).
   - No modal de **Detalhes do Orçamento** (`verDetalhes`), as linhas de status operacional e financeiro também interpolam diretamente `${orc.status_operacional}` e `${orc.status_financeiro}` sem higienização.
2. **Filtro Operacional Pré-Travado em `GERADO`:**
   - Na barra de filtros, a combobox de status operacional inicializa travada no valor `GERADO`. Isso ocorre porque o elemento `<select id="filtro-orc-status">` não possui a opção neutra `<option value="">TODOS OS STATUS</option>`. Como resultado, o navegador seleciona a primeira opção (`GERADO`) e o utilitário `initMultiSelectCombobox` a marca como selecionada, filtrando exclusivamente orçamentos em status `GERADO` na carga inicial da tela.
3. **Corte Visual do Filtro Financeiro (`FINANCEIRO: TOD▼`):**
   - O `<select id="filtro-orc-status-fin">` possui largura definida em `width: 175px; min-width: 165px;`. Devido ao padding interno e à seta do dropdown do design system, o texto `"FINANCEIRO: TODOS"` é truncado visualmente para `"FINANCEIRO: TOD▼"`.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend: Exposição dos Campos Display nos Serializers de Orçamento
No Django ORM, o modelo `Orcamento` define:
- `STATUS_OPERACIONAL_CHOICES` com rótulos amigáveis (`'EM_EXECUCAO': 'EM EXECUÇÃO'`, `'CONCLUIDO': 'CONCLUÍDO'`).
- `STATUS_FINANCEIRO_CHOICES` com rótulos amigáveis (`'A_FATURAR': 'A FATURAR'`).

Em `backend/apps/orcamentos/serializers.py`:
1. Adicionar no `OrcamentoSerializer`:
   ```python
   status_operacional_display = serializers.CharField(source='get_status_operacional_display', read_only=True)
   status_financeiro_display = serializers.CharField(source='get_status_financeiro_display', read_only=True)
   ```
2. Adicionar ambos os campos à lista `fields` de `OrcamentoSerializer`.
3. Por herança, `OrcamentoDetailSerializer` também herdará e disponibilizará esses campos no endpoint de detalhes (`/api/orcamentos/{id}/`).

### 2.2 Frontend: Higienização Universal contra Underscore e Formatação de Status
Em `frontend/assets/js/views/orcamentos-view.js`:
1. **Na Tabela de Listagem de Orçamentos (linhas 125-140):**
   - Obter os textos formatados com prioridade para a representação do backend e fallback seguro pelo utilitário `formatarStatus`:
     ```javascript
     const statusOpTexto = orc.status_operacional_display || window.EMCUtils.formatarStatus(orc.status_operacional);
     const statusFinTexto = orc.status_financeiro_display || window.EMCUtils.formatarStatus(orc.status_financeiro);
     ```
   - Renderizar no DOM:
     ```html
     <td><span class="status-chip ${badgeOp}">${window.EMCUtils.escapeHtml(statusOpTexto)}</span></td>
     <td><span class="status-chip ${badgeFin}">${window.EMCUtils.escapeHtml(statusFinTexto)}</span></td>
     ```
2. **No Modal de Detalhes (`verDetalhes`, linhas 830-835):**
   - Obter `statusOpTextoModal` e `statusFinTextoModal` da mesma forma e aplicar as classes dinâmicas `badgeOp` e `badgeFin` em vez de chips estáticos.
3. **Na Tela de Faturamento (`faturamento-view.js` linhas 253 e 315):**
   - Aplicar `window.EMCUtils.formatarStatus(orc.status_operacional)` na listagem de orçamentos para conta corrente.

### 2.3 Frontend: Ajuste da Barra de Filtros de Orçamentos
Em `frontend/assets/js/views/orcamentos-view.js`:
1. **Filtro de Status Operacional:**
   - Inserir a opção neutra vazia no início do select:
     ```html
     <select id="filtro-orc-status" class="form-control">
       <option value="">TODOS OS STATUS OPERACIONAIS</option>
       <option value="GERADO">GERADO</option>
       <option value="ENVIADO">ENVIADO</option>
       ...
     </select>
     ```
   - No `initMultiSelectCombobox`, definir `placeholder: 'OPERACIONAL: TODOS'` e `prefix: 'OPERACIONAL'`.
   - Isso garante que a carga inicial da tela exiba todos os orçamentos (sem pré-filtrar exclusivamente por `GERADO`).
2. **Filtro de Status Financeiro:**
   - Expandir a largura do container para `width: 220px; min-width: 195px;`, garantindo que o texto `"FINANCEIRO: TODOS"` não sofra corte ou ellipsis com a seta.

### 2.4 Versionamento de Cache PWA e Governança
- Incrementar `CACHE_NAME` no `frontend/sw.js` para `'emc-soldas-v4.56'`.
- Atualizar as query strings em `frontend/index.html` para `?v=4.56`.

---

## 3. Arquivos Afetados

| Arquivo | Natureza da Modificação |
| :--- | :--- |
| `backend/apps/orcamentos/serializers.py` | Adicionar `status_operacional_display` e `status_financeiro_display` |
| `backend/apps/orcamentos/tests.py` | Adicionar asserção dos campos `_display` na listagem da API |
| `frontend/assets/js/views/orcamentos-view.js` | Formatar status na tabela e no modal, ajustar opção neutra no operacional e expandir largura do financeiro |
| `frontend/assets/js/views/faturamento-view.js` | Formatar status operacional na listagem de orçamentos da conta corrente |
| `frontend/sw.js` | Incrementar versão do cache para `v4.56` |
| `frontend/index.html` | Atualizar sufixos para `?v=4.56` |
| `docs/STATUS.md` | Atualizar checklist e versão viva do sistema |

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados:**
   - Executar `python manage.py test apps.orcamentos` garantindo 100% de sucesso.
   - Executar a suíte de testes globais `python manage.py test`.
2. **Validação Manual de Interface:**
   - Recarregar com `Ctrl + Shift + R`.
   - Acessar a tela **Orçamentos Comerciais**.
   - Conferir se a barra de filtros inicializa com `OPERACIONAL: TODOS` e `FINANCEIRO: TODOS` (sem corte de texto).
   - Conferir se a tag do Orçamento #1 exibe `A FATURAR` (sem `_`).
   - Abrir o modal de detalhes e conferir se os status aparecem formatados sem `_`.

---

## 5. Governança e Commit Semântico

Após a validação, executar commit atômico:
- **Mensagem:** `fix(orcamentos): formatar exibicao de status e ajustar filtros`

---

## 6. Relatório de Execução e Evidências

1. **Backend (`backend/apps/orcamentos/serializers.py`):**
   - Adicionados os campos `status_operacional_display` e `status_financeiro_display` utilizando `get_status_operacional_display` e `get_status_financeiro_display` do modelo Django ORM.
   - Ambos os campos adicionados aos `fields` de `OrcamentoSerializer` e herdados por `OrcamentoDetailSerializer`.
2. **Frontend (`frontend/assets/js/views/orcamentos-view.js`):**
   - Na tabela de orçamentos, o status operacional e financeiro são exibidos com prioridade nos campos `_display` e fallback universal para `window.EMCUtils.formatarStatus()`, eliminando o underscore (`A FATURAR` em vez de `A_FATURAR`, `EM EXECUÇÃO` em vez de `EM_EXECUCAO`).
   - No modal de detalhes (`verDetalhes`), formatados os chips de status operacional e financeiro sem underscore e com classes de badge dinâmicas (`badgeOpModal`, `badgeFinModal`).
   - Na barra de filtros, inserida a opção neutra `<option value="">TODOS OS STATUS OPERACIONAIS</option>` e definido o placeholder `OPERACIONAL: TODOS`, impedindo o travamento inicial em `GERADO`.
   - Ampliada a largura do select de status financeiro para `width: 215px; min-width: 195px;`, eliminando o corte de texto (`FINANCEIRO: TODOS`).
3. **Frontend (`frontend/assets/js/views/faturamento-view.js`):**
   - Aplicado `window.EMCUtils.formatarStatus(orc.status_operacional)` na listagem de orçamentos da conta corrente e detalhes da fatura.
4. **Testes Automatizados:**
   - Adicionadas asserções em `backend/apps/orcamentos/tests.py` validando os campos `status_operacional_display` e `status_financeiro_display`.
   - Execução de `apps.orcamentos` e `apps.faturamento`: 24 testes executados com 100% de sucesso.
5. **Versionamento PWA:**
   - `CACHE_NAME` atualizado para `emc-soldas-v4.56` em `frontend/sw.js` e sufixos atualizados para `?v=4.56` em `frontend/index.html`.

