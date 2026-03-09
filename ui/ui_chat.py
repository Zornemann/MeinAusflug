import streamlit as st

from app.chat_engine import render_chat as _render_chat_engine, chat_input as _chat_input_engine


def _resolve_trip_key(data: dict, requested: str) -> str:
    trips = data.get("trips", {}) if isinstance(data, dict) else {}
    if not requested:
        return requested
    if requested in trips:
        return requested

    requested_l = str(requested).strip().lower()
    for key, trip in trips.items():
        if not isinstance(trip, dict):
            continue

        aliases = trip.get("aliases", []) or []
        if isinstance(aliases, list):
            for alias in aliases:
                if str(alias).strip().lower() == requested_l:
                    return key

        if str(trip.get("name", "")).strip().lower() == requested_l:
            return key

        details = trip.get("details", {}) or {}
        for cand in (details.get("destination", ""), details.get("loc_name", "")):
            if str(cand).strip().lower() == requested_l:
                return key

    return requested


def render_chat(data: dict, trip_name: str, user: str):
    """
    Kompatibler Wrapper für die bestehende App-Struktur.
    Nutzt die stabile Chat-Engine mit nativer Streamlit-Darstellung,
    damit keine HTML-Tags mehr als Text sichtbar werden.
    Zusätzlich wird der echte Trip-Key aufgelöst, damit bei Aliasen
    oder umbenannten Reisen immer der richtige Datensatz geladen wird.
    """
    data.setdefault("trips", {})
    resolved_trip_name = _resolve_trip_key(data, trip_name)
    data["trips"].setdefault(resolved_trip_name, {})
    print(f"CHAT ACTIVE TRIP -> requested={trip_name!r}, resolved={resolved_trip_name!r}")

    st.subheader("💬 Chat")
    _render_chat_engine(data, resolved_trip_name, user)
    _chat_input_engine(data, resolved_trip_name, user)
