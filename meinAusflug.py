from __future__ import annotations

import datetime
import urllib.parse

import requests
import streamlit as st

from app.theme import apply_theme
from core.config import APP_NAME, APP_URL
from core.storage import (
    get_chat_unread_count,
    get_checklist_unread_count,
    load_db,
    mark_read,
    normalize_data,
    save_db,
)
from ui.ui_chat import render_chat
from ui.ui_checklist import render_checklist
from ui.ui_costs import render_costs
from ui.ui_info import render_info
from ui.ui_photos import render_photos

st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")
apply_theme()

data = normalize_data(load_db())


def weather_icon_from_code(code: int) -> str:
    mapping = {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️",
        45: "🌫️", 48: "🌫️",
        51: "🌦️", 53: "🌦️", 55: "🌦️",
        56: "🌨️", 57: "🌨️",
        61: "🌧️", 63: "🌧️", 65: "🌧️",
        66: "🌨️", 67: "🌨️",
        71: "❄️", 73: "❄️", 75: "❄️", 77: "❄️",
        80: "🌦️", 81: "🌧️", 82: "⛈️",
        85: "🌨️", 86: "❄️",
        95: "⛈️", 96: "⛈️", 99: "⛈️",
    }
    return mapping.get(int(code), "🌡️")


@st.cache_data(show_spinner=False, ttl=1800)
def get_weather_data(city: str):
    city = (city or "").strip()
    if not city:
        return None
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=de&format=json",
            timeout=8,
        ).json()
        if not geo.get("results"):
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        return requests.get(
            (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
                "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                "&forecast_days=7&timezone=Europe%2FBerlin"
            ),
            timeout=8,
        ).json()
    except Exception:
        return None


if "user" not in st.session_state:
    st.title("🌍 MeinAusflug")
    preset_name = st.query_params.get("invite_name", "") or ""
    user_name = st.text_input("Dein Name", value=preset_name)
    if st.button("Starten", use_container_width=True) and user_name.strip():
        st.session_state.user = user_name.strip()
        st.rerun()
    st.stop()

user = st.session_state.user
trips = data.get("trips", {})
if not trips:
    st.warning("Noch keine Reisen vorhanden")
    st.stop()

trip_keys = list(trips.keys())
qp_trip = st.query_params.get("trip")

if "selected_trip" not in st.session_state:
    st.session_state.selected_trip = qp_trip if qp_trip in trips else trip_keys[0]
elif st.session_state.selected_trip not in trips:
    st.session_state.selected_trip = trip_keys[0]

# widget state kept separate from application state
if "trip_selector" not in st.session_state or st.session_state.trip_selector not in trips:
    st.session_state.trip_selector = st.session_state.selected_trip

def _on_trip_change():
    st.session_state.selected_trip = st.session_state.trip_selector

with st.sidebar:
    st.markdown(f"### 👋 {user}")
    st.selectbox(
        "Reise wählen",
        trip_keys,
        key="trip_selector",
        on_change=_on_trip_change,
    )

trip_key = st.session_state.selected_trip
trip = trips[trip_key]

participants = trip.setdefault("participants", {})
participant_added = False
if user not in participants:
    participants[user] = {
        "display_name": user,
        "role": "member",
        "joined_at": datetime.datetime.now().isoformat(),
    }
    participant_added = True
else:
    participants[user].setdefault("display_name", user)
    participants[user].setdefault("role", "member")
    participants[user].setdefault("joined_at", datetime.datetime.now().isoformat())

trip.setdefault("details", {})
trip.setdefault("messages", [])
trip.setdefault("tasks", [])
trip.setdefault("expenses", [])
trip.setdefault("images", [])
trip.setdefault("last_read", {})

if participant_added:
    save_db(data)

role = participants.get(user, {}).get("role", "member")
chat_unread = get_chat_unread_count(trip, user)
check_unread = get_checklist_unread_count(trip, user)

with st.sidebar:
    st.caption(f"Rolle: {role}")
    st.caption("Einladungslink und Teilnehmerverwaltung findest du unter „Infos“.")
    if st.button("Neu laden", use_container_width=True):
        st.rerun()

st.title(f"🌍 {trip.get('name', trip_key)}")

summary_cols = st.columns(4)
summary_cols[0].metric("Teilnehmer", len(participants))
summary_cols[1].metric("Nachrichten", len(trip.get("messages", [])), delta=f"{chat_unread} neu" if chat_unread else None)
summary_cols[2].metric("Checkliste", len(trip.get("tasks", [])), delta=f"{check_unread} neu" if check_unread else None)
summary_cols[3].metric("Kosten", f"{sum(float(e.get('amount', 0) or 0) for e in trip.get('expenses', [])):.2f} €")

sections = [
    "Übersicht",
    f"Chat • {chat_unread}" if chat_unread else "Chat",
    f"Checkliste • {check_unread}" if check_unread else "Checkliste",
    "Kosten",
    "Fotos",
    "Infos",
]
selected = st.radio("Bereich", sections, horizontal=True, label_visibility="collapsed")

details = trip.setdefault("details", {})

if selected.startswith("Übersicht"):
    st.subheader("📍 Reiseübersicht")
    can_edit = role == "admin"

    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("Reiseziel", details.get("destination", ""), disabled=not can_edit)
        city = st.text_input("Ort", details.get("city", ""), disabled=not can_edit)
        street = st.text_input("Straße", details.get("street", ""), disabled=not can_edit)
        homepage = st.text_input("Homepage", details.get("homepage", ""), disabled=not can_edit)
    with c2:
        start = st.date_input("Start", value=datetime.date.fromisoformat(details.get("start_date", str(datetime.date.today()))) if details.get("start_date") else datetime.date.today(), disabled=not can_edit)
        end = st.date_input("Ende", value=datetime.date.fromisoformat(details.get("end_date", str(datetime.date.today()))) if details.get("end_date") else datetime.date.today(), disabled=not can_edit)
        meet_date = st.date_input("Treffpunkt Datum", value=datetime.date.fromisoformat(details.get("meet_date", str(datetime.date.today()))) if details.get("meet_date") else datetime.date.today(), disabled=not can_edit)
        meet_time = st.time_input("Treffpunkt Uhrzeit", value=datetime.time.fromisoformat(details.get("meet_time", "18:00")) if details.get("meet_time") else datetime.time(18, 0), disabled=not can_edit)

    extra = st.text_area("Zusätzliche Infos", details.get("extra", ""), disabled=not can_edit)

    new_details = {
        **details,
        "destination": destination,
        "city": city,
        "street": street,
        "homepage": homepage,
        "start_date": str(start),
        "end_date": str(end),
        "meet_date": str(meet_date),
        "meet_time": meet_time.strftime("%H:%M"),
        "extra": extra,
    }
    if can_edit and new_details != details:
        trip["details"] = new_details
        save_db(data)

    address = ", ".join(x for x in [street, city] if x.strip())
    if address:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
        st.link_button("🗺️ Adresse in Google Maps öffnen", maps_url, use_container_width=True)

    st.caption(f"Treffpunkt: {meet_date.strftime('%d.%m.%Y')} um {meet_time.strftime('%H:%M')} Uhr")

    weather_city = city or destination
    weather = get_weather_data(weather_city)
    if weather_city:
        st.subheader("🌤️ Wetter")
        if weather:
            current = weather.get("current", {})
            current_icon = weather_icon_from_code(current.get("weather_code", 0))
            wc1, wc2, wc3, wc4 = st.columns([1.15, 1, 1, 1])
            with wc1:
                st.markdown(f"<div style='font-size:64px; line-height:1;'>{current_icon}</div>", unsafe_allow_html=True)
            with wc2:
                st.metric("Aktuell", f"{current.get('temperature_2m', '–')}°C")
            with wc3:
                st.metric("Gefühlt", f"{current.get('apparent_temperature', '–')}°C")
            with wc4:
                st.metric("Wind", f"{current.get('wind_speed_10m', '–')} km/h")
        else:
            st.info("Wetterdaten aktuell nicht verfügbar.")

elif selected.startswith("Chat"):
    mark_read(trip, user, "chat")
    save_db(data)
    render_chat(data, trip_key, user)

elif selected.startswith("Checkliste"):
    mark_read(trip, user, "checklist")
    save_db(data)
    render_checklist(data, trip_key, user)

elif selected == "Kosten":
    render_costs(data, trip_key, user)

elif selected == "Fotos":
    render_photos(data, trip_key)

else:
    render_info(data, trip_key, user, APP_URL)
