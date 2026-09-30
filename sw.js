// Service worker: caches the app + data so it opens instantly and works offline.
// CACHE is stamped with the build id by pipeline/publish.py; a new id on each deploy
// makes browsers install the new version and delete the old cache.
const CACHE = "pg-8f1adc9-1790747023";
const FILES = ["./", "index.html", "styles.css", "app.js", "engine.js", "favicon.svg", "manifest.webmanifest",
  "icon-192.png", "icon-512.png", "data/results.json", "data/merit_map.json", "data/gujarat.json", "data/mcc.json", "data/meta.json"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k.startsWith("pg-") && k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

// cache first for our own files; everything else (e.g. analytics) goes straight to the network
self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // page URLs carry ?app=… params; they all map to the one cached index.html
  const key = req.mode === "navigate" ? "./" : req;
  e.respondWith(caches.match(key, { ignoreSearch: req.mode === "navigate" })
    .then((hit) => hit || fetch(req)));
});
