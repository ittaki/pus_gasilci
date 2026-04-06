import requests
import streamlit as st


def render():
    st.title("ARSO XML Debug")

    url = "https://www.arso.gov.si/xml/vode/hidro_podatki_dnevno_porocilo.xml"

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        st.success("XML loaded successfully")
        st.write("Status code:", response.status_code)

        st.subheader("First 3000 characters of XML")
        st.code(response.text[:3000])

    except Exception as e:
        st.error(f"Error loading XML: {e}")
