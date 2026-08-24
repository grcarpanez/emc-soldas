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
  // 3. GESTÃO DE EQUIPE (RBAC & CONTROLE DE ACESSO)
  // ==========================================================================
  async renderEquipe(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO DE COLABORADORES, PERFIS (ADMIN/OPERADOR), 10 TOGGLES RBAC E ATIVAÇÃO</p>
          </div>
          <button class="btn btn-primary" id="btn-convidar-usuario">+ CONVIDAR COLABORADOR</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>COLABORADOR / E-MAIL</th>
              <th>PERFIL BASE</th>
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
            <label class="form-label">Nome Completo do Colaborador *</label>
            <input type="text" id="convite-nome" class="form-control" placeholder="NOME DO COLABORADOR" required autofocus>
          </div>
          <div class="form-group">
            <label class="form-label">E-mail de Acesso *</label>
            <input type="email" id="convite-email" class="form-control" placeholder="colaborador@emcsoldas.com.br" required data-no-transform="true">
          </div>
          <div class="form-group">
            <label class="form-label">Perfil Base Inicial *</label>
            <select id="convite-role" class="form-control">
              <option value="Operador" selected>OPERADOR (ACESSO RESTRITO POR TOGGLES)</option>
              <option value="Admin">ADMINISTRADOR (ACESSO TOTAL PLENO)</option>
            </select>
          </div>
        `,
        onConfirm: async () => {
          const nome = document.getElementById('convite-nome').value.trim();
          const email = document.getElementById('convite-email').value.trim().toLowerCase();
          const role = document.getElementById('convite-role').value;

          if (!nome || !email) {
            window.EMCUtils.showToast('Informe o nome e e-mail do colaborador.', 'warning');
            return false;
          }

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.USUARIOS.CONVIDAR, { nome, email, role });
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

      if (!usuarios.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center mono-text" style="padding: 24px;">Nenhum colaborador encontrado.</td></tr>';
        return;
      }

      const currentUserId = window.auth.user?.id;
      let html = '';

      usuarios.forEach((u) => {
        const isSelf = currentUserId && (currentUserId === u.id);
        const isBloqueado = u.bloqueado_ate && new Date(u.bloqueado_ate) > new Date();
        const isAdmin = (u.role === 'Admin' || u.role === 'ADMIN');

        let statusChip = '';
        if (isBloqueado) {
          statusChip = '<span class="status-chip danger">BLOQUEADO (BRUTE-FORCE)</span>';
        } else if (!u.is_ativo) {
          statusChip = '<span class="status-chip secondary">DESATIVADO</span>';
        } else {
          statusChip = '<span class="status-chip success">ATIVO</span>';
        }

        // Ação de Ativação / Desativação com proteção para o usuário logado
        let btnStatus = '';
        if (isSelf) {
          btnStatus = `<button class="btn btn-ghost btn-sm" disabled title="Não é permitido desativar seu próprio usuário" style="opacity: 0.35; cursor: not-allowed;">DESATIVAR</button>`;
        } else if (u.is_ativo) {
          btnStatus = `<button class="btn btn-danger btn-sm" onclick="window.AdministracaoView.confirmarDesativacaoUsuario(${u.id}, '${window.EMCUtils.escapeHtml(u.nome || u.email)}')">DESATIVAR</button>`;
        } else {
          btnStatus = `<button class="btn btn-primary btn-sm" onclick="window.AdministracaoView.ativarUsuario(${u.id}, '${window.EMCUtils.escapeHtml(u.nome || u.email)}')">ATIVAR</button>`;
        }

        html += `
          <tr>
            <td class="mono-text">#${u.id}</td>
            <td>
              <strong>${window.EMCUtils.escapeHtml(u.nome || 'COLABORADOR')}</strong>
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 2px;">
                ${window.EMCUtils.escapeHtml(u.email)}
              </div>
            </td>
            <td>
              <span class="status-chip ${isAdmin ? 'warning' : 'info'}">${isAdmin ? 'ADMINISTRADOR' : 'OPERADOR'}</span>
              ${isSelf ? '<span class="status-chip secondary" style="font-size: 10px; margin-left: 4px;">VOCÊ</span>' : ''}
            </td>
            <td>
              ${statusChip}
            </td>
            <td style="text-align: right; white-space: nowrap;">
              <div style="display: inline-flex; gap: 6px; align-items: center;">
                ${isBloqueado ? `
                  <button class="btn btn-warning btn-sm" onclick="window.AdministracaoView.desbloquearUsuario(${u.id})">DESBLOQUEAR</button>
                ` : ''}
                <button class="btn btn-secondary btn-sm" onclick="window.AdministracaoView.gerenciarPermissoesEPerfil(${u.id})">PERMISSÕES & PERFIL</button>
                ${btnStatus}
              </div>
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
      const endpoint = `${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/desbloquear/`;
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast('Conta desbloqueada com sucesso!', 'success');
      this.renderEquipe(document.getElementById('administracao-tab-content'));
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao desbloquear conta.', 'error');
    }
  },

  async confirmarDesativacaoUsuario(userId, userNome) {
    window.EMCUtils.openModal({
      title: 'CONFIRMAR DESATIVAÇÃO DE COLABORADOR',
      size: 'sm',
      confirmText: 'CONFIRMAR DESATIVAÇÃO',
      content: `
        <div style="padding: 8px 0;">
          <p style="font-size: 13.5px; line-height: 1.6; margin-bottom: 12px;">
            Deseja realmente desativar o acesso de <strong>${userNome}</strong> (#${userId})?
          </p>
          <div class="alert-banner alert-warning" style="font-size: 12px;">
            O colaborador será impedido de realizar login no sistema até que sua conta seja reativada por um Administrador.
          </div>
        </div>
      `,
      onConfirm: async () => {
        try {
          const endpoint = `${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/desativar/`;
          await window.api.post(endpoint, {});
          window.EMCUtils.showToast(`Usuário ${userNome} desativado com sucesso.`, 'success');
          this.renderEquipe(document.getElementById('administracao-tab-content'));
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao desativar usuário.', 'error');
          return false;
        }
      }
    });
  },

  async ativarUsuario(userId, userNome) {
    try {
      const endpoint = `${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/ativar/`;
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast(`Usuário ${userNome} ativado com sucesso!`, 'success');
      this.renderEquipe(document.getElementById('administracao-tab-content'));
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao ativar usuário.', 'error');
    }
  },

  async gerenciarPermissoesEPerfil(userId) {
    try {
      // Busca dados completos do usuário e permissões
      const userRes = await window.api.get(`${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/`);
      const permRes = await window.api.get(`${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/permissoes/`);

      const usuario = userRes || {};
      const perm = permRes.permissoes || usuario.permissoes || {};
      const currentRole = usuario.role || 'Operador';
      const isAdmin = (currentRole === 'Admin' || currentRole === 'ADMIN');

      // Busca todos os usuários para saber se este é o único Admin
      const todosUsuariosRes = await window.api.get(window.CONFIG.ENDPOINTS.USUARIOS.LISTA);
      const todosUsuarios = todosUsuariosRes.results || todosUsuariosRes || [];
      const totalAdminsAtivos = todosUsuarios.filter(u => (u.role === 'Admin' || u.role === 'ADMIN') && u.is_ativo && u.id !== userId).length;
      const isUnicoAdmin = isAdmin && totalAdminsAtivos === 0;

      const toggles = [
        { key: 'acesso_comercial', label: '01. Acesso Comercial (Orçamentos, Faturas e Clientes)' },
        { key: 'acesso_tesouraria', label: '02. Acesso à Tesouraria (Caixa Real, Contas e Estornos)' },
        { key: 'acesso_compras', label: '03. Acesso a Compras (Notas Fiscais de Entrada)' },
        { key: 'gestao_catalogo', label: '04. Gestão de Catálogo (Itens, Produtos e Motor BOM)' },
        { key: 'visao_relatorios', label: '05. Visualização de Relatórios Estratégicos & DRE' },
        { key: 'cadastros_financeiros', label: '06. Cadastros Financeiros (Contas e Regras)' },
        { key: 'gestao_dicionario_uom', label: '07. Dicionário Central UOM e Atributos Técnicos' },
        { key: 'configuracoes_globais', label: '08. Configurações Globais, Empresa e SMTP' },
        { key: 'gestao_equipe', label: '09. Gestão de Equipe, Permissões e Desbloqueio' },
        { key: 'auditoria_logs_recovery', label: '10. Auditoria, Log Viewer do Servidor e Lixeira' }
      ];

      let htmlToggles = '<div id="container-toggles-rbac" style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">';
      toggles.forEach((t) => {
        const checked = (isAdmin || perm[t.key]) ? 'checked' : '';
        const disabled = isAdmin ? 'disabled' : '';
        htmlToggles += `
          <label style="display: flex; align-items: center; gap: 8px; background-color: var(--color-surface-container); padding: 10px; border: 1px solid var(--color-steel-gray); cursor: ${isAdmin ? 'default' : 'pointer'};">
            <input type="checkbox" id="toggle-${t.key}" class="toggle-rbac-item" ${checked} ${disabled}>
            <span style="font-size: 13px;">${t.label}</span>
          </label>
        `;
      });
      htmlToggles += '</div>';

      const modalContent = `
        <div style="margin-bottom: 20px; background-color: var(--color-surface-container); padding: 14px; border: 1px solid var(--color-steel-gray);">
          <h4 style="font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--color-rust-orange);">1. PERFIL BASE DE ACESSO (ROLE)</h4>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: center;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="modal-user-role">Papel do Colaborador *</label>
              <select id="modal-user-role" class="form-control">
                <option value="Operador" ${!isAdmin ? 'selected' : ''}>OPERADOR (PERSONALIZÁVEL)</option>
                <option value="Admin" ${isAdmin ? 'selected' : ''}>ADMINISTRADOR (ACESSO PLENO)</option>
              </select>
            </div>
            <div style="font-size: 12px; color: var(--color-on-surface-variant); line-height: 1.5;">
              ${isUnicoAdmin
                ? '<div class="alert-banner alert-warning" style="margin: 0; padding: 6px 10px; font-size: 11px;"><strong>[BLOQUEIO]</strong> Único Administrador ativo do sistema. Rebaixamento bloqueado.</div>'
                : 'Administradores possuem direitos irrestritos a todos os 10 módulos. Operadores têm acesso regulado pela matriz abaixo.'
              }
            </div>
          </div>
        </div>

        <div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="font-size: 13px; font-weight: 700; color: var(--color-rust-orange);">2. MATRIZ DOS 10 TOGGLES DINÂMICOS (RBAC)</h4>
            <span id="role-hint-badge" class="status-chip ${isAdmin ? 'warning' : 'info'}" style="font-size: 11px;">
              ${isAdmin ? 'ACESSO TOTAL HABILITADO' : 'ACESSO RESTRITO POR TOGGLES'}
            </span>
          </div>
          ${htmlToggles}
        </div>
      `;

      window.EMCUtils.openModal({
        title: `GESTÃO DE ACESSO & PERMISSÕES (RBAC) - ${window.EMCUtils.escapeHtml(usuario.nome || usuario.email).toUpperCase()} (#${userId})`,
        size: 'lg',
        confirmText: 'SALVAR PERMISSÕES & PERFIL',
        content: modalContent,
        onConfirm: async () => {
          const selectedRole = document.getElementById('modal-user-role')?.value || currentRole;
          const isNowAdmin = (selectedRole === 'Admin');

          const payloadPermissoes = {};
          toggles.forEach((t) => {
            const inputEl = document.getElementById(`toggle-${t.key}`);
            payloadPermissoes[t.key] = isNowAdmin ? true : (inputEl ? inputEl.checked : false);
          });

          try {
            // 1. Atualiza Perfil (se modificado)
            if (selectedRole !== currentRole) {
              await window.api.post(`${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/alterar-perfil/`, { role: selectedRole });
            }

            // 2. Atualiza os 10 Toggles Dinâmicos
            await window.api.patch(`${window.CONFIG.ENDPOINTS.USUARIOS.LISTA}${userId}/permissoes/`, payloadPermissoes);

            window.EMCUtils.showToast('Perfil e permissões atualizados com sucesso!', 'success');

            // Se alterou o próprio usuário logado, atualiza o contexto de autenticação
            if (window.auth.user && window.auth.user.id === userId) {
              await window.auth.checkAuth();
            }

            this.renderEquipe(document.getElementById('administracao-tab-content'));
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar permissões e perfil.', 'error');
            return false;
          }
        }
      });

      // Dinâmica de alternância de perfil no modal
      const roleSelect = document.getElementById('modal-user-role');
      roleSelect?.addEventListener('change', (e) => {
        const isAdm = e.target.value === 'Admin';
        const hintBadge = document.getElementById('role-hint-badge');
        if (hintBadge) {
          hintBadge.textContent = isAdm ? 'ACESSO TOTAL HABILITADO' : 'ACESSO RESTRITO POR TOGGLES';
          hintBadge.className = `status-chip ${isAdm ? 'warning' : 'info'}`;
        }

        document.querySelectorAll('.toggle-rbac-item').forEach((chk) => {
          if (isAdm) {
            chk.checked = true;
            chk.disabled = true;
            chk.closest('label').style.cursor = 'default';
          } else {
            chk.disabled = false;
            chk.closest('label').style.cursor = 'pointer';
          }
        });
      });
    } catch (e) {
      window.EMCUtils.showToast(e.message || 'Erro ao carregar dados do colaborador.', 'error');
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
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-sincronizar-logs">SINCRONIZAR MANIFESTO</button>
            <button class="btn btn-danger btn-sm" id="btn-expurgar-logs">EXPURGAR LOGS EXPIRADOS (COM BACKUP)</button>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DATA DO LOG</th>
              <th>ARQUIVO FÍSICO</th>
              <th>TAMANHO</th>
              <th>TOTAL DE EVENTOS</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-logs-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-sincronizar-logs')?.addEventListener('click', async () => {
      try {
        const res = await window.api.post(`${window.CONFIG.ENDPOINTS.ADMINISTRACAO.CONTROLE_LOGS}sincronizar/`, {});
        window.EMCUtils.showToast(`Manifesto sincronizado! Total: ${res.total_arquivos} arquivo(s).`, 'success');
        this.renderLogViewer(container);
      } catch (err) {
        window.EMCUtils.showToast(err.message || 'Erro ao sincronizar manifesto.', 'error');
      }
    });

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
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Nenhum arquivo de log diário catalogado no momento.</td></tr>';
        return;
      }

      let html = '';
      logs.forEach((l) => {
        const dataValida = l.data_criacao || l.data_log || '';
        const totalLinhas = l.total_eventos ?? l.quantidade_linhas ?? 0;
        const tamanhoStr = l.tamanho_formatado || (l.tamanho_bytes ? `${l.tamanho_bytes} B` : '-');
        const nomeArquivo = (l.caminho_arquivo_fisico || '').split('/').pop().split('\\').pop();

        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(dataValida)}</td>
            <td class="mono-text" style="font-size: 12px;"><strong>${window.EMCUtils.escapeHtml(l.caminho_arquivo_fisico)}</strong></td>
            <td class="mono-text" style="font-size: 12px;">${tamanhoStr}</td>
            <td class="mono-text"><span class="status-chip ${totalLinhas > 0 ? 'info' : 'secondary'}">${totalLinhas} evento(s)</span></td>
            <td style="text-align: right;">
              <button class="btn btn-secondary btn-sm" onclick="window.AdministracaoView.visualizarLog('${dataValida}', '${nomeArquivo}')">VER LOG</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-logs-tbody').innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async visualizarLog(dataLog, nomeArquivo, nivelFiltro = 'TODOS', buscaFiltro = '') {
    const ident = nomeArquivo || dataLog || 'hoje';
    try {
      const queryParams = new URLSearchParams({
        arquivo: ident,
        nivel: nivelFiltro,
        limit: '300'
      });
      if (buscaFiltro) queryParams.set('busca', buscaFiltro);

      const endpoint = `${window.CONFIG.ENDPOINTS.ADMINISTRACAO.LOG_VIEWER}?${queryParams.toString()}`;
      const res = await window.api.get(endpoint);

      const totalArquivo = res.total_linhas_arquivo ?? (res.linhas ? res.linhas.length : 0);
      const totalFiltradas = res.total_linhas_filtradas ?? totalArquivo;
      const linhas = res.linhas || [];

      let linhasHtml = '';
      if (linhas.length === 0) {
        linhasHtml = `<div style="padding: 20px; text-align: center; color: var(--color-steel-gray);">Nenhum evento registrado para os filtros selecionados.</div>`;
      } else {
        linhas.forEach((item) => {
          let cor = '#e4e2e1'; // Padrão
          let bg = 'transparent';
          let tagBadge = '';

          const cat = item.categoria || (item.is_error ? 'ERROR' : item.is_security ? 'SEGURANCA' : item.is_audit ? 'AUDIT' : item.is_warning ? 'WARNING' : item.is_http ? 'HTTP' : 'INFO');

          if (cat === 'ERROR') {
            cor = '#ffb4ab';
            bg = 'rgba(147, 0, 10, 0.2)';
            tagBadge = '<span style="background: #93000a; color: #ffdad6; padding: 1px 5px; font-size: 10px; font-weight: 700; margin-right: 6px;">ERROR</span>';
          } else if (cat === 'SEGURANCA') {
            cor = '#c2c6d2';
            bg = 'rgba(100, 104, 114, 0.2)';
            tagBadge = '<span style="background: #2c3139; color: #e4e8f4; padding: 1px 5px; font-size: 10px; font-weight: 700; margin-right: 6px;">SEGURANÇA</span>';
          } else if (cat === 'AUDIT') {
            cor = '#72cf88';
            bg = 'rgba(0, 77, 37, 0.15)';
            tagBadge = '<span style="background: #004d25; color: #b7f4c5; padding: 1px 5px; font-size: 10px; font-weight: 700; margin-right: 6px;">AUDIT</span>';
          } else if (cat === 'WARNING') {
            cor = '#ffb59c';
            tagBadge = '<span style="background: #5c1a00; color: #ffe2d9; padding: 1px 5px; font-size: 10px; font-weight: 700; margin-right: 6px;">WARN</span>';
          } else if (cat === 'HTTP') {
            cor = '#a5a9b4';
            tagBadge = '<span style="background: #1c1b1b; border: 1px solid #44474e; color: #c4c7c5; padding: 0 4px; font-size: 10px; font-weight: 600; margin-right: 6px;">HTTP</span>';
          } else if (cat === 'DEBUG') {
            cor = '#8e9199';
            tagBadge = '<span style="background: #131313; border: 1px solid #71797e; color: #a5a9b4; padding: 0 4px; font-size: 10px; font-weight: 600; margin-right: 6px;">DEBUG</span>';
          } else {
            cor = '#e4e2e1';
            tagBadge = '<span style="background: #282a2d; color: #c4c7c5; padding: 1px 4px; font-size: 10px; font-weight: 600; margin-right: 6px;">INFO</span>';
          }

          linhasHtml += `
            <div style="background-color: ${bg}; padding: 5px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 12px; line-height: 1.5; font-family: 'JetBrains Mono', monospace; word-break: break-all;">
              <span style="color: var(--color-steel-gray); margin-right: 8px; user-select: none;">#${item.linha_numero || ''}</span>
              ${tagBadge}
              <span style="color: ${cor};">${window.EMCUtils.escapeHtml(item.conteudo)}</span>
            </div>
          `;
        });
      }

      window.EMCUtils.openModal({
        title: `LOG DO SERVIDOR - ${ident.toUpperCase()} (${totalFiltradas} de ${totalArquivo} eventos)`,
        size: 'xl',
        hideFooter: true,
        content: `
          <div style="margin-bottom: 12px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; background-color: var(--color-surface-container); padding: 10px; border: 1px solid var(--color-steel-gray);">
            <div style="display: flex; gap: 6px; align-items: center;">
              <label style="font-size: 12px; font-family: 'JetBrains Mono', monospace;">CATEGORIA / NÍVEL:</label>
              <select id="log-modal-nivel" class="form-control" style="width: 250px; height: 32px; font-size: 12px; padding: 2px 8px;">
                <option value="TODOS" ${nivelFiltro === 'TODOS' ? 'selected' : ''}>TODOS OS EVENTOS</option>
                <option value="AUDIT" ${nivelFiltro === 'AUDIT' ? 'selected' : ''}>[AUDIT] AUDITORIA E MUTAÇÕES</option>
                <option value="SEGURANCA" ${nivelFiltro === 'SEGURANCA' || nivelFiltro === 'SEGURANÇA' ? 'selected' : ''}>[SEGURANÇA] ACESSOS E BLOQUEIOS</option>
                <option value="ERROR" ${nivelFiltro === 'ERROR' ? 'selected' : ''}>[ERROR] ERROS E FALHAS</option>
                <option value="WARNING" ${nivelFiltro === 'WARNING' ? 'selected' : ''}>[WARNING] AVISOS E ALERTAS</option>
                <option value="HTTP" ${nivelFiltro === 'HTTP' ? 'selected' : ''}>[HTTP] TRÁFEGO DE REQUISIÇÕES WEB</option>
                <option value="INFO" ${nivelFiltro === 'INFO' ? 'selected' : ''}>[INFO] OPERAÇÕES INFORMATIVAS</option>
                <option value="DEBUG" ${nivelFiltro === 'DEBUG' ? 'selected' : ''}>[DEBUG] DETALHES TÉCNICOS</option>
              </select>
            </div>
            <div style="flex: 1; min-width: 200px;">
              <input type="text" id="log-modal-busca" class="form-control" placeholder="Filtrar por texto, usuário, entidade ou IP..." value="${window.EMCUtils.escapeHtml(buscaFiltro)}" style="height: 32px; font-size: 12px;">
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-filtrar-log-modal" style="height: 32px;">FILTRAR</button>
          </div>

          <div id="log-modal-linhas-container" style="background-color: var(--color-surface-container-lowest); padding: 8px; border: 1px solid var(--color-steel-gray); max-height: 520px; overflow-y: auto;">
            ${linhasHtml}
          </div>
        `
      });

      document.getElementById('btn-filtrar-log-modal')?.addEventListener('click', () => {
        const novoNivel = document.getElementById('log-modal-nivel')?.value || 'TODOS';
        const novaBusca = document.getElementById('log-modal-busca')?.value || '';
        this.visualizarLog(dataLog, nomeArquivo, novoNivel, novaBusca);
      });

      document.getElementById('log-modal-busca')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          const novoNivel = document.getElementById('log-modal-nivel')?.value || 'TODOS';
          const novaBusca = document.getElementById('log-modal-busca')?.value || '';
          this.visualizarLog(dataLog, nomeArquivo, novoNivel, novaBusca);
        }
      });
    } catch (e) {
      window.EMCUtils.showToast(e.message || 'Erro ao abrir arquivo de log.', 'error');
    }
  },

  // ==========================================================================
  // 5. PAINEL DE LIXEIRA & RESTAURAÇÃO (100% SOFT DELETE)
  // ==========================================================================
  async renderLixeira(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">AUDITORIA DE REGISTROS INATIVADOS COM RESTAURAÇÃO LÓGICA EM 1 CLIQUE</p>
          </div>
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <input type="text" id="filtro-lixeira-busca" class="form-control" placeholder="BUSCAR POR NOME, PLACA, ID OU DETALHES..." style="max-width: 360px;">
            <select id="filtro-lixeira-entidade" class="form-control" style="width: 320px;">
              <option value="" selected>TODAS AS ENTIDADES (HISTÓRICO COMPLETO)</option>
              <option value="clientes">CLIENTES / FORNECEDORES</option>
              <option value="equipamentos">EQUIPAMENTOS / VEÍCULOS</option>
              <option value="orcamentos">ORÇAMENTOS</option>
              <option value="faturas">FATURAS</option>
              <option value="itens">INSUMOS / ITENS</option>
              <option value="produtos">PRODUTOS BOM</option>
              <option value="lancamentos">LANÇAMENTOS FINANCEIROS</option>
              <option value="documentos_compra">NOTAS FISCAIS DE COMPRA</option>
              <option value="contas_bancarias">CONTAS BANCÁRIAS</option>
              <option value="cartoes">CARTÕES CORPORATIVOS</option>
              <option value="categorias_financeiras">CATEGORIAS FINANCEIRAS</option>
              <option value="meios_pagamento">MEIOS DE PAGAMENTO</option>
              <option value="regras_pagamento">REGRAS DE PAGAMENTO</option>
              <option value="dicionario_uom">UNIDADES DE MEDIDA (UOM)</option>
              <option value="dicionario_atributos">ATRIBUTOS TÉCNICOS</option>
              <option value="usuarios">USUÁRIOS / COLABORADORES</option>
            </select>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>TIPO / ENTIDADE</th>
              <th>IDENTIFICAÇÃO DO REGISTRO</th>
              <th>DELETADO EM</th>
              <th>DELETADO POR</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-lixeira-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    const selectEntidade = document.getElementById('filtro-lixeira-entidade');
    const inputBusca = document.getElementById('filtro-lixeira-busca');

    selectEntidade?.addEventListener('change', () => this.carregarLixeira());
    inputBusca?.addEventListener('input', () => this.carregarLixeira());

    await this.carregarLixeira();
  },

  async carregarLixeira() {
    const tbody = document.getElementById('lista-lixeira-tbody');
    if (!tbody) return;

    const entidade = document.getElementById('filtro-lixeira-entidade')?.value || '';
    const busca = document.getElementById('filtro-lixeira-busca')?.value.trim() || '';

    try {
      const params = new URLSearchParams();
      if (entidade) params.append('entidade', entidade);
      if (busca) params.append('busca', busca);

      const qs = params.toString() ? `?${params.toString()}` : '';
      const endpoint = `${window.CONFIG.ENDPOINTS.ADMINISTRACAO.LIXEIRA}${qs}`;
      const res = await window.api.get(endpoint);
      const lista = res.itens || res.results || (Array.isArray(res) ? res : []);

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Lixeira vazia para os filtros selecionados.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item) => {
        const podeRestaurar = item.pode_restaurar !== false;
        const btnRestaurar = podeRestaurar
          ? `<button class="btn btn-primary btn-sm" onclick="window.AdministracaoView.restaurarRegistro('${item.entidade}', ${item.id})">RESTAURAR</button>`
          : '<span class="status-chip warning" style="font-size: 11px;">SEM PERMISSÃO</span>';

        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td><span class="status-chip info" style="font-size: 11px;">${window.EMCUtils.escapeHtml(item.entidade_nome || item.entidade)}</span></td>
            <td>
              <strong>${window.EMCUtils.escapeHtml(item.identificador || 'Registro')}</strong>
              ${item.detalhes ? `<div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 2px;">${window.EMCUtils.escapeHtml(item.detalhes)}</div>` : ''}
            </td>
            <td class="mono-text">${window.EMCUtils.formatarDataHoraPtBr(item.deleted_at)}</td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.deleted_by_nome || 'Sistema')}</td>
            <td style="text-align: right; white-space: nowrap;">
              ${btnRestaurar}
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async restaurarRegistro(entidade, id) {
    try {
      const endpoint = window.CONFIG.ENDPOINTS.ADMINISTRACAO.RESTAURAR_LIXEIRA.replace('{entidade}', entidade).replace('{id}', id);
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast(`Registro #${id} restaurado com sucesso!`, 'success');
      this.carregarLixeira();
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
