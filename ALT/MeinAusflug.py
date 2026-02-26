import streamlit as st
import pandas as pd
import json
import os
import base64
import requests
import datetime
from io import BytesIO
from PIL import Image
from geopy.geocoders import Nominatim
import urllib.parse

# --- KONFIGURATION & DATEN ---
DB_FILE = "reisen_daten.json"
ADMIN_PASSWORD = "Admin123" 
APP_ICON_URL = "https://github.com/Zornemann/MeinAusflug/blob/main/MeinAusflug.jpg?raw=true" 

TEMPLATES = {
    "🛶 Kanu-Tour": ["Schwimmweste", "Wasserdichte Tonne", "Sonnenschutz", "Wechselkleidung", "Paddel-Handschuhe"],
    "⛺ Camping": ["Zelt", "Isomatte", "Schlafsack", "Gaskocher", "Taschenlampe", "Powerbank"],
    "🥾 Wandern": ["Wanderschuhe", "Regenjacke", "Erste-Hilfe-Set", "Trinkflasche", "Wanderkarte"]
}

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                if "trips" in data: return data
            except: pass
    return {"trips": {}}

def save_all_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_empty_trip(name):
    return {
        "name": name, "status": "In Planung",
        "participants": {"Dennis": "Kanu2024"}, 
        "info": {"Name1": "", "Name2": "", "Strasse": "", "PLZ": "", "Ort": "", "Homepage": "https://", "Kontakt": "", "Startdatum": None, "Enddatum": None, "Treffpunkt": "", "Ankunft": None},
        "categories": ["Verpflegung", "Ausstattung", "Sonstiges"],
        "tasks": [], "messages": [], "expenses": [], "images": [],
        "last_read": {}
    }

if 'all_db' not in st.session_state:
    st.session_state.all_db = load_all_data()

# --- MOBILE APP HEADER & STYLING ---
st.set_page_config(page_title="MeinAusflug PRO", layout="wide", page_icon="🌍")

st.markdown(f"""
    <link rel="icon" href="{APP_ICON_URL}">
    <link rel="apple-touch-icon" href="{APP_ICON_URL}">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        .stButton button {{ width: 100%; height: 3.5rem; border-radius: 12px; font-weight: bold; }}
        .chat-bubble {{ padding: 12px; border-radius: 18px; margin-bottom: 8px; font-size: 15px; line-height: 1.4; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{ height: 45px; white-space: nowrap; font-size: 14px; }}
    </style>
""", unsafe_allow_html=True)

# --- HILFSFUNKTIONEN ---
def get_weather_forecast(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto&forecast_days=3"
    try:
        res = requests.get(url).json()
        return res['daily']
    except: return None

def get_weather_emoji(code):
    mapping = {0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 51: "🌦️", 61: "🌧️", 71: "❄️", 95: "⚡"}
    return mapping.get(code, "🌡️")

# --- LOGIN-SYSTEM ---
def check_auth():
    if "auth_user" not in st.session_state:
        st.title("🔐 Crew-Login")
        all_trips = list(st.session_state.all_db["trips"].keys())
        if not all_trips:
            st.warning("Keine Reisen vorhanden.")
            pwd = st.text_input("Admin-Passwort", type="password")
            if st.button("Anmelden"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.auth_user = "Admin"; st.rerun()
            return False
        sel_trip = st.selectbox("Reise wählen:", all_trips)
        trip_ref = st.session_state.all_db["trips"][sel_trip]
        user = st.selectbox("Wer bist du?", list(trip_ref["participants"].keys()))
        pwd = st.text_input("Passwort", type="password")
        c1, c2 = st.columns(2)
        if c1.button("Login"):
            if trip_ref["participants"].get(user) == pwd:
                st.session_state.auth_user = user
                st.session_state.current_trip = sel_trip; st.rerun()
            else: st.error("Passwort falsch!")
        if c2.button("Notfall-Admin Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.auth_user = "Admin"; st.session_state.current_trip = sel_trip; st.rerun()
            else: st.error("Admin-Passwort falsch!")
        return False
    return True

if check_auth():
    geolocator = Nominatim(user_agent="MeinAusflug_App_Final_V1")
    trip = st.session_state.all_db["trips"][st.session_state.current_trip]

    # --- SIDEBAR ---
    with st.sidebar:
        st.header(f"📱 {st.session_state.auth_user}")
        if st.button("🚪 Abmelden"):
            for k in ["auth_user", "current_trip"]: 
                if k in st.session_state: del st.session_state[k]
            st.rerun()
        st.divider()
        trip["status"] = st.selectbox("Reise-Status", ["In Planung", "Aktiv", "Abgeschlossen"], 
                                     index=["In Planung", "Aktiv", "Abgeschlossen"].index(trip.get("status", "In Planung")))
        with st.expander("👤 Crew verwalten"):
            np = st.text_input("Name"); npw = st.text_input("PW", type="password")
            if st.button("Hinzufügen"):
                trip["participants"][np] = npw; save_all_data(st.session_state.all_db); st.rerun()
        
        for p in list(trip["participants"].keys()):
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"🚣 {p}")
            if c2.button("🗑️", key=f"del_p_{p}"):
                if len(trip["participants"]) > 1:
                    del trip["participants"][p]
                    save_all_data(st.session_state.all_db); st.rerun()

    # Chat-Badge Logik
    lr = trip.get("last_read", {}).get(st.session_state.auth_user, "2000")
    unread = len([m for m in trip["messages"] if m.get("time", "2000") > lr])
    chat_label = f"💬 Chat ({unread})" if unread > 0 else "💬 Chat"

    t1, t2, t3, t4, t5 = st.tabs(["🏠 Info", "✅ Check", "💰 Geld", chat_label, "📸 Fotos"])

    # --- TAB 1: INFOS & KARTE ---
    with t1:
        col_a, col_b = st.columns([1, 1.2])
        with col_a:
            st.subheader("📝 Ziel-Informationen")
            ti = trip["info"]
            ti["Name1"] = st.text_input("Ziel Name", ti.get("Name1", ""))
            ti["Name2"] = st.text_input("Zusatz", ti.get("Name2", ""))
            ti["Strasse"] = st.text_input("Straße & Hausnr.", ti.get("Strasse", ""))
            c_p, c_o = st.columns([0.3, 0.7])
            ti["PLZ"] = c_p.text_input("PLZ", ti.get("PLZ", ""))
            ti["Ort"] = c_o.text_input("Ort", ti.get("Ort", ""))
            # NEU: Layout-Wunsch
            ti["Homepage"] = st.text_input("Startseite", ti.get("Homepage", "https://"))
            ti["Kontakt"] = st.text_input("Telefon / Kontakt", ti.get("Kontakt", ""))
            
            st.divider(); st.write("**Zeitraum**")
            cv, cb = st.columns(2)
            try:
                ds = datetime.datetime.strptime(ti["Startdatum"], "%Y-%m-%d").date() if ti.get("Startdatum") else datetime.date.today()
                de = datetime.datetime.strptime(ti["Enddatum"], "%Y-%m-%d").date() if ti.get("Enddatum") else datetime.date.today()
            except: ds = de = datetime.date.today()
            ns = cv.date_input("von", ds); ne = cb.date_input("bis", de)
            if ne < ns: ne = ns; st.warning("Enddatum korrigiert.")
            ti["Startdatum"], ti["Enddatum"] = ns.strftime("%Y-%m-%d"), ne.strftime("%Y-%m-%d")
            
            ti["Treffpunkt"] = st.text_input("Treffpunkt-Details", ti.get("Treffpunkt", ""))
            st.write("**Ankunft am Treffpunkt**")
            try: dv = datetime.datetime.strptime(ti["Ankunft"], "%Y-%m-%d %H:%M") if ti.get("Ankunft") else datetime.datetime.now()
            except: dv = datetime.datetime.now()
            cad, cat = st.columns(2)
            ad = cad.date_input("Datum", dv.date(), key="ad_main"); at = cat.time_input("Zeit", dv.time(), key="at_main")
            ti["Ankunft"] = f"{ad.strftime('%Y-%m-%d')} {at.strftime('%H:%M')}"
            
            trip["info"] = ti; save_all_data(st.session_state.all_db)
            
        with col_b:
            st.subheader("🗺️ Karte & Wetter")
            addr = f"{ti.get('Strasse', '')}, {ti.get('PLZ', '')} {ti.get('Ort', '')}".strip()
            if len(addr) > 5:
                z_lvl = st.slider("Zoom", 1, 20, 15)
                map_url = f"https://www.google.com/maps?q={urllib.parse.quote(addr)}&z={z_lvl}&output=embed"
                st.components.v1.iframe(map_url, height=400)
                st.markdown(f'''<a href="https://www.google.com/maps?q={urllib.parse.quote(addr)}" target="_blank"><button style="width:100%; height:50px; background:#4285F4; color:white; border:none; border-radius:10px; font-weight:bold;">🚀 Navigation starten</button></a>''', unsafe_allow_html=True)
                if ti.get("Ort"):
                    st.divider(); loc = geolocator.geocode(ti["Ort"])
                    if loc:
                        w = get_weather_forecast(loc.latitude, loc.longitude)
                        if w:
                            w_cols = st.columns(3)
                            for i in range(3):
                                with w_cols[i]:
                                    st.metric(w['time'][i][-5:], f"{get_weather_emoji(w['weathercode'][i])} {w['temperature_2m_max'][i]}°")
                                    st.caption(f"💧 {w['precipitation_sum'][i]}mm")

      # --- TAB 2: PRÜFEN (CHECKLISTEN & VORLAGEN) ---
    with t2:
        st.header("✅ Was bringe ich mit?")
        
        # Initialisierung der Vorlagen-Struktur, falls nicht vorhanden
        if "custom_templates" not in trip:
            trip["custom_templates"] = {}
        
        crew_namen = list(trip["participants"].keys())

        # --- 1. FILTER & VORLAGEN-LOGIK ---
        col_f1, col_f2 = st.columns([0.6, 0.4])
        
        with col_f1:
            filter_who_t = st.selectbox("🔍 Teilnehmer filtern:", ["Alle"] + crew_namen, key="ft")
        
        with col_f2:
            with st.expander("✨ Vorlagen verwalten"):
                # Neue Vorlage erstellen
                t_name = st.text_input("Name der neuen Vorlage", placeholder="z.B. Grillabend")
                t_items = st.text_area("Was wird benötigt? (Eines pro Zeile)")
                if st.button("Vorlage speichern"):
                    if t_name and t_items:
                        items_list = [i.strip() for i in t_items.split("\n") if i.strip()]
                        trip["custom_templates"][t_name] = items_list
                        save_all_data(st.session_state.all_db)
                        st.success(f"Vorlage '{t_name}' erstellt!")
                        st.rerun()
                
                st.divider()
                
                # Vorhandene Vorlagen laden oder löschen
                if trip["custom_templates"]:
                    sel_tpl = st.selectbox("Eigene Vorlage wählen:", list(trip["custom_templates"].keys()))
                    c_load, c_del_tpl = st.columns(2)
                    if c_load.button("📥 Items laden"):
                        for item in trip["custom_templates"][sel_tpl]:
                            trip["tasks"].append({"job": item, "cat": "Sonstiges", "who": [], "done": False})
                        save_all_data(st.session_state.all_db)
                        st.rerun()
                    if c_del_tpl.button("🗑️ Vorlage weg"):
                        del trip["custom_templates"][sel_tpl]
                        save_all_data(st.session_state.all_db)
                        st.rerun()
                else:
                    st.info("Noch keine Vorlagen erstellt.")

        # --- 2. EINZELNES ITEM HINZUFÜGEN ---
        with st.expander("➕ Neues Item hinzufügen"):
            nj = st.text_input("Was bringe ich mit?", placeholder="Was genau?")
            nw = st.multiselect("Wer bringt es mit?", crew_namen)
            if st.button("Hinzufügen"):
                if nj:
                    trip["tasks"].append({"job": nj, "cat": "Sonstiges", "who": nw, "done": False})
                    save_all_data(st.session_state.all_db)
                    st.rerun()

        st.divider()

        # --- 3. ANZEIGE DER LISTE ---
        # Wir nutzen Kategorien nur intern, zeigen sie aber flach an
        tasks_to_show = trip["tasks"]
        if filter_who_t != "Alle":
            tasks_to_show = [x for x in tasks_to_show if filter_who_t in x.get("who", [])]

        if not tasks_to_show:
            st.info("Hier ist noch alles leer. Füge Items hinzu oder lade eine Vorlage!")
        else:
            for i, tk in enumerate(trip["tasks"]):
                # Nur anzeigen, wenn Filter passt
                if filter_who_t == "Alle" or filter_who_t in tk.get("who", []):
                    c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
                    
                    # Status ändern
                    if c1.checkbox("", value=tk["done"], key=f"tk_check_{i}"):
                        trip["tasks"][i]["done"] = not tk["done"]
                        save_all_data(st.session_state.all_db)
                        st.rerun()
                    
                    # Text & Wer
                    wer_text = f" ({', '.join(tk['who'])})" if tk['who'] else " (Offen)"
                    label = f"{'~~' if tk['done'] else '**'}{tk['job']}{'~~' if tk['done'] else '**'}{wer_text}"
                    c2.write(label)
                    
                    # Löschen
                    if c3.button("🗑️", key=f"tk_del_{i}"):
                        trip["tasks"].pop(i)
                        save_all_data(st.session_state.all_db)
                        st.rerun()
                        
    # --- TAB 3: KOSTEN ---
    with t3:
        if trip["expenses"]:
            csv = pd.DataFrame(trip["expenses"]).to_csv(index=False).encode('utf-8')
            st.download_button("📥 CSV Export", data=csv, file_name=f"abrechnung_{trip['name']}.csv", mime='text/csv')
        with st.expander("💸 Neue Ausgabe"):
            am = st.number_input("Euro", min_value=0.0); ds = st.text_input("Zweck")
            if st.button("Speichern") and am > 0:
                trip["expenses"].append({"payer": st.session_state.auth_user, "amount": am, "desc": ds})
                save_all_data(st.session_state.all_db); st.rerun()
        if trip["expenses"]:
            st.dataframe(pd.DataFrame(trip["expenses"]), use_container_width=True)
            tot = sum(e["amount"] for e in trip["expenses"]); sh = tot / len(crew)
            st.info(f"Gesamt: {tot:.2f}€ | Kopf: {sh:.2f}€")
            balances = {p: -sh for p in crew}
            for i in trip["expenses"]: balances[i["payer"]] += i["amount"]
            for p, b in balances.items(): st.write(f"**{p}** {'bekommt' if b > 0 else 'schuldet'} **{abs(b):.2f}€**")

    # --- TAB 4: CHAT ---
    # --- TAB 4: CHAT MIT BEARBEITUNGSFUNKTION ---
    with t4:
        if "last_read" not in trip: trip["last_read"] = {}
        trip["last_read"][st.session_state.auth_user] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_all_data(st.session_state.all_db)
        
        chat_c = st.container(height=450)
        with chat_c:
            for i, m in enumerate(trip["messages"]):
                is_me = m['user'] == st.session_state.auth_user
                msg_text = m.get('text', '') 
                msg_user = m.get('user', 'Unbekannt')
                msg_time = m.get('time', '')[11:16]

                # Spalten für Nachricht + Bearbeiten-Button (nur bei eigenen)
                if is_me:
                    col_msg, col_edit = st.columns([0.85, 0.15])
                    with col_msg:
                        st.markdown(f"""
                            <div style="display: flex; justify-content: flex-end; margin-bottom: 5px;">
                                <div class="chat-bubble" style="background-color: #dcf8c6; color: black; min-width: 80px;">
                                    <small style="color: #555;"><b>{msg_user}</b></small><br>{msg_text}
                                    <div style="text-align: right; font-size: 10px; color: gray; margin-top: 4px;">{msg_time}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Bearbeitungs-Dialog für eigene Nachrichten
                    with col_edit:
                        if st.button("✏️", key=f"edit_btn_{i}"):
                            st.session_state[f"editing_{i}"] = True
                    
                    if st.session_state.get(f"editing_{i}"):
                        with st.form(key=f"form_edit_{i}"):
                            new_text = st.text_input("Nachricht bearbeiten", value=msg_text)
                            if st.form_submit_button("Speichern"):
                                trip["messages"][i] = new_text
                                # Optional: Markierung als bearbeitet
                                if " (bearbeitet)" not in trip["messages"][i]:
                                    trip["messages"][i] += " (bearbeitet)"
                                save_all_data(st.session_state.all_db)
                                del st.session_state[f"editing_{i}"]
                                st.rerun()
                            if st.form_submit_button("Abbrechen"):
                                del st.session_state[f"editing_{i}"]
                                st.rerun()
                else:
                    # Nachrichten von anderen (ohne Bearbeiten-Button)
                    st.markdown(f"""
                        <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                            <div class="chat-bubble" style="background-color: #f0f0f0; color: black; min-width: 80px;">
                                <small style="color: #555;"><b>{msg_user}</b></small><br>{msg_text}
                                <div style="text-align: right; font-size: 10px; color: gray; margin-top: 4px;">{msg_time}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Neue Nachricht senden
        with st.form("msg_input", clear_on_submit=True):
            c1, c2 = st.columns([0.85, 0.15])
            txt = c1.text_input("Nachricht", placeholder="Tippen...", label_visibility="collapsed")
            if c2.form_submit_button("✈️") and txt:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                trip["messages"].append({"user": st.session_state.auth_user, "text": txt, "time": now})
                save_all_data(st.session_state.all_db)
                st.rerun()
                
    # --- TAB 5: FOTOS ---
    with t5:
        up = st.file_uploader("📷 Bilder wählen", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        if st.button("Upload"):
            for f in up:
                im = Image.open(f); im.thumbnail((800, 800))
                buf = BytesIO(); im.save(buf, format="JPEG", quality=75)
                trip["images"].append({"data": base64.b64encode(buf.getvalue()).decode(), "caption": ""})
            save_all_data(st.session_state.all_db); st.rerun()
        
        cols = st.columns(2)
        for i, img_obj in enumerate(trip["images"]):
            with cols[i % 2]:
                dec = base64.b64decode(img_obj["data"])
                st.image(dec, use_container_width=True)
                with st.expander("⚙️ Bearbeiten"):
                    cp = st.text_input("Caption", img_obj.get("caption", ""), key=f"c_{i}")
                    if cp != img_obj.get("caption", ""): trip["images"][i]["caption"] = cp; save_all_data(st.session_state.all_db)
                    if st.button("🔄 Drehen", key=f"r_{i}"):
                        pi = Image.open(BytesIO(dec)).rotate(-90, expand=True)
                        b = BytesIO(); pi.save(b, format="JPEG")
                        trip["images"][i]["data"] = base64.b64encode(b.getvalue()).decode(); save_all_data(st.session_state.all_db); st.rerun()
                    if st.button("🗑️ Löschen", key=f"li_{i}"): trip["images"].pop(i); save_all_data(st.session_state.all_db); st.rerun()
                if img_obj["caption"]: st.caption(img_obj["caption"])