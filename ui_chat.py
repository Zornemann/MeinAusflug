import streamlit as st
import datetime  # FEHLTE: Wichtig für den Zeitstempel!
from utils import format_time_short
from storage import save_db, new_id
# from email_service import send_chat_notification # Falls vorhanden, sonst auskommentiert lassen

# -------------------------------------------------
# Chat Tab / Chat auf Startseite
# -------------------------------------------------
def render_chat(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.subheader("💬 Chat")

    # -------------------------------
    # Nachrichtenliste anzeigen
    # -------------------------------
    # Wir nutzen ein einfaches div-Layout für die Anzeige
    for msg in trip["messages"]:
        is_me = (msg.get("user") == user)
        
        # SICHERHEITS-CHECK: Falls 'time' in alten Nachrichten fehlt
        time_val = msg.get("time", datetime.datetime.now().isoformat())
        display_time = format_time_short(time_val)

        if is_me:
            st.markdown(
                f"<div style='text-align:right; background:#dcf8c6; padding:10px; border-radius:12px; margin:5px; color:black;'>"
                f"<b>{msg.get('user', 'Unbekannt')}</b><br>{msg.get('text', '')}"
                f"<div style='font-size:10px; color:gray;'>{display_time}</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='text-align:left; background:#eee; padding:10px; border-radius:12px; margin:5px; color:black;'>"
                f"<b>{msg.get('user', 'Unbekannt')}</b><br>{msg.get('text', '')}"
                f"<div style='font-size:10px; color:gray;'>{display_time}</div></div>",
                unsafe_allow_html=True
            )

    # -------------------------------
    # Neue Nachricht senden
    # -------------------------------
    with st.form("form_new_message", clear_on_submit=True):
        new_msg_text = st.text_input("Nachricht", placeholder="Tippen …")
        if st.form_submit_button("Senden") and new_msg_text:
            # Nachricht zum Trip hinzufügen
            new_entry = {
                "id": new_id("msg"),
                "user": user,
                "text": new_msg_text,
                "time": datetime.datetime.now().isoformat()
            }
            trip["messages"].append(new_entry)

            # OPTIONAL: E-Mail Benachrichtigung (nur wenn Modul aktiv)
            # for p_name, p_info in trip.get("participants", {}).items():
            #    if p_name != user and isinstance(p_info, dict) and p_info.get("email"):
            #        try: send_chat_notification(p_name, p_info["email"], new_msg_text)
            #        except: pass

            save_db(data)
            st.rerun() # Aktualisiert die Seite sofort