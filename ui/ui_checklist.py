from __future__ import annotations

import datetime
from io import BytesIO

import streamlit as st

from core.storage import new_id, save_db

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None
    A4 = None
    mm = None
    colors = None
    stringWidth = None

CATEGORY_OPTIONS = ["Ausrüstung", "Verpflegung", "Sonstiges"]
PRIORITY_OPTIONS = ["Hoch", "Mittel", "Niedrig"]

TEMPLATES = {
    "Camping": [
        ("Zelt", "Ausrüstung"),
        ("Schlafsack", "Ausrüstung"),
        ("Gaskocher", "Ausrüstung"),
        ("Würstchen", "Verpflegung"),
    ],
    "Grillen": [
        ("Grillzange", "Ausrüstung"),
        ("Kohle", "Ausrüstung"),
        ("Getränke", "Verpflegung"),
        ("Salate", "Verpflegung"),
    ],
}


def _task_text(task: dict) -> str:
    return str(task.get("text") or "Unbenannter Eintrag")


def _task_assignees(task: dict) -> list[str]:
    assignees = task.get("assignees")
    if isinstance(assignees, list):
        return [str(x) for x in assignees if str(x).strip()]
    return []


def _task_done(task: dict) -> bool:
    return bool(task.get("done"))


def _task_for_all(task: dict) -> bool:
    return bool(task.get("for_all"))


def _task_category(task: dict) -> str:
    category = str(task.get("category") or "").strip()
    return category if category in CATEGORY_OPTIONS else "Sonstiges"


def _task_priority(task: dict) -> str:
    priority = str(task.get("priority") or "").strip()
    return priority if priority in PRIORITY_OPTIONS else "Mittel"


def _matches_person_filter(task: dict, selected_person: str) -> bool:
    if selected_person == "Alle":
        return True
    if _task_for_all(task):
        return True
    return selected_person in _task_assignees(task)


def _matches_category_filter(task: dict, selected_category: str) -> bool:
    return selected_category == "Alle" or _task_category(task) == selected_category


def _matches_status_filter(task: dict, selected_status: str) -> bool:
    if selected_status == "Alle":
        return True
    if selected_status == "Offen":
        return not _task_done(task)
    return _task_done(task)


def _sort_tasks(tasks: list[dict], sort_mode: str) -> list[dict]:
    priority_rank = {"Hoch": 0, "Mittel": 1, "Niedrig": 2}
    if sort_mode == "Priorität":
        return sorted(tasks, key=lambda t: (priority_rank.get(_task_priority(t), 1), _task_done(t), t.get("due_date") or "9999-12-31"))
    if sort_mode == "Fälligkeitsdatum":
        return sorted(tasks, key=lambda t: (t.get("due_date") or "9999-12-31", _task_done(t), priority_rank.get(_task_priority(t), 1)))
    if sort_mode == "Status":
        return sorted(tasks, key=lambda t: (_task_done(t), priority_rank.get(_task_priority(t), 1), t.get("due_date") or "9999-12-31"))
    return tasks


def _build_filtered_tasks(tasks: list[dict], selected_person: str, selected_category: str, selected_status: str, sort_mode: str) -> list[dict]:
    filtered = [
        task for task in tasks
        if _matches_person_filter(task, selected_person)
        and _matches_category_filter(task, selected_category)
        and _matches_status_filter(task, selected_status)
    ]
    return _sort_tasks(filtered, sort_mode)


def _wrap_text(c: canvas.Canvas, text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _generate_checklist_pdf(trip_name: str, selected_person: str, selected_category: str, tasks: list[dict]) -> bytes:
    if canvas is None:
        raise RuntimeError("ReportLab ist nicht installiert.")
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left = 18 * mm
    right = width - 18 * mm
    top = height - 18 * mm
    y = top

    def new_page():
        nonlocal y
        c.showPage()
        y = top

    def draw_header():
        nonlocal y
        c.setTitle(f"Checkliste - {trip_name}")
        c.setFont("Helvetica-Bold", 18)
        c.drawString(left, y, f"Checkliste - {trip_name}")
        y -= 9 * mm
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.HexColor("#444444"))
        c.drawString(left, y, f"Filter Person: {selected_person}")
        y -= 5 * mm
        c.drawString(left, y, f"Filter Kategorie: {selected_category}")
        y -= 5 * mm
        c.drawString(left, y, f"Erstellt am: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        y -= 8 * mm
        c.setFillColor(colors.black)

    draw_header()

    if not tasks:
        c.setFont("Helvetica", 12)
        c.drawString(left, y, "Keine Einträge für die aktuellen Filter vorhanden.")
        c.save()
        return buffer.getvalue()

    for task in tasks:
        text = _task_text(task)
        category = _task_category(task)
        priority = _task_priority(task)
        due = task.get("due_date") or "–"
        assignees = "Für alle" if _task_for_all(task) else ", ".join(_task_assignees(task)) or "Nicht zugewiesen"
        checked = _task_done(task)

        content_width = (right - left) - 12 * mm
        text_lines = _wrap_text(c, text, "Helvetica-Bold", 11, content_width)
        meta_lines = _wrap_text(c, f"Kategorie: {category} | Priorität: {priority} | Fällig: {due} | Zuständig: {assignees}", "Helvetica", 9, content_width)
        line_height = 5 * mm
        block_height = max(14 * mm, (len(text_lines) + len(meta_lines)) * line_height + 5 * mm)

        if y - block_height < 18 * mm:
            new_page()
            draw_header()

        box_size = 5 * mm
        c.rect(left, y - box_size, box_size, box_size, stroke=1, fill=0)
        if checked:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(left + 1.1 * mm, y - 4.3 * mm, "X")

        text_x = left + 9 * mm
        text_y = y
        c.setFont("Helvetica-Bold", 11)
        for line in text_lines:
            c.drawString(text_x, text_y, line)
            text_y -= line_height

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#555555"))
        for line in meta_lines:
            c.drawString(text_x, text_y, line)
            text_y -= line_height
        c.setFillColor(colors.black)

        c.line(left, y - block_height + 2 * mm, right, y - block_height + 2 * mm)
        y -= block_height

    c.save()
    return buffer.getvalue()


def render_checklist(data: dict, trip_key: str, user: str) -> None:
    trip = data["trips"][trip_key]
    tasks = trip.setdefault("tasks", [])
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")
    participant_names = sorted(list(participants.keys()))

    st.subheader("🧭 Ausrüstung & Verpflegung")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2.4, 1.5, 1.3, 1.4])
    with filter_col1:
        selected_person = st.selectbox("🔎 Zeige Items von:", ["Alle"] + participant_names, key=f"checklist_person_filter_{trip_key}")
    with filter_col2:
        selected_category = st.selectbox("Kategoriefilter:", ["Alle"] + CATEGORY_OPTIONS, key=f"checklist_category_filter_{trip_key}")
    with filter_col3:
        selected_status = st.selectbox("Status", ["Alle", "Offen", "Erledigt"], key=f"checklist_status_filter_{trip_key}")
    with filter_col4:
        sort_mode = st.selectbox("Sortierung", ["Standard", "Priorität", "Fälligkeitsdatum", "Status"], key=f"checklist_sort_{trip_key}")

    filtered_tasks = _build_filtered_tasks(tasks, selected_person, selected_category, selected_status, sort_mode)

    export_col1, export_col2 = st.columns([3, 1])
    with export_col1:
        with st.popover("Vorlage hinzufügen", use_container_width=False):
            st.caption("Schnelle Startvorlagen")
            for template_name, items in TEMPLATES.items():
                if st.button(template_name, key=f"tpl_{trip_key}_{template_name}", use_container_width=True):
                    now = datetime.datetime.now().isoformat(timespec="minutes")
                    for item_text, category in items:
                        trip["tasks"].append(
                            {
                                "id": new_id("task"),
                                "text": item_text,
                                "assignees": [],
                                "category": category,
                                "for_all": True,
                                "done": False,
                                "priority": "Mittel",
                                "due_date": "",
                                "created_by": user,
                                "created_at": now,
                                "updated_by": user,
                                "updated_at": now,
                            }
                        )
                    save_db(data)
                    st.rerun()
    with export_col2:
        if canvas is None:
            st.info("PDF-Export benötigt reportlab.")
        else:
            pdf_bytes = _generate_checklist_pdf(trip.get("name", trip_key), selected_person, selected_category, filtered_tasks)
            st.download_button(
                "PDF exportieren",
                data=pdf_bytes,
                file_name=f"checkliste_{trip.get('name', trip_key).replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_checklist_pdf_{trip_key}",
            )

    can_edit = role in {"admin", "editor", "member"}
    if can_edit:
        with st.expander("➕ Neues Element hinzufügen", expanded=False):
            form_col1, form_col2, form_col3 = st.columns([3, 1.3, 1.4])
            with form_col1:
                item_text = st.text_input("Was wird benötigt?", key=f"checklist_text_{trip_key}", placeholder="z. B. Gaskocher, Zelt, Würstchen ...")
                assignees = st.multiselect("Wer bringt es mit?", participant_names, key=f"checklist_assignees_{trip_key}", placeholder="Optionen auswählen")
            with form_col2:
                category = st.selectbox("Kategorie", CATEGORY_OPTIONS, key=f"checklist_category_{trip_key}")
                priority = st.selectbox("Priorität", PRIORITY_OPTIONS, key=f"checklist_priority_{trip_key}")
            with form_col3:
                due_date = st.date_input("Fällig bis", value=None, key=f"checklist_due_{trip_key}")
                for_all = st.checkbox("Für alle", key=f"checklist_for_all_{trip_key}")

            if st.button("Hinzufügen", key=f"checklist_add_button_{trip_key}", use_container_width=False):
                if item_text.strip():
                    now = datetime.datetime.now().isoformat(timespec="minutes")
                    trip["tasks"].append(
                        {
                            "id": new_id("task"),
                            "text": item_text.strip(),
                            "assignees": assignees,
                            "category": category,
                            "for_all": for_all,
                            "done": False,
                            "priority": priority,
                            "due_date": str(due_date) if due_date else "",
                            "created_by": user,
                            "created_at": now,
                            "updated_by": user,
                            "updated_at": now,
                        }
                    )
                    save_db(data)
                    st.rerun()
                else:
                    st.warning("Bitte zuerst einen Eintrag eingeben.")

    if not filtered_tasks:
        st.info("Keine Checklisten-Einträge für die aktuellen Filter vorhanden.")
        return

    prio_class = {"Hoch": "me-pill-prio-hoch", "Mittel": "me-pill-prio-mittel", "Niedrig": "me-pill-prio-niedrig"}

    for task in filtered_tasks:
        task_id = task.get("id")
        row = st.columns([12, 3, 1.2])
        with row[0]:
            assignee_text = "Für alle" if task.get("for_all") else ", ".join(task.get("assignees", [])) or "Nicht zugewiesen"
            due_text = task.get("due_date") or "Kein Datum"
            badges = (
                f"<span class='me-pill me-pill-muted'>{_task_category(task)}</span> "
                f"<span class='me-pill {prio_class.get(_task_priority(task), 'me-pill-prio-mittel')}'>{_task_priority(task)}</span> "
                f"<span class='me-pill me-pill-muted'>{assignee_text}</span> "
                f"<span class='me-pill me-pill-muted'>Fällig: {due_text}</span>"
            )
            st.markdown(badges, unsafe_allow_html=True)
            checked = st.checkbox(_task_text(task), value=_task_done(task), key=f"task_done_{trip_key}_{task_id}")
            if checked != _task_done(task):
                for real_task in trip.get("tasks", []):
                    if real_task.get("id") == task_id:
                        real_task["done"] = checked
                        real_task["updated_by"] = user
                        real_task["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
                        break
                save_db(data)
                st.rerun()

        with row[1]:
            if role in {"admin", "editor"} or task.get("created_by") == user:
                with st.popover("Bearbeiten", use_container_width=True):
                    edit_text = st.text_input("Text", value=_task_text(task), key=f"task_edit_text_{trip_key}_{task_id}")
                    edit_priority = st.selectbox("Priorität", PRIORITY_OPTIONS, index=PRIORITY_OPTIONS.index(_task_priority(task)), key=f"task_edit_priority_{trip_key}_{task_id}")
                    edit_due = st.text_input("Fälligkeitsdatum", value=task.get("due_date") or "", key=f"task_edit_due_{trip_key}_{task_id}", placeholder="YYYY-MM-DD")
                    if st.button("Speichern", key=f"task_edit_save_{trip_key}_{task_id}", use_container_width=True):
                        for real_task in trip.get("tasks", []):
                            if real_task.get("id") == task_id:
                                real_task["text"] = edit_text.strip() or _task_text(task)
                                real_task["priority"] = edit_priority
                                real_task["due_date"] = edit_due.strip()
                                real_task["updated_by"] = user
                                real_task["updated_at"] = datetime.datetime.now().isoformat(timespec="minutes")
                                break
                        save_db(data)
                        st.rerun()

        with row[2]:
            can_delete = role in {"admin", "editor"} or task.get("created_by") == user or user in task.get("assignees", [])
            if can_delete and st.button("🗑️", key=f"delete_task_{trip_key}_{task_id}", use_container_width=True):
                trip["tasks"] = [t for t in trip.get("tasks", []) if t.get("id") != task_id]
                save_db(data)
                st.rerun()
