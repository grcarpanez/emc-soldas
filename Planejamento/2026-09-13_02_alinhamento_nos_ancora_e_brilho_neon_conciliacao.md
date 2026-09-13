# Plano de Implementação: Alinhamento dos Nós Âncora e Brilho Neon na Conciliação Visual

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed:** Aprovado formalmente pelo usuário no artifact implementation_plan.md em 2026-09-13 13:11:06.

---

## 1. Contexto e Objetivos
O usuário identificou duas oportunidades de refinamento visual de alta relevância:
1. **Ponto de Chegada da Linha no Card:** A linha verde atingia o meio do texto do card da direita ("PRÉ-LANÇAMENTO #1") porque o seletor CSS do nó âncora estava restrito à classe `.split-item`. Devemos fazer com que ela chegue exatamente a um botão/nó idêntico na borda esquerda do card da direita (`left: -5px; top: 50%; transform: translateY(-50%)`), criando uma coerência visual simétrica de nó a nó.
2. **Efeito de Luz Neon na Linha Bézier:** O usuário solicitou uma sombra verde na linha que traga a impressão de luz neon, mantendo nitidez consistente e sem borrar na tela.

---

## 2. Decisões Técnicas e Arquiteturais
- **Nó Âncora Universal:** Desacoplar o seletor `.anchor-node` no CSS e aplicar a classe `.split-item` ao `.pre-lancamento-card`, posicionando o botão verde na borda esquerda (`left: -5px`), com o mesmo formato circular, borda escura e sombra verde (`box-shadow: 0 0 8px rgba(46, 125, 50, 0.9), 0 0 2px #4CAF50`).
- **Efeito Neon Acelerado por GPU (SVG drop-shadow):**
  - Aplicação de `filter: drop-shadow(0 0 3px rgba(76, 175, 80, 0.85)) drop-shadow(0 0 6px rgba(46, 125, 50, 0.45));` na classe `.svg-path-match`.
  - Esse filtro é renderizado nativamente pelo motor gráfico vetorial em tempo real, acompanhando perfeitamente a curva e o scroll sem borrar ou criar artefatos estáticos.
  - No estado hover/destaque, o brilho se expande suavemente.
- **Versionamento PWA:** Elevação de versão para `v4.20` no `frontend/sw.js` e `frontend/index.html` (Regra 12 de governança).

---

## 3. Arquivos Afetados
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/conciliacao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `walkthrough.md`
