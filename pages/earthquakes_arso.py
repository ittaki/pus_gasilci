import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import pandas as pd

EMSC_BASE = (
    "https://www.seismicportal.eu/fdsnws/event/1/query"
    "?format=json&limit=200"
    "&minlat=45.0&maxlat=47.5&minlon=12.5&maxlon=17.5"
    "&minmagnitude=0.5"
)

@st.cache_data(ttl=900)
def fetch_quakes(days=30):
    try:
        start = (datetime.utcnow()-timedelta(days=days)).strftime("%Y-%m-%d")
        r = requests.get(EMSC_BASE+f"&starttime={start}", timeout=20)
        if r.status_code != 200:
            return pd.DataFrame(), f"HTTP {r.status_code}"
        feats = r.json().get("features",[])
        rows = []
        for f in feats:
            p = f["properties"]
            c = f["geometry"]["coordinates"]
            rows.append({"cas":p.get("time",""),"mag":p.get("mag"),
                "globina_km":p.get("depth"),
                "lokacija":p.get("flynn_region",p.get("place","")),
                "lat":c[1],"lon":c[0]})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["cas"] = pd.to_datetime(df["cas"],errors="coerce")
            df = df.sort_values("cas",ascending=False)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def mag_color(mag):
    try: m=float(mag)
    except: return "gray"
    if m>=4.0: return "red"
    elif m>=2.5: return "orange"
    else: return "green"

def render():
    st.title("Potresi - EMSC SeismicPortal")
    st.caption(f"EMSC FDSN | Slovenija in okolica | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    days = st.slider("Obdobje (dni)", 7, 90, 30, 7)
    with st.spinner("Nalagam..."):
        df, err = fetch_quakes(days)
    if err:
        st.error(f"Napaka: {err}"); return
    if df.empty:
        st.info("Ni potresov v tem obdobju."); return
    c1,c2,c3 = st.columns(3)
    c1.metric(f"Potresi ({days} dni)", len(df))
    c2.metric("Mag >= 2.0", len(df[df["mag"]>=2.0]))
    c3.metric("Zadnji potres", str(df.iloc[0]["cas"])[:16])
    st.markdown("---")
    st.subheader("Karta potresov")
    m = folium.Map(location=[46.1,14.8], zoom_start=7, tiles="CartoDB positron")
    for _, row in df.iterrows():
        if pd.isna(row["lat"]) or pd.isna(row["lon"]): continue
        color = mag_color(row["mag"])
        radius = max(5, float(row["mag"] or 1)*3)
        popup = (f"<b>Mag:</b> {row['mag']}<br>"
                 f"<b>Cas:</b> {str(row['cas'])[:16]}<br>"
                 f"<b>Globina:</b> {row['globina_km']} km<br>"
                 f"<b>Lokacija:</b> {row['lokacija']}")
        folium.CircleMarker(
            location=[row["lat"],row["lon"]],
            radius=radius, color=color, fill=True, fill_opacity=0.7,
            popup=folium.Popup(popup,max_width=250),
            tooltip=f"M{row['mag']} - {row['lokacija']}"
        ).add_to(m)
    st_folium(m, width=800, height=500)
    st.subheader("Zadnji potresi")
    show=[c for c in ["cas","mag","globina_km","lokacija","lat","lon"] if c in df.columns]
    st.dataframe(df[show].head(50), use_container_width=True)
    st.subheader("Magnitude skozi cas")
    st.line_chart(df[["cas","mag"]].dropna().set_index("cas").sort_index())

if __name__ == "__main__":
    render()
