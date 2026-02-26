import json
import os
import uuid
import datetime
from config import DB_FILE, BACKUP_FOLDER, MAX_BACKUPS

# -----------------------------------------
# EINDEUTIGE IDs
# -----------------------------------------
def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

# -----------------------------------------
# AUDIT-LOG
# -----------------------------------------
def log_event(data, trip, user, event):
    if "log" not in data["trips"][trip]:
        data["trips"][trip]["log"] = []

    data["trips"][trip]["log"].append({
        "id": new_id("log"),
        "user": user,
        "event": event,
        "time": datetime.datetime.now().isoformat()
    })

# -----------------------------------------
# Backups erstellen
# -----------------------------------------
def create_backup():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_FOLDER, f"backup_{ts}.json")
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as src:
            with open(backup_file, "w") as dst:
                dst.write(src.read())

    # alte Backups entfernen
    backups = sorted(os.listdir(BACKUP_FOLDER))
    if len(backups) > MAX_BACKUPS:
        for f in backups[:-MAX_BACKUPS]:
            os.remove(os.path.join(BACKUP_FOLDER, f))

# -----------------------------------------
# Datenbank laden
# -----------------------------------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {"trips": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"trips": {}}

# -----------------------------------------
# Datenbank speichern
# -----------------------------------------
def save_db(data):
    create_backup()
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
