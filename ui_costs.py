import streamlit as st
import pandas as pd
from storage import save_db

def render_costs(data, trip_name, user):
    trip = data["trips"][trip_name]

    st.header("💰 Kosten")

    crew = list(trip["participants"].keys())

    # Neue Ausgabe
    with st.expander("Neue Ausgabe"):
        amount = st.number_input("Euro", min_value=0.0)
        desc = st.text_input("Beschreibung")
        if st.button("Speichern") and amount > 0:
            trip["expenses"].append({
                "payer": user,
                "amount": amount,
                "desc": desc
            })
            save_db(data)
            st.experimental_rerun()

    if trip["expenses"]:
        df = pd.DataFrame(trip["expenses"])
        st.dataframe(df)

        total = df["amount"].sum()
        per_head = total / len(crew)

        st.info(f"Gesamt: {total:.2f} € • Pro Person: {per_head:.2f} €")

        balances = {p: -per_head for p in crew}
        for e in trip["expenses"]:
            balances[e["payer"]] += e["amount"]

        for p, b in balances.items():
            if b >= 0:
                st.write(f"**{p}** bekommt **{b:.2f} €**")
            else:
                st.write(f"**{p}** schuldet **{-b:.2f} €**")
