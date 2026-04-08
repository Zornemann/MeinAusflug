from __future__ import annotations

import datetime
import html
import streamlit as st

from core.storage import new_id, save_db


def render_chat(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]
    messages = trip.setdefault("messages", [])
    role = trip.get("participants", {}).get(user, {}).get("role", "member")
    can_clear_all = role == "admin"

    top_left, top_right = st.columns([0.72, 0.28])
    with top_left:
        st.subheader("💬 Chat")
    with top_right:
        if can_clear_all:
            with st.popover("Chat verwalten", use_container_width=True):
                st.caption("Nur Admins können den gesamten Chat leeren.")
                confirm_clear = st.checkbox("Ja, alle Nachrichten löschen", key=f"confirm_clear_chat_{trip_key}")
                if st.button("Gesamten Chat löschen", key=f"clear_chat_{trip_key}", use_container_width=True, disabled=not confirm_clear):
                    trip["messages"] = []
                    save_db(data)
                    st.rerun()

    if not messages:
        st.info("Noch keine Nachrichten.")

    for idx, msg in enumerate(messages[-100:]):
        msg_id = msg.get("id", f"msg_{idx}")
        author = msg.get("user", "Unbekannt")
        text = msg.get("text", "")
        created = (msg.get("time", "") or "")[:16].replace("T", " ")
        mine = author == user
        can_delete = mine or can_clear_all
        bg = "#1d3a5a" if mine else "#1b2230"
        border = "#4f8cff" if mine else "#2a3342"
        align = "margin-left:auto;" if mine else "margin-right:auto;"
        delete_col, bubble_col = st.columns([0.08, 0.92]) if can_delete else (None, st.container())

        if can_delete:
            with delete_col:
                st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete_msg_{trip_key}_{msg_id}", help="Nachricht löschen"):
                    trip["messages"] = [x for x in messages if x.get("id") != msg_id]
                    save_db(data)
                    st.rerun()
            with bubble_col:
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
                        <div style="font-weight:700; margin-bottom:6px; font-size:0.96rem;">{html.escape(author)}</div>
                        <div style="font-size:1rem; line-height:1.45; word-break:break-word; white-space:pre-wrap;">{html.escape(text)}</div>
                        <div style="opacity:.72; font-size:.78rem; margin-top:6px;">{html.escape(created)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
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
                    <div style="font-weight:700; margin-bottom:6px; font-size:0.96rem;">{html.escape(author)}</div>
                    <div style="font-size:1rem; line-height:1.45; word-break:break-word; white-space:pre-wrap;">{html.escape(text)}</div>
                    <div style="opacity:.72; font-size:.78rem; margin-top:6px;">{html.escape(created)}</div>
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
