/**
 * EMC Soldas - Views de Autenticação (Login, Recuperação de Senha, Ativação)
 */

window.AuthView = {
  renderLogin(container) {
    container.innerHTML = `
      <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="card" style="width: 100%; max-width: 440px; border: 1px solid var(--color-steel-gray); border-top: 3px solid var(--color-rust-orange);">
          <div class="card-header text-center" style="display: block; border-bottom: 1px solid var(--color-steel-gray);">
            <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 8px;">
              <div style="width: 16px; height: 16px; background-color: var(--color-rust-orange);"></div>
              <h2 style="font-size: 22px; font-weight: 700; letter-spacing: 0.05em;">EMC SOLDAS</h2>
            </div>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">SISTEMA INTEGRADO DE GESTÃO INDUSTRIAL</p>
          </div>

          <form id="form-login" style="padding-top: 16px;">
            <div class="form-group">
              <label class="form-label" for="login-email">E-mail do Colaborador</label>
              <input type="email" id="login-email" class="form-control" placeholder="colaborador@emcsoldas.com.br" required data-no-transform="true" autofocus>
            </div>

            <div class="form-group">
              <label class="form-label" for="login-password">Senha de Acesso</label>
              <input type="password" id="login-password" class="form-control" placeholder="••••••••" required data-no-transform="true">
            </div>

            <div id="login-error-alert" class="alert-banner alert-danger" style="display: none; margin-bottom: 16px;"></div>

            <div style="margin-bottom: 16px; display: flex; justify-content: flex-end;">
              <a href="#/forgot-password" class="mono-text" style="font-size: 12px; color: var(--color-rust-orange); text-decoration: none;">Esqueci minha senha</a>
            </div>

            <button type="submit" id="btn-submit-login" class="btn btn-primary w-100" style="height: 46px;">
              ENTRAR NO SISTEMA
            </button>
          </form>
        </div>
      </div>
    `;

    const form = document.getElementById('form-login');
    const emailInput = document.getElementById('login-email');
    const passInput = document.getElementById('login-password');
    const errorAlert = document.getElementById('login-error-alert');
    const submitBtn = document.getElementById('btn-submit-login');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorAlert.style.display = 'none';
      submitBtn.disabled = true;
      submitBtn.textContent = 'AUTENTICANDO...';

      const email = emailInput.value.trim().toLowerCase();
      const password = passInput.value;

      const res = await window.auth.login(email, password);

      if (res.success) {
        window.EMCUtils.showToast('Login realizado com sucesso.', 'success');
        window.location.hash = '#/dashboard';
      } else {
        errorAlert.textContent = res.message || 'Credenciais inválidas ou conta bloqueada.';
        errorAlert.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.textContent = 'ENTRAR NO SISTEMA';
      }
    });
  },

  renderForgotPassword(container) {
    container.innerHTML = `
      <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="card" style="width: 100%; max-width: 440px; border: 1px solid var(--color-steel-gray); border-top: 3px solid var(--color-rust-orange);">
          <div class="card-header text-center" style="display: block;">
            <h2 style="font-size: 20px; font-weight: 700;">RECUPERAÇÃO DE ACESSO</h2>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 4px;">RECEBA UM CÓDIGO DE 8 DÍGITOS NO SEU E-MAIL</p>
          </div>

          <form id="form-forgot" style="padding-top: 16px;">
            <div class="form-group">
              <label class="form-label" for="forgot-email">E-mail Cadastrado</label>
              <input type="email" id="forgot-email" class="form-control" placeholder="colaborador@emcsoldas.com.br" required data-no-transform="true" autofocus>
            </div>

            <div id="forgot-error-alert" class="alert-banner alert-danger" style="display: none;"></div>

            <button type="submit" id="btn-submit-forgot" class="btn btn-primary w-100" style="margin-bottom: 12px;">
              ENVIAR CÓDIGO DE RECUPERAÇÃO
            </button>

            <a href="#/login" class="btn btn-secondary w-100 text-center">VOLTAR AO LOGIN</a>
          </form>
        </div>
      </div>
    `;

    const form = document.getElementById('form-forgot');
    const emailInput = document.getElementById('forgot-email');
    const submitBtn = document.getElementById('btn-submit-forgot');
    const errorAlert = document.getElementById('forgot-error-alert');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      submitBtn.disabled = true;
      submitBtn.textContent = 'ENVIANDO...';
      errorAlert.style.display = 'none';

      const email = emailInput.value.trim().toLowerCase();

      try {
        await window.api.post(window.CONFIG.ENDPOINTS.AUTH.FORGOT_PASSWORD, { email });
        window.EMCUtils.showToast('Código de 8 dígitos enviado com sucesso para o seu e-mail.', 'success');
        window.location.hash = `#/reset-password?email=${encodeURIComponent(email)}`;
      } catch (err) {
        errorAlert.textContent = err.message || 'Erro ao solicitar código.';
        errorAlert.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.textContent = 'ENVIAR CÓDIGO DE RECUPERAÇÃO';
      }
    });
  },

  renderResetPassword(container, params = {}) {
    const defaultEmail = params.email || '';

    container.innerHTML = `
      <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="card" style="width: 100%; max-width: 440px; border: 1px solid var(--color-steel-gray); border-top: 3px solid var(--color-rust-orange);">
          <div class="card-header text-center" style="display: block;">
            <h2 style="font-size: 20px; font-weight: 700;">DEFINIR NOVA SENHA</h2>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 4px;">DIGITE O CÓDIGO RECEBIDO E SUA NOVA SENHA</p>
          </div>

          <form id="form-reset" style="padding-top: 16px;">
            <div class="form-group">
              <label class="form-label" for="reset-email">E-mail</label>
              <input type="email" id="reset-email" class="form-control" value="${window.EMCUtils.escapeHtml(defaultEmail)}" required data-no-transform="true">
            </div>

            <div class="form-group">
              <label class="form-label" for="reset-code">Código de 8 Dígitos</label>
              <input type="text" id="reset-code" class="form-control mono-text" maxlength="8" placeholder="Ex: 84920184" required data-no-transform="true">
            </div>

            <div class="form-group">
              <label class="form-label" for="reset-password">Nova Senha</label>
              <input type="password" id="reset-password" class="form-control" placeholder="••••••••" required data-no-transform="true">
            </div>

            <div id="reset-error-alert" class="alert-banner alert-danger" style="display: none;"></div>

            <button type="submit" id="btn-submit-reset" class="btn btn-primary w-100" style="margin-bottom: 12px;">
              CONFIRMAR NOVA SENHA
            </button>

            <a href="#/login" class="btn btn-secondary w-100 text-center">VOLTAR AO LOGIN</a>
          </form>
        </div>
      </div>
    `;

    const form = document.getElementById('form-reset');
    const submitBtn = document.getElementById('btn-submit-reset');
    const errorAlert = document.getElementById('reset-error-alert');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      submitBtn.disabled = true;
      submitBtn.textContent = 'PROCESSANDO...';
      errorAlert.style.display = 'none';

      const email = document.getElementById('reset-email').value.trim().toLowerCase();
      const code = document.getElementById('reset-code').value.trim();
      const new_password = document.getElementById('reset-password').value;

      try {
        await window.api.post(window.CONFIG.ENDPOINTS.AUTH.RESET_PASSWORD, { email, code, new_password });
        window.EMCUtils.showToast('Senha redefinida com sucesso! Faça login com suas novas credenciais.', 'success');
        window.location.hash = '#/login';
      } catch (err) {
        errorAlert.textContent = err.message || 'Código inválido ou expirado.';
        errorAlert.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.textContent = 'CONFIRMAR NOVA SENHA';
      }
    });
  },

  renderActivateAccount(container, params = {}) {
    const token = params.token || '';

    container.innerHTML = `
      <div style="min-height: 80vh; display: flex; align-items: center; justify-content: center; padding: 20px;">
        <div class="card" style="width: 100%; max-width: 440px; border: 1px solid var(--color-steel-gray); border-top: 3px solid var(--color-rust-orange);">
          <div class="card-header text-center" style="display: block;">
            <h2 style="font-size: 20px; font-weight: 700;">PRIMEIRO ACESSO</h2>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 4px;">DEFINA SUA SENHA DE ACESSO AO SISTEMA</p>
          </div>

          <form id="form-activate" style="padding-top: 16px;">
            <div class="form-group">
              <label class="form-label" for="activate-password">Criar Nova Senha</label>
              <input type="password" id="activate-password" class="form-control" placeholder="••••••••" required data-no-transform="true" autofocus>
            </div>

            <div class="form-group">
              <label class="form-label" for="activate-pin">Criar PIN de Destravamento (6 dígitos)</label>
              <input type="password" id="activate-pin" class="form-control mono-text" maxlength="6" placeholder="000000" required data-no-transform="true">
            </div>

            <div id="activate-error-alert" class="alert-banner alert-danger" style="display: none;"></div>

            <button type="submit" id="btn-submit-activate" class="btn btn-primary w-100" style="margin-bottom: 12px;">
              ATIVAR CONTA E ENTRAR
            </button>
          </form>
        </div>
      </div>
    `;

    const form = document.getElementById('form-activate');
    const submitBtn = document.getElementById('btn-submit-activate');
    const errorAlert = document.getElementById('activate-error-alert');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      submitBtn.disabled = true;
      submitBtn.textContent = 'ATIVANDO...';
      errorAlert.style.display = 'none';

      const password = document.getElementById('activate-password').value;
      const pin = document.getElementById('activate-pin').value.trim();

      if (pin.length !== 6 || !/^\d{6}$/.test(pin)) {
        errorAlert.textContent = 'O PIN deve conter exatamente 6 dígitos numéricos.';
        errorAlert.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.textContent = 'ATIVAR CONTA E ENTRAR';
        return;
      }

      try {
        await window.api.post(window.CONFIG.ENDPOINTS.AUTH.ACTIVATE_ACCOUNT, { token, password, pin });
        window.EMCUtils.showToast('Conta ativada com sucesso! Você já pode acessar o sistema.', 'success');
        window.location.hash = '#/login';
      } catch (err) {
        errorAlert.textContent = err.message || 'Token de ativação inválido ou expirado.';
        errorAlert.style.display = 'flex';
        submitBtn.disabled = false;
        submitBtn.textContent = 'ATIVAR CONTA E ENTRAR';
      }
    });
  }
};
