# Plano de Implementação - Interatividade, Rolagem e Suporte Mobile no Tooltip do Gráfico

**ID da Tarefa:** `2026-10-03_09_fix_tooltip_interatividade_scroll_mobile`  
**Data:** 03/10/2026  
**Status:** `Concluído`  
**Autor:** Antigravity AI  
**Registro do Proceed:** Aprovado pelo usuário em 03/10/2026 às 15:46 ("Proceed")  

---

## 1. Contexto e Objetivos

Garantir que os operadores consigam explorar e rolar a lista completa de categorias financeiras dentro do tooltip das barras do gráfico, tanto em computadores (Desktop com mouse) quanto em dispositivos móveis (Smartphones/Tablets com tela sensível ao toque).

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Ajustes no Design System (`frontend/assets/css/industrial-integrity.css`)
1. **Ativação de Eventos de Ponteiro:**
   - Definir `pointer-events: auto;` em `.chart-tooltip.visible` (mantendo `pointer-events: none` apenas quando oculto/invisível para não obstruir cliques na tela).
2. **Isolamento de Rolagem (Scroll Chaining / Mobile):**
   - Na lista `.chart-tooltip-list`, aplicar:
     - `overscroll-behavior: contain;` (impede que o scroll chegue ao final da lista e comece a rolar a página principal no celular ou no desktop).
     - `-webkit-overflow-scrolling: touch;` (garante aceleração por hardware e rolagem fluida e inercial no iOS/Android).
     - `touch-action: pan-y;` (informa explicitamente ao navegador que gestos verticais pertencem à lista interna).
3. **Botão de Fechamento Industrial (`.chart-tooltip-close`):**
   - Inclusão de um botão sutil `[✕]` no canto superior direito do cabeçalho do tooltip (0px border-radius, `JetBrains Mono`, hover sutil), facilitando o fechamento instantâneo tanto no Desktop quanto no Mobile.

### 2.2 Ponte de Tolerância e Gestão de Eventos (`frontend/assets/js/views/dashboard-view.js`)
1. **Ponte de Tolerância no Desktop (*Hover Grace Period*):**
   - Implementação de um temporizador de saída (`hideTimeout` de 250ms).
   - Quando o mouse sai da barra (`mouseleave` da barra), o tooltip não desaparece instantaneamente; ele aguarda 250ms.
   - Se o cursor entrar no tooltip (`mouseenter` do tooltip), o cancelamento do fechamento é acionado (`clearTimeout(hideTimeout)`), mantendo o tooltip aberto e fixo enquanto o usuário navega e rola a lista com a rodinha do mouse ou arrasta a barra de rolagem.
   - Quando o mouse sai do tooltip (`mouseleave` do tooltip), ele fecha suavemente após 200ms.
   - Caso o mouse retorne à barra ou vá para outra barra, qualquer fechamento pendente é cancelado imediatamente.
2. **Fixação e Rolagem no Mobile:**
   - No celular, o toque na barra abre e fixa o tooltip.
   - Como `pointer-events: auto` e `overscroll-behavior: contain` estarão ativos, o toque e arraste do dedo rolam estritamente a lista de categorias.
   - Adição de `e.stopPropagation()` no toque do tooltip para garantir que o gesto de rolagem não acione o listener de fechar ao clicar fora.
   - O operador pode fechar o tooltip tocando no botão `[✕]` ou tocando em qualquer área externa do gráfico.

### 2.3 Versionamento de Assets PWA
- Elevação mandatória da versão do Service Worker em `frontend/sw.js` para `CACHE_NAME = 'emc-soldas-v4.40'`.
- Atualização dos parâmetros de cache-busting em `frontend/index.html` para `?v=4.40`.

---

## 3. Arquivos Afetados

| Arquivo | Responsabilidade / Modificação |
|---|---|
| `Planejamento/2026-10-03_09_fix_tooltip_interatividade_scroll_mobile.md` | Registro formal do plano de implementação e aprovação (`Proceed`). |
| `frontend/assets/css/industrial-integrity.css` | Adição de `pointer-events: auto`, `overscroll-behavior: contain`, `touch-action: pan-y` e classe `.chart-tooltip-close`. |
| `frontend/assets/js/views/dashboard-view.js` | Implementação do timer de tolerância no Desktop, escuta de eventos no próprio tooltip, botão `[✕]` e controle de propagação no Mobile. |
| `frontend/sw.js` | Incremento da versão do cache para `emc-soldas-v4.40`. |
| `frontend/index.html` | Atualização do cache-busting para `?v=4.40`. |
| `docs/STATUS.md` | Atualização do checklist e histórico de versão. |

---

## 4. Plano de Verificação e Testes

1. **Testes no Desktop (Navegação com Mouse):**
   - Passar o mouse sobre uma barra com muitas categorias.
   - Mover o mouse da barra em direção ao tooltip: verificar que o tooltip permanece aberto e transitável.
   - Rolar a rodinha do mouse sobre a lista: conferir que a barra de rolagem interna se movimenta perfeitamente até a última categoria.
   - Tirar o mouse do tooltip: verificar que ele fecha suavemente após o intervalo de tolerância.
   - Clicar no botão `[✕]`: conferir que fecha imediatamente.
2. **Testes no Mobile / Modo Touch (Simulador e Celular):**
   - Tocar em uma barra para abrir o tooltip.
   - Arrastar o dedo verticalmente sobre a lista de categorias: verificar que a lista interna rola com fluidez sem rolar o restante da página.
   - Tocar no botão `[✕]` ou em qualquer ponto fora do gráfico: verificar que o tooltip fecha de imediato.
3. **Bateria de Testes Automatizados:**
   - Executar `python backend/manage.py test backend/apps/relatorios/` e a suíte completa para assegurar 100% de integridade.
4. **Commit Semântico:**
   - Executar commit formal: `fix(dashboard): permitir scroll e interatividade no tooltip do grafico`.

---

## 5. Relatório de Execução e Homologação

- **Ajustes no CSS Industrial Integrity (`industrial-integrity.css`):**
  - Adicionado `pointer-events: auto;` em `.chart-tooltip.visible`, permitindo interação com mouse e toque.
  - Adicionado `overscroll-behavior: contain;`, `-webkit-overflow-scrolling: touch;` e `touch-action: pan-y;` em `.chart-tooltip-list`, isolando a rolagem interna do tooltip sem propagar para o scroll da janela principal.
  - Implementado botão de fechar `.chart-tooltip-close` com estilo industrial e hover temático.
- **Ajustes de Interatividade no JS (`dashboard-view.js`):**
  - Implementado timer de tolerância no Desktop com `agendarOcultarTooltip(250)` e `cancelarOcultarTooltip()`. Ao mover o cursor da barra para o tooltip, o `mouseenter` no tooltip preserva a exibição fixa e permite rolar a lista confortavelmente.
  - Adicionado `e.stopPropagation()` no toque do tooltip no mobile, garantindo que o arraste do dedo role exclusivamente a lista interna sem disparar o fechador de clique externo.
  - Adicionado botão físico `[✕]` permitindo fechamento explícito tanto no desktop quanto no celular.
- **Versionamento PWA:**
  - `frontend/sw.js` atualizado para `CACHE_NAME = 'emc-soldas-v4.40'`.
  - `frontend/index.html` atualizado com sufixos `?v=4.40`.
- **Suíte de Testes:**
  - 14 testes de `apps.relatorios` validados com 100% de sucesso.

