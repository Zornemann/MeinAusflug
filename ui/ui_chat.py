from __future__ import annotations

import datetime
import streamlit as st

from core.storage import new_id, save_db


def _ensure_message_ids(trip: dict, data: dict) -> None:
    changed = False
    for msg in trip.get("messages", []):
        if not msg.get("id"):
            msg["id"] = new_id()
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


def render_chat(data: dict, trip_key: str, user: str) -> None:
    trips = data.setdefault("trips", {})
    trip = trips.setdefault(trip_key, {})
    messages = trip.setdefault("messages", [])
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")

    _ensure_message_ids(trip, data)

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
        row_left, row_right = st.columns([18, 2])

        with row_left:
            st.markdown(
                (
                    "<div class='me-chat-row'>"
                    f"<div><strong>{msg.get('author', 'Unbekannt')}</strong></div>"
                    f"<div class='me-soft' style='font-size:0.9rem; margin: 0.15rem 0 0.6rem 0;'>{_format_ts(msg.get('created_at', ''))}</div>"
                    f"<div>{(msg.get('text') or '').replace(chr(10), '<br>')}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        can_delete = role == "admin" or msg.get("author") == user
        with row_right:
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
                    }
                )
                save_db(data)
                st.rerun()
            else:
                st.warning("Bitte zuerst eine Nachricht eingeben.")
