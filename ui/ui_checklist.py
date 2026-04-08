from __future__ import annotations

import datetime
import html
import streamlit as st

from core.storage import new_id, save_db

CATEGORIES = ["Ausrüstung", "Verpflegung", "Sonstiges"]


def _badge(label: str, bg: str, fg: str = "#f8fbff") -> str:
    return (
        f"<span style='display:inline-block; margin:0 .35rem .35rem 0; padding:.18rem .6rem; "
        f"border-radius:999px; background:{bg}; color:{fg}; font-size:.8rem; border:1px solid rgba(255,255,255,.08);'>"
        f"{html.escape(label)}</span>"
    )


def render_checklist(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]
    st.header("🧭 Ausrüstung & Verpflegung")

    participants = trip.get("participants", {})
    crew = sorted(list(participants.keys()))
    tasks = trip.setdefault("tasks", [])

    filter_col_1, filter_col_2 = st.columns([0.58, 0.42])
    with filter_col_1:
        sel_user = st.selectbox("🔍 Zeige Items von:", ["Alle"] + crew, key=f"filter_user_{trip_name}")
    with filter_col_2:
        sel_category = st.selectbox("Kategorie filtern:", ["Alle"] + CATEGORIES, key=f"filter_category_{trip_name}")

    display_tasks = tasks
    if sel_user != "Alle":
        display_tasks = [
            t for t in display_tasks
            if t.get("for_all") or (isinstance(t.get("who"), list) and sel_user in t.get("who", []))
        ]
    if sel_category != "Alle":
        display_tasks = [t for t in display_tasks if (t.get("category") or "Ausrüstung") == sel_category]

    with st.expander("➕ Neues Item hinzufügen"):
        job = st.text_input("Was wird benötigt?", placeholder="z.B. Gaskocher, Zelt, Nudeln...", key=f"new_job_input_{trip_name}")
        row1, row2 = st.columns([0.62, 0.38])
        with row1:
            who = st.multiselect("Wer bringt es mit?", crew, key=f"new_who_input_{trip_name}")
        with row2:
            category = st.selectbox("Kategorie", CATEGORIES, key=f"new_category_input_{trip_name}")
        for_all = st.checkbox("Für alle", key=f"new_for_all_{trip_name}", help="Kennzeichnet das Item als allgemein relevant für alle Teilnehmer.")

        if st.button("Hinzufügen", key=f"btn_add_task_{trip_name}"):
            if job.strip():
                now_iso = datetime.datetime.now().replace(microsecond=0).isoformat()
                tasks.append(
                    {
                        "id": new_id("task"),
                        "job": job.strip(),
                        "who": who,
                        "done": False,
                        "category": category,
                        "for_all": for_all,
                        "created_at": now_iso,
                        "created_by": user,
                        "updated_at": now_iso,
                        "updated_by": user,
                    }
                )
                save_db(data)
                st.success(f"'{job}' hinzugefügt!")
                st.rerun()
            else:
                st.warning("Bitte gib an, was mitgebracht werden soll.")

    st.divider()

    if not display_tasks:
        st.info("Keine passenden Items vorhanden.")
    else:
        for i, t in enumerate(display_tasks):
            t_id = t.get("id", f"task_{i}")
            c1, c2, c3 = st.columns([0.08, 0.77, 0.15])

            is_done = t.get("done", False)
            changed = c1.checkbox("", value=is_done, key=f"check_{trip_name}_{t_id}")
            if changed != is_done:
                t["done"] = changed
                t["updated_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
                t["updated_by"] = user
                save_db(data)
                st.rerun()

            who_txt = ", ".join(t.get("who", [])) if t.get("who") else "Offen"
            category = t.get("category") or "Ausrüstung"
            badges = _badge(category, "rgba(124,156,255,.20)")
            if t.get("for_all"):
                badges += _badge("Für alle", "rgba(57, 181, 74, .18)")
            if t.get("who"):
                badges += _badge(who_txt, "rgba(255,255,255,.08)", "#dfe8ff")
            else:
                badges += _badge("Offen", "rgba(255,255,255,.06)", "#d0daef")

            label = f"~~{html.escape(t.get('job', ''))}~~" if t.get("done") else f"**{html.escape(t.get('job', ''))}**"
            c2.markdown(f"{label}<br>{badges}", unsafe_allow_html=True)

            if c3.button("🗑️", key=f"del_{trip_name}_{t_id}"):
                trip["tasks"] = [x for x in tasks if x.get("id") != t_id]
                save_db(data)
                st.rerun()
