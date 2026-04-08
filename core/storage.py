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


def _extract_author(msg: dict) -> str:
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
                or participant.get("id")
            )
    if not author:
        meta = msg.get("meta")
        if isinstance(meta, dict):
            author = (
                meta.get("author")
                or meta.get("user")
                or meta.get("name")
                or meta.get("created_by")
                or meta.get("display_name")
            )
    return str(author).strip() if str(author or "").strip() else "Unbekannt"


def _extract_text(msg: dict) -> str:
    return str(msg.get("text") or msg.get("message") or msg.get("content") or msg.get("body") or "")


def _extract_time(msg: dict) -> str:
    return (
        msg.get("time")
        or msg.get("created_at")
        or msg.get("timestamp")
        or msg.get("date")
        or datetime.datetime.now().replace(microsecond=0).isoformat()
    )


def _normalize_message(msg: dict) -> dict:
    if not isinstance(msg, dict):
        now = datetime.datetime.now().replace(microsecond=0).isoformat()
        return {
            "id": new_id("msg"),
            "author": "System",
            "user": "System",
            "created_by": "System",
            "display_name": "System",
            "text": str(msg),
            "message": str(msg),
            "time": now,
            "created_at": now,
            "read_by": [],
            "reactions": {},
            "pinned": False,
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

    author = _extract_author(msg)
    text = _extract_text(msg)
    timestamp = _extract_time(msg)

    return {
        "id": msg.get("id") or new_id("msg"),
        "author": author,
        "user": author,
        "created_by": msg.get("created_by") or author,
        "display_name": msg.get("display_name") or author,
        "text": text,
        "message": text,
        "time": timestamp,
        "created_at": msg.get("created_at") or timestamp,
        "updated_at": msg.get("updated_at") or "",
        "read_by": msg.get("read_by") if isinstance(msg.get("read_by"), list) else [],
        "reactions": normalized_reactions,
        "pinned": bool(msg.get("pinned")),
    }


def _normalize_task(task: dict) -> dict:
    if not isinstance(task, dict):
        now = datetime.datetime.now().replace(microsecond=0).isoformat()
        return {
            "id": new_id("task"),
            "text": str(task),
            "assignees": [],
            "category": "Sonstiges",
            "for_all": False,
            "done": False,
            "priority": "Mittel",
            "due_date": "",
            "created_at": now,
            "created_by": "",
            "updated_at": now,
            "updated_by": "",
        }

    assignees = task.get("assignees")
    if not isinstance(assignees, list):
        if isinstance(assignees, str) and assignees.strip():
            assignees = [assignees.strip()]
        else:
            assignees = []

    return {
        "id": task.get("id") or new_id("task"),
        "text": str(task.get("text") or task.get("item") or task.get("title") or task.get("task") or "Unbenannter Eintrag"),
        "assignees": [str(a) for a in assignees if str(a).strip()],
        "category": str(task.get("category") or "Sonstiges"),
        "for_all": bool(task.get("for_all") or task.get("forall") or task.get("all")),
        "done": bool(task.get("done") or task.get("checked") or task.get("completed")),
        "priority": str(task.get("priority") or "Mittel"),
        "due_date": str(task.get("due_date") or ""),
        "created_at": task.get("created_at") or datetime.datetime.now().replace(microsecond=0).isoformat(),
        "created_by": str(task.get("created_by") or ""),
        "updated_at": task.get("updated_at") or "",
        "updated_by": str(task.get("updated_by") or ""),
    }


def _normalize_expense(exp: dict) -> dict:
    if not isinstance(exp, dict):
        return {
            "id": new_id("exp"),
            "title": str(exp),
            "payer": "",
            "amount": 0.0,
            "shared_with": [],
            "created_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "notes": "",
            "category": "Allgemein",
        }
    shared_with = exp.get("shared_with")
    if not isinstance(shared_with, list):
        if isinstance(shared_with, str) and shared_with.strip():
            shared_with = [shared_with.strip()]
        else:
            shared_with = []
    return {
        "id": exp.get("id") or new_id("exp"),
        "title": str(exp.get("title") or exp.get("name") or "Ausgabe"),
        "payer": str(exp.get("payer") or ""),
        "amount": float(exp.get("amount", 0) or 0),
        "shared_with": [str(x) for x in shared_with if str(x).strip()],
        "created_at": exp.get("created_at") or datetime.datetime.now().replace(microsecond=0).isoformat(),
        "notes": str(exp.get("notes") or ""),
        "category": str(exp.get("category") or "Allgemein"),
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
        trip.setdefault("images", [])
        trip.setdefault("details", {})
        trip.setdefault("last_read", {})

        legacy_chat = trip.get("chat") if isinstance(trip.get("chat"), list) else []
        current_messages = trip.get("messages") if isinstance(trip.get("messages"), list) else []
        source_messages = current_messages or legacy_chat
        normalized_messages = [_normalize_message(msg) for msg in source_messages]
        trip["messages"] = normalized_messages
        trip["chat"] = deepcopy(normalized_messages)

        tasks = trip.get("tasks") if isinstance(trip.get("tasks"), list) else []
        trip["tasks"] = [_normalize_task(task) for task in tasks]

        expenses = trip.get("expenses") if isinstance(trip.get("expenses"), list) else []
        trip["expenses"] = [_normalize_expense(exp) for exp in expenses]

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

        participants = trip["participants"]
        for participant_key, meta in list(participants.items()):
            if not isinstance(meta, dict):
                participants[participant_key] = {
                    "display_name": str(participant_key),
                    "role": "member",
                }
                meta = participants[participant_key]
            meta.setdefault("display_name", str(participant_key))
            if meta.get("role") not in {"admin", "editor", "member", "viewer"}:
                meta["role"] = "member"

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
        if isinstance(msg, dict)
        and (msg.get("user") or msg.get("author")) != user
        and (msg.get("time") or msg.get("created_at") or "") > last
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
