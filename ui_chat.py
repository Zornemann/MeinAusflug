import datetime
import time

import streamlit as st

try:
    from core.push_service import send_push
    from core.storage import get_push_tokens_for_trip, new_id, save_db
except Exception:
    from storage import new_id, save_db, get_push_tokens_for_trip  # type: ignore
    from push_service import send_push  # type: ignore

try:
    from core.utils import format_time_short
except Exception:
    from utils import format_time_short  # type: ignore


def _compact_reaction_bar(message_id: str):
    emojis = ["👍", "❤️", "😂", "😮", "😢"]
    cols = st.columns(len(emojis), gap="small")
    selected = None
    for i, emoji in enumerate(emojis):
        with cols[i]:
            if st.button(emoji, key=f"react_{message_id}_{emoji}", use_container_width=True):
                selected = emoji
    return selected


def _send_chat_push_if_needed(trip: dict, trip_name: str, sender: str, text: str):
    try:
        tokens = get_push_tokens_for_trip(trip.get("trip_id") or trip_name, exclude_user=sender)
        if not tokens:
            return
        send_push(
            tokens=tokens,
            title=f"Neue Nachricht in {trip.get('name') or trip_name}",
            body=f"{sender}: {(text or '')[:80]}",
        )
    except Exception:
        pass


def render_chat(data, trip_name, user):
    trip = data["trips"][trip_name]

    if "messages" not in trip or not isinstance(trip["messages"], list):
        trip["messages"] = []
    if "typing" not in trip or not isinstance(trip["typing"], dict):
        trip["typing"] = {}

    participants = trip.get("participants", {})
    total_users = max(len(participants), 1)

    now = time.time()
    trip["typing"] = {u: ts for u, ts in trip["typing"].items() if now - ts < 7}

    for idx, msg in enumerate(trip["messages"]):
        if "read_by" not in msg or not isinstance(msg["read_by"], list):
            msg["read_by"] = []
        if user not in msg["read_by"]:
            msg["read_by"].append(user)

        is_me = msg.get("user") == user
        msg_id = msg.get("id") or f"msg_{idx}"
        text = msg.get("text", "")
        time_val = msg.get("time", datetime.datetime.now().isoformat())
        display_time = format_time_short(time_val)

        read_count = len(msg.get("read_by", []))
        if read_count >= total_users:
            status_haken = "<span style='color:#34b7f1; font-weight:bold;'>✔✔</span>"
        elif read_count > 1:
            status_haken = "<span style='color:gray;'>✔✔</span>"
        else:
            status_haken = "<span style='color:gray;'>✔</span>"

        if is_me:
            st.markdown(
                f"""
                <div style='
                    text-align:right;
                    background:#dcf8c6;
                    padding:12px;
                    border-radius:15px 15px 2px 15px;
                    margin:8px 0 4px auto;
                    color:black;
                    max-width:85%;
                    box-shadow:2px 2px 5px rgba(0,0,0,0.1);
                    border:1px solid #c7e5b3;'>
                    <b style='color:#4a7c2c;'>Ich</b><br>{text}
                    <div style='font-size:10px; color:#777; margin-top:5px;'>
                        {display_time} {status_haken}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style='
                    text-align:left;
                    background:#ffffff;
                    padding:12px;
                    border-radius:15px 15px 15px 2px;
                    margin:8px auto 4px 0;
                    color:black;
                    max-width:85%;
                    box-shadow:-2px 2px 5px rgba(0,0,0,0.08);
                    border:1px solid #eee;'>
                    <b style='color:#555;'>{msg.get('user', 'Teilnehmer')}</b><br>{text}
                    <div style='font-size:10px; color:#999; margin-top:5px;'>
                        {display_time}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.container():
            reaction = _compact_reaction_bar(msg_id)
            if reaction:
                msg.setdefault("reactions", {})
                msg["reactions"].setdefault(reaction, [])
                if user not in msg["reactions"][reaction]:
                    msg["reactions"][reaction].append(user)
                    save_db(data)
                    st.rerun()

            reactions = msg.get("reactions", {})
            if reactions:
                chips = []
                for emoji, users in reactions.items():
                    if isinstance(users, list) and users:
                        chips.append(f"{emoji} {len(users)}")
                if chips:
                    st.caption("   ".join(chips))

    typing_others = [u for u in trip["typing"] if u != user]
    if typing_others:
        st.markdown(
            f"<i style='font-size:12px; color:#888;'>✍️ {', '.join(typing_others)} schreibt gerade...</i>",
            unsafe_allow_html=True,
        )

    new_msg_text = st.text_input(
        "Nachricht schreiben",
        placeholder="Deine Nachricht...",
        key=f"chat_input_val_{trip_name}",
        label_visibility="collapsed",
    )

    if new_msg_text:
        trip["typing"][user] = time.time()

    if st.button("👉 Abschicken", key=f"chat_send_btn_{trip_name}", use_container_width=True):
        if new_msg_text:
            if user in trip["typing"]:
                del trip["typing"][user]

            new_entry = {
                "id": new_id("msg"),
                "user": user,
                "text": new_msg_text,
                "time": datetime.datetime.now().isoformat(),
                "read_by": [user],
                "reactions": {},
            }
            trip["messages"].append(new_entry)
            save_db(data)
            _send_chat_push_if_needed(trip, trip_name, user, new_msg_text)
            st.rerun()
