// Cache name/version
const CACHE_NAME = 'ble-viz-cache-v1';

// Files to cache (adjust paths if your UI is mounted under /ui/)
const ASSETS = [
    '/index.html',
    '/manifest.json',
    '/service-worker.js',
    // Plotly is loaded from CDN, so no need to cache locally
];

// Install: cache the shell
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_NAME)
        .then(cache => cache.addAll(ASSETS))
        .then(() => self.skipWaiting())
    );
});

// Activate: clean up old caches
self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))
        )
    );
});

// Fetch: try network first, fallback to cache
self.addEventListener('fetch', e => {
    e.respondWith(
        fetch(e.request).catch(() => caches.match(e.request))
    );
});