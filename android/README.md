# Android-Wrapper (TWA)

Dieses Projekt ist für **PWA + Trusted Web Activity (Bubblewrap)** vorbereitet.

## Empfohlener Ablauf
1. Streamlit-App online veröffentlichen
2. Eigene Domain oder stabile HTTPS-URL nutzen
3. `manifest.json` und `service-worker.js` prüfen
4. Mit Bubblewrap ein Android-Projekt erzeugen
5. `app-release.aab` für den Play Store bauen

## Bubblewrap
```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://DEINE-DOMAIN/app/static/manifest.json
bubblewrap build
```

## Hinweise
- Package-Name z. B. `com.meinausflug.app`
- Für TWA brauchst du Digital Asset Links auf deiner Domain
- Die URL muss dauerhaft per HTTPS erreichbar sein
