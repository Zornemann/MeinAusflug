import streamlit as st

def apply_theme():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    mode = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    st.session_state.dark_mode = mode

    if mode:
        bg = "#0e1117"
        text = "#ffffff"
        card = "#1c1f26"
        border = "rgba(255,255,255,0.08)"
    else:
        bg = "#ffffff"
        text = "#000000"
        card = "#f8f9fa"
        border = "rgba(0,0,0,0.08)"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg};
            color: {text};
        }}

        .stButton button {{
            border-radius: 10px;
        }}

        div[data-testid="stVerticalBlock"] {{
            border-color: {border};
        }}

        @media (max-width: 768px) {{
            .stButton button {{
                width: 100%;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ Strong "no translate" for Chrome/Google Translate
    st.components.v1.html(
        """
        <script>
          (function () {
            try {
              const doc = window.parent.document;

              doc.documentElement.lang = "de";
              doc.documentElement.setAttribute("translate", "no");
              doc.documentElement.classList.add("notranslate");

              if (doc.body) {
                doc.body.setAttribute("translate", "no");
                doc.body.classList.add("notranslate");
              }

              const head = doc.head;
              if (head && !head.querySelector('meta[name="google"][content="notranslate"]')) {
                const m = doc.createElement("meta");
                m.name = "google";
                m.content = "notranslate";
                head.appendChild(m);
              }
            } catch(e) {}
          })();
        </script>
        """,
        height=0,
    )