from __future__ import annotations

import urllib.parse

import streamlit as st

try:
    from core.storage import save_db
    from core.config import APP_URL
except Exception:  # fallback for flat project layout
    from storage import save_db
    from config import APP_URL

try:
    from core.utils import generate_qr_code
except Exception:
    try:
        from utils import generate_qr_code
    except Exception:
        generate_qr_code = None


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    details = trip.setdefault("details", {})
    participants = trip.setdefault("participants", {})

    st.subheader("📝 Reise-Zentrale & Teilnehmer")

    col1, col2 = st.columns(2)
    with col1:
        details["homepage"] = st.text_input(
            "🌐 Homepage",
            details.get("homepage", "https://"),
            key=f"info_homepage_{trip_name}",
        )
    with col2:
        details["kontakt"] = st.text_input(
            "📞 Kontakt (Telefon/E-Mail)",
            details.get("kontakt", ""),
            key=f"info_kontakt_{trip_name}",
        )

    st.divider()
    st.subheader("👥 Teilnehmer einladen")

    with st.form(f"invite_form_{trip_name}"):
        c1, c2 = st.columns(2)
        with c1:
            invite_name = st.text_input("Name", key=f"invite_name_{trip_name}")
            invite_email = st.text_input("E-Mail", key=f"invite_email_{trip_name}")
        with c2:
            invite_display = st.text_input("Anzeigename", key=f"invite_display_{trip_name}")
            invite_role = st.selectbox(
                "Rolle",
                ["member", "admin"],
                index=0,
                key=f"invite_role_{trip_name}",
            )
        submitted = st.form_submit_button("Teilnehmer hinzufügen", use_container_width=True)

    if submitted:
        if invite_name.strip():
            key = invite_name.strip()
            participants[key] = {
                **participants.get(key, {}),
                "display_name": invite_display.strip() or key,
                "email": invite_email.strip(),
                "role": invite_role,
                "status": participants.get(key, {}).get("status", "invited"),
            }
            save_db(data)
            st.success(f"Teilnehmer '{key}' hinzugefügt.")
            st.rerun()
        else:
            st.warning("Bitte mindestens einen Namen eingeben.")

    if participants:
        for person_key, meta in participants.items():
            d1, d2, d3 = st.columns([2, 2, 1])
            display_name = meta.get("display_name") or person_key
            email = meta.get("email", "")
            role = meta.get("role", "member")
            d1.write(f"**{display_name}**")
            d2.caption(f"{email or 'ohne E-Mail'} · {role}")
            if d3.button("Entfernen", key=f"remove_participant_{trip_name}_{person_key}"):
                participants.pop(person_key, None)
                save_db(data)
                st.rerun()

    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    c_qr, c_text = st.columns([1, 2])
    with c_qr:
        if generate_qr_code:
            try:
                qr_img = generate_qr_code(APP_URL)
                st.image(qr_img, width=180)
            except Exception:
                st.info("QR-Code konnte nicht erzeugt werden.")
        else:
            st.info("QR-Code-Funktion nicht verfügbar.")
    with c_text:
        st.write("Mit diesem Link kommen Teilnehmer direkt zur App.")
        st.code(APP_URL)
        st.caption("Den Link kannst du kopieren und per Messenger oder E-Mail versenden.")

    st.divider()
    st.subheader("🗺️ Navigation")
    address = f"{details.get('street', '')}, {details.get('plz', '')} {details.get('city', '')}".strip(", ")

    if len(address) > 5:
        encoded_addr = urllib.parse.quote(address)
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
        st.link_button("🚗 Navigation in Google Maps starten", google_maps_url, use_container_width=True)
        st.caption(f"Ziel: {address}")
    else:
        st.info("Trage auf der Startseite eine Adresse ein, um die Navigation zu nutzen.")

    trip["details"] = details
    save_db(data)
