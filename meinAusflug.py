import streamlit as st
from config import APP_NAME, APP_ICON_URL, ADMIN_PASSWORD
from storage import load_db, save_db, new_id
from ui_chat import render_chat
from ui_checklist import render_checklist
from ui_info import render_info
from ui_costs import render_costs
from ui_photos import render_photos

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
        "participants": {},
        "info": {},
        "messages": [],
        "tasks": [],
        "expenses": [],
        "images": [],
        "last_read": {},
        "log": []
    }

# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
def login_ui():
    st.title("🔐 Login")

    trips = list(data["trips"].keys())
    if not trips:
        st.info("Noch keine Reise angelegt.")
        trip_name = st.text_input("Reise anlegen")
        if st.button("Erstellen"):
            data["trips"][trip_name] = create_trip(trip_name)
            save_db(data)
            st.experimental_rerun()
        return None, None

    trip_name = st.selectbox("Reise wählen", trips)
    user = st.text_input("Nutzername")
    pwd = st.text_input("Passwort", type="password")

    if st.button("Login"):
        trip = data["trips"][trip_name]
        if user in trip["participants"] and trip["participants"][user]["password"] == pwd:
            st.session_state.user = user
            st.session_state.trip = trip_name
            st.experimental_rerun()
        elif pwd == ADMIN_PASSWORD:
            st.session_state.user = "Admin"
            st.session_state.trip = trip_name
            st.experimental_rerun()
        else:
            st.error("Falsches Passwort")

    return None, None

# ----------------------------------------------------
# MAIN UI
# ----------------------------------------------------
if "user" not in st.session_state:
    login_ui()
else:
    user = st.session_state.user
    trip_name = st.session_state.trip
    trip = data["trips"][trip_name]

    st.set_page_config(page_title=APP_NAME, page_icon="🌍", layout="wide")

    with st.sidebar:
        st.header(f"👤 {user}")
        if st.button("Abmelden"):
            del st.session_state["user"]
            del st.session_state["trip"]
            st.experimental_rerun()

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

    save_db(data)
