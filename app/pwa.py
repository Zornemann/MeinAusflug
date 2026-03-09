from __future__ import annotations

import streamlit as st

MANIFEST_CANDIDATES = [
    "/app/static/manifest.json",
    "/static/manifest.json",
    "./app/static/manifest.json",
]
SW_CANDIDATES = [
    "/app/static/service-worker.js",
    "/static/service-worker.js",
    "./app/static/service-worker.js",
]
ICON_192_CANDIDATES = [
    "/app/static/icons/icon-192.png",
    "/static/icons/icon-192.png",
]
ICON_512_CANDIDATES = [
    "/app/static/icons/icon-512.png",
    "/static/icons/icon-512.png",
]


def enable_pwa(app_name: str = "MeinAusflug", theme_color: str = "#0e1117") -> None:
    """Inject PWA and iOS meta tags and register a service worker if static files are reachable."""
    st.components.v1.html(
        f"""
        <script>
        (async function () {{
          const doc = window.parent.document;
          const manifestCandidates = {MANIFEST_CANDIDATES!r};
          const swCandidates = {SW_CANDIDATES!r};
          const icon192Candidates = {ICON_192_CANDIDATES!r};
          const icon512Candidates = {ICON_512_CANDIDATES!r};

          async function findReachable(paths) {{
            for (const path of paths) {{
              try {{
                const response = await fetch(path, {{ method: "GET", cache: "no-store" }});
                if (response.ok) return path;
              }} catch (err) {{}}
            }}
            return null;
          }}

          function upsertMeta(attrs) {{
            const selector = Object.entries(attrs)
              .filter(([k]) => k !== "content")
              .map(([k, v]) => `[{k}="${{String(v).replace(/"/g, '\\"')}}"]`)
              .join("");
            let el = doc.head.querySelector(`meta${{selector}}`);
            if (!el) {{
              el = doc.createElement("meta");
              doc.head.appendChild(el);
            }}
            Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
          }}

          function upsertLink(rel, href, extra = {{}}) {{
            let el = doc.head.querySelector(`link[rel="${{rel}}"]`);
            if (!el) {{
              el = doc.createElement("link");
              el.rel = rel;
              doc.head.appendChild(el);
            }}
            el.href = href;
            Object.entries(extra).forEach(([k, v]) => el.setAttribute(k, v));
          }}

          doc.documentElement.lang = "de";
          doc.documentElement.setAttribute("translate", "no");
          if (doc.body) doc.body.setAttribute("translate", "no");

          upsertMeta({{ name: "theme-color", content: "{theme_color}" }});
          upsertMeta({{ name: "apple-mobile-web-app-capable", content: "yes" }});
          upsertMeta({{ name: "apple-mobile-web-app-status-bar-style", content: "black-translucent" }});
          upsertMeta({{ name: "apple-mobile-web-app-title", content: "{app_name}" }});
          upsertMeta({{ name: "mobile-web-app-capable", content: "yes" }});
          upsertMeta({{ name: "google", content: "notranslate" }});

          const manifestPath = await findReachable(manifestCandidates);
          const icon192Path = await findReachable(icon192Candidates);
          const icon512Path = await findReachable(icon512Candidates);
          const swPath = await findReachable(swCandidates);

          if (manifestPath) upsertLink("manifest", manifestPath);
          if (icon192Path) upsertLink("icon", icon192Path, {{ sizes: "192x192" }});
          if (icon512Path) upsertLink("apple-touch-icon", icon512Path);

          if (swPath && "serviceWorker" in navigator) {{
            try {{
              await navigator.serviceWorker.register(swPath, {{ scope: "/" }});
            }} catch (err) {{
              console.warn("SW registration failed", err);
            }}
          }}
        }})();
        </script>
        """,
        height=0,
    )
