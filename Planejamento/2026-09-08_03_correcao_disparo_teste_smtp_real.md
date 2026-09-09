# Planejamento: Correção e Habilitação de Disparo Real de Teste SMTP

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Pendente de Aprovação (Aguardando Proceed)
- **Registro do Proceed:** Pendente.

---

## 1. Contexto e Diagnóstico
O usuário configurou seus dados de e-mail do Google (Host `smtp.gmail.com`, Porta `587`, Senha de App), mas ao clicar no botão de teste de disparo de e-mail nenhum e-mail chega à sua caixa postal.
### Causas Raiz Identificadas:
1. **Fallback de Desenvolvimento em `services.py`:**
   A função `testar_conexao_smtp()` continha a seguinte checagem:
   ```python
   if 'locmem' in backend_configurado or 'console' in backend_configurado:
       conexao = get_connection()
   ```
   Como o `settings.py` local possui `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`, o Django em vez de conectar ao servidor SMTP do Google imprimia o e-mail no console do Python (`console.EmailBackend`).
2. **Divergência de Parâmetro Frontend / Backend:**
   O frontend (`administracao-view.js`) enviava `{ email_destino }`, enquanto o serializer (`TesteSmtpSerializer`) e o serviço esperavam `destinatario`.
3. **Disparo com Dados em Tela (Sem exigir salvar previamente):**
   O botão de teste deve enviar os dados atualmente preenchidos no formulário (Host, Porta, Usuário, Senha preenchida, Nome Remetente) para permitir testar as credenciais antes mesmo de salvar, ou usar as do banco se a senha não for redigitada.

---

## 2. Decisões Técnicas e Arquiteturais
- **Backend (`apps/administracao/services.py`):**
  - O teste de conexão SMTP deve **sempre utilizar conexão SMTP real** (`EmailBackend(host=..., port=..., username=..., password=..., use_tls=True, timeout=15)`), garantindo que a rotina realmente valide o handshake com os servidores de correio (ex: Gmail). Mantém suporte a `locmem` apenas quando executado sob a suíte de testes unitários automatizados do Django (`test_runner`).
- **Backend (`apps/administracao/serializers.py`):**
  - Adicionar suporte a `email_destino` como alias para `destinatario` no `TesteSmtpSerializer`.
- **Frontend (`administracao-view.js`):**
  - No clique de `#btn-testar-smtp`: coletar os valores dos inputs da tela (`smtp-host`, `smtp-port`, `smtp-user`, `smtp-pass`, `smtp-remetente`) e enviar junto com o `destinatario` (digitado ou sugerido como o próprio `smtp-user`).
  - Adicionar botões de Preset Rápido (ex: botão `GMAIL` que preenche `smtp.gmail.com`, porta `587` e foca no campo de usuário).
- **Versionamento PWA:**
  - `CACHE_NAME = 'emc-soldas-v3.8'` em `frontend/sw.js`.
  - Sufixos `?v=3.8` em `frontend/index.html`.

---

## 3. Arquivos a Modificar
- `backend/apps/administracao/services.py`
- `backend/apps/administracao/serializers.py`
- `frontend/assets/js/views/administracao-view.js`
- `frontend/sw.js`
- `frontend/index.html`

---

## 4. Verificação e Testes
- Bateria de testes automatizados do Django (`apps.administracao`).
- Teste real com disparo via Gmail para a caixa postal do usuário.

---

## 5. Relatório de Execução
- **Backend Services:** Em ackend/apps/administracao/services.py, 	estar_conexao_smtp() agora abre socket direto via EmailBackend com 	imeout=15, eliminando o interceptador de console local em tempo de execução real (mantendo locmem para testes unitários).
- **Backend Serializers:** Em ackend/apps/administracao/serializers.py, TesteSmtpSerializer suporta email_destino como alias de destinatario.
- **Frontend Views:** Em rontend/assets/js/views/administracao-view.js, #btn-testar-smtp coleta os valores em tempo real da tela (inclusive senha de app digitada no momento) e adicionados botões de preset rápido para Google Gmail e Microsoft Outlook.
- **Versionamento PWA:** CACHE_NAME = 'emc-soldas-v3.8' em rontend/sw.js e tags atualizadas com ?v=3.8 em rontend/index.html.
- **Testes Automatizados:** 17 testes executados em pps.administracao com 100% de aprovação.
