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
    Temporarily disable native/browser push initialization in the web app.

    Reason:
    The injected HTML/JS push bootstrap caused white-screen / reload-loop issues
    on Render while the web version is starting. The token-consume flow via query
    params below remains in place, so the push setup can be re-enabled later once
    the Capacitor-only path is separated cleanly from the web path.
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

