from __future__ import annotations

import datetime
import json
import os
import uuid

DB_FILE = os.getenv("DB_FILE", "data/reisen_daten.json")


def load_db() -> dict:
    if not os.path.exists(DB_FILE):
        return {"trips": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"trips": {}}


def save_db(data: dict) -> None:
    os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


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
        trip.setdefault("messages", [])
        trip.setdefault("tasks", [])
        trip.setdefault("expenses", [])
        trip.setdefault("images", [])
        trip.setdefault("details", {})
        trip.setdefault("last_read", {})
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

        for msg in trip.get("messages", []):
            if isinstance(msg, dict):
                msg.setdefault("id", new_id("msg"))
                msg.setdefault("user", "Unbekannt")
                msg.setdefault("text", "")
                msg.setdefault("time", "")

        for task in trip.get("tasks", []):
            if isinstance(task, dict):
                task.setdefault("id", new_id("task"))
                task.setdefault("job", "")
                task.setdefault("who", [])
                task.setdefault("done", False)
                task.setdefault("category", "Ausrüstung")
                task.setdefault("for_all", False)
                task.setdefault("created_at", "")
                task.setdefault("created_by", "")
                task.setdefault("updated_at", task.get("created_at", ""))
                task.setdefault("updated_by", task.get("created_by", ""))
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
