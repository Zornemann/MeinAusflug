import smtplib
import urllib.parse
from email.mime.text import MIMEText

from core.config import EMAIL_SENDER, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT, APP_NAME


def send_system_email(to_email: str, subject: str, body: str):
    """
    Sendet eine E-Mail über SMTP.
    Rückgabe: (ok: bool, message: str)
    """
    if not to_email:
        return False, "Keine Empfänger-E-Mail angegeben."

    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False, "E-Mail Versand ist nicht konfiguriert (EMAIL_SENDER/EMAIL_PASSWORD fehlen)."

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            # TLS wenn möglich/gewünscht
            try:
                server.starttls()
                server.ehlo()
            except Exception:
                # Manche SMTP Server wollen kein STARTTLS auf dem Port
                pass

            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [to_email], msg.as_string())
        return True, "✅ Einladung wurde per E-Mail versendet."
    except Exception as e:
        return False, f"❌ Fehler beim Versand: {e}"


def get_mailto_link(to_email: str, subject: str, body: str) -> str:
    """
    Erstellt einen mailto:-Link, damit der Nutzer sein Mailprogramm nutzen kann.
    """
    q_subject = urllib.parse.quote(subject or "")
    q_body = urllib.parse.quote(body or "")
    return f"mailto:{to_email}?subject={q_subject}&body={q_body}"