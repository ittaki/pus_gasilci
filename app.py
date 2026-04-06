import streamlit as st
import pandas as pd
import datetime
import requests
import xml.etree.ElementTree as ET

st.set_page_config(
    page_title="Gasilski Operativni Center",
    page_icon="🚒",
    layout="wide"
)

page = st.sidebar.selectbox(
    "Select page",
    ["Main", "Floods"]
)

if page == "Main":
    # FUNKCIJA ZA ARSO PODATKE
    def get_arso_data():
        url = "https://www.arso.gov.si/xml/vreme/podatki/dz_zadnji.xml"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for postaja in root.findall('metPod'):
                    # Popravljen pogoj za iskanje postaje
                    if postaja.find('domain_title').text in ['LJUBLJANA_BEZIGRAD', 'Ljubljana']:
                        return {
                            "temp": postaja.find('t').text, 
                            "vlaga": postaja.find('rh').text, 
                            "veter": postaja.find('ff_val').text, 
                            "opis": postaja.find('nn_decode_short').text
                        }
            return None
        except Exception as e:
            return None
    
    # --- FUNKCIJA ZA PROMETNE INFORMACIJE (OPSI/Promet.si) ---
    def get_traffic_data():
        # RSS vir za izredne dogodke na cestah
        url = "https://www.promet.si/dc/rss.izredni.dogodki.sl"
        try:
            response = requests.get(url, timeout=10)
            # Preprosto preberemo besedilo (za demo namen)
            # V pravi aplikaciji bi tukaj parzali RSS feed
            return response.status_code == 200
        except:
            return False
    
    # --- NASLOV ---
    st.title("🚒 Gasilski Operativni Center")
    st.markdown("---")
    
    # --- STRANSKA VRSTICA ---
    with st.sidebar:
        st.header("Status Enote")
        st.success("Enota: Ljubljana-Mesto")
        if st.button("🚨 SPROŽI ALARM"):
            st.error("ALARM POSLAN!")
        
        st.divider()
        st.subheader("Hitri ARSO vpogled")
        vreme = get_arso_data()
        if vreme:
            st.metric("Temp", f"{vreme['temp']} °C")
            st.metric("Veter", f"{vreme['veter']} m/s")
        else:
            st.warning("Podatki ARSO trenutno niso na voljo.")
    
    # --- GLAVNA RAZPOREDITEV ---
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📍 GURS Interaktivna mapa")
        # Glavno okno za delo s parcelami in hidranti
        st.components.v1.iframe("https://ipi.eprostor.gov.si/jv/", height=800, scrolling=True)
    
    with col2:
        st.subheader("📈 ARSO Vremenska napoved")
        arso_lj_url = "https://vreme.arso.gov.si/napoved/Ljubljana/graf"
        st.components.v1.iframe(arso_lj_url, height=400, scrolling=True)
        
        st.divider()
    
        st.subheader("🛣️ Stanje na cestah")
        # promet.si
        st.info("Povezava do uradnih podatkov:")
        st.link_button("Odpri Promet.si (Izredni dogodki)", "https://www.promet.si/sl/prometni-zemljevid")
        
        # Google Maps 
        google_traffic_url = "https://www.google.com/maps/embed?pb=!1m14!1m12!1m3!1d44324.437651667!2d14.5058!3d46.0569!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!5e0!3m2!1ssl!2ssi!4v1700000000000!5m2!1ssl!2ssi&layer=t"
        st.components.v1.iframe(google_traffic_url, height=400)
    
        st.divider()
        
        st.subheader("📋 Dnevni nalog")
        st.info("Prioriteta: Pregled hidrantnega omrežja v coni Šiška.")
        st.checkbox("Pregled vozil GVC 16/25", value=True)
        st.checkbox("Preverjanje radijskih zvez", value=False)
    
    # Dodatek spodaj za polno širino
    st.markdown("---")
    st.subheader("ℹ️ Viri podatkov")
    st.write("Aplikacija združuje GURS (Prostorski portal), ARSO (Vremenske storitve) in OPSI/Promet.si (Stanje na cestah).")
elif page == "Floods":
    st.title("TEST PAGE")
    st.write("If you see this, app.py is controlling the Floods page.")
