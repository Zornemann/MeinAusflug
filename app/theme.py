from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0b1020;
          --bg-soft: #11182b;
          --card: rgba(20, 28, 48, 0.82);
          --card-2: rgba(33, 47, 80, 0.96);
          --text: #f7f9fc;
          --muted: #aeb8cc;
          --border: rgba(130, 153, 196, 0.18);
          --accent: #7c9cff;
          --shadow: 0 10px 30px rgba(0,0,0,.22);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(124,156,255,.16), transparent 28%),
            radial-gradient(circle at top right, rgba(94,234,212,.12), transparent 24%),
            linear-gradient(180deg, #0b1020 0%, #0f172a 100%);
          color: var(--text);
        }

        html, body, [class*="css"] { color: var(--text); }
        header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
        div[data-testid="stDecoration"] { display: none !important; }

        .block-container { max-width: 1120px; padding-top: 0.25rem; padding-bottom: 4rem; }
        h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--text); }

        section[data-testid="stSidebar"] {
          background: rgba(10, 15, 28, 0.96);
          border-right: 1px solid var(--border);
        }

        div[data-testid="stMetric"] {
          background: var(--card);
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
          border-radius: 20px;
          padding: 0.95rem 1rem;
        }

        div[data-testid="stTextInputRoot"] > div,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-baseweb="select"] > div,
        .stTimeInput input {
          background: var(--card-2) !important;
          color: var(--text) !important;
          border: 1px solid var(--border) !important;
          border-radius: 16px !important;
        }

        input, textarea, select {
          color: var(--text) !important;
          -webkit-text-fill-color: var(--text) !important;
        }

        input::placeholder, textarea::placeholder {
          color: #9fb0d4 !important;
          opacity: 1 !important;
          -webkit-text-fill-color: #9fb0d4 !important;
        }

        div[data-baseweb="select"] *, div[data-baseweb="select"] svg {
          color: var(--text) !important;
          fill: var(--text) !important;
          -webkit-text-fill-color: var(--text) !important;
        }

        div[data-baseweb="popover"],
        div[data-baseweb="popover"] *,
        ul[data-baseweb="menu"],
        ul[data-baseweb="menu"] *,
        div[role="listbox"],
        div[role="listbox"] * {
          color: #f7f9fc !important;
          -webkit-text-fill-color: #f7f9fc !important;
        }

        ul[data-baseweb="menu"],
        div[role="listbox"] {
          background: rgba(17, 24, 43, 0.99) !important;
          border: 1px solid rgba(130, 153, 196, 0.18) !important;
          border-radius: 16px !important;
          box-shadow: 0 10px 30px rgba(0,0,0,.22) !important;
        }

        div[role="listbox"] [role="option"]:hover,
        ul[data-baseweb="menu"] li:hover {
          background: rgba(124,156,255,.18) !important;
        }

        div[data-testid="stForm"] {
          background: rgba(10, 16, 31, 0.34);
          border: 1px solid rgba(130, 153, 196, 0.08);
          border-radius: 18px;
          padding: 0.35rem 0.35rem 0.85rem 0.35rem;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stLinkButton > a,
        div[data-testid="stForm"] button,
        div[data-testid="stPopoverButton"] button,
        button[kind],
        button[data-testid] {
          background: linear-gradient(180deg, rgba(33,47,80,0.98), rgba(21,30,50,0.98)) !important;
          border: 1px solid rgba(124,156,255,.32) !important;
          border-radius: 16px !important;
          min-height: 2.85rem;
          color: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
          fill: #f8fbff !important;
          stroke: #f8fbff !important;
          font-weight: 700 !important;
          opacity: 1 !important;
          box-shadow: var(--shadow);
        }

        .stButton > button *,
        .stDownloadButton > button *,
        .stLinkButton > a *,
        div[data-testid="stForm"] button *,
        div[data-testid="stPopoverButton"] button *,
        button[kind] *,
        button[data-testid] * {
          color: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
          fill: #f8fbff !important;
          stroke: #f8fbff !important;
          opacity: 1 !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover,
        div[data-testid="stForm"] button:hover,
        div[data-testid="stPopoverButton"] button:hover,
        button[kind]:hover {
          border-color: rgba(124,156,255,.58) !important;
          transform: translateY(-1px);
        }

        .stButton > button:disabled,
        .stButton > button[disabled],
        div[data-testid="stForm"] button:disabled,
        div[data-testid="stForm"] button[disabled],
        div[data-testid="stPopoverButton"] button:disabled,
        div[data-testid="stPopoverButton"] button[disabled],
        button[kind="secondaryFormSubmit"],
        button[kind="secondaryFormSubmit"]:disabled,
        button[kind="secondaryFormSubmit"][disabled] {
          background: linear-gradient(180deg, rgba(53, 65, 94, 0.98), rgba(38, 49, 75, 0.98)) !important;
          color: #e8eefc !important;
          -webkit-text-fill-color: #e8eefc !important;
          border: 1px solid rgba(124,156,255,.28) !important;
          opacity: 1 !important;
        }

        .stButton > button:disabled *,
        .stButton > button[disabled] *,
        div[data-testid="stForm"] button:disabled *,
        div[data-testid="stForm"] button[disabled] *,
        div[data-testid="stPopoverButton"] button:disabled *,
        div[data-testid="stPopoverButton"] button[disabled] *,
        button[kind="secondaryFormSubmit"] *,
        button[kind="secondaryFormSubmit"]:disabled *,
        button[kind="secondaryFormSubmit"][disabled] * {
          color: #e8eefc !important;
          -webkit-text-fill-color: #e8eefc !important;
          fill: #e8eefc !important;
          stroke: #e8eefc !important;
          opacity: 1 !important;
        }

        div[role="radiogroup"] {
          position: sticky;
          top: 0.35rem;
          z-index: 50;
          display: flex;
          gap: 0.55rem;
          flex-wrap: wrap;
          padding: 0.55rem;
          margin: 0 0 1rem 0;
          border-radius: 20px;
          background: rgba(13, 19, 35, 0.88);
          backdrop-filter: blur(12px);
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
        }

        div[role="radiogroup"] label {
          background: rgba(24, 35, 61, 0.95);
          border: 1px solid rgba(130, 153, 196, 0.14);
          border-radius: 999px;
          padding: 0.38rem 0.95rem;
          min-height: 42px;
          display: flex !important;
          align-items: center;
          justify-content: center;
          font-weight: 700;
        }

        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
          display: none !important;
        }

        .me-chat-row {
          background: rgba(14, 21, 40, 0.45);
          border: 1px solid rgba(130, 153, 196, 0.10);
          border-radius: 16px;
          padding: 0.9rem;
          margin-bottom: 0.8rem;
        }

        .me-soft { color: var(--muted) !important; }

        @media (max-width: 768px) {
          .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
          .stButton > button, .stDownloadButton > button, .stLinkButton > a, div[data-testid="stForm"] button { width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
