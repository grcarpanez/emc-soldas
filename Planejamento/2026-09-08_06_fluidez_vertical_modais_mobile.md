# Planejamento: Fluidez Vertical e Eliminação de Scroll Horizontal em Modais Mobile

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Aprovado via interface pelo usuário em 2026-09-08 19:09:25.

---

## 1. Contexto e Diagnóstico do Problema
Conforme evidenciado pelas capturas no smartphone (Chrome Android):
1. **Grids rígidos inline com 2 e 3 colunas:**
   - No modal de Regras de Pagamento (`abrirModalRegraPagamento`), campos como `Nº de Parcelas`, `1ª Parcela (Dias)` e `Intervalo (Dias)` foram definidos com `display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;` inline.
   - Em telas estreitas (360px a 420px de celulares em retrato), três campos com rótulos descritivos não cabem lado a lado. O navegador atinge o `min-width` intrínseco dos inputs e rótulos, forçando o container a ultrapassar a largura do modal e gerando **barra de rolagem horizontal indesejada**.
   - Em modo paisagem, a altura reduzida combinada com larguras fixas também causa corte lateral e rolagem bidirecional.
2. **Ausência de `overflow-x: hidden` no corpo dos modais:**
   - A classe `.modal-body` possui `overflow-y: auto;`, mas não bloqueia o transbordamento horizontal (`overflow-x: hidden;`).
3. **Falta de classes utilitárias responsivas para grids em formulários:**
   - O seletor anterior de colapso exigia a tag `form`, ausente em modais gerados dinamicamente via `openModal`.

---

## 2. Decisões Técnicas e Arquiteturais
1. **Blindagem Global Anti-Scroll Horizontal no Modal (`industrial-integrity.css`):**
   - Configuração de `overflow-x: hidden;` e `box-sizing: border-box;` em `.modal-card` e `.modal-body`.
2. **Classes Utilitárias de Grids Responsivos (`.form-grid-2` e `.form-grid-3`):**
   - Em telas `<= 768px`, colapso compulsório para 1 coluna (`grid-template-columns: 1fr !important;`), tanto para classes explícitas quanto para divs de grid em `.modal-body`.
3. **Reestruturação do Modal de Regras de Pagamento (`administracao-view.js`):**
   - Substituição de grids inline pelas classes `.form-grid-2` e `.form-grid-3`.
   - Quebra vertical limpa e confortável para todos os campos em telas mobile.
4. **Versionamento PWA (Regra Mandatória 12 do AGENTS.md):**
   - Atualização de `CACHE_NAME = 'emc-soldas-v4.1'` em `frontend/sw.js`.
   - Atualização dos sufixos de cache-busting para `?v=4.1` em `frontend/index.html`.

---

## 3. Arquivos Afetados
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/administracao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `Planejamento/2026-09-08_06_fluidez_vertical_modais_mobile.md`

---

## 4. Verificação e Testes
- Testes automatizados do Django: `python backend/manage.py test apps.administracao apps.financeiro`.
- Verificação visual no smartphone (Chrome Android) e emulação DevTools.

---

## 5. Relatório de Execução Pós-Conclusão
- **Blindagem CSS Concluída:** Adicionado `overflow-x: hidden;` e `box-sizing: border-box;` em `.modal-card` e `.modal-body` no `industrial-integrity.css`, eliminando o transbordamento lateral.
- **Grids Responsivos:** Criadas as classes `.form-grid-2` e `.form-grid-3`, e o seletor responsivo de colapso de grids foi expandido para alcançar todos os modais da SPA (`.modal-body div[style*="grid-template-columns"]`, `.modal-body div[style*="display: grid"]`, `.form-grid-2`, `.form-grid-3`).
- **Modal de Regras Reestruturado:** Todos os campos quebram verticalmente no celular, com espaçamento adequado e sem qualquer barra de rolagem horizontal.
- **Versionamento Sincronizado:** Service Worker elevado para `emc-soldas-v4.1` e tags do `index.html` com `?v=4.1`.
- **Testes Automatizados:** 34 testes executados e 100% aprovados sem erros.
