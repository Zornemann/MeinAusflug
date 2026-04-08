from __future__ import annotations

import datetime
import json
import os
import uuid
from copy import deepcopy

DB_FILE = os.getenv("DB_FILE", "data/reisen_daten.json")


def load_db() -> dict:
    if not os.path.exists(DB_FILE):
        return {"trips": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"trips": {}}


def _prepare_for_save(data: dict) -> dict:
    payload = deepcopy(data)
    trips = payload.setdefault("trips", {})
    for trip in trips.values():
        messages = trip.setdefault("messages", [])
        trip["chat"] = deepcopy(messages)
    return payload


def save_db(data: dict) -> None:
    os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
    payload = _prepare_for_save(data)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _normalize_message(msg: dict) -> dict:
    if not isinstance(msg, dict):
        return {
            "id": new_id("msg"),
            "user": "System",
            "text": str(msg),
            "time": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "read_by": [],
            "reactions": {},
        }

    reactions = msg.get("reactions") or {}
    if not isinstance(reactions, dict):
        reactions = {}

    normalized_reactions: dict[str, list[str]] = {}
    for emoji, users in reactions.items():
        if isinstance(users, list):
            cleaned = [str(u) for u in users if str(u).strip()]
        elif isinstance(users, str) and users.strip():
            cleaned = [users.strip()]
        else:
            cleaned = []
        normalized_reactions[str(emoji)] = list(dict.fromkeys(cleaned))

    return {
        "id": msg.get("id") or new_id("msg"),
        "user": msg.get("user") or msg.get("author") or "Unbekannt",
        "text": msg.get("text") or "",
        "time": msg.get("time") or msg.get("created_at") or datetime.datetime.now().replace(microsecond=0).isoformat(),
        "read_by": msg.get("read_by") if isinstance(msg.get("read_by"), list) else [],
        "reactions": normalized_reactions,
    }


def normalize_data(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    trips = data.setdefault("trips", {})
    for trip_key, trip in trips.items():
        if not isinstance(trip, dict):
            trips[trip_key] = {"name": str(trip_key)}
            trip = trips[trip_key]

        trip.setdefault("name", trip_key)
        trip.setdefault("participants", {})
        trip.setdefault("expenses", [])
        trip.setdefault("images", [])
        trip.setdefault("details", {})
        trip.setdefault("last_read", {})
        trip.setdefault("tasks", [])

        legacy_chat = trip.get("chat") if isinstance(trip.get("chat"), list) else []
        current_messages = trip.get("messages") if isinstance(trip.get("messages"), list) else []

        source_messages = current_messages or legacy_chat
        normalized_messages = [_normalize_message(msg) for msg in source_messages]
        trip["messages"] = normalized_messages
        trip["chat"] = deepcopy(normalized_messages)

        details = trip["details"]
        details.setdefault("destination", "")
        details.setdefault("city", "")
        details.setdefault("street", "")
        details.setdefault("postal_code", "")
        details.setdefault("homepage", "")
        details.setdefault("extra", "")
        details.setdefault("start_date", str(datetime.date.today()))
        details.setdefault("end_date", str(datetime.date.today()))
        details.setdefault("meet_date", str(datetime.date.today()))
        details.setdefault("meet_time", "18:00")

    return data


def mark_read(trip: dict, user: str, area: str) -> None:
    lr = trip.setdefault("last_read", {})
    user_lr = lr.setdefault(user, {})
    user_lr[area] = datetime.datetime.now().replace(microsecond=0).isoformat()


def get_chat_unread_count(trip: dict, user: str) -> int:
    last = trip.get("last_read", {}).get(user, {}).get("chat", "")
    return sum(
        1
        for msg in trip.get("messages", [])
        if isinstance(msg, dict) and msg.get("user") != user and (msg.get("time") or "") > last
    )


def get_checklist_unread_count(trip: dict, user: str) -> int:
    last = trip.get("last_read", {}).get(user, {}).get("checklist", "")
    unread = 0
    for task in trip.get("tasks", []):
        event_time = task.get("updated_at") or task.get("created_at") or ""
        event_user = task.get("updated_by") or task.get("created_by") or ""
        if event_user != user and event_time > last:
            unread += 1
    return unread
