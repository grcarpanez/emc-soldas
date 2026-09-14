# Plano de Implementação: Responsividade Mobile da Barra de Ferramentas de Conciliação Bancária

Este plano estabelece as correções de layout e calibração de regras CSS para eliminar o transbordamento (*overflow*) horizontal do botão **CONFIRMAR CONCILIAÇÃO** e equalizar a barra de ferramentas de conciliação bancária (`#/conciliacao`) em telas de smartphones.

---

## 1. Contexto e Diagnóstico

Conforme evidenciado no print enviado pelo usuário (`media_1789418841611.jpg`):
1. **Transbordamento Horizontal:** No modo de visualização mobile (telas `<= 768px`), os botões de ação contextuais:
   - `[⚡ AUTO-MATCH (±3 DIAS)]` (~160px)
   - `[+ LANÇAMENTO RÁPIDO]` (~155px)
   - `[CONFIRMAR CONCILIAÇÃO]` (~185px)
   Estão alinhados dentro de um container com `display: flex; gap: 8px; align-items: center;` **sem `flex-wrap: wrap;`**.
2. **Soma das Larguras:** A largura mínima somada é de ~516px, enquanto a largura disponível na tela do celular é de ~340px a ~390px.
3. **Resultado Visual:** O botão primário `[CONFIRMAR CONCILIAÇÃO]` é empurrado para a direita e extrapolado para fora da borda do card, ficando cortado (`CONFIRMA...`).
4. **Outros Elementos da Barra:** O seletor de conta bancária, os botões de modo (`MODO 1` e `MODO 2`) e o checkbox `ROLAGEM SIMULTÂNEA` também precisam de distribuição fluida e empilhamento vertical limpo para garantir ergonomia de toque e estética impecável (*Industrial Integrity*).

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Estruturação Semântica em Classes no Design System (`industrial-integrity.css`)
Substituir os estilos inline rígidos por classes modulares com media query responsiva para `@media (max-width: 768px)`:
- `.conciliacao-toolbar-content`: container flex com `flex-wrap: wrap; gap: 12px;`.
- `.conciliacao-conta-group`: seletor de conta bancária com `flex: 1; min-width: 0;`.
- `.conciliacao-modos-group`: grupo de botões de alternância de modos ocupando `100%` da largura no mobile, com cada botão assumindo `flex: 1; text-align: center;`.
- `.conciliacao-sync-group`: container de rolagem simultânea centralizado e ajustado.
- `.conciliacao-acoes-group`: container de botões com `display: flex; flex-wrap: wrap; width: 100%; gap: 8px;`.
  - No mobile, os botões secundários `⚡ AUTO-MATCH` e `+ LANÇAMENTO RÁPIDO` dividem a linha superior (`flex: 1 1 calc(50% - 4px);`).
  - O botão primário `CONFIRMAR CONCILIAÇÃO` (e no Modo 2 o `⚡ GERAR E CONCILIAR EM LOTE`) ocupa a linha de baixo com largura total de 100% (`flex: 1 1 100%; width: 100%;`), oferecendo área de clique ampla e visibilidade imediata sem corte.

### 2.2 Versionamento PWA (Regra 12 de AGENTS.md)
- Atualizar `CACHE_NAME = 'emc-soldas-v4.30'` em `frontend/sw.js`.
- Atualizar sufixos de versão `?v=4.30` em `frontend/index.html`.

---

## 3. Arquivos a Modificar

1. `frontend/assets/css/industrial-integrity.css`:
   - Adicionar regras de layout e media query responsiva para a toolbar de conciliação bancária (`.conciliacao-toolbar-*`).
2. `frontend/assets/js/views/conciliacao-view.js`:
   - Atualizar a marcação HTML da toolbar para utilizar as novas classes semânticas.
3. `frontend/sw.js`:
   - Incrementar versão de cache para `v4.30`.
4. `frontend/index.html`:
   - Atualizar sufixo `?v=4.30` em todas as tags de script e estilo.

---

## 4. Plano de Verificação e Testes

1. **Validação de Renderização:**
   - Conferir se os botões quebram ordenadamente em 2 linhas no mobile (linha 1: Auto-Match e Lançamento Rápido; linha 2: Confirmar Conciliação com 100% de largura).
   - Verificar se o seletor de contas e botões de modo se ajustam sem transbordamento em larguras de 360px a 414px.
2. **Homologação da Suíte Automatizada:**
   - Executar `.\venv\Scripts\python.exe backend/manage.py test backend/` para garantir 100% de aprovação dos 185 testes.
---
 
 ## 5. Registro de Execução e Homologação
 
 - **Status:** Concluído com Sucesso
 - **Data de Conclusão:** 2026-09-14
 - **Versão PWA Entregue:** `v4.30` (`CACHE_NAME = 'emc-soldas-v4.30'` e `?v=4.30` no `index.html`)
 - **Suíte de Testes Automatizados:** 185 testes executados com 100% de sucesso (`Ran 185 tests in 76.110s - OK`).
 - **Resultados de UX Mobile:**
   - O grupo de ações contextuais (`#barra-acoes-contextuais`) agora quebra naturalmente em duas linhas em resoluções `<= 768px`:
     - Linha 1: `⚡ AUTO-MATCH (±3 DIAS)` e `+ LANÇAMENTO RÁPIDO` dividem a largura uniformemente (50% cada).
     - Linha 2: `CONFIRMAR CONCILIAÇÃO` (ou `⚡ GERAR E CONCILIAR EM LOTE` no Modo 2) assume 100% de largura, com destaque primário, altura e padding ergonômicos e sem nenhum corte ou transbordamento lateral.
