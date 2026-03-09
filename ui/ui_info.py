import datetime
import urllib.parse

import streamlit as st

from core.config import APP_URL
from core.storage import save_db
from core.utils_email import get_mailto_link, send_system_email


def _qr_image_url(text: str, size: int = 200) -> str:
    payload = urllib.parse.quote(text or "")
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={payload}"


def _participant_meta(trip: dict, username: str) -> dict:
    participants = trip.setdefault("participants", {})
    pdata = participants.get(username)
    if not isinstance(pdata, dict):
        pdata = {"display_name": username, "status": "accepted", "email": "", "role": "member"}
        participants[username] = pdata
    pdata.setdefault("display_name", username)
    pdata.setdefault("status", "accepted")
    pdata.setdefault("email", "")
    pdata.setdefault("invited_by", "")
    pdata.setdefault("role", "member")
    return pdata


def _invite_body(app_url: str, trip_name: str, invitee_name: str, inviter_name: str) -> str:
    return (
        f"Hallo {invitee_name},\n\n"
        f"{inviter_name} hat dich zu '{trip_name}' in MeinAusflug eingeladen.\n\n"
        f"Direkt zur App: {app_url}\n\n"
        "Bitte melde dich dort mit deinem Namen an.\n"
        "Sobald du die Reise öffnest, wirst du als Teilnehmer angezeigt.\n"
    )


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip.get("details", {})
    if not isinstance(ti, dict):
        ti = {}

    st.subheader("📝 Reise-Zentrale & Quick-Links")

    changed = False

    col1, col2 = st.columns(2)
    with col1:
        new_hp = st.text_input("🌐 Homepage (Unterkunft/Ziel)", ti.get("homepage", "https://"), key=f"info_hp_{trip_name}")
    with col2:
        new_kontakt = st.text_input("📞 Kontakt (Telefon/E-Mail)", ti.get("kontakt", ""), key=f"info_kontakt_{trip_name}")

    if new_hp != ti.get("homepage", "https://"):
        ti["homepage"] = new_hp
        changed = True
    if new_kontakt != ti.get("kontakt", ""):
        ti["kontakt"] = new_kontakt
        changed = True

    st.divider()
    st.subheader("👥 Teilnehmer einladen & verwalten")

    current_user = st.session_state.get("user", "")
    participants = trip.setdefault("participants", {})
    _participant_meta(trip, current_user)

    with st.form(f"invite_participant_{trip_name}", clear_on_submit=True):
        c1, c2 = st.columns(2)
        invite_name = c1.text_input("Name des Teilnehmers")
        invite_email = c2.text_input("E-Mail (optional)")
        c3, c4 = st.columns(2)
        invite_display = c3.text_input("Anzeigename (optional)")
        invite_role = c4.selectbox("Rolle", ["member", "admin"], format_func=lambda x: "Mitglied" if x == "member" else "Admin")
        send_mail = st.checkbox("Einladungs-E-Mail senden", value=bool(invite_email.strip()))
        submitted = st.form_submit_button("➕ Teilnehmer hinzufügen", use_container_width=True)

        if submitted:
            uname = (invite_name or "").strip()
            email = (invite_email or "").strip()
            if not uname:
                st.warning("Bitte gib einen Namen ein.")
            else:
                pdata = _participant_meta(trip, uname)
                pdata["display_name"] = (invite_display or uname).strip()
                pdata["email"] = email
                pdata["role"] = invite_role
                pdata["status"] = "invited" if email else "accepted"
                pdata["invited_by"] = current_user
                pdata["invited_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
                save_db(data)
                body = _invite_body(APP_URL, trip.get("name") or trip_name, pdata["display_name"], current_user or "Jemand")
                if email and send_mail:
                    ok, message = send_system_email(email, f"Einladung zu {trip.get('name') or trip_name}", body)
                    if ok:
                        st.success(message)
                    else:
                        st.warning(message)
                        st.markdown(f"[Einladung im Mailprogramm öffnen]({get_mailto_link(email, f'Einladung zu {trip.get('name') or trip_name}', body)})")
                elif email:
                    st.markdown(f"[Einladung im Mailprogramm öffnen]({get_mailto_link(email, f'Einladung zu {trip.get('name') or trip_name}', body)})")
                st.session_state.force_reload = True
                st.rerun()

    if participants:
        for uname in sorted(participants.keys(), key=lambda x: x.lower()):
            pdata = _participant_meta(trip, uname)
            cols = st.columns([0.28, 0.24, 0.18, 0.18, 0.12])
            display = pdata.get("display_name") or uname
            status = pdata.get("status", "accepted")
            role = pdata.get("role", "member")
            email = pdata.get("email", "") or "–"
            cols[0].write(f"**{display}**\n\n`{uname}`")
            cols[1].write(email)
            cols[2].write("Eingeladen" if status == "invited" else "Aktiv")
            cols[3].write("Admin" if role == "admin" else "Mitglied")
            if uname != current_user:
                if cols[4].button("🗑️", key=f"del_part_{trip_name}_{uname}"):
                    participants.pop(uname, None)
                    save_db(data)
                    st.session_state.force_reload = True
                    st.rerun()
            else:
                cols[4].caption("Du")

    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    with cq:
        st.image(_qr_image_url(APP_URL, size=220), width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen, um direkt zur App zu gelangen.")
        st.code(APP_URL)
        if st.button("Link in Zwischenablage", key=f"info_copy_link_{trip_name}"):
            st.toast("Link kopiert – markiere ihn und nutze Strg+C.")

    st.divider()
    st.subheader("🗺️ Navigation")

    address = f"{ti.get('street', '')}, {ti.get('plz', '')} {ti.get('city', '')}".strip().strip(",")
    address = " ".join(address.split())

    if len(address) > 5:
        encoded_addr = urllib.parse.quote(address)
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"

        st.markdown(
            f"""
            <a href='{google_maps_url}' target='_blank' style="text-decoration:none;">
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
                    🚗 Navigation in Google Maps starten
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.caption(f"Ziel: {address}")
    else:
        st.info("Trage auf der Startseite eine Adresse ein (Straße/PLZ/Ort), um die Navigation zu nutzen.")

    if changed:
        trip["details"] = ti
        save_db(data)
