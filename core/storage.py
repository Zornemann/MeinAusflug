import os
import json
import shutil
import datetime
from typing import Optional, Tuple

from core.config import DB_FILE, BACKUP_FOLDER, MAX_BACKUPS

PSYCOPG_IMPORT_ERROR = None
try:
    import psycopg
except Exception as e:
    psycopg = None
    PSYCOPG_IMPORT_ERROR = str(e)


def _get_supabase_db_url() -> Optional[str]:
    url = os.getenv("SUPABASE_DB_URL") or os.getenv("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st  # type: ignore
        if "SUPABASE_DB_URL" in st.secrets:
            return st.secrets["SUPABASE_DB_URL"]
        if "connections" in st.secrets and "sql" in st.secrets["connections"]:
            c = st.secrets["connections"]["sql"]
            if isinstance(c, dict) and "url" in c:
                return c["url"]
    except Exception:
        pass
    return None


def _cloud_enabled() -> bool:
    return psycopg is not None and bool(_get_supabase_db_url())


def get_storage_status() -> dict:
    url = _get_supabase_db_url()
    if psycopg is None:
        return {"mode": "local", "reason": f"psycopg nicht importierbar: {PSYCOPG_IMPORT_ERROR or 'unbekannt'}", "has_db_url": bool(url)}
    if not url:
        return {"mode": "local", "reason": "SUPABASE_DB_URL/DATABASE_URL nicht gesetzt", "has_db_url": False}
    return {"mode": "cloud", "reason": "Supabase/Postgres aktiv", "has_db_url": True}


def _cloud_conn():
    url = _get_supabase_db_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL/DATABASE_URL fehlt.")
    if "sslmode=" not in url:
        joiner = "&" if "?" in url else "?"
        url = url + f"{joiner}sslmode=require"
    return psycopg.connect(url)


def create_backup() -> None:
    try:
        if not os.path.exists(DB_FILE):
            return
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_FOLDER, f"backup_{ts}.json")
        shutil.copy2(DB_FILE, backup_file)
        backups = sorted([os.path.join(BACKUP_FOLDER, f) for f in os.listdir(BACKUP_FOLDER) if f.lower().endswith('.json')], key=os.path.getmtime)
        if len(backups) > MAX_BACKUPS:
            for f in backups[:-MAX_BACKUPS]:
                try:
                    os.remove(f)
                except Exception:
                    pass
    except Exception as e:
        print(f"Backup-Fehler: {e}")


def _load_local() -> dict:
    if not os.path.exists(DB_FILE):
        return {"trips": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return normalize_data(data)
    except Exception:
        return {"trips": {}}


def _save_local(data: dict) -> None:
    create_backup()
    os.makedirs(os.path.dirname(DB_FILE) or ".", exist_ok=True)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(normalize_data(data), f, indent=4, ensure_ascii=False)


def _merge_unique_dict_items(primary: list, secondary: list, key: str) -> list:
    out = []
    seen = set()
    for src in (primary or [], secondary or []):
        if not isinstance(src, list):
            continue
        for item in src:
            if not isinstance(item, dict):
                continue
            item_id = item.get(key)
            marker = (item_id if item_id else json.dumps(item, sort_keys=True, ensure_ascii=False))
            if marker in seen:
                continue
            seen.add(marker)
            out.append(item)
    return out


def _trip_aliases(key: str, trip: dict) -> set:
    aliases = {str(key).strip()}
    if isinstance(trip, dict):
        for cand in [trip.get('name')]:
            if cand:
                aliases.add(str(cand).strip())
        details = trip.get('details') if isinstance(trip.get('details'), dict) else {}
        info = trip.get('info') if isinstance(trip.get('info'), dict) else {}
        for cand in [details.get('destination'), details.get('loc_name'), info.get('Name1'), info.get('Treffpunkt')]:
            if cand:
                aliases.add(str(cand).strip())
        raw_aliases = trip.get('aliases', [])
        if isinstance(raw_aliases, list):
            aliases.update(str(a).strip() for a in raw_aliases if a)
    return {a for a in aliases if a}


def _normalize_trip(key: str, trip: dict) -> dict:
    if not isinstance(trip, dict):
        trip = {}
    trip.setdefault('name', key)
    trip.setdefault('status', 'In Planung')
    if not isinstance(trip.get('participants'), dict):
        if isinstance(trip.get('participants'), list):
            trip['participants'] = {str(n): {'password': ''} for n in trip['participants']}
        else:
            trip['participants'] = {}
    if not isinstance(trip.get('typing'), dict):
        trip['typing'] = {}
    if not isinstance(trip.get('presence'), dict):
        trip['presence'] = {}
    if not isinstance(trip.get('details'), dict):
        trip['details'] = {}
    if not isinstance(trip.get('last_read'), dict):
        trip['last_read'] = {}
    d = trip['details']
    d.setdefault('destination', '')
    d.setdefault('loc_name', '')
    d.setdefault('homepage', d.get('loc_name', ''))
    d.setdefault('extra', '')
    d.setdefault('street', '')
    d.setdefault('plz', '')
    d.setdefault('city', '')
    today = str(datetime.date.today())
    d.setdefault('start_date', today)
    d.setdefault('end_date', today)
    d.setdefault('meet_date', today)
    d.setdefault('meet_time', '18:00')
    messages = trip.get('messages') if isinstance(trip.get('messages'), list) else []
    chat = trip.get('chat') if isinstance(trip.get('chat'), list) else []
    merged_messages = _merge_unique_dict_items(messages, chat, 'id')
    trip['messages'] = merged_messages
    trip['chat'] = merged_messages
    tasks = trip.get('tasks') if isinstance(trip.get('tasks'), list) else []
    checklist = trip.get('checklist') if isinstance(trip.get('checklist'), list) else []
    merged_tasks = _merge_unique_dict_items(tasks, checklist, 'id')
    trip['tasks'] = merged_tasks
    trip['checklist'] = merged_tasks
    if not isinstance(trip.get('expenses'), list):
        trip['expenses'] = []
    if not isinstance(trip.get('images'), list):
        trip['images'] = []
    if not isinstance(trip.get('categories'), list):
        trip['categories'] = ['Verpflegung', 'Ausstattung', 'Sonstiges']
    aliases = sorted(_trip_aliases(key, trip))
    trip['aliases'] = aliases
    trip.setdefault('trip_id', f"trip_{abs(hash('|'.join(aliases))) % 10_000_000}")
    return trip


def normalize_data(data: dict) -> dict:
    if not isinstance(data, dict):
        data = {}
    trips = data.get('trips')
    if not isinstance(trips, dict):
        trips = {}
    normalized = {}
    groups = []  # list of (aliases, merged_trip)
    for key, trip in trips.items():
        t = _normalize_trip(str(key), trip)
        aliases = _trip_aliases(str(key), t)
        match = None
        for g in groups:
            if aliases & g[0]:
                match = g
                break
        if match is None:
            groups.append([set(aliases), t])
        else:
            merged_aliases, base = match
            base['messages'] = _merge_unique_dict_items(base.get('messages', []), t.get('messages', []), 'id')
            base['chat'] = base['messages']
            base['tasks'] = _merge_unique_dict_items(base.get('tasks', []), t.get('tasks', []), 'id')
            base['checklist'] = base['tasks']
            for field in ('participants', 'typing', 'presence', 'last_read', 'custom_templates'):
                if isinstance(t.get(field), dict):
                    base.setdefault(field, {})
                    base[field].update(t[field])
            for field in ('expenses', 'images', 'categories'):
                if isinstance(t.get(field), list):
                    base.setdefault(field, [])
                    if field == 'categories':
                        base[field] = list(dict.fromkeys(base[field] + t[field]))
                    else:
                        base[field] = _merge_unique_dict_items(base[field], t[field], 'id') if field != 'images' else base[field] + [x for x in t[field] if x not in base[field]]
            # prefer filled details/name/info
            if isinstance(t.get('details'), dict):
                base.setdefault('details', {})
                for k2, v2 in t['details'].items():
                    if v2 and not base['details'].get(k2):
                        base['details'][k2] = v2
            if t.get('name') and (not base.get('name') or len(str(t.get('name'))) > len(str(base.get('name')))):
                base['name'] = t['name']
            if isinstance(t.get('info'), dict):
                base.setdefault('info', {})
                for k2, v2 in t['info'].items():
                    if v2 and not base['info'].get(k2):
                        base['info'][k2] = v2
            merged_aliases.update(aliases)
            base['aliases'] = sorted(merged_aliases)
    # materialize every alias key to same merged content copy
    for aliases, trip in groups:
        trip = _normalize_trip(trip.get('name') or next(iter(aliases)), trip)
        trip['aliases'] = sorted(aliases)
        keys = set(aliases)
        keys.add(trip.get('name') or '')
        details = trip.get('details', {})
        for cand in [details.get('destination'), details.get('loc_name')]:
            if cand:
                keys.add(str(cand).strip())
        info = trip.get('info') if isinstance(trip.get('info'), dict) else {}
        if info.get('Name1'):
            keys.add(str(info.get('Name1')).strip())
        for k in [k for k in keys if k]:
            normalized[k] = json.loads(json.dumps(trip, ensure_ascii=False))
    data['trips'] = normalized
    return data


def resolve_trip_key(data: dict, requested: str) -> str:
    trips = (data or {}).get('trips', {})
    if requested in trips:
        return requested
    requested_norm = (requested or '').strip().lower()
    for key, trip in trips.items():
        aliases = _trip_aliases(key, trip)
        if requested_norm in {a.lower() for a in aliases}:
            return key
    return requested


def load_db() -> dict:
    if _cloud_enabled():
        with _cloud_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('select data from app_state where id=1;')
                row = cur.fetchone()
                if not row:
                    cur.execute('insert into app_state (id, data) values (1, %s::jsonb) on conflict (id) do nothing;', (json.dumps({'trips': {}}, ensure_ascii=False),))
                    conn.commit()
                    return {'trips': {}}
                data = row[0]
                if isinstance(data, str):
                    data = json.loads(data)
                return normalize_data(data)
    return _load_local()


def save_db(data: dict) -> None:
    data = normalize_data(data)
    if _cloud_enabled():
        payload = json.dumps(data, ensure_ascii=False)
        with _cloud_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    insert into app_state (id, data, updated_at)
                    values (1, %s::jsonb, now())
                    on conflict (id) do update
                      set data = excluded.data,
                          updated_at = now();
                """, (payload,))
            conn.commit()
        return
    _save_local(data)


def new_id(prefix: str = 'id') -> str:
    import uuid
    ts = datetime.datetime.now().strftime('%H%M%S')
    return f"{prefix}_{ts}_{uuid.uuid4().hex[:6]}"
