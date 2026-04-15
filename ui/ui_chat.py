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


def _chat_styles() -> None:
    st.markdown(
        """
        <style>
        .ma-chat-shell {
          display: flex;
          flex-direction: column;
          gap: .9rem;
          margin-top: .35rem;
          margin-bottom: .65rem;
        }

        .ma-chat-card {
          background: linear-gradient(180deg, rgba(14,22,42,.68), rgba(9,15,31,.72));
          border: 1px solid rgba(130,153,196,.14);
          border-radius: 22px;
          padding: 1rem 1rem .9rem 1rem;
          box-shadow: 0 10px 22px rgba(0,0,0,.14);
        }

        .ma-chat-card.mine {
          border-color: rgba(124,156,255,.32);
          box-shadow: 0 12px 24px rgba(124,156,255,.08);
        }

        .ma-chat-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: .85rem;
          margin-bottom: .55rem;
        }

        .ma-chat-person {
          display: flex;
          align-items: center;
          gap: .7rem;
          min-width: 0;
        }

        .ma-chat-avatar {
          width: 38px;
          height: 38px;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-weight: 800;
          font-size: .95rem;
          color: #ffffff;
          background: linear-gradient(180deg, rgba(88,122,214,.92), rgba(57,84,158,.96));
          border: 1px solid rgba(255,255,255,.10);
          flex-shrink: 0;
        }

        .ma-chat-namewrap {
          min-width: 0;
          display: flex;
          flex-direction: column;
          gap: .05rem;
        }

        .ma-chat-name {
          font-weight: 800;
          color: #ffffff;
          font-size: 1rem;
          line-height: 1.15;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .ma-chat-sub {
          color: #9fb0d4;
          font-size: .82rem;
          line-height: 1.1;
        }

        .ma-chat-text {
          color: #f7f9fc;
          line-height: 1.55;
          font-size: .98rem;
          white-space: normal;
          word-break: break-word;
          margin-top: .2rem;
        }

        .ma-chat-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: .75rem;
          margin-top: .75rem;
          flex-wrap: wrap;
        }

        .ma-chat-seen {
          color: #8ea1c7;
          font-size: .8rem;
        }

        .ma-chat-tools {
          display: flex;
          align-items: center;
          gap: .45rem;
          flex-wrap: wrap;
          margin-top: .55rem;
        }

        .ma-chat-search-wrap {
          background: rgba(10,16,31,.34);
          border: 1px solid rgba(130,153,196,.08);
          border-radius: 18px;
          padding: .25rem .25rem .2rem .25rem;
          margin-bottom: .75rem;
        }

        .ma-chat-empty {
          background: rgba(14,21,40,.42);
          border: 1px dashed rgba(130,153,196,.18);
          border-radius: 18px;
          padding: 1rem;
          color: #c7d3ef;
        }

        .ma-chat-compose-label {
          margin-top: .1rem;
          margin-bottom: .35rem;
          font-weight: 700;
        }

        @media (max-width: 768px) {
          .ma-chat-card {
            padding: .85rem .85rem .8rem .85rem;
            border-radius: 18px;
          }
          .ma-chat-head {
            align-items: flex-start;
            flex-direction: column;
            gap: .45rem;
          }
          .ma-chat-meta {
            align-items: flex-start;
            flex-direction: column;
            gap: .45rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _avatar_text(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned:
        return "?"
    parts = [p for p in cleaned.split() if p]
    if len(parts) >= 2:
        return (parts[0][:1] + parts[1][:1]).upper()
    return cleaned[:2].upper()


def render_chat(data: dict, trip_key: str, user: str) -> None:
    trips = data.setdefault("trips", {})
    trip = trips.setdefault(trip_key, {})
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")
    messages = trip.setdefault("messages", [])

    _chat_styles()

    if _mark_messages_as_seen(trip, user):
        save_db(data)

    toolbar_left, toolbar_right = st.columns([3.2, 1.2])
    with toolbar_left:
        st.markdown("<div class='ma-chat-search-wrap'>", unsafe_allow_html=True)
        search = st.text_input(
            "Suche im Chat",
            placeholder="Nach Namen oder Text suchen ...",
            key=f"chat_search_{trip_key}",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with toolbar_right:
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
        st.markdown(
            "<div class='ma-chat-empty'>Noch keine Nachrichten für die aktuelle Ansicht vorhanden.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='ma-chat-shell'>", unsafe_allow_html=True)
        for idx, msg in enumerate(filtered_messages):
            msg_id = msg.get("id") or f"{idx}"
            author_raw = _raw_message_author(msg)
            author_display = _display_author(msg, participants)
            can_delete = role == "admin" or author_raw == user or author_display == user
            can_edit = role in {"admin", "editor"} or author_raw == user or author_display == user
            can_pin = role in {"admin", "editor"}

            is_mine = author_raw == user or author_display == user
            summary = _reaction_summary_html(msg, user)
            safe_author = html.escape(author_display)
            safe_text = html.escape(_message_text(msg)).replace("\n", "<br>")
            pin_marker = "📌 " if msg.get("pinned") else ""
            avatar = html.escape(_avatar_text(author_display))
            mine_class = " mine" if is_mine else ""

            seen_names = []
            for seen_user in msg.get("read_by", []):
                meta = participants.get(seen_user, {})
                seen_names.append(meta.get("display_name") or seen_user)

            seen_html = ""
            if seen_names:
                seen_html = f"<div class='ma-chat-seen'>Gelesen von: {html.escape(', '.join(seen_names[:6]))}</div>"

            st.markdown(
                (
                    f"<div class='ma-chat-card{mine_class}'>"
                    "<div class='ma-chat-head'>"
                    "<div class='ma-chat-person'>"
                    f"<div class='ma-chat-avatar'>{avatar}</div>"
                    "<div class='ma-chat-namewrap'>"
                    f"<div class='ma-chat-name'>{pin_marker}{safe_author}</div>"
                    f"<div class='ma-chat-sub'>{_format_ts(_message_timestamp(msg))}</div>"
                    "</div>"
                    "</div>"
                    "</div>"
                    f"<div class='ma-chat-text'>{safe_text}</div>"
                    f"{summary}"
                    "<div class='ma-chat-meta'>"
                    f"{seen_html or '<div></div>'}"
                    "</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            action_cols = st.columns([1.0, 1.25, 1.0, 8.75])
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
                    pin_label = "📌 Lösen" if msg.get("pinned") else "📌 Pin"
                    if st.button(pin_label, key=f"pin_{trip_key}_{msg_id}", use_container_width=True):
                        for real_msg in trip.get("messages", []):
                            if real_msg.get("id") == msg_id:
                                real_msg["pinned"] = not bool(real_msg.get("pinned"))
                                save_db(data)
                                st.rerun()
            with action_cols[3]:
                st.write("")
            if can_delete:
                delete_cols = st.columns([11.4, 0.6])
                with delete_cols[1]:
                    if st.button("🗑️", key=f"delete_msg_{trip_key}_{msg_id}", help="Nachricht löschen", use_container_width=True):
                        trip["messages"] = [m for m in trip.get("messages", []) if m.get("id") != msg_id]
                        save_db(data)
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    can_post = role in {"admin", "editor", "member"}
    if can_post:
        st.markdown("<div class='ma-chat-compose-label'>Nachricht</div>", unsafe_allow_html=True)
        with st.form(key=f"chat_form_{trip_key}", clear_on_submit=True):
            text = st.text_area(
                "Nachricht",
                placeholder="Schreibe eine Nachricht ...",
                key=f"chat_text_{trip_key}",
                label_visibility="collapsed",
                height=120,
            )
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
