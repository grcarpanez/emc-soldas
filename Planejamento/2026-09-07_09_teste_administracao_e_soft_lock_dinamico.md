# Planejamento: Testes da Central do Administrador, Soft Lock por Uso Efetivo do Sistema & Máscaras Iniciais

## Metadados
- **Data:** 2026-09-07
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Aprovado via interface pelo usuário em 2026-09-07 16:26:21.

---

## 1. Diretriz do Usuário & Contexto
O Soft Lock é a proteção exclusiva do sistema EMC Soldas, vinculado à utilização efetiva da aplicação web e não do computador ou sistema operacional.
- O que reseta o timer: Requisições de API (`window.api.request`), cliques intencionais no DOM (`click`), digitação em campos (`input`/`change`) e submissão de formulários (`submit`).
- O que NÃO reseta: Movimento passivo de mouse (`mousemove`), ruídos de sensores ópticos e atividade em outros softwares do Windows.
- Standby / Segundo Plano: O tempo continua correndo. Ao atingir o tempo configurado (ex: 60s), a tela é travada com o PIN.
- Máscaras Iniciais: Os campos CNPJ e Telefone na Aba de Parâmetros Globais devem abrir 100% mascarados na renderização da tela, sem depender de o usuário começar a digitar.

---

## 2. Decisões Técnicas e Arquiteturais
- **`auth.js`:**
  - `this.lastActivityTimestamp = Date.now()`.
  - Método `registrarAtividadeEfetiva(origem)` que atualiza `this.lastActivityTimestamp = Date.now()`.
  - Heartbeat contínuo (`setInterval` a cada 1.000 ms) verificando `Date.now() - this.lastActivityTimestamp >= this.inactivityTimeoutMs`.
  - Remoção completa do evento `mousemove`.
  - Escutas estritas para `click`, `input`, `change`, `submit`.
  - Verificação imediata no retorno de foco (`visibilitychange` e `window.focus`).
- **`api.js`:**
  - No método `request()`, invocar `window.auth?.registrarAtividadeEfetiva('API Request')`.
- **`utils.js`:**
  - Implementação de `aplicarMascarasEmContainer(container)`.
- **`administracao-view.js`:**
  - Formatação com `formatarCpfCnpjDinamico` e `formatarTelefoneDinamico` no template e chamada de `aplicarMascarasEmContainer(container)`.
- **Cache PWA & Versionamento:**
  - `frontend/sw.js` com estratégia Network-First para scripts e bump para `v3.5`.
  - `frontend/index.html` com tags atualizadas para `?v=3.5`.

---

## 3. Relatório de Execução e Verificação
- Suíte completa de testes automatizados do Django (`apps.authentication` e `apps.administracao`) executada com **36 testes rodados e 100% de aprovação (OK)**.
- O Soft Lock agora opera estritamente com base na atividade no sistema:
  - Movimentos passivos de mouse não resetam o tempo.
  - O sistema bloqueia após o tempo exato (ex: 60 segundos) mesmo se o usuário estiver usando outros aplicativos no Windows.
  - Ao retornar para o sistema, se o tempo tiver expirado, o modal de PIN aparece imediatamente.
  - Os campos CNPJ e Telefone abrem imediatamente mascarados (`00.000.000/0001-00` e `(11) 99999-9999`).
