from __future__ import annotations

import datetime

import streamlit as st

try:
    from core.storage import save_db, new_id
except Exception:  # fallback for flat project layout
    from storage import save_db, new_id


def render_checklist(data, trip_name, user):
    trip = data["trips"][trip_name]
    st.header("🧭 Ausrüstung & Verpflegung")

    participants = trip.get("participants", {})
    crew = sorted(list(participants.keys()))

    tasks = trip.setdefault("tasks", [])
    trip.setdefault("checklist", tasks)

    sel_user = st.selectbox("🔍 Zeige Items von:", ["Alle"] + crew, key=f"filter_user_{trip_name}")

    display_tasks = tasks
    if sel_user != "Alle":
        display_tasks = [
            t for t in tasks if isinstance(t.get("who"), list) and sel_user in t.get("who", [])
        ]

    with st.expander("➕ Neues Item hinzufügen"):
        job = st.text_input(
            "Was wird benötigt?",
            placeholder="z.B. Gaskocher, Zelt, Nudeln...",
            key=f"new_job_input_{trip_name}",
        )
        who = st.multiselect("Wer bringt es mit?", crew, key=f"new_who_input_{trip_name}")

        if st.button("Hinzufügen", key=f"btn_add_task_{trip_name}"):
            if job.strip():
                now_iso = datetime.datetime.now().replace(microsecond=0).isoformat()
                new_task = {
                    "id": new_id("task") if callable(new_id) else f"task_{len(tasks)+1}",
                    "job": job.strip(),
                    "who": who,
                    "done": False,
                    "created_at": now_iso,
                    "created_by": user,
                    "updated_at": now_iso,
                    "updated_by": user,
                }
                tasks.append(new_task)
                save_db(data)
                st.success(f"'{job}' hinzugefügt!")
                st.rerun()
            else:
                st.warning("Bitte gib an, was mitgebracht werden soll.")

    st.divider()

    if not display_tasks:
        st.info(f"Keine Items für '{sel_user}' vorhanden.")
    else:
        for i, t in enumerate(display_tasks):
            t_id = t.get("id", f"task_{i}")
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])

            is_done = t.get("done", False)
            changed = c1.checkbox("", value=is_done, key=f"check_{trip_name}_{t_id}")
            if changed != is_done:
                t["done"] = changed
                t["updated_at"] = datetime.datetime.now().replace(microsecond=0).isoformat()
                t["updated_by"] = user
                save_db(data)
                st.rerun()

            who_txt = ", ".join(t.get("who", [])) if t.get("who") else "Offen"
            label = f"~~{t.get('job')}~~" if t.get("done") else f"**{t.get('job')}**"
            c2.markdown(f"{label}  \n*{who_txt}*", unsafe_allow_html=True)

            if c3.button("🗑️", key=f"del_{trip_name}_{t_id}"):
                trip["tasks"] = [x for x in tasks if x.get("id") != t_id]
                trip["checklist"] = trip["tasks"]
                save_db(data)
                st.rerun()

    st.divider()
    st.subheader("📄 Export & Druck")

    if sel_user != "Alle":
        user_items = [t.get("job") for t in display_tasks if not t.get("done")]

        if user_items:
            st.write(f"Offene Items für {sel_user}:")
            export_text = f"CHECKLISTE FÜR {sel_user.upper()}\nReise: {trip_name}\n" + "-" * 20 + "\n"
            for item in user_items:
                export_text += f"[ ] {item}\n"

            st.download_button(
                label=f"📥 Liste für {sel_user} als .txt speichern",
                data=export_text,
                file_name=f"Checkliste_{sel_user}.txt",
                mime="text/plain",
            )
        else:
            st.success(f"Super! {sel_user} hat bereits alles erledigt.")
    else:
        st.caption("Wähle einen Teilnehmer oben aus, um eine persönliche Liste zu exportieren.")
