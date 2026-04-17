from __future__ import annotations

import datetime
from typing import Iterable
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
        45: "🌫️", 48: "🌫️", 51: "🌦️", 53: "🌦️", 55: "🌦️",
        56: "🌨️", 57: "🌨️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
        66: "🌨️", 67: "🌨️", 71: "❄️", 73: "❄️", 75: "❄️", 77: "❄️",
        80: "🌦️", 81: "🌧️", 82: "⛈️", 85: "🌨️", 86: "❄️",
        95: "⛈️", 96: "⛈️", 99: "⛈️",
    }
    return mapping.get(int(code), "🌡️")


def _parse_time(raw: str) -> datetime.time:
    try:
        return datetime.time.fromisoformat(raw)
    except Exception:
        return datetime.time(18, 0)


def _clean_candidates(candidates: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for candidate in candidates:
        value = (candidate or "").strip()
        if value and value not in seen:
            seen.append(value)
    return seen


def _parse_iso_date_or_default(raw: str | None) -> datetime.date:
    try:
        return datetime.date.fromisoformat(str(raw))
    except Exception:
        return datetime.date.today()


def _render_safe_date_input(label: str, value: str, key: str, disabled: bool = False) -> tuple[str, bool]:
    current_date = _parse_iso_date_or_default(value)
    default_text = current_date.isoformat()

    entered = st.text_input(
        label,
        value=default_text,
        key=key,
        disabled=disabled,
        placeholder="YYYY-MM-DD",
        help="Datumsformat: YYYY-MM-DD",
    )

    if disabled:
        return default_text, True

    text = (entered or "").strip()
    if not text:
        st.caption("Bitte Datum im Format YYYY-MM-DD eingeben.")
        return default_text, False

    try:
        parsed = datetime.date.fromisoformat(text)
        return parsed.isoformat(), True
    except ValueError:
        st.caption("Ungültiges Datum. Bitte YYYY-MM-DD verwenden.")
        return default_text, False


@st.cache_data(show_spinner=False, ttl=86400)
def geocode_location(*location_candidates: str):
    queries = _clean_candidates(location_candidates)
    if not queries:
        return None, "Keine Ortsangabe vorhanden"

    headers = {"User-Agent": f"{APP_NAME}/1.0 ({APP_URL})"}

    try:
        for query in queries:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": query, "count": 1, "language": "de", "format": "json"},
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results") or []
            if results:
                first = results[0]
                return {
                    "query": query,
                    "latitude": first["latitude"],
                    "longitude": first["longitude"],
                    "label": first.get("name", query),
                }, None
        return None, f"Kein Geocoding-Treffer für: {queries}"
    except requests.RequestException as exc:
        return None, f"Geocoding-Fehler: {type(exc).__name__}: {exc}"
    except Exception as exc:
        return None, f"Geocoding-Fehler: {type(exc).__name__}: {exc}"


@st.cache_data(show_spinner=False, ttl=21600)
def get_weather_forecast(latitude: float, longitude: float):
    headers = {"User-Agent": f"{APP_NAME}/1.0 ({APP_URL})"}
    try:
        response = requests.get(
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
        if response.status_code == 429:
            return None, "RATE_LIMIT"
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Anfragefehler: {type(exc).__name__}: {exc}"
    except Exception as exc:
        return None, f"Anfragefehler: {type(exc).__name__}: {exc}"


def _weather_cache_key(details: dict) -> str:
    return "|".join(
        [
            str(details.get("postal_code", "")).strip(),
            str(details.get("city", "")).strip(),
            str(details.get("destination", "")).strip(),
            str(details.get("street", "")).strip(),
        ]
    )


def _save_weather_cache(trip: dict, location: dict, weather: dict) -> None:
    trip["weather_cache"] = {
        "location": location,
        "weather": weather,
        "updated_at": datetime.datetime.now().isoformat(timespec="minutes"),
    }


def _get_cached_weather_if_matching(trip: dict, details: dict):
    cache = trip.get("weather_cache") or {}
    if not cache:
        return None
    if cache.get("cache_key") != _weather_cache_key(details):
        return None
    return cache


def _render_weather_block(trip: dict, details: dict, allow_refresh: bool = True) -> None:
    postal_code = details.get("postal_code", "")
    city = details.get("city", "")
    destination = details.get("destination", "")
    weather_label = city or destination or postal_code
    if not weather_label:
        return

    st.subheader("🌤️ Wetter")
    weather_candidates = [f"{postal_code} {city}".strip(), city, destination]
    cache_key = _weather_cache_key(details)
    cached = _get_cached_weather_if_matching(trip, details)

    refresh_clicked = False
    if allow_refresh:
        rc1, rc2 = st.columns([1.6, 5])
        with rc1:
            refresh_clicked = st.button("Wetter aktualisieren", key=f"refresh_weather_{cache_key}", use_container_width=True)

    location = None
    location_error = None

    if refresh_clicked and cached:
        cached = None
        get_weather_forecast.clear()

    if cached:
        location = cached.get("location")
        weather = cached.get("weather")
        updated_at = cached.get("updated_at", "")
        if location:
            st.caption(f"Gespeicherte Wetterdaten für: {location.get('query', weather_label)}")
        if updated_at:
            st.caption(f"Zuletzt aktualisiert: {updated_at}")
        _render_weather_metrics(weather)
        return

    location, location_error = geocode_location(*weather_candidates)
    if not location:
        st.info(location_error or "Wetterdaten aktuell nicht verfügbar.")
        return

    weather, weather_error = get_weather_forecast(location["latitude"], location["longitude"])

    if weather:
        trip["weather_cache"] = {
            "cache_key": cache_key,
            "location": location,
            "weather": weather,
            "updated_at": datetime.datetime.now().isoformat(timespec="minutes"),
        }
        save_db(data)
        st.caption(f"Wetter gefunden über: {location['query']}")
        _render_weather_metrics(weather)
        return

    if weather_error == "RATE_LIMIT":
        cached = _get_cached_weather_if_matching(trip, details)
        if cached:
            updated_at = cached.get("updated_at", "")
            st.info("Wetterdienst hat das Limit erreicht. Es werden die zuletzt gespeicherten Wetterdaten angezeigt.")
            if updated_at:
                st.caption(f"Zuletzt aktualisiert: {updated_at}")
            _render_weather_metrics(cached.get("weather") or {})
        else:
            st.info("Wetterdienst hat das Limit erreicht. Bitte später erneut versuchen.")
        return

    if cached:
        updated_at = cached.get("updated_at", "")
        st.info("Live-Wetter aktuell nicht verfügbar. Es werden die zuletzt gespeicherten Wetterdaten angezeigt.")
        if updated_at:
            st.caption(f"Zuletzt aktualisiert: {updated_at}")
        _render_weather_metrics(cached.get("weather") or {})
        return

    st.info(weather_error or "Wetterdaten aktuell nicht verfügbar.")


def _render_weather_metrics(weather: dict) -> None:
    current = weather.get("current", {})
    current_icon = weather_icon_from_code(current.get("weather_code", 0))
    wc1, wc2, wc3, wc4 = st.columns([1.15, 1, 1, 1])
    with wc1:
        st.markdown(f"<div style='font-size:56px; line-height:1;'>{current_icon}</div>", unsafe_allow_html=True)
    with wc2:
        st.metric("Aktuell", f"{current.get('temperature_2m', '–')}°C")
    with wc3:
        st.metric("Gefühlt", f"{current.get('apparent_temperature', '–')}°C")
    with wc4:
        st.metric("Wind", f"{current.get('wind_speed_10m', '–')} km/h")

    daily = weather.get("daily", {}) or {}
    days = daily.get("time", []) or []
    weather_codes = daily.get("weather_code", []) or []
    temp_max = daily.get("temperature_2m_max", []) or []
    temp_min = daily.get("temperature_2m_min", []) or []
    rain = daily.get("precipitation_probability_max", []) or []

    if days:
        st.markdown("#### Vorschau")
        cols = st.columns(min(3, len(days)))
        for idx, day in enumerate(days[:3]):
            icon = weather_icon_from_code(weather_codes[idx]) if idx < len(weather_codes) else "🌡️"
            max_temp = temp_max[idx] if idx < len(temp_max) else "–"
            min_temp = temp_min[idx] if idx < len(temp_min) else "–"
            rain_value = rain[idx] if idx < len(rain) else "–"
            try:
                label = datetime.date.fromisoformat(day).strftime("%a, %d.%m.")
            except Exception:
                label = str(day)
            with cols[idx]:
                st.markdown(
                    (
                        "<div class='me-card'>"
                        f"<strong>{label}</strong><br>"
                        f"{icon} {max_temp}° / {min_temp}°<br>"
                        f"<span class='me-soft'>Regen: {rain_value}%</span>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )


def _handle_in_app_notifications(trip_key: str, current_chat_unread: int, current_checklist_unread: int) -> None:
    notif = st.session_state.setdefault(
        "notify_settings",
        {
            "chat": True,
            "checklist": True,
        },
    )
    cache = st.session_state.setdefault("notify_cache", {})
    trip_cache = cache.setdefault(trip_key, {"chat": current_chat_unread, "checklist": current_checklist_unread, "initialized": False})

    if not trip_cache.get("initialized"):
        trip_cache["chat"] = current_chat_unread
        trip_cache["checklist"] = current_checklist_unread
        trip_cache["initialized"] = True
        return

    if notif.get("chat", True) and current_chat_unread > trip_cache.get("chat", 0):
        diff = current_chat_unread - trip_cache.get("chat", 0)
        st.toast(f"💬 {diff} neue Chatnachricht{'en' if diff != 1 else ''}", icon="🔔")

    if notif.get("checklist", True) and current_checklist_unread > trip_cache.get("checklist", 0):
        diff = current_checklist_unread - trip_cache.get("checklist", 0)
        st.toast(f"📝 {diff} neue{'r' if diff == 1 else ''} Checklisten-Eintrag{'' if diff == 1 else 'e'}", icon="🔔")

    trip_cache["chat"] = current_chat_unread
    trip_cache["checklist"] = current_checklist_unread


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
    if participants[user].get("role") not in {"admin", "editor", "member", "viewer"}:
        participants[user]["role"] = "member"
    participants[user].setdefault("role", "member")
    participants[user].setdefault("joined_at", datetime.datetime.now().isoformat())

trip.setdefault("details", {})
trip.setdefault("messages", [])
trip.setdefault("tasks", [])
trip.setdefault("expenses", [])
trip.setdefault("images", [])
trip.setdefault("last_read", {})
trip.setdefault("weather_cache", {})

if needs_save:
    save_db(data)

role = participants.get(user, {}).get("role", "member")
chat_unread = get_chat_unread_count(trip, user)
check_unread = get_checklist_unread_count(trip, user)

_handle_in_app_notifications(trip_key, chat_unread, check_unread)

with st.sidebar:
    st.markdown("#### 🔔 Benachrichtigungen")
    notify_settings = st.session_state.setdefault("notify_settings", {"chat": True, "checklist": True})
    notify_settings["chat"] = st.checkbox("Neue Chatnachrichten", value=notify_settings.get("chat", True), key="notify_chat")
    notify_settings["checklist"] = st.checkbox("Neue Checklisten-Einträge", value=notify_settings.get("checklist", True), key="notify_checklist")
    st.caption("Hinweise erscheinen in der App, solange sie geöffnet ist.")
    st.markdown(f"**Rolle:** {role}")

st.title(f"🌍 {trip.get('name', trip_key)}")

nav_items = [
    ("overview", "Übersicht"),
    ("chat", "Chat"),
    ("checklist", "Checkliste"),
    ("costs", "Kosten"),
    ("photos", "Fotos"),
    ("infos", "Infos"),
]
nav_labels = [label for _, label in nav_items]
nav_map = {label: key for key, label in nav_items}
current_key = st.session_state.get("top_nav_key", "overview")
current_label = next((label for key, label in nav_items if key == current_key), "Übersicht")

selected_label = st.radio(
    "Bereich",
    nav_labels,
    horizontal=True,
    label_visibility="collapsed",
    index=nav_labels.index(current_label) if current_label in nav_labels else 0,
)
selected = nav_map[selected_label]
st.session_state.top_nav_key = selected

summary_cols = st.columns(4)
summary_cols[0].metric("Teilnehmer", len(participants))
summary_cols[1].metric("Nachrichten", len(trip.get("messages", [])), delta=f"{chat_unread} neu" if chat_unread else None)
summary_cols[2].metric("Checkliste", len(trip.get("tasks", [])), delta=f"{check_unread} neu" if check_unread else None)
summary_cols[3].metric("Kosten", f"{sum(float(e.get('amount', 0) or 0) for e in trip.get('expenses', [])):.2f} €")

details = trip.setdefault("details", {})

if selected == "overview":
    st.subheader("📍 Reiseübersicht")
    can_edit = role in {"admin", "editor"}
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("Urlaub", details.get("destination", ""), disabled=not can_edit)
        city = st.text_input("Ort", details.get("city", ""), disabled=not can_edit)
        street = st.text_input("Straße", details.get("street", ""), disabled=not can_edit)
        postal_code = st.text_input("Postleitzahl", details.get("postal_code", ""), disabled=not can_edit)
        homepage = st.text_input("Startseite", details.get("homepage", ""), disabled=not can_edit)
    with c2:
        start_date_value, start_ok = _render_safe_date_input(
            "Start",
            details.get("start_date", str(datetime.date.today())),
            key=f"start_safe_{trip_key}",
            disabled=not can_edit,
        )
        end_date_value, end_ok = _render_safe_date_input(
            "Ende",
            details.get("end_date", str(datetime.date.today())),
            key=f"end_safe_{trip_key}",
            disabled=not can_edit,
        )
        meet_date_value, meet_ok = _render_safe_date_input(
            "Treffpunkt Datum",
            details.get("meet_date", str(datetime.date.today())),
            key=f"meet_safe_{trip_key}",
            disabled=not can_edit,
        )
        meet_time = st.time_input("Treffpunkt Uhrzeit", value=_parse_time(details.get("meet_time", "18:00")), disabled=not can_edit)

    extra = st.text_area("Zusätzliche Informationen", details.get("extra", ""), disabled=not can_edit)

    dates_valid = start_ok and end_ok and meet_ok

    new_details = {
        **details,
        "destination": destination,
        "city": city,
        "street": street,
        "postal_code": postal_code,
        "homepage": homepage,
        "start_date": start_date_value,
        "end_date": end_date_value,
        "meet_date": meet_date_value,
        "meet_time": meet_time.strftime("%H:%M"),
        "extra": extra,
    }
    if can_edit and dates_valid and new_details != details:
        trip["details"] = new_details
        save_db(data)

    address = ", ".join(x for x in [street, postal_code, city] if x.strip())
    if address:
        maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
        st.link_button("🗺️ Adresse in Google Maps öffnen", maps_url, use_container_width=True)

    if homepage:
        st.link_button("🌐 Homepage öffnen", homepage, use_container_width=True)

    try:
        meet_date_display = datetime.date.fromisoformat(meet_date_value).strftime("%d.%m.%Y")
    except Exception:
        meet_date_display = meet_date_value
    st.caption(f"Treffpunkt: {meet_date_display} um {meet_time.strftime('%H:%M')} Uhr")

    _render_weather_block(trip, details, allow_refresh=True)

elif selected == "chat":
    if chat_unread:
        mark_read(trip, user, "chat")
        save_db(data)
        st.session_state.setdefault("notify_cache", {}).setdefault(trip_key, {})["chat"] = 0
    render_chat(data, trip_key, user)

elif selected == "checklist":
    if check_unread:
        mark_read(trip, user, "checklist")
        save_db(data)
        st.session_state.setdefault("notify_cache", {}).setdefault(trip_key, {})["checklist"] = 0
    render_checklist(data, trip_key, user)

elif selected == "costs":
    render_costs(data, trip_key, user)

elif selected == "photos":
    render_photos(data, trip_key)

else:
    render_info(data, trip_key, user, APP_URL)
