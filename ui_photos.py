import streamlit as st
from utils import convert_to_webp
from storage import save_db
from io import BytesIO
import base64
from PIL import Image
import uuid # FEHLTE: Hilft beim Erzeugen sicherer IDs

def render_photos(data, trip_name):
    # Sicherstellen, dass die Trip-Daten korrekt geladen werden
    if "trips" not in data or trip_name not in data["trips"]:
        st.error("Reise nicht gefunden.")
        return
        
    trip = data["trips"][trip_name]

    st.header("📸 Fotos")

    # Sicherstellen, dass die Liste "images" existiert
    if "images" not in trip:
        trip["images"] = []

    uploaded = st.file_uploader("Bilder hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Upload") and uploaded:
        for file in uploaded:
            img_bytes = file.read()
            # Konvertierung zu WebP (spart Platz in der JSON)
            webp_bytes = convert_to_webp(img_bytes)

            # Eindeutige ID erzeugen (Dateiname + Zufall), um Key-Fehler zu vermeiden
            unique_id = f"{file.name}_{uuid.uuid4().hex[:6]}"

            trip["images"].append({
                "id": unique_id,
                "data": base64.b64encode(webp_bytes).decode(),
                "caption": ""
            })

        save_db(data)
        st.rerun()

    # Bilder in zwei Spalten anzeigen
    cols = st.columns(2)

    for i, img in enumerate(trip["images"]):
        # REPARATUR-LOGIK: Falls ID fehlt, temporäre ID für diesen Durchlauf generieren
        img_id = img.get("id", f"old_img_{i}")
        
        with cols[i % 2]:
            try:
                data_bytes = base64.b64decode(img["data"])
                st.image(data_bytes)

                with st.expander("Bearbeiten"):
                    # Caption-Feld mit sicherem Key
                    current_caption = img.get("caption", "")
                    new_caption = st.text_input("Bildunterschrift", value=current_caption, key=f"c_{img_id}")
                    
                    if new_caption != current_caption:
                        img["caption"] = new_caption
                        save_db(data)
                        # Kein rerun hier nötig, da Textfelder den State selbst halten

                    col_rot, col_del = st.columns(2)

                    if col_rot.button("Drehen 🔄", key=f"rot_{img_id}"):
                        im = Image.open(BytesIO(data_bytes)).rotate(-90, expand=True)
                        buf = BytesIO()
                        im.save(buf, format="WEBP")
                        img["data"] = base64.b64encode(buf.getvalue()).decode()
                        save_db(data)
                        st.rerun()

                    if col_del.button("Löschen 🗑️", key=f"del_{img_id}"):
                        trip["images"] = [x for x in trip["images"] if x.get("id") != img.get("id") or x == img]
                        save_db(data)
                        st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Laden eines Bildes: {e}")

# Hinweis: st.experimental_rerun() wurde durch st.rerun() ersetzt.