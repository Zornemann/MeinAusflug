import qrcode
from io import BytesIO
from PIL import Image
import base64
import datetime

# -------------------------------------------------
# QR-Code für App-Link erzeugen
# -------------------------------------------------
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# -------------------------------------------------
# WebP Bild komprimieren
# -------------------------------------------------
def convert_to_webp(image_bytes, quality=70):
    img = Image.open(BytesIO(image_bytes))
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality)
    return buf.getvalue()

# -------------------------------------------------
# Datumsformatierung
# -------------------------------------------------
def now_iso():
    return datetime.datetime.now().isoformat()

def format_time_short(timestr):
    try:
        return timestr[11:16]
    except:
        return ""

# -------------------------------------------------
# Badge-Anzeige: neue Nachrichten oder neue Tasks
# -------------------------------------------------
def count_unread(messages, user, last_read_ts):
    return len([m for m in messages if m["time"] > last_read_ts and m["user"] != user])
