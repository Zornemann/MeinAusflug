import streamlit as st
import urllib.parse

from core.storage import save_db
from core.config import APP_URL


def _qr_image_url(text: str, size: int = 200) -> str:
    payload = urllib.parse.quote(text or "")
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={payload}"


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip.get("details", {})
    if not isinstance(ti, dict):
        ti = {}

    st.subheader("📝 Reise-Zentrale & Quick-Links")
    changed = False

    col1, col2 = st.columns(2)
    with col1:
        new_hp = st.text_input("🌐 Homepage", ti.get("homepage", ti.get("loc_name", "https://")), key=f"info_hp_{trip_name}")
    with col2:
        new_kontakt = st.text_input("📞 Kontakt (Telefon/E-Mail)", ti.get("kontakt", ""), key=f"info_kontakt_{trip_name}")

    if new_hp != ti.get("homepage", ti.get("loc_name", "https://")):
        ti["homepage"] = new_hp
        ti["loc_name"] = new_hp
        changed = True
    if new_kontakt != ti.get("kontakt", ""):
        ti["kontakt"] = new_kontakt
        changed = True

    st.divider()
    st.subheader("👥 Teilnehmer einladen")
    participants = trip.setdefault("participants", {})
    with st.form(f"invite_form_{trip_name}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        email = c2.text_input("E-Mail (optional)")
        add = st.form_submit_button("Teilnehmer hinzufügen", use_container_width=True)
        if add and name.strip():
            participants.setdefault(name.strip(), {
                "display_name": name.strip(),
                "email": email.strip(),
                "status": "accepted",
            })
            save_db(data)
            st.success(f"{name.strip()} hinzugefügt")
            st.rerun()

    if participants:
        for uname, pdata in list(participants.items()):
            row = st.columns([0.35, 0.35, 0.2, 0.1])
            row[0].write((pdata.get("display_name") if isinstance(pdata, dict) else uname) or uname)
            row[1].write((pdata.get("email") if isinstance(pdata, dict) else "") or "—")
            if row[2].button("Einladungslink", key=f"invite_link_{trip_name}_{uname}"):
                invite_link = f"{APP_URL}?trip={urllib.parse.quote(trip_name)}"
                st.code(invite_link)
            if uname != st.session_state.get("user") and row[3].button("🗑️", key=f"remove_participant_{trip_name}_{uname}"):
                participants.pop(uname, None)
                save_db(data)
                st.rerun()

    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    with cq:
        st.image(_qr_image_url(APP_URL, size=220), width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen, um direkt zur App zu gelangen.")
        st.code(APP_URL)
        if st.button("Link anzeigen", key=f"info_copy_link_{trip_name}"):
            st.toast("Link eingeblendet – bitte markieren und kopieren.")

    st.divider()
    st.subheader("🗺️ Navigation")
    address = f"{ti.get('street', '')}, {ti.get('plz', '')} {ti.get('city', '')}".strip().strip(",")
    address = " ".join(address.split())
    if len(address) > 5:
        encoded_addr = urllib.parse.quote(address)
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
        st.link_button("🚗 Navigation in Google Maps starten", google_maps_url, use_container_width=True)
        st.caption(f"Ziel: {address}")
    else:
        st.info("Trage auf der Startseite eine Adresse ein (Straße/PLZ/Ort), um die Navigation zu nutzen.")

    if changed:
        trip["details"] = ti
        save_db(data)
