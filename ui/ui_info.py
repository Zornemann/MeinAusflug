from __future__ import annotations

import urllib.parse
import streamlit as st

from core.storage import save_db

ROLE_OPTIONS = ["viewer", "member", "editor", "admin"]
ROLE_HELP = {
    "viewer": "Kann Inhalte ansehen",
    "member": "Kann chatten und Aufgaben pflegen",
    "editor": "Kann Reiseinhalte und Kosten bearbeiten",
    "admin": "Voller Zugriff inkl. Teilnehmerverwaltung",
}


def render_info(data: dict, trip_key: str, user: str, app_url: str):
    trip = data["trips"][trip_key]
    participants = trip.setdefault("participants", {})
    details = trip.setdefault("details", {})
    viewer_role = participants.get(user, {}).get("role", "member")

    st.subheader("👥 Teilnehmer & Einladungen")

    with st.form(f"invite_form_{trip_key}"):
        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            new_name = st.text_input("Name")
        with c2:
            display_name = st.text_input("Anzeigename")
        with c3:
            role = st.selectbox("Rolle", ROLE_OPTIONS, index=ROLE_OPTIONS.index("member"), disabled=viewer_role != "admin")
        submitted = st.form_submit_button("Teilnehmer hinzufügen", use_container_width=True)

    if submitted:
        if not new_name.strip():
            st.warning("Bitte einen Namen eingeben.")
        elif new_name.strip() in participants:
            st.warning("Teilnehmer existiert bereits.")
        else:
            participants[new_name.strip()] = {
                "display_name": display_name.strip() or new_name.strip(),
                "role": role if viewer_role == "admin" else "member",
            }
            save_db(data)
            st.success("Teilnehmer hinzugefügt.")
            st.rerun()

    for person, meta in participants.items():
        c1, c2, c3, c4 = st.columns([2, 1.2, 1.4, .8])
        c1.write(f"👤 **{meta.get('display_name') or person}**")
        c2.caption(f"Rolle: {meta.get('role', 'member')}")
        c3.caption(ROLE_HELP.get(meta.get("role", "member"), ""))
        if viewer_role == "admin" and person != user:
            new_role = c4.selectbox(
                " ",
                ROLE_OPTIONS,
                index=ROLE_OPTIONS.index(meta.get("role", "member")) if meta.get("role", "member") in ROLE_OPTIONS else 1,
                key=f"role_{trip_key}_{person}",
                label_visibility="collapsed",
            )
            if new_role != meta.get("role", "member"):
                meta["role"] = new_role
                save_db(data)
                st.rerun()

    st.divider()

    trip_link = f"{app_url}?trip={urllib.parse.quote(trip_key)}"
    st.subheader("🔗 Einladungslink")
    st.text_input("Link", trip_link, key=f"trip_link_{trip_key}")
    st.caption("Mit diesem Link wird die Reise direkt geöffnet.")

    if details.get("homepage"):
        st.link_button("🌐 Homepage öffnen", details["homepage"], use_container_width=True)
