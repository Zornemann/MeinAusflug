from __future__ import annotations

import datetime
import json
import urllib.parse
from pathlib import Path

import requests
import streamlit as st
from streamlit.components.v1 import html
from streamlit_autorefresh import st_autorefresh

from app.chat_engine import render_online_bar
from app.theme import apply_theme
from core.config import APP_NAME, APP_URL
from core.storage import get_storage_status, load_db, normalize_data, save_db, save_push_token
from ui.ui_chat import render_chat
from ui.ui_checklist import render_checklist
from ui.ui_costs import render_costs
from ui.ui_info import render_info
from ui.ui_photos import render_photos


def init_push_notifications(user_name: str, trip_id: str):
    """
    Registers browser/native push permissions. In a Capacitor Android app, the
    FCM registration token is forwarded back into Streamlit via query params and
    then stored in Supabase through save_push_token().
    """
    state_key = f"push_init_done_{trip_id}_{user_name}"
    if st.session_state.get(state_key):
        return

    payload = json.dumps({"user_name": user_name, "trip_id": trip_id})
    html(
        f"""
        <script>
        (async function () {{
          try {{
            if ("Notification" in window && Notification.permission === "default") {{
              try {{ await Notification.requestPermission(); }} catch (e) {{}}
            }}

            const cap = window.Capacitor;
            const push = cap && cap.Plugins && cap.Plugins.PushNotifications;
            if (!push) return;

            let perm = await push.checkPermissions();
            if (!perm || perm.receive === "prompt") {{
              perm = await push.requestPermissions();
            }}
            if (!perm || perm.receive !== "granted") {{
              console.log("Push permission not granted");
              return;
            }}

            await push.register();

            if (window.__meinausflugPushListenersAdded) return;
            window.__meinausflugPushListenersAdded = true;

            push.addListener("registration", (token) => {{
              try {{
                const u = new URL(window.parent.location.href);
                u.searchParams.set("push_token", token.value || "");
                u.searchParams.set("push_trip", {payload}.trip_id);
                u.searchParams.set("push_user", {payload}.user_name);
                u.searchParams.set("push_platform", "android");
                window.parent.location.href = u.toString();
              }} catch (e) {{
                console.warn("Token redirect failed", e);
              }}
            }});

            push.addListener("registrationError", (err) => {{
              console.warn("Push registration error", err);
            }});

            push.addListener("pushNotificationReceived", (notification) => {{
              try {{
                if ("Notification" in window && Notification.permission === "granted") {{
                  new Notification(notification.title || "MeinAusflug", {{
                    body: notification.body || ""
                  }});
                }}
              }} catch (e) {{}}
            }});

            push.addListener("pushNotificationActionPerformed", (notification) => {{
              console.log("Push action", notification);
            }});
          }} catch (e) {{
            console.warn("Push init failed", e);
          }}
        }})();
        </script>
        """,
        height=0,
    )

    st.session_state[state_key] = True


manifest_path = Path("static/manifest.json")
if st.query_params.get("manifest") == "1" and manifest_path.exists():
    st.json(json.loads(manifest_path.read_text(encoding="utf-8")))
    st.stop()

st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")



def consume_push_token_from_query_params():
    token = (st.query_params.get("push_token") or "").strip()
    trip_id = (st.query_params.get("push_trip") or "").strip()
    user_name = (st.query_params.get("push_user") or "").strip()
    platform = (st.query_params.get("push_platform") or "android").strip()

    if token and trip_id and user_name:
        try:
            save_push_token(user_name=user_name, trip_id=trip_id, token=token, platform=platform)
            st.session_state["push_token_saved"] = True
        except Exception as e:
            st.session_state["push_token_error"] = str(e)
        finally:
            for key in ("push_token", "push_trip", "push_user", "push_platform"):
                try:
                    del st.query_params[key]
                except Exception:
                    pass
consume_push_token_from_query_params()

