import streamlit as st
from utils import format_time_short
from storage import save_db, new_id
from email_service import send_chat_notification

# -------------------------------------------------
# Chat Tab / Chat auf Startseite
# -------------------------------------------------
def render_chat(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.subheader("💬 Chat")

    # -------------------------------
    # Nachrichtenliste anzeigen
    # -------------------------------
    chat_container = st.container()
    with chat_container:
        for msg in trip["messages"]:
            is_me = (msg["user"] == user)

            if is_me:
                st.markdown(
                    f"<div style='text-align:right; background:#dcf8c6; padding:10px; border-radius:12px; margin:5px;'>"
                    f"<b>{msg['user']}</b><br>{msg['text']}"
                    f"<div style='font-size:10px; color:gray;'>{format_time_short(msg['time'])}</div></div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div style='text-align:left; background:#eee; padding:10px; border-radius:12px; margin:5px;'>"
                    f"<b>{msg['user']}</b><br>{msg['text']}"
                    f"<div style='font-size:10px; color:gray;'>{format_time_short(msg['time'])}</div></div>",
                    unsafe_allow_html=True
                )

    # -------------------------------
    # Neue Nachricht senden
    # -------------------------------
    with st.form("form_new_message", clear_on_submit=True):
        msg = st.text_input("Nachricht", placeholder="Tippen …")
        if st.form_submit_button("Senden") and msg:
            trip["messages"].append({
                "id": new_id("msg"),
                "user": user,
                "text": msg,
                "time": datetime.datetime.now().isoformat()
            })

            # OPTIONAL: E-Mail an alle außer Sender
            for p_name, p_info in trip["participants"].items():
                if p_name != user and p_info.get("email"):
                    try:
                        send_chat_notification(p_name, p_info["email"], msg)
                    except:
                        pass

            save_db(data)
            st.experimental_rerun()
