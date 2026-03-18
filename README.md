

## Mobile / PWA

Dieses Projekt ist für eine mobile Nutzung als **PWA** vorbereitet.

- `.streamlit/config.toml` aktiviert statische Dateien
- `static/manifest.json` enthält die PWA-Metadaten
- `static/service-worker.js` registriert einfaches Caching
- `android/README.md` beschreibt den Weg in den Play Store via Bubblewrap/TWA
- `ios/README.md` beschreibt die iPhone-Nutzung als Home-Screen-App

Vor dem Store-Einsatz sollte die App unter einer stabilen HTTPS-URL veröffentlicht werden.
