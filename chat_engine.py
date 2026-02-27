import streamlit as st
import datetime
import os
import time
import re
import html as _html
from typing import Optional, List, Tuple

from storage import save_db, new_id

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

def _now_iso() -> str:
    return datetime.datetime.now().isoformat()

def _format_time_hhmm(iso_or_hhmm: str) -> str:
    if not iso_or_hhmm:
        return ""
    if len(iso_or_hhmm) == 5 and ":" in iso_or_hhmm:
        return iso_or_hhmm
    try:
        dt = datetime.datetime.fromisoformat(iso_or_hhmm)
        return dt.strftime("%H:%M")
    except Exception:
        return str(iso_or_hhmm)[:5]

def _clean_legacy_text(t: str) -> str:
    if not t:
        return ""
    t = _META_RAW_RE.sub("", t)
    t = _META_ESC_RE.sub("", t)
    return t.strip()

def _safe_text_for_markdown(t: str) -> str:
    """
    Safe text for st.markdown:
    - remove legacy junk
    - escape to avoid unintended HTML rendering
    - keep line breaks
    """
    t = _clean_legacy_text(t or "")
    t = _html.escape(t)
    return t.replace("\n", "<br>")

def _safe_upload_path(msg_id: str, filename: str) -> str:
    base = os.path.basename(filename or "upload")
    name, ext = os.path.splitext(base)
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ", ".")).strip()
    safe = safe[:60] if safe else "upload"
    ext = ext[:12]
    return os.path.join(UPLOAD_FOLDER, f"{msg_id}_{safe}{ext}")

def _play_notification_sound():
    st.components.v1.html(
        """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/button-3.mp3" type="audio/mpeg">
        </audio>
        """,
        height=0,
    )

def _ensure_trip_structures(trip: dict):
    if "messages" not in trip or not isinstance(trip["messages"], list):
        trip["messages"] = []
    if "typing" not in trip or not isinstance(trip["typing"], dict):
        trip["typing"] = {}
    if "presence" not in trip or not isinstance(trip["presence"], dict):
        trip["presence"] = {}

def _participants_list(trip: dict) -> List[str]:
    p = trip.get("participants", {})
    if isinstance(p, dict):
        return list(p.keys())
    if isinstance(p, list):
        return list(p)
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

def _render_reactions_line(msg: dict):
    reactions = msg.get("reactions") or {}
    if not reactions:
        return
    parts = []
    for emoji, users in reactions.items():
        if isinstance(users, list) and users:
            parts.append(f"{emoji} {len(users)}")
    if parts:
        st.caption("  ".join(parts))

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
def render_online_bar(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    key = f"last_presence_write_{trip_name}"
    now = time.time()
    if key not in st.session_state or now - st.session_state[key] > 10:
        trip["presence"][user] = now
        st.session_state[key] = now
        save_db(data)

    online = get_online_users(trip, window_seconds=25)
    if online:
        st.caption(f"🟢 Online: {', '.join(online)}")
    else:
        st.caption("⚪ Niemand gerade online")


def render_chat(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    role = st.session_state.get("role", "member")
    total_users = _total_users(trip)

    # typing cleanup
    now = time.time()
    trip["typing"] = {u: ts for u, ts in trip["typing"].items() if now - ts < 7}

    # sound only on new last msg from others
    last_msg_id = trip["messages"][-1]["id"] if trip["messages"] else None
    ss_key = f"last_seen_msgid_{trip_name}"
    prev_last_id = st.session_state.get(ss_key)
    if last_msg_id and prev_last_id != last_msg_id:
        last_msg = trip["messages"][-1]
        if last_msg.get("user") != user and _is_visible_to_user(last_msg, user, role):
            _play_notification_sound()
        st.session_state[ss_key] = last_msg_id
    elif last_msg_id and prev_last_id is None:
        st.session_state[ss_key] = last_msg_id

    # Scroll container (IMPORTANT: no HTML wrapper around Streamlit widgets)
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

            is_me = (msg.get("user") == user)

            # mark read
            if not is_me and user not in msg["read_by"]:
                msg["read_by"].append(user)
                db_dirty = True

            # clean legacy text in-place
            if isinstance(msg.get("text"), str):
                cleaned = _clean_legacy_text(msg["text"])
                if cleaned != msg["text"]:
                    msg["text"] = cleaned
                    db_dirty = True

            time_str = _format_time_hhmm(msg.get("time", ""))
            ticks_txt, ticks_css = _compute_ticks(msg, total_users)

            header_name = "Ich" if is_me else msg.get("user", "Teilnehmer")

            # privacy label
            to = msg.get("to")
            privacy = ""
            if to not in (None, "", "ALL"):
                privacy = f"🔒 Privat" if not is_me else f"🔒 Privat an **{_html.escape(str(to))}**"

            # Use chat_message (stable layout)
            with st.chat_message("user" if is_me else "assistant"):
                st.markdown(f"**{_html.escape(str(header_name))}**  ", unsafe_allow_html=True)
                st.markdown(_safe_text_for_markdown(msg.get("text", "")), unsafe_allow_html=True)
                if privacy:
                    st.caption(privacy)

                # footer time + ticks
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

                # attachment
                if msg.get("file"):
                    try:
                        with open(msg["file"], "rb") as f:
                            st.download_button(
                                "📎 Anhang herunterladen",
                                data=f,
                                file_name=os.path.basename(msg["file"]),
                                key=f"dl_{trip_name}_{msg['id']}",
                            )
                    except Exception:
                        st.caption("📎 Datei nicht gefunden")

                # reactions
                rx_cols = st.columns([0.12, 0.12, 0.12, 0.12, 0.12])
                emojis = ["👍", "❤️", "😂", "😮", "😢"]
                for i, em in enumerate(emojis):
                    if rx_cols[i].button(em, key=f"rx_{trip_name}_{msg['id']}_{em}"):
                        _toggle_reaction(msg, em, user)
                        save_db(data)
                        st.rerun()
                _render_reactions_line(msg)

                # edit/delete
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

        # delete after render loop
        if to_delete_id and to_delete_msg:
            trip["messages"] = [m for m in trip["messages"] if m.get("id") != to_delete_id]
            try:
                if to_delete_msg.get("file") and os.path.exists(to_delete_msg["file"]):
                    os.remove(to_delete_msg["file"])
            except Exception:
                pass
            save_db(data)
            st.rerun()

    if db_dirty:
        save_db(data)

    # Page scroll to bottom so input is visible (best-effort)
    st.components.v1.html(
        """
        <script>
          try { window.parent.scrollTo(0, document.body.scrollHeight); } catch(e) {}
        </script>
        """,
        height=0,
    )


def chat_input(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]
    _ensure_trip_structures(trip)

    participants = sorted([p for p in _participants_list(trip) if p != user])
    recipients = ["ALL"] + participants
    recipient_label = {"ALL": "🌐 Alle (öffentlich)"}

    with st.form(f"chat_form_{trip_name}", clear_on_submit=True):
        a, b = st.columns([0.7, 0.3])
        recipient = b.selectbox(
            "Empfänger",
            options=recipients,
            format_func=lambda x: recipient_label.get(x, f"🔒 Privat an {x}"),
            label_visibility="collapsed",
            key=f"to_{trip_name}",
        )

        col1, col2 = st.columns([0.85, 0.15])
        text = col1.text_input(
            "Nachricht",
            label_visibility="collapsed",
            placeholder="Schreibe etwas…",
            key=f"txt_{trip_name}",
        )
        file = col2.file_uploader("📎", label_visibility="collapsed", key=f"file_{trip_name}")

        if text:
            trip["typing"][user] = time.time()

        send = st.form_submit_button("📨 Senden")

        if send and (text or file):
            if user in trip["typing"]:
                del trip["typing"][user]

            msg_id = new_id("msg")
            file_path = None

            if file:
                file_path = _safe_upload_path(msg_id, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())

            trip["messages"].append(
                {
                    "id": msg_id,
                    "user": user,
                    "text": (text or "").strip(),
                    "file": file_path,
                    "time": datetime.datetime.now().isoformat(),
                    "read_by": [user],
                    "to": recipient if recipient != "ALL" else "ALL",
                    "reactions": {},
                }
            )

            trip["presence"][user] = time.time()
            save_db(data)
            st.rerun()