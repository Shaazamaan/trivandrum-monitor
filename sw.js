const CACHE_NAME = 'hashcovets-v1';
const ASSETS = [
    './',
    './index.html',
    './manifest.json',
    './logo-icon.png',
    './logo-full.png',
    './icon-192.png',
    './icon-512.png'
];

self.addEventListener('install', (e) => {
    self.skipWaiting(); // Force new service worker to activate immediately
    e.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(clients.claim()); // Take control of open tabs immediately
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((response) => response || fetch(e.request))
    );
});
