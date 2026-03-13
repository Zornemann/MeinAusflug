import streamlit as st
import time

def auto_refresh(interval: int = 5):
    """Einfaches Live-Refresh.
    Wichtig: setzt force_reload=True, damit die App beim nächsten Run wirklich wieder load_db() zieht
    (und nicht nur den Session-State weiter nutzt).
    """
    if "auto_refresh_enabled" not in st.session_state:
        st.session_state.auto_refresh_enabled = True

    enabled = st.sidebar.toggle("🔄 Live-Chat", value=st.session_state.auto_refresh_enabled)
    st.session_state.auto_refresh_enabled = enabled

    if not enabled:
        return

    now = time.time()
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = now
        return

    if now - st.session_state.last_refresh >= interval:
        st.session_state.last_refresh = now
        st.session_state.force_reload = True
        st.rerun()
