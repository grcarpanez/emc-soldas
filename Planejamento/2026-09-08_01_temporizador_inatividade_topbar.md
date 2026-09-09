# Planejamento: Temporizador de Inatividade na Topbar (Soft Lock Countdown)

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Aprovado via interface pelo usuário em 2026-09-08 14:01:45.

---

## 1. Contexto e Objetivos
Adicionar um temporizador visual de contagem regressiva em tempo real na Topbar da aplicação (ao lado do chip `ONLINE`), exibindo o tempo exato restante até o acionamento do Soft Lock, com alerta visual de atenção fixo nos últimos 30 segundos.

---

## 2. Decisões Técnicas e Arquiteturais
- Elemento HTML `<span class="status-chip secondary mono-text" id="session-timer-chip">⏱ --:--</span>` na topbar de `frontend/index.html`.
- Método `atualizarIndicadorTemporizador()` no `AuthManager` (`frontend/assets/js/auth.js`), sincronizado com o heartbeat contínuo a cada 1 segundo.
- Alerta visual: quando o tempo restante for `<= 30 segundos`, o elemento recebe a classe `status-chip warning` (Rust Orange / Amarelo Industrial). Quando superior a 30 segundos, mantém `status-chip secondary`.
- Ocultação automática quando a sessão estiver desautenticada ou enquanto o modal de PIN (Soft Lock) estiver ativo.
- Incremento de versão para `emc-soldas-v3.6` no Service Worker (`frontend/sw.js`) e cache-busting em `frontend/index.html` com `?v=3.6`.

---

## 3. Arquivos a Modificar
- `frontend/index.html`
- `frontend/assets/js/auth.js`
- `frontend/sw.js`

---

## 4. Verificação e Testes
- Bateria de testes automatizados do Django (`apps.authentication` e `apps.administracao`).
- Teste visual da contagem segundo a segundo na barra superior.
- Teste da transição para cor de alerta aos 30 segundos.
- Teste do reinício imediato ao interagir com o sistema.

---

## 5. Relatório de Execução
- **Implementação:** Concluída com sucesso em `frontend/index.html`, `frontend/assets/js/auth.js` e `frontend/sw.js`.
- **Versionamento PWA:** Atualizado para `CACHE_NAME = 'emc-soldas-v3.6'` e query strings `?v=3.6`.
- **Testes Automatizados:** 36 testes executados via `python backend/manage.py test apps.authentication apps.administracao` com 100% de aprovação (0 falhas).
