import os

APP_NAME = "MeinAusflug PRO"
APP_URL = "https://mein-ausflug.streamlit.app"
APP_ICON_URL = "https://github.com/Zornemann/MeinAusflug/blob/main/MeinAusflug.jpg?raw=true"

# Secrets immer aus ENV/Secrets, nie hardcoden:
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")  # Gmail: App-Passwort!
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

DB_FILE = os.getenv("DB_FILE", "data/reisen_daten.json")
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER", "backups")
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "20"))

PRIMARY_COLOR = "#4285F4"
