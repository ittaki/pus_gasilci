import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import pandas as pd
from io import StringIO

FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Europe_7d.csv"
SLO = {"lat_min":45.4,"lat_max":46.9,"lon_min":13.3,"lon_max":16.6}

@st.cache_data(ttl=3600)
def fetch_fires():
    try:
        r = requests.get(FIRMS_URL, timeout=30)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"
        if "latitude" not in r.text:
            return pd.DataFrame(), "Nema CSV podataka"
        df = pd.read_csv(StringIO(r.text))
        df = df[
            (df["latitude"]>=SLO["lat_min"])&(df["latitude"]<=SLO["lat_max"])&
            (df["longitude"]>=SLO["lon_min"])&(df["longitude"]<=SLO["lon_max"])
        ].reset_index(drop=True)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def frp_color(frp):
    try: f=float(frp)
    except: return "gray"
    if f>=50: return "red"
    elif f>=10: return "orange"
    else: return "yellow"

def render():
    st.title("Aktivni pozari - FIRMS (7 dni)")
    st.caption(f"NASA FIRMS VIIRS C2 Europa | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    with st.spinner("Nalagam pozarne podatke..."):
        df, err = fetch_fires()
    c1,c2,c3 = st.columns(3)
    c1.metric("Zaznani pozari (SLO okolica)", len(df) if err is None else "N/A")
    if err is None and len(df)>0:
        if "frp" in df.columns: c2.metric("Max FRP (MW)", f"{df['frp'].max():.1f}")
        if "acq_date" in df.columns: c3.metric("Zadnji zaznani", df["acq_date"].max())
    if err: st.error(f"Napaka: {err}")
    st.subheader("Karta pozarov")
    m = folium.Map(location=[46.1,14.8], zoom_start=7, tiles="OpenStreetMap")
    if err is None and len(df)>0:
        for _, row in df.iterrows():
            color = frp_color(row.get("frp",0))
            popup = (f"<b>Datum:</b> {row.get('acq_date','?')}<br>"
                     f"<b>FRP:</b> {row.get('frp','?' )} MW<br>"
                     f"<b>Zaupanje:</b> {row.get('confidence','?')}")
            folium.CircleMarker(
                location=[row["latitude"],row["longitude"]],
                radius=8, color=color, fill=True, fill_opacity=0.8,
                popup=folium.Popup(popup, max_width=250),
                tooltip=f"FRP: {row.get('frp','?' )} MW"
            ).add_to(m)
        st.success(f"{len(df)} pozarnih tock")
    elif err is None:
        st.success("Ni aktivnih pozarov v SLO obmocju (7 dni)")
        folium.Marker([46.1,14.8], popup="Ni pozarov",
            icon=folium.Icon(color="green",icon="check")).add_to(m)
    st_folium(m, width=800, height=480)
    if err is None and len(df)>0:
        st.subheader("Tabela")
        cols=[c for c in ["acq_date","acq_time","latitude","longitude","frp","confidence","satellite"] if c in df.columns]
        st.dataframe(df[cols].sort_values("acq_date",ascending=False),use_container_width=True)

if __name__ == "__main__":
    render()
