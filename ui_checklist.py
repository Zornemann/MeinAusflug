import streamlit as st
from storage import save_db, new_id

# -------------------------------------------------
# Checkliste (Ausrüstung / Verpflegung)
# -------------------------------------------------
def render_checklist(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.header("🧭 Ausrüstung & Verpflegung")

    # Sicherstellen, dass participants ein Dictionary ist
    participants = trip.get("participants", {})
    crew = sorted(list(participants.keys()))

    # 1. Sicherstellen, dass die Liste "tasks" existiert
    if "tasks" not in trip:
        trip["tasks"] = []
    
    # ---------------------------------------
    # Filter
    # ---------------------------------------
    sel_user = st.selectbox("🔍 Zeige Items von:", ["Alle"] + crew, key="filter_user")

    # Filter-Logik
    display_tasks = trip["tasks"]
    if sel_user != "Alle":
        display_tasks = [t for t in trip["tasks"] if isinstance(t.get("who"), list) and sel_user in t["who"]]

    # ---------------------------------------
    # Neues Item hinzufügen
    # ---------------------------------------
    with st.expander("➕ Neues Item hinzufügen"):
        job = st.text_input("Was wird benötigt?", placeholder="z.B. Gaskocher, Zelt, Nudeln...", key="new_job_input")
        who = st.multiselect("Wer bringt es mit?", crew, key="new_who_input")
        
        if st.button("Hinzufügen", key="btn_add_task"):
            if job:
                new_task = {
                    "id": new_id("task"),
                    "job": job,
                    "who": who,
                    "done": False
                }
                trip["tasks"].append(new_task) # FIX: Hier hieß es vorher new_entry
                save_db(data)
                st.success(f"'{job}' hinzugefügt!")
                st.rerun()
            else:
                st.warning("Bitte gib an, was mitgebracht werden soll.")

    st.divider()

    # ---------------------------------------
    # Liste anzeigen
    # ---------------------------------------
    if not display_tasks:
        st.info(f"Keine Items für '{sel_user}' vorhanden.")
    else:
        for i, t in enumerate(display_tasks):
            t_id = t.get("id", f"task_{i}")
            
            # Spalten: Checkbox | Text | Löschen
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])

            # Status ändern
            is_done = t.get("done", False)
            if c1.checkbox("", value=is_done, key=f"check_{t_id}"):
                t["done"] = not is_done
                save_db(data)
                st.rerun()

            # Text-Anzeige mit Durchstreichen bei Erledigt
            who_txt = ", ".join(t.get("who", [])) if t.get("who") else "Offen"
            label = f"~~{t.get('job')}~~" if is_done else f"**{t.get('job')}**"
            c2.markdown(f"{label}  \n*{who_txt}*", unsafe_allow_html=True)

            # Lösch-Button (FIX: Eindeutige ID-Filterung)
            if c3.button("🗑️", key=f"del_{t_id}"):
                trip["tasks"] = [x for x in trip["tasks"] if x.get("id") != t_id]
                save_db(data)
                st.rerun()

    st.divider()

    # ---------------------------------------
    # Export-Bereich (PDF/Text)
    # ---------------------------------------
    st.subheader("📄 Export & Druck")
    
    if sel_user != "Alle":
        user_items = [t.get("job") for t in display_tasks if not t.get("done")]
        
        if user_items:
            st.write(f"Offene Items für {sel_user}:")
            # Einfacher Text-Export als Fallback für PDF-Service
            export_text = f"CHECKLISTE FÜR {sel_user.upper()}\nReise: {trip_name}\n" + "-"*20 + "\n"
            for item in user_items:
                export_text += f"[ ] {item}\n"
            
            st.download_button(
                label=f"📥 Liste für {sel_user} als .txt speichern",
                data=export_text,
                file_name=f"Checkliste_{sel_user}.txt",
                mime="text/plain"
            )
        else:
            st.success(f"Super! {sel_user} hat bereits alles erledigt.")
    else:
        st.caption("Wähle einen Teilnehmer oben aus, um eine persönliche Liste zu exportieren.")