import streamlit as st
from core.utils import convert_to_webp
from core.storage import save_db
from io import BytesIO
import base64
from PIL import Image
import uuid

def render_photos(data, trip_name):
    if "trips" not in data or trip_name not in data["trips"]:
        st.error("Reise nicht gefunden.")
        return
        
    trip = data["trips"][trip_name]
    if "images" not in trip:
        trip["images"] = []

    st.header("📸 Reise-Galerie")

    # --- UPLOAD BEREICH ---
    with st.expander("📤 Neue Fotos hochladen"):
        uploaded = st.file_uploader("Bilder wählen", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if st.button("Hochladen & Optimieren", key="upload_btn"):
            if uploaded:
                with st.spinner("Bilder werden verarbeitet..."):
                    for file in uploaded:
                        # Bild öffnen und skalieren (um JSON klein zu halten)
                        img = Image.open(file)
                        max_size = (1024, 1024) # Max 1024px Breite/Höhe
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # In WebP umwandeln
                        buf = BytesIO()
                        img.save(buf, format="WEBP", quality=70)
                        webp_bytes = buf.getvalue()

                        unique_id = f"img_{uuid.uuid4().hex[:8]}"

                        trip["images"].append({
                            "id": unique_id,
                            "data": base64.b64encode(webp_bytes).decode(),
                            "caption": "",
                            "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                        })
                    save_db(data)
                    st.success(f"{len(uploaded)} Bilder hinzugefügt!")
                    st.rerun()

    st.divider()

    # --- ANZEIGE BEREICH ---
    if not trip["images"]:
        st.info("Noch keine Fotos hochgeladen. Sei der Erste!")
    else:
        # Bilder in 3 Spalten (sieht auf Desktop besser aus)
        cols = st.columns(3)

        for i, img in enumerate(trip["images"]):
            img_id = img.get("id", f"old_{i}")
            
            with cols[i % 3]:
                try:
                    data_bytes = base64.b64decode(img["data"])
                    st.image(data_bytes)
                    
                    if img.get("caption"):
                        st.caption(f"💬 {img['caption']}")

                    with st.expander("⚙️ Optionen"):
                        # Bildunterschrift
                        new_cap = st.text_input("Unterschrift", value=img.get("caption", ""), key=f"cap_{img_id}")
                        if new_cap != img.get("caption"):
                            img["caption"] = new_cap
                            save_db(data)
                            st.rerun()

                        c_rot, c_del = st.columns(2)
                        
                        # Drehen
                        if c_rot.button("🔄 Drehen", key=f"rot_{img_id}"):
                            im = Image.open(BytesIO(data_bytes)).rotate(-90, expand=True)
                            buf = BytesIO()
                            im.save(buf, format="WEBP", quality=75)
                            img["data"] = base64.b64encode(buf.getvalue()).decode()
                            save_db(data)
                            st.rerun()

                        # Löschen (Gefestigte Logik)
                        if c_del.button("🗑️ Löschen", key=f"del_{img_id}"):
                            trip["images"] = [x for x in trip["images"] if x.get("id") != img_id]
                            save_db(data)
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Fehler: {e}")
