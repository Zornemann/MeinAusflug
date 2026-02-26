import smtplib
import ssl
from email.message import EmailMessage
from config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, APP_URL

# -----------------------------------------------------
# E-Mail-Sende-Funktion (Grundfunktion)
# -----------------------------------------------------
def send_email(to, subject, body, attachments=None):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    # PDF- oder andere Dateien anhängen
    if attachments:
        for filename, filedata in attachments.items():
            msg.add_attachment(
                filedata,
                maintype="application",
                subtype="pdf",
                filename=filename
            )

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# -----------------------------------------------------
# E-Mail-Vorlagen
# -----------------------------------------------------
def send_invitation_email(name, email, password):
    subject = "Einladung zu MeinAusflug"
    body = f"""
Hallo {name},

du wurdest zu einer Reise hinzugefügt.

Hier sind deine Zugangsdaten:

Login-Seite: {APP_URL}
Benutzername: {name}
Passwort: {password}

Du kannst dein Passwort nach dem Einloggen jederzeit ändern.

Bis bald!
"""
    send_email(email, subject, body)

def send_password_changed_email(name, email):
    subject = "Dein Passwort wurde geändert"
    body = f"""
Hallo {name},

dein Passwort für MeinAusflug wurde erfolgreich geändert.

Falls du das nicht warst, kontaktiere bitte sofort den Administrator.
"""
    send_email(email, subject, body)

def send_chat_notification(name, email, msg_text):
    subject = "Neue Chat-Nachricht in deiner Reise"
    body = f"""
Hallo {name},

es gibt eine neue Chat-Nachricht:

"{msg_text}"

Zur App:
{APP_URL}
"""
    send_email(email, subject, body)

def send_checklist_update(name, email, item):
    subject = "Checkliste aktualisiert"
    body = f"""
Hallo {name},

ein Eintrag in deiner Checkliste wurde geändert:

"{item}"

Zur App:
{APP_URL}
"""
    send_email(email, subject, body)

def send_checklist_pdf(name, email, pdf_bytes, trip_name):
    subject = f"Deine Checkliste – {trip_name}"
    body = f"""
Hallo {name},

anbei findest du die finale Checkliste für deinen Ausflug.

Viel Spaß und gute Vorbereitung!

Beste Grüße
"""
    send_email(
        email,
        subject,
        body,
        attachments={f"Checkliste_{name}.pdf": pdf_bytes}
    )
