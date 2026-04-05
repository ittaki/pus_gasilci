import requests
import streamlit as st


REGIONS = {
    "Ljubljana": {
        "lat": 46.0569,
        "lon": 14.5058,
        "map_query": "Ljubljana, Slovenia",
    },
    "Maribor": {
        "lat": 46.5547,
        "lon": 15.6459,
        "map_query": "Maribor, Slovenia",
    },
    "Celje": {
        "lat": 46.2397,
        "lon": 15.2677,
        "map_query": "Celje, Slovenia",
    },
    "Kranj": {
        "lat": 46.2389,
        "lon": 14.3556,
        "map_query": "Kranj, Slovenia",
    },
    "Koper": {
        "lat": 45.5481,
        "lon": 13.7302,
        "map_query": "Koper, Slovenia",
    },
    "Novo Mesto": {
        "lat": 45.8030,
        "lon": 15.1689,
        "map_query": "Novo Mesto, Slovenia",
    },
    "Murska Sobota": {
        "lat": 46.6625,
        "lon": 16.1664,
        "map_query": "Murska Sobota, Slovenia",
    },
    "Nova Gorica": {
        "lat": 45.9560,
        "lon": 13.6484,
        "map_query": "Nova Gorica, Slovenia",
    },
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@st.cache_data(ttl=900)
def fetch_weather(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation",
            "rain",
        ],
        "hourly": ["precipitation"],
        "forecast_days": 1,
        "timezone": "auto",
        "wind_speed_unit": "ms",
        "precipitation_unit": "mm",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    rainfall_24h = None
    precip_values = hourly.get("precipitation")
    if isinstance(precip_values, list) and precip_values:
        rainfall_24h = round(sum(v for v in precip_values if isinstance(v, (int, float))), 1)

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind": current.get("wind_speed_10m"),
        "rain_now": current.get("rain", current.get("precipitation")),
        "rainfall_24h": rainfall_24h,
        "current_time": current.get("time"),
    }


def warning_level(rain_now, rainfall_24h):
    rain_now = rain_now or 0
    rainfall_24h = rainfall_24h or 0

    if rain_now >= 10 or rainfall_24h >= 60:
        return "High", "error", "High rainfall intensity or accumulation detected."
    if rain_now >= 4 or rainfall_24h >= 25:
        return "Moderate", "warning", "Elevated rainfall conditions detected."
    return "Low", "success", "No significant rainfall signal detected."


def render():
    if "floods_mode" not in st.session_state:
        st.session_state.floods_mode = None

    mode = st.session_state.floods_mode

    if mode == "Archived Information":
        page_background = """
        .stApp {
            background: linear-gradient(180deg, #6082B6 0%, #4f6fa3 100%);
        }
        """
        title_color = "#f8fafc"
        subtitle_color = "#eef2ff"
        divider_color = "rgba(255, 255, 255, 0.20)"
    else:
        page_background = """
        .stApp {
            background: linear-gradient(180deg, #eaf4fb 0%, #dfeef8 100%);
        }
        """
        title_color = "#0f172a"
        subtitle_color = "#475569"
        divider_color = "rgba(148, 163, 184, 0.22)"

    st.markdown(
        f"""
    <style>
        {page_background}

        html, body, [class*="css"] {{
            font-family: "Inter", "Segoe UI", sans-serif;
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }}

        .main-title {{
            font-size: 2.6rem;
            font-weight: 800;
            color: {title_color};
            margin-bottom: 0.25rem;
        }}

        .subtitle {{
            color: {subtitle_color};
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }}

        .mode-card {{
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 12px;
        }}

        .landing-card {{
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(6px);
            border: 1px solid rgba(191, 219, 254, 0.75);
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        }}

        .current-card {{
            background: rgba(255, 255, 255, 0.90);
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }}

        .history-card {{
            background: rgba(15, 23, 42, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #f8fafc;
            backdrop-filter: blur(8px);
            box-shadow: 0 12px 30px rgba(31, 41, 55, 0.22);
        }}

        .small-label {{
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #64748b;
            margin-bottom: 8px;
            font-weight: 700;
        }}

        .history-card .small-label {{
            color: #f1f5f9;
            opacity: 0.88;
        }}

        .big-text {{
            font-size: 1.25rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 8px;
        }}

        .history-card .big-text {{
            color: #ffffff;
            font-size: 1.3rem;
            font-weight: 800;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
        }}

        .history-card p,
        .history-card span,
        .history-card div {{
            color: #f8fafc;
        }}

        .wave-wrap {{
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 28px;
            background: linear-gradient(135deg, rgba(255,255,255,0.45) 0%, rgba(224,242,254,0.45) 100%);
            border: 1px solid rgba(191, 219, 254, 0.9);
            box-shadow: 0 12px 32px rgba(14, 116, 144, 0.08);
            margin-bottom: 20px;
        }}

        .wave-wrap::before,
        .wave-wrap::after {{
            content: "";
            position: absolute;
            left: -10%;
            width: 120%;
            height: 140px;
            border-radius: 45%;
            background: rgba(56, 189, 248, 0.12);
        }}

        .wave-wrap::before {{
            bottom: -70px;
        }}

        .wave-wrap::after {{
            bottom: -95px;
            background: rgba(14, 165, 233, 0.08);
        }}

        div[data-testid="stButton"] > button {{
            border-radius: 14px;
            height: 3.2rem;
            font-weight: 700;
            border: 1px solid #dbeafe;
        }}

        div[data-testid="stSelectbox"] > div {{
            border-radius: 12px;
        }}

        hr {{
            border-color: {divider_color};
        }}

        [data-testid="stInfo"],
        [data-testid="stSuccess"],
        [data-testid="stWarning"],
        [data-testid="stError"] {{
            border-radius: 14px;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="wave-wrap">
        <div class="main-title">🌊 Floods</div>
        <div class="subtitle">Operational floods workspace</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### Select mode")
    c1, c2 = st.columns(2)

    with c1:
        if st.button("📡 Current Information", use_container_width=True):
            st.session_state.floods_mode = "Current Information"
            st.rerun()

    with c2:
        if st.button("🗂️ Archived Information", use_container_width=True):
            st.session_state.floods_mode = "Archived Information"
            st.rerun()

    mode = st.session_state.floods_mode
    st.markdown("---")

    if mode is None:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
                <div class="mode-card landing-card">
                    <div class="small-label">Live operations</div>
                    <div class="big-text">Current Information</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown("""
                <div class="mode-card landing-card">
                    <div class="small-label">Archive workspace</div>
                    <div class="big-text">Archived Information</div>
                </div>
            """, unsafe_allow_html=True)

        st.info("Choose a mode to continue.")
        return

    if mode == "Current Information":
        st.markdown("""
        <div class="mode-card current-card">
            <div class="small-label">Current mode</div>
            <div class="big-text">Current flood monitoring and area-specific updates.</div>
        </div>
        """, unsafe_allow_html=True)

        area = st.selectbox(
            "Select area",
            list(REGIONS.keys()),
            index=None,
            placeholder="Choose an area",
        )

        st.markdown("---")

        if area is None:
            st.info("Select an area to continue.")
            return

        cfg = REGIONS[area]

        try:
            weather = fetch_weather(cfg["lat"], cfg["lon"])
            weather_error = None
        except Exception as exc:
            weather = None
            weather_error = str(exc)

        st.success(f"Area selected: {area}")

        m1, m2, m3, m4 = st.columns(4)

        if weather:
            m1.metric(
                "Temperature",
                "—" if weather["temperature"] is None else f'{weather["temperature"]:.1f} °C'
            )
            m2.metric(
                "Rainfall (24h)",
                "—" if weather["rainfall_24h"] is None else f'{weather["rainfall_24h"]:.1f} mm'
            )
            m3.metric(
                "Wind",
                "—" if weather["wind"] is None else f'{weather["wind"]:.1f} m/s'
            )
            m4.metric(
                "Humidity",
                "—" if weather["humidity"] is None else f'{weather["humidity"]:.0f} %'
            )
        else:
            m1.metric("Temperature", "—")
            m2.metric("Rainfall (24h)", "—")
            m3.metric("Wind", "—")
            m4.metric("Humidity", "—")

        left, right = st.columns([1, 1])

        with left:
            st.markdown("""
            <div class="mode-card current-card">
                <div class="small-label">Current weather</div>
                <div class="big-text">Live regional conditions</div>
            </div>
            """, unsafe_allow_html=True)

            if weather_error:
                st.error(f"Could not load live weather data: {weather_error}")
            elif weather:
                st.write(f"**Location:** {area}")
                st.write(f"**Current temperature:** {weather['temperature']:.1f} °C" if weather["temperature"] is not None else "**Current temperature:** —")
                st.write(f"**Current rainfall:** {weather['rain_now']:.1f} mm" if weather["rain_now"] is not None else "**Current rainfall:** —")
                st.write(f"**Updated:** {weather['current_time'] or '—'}")
            else:
                st.warning("No weather data is available for this area right now.")

        with right:
            st.markdown("""
            <div class="mode-card current-card">
                <div class="small-label">Weather warnings</div>
                <div class="big-text">Rainfall-based warning estimate</div>
            </div>
            """, unsafe_allow_html=True)

            if weather:
                level, box_type, message = warning_level(weather["rain_now"], weather["rainfall_24h"])
                if box_type == "error":
                    st.error(f"{level} warning")
                elif box_type == "warning":
                    st.warning(f"{level} warning")
                else:
                    st.success(f"{level} warning")

                st.write(message)
                st.write(f"**Current rainfall:** {weather['rain_now'] if weather['rain_now'] is not None else '—'} mm")
                st.write(f"**24h rainfall:** {weather['rainfall_24h'] if weather['rainfall_24h'] is not None else '—'} mm")
            else:
                st.info("Warning estimate unavailable because live weather data could not be loaded.")

        st.markdown("---")

        map_col, rain_col = st.columns([1.2, 0.8])

        with map_col:
            st.markdown("""
            <div class="mode-card current-card">
                <div class="small-label">Area overview</div>
                <div class="big-text">Region map</div>
            </div>
            """, unsafe_allow_html=True)

            query = cfg["map_query"].replace(" ", "+")
            st.components.v1.iframe(
                f"https://www.google.com/maps?q={query}&output=embed",
                height=420,
                scrolling=False,
            )

        with rain_col:
            st.markdown("""
            <div class="mode-card current-card">
                <div class="small-label">Rainfall summary</div>
                <div class="big-text">Area precipitation status</div>
            </div>
            """, unsafe_allow_html=True)

            if weather:
                rain_now = weather["rain_now"] if weather["rain_now"] is not None else 0
                rain_24h = weather["rainfall_24h"] if weather["rainfall_24h"] is not None else 0

                if rain_now >= 10 or rain_24h >= 60:
                    st.error("High precipitation signal")
                elif rain_now >= 4 or rain_24h >= 25:
                    st.warning("Moderate precipitation signal")
                else:
                    st.success("Low precipitation signal")

                st.write(f"**Current rainfall:** {rain_now} mm")
                st.write(f"**Rainfall in the next/selected 24h window:** {rain_24h} mm")
            else:
                st.info("Rainfall summary unavailable.")

    elif mode == "Archived Information":
        st.markdown("""
        <div class="mode-card history-card">
            <div class="small-label">Archived mode</div>
            <div class="big-text">Archive of past events, documents, reports, maps, and historical resources.</div>
        </div>
        """, unsafe_allow_html=True)

        history_type = st.selectbox(
            "Select archive type",
            [
                "Past flood events",
                "Reports",
                "Maps",
                "Operational notes",
                "Reference materials",
            ],
            index=None,
            placeholder="Choose a historical category",
        )

        st.markdown("---")

        if history_type is None:
            st.info("Select a historical category to continue.")
            return

        st.success(f"Archive selected: {history_type}")

        c1, c2 = st.columns([1, 1])

        with c1:
            st.markdown("""
            <div class="mode-card history-card">
                <div class="small-label">Archived workspace</div>
                <div class="big-text">Archived information view</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown("""
            <div class="mode-card history-card">
                <div class="small-label">Selected archive</div>
                <div class="big-text">Resource category</div>
            </div>
            """, unsafe_allow_html=True)

            st.write(f"Selected archive type: **{history_type}**")
            st.write("Placeholder: archived resources will appear here.")
