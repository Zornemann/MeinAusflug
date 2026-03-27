from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0e1117;
          --card: #151a21;
          --card-2: #1b2230;
          --text: #f4f7fb;
          --muted: #b7c0cf;
          --border: #2a3342;
          --accent: #6ea8fe;
          --accent-2: #8bb9ff;
          --success: #8fe3b0;
          --warning: #ffd27d;
        }

        html, body, [class*="css"] {
          color: var(--text);
        }

        .stApp {
          background: var(--bg);
        }

        .block-container {
          padding-top: 1rem;
          padding-bottom: 4rem;
          max-width: 1050px;
        }

        h1, h2, h3, h4, h5, h6, p, span, label, div {
          color: var(--text);
        }

        small, .stCaption, .stMarkdown p em {
          color: var(--muted) !important;
        }

        section[data-testid="stSidebar"] {
          background: #11161d;
          border-right: 1px solid var(--border);
        }

        div[data-testid="stMetric"] {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 0.8rem 0.9rem;
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
          border-radius: 14px !important;
        }

        input::placeholder,
        textarea::placeholder {
          color: #98a4b8 !important;
          opacity: 1 !important;
        }

        textarea, input {
          font-size: 1rem !important;
        }

        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
          border-radius: 14px !important;
          border: 1px solid var(--border) !important;
          background: var(--card-2) !important;
          color: var(--text) !important;
          min-height: 2.8rem;
          font-weight: 600;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stLinkButton > a:hover {
          border-color: var(--accent) !important;
          color: white !important;
        }

        button[kind="primary"] {
          background: var(--accent) !important;
          color: #08111f !important;
        }

        div[role="radiogroup"] {
          gap: 0.4rem;
          flex-wrap: wrap;
        }

        div[role="radiogroup"] label {
          background: var(--card);
          border: 1px solid var(--border);
          border-radius: 999px;
          padding: 0.3rem 0.8rem;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.35rem;
          flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
          height: auto;
          min-height: 42px;
          border-radius: 999px;
          padding: 0.55rem 0.9rem;
          background: var(--card);
          color: var(--text);
          border: 1px solid var(--border);
        }

        .stTabs [aria-selected="true"] {
          background: var(--accent) !important;
          color: #08111f !important;
        }

        .stAlert {
          border-radius: 16px;
        }

        .stMarkdown code {
          background: #121821;
          color: #d5e6ff;
        }

        iframe {
          border-radius: 18px !important;
        }

        @media (max-width: 768px) {
          .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
            padding-top: 0.5rem;
            padding-bottom: 5rem;
          }

          h1 {
            font-size: 1.55rem !important;
            line-height: 1.2;
          }

          h2 {
            font-size: 1.2rem !important;
          }

          h3 {
            font-size: 1.05rem !important;
          }

          p, label, span, div {
            font-size: 0.98rem;
          }

          div[data-testid="stMetric"] {
            padding: 0.65rem 0.7rem;
          }

          div[data-testid="stMetricValue"] {
            font-size: 1.05rem !important;
          }

          .stTabs [data-baseweb="tab"] {
            min-height: 38px;
            padding: 0.45rem 0.75rem;
            font-size: 0.92rem;
          }

          .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            width: 100%;
            min-height: 2.9rem;
            font-size: 0.98rem;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
