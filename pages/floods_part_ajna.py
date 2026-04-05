import streamlit as st


def render():
    if "floods_mode" not in st.session_state:
        st.session_state.floods_mode = None

    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(180deg, #f8fbff 0%, #eef6fb 100%);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        .main-title {
            font-size: 2.6rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }

        .subtitle {
            color: #475569;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        .mode-card {
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 12px;
        }

        .landing-card {
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(6px);
        }

        .current-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }

        .history-card {
            background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
            border: 1px solid #334155;
            color: #f8fafc;
            box-shadow: 0 10px 30px rgba(2, 6, 23, 0.35);
        }

        .small-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 700;
        }

        .history-card .small-label {
            color: #94a3b8;
        }

        .big-text {
            font-size: 1.25rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }

        .history-card .big-text {
            color: #f8fafc;
        }

        .body-text {
            color: #334155;
            line-height: 1.6;
        }

        .history-card .body-text {
            color: #cbd5e1;
        }

        .wave-wrap {
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(239,246,255,0.92) 100%);
            border: 1px solid rgba(191, 219, 254, 0.8);
            box-shadow: 0 12px 32px rgba(14, 116, 144, 0.08);
            margin-bottom: 20px;
        }

        .wave-wrap::before,
        .wave-wrap::after {
            content: "";
            position: absolute;
            left: -10%;
            width: 120%;
            height: 140px;
            border-radius: 45%;
            background: rgba(56, 189, 248, 0.12);
        }

        .wave-wrap::before {
            bottom: -70px;
        }

        .wave-wrap::after {
            bottom: -95px;
            background: rgba(14, 165, 233, 0.08);
        }

        div[data-testid="stButton"] > button {
            border-radius: 14px;
            height: 3.2rem;
            font-weight: 700;
            border: 1px solid #dbeafe;
        }

        div[data-testid="stSelectbox"] > div {
            border-radius: 12px;
        }

        .section-spacer {
            height: 8px;
        }
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

    with col2:
        if st.button("🗂️ Historical Information", use_container_width=True):
            st.session_state.floods_mode = "Historical Information"

    mode = st.session_state.floods_mode

    st.markdown("---")

    if mode is None:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div class="mode-card landing-card">
                <div class="small-label">Live operations</div>
                <div class="big-text">Current Information</div>
                <div class="body-text">
                    Use this mode for real-time area-based monitoring, alerts, and operational awareness.
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="mode-card landing-card">
                <div class="small-label">Archive workspace</div>
                <div class="big-text">Historical Information</div>
                <div class="body-text">
                    Use this mode to browse past flood events, reports, maps, notes, and other archived resources.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.info("Choose a mode to continue.")

    elif mode == "Current Information":
        st.markdown("""
        <div class="mode-card current-card">
            <div class="small-label">Current mode</div>
            <div class="big-text">Live operational information</div>
            <div class="body-text">
                Clean live workspace for current flood monitoring and area-specific updates.
            </div>
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
                    <div class="body-text">
                        This section will later display real-time flood alerts, weather warnings,
                        emergency notices, and operational updates for the selected area.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.warning("Placeholder: live alerts for the selected area will appear here.")

            with col2:
                st.markdown("""
                <div class="mode-card current-card">
                    <div class="small-label">Area overview</div>
                    <div class="big-text">Regional operational view</div>
                    <div class="body-text">
                        This section will later contain the map, water levels, rainfall,
                        infrastructure status, and other live area-specific information.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.write(f"Selected area: **{area}**")
                st.write("Placeholder: map and metrics for this area will appear here.")

    elif mode == "Historical Information":
        st.markdown("""
        <div class="mode-card history-card">
            <div class="small-label">Historical mode</div>
            <div class="big-text">Archive and reference materials</div>
            <div class="body-text">
                Dark archive workspace for past events, documents, reports, maps, and historical resources.
            </div>
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
                    <div class="small-label">Historical workspace</div>
                    <div class="big-text">Archived information view</div>
                    <div class="body-text">
                        This section will later contain archived flood events, stored reports,
                        historical maps, notes, and supporting materials.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="mode-card history-card">
                    <div class="small-label">Selected archive</div>
                    <div class="big-text">Resource category</div>
                    <div class="body-text">
                        Use this area to browse structured archive content for the selected category.
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.write(f"Selected archive type: **{history_type}**")
                st.write("Placeholder: archived resources will appear here.")
