self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.map((key) => caches.delete(key)));
      const clientsList = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      for (const client of clientsList) {
        client.postMessage({ type: "MEINAUSFLUG_PWA_DISABLED" });
      }
    } catch (e) {}
    await self.registration.unregister();
    self.clients.claim();
  })());
});

self.addEventListener("fetch", () => {});
