# Planejamento: Acesso Remoto Temporário via Cloudflare Quick Tunnels

- **Data:** 2026-09-08
- **Autor:** Antigravity (Pair Programming AI) & Usuário
- **Status:** Concluído
- **Registro de Aprovação (Proceed):** Aprovado pelo usuário em 2026-09-08 às 18:32.

---

## 1. Contexto e Objetivos

O usuário necessita acessar a aplicação em execução no ambiente de desenvolvimento local (desktop) a partir de dispositivos móveis ou computadores externos fora da rede Wi-Fi local para realização de testes visuais e treinamentos práticos de uso.

Para evitar a necessidade de redirecionamento arriscado de portas no roteador residencial (Port Forwarding), adotou-se o uso do **Cloudflare Quick Tunnels** (`trycloudflare.com`). Essa ferramenta estabelece um túnel criptografado seguro e gera uma URL pública temporária com SSL (`https://*.trycloudflare.com`).

---

## 2. Decisões Técnicas e Arquiteturais

1. **Isolamento Estrito em Modo de Desenvolvimento (`DEBUG = True`):**
   - A permissão do wildcard `https://*.trycloudflare.com` para validação de CSRF é injetada estritamente dentro da condicional `if DEBUG:`.
   - Em produção (`DEBUG = False`), a lista `CSRF_TRUSTED_ORIGINS` ignora completamente esse domínio, prevenindo vulnerabilidades de CSRF originadas de domínios públicos de terceiros.

2. **Diretriz de Reversão / Rollback Mandatório na Fase 15:**
   - O item de rollback é expressamente registrado nos arquivos de governança (`docs/PLANO.md` e `docs/STATUS.md`).
   - Durante a Fase 15 (Hardening e Deploy), a linha correspondente em `backend/config/settings.py` deve ser formalmente auditada e removida.

3. **Facilidade Operacional:**
   - Criação do utilitário `tools/iniciar_cloudflare_tunnel.bat` para verificação de dependência do `cloudflared.exe` e execução do comando com inicialização automática e mensagens claras em português.

---

## 3. Arquivos Afetados

- `backend/config/settings.py` (Adição condicional do wildcard do Cloudflare em `CSRF_TRUSTED_ORIGINS`)
- `tools/iniciar_cloudflare_tunnel.bat` (Script utilitário para Windows)
- `docs/PLANO.md` (Registro da tarefa de rollback na Fase 15)
- `docs/STATUS.md` (Registro do status atual e pendência na Fase 15)

---

## 4. Plano de Verificação e Testes

- Execução dos testes automatizados de autenticação e core do Django (`python backend/manage.py test core apps.authentication`).
- Verificação de sintaxe e carregamento seguro do arquivo `settings.py`.
- Instrução detalhada para o usuário inicializar o túnel e validar no navegador externo.
