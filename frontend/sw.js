/**
 * Service Worker para resiliência offline e cache de assets estáticos
 * Sistema EMC Soldas - Industrial Integrity PWA
 */

const CACHE_NAME = 'emc-soldas-v1';
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/assets/css/industrial-integrity.css',
  '/assets/css/layout.css',
  '/assets/js/config.js',
  '/assets/js/api.js',
  '/assets/js/app.js'
];

// Instalação: Cache dos assets essenciais
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pré-carregando assets estáticos...');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Service Worker] Falha ao pré-carregar alguns assets estáticos:', err);
      });
    })
  );
  self.skipWaiting();
});

// Ativação: Limpeza de caches obsoletos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removendo cache antigo:', key);
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Interceptação de requisições: Network-First com fallback para Cache
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Requisições para a API REST (/api/) são sempre Network-First (sem cache estático bruto)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({
            status: 'offline',
            message: 'Sem conexão com o servidor da oficina. Operação offline.'
          }),
          {
            headers: { 'Content-Type': 'application/json' },
            status: 503
          }
        );
      })
    );
    return;
  }

  // Requisições de arquivos estáticos: Cache-First ou Network-First com fallback
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Atualiza o cache em segundo plano (Stale-While-Revalidate)
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, networkResponse);
            });
          }
        }).catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((networkResponse) => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }

        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return networkResponse;
      }).catch(() => {
        // Fallback para o index.html em navegação
        if (event.request.mode === 'navigate') {
          return caches.match('/');
        }
      });
    })
  );
});
