# Plano de Implementação: Conciliação Bancária Visual com Linhas de Match e Importação em Lote

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed:** Aprovado explicitamente pelo usuário em 2026-09-13 12:54:51 ("Vamos fazer. Estou com medo de não ficar bom mas qualquer coisa, o projeto está versionado, é só voltarmos. Execute o plano").

---

## 1. Contexto e Objetivos
Evoluir a tela de Conciliação Bancária Split-Screen (`apps/conciliacao` e `frontend/assets/js/views/conciliacao-view.js`) para suportar:
1. Conexões Visuais de Match (Linhas Bézier SVG nativas e leves ligando o extrato bancário ao ERP);
2. Modo Duplo de Operação (Dual-Mode):
   - Modo 1: Conferência & Match de títulos já existentes no ERP;
   - Modo 2: Importação Total e Geração em Lote a partir do extrato, com grade de pré-lançamentos espelhados, dropdown inline de categorias DRE, exclusão individual de itens indesejados e criação em lote atômica no banco.

---

## 2. Decisões Arquiteturais e Execução Técnica
- **Backend:**
  - Novo endpoint `POST /api/conciliacao/importacao-lote/` protegido por JWT e `HasTesourariaAccess`.
  - Serializers de validação em lote e service com `transaction.atomic()`, atualizando o saldo real da conta e gravando auditoria perpétua (`is_conciliado = True`, data e operador).
  - Testes unitários dedicados em `apps/conciliacao/tests.py` cobrindo sucesso, geração atômica e atualização de saldo.
- **Frontend:**
  - Alternador de modos no topo da tela de Conciliação.
  - Overlay SVG responsivo com cálculo dinâmico de âncoras relativas para desenhar curvas Bézier cúbicas (`M x1 y1 C cx1 y1, cx2 y2, x2 y2`).
  - Cards industriais com 0px border-radius, tipografia técnica e nós conectores em verde e âmbar.
  - Grid de pré-lançamentos no Modo 2 com seleção rápida de categorias contábeis e descarte individual.
  - Versionamento PWA elevado para `v4.19` no `frontend/sw.js` e `frontend/index.html`.

---

## 3. Relatório de Execução e Testes
- **Testes Backend Django:** Suíte de `apps.conciliacao` aprovada com 100% de sucesso (11/11 testes).
- **Design System:** Rigorosamente conforme `docs/DESIGN.md` (0px border-radius, nós industriais, Dark Iron e Industrial Rust).
- **Cache-Busting:** Sincronizado para `v4.19` com instrução obrigatória de recarregamento forçado (`Ctrl + Shift + R`).
