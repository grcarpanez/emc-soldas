# Registro de Planejamento: Correção da Seleção do Tipo de Cadastro na Edição de Clientes/Fornecedores (PWA v3.1)

- **Identificador:** `Planejamento/2026-09-07_06_correcao_combobox_tipo_edicao_cliente.md`
- **Data:** 2026-09-07
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-07T15:17:51-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Diagnóstico
Ao clicar no botão "EDITAR" de um cliente ou fornecedor, o modal de cadastro completo abria a combobox de Tipo sempre com o valor "CLIENTE", mesmo que o parceiro fosse "FORNECEDOR" ou "AMBOS".
A causa raiz foi a comparação case-sensitive estrita (`cliente?.tipo === 'FORNECEDOR'`), enquanto a API devolve o valor em PascalCase (`'Fornecedor'` / `'Ambos'`).
Nenhum option ficava com `selected` e o navegador selecionava o primeiro option por padrão (`CLIENTE`), gerando risco de sobrescrever o tipo no banco de dados.

---

## 2. Decisões Técnicas e Arquiteturais
1. Normalizar o tipo no frontend antes de renderizar o formulário: `const tipoAtual = (cliente?.tipo || 'CLIENTE').toUpperCase()`.
2. Normalizar outros pontos de validação de tipo em `cadastros-view.js` (badges da tabela e filtro de frota) e `orcamentos-view.js` (filtro de clientes).
3. Cumprimento rigoroso da Regra 12 de Versionamento PWA:
   - Elevação de `CACHE_NAME` de `'emc-soldas-v3.0'` para `'emc-soldas-v3.1'` no `frontend/sw.js`.
   - Atualização da query string para `?v=3.1` em todos os scripts e folhas de estilo no `frontend/index.html`.

---

## 3. Arquivos Modificados
- `frontend/assets/js/views/cadastros-view.js`:
  - `abrirModalCadastroCompleto`: `const tipoAtual = (cliente?.tipo || 'CLIENTE').toUpperCase()` e seleção do option com `tipoAtual`.
  - `carregarListaClientes`: `const itemTipoUpper = (item.tipo || '').toUpperCase()` para definição correta de `badgeTipo` e `btnFrota`.
  - `abrirModalEquipamento`: normalização `(c.tipo || '').toUpperCase() !== 'FORNECEDOR'` na filtragem de clientes para frota.
- `frontend/assets/js/views/orcamentos-view.js`:
  - `abrirModalNovoOrcamento`: normalização `(c.tipo || '').toUpperCase() !== 'FORNECEDOR'` na lista de clientes para orçamentos.
- `frontend/sw.js`: incremento de cache para `emc-soldas-v3.1`.
- `frontend/index.html`: query string de cache-busting atualizada para `?v=3.1`.
- `docs/STATUS.md`: atualização da documentação viva.

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes Automatizados:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test apps.cadastros`
   - Resultado: 17 testes executados com 100% de sucesso (`OK`).
2. **Versionamento PWA:**
   - Bundles sincronizados com `v3.1` em `sw.js` e `index.html`.
