import streamlit as st

st.set_page_config(page_title="Floods", layout="wide")

st.title("🌊 Flood Monitoring – Ajna")
st.markdown("---")

# --- TOP METRICS ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Water Level", "1.8 m", "+0.2 m")

with col2:
    st.metric("Rainfall (24h)", "42 mm", "+5 mm")

with col3:
    st.metric("Risk Level", "HIGH")

st.markdown("---")

# --- MAP / MAIN AREA ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Flood Map")
    st.components.v1.iframe(
        "https://www.google.com/maps?q=Ljubljana&output=embed",
        height=500
    )

with col2:
    st.subheader("⚠️ Alerts")
    st.warning("River Sava rising rapidly")
    st.error("Flood risk in northern districts")
    st.info("Evacuation readiness recommended")

st.markdown("---")

# --- NOTES / ACTIONS ---
st.subheader("📋 Actions")

st.checkbox("Check drainage systems")
st.checkbox("Deploy pumps")
st.checkbox("Notify emergency teams")

st.markdown("---")

st.write("Data will later be connected to real flood monitoring systems.")
