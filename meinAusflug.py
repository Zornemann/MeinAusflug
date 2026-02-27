import streamlit as st
import datetime
import requests
import urllib.parse
from streamlit.components.v1 import html

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from config import APP_NAME, APP_ICON_URL, ADMIN_PASSWORD, APP_URL
from storage import load_db, save_db
from ui_checklist import render_checklist
from ui_info import render_info
from ui_costs import render_costs
from ui_photos import render_photos
from utils_email import send_system_email, get_mailto_link

from chat_engine import render_chat, chat_input, render_online_bar
from theme import apply_theme
from live_sync import auto_refresh

try:
    from pwa import enable_pwa
except Exception:
    enable_pwa = None


st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

st.markdown("""
<style>
.weather-card {
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    background-color: rgba(151, 166, 195, 0.1);
    margin: 5px;
}
.weather-icon { font-size: 2.5rem; }
.weather-temp { font-size: 1.2rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def get_map_html(address: str) -> str:
    if not address or len(address) < 3:
        return ""
    encoded_addr = urllib.parse.quote(address)
    return f'<iframe width="100%" height="400" frameborder="0" style="border:0" src="https://maps.google.com/maps?q={encoded_addr}&t=&z=14&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>'


def get_weather_data(city: str):
    if not city:
        return None
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
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
            w_res["current_weather"]["icon"] = icons.get(w_res["current_weather"]["weathercode"], "🌡️")

        forecast = []
        if "daily" in w_res:
            for i in range(min(7, len(w_res["daily"]["time"]))):
                code = w_res["daily"]["weathercode"][i]
                forecast.append({
                    "date": w_res["daily"]["time"][i],
                    "max": w_res["daily"]["temperature_2m_max"][i],
                    "min": w_res["daily"]["temperature_2m_min"][i],
                    "icon": icons.get(code, "🌡️")
                })
        w_res["forecast"] = forecast
        return w_res
    except Exception:
        return None


def calculate_distance(home_city: str, dest_city: str):
    if not home_city or not dest_city:
        return None
    try:
        geolocator = Nominatim(user_agent="mein_ausflug_pro_planner")
        loc1 = geolocator.geocode(home_city)
        loc2 = geolocator.geocode(dest_city)
        if loc1 and loc2:
            return round(geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km, 1)
    except:
        return None


def create_trip(name: str):
    return {
        "name": name,
        "status": "In Planung",
        "participants": {},
        "messages": [],
        "typing": {},
        "presence": {},
        "tasks": [],
        "expenses": [],
        "images": [],
        "details": {
            "destination": "",
            "loc_name": "",
            "extra": "",
            "street": "",
            "plz": "",
            "city": "",
            "start_date": str(datetime.date.today()),
            "end_date": str(datetime.date.today() + datetime.timedelta(days=3)),
            "meet_date": str(datetime.date.today()),
            "meet_time": "18:00",
        }
    }


def ensure_participants_dict(trip: dict):
    if isinstance(trip.get("participants"), list):
        trip["participants"] = {n: {"password": ADMIN_PASSWORD} for n in trip["participants"]}
    if "participants" not in trip or not isinstance(trip["participants"], dict):
        trip["participants"] = {}


def ensure_details(trip: dict, trip_name: str):
    if "details" not in trip or not isinstance(trip["details"], dict):
        trip["details"] = create_trip(trip_name)["details"]


# --------------------------
# DB init
# --------------------------
if "db" not in st.session_state:
    st.session_state.db = load_db()
data = st.session_state.db
if "trips" not in data:
    data["trips"] = {}


def login_ui():
    st.title("🔐 Reise-Login")
    trips = list(data["trips"].keys())

    if not trips:
        new_name = st.text_input("Erste Reise erstellen", key="login_new_t")
        if st.button("Starten"):
            if not new_name:
                st.error("Bitte gib einen Namen für die Reise ein.")
                return
            data["trips"][new_name] = create_trip(new_name)
            save_db(data)
            st.rerun()
        return

    trip_sel = st.selectbox("Reise wählen", trips, key="login_sel")
    user_in = st.text_input("Dein Name", key="login_user")
    pwd_in = st.text_input("Passwort", type="password", key="login_pwd")

    if st.button("Anmelden / Beitreten"):
        if not user_in:
            st.error("Bitte gib deinen Namen ein.")
            return

        trip = data["trips"][trip_sel]
        ensure_participants_dict(trip)

        participants = trip["participants"]
        ok_user = user_in in participants and participants[user_in].get("password") == pwd_in
        ok_admin = (pwd_in == ADMIN_PASSWORD and pwd_in != "")

        if ok_user or ok_admin:
            if user_in not in participants:
                participants[user_in] = {"password": pwd_in}

            save_db(data)
            st.session_state.user = user_in
            st.session_state.trip = trip_sel
            st.session_state.role = "admin" if ok_admin else "member"
            st.rerun()
        else:
            st.error("Login fehlgeschlagen.")


# --------------------------
# App start
# --------------------------
if "user" not in st.session_state:
    login_ui()
    st.stop()

apply_theme()
auto_refresh(interval=5)

if enable_pwa:
    enable_pwa(app_name=APP_NAME)

user, trip_name = st.session_state.user, st.session_state.trip
if trip_name not in data["trips"]:
    st.error("Die ausgewählte Reise existiert nicht mehr.")
    for k in ("user", "trip", "role"):
        st.session_state.pop(k, None)
    st.rerun()

trip = data["trips"][trip_name]
ensure_participants_dict(trip)
ensure_details(trip, trip_name)

if "role" not in st.session_state:
    st.session_state.role = "member"


# ✅ DB Cleanup V3 (runs once, even if you had older cleanup flags)
if "did_chat_cleanup_v3" not in st.session_state:
    import re
    meta_raw = re.compile(
        r"<div[^>]*\bclass\s*=\s*['\"][^'\"]*\bmeta\b[^'\"]*['\"][\s\S]*?</div>",
        re.I
    )
    meta_esc = re.compile(
        r"&lt;div[^&]*\bclass\s*=\s*(?:&quot;|\"|')?[^&]*\bmeta\b[^&]*(?:&quot;|\"|')?[\s\S]*?&lt;/div&gt;",
        re.I
    )

    changed = False
    for m in trip.get("messages", []) or []:
        if isinstance(m, dict) and isinstance(m.get("text"), str):
            old = m["text"]
            new = meta_raw.sub("", old)
            new = meta_esc.sub("", new)
            new = new.strip()
            if new != old:
                m["text"] = new
                changed = True

    if changed:
        save_db(data)
    st.session_state.did_chat_cleanup_v3 = True


with st.sidebar:
    if APP_ICON_URL:
        st.image(APP_ICON_URL, width=120)

    st.header(f"👤 {user}")
    st.caption(f"Rolle: {'🛠️ Admin' if st.session_state.role == 'admin' else '👥 Member'}")

    with st.expander("🔑 Passwort ändern"):
        new_p = st.text_input("Neues Passwort", type="password", key="s_pw")
        if st.button("Speichern", key="s_pw_b"):
            if user not in trip["participants"]:
                trip["participants"][user] = {"password": new_p}
            else:
                trip["participants"][user]["password"] = new_p
            save_db(data)
            st.success("Geändert!")

    st.divider()
    st.subheader("✉️ Freunde einladen")
    f_mail = st.text_input("E-Mail Adresse", key="s_mail")

    if f_mail:
        subj = f"Einladung: {trip_name}"
        body = f"Komm in unsere Reise-App: {APP_URL}\nLogin: {f_mail.split('@')[0]}\nPasswort: {ADMIN_PASSWORD}"

        if st.button("✉️ Einladung senden", key="s_mail_b"):
            with st.spinner("Sende..."):
                ok, msg = send_system_email(f_mail, subj, body)
                st.success(msg) if ok else st.error(msg)

        st.markdown(
            f'<a href="{get_mailto_link(f_mail, subj, body)}" target="_blank">📧 Mail-Programm öffnen</a>',
            unsafe_allow_html=True
        )

    # "Abmelden" ist korrekt (Logout)
    if st.button("🚪 Abmelden", key="s_logout"):
        for k in ("user", "trip", "role"):
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()
    with st.expander("🛠️ Admin-Bereich"):
        admin_pw = st.text_input("Admin-Passwort", type="password", key="admin_access_pw")
        if admin_pw == ADMIN_PASSWORD:
            st.session_state.role = "admin"
            st.warning("Vorsicht: Aktionen sind endgültig!")
            if st.button(f"🗑️ '{trip_name}' löschen", key="admin_del_current"):
                if len(data.get("trips", {})) > 1:
                    del data["trips"][trip_name]
                    save_db(data)
                    for k in ("user", "trip", "role"):
                        st.session_state.pop(k, None)
                    st.rerun()
                else:
                    st.error("Du brauchst mindestens 2 Reisen, damit du diese löschen kannst.")

            if st.button("🧨 Alle Reisen löschen", key="admin_del_all"):
                data["trips"] = {}
                save_db(data)
                for k in ("user", "trip", "role"):
                    st.session_state.pop(k, None)
                st.rerun()

            import json
            db_str = json.dumps(data, indent=4, ensure_ascii=False)
            st.download_button("📥 Datenbank-Backup", data=db_str, file_name="backup.json", mime="application/json")


tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Startseite", "🧭 Ausrüstung", "📝 Infos", "💰 Kosten", "📸 Fotos"])

with tab1:
    st.title(f"🌍 {trip_name}")

    with st.expander("✏️ Reisedetails & Treffpunkt bearbeiten"):
        c1, c2 = st.columns(2)
        with c1:
            e_dest = st.text_input("Ausflugsziel", value=trip["details"].get("destination", ""), key="t1_dest")
            e_loc = st.text_input("Unterkunft Name", value=trip["details"].get("loc_name", ""), key="t1_loc")
            e_home = st.text_input("Dein Startort (für Distanz)", key="t1_home")

            sd = datetime.date.fromisoformat(trip["details"]["start_date"])
            ed = datetime.date.fromisoformat(trip["details"]["end_date"])
            e_range = st.date_input("Zeitraum", [sd, ed], key="t1_range")

        with c2:
            e_str = st.text_input("Straße & Nr.", value=trip["details"].get("street", ""), key="t1_str")
            e_plz = st.text_input("PLZ", value=trip["details"].get("plz", ""), key="t1_plz")
            e_city = st.text_input("Ort", value=trip["details"].get("city", ""), key="t1_city")

            md = datetime.date.fromisoformat(trip["details"]["meet_date"])
            mt_str = trip["details"].get("meet_time", "18:00")
            mt = datetime.time.fromisoformat(mt_str if ":" in mt_str else "18:00")

            mc1, mc2 = st.columns(2)
            e_md = mc1.date_input("Treffen am", md, key="t1_md")
            e_mt = mc2.time_input("Um", mt, key="t1_mt")

        if st.button("💾 Speichern", key="t1_save"):
            if isinstance(e_range, (list, tuple)) and len(e_range) >= 1:
                s_s = str(e_range[0])
                e_s = str(e_range[1]) if len(e_range) > 1 else str(e_range[0])
            else:
                s_s = trip["details"]["start_date"]
                e_s = trip["details"]["end_date"]

            trip["details"].update({
                "destination": e_dest,
                "loc_name": e_loc,
                "street": e_str,
                "plz": e_plz,
                "city": e_city,
                "start_date": s_s,
                "end_date": e_s,
                "meet_date": str(e_md),
                "meet_time": e_mt.strftime("%H:%M"),
            })
            save_db(data)
            st.rerun()

    st.divider()

    render_online_bar(data, trip_name, user)
    render_chat(data, trip_name, user)
    chat_input(data, trip_name, user)

with tab2:
    render_checklist(data, trip_name, user)

with tab3:
    render_info(data, trip_name)

with tab4:
    render_costs(data, trip_name, user)

with tab5:
    render_photos(data, trip_name)