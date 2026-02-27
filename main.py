import streamlit as st
from storage import load_db, save_db
from config import APP_NAME
from theme import apply_theme
from live_sync import auto_refresh
from chat_engine import render_chat, chat_input
from dashboard import render_dashboard

st.set_page_config(page_title=APP_NAME, layout="wide")

if "db" not in st.session_state:
    st.session_state.db = load_db()

data = st.session_state.db

if "user" not in st.session_state:
    st.title("Login")
    user = st.text_input("Name")
    if st.button("Start"):
        st.session_state.user = user
        st.session_state.trip = list(data["trips"].keys())[0]
        st.rerun()
    st.stop()

apply_theme()
auto_refresh(5)

trip_name = st.session_state.trip
trip = data["trips"][trip_name]
user = st.session_state.user

st.title(f"🌍 {trip_name}")

render_dashboard(trip)

st.divider()

render_chat(data, trip_name, user)
chat_input(data, trip_name, user)

save_db(data)