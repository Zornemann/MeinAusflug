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
        "participants": {},  # Wird als Dictionary {Name: {password: ...}} genutzt
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

    # Sicherstellen, dass der "trips"-Key existiert
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
            else:
                st.warning("Bitte einen Namen eingeben.")
        return

    trip_name = st.selectbox("Reise wählen", trips)
    user = st.text_input("Dein Nutzername")
    pwd = st.text_input("Passwort", type="password")

    if st.button("Login / Beitreten"):
        if not user:
            st.error("Bitte einen Nutzernamen eingeben.")
            return

        trip = data["trips"][trip_name]
        
        # Prüfung: Existiert der Nutzer bereits in dieser Reise?
        user_exists = user in trip["participants"]
        
        # FALL 1: Bekannter Nutzer loggt sich ein
        if user_exists and trip["participants"][user].get("password") == pwd:
            st.session_state.user = user
            st.session_state.trip = trip_name
            st.rerun()
            
        # FALL 2: Admin-Login ODER neuer Nutzer tritt mit Admin-PW bei
        elif pwd == ADMIN_PASSWORD and pwd != "":
            if not user_exists:
                # Nutzer neu anlegen
                trip["participants"][user] = {"password": pwd}
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
    
    # Sicherheitshalber prüfen, ob die Reise noch existiert
    if trip_name not in data["trips"]:
        st.error("Reise wurde gelöscht.")
        del st.session_state["user"]
        st.rerun()
        
    trip = data["trips"][trip_name]

    # Sidebar für Nutzer-Info und Logout
    with st.sidebar:
        st.header(f"👤 {user}")
        st.write(f"📍 Reise: **{trip_name}**")
        if st.button("Abmelden"):
            del st.session_state["user"]
            del st.session_state["trip"]
            st.rerun()

    # Tabs für die verschiedenen Funktionen
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Start (Chat)",
        "🧭 Ausrüstung / Verpflegung",
        "📝 Ziel-Infos",
        "💰 Kosten",
        "📸 Fotos"
    ])

    with tab1:
        render_chat(data, trip_name, user)

    with tab2:
        render_checklist(data, trip_name, user)

    with tab3:
        render_info(data, trip_name)

    with tab4:
        render_costs(data, trip_name, user)

    with tab5:
        render_photos(data, trip_name)

    # Automatisches Speichern am Ende jeder Interaktion
    save_db(data)