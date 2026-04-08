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
except Exception:  # pragma: no cover
    canvas = None
    A4 = None
    mm = None
    colors = None
    stringWidth = None


CATEGORY_OPTIONS = ["Ausrüstung", "Verpflegung", "Sonstiges"]


def _task_text(task: dict) -> str:
    return (
        task.get("text")
        or task.get("item")
        or task.get("title")
        or task.get("task")
        or "Unbenannter Eintrag"
    )


def _task_assignees(task: dict) -> list[str]:
    assignees = task.get("assignees")
    if isinstance(assignees, list):
        return [str(x) for x in assignees if str(x).strip()]
    if isinstance(assignees, str) and assignees.strip():
        return [assignees.strip()]

    for key in ("owners", "who", "assigned_to"):
        value = task.get(key)
        if isinstance(value, list):
            return [str(x) for x in value if str(x).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
    return []


def _task_done(task: dict) -> bool:
    return bool(task.get("done") or task.get("checked") or task.get("completed"))


def _task_for_all(task: dict) -> bool:
    return bool(task.get("for_all") or task.get("forall") or task.get("all"))


def _task_category(task: dict) -> str:
    category = str(task.get("category") or "").strip()
    return category if category in CATEGORY_OPTIONS else "Sonstiges"


def _ensure_task_shape(trip: dict, data: dict) -> None:
    changed = False
    tasks = trip.setdefault("tasks", [])

    for task in tasks:
        if not task.get("id"):
            task["id"] = new_id()
            changed = True

        normalized_text = _task_text(task)
        if task.get("text") != normalized_text:
            task["text"] = normalized_text
            changed = True

        normalized_assignees = _task_assignees(task)
        if task.get("assignees") != normalized_assignees:
            task["assignees"] = normalized_assignees
            changed = True

        normalized_category = _task_category(task)
        if task.get("category") != normalized_category:
            task["category"] = normalized_category
            changed = True

        normalized_for_all = _task_for_all(task)
        if task.get("for_all") != normalized_for_all:
            task["for_all"] = normalized_for_all
            changed = True

        normalized_done = _task_done(task)
        if task.get("done") != normalized_done:
            task["done"] = normalized_done
            changed = True

        if "created_at" not in task:
            task["created_at"] = datetime.datetime.now().isoformat(timespec="minutes")
            changed = True

    if changed:
        save_db(data)


def _matches_person_filter(task: dict, selected_person: str) -> bool:
    if selected_person == "Alle":
        return True
    if _task_for_all(task):
        return True
    return selected_person in _task_assignees(task)


def _matches_category_filter(task: dict, selected_category: str) -> bool:
    if selected_category == "Alle":
        return True
    return _task_category(task) == selected_category


def _build_filtered_tasks(tasks: list[dict], selected_person: str, selected_category: str) -> list[dict]:
    return [
        task
        for task in tasks
        if _matches_person_filter(task, selected_person) and _matches_category_filter(task, selected_category)
    ]


def _wrap_text(c: canvas.Canvas, text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
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


def _generate_checklist_pdf(
    trip_name: str,
    selected_person: str,
    selected_category: str,
    tasks: list[dict],
) -> bytes:
    if canvas is None:
        raise RuntimeError("ReportLab ist nicht installiert.")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 18 * mm
    right = width - 18 * mm
    top = height - 18 * mm
    y = top

    def new_page() -> None:
        nonlocal y
        c.showPage()
        y = top

    def draw_header() -> None:
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

    for index, task in enumerate(tasks, start=1):
        text = _task_text(task)
        category = _task_category(task)
        assignees = "Für alle" if _task_for_all(task) else ", ".join(_task_assignees(task)) or "Nicht zugewiesen"
        checked = _task_done(task)

        content_width = (right - left) - 12 * mm
        text_lines = _wrap_text(c, text, "Helvetica-Bold", 11, content_width)
        meta_lines = _wrap_text(c, f"Kategorie: {category} | Zuständig: {assignees}", "Helvetica", 9, content_width)
        line_height = 5 * mm
        block_height = max(12 * mm, (len(text_lines) + len(meta_lines)) * line_height + 5 * mm)

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
    trips = data.setdefault("trips", {})
    trip = trips.setdefault(trip_key, {})
    tasks = trip.setdefault("tasks", [])
    participants = trip.setdefault("participants", {})
    role = participants.get(user, {}).get("role", "member")
    participant_names = sorted(participants.keys())

    _ensure_task_shape(trip, data)

    st.subheader("🧭 Ausrüstung & Verpflegung")

    filter_col1, filter_col2 = st.columns([3, 2])
    with filter_col1:
        selected_person = st.selectbox(
            "🔎 Zeige Items von:",
            ["Alle"] + participant_names,
            key=f"checklist_person_filter_{trip_key}",
        )
    with filter_col2:
        selected_category = st.selectbox(
            "Kategoriefilter:",
            ["Alle"] + CATEGORY_OPTIONS,
            key=f"checklist_category_filter_{trip_key}",
        )

    filtered_tasks = _build_filtered_tasks(tasks, selected_person, selected_category)

    export_col1, export_col2 = st.columns([3, 1])
    with export_col2:
        if canvas is None:
            st.info("PDF-Export benötigt reportlab.")
        else:
            pdf_bytes = _generate_checklist_pdf(
                trip_name=trip.get("name", trip_key),
                selected_person=selected_person,
                selected_category=selected_category,
                tasks=filtered_tasks,
            )
            st.download_button(
                "PDF exportieren",
                data=pdf_bytes,
                file_name=f"checkliste_{trip.get('name', trip_key).replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_checklist_pdf_{trip_key}",
            )

    with st.expander("➕ Neues Element hinzufügen", expanded=False):
        form_col1, form_col2 = st.columns([3, 2])
        with form_col1:
            item_text = st.text_input("Was wird benötigt?", key=f"checklist_text_{trip_key}", placeholder="z. B. Gaskocher, Zelt, Würstchen ...")
            assignees = st.multiselect(
                "Wer bringt es mit?",
                participant_names,
                key=f"checklist_assignees_{trip_key}",
                placeholder="Optionen auswählen",
            )
        with form_col2:
            category = st.selectbox("Kategorie", CATEGORY_OPTIONS, key=f"checklist_category_{trip_key}")
            for_all = st.checkbox("Für alle", key=f"checklist_for_all_{trip_key}")

        if st.button("Hinzufügen", key=f"checklist_add_button_{trip_key}", use_container_width=False):
            if item_text.strip():
                trip.setdefault("tasks", []).append(
                    {
                        "id": new_id(),
                        "text": item_text.strip(),
                        "assignees": assignees,
                        "category": category,
                        "for_all": for_all,
                        "done": False,
                        "created_by": user,
                        "created_at": datetime.datetime.now().isoformat(timespec="minutes"),
                    }
                )
                save_db(data)
                st.rerun()
            else:
                st.warning("Bitte zuerst einen Eintrag eingeben.")

    if not filtered_tasks:
        st.info("Keine Checklisten-Einträge für die aktuellen Filter vorhanden.")
        return

    for task in filtered_tasks:
        task_id = task.get("id")
        row1, row2 = st.columns([14, 1])

        with row1:
            badges = [f"**{_task_category(task)}**"]
            badges.append("**Für alle**" if _task_for_all(task) else ", ".join(_task_assignees(task)) or "Nicht zugewiesen")
            st.markdown(f"{' • '.join(badges)}")
            checked = st.checkbox(
                _task_text(task),
                value=_task_done(task),
                key=f"task_done_{trip_key}_{task_id}",
            )

            if checked != _task_done(task):
                for real_task in trip.get("tasks", []):
                    if real_task.get("id") == task_id:
                        real_task["done"] = checked
                        break
                save_db(data)
                st.rerun()

        with row2:
            can_delete = role == "admin" or task.get("created_by") == user or user in _task_assignees(task)
            if can_delete:
                if st.button("🗑️", key=f"delete_task_{trip_key}_{task_id}", use_container_width=True):
                    trip["tasks"] = [t for t in trip.get("tasks", []) if t.get("id") != task_id]
                    save_db(data)
                    st.rerun()
