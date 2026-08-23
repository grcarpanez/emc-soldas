/**
 * EMC Soldas - Aplicação Principal SPA / PWA (Industrial Integrity)
 * Inicialização, Registro de Service Worker, Gestão de Conexão e Roteamento.
 */

document.addEventListener('DOMContentLoaded', async () => {
  console.log('[EMC Soldas] Inicializando PWA Industrial Integrity...');

  // 1. Registro do Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => console.log('[PWA] Service Worker ativo no escopo:', reg.scope))
      .catch((err) => console.warn('[PWA] Falha ao registrar Service Worker:', err));
  }

  // 2. Monitoramento de Conexão Online / Offline
  const updateOnlineStatus = () => {
    const statusChip = document.getElementById('network-status-chip');
    if (statusChip) {
      if (navigator.onLine) {
        statusChip.textContent = 'ONLINE';
        statusChip.className = 'status-chip success';
      } else {
        statusChip.textContent = 'OFFLINE (CACHE)';
        statusChip.className = 'status-chip warning';
        window.EMCUtils?.showToast('Você está offline. Operando em modo de contingência local.', 'warning');
      }
    }
  };

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();

  // 3. Botão de Bloqueio Manual (Soft Lock)
  document.getElementById('btn-manual-soft-lock')?.addEventListener('click', () => {
    window.auth.triggerSoftLock();
  });

  // 4. Botão de Logout
  document.getElementById('btn-topbar-logout')?.addEventListener('click', async () => {
    if (confirm('Deseja realmente encerrar sua sessão?')) {
      await window.auth.logout();
    }
  });

  // 5. Toggle de Sidebar para Mobile e Tablet
  const toggleBtn = document.getElementById('btn-toggle-sidebar');
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  const closeSidebar = () => {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('open');
  };

  const openSidebar = () => {
    sidebar?.classList.add('open');
    overlay?.classList.add('open');
  };

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      if (sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });

    overlay?.addEventListener('click', closeSidebar);

    // Fecha a sidebar ao clicar em um link de navegação
    document.querySelectorAll('.sidebar-nav .nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        if (window.innerWidth <= 1024) {
          closeSidebar();
        }
      });
    });
  }

  // 6. Verificação Inicial de Autenticação e Roteamento
  await window.auth.checkAuth();
  await window.router.handleRouteChange();
});

