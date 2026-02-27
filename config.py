import os

# ---------------------------
# ALLGEMEINE APP-EINSTELLUNGEN
# ---------------------------
APP_NAME = "MeinAusflug PRO"
APP_URL = "https://mein-ausflug.streamlit.app"
APP_ICON_URL = "https://github.com/Zornemann/MeinAusflug/blob/main/MeinAusflug.jpg?raw=true"

# ---------------------------
# ADMIN & SICHERHEIT
# ---------------------------
# TIPP: Im Live-Betrieb Admin123 durch ein sichereres Passwort ersetzen!
ADMIN_PASSWORD = "Admin123" 

# ---------------------------
# EMAIL-KONFIGURATION (GMAIL)
# ---------------------------
# WICHTIG: Gmail benötigt ein "App-Passwort", nicht dein normales Google-Passwort!
EMAIL_SENDER = "denniszorn81@gmail.com"
EMAIL_PASSWORD = "Woodstock81!" 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ---------------------------
# DATEIEN & BACKUP-SYSTEM
# ---------------------------
DB_FILE = "reisen_daten.json"
BACKUP_FOLDER = "backups"
MAX_BACKUPS = 10  # Älteste Backups werden bei Überschreitung gelöscht

# Sicherstellen, dass der Backup-Ordner existiert
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

# ---------------------------
# DESIGN / UI KONSTANTEN
# ---------------------------
PRIMARY_COLOR = "#4285F4"  # Das Google-Blau für Buttons etc.