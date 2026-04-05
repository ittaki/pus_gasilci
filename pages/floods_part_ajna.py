import streamlit as st


def render():
    if "floods_mode" not in st.session_state:
        st.session_state.floods_mode = None

    mode = st.session_state.floods_mode

    if mode == "Archived Information":
        page_background = """
        .stApp {
            background: linear-gradient(180deg, #6082B6 0%, #4f6fa3 100%);
        }
        """
        title_color = "#f8fafc"
        subtitle_color = "#eef2ff"
        divider_color = "rgba(255, 255, 255, 0.20)"
    else:
        page_background = """
        .stApp {
            background: linear-gradient(180deg, #eaf4fb 0%, #dfeef8 100%);
        }
        """
        title_color = "#0f172a"
        subtitle_color = "#475569"
        divider_color = "rgba(148, 163, 184, 0.22)"

    st.markdown(f"""
    <style>
        {page_background}

        html, body, [class*="css"] {{
            font-family: "Inter", "Segoe UI", sans-serif;
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}

        .main-title {{
            font-size: 2.6rem;
            font-weight: 800;
            color: {title_color};
            margin-bottom: 0.25rem;
        }}

        .subtitle {{
            color: {subtitle_color};
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }}

        .mode-card {{
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 12px;
        }}

        .landing-card {{
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(191, 219, 254, 0.75);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }}

        .current-card {{
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }}

        .history-card {{
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #f8fafc;
            backdrop-filter: blur(8px);
            box-shadow: 0 12px 30px rgba(31, 41, 55, 0.22);
        }}

        .small-label {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 700;
        }}

        .history-card .small-label {{
            color: #f1f5f9;
            opacity: 0.88;
        }}

        .big-text {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }}

        .history-card .big-text {{
            color: #ffffff;
            font-size: 1.3rem;
            font-weight: 800;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
        }}

        .history-card p,
        .history-card span,
        .history-card div {{
            color: #f8fafc;
        }}

        .wave-wrap {{
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,0.45) 0%, rgba(224,242,254,0.45) 100%);
            border: 1px solid rgba(191, 219, 254, 0.9);
            box-shadow: 0 12px 32px rgba(14, 116, 144, 0.08);
            margin-bottom: 20px;
        }}

        .wave-wrap::before,
        .wave-wrap::after {{
            content: "";
            position: absolute;
            left: -10%;
            width: 120%;
            height: 140px;
            border-radius: 45%;
            background: rgba(56, 189, 248, 0.12);
        }}

        .wave-wrap::before {{
            bottom: -70px;
        }}

        .wave-wrap::after {{
            bottom: -95px;
            background: rgba(14, 165, 233, 0.08);
        }}

        div[data-testid="stButton"] > button {{
            border-radius: 14px;
            height: 3.2rem;
            font-weight: 700;
            border: 1px solid #dbeafe;
        }}

        div[data-testid="stSelectbox"] > div {{
            border-radius: 12px;
        }}

        hr {{
            border-color: {divider_color};
        }}

        [data-testid="stInfo"] {{
            border-radius: 14px;
        }}

        [data-testid="stSuccess"] {{
            border-radius: 14px;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="wave-wrap">
        <div class="main-title">🌊 Floods</div>
        <div class="subtitle">Operational floods workspace</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Select mode")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📡 Current Information", use_container_width=True):
            st.session_state.floods_mode = "Current Information"
            st.rerun()

    with col2:
        if st.button("🗂️ Archived Information", use_container_width=True):
            st.session_state.floods_mode = "Archived Information"
            st.rerun()

    mode = st.session_state.floods_mode

    st.markdown("---")

    if mode is None:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div class="mode-card landing-card">
                <div class="small-label">Live operations</div>
                <div class="big-text">Current Information</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="mode-card landing-card">
                <div class="small-label">Archive workspace</div>
                <div class="big-text">Archived Information</div>
            </div>
            """, unsafe_allow_html=True)

        st.info("Choose a mode to continue.")

    elif mode == "Current Information":
        st.markdown("""
        <div class="mode-card current-card">
            <div class="small-label">Current mode</div>
            <div class="big-text">Current flood monitoring and area-specific updates.</div>
        </div>
        """, unsafe_allow_html=True)

        area = st.selectbox(
            "Select area",
            [
                "Ljubljana",
                "Maribor",
                "Celje",
                "Kranj",
                "Koper",
                "Novo Mesto",
                "Murska Sobota",
                "Nova Gorica",
            ],
            index=None,
            placeholder="Choose an area",
        )

        st.markdown("---")

        if area is None:
            st.info("Select an area to continue.")
        else:
            st.success(f"Area selected: {area}")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("""
                <div class="mode-card current-card">
                    <div class="small-label">Current alerts</div>
                    <div class="big-text">Live warnings and notices</div>
                </div>
                """, unsafe_allow_html=True)

                st.warning("Placeholder: live alerts for the selected area will appear here.")

            with col2:
                st.markdown("""
                <div class="mode-card current-card">
                    <div class="small-label">Area overview</div>
                    <div class="big-text">Regional operational view</div>
                </div>
                """, unsafe_allow_html=True)

                st.write(f"Selected area: **{area}**")
                st.write("Placeholder: map and metrics for this area will appear here.")

    elif mode == "Archived Information":
        st.markdown("""
        <div class="mode-card history-card">
            <div class="small-label">Archived mode</div>
            <div class="big-text">Archive of past events, documents, reports, maps, and historical resources.</div>
        </div>
        """, unsafe_allow_html=True)

        history_type = st.selectbox(
            "Select archive type",
            [
                "Past flood events",
                "Reports",
                "Maps",
                "Operational notes",
                "Reference materials",
            ],
            index=None,
            placeholder="Choose a historical category",
        )

        st.markdown("---")

        if history_type is None:
            st.info("Select a historical category to continue.")
        else:
            st.success(f"Archive selected: {history_type}")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("""
                <div class="mode-card history-card">
                    <div class="small-label">Archived workspace</div>
                    <div class="big-text">Archived information view</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="mode-card history-card">
                    <div class="small-label">Selected archive</div>
                    <div class="big-text">Resource category</div>
                </div>
                """, unsafe_allow_html=True)

                st.write(f"Selected archive type: **{history_type}**")
                st.write("Placeholder: archived resources will appear here.")
