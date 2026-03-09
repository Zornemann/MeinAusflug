import streamlit as st

def enable_pwa(app_name: str = "MeinAusflug", theme_color: str = "#0e1117"):
    """
    Best-effort PWA: inject manifest + service worker via Blob URLs.
    Installation support depends on hosting & browser policy.
    """
    st.components.v1.html(
        f"""
        <script>
        (function() {{
            const manifest = {{
                "name": "{app_name}",
                "short_name": "{app_name}",
                "start_url": ".",
                "display": "standalone",
                "background_color": "{theme_color}",
                "theme_color": "{theme_color}",
                "icons": []
            }};
            const manifestBlob = new Blob([JSON.stringify(manifest)], {{type: "application/json"}});
            const manifestURL = URL.createObjectURL(manifestBlob);
            let link = document.querySelector('link[rel="manifest"]');
            if (!link) {{
                link = document.createElement('link');
                link.rel = 'manifest';
                document.head.appendChild(link);
            }}
            link.href = manifestURL;

            // Simple SW (cache shell best-effort)
            const swCode = `
                self.addEventListener('install', (e) => {{
                    self.skipWaiting();
                }});
                self.addEventListener('activate', (e) => {{
                    e.waitUntil(self.clients.claim());
                }});
                self.addEventListener('fetch', (e) => {{
                    // passthrough (no aggressive caching)
                }});
            `;
            if ('serviceWorker' in navigator) {{
                const swBlob = new Blob([swCode], {{type: 'text/javascript'}});
                const swURL = URL.createObjectURL(swBlob);
                navigator.serviceWorker.register(swURL).catch(()=>{{}});
            }}
        }})();
        </script>
        """,
        height=0,
    )