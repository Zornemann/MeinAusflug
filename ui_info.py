import streamlit as st
import datetime
import urllib.parse
from storage import save_db
from utils import generate_qr_code
from config import APP_URL

def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    # Wir nutzen die "details" Struktur aus der main.py
    ti = trip.get("details", {})

    st.subheader("📝 Reise-Zentrale & Quick-Links")

    # 1. Zusätzliche Infos (Homepage & Kontakt)
    col1, col2 = st.columns(2)
    with col1:
        ti["homepage"] = st.text_input("🌐 Homepage (Unterkunft/Ziel)", ti.get("homepage", "https://"), key="info_hp")
    with col2:
        ti["kontakt"] = st.text_input("📞 Kontakt (Telefon/E-Mail)", ti.get("kontakt", ""), key="info_kontakt")

    # 2. QR-Code zum Teilen
    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    with cq:
        qr_img = generate_qr_code(APP_URL)
        st.image(qr_img, width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen, um direkt zur App zu gelangen.")
        st.code(APP_URL)
        if st.button("Link in Zwischenablage", key="info_copy_link"):
            st.toast("Link kopiert (Strg+C nutzen)")

    st.divider()

    # 3. Schnell-Navigation (Externer Link)
    st.subheader("🗺️ Navigation")
    address = f"{ti.get('street', '')}, {ti.get('plz', '')} {ti.get('city', '')}".strip(", ")
    
    if len(address) > 5:
        # FIX: Korrekter Google Maps Navigations-Link mit /maps/dir/
        encoded_addr = urllib.parse.quote(address)
        google_maps_url = f"https://www.google.com{encoded_addr}"
        
        st.markdown(
            f"""
            <a href='{google_maps_url}' target='_blank'>
                <button style='
                    width:100%; 
                    height:60px; 
                    background-color:#4285F4; 
                    color:white; 
                    border:none; 
                    border-radius:10px; 
                    font-size:18px; 
                    font-weight:bold;
                    cursor:pointer;'>
                    🚗 Navigation in Google Maps App starten
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.caption(f"Ziel: {address}")
    else:
        st.info("Trage auf der Startseite eine Adresse ein, um die Navigation zu nutzen.")

    # Speichern der neuen Felder (homepage, kontakt) in die details
    trip["details"] = ti
    save_db(data)