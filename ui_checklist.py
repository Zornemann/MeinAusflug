import streamlit as st
from storage import save_db, new_id
# Falls diese Services noch nicht fertig sind, können sie Fehlermeldungen werfen
try:
    from email_service import send_checklist_pdf
    from pdf_service import generate_checklist_pdf
except ImportError:
    pass

# -------------------------------------------------
# Checkliste (Ausrüstung / Verpflegung)
# -------------------------------------------------
def render_checklist(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.header("🧭 Ausrüstung / Verpflegung")

    # Sicherstellen, dass participants ein Dictionary ist
    participants = trip.get("participants", {})
    crew = list(participants.keys())

    # ---------------------------------------
    # Filter
    # ---------------------------------------
    sel_user = st.selectbox("🔍 Zeige Items von:", ["Alle"] + crew)

    # Sicherstellen, dass tasks eine Liste ist
    if "tasks" not in trip:
        trip["tasks"] = []
    
    tasks = trip["tasks"]
    if sel_user != "Alle":
        tasks = [t for t in tasks if isinstance(t.get("who"), list) and sel_user in t["who"]]

    # ---------------------------------------
    # Neues Item hinzufügen
    # ---------------------------------------
    with st.expander("➕ Neues Item"):
        job = st.text_input("Was?")
        who = st.multiselect("Wer bringt es mit?", crew)
        if st.button("Hinzufügen"):
            if job:
                new_task = {
                    "id": new_id("task"),
                    "job": job,
                    "who": who,
                    "done": False
                }
                trip["tasks"].append(new_entry)
                save_db(data)
                st.rerun()

    # ---------------------------------------
    # Liste anzeigen
    # ---------------------------------------
    if not tasks:
        st.info("Keine Items vorhanden.")
    else:
        for i, t in enumerate(tasks):
            # REPARATUR: Falls ID fehlt, generieren wir eine temporäre für den Key
            t_id = t.get("id", f"task_{i}")
            
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])

            # Checkbox für Erledigt-Status
            if c1.checkbox("", value=t.get("done", False), key=f"check_{t_id}"):
                t["done"] = not t.get("done", False)
                save_db(data)
                st.rerun()

            who_list = t.get("who", [])
            who_txt = ", ".join(who_list) if who_list else "Offen"
            
            is_done = t.get("done", False)
            label = f"~~{t.get('job', 'Unbekannt')}~~" if is_done else t.get('job', 'Unbekannt')
            c2.write(f"{label} ({who_txt})")

            # Lösch-Button
            if c3.button("🗑️", key=f"del_{t_id}"):
                trip["tasks"] = [x for x in trip["tasks"] if x.get("id") != t.get("id") or x == t]
                save_db(data)
                st.rerun()

    st.divider()

    # ---------------------------------------
    # PDF EXPORT + MAIL-VERSAND
    # ---------------------------------------
    st.subheader("📄 Checkliste exportieren / versenden")

    if sel_user != "Alle":
        user_items = [t.get("job") for t in trip["tasks"] if isinstance(t.get("who"), list) and sel_user in t["who"]]

        col_pdf, col_mail = st.columns(2)

        with col_pdf:
            if st.button(f"PDF für {sel_user} erstellen"):
                try:
                    pdf = generate_checklist_pdf(sel_user, user_items, trip_name)
                    st.download_button(f"📥 PDF herunterladen", data=pdf,
                                       file_name=f"Checkliste_{sel_user}.pdf")
                except NameError:
                    st.error("PDF-Service nicht konfiguriert.")

        with col_mail:
            # Sicherer Zugriff auf Teilnehmer-Daten (Dictionary vs. String Check)
            u_data = participants.get(sel_user, {})
            email = u_data.get("email", "") if isinstance(u_data, dict) else ""

            if email:
                if st.button(f"📧 An {sel_user} senden"):
                    try:
                        pdf = generate_checklist_pdf(sel_user, user_items, trip_name)
                        send_checklist_pdf(sel_user, email, pdf, trip_name)
                        st.success("Gesendet!")
                    except NameError:
                        st.error("E-Mail-Service nicht konfiguriert.")
            else:
                st.warning("Keine E-Mail für diesen Nutzer hinterlegt.")
    else:
        st.info("Bitte einen Teilnehmer oben auswählen, um ein PDF zu generieren.")