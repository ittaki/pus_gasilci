import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os

NASA_FIRMS_API_KEY = os.environ.get("FIRMS_API_KEY", "fe0ebf60ed55aa1cd2f70abb9ddb2978")

# Bbox za Sloveniju + šira okolica
SLO_BBOX = {"lat_min": 45.0, "lat_max": 47.5, "lon_min": 12.5, "lon_max": 17.5}

FIRMS_URL = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{NASA_FIRMS_API_KEY}/VIIRS_SNPP_NRT/"
    f"{SLO_BBOX['lon_min']},{SLO_BBOX['lat_min']},"
    f"{SLO_BBOX['lon_max']},{SLO_BBOX['lat_max']}/2"
)

@st.cache_data(ttl=3600)
def fetch_firms_data():
    try:
        r = requests.get(FIRMS_URL, timeout=15)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"
        if "latitude" not in r.text:
            return pd.DataFrame(), None
        from io import StringIO
        df = pd.read_csv(StringIO(r.text))
        return df, None
    except requests.Timeout:
        return pd.DataFrame(), "Timeout pri NASA FIRMS"
    except Exception as e:
        return pd.DataFrame(), str(e)

def frp_color(frp):
    try:
        f = float(frp)
    except (ValueError, TypeError):
        return "gray"
    if f >= 50:
        return "red"
    elif f >= 10:
        return "orange"
    else:
        return "yellow"

def render():
    st.title("🔥 Aktivni požari NASA FIRMS")
    st.caption(
        f"Vir: NASA FIRMS VIIRS · Zadnja 2 dni · "
        f"Posodobljeno: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    df, err = fetch_firms_data()

    if err:
        st.error(f"Napaka pri nalaganju podatkov: {err}")
        return

    # KPI metrike
    col1, col2, col3 = st.columns(3)
    col1.metric("Zaznani požari (48h)", len(df))

    if not df.empty and "frp" in df.columns:
        col2.metric("Max intenziteta (FRP)", f"{df['frp'].max():.1f} MW")
        col3.metric("Zadnja zaznava", str(df["acq_time"].max()) if "acq_time" in df.columns else "N/A")
    else:
        col2.metric("Max intenziteta (FRP)", "N/A")
        col3.metric("Zadnja zaznava", "N/A")

    st.divider()

    # Folium mapa
    st.subheader("🗺️ Karta požarov")
    m = folium.Map(location=[46.1, 14.8], zoom_start=7, tiles="CartoDB positron")

    if df.empty:
        st.success("✅ Ni aktivnih požarov v zadnjih 48 urah v okolici Slovenije.")
    else:
        st.warning(f"⚠️ Zaznanih {len(df)} požarnih točk v zadnjih 48 urah!")
        for _, row in df.iterrows():
            frp = row.get("frp", 0)
            lat = row.get("latitude")
            lon = row.get("longitude")
            if pd.isna(lat) or pd.isna(lon):
                continue
            folium.CircleMarker(
                location=[lat, lon],
                radius=max(5, float(frp or 0) / 8),
                color=frp_color(frp),
                fill_color=frp_color(frp),
                fill=True,
                fill_opacity=0.8,
                popup=folium.Popup(
                    f"<b>🔥 Požar</b><br>"
                    f"FRP: {frp} MW<br>"
                    f"Datum: {row.get('acq_date', '?')}<br>"
                    f"Čas: {row.get('acq_time', '?')}<br>"
                    f"Zaupanje: {row.get('confidence', '?')}",
                    max_width=220
                ),
                tooltip=f"FRP: {frp} MW — {row.get('acq_date', '')}"
            ).add_to(m)

    # legenda
    legend = """
    <div style="position:fixed;bottom:30px;left:30px;background:white;
                padding:10px;border-radius:8px;font-size:12px;z-index:1000;
                border:1px solid #ccc;box-shadow:2px 2px 6px rgba(0,0,0,0.2)">
        <b>Intenziteta (FRP)</b><br>
        🔴 ≥ 50 MW &nbsp; 🟠 ≥ 10 MW &nbsp; 🟡 &lt; 10 MW
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))
    st_folium(m, width="100%", height=500)

    #Tabela
    if not df.empty:
        st.divider()
        st.subheader("📋 Podrobnosti")
        cols_show = ["latitude", "longitude", "acq_date", "acq_time", "frp", "confidence", "bright_ti4"]
        st.dataframe(
            df[[c for c in cols_show if c in df.columns]],
            use_container_width=True,
            hide_index=True
        )

render()