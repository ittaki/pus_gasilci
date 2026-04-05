import streamlit as st

st.set_page_config(page_title="Floods", page_icon="🌊", layout="wide")

st.title("🌊 Floods")
st.caption("Operational floods workspace")

st.markdown("---")

mode = st.radio(
    "Select mode",
    ["Current Information", "Historical Information"],
    horizontal=True,
)

st.markdown("---")

if mode == "Current Information":
    st.subheader("Current Information")

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

        st.markdown("### Live area workspace")
        st.write("This is where current flood information for the selected area will appear.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Current alerts")
            st.write("Placeholder for live warnings, flood notices, and emergency updates.")

        with col2:
            st.markdown("#### Area overview")
            st.write("Placeholder for map, water levels, weather, and operational status.")

elif mode == "Historical Information":
    st.subheader("Historical Information")

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

        st.markdown("### Historical workspace")
        st.write("This is where archived flood information and reference resources will appear.")
