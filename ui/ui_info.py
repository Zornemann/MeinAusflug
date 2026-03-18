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


def _mailto_link(trip_name: str, share_url: str, recipient_mail: str, recipient_name: str) -> str:
    subject = urllib.parse.quote(f"Einladung zu {trip_name}")
    body = urllib.parse.quote(
        f"Hallo {recipient_name or ''},\n\n"
        f"du bist zu '{trip_name}' eingeladen.\n"
        f"Hier ist der Link zur App/Reise:\n{share_url}\n\n"
        f"Viele Grüße"
    )
    return f"mailto:{recipient_mail}?subject={subject}&body={body}"


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip.get("details", {})
    if not isinstance(ti, dict):
        ti = {}
        trip["details"] = ti

    st.subheader("📝 Reise-Zentrale & Quick-Links")
    changed = False

    col1, col2 = st.columns(2)
    with col1:
        new_hp = st.text_input(
            "🌐 Homepage",
            ti.get("homepage", ti.get("loc_name", "")),
            key=f"info_hp_{trip_name}",
            placeholder="https://...",
        )
    with col2:
        new_kontakt = st.text_input(
            "📞 Kontakt (Telefon/E-Mail)",
            ti.get("kontakt", ""),
            key=f"info_kontakt_{trip_name}",
        )

    if new_hp != ti.get("homepage", ti.get("loc_name", "")):
        ti["homepage"] = new_hp
        ti["loc_name"] = new_hp
        changed = True
    if new_kontakt != ti.get("kontakt", ""):
        ti["kontakt"] = new_kontakt
        changed = True

    if changed:
        trip["details"] = ti
        save_db(data)

    st.divider()
    st.subheader("👥 Teilnehmer einladen")
    st.caption("Teilnehmer hinzufügen, Einladungslink kopieren oder direkt per Mail teilen.")
    participants = trip.setdefault("participants", {})
    current_user = st.session_state.get("user")
    share_url = _invite_link(trip_name)

    with st.form(f"invite_form_{trip_name}", clear_on_submit=True):
        c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
        name = c1.text_input("Name")
        email = c2.text_input("E-Mail (optional)")
        status = c3.selectbox("Status", ["accepted", "invited"], index=1)
        add = st.form_submit_button("Teilnehmer hinzufügen", use_container_width=True)
        if add and name.strip():
            uname = name.strip()
            participants[uname] = {
                "display_name": uname,
                "email": email.strip(),
                "status": status,
            }
            save_db(data)
            st.success(f"{uname} hinzugefügt")
            st.rerun()

    quick_cols = st.columns([2, 1])
    with quick_cols[0]:
        st.code(share_url)
    with quick_cols[1]:
        st.link_button("🔗 Reise-Link öffnen", share_url, use_container_width=True)

    if participants:
        header = st.columns([0.24, 0.24, 0.16, 0.18, 0.18])
        header[0].markdown("**Name**")
        header[1].markdown("**E-Mail**")
        header[2].markdown("**Status**")
        header[3].markdown("**Einladen**")
        header[4].markdown("**Aktion**")

        for uname, pdata in list(participants.items()):
            display_name = uname
            mail = ""
            status = "accepted"
            if isinstance(pdata, dict):
                display_name = pdata.get("display_name") or uname
                mail = pdata.get("email") or ""
                status = pdata.get("status", "accepted") or "accepted"

            row = st.columns([0.24, 0.24, 0.16, 0.18, 0.18])
            row[0].write(display_name)
            row[1].write(mail or "—")
            row[2].write("Eingeladen" if status == "invited" else "Aktiv")

            if mail:
                row[3].link_button(
                    "📧 Mail",
                    _mailto_link(trip_name, share_url, mail, display_name),
                    use_container_width=True,
                )
            else:
                if row[3].button("🔗 Link", key=f"invite_link_{trip_name}_{uname}", use_container_width=True):
                    st.code(share_url)

            if uname != current_user and row[4].button("Entfernen", key=f"remove_participant_{trip_name}_{uname}", use_container_width=True):
                participants.pop(uname, None)
                save_db(data)
                st.rerun()
    else:
        st.info("Noch keine Teilnehmer vorhanden.")

    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    with cq:
        st.image(_qr_image_url(share_url, size=220), width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen oder sende ihnen direkt den Link.")
        st.code(share_url)
        st.caption("Tipp: Auf Android kann der Link direkt in der App geöffnet werden.")

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
