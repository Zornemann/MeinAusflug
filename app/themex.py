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
          --accent-strong: #94adff;
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

        .block-container {
          max-width: 1120px;
          padding-top: 0.25rem;
          padding-bottom: 4rem;
        }

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
        div[data-testid="stTextArea"] > div,
        div[data-testid="stNumberInput"] > div,
        div[data-testid="stDateInput"] > div,
        div[data-baseweb="select"] > div,
        .stTimeInput > div,
        .stTextInput > div > div,
        .stTextArea > div > div {
          background: var(--card-2) !important;
          border: 1px solid var(--border) !important;
          border-radius: 16px !important;
        }

        div[data-testid="stTextInputRoot"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        .stTimeInput input,
        .stTextInput input,
        .stTextArea textarea,
        input[type="text"],
        input[type="email"],
        input[type="password"],
        input[type="number"],
        input[type="date"],
        textarea {
          background: transparent !important;
          color: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
          caret-color: #f8fbff !important;
          border: none !important;
          box-shadow: none !important;
          opacity: 1 !important;
        }

        /* Login/name input explicitly dark */
        .stTextInput input,
        .stTextInput input:focus,
        .stTextInput input:active {
          background-color: rgba(33, 47, 80, 0.01) !important;
          color: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
        }

        div[data-testid="stTextInputRoot"] input:disabled,
        div[data-testid="stTextArea"] textarea:disabled,
        div[data-testid="stNumberInput"] input:disabled,
        div[data-testid="stDateInput"] input:disabled,
        .stTimeInput input:disabled,
        .stTextInput input:disabled,
        input[disabled],
        textarea[disabled],
        input[readonly],
        textarea[readonly] {
          background: transparent !important;
          color: #eef4ff !important;
          -webkit-text-fill-color: #eef4ff !important;
          opacity: 1 !important;
        }

        input:-webkit-autofill,
        input:-webkit-autofill:hover,
        input:-webkit-autofill:focus,
        textarea:-webkit-autofill,
        textarea:-webkit-autofill:hover,
        textarea:-webkit-autofill:focus {
          -webkit-text-fill-color: #f8fbff !important;
          -webkit-box-shadow: 0 0 0px 1000px rgba(33, 47, 80, 0.96) inset !important;
          box-shadow: 0 0 0px 1000px rgba(33, 47, 80, 0.96) inset !important;
          transition: background-color 9999s ease-in-out 0s !important;
          caret-color: #f8fbff !important;
        }

        input::placeholder,
        textarea::placeholder {
          color: #9fb0d4 !important;
          opacity: 1 !important;
          -webkit-text-fill-color: #9fb0d4 !important;
        }

        /* Closed date fields dark and readable */
        div[data-testid="stDateInput"] > div,
        div[data-testid="stDateInput"] [data-baseweb="input"] {
          background: rgba(33, 47, 80, 0.96) !important;
          border: 1px solid rgba(130, 153, 196, 0.18) !important;
          border-radius: 16px !important;
        }

        div[data-testid="stDateInput"] input,
        div[data-testid="stDateInput"] input:focus,
        div[data-testid="stDateInput"] input:active,
        div[data-testid="stDateInput"] [data-baseweb="input"] input,
        div[data-testid="stDateInput"] [data-baseweb="input"] input:focus,
        div[data-testid="stDateInput"] [data-baseweb="input"] input:active,
        .stDateInput input,
        .stDateInput input:focus,
        .stDateInput input:active {
          background: transparent !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          opacity: 1 !important;
          caret-color: #ffffff !important;
        }

        div[data-testid="stDateInput"] svg,
        div[data-testid="stDateInput"] button,
        div[data-testid="stDateInput"] button svg,
        .stDateInput svg {
          color: #f8fbff !important;
          fill: #f8fbff !important;
          stroke: #f8fbff !important;
          opacity: 1 !important;
        }

        /* Calendar popup: keep popup light, make content dark/readable */
        div[role="dialog"] > div {
          background: #ffffff !important;
          border: 1px solid rgba(0,0,0,.08) !important;
          border-radius: 18px !important;
          box-shadow: 0 10px 30px rgba(0,0,0,.25) !important;
        }

        div[role="dialog"],
        div[role="dialog"] * {
          color: #1f2937 !important;
          -webkit-text-fill-color: #1f2937 !important;
        }

        div[role="dialog"] button,
        div[role="dialog"] select,
        div[role="dialog"] option,
        div[role="dialog"] th,
        div[role="dialog"] td,
        div[role="dialog"] span,
        div[role="dialog"] label {
          color: #1f2937 !important;
          -webkit-text-fill-color: #1f2937 !important;
          background: transparent !important;
          opacity: 1 !important;
        }

        div[role="dialog"] svg {
          color: #1f2937 !important;
          fill: #1f2937 !important;
          stroke: #1f2937 !important;
        }

        div[role="dialog"] button:hover {
          background: rgba(124,156,255,.12) !important;
        }

        div[role="dialog"] button[aria-selected="true"],
        div[role="dialog"] td[aria-selected="true"] button,
        div[role="dialog"] td[aria-selected="true"] {
          background: rgba(124,156,255,.22) !important;
          color: #0f172a !important;
          -webkit-text-fill-color: #0f172a !important;
          border-radius: 999px !important;
        }

        div[data-baseweb="select"] *,
        div[data-baseweb="select"] svg,
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
          color: #f8fbff !important;
          fill: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
          opacity: 1 !important;
        }

        div[data-baseweb="popover"] > div,
        [role="listbox"],
        ul[data-baseweb="menu"] {
          background: rgba(17, 24, 43, 0.995) !important;
          border: 1px solid rgba(130, 153, 196, 0.18) !important;
          border-radius: 16px !important;
          box-shadow: 0 10px 30px rgba(0,0,0,.22) !important;
        }

        [role="listbox"] [role="option"],
        ul[data-baseweb="menu"] li,
        div[data-baseweb="popover"] [role="option"] {
          background: rgba(17, 24, 43, 0.995) !important;
          color: #f7f9fc !important;
          border-radius: 10px !important;
          margin: 0.12rem 0.3rem !important;
          padding-top: 0.5rem !important;
          padding-bottom: 0.5rem !important;
          opacity: 1 !important;
        }

        [role="listbox"] [role="option"] *,
        ul[data-baseweb="menu"] li *,
        div[data-baseweb="popover"] [role="option"] * {
          background: transparent !important;
          color: #f7f9fc !important;
          -webkit-text-fill-color: #f7f9fc !important;
          opacity: 1 !important;
        }

        [role="listbox"] [role="option"]:hover,
        ul[data-baseweb="menu"] li:hover,
        div[data-baseweb="popover"] [role="option"]:hover {
          background: rgba(124,156,255,.18) !important;
          color: #ffffff !important;
        }

        [role="listbox"] [role="option"][aria-selected="true"],
        ul[data-baseweb="menu"] li[aria-selected="true"],
        div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
          background: rgba(124,156,255,.26) !important;
          color: #ffffff !important;
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

        div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child { display: none !important; }

        @media (max-width: 768px) {
          .block-container { padding-left: 0.8rem; padding-right: 0.8rem; }
          div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.5rem;
            padding: 0.5rem;
            border-radius: 18px;
          }
          div[role="radiogroup"] label {
            width: 100% !important;
            min-height: 48px;
            padding: 0.4rem 0.5rem;
            border-radius: 14px;
            text-align: center;
            font-size: 0.92rem;
            line-height: 1.1;
          }
          .stButton > button, .stDownloadButton > button, .stLinkButton > a, div[data-testid="stForm"] button {
            width: 100%;
          }
        }

        @media (max-width: 460px) {
          div[role="radiogroup"] { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
