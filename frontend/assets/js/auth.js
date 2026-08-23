/**
 * EMC Soldas - Módulo de Autenticação, Gestão de Sessão, PIN e RBAC
 */

class AuthManager {
  constructor() {
    this.user = null;
    this.isAuthenticated = false;
    this.isSoftLocked = false;
    this.inactivityTimer = null;
    this.failedPinAttempts = 0;
    this.inactivityTimeoutMs = (window.CONFIG?.SOFT_LOCK_TIMEOUT_MINUTES || 30) * 60 * 1000;

    this.initEventListeners();
  }

  initEventListeners() {
    // Eventos de atividade do usuário para resetar timer de ociosidade
    const userEvents = ['mousedown', 'mousemove', 'keydown', 'touchstart', 'scroll'];
    userEvents.forEach((ev) => {
      window.addEventListener(ev, () => this.resetInactivityTimer(), { passive: true });
    });

    // Evento de desautenticação global (401)
    window.addEventListener('auth:unauthorized', () => {
      this.handleUnauthorized();
    });

    // Evento de acesso negado (403)
    window.addEventListener('auth:forbidden', () => {
      window.EMCUtils?.showToast('Acesso negado. Você não possui permissão para esta operação.', 'warning');
    });

    // Evento de throttling (429)
    window.addEventListener('api:throttled', () => {
      window.EMCUtils?.showToast('Limite de requisições atingido. Por favor, aguarde alguns instantes.', 'warning');
    });
  }

  resetInactivityTimer() {
    if (!this.isAuthenticated || this.isSoftLocked) return;

    if (this.inactivityTimer) {
      clearTimeout(this.inactivityTimer);
    }

    this.inactivityTimer = setTimeout(() => {
      this.triggerSoftLock();
    }, this.inactivityTimeoutMs);
  }

  triggerSoftLock() {
    if (!this.isAuthenticated || this.isSoftLocked) return;
    this.isSoftLocked = true;
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    this.showPinModal();
  }

  showPinModal() {
    const modalRoot = document.getElementById('modal-root');
    if (!modalRoot) return;

    modalRoot.innerHTML = `
      <div class="modal-overlay modal-soft-lock-overlay" id="soft-lock-modal">
        <div class="modal-card modal-size-sm text-center" style="border: 2px solid var(--color-rust-orange);">
          <div class="modal-header justify-center" style="border-bottom: 1px solid var(--color-steel-gray);">
            <div style="width: 14px; height: 14px; background-color: var(--color-rust-orange); margin-right: 8px;"></div>
            <h3 class="modal-title">[SISTEMA TRAVADO - SOFT LOCK]</h3>
          </div>
          <div class="modal-body" style="padding: 24px 16px;">
            <p style="color: var(--color-on-surface-variant); font-size: 14px; margin-bottom: 16px;">
              Sessão protegida por 30 min de ociosidade.<br>
              Digite seu <strong>PIN de 6 dígitos</strong> para destravar a tela.
            </p>

            <div class="form-group" style="max-width: 220px; margin: 0 auto 16px auto;">
              <input 
                type="password" 
                id="soft-lock-pin-input" 
                class="form-control text-center mono-text" 
                style="font-size: 24px; letter-spacing: 8px; height: 48px;" 
                maxlength="6" 
                placeholder="******" 
                autocomplete="off"
                autofocus
              >
            </div>

            <div id="pin-error-msg" class="mono-text" style="color: var(--color-error); font-size: 12px; margin-bottom: 16px; min-height: 18px;"></div>

            <div style="display: flex; flex-direction: column; gap: 8px;">
              <button class="btn btn-primary" id="btn-unlock-pin" style="width: 100%;">
                DESTRAVAR TELA
              </button>
              <button class="btn btn-ghost btn-sm" id="btn-soft-lock-logout" style="width: 100%;">
                Sair / Trocar de Usuário
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    const pinInput = document.getElementById('soft-lock-pin-input');
    const unlockBtn = document.getElementById('btn-unlock-pin');
    const logoutBtn = document.getElementById('btn-soft-lock-logout');
    const errorMsg = document.getElementById('pin-error-msg');

    setTimeout(() => { pinInput?.focus(); }, 100);

    const handleUnlock = async () => {
      const pin = pinInput.value.trim();
      if (!pin || pin.length !== 6) {
        errorMsg.textContent = 'O PIN DEVE CONTER EXATAMENTE 6 DÍGITOS.';
        return;
      }

      try {
        unlockBtn.disabled = true;
        unlockBtn.textContent = 'VALIDANDO...';
        await window.api.post(window.CONFIG.ENDPOINTS.AUTH.UNLOCK_PIN, { pin });
        
        // Destravado com sucesso
        this.isSoftLocked = false;
        this.failedPinAttempts = 0;
        modalRoot.innerHTML = '';
        this.resetInactivityTimer();
        window.EMCUtils?.showToast('Tela destravada com sucesso.', 'success');
      } catch (err) {
        this.failedPinAttempts++;
        const restantes = 3 - this.failedPinAttempts;
        if (restantes <= 0 || err.status === 401) {
          // Hard lock acionado pelo backend
          modalRoot.innerHTML = '';
          this.handleUnauthorized('Limite de 3 tentativas de PIN atingido. Sessão encerrada.');
        } else {
          errorMsg.textContent = `PIN INCORRETO. ${restantes} TENTATIVA(S) RESTANTE(S).`;
          pinInput.value = '';
          pinInput.focus();
        }
      } finally {
        unlockBtn.disabled = false;
        unlockBtn.textContent = 'DESTRAVAR TELA';
      }
    };

    unlockBtn?.addEventListener('click', handleUnlock);
    pinInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleUnlock();
    });

    logoutBtn?.addEventListener('click', () => {
      modalRoot.innerHTML = '';
      this.logout();
    });
  }

  async checkAuth() {
    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.AUTH.ME);
      const userData = res.user || res.usuario || (res.id ? res : null);
      if (userData && userData.id) {
        this.user = userData;
        this.isAuthenticated = true;
        this.isSoftLocked = false;
        this.failedPinAttempts = 0;
        this.resetInactivityTimer();
        this.updateUiUserBar();
        return true;
      }
    } catch {
      this.user = null;
      this.isAuthenticated = false;
    }
    return false;
  }

  async login(email, password) {
    try {
      const res = await window.api.post(window.CONFIG.ENDPOINTS.AUTH.LOGIN, { email, password });
      this.user = res.user || res.usuario || (res.id ? res : null);
      this.isAuthenticated = true;
      this.isSoftLocked = false;
      this.failedPinAttempts = 0;
      this.resetInactivityTimer();
      this.updateUiUserBar();
      window.dispatchEvent(new CustomEvent('auth:login_success'));
      return { success: true };
    } catch (err) {
      console.error('[Auth Error Login]:', err);
      return {
        success: false,
        message: err.message || 'Falha ao autenticar.',
        status: err.status
      };
    }
  }

  async logout() {
    try {
      await window.api.post(window.CONFIG.ENDPOINTS.AUTH.LOGOUT, {});
    } catch (e) {
      console.warn('[Logout API error]', e);
    }
    this.user = null;
    this.isAuthenticated = false;
    this.isSoftLocked = false;
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    window.location.hash = '#/login';
    this.updateUiUserBar();
    window.dispatchEvent(new CustomEvent('auth:logged_out'));
  }

  handleUnauthorized(mensagem = 'Sua sessão expirou. Faça login novamente.') {
    this.user = null;
    this.isAuthenticated = false;
    this.isSoftLocked = false;
    if (this.inactivityTimer) clearTimeout(this.inactivityTimer);
    window.location.hash = '#/login';
    this.updateUiUserBar();
    if (mensagem) {
      window.EMCUtils?.showToast(mensagem, 'warning');
    }
  }

  hasPermission(toggleName) {
    if (!this.user) return false;
    const roleUpper = (this.user.role || '').toUpperCase();
    if (roleUpper === 'ADMIN' || this.user.is_admin) return true;
    if (!this.user.permissoes) return false;
    return !!this.user.permissoes[toggleName];
  }

  updateUiUserBar() {
    const userRoleEl = document.getElementById('user-role-badge');
    const userEmailEl = document.getElementById('user-email-display');
    const appSidebar = document.getElementById('app-sidebar');
    const topbarActions = document.getElementById('topbar-actions-container');

    if (this.isAuthenticated && this.user) {
      const roleUpper = (this.user.role || '').toUpperCase();
      const isAdmin = roleUpper === 'ADMIN' || !!this.user.is_admin;

      if (userEmailEl) userEmailEl.textContent = this.user.email;
      if (userRoleEl) {
        userRoleEl.textContent = isAdmin ? 'ADMINISTRADOR' : 'OPERADOR';
        userRoleEl.className = `status-chip ${isAdmin ? 'warning' : 'info'}`;
      }
      if (appSidebar) appSidebar.style.display = 'flex';
      if (topbarActions) topbarActions.style.display = 'flex';

      // Atualiza visibilidade dos menus na sidebar conforme RBAC
      this.updateSidebarPermissions();
    } else {
      if (appSidebar) appSidebar.style.display = 'none';
      if (topbarActions) topbarActions.style.display = 'none';
    }
  }

  updateSidebarPermissions() {
    const roleUpper = (this.user?.role || '').toUpperCase();
    const isAdmin = roleUpper === 'ADMIN' || !!this.user?.is_admin;

    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach((item) => {
      const permission = item.dataset.permission;
      if (!permission) return;

      if (isAdmin || this.hasPermission(permission)) {
        item.style.display = 'flex';
        item.classList.remove('nav-item-disabled');
      } else {
        item.style.display = 'none';
      }
    });
  }
}

window.auth = new AuthManager();
