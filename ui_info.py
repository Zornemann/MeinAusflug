import streamlit as st
from core.storage import save_db

def render_info(data: dict, trip_key: str):
    trip = data["trips"][trip_key]

    st.subheader("👥 Teilnehmer")

    participants = trip.setdefault("participants", {})

    for name in participants:
        st.write("•", name)

    st.divider()

    st.subheader("➕ Teilnehmer hinzufügen")

    new_user = st.text_input("Name")

    if st.button("Hinzufügen"):
        if new_user and new_user not in participants:
            participants[new_user] = {"display_name": new_user}
            save_db(data)
            st.rerun()

    st.divider()

    st.subheader("🔗 Einladungslink")

    link = f"?trip={trip_key}"

    st.code(link)
    st.caption("Diesen Link teilen")
