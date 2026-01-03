const CACHE_NAME = "agenda-ho-v2";

const URLS = [
  "/",
  "/static/manifest.json"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {

  const url = new URL(event.request.url);

  // 🚫 NÃO interceptar POST
  if (event.request.method !== "GET") {
    return;
  }

  // 🚫 NÃO interceptar rotas dinâmicas
  if (
    url.pathname.startsWith("/exportar") ||
    url.pathname.startsWith("/editar-dia")
  ) {
    return;
  }

  // ✅ Cache apenas GET estático
  event.respondWith(
    caches.match(event.request).then(resp => {
      return resp || fetch(event.request);
    })
  );
});
