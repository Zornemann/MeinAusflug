import streamlit as st
import pandas as pd
from core.storage import save_db


def render_costs(data, trip_name, user):
    trip = data["trips"][trip_name]

    if "expenses" not in trip or not isinstance(trip["expenses"], list):
        trip["expenses"] = []

    participants = trip.get("participants", {})
    crew = list(participants.keys()) if isinstance(participants, dict) else []
    if user not in crew:
        crew = crew + [user]  # fallback

    st.header("💰 Kosten")

    with st.expander("➕ Neue Ausgabe", expanded=True):
        amount = st.number_input("Betrag in €", min_value=0.0, step=1.0, value=0.0)
        desc = st.text_input("Beschreibung", placeholder="z.B. Sprit, Einkauf, Tickets…")

        c1, c2 = st.columns([0.25, 0.75])
        if c1.button("Speichern", width='stretch') and amount > 0 and desc.strip():
            trip["expenses"].append({
                "payer": user,
                "amount": float(amount),
                "desc": desc.strip()
            })
            save_db(data)
            st.rerun()
        if c2.button("Felder leeren", width='stretch'):
            st.rerun()

    if not trip["expenses"]:
        st.info("Noch keine Ausgaben eingetragen.")
        return

    df = pd.DataFrame(trip["expenses"])
    if not df.empty:
        st.dataframe(df, width='stretch')

    total = float(df["amount"].sum()) if "amount" in df.columns else 0.0
    per_head = (total / len(crew)) if crew else 0.0
    st.info(f"Gesamt: {total:.2f} € • Pro Person: {per_head:.2f} €")

    balances = {p: -per_head for p in crew}
    for e in trip["expenses"]:
        payer = e.get("payer")
        amt = float(e.get("amount", 0) or 0)
        if payer in balances:
            balances[payer] += amt

    st.subheader("🧾 Ausgleich")
    for p, b in balances.items():
        if b >= 0:
            st.write(f"**{p}** bekommt **{b:.2f} €**")
        else:
            st.write(f"**{p}** schuldet **{-b:.2f} €**")