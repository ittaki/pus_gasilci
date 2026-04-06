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
    "Ljubljana": ["Ljubljanica", "Sava", "Gradaščica", "Iška", "Kamniška Bistrica"],
    "Maribor": ["Drava", "Dravinja", "Pesnica"],
    "Celje": ["Savinja", "Voglajna", "Hudinja"],
    "Kranj": ["Sava", "Kokra", "Sora"],
    "Koper": ["Rižana", "Dragonja", "Badaševica"],
    "Novo Mesto": ["Krka", "Kolpa", "Temenica"],
    "Murska Sobota": ["Mura", "Ledava", "Ščavnica"],
    "Nova Gorica": ["Soča", "Vipava", "Idrijca"],
}

ARSO_RIVER_URL = "https://www.arso.gov.si/xml/vode/hidro_podatki_dnevno_porocilo.xml"


# -----------------------------
# HELPERS
# -----------------------------
def strip_ns(tag: str) -> str:
    return tag.split("}")[-1].lower() if tag else ""


def text_or_none(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def matches_any(tag_name: str, options):
    return any(opt in tag_name for opt in options)


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
        "hourly": ["precipitation", "relative_humidity_2m"],
        "forecast_days": 1,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
    }

    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    rain_24h = None
    if isinstance(hourly.get("precipitation"), list):
        rain_24h = round(sum(v for v in hourly["precipitation"] if isinstance(v, (int, float))), 1)

    humidity = None
    if isinstance(hourly.get("relative_humidity_2m"), list) and hourly["relative_humidity_2m"]:
        humidity = hourly["relative_humidity_2m"][0]

    return {
        "temp": current.get("temperature_2m"),
        "wind": current.get("wind_speed_10m"),
        "rain_now": current.get("precipitation"),
        "rain_24h": rain_24h,
        "humidity": humidity,
        "time": current.get("time"),
    }


# -----------------------------
# ARSO RIVER DATA
# -----------------------------
@st.cache_data(ttl=86400)
def fetch_rivers():
    url = "https://www.arso.gov.si/xml/vode/hidro_podatki_dnevno_porocilo.xml"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.text
    response = requests.get(ARSO_RIVER_URL, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    stations = []

    # Try any element whose tag contains "postaja"
    for node in root.iter():
        node_tag = strip_ns(node.tag)
        if "postaja" not in node_tag:
            continue

        station = {
            "river": None,
            "name": None,
            "level": None,
            "flow": None,
            "trend": None,
            "status": None,
        }

        for child in node:
            tag = strip_ns(child.tag)
            val = text_or_none(child.text)

            if not val:
                continue

            if matches_any(tag, ["reka"]):
                station["river"] = val
            elif matches_any(tag, ["ime", "merilno_mesto", "postaja"]):
                # avoid overwriting with nested generic "postaja" text unless name is empty
                if station["name"] is None:
                    station["name"] = val
            elif matches_any(tag, ["vodostaj"]):
                station["level"] = val
            elif matches_any(tag, ["pretok"]):
                station["flow"] = val
            elif matches_any(tag, ["trend", "tendenca"]):
                station["trend"] = val
            elif matches_any(tag, ["opis", "status", "stanje"]):
                station["status"] = val

        if station["river"]:
            stations.append(station)

    # Fallback parser: sometimes data may be nested more deeply than one level
    if not stations:
        current_station = None
        for node in root.iter():
            tag = strip_ns(node.tag)
            val = text_or_none(node.text)

            if "postaja" in tag:
                if current_station and current_station.get("river"):
                    stations.append(current_station)
                current_station = {
                    "river": None,
                    "name": None,
                    "level": None,
                    "flow": None,
                    "trend": None,
                    "status": None,
                }
                continue

            if current_station is None or not val:
                continue

            if matches_any(tag, ["reka"]):
                current_station["river"] = val
            elif matches_any(tag, ["ime", "merilno_mesto"]):
                current_station["name"] = current_station["name"] or val
            elif matches_any(tag, ["vodostaj"]):
                current_station["level"] = val
            elif matches_any(tag, ["pretok"]):
                current_station["flow"] = val
            elif matches_any(tag, ["trend", "tendenca"]):
                current_station["trend"] = val
            elif matches_any(tag, ["opis", "status", "stanje"]):
                current_station["status"] = val

        if current_station and current_station.get("river"):
            stations.append(current_station)

    # Deduplicate a bit
    cleaned = []
    seen = set()
    for s in stations:
        key = (
            s.get("river") or "",
            s.get("name") or "",
            s.get("level") or "",
            s.get("flow") or "",
        )
        if key not in seen:
            seen.add(key)
            cleaned.append(s)

    return cleaned


def filter_rivers(region, stations):
    rivers = REGION_RIVERS[region]
    filtered = []

    for s in stations:
        river_name = (s.get("river") or "").lower()
        if any(r.lower() in river_name for r in rivers):
            filtered.append(s)

    return filtered


def rainfall_warning_label(rain_now, rain_24h):
    rain_now = rain_now or 0
    rain_24h = rain_24h or 0

    if rain_now > 10 or rain_24h > 60:
        return "High flood risk", "error"
    if rain_now > 4 or rain_24h > 25:
        return "Moderate flood risk", "warning"
    return "Low flood risk", "success"


# -----------------------------
# PAGE
# -----------------------------
def render():
    st.title("🌊 Flood Monitoring")

    area = st.selectbox("Select area", list(REGIONS.keys()))
    cfg = REGIONS[area]

    # ---------------- WEATHER
    weather_error = None
    weather = None
    try:
        weather = fetch_weather(cfg["lat"], cfg["lon"])
    except Exception as e:
        weather_error = str(e)

    st.subheader("📊 Weather")

    c1, c2, c3, c4 = st.columns(4)

    if weather:
        c1.metric("Temp", f"{weather['temp']} °C" if weather["temp"] is not None else "—")
        c2.metric("Rain (now)", f"{weather['rain_now']} mm" if weather["rain_now"] is not None else "—")
        c3.metric("Rain (24h)", f"{weather['rain_24h']} mm" if weather["rain_24h"] is not None else "—")
        c4.metric("Wind", f"{weather['wind']} m/s" if weather["wind"] is not None else "—")
    else:
        c1.metric("Temp", "—")
        c2.metric("Rain (now)", "—")
        c3.metric("Rain (24h)", "—")
        c4.metric("Wind", "—")

    if weather_error:
        st.error(f"Weather data error: {weather_error}")

    # ---------------- WARNINGS
    st.subheader("⚠️ Rainfall Warning")

    if weather:
        label, kind = rainfall_warning_label(weather["rain_now"], weather["rain_24h"])
        if kind == "error":
            st.error(label)
        elif kind == "warning":
            st.warning(label)
        else:
            st.success(label)
    else:
        st.info("Warning estimate unavailable.")

    # ---------------- RIVERS
st.subheader("🔍 RAW XML (debug)")

xml_data = fetch_rivers()

st.code(xml_data[:2000])

    try:
        stations = fetch_rivers()
        region_rivers = filter_rivers(area, stations)
    except Exception as e:
        river_error = str(e)

    if river_error:
        st.error(f"River data error: {river_error}")
        st.link_button("Open ARSO river XML", ARSO_RIVER_URL)

    elif not region_rivers:
        st.warning("No region-matched river entries were found in the current ARSO XML.")
        with st.expander("Show first 10 parsed ARSO entries for debugging"):
            st.write(stations[:10])
        st.link_button("Open ARSO river XML", ARSO_RIVER_URL)

    else:
        for r in region_rivers:
            title = f"{r.get('river', 'Unknown river')} – {r.get('name', 'Unknown station')}"
            st.markdown(f"**{title}**")

            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**Water level:** {r.get('level') or '—'}")
            col2.write(f"**Flow:** {r.get('flow') or '—'}")
            col3.write(f"**Trend:** {r.get('trend') or '—'}")
            col4.write(f"**Status:** {r.get('status') or '—'}")

            st.markdown("---")

    # ---------------- MAP
    st.subheader("📍 Map")
    st.components.v1.iframe(
        f"https://www.google.com/maps?q={cfg['map']}&output=embed",
        height=400,
    )
