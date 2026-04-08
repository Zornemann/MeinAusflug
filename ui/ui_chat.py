from __future__ import annotations

import datetime
import html
import streamlit as st

from core.storage import new_id, save_db

REACTIONS = ["👍", "❤️", "😂", "🎉", "😮", "😢", "🙏"]


def _raw_message_author(msg: dict) -> str:
    return str(msg.get("author") or msg.get("user") or msg.get("created_by") or msg.get("display_name") or "Unbekannt")


def _display_author(msg: dict, participants: dict) -> str:
    raw_author = _raw_message_author(msg)
    participant = participants.get(raw_author)
    if isinstance(participant, dict):
        display_name = str(participant.get("display_name") or "").strip()
        if display_name:
            return display_name
    for participant_id, participant_data in participants.items():
        if not isinstance(participant_data, dict):
            continue
        display_name = str(participant_data.get("display_name") or "").strip()
        aliases = {
            str(participant_id).strip(),
            str(participant_data.get("name") or "").strip(),
            str(participant_data.get("user") or "").strip(),
            str(participant_data.get("username") or "").strip(),
            display_name,
        }
        if raw_author in aliases and display_name:
            return display_name
    return raw_author


def _message_text(msg: dict) -> str:
    return str(msg.get("text") or "")


def _message_timestamp(msg: dict) -> str:
    return msg.get("created_at") or msg.get("time") or ""


def _format_ts(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return raw


def _mark_messages_as_seen(trip: dict, user: str) -> bool:
    changed = False
    for msg in trip.get("messages", []):
        seen = msg.setdefault("read_by", [])
        if user not in seen:
            seen.append(user)
            changed = True
    return changed


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
            pills.append(f"<span class='me-reaction-pill{active}'>{emoji} <strong>{len(users)}</strong></span>")
    return "<div class='me-reactions'>" + "".join(pills) + "</div>" if pills else ""


def render_chat(data: dict, trip_key: str, user: str) -> None:
    trips = data.setdefault("trips", {})
    trip = trips.setdefault(trip_key, {})
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")
    messages = trip.setdefault("messages", [])

    if _mark_messages_as_seen(trip, user):
        save_db(data)

    filter_col, info_col = st.columns([2, 1])
    with filter_col:
        search = st.text_input("Suche im Chat", placeholder="Nach Namen oder Text suchen ...", key=f"chat_search_{trip_key}")
    with info_col:
        only_pinned = st.checkbox("Nur angepinnte", key=f"chat_only_pinned_{trip_key}")

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
            st.caption(f"Deine Rolle: {role}")

    filtered_messages = list(messages)
    if search.strip():
        q = search.strip().lower()
        filtered_messages = [
            msg for msg in filtered_messages
            if q in _display_author(msg, participants).lower() or q in _message_text(msg).lower()
        ]
    if only_pinned:
        filtered_messages = [msg for msg in filtered_messages if msg.get("pinned")]

    filtered_messages.sort(
        key=lambda m: (
            0 if m.get("pinned") else 1,
            _message_timestamp(m),
        ),
        reverse=False,
    )

    if not filtered_messages:
        st.info("Keine Nachrichten für die aktuelle Ansicht vorhanden.")
    else:
        for idx, msg in enumerate(filtered_messages):
            msg_id = msg.get("id") or f"{idx}"
            author_raw = _raw_message_author(msg)
            author_display = _display_author(msg, participants)
            can_delete = role == "admin" or author_raw == user or author_display == user
            can_edit = role in {"admin", "editor"} or author_raw == user or author_display == user
            can_pin = role in {"admin", "editor"}

            left, right = st.columns([18, 2])
            with left:
                safe_author = html.escape(author_display)
                safe_text = html.escape(_message_text(msg)).replace("\n", "<br>")
                summary = _reaction_summary_html(msg, user)
                pin_marker = "📌 " if msg.get("pinned") else ""
                seen_names = []
                for seen_user in msg.get("read_by", []):
                    meta = participants.get(seen_user, {})
                    seen_names.append(meta.get("display_name") or seen_user)

                read_info = ""
                if seen_names:
                    read_info = f"<div class='me-soft' style='margin-top:.45rem;font-size:.82rem;'>Gelesen von: {html.escape(', '.join(seen_names[:6]))}</div>"

                st.markdown(
                    (
                        "<div class='me-chat-row'>"
                        "<div class='me-chat-head'>"
                        f"<div class='me-chat-author'>{pin_marker}{safe_author}</div>"
                        f"<div class='me-soft'>{_format_ts(_message_timestamp(msg))}</div>"
                        "</div>"
                        f"<div class='me-chat-text'>{safe_text}</div>"
                        f"{summary}"
                        f"{read_info}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )

                action_cols = st.columns([1.2, 1.4, 1.2, 6])
                with action_cols[0]:
                    with st.popover("😊", use_container_width=True):
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
                with action_cols[1]:
                    if can_edit:
                        with st.popover("✏️ Bearbeiten", use_container_width=True):
                            edit_text = st.text_area("Nachricht bearbeiten", value=_message_text(msg), key=f"edit_text_{trip_key}_{msg_id}")
                            if st.button("Änderung speichern", key=f"save_edit_{trip_key}_{msg_id}", use_container_width=True):
                                for real_msg in trip.get("messages", []):
                                    if real_msg.get("id") == msg_id:
                                        real_msg["text"] = edit_text.strip()
                                        real_msg["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
                                        save_db(data)
                                        st.rerun()
                with action_cols[2]:
                    if can_pin:
                        pin_label = "📌 Lösen" if msg.get("pinned") else "📌 Anpinnen"
                        if st.button(pin_label, key=f"pin_{trip_key}_{msg_id}", use_container_width=True):
                            for real_msg in trip.get("messages", []):
                                if real_msg.get("id") == msg_id:
                                    real_msg["pinned"] = not bool(real_msg.get("pinned"))
                                    save_db(data)
                                    st.rerun()

            with right:
                if can_delete and st.button("🗑️", key=f"delete_msg_{trip_key}_{msg_id}", help="Nachricht löschen", use_container_width=True):
                    trip["messages"] = [m for m in trip.get("messages", []) if m.get("id") != msg_id]
                    save_db(data)
                    st.rerun()

    can_post = role in {"admin", "editor", "member"}
    if can_post:
        with st.form(key=f"chat_form_{trip_key}", clear_on_submit=True):
            text = st.text_area("Nachricht", placeholder="Schreibe eine Nachricht ...", key=f"chat_text_{trip_key}")
            submitted = st.form_submit_button("Senden", use_container_width=True)
            if submitted:
                if text.strip():
                    trip.setdefault("messages", []).append(
                        {
                            "id": new_id("msg"),
                            "author": user,
                            "user": user,
                            "created_by": user,
                            "display_name": participants.get(user, {}).get("display_name") or user,
                            "text": text.strip(),
                            "created_at": datetime.datetime.now().isoformat(timespec="minutes"),
                            "reactions": {},
                            "read_by": [user],
                            "pinned": False,
                        }
                    )
                    save_db(data)
                    st.rerun()
                else:
                    st.warning("Bitte zuerst eine Nachricht eingeben.")
    else:
        st.info("Mit deiner Rolle kannst du den Chat lesen, aber keine neuen Nachrichten senden.")
