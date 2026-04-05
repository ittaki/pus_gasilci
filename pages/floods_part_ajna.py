import streamlit as st


def render():
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .main-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #475569;
            font-size: 1rem;
            margin-bottom: 1.2rem;
        }

        .section-card {
            background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
            border: 1px solid #dbeafe;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
        }

        .info-card {
            background: #f8fafc;
            border-left: 6px solid #2563eb;
            border-radius: 12px;
            padding: 16px;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .archive-card {
            background: #fff7ed;
            border-left: 6px solid #ea580c;
            border-radius: 12px;
            padding: 16px;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .small-label {
            font-size: 0.85rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }

        .big-text {
            font-size: 1.2rem;
            font-weight: 700;
            color: #0f172a;
        }
    </style>
    """, unsafe_allow_html=True)

    if "floods_mode" not in st.session_state:
        st.session_state.floods_mode = "Current Information"

    st.markdown("<div class='main-title'>🌊 Floods</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Operational floods workspace</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

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

    if mode == "Current Information":
        st.markdown("""
        <div class='section-card'>
            <div class='small-label'>Current mode</div>
            <div class='big-text'>Live operational information</div>
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
                <div class='info-card'>
                    <div class='small-label'>Current alerts</div>
                    <div class='big-text'>Live warnings and notices</div>
                    <p style='margin-top:8px; color:#334155;'>
                        This section will later display real-time flood alerts, weather warnings,
                        emergency notices, and operational updates for the selected area.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.warning("Placeholder: live alerts for the selected area will appear here.")
                st.info("Placeholder: additional current-status details will appear here.")

            with col2:
                st.markdown("""
                <div class='info-card'>
                    <div class='small-label'>Area overview</div>
                    <div class='big-text'>Regional operational view</div>
                    <p style='margin-top:8px; color:#334155;'>
                        This section will later contain the map, water levels, rainfall,
                        infrastructure status, and other live area-specific information.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                st.write(f"Selected area: **{area}**")
                st.write("Placeholder: map and metrics for this area will appear here.")

    elif mode == "Historical Information":
        st.markdown("""
        <div class='section-card'>
            <div class='small-label'>Historical mode</div>
            <div class='big-text'>Archive and reference materials</div>
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

            st.markdown("""
            <div class='archive-card'>
                <div class='small-label'>Historical workspace</div>
                <div class='big-text'>Archived information view</div>
                <p style='margin-top:8px; color:#334155;'>
                    This section will later contain archived flood events, stored reports,
                    historical maps, notes, and supporting materials.
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.write(f"Selected archive type: **{history_type}**")
            st.write("Placeholder: archived resources will appear here.")
