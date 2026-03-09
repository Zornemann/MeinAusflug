<<<<<<< HEAD
import streamlit as st
import datetime
import requests
import urllib.parse
from streamlit.components.v1 import html
=======
from streamlit.components.v1 import html
import streamlit as st
import datetime
import datetime as dt
import requests
import secrets
import urllib.parse
from core.storage import load_db, save_db, get_storage_status, normalize_data
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

<<<<<<< HEAD
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
=======
from core.config import APP_NAME, APP_ICON_URL, ADMIN_PASSWORD, APP_URL
from core.utils_email import send_system_email, get_mailto_link

from ui.ui_checklist import render_checklist
from ui.ui_info import render_info
from ui.ui_costs import render_costs
from ui.ui_photos import render_photos

from ui.ui_chat import render_chat
from app.chat_engine import render_online_bar
from app.theme import apply_theme
from app.live_sync import auto_refresh

# optional pwa (je nachdem wo du sie liegen hast)
try:
    from app.pwa import enable_pwa
except Exception:
    try:
        from pwa import enable_pwa
    except Exception:
        enable_pwa = None


INVITE_EXPIRE_DAYS = 7  # ✅ Idee (1): Einladungen laufen ab
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)


st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

<<<<<<< HEAD
=======
storage_status = get_storage_status()

>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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


<<<<<<< HEAD
=======
# Defensive fallback: some older project states may miss normalize_data in core.storage
if "normalize_data" not in globals():
    def normalize_data(data):
        if not isinstance(data, dict):
            data = {}
        trips = data.setdefault("trips", {})
        for trip_name, trip in list(trips.items()):
            if not isinstance(trip, dict):
                trip = {}
                trips[trip_name] = trip
            messages = trip.get("messages") or trip.get("chat") or []
            tasks = trip.get("tasks") or trip.get("checklist") or []
            trip["messages"] = messages
            trip["chat"] = messages
            trip["tasks"] = tasks
            trip["checklist"] = tasks
            trip.setdefault("participants", {})
            trip.setdefault("details", create_trip(trip_name)["details"] if "create_trip" in globals() else {})
            aliases = trip.setdefault("aliases", [])
            if isinstance(aliases, list) and trip_name not in aliases:
                aliases.append(trip_name)
        return data



def now_iso() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def parse_iso_dt(s: str):
    try:
        return datetime.datetime.fromisoformat(s)
    except Exception:
        return None


>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
def get_map_html(address: str) -> str:
    if not address or len(address) < 3:
        return ""
    encoded_addr = urllib.parse.quote(address)
<<<<<<< HEAD
    return f'<iframe width="100%" height="400" frameborder="0" style="border:0" src="https://maps.google.com/maps?q={encoded_addr}&t=&z=14&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>'
=======
    return (
        f'<iframe width="100%" height="400" frameborder="0" style="border:0" '
        f'src="https://maps.google.com/maps?q={encoded_addr}&t=&z=14&ie=UTF8&iwloc=&output=embed" '
        f'allowfullscreen></iframe>'
    )
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)


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

<<<<<<< HEAD
        icons = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 51: "🌦️", 61: "🌧️", 71: "❄️", 95: "⚡"}
=======
        icons = {
            0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️",
            51: "🌦️", 61: "🌧️", 71: "❄️", 95: "⚡"
        }
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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
<<<<<<< HEAD
    except:
=======
    except Exception:
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
        return None


def create_trip(name: str):
    return {
        "name": name,
        "status": "In Planung",
<<<<<<< HEAD
        "participants": {},
=======
        "participants": {},   # Dict: username -> meta
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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
<<<<<<< HEAD
=======
            "home_city": "",
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
            "start_date": str(datetime.date.today()),
            "end_date": str(datetime.date.today() + datetime.timedelta(days=3)),
            "meet_date": str(datetime.date.today()),
            "meet_time": "18:00",
        }
    }

<<<<<<< HEAD

def ensure_participants_dict(trip: dict):
    if isinstance(trip.get("participants"), list):
        trip["participants"] = {n: {"password": ADMIN_PASSWORD} for n in trip["participants"]}
    if "participants" not in trip or not isinstance(trip["participants"], dict):
        trip["participants"] = {}
=======
def resolve_trip_key(data: dict, requested: str) -> str:
    """Resolve a trip key by exact key, alias, destination, loc_name, or stored name."""
    trips = data.get("trips", {}) if isinstance(data, dict) else {}
    if not requested:
        return requested

    if requested in trips:
        return requested

    requested_l = str(requested).strip().lower()
    for key, trip in trips.items():
        if not isinstance(trip, dict):
            continue

        aliases = trip.get("aliases", []) or []
        if isinstance(aliases, list):
            for alias in aliases:
                if str(alias).strip().lower() == requested_l:
                    return key

        if str(trip.get("name", "")).strip().lower() == requested_l:
            return key

        details = trip.get("details", {}) or {}
        for cand in (details.get("destination", ""), details.get("loc_name", "")):
            if str(cand).strip().lower() == requested_l:
                return key

    return requested



def ensure_participants_dict(trip: dict) -> bool:
    # Altformat: Liste -> Dict
    changed = False
    if isinstance(trip.get("participants"), list):
        trip["participants"] = {n: {"password": ""} for n in trip["participants"]}
        changed = True

    if "participants" not in trip or not isinstance(trip["participants"], dict):
        trip["participants"] = {}
        changed = True

    # Normalize
    for uname, pdata in list(trip["participants"].items()):
        if not isinstance(pdata, dict):
            trip["participants"][uname] = {"password": ""}
            changed = True
            pdata = trip["participants"][uname]

        pdata.setdefault("password", "")
        pdata.setdefault("email", "")
        pdata.setdefault("status", "accepted")  # vorhandene Nutzer => accepted
        pdata.setdefault("invited_by", "")
        pdata.setdefault("display_name", "")
        pdata.setdefault("role", "member")      # ✅ Idee (2): Rollen pro Reise
        # token/invited_at/expires_at nur wenn invited

    return changed
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)


def ensure_details(trip: dict, trip_name: str):
    if "details" not in trip or not isinstance(trip["details"], dict):
        trip["details"] = create_trip(trip_name)["details"]
<<<<<<< HEAD


# --------------------------
# DB init
# --------------------------
if "db" not in st.session_state:
    st.session_state.db = load_db()
data = st.session_state.db
if "trips" not in data:
    data["trips"] = {}


def login_ui():
=======
    trip["details"].setdefault("home_city", "")


def _make_unique_username(trip: dict, base: str, email: str) -> str:
    base = (base or "user").strip()
    base = "".join(ch for ch in base if ch.isalnum() or ch in ("_", "-")).strip("_-") or "user"

    if base not in trip["participants"]:
        return base

    ex = trip["participants"].get(base, {})
    if isinstance(ex, dict) and ex.get("email", "").lower() == email.lower():
        return base

    i = 2
    while True:
        cand = f"{base}_{i}"
        if cand not in trip["participants"]:
            return cand
        ex2 = trip["participants"].get(cand, {})
        if isinstance(ex2, dict) and ex2.get("email", "").lower() == email.lower():
            return cand
        i += 1


def invite_user(trip: dict, email: str, inviter: str) -> dict:
    """
    ✅ Idee (1): Einladungen mit Ablauf
    ✅ Idee (2): Rollen pro Reise
    """
    email = email.strip()
    base_user = email.split("@")[0].strip() if "@" in email else email
    uname = _make_unique_username(trip, base_user, email)

    token = secrets.token_urlsafe(20)
    invited_at = now_iso()
    expires_at = (datetime.datetime.now() + datetime.timedelta(days=INVITE_EXPIRE_DAYS)).replace(microsecond=0).isoformat()

    trip["participants"].setdefault(uname, {})
    trip["participants"][uname].update({
        "email": email,
        "status": "invited",
        "invited_by": inviter,
        "token": token,
        "invited_at": invited_at,
        "expires_at": expires_at,
        "password": "",          # Passwort wird beim Annehmen gesetzt
        "display_name": trip["participants"][uname].get("display_name", ""),
        "role": "member",
    })
    return {"username": uname, "token": token, "expires_at": expires_at}


def find_invite_by_token(data: dict, trip_name: str, token: str):
    if trip_name not in data.get("trips", {}):
        return None, None, None
    trip = data["trips"][trip_name]
    ensure_participants_dict(trip)
    for uname, pdata in trip["participants"].items():
        if isinstance(pdata, dict) and pdata.get("token") == token and pdata.get("status") == "invited":
            return trip, uname, pdata
    return None, None, None


def invite_is_expired(pdata: dict) -> bool:
    exp = parse_iso_dt(pdata.get("expires_at", ""))
    if not exp:
        return False
    return datetime.datetime.now() > exp


def accept_invite_flow(data: dict) -> bool:
    """
    ✅ Idee (1): Ablauf prüfen
    Token-Link: ?trip=<name>&invite=<token>
    -> Passwort setzen, accepted, token löschen, auto-login
    """
    trip_name = st.query_params.get("trip")
    token = st.query_params.get("invite")
    if not trip_name or not token:
        return False

    trip, uname, pdata = find_invite_by_token(data, trip_name, token)
    if not trip:
        st.title("❌ Einladung ungültig")
        st.error("Der Einladungs-Link ist ungültig oder wurde bereits genutzt.")
        st.stop()
        return True

    if invite_is_expired(pdata):
        st.title("⌛ Einladung abgelaufen")
        st.error(f"Diese Einladung ist abgelaufen (gültig bis: {pdata.get('expires_at','?')}). Bitte neu einladen lassen.")
        st.stop()
        return True

    st.title("✅ Einladung annehmen")
    st.write(f"Reise: **{trip_name}**")
    st.write(f"Benutzername: **{uname}**")
    st.write(f"E-Mail: **{pdata.get('email','-')}**")
    st.caption(f"Gültig bis: {pdata.get('expires_at','')}")

    with st.form("accept_invite_form"):
        display = st.text_input("Anzeigename (optional)", value=pdata.get("display_name", ""))
        pw1 = st.text_input("Neues Passwort", type="password")
        pw2 = st.text_input("Passwort wiederholen", type="password")
        ok = st.form_submit_button("Einladung annehmen & starten")

        if ok:
            if not pw1 or len(pw1) < 4:
                st.error("Bitte ein Passwort mit mindestens 4 Zeichen vergeben.")
                st.stop()

            if pw1 != pw2:
                st.error("Die Passwörter stimmen nicht überein.")
                st.stop()

            trip["participants"][uname]["password"] = pw1
            trip["participants"][uname]["status"] = "accepted"
            trip["participants"][uname]["display_name"] = display.strip()
            trip["participants"][uname].pop("token", None)
            trip["participants"][uname].pop("invited_at", None)
            trip["participants"][uname].pop("expires_at", None)

            save_db(data)

            # Auto-login
            st.session_state.user = uname
            st.session_state.trip = trip_name
            st.session_state.role = "admin" if trip["participants"][uname].get("role") == "admin" else "member"
            st.success("Erfolgreich angenommen. Du wirst eingeloggt…")
            st.rerun()

    st.stop()
    return True


# --------------------------
# DB init / Live-Reload
# --------------------------
if "force_reload" not in st.session_state:
    st.session_state.force_reload = False

# Bei jedem Script-Run frisch laden, damit Auto-Refresh auch fremde Änderungen sieht.
data = normalize_data(load_db())
st.session_state.db = data
st.session_state.force_reload = False

if "trips" not in data or not isinstance(data["trips"], dict):
    data["trips"] = {}
    st.session_state.db = data

with st.sidebar:
    mode_label = "☁️ Supabase" if storage_status.get("mode") == "cloud" else "💾 Lokal"
    st.caption(f"Speicher: {mode_label}")
    if storage_status.get("mode") != "cloud":
        st.warning(storage_status.get("reason", "Lokaler Fallback aktiv"), icon="⚠️")


def login_ui():
    # Falls Einladung über Token-Link
    if accept_invite_flow(data):
        return

>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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

<<<<<<< HEAD
    trip_sel = st.selectbox("Reise wählen", trips, key="login_sel")
    user_in = st.text_input("Dein Name", key="login_user")
    pwd_in = st.text_input("Passwort", type="password", key="login_pwd")

    if st.button("Anmelden / Beitreten"):
=======
    trip_q = st.query_params.get("trip")
    default_trip = trip_q if trip_q in trips else trips[0]
    trip_sel = st.selectbox("Reise wählen", trips, index=trips.index(default_trip), key="login_sel")

    user_in = st.text_input("Dein Name", key="login_user")
    pwd_in = st.text_input("Passwort", type="password", key="login_pwd")

    if st.button("Anmelden"):
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
        if not user_in:
            st.error("Bitte gib deinen Namen ein.")
            return

        trip = data["trips"][trip_sel]
        ensure_participants_dict(trip)
<<<<<<< HEAD

        participants = trip["participants"]
        ok_user = user_in in participants and participants[user_in].get("password") == pwd_in
        ok_admin = (pwd_in == ADMIN_PASSWORD and pwd_in != "")

        if ok_user or ok_admin:
            if user_in not in participants:
                participants[user_in] = {"password": pwd_in}
=======
        participants = trip["participants"]

        # Admin override (globales Admin-Passwort bleibt als "Master-Key" bestehen)
        ok_admin_override = (pwd_in == ADMIN_PASSWORD and pwd_in != "")

        # normaler Login: User muss existieren + Passwort passen
        ok_user = (user_in in participants and participants[user_in].get("password") == pwd_in and pwd_in != "")

        if ok_user or ok_admin_override:
            # Wenn Admin override: User anlegen falls nicht existiert
            if user_in not in participants and ok_admin_override:
                participants[user_in] = {
                    "password": "",
                    "email": "",
                    "status": "accepted",
                    "invited_by": "",
                    "display_name": "",
                    "role": "admin",   # ✅ override => admin
                }
            elif ok_admin_override:
                # bestehender User wird admin
                participants[user_in]["role"] = "admin"
                participants[user_in]["status"] = "accepted"
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)

            save_db(data)
            st.session_state.user = user_in
            st.session_state.trip = trip_sel
<<<<<<< HEAD
            st.session_state.role = "admin" if ok_admin else "member"
=======
            st.session_state.role = "admin" if participants[user_in].get("role") == "admin" else "member"
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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
<<<<<<< HEAD
auto_refresh(interval=5)
=======
# auto_refresh(interval=5)
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)

##if enable_pwa:
    ##enable_pwa(app_name=APP_NAME)

<<<<<<< HEAD
user, trip_name = st.session_state.user, st.session_state.trip
=======
user, trip_name = st.session_state.user, resolve_trip_key(data, st.session_state.trip)
st.session_state.trip = trip_name
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
if trip_name not in data["trips"]:
    st.error("Die ausgewählte Reise existiert nicht mehr.")
    for k in ("user", "trip", "role"):
        st.session_state.pop(k, None)
    st.rerun()

trip = data["trips"][trip_name]
<<<<<<< HEAD
ensure_participants_dict(trip)
ensure_details(trip, trip_name)

if "role" not in st.session_state:
    st.session_state.role = "member"


# ✅ DB Cleanup V3 (runs once, even if you had older cleanup flags)
=======
changed_participants = ensure_participants_dict(trip)
ensure_details(trip, trip_name)
trip["messages"] = trip.get("messages") or trip.get("chat") or []
trip["chat"] = trip["messages"]
trip["tasks"] = trip.get("tasks") or trip.get("checklist") or []
trip["checklist"] = trip["tasks"]
trip.setdefault("participants", {})
trip.setdefault("details", create_trip(trip_name)["details"])
if changed_participants:
    normalize_data(data)
    save_db(data)

# Rolle aus Trip ableiten (pro Reise)
role = trip.get("participants", {}).get(user, {}).get("role", "member")
st.session_state.role = "admin" if role == "admin" else "member"


# ✅ DB Cleanup V3 (fix: meta-divs in alten Nachrichten)
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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

<<<<<<< HEAD
    st.header(f"👤 {user}")
=======
    pdata = trip.get("participants", {}).get(user, {}) if isinstance(trip.get("participants"), dict) else {}
    disp = (pdata.get("display_name") or "").strip()
    st.header(f"👤 {disp or user}")
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
    st.caption(f"Rolle: {'🛠️ Admin' if st.session_state.role == 'admin' else '👥 Member'}")

    with st.expander("🔑 Passwort ändern"):
        new_p = st.text_input("Neues Passwort", type="password", key="s_pw")
        if st.button("Speichern", key="s_pw_b"):
<<<<<<< HEAD
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
=======
            trip["participants"].setdefault(user, {})
            trip["participants"][user]["password"] = new_p
            trip["participants"][user]["status"] = "accepted"
            save_db(data)
            st.success("Geändert!")

    with st.expander("🪪 Anzeigename ändern"):
        new_dn = st.text_input("Anzeigename", value=disp, key="s_dn")
        if st.button("Speichern", key="s_dn_b"):
            trip["participants"].setdefault(user, {})
            trip["participants"][user]["display_name"] = new_dn.strip()
            save_db(data)
            st.success("Gespeichert!")

    st.divider()
    st.subheader("✉️ Freunde einladen (Token-Link)")

    invite_mail = st.text_input("E-Mail Adresse", key="s_mail")

    if invite_mail:
        subj = f"Einladung: {trip_name}"

        if st.button("✉️ Einladung senden", key="s_mail_b"):
            info = invite_user(trip, invite_mail, inviter=user)
            save_db(data)

            invite_link = f"{APP_URL}?trip={trip_name}&invite={info['token']}"
            body = (
                f"Hallo!\n\n"
                f"Du wurdest von {disp or user} zur Reise '{trip_name}' eingeladen.\n\n"
                f"✅ Klicke hier, um die Einladung anzunehmen und dein Passwort zu setzen:\n"
                f"{invite_link}\n\n"
                f"Dein Benutzername ist: {info['username']}\n"
                f"Gültig bis: {info['expires_at']}\n"
            )

            with st.spinner("Sende..."):
                ok, msg = send_system_email(invite_mail, subj, body)
                st.success("Einladung verschickt!") if ok else st.error(msg)

            st.markdown(
                f'<a href="{get_mailto_link(invite_mail, subj, body)}" target="_blank">📧 Mail-Programm öffnen</a>',
                unsafe_allow_html=True
            )

    st.markdown("### Teilnehmer")
    participants = trip.get("participants", {}) if isinstance(trip.get("participants"), dict) else {}
    accepted = [u for u, p in participants.items() if isinstance(p, dict) and p.get("status") == "accepted"]
    invited = [u for u, p in participants.items() if isinstance(p, dict) and p.get("status") == "invited"]

    def label_user(u: str) -> str:
        p = participants.get(u, {}) or {}
        dn = (p.get("display_name") or "").strip()
        return dn if dn else u

    st.caption(f"✅ Angenommen: {', '.join([label_user(u) for u in accepted]) if accepted else '-'}")
    st.caption(f"📩 Offen: {', '.join([label_user(u) for u in invited]) if invited else '-'}")

    if st.session_state.role == "admin" and invited:
        with st.expander("📩 Offene Einladungen verwalten"):
            for uname in invited:
                p = participants.get(uname, {})
                email = p.get("email", "")
                token = p.get("token", "")
                exp = p.get("expires_at", "")
                cols = st.columns([0.50, 0.25, 0.25])
                cols[0].write(f"**{label_user(uname)}**  \n{email}\n\n_gültig bis: {exp}_")

                if cols[1].button("Erneut senden", key=f"resend_{uname}"):
                    # falls abgelaufen/kein token: neu ausstellen
                    if not token or invite_is_expired(p):
                        info = invite_user(trip, email, inviter=user)
                        save_db(data)
                        token = info["token"]
                        exp = info["expires_at"]

                    invite_link = f"{APP_URL}?trip={trip_name}&invite={token}"
                    subj = f"Einladung: {trip_name}"
                    body = (
                        f"Hallo!\n\n"
                        f"Hier ist dein Einladungs-Link zur Reise '{trip_name}':\n"
                        f"{invite_link}\n\n"
                        f"Benutzername: {uname}\n"
                        f"Gültig bis: {exp}\n"
                    )
                    ok, msg = send_system_email(email, subj, body)
                    st.success("Erneut gesendet!") if ok else st.error(msg)

                if cols[2].button("Widerrufen", key=f"revoke_{uname}"):
                    del trip["participants"][uname]
                    save_db(data)
                    st.rerun()

>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
    if st.button("🚪 Abmelden", key="s_logout"):
        for k in ("user", "trip", "role"):
            st.session_state.pop(k, None)
        st.rerun()

    st.divider()
    with st.expander("🛠️ Admin-Bereich"):
<<<<<<< HEAD
        admin_pw = st.text_input("Admin-Passwort", type="password", key="admin_access_pw")
        if admin_pw == ADMIN_PASSWORD:
            st.session_state.role = "admin"
=======
        st.caption("Tipp: Admin-Rechte pro Reise bekommst du durch Login mit dem globalen Admin-Passwort.")
        admin_pw = st.text_input("Admin-Passwort", type="password", key="admin_access_pw")
        if admin_pw == ADMIN_PASSWORD:
            # Admin Override für aktuelle Sitzung
            trip["participants"].setdefault(user, {})
            trip["participants"][user]["role"] = "admin"
            trip["participants"][user]["status"] = "accepted"
            save_db(data)
            st.session_state.role = "admin"
            st.success("Admin-Rechte für diese Reise aktiviert.")

>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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
<<<<<<< HEAD
            e_home = st.text_input("Dein Startort (für Distanz)", key="t1_home")

            sd = datetime.date.fromisoformat(trip["details"]["start_date"])
            ed = datetime.date.fromisoformat(trip["details"]["end_date"])
=======
            e_home = st.text_input("Dein Startort (für Distanz)", value=trip["details"].get("home_city", ""), key="t1_home")

            # Korrektur: Nutze dt. statt datetime
            sd = dt.date.fromisoformat(trip["details"]["start_date"])
            ed = dt.date.fromisoformat(trip["details"]["end_date"])
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
            e_range = st.date_input("Zeitraum", [sd, ed], key="t1_range")

        with c2:
            e_str = st.text_input("Straße & Nr.", value=trip["details"].get("street", ""), key="t1_str")
            e_plz = st.text_input("PLZ", value=trip["details"].get("plz", ""), key="t1_plz")
            e_city = st.text_input("Ort", value=trip["details"].get("city", ""), key="t1_city")

<<<<<<< HEAD
            md = datetime.date.fromisoformat(trip["details"]["meet_date"])
            mt_str = trip["details"].get("meet_time", "18:00")
            mt = datetime.time.fromisoformat(mt_str if ":" in mt_str else "18:00")
=======
            # Korrektur: Nutze dt. statt datetime
            md = dt.date.fromisoformat(trip["details"]["meet_date"])
            mt_str = trip["details"].get("meet_time", "18:00")
            # Korrektur: Nutze dt. statt datetime
            mt = dt.time.fromisoformat(mt_str if ":" in mt_str else "18:00")
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)

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
<<<<<<< HEAD
=======
                "home_city": e_home,
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)
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

<<<<<<< HEAD
    render_online_bar(data, trip_name, user)
    render_chat(data, trip_name, user)
    chat_input(data, trip_name, user)
=======
    ti = trip.get("details", {})
    dest = (ti.get("destination") or "").strip()
    street = (ti.get("street") or "").strip()
    plz = (ti.get("plz") or "").strip()
    city = (ti.get("city") or "").strip()
    home_city = (ti.get("home_city") or "").strip()

    if dest:
        st.subheader(f"📍 {dest}")

    addr_parts = [p for p in [street, f"{plz} {city}".strip()] if p]
    address = ", ".join(addr_parts).strip()

    try:
        s_date_fmt = datetime.date.fromisoformat(ti["start_date"]).strftime("%d.%m.%Y")
        e_date_fmt = datetime.date.fromisoformat(ti["end_date"]).strftime("%d.%m.%Y")
        st.caption(f"📅 Zeitraum: {s_date_fmt} – {e_date_fmt}")
    except Exception:
        pass

    try:
        m_date_fmt = datetime.date.fromisoformat(ti["meet_date"]).strftime("%d.%m.%Y")
        st.info(f"🕒 Treffen: {m_date_fmt} um {ti.get('meet_time','')}")
    except Exception:
        pass

    colL, colR = st.columns([0.55, 0.45])

    with colL:
        if address:
            st.write(f"**Adresse:** {address}")
        else:
            st.warning("Für Karte/Wetter bitte Straße & Ort eintragen.")

        if home_city and city:
            d_km = calculate_distance(home_city, city)
            if d_km is not None:
                st.metric("📏 Entfernung (ca.)", f"{d_km} km")

        if city:
            w = get_weather_data(city)
            if w and "current_weather" in w:
                cw = w["current_weather"]
                st.metric(f"{cw.get('icon','🌡️')} Aktuell", f"{cw.get('temperature','?')} °C")
                forecast = w.get("forecast", [])[:7]
                if forecast:
                    st.caption("☀️ Wettervorhersage (7 Tage)")
                    cols = st.columns(len(forecast))
                    for i, day in enumerate(forecast):
                        try:
                            d_obj = datetime.date.fromisoformat(day["date"])
                            day_label = d_obj.strftime("%a")
                        except Exception:
                            day_label = str(day.get("date", ""))[:10]

                        with cols[i]:
                            st.markdown(
                                f"""
                                <div class="weather-card">
                                    <div style="font-size: 0.9rem;">{day_label}</div>
                                    <div class="weather-icon">{day.get('icon','🌡️')}</div>
                                    <div class="weather-temp">{int(day.get('max',0))}°</div>
                                    <div style="font-size: 0.8rem; color: gray;">{int(day.get('min',0))}°</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

    with colR:
        if address:
            html(get_map_html(address), height=400)
        else:
            st.empty()

    st.divider()

    render_online_bar(data, trip_name, user)
    render_chat(data, trip_name, user)
>>>>>>> 656eda1 (Initial working version: Chat + Checklist with Supabase storage)

with tab2:
    render_checklist(data, trip_name, user)

with tab3:
    render_info(data, trip_name)

with tab4:
    render_costs(data, trip_name, user)

with tab5:
    render_photos(data, trip_name)