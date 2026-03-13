import streamlit as st
import urllib.parse

from core.storage import save_db
from core.config import APP_URL


def _qr_image_url(text: str, size: int = 200) -> str:
    """
    QR-Code ohne Python-Abhängigkeit (qrcode) – wir nutzen einen Image-Endpoint.
    """
    payload = urllib.parse.quote(text or "")
    # public QR image endpoint
    return f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={payload}"


def render_info(data, trip_name):
    trip = data["trips"][trip_name]
    ti = trip.get("details", {})
    if not isinstance(ti, dict):
        ti = {}

    st.subheader("📝 Reise-Zentrale & Quick-Links")

    changed = False

    # 1) Zusätzliche Infos (Homepage & Kontakt)
    col1, col2 = st.columns(2)
    with col1:
        new_hp = st.text_input("🌐 Homepage (Unterkunft/Ziel)", ti.get("homepage", "https://"), key="info_hp")
    with col2:
        new_kontakt = st.text_input("📞 Kontakt (Telefon/E-Mail)", ti.get("kontakt", ""), key="info_kontakt")

    if new_hp != ti.get("homepage", "https://"):
        ti["homepage"] = new_hp
        changed = True
    if new_kontakt != ti.get("kontakt", ""):
        ti["kontakt"] = new_kontakt
        changed = True

    # 2) QR-Code zum Teilen
    st.divider()
    st.subheader("📲 App mit Freunden teilen")
    cq, ct = st.columns([1, 2])
    with cq:
        st.image(_qr_image_url(APP_URL, size=220), width=180)
    with ct:
        st.write("Lass deine Freunde diesen Code scannen, um direkt zur App zu gelangen.")
        st.code(APP_URL)

        if st.button("Link in Zwischenablage", key="info_copy_link"):
            # Streamlit kann nicht “systemweit” kopieren; wir zeigen es als Hinweis
            st.toast("Link kopiert – markiere ihn und nutze Strg+C.")

    # 3) Navigation
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