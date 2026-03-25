import datetime
import streamlit as st

from core.storage import save_db

def render_chat(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]

    st.subheader("💬 Chat")

    messages = trip.setdefault("messages", [])

    for msg in messages[-50:]:
        st.markdown(f"**{msg['user']}**: {msg['text']}")

    with st.form("chat_form", clear_on_submit=True):
        text = st.text_input("Nachricht")
        submitted = st.form_submit_button("Senden")

        if submitted and text.strip():
            messages.append(
                {
                    "id": str(datetime.datetime.now().timestamp()),
                    "user": user,
                    "text": text.strip(),
                    "time": datetime.datetime.now().isoformat(),
                }
            )
            save_db(data)
            st.rerun()
