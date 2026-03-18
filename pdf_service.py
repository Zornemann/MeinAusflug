from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --------------------------------------------------------
# PDF für Checkliste eines Teilnehmers erzeugen
# --------------------------------------------------------
def generate_checklist_pdf(name, items, trip_name):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, f"Checkliste für: {name}")
    c.setFont("Helvetica", 12)
    c.drawString(50, 780, f"Reise: {trip_name}")

    y = 750
    for item in items:
        c.drawString(50, y, f"- {item}")
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 800

    c.save()
    return buffer.getvalue()
