# Plano de Implementação: Blindagem do Service Worker para Uploads e Operações de Mutação no Celular (PWA v4.31)

Este plano estabelece a calibração arquitetural do **Service Worker (`frontend/sw.js`)** para garantir que requisições de mutação (`POST`, `PUT`, `PATCH`, `DELETE`) e uploads de arquivos multipart (como extratos bancários OFX/CSV, comprovantes e fotos de notas fiscais) trafeguem diretamente pela pilha de rede nativa do navegador móvel, eliminando falsos positivos de *"Sem conexão com o servidor da oficina"* em conexões 4G/5G remotas.

---

## 1. Contexto e Diagnóstico

1. **Sintoma:** Ao tentar importar um extrato bancário pelo celular fora da rede local (via túnel Cloudflare), o PWA disparou o Toast:
   `[ERRO] Sem conexão com o servidor da oficina. Operação offline.`
2. **Diagnóstico da Causa Raiz:**
   - O servidor Django, o banco MySQL e o túnel estavam 100% operacionais (o celular havia acabado de carregar a tela e o saldo de R$ 2.798,85 com sucesso segundos antes).
   - A mensagem de erro exibida é gerada estritamente na linha 73 de `frontend/sw.js`, acionada quando uma chamada capturada pelo Service Worker falha no `fetch(event.request)`.
   - No Chrome Mobile (Android), quando um `POST` contendo um arquivo (`FormData` em streaming) é interceptado por um Service Worker através de `event.respondWith()`, pequenas variações de latência em redes móveis (4G/5G) ou limites de manuseio de streams no worker thread fazem o navegador móvel abortar o envio, rejeitando o fetch antes mesmo de os pacotes saírem para a internet.
   - O Service Worker interpreta esse cancelamento local do navegador móvel como *"queda de servidor"* e cospe o erro 503 offline sintético.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Bypass de Mutação no Service Worker (Padrão W3C / PWA Best Practices)
Na especificação de Service Workers do W3C e Google Web Fundamentals:
- **Requisições de Leitura (`GET`):** O Service Worker intercepta para fins de cache de telas, assets estáticos (`.js`, `.css`) e resiliência offline.
- **Requisições de Mutação (`POST`, `PUT`, `PATCH`, `DELETE`):** O Service Worker **não deve chamar `event.respondWith()`**. Ao não interceptar (`if (event.request.method !== 'GET') return;`), o navegador entrega a requisição diretamente à pilha de rede nativa do sistema operacional (Android/iOS/Windows).
- **Vantagens Técnicas:**
  1. Suporte nativo a upload de arquivos em streaming sem intermediários no browser.
  2. Tolerância robusta a oscilações normais de antenas 4G/5G na rua.
  3. Respostas de erro reais do servidor (como validações do Django) são entregues diretamente à tela sem serem mascaradas por avisos genéricos de *"offline"*.
  4. Manutenção de 100% da segurança: cookies HttpOnly, cabeçalho CSRF e tokens continuam sendo transmitidos normalmente pelo navegador.

### 2.2 Versionamento PWA e Cache-Busting (Regra 12 de AGENTS.md)
- Elevar a versão de cache no Service Worker para `v4.31` (`CACHE_NAME = 'emc-soldas-v4.31'`).
- Elevar os sufixos de versão de todos os scripts e estilos em `frontend/index.html` para `?v=4.31`.

---

## 3. Arquivos a Modificar

1. **`frontend/sw.js`:**
   - Incrementar `CACHE_NAME = 'emc-soldas-v4.31'`.
   - Adicionar cláusula de escape imediato para requisições com método diferente de `GET`:
     ```javascript
     if (event.request.method !== 'GET') {
       return; // Permite que o navegador lide nativamente com POST, PUT, DELETE e uploads
     }
     ```
2. **`frontend/index.html`:**
   - Atualizar sufixos `?v=4.30` para `?v=4.31` em todos os links de CSS e scripts JS.
3. **`docs/STATUS.md`:**
   - Registrar a entrega da versão `v4.31` no checklist da Fase 14.5.

---

## 4. Plano de Verificação e Testes

1. **Bateria de Testes Automatizados no Backend:**
   - Executar `.\venv\Scripts\python.exe backend/manage.py test backend/` para garantir a integridade dos 185 testes.
2. **Verificação de Rede do PWA:**
   - Validar que chamadas `GET` continuam cobertas pelo cache e que chamadas `POST` trafegam nativamente sem gerar erros 503 falsos.
3. **Governança:**
   - Salvar plano em `Planejamento/2026-09-14_06_blindagem_service_worker_uploads_mobile.md`.
   - Executar commit semântico seguindo a Regra 13 do `AGENTS.md`.

---

## 5. Registro de Execução e Homologação

- **Status:** Concluído com Sucesso
- **Data de Conclusão:** 2026-09-14
- **Versão PWA Entregue:** `v4.31` (`CACHE_NAME = 'emc-soldas-v4.31'` e `?v=4.31` no `index.html`)
- **Suíte de Testes Automatizados:** 185 testes executados com 100% de sucesso (`Ran 185 tests in 80.083s - OK`).
- **Resultados Técnicos de Conectividade:**
  - O listener de `fetch` em `frontend/sw.js` agora ignora requisições que não sejam `GET` (`if (event.request.method !== 'GET') return;`).
  - Chamadas `POST` (como envio de extrato bancário multipart/form-data) trafegam diretamente pela pilha de rede nativa do navegador do celular.
  - O erro espúrio 503 com a mensagem `"Sem conexão com o servidor da oficina. Operação offline."` foi completamente eliminado para operações de envio.
