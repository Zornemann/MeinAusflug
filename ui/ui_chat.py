from __future__ import annotations

import datetime
import streamlit as st

from core.storage import new_id, save_db


def _ensure_message_ids(messages: list[dict]) -> bool:
    changed = False
    for msg in messages:
        if isinstance(msg, dict) and not msg.get("id"):
            msg["id"] = new_id("msg")
            changed = True
    return changed


def render_chat(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]
    messages = trip.setdefault("messages", [])
    role = trip.get("participants", {}).get(user, {}).get("role", "member")
    can_clear_all = role == "admin"

    if _ensure_message_ids(messages):
        save_db(data)

    top_left, top_right = st.columns([0.72, 0.28])
    with top_left:
        st.subheader("💬 Chat")
    with top_right:
        if can_clear_all:
            with st.popover("Chat verwalten", use_container_width=True):
                st.caption("Nur Admins können den gesamten Chat leeren.")
                confirm_clear = st.checkbox("Ja, alle Nachrichten löschen", key=f"confirm_clear_chat_{trip_key}")
                if st.button(
                    "Gesamten Chat löschen",
                    key=f"clear_chat_{trip_key}",
                    use_container_width=True,
                    disabled=not confirm_clear,
                ):
                    trip["messages"] = []
                    save_db(data)
                    st.rerun()

    visible_messages = list(trip.get("messages", [])[-100:])
    if not visible_messages:
        st.info("Noch keine Nachrichten.")

    for msg in visible_messages:
        msg_id = msg.get("id") or new_id("msg")
        author = msg.get("user", "Unbekannt")
        text = msg.get("text", "")
        created = (msg.get("time", "") or "")[:16].replace("T", " ")
        mine = author == user
        can_delete = mine or can_clear_all

        outer = st.container()
        left, right = outer.columns([0.92, 0.08], vertical_alignment="top") if can_delete else (outer, None)

        with left:
            with st.container(border=True):
                name_col, time_col = st.columns([0.7, 0.3])
                with name_col:
                    st.markdown(f"**{author}**")
                with time_col:
                    if created:
                        st.caption(created)
                st.write(text)

        if can_delete and right is not None:
            with right:
                st.markdown("<div style='height: 0.25rem;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete_msg_{trip_key}_{msg_id}", help="Nachricht löschen"):
                    trip["messages"] = [m for m in trip.get("messages", []) if m.get("id") != msg_id]
                    save_db(data)
                    st.rerun()

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
            trip.setdefault("messages", []).append(
                {
                    "id": new_id("msg"),
                    "user": user,
                    "text": text.strip(),
                    "time": datetime.datetime.now().replace(microsecond=0).isoformat(),
                }
            )
            save_db(data)
            st.rerun()
