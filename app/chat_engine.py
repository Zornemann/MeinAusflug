import datetime
import html as _html
import os
import re
import time
from typing import List, Optional, Tuple

import streamlit as st

from core.storage import new_id, normalize_data, save_db

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Legacy cleanup (robust)
# -----------------------------
# RAW:     <div class="meta meta-left"> ... </div>
# ESCAPED: &lt;div class="meta meta-left"&gt; ... &lt;/div&gt;
_META_RAW_RE = re.compile(
    r"<div[^>]*\bclass\s*=\s*['\"][^'\"]*\bmeta\b[^'\"]*['\"][\s\S]*?</div>",
    re.IGNORECASE,
)
_META_ESC_RE = re.compile(
    r"&lt;div[^&]*\bclass\s*=\s*(?:&quot;|\"|')?[^&]*\bmeta\b[^&]*(?:&quot;|\"|')?[\s\S]*?&lt;/div&gt;",
    re.IGNORECASE,
)

REACTION_EMOJIS = ["👍", "❤️", "😂", "😮", "😢"]


def _now_iso() -> str:
    return datetime.datetime.now().isoformat()


def _format_time_hhmm(iso_or_hhmm: str) -> str:
    if not iso_or_hhmm:
        return ""
    try:
        text = str(iso_or_hhmm).strip()
        if len(text) == 5 and ":" in text:
            return text
        dt = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        text = str(iso_or_hhmm).strip()
        return text[:16]


def _clean_legacy_text(text: str) -> str:
    if not text:
        return ""
    text = _META_RAW_RE.sub("", text)
    text = _META_ESC_RE.sub("", text)
    return text.strip()


def _safe_text_for_markdown(text: str) -> str:
    """
    Safe text for st.markdown:
    - remove legacy junk
    - escape to avoid unintended HTML rendering
    - keep line breaks
    """
    text = _clean_legacy_text(text or "")
    text = _html.escape(text)
    return text.replace("\n", "<br>")


def _safe_upload_path(msg_id: str, filename: str) -> str:
    base = os.path.basename(filename or "upload")
    name, ext = os.path.splitext(base)
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ", ".")).strip()
    safe = safe[:60] if safe else "upload"
    ext = ext[:12]
    return os.path.join(UPLOAD_FOLDER, f"{msg_id}_{safe}{ext}")


def _play_notification_sound() -> None:
    # Platzhalter: Browser-/native Benachrichtigung läuft an anderer Stelle.
    return


def _ensure_trip_structures(trip: dict) -> None:
    messages = trip.get("messages") if isinstance(trip.get("messages"), list) else []
    chat = trip.get("chat") if isinstance(trip.get("chat"), list) else []
    merged = []
    seen = set()
    for src in (messages, chat):
        for msg in src:
            mid = msg.get("id") if isinstance(msg, dict) else None
            marker = mid or str(msg)
            if marker in seen:
                continue
            seen.add(marker)
            merged.append(msg)
    trip["messages"] = merged
    trip["chat"] = merged
    if "typing" not in trip or not isinstance(trip["typing"], dict):
        trip["typing"] = {}
    if "presence" not in trip or not isinstance(trip["presence"], dict):
        trip["presence"] = {}


def _participants_list(trip: dict) -> List[str]:
    participants = trip.get("participants", {})
    if isinstance(participants, dict):
        return list(participants.keys())
    if isinstance(participants, list):
        return list(participants)
    return []


def _total_users(trip: dict) -> int:
    return max(1, len(_participants_list(trip)))


def _compute_ticks(msg: dict, total_users: int) -> Tuple[str, str]:
    read_by = msg.get("read_by", []) or []
    read_count = len(set(read_by))
    if total_users <= 1:
        return "✔", "color: gray;"
    if read_count >= total_users:
        return "✔✔", "color:#34b7f1; font-weight:700;"
    if read_count > 1:
        return "✔✔", "color: gray;"
    return "✔", "color: gray;"


def _is_visible_to_user(msg: dict, user: str, role: str) -> bool:
    to = msg.get("to")
    sender = msg.get("user")
    if role == "admin":
        return True
    if to in (None, "", "ALL"):
        return True
    return sender == user or to == user


def _toggle_reaction(msg: dict, emoji: str, user: str) -> None:
    if "reactions" not in msg or not isinstance(msg["reactions"], dict):
        msg["reactions"] = {}
    users = msg["reactions"].get(emoji, [])
    if not isinstance(users, list):
        users = []
    if user in users:
        users = [u for u in users if u != user]
    else:
        users = users + [user]
    if users:
        msg["reactions"][emoji] = users
    else:
        msg["reactions"].pop(emoji, None)


def _render_reactions_line(msg: dict) -> None:
    reactions = msg.get("reactions") or {}
    if not reactions:
        return
    parts = []
    for emoji, users in reactions.items():
        if isinstance(users, list) and users:
            parts.append(f"{emoji} {len(users)}")
    if parts:
        st.caption(" · ".join(parts))


def _render_reaction_buttons(msg: dict, trip_name: str, user: str, data: dict) -> None:
    st.markdown(
        """
        <style>
        .compact-reactions [data-testid="column"] {padding-right: 0.2rem !important;}
        .compact-reactions .stButton > button {
            min-height: 2rem !important;
            padding: 0.15rem 0.35rem !important;
            font-size: 0.95rem !important;
            border-radius: 999px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="compact-reactions">', unsafe_allow_html=True)
    cols = st.columns([1, 1, 1, 1, 1, 8], gap="small")
    for idx, emoji in enumerate(REACTION_EMOJIS):
        if cols[idx].button(emoji, key=f"rx_{trip_name}_{msg['id']}_{emoji}", use_container_width=True):
            _toggle_reaction(msg, emoji, user)
            save_db(data)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    _render_reactions_line(msg)


# -----------------------------
# Presence
# -----------------------------
def get_online_users(trip: dict, window_seconds: int = 20) -> List[str]:
    now = time.time()
    presence = trip.get("presence", {})
    if not isinstance(presence, dict):
        return []
    return sorted([u for u, ts in presence.items() if now - ts <= window_seconds])


# -----------------------------
# Public API
# -----------------------------
def render_online_bar(data: dict, trip_name: str, user: str) -> None:
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    session_key = f"last_presence_write_{trip_name}"
    now = time.time()
    if session_key not in st.session_state or now - st.session_state[session_key] > 10:
        trip["presence"][user] = now
        st.session_state[session_key] = now
        save_db(data)

    online = get_online_users(trip, window_seconds=25)
    if online:
        st.caption(f"🟢 Online: {', '.join(online)}")
    else:
        st.caption("⚪ Niemand gerade online")


def render_chat(data: dict, trip_name: str, user: str) -> None:
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    role = st.session_state.get("role", "member")
    total_users = _total_users(trip)

    # typing cleanup
    now = time.time()
    trip["typing"] = {u: ts for u, ts in trip["typing"].items() if now - ts < 7}

    # Sound only on new last msg from others
    last_msg_id = trip["messages"][-1]["id"] if trip["messages"] else None
    session_key = f"last_seen_msgid_{trip_name}"
    prev_last_id = st.session_state.get(session_key)
    if last_msg_id and prev_last_id != last_msg_id:
        last_msg = trip["messages"][-1]
        if last_msg.get("user") != user and _is_visible_to_user(last_msg, user, role):
            _play_notification_sound()
        st.session_state[session_key] = last_msg_id
    elif last_msg_id and prev_last_id is None:
        st.session_state[session_key] = last_msg_id

    db_dirty = False

    with st.container(height=450, border=True):
        to_delete_id: Optional[str] = None
        to_delete_msg: Optional[dict] = None

        for msg in list(trip["messages"]):
            msg.setdefault("id", new_id("msg"))
            msg.setdefault("user", "Teilnehmer")
            msg.setdefault("text", "")
            msg.setdefault("time", _now_iso())
            msg.setdefault("read_by", [])
            msg.setdefault("reactions", {})

            if not _is_visible_to_user(msg, user, role):
                continue

            is_me = msg.get("user") == user

            # Mark read
            if not is_me and user not in msg["read_by"]:
                msg["read_by"].append(user)
                db_dirty = True

            # Clean legacy text in-place
            if isinstance(msg.get("text"), str):
                cleaned = _clean_legacy_text(msg["text"])
                if cleaned != msg["text"]:
                    msg["text"] = cleaned
                    db_dirty = True

            time_str = _format_time_hhmm(msg.get("time", ""))
            ticks_txt, ticks_css = _compute_ticks(msg, total_users)
            header_name = "Ich" if is_me else msg.get("user", "Teilnehmer")

            # Privacy label
            to = msg.get("to")
            privacy = ""
            if to not in (None, "", "ALL"):
                privacy = "🔒 Privat" if not is_me else f"🔒 Privat an **{_html.escape(str(to))}**"

            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(f"**{_html.escape(str(header_name))}**", unsafe_allow_html=True)
                st.markdown(_safe_text_for_markdown(msg.get("text", "")), unsafe_allow_html=True)
                if privacy:
                    st.caption(privacy)

                if is_me:
                    st.markdown(
                        f"<div style='font-size:11px;color:#777;text-align:right;'>{time_str} "
                        f"<span style='{ticks_css}'>{ticks_txt}</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='font-size:11px;color:#999;text-align:left;'>{time_str}</div>",
                        unsafe_allow_html=True,
                    )

                if msg.get("file"):
                    try:
                        with open(msg["file"], "rb") as file_handle:
                            st.download_button(
                                "📎 Anhang herunterladen",
                                data=file_handle,
                                file_name=os.path.basename(msg["file"]),
                                key=f"dl_{trip_name}_{msg['id']}",
                            )
                    except Exception:
                        st.caption("📎 Datei nicht gefunden")

                _render_reaction_buttons(msg, trip_name, user, data)

                can_moderate = is_me or role == "admin"
                if can_moderate:
                    c1, c2 = st.columns([0.15, 0.15])
                    if c1.button("✏️ Bearbeiten", key=f"edit_btn_{trip_name}_{msg['id']}"):
                        st.session_state[f"edit_{trip_name}_{msg['id']}"] = True
                    if c2.button("🗑️ Löschen", key=f"del_btn_{trip_name}_{msg['id']}"):
                        to_delete_id = msg["id"]
                        to_delete_msg = msg

                if st.session_state.get(f"edit_{trip_name}_{msg['id']}"):
                    new_text = st.text_area(
                        "Text bearbeiten",
                        value=msg.get("text", ""),
                        key=f"edit_input_{trip_name}_{msg['id']}",
                    )
                    s1, s2 = st.columns([0.2, 0.2])
                    if s1.button("💾 Speichern", key=f"save_btn_{trip_name}_{msg['id']}"):
                        msg["text"] = (new_text or "").strip()
                        st.session_state[f"edit_{trip_name}_{msg['id']}"] = False
                        save_db(data)
                        st.rerun()
                    if s2.button("Abbrechen", key=f"cancel_btn_{trip_name}_{msg['id']}"):
                        st.session_state[f"edit_{trip_name}_{msg['id']}"] = False
                        st.rerun()

        typing_others = [u for u in trip["typing"].keys() if u != user]
        if typing_others:
            st.caption(f"✍️ {', '.join(typing_others)} schreibt gerade…")

        if to_delete_id and to_delete_msg:
            trip["messages"] = [m for m in trip["messages"] if m.get("id") != to_delete_id]
            try:
                if to_delete_msg.get("file") and os.path.exists(to_delete_msg["file"]):
                    os.remove(to_delete_msg["file"])
            except Exception:
                pass
            trip["chat"] = trip["messages"]
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()

    if db_dirty:
        save_db(data)


def chat_input(data: dict, trip_name: str, user: str) -> None:
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    participants = sorted([p for p in _participants_list(trip) if p != user])
    recipients = ["ALL"] + participants
    recipient_label = {"ALL": "🌐 Alle (öffentlich)"}

    with st.form(f"chat_form_{trip_name}", clear_on_submit=True):
        col_message, col_recipient = st.columns([0.7, 0.3])
        recipient = col_recipient.selectbox(
            "Empfänger",
            options=recipients,
            format_func=lambda x: recipient_label.get(x, f"🔒 Privat an {x}"),
            label_visibility="collapsed",
            key=f"to_{trip_name}",
        )

        col_text, col_file = st.columns([0.85, 0.15])
        text = col_text.text_input(
            "Nachricht",
            label_visibility="collapsed",
            placeholder="Schreibe etwas…",
            key=f"txt_{trip_name}",
        )
        file = col_file.file_uploader("📎", label_visibility="collapsed", key=f"file_{trip_name}")

        if text:
            trip["typing"][user] = time.time()

        send = st.form_submit_button("📨 Senden")

        if send and (text or file):
            trip["typing"].pop(user, None)

            msg_id = new_id("msg")
            file_path = None

            if file:
                file_path = _safe_upload_path(msg_id, file.name)
                with open(file_path, "wb") as file_handle:
                    file_handle.write(file.getbuffer())

            new_msg = {
                "id": msg_id,
                "user": user,
                "text": (text or "").strip(),
                "file": file_path,
                "time": _now_iso(),
                "read_by": [user],
                "to": recipient if recipient != "ALL" else "ALL",
                "reactions": {},
            }
            trip["messages"].append(new_msg)
            trip["chat"] = trip["messages"]
            trip["presence"][user] = time.time()
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()
