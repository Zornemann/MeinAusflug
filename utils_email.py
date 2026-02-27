import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, APP_NAME

def send_system_email(recipient_email, subject, body_text):
    """Versendet eine echte E-Mail über deinen Gmail-Account."""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{APP_NAME} <{EMAIL_SENDER}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Verbindung mit SSL (Port 465)
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True, "✅ E-Mail wurde erfolgreich versendet!"
    except Exception as e:
        return False, f"❌ Fehler: {str(e)}"

def get_mailto_link(recipient, subject, body):
    """Erzeugt einen mailto-Link als Backup für das lokale Mail-Programm."""
    subj_enc = urllib.parse.quote(subject)
    body_enc = urllib.parse.quote(body)
    return f"mailto:{recipient}?subject={subj_enc}&body={body_enc}"