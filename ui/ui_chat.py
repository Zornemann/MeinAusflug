from __future__ import annotations

import datetime
import html
import streamlit as st

from core.storage import new_id, save_db

REACTIONS = ["👍", "❤️", "😂", "🎉", "😮", "😢", "🙏"]


def _ensure_message_shape(trip: dict, data: dict) -> None:
    changed = False
    for msg in trip.get("messages", []):
        if not msg.get("id"):
            msg["id"] = new_id()
            changed = True
        if "reactions" not in msg or not isinstance(msg.get("reactions"), dict):
            msg["reactions"] = {}
            changed = True
    if changed:
        save_db(data)


def _format_ts(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return raw


def _toggle_reaction(message: dict, emoji: str, user: str) -> None:
    reactions = message.setdefault("reactions", {})
    users = reactions.setdefault(emoji, [])
    if user in users:
        users.remove(user)
    else:
        users.append(user)
    if not users:
        reactions.pop(emoji, None)


def _reaction_summary_html(message: dict, user: str) -> str:
    reactions = message.get("reactions", {}) or {}
    pills = []
    for emoji in REACTIONS:
        users = reactions.get(emoji, [])
        if users:
            active = " me-active" if user in users else ""
            pills.append(
                f"<span class='me-reaction-pill{active}'>{emoji} <strong>{len(users)}</strong></span>"
            )
    if not pills:
        return ""
    return "<div class='me-reactions'>" + "".join(pills) + "</div>"


def render_chat(data: dict, trip_key: str, user: str) -> None:
    trips = data.setdefault("trips", {})
    trip = trips.setdefault(trip_key, {})
    messages = trip.setdefault("messages", [])
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")

    _ensure_message_shape(trip, data)

    header_left, header_right = st.columns([3, 1])
    with header_left:
        st.subheader("💬 Chat")
    with header_right:
        with st.popover("Chat verwalten", use_container_width=True):
            st.caption("Nachrichten verwalten")
            if role == "admin":
                if st.button("Gesamten Chat leeren", key=f"clear_chat_{trip_key}", use_container_width=True):
                    trip["messages"] = []
                    save_db(data)
                    st.rerun()
            else:
                st.info("Nur Admins können den gesamten Chat leeren.")

    if not messages:
        st.info("Noch keine Nachrichten vorhanden.")

    for idx, msg in enumerate(list(messages)):
        msg_id = msg.get("id") or f"{idx}"

        outer_left, outer_right = st.columns([18, 2])
        with outer_left:
            safe_author = html.escape(str(msg.get("author", "Unbekannt")))
            safe_text = html.escape(str(msg.get("text", ""))).replace("\n", "<br>")
            summary = _reaction_summary_html(msg, user)

            st.markdown(
                (
                    "<div class='me-chat-row'>"
                    "<div class='me-chat-head'>"
                    f"<div class='me-chat-author'>{safe_author}</div>"
                    f"<div class='me-soft'>{_format_ts(msg.get('created_at', ''))}</div>"
                    "</div>"
                    f"<div class='me-chat-text'>{safe_text}</div>"
                    f"{summary}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            with st.container():
                st.markdown("<div class='me-reaction-picker'>", unsafe_allow_html=True)
                reaction_cols = st.columns(len(REACTIONS))
                for col, emoji in zip(reaction_cols, REACTIONS):
                    with col:
                        if st.button(emoji, key=f"react_{trip_key}_{msg_id}_{emoji}", use_container_width=True):
                            for real_msg in trip.get("messages", []):
                                if real_msg.get("id") == msg_id:
                                    _toggle_reaction(real_msg, emoji, user)
                                    save_db(data)
                                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        with outer_right:
            can_delete = role == "admin" or msg.get("author") == user
            if can_delete:
                if st.button("🗑️", key=f"delete_msg_{trip_key}_{msg_id}", help="Nachricht löschen", use_container_width=True):
                    trip["messages"] = [m for m in trip.get("messages", []) if m.get("id") != msg_id]
                    save_db(data)
                    st.rerun()
            else:
                st.write("")

    with st.form(key=f"chat_form_{trip_key}", clear_on_submit=True):
        text = st.text_area("Nachricht", placeholder="Schreibe eine Nachricht ...", key=f"chat_text_{trip_key}")
        submitted = st.form_submit_button("Senden", use_container_width=True)
        if submitted:
            if text.strip():
                trip.setdefault("messages", []).append(
                    {
                        "id": new_id(),
                        "author": user,
                        "text": text.strip(),
                        "created_at": datetime.datetime.now().isoformat(timespec="minutes"),
                        "reactions": {},
                    }
                )
                save_db(data)
                st.rerun()
            else:
                st.warning("Bitte zuerst eine Nachricht eingeben.")
