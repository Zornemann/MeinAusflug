import streamlit as st
from utils import convert_to_webp
from storage import save_db
from io import BytesIO
import base64
from PIL import Image

def render_photos(data, trip_name):
    trip = data["trips"][trip_name]

    st.header("📸 Fotos")

    uploaded = st.file_uploader("Bilder hochladen", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if st.button("Upload") and uploaded:
        for file in uploaded:
            img_bytes = file.read()
            webp_bytes = convert_to_webp(img_bytes)

            trip["images"].append({
                "id": file.name,
                "data": base64.b64encode(webp_bytes).decode(),
                "caption": ""
            })

        save_db(data)
        st.experimental_rerun()

    cols = st.columns(2)

    for i, img in enumerate(trip["images"]):
        with cols[i % 2]:
            data_bytes = base64.b64decode(img["data"])
            st.image(data_bytes)

            with st.expander("Bearbeiten"):
                caption = st.text_input("Caption", img["caption"], key="c_"+img["id"])
                if caption != img["caption"]:
                    img["caption"] = caption
                    save_db(data)

                if st.button("Drehen", key="rot_"+img["id"]):
                    im = Image.open(BytesIO(data_bytes)).rotate(-90, expand=True)
                    buf = BytesIO()
                    im.save(buf, format="WEBP")
                    img["data"] = base64.b64encode(buf.getvalue()).decode()
                    save_db(data)
                    st.experimental_rerun()

                if st.button("Löschen", key="del_"+img["id"]):
                    trip["images"] = [x for x in trip["images"] if x["id"] != img["id"]]
                    save_db(data)
                    st.experimental_rerun()
