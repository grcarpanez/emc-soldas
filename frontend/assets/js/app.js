/**
 * Aplicação Principal PWA (EMC Soldas).
 * Inicialização, Registro de Service Worker e Gestão de Ociosidade (Soft Lock).
 */

document.addEventListener('DOMContentLoaded', () => {
  console.log('EMC Soldas - Sistema Inicializado (Industrial Integrity PWA)');

  // 1. Registro do Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((reg) => console.log('[PWA] Service Worker registrado com sucesso:', reg.scope))
        .catch((err) => console.warn('[PWA] Falha ao registrar Service Worker:', err));
    });
  }

  // 2. Temporizador de Ociosidade (Soft Lock - 30 Minutos)
  let inactivityTimer = null;
  const INACTIVITY_LIMIT_MS = (window.CONFIG?.SOFT_LOCK_TIMEOUT_MINUTES || 30) * 60 * 1000;

  function resetInactivityTimer() {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    inactivityTimer = setTimeout(() => {
      triggerSoftLock();
    }, INACTIVITY_LIMIT_MS);
  }

  function triggerSoftLock() {
    console.warn('[Segurança] Tempo de ociosidade atingido (30 min). Ativando Soft Lock.');
    window.dispatchEvent(new CustomEvent('auth:soft_lock'));
  }

  // Monitora interações do usuário para renovar o timer
  ['mousedown', 'mousemove', 'keydown', 'touchstart', 'scroll'].forEach((event) => {
    window.addEventListener(event, resetInactivityTimer, { passive: true });
  });

  resetInactivityTimer();

  // 3. Ouvintes de Eventos Globais de Autenticação
  window.addEventListener('auth:unauthorized', () => {
    console.log('[Auth] Redirecionando para Login...');
    // A ser integrado na Fase 3
  });

  window.addEventListener('auth:soft_lock', () => {
    console.log('[Auth] Exibindo modal de destravamento com PIN de 6 dígitos...');
    // A ser integrado na Fase 3
  });
});
