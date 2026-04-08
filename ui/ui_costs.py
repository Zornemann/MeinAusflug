from __future__ import annotations

import csv
import datetime
from io import StringIO

import streamlit as st

from core.storage import new_id, save_db

CATEGORIES = ["Allgemein", "Transport", "Essen", "Unterkunft", "Freizeit"]


def _compute_balances(participants: list[str], expenses: list[dict]) -> dict[str, float]:
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
    return balances


def _settlement_suggestions(balances: dict[str, float]) -> list[tuple[str, str, float]]:
    creditors = [[p, round(v, 2)] for p, v in balances.items() if v > 0.01]
    debtors = [[p, round(-v, 2)] for p, v in balances.items() if v < -0.01]
    suggestions = []

    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        amount = round(min(debt, credit), 2)
        if amount > 0:
            suggestions.append((debtor, creditor, amount))
        debtors[i][1] = round(debt - amount, 2)
        creditors[j][1] = round(credit - amount, 2)
        if debtors[i][1] <= 0.01:
            i += 1
        if creditors[j][1] <= 0.01:
            j += 1
    return suggestions


def _csv_export(expenses: list[dict]) -> str:
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Titel", "Kategorie", "Betrag", "Bezahlt von", "Aufgeteilt auf", "Notizen", "Erstellt am"])
    for e in expenses:
        writer.writerow([
            e.get("title", ""),
            e.get("category", ""),
            f"{float(e.get('amount', 0) or 0):.2f}",
            e.get("payer", ""),
            ", ".join(e.get("shared_with", []) or []),
            e.get("notes", ""),
            e.get("created_at", ""),
        ])
    return output.getvalue()


def render_costs(data: dict, trip_key: str, user: str):
    trip = data["trips"][trip_key]
    participants_meta = trip.get("participants", {})
    role = participants_meta.get(user, {}).get("role", "member")
    participants = sorted(list(participants_meta.keys()))
    expenses = trip.setdefault("expenses", [])

    st.subheader("💶 Kosten")

    can_edit = role in {"admin", "editor", "member"}
    if can_edit:
        with st.expander("➕ Ausgabe hinzufügen"):
            c1, c2, c3 = st.columns([2, 1.2, 1.4])
            with c1:
                title = st.text_input("Bezeichnung", key=f"exp_title_{trip_key}")
                payer = st.selectbox("Bezahlt von", participants or [user], key=f"exp_payer_{trip_key}")
                notes = st.text_area("Notizen", key=f"exp_notes_{trip_key}", height=80)
            with c2:
                amount = st.number_input("Betrag (€)", min_value=0.0, step=1.0, key=f"exp_amount_{trip_key}")
                category = st.selectbox("Kategorie", CATEGORIES, key=f"exp_category_{trip_key}")
            with c3:
                shared_with = st.multiselect("Aufteilen auf", participants or [user], default=participants or [user], key=f"exp_shared_{trip_key}")

            if st.button("Speichern", key=f"save_expense_{trip_key}"):
                if title.strip() and amount > 0 and shared_with:
                    expenses.append({
                        "id": new_id("exp"),
                        "title": title.strip(),
                        "payer": payer,
                        "amount": float(amount),
                        "shared_with": shared_with,
                        "notes": notes.strip(),
                        "category": category,
                        "created_at": datetime.datetime.now().replace(microsecond=0).isoformat(),
                    })
                    save_db(data)
                    st.rerun()

    if not expenses:
        st.info("Noch keine Kosten erfasst.")
        return

    summary_cols = st.columns([2, 1, 1])
    with summary_cols[0]:
        st.download_button(
            "CSV exportieren",
            data=_csv_export(expenses),
            file_name=f"kosten_{trip.get('name', trip_key).replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"costs_csv_{trip_key}",
        )
    with summary_cols[1]:
        total_amount = sum(float(e.get("amount", 0) or 0) for e in expenses)
        st.metric("Gesamt", f"{total_amount:.2f} €")
    with summary_cols[2]:
        st.metric("Einträge", str(len(expenses)))

    for e in expenses:
        with st.container():
            st.markdown(
                f"<div class='me-card'><strong>{e.get('title')}</strong><br>"
                f"<span class='me-soft'>{e.get('category', 'Allgemein')} · bezahlt von {e.get('payer')} · {float(e.get('amount', 0) or 0):.2f} €</span><br>"
                f"<span class='me-soft'>Aufgeteilt auf: {', '.join(e.get('shared_with', []) or [])}</span>"
                + (f"<br><span class='me-soft'>{e.get('notes')}</span>" if e.get('notes') else "")
                + "</div>",
                unsafe_allow_html=True,
            )

    balances = _compute_balances(participants, expenses)

    st.divider()
    st.subheader("🧾 Ausgleich")
    suggestions = _settlement_suggestions(balances)
    if suggestions:
        for debtor, creditor, amount in suggestions:
            st.success(f"{debtor} zahlt {amount:.2f} € an {creditor}")
    else:
        st.info("Alle sind bereits ausgeglichen.")

    with st.expander("Kontostände je Person", expanded=False):
        for person, balance in balances.items():
            if balance > 0.01:
                st.success(f"{person} bekommt {balance:.2f} € zurück")
            elif balance < -0.01:
                st.warning(f"{person} schuldet {-balance:.2f} €")
            else:
                st.info(f"{person} ist ausgeglichen")
