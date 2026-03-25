# FIXED VERSION with full features

import datetime
import urllib.parse
import requests
import streamlit as st

from app.theme import apply_theme
from core.config import APP_NAME
from core.storage import load_db, normalize_data, save_db
from ui.ui_chat import render_chat
from ui.ui_checklist import render_checklist
from ui.ui_costs import render_costs
from ui.ui_info import render_info
from ui.ui_photos import render_photos

st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")
apply_theme()

data = normalize_data(load_db())

if "user" not in st.session_state:
    st.title("🌍 MeinAusflug")
    name = st.text_input("Dein Name")
    if st.button("Starten") and name.strip():
        st.session_state.user = name.strip()
        st.rerun()
    st.stop()

user = st.session_state.user
trips = data.get("trips", {})

if not trips:
    st.warning("Noch keine Reisen vorhanden")
    st.stop()

trip_key = st.sidebar.selectbox("Reise wählen", list(trips.keys()))
trip = trips[trip_key]

participants = trip.setdefault("participants", {})
if user not in participants:
    participants[user] = {"display_name": user}
    save_db(data)

st.title(f"🌍 {trip.get('name', trip_key)}")

def unread_count(items, user):
    last = st.session_state.get(f"last_seen_{user}", "")
    return len([i for i in items if i.get("time","") > last])

chat_unread = unread_count(trip.get("messages", []), user)
tasks_unread = unread_count(trip.get("tasks", []), user)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Übersicht",
    f"Chat ({chat_unread})" if chat_unread else "Chat",
    f"Checkliste ({tasks_unread})" if tasks_unread else "Checkliste",
    "Kosten",
    "Fotos",
    "Infos"
])

with tab1:
    st.subheader("📍 Reiseübersicht")

    details = trip.setdefault("details", {})

    destination = st.text_input("Urlaub", details.get("destination", ""))
    city = st.text_input("Ort", details.get("city", ""))
    street = st.text_input("Straße", details.get("street", ""))

    start = st.date_input("Start", value=datetime.date.today())
    end = st.date_input("Ende", value=datetime.date.today())

    meet_date = st.date_input("Treffpunkt Datum", value=datetime.date.today())
    meet_time = st.time_input("Treffpunkt Uhrzeit", value=datetime.datetime.now().time())

    details.update({
        "destination": destination,
        "city": city,
        "street": street,
        "start_date": str(start),
        "end_date": str(end),
        "meet_date": str(meet_date),
        "meet_time": str(meet_time)
    })
    save_db(data)

    if city:
        try:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1",
                timeout=5
            ).json()

            if geo.get("results"):
                lat = geo["results"][0]["latitude"]
                lon = geo["results"][0]["longitude"]

                weather = requests.get(
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min",
                    timeout=5
                ).json()

                st.subheader("🌤️ Wetter")
                for i in range(min(3, len(weather["daily"]["time"]))):
                    st.write(
                        weather["daily"]["time"][i],
                        f"{weather['daily']['temperature_2m_max'][i]}° / {weather['daily']['temperature_2m_min'][i]}°"
                    )
        except:
            st.info("Wetter nicht verfügbar")

with tab2:
    render_chat(data, trip_key, user)

with tab3:
    render_checklist(data, trip_key, user)

with tab4:
    render_costs(data, trip_key, user)

with tab5:
    render_photos(data, trip_key)

with tab6:
    render_info(data, trip_key)
