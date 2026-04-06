import requests
import streamlit as st
import xml.etree.ElementTree as ET


# -----------------------------
# REGION CONFIG
# -----------------------------
REGIONS = {
    "Ljubljana": {"lat": 46.0569, "lon": 14.5058, "map": "Ljubljana, Slovenia"},
    "Maribor": {"lat": 46.5547, "lon": 15.6459, "map": "Maribor, Slovenia"},
    "Celje": {"lat": 46.2397, "lon": 15.2677, "map": "Celje, Slovenia"},
    "Kranj": {"lat": 46.2389, "lon": 14.3556, "map": "Kranj, Slovenia"},
    "Koper": {"lat": 45.5481, "lon": 13.7302, "map": "Koper, Slovenia"},
    "Novo Mesto": {"lat": 45.8030, "lon": 15.1689, "map": "Novo Mesto, Slovenia"},
    "Murska Sobota": {"lat": 46.6625, "lon": 16.1664, "map": "Murska Sobota, Slovenia"},
    "Nova Gorica": {"lat": 45.9560, "lon": 13.6484, "map": "Nova Gorica, Slovenia"},
}

# -----------------------------
# RIVER → REGION MAPPING
# -----------------------------
REGION_RIVERS = {
    "Ljubljana": ["Ljubljanica", "Sava", "Gradaščica", "Iška"],
    "Maribor": ["Drava", "Dravinja", "Pesnica"],
    "Celje": ["Savinja", "Voglajna", "Hudinja"],
    "Kranj": ["Sava", "Kokra", "Sora"],
    "Koper": ["Rižana", "Dragonja", "Badaševica"],
    "Novo Mesto": ["Krka", "Kolpa", "Temenica"],
    "Murska Sobota": ["Mura", "Ledava", "Ščavnica"],
    "Nova Gorica": ["Soča", "Vipava", "Idrijca"],
}


# -----------------------------
# WEATHER (Open-Meteo)
# -----------------------------
@st.cache_data(ttl=900)
def fetch_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "wind_speed_10m", "precipitation"],
        "hourly": ["precipitation"],
        "forecast_days": 1,
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    current = data["current"]
    rain_24h = sum(data["hourly"]["precipitation"])

    return {
        "temp": current["temperature_2m"],
        "wind": current["wind_speed_10m"],
        "rain_now": current["precipitation"],
        "rain_24h": round(rain_24h, 1),
    }


# -----------------------------
# ARSO RIVER DATA
# -----------------------------
@st.cache_data(ttl=86400)
def fetch_rivers():
    url = "https://www.arso.gov.si/xml/vode/hidro_podatki_dnevno_porocilo.xml"
    r = requests.get(url, timeout=20)
    root = ET.fromstring(r.content)

    stations = []

    for postaja in root.findall(".//postaja"):
        river = postaja.findtext("reka")
        name = postaja.findtext("ime")
        vodostaj = postaja.findtext("vodostaj")
        pretok = postaja.findtext("pretok")

        if river:
            stations.append({
                "river": river,
                "name": name,
                "level": vodostaj,
                "flow": pretok,
            })

    return stations


def filter_rivers(region, stations):
    rivers = REGION_RIVERS[region]
    return [s for s in stations if s["river"] in rivers]


# -----------------------------
# APP
# -----------------------------
def render():
    st.title("🌊 Flood Monitoring")

    area = st.selectbox("Select area", list(REGIONS.keys()))

    cfg = REGIONS[area]

    # ---------------- WEATHER
    weather = fetch_weather(cfg["lat"], cfg["lon"])

    st.subheader("📊 Weather")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Temp", f"{weather['temp']} °C")
    c2.metric("Rain (now)", f"{weather['rain_now']} mm")
    c3.metric("Rain (24h)", f"{weather['rain_24h']} mm")
    c4.metric("Wind", f"{weather['wind']} m/s")

    # ---------------- WARNINGS
    st.subheader("⚠️ Rainfall Warning")

    if weather["rain_now"] > 10 or weather["rain_24h"] > 60:
        st.error("High flood risk")
    elif weather["rain_now"] > 4 or weather["rain_24h"] > 25:
        st.warning("Moderate flood risk")
    else:
        st.success("Low flood risk")

    # ---------------- RIVERS
    st.subheader("🌊 River Status")

    try:
        stations = fetch_rivers()
        region_rivers = filter_rivers(area, stations)

        if not region_rivers:
            st.info("No river data for this region")
        else:
            for r in region_rivers:
                st.markdown(f"**{r['river']} – {r['name']}**")

                col1, col2 = st.columns(2)
                col1.write(f"Water level: {r['level']}")
                col2.write(f"Flow: {r['flow']}")

                st.markdown("---")

    except Exception as e:
        st.error(f"River data error: {e}")

    # ---------------- MAP
    st.subheader("📍 Map")

    st.components.v1.iframe(
        f"https://www.google.com/maps?q={cfg['map']}&output=embed",
        height=400
    )
