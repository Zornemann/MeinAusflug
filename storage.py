import json
import os
import uuid
import datetime
import shutil
from config import DB_FILE, BACKUP_FOLDER, MAX_BACKUPS

# -----------------------------------------
# EINDEUTIGE IDs (z.B. für Chat-Nachrichten oder Kosten-Einträge)
# -----------------------------------------
def new_id(prefix):
    """Erzeugt eine kurze, eindeutige ID mit Zeitstempel-Anteil."""
    return f"{prefix}_{datetime.datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}"

# -----------------------------------------
# AUDIT-LOG (Wer hat was wann gemacht?)
# -----------------------------------------
def log_event(data, trip_name, user, event):
    """Protokolliert Änderungen in der Reise-Datenbank."""
    if trip_name not in data["trips"]:
        return
    
    if "log" not in data["trips"][trip_name]:
        data["trips"][trip_name]["log"] = []

    data["trips"][trip_name]["log"].append({
        "id": new_id("log"),
        "user": user,
        "event": event,
        "time": datetime.datetime.now().isoformat()
    })

# -----------------------------------------
# BACKUPS ERSTELLEN (Sicherungskopie vor dem Speichern)
# -----------------------------------------
def create_backup():
    """Erstellt eine Kopie der aktuellen Datenbank im Backup-Ordner."""
    if not os.path.exists(DB_FILE):
        return

    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    # Zeitstempel für Dateinamen erzeugen
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_FOLDER, f"backup_{ts}.json")
    
    # Sicherungskopie erstellen
    try:
        shutil.copy2(DB_FILE, backup_file)
    except Exception as e:
        print(f"Backup-Fehler: {e}")

    # Alte Backups entfernen (Rotation)
    try:
        # Liste alle Dateien im Backup-Ordner auf und sortiere sie
        backups = sorted([os.path.join(BACKUP_FOLDER, f) for f in os.listdir(BACKUP_FOLDER)], key=os.path.getmtime)
        
        # Wenn mehr Backups vorhanden sind als erlaubt, lösche die ältesten
        if len(backups) > MAX_BACKUPS:
            for f in backups[:-MAX_BACKUPS]:
                os.remove(f)
    except Exception as e:
        print(f"Fehler bei Backup-Rotation: {e}")

# -----------------------------------------
# DATENBANK LADEN
# -----------------------------------------
def load_db():
    """Lädt die JSON-Datenbank. Erstellt eine leere Struktur, falls Datei fehlt."""
    if not os.path.exists(DB_FILE):
        return {"trips": {}}
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        # Falls die Datei korrupt ist, geben wir eine leere Struktur zurück
        return {"trips": {}}

# -----------------------------------------
# DATENBANK SPEICHERN
# -----------------------------------------
def save_db(data):
    """Speichert den aktuellen Stand und erstellt vorher ein Backup."""
    # Erst Backup vom alten Stand machen
    create_backup()
    
    # Dann neuen Stand schreiben
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Speicherfehler: {e}")