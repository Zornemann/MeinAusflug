from __future__ import annotations

import datetime
import urllib.parse
from typing import Iterable

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
        45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️",
        56: "🌨️", 57: "🌨️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
        66: "🌨️", 67: "🌨️", 71: "❄️", 73: "❄️", 75: "❄️", 77: "❄️",
        80: "🌦️", 81: "🌧️", 82: "⛈️", 85: "🌨️", 86: "❄️",
        95: "⛈️", 96: "⛈️", 99: "⛈️",
    }
    return mapping.get(int(code), "🌡️")


def _first_non_empty(values: Iterable[str]) -> str:
    for value in values:
        if value and str(value).strip():
            return str(value).strip()
    return ""


def _parse_time(value: str | None) -> datetime.time:
    raw = (value or "18:00").strip()
    try:
        return datetime.time.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.datetime.strptime(raw, "%H:%M").time()
        except ValueError:
            return datetime.time(18, 0)


def _weather_headers() -> dict[str, str]:
    app_url = (APP_URL or "").strip()
    user_agent = f"{APP_NAME}/1.0"
    if app_url:
        user_agent = f"{user_agent} ({app_url})"
    return {"User-Agent": user_agent}


@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def geocode_location(*location_candidates: str):
    queries: list[str] = []
    for candidate in location_candidates:
        cleaned = (candidate or "").strip()
        if cleaned and cleaned not in queries:
            queries.append(cleaned)

    if not queries:
        return None, "Keine Ortsangabe vorhanden"

    headers = _weather_headers()

    try:
        for query in queries:
            geo_response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": query,
                    "count": 3,
                    "language": "de",
                    "format": "json",
                },
                headers=headers,
                timeout=10,
            )
            geo_response.raise_for_status()
            geo = geo_response.json()
            results = geo.get("results") or []
            if results:
                first = results[0]
                chosen_location = ", ".join(
                    str(part).strip()
                    for part in [
                        first.get("name"),
                        first.get("admin1"),
                        first.get("country"),
                    ]
                    if part and str(part).strip()
                )
                return {
                    "latitude": first["latitude"],
                    "longitude": first["longitude"],
                    "source_query": query,
                    "source_location": chosen_location,
                }, None

        return None, f"Kein Geocoding-Treffer für: {', '.join(queries)}"
    except requests.RequestException as exc:
        return None, f"Geocoding-Fehler: {type(exc).__name__}: {exc}"
    except Exception as exc:
        return None, f"Allgemeiner Geocoding-Fehler: {type(exc).__name__}: {exc}"


@st.cache_data(show_spinner=False, ttl=60 * 60)
def fetch_weather_forecast(latitude: float, longitude: float):
    headers = _weather_headers()

    try:
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 3,
                "timezone": "Europe/Berlin",
            },
            headers=headers,
            timeout=10,
        )

        if weather_response.status_code == 429:
            return None, "Wetterdienst-Limit erreicht. Bitte später erneut versuchen."

        weather_response.raise_for_status()
        return weather_response.json(), None
    except requests.RequestException as exc:
        return None, f"Anfragefehler: {type(exc).__name__}: {exc}"
    except Exception as exc:
        return None, f"Allgemeiner Wetter-Fehler: {type(exc).__name__}: {exc}"


def get_weather_data(*location_candidates: str):
    geo_result, geo_error = geocode_location(*location_candidates)
    if not geo_result:
        return None, geo_error

    weather_data, weather_error = fetch_weather_forecast(
        geo_result["latitude"],
        geo_result["longitude"],
    )
    if not weather_data:
        return None, weather_error

    return {
        "source_query": geo_result.get("source_query"),
        "source_location": geo_result.get("source_location"),
        "data": weather_data,
    }, None

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
initial_trip = qp_trip if qp_trip in trips else trip_keys[0]

if "selected_trip" not in st.session_state or st.session_state.selected_trip not in trips:
    st.session_state.selected_trip = initial_trip

with st.sidebar:
    st.markdown(f"### 👋 {user}")
    trip_key = st.selectbox("Reise wählen", trip_keys, key="selected_trip")
    st.caption("Einladungslink und Teilnehmerverwaltung findest du unter „Infos“.")
    if st.button("Neu laden", use_container_width=True):
        st.rerun()

trip = trips[trip_key]

participants = trip.setdefault("participants", {})
needs_save = False
if user not in participants:
    participants[user] = {
        "display_name": user,
        "role": "member",
        "joined_at": datetime.datetime.now().isoformat(),
    }
    needs_save = True
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

if needs_save:
    save_db(data)

role = participants.get(user, {}).get("role", "member")
chat_unread = get_chat_unread_count(trip, user)
check_unread = get_checklist_unread_count(trip, user)

st.title(f"🌍 {trip.get('name', trip_key)}")

section_options = ["overview", "chat", "checklist", "costs", "photos", "infos"]
section_labels = {
    "overview": "Übersicht",
    "chat": f"Chat{' • ' + str(chat_unread) if chat_unread else ''}",
    "checklist": f"Checkliste{' • ' + str(check_unread) if check_unread else ''}",
    "costs": "Kosten",
    "photos": "Fotos",
    "infos": "Infos",
}
selected = st.radio(
    "Bereich",
    section_options,
    horizontal=True,
    label_visibility="collapsed",
    key="top_nav",
    format_func=lambda option: section_labels.get(option, option),
)

summary_cols = st.columns(4)
summary_cols[0].metric("Teilnehmer", len(participants))
summary_cols[1].metric("Nachrichten", len(trip.get("messages", [])), delta=f"{chat_unread} neu" if chat_unread else None)
summary_cols[2].metric("Checkliste", len(trip.get("tasks", [])), delta=f"{check_unread} neu" if check_unread else None)
summary_cols[3].metric("Kosten", f"{sum(float(e.get('amount', 0) or 0) for e in trip.get('expenses', [])):.2f} €")

details = trip.setdefault("details", {})

if selected == "overview":
    st.subheader("📍 Reiseübersicht")
    can_edit = role == "admin"
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("Reiseziel", details.get("destination", ""), disabled=not can_edit)
        city = st.text_input("Ort", details.get("city", ""), disabled=not can_edit)
        street = st.text_input("Straße", details.get("street", ""), disabled=not can_edit)
        postal_code = st.text_input("Postleitzahl", details.get("plz", ""), disabled=not can_edit)
        homepage = st.text_input("Homepage", details.get("homepage", ""), disabled=not can_edit)
    with c2:
        start = st.date_input("Start", value=datetime.date.fromisoformat(details.get("start_date", str(datetime.date.today()))) if details.get("start_date") else datetime.date.today(), disabled=not can_edit)
        end = st.date_input("Ende", value=datetime.date.fromisoformat(details.get("end_date", str(datetime.date.today()))) if details.get("end_date") else datetime.date.today(), disabled=not can_edit)
        meet_date = st.date_input("Treffpunkt Datum", value=datetime.date.fromisoformat(details.get("meet_date", str(datetime.date.today()))) if details.get("meet_date") else datetime.date.today(), disabled=not can_edit)
        meet_time = st.time_input("Treffpunkt Uhrzeit", value=_parse_time(details.get("meet_time")), disabled=not can_edit)

    extra = st.text_area("Zusätzliche Infos", details.get("extra", ""), disabled=not can_edit)

    new_details = {
        **details,
        "destination": destination,
        "city": city,
        "street": street,
        "plz": postal_code,
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

    address = ", ".join(x for x in [street, postal_code, city] if x.strip())
    if address:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
        st.link_button("🗺️ Adresse in Google Maps öffnen", maps_url, use_container_width=True)

    if homepage:
        st.link_button("🌐 Homepage öffnen", homepage, use_container_width=True)

    st.caption(f"Treffpunkt: {meet_date.strftime('%d.%m.%Y')} um {meet_time.strftime('%H:%M')} Uhr")

    weather_queries = [
        " ".join(x for x in [postal_code, city] if x.strip()),
        city,
        destination,
    ]
    weather_label = _first_non_empty([city, destination, address])
    weather_result, weather_error = get_weather_data(*weather_queries)
    if weather_label:
        st.subheader("🌤️ Wetter")
        if weather_result:
            weather = weather_result["data"]
            source_query = weather_result.get("source_query")
            source_location = weather_result.get("source_location")
            if source_query:
                source_text = source_location or source_query
                st.caption(f"Gefunden über: {source_text}")

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

            daily = weather.get("daily", {})
            dates = daily.get("time", [])[:3]
            max_temps = daily.get("temperature_2m_max", [])[:3]
            min_temps = daily.get("temperature_2m_min", [])[:3]
            rain = daily.get("precipitation_probability_max", [])[:3]
            weather_codes = daily.get("weather_code", [])[:3]
            if dates:
                st.caption(f"Vorhersage für {weather_label}")
                forecast_cols = st.columns(len(dates))
                for idx, day in enumerate(dates):
                    icon = weather_icon_from_code(weather_codes[idx]) if idx < len(weather_codes) else "🌡️"
                    max_temp = max_temps[idx] if idx < len(max_temps) else "–"
                    min_temp = min_temps[idx] if idx < len(min_temps) else "–"
                    rain_value = rain[idx] if idx < len(rain) else "–"
                    with forecast_cols[idx]:
                        st.markdown(
                            f"<div class='me-card'><strong>{datetime.date.fromisoformat(day).strftime('%a, %d.%m.')}</strong><br>{icon} {max_temp}° / {min_temp}°<br><span class='me-soft'>Regen: {rain_value}%</span></div>",
                            unsafe_allow_html=True,
                        )
        else:
            st.warning(weather_error or f"Wetterdaten für {weather_label} aktuell nicht verfügbar.")

elif selected == "chat":
    if chat_unread:
        mark_read(trip, user, "chat")
        save_db(data)
    render_chat(data, trip_key, user)

elif selected == "checklist":
    if check_unread:
        mark_read(trip, user, "checklist")
        save_db(data)
    render_checklist(data, trip_key, user)

elif selected == "costs":
    render_costs(data, trip_key, user)

elif selected == "photos":
    render_photos(data, trip_key)

else:
    render_info(data, trip_key, user, APP_URL)
