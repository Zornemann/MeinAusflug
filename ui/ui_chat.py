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
        bg = "#1d3a5a" if mine else "#1b2230"
        border = "#4f8cff" if mine else "#2a3342"
        align = "margin-left:auto;" if mine else "margin-right:auto;"
        with st.container():
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    color:#f4f7fb;
                    padding:12px 14px;
                    border-radius:16px;
                    margin:8px 0;
                    border:1px solid {border};
                    max-width:860px;
                    {align}">
                    <div style="font-weight:700; margin-bottom:6px; font-size:0.96rem;">{author}</div>
                    <div style="font-size:1rem; line-height:1.45; word-break:break-word;">{text}</div>
                    <div style="opacity:.72; font-size:.78rem; margin-top:6px;">{created[:16].replace('T', ' ')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)

    with st.form(f"chat_form_{trip_key}", clear_on_submit=True):
        text = st.text_area(
            "Nachricht",
            placeholder="Schreibe eine Nachricht …",
            height=110,
            key=f"chat_textarea_{trip_key}",
        )
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
