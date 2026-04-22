from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0b1020;
          --card: rgba(20, 28, 48, 0.82);
          --card-2: rgba(33, 47, 80, 0.96);
          --text: #f7f9fc;
          --muted: #aeb8cc;
          --border: rgba(130, 153, 196, 0.18);
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
          padding-top: 0.4rem;
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

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
          color: #c8d5f4 !important;
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

        input::placeholder,
        textarea::placeholder {
          color: #9fb0d4 !important;
          opacity: 1 !important;
          -webkit-text-fill-color: #9fb0d4 !important;
        }

        div[data-testid="stDateInput"] > div,
        div[data-testid="stDateInput"] [data-baseweb="input"] {
          background: rgba(33, 47, 80, 0.96) !important;
          border: 1px solid rgba(130, 153, 196, 0.18) !important;
          border-radius: 16px !important;
        }

        div[data-testid="stDateInput"] input,
        div[data-testid="stDateInput"] input:focus,
        div[data-testid="stDateInput"] [data-baseweb="input"] input,
        .stDateInput input {
          background: transparent !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          opacity: 1 !important;
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

        div[data-testid="stExpander"] {
          background: rgba(10,16,31,.38);
          border: 1px solid rgba(130,153,196,.10);
          border-radius: 18px;
          overflow: hidden;
        }

        div[data-testid="stExpander"] details summary {
          background: rgba(20, 28, 48, 0.62);
          border-radius: 18px;
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

        .me-mobile-note {
          color: #aeb8cc;
          font-size: .86rem;
          margin-top: .2rem;
          margin-bottom: .35rem;
        }


        /* Aktiver Reiter klar hervorheben */
        div[role="radiogroup"] label:has(input:checked),
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] {
          background: linear-gradient(180deg, rgba(124,156,255,.32), rgba(78,112,214,.38)) !important;
          border: 1px solid rgba(162, 186, 255, 0.65) !important;
          box-shadow: 0 8px 22px rgba(124,156,255,.22) !important;
          transform: translateY(-1px);
        }

        div[role="radiogroup"] label:has(input:checked) *,
        div[role="radiogroup"] label[data-baseweb="radio"][aria-checked="true"] * {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          font-weight: 800 !important;
        }

        div[role="radiogroup"] label:hover {
          border-color: rgba(124,156,255,.34) !important;
        }


        @media (max-width: 900px) {
          .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 0.35rem !important;
          }

          h1 { font-size: 2.2rem !important; }
          h2 { font-size: 1.6rem !important; }
          h3 { font-size: 1.3rem !important; }

          section[data-testid="stSidebar"] {
            display: none !important;
          }

          div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.45rem;
            padding: 0.45rem;
            border-radius: 18px;
          }

          div[role="radiogroup"] label {
            width: 100% !important;
            min-height: 48px;
            padding: 0.45rem 0.5rem;
            border-radius: 14px;
            text-align: center;
            font-size: 0.92rem;
            line-height: 1.1;
          }

          [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
            width: 100% !important;
          }

          div[data-testid="stMetric"] {
            padding: 0.8rem 0.9rem;
            border-radius: 18px;
          }

          .stButton > button,
          .stDownloadButton > button,
          .stLinkButton > a,
          div[data-testid="stForm"] button {
            width: 100%;
            min-height: 3rem;
          }

          textarea, input, select {
            font-size: 16px !important;
          }
        }

        @media (max-width: 560px) {
          div[role="radiogroup"] {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
