import requests
import streamlit as st
from datetime import datetime

REGIONS = {
    "Ljubljana":     {"lat": 46.0569, "lon": 14.5058},
    "Maribor":       {"lat": 46.5547, "lon": 15.6459},
    "Celje":         {"lat": 46.2397, "lon": 15.2677},
    "Kranj":         {"lat": 46.2389, "lon": 14.3556},
    "Koper":         {"lat": 45.5481, "lon": 13.7302},
    "Novo Mesto":    {"lat": 45.8030, "lon": 15.1689},
    "Murska Sobota": {"lat": 46.6625, "lon": 16.1664},
    "Nova Gorica":   {"lat": 45.9560, "lon": 13.6484},
}
REGION_RIVERS = {
    "Ljubljana":     ["Ljubljanica","Sava","Gradascica","Iska"],
    "Maribor":       ["Drava","Dravinja","Pesnica"],
    "Celje":         ["Savinja","Voglajna","Hudinja"],
    "Kranj":         ["Sava","Kokra","Sora"],
    "Koper":         ["Rizana","Dragonja","Badasevica"],
    "Novo Mesto":    ["Krka","Kolpa","Temenica"],
    "Murska Sobota": ["Mura","Ledava","Scavnica"],
    "Nova Gorica":   ["Soca","Vipava","Idrijca"],
}

@st.cache_data(ttl=900)
def fetch_weather(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": ["temperature_2m","wind_speed_10m","precipitation"],
            "hourly": ["precipitation"], "forecast_days": 1,
        }, timeout=20)
        d = r.json()
        c = d["current"]
        return {"temp": c["temperature_2m"], "wind": c["wind_speed_10m"],
                "rain_now": c["precipitation"],
                "rain_24h": round(sum(d["hourly"]["precipitation"]),1)}, None
    except Exception as e:
        return None, str(e)

@st.cache_data(ttl=1800)
def fetch_rivers():
    try:
        url = "https://www.arso.gov.si/xml/vode/hidro_podatki_dnevno_porocilo.xml"
        r = requests.get(url, timeout=25)
        if r.status_code != 200:
            return [], f"HTTP {r.status_code}"
        content = r.content.replace(b"&", b"&amp;")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        out = []
        for p in root.iter("postaja"):
            def g(tag, _p=p):
                el = _p.find(tag)
                return el.text.strip() if el is not None and el.text else "-"
            out.append({"river":g("reka"),"name":g("ime"),"level":g("vodostaj"),"flow":g("pretok")})
        return out, None
    except Exception as e:
        return [], str(e)

def render():
    st.title("Flood Monitoring")
    st.caption(f"Open-Meteo + ARSO Hidro | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    area = st.selectbox("Izberi obmocje", list(REGIONS.keys()))
    cfg = REGIONS[area]

    st.subheader("Vreme")
    w, werr = fetch_weather(cfg["lat"], cfg["lon"])
    if werr or w is None:
        st.error(f"Napaka: {werr}")
    else:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Temperatura", f"{w['temp']} C")
        c2.metric("Padavine zdaj", f"{w['rain_now']} mm")
        c3.metric("Padavine 24h", f"{w['rain_24h']} mm")
        c4.metric("Veter", f"{w['wind']} km/h")
        st.subheader("Opozorilo")
        if w["rain_now"]>10 or w["rain_24h"]>60: st.error("VISOKO tveganje za poplave!")
        elif w["rain_now"]>4 or w["rain_24h"]>25: st.warning("ZMERNO tveganje")
        else: st.success("Nizko tveganje")

    st.subheader("Stanje rek")
    stations, rerr = fetch_rivers()
    if rerr:
        st.warning(f"Podatki o rekah nedosegljivi: {rerr}")
    else:
        rivers = REGION_RIVERS.get(area, [])
        rs = [s for s in stations if any(rv.lower() in s["river"].lower() for rv in rivers)]
        if not rs: st.info("Ni podatkov za to obmocje.")
        else:
            for rv in rs:
                st.markdown(f"**{rv['river']} - {rv['name']}**")
                col1,col2 = st.columns(2)
                col1.metric("Vodostaj (cm)", rv["level"])
                col2.metric("Pretok (m3/s)", rv["flow"])
                st.markdown("---")

    st.subheader("Karta")
    st.iframe(
        f"https://www.google.com/maps?q={cfg['lat']},{cfg['lon']}&z=10&output=embed",
        height=400)

if __name__ == "__main__":
    render()
