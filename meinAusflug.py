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
from core.storage import get_storage_status, load_db, normalize_data, save_db
from ui.ui_chat import render_chat
from ui.ui_checklist import render_checklist
from ui.ui_costs import render_costs
from ui.ui_info import render_info
from ui.ui_photos import render_photos


manifest_path = Path("static/manifest.json")
if st.query_params.get("manifest") == "1" and manifest_path.exists():
    st.json(json.loads(manifest_path.read_text(encoding="utf-8")))
    st.stop()

st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

DEFAULT_TRIP_DETAILS = {
    "destination": "",
    "homepage": "",
    "kontakt": "",
    "extra": "",
    "street": "",
    "plz": "",
    "city": "",
    "start_date": str(datetime.date.today()),
    "end_date": str(datetime.date.today()),
    "meet_date": str(datetime.date.today()),
    "meet_time": "18:00",
}

WEATHER_ICONS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌦️", 56: "🌧️", 57: "🌧️",
    61: "🌧️", 63: "🌧️", 65: "🌧️", 66: "🌧️", 67: "🌧️",
    71: "❄️", 73: "❄️", 75: "❄️", 77: "❄️",
    80: "🌦️", 81: "🌧️", 82: "🌧️",
    85: "❄️", 86: "❄️",
    95: "⚡", 96: "⛈️", 99: "⛈️",
}

WEATHER_LABELS = {
    0: "Klar",
    1: "Meist klar",
    2: "Teilweise bewölkt",
    3: "Bewölkt",
    45: "Nebel",
    48: "Raureifnebel",
    51: "Leichter Nieselregen",
    53: "Nieselregen",
    55: "Starker Nieselregen",
    56: "Gefrierender Nieselregen",
    57: "Starker gefrierender Nieselregen",
    61: "Leichter Regen",
    63: "Regen",
    65: "Starker Regen",
    66: "Leichter gefrierender Regen",
    67: "Starker gefrierender Regen",
    71: "Leichter Schneefall",
    73: "Schneefall",
    75: "Starker Schneefall",
    77: "Schneegriesel",
    80: "Leichte Regenschauer",
    81: "Regenschauer",
    82: "Starke Regenschauer",
    85: "Leichte Schneeschauer",
    86: "Starke Schneeschauer",
    95: "Gewitter",
    96: "Gewitter mit Hagel",
    99: "Starkes Gewitter mit Hagel",
}


def create_trip(name: str) -> dict:
    return {
        "name": name,
        "status": "In Planung",
        "participants": {},
        "typing": {},
        "presence": {},
        "messages": [],
        "chat": [],
        "tasks": [],
        "checklist": [],
        "expenses": [],
        "images": [],
        "details": DEFAULT_TRIP_DETAILS.copy(),
        "aliases": [name],
        "last_read": {},
    }


@st.cache_data(show_spinner=False, ttl=1800)
def get_weather_data(city: str):
    city = (city or "").strip()
    if not city:
        return None

    try:
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            f"name={urllib.parse.quote(city)}&count=1&language=de&format=json"
        )
        geo_res = requests.get(geo_url, timeout=10)
        geo_res.raise_for_status()
        geo_data = geo_res.json()
        results = geo_data.get("results") or []
        if not results:
            return None

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
            "weather_code,wind_speed_10m,wind_direction_10m"
            "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,"
            "precipitation_probability_max,sunrise,sunset,wind_speed_10m_max"
            "&timezone=Europe%2FBerlin&forecast_days=5"
        )
        weather_res = requests.get(weather_url, timeout=10)
        weather_res.raise_for_status()
        weather = weather_res.json()

        current = weather.get("current") or {}
        current_code = current.get("weather_code")
        current["icon"] = WEATHER_ICONS.get(current_code, "🌡️")
        current["label"] = WEATHER_LABELS.get(current_code, "Wetter")

        daily = weather.get("daily") or {}
        forecast = []
        times = daily.get("time") or []
        for i, day in enumerate(times[:5]):
            code_list = daily.get("weather_code") or []
            max_list = daily.get("temperature_2m_max") or []
            min_list = daily.get("temperature_2m_min") or []
            rain_list = daily.get("precipitation_sum") or []
            prob_list = daily.get("precipitation_probability_max") or []
            wind_list = daily.get("wind_speed_10m_max") or []
            sunrise_list = daily.get("sunrise") or []
            sunset_list = daily.get("sunset") or []

            code = code_list[i] if i < len(code_list) else None
            forecast.append(
                {
                    "date": day,
                    "max": max_list[i] if i < len(max_list) else "–",
                    "min": min_list[i] if i < len(min_list) else "–",
                    "rain": rain_list[i] if i < len(rain_list) else "–",
                    "rain_prob": prob_list[i] if i < len(prob_list) else "–",
                    "wind_max": wind_list[i] if i < len(wind_list) else "–",
                    "sunrise": sunrise_list[i] if i < len(sunrise_list) else "",
                    "sunset": sunset_list[i] if i < len(sunset_list) else "",
                    "icon": WEATHER_ICONS.get(code, "🌡️"),
                    "label": WEATHER_LABELS.get(code, "Wetter"),
                }
            )

        return {
            "place_name": place.get("name") or city,
            "admin1": place.get("admin1") or "",
            "country": place.get("country") or "",
            "latitude": lat,
            "longitude": lon,
            "current": current,
            "forecast": forecast,
        }
    except Exception:
        return None


def get_trip_choices(data: dict):
    trips = data.get("trips", {})
    seen = set()
    choices = []
    for key, trip in trips.items():
        if not isinstance(trip, dict):
            continue
        trip_id = trip.get("trip_id") or key
        if trip_id in seen:
            continue
        seen.add(trip_id)
        name = trip.get("name") or key
        choices.append((name, key))
    choices.sort(key=lambda x: x[0].lower())
    return choices


def ensure_logged_in():
    if "user" in st.session_state and st.session_state.user:
        return

    st.title(APP_NAME)
    st.subheader("Anmeldung")
    with st.form("login_form"):
        user = st.text_input("Dein Name")
        submitted = st.form_submit_button("Starten", use_container_width=True)
    if submitted and user.strip():
        st.session_state.user = user.strip()
        st.session_state.role = "member"
        st.rerun()
    st.stop()


def load_current_data():
    force_reload = st.session_state.pop("force_reload", False)
    if force_reload or "db" not in st.session_state:
        st.session_state.db = normalize_data(load_db())
    return st.session_state.db


def ensure_participant(trip: dict, user: str):
    participants = trip.setdefault("participants", {})
    if user not in participants or not isinstance(participants.get(user), dict):
        participants[user] = {
            "display_name": user,
            "status": "accepted",
            "joined_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
        }
    else:
        participants[user].setdefault("display_name", user)
        participants[user].setdefault("status", "accepted")
    trip.setdefault("last_read", {})


def _get_last_read(trip: dict, user: str, area: str) -> str:
    lr = trip.setdefault("last_read", {})
    if not isinstance(lr.get(user), dict):
        lr[user] = {"chat": "", "checklist": ""}
    lr[user].setdefault("chat", "")
    lr[user].setdefault("checklist", "")
    return lr[user].get(area, "") or ""


def _set_last_read(trip: dict, user: str, area: str) -> bool:
    now_iso = datetime.datetime.now().replace(microsecond=0).isoformat()
    lr = trip.setdefault("last_read", {})
    if not isinstance(lr.get(user), dict):
        lr[user] = {}
    changed = lr[user].get(area) != now_iso
    lr[user][area] = now_iso
    return changed


def _chat_unread_count(trip: dict, user: str) -> int:
    last_read = _get_last_read(trip, user, "chat")
    unread = 0
    for msg in trip.get("messages", []) or trip.get("chat", []):
        if not isinstance(msg, dict):
            continue
        if msg.get("user") == user:
            continue
        if (msg.get("time") or "") > last_read:
            unread += 1
    return unread


def _task_event_time(task: dict) -> str:
    return task.get("updated_at") or task.get("created_at") or ""


def _task_event_user(task: dict) -> str:
    return task.get("updated_by") or task.get("created_by") or task.get("brought_by") or ""


def _checklist_unread_count(trip: dict, user: str) -> int:
    last_read = _get_last_read(trip, user, "checklist")
    unread = 0
    for task in trip.get("tasks", []) or trip.get("checklist", []):
        if not isinstance(task, dict):
            continue
        if _task_event_user(task) == user:
            continue
        if _task_event_time(task) > last_read:
            unread += 1
    return unread


def _browser_notify(title: str, body: str, key: str):
    safe_title = json.dumps(title)
    safe_body = json.dumps(body)
    html(
        f"""
        <script>
        (async function() {{
          try {{
            if (!('Notification' in window)) return;
            if (Notification.permission === 'granted') {{
              new Notification({safe_title}, {{ body: {safe_body} }});
            }} else if (Notification.permission !== 'denied') {{
              const p = await Notification.requestPermission();
              if (p === 'granted') new Notification({safe_title}, {{ body: {safe_body} }});
            }}
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        key=key,
    )


def _invite_link(trip_name: str) -> str:
    base = (APP_URL or "").rstrip("/")
    trip_param = urllib.parse.quote(trip_name or "")
    return f"{base}/?trip={trip_param}" if base else f"?trip={trip_param}"


def _fmt_time(value: str) -> str:
    if not value:
        return "–"
    try:
        return value.split("T", 1)[1][:5]
    except Exception:
        return value


def _render_weather_section(details: dict):
    weather_city = (details.get("city") or details.get("destination") or "").strip()
    st.markdown("### 🌤️ Wetter")

    if not weather_city:
        st.info("Für die Wettervorschau bitte mindestens Ort oder Reiseziel eintragen.")
        return

    weather = get_weather_data(weather_city)
    if not weather:
        st.warning(f"Für '{weather_city}' konnten aktuell keine Wetterdaten geladen werden.")
        return

    place_bits = [weather.get("place_name"), weather.get("admin1"), weather.get("country")]
    st.caption(", ".join([x for x in place_bits if x]))

    current = weather.get("current") or {}
    current_cols = st.columns(4)
    current_cols[0].metric(
        "Jetzt",
        f'{current.get("temperature_2m", "–")}°C',
        f'gefühlt {current.get("apparent_temperature", "–")}°C' if current.get("apparent_temperature") is not None else None,
    )
    current_cols[1].metric("Luftfeuchte", f'{current.get("relative_humidity_2m", "–")} %')
    current_cols[2].metric("Wind", f'{current.get("wind_speed_10m", "–")} km/h')
    current_cols[3].metric("Wetterlage", current.get("icon", "🌡️"), current.get("label", ""))

    forecast = weather.get("forecast") or []
    if forecast:
        day_cols = st.columns(len(forecast))
        for col, day in zip(day_cols, forecast):
            with col:
                st.metric(day["date"], f'{day["max"]}°C', f'{day["min"]}°C')
                st.caption(f'{day["icon"]} {day["label"]}')
                st.caption(f'Regen: {day["rain"]} mm')
                st.caption(f'Wahrsch.: {day["rain_prob"]} %')
                st.caption(f'Wind max.: {day["wind_max"]} km/h')
                st.caption(f'Sonne: {_fmt_time(day["sunrise"])} / {_fmt_time(day["sunset"])}')


def _render_participant_preview(trip_key: str, trip: dict):
    participants = trip.get("participants", {}) if isinstance(trip.get("participants"), dict) else {}
    with st.expander("👥 Teilnehmer & Einladung", expanded=False):
        if not participants:
            st.info("Noch keine Teilnehmer angelegt. Du kannst sie im Bereich 'Infos' hinzufügen.")
        else:
            names = []
            for uname, pdata in participants.items():
                if isinstance(pdata, dict):
                    names.append((pdata.get("display_name") or uname).strip())
                else:
                    names.append(str(uname))
            st.write(", ".join(sorted([n for n in names if n])))

        invite_url = _invite_link(trip.get("name") or trip_key)
        st.code(invite_url)
        st.caption("Diesen Link kannst du an Teilnehmer weitergeben.")


def render_trip_overview(data: dict, trip_key: str):
    trip = data["trips"][trip_key]
    details = trip.setdefault("details", DEFAULT_TRIP_DETAILS.copy())

    st.subheader("📅 Reiseübersicht")
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("Reiseziel", details.get("destination", ""), key=f"dest_{trip_key}")
        homepage = st.text_input("Homepage", details.get("homepage") or details.get("loc_name", ""), key=f"homepage_{trip_key}")
        street = st.text_input("Straße", details.get("street", ""), key=f"street_{trip_key}")
        meet_date = st.date_input(
            "Treffpunkt am (Datum)",
            value=datetime.date.fromisoformat(details.get("meet_date", str(datetime.date.today()))),
            key=f"meet_date_{trip_key}",
        )

    with c2:
        city = st.text_input("Ort", details.get("city", ""), key=f"city_{trip_key}")
        plz = st.text_input("PLZ", details.get("plz", ""), key=f"plz_{trip_key}")
        start_date = st.date_input(
            "Startdatum",
            value=datetime.date.fromisoformat(details.get("start_date", str(datetime.date.today()))),
            key=f"start_{trip_key}",
        )
        meet_time = st.time_input(
            "Treffpunkt am (Uhrzeit)",
            value=datetime.time.fromisoformat(details.get("meet_time", "18:00")),
            key=f"meet_time_{trip_key}",
        )

    c3, c4 = st.columns(2)
    with c3:
        end_date = st.date_input(
            "Enddatum",
            value=datetime.date.fromisoformat(details.get("end_date", str(datetime.date.today()))),
            key=f"end_{trip_key}",
        )
    with c4:
        st.caption("Treffpunkt")
        st.write(f"{meet_date.strftime('%d.%m.%Y')} um {meet_time.strftime('%H:%M')} Uhr")

    extra = st.text_area("Zusätzliche Infos", details.get("extra", ""), key=f"extra_{trip_key}")

    new_details = {
        **details,
        "destination": destination,
        "homepage": homepage,
        "loc_name": homepage,
        "street": street,
        "city": city,
        "plz": plz,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "meet_date": str(meet_date),
        "meet_time": meet_time.strftime("%H:%M"),
        "extra": extra,
    }
    if new_details != details:
        trip["details"] = new_details
        save_db(data)

    address = ", ".join(x for x in [street, f"{plz} {city}".strip()] if x.strip())
    if address:
        st.markdown("### 🗺️ Karte")
        encoded_addr = urllib.parse.quote(address)
        html(
            f'<iframe width="100%" height="350" frameborder="0" style="border:0;border-radius:12px" '
            f'src="https://maps.google.com/maps?q={encoded_addr}&t=&z=14&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>',
            height=360,
        )

    _render_weather_section(new_details)
    _render_participant_preview(trip_key, trip)


ensure_logged_in()
data = load_current_data()
apply_theme()

with st.sidebar:
    st.title("🌍 MeinAusflug")
    st.write(f"Angemeldet als **{st.session_state.user}**")
    status = get_storage_status()
    st.caption(f"Speicher: {status.get('mode', 'unbekannt')}")

    auto_refresh = st.toggle("Auto-Refresh für Benachrichtigungen", value=True, key="auto_refresh_toggle")
    if auto_refresh:
        st_autorefresh(interval=20_000, key="autorefresh_global")
    st.caption("Browser-Benachrichtigungen werden beim ersten neuen Eintrag angefragt.")

    choices = get_trip_choices(data)
    labels = [name for name, _ in choices]
    keys = {name: key for name, key in choices}

    new_trip = st.text_input("Neue Reise")
    if st.button("Reise anlegen", use_container_width=True) and new_trip.strip():
        key = new_trip.strip()
        data.setdefault("trips", {})[key] = create_trip(key)
        save_db(data)
        st.session_state.selected_trip = key
        st.rerun()

    if not choices:
        st.info("Lege links eine Reise an.")
        st.stop()

    default_key = st.session_state.get("selected_trip") or choices[0][1]
    default_label = next((name for name, key in choices if key == default_key), choices[0][0])
    selected_label = st.selectbox(
        "Reise wählen",
        labels,
        index=labels.index(default_label) if default_label in labels else 0,
    )
    trip_key = keys[selected_label]
    st.session_state.selected_trip = trip_key

    if st.button("Neu laden", use_container_width=True):
        st.session_state.force_reload = True
        st.rerun()

trip = data["trips"][trip_key]
ensure_participant(trip, st.session_state.user)
save_db(data)

chat_unread = _chat_unread_count(trip, st.session_state.user)
check_unread = _checklist_unread_count(trip, st.session_state.user)

prev_chat = st.session_state.get(f"prev_chat_unread_{trip_key}", chat_unread)
prev_check = st.session_state.get(f"prev_check_unread_{trip_key}", check_unread)
if chat_unread > prev_chat:
    st.toast(f"💬 {chat_unread - prev_chat} neue Chat-Nachricht(en)")
    _browser_notify(
        "MeinAusflug",
        f"{chat_unread - prev_chat} neue Chat-Nachricht(en) in {trip.get('name') or trip_key}",
        f"chatnotify_{trip_key}_{chat_unread}",
    )
if check_unread > prev_check:
    st.toast(f"✅ {check_unread - prev_check} neue Checklisten-Änderung(en)")
    _browser_notify(
        "MeinAusflug",
        f"{check_unread - prev_check} neue Checklisten-Änderung(en) in {trip.get('name') or trip_key}",
        f"checknotify_{trip_key}_{check_unread}",
    )
st.session_state[f"prev_chat_unread_{trip_key}"] = chat_unread
st.session_state[f"prev_check_unread_{trip_key}"] = check_unread

st.title(f"🌍 {trip.get('name') or trip_key}")
summary_cols = st.columns(3)
summary_cols[0].metric("Teilnehmer", len(trip.get("participants", {})))
summary_cols[1].metric(
    "Nachrichten",
    len(trip.get("messages", []) or trip.get("chat", [])),
    delta=f"{chat_unread} neu" if chat_unread else None,
)
summary_cols[2].metric(
    "Checklistenpunkte",
    len(trip.get("tasks", []) or trip.get("checklist", [])),
    delta=f"{check_unread} neu" if check_unread else None,
)

section_options = [
    "Übersicht",
    f"Chat{' • ' + str(chat_unread) if chat_unread else ''}",
    f"Checkliste{' • ' + str(check_unread) if check_unread else ''}",
    "Kosten",
    "Fotos",
    "Infos",
]
default_section = st.session_state.get(f"section_{trip_key}", "Übersicht")
if default_section not in section_options:
    default_section = "Übersicht"
section = st.radio(
    "Bereich",
    section_options,
    horizontal=True,
    label_visibility="collapsed",
    index=section_options.index(default_section),
)
st.session_state[f"section_{trip_key}"] = section

if section.startswith("Übersicht"):
    render_trip_overview(data, trip_key)
elif section.startswith("Chat"):
    if _set_last_read(trip, st.session_state.user, "chat"):
        save_db(data)
    render_online_bar(data, trip_key, st.session_state.user)
    render_chat(data, trip_key, st.session_state.user)
elif section.startswith("Checkliste"):
    if _set_last_read(trip, st.session_state.user, "checklist"):
        save_db(data)
    render_checklist(data, trip_key, st.session_state.user)
elif section == "Kosten":
    render_costs(data, trip_key, st.session_state.user)
elif section == "Fotos":
    render_photos(data, trip_key)
else:
    render_info(data, trip_key)
