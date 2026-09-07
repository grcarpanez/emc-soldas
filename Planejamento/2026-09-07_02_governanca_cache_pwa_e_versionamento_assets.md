# Plano de Implementação: Governança Perpétua de Cache PWA e Versionamento de Assets (v2.8)

- **Data de Elaboração:** 2026-09-07
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluído
- **Proceed do Usuário:** Aprovado em 2026-09-07 ("Façamos isso, porque se entendi bem, se eu não tivesse levantado essa questão, o registro não teria sido feito.")

---

## 1. Contexto e Objetivos

Durante os testes manuais da nova máscara universal de placas (`###-####`), foi detectado que o navegador do usuário continuava executando a lógica legada (aceitando todas as letras sem hífen e aceitando todos os números com hífen).

### Causa Raiz Técnica
1. O sistema EMC Soldas é uma Progressive Web App (PWA) client-side com Service Worker (`frontend/sw.js`).
2. O Service Worker utilizava a estratégia de cache estático agressivo (`CACHE_NAME = 'emc-soldas-v2.7'`).
3. O arquivo `frontend/index.html` importava os scripts sem sufixo de versionamento por query string (`/assets/js/utils.js`).
4. Por consequência, mesmo após a atualização no servidor, o navegador continuava entregando o arquivo `utils.js` antigo em cache.

### Decisão Arquitetural e de Governança
O usuário levantou um princípio de engenharia essencial: **alterações de peso arquitetural (como a necessidade de sincronizar versionadores de assets e caches em toda modificação de frontend) devem ser obrigatoriamente documentadas em arquivos que toda IA lê antes de qualquer planejamento em qualquer chat**.

---

## 2. Decisões Técnicas Implementadas

1. **Blindagem no `AGENTS.md` (Constituição do Repositório):**
   - Adicionada a Regra Mandatória 12 na Seção 6: "Política Mandatória de Versionamento de Assets Frontend e Cache do Service Worker (PWA)".
   - Atualizado o ciclo de trabalho na Seção 7 (Fase 2 e 3): toda modificação em JS ou CSS obriga a incrementar o `CACHE_NAME` em `sw.js` e os sufixos `?v=X.Y` no `index.html`.
2. **Registro Preventivo no `docs/ERROS.md`:**
   - Documentado o incidente de cache stale, demonstrando a causa raiz e o protocolo de prevenção com versionamento simétrico.
3. **Execução Técnica da Versão v2.8:**
   - `frontend/sw.js`: Constante `CACHE_NAME` atualizada para `'emc-soldas-v2.8'`, garantindo purga de caches antigos no evento `activate`.
   - `frontend/index.html`: Todas as tags `<script>` e `<link rel="stylesheet">` atualizadas com `?v=2.8`.
4. **Atualização nos Arquivos Vivos:**
   - `docs/STATUS.md` atualizado na Fase 14.5 com a nova convenção de versionamento de assets.

---

## 3. Arquivos Modificados

- `AGENTS.md` (Regra 12 de versionamento PWA e ciclo de trabalho)
- `docs/ERROS.md` (Registro do erro e prevenção de cache PWA stale)
- `docs/STATUS.md` (Registro de progresso na Fase 14.5)
- `frontend/sw.js` (Incremento de `CACHE_NAME` para `'emc-soldas-v2.8'`)
- `frontend/index.html` (Sufixo `?v=2.8` em todos os scripts e CSS)
- `Planejamento/2026-09-07_02_governanca_cache_pwa_e_versionamento_assets.md` (Este documento)

---

## 4. Verificação e Testes

- [x] Testes unitários do Django executados: 157 testes aprovados com 100% de sucesso (`OK`).
- [x] Testes específicos do app `cadastros`: 16 testes aprovados com 100% de sucesso (`OK`).
- [x] Simulação em Node.js da função `formatarPlacaVeiculo`:
  - `1234` -> rejeitado (retorna vazio)
  - `ABC1234` -> `ABC-1234` (hífen automático)
  - `ABC1D23` -> `ABC-1D23` (hífen automático)
  - `AAAAAAA` -> aceita apenas `AAA` (bloqueia letras adicionais)
- [x] Instruções de recarregamento forçado (`Ctrl + Shift + R`) fornecidas ao usuário para descarte do cache local do navegador.
