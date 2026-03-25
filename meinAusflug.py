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
    return len([i for i in items if isinstance(i, dict) and i.get("time", "") > last])


def weather_icon_from_code(code: int) -> str:
    mapping = {
        0: "☀️",
        1: "🌤️",
        2: "⛅",
        3: "☁️",
        45: "🌫️",
        48: "🌫️",
        51: "🌦️",
        53: "🌦️",
        55: "🌦️",
        56: "🌨️",
        57: "🌨️",
        61: "🌧️",
        63: "🌧️",
        65: "🌧️",
        66: "🌨️",
        67: "🌨️",
        71: "❄️",
        73: "❄️",
        75: "❄️",
        77: "❄️",
        80: "🌦️",
        81: "🌧️",
        82: "⛈️",
        85: "🌨️",
        86: "❄️",
        95: "⛈️",
        96: "⛈️",
        99: "⛈️",
    }
    return mapping.get(int(code), "🌡️")


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
    homepage = st.text_input("Homepage", details.get("homepage", ""))

    start = st.date_input(
        "Start",
        value=datetime.date.fromisoformat(details.get("start_date", str(datetime.date.today())))
        if details.get("start_date") else datetime.date.today()
    )
    end = st.date_input(
        "Ende",
        value=datetime.date.fromisoformat(details.get("end_date", str(datetime.date.today())))
        if details.get("end_date") else datetime.date.today()
    )

    meet_date = st.date_input(
        "Treffpunkt Datum",
        value=datetime.date.fromisoformat(details.get("meet_date", str(datetime.date.today())))
        if details.get("meet_date") else datetime.date.today()
    )
    default_time = details.get("meet_time", "18:00")
    try:
        parsed_time = datetime.time.fromisoformat(default_time)
    except Exception:
        parsed_time = datetime.time(hour=18, minute=0)
    meet_time = st.time_input("Treffpunkt Uhrzeit", value=parsed_time)

    details.update({
        "destination": destination,
        "city": city,
        "street": street,
        "homepage": homepage,
        "start_date": str(start),
        "end_date": str(end),
        "meet_date": str(meet_date),
        "meet_time": meet_time.strftime("%H:%M"),
    })
    save_db(data)

    if city:
        try:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=de&format=json",
                timeout=8,
            ).json()

            if geo.get("results"):
                lat = geo["results"][0]["latitude"]
                lon = geo["results"][0]["longitude"]

                weather = requests.get(
                    (
                        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                        "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
                        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                        "&forecast_days=7&timezone=Europe%2FBerlin"
                    ),
                    timeout=8,
                ).json()

                st.subheader("🌤️ Wetter")

                current = weather.get("current", {})
                current_code = current.get("weather_code", 0)
                current_icon = weather_icon_from_code(current_code)

                c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
                with c1:
                    st.markdown(f"<div style='font-size:64px; line-height:1;'>{current_icon}</div>", unsafe_allow_html=True)
                with c2:
                    st.metric("Aktuell", f"{current.get('temperature_2m', '–')}°C")
                with c3:
                    st.metric("Gefühlt", f"{current.get('apparent_temperature', '–')}°C")
                with c4:
                    st.metric("Wind", f"{current.get('wind_speed_10m', '–')} km/h")

                daily = weather.get("daily", {})
                dates = daily.get("time", [])
                tmax = daily.get("temperature_2m_max", [])
                tmin = daily.get("temperature_2m_min", [])
                codes = daily.get("weather_code", [])
                rain_prob = daily.get("precipitation_probability_max", [])

                if dates:
                    st.markdown("### 7-Tage-Vorschau")
                    cols = st.columns(7)
                    for i in range(min(7, len(dates))):
                        icon = weather_icon_from_code(codes[i] if i < len(codes) else 0)
                        with cols[i]:
                            try:
                                day_label = datetime.date.fromisoformat(dates[i]).strftime("%a\n%d.%m.")
                            except Exception:
                                day_label = dates[i]
                            st.markdown(f"**{day_label}**")
                            st.markdown(
                                f"<div style='font-size:42px; text-align:center; margin:8px 0 2px 0;'>{icon}</div>",
                                unsafe_allow_html=True,
                            )
                            max_txt = f"{tmax[i]}°" if i < len(tmax) else "–"
                            min_txt = f"{tmin[i]}°" if i < len(tmin) else "–"
                            rain_txt = f"{rain_prob[i]}%" if i < len(rain_prob) else "–"
                            st.caption(f"Max {max_txt}")
                            st.caption(f"Min {min_txt}")
                            st.caption(f"Regen {rain_txt}")
            else:
                st.info("Für diesen Ort konnten keine Wetterdaten gefunden werden.")
        except Exception:
            st.info("Wetterdaten aktuell nicht verfügbar")
    else:
        st.info("Trage einen Ort ein, damit die Wettervorschau angezeigt werden kann.")

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
