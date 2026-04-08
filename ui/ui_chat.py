from __future__ import annotations

import datetime
import html
import streamlit as st

from core.storage import new_id, save_db

REACTIONS = ["👍", "❤️", "😂", "🎉", "😮", "😢", "🙏"]


def _message_author(msg: dict) -> str:
    author = (
        msg.get("author")
        or msg.get("user")
        or msg.get("name")
        or msg.get("sender")
        or msg.get("created_by")
        or msg.get("username")
        or msg.get("display_name")
    )

    if not author:
        participant = msg.get("participant")
        if isinstance(participant, dict):
            author = (
                participant.get("display_name")
                or participant.get("name")
                or participant.get("user")
            )

    if not author:
        meta = msg.get("meta")
        if isinstance(meta, dict):
            author = (
                meta.get("author")
                or meta.get("user")
                or meta.get("name")
                or meta.get("created_by")
            )

    return str(author).strip() if str(author or "").strip() else "Unbekannt"


def _message_text(msg: dict) -> str:
    text = (
        msg.get("text")
        or msg.get("message")
        or msg.get("content")
        or msg.get("body")
        or ""
    )
    return str(text)


def _message_timestamp(msg: dict) -> str:
    return (
        msg.get("created_at")
        or msg.get("timestamp")
        or msg.get("time")
        or msg.get("date")
        or ""
    )


def _ensure_message_shape(trip: dict, data: dict) -> None:
    changed = False
    for msg in trip.get("messages", []):
        if not msg.get("id"):
            msg["id"] = new_id()
            changed = True

        normalized_author = _message_author(msg)
        if msg.get("author") != normalized_author:
            msg["author"] = normalized_author
            changed = True

        normalized_text = _message_text(msg)
        if msg.get("text") != normalized_text:
            msg["text"] = normalized_text
            changed = True

        normalized_created_at = _message_timestamp(msg)
        if normalized_created_at and msg.get("created_at") != normalized_created_at:
            msg["created_at"] = normalized_created_at
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
            safe_author = html.escape(_message_author(msg))
            safe_text = html.escape(_message_text(msg)).replace("\n", "<br>")
            summary = _reaction_summary_html(msg, user)

            st.markdown(
                (
                    "<div class='me-chat-row'>"
                    "<div class='me-chat-head'>"
                    f"<div class='me-chat-author'>{safe_author}</div>"
                    f"<div class='me-soft'>{_format_ts(_message_timestamp(msg))}</div>"
                    "</div>"
                    f"<div class='me-chat-text'>{safe_text}</div>"
                    f"{summary}"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            with st.popover("😊 Reaktion", use_container_width=False):
                st.caption("Reaktion auswählen")
                cols = st.columns(len(REACTIONS))
                for col, emoji in zip(cols, REACTIONS):
                    with col:
                        if st.button(emoji, key=f"react_{trip_key}_{msg_id}_{emoji}", use_container_width=True):
                            for real_msg in trip.get("messages", []):
                                if real_msg.get("id") == msg_id:
                                    _toggle_reaction(real_msg, emoji, user)
                                    save_db(data)
                                    st.rerun()

        with outer_right:
            can_delete = role == "admin" or _message_author(msg) == user
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
                        "created_by": user,
                        "text": text.strip(),
                        "created_at": datetime.datetime.now().isoformat(timespec="minutes"),
                        "reactions": {},
                    }
                )
                save_db(data)
                st.rerun()
            else:
                st.warning("Bitte zuerst eine Nachricht eingeben.")
