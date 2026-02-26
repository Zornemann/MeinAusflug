import streamlit as st
from storage import save_db, new_id
from email_service import send_checklist_pdf
from pdf_service import generate_checklist_pdf

# -------------------------------------------------
# Checkliste (Ausrüstung / Verpflegung)
# -------------------------------------------------
def render_checklist(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.header("🧭 Ausrüstung / Verpflegung")

    crew = list(trip["participants"].keys())

    # ---------------------------------------
    # Filter
    # ---------------------------------------
    sel_user = st.selectbox("🔍 Zeige Items von:", ["Alle"] + crew)

    tasks = trip["tasks"]
    if sel_user != "Alle":
        tasks = [t for t in tasks if sel_user in t["who"]]

    # ---------------------------------------
    # Neues Item hinzufügen
    # ---------------------------------------
    with st.expander("➕ Neues Item"):
        job = st.text_input("Was?")
        who = st.multiselect("Wer bringt es mit?", crew)
        if st.button("Hinzufügen"):
            if job:
                tasks_all = trip["tasks"]
                tasks_all.append({
                    "id": new_id("task"),
                    "job": job,
                    "who": who,
                    "done": False
                })
                trip["tasks"] = tasks_all
                save_db(data)
                st.experimental_rerun()

    # ---------------------------------------
    # Liste anzeigen
    # ---------------------------------------
    if not tasks:
        st.info("Keine Items vorhanden.")
    else:
        for t in tasks:
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])

            if c1.checkbox("", value=t["done"], key=t["id"]):
                t["done"] = not t["done"]
                save_db(data)
                st.experimental_rerun()

            who_txt = ", ".join(t["who"]) if t["who"] else "Offen"
            c2.write(f"{'~~' if t['done'] else ''}{t['job']}{'~~' if t['done'] else ''} ({who_txt})")

            if c3.button("🗑️", key="del_"+t["id"]):
                trip["tasks"] = [x for x in trip["tasks"] if x["id"] != t["id"]]
                save_db(data)
                st.experimental_rerun()

    st.divider()

    # ---------------------------------------
    # PDF EXPORT + MAIL-VERSAND
    # ---------------------------------------
    st.subheader("📄 Checkliste exportieren / versenden")

    if sel_user != "Alle":
        items = [t["job"] for t in trip["tasks"] if sel_user in t["who"]]

        if st.button(f"PDF für {sel_user} erstellen"):
            pdf = generate_checklist_pdf(sel_user, items, trip_name)
            st.download_button(f"PDF herunterladen ({sel_user})", data=pdf,
                               file_name=f"Checkliste_{sel_user}.pdf")

        email = trip["participants"][sel_user].get("email", "")

        if email and st.button(f"Per Mail an {sel_user} verschicken"):
            pdf = generate_checklist_pdf(sel_user, items, trip_name)
            send_checklist_pdf(sel_user, email, pdf, trip_name)
            st.success("Gesendet!")
    else:
        st.info("Bitte einen Teilnehmer auswählen.")
