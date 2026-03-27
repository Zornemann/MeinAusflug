from __future__ import annotations

import datetime
import streamlit as st

from core.storage import new_id, save_db


def render_chat(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]
    messages = trip.setdefault("messages", [])

    st.subheader("💬 Chat")

    if not messages:
        st.info("Noch keine Nachrichten.")

    for msg in messages[-100:]:
        author = msg.get("user", "Unbekannt")
        text = msg.get("text", "")
        created = msg.get("time", "")
        mine = author == user
        box = st.container()
        with box:
            st.markdown(
                f"""
                <div style="
                    background:{'#E8F2FF' if mine else '#F5F5F5'};
                    padding:10px 12px;
                    border-radius:14px;
                    margin:6px 0;
                    border:1px solid #E0E0E0;">
                    <div style="font-weight:600; margin-bottom:4px;">{author}</div>
                    <div style="font-size:1rem;">{text}</div>
                    <div style="opacity:.65; font-size:.78rem; margin-top:4px;">{created[:16].replace('T', ' ')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.form(f"chat_form_{trip_key}", clear_on_submit=True):
        text = st.text_input("Nachricht", placeholder="Schreibe eine Nachricht …")
        submitted = st.form_submit_button("Senden", use_container_width=True)
        if submitted and text.strip():
            messages.append(
                {
                    "id": new_id("msg"),
                    "user": user,
                    "text": text.strip(),
                    "time": datetime.datetime.now().replace(microsecond=0).isoformat(),
                }
            )
            save_db(data)
            st.rerun()
