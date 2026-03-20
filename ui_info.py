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


def _invite_link(trip_name: str) -> str:
    base = (APP_URL or "").rstrip("/")
    trip_param = urllib.parse.quote(trip_name or "")
    return f"{base}/?trip={trip_param}" if base else f"?trip={trip_param}"


def _save_if_changed(data: dict, trip: dict, original_details: dict, original_participants: dict) -> None:
    if trip.get("details") != original_details or trip.get("participants") != original_participants:
        save_db(data)


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    details = trip.setdefault("details", {})
    participants = trip.setdefault("participants", {})

    original_details = dict(details)
    original_participants = {k: dict(v) if isinstance(v, dict) else v for k, v in participants.items()}

    st.subheader("📝 Reise-Zentrale & Teilnehmer")

    col1, col2 = st.columns(2)
    with col1:
        details["homepage"] = st.text_input(
            "🌐 Homepage",
            details.get("homepage", "https://"),
            key=f"info_homepage_{trip_name}",
            placeholder="https://...",
        )
    with col2:
        details["kontakt"] = st.text_input(
            "📞 Kontakt (Telefon/E-Mail)",
            details.get("kontakt", ""),
            key=f"info_kontakt_{trip_name}",
            placeholder="Telefon oder E-Mail",
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
        key = invite_name.strip()
        if not key:
            st.warning("Bitte mindestens einen Namen eingeben.")
        elif key in participants:
            st.warning(f"Teilnehmer '{key}' existiert bereits.")
        else:
            participants[key] = {
                "display_name": invite_display.strip() or key,
                "email": invite_email.strip(),
                "role": invite_role,
                "status": "invited",
            }
            save_db(data)
            st.success(f"Teilnehmer '{key}' hinzugefügt.")
            st.rerun()

    if participants:
        st.markdown("#### Aktuelle Teilnehmer")
        for person_key, meta in participants.items():
            d1, d2, d3 = st.columns([2, 2, 1])
            display_name = meta.get("display_name") or person_key if isinstance(meta, dict) else person_key
            email = meta.get("email", "") if isinstance(meta, dict) else ""
            role = meta.get("role", "member") if isinstance(meta, dict) else "member"
            d1.markdown(f"👤 **{display_name}**")
            d2.caption(f"📧 {email or 'keine E-Mail'} · 🔑 {role}")
            if d3.button("Entfernen", key=f"remove_participant_{trip_name}_{person_key}"):
                participants.pop(person_key, None)
                save_db(data)
                st.rerun()

    st.divider()
    st.subheader("📲 App mit Freunden teilen")

    invite_url = _invite_link(trip.get("name") or trip_name)

    c_qr, c_text = st.columns([1, 2])
    with c_qr:
        if generate_qr_code:
            try:
                qr_img = generate_qr_code(invite_url)
                st.image(qr_img, width=160)
            except Exception:
                st.info("QR-Code konnte nicht erzeugt werden.")
        else:
            st.info("QR-Code-Funktion nicht verfügbar.")
    with c_text:
        st.write("Mit diesem Link kommen Teilnehmer direkt zu dieser Reise.")
        st.text_input("Einladungslink", invite_url, key=f"invite_link_{trip_name}")
        st.caption("Den Link kannst du kopieren und per Messenger oder E-Mail versenden.")

    st.divider()
    st.subheader("🔔 Benachrichtigungen")
    st.caption(
        "Echte Push-Benachrichtigungen auf Android funktionieren über die native Capacitor-App. "
        "Für den Browser werden Benachrichtigungen direkt in der App angefragt."
    )

    st.divider()
    st.subheader("🗺️ Navigation")
    address = f"{details.get('street', '')}, {details.get('plz', '')} {details.get('city', '')}".strip(", ")

    if address and address.strip():
        encoded_addr = urllib.parse.quote(address)
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_addr}"
        st.link_button("🚗 Navigation in Google Maps starten", google_maps_url, use_container_width=True)
        st.caption(f"Ziel: {address}")
    else:
        st.info("Trage auf der Startseite eine Adresse ein, um die Navigation zu nutzen.")

    trip["details"] = details
    _save_if_changed(data, trip, original_details, original_participants)
