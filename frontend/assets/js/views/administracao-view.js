/**
 * EMC Soldas - View de Central Administrativa, Configurações Globais, SMTP, Equipe e Lixeira
 */

window.AdministracaoView = {
  currentTab: 'parametros',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CENTRAL DO ADMINISTRADOR</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">PARÂMETROS DA EMPRESA, SMTP, GESTÃO DE EQUIPE, LOG VIEWER E LIXEIRA</p>
        </div>
      </div>

      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'parametros' ? 'active' : ''}" id="tab-btn-adm-param">
          PARÂMETROS GLOBAIS
        </button>
        <button class="tab-btn ${this.currentTab === 'smtp' ? 'active' : ''}" id="tab-btn-adm-smtp">
          SERVIÇO SMTP (E-MAILS)
        </button>
        <button class="tab-btn ${this.currentTab === 'dicionarios' ? 'active' : ''}" id="tab-btn-adm-dicionarios">
          DICIONÁRIOS MESTRES (UOM & ATRIBUTOS)
        </button>
        <button class="tab-btn ${this.currentTab === 'equipe' ? 'active' : ''}" id="tab-btn-adm-equipe">
          GESTÃO DE EQUIPE (RBAC)
        </button>
        <button class="tab-btn ${this.currentTab === 'logs' ? 'active' : ''}" id="tab-btn-adm-logs">
          LOG VIEWER DO SERVIDOR
        </button>
        <button class="tab-btn ${this.currentTab === 'lixeira' ? 'active' : ''}" id="tab-btn-adm-lixeira">
          PAINEL DE LIXEIRA & RESTAURAÇÃO
        </button>
      </div>

      <div id="administracao-tab-content"></div>
    `;

    document.getElementById('tab-btn-adm-param')?.addEventListener('click', () => {
      this.currentTab = 'parametros';
      this.render(container);
    });
    document.getElementById('tab-btn-adm-smtp')?.addEventListener('click', () => {
      this.currentTab = 'smtp';
      this.render(container);
    });
    document.getElementById('tab-btn-adm-dicionarios')?.addEventListener('click', () => {
      this.currentTab = 'dicionarios';
      this.render(container);
    });
    document.getElementById('tab-btn-adm-equipe')?.addEventListener('click', () => {
      this.currentTab = 'equipe';
      this.render(container);
    });
    document.getElementById('tab-btn-adm-logs')?.addEventListener('click', () => {
      this.currentTab = 'logs';
      this.render(container);
    });
    document.getElementById('tab-btn-adm-lixeira')?.addEventListener('click', () => {
      this.currentTab = 'lixeira';
      this.render(container);
    });

    const content = document.getElementById('administracao-tab-content');
    if (this.currentTab === 'parametros') {
      this.renderParametros(content);
    } else if (this.currentTab === 'smtp') {
      this.renderSmtp(content);
    } else if (this.currentTab === 'dicionarios') {
      this.renderDicionariosMestres(content);
    } else if (this.currentTab === 'equipe') {
      this.renderEquipe(content);
    } else if (this.currentTab === 'logs') {
      this.renderLogViewer(content);
    } else if (this.currentTab === 'lixeira') {
      this.renderLixeira(content);
    }
  },

  // ==========================================================================
  // 1. PARÂMETROS GLOBAIS
  // ==========================================================================
  async renderParametros(container) {
    container.innerHTML = `<div class="card text-center" style="padding: 40px;"><div class="loader-spinner"></div></div>`;

    try {
      const config = await window.api.get(`${window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONFIGURACOES_GLOBAIS}1/`);

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <h3>DADOS DA EMPRESA & PARÂMETROS OPERACIONAIS</h3>
            <span class="status-chip info">CONFIGURAÇÃO GLOBAL</span>
          </div>

          <form id="form-config-global">
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 16px;">
              <div class="form-group">
                <label class="form-label" for="cfg-razao">Razão Social da Oficina *</label>
                <input type="text" id="cfg-razao" class="form-control" value="${config.razao_social || ''}" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="cfg-cnpj">CNPJ da Empresa *</label>
                <input type="text" id="cfg-cnpj" class="form-control mono-text" data-mask="cpf-cnpj" value="${config.cnpj || ''}" required>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              <div class="form-group">
                <label class="form-label" for="cfg-telefone">Telefone / WhatsApp de Contato</label>
                <input type="text" id="cfg-telefone" class="form-control mono-text" data-mask="telefone" value="${config.telefone_contato || ''}">
              </div>
              <div class="form-group">
                <label class="form-label" for="cfg-endereco">Endereço Completo da Oficina</label>
                <input type="text" id="cfg-endereco" class="form-control" value="${config.endereco_oficina || ''}">
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 16px; margin-top: 16px; border-top: 1px solid var(--color-steel-gray); padding-top: 16px;">
              <div class="form-group">
                <label class="form-label" for="cfg-taxa-mo">Taxa Mão de Obra (R$/Hora) *</label>
                <input type="text" id="cfg-taxa-mo" class="form-control mono-text" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(config.taxa_mao_de_obra_hora || 120)}" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="cfg-validade">Validade Padrão Orçamento (Dias)</label>
                <input type="number" id="cfg-validade" class="form-control mono-text" value="${config.validade_orcamento_dias || 15}" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="cfg-ociosidade">Tempo Soft Lock (Minutos)</label>
                <input type="number" id="cfg-ociosidade" class="form-control mono-text" value="${config.tempo_ociosidade_minutos || 30}" required>
              </div>
              <div class="form-group">
                <label class="form-label" for="cfg-retencao-logs">Retenção de Logs (Dias)</label>
                <input type="number" id="cfg-retencao-logs" class="form-control mono-text" value="${config.retencao_logs_dias || 90}" required>
              </div>
            </div>

            <div class="text-right mt-16">
              <button type="submit" class="btn btn-primary" id="btn-salvar-config">SALVAR PARÂMETROS</button>
            </div>
          </form>
        </div>
      `;

      document.getElementById('form-config-global')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-salvar-config');
        btn.disabled = true;
        btn.textContent = 'SALVANDO...';

        try {
          const payload = {
            razao_social: document.getElementById('cfg-razao').value.trim(),
            cnpj: window.EMCUtils.extrairApenasDigitos(document.getElementById('cfg-cnpj').value),
            telefone_contato: window.EMCUtils.extrairApenasDigitos(document.getElementById('cfg-telefone').value),
            endereco_oficina: document.getElementById('cfg-endereco').value.trim(),
            taxa_mao_de_obra_hora: window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cfg-taxa-mo').value),
            validade_orcamento_dias: parseInt(document.getElementById('cfg-validade').value, 10),
            tempo_ociosidade_minutos: parseInt(document.getElementById('cfg-ociosidade').value, 10),
            retencao_logs_dias: parseInt(document.getElementById('cfg-retencao-logs').value, 10)
          };

          await window.api.put(`${window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONFIGURACOES_GLOBAIS}1/`, payload);
          window.EMCUtils.showToast('Parâmetros globais atualizados com sucesso!', 'success');
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar parâmetros.', 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = 'SALVAR PARÂMETROS';
        }
      });
    } catch (err) {
      container.innerHTML = `<div class="alert-banner alert-danger">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  // ==========================================================================
  // 2. SERVIÇO SMTP
  // ==========================================================================
  async renderSmtp(container) {
    container.innerHTML = `<div class="card text-center" style="padding: 40px;"><div class="loader-spinner"></div></div>`;

    try {
      const config = await window.api.get(`${window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONFIGURACOES_GLOBAIS}1/`);

      container.innerHTML = `
        <div class="card">
          <div class="card-header">
            <h3>CONFIGURAÇÃO DO SERVIDOR SMTP (DISPARO DE E-MAILS)</h3>
            <span class="status-chip warning">CRIPTOGRAFIA AES-256</span>
          </div>

          <form id="form-smtp-config">
            <div style="display: grid; grid-template-columns: 2fr 100px; gap: 16px;">
              <div class="form-group">
                <label class="form-label" for="smtp-host">Host do Servidor SMTP *</label>
                <input type="text" id="smtp-host" class="form-control" placeholder="smtp.gmail.com" value="${config.smtp_host || ''}" required data-no-transform="true">
              </div>
              <div class="form-group">
                <label class="form-label" for="smtp-port">Porta *</label>
                <input type="number" id="smtp-port" class="form-control mono-text" placeholder="587" value="${config.smtp_port || 587}" required>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
              <div class="form-group">
                <label class="form-label" for="smtp-user">Usuário / E-mail de Autenticação *</label>
                <input type="email" id="smtp-user" class="form-control" placeholder="notificacoes@emcsoldas.com.br" value="${config.smtp_user || ''}" required data-no-transform="true">
              </div>
              <div class="form-group">
                <label class="form-label" for="smtp-pass">Senha / App Password (Criptografada no Banco)</label>
                <input type="password" id="smtp-pass" class="form-control" placeholder="••••••••••••" data-no-transform="true">
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="smtp-remetente">Nome de Exibição do Remetente</label>
              <input type="text" id="smtp-remetente" class="form-control" value="${config.email_remetente_nome || 'EMC SOLDAS - OFICINA'}">
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px; border-top: 1px solid var(--color-steel-gray); padding-top: 16px;">
              <button type="button" class="btn btn-secondary" id="btn-testar-smtp">⚡ TESTAR DISPARO EM TEMPO REAL</button>
              <button type="submit" class="btn btn-primary" id="btn-salvar-smtp">SALVAR CONFIGURAÇÃO SMTP</button>
            </div>
          </form>
        </div>
      `;

      document.getElementById('btn-testar-smtp')?.addEventListener('click', async () => {
        const btn = document.getElementById('btn-testar-smtp');
        btn.disabled = true;
        btn.textContent = 'DISPARANDO TESTE...';

        try {
          const email_destino = prompt('Digite o e-mail de destino para receber o teste:', window.auth.user?.email || 'admin@emcsoldas.com.br');
          if (!email_destino) {
            btn.disabled = false;
            btn.textContent = '⚡ TESTAR DISPARO EM TEMPO REAL';
            return;
          }

          const res = await window.api.post(window.CONFIG.ENDPOINTS.ADMINISTRACAO.TESTAR_SMTP, { email_destino });
          window.EMCUtils.showToast(res.message || 'E-mail de teste enviado com sucesso!', 'success');
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Falha ao disparar e-mail de teste.', 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = '⚡ TESTAR DISPARO EM TEMPO REAL';
        }
      });

      document.getElementById('form-smtp-config')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
          smtp_host: document.getElementById('smtp-host').value.trim(),
          smtp_port: parseInt(document.getElementById('smtp-port').value, 10),
          smtp_user: document.getElementById('smtp-user').value.trim(),
          email_remetente_nome: document.getElementById('smtp-remetente').value.trim()
        };

        const senha = document.getElementById('smtp-pass').value;
        if (senha) payload.smtp_password = senha;

        try {
          await window.api.put(`${window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONFIGURACOES_GLOBAIS}1/`, payload);
          window.EMCUtils.showToast('Configurações SMTP salvas e protegidas via AES-256!', 'success');
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar SMTP.', 'error');
        }
      });
    } catch (err) {
      container.innerHTML = `<div class="alert-banner alert-danger">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  // ==========================================================================
  // 3. GESTÃO DE EQUIPE (RBAC)
  // ==========================================================================
  async renderEquipe(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">COLABORADORES, MATRIZ DOS 10 TOGGLES DINÂMICOS E ONBOARDING</p>
          <button class="btn btn-primary" id="btn-convidar-usuario">+ CONVIDAR COLABORADOR</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>E-MAIL</th>
              <th>PERFIL</th>
              <th>STATUS DE ACESSO</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-usuarios-tbody">
            <tr><td colspan="5" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-convidar-usuario')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'CONVIDAR NOVO COLABORADOR (ONBOARDING)',
        size: 'sm',
        confirmText: 'ENVIAR CONVITE',
        content: `
          <div class="form-group">
            <label class="form-label">E-mail do Colaborador *</label>
            <input type="email" id="convite-email" class="form-control" placeholder="colaborador@emcsoldas.com.br" required data-no-transform="true" autofocus>
          </div>
          <div class="form-group">
            <label class="form-label">Perfil Base *</label>
            <select id="convite-role" class="form-control">
              <option value="OPERADOR" selected>OPERADOR</option>
              <option value="ADMIN">ADMINISTRADOR</option>
            </select>
          </div>
        `,
        onConfirm: async () => {
          const email = document.getElementById('convite-email').value.trim().toLowerCase();
          const role = document.getElementById('convite-role').value;

          if (!email) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.USUARIOS.CONVIDAR, { email, role });
            window.EMCUtils.showToast('Convite com link de ativação enviado por e-mail com sucesso!', 'success');
            this.renderEquipe(container);
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao enviar convite.', 'error');
            return false;
          }
        }
      });
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.USUARIOS.LISTA);
      const usuarios = res.results || res || [];
      const tbody = document.getElementById('lista-usuarios-tbody');

      let html = '';
      usuarios.forEach((u) => {
        const isBloqueado = !!u.bloqueado_ate;
        html += `
          <tr>
            <td class="mono-text">#${u.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(u.email)}</strong></td>
            <td><span class="status-chip ${u.role === 'ADMIN' ? 'warning' : 'info'}">${u.role}</span></td>
            <td>
              <span class="status-chip ${isBloqueado ? 'danger' : 'success'}">${isBloqueado ? 'BLOQUEADO (BRUTE-FORCE)' : 'ATIVO'}</span>
            </td>
            <td style="text-align: right; white-space: nowrap;">
              ${isBloqueado ? `
                <button class="btn btn-primary btn-sm" onclick="window.AdministracaoView.desbloquearUsuario(${u.id})">DESBLOQUEAR</button>
              ` : ''}
              <button class="btn btn-secondary btn-sm" onclick="window.AdministracaoView.gerenciarPermissoes(${u.id})">PERMISSÕES (10 TOGGLES)</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-usuarios-tbody').innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async desbloquearUsuario(userId) {
    try {
      const endpoint = window.CONFIG.ENDPOINTS.USUARIOS.DESBLOQUEAR.replace('{id}', userId);
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast('Conta desbloqueada com sucesso!', 'success');
      this.renderEquipe(document.getElementById('administracao-tab-content'));
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao desbloquear conta.', 'error');
    }
  },

  async gerenciarPermissoes(userId) {
    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.PERMISSOES.LISTA}?usuario_id=${userId}`);
      const perm = (res.results && res.results[0]) || res[0] || {};

      const toggles = [
        { key: 'acesso_comercial', label: '01. Acesso Comercial (Orçamentos e Faturas)' },
        { key: 'acesso_tesouraria', label: '02. Acesso à Tesouraria (Caixa e Estornos)' },
        { key: 'acesso_compras', label: '03. Acesso a Compras (Notas de Entrada)' },
        { key: 'gestao_catalogo', label: '04. Gestão de Catálogo (Itens e BOM)' },
        { key: 'visao_relatorios', label: '05. Visualização de Relatórios Estratégicos' },
        { key: 'cadastros_financeiros', label: '06. Cadastros Financeiros (Contas e Regras)' },
        { key: 'gestao_dicionario_uom', label: '07. Dicionário Central UOM e Atributos' },
        { key: 'configuracoes_globais', label: '08. Configurações Globais e SMTP' },
        { key: 'gestao_equipe', label: '09. Gestão de Equipe e Colaboradores' },
        { key: 'auditoria_logs_recovery', label: '10. Auditoria, Log Viewer e Lixeira' }
      ];

      let htmlToggles = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">';
      toggles.forEach((t) => {
        const checked = perm[t.key] ? 'checked' : '';
        htmlToggles += `
          <label style="display: flex; align-items: center; gap: 8px; background-color: var(--color-surface-container); padding: 10px; border: 1px solid var(--color-steel-gray); cursor: pointer;">
            <input type="checkbox" id="toggle-${t.key}" ${checked}>
            <span style="font-size: 13px;">${t.label}</span>
          </label>
        `;
      });
      htmlToggles += '</div>';

      window.EMCUtils.openModal({
        title: `MATRIZ DE PERMISSÕES DINÂMICAS (RBAC) - USUÁRIO #${userId}`,
        size: 'lg',
        confirmText: 'SALVAR PERMISSÕES',
        content: htmlToggles,
        onConfirm: async () => {
          const payload = {};
          toggles.forEach((t) => {
            payload[t.key] = document.getElementById(`toggle-${t.key}`).checked;
          });

          try {
            if (perm.id) {
              await window.api.patch(`${window.CONFIG.ENDPOINTS.PERMISSOES.LISTA}${perm.id}/`, payload);
            } else {
              await window.api.post(window.CONFIG.ENDPOINTS.PERMISSOES.LISTA, { usuario_id: userId, ...payload });
            }
            window.EMCUtils.showToast('Permissões dinâmicas salvas com sucesso!', 'success');
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar permissões.', 'error');
            return false;
          }
        }
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar permissões.', 'error');
    }
  },

  // ==========================================================================
  // 4. LOG VIEWER
  // ==========================================================================
  async renderLogViewer(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">ARQUIVOS DIÁRIOS DE LOG FÍSICO COM MANIFESTO TTL</p>
          <button class="btn btn-danger btn-sm" id="btn-expurgar-logs">EXPURGAR LOGS EXPIRADOS (COM BACKUP)</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DATA DO LOG</th>
              <th>ARQUIVO FÍSICO</th>
              <th>TOTAL DE EVENTOS</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-logs-tbody">
            <tr><td colspan="5" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-expurgar-logs')?.addEventListener('click', async () => {
      if (!confirm('Deseja executar a rotina de expurgo TTL com envio prévio de backup por e-mail?')) return;
      try {
        const res = await window.api.post(window.CONFIG.ENDPOINTS.ADMINISTRACAO.EXPURGAR_LOGS, {});
        window.EMCUtils.showToast(res.message || 'Rotina de expurgo executada com sucesso!', 'success');
        this.renderLogViewer(container);
      } catch (err) {
        window.EMCUtils.showToast(err.message || 'Erro no expurgo.', 'error');
      }
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONTROLE_LOGS);
      const logs = res.results || res || [];
      const tbody = document.getElementById('lista-logs-tbody');

      if (!logs.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center mono-text" style="padding: 24px;">Nenhum arquivo de log diário catalogado no momento.</td></tr>';
        return;
      }

      let html = '';
      logs.forEach((l) => {
        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(l.data_log)}</td>
            <td class="mono-text" style="font-size: 12px;">${window.EMCUtils.escapeHtml(l.caminho_arquivo_fisico)}</td>
            <td class="mono-text">${l.quantidade_linhas || 0}</td>
            <td style="text-align: right;">
              <button class="btn btn-secondary btn-sm" onclick="window.AdministracaoView.visualizarLog('${l.data_log}')">VER LOG</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-logs-tbody').innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async visualizarLog(dataLog) {
    try {
      const endpoint = `${window.CONFIG.ENDPOINTS.ADMINISTRACAO.LOG_VIEWER}?data=${dataLog}`;
      const res = await window.api.get(endpoint);

      window.EMCUtils.openModal({
        title: `LOG DO SERVIDOR - ${dataLog}`,
        size: 'xl',
        hideFooter: true,
        content: `
          <pre class="mono-text" style="background-color: var(--color-surface-container-lowest); color: #72cf88; padding: 16px; border: 1px solid var(--color-steel-gray); max-height: 500px; overflow-y: auto; font-size: 12px; white-space: pre-wrap;">
${window.EMCUtils.escapeHtml(res.conteudo || 'Arquivo de log vazio.')}
          </pre>
        `
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao abrir arquivo de log.', 'error');
    }
  },

  // ==========================================================================
  // 5. PAINEL DE LIXEIRA & RESTAURAÇÃO (100% SOFT DELETE)
  // ==========================================================================
  async renderLixeira(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">AUDITORIA DE REGISTROS INATIVADOS COM RESTAURAÇÃO LÓGICA EM 1 CLIQUE</p>
          <select id="filtro-lixeira-entidade" class="form-control" style="width: 220px;">
            <option value="orcamentos">ORÇAMENTOS</option>
            <option value="faturas">FATURAS</option>
            <option value="clientes">CLIENTES / FORNECEDORES</option>
            <option value="itens">INSUMOS / ITENS</option>
            <option value="produtos">PRODUTOS BOM</option>
          </select>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>IDENTIFICAÇÃO DO REGISTRO</th>
              <th>DELETADO EM</th>
              <th>DELETADO POR</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-lixeira-tbody">
            <tr><td colspan="5" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    const selectEntidade = document.getElementById('filtro-lixeira-entidade');
    selectEntidade?.addEventListener('change', () => this.carregarLixeira(selectEntidade.value));

    this.carregarLixeira(selectEntidade?.value || 'orcamentos');
  },

  async carregarLixeira(entidade) {
    const tbody = document.getElementById('lista-lixeira-tbody');
    if (!tbody) return;

    try {
      const endpoint = `${window.CONFIG.ENDPOINTS.ADMINISTRACAO.LIXEIRA}?entidade=${entidade}`;
      const res = await window.api.get(endpoint);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center mono-text" style="padding: 24px;">Lixeira vazia para esta entidade.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item) => {
        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(item.identificacao || item.nome || item.descricao || 'Registro')}</strong></td>
            <td class="mono-text">${window.EMCUtils.formatarDataHoraPtBr(item.deleted_at)}</td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.deleted_by_email || 'Colaborador')}</td>
            <td style="text-align: right;">
              <button class="btn btn-primary btn-sm" onclick="window.AdministracaoView.restaurarRegistro('${entidade}', ${item.id})">RESTAURAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async restaurarRegistro(entidade, id) {
    try {
      const endpoint = window.CONFIG.ENDPOINTS.ADMINISTRACAO.RESTAURAR_LIXEIRA.replace('{entidade}', entidade).replace('{id}', id);
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast(`Registro #${id} restaurado com sucesso!`, 'success');
      this.carregarLixeira(entidade);
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao restaurar registro.', 'error');
    }
  },

  // ==========================================================================
  // 6. DICIONÁRIOS MESTRES (UOM & ATRIBUTOS TÉCNICOS)
  // ==========================================================================
  async renderDicionariosMestres(container) {
    container.innerHTML = `
      <div class="grid grid-cols-12 mb-24">
        <!-- Card 1: Dicionário UOM -->
        <div class="card col-span-6">
          <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <h3>UNIDADES DE MEDIDA (UOM)</h3>
              <p class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">PADRÕES DE COMPRA, CONSUMO E VENDA</p>
            </div>
            <button class="btn btn-primary btn-sm" id="btn-novo-uom-adm">+ NOVA UOM</button>
          </div>
          <div class="table-container" style="max-height: 400px; overflow-y: auto;">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>SIGLA</th>
                  <th>DESCRIÇÃO OFICIAL</th>
                </tr>
              </thead>
              <tbody id="lista-uom-adm-tbody">
                <tr><td colspan="3" class="text-center"><div class="loader-spinner"></div></td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Card 2: Catálogo de Atributos Técnicos -->
        <div class="card col-span-6">
          <div class="card-header" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <h3>ATRIBUTOS TÉCNICOS</h3>
              <p class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">PROPRIEDADES DINÂMICAS DE INSUMOS</p>
            </div>
            <button class="btn btn-primary btn-sm" id="btn-novo-attr-adm">+ NOVO ATRIBUTO</button>
          </div>
          <div class="table-container" style="max-height: 400px; overflow-y: auto;">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>NOME DO ATRIBUTO</th>
                  <th style="text-align: right;">STATUS</th>
                </tr>
              </thead>
              <tbody id="lista-attr-adm-tbody">
                <tr><td colspan="3" class="text-center"><div class="loader-spinner"></div></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-novo-uom-adm')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'NOVA UNIDADE DE MEDIDA (UOM)',
        size: 'sm',
        confirmText: 'SALVAR',
        content: `
          <div class="form-group">
            <label class="form-label">Sigla (Ex: KG, M2, L, UN, CX) *</label>
            <input type="text" id="uom-sigla" class="form-control mono-text" maxlength="10" required autofocus>
          </div>
          <div class="form-group">
            <label class="form-label">Descrição Oficial *</label>
            <input type="text" id="uom-desc" class="form-control" required>
          </div>
        `,
        onConfirm: async () => {
          const sigla = document.getElementById('uom-sigla').value.trim();
          const descricao = document.getElementById('uom-desc').value.trim();
          if (!sigla || !descricao) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM, { sigla, descricao });
            window.EMCUtils.showToast('UOM cadastrada com sucesso!', 'success');
            this.carregarUomsAdm();
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar UOM.', 'error');
            return false;
          }
        }
      });
    });

    document.getElementById('btn-novo-attr-adm')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'NOVO ATRIBUTO TÉCNICO',
        size: 'sm',
        confirmText: 'SALVAR',
        content: `
          <div class="form-group">
            <label class="form-label">Nome do Atributo (Ex: ESPESSURA, LIGA, ROSCA) *</label>
            <input type="text" id="attr-nome" class="form-control" required autofocus>
          </div>
        `,
        onConfirm: async () => {
          const nome_atributo = document.getElementById('attr-nome').value.trim();
          if (!nome_atributo) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_ATRIBUTOS, { nome_atributo });
            window.EMCUtils.showToast('Atributo técnico cadastrado!', 'success');
            this.carregarAtributosAdm();
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar atributo.', 'error');
            return false;
          }
        }
      });
    });

    await Promise.all([this.carregarUomsAdm(), this.carregarAtributosAdm()]);
  },

  async carregarUomsAdm() {
    const tbody = document.getElementById('lista-uom-adm-tbody');
    if (!tbody) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center mono-text">Nenhuma UOM cadastrada.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((u) => {
        html += `
          <tr>
            <td class="mono-text">#${u.id}</td>
            <td class="mono-text"><strong>${window.EMCUtils.escapeHtml(u.sigla)}</strong></td>
            <td>${window.EMCUtils.escapeHtml(u.descricao)}</td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="3" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async carregarAtributosAdm() {
    const tbody = document.getElementById('lista-attr-adm-tbody');
    if (!tbody) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_ATRIBUTOS);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center mono-text">Nenhum atributo cadastrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((a) => {
        html += `
          <tr>
            <td class="mono-text">#${a.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(a.nome_atributo)}</strong></td>
            <td style="text-align: right;"><span class="status-chip success">ATIVO</span></td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="3" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  }
};
