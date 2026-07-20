const CACHE_NAME = 'nr1map-v1';
const BASE = '/NR-1Map';

const ARQUIVOS_CACHE = [
  BASE + '/',
  BASE + '/index.html',
  BASE + '/admin.html',
  BASE + '/painel.html',
  BASE + '/usuario.html',
  BASE + '/colaborador.html',
  BASE + '/parceiro.html',
  BASE + '/representantes.html',
  BASE + '/instalar-app.html',
  BASE + '/manifest.json',
  BASE + '/nr1maps logo.png',
  BASE + '/nr1maps logo 512.png',
  BASE + '/cbo-database.js',
  'https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap'
];

// Instalação — cacheia arquivos essenciais
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(ARQUIVOS_CACHE);
    }).catch(function(err) {
      console.log('[SW] Erro ao cachear:', err);
    })
  );
  self.skipWaiting();
});

// Ativação — remove caches antigos
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) { return key !== CACHE_NAME; })
            .map(function(key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

// Fetch — Network first para Firebase, Cache first para assets
self.addEventListener('fetch', function(event) {
  var url = event.request.url;

  // Firebase sempre vai para a rede (dados em tempo real)
  if (url.includes('firestore.googleapis.com') ||
      url.includes('firebase') ||
      url.includes('googleapis.com/identitytoolkit') ||
      url.includes('securetoken.googleapis.com')) {
    return; // deixa o browser resolver normalmente
  }

  event.respondWith(
    caches.match(event.request).then(function(cached) {
      // Network first: tenta buscar versão atualizada
      return fetch(event.request).then(function(response) {
        // Cacheia só respostas válidas de assets estáticos
        if (response && response.status === 200 && event.request.method === 'GET') {
          var clone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(event.request, clone);
          });
        }
        return response;
      }).catch(function() {
        // Sem rede — retorna cache
        return cached || caches.match(BASE + '/index.html');
      });
    })
  );
});

// Mensagem de atualização
self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
