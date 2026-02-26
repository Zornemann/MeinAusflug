import streamlit as st
import datetime
import urllib.parse
from geopy.geocoders import Nominatim
from storage import save_db
from utils import generate_qr_code
from config import APP_URL

def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip["info"]

    st.subheader("📝 Ziel-Informationen")

    # ----------------------------
    # Name, Adresse
    # ----------------------------
    ti["Name1"] = st.text_input("Ziel Name", ti.get("Name1",""))
    ti["Name2"] = st.text_input("Zusatz", ti.get("Name2",""))
    ti["Strasse"] = st.text_input("Straße", ti.get("Strasse",""))

    cplz, cort = st.columns([0.3,0.7])
    ti["PLZ"] = cplz.text_input("PLZ", ti.get("PLZ",""))
    ti["Ort"] = cort.text_input("Ort", ti.get("Ort",""))

    ti["Homepage"] = st.text_input("Homepage", ti.get("Homepage","https://"))
    ti["Kontakt"] = st.text_input("Kontakt", ti.get("Kontakt",""))

    # ----------------------------
    # Zeitraum
    # ----------------------------
    c1, c2 = st.columns(2)
    try:
        sd = datetime.date.fromisoformat(ti["Startdatum"])
    except:
        sd = datetime.date.today()

    try:
        ed = datetime.date.fromisoformat(ti["Enddatum"])
    except:
        ed = sd

    sd_new = c1.date_input("Von", sd)
    ed_new = c2.date_input("Bis", ed)

    if ed_new < sd_new:
        ed_new = sd_new
        st.warning("Enddatum angepasst.")

    ti["Startdatum"] = sd_new.isoformat()
    ti["Enddatum"] = ed_new.isoformat()

    # ----------------------------
    # Ankunft automatisch = Von-Datum
    # ----------------------------
    try:
        ad_ts = datetime.datetime.fromisoformat(ti["Ankunft"])
    except:
        ad_ts = datetime.datetime.combine(sd_new, datetime.time(9,0))

    ad_date = st.date_input("Ankunfts-Datum", ad_ts.date())
    ad_time = st.time_input("Ankunfts-Zeit", ad_ts.time())

    ti["Ankunft"] = f"{ad_date.isoformat()} {ad_time.strftime('%H:%M')}"

    trip["info"] = ti
    save_db(data)

    st.divider()

    # ----------------------------
    # QR-Code
    # ----------------------------
    st.subheader("📲 QR-Code zum Öffnen der App")
    qr = generate_qr_code(APP_URL)
    st.image(qr, width=200)

    st.write("Link zur App:", APP_URL)

    st.divider()

    # ----------------------------
    # Karte
    # ----------------------------
    st.subheader("🗺️ Karte")
    address = f"{ti['Strasse']}, {ti['PLZ']} {ti['Ort']}"

    if len(address.strip()) > 5:
        zoom = st.slider("Zoom", 1, 18, 15)
        link = f"https://www.google.com/maps?q={urllib.parse.quote(address)}&z={zoom}&output=embed"
        st.components.v1.iframe(link, height=400)

        st.markdown(
            f"<a href='https://www.google.com/maps?q={urllib.parse.quote(address)}' target='_blank'>"
            f"<button style='width:100%; height:50px; background:#4285F4; color:white;'>Navigation starten</button></a>",
            unsafe_allow_html=True
        )
