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
        bg = "linear-gradient(180deg, rgba(73,117,255,.35), rgba(46,74,160,.35))" if mine else "rgba(27, 38, 66, 0.92)"
        border = "rgba(124,156,255,.45)" if mine else "rgba(130, 153, 196, 0.18)"
        align = "margin-left:auto;" if mine else "margin-right:auto;"
        with st.container():
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    color:#f4f7fb;
                    padding:12px 14px;
                    border-radius:18px;
                    margin:8px 0;
                    border:1px solid {border};
                    max-width:860px;
                    box-shadow:0 10px 30px rgba(0,0,0,.15);
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
