from __future__ import annotations

import datetime
import streamlit as st

from core.storage import new_id, save_db


def render_costs(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]
    participants = sorted(list(trip.get("participants", {}).keys()))
    expenses = trip.setdefault("expenses", [])

    st.subheader("💶 Kosten")

    with st.expander("➕ Ausgabe hinzufügen"):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Bezeichnung", key=f"exp_title_{trip_key}")
            payer = st.selectbox("Bezahlt von", participants or [user], key=f"exp_payer_{trip_key}")
        with c2:
            amount = st.number_input("Betrag (€)", min_value=0.0, step=1.0, key=f"exp_amount_{trip_key}")
            shared_with = st.multiselect("Aufteilen auf", participants or [user], default=participants or [user], key=f"exp_shared_{trip_key}")

        if st.button("Speichern", key=f"save_expense_{trip_key}"):
            if title.strip() and amount > 0 and shared_with:
                expenses.append({
                    "id": new_id("exp"),
                    "title": title.strip(),
                    "payer": payer,
                    "amount": float(amount),
                    "shared_with": shared_with,
                    "created_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
                })
                save_db(data)
                st.rerun()

    if not expenses:
        st.info("Noch keine Kosten erfasst.")
        return

    for e in expenses:
        st.write(f"**{e.get('title')}** – {e.get('amount', 0):.2f} € · bezahlt von {e.get('payer')}")

    balances = {p: 0.0 for p in participants}
    for e in expenses:
        amount = float(e.get("amount", 0) or 0)
        payer = e.get("payer")
        shared = e.get("shared_with", []) or participants
        if not shared:
            continue
        share = amount / len(shared)
        for person in shared:
            balances[person] -= share
        if payer in balances:
            balances[payer] += amount

    st.divider()
    st.subheader("🧾 Ausgleich")
    for person, balance in balances.items():
        if balance > 0.01:
            st.success(f"{person} bekommt {balance:.2f} € zurück")
        elif balance < -0.01:
            st.warning(f"{person} schuldet {-balance:.2f} €")
        else:
            st.info(f"{person} ist ausgeglichen")
