import datetime
import urllib.parse

import requests
import streamlit as st
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from streamlit.components.v1 import html

from app.chat_engine import mark_chat_read, render_online_bar, unread_chat_count
from app.theme import apply_theme
from core.config import APP_NAME, APP_URL
from core.storage import get_storage_status, load_db, normalize_data, save_db
from ui.ui_chat import render_chat
from ui.ui_checklist import render_checklist
from ui.ui_costs import render_costs
from ui.ui_info import render_info
from ui.ui_photos import render_photos

st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")


DEFAULT_TRIP_DETAILS = {
    "destination": "",
    "loc_name": "",
    "extra": "",
    "street": "",
    "plz": "",
    "city": "",
    "home_city": "",
    "start_date": str(datetime.date.today()),
    "end_date": str(datetime.date.today()),
    "meet_date": str(datetime.date.today()),
    "meet_time": "18:00",
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
    }


@st.cache_data(show_spinner=False, ttl=1800)
def get_weather_data(city: str):
    city = (city or "").strip()
    if not city:
        return None
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=de&format=json"
        geo_res = requests.get(geo_url, timeout=10).json()
        if "results" not in geo_res or not geo_res["results"]:
            return None
        res = geo_res["results"][0]
        lat, lon = res["latitude"], res["longitude"]

        w_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&daily=weathercode,temperature_2m_max,temperature_2m_min"
            "&current_weather=true&timezone=Europe%2FBerlin"
        )
        w_res = requests.get(w_url, timeout=10).json()
        icons = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 51: "🌦️", 61: "🌧️", 71: "❄️", 95: "⚡"}
        if "current_weather" in w_res:
            w_res["current_weather"]["icon"] = icons.get(w_res["current_weather"].get("weathercode"), "🌡️")
        forecast = []
        if "daily" in w_res:
            for i in range(min(5, len(w_res["daily"]["time"]))):
                code = w_res["daily"]["weathercode"][i]
                forecast.append(
                    {
                        "date": w_res["daily"]["time"][i],
                        "max": w_res["daily"]["temperature_2m_max"][i],
                        "min": w_res["daily"]["temperature_2m_min"][i],
                        "icon": icons.get(code, "🌡️"),
                    }
                )
        w_res["forecast"] = forecast
        return w_res
    except Exception:
        return None


@st.cache_data(show_spinner=False, ttl=1800)
def distance_km(home_city: str, dest_city: str):
    try:
        geolocator = Nominatim(user_agent="meinausflug-app")
        loc1 = geolocator.geocode(home_city)
        loc2 = geolocator.geocode(dest_city)
        if loc1 and loc2:
            return round(geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km, 1)
    except Exception:
        return None
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



def _ensure_last_read(trip: dict):
    if not isinstance(trip.get("last_read"), dict):
        trip["last_read"] = {}


def _last_read_value(trip: dict, user: str, key: str) -> str:
    _ensure_last_read(trip)
    return str(trip["last_read"].get(f"{user}:{key}") or trip["last_read"].get(user) or "2000-01-01T00:00:00")


def _unread_checklist_count(trip: dict, user: str) -> int:
    last_read = _last_read_value(trip, user, "checklist")
    count = 0
    for t in trip.get("tasks", []) or trip.get("checklist", []):
        ts = str(t.get("updated_at") or t.get("created_at") or "")
        actor = str(t.get("updated_by") or t.get("created_by") or "")
        if ts > last_read and actor != user:
            count += 1
    return count


def _mark_checklist_read(trip: dict, data: dict, user: str):
    _ensure_last_read(trip)
    trip["last_read"][f"{user}:checklist"] = datetime.datetime.now().replace(microsecond=0).isoformat()
    save_db(data)


def _show_unread_toasts(chat_unread: int, checklist_unread: int):
    prev_chat = st.session_state.get("_prev_chat_unread")
    prev_check = st.session_state.get("_prev_check_unread")
    if prev_chat is not None and chat_unread > prev_chat:
        st.toast(f"💬 {chat_unread - prev_chat} neue Chat-Nachricht(en)")
    if prev_check is not None and checklist_unread > prev_check:
        st.toast(f"✅ {checklist_unread - prev_check} neue Checklisten-Änderung(en)")
    st.session_state["_prev_chat_unread"] = chat_unread
    st.session_state["_prev_check_unread"] = checklist_unread


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



def render_trip_overview(data: dict, trip_key: str):
    trip = data["trips"][trip_key]
    details = trip.setdefault("details", DEFAULT_TRIP_DETAILS.copy())

    st.subheader("📅 Reiseübersicht")
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("Reiseziel", details.get("destination", ""), key=f"dest_{trip_key}")
        loc_name = st.text_input("Ort / Unterkunft", details.get("loc_name", ""), key=f"loc_{trip_key}")
        home_city = st.text_input("Startort", details.get("home_city", ""), key=f"home_{trip_key}")
        street = st.text_input("Straße", details.get("street", ""), key=f"street_{trip_key}")
    with c2:
        city = st.text_input("Ort", details.get("city", ""), key=f"city_{trip_key}")
        plz = st.text_input("PLZ", details.get("plz", ""), key=f"plz_{trip_key}")
        start_date = st.date_input("Startdatum", value=datetime.date.fromisoformat(details.get("start_date", str(datetime.date.today()))), key=f"start_{trip_key}")
        end_date = st.date_input("Enddatum", value=datetime.date.fromisoformat(details.get("end_date", str(datetime.date.today()))), key=f"end_{trip_key}")

    extra = st.text_area("Zusätzliche Infos", details.get("extra", ""), key=f"extra_{trip_key}")

    new_details = {
        **details,
        "destination": destination,
        "loc_name": loc_name,
        "home_city": home_city,
        "street": street,
        "city": city,
        "plz": plz,
        "start_date": str(start_date),
        "end_date": str(end_date),
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

    weather_city = city or destination
    weather = get_weather_data(weather_city)
    if weather and weather.get("forecast"):
        st.markdown("### 🌤️ Wetter")
        cols = st.columns(len(weather["forecast"]))
        for col, day in zip(cols, weather["forecast"]):
            with col:
                st.metric(day["date"], f"{day['max']}°C", f"{day['min']}°C")
                st.caption(day["icon"])

    if home_city and destination:
        dist = distance_km(home_city, destination)
        if dist:
            st.info(f"Entfernung ca. {dist} km")


ensure_logged_in()
data = load_current_data()
apply_theme()

with st.sidebar:
    st.title("🌍 MeinAusflug")
    st.write(f"Angemeldet als **{st.session_state.user}**")
    status = get_storage_status()
    st.caption(f"Speicher: {status.get('mode', 'unbekannt')}")

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
    selected_label = st.selectbox("Reise wählen", labels, index=labels.index(default_label) if default_label in labels else 0)
    trip_key = keys[selected_label]
    st.session_state.selected_trip = trip_key

    if st.button("Neu laden", use_container_width=True):
        st.session_state.force_reload = True
        st.rerun()

trip = data["trips"][trip_key]
ensure_participant(trip, st.session_state.user)
save_db(data)

st.title(f"🌍 {trip.get('name') or trip_key}")

summary_cols = st.columns(5)
chat_unread = unread_chat_count(trip, st.session_state.user, st.session_state.get("role", "member"))
check_unread = _unread_checklist_count(trip, st.session_state.user)
_show_unread_toasts(chat_unread, check_unread)
summary_cols[0].metric("Teilnehmer", len(trip.get("participants", {})))
summary_cols[1].metric("Nachrichten", len(trip.get("messages", []) or trip.get("chat", [])), delta=f"{chat_unread} neu" if chat_unread else None)
summary_cols[2].metric("Checklistenpunkte", len(trip.get("tasks", []) or trip.get("checklist", [])), delta=f"{check_unread} neu" if check_unread else None)
summary_cols[3].metric("Ungelesen Chat", chat_unread)
summary_cols[4].metric("Ungelesen Checkliste", check_unread)

nav_options = [
    "Übersicht",
    f"Chat{' 🔔' if chat_unread else ''}",
    f"Checkliste{' 🔔' if check_unread else ''}",
    "Kosten",
    "Fotos",
    "Infos",
]
selected_view = st.segmented_control(
    "Bereich",
    nav_options,
    default=st.session_state.get("selected_view", nav_options[0]),
    selection_mode="single",
)
st.session_state.selected_view = selected_view

if selected_view == "Übersicht":
    render_trip_overview(data, trip_key)
elif selected_view == nav_options[1]:
    if chat_unread:
        mark_chat_read(trip, data, st.session_state.user)
    render_online_bar(data, trip_key, st.session_state.user)
    render_chat(data, trip_key, st.session_state.user)
elif selected_view == nav_options[2]:
    if check_unread:
        _mark_checklist_read(trip, data, st.session_state.user)
    render_checklist(data, trip_key, st.session_state.user)
elif selected_view == "Kosten":
    render_costs(data, trip_key, st.session_state.user)
elif selected_view == "Fotos":
    render_photos(data, trip_key)
else:
    render_info(data, trip_key)
