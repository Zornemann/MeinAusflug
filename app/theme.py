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
          --card-2: rgba(27, 38, 66, 0.92);
          --text: #f7f9fc;
          --muted: #aeb8cc;
          --border: rgba(130, 153, 196, 0.18);
          --accent: #7c9cff;
          --accent-2: #5eead4;
          --shadow: 0 10px 30px rgba(0,0,0,.22);
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(124,156,255,.16), transparent 28%),
            radial-gradient(circle at top right, rgba(94,234,212,.12), transparent 24%),
            linear-gradient(180deg, #0b1020 0%, #0f172a 100%);
          color: var(--text);
        }

        html, body, [class*="css"] {
          color: var(--text);
        }

        header[data-testid="stHeader"] {
          background: transparent !important;
          height: 0 !important;
        }

        div[data-testid="stToolbar"] {
          top: 0.35rem;
          right: 0.5rem;
        }

        div[data-testid="stDecoration"] {
          display: none !important;
        }

        .block-container {
          max-width: 1120px;
          padding-top: 0.2rem;
          padding-bottom: 5rem;
        }

        h1, h2, h3, h4, h5, h6, p, span, label, div {
          color: var(--text);
        }

        section[data-testid="stSidebar"] {
          background: rgba(10, 15, 28, 0.96);
          border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] div {
          color: var(--text);
        }

        div[data-testid="stMetric"] {
          background: var(--card);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border);
          box-shadow: var(--shadow);
          border-radius: 20px;
          padding: 0.95rem 1rem;
        }

        div[data-testid="stMetricLabel"] {
          color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
          color: var(--text);
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

        /* Selectbox / Multiselect: Wert, Placeholder, Pfeil und Dropdown lesbar machen */
        div[data-baseweb="select"] * {
          color: var(--text) !important;
        }

        div[data-baseweb="select"] input {
          -webkit-text-fill-color: var(--text) !important;
          color: var(--text) !important;
          caret-color: var(--text) !important;
        }

        div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
          color: var(--text) !important;
        }

        div[data-baseweb="select"] svg {
          fill: var(--text) !important;
          color: var(--text) !important;
        }

        /* BaseWeb Dropdown-Menüs werden oft in ein Portal gerendert.
           Deshalb die Menü-Container und Einträge separat sehr explizit stylen. */
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {
          color: #f7f9fc !important;
        }

        ul[data-baseweb="menu"],
        div[data-baseweb="menu"],
        div[role="listbox"],
        [data-testid="stSelectboxVirtualDropdown"],
        [data-testid="stMultiSelectVirtualDropdown"] {
          background: rgba(17, 24, 43, 0.99) !important;
          color: #f7f9fc !important;
          border: 1px solid rgba(130, 153, 196, 0.18) !important;
          border-radius: 16px !important;
          box-shadow: 0 10px 30px rgba(0,0,0,.22) !important;
        }

        ul[data-baseweb="menu"] li,
        ul[data-baseweb="menu"] li * ,
        div[data-baseweb="menu"] [role="option"],
        div[data-baseweb="menu"] [role="option"] *,
        div[role="listbox"] [role="option"],
        div[role="listbox"] [role="option"] *,
        [data-testid="stSelectboxVirtualDropdown"] li,
        [data-testid="stSelectboxVirtualDropdown"] li *,
        [data-testid="stMultiSelectVirtualDropdown"] li,
        [data-testid="stMultiSelectVirtualDropdown"] li * {
          background: transparent !important;
          color: #f7f9fc !important;
          -webkit-text-fill-color: #f7f9fc !important;
        }

        ul[data-baseweb="menu"] li:hover,
        div[data-baseweb="menu"] [role="option"]:hover,
        div[role="listbox"] [role="option"]:hover,
        [data-testid="stSelectboxVirtualDropdown"] li:hover,
        [data-testid="stMultiSelectVirtualDropdown"] li:hover {
          background: rgba(124,156,255,.18) !important;
        }

        ul[data-baseweb="menu"] li[aria-selected="true"],
        div[data-baseweb="menu"] [role="option"][aria-selected="true"],
        div[role="listbox"] [role="option"][aria-selected="true"],
        [data-testid="stSelectboxVirtualDropdown"] li[aria-selected="true"],
        [data-testid="stMultiSelectVirtualDropdown"] li[aria-selected="true"] {
          background: rgba(124,156,255,.26) !important;
          color: #ffffff !important;
        }

        div[role="listbox"] {
          background: rgba(17, 24, 43, 0.98) !important;
          border: 1px solid var(--border) !important;
          border-radius: 16px !important;
          box-shadow: var(--shadow) !important;
        }

        div[role="option"] {
          background: transparent !important;
          color: var(--text) !important;
        }

        div[role="option"]:hover {
          background: rgba(124,156,255,.16) !important;
        }

        /* Sidebar-Selectbox und Dropdowns stärker kontrastieren */
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
          background: linear-gradient(180deg, rgba(29, 42, 74, 0.98), rgba(20, 30, 53, 0.98)) !important;
          border: 1px solid rgba(130, 153, 196, 0.24) !important;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] div[data-baseweb="select"] span,
        section[data-testid="stSidebar"] div[data-baseweb="select"] input,
        section[data-testid="stSidebar"] div[data-baseweb="select"] div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
          color: #f8fbff !important;
          fill: #f8fbff !important;
          -webkit-text-fill-color: #f8fbff !important;
          font-weight: 600;
        }

        /* Geöffnete Dropdown-Liste */
        div[role="listbox"] [role="option"] {
          color: #f7f9fc !important;
          background: transparent !important;
          border-radius: 12px;
          margin: 0.15rem 0.3rem;
          padding-top: 0.45rem !important;
          padding-bottom: 0.45rem !important;
        }

        div[role="listbox"] [role="option"][aria-selected="true"] {
          background: rgba(124,156,255,.24) !important;
          color: #ffffff !important;
        }

        /* MultiSelect-Tags bei "Wer bringt es mit?" */
        div[data-baseweb="tag"] {
          background: rgba(124,156,255,.18) !important;
          border: 1px solid rgba(124,156,255,.35) !important;
          border-radius: 999px !important;
        }

        div[data-baseweb="tag"] span,
        div[data-baseweb="tag"] div,
        div[data-baseweb="tag"] svg {
          color: #f8fbff !important;
          fill: #f8fbff !important;
        }

        /* Placeholder in Selects lesbarer machen */
        div[data-baseweb="select"] input::placeholder,
        div[data-baseweb="select"] input::-webkit-input-placeholder {
          color: #b7c4e3 !important;
          -webkit-text-fill-color: #b7c4e3 !important;
          opacity: 1 !important;
        }

        input::placeholder,
        textarea::placeholder {
          color: #90a0bf !important;
          opacity: 1 !important;
        }

        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
          border-radius: 16px !important;
          border: 1px solid var(--border) !important;
          background: linear-gradient(180deg, rgba(33,47,80,0.95), rgba(21,30,50,0.95)) !important;
          color: var(--text) !important;
          min-height: 2.9rem;
          font-weight: 700;
          box-shadow: var(--shadow);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
          border-color: rgba(124,156,255,.55) !important;
          transform: translateY(-1px);
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

        .me-card {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 22px;
          padding: 1rem 1.05rem;
          box-shadow: var(--shadow);
          backdrop-filter: blur(8px);
          margin-bottom: .85rem;
        }

        .me-soft {
          color: var(--muted);
        }

        .stAlert, iframe, .element-container .stImage img {
          border-radius: 20px !important;
        }

        @media (max-width: 768px) {
          .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.4rem;
            padding-bottom: 5.5rem;
          }

          h1 {
            font-size: 1.55rem !important;
            line-height: 1.18;
            margin-bottom: 0.4rem !important;
          }

          div[role="radiogroup"] {
            top: 0.2rem;
            padding: 0.45rem;
            gap: 0.42rem;
            border-radius: 18px;
          }

          div[role="radiogroup"] label {
            min-height: 40px;
            padding: 0.3rem 0.8rem;
            font-size: 0.92rem;
          }

          .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            width: 100%;
          }

          div[data-testid="stMetric"] {
            padding: 0.7rem 0.8rem;
          }

          .me-card {
            padding: 0.85rem 0.9rem;
            border-radius: 18px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
