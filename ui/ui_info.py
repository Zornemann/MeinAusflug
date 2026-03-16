import urllib.parse

import streamlit as st

from core.config import APP_URL
from core.storage import save_db


def _qr_image_url(text: str, size: int = 200) -> str:
    payload = urllib.parse.quote(text or "")
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={payload}"


def _invite_link(trip_name: str) -> str:
    base = (APP_URL or "").rstrip("/")
    if not base:
        return f"?trip={urllib.parse.quote(trip_name)}"
    return f"{base}/?trip={urllib.parse.quote(trip_name)}"


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip.get("details", {})
    if not isinstance(ti, dict):
        ti = {}

    st.subheader("📝 Reise-Zentrale & Quick-Links")
    changed = False

    col1, col2 = st.columns(2)
    with col1:
        new_hp = st.text_input(
            "🌐 Homepage",
            ti.get("homepage", ti.get("loc_name", "https://")),
            key=f"info_hp_{trip_name}",
        )
    with col2:
        new_kontakt = st.text_input(
            "📞 Kontakt (Telefon/E-Mail)",
            ti.get("kontakt", ""),
            key=f"info_kontakt_{trip_name}",
        )

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
    current_user = st.session_state.get("user")

    with st.form(f"invite_form_{trip_name}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        email = c2.text_input("E-Mail (optional)")
        add = st.form_submit_button("Teilnehmer hinzufügen", use_container_width=True)
        if add and name.strip():
            participants.setdefault(
                name.strip(),
                {
                    "display_name": name.strip(),
                    "email": email.strip(),
                    "status": "accepted",
                },
            )
            save_db(data)
            st.success(f"{name.strip()} hinzugefügt")
            st.rerun()

    if participants:
        for uname, pdata in list(participants.items()):
            display_name = uname
            mail = ""
            if isinstance(pdata, dict):
                display_name = pdata.get("display_name") or uname
                mail = pdata.get("email") or ""
            row = st.columns([0.30, 0.28, 0.24, 0.18])
            row[0].write(display_name)
            row[1].write(mail or "—")
            if row[2].button("Einladungslink", key=f"invite_link_{trip_name}_{uname}"):
                st.code(_invite_link(trip_name))
            if uname != current_user and row[3].button("Entfernen", key=f"remove_participant_{trip_name}_{uname}"):
                participants.pop(uname, None)
                save_db(data)
                st.rerun()

    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    share_url = _invite_link(trip_name)
    with cq:
        st.image(_qr_image_url(share_url, size=220), width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen, um direkt zur App bzw. zu dieser Reise zu gelangen.")
        st.code(share_url)
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
