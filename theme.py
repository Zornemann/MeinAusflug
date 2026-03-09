import streamlit as st


def apply_theme():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    mode = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    st.session_state.dark_mode = mode

    if mode:
        bg = "#0e1117"
        text = "#ffffff"
        border = "rgba(255,255,255,0.08)"
    else:
        bg = "#ffffff"
        text = "#000000"
        border = "rgba(0,0,0,0.08)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {text};
            -webkit-tap-highlight-color: transparent;
        }}

        .stButton button, .stDownloadButton button {{
            border-radius: 10px;
            min-height: 44px;
        }}

        .stTextInput input, .stTextArea textarea, .stDateInput input, .stTimeInput input, .stNumberInput input {{
            min-height: 44px;
            font-size: 16px;
        }}

        div[data-testid="stVerticalBlock"] {{
            border-color: {border};
        }}

        [data-testid="stImage"] img {{
            border-radius: 12px;
        }}

        @media (max-width: 768px) {{
            .block-container {{
                padding-top: 1rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
                padding-bottom: 5rem;
            }}

            .stButton button, .stDownloadButton button {{
                width: 100%;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
