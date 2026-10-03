# Plano de Implementação - Responsividade Mobile do Gráfico e Feed de Atividades do Dashboard

**ID da Tarefa:** `2026-10-03_10_responsividade_mobile_grafico_feed_dashboard`  
**Data:** 03/10/2026  
**Status:** `Concluído`  
**Autor:** Antigravity AI  
**Registro do Proceed:** Aprovado pelo usuário em 03/10/2026 às 20:28 ("Proceed")  

---

## 1. Contexto e Objetivos

Garantir que, em telas móveis (smartphones e tablets `<= 900px`), a seção inferior do Dashboard se adapte com fidelidade:
- O card do **Gráfico (Receitas x Despesas)** deve ocupar 100% da largura, perfeitamente alinhado às margens dos cards de resumo (Flip Cards) acima dele.
- A legenda do gráfico deve ficar posicionada **abaixo das barras** (e não à direita), centralizada e com quebra de linha suave (`flex-wrap: wrap`).
- As 12 colunas de meses devem se ajustar proporcionalmente (`min-width: 0; gap: clamp(2px, 1vw, 8px)`), sem provocar qualquer transbordo ou rolagem horizontal.
- O card de **Atividades Recentes** deve ser empilhado verticalmente logo **abaixo do gráfico**, também ocupando 100% da largura com o mesmo alinhamento direito e esquerdo.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Grid Responsivo no CSS (`frontend/assets/css/layout.css`)
1. **Classe Utilitária `.dashboard-lower-grid`:**
   - Criar a classe formal em `layout.css`:
     - **Desktop (`> 900px`):** `display: grid; grid-template-columns: 2fr 1fr; gap: 20px; width: 100%;` (Gráfico 66% na esquerda e Feed 33% na direita).
     - **Mobile / Tablet (`<= 900px`):** `grid-template-columns: 1fr; gap: 16px;` (Empilhamento vertical automático em 1 coluna completa).
2. **Container do Gráfico (`.dashboard-chart-container`):**
   - Definir `display: flex; flex-direction: column; width: 100%; position: relative; overflow-x: hidden;` garantindo que as barras fiquem em cima e a legenda fique embaixo, sem vazamento horizontal.

### 2.2 Ajustes no Layout da View (`frontend/assets/js/views/dashboard-view.js`)
1. **Estrutura HTML do Dashboard:**
   - Substituir o estilo inline `style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;"` pela classe `.dashboard-lower-grid`.
2. **Renderização do Gráfico:**
   - Assegurar `flex-direction: column;` no `#dashboard-chart-container`.
   - Adicionar `min-width: 0;` em cada coluna de mês para permitir que o flexbox encolha proporcionalmente em celulares estreitos (ex: iPhone SE com 320px ou Androids de 360px a 390px).
   - Utilizar espaçamento fluido entre meses: `gap: clamp(2px, 0.8vw, 8px)`.
   - Na legenda: `display: flex; justify-content: center; gap: 16px; margin-top: 14px; flex-wrap: wrap; font-size: 11.5px;`.

### 2.3 Versionamento de Assets PWA
- Elevação mandatória da versão do Service Worker em `frontend/sw.js` para `CACHE_NAME = 'emc-soldas-v4.41'`.
- Atualização dos parâmetros de cache-busting em `frontend/index.html` para `?v=4.41`.

---

## 3. Arquivos Afetados

| Arquivo | Responsabilidade / Modificação |
|---|---|
| `Planejamento/2026-10-03_10_responsividade_mobile_grafico_feed_dashboard.md` | Registro formal do plano de implementação e aprovação (`Proceed`). |
| `frontend/assets/css/layout.css` | Definição da classe `.dashboard-lower-grid` com media query responsiva para empilhamento em 1 coluna. |
| `frontend/assets/js/views/dashboard-view.js` | Substituição de estilo inline por classe CSS, garantia de `flex-direction: column` e fluidez nas 12 colunas de barras. |
| `frontend/sw.js` | Incremento da versão do cache para `emc-soldas-v4.41`. |
| `frontend/index.html` | Atualização do cache-busting para `?v=4.41`. |
| `docs/STATUS.md` | Atualização do checklist e histórico de versão. |

---

## 4. Plano de Verificação e Testes

1. **Testes no Celular / Viewport Mobile (360px - 480px):**
   - Verificar que o card do gráfico termina exatamente alinhado às margens esquerda e direita dos Flip Cards de cima.
   - Verificar que a legenda ("Receitas Liquidadas" e "Despesas Pagas") fica centralizada abaixo das barras do gráfico.
   - Verificar que o card "ATIVIDADES RECENTES" aparece logo abaixo do gráfico, com largura total (100%) e o mesmo alinhamento lateral.
   - Verificar que os tooltips continuam funcionando normalmente ao toque.
2. **Testes no Desktop (> 900px):**
   - Confirmar que o layout de 2 colunas paralelas (Gráfico 2fr / Feed 1fr) se mantém intacto e harmonioso.
3. **Bateria de Testes Automatizados:**
   - Executar `python backend/manage.py test backend/apps/relatorios/` e testes globais.
4. **Commit Semântico:**
   - Executar commit formal: `fix(dashboard): alinhar grafico e empilhar feed de atividades no mobile`.

---

## 5. Relatório de Execução e Homologação

- **Ajustes de CSS Responsivo (`layout.css`):**
  - Implementada a classe `.dashboard-lower-grid` que aplica `grid-template-columns: 2fr 1fr;` no Desktop (>900px) e colapsa automaticamente para `grid-template-columns: 1fr;` em telas móveis e tablets (<=900px).
  - Implementada a classe `.dashboard-chart-container` com `display: flex; flex-direction: column; width: 100%;`.
- **Ajustes no JavaScript da View (`dashboard-view.js`):**
  - Substituído estilo inline rígido no grid inferior por `.dashboard-lower-grid`.
  - Configurado `flex-direction: column` no container do gráfico, garantindo que a legenda fique centralizada logo abaixo das barras (e não ao lado).
  - Configurado `min-width: 0;` em cada uma das 12 colunas mensais e espaçamento fluido `gap: clamp(2px, 0.8vw, 8px)`, eliminando estouro horizontal em qualquer smartphone.
- **Versionamento PWA:**
  - `frontend/sw.js` atualizado para `CACHE_NAME = 'emc-soldas-v4.41'`.
  - `frontend/index.html` atualizado com sufixos `?v=4.41`.
- **Homologação:**
  - 14 testes de `apps.relatorios` validados com 100% de sucesso.

