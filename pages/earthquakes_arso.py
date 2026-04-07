import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from bs4 import BeautifulSoup
from datetime import datetime

ARSO_URL = "https://potresi.arso.gov.si/"

# USGS FDSN pokriva Slovenijo i vraća koordinate za mapu
USGS_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson"
    "&minlongitude=13.3&maxlongitude=17.0"
    "&minlatitude=45.0&maxlatitude=47.5"
    "&limit=50"
    "&minmagnitude=0.5"
    "&orderby=time"
)

@st.cache_data(ttl=900)  # osvježi svaki 15 min
def fetch_arso_table():
    try:
        r = requests.get(ARSO_URL, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return pd.DataFrame(), "Tabela ni bila najdena"
        rows = []
        for tr in table.find_all("tr")[1:]:  # preskoči header
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cols) >= 4:
                # stolpci: datum, magnituda, intenziteta, lokacija, čutili
                rows.append({
                    "Datum/čas": cols[0] if len(cols) > 0 else "",
                    "Mag.": cols[1] if len(cols) > 1 else "",
                    "Int.": cols[2] if len(cols) > 2 else "",
                    "Lokacija": cols[3] if len(cols) > 3 else "",
                    "Čutili": cols[4] if len(cols) > 4 else "0",
                })
        return pd.DataFrame(rows), None
    except requests.Timeout:
        return pd.DataFrame(), "Timeout pri povezavi z ARSO"
    except Exception as e:
        return pd.DataFrame(), str(e)

@st.cache_data(ttl=900)
def fetch_usgs_map():
    try:
        r = requests.get(USGS_URL, timeout=30)
        data = r.json()
        quakes = []
        for f in data.get("features", []):
            p = f["properties"]
            coords = f["geometry"]["coordinates"]  # [lon, lat, depth]
            quakes.append({
                "lat": coords[1],
                "lon": coords[0],
                "depth": coords[2],
                "mag": p.get("mag", 0),
                "place": p.get("place", ""),
                "time": pd.to_datetime(p.get("time"), unit="ms").strftime("%d.%m.%Y %H:%M"),
            })
        return quakes, None
    except requests.Timeout:
        return [], "Timeout pri USGS"
    except Exception as e:
        return [], str(e)

def mag_color(mag):
    if mag is None:
        return "gray"
    try:
        m = float(mag)
    except (ValueError, TypeError):
        return "gray"
    if m >= 3.0:
        return "red"
    elif m >= 2.0:
        return "orange"
    else:
        return "green"

def render():
    st.title("🌍 Potresi ARSO")
    st.caption(f"Vir: ARSO potresi (zadnjih 30 dni) · Posodobljeno: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    df, err_arso = fetch_arso_table()
    quakes, err_usgs = fetch_usgs_map()

    #st.write(quakes)


    # ── KPI metrike
    col1, col2, col3 = st.columns(3)

    if not df.empty:
        col1.metric("Potresi (30 dni)", len(df))
        # filtriraj magnitude ≥ 2.0
        strong = df[df["Mag."].apply(
            lambda x: float(x) >= 2.0 if x.replace(",", ".").replace(".", "").isdigit() else False
        )]
        col2.metric("Mag. ≥ 2.0", len(strong))
        col3.metric("Zadnji potres", df["Datum/čas"].iloc[0] if len(df) > 0 else "N/A")
    else:
        col1.metric("Potresi (30 dni)", "N/A")

    if err_arso:
        st.warning(f"⚠️ ARSO tabela: {err_arso}")

    st.divider()

    # ── Folium mapa (USGS koordinate)
    st.subheader("🗺️ Karta potresov")
    if err_usgs:
        st.warning(f"⚠️ Mapa: {err_usgs}")
    else:
        m = folium.Map(location=[46.1, 14.8], zoom_start=8, tiles="CartoDB positron")
        for q in quakes:
            folium.CircleMarker(
                location=[q["lat"], q["lon"]],
                radius=max(4, float(q["mag"] or 0) * 3),
                color=mag_color(q["mag"]),
                #fill_color=mag_color(q["mag"]),
                fill=True,
                fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>Mag. {q['mag']}</b><br>"
                    f"{q['place']}<br>"
                    f"Globina: {q['depth']:.1f} km<br>"
                    f"{q['time']}",
                    max_width=220
                ),
                tooltip=f"Mag. {q['mag']} — {q['place']}"
            ).add_to(m)

        # legenda
        legend = """
        <div style="position:fixed;bottom:30px;left:30px;background:white;
                    padding:10px;border-radius:8px;font-size:12px;z-index:1000;
                    border:1px solid #ccc;">
            <b>Magnituda</b><br>
            🔴 ≥ 3.0 &nbsp; 🟠 ≥ 2.0 &nbsp; 🟢 &lt; 2.0
        </div>"""
        m.get_root().html.add_child(folium.Element(legend))
        st_folium(m, width="100%", height=500)

    st.divider()

    # ── ARSO tabela
    st.subheader("📋 Zadnji potresi (ARSO)")
    if df.empty:
        st.info("Ni podatkov iz ARSO.")
    else:
        # highlight redovi s mag ≥ 2.0
        st.dataframe(df, use_container_width=True, hide_index=True)
