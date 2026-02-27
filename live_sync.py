import streamlit as st
import time

def auto_refresh(interval: int = 5):
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
        st.rerun()