const CACHE_NAME = 'ble-viz-cache-v1';
const ASSETS = [
  '/ui/',
  '/ui/index.html',
  '/ui/manifest.json',
  // your CSS/JS assets:
  'https://cdn.plot.ly/plotly-latest.min.js',
  '/ui/service-worker.js'
  // plus any bundled JS/CSS you serve
];

// install event: cache shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

// activate event: clean up old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => {
        if (k !== CACHE_NAME) return caches.delete(k);
      }))
    )
  );
});

// fetch event: network-first for dynamic, cache fallback
self.addEventListener('fetch', e => {
  e.respondWith(
    fetch(e.request)
      .then(res => {
        // optionally update cache
        return res;
      })
      .catch(() =>
        caches.match(e.request)
      )
  );
});
