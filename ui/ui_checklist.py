import csv
import datetime
import io

import streamlit as st

from core.storage import new_id, normalize_data, save_db

CATEGORIES = ["Verpflegung", "Ausrüstung", "Sonstiges"]


def _normalize_category(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return "Sonstiges"
    mapping = {
        "Sonstige": "Sonstiges",
        "Sonstiges": "Sonstiges",
        "Ausrüstung": "Ausrüstung",
        "Verpflegung": "Verpflegung",
    }
    return mapping.get(raw, raw if raw in CATEGORIES else "Sonstiges")


def _participants(trip: dict) -> dict:
    p = trip.get("participants", {})
    return p if isinstance(p, dict) else {}


def _display_name(trip: dict, username: str) -> str:
    username = (username or "").strip()
    if not username:
        return ""
    p = _participants(trip).get(username)
    if isinstance(p, dict):
        dn = (p.get("display_name") or "").strip()
        return dn if dn else username
    return username


def _accepted_usernames(trip: dict) -> list[str]:
    parts = _participants(trip)
    names = []
    for uname, pdata in parts.items():
        if not isinstance(pdata, dict):
            continue
        if pdata.get("status", "accepted") == "accepted":
            names.append(uname)
    return sorted(list(dict.fromkeys(names)))


def _user_select_options(trip: dict, current_user: str) -> tuple[list[str], dict[str, str]]:
    usernames = _accepted_usernames(trip)
    if current_user and current_user not in usernames:
        usernames.append(current_user)

    labels: list[str] = []
    label_to_username: dict[str, str] = {}
    seen = set()

    for u in sorted(usernames):
        dn = _display_name(trip, u) or u
        label = dn
        if label in seen:
            label = f"{dn} ({u})"
        seen.add(label)
        labels.append(label)
        label_to_username[label] = u

    return labels, label_to_username


def _safe_index(options: list[str], value: str, default: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return default


def _now_iso() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def _format_created_at(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return "-"
    try:
        dt = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return text


def _migrate_and_fix_ids(trip: dict) -> bool:
    changed = False
    if "tasks" not in trip or not isinstance(trip["tasks"], list):
        trip["tasks"] = []
        return True

    for t in trip["tasks"]:
        if not isinstance(t, dict):
            continue

        if "done" not in t:
            t["done"] = False
            changed = True
        if "qty" not in t or t.get("qty") in (None, "", 0):
            t["qty"] = 1
            changed = True
        if not (t.get("item") or "").strip():
            if (t.get("text") or "").strip():
                t["item"] = t["text"].strip()
            elif (t.get("job") or "").strip():
                t["item"] = t["job"].strip()
            else:
                t["item"] = ""
            changed = True

        old_cat = t.get("cat") or t.get("category") or ""
        norm_cat = _normalize_category(old_cat)
        if t.get("cat") != norm_cat:
            t["cat"] = norm_cat
            changed = True

        if "created_by" not in t:
            t["created_by"] = ""
            changed = True
        if "created_at" not in t:
            t["created_at"] = ""
            changed = True
        if "updated_at" not in t:
            t["updated_at"] = t.get("created_at", "")
            changed = True
        if "updated_by" not in t:
            t["updated_by"] = t.get("created_by", "")
            changed = True

        if "brought_by" not in t or not str(t.get("brought_by") or "").strip():
            if (t.get("assigned") or "").strip():
                t["brought_by"] = t["assigned"].strip()
            else:
                who = t.get("who")
                if isinstance(who, list) and who:
                    t["brought_by"] = str(who[0]).strip()
                elif isinstance(who, str) and who.strip():
                    t["brought_by"] = who.strip()
                else:
                    t["brought_by"] = ""
            changed = True

    seen = set()
    for t in trip["tasks"]:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid or tid in seen:
            t["id"] = new_id("task")
            changed = True
            tid = t["id"]
        seen.add(tid)

    return changed


def _apply_quick_change(trip: dict, data: dict, tid: str, label_to_user: dict[str, str], user: str):
    b_label = st.session_state.get(f"brought_{tid}", "")
    done_val = bool(st.session_state.get(f"done_{tid}", False))

    for t in trip.get("tasks", []):
        if str(t.get("id") or "").strip() == tid:
            current_b = (t.get("brought_by") or "").strip()
            new_b = (label_to_user.get(b_label, current_b) or "").strip()

            changed = False
            if new_b != current_b:
                t["brought_by"] = new_b
                changed = True
            if done_val != bool(t.get("done", False)):
                t["done"] = done_val
                changed = True

            if changed:
                t["updated_at"] = _now_iso()
                t["updated_by"] = user
                _sync_task_aliases(trip)
                normalize_data(data)
                save_db(data)
                st.session_state.force_reload = True
            break


def _sync_task_aliases(trip: dict):
    tasks = trip.get("tasks") if isinstance(trip.get("tasks"), list) else []
    checklist = trip.get("checklist") if isinstance(trip.get("checklist"), list) else []
    merged = []
    seen = set()
    for src in (tasks, checklist):
        for t in src:
            tid = t.get("id") if isinstance(t, dict) else None
            marker = tid or str(t)
            if marker in seen:
                continue
            seen.add(marker)
            merged.append(t)
    trip["tasks"] = merged
    trip["checklist"] = merged


def render_checklist(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]

    if _migrate_and_fix_ids(trip):
        save_db(data)
        st.session_state.force_reload = True
        st.rerun()

    st.subheader("🧭 Ausrüstung / Checkliste")
    st.markdown(
        """
        <style>
        .cl-head {font-size: 16px; font-weight: 800; padding: 6px 0 10px 0;}
        .cl-text {font-size: 16px; padding: 8px 4px;}
        .cl-muted {color: #777;}
        div[data-testid="stHorizontalBlock"] {align-items: center;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    labels, label_to_user = _user_select_options(trip, user)

    st.markdown("### Hinzufügen")
    with st.form(f"add_task_{trip_name}", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([4, 1.2, 1.6, 2.2])
        item = c1.text_input("Was fehlt?", key=f"new_item_{trip_name}")
        qty = c2.number_input("Menge", min_value=1, value=1, step=1, key=f"new_qty_{trip_name}")
        cat = c3.selectbox("Kategorie", CATEGORIES, key=f"new_cat_{trip_name}")
        owner_label = c4.selectbox("Mitgebracht von", labels, key=f"new_owner_{trip_name}") if labels else ""
        submitted = st.form_submit_button("Hinzufügen", use_container_width=True)
        if submitted and item.strip():
            owner = label_to_user.get(owner_label, user) if owner_label else user
            trip.setdefault("tasks", []).append(
                {
                    "id": new_id("task"),
                    "item": item.strip(),
                    "qty": int(qty),
                    "cat": _normalize_category(cat),
                    "brought_by": owner,
                    "done": False,
                    "created_by": user,
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                    "updated_by": user,
                }
            )
            _sync_task_aliases(trip)
            normalize_data(data)
            save_db(data)
            st.success("Checklistenpunkt hinzugefügt")
            st.rerun()

    st.markdown("### Liste")
    tasks = trip.get("tasks", [])
    if not tasks:
        st.info("Noch keine Checklistenpunkte vorhanden.")
    else:
        header = st.columns([0.08, 0.34, 0.1, 0.18, 0.18, 0.12])
        header[0].markdown("<div class='cl-head'>Erledigt</div>", unsafe_allow_html=True)
        header[1].markdown("<div class='cl-head'>Eintrag</div>", unsafe_allow_html=True)
        header[2].markdown("<div class='cl-head'>Menge</div>", unsafe_allow_html=True)
        header[3].markdown("<div class='cl-head'>Kategorie</div>", unsafe_allow_html=True)
        header[4].markdown("<div class='cl-head'>Mitgebracht von</div>", unsafe_allow_html=True)
        header[5].markdown("<div class='cl-head'>Aktion</div>", unsafe_allow_html=True)

        for task in tasks:
            if not isinstance(task, dict):
                continue
            tid = str(task.get("id") or "")
            owner = (task.get("brought_by") or "").strip()
            owner_label = _display_name(trip, owner) or owner or (labels[0] if labels else "")
            if owner_label not in labels and labels:
                owner_label = labels[0]
            row = st.columns([0.08, 0.34, 0.1, 0.18, 0.18, 0.12])
            with row[0]:
                st.checkbox(
                    "",
                    value=bool(task.get("done", False)),
                    key=f"done_{tid}",
                    on_change=_apply_quick_change,
                    args=(trip, data, tid, label_to_user, user),
                )
            with row[1]:
                st.markdown(f"<div class='cl-text'>{task.get('item', '')}</div>", unsafe_allow_html=True)
                st.caption(
                    f"angelegt von {_display_name(trip, task.get('created_by') or '') or task.get('created_by') or '-'} · {_format_created_at(task.get('created_at', ''))}"
                )
            with row[2]:
                st.markdown(f"<div class='cl-text'>{int(task.get('qty', 1) or 1)}</div>", unsafe_allow_html=True)
            with row[3]:
                st.markdown(f"<div class='cl-text'>{task.get('cat', 'Sonstiges')}</div>", unsafe_allow_html=True)
            with row[4]:
                st.selectbox(
                    "",
                    labels,
                    index=_safe_index(labels, owner_label, 0) if labels else None,
                    key=f"brought_{tid}",
                    label_visibility="collapsed",
                    on_change=_apply_quick_change,
                    args=(trip, data, tid, label_to_user, user),
                )
            with row[5]:
                if st.button("🗑️", key=f"del_{tid}"):
                    trip["tasks"] = [t for t in trip.get("tasks", []) if str(t.get("id") or "") != tid]
                    _sync_task_aliases(trip)
                    normalize_data(data)
                    save_db(data)
                    st.rerun()

    st.divider()
    csv_rows = []
    for task in trip.get("tasks", []):
        if not isinstance(task, dict):
            continue
        csv_rows.append(
            {
                "item": task.get("item", ""),
                "qty": task.get("qty", 1),
                "cat": task.get("cat", "Sonstiges"),
                "brought_by": _display_name(trip, task.get("brought_by", "")),
                "done": "ja" if task.get("done", False) else "nein",
            }
        )
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["item", "qty", "cat", "brought_by", "done"])
    writer.writeheader()
    writer.writerows(csv_rows)
    st.download_button(
        "CSV exportieren",
        data=csv_buffer.getvalue().encode("utf-8"),
        file_name=f"checkliste_{trip_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )
