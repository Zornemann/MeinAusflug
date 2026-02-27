import streamlit as st
import datetime
import time
from utils import format_time_short
from storage import save_db, new_id

def render_chat(data, trip_name, user):
    trip = data["trips"][trip_name]
    
    # 1. INITIALISIERUNG & SCHREIB-STATUS
    if "messages" not in trip: trip["messages"] = []
    if "typing" not in trip: trip["typing"] = {}
    
    participants = trip.get("participants", {})
    total_users = len(participants)

    # Schreib-Status aufräumen (älter als 7 Sek. löschen)
    now = time.time()
    trip["typing"] = {u: ts for u, ts in trip["typing"].items() if now - ts < 7}

    # 2. NACHRICHTEN ANZEIGEN & GELESEN MARKIEREN
    for msg in trip["messages"]:
        # Mark as read
        if "read_by" not in msg: msg["read_by"] = []
        if user not in msg["read_by"]:
            msg["read_by"].append(user)

        is_me = (msg.get("user") == user)
        time_val = msg.get("time", datetime.datetime.now().isoformat())
        display_time = format_time_short(time_val)
        
        # Haken-Logik (Gelesen-Status)
        read_count = len(msg.get("read_by", []))
        if read_count >= total_users:
            status_haken = "<span style='color:#34b7f1; font-weight:bold;'>✔✔</span>" # Blau: Alle
        elif read_count > 1:
            status_haken = "<span style='color:gray;'>✔✔</span>"    # Grau: Gelesen
        else:
            status_haken = "<span style='color:gray;'>✔</span>"     # Ein Haken: Gesendet
            
        if is_me:
            # Deine Nachrichten (Grün mit Schatten rechts)
            st.markdown(
                f"""
                <div style='
                    text-align: right; 
                    background: #dcf8c6; 
                    padding: 12px; 
                    border-radius: 15px 15px 2px 15px; 
                    margin: 8px 0 8px auto; 
                    color: black; 
                    max-width: 85%; 
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                    border: 1px solid #c7e5b3;'>
                    <b style='color: #4a7c2c;'>Ich</b><br>{msg.get('text', '')}
                    <div style='font-size: 10px; color: #777; margin-top: 5px;'>
                        {display_time} {status_haken}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            # Nachrichten der anderen (Grau mit Schatten links)
            st.markdown(
                f"""
                <div style='
                    text-align: left; 
                    background: #ffffff; 
                    padding: 12px; 
                    border-radius: 15px 15px 15px 2px; 
                    margin: 8px auto 8px 0; 
                    color: black; 
                    max-width: 85%; 
                    box-shadow: -2px 2px 5px rgba(0,0,0,0.08);
                    border: 1px solid #eee;'>
                    <b style='color: #555;'>{msg.get('user', 'Teilnehmer')}</b><br>{msg.get('text', '')}
                    <div style='font-size: 10px; color: #999; margin-top: 5px;'>
                        {display_time}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

    # 3. WER SCHREIBT GERADE?
    typing_others = [u for u in trip["typing"] if u != user]
    if typing_others:
        st.markdown(f"<i style='font-size: 12px; color: #888;'>✍️ {', '.join(typing_others)} schreibt gerade...</i>", unsafe_allow_html=True)

    # 4. EINGABEMASKE
    # Label_visibility="collapsed" versteckt das Label für eine kompakte Ansicht
    new_msg_text = st.text_input("Nachricht schreiben", placeholder="Deine Nachricht...", key="chat_input_val", label_visibility="collapsed")
    
    if new_msg_text:
        trip["typing"][user] = time.time()
    
    # "Abschicken" verhindert den Chrome-Übersetzungsfehler "Sündigen"
    if st.button("👉 Abschicken", key="chat_send_btn", use_container_width=True):
        if new_msg_text:
            if user in trip["typing"]: del trip["typing"][user]
            
            new_entry = {
                "id": new_id("msg"),
                "user": user,
                "text": new_msg_text,
                "time": datetime.datetime.now().isoformat(),
                "read_by": [user]
            }
            trip["messages"].append(new_entry)
            save_db(data)
            st.rerun()