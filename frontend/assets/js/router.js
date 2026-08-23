/**
 * EMC Soldas - Roteador Client-Side SPA (Single Page Application)
 * Gerenciamento de rotas, interceptação de autenticação e proteção RBAC.
 */

class SpaRouter {
  constructor() {
    this.routes = {};
    this.currentRoute = null;

    window.addEventListener('hashchange', () => this.handleRouteChange());
  }

  register(path, options) {
    this.routes[path] = options;
  }

  async handleRouteChange() {
    const hash = window.location.hash || '#/dashboard';
    const [pathWithQuery] = hash.split('?');
    const path = pathWithQuery.replace('#', '') || '/dashboard';
    const queryString = hash.includes('?') ? hash.split('?')[1] : '';
    const params = Object.fromEntries(new URLSearchParams(queryString));

    const routeConfig = this.routes[path] || this.routes['/dashboard'];

    if (!routeConfig) {
      console.warn(`[Router] Rota não encontrada: ${path}`);
      return;
    }

    // 1. Verificação de Autenticação
    if (routeConfig.requiresAuth !== false) {
      if (!window.auth.isAuthenticated) {
        const isAuthed = await window.auth.checkAuth();
        if (!isAuthed) {
          window.location.hash = '#/login';
          return;
        }
      }
    }

    // 2. Verificação de Permissão RBAC (se especificada)
    if (routeConfig.permission && !window.auth.hasPermission(routeConfig.permission)) {
      window.EMCUtils?.showToast('Acesso negado: Seu perfil não possui permissão para este módulo.', 'warning');
      window.location.hash = '#/dashboard';
      return;
    }

    // 3. Atualiza Título da Topbar
    const pageTitleEl = document.getElementById('page-title');
    if (pageTitleEl && routeConfig.title) {
      pageTitleEl.textContent = routeConfig.title;
    }

    // 4. Atualiza Item Ativo na Sidebar
    this.updateActiveSidebarNav(path);

    // 5. Renderiza a View no Container #app-root
    const appRoot = document.getElementById('app-root');
    if (appRoot && typeof routeConfig.handler === 'function') {
      try {
        await routeConfig.handler(appRoot, params);
      } catch (err) {
        console.error(`[Router Error] Falha ao renderizar rota ${path}:`, err);
        appRoot.innerHTML = `
          <div class="alert-banner alert-danger">
            <strong>Ocorreu um erro ao carregar esta tela:</strong> ${window.EMCUtils?.escapeHtml(err.message || 'Erro inesperado.')}
          </div>
        `;
      }
    }

    this.currentRoute = path;
  }

  updateActiveSidebarNav(currentPath) {
    document.querySelectorAll('.sidebar-nav .nav-item').forEach((item) => {
      const route = item.dataset.route;
      if (route && currentPath.includes(route)) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });
  }

  navigate(path) {
    window.location.hash = `#${path.startsWith('/') ? path : '/' + path}`;
  }
}

window.router = new SpaRouter();

// Registro das Rotas da Aplicação
window.router.register('/login', {
  title: 'Acesso ao Sistema',
  requiresAuth: false,
  handler: (container) => window.AuthView.renderLogin(container)
});

window.router.register('/forgot-password', {
  title: 'Recuperação de Senha',
  requiresAuth: false,
  handler: (container) => window.AuthView.renderForgotPassword(container)
});

window.router.register('/reset-password', {
  title: 'Definir Nova Senha',
  requiresAuth: false,
  handler: (container, params) => window.AuthView.renderResetPassword(container, params)
});

window.router.register('/activate-account', {
  title: 'Ativação de Conta',
  requiresAuth: false,
  handler: (container, params) => window.AuthView.renderActivateAccount(container, params)
});

window.router.register('/dashboard', {
  title: 'Painel de Operações',
  requiresAuth: true,
  handler: (container) => window.DashboardView.render(container)
});

window.router.register('/orcamentos', {
  title: 'Orçamentos Comerciais',
  requiresAuth: true,
  permission: 'acesso_comercial',
  handler: (container) => window.OrcamentosView.render(container)
});

window.router.register('/faturamento', {
  title: 'Faturamento & Conta Corrente',
  requiresAuth: true,
  permission: 'acesso_comercial',
  handler: (container) => window.FaturamentoView.render(container)
});

window.router.register('/tesouraria', {
  title: 'Tesouraria & Caixa Real',
  requiresAuth: true,
  permission: 'acesso_tesouraria',
  handler: (container) => window.FinanceiroView.render(container)
});

window.router.register('/conciliacao', {
  title: 'Conciliação Bancária',
  requiresAuth: true,
  permission: 'acesso_tesouraria',
  handler: (container) => window.ConciliacaoView.render(container)
});

window.router.register('/compras', {
  title: 'Compras & Notas de Entrada',
  requiresAuth: true,
  permission: 'acesso_compras',
  handler: (container) => window.ComprasView.render(container)
});

window.router.register('/catalogo', {
  title: 'Catálogo & Motor BOM',
  requiresAuth: true,
  permission: 'gestao_catalogo',
  handler: (container) => window.CatalogoView.render(container)
});

window.router.register('/clientes', {
  title: 'Clientes & Equipamentos',
  requiresAuth: true,
  handler: (container) => window.CadastrosView.render(container)
});

window.router.register('/relatorios', {
  title: 'Central Analítica & Relatórios',
  requiresAuth: true,
  permission: 'visao_relatorios',
  handler: (container) => window.RelatoriosView.render(container)
});

window.router.register('/administracao', {
  title: 'Central do Administrador',
  requiresAuth: true,
  permission: 'configuracoes_globais',
  handler: (container) => window.AdministracaoView.render(container)
});
