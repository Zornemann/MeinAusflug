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
    mapping = {"Sonstige": "Sonstiges", "Sonstiges": "Sonstiges", "Ausrüstung": "Ausrüstung", "Verpflegung": "Verpflegung"}
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
        if pdata.get("status", "accepted") != "removed":
            names.append(uname)
    return sorted(list(dict.fromkeys(names)))


def _user_select_options(trip: dict, current_user: str) -> tuple[list[str], dict[str, str]]:
    usernames = _accepted_usernames(trip)
    if current_user and current_user not in usernames:
        usernames.append(current_user)
    labels = []
    label_to_username = {}
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


def _last_read_value(trip: dict, user: str, key: str) -> str:
    last_read = trip.setdefault("last_read", {})
    if not isinstance(last_read, dict):
        trip["last_read"] = {}
        last_read = trip["last_read"]
    return str(last_read.get(f"{user}:{key}") or last_read.get(user) or "2000-01-01T00:00:00")


def _unread_checklist_count(trip: dict, user: str) -> int:
    last_read = _last_read_value(trip, user, "checklist")
    count = 0
    for t in trip.get("tasks", []):
        ts = str(t.get("updated_at") or t.get("created_at") or "")
        actor = str(t.get("updated_by") or t.get("created_by") or "")
        if ts > last_read and actor != user:
            count += 1
    return count


def _mark_checklist_read(trip: dict, data: dict, user: str):
    trip.setdefault("last_read", {})[f"{user}:checklist"] = _now_iso()
    save_db(data)


def _touch_task(task: dict, actor: str):
    task["updated_at"] = _now_iso()
    task["updated_by"] = actor


def _migrate_and_fix_ids(trip: dict) -> bool:
    changed = False
    if "tasks" not in trip or not isinstance(trip["tasks"], list):
        trip["tasks"] = []
        return True
    for t in trip["tasks"]:
        if not isinstance(t, dict):
            continue
        if "done" not in t:
            t["done"] = False; changed = True
        if "qty" not in t or t.get("qty") in (None, "", 0):
            t["qty"] = 1; changed = True
        if not (t.get("item") or "").strip():
            if (t.get("text") or "").strip():
                t["item"] = t["text"].strip(); changed = True
            elif (t.get("job") or "").strip():
                t["item"] = t["job"].strip(); changed = True
            else:
                t["item"] = ""; changed = True
        old_cat = t.get("cat") or t.get("category") or ""
        norm_cat = _normalize_category(old_cat)
        if t.get("cat") != norm_cat:
            t["cat"] = norm_cat; changed = True
        if "created_by" not in t:
            t["created_by"] = ""; changed = True
        if "created_at" not in t:
            t["created_at"] = ""; changed = True
        if "updated_at" not in t:
            t["updated_at"] = t.get("created_at", ""); changed = True
        if "updated_by" not in t:
            t["updated_by"] = t.get("created_by", ""); changed = True
        if "brought_by" not in t or not str(t.get("brought_by") or "").strip():
            if (t.get("assigned") or "").strip():
                t["brought_by"] = t["assigned"].strip(); changed = True
            else:
                who = t.get("who")
                if isinstance(who, list) and who:
                    t["brought_by"] = str(who[0]).strip(); changed = True
                elif isinstance(who, str) and who.strip():
                    t["brought_by"] = who.strip(); changed = True
                else:
                    t["brought_by"] = ""; changed = True
    seen = set()
    for t in trip["tasks"]:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or "").strip()
        if not tid or tid in seen:
            t["id"] = new_id("task"); changed = True; tid = t["id"]
        seen.add(tid)
    return changed


def _sync_task_aliases(trip: dict):
    tasks = trip.get("tasks") if isinstance(trip.get("tasks"), list) else []
    checklist = trip.get("checklist") if isinstance(trip.get("checklist"), list) else []
    merged, seen = [], set()
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


def _apply_quick_change(trip: dict, data: dict, tid: str, label_to_user: dict[str, str], user: str):
    b_label = st.session_state.get(f"brought_{tid}", "")
    done_val = bool(st.session_state.get(f"done_{tid}", False))
    for t in trip.get("tasks", []):
        if str(t.get("id") or "").strip() == tid:
            current_b = (t.get("brought_by") or "").strip()
            new_b = (label_to_user.get(b_label, current_b) or "").strip()
            changed = False
            if new_b != current_b:
                t["brought_by"] = new_b; changed = True
            if done_val != bool(t.get("done", False)):
                t["done"] = done_val; changed = True
            if changed:
                _touch_task(t, user)
                _sync_task_aliases(trip)
                normalize_data(data)
                save_db(data)
                st.session_state.force_reload = True
            break


def render_checklist(data: dict, trip_name: str, user: str):
    trip = data["trips"][trip_name]
    if _migrate_and_fix_ids(trip):
        save_db(data)
        st.session_state.force_reload = True
        st.rerun()

    unread_count = _unread_checklist_count(trip, user)
    st.subheader("🧭 Ausrüstung / Checkliste")
    if unread_count > 0:
        st.info(f"🔔 {unread_count} neue oder geänderte Checklistenpunkte noch nicht gelesen.")
        if st.button("Als gelesen markieren", key=f"mark_check_read_{trip_name}"):
            _mark_checklist_read(trip, data, user)
            st.rerun()

    st.markdown("""
        <style>
        .cl-head {font-size: 16px; font-weight: 800; padding: 6px 0 10px 0;}
        .cl-text {font-size: 16px; padding: 8px 4px;}
        .cl-muted {color: #777;}
        div[data-testid="stHorizontalBlock"] {align-items: center;}
        </style>
        """, unsafe_allow_html=True)

    labels, label_to_user = _user_select_options(trip, user)

    with st.form(f"add_task_form_{trip_name}", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([0.44, 0.10, 0.18, 0.28])
        item = c1.text_input("Was bringe ich mit", placeholder="z.B. Zahnbürste", label_visibility="collapsed")
        qty = c2.number_input("Anzahl", min_value=1, step=1, value=1, label_visibility="collapsed")
        cat = c3.selectbox("Kategorie", CATEGORIES, index=1, label_visibility="collapsed")
        default_label = next((lb for lb, u in label_to_user.items() if u == user), labels[0] if labels else user)
        brought_label = c4.selectbox("Wer bringt es mit", options=labels if labels else [user], index=(labels.index(default_label) if labels and default_label in labels else 0), label_visibility="collapsed")
        add = st.form_submit_button("➕ Hinzufügen")
        if add and (item or "").strip():
            trip["tasks"].append({
                "id": new_id("task"),
                "item": item.strip(),
                "qty": int(qty),
                "cat": _normalize_category(cat),
                "brought_by": label_to_user.get(brought_label, user),
                "created_by": user,
                "created_at": _now_iso(),
                "updated_at": _now_iso(),
                "updated_by": user,
                "done": False,
            })
            _sync_task_aliases(trip)
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()

    tasks = trip.get("tasks", [])
    if not tasks:
        st.info("Noch keine Punkte in der Checkliste.")
        return

    f1, f2, f3, f4, f5, f6 = st.columns([0.28, 0.14, 0.18, 0.16, 0.12, 0.12])
    q = f1.text_input("Suche", placeholder="Suche...", label_visibility="collapsed", key=f"check_q_{trip_name}")
    status = f2.selectbox("Status", ["Alle", "Offen", "Erledigt"], index=0, label_visibility="collapsed", key=f"check_status_{trip_name}")
    cat_filter = f3.selectbox("Kategorie", ["Alle"] + CATEGORIES, index=0, label_visibility="collapsed", key=f"check_cat_{trip_name}")
    person_label = f4.selectbox("Wer bringt's", ["Alle"] + (labels if labels else []), index=0, label_visibility="collapsed", key=f"check_person_{trip_name}")
    sort = f5.selectbox("Sort", ["A–Z", "Neu"], index=0, label_visibility="collapsed", key=f"check_sort_{trip_name}")
    export_mode = f6.selectbox("Export", ["Alle", "Gefiltert"], index=1, label_visibility="collapsed", key=f"check_export_{trip_name}")

    def matches(t: dict) -> bool:
        txt = (t.get("item") or "").lower()
        if (q or "").strip() and q.lower() not in txt:
            return False
        if status == "Offen" and bool(t.get("done")):
            return False
        if status == "Erledigt" and not bool(t.get("done")):
            return False
        if cat_filter != "Alle" and _normalize_category(t.get("cat")) != cat_filter:
            return False
        if person_label != "Alle":
            wanted_user = label_to_user.get(person_label, "")
            if (t.get("brought_by") or "") != wanted_user:
                return False
        return True

    filtered = [t for t in tasks if matches(t)]
    filtered.sort(key=lambda t: (t.get("item") or "").lower()) if sort == "A–Z" else None
    if sort != "A–Z":
        filtered = list(reversed(filtered))

    export_rows = tasks if export_mode == "Alle" else filtered
    if export_rows:
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";")
        writer.writerow(["Kategorie", "Was bringe ich mit", "Anzahl", "Wer bringt es mit", "Eingetragen von", "Eingetragen am", "Erledigt"])
        for t in export_rows:
            writer.writerow([_normalize_category(t.get("cat")), t.get("item", ""), int(t.get("qty") or 1), _display_name(trip, t.get("brought_by", "")), _display_name(trip, t.get("created_by", "")), _format_created_at(t.get("created_at", "")), "ja" if bool(t.get("done")) else "nein"])
        st.download_button("⬇️ CSV herunterladen", data=buf.getvalue().encode("utf-8-sig"), file_name=f"{trip_name}_checkliste.csv", mime="text/csv")

    if not filtered:
        st.info("Keine Einträge für die gewählten Filter.")
        return

    h = st.columns([0.14, 0.30, 0.08, 0.18, 0.14, 0.06, 0.04, 0.03, 0.03])
    headers = ["Kategorie", "Was bringe ich mit", "Anzahl", "Wer bringt es mit", "Eingetragen von / am", "✓", "✏️", "🙋", "🗑️"]
    for col, title in zip(h, headers):
        col.markdown(f'<div class="cl-head">{title}</div>', unsafe_allow_html=True)

    for t in filtered:
        tid = str(t.get("id") or "").strip()
        if not tid:
            tid = new_id("task")
            t["id"] = tid
            _sync_task_aliases(trip)
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()
        suffix = tid
        if not (t.get("created_by") or "").strip():
            t["created_by"] = user
        if not (t.get("brought_by") or "").strip():
            t["brought_by"] = user
        t["cat"] = _normalize_category(t.get("cat"))
        editing_key = f"edit_{suffix}"
        is_editing = bool(st.session_state.get(editing_key, False))
        cols = st.columns([0.14, 0.30, 0.08, 0.18, 0.14, 0.06, 0.04, 0.03, 0.03])

        if not is_editing:
            cols[0].markdown(f'<div class="cl-text">{t.get("cat")}</div>', unsafe_allow_html=True)
            item_val = (t.get("item") or "").strip()
            empty_html = '<span class="cl-muted">(leer)</span>'
            cols[1].markdown(f'<div class="cl-text">{item_val or empty_html}</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div class="cl-text">{int(t.get("qty") or 1)}</div>', unsafe_allow_html=True)
        else:
            cols[0].selectbox("cat_edit", CATEGORIES, index=_safe_index(CATEGORIES, t.get("cat"), default=0), key=f"cat_edit_{suffix}", label_visibility="collapsed")
            cols[1].text_input("item_edit", value=t.get("item", ""), key=f"item_edit_{suffix}", label_visibility="collapsed")
            cols[2].number_input("qty_edit", min_value=1, step=1, value=int(t.get("qty") or 1), key=f"qty_edit_{suffix}", label_visibility="collapsed")

        current_b = (t.get("brought_by") or user).strip()
        current_label = next((lb for lb, u in label_to_user.items() if u == current_b), None)
        row_labels = (labels or []).copy()
        if current_label is None:
            current_label = current_b
            if current_label not in row_labels:
                row_labels.append(current_label)
        cols[3].selectbox("brought_by", options=row_labels if row_labels else [current_label], index=(row_labels.index(current_label) if current_label in row_labels else 0), key=f"brought_{suffix}", label_visibility="collapsed", on_change=_apply_quick_change, args=(trip, data, suffix, label_to_user, user))

        created_by_label = _display_name(trip, t.get("created_by", "")) or "-"
        created_at_label = _format_created_at(t.get("created_at", ""))
        cols[4].markdown(f'<div class="cl-text">{created_by_label}<br><span class="cl-muted">{created_at_label}</span></div>', unsafe_allow_html=True)
        cols[5].checkbox(f"Erledigt {suffix}", value=bool(t.get("done", False)), key=f"done_{suffix}", label_visibility="collapsed", on_change=_apply_quick_change, args=(trip, data, suffix, label_to_user, user))

        if not is_editing:
            if cols[6].button("✏️", key=f"editbtn_{suffix}"):
                st.session_state[editing_key] = True
                st.session_state[f"cat_edit_{suffix}"] = t.get("cat")
                st.session_state[f"item_edit_{suffix}"] = t.get("item", "")
                st.session_state[f"qty_edit_{suffix}"] = int(t.get("qty") or 1)
                st.rerun()
        else:
            sc1, sc2 = cols[6].columns(2)
            if sc1.button("💾", key=f"save_{suffix}"):
                t["cat"] = _normalize_category(st.session_state.get(f"cat_edit_{suffix}", "Sonstiges"))
                t["item"] = (st.session_state.get(f"item_edit_{suffix}", "") or "").strip()
                t["qty"] = int(st.session_state.get(f"qty_edit_{suffix}", 1) or 1)
                _touch_task(t, user)
                st.session_state[editing_key] = False
                _sync_task_aliases(trip)
                normalize_data(data)
                save_db(data)
                st.session_state.force_reload = True
                st.rerun()
            if sc2.button("✖️", key=f"cancel_{suffix}"):
                st.session_state[editing_key] = False
                st.rerun()

        if cols[7].button("Ich", key=f"claim_{suffix}"):
            t["brought_by"] = user
            _touch_task(t, user)
            _sync_task_aliases(trip)
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()

        if cols[8].button("🗑️", key=f"del_{suffix}"):
            trip["tasks"] = [x for x in trip["tasks"] if str(x.get("id") or "").strip() != tid]
            _sync_task_aliases(trip)
            normalize_data(data)
            save_db(data)
            st.session_state.force_reload = True
            st.rerun()
