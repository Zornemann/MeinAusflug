from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from core.config import APP_NAME
from core.storage import save_push_token


def init_push_notifications(user_name: str, trip_id: str):
    """
    Temporarily disabled in the web app.
    Native push will be re-enabled later for the Capacitor build only.
    """
    return


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

st.title(APP_NAME)
st.success("App läuft ✅")

if st.session_state.get("push_token_saved"):
    st.info("Push-Token wurde gespeichert.")

if st.session_state.get("push_token_error"):
    st.warning(f"Push-Token konnte nicht gespeichert werden: {st.session_state['push_token_error']}")

st.write("Diese stabile Debug-Version stellt sicher, dass Render sauber startet.")
st.write("Als Nächstes können die UI-Module schrittweise wieder eingebunden werden.")

with st.expander("Moduldiagnose"):
    checks = {}
    for module_name in (
        "app.chat_engine",
        "ui.ui_chat",
        "ui.ui_info",
        "ui.ui_checklist",
        "ui.ui_costs",
        "ui.ui_photos",
    ):
        try:
            __import__(module_name)
            checks[module_name] = "ok"
        except Exception as exc:
            checks[module_name] = f"Fehler: {exc}"
    st.json(checks)
