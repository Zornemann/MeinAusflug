import streamlit as st
import datetime

def render_dashboard(trip):
    st.subheader("📅 Reiseübersicht")

    start = datetime.date.fromisoformat(trip["details"]["start_date"])
    end = datetime.date.fromisoformat(trip["details"]["end_date"])

    st.markdown(f"**{start.strftime('%d.%m.%Y')} – {end.strftime('%d.%m.%Y')}**")
    st.markdown(f"📍 {trip['details']['destination']}")