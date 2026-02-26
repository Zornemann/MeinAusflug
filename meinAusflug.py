import streamlit as st
from config import APP_NAME, APP_ICON_URL, ADMIN_PASSWORD
from storage import load_db, save_db, new_id
from ui_chat import render_chat
from ui_checklist import render_checklist
from ui_info import render_info
from ui_costs import render_costs
from ui_photos import render_photos

# ----------------------------------------------------
# CONFIG (Muss die ALLERERSTE Streamlit-Anweisung sein)
# ----------------------------------------------------
st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

# ----------------------------------------------------
# LOAD DB
# ----------------------------------------------------
if "db" not in st.session_state:
    st.session_state.db = load_db()

data = st.session_state.db

# ----------------------------------------------------
# FUNKTION: NEUE REISE
# ----------------------------------------------------
def create_trip(name):
    return {
        "name": name,
        "status": "In Planung",
        "participants": {},  # Format: {"Name": {"password": "..."}}
        "info": {},
        "messages": [],
        "tasks": [],
        "expenses": [],
        "images": [],
        "last_read": {},
        "log": []
    }

# ----------------------------------------------------
# LOGIN UI
# ----------------------------------------------------
def login_ui():
    st.title("🔐 Login")

    if "trips" not in data:
        data["trips"] = {}

    trips = list(data["trips"].keys())
    
    if not trips:
        st.info("Noch keine Reise angelegt.")
        new_trip_name = st.text_input("Name der neuen Reise")
        if st.button("Reise erstellen"):
            if new_trip_name:
                data["trips"][new_trip_name] = create_trip(new_trip_name)
                save_db(data)
                st.rerun()
        return

    trip_name = st.selectbox("Reise wählen", trips)
    user = st.text_input("Dein Nutzername")
    pwd = st.text_input("Passwort", type="password")

    if st.button("Login / Beitreten"):
        if not user:
            st.error("Bitte einen Nutzernamen eingeben.")
            return

        trip = data["trips"][trip_name]
        
        # --- REPARATUR-LOGIK START ---
        # Falls participants noch eine Liste ist, wandeln wir sie in ein Dictionary um
        if isinstance(trip.get("participants"), list):
            trip["participants"] = {name: {"password": ADMIN_PASSWORD} for name in trip["participants"]}
            save_db(data)
        # --- REPARATUR-LOGIK ENDE ---

        participants = trip.get("participants", {})
        user_data = participants.get(user)
        
        # FALL 1: Nutzer existiert (als Dictionary) und Passwort stimmt
        if isinstance(user_data, dict) and user_data.get("password") == pwd:
            st.session_state.user = user
            st.session_state.trip = trip_name
            st.rerun()
            
        # FALL 2: Neuer Nutzer oder Reparatur alter String-Einträge via Admin-PW
        elif pwd == ADMIN_PASSWORD and pwd != "":
            # Falls Nutzer ein String ist oder gar nicht existiert: Neu anlegen
            participants[user] = {"password": pwd}
            save_db(data)
            st.session_state.user = user
            st.session_state.trip = trip_name
            st.rerun()
        else:
            st.error("Falsches Passwort oder Zugriff verweigert.")

# ----------------------------------------------------
# MAIN APP LOGIK
# ----------------------------------------------------
if "user" not in st.session_state:
    login_ui()
else:
    user = st.session_state.user
    trip_name = st.session_state.trip
    
    if trip_name not in data["trips"]:
        st.error("Reise wurde gelöscht.")
        del st.session_state["user"]
        st.rerun()
        
    trip = data["trips"][trip_name]

    with st.sidebar:
        st.header(f"👤 {user}")
        st.write(f"📍 Reise: **{trip_name}**")
        if st.button("Abmelden"):
            del st.session_state["user"]
            del st.session_state["trip"]
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Start (Chat)", "🧭 Ausrüstung", "📝 Infos", "💰 Kosten", "📸 Fotos"
    ])

    with tab1: render_chat(data, trip_name, user)
    with tab2: render_checklist(data, trip_name, user)
    with tab3: render_info(data, trip_name)
    with tab4: render_costs(data, trip_name, user)
    with tab5: render_photos(data, trip_name)

    save_db(data)