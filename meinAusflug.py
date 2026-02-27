import streamlit as st
import datetime
import requests
import urllib.parse
from streamlit.components.v1 import html

# Externe Bibliotheken
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Eigene Module importieren
from config import APP_NAME, APP_ICON_URL, ADMIN_PASSWORD, APP_URL
from storage import load_db, save_db, new_id
from ui_chat import render_chat
from ui_checklist import render_checklist
from ui_info import render_info
from ui_costs import render_costs
from ui_photos import render_photos
from utils_email import send_system_email, get_mailto_link

# ----------------------------------------------------
# 1. CONFIG
# ----------------------------------------------------
st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

# CSS für größere Wetter-Anzeige & Chat-Styling
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

# ----------------------------------------------------
# 2. HILFSFUNKTIONEN (Wetter, Karte, Distanz)
# ----------------------------------------------------
def get_map_html(address):
    """Erzeugt ein Google Maps Iframe ohne API-Key."""
    if not address or len(address) < 3: return ""
    encoded_addr = urllib.parse.quote(address)
    # FIX: Doppelte geschweifte Klammer entfernt und Pfad /maps?q= sichergestellt
    return f'<iframe width="100%" height="400" frameborder="0" style="border:0" src="https://maps.google.com/maps?q={encoded_addr}&t=&z=14&ie=UTF8&iwloc=&output=embed" allowfullscreen></iframe>'

def get_weather_data(city):
    """Holt Wetterdaten und 7-Tage-Vorhersage mit expliziten API-Pfaden."""
    if not city: return None
    try:
        # PFAD GEPRÜFT: /v1/search?name= muss vorhanden sein
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
        geo_res = requests.get(geo_url, timeout=10).json()
        
        if "results" in geo_res and len(geo_res["results"]) > 0:
            # FIX: Zugriff auf das erste Element [0] sichergestellt
            res = geo_res["results"][0]
            lat, lon = res["latitude"], res["longitude"]
            
            # PFAD GEPRÜFT: /v1/forecast?latitude= muss vorhanden sein
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&current_weather=true&timezone=Europe%2FBerlin"
            w_res = requests.get(w_url, timeout=10).json()
            
            icons = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 51: "🌦️", 61: "🌧️", 71: "❄️", 95: "⚡"}
            
            if "current_weather" in w_res:
                w_res["current_weather"]["icon"] = icons.get(w_res["current_weather"]["weathercode"], "🌡️")
            
            # Vorhersage-Daten aufbereiten
            forecast = []
            if "daily" in w_res:
                for i in range(min(7, len(w_res["daily"]["time"]))):
                    day_code = w_res["daily"]["weathercode"][i]
                    forecast.append({
                        "date": w_res["daily"]["time"][i],
                        "max": w_res["daily"]["temperature_2m_max"][i],
                        "min": w_res["daily"]["temperature_2m_min"][i],
                        "icon": icons.get(day_code, "🌡️")
                    })
            w_res["forecast"] = forecast
            return w_res
    except Exception as e:
        print(f"Fehler bei Wetter-Abfrage: {e}")
        return None
    return None

def calculate_distance(home_city, dest_city):
    if not home_city or not dest_city: return None
    try:
        geolocator = Nominatim(user_agent="mein_ausflug_pro_planner")
        loc1 = geolocator.geocode(home_city)
        loc2 = geolocator.geocode(dest_city)
        if loc1 and loc2:
            return round(geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km, 1)
    except: return None

# ----------------------------------------------------
# 3. DATENBANK INITIALISIERUNG
# ----------------------------------------------------
if "db" not in st.session_state:
    st.session_state.db = load_db()
data = st.session_state.db

def create_trip(name):
    return {
        "name": name, "status": "In Planung", "participants": {}, "messages": [], "tasks": [], "expenses": [], "images": [],
        "details": {
            "destination": "", "loc_name": "", "extra": "", "street": "", "plz": "", "city": "",
            "start_date": str(datetime.date.today()), "end_date": str(datetime.date.today() + datetime.timedelta(days=3)),
            "meet_date": str(datetime.date.today()), "meet_time": "18:00"
        }
    }

# ----------------------------------------------------
# 4. LOGIN UI
# ----------------------------------------------------
def login_ui():
    st.title("🔐 Reise-Login")
    if "trips" not in data: data["trips"] = {}
    trips = list(data["trips"].keys())
    if not trips:
        new_name = st.text_input("Erste Reise erstellen", key="login_new_t")
        if st.button("Starten"):
            data["trips"][new_name] = create_trip(new_name)
            save_db(data); st.rerun()
        return
    trip_sel = st.selectbox("Reise wählen", trips, key="login_sel")
    user_in = st.text_input("Dein Name", key="login_user")
    pwd_in = st.text_input("Passwort", type="password", key="login_pwd")
    if st.button("Anmelden / Beitreten"):
        trip = data["trips"][trip_sel]
        if isinstance(trip.get("participants"), list):
            trip["participants"] = {n: {"password": ADMIN_PASSWORD} for n in trip["participants"]}
        participants = trip.get("participants", {})
        if (user_in in participants and participants[user_in]["password"] == pwd_in) or (pwd_in == ADMIN_PASSWORD and pwd_in != ""):
            if user_in not in participants: participants[user_in] = {"password": pwd_in}
            save_db(data)
            st.session_state.user, st.session_state.trip = user_in, trip_sel
            st.rerun()
        else: st.error("Login fehlgeschlagen.")

# ----------------------------------------------------
# 5. HAUPT APP
# ----------------------------------------------------
if "user" not in st.session_state:
    login_ui()
else:
    user, trip_name = st.session_state.user, st.session_state.trip
    trip = data["trips"][trip_name]
    if "details" not in trip: trip["details"] = create_trip(trip_name)["details"]

    with st.sidebar:
        if APP_ICON_URL: 
            st.image(APP_ICON_URL, width=120)
        
        st.header(f"👤 {user}")
        
        with st.expander("🔑 Passwort ändern"):
            new_p = st.text_input("Neues Passwort", type="password", key="s_pw")
            if st.button("Speichern", key="s_pw_b"):
                trip["participants"][user]["password"] = new_p
                save_db(data)
                st.success("Geändert!")
        
        st.divider()
        st.subheader("✉️ Freunde einladen")
        f_mail = st.text_input("E-Mail Adresse", key="s_mail")
        
        if f_mail:
            subj = f"Einladung: {trip_name}"
            body = f"Komm in unsere Reise-App: {APP_URL}\nLogin: {f_mail.split('@')}\nPasswort: {ADMIN_PASSWORD}"
            
            # KORREKTUR: Alle folgenden Zeilen müssen unter das 'if st.button' eingerückt sein!
            if st.button("✉️ Einladung abschicken", key="s_mail_b"):
                with st.spinner("Sende..."):
                    ok, msg = send_system_email(f_mail, subj, body)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
            
            st.markdown(f'<a href="{get_mailto_link(f_mail, subj, body)}" target="_blank">📧 Mail-Programm öffnen</a>', unsafe_allow_html=True)
        
        if st.button("🚪 Abmelden", key="s_logout"):
            for key in ["user", "trip"]: 
                if key in st.session_state: 
                    del st.session_state[key]
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Startseite", "🧭 Ausrüstung", "📝 Infos", "💰 Kosten", "📸 Fotos"])

    with tab1:
        st.title(f"🌍 {trip_name}")
        with st.expander("✏️ Reisedetails & Treffpunkt bearbeiten"):
            c1, c2 = st.columns(2)
            with c1:
                e_dest = st.text_input("Ausflugsziel", value=trip["details"]["destination"], key="t1_dest")
                e_loc = st.text_input("Unterkunft Name", value=trip["details"]["loc_name"], key="t1_loc")
                e_home = st.text_input("Dein Startort (für Distanz)", key="t1_home")
                sd = datetime.date.fromisoformat(trip["details"]["start_date"])
                ed = datetime.date.fromisoformat(trip["details"]["end_date"])
                e_range = st.date_input("Zeitraum", [sd, ed], key="t1_range")
            with c2:
                e_str = st.text_input("Straße & Nr.", value=trip["details"]["street"], key="t1_str")
                e_plz = st.text_input("PLZ", value=trip["details"]["plz"], key="t1_plz")
                e_city = st.text_input("Ort", value=trip["details"]["city"], key="t1_city")
                md = datetime.date.fromisoformat(trip["details"]["meet_date"])
                mt_str = trip["details"].get("meet_time", "18:00")
                mt = datetime.time.fromisoformat(mt_str if ":" in mt_str else "18:00")
                mc1, mc2 = st.columns(2)
                e_md = mc1.date_input("Treffen am", md, key="t1_md")
                e_mt = mc2.time_input("Um", mt, key="t1_mt")
            if st.button("💾 Speichern", key="t1_save"):
                s_s = str(e_range) if isinstance(e_range, (list, tuple)) and len(e_range) > 0 else trip["details"]["start_date"]
                e_s = str(e_range) if isinstance(e_range, (list, tuple)) and len(e_range) > 1 else s_s
                trip["details"].update({
                    "destination": e_dest, "loc_name": e_loc, "street": e_str, "plz": e_plz, "city": e_city,
                    "start_date": s_s, "end_date": e_s, "meet_date": str(e_md), "meet_time": e_mt.strftime("%H:%M")
                })
                save_db(data); st.rerun()

        st.divider()
        
 # --- DASHBOARD ANZEIGE ---
        s_date_fmt = datetime.date.fromisoformat(trip['details']['start_date']).strftime('%d.%m.%Y')
        e_date_fmt = datetime.date.fromisoformat(trip['details']['end_date']).strftime('%d.%m.%Y')
        st.markdown(f"### 📅 Reisezeitraum: **{s_date_fmt}** bis **{e_date_fmt}**")
        
        d1, d2 = st.columns([0.6, 0.4])
        with d1:
            st.markdown(f"## 📍 {trip['details']['destination'] or 'Ziel festlegen'}")
            if trip["details"]["city"]:
                st.markdown(f"#### 🏠 {trip['details']['loc_name']}")
                st.markdown(f"##### {trip['details']['street']}, {trip['details']['plz']} {trip['details']['city']}")
                
                m_date_fmt = datetime.date.fromisoformat(trip['details']['meet_date']).strftime('%d.%m.%Y')
                st.warning(f"### 🕒 Treffpunkt: **{m_date_fmt}** um **{trip['details']['meet_time']}** Uhr")
                
                # Wetter & Entfernung
                w_c1, w_c2 = st.columns(2)
                if e_home:
                    dist = calculate_distance(e_home, trip["details"]["city"])
                    if dist: w_c1.metric("🚗 Entfernung", f"{dist} km")
                
                weather = get_weather_data(trip["details"]["city"])
                if weather:
                    w_c2.metric(f"{weather['current_weather']['icon']} Aktuell", f"{weather['current_weather']['temperature']} °C")
                    
                    st.write("---")
                    st.subheader("☀️ Wettervorhersage nächsten 7 Tage")
                    cols = st.columns(7)
                    for idx, day in enumerate(weather["forecast"]):
                        with cols[idx]:
                            d_obj = datetime.date.fromisoformat(day["date"])
                            st.markdown(f"""
                                <div class="weather-card">
                                    <div style="font-size: 0.9rem;">{d_obj.strftime('%a')}</div>
                                    <div class="weather-icon">{day['icon']}</div>
                                    <div class="weather-temp">{int(day['max'])}°</div>
                                    <div style="font-size: 0.8rem; color: gray;">{int(day['min'])}°</div>
                                </div>
                            """, unsafe_allow_html=True)
        with d2:
            if trip["details"]["street"] and trip["details"]["city"]:
                full_addr = f"{trip['details']['street']}, {trip['details']['plz']} {trip['details']['city']}"
                html(get_map_html(full_addr), height=400)

        # --- CHAT BEREICH ---
        st.divider()
        chat_placeholder = st.container(height=450, border=True)

        with chat_placeholder:
            render_chat(data, trip_name, user)
            
            # JavaScript für Auto-Scroll nach unten
            st.components.v1.html(f"""
                <script>
                function fixScroll() {{
                    const container = window.parent.document.querySelector('div[data-testid="stVerticalBlockBorderWrapper"] div[style*="overflow: auto"]');
                    if (container) {{
                        container.scrollTop = container.scrollHeight;
                    }}
                }}
                fixScroll();
                setTimeout(fixScroll, 500);
                setTimeout(fixScroll, 1500);
                </script>
            """, height=0)

        # Eingabemaske UNTER dem Container
        with st.form("new_msg_form", clear_on_submit=True):
            col_input, col_btn = st.columns([0.8, 0.2])
            new_txt = col_input.text_input("Nachricht", label_visibility="collapsed", placeholder="Schreibe etwas...")
            if col_btn.form_submit_button("👉 Abschicken") and new_txt:
                # SPEICHER-LOGIK ERGÄNZT
                new_entry = {
                    "id": new_id("msg"),
                    "user": user,
                    "text": new_txt,
                    "time": datetime.datetime.now().isoformat(),
                    "read_by": [user]
                }
                trip["messages"].append(new_entry)
                save_db(data)
                st.rerun()

    # --- ANDERE TABS ---
    with tab2: render_checklist(data, trip_name, user)
    with tab3: render_info(data, trip_name)
    with tab4: render_costs(data, trip_name, user)
    with tab5: render_photos(data, trip_name)
    
    save_db(data)

    # --- ADMIN MENÜ (Muss in den sidebar-Block oben in deinem Code!) ---
    # Falls du es hier unten lässt, wird es nur im Hauptbereich angezeigt.
    # Verschiebe diesen Block am besten in das 'with st.sidebar:' deiner main.py
    with st.sidebar:
        st.divider()
        with st.expander("🛠️ Admin-Bereich"):
            admin_pw = st.text_input("Admin-Passwort", type="password", key="admin_access_pw")
            if admin_pw == ADMIN_PASSWORD:
                st.warning("Vorsicht: Aktionen sind endgültig!")
                if st.button(f"🗑️ '{trip_name}' löschen", key="admin_del_current"):
                    if len(data["trips"]) > 1:
                        del data["trips"][trip_name]
                        save_db(data)
                        del st.session_state["user"]
                        st.rerun()
                if st.button("🧨 Alle Reisen löschen", key="admin_del_all"):
                    data["trips"] = {}
                    save_db(data)
                    del st.session_state["user"]
                    st.rerun()
                
                import json
                db_str = json.dumps(data, indent=4, ensure_ascii=False)
                st.download_button("📥 Datenbank-Backup", data=db_str, file_name="backup.json", mime="application/json")