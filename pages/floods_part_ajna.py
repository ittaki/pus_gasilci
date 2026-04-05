import datetime as dt
import requests
import streamlit as st
import xml.etree.ElementTree as ET


REGIONS = {
    "Ljubljana": {
        "station_candidates": ["LJUBLJANA_BEZIGRAD", "Ljubljana", "LJUBL-ANA_BEZIGRAD"],
        "warning_zone": "SLOVENIA_CENTRAL",
        "map_query": "Ljubljana, Slovenia",
    },
    "Maribor": {
        "station_candidates": ["MARIBOR", "Maribor"],
        "warning_zone": "SLOVENIA_NORTH-EAST",
        "map_query": "Maribor, Slovenia",
    },
    "Celje": {
        "station_candidates": ["CELJE", "Celje"],
        "warning_zone": "SLOVENIA_NORTH-EAST",
        "map_query": "Celje, Slovenia",
    },
    "Kranj": {
        "station_candidates": ["KRANJ", "Kranj"],
        "warning_zone": "SLOVENIA_NORTH-WEST",
        "map_query": "Kranj, Slovenia",
    },
    "Koper": {
        "station_candidates": ["KOPER", "Koper", "KOPER_MARKOVEC"],
        "warning_zone": "SLOVENIA_SOUTH-WEST",
        "map_query": "Koper, Slovenia",
    },
    "Novo Mesto": {
        "station_candidates": ["NOVO_MESTO", "Novo mesto", "NOVO MESTO"],
        "warning_zone": "SLOVENIA_SOUTH-EAST",
        "map_query": "Novo Mesto, Slovenia",
    },
    "Murska Sobota": {
        "station_candidates": ["MURSKA_SOBOTA", "Murska Sobota"],
        "warning_zone": "SLOVENIA_NORTH-EAST",
        "map_query": "Murska Sobota, Slovenia",
    },
    "Nova Gorica": {
        "station_candidates": ["NOVA_GORICA", "Nova Gorica"],
        "warning_zone": "SLOVENIA_SOUTH-WEST",
        "map_query": "Nova Gorica, Slovenia",
    },
}


OBS_URL = "https://www.arso.gov.si/xml/vreme/podatki/dz_zadnji.xml"
WARNING_OVERVIEW_URL = "https://meteo.arso.gov.si/met/sl/warning/"
RADAR_URL = "https://meteo.arso.gov.si/met/sl/weather/observ/radar/"


def safe_text(node, tag_names):
    for tag in tag_names:
        child = node.find(tag)
        if child is not None and child.text and str(child.text).strip():
            return str(child.text).strip()
    return None


def to_float_maybe(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "."))
    except Exception:
        return None


@st.cache_data(ttl=600)
def fetch_station_weather():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(OBS_URL, headers=headers, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    stations = []
    for station in root.findall(".//metPod"):
        name = safe_text(station, ["domain_title", "title", "domain_longtitle", "valid_domain_title"])
        if not name:
            continue

        stations.append(
            {
                "name": name,
                "temp": safe_text(station, ["t", "temp", "ta"]),
                "humidity": safe_text(station, ["rh", "humidity"]),
                "wind": safe_text(station, ["ff_val", "ff", "wind_speed"]),
                "condition": safe_text(station, ["nn_decode_short", "weather_desc", "wwsyn_shorttext"]),
                "rain": safe_text(
                    station,
                    [
                        "rr_val",
                        "rr_10min",
                        "rr_30min",
                        "rr_1h",
                        "precipitation",
                        "padavine",
                    ],
                ),
                "updated": safe_text(station, ["tsValid_issued", "valid", "updated"]),
            }
        )
    return stations


def match_station(region_name, stations):
    candidates = REGIONS[region_name]["station_candidates"]
    lowered = {c.lower() for c in candidates}

    # Exact-ish match first
    for station in stations:
        station_name = station["name"].lower()
        if station_name in lowered:
            return station
        if any(c.lower() in station_name for c in candidates):
            return station

    # Fallback to first candidate prefix/contains
    for station in stations:
        station_name = station["name"].lower()
        if any(part.lower().replace("_", " ") in station_name for part in candidates):
            return station

    return None


@st.cache_data(ttl=900)
def fetch_warning(zone_code):
    """
    First-pass regional warning fetch.
    ARSO warning filenames can vary by hazard and zone, so this function
    tries the most useful rain-focused CAP files first and fails gracefully.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    hazard_candidates = ["rain", "thunderstorm", "wind", "snow", "ice"]
    base = "https://meteo.arso.gov.si/uploads/probase/www/warning/text/sl"

    for hazard in hazard_candidates:
        url = f"{base}/warning_{hazard}_{zone_code}_latest_CAP.xml"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200 or not response.content:
                continue

            root = ET.fromstring(response.content)

            # CAP files commonly use namespaces. Strip them when needed.
            def find_any_text(possible_names):
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1]
                    if tag in possible_names and elem.text and elem.text.strip():
                        return elem.text.strip()
                return None

            headline = find_any_text(["headline"])
            event = find_any_text(["event"])
            severity = find_any_text(["severity"])
            urgency = find_any_text(["urgency"])
            description = find_any_text(["description"])
            sent = find_any_text(["sent"])
            area_desc = find_any_text(["areaDesc"])

            if headline or event:
                return {
                    "headline": headline or event or "Weather warning",
                    "event": event,
                    "severity": severity,
                    "urgency": urgency,
                    "description": description,
                    "sent": sent,
                    "area_desc": area_desc,
                    "source_url": url,
                }
        except Exception:
            continue

    return None


def weather_warning_color(severity):
    if not severity:
        return "info"
    sev = severity.lower()
    if sev in {"extreme", "severe"}:
        return "error"
    if sev in {"moderate"}:
        return "warning"
    return "info"


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
            st.markdown(
                """
                <div class="mode-card landing-card">
                    <div class="small-label">Live operations</div>
                    <div class="big-text">Current Information</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="mode-card landing-card">
                    <div class="small-label">Archive workspace</div>
                    <div class="big-text">Archived Information</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.info("Choose a mode to continue.")
        return

    if mode == "Current Information":
        st.markdown(
            """
            <div class="mode-card current-card">
                <div class="small-label">Current mode</div>
                <div class="big-text">Current flood monitoring and area-specific updates.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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

        region_cfg = REGIONS[area]

        # WEATHER / RAINFALL
        weather_error = None
        station = None
        try:
            stations = fetch_station_weather()
            station = match_station(area, stations)
        except Exception as exc:
            weather_error = str(exc)

        # WARNINGS
        warning = None
        warning_error = None
        try:
            warning = fetch_warning(region_cfg["warning_zone"])
        except Exception as exc:
            warning_error = str(exc)

        st.success(f"Area selected: {area}")

        # TOP METRICS
        m1, m2, m3, m4 = st.columns(4)

        if station:
            with m1:
                st.metric("Temperature", f"{station['temp'] or '—'} °C")
            with m2:
                st.metric("Rainfall", f"{station['rain'] or '—'} mm")
            with m3:
                st.metric("Wind", f"{station['wind'] or '—'} m/s")
            with m4:
                st.metric("Humidity", f"{station['humidity'] or '—'} %")
        else:
            with m1:
                st.metric("Temperature", "—")
            with m2:
                st.metric("Rainfall", "—")
            with m3:
                st.metric("Wind", "—")
            with m4:
                st.metric("Humidity", "—")

        st.markdown("")

        left, right = st.columns([1, 1])

        with left:
            st.markdown(
                """
                <div class="mode-card current-card">
                    <div class="small-label">Current weather</div>
                    <div class="big-text">Station-based conditions</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if weather_error:
                st.error(f"Could not load ARSO weather data: {weather_error}")
            elif station:
                st.write(f"**Station:** {station['name']}")
                st.write(f"**Condition:** {station['condition'] or '—'}")
                st.write(f"**Updated:** {station['updated'] or '—'}")
                st.write(f"**Rainfall:** {station['rain'] or '—'} mm")
            else:
                st.warning("No matching ARSO station was found for this area in the current feed.")

        with right:
            st.markdown(
                """
                <div class="mode-card current-card">
                    <div class="small-label">Weather warnings</div>
                    <div class="big-text">Regional warning status</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if warning:
                sev = weather_warning_color(warning.get("severity"))
                text = warning.get("headline") or "Weather warning"
                if sev == "error":
                    st.error(text)
                elif sev == "warning":
                    st.warning(text)
                else:
                    st.info(text)

                if warning.get("event"):
                    st.write(f"**Event:** {warning['event']}")
                if warning.get("severity"):
                    st.write(f"**Severity:** {warning['severity']}")
                if warning.get("urgency"):
                    st.write(f"**Urgency:** {warning['urgency']}")
                if warning.get("area_desc"):
                    st.write(f"**Area:** {warning['area_desc']}")
                if warning.get("sent"):
                    st.write(f"**Issued:** {warning['sent']}")
                if warning.get("description"):
                    st.write(warning["description"])
            else:
                st.info("No regional CAP warning was found in the first-pass feed lookup.")
                st.link_button("Open ARSO warning overview", WARNING_OVERVIEW_URL)

            if warning_error:
                st.caption(f"Warning feed note: {warning_error}")

        st.markdown("---")

        map_col, rain_col = st.columns([1.2, 0.8])

        with map_col:
            st.markdown(
                """
                <div class="mode-card current-card">
                    <div class="small-label">Area overview</div>
                    <div class="big-text">Region map</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            query = region_cfg["map_query"].replace(" ", "+")
            st.components.v1.iframe(
                f"https://www.google.com/maps?q={query}&output=embed",
                height=420,
                scrolling=False,
            )

        with rain_col:
            st.markdown(
                """
                <div class="mode-card current-card">
                    <div class="small-label">Rainfall resources</div>
                    <div class="big-text">ARSO precipitation view</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if station:
                rain_num = to_float_maybe(station["rain"])
                if rain_num is not None:
                    if rain_num >= 10:
                        st.error(f"High station rainfall: {station['rain']} mm")
                    elif rain_num >= 2:
                        st.warning(f"Moderate station rainfall: {station['rain']} mm")
                    else:
                        st.success(f"Low station rainfall: {station['rain']} mm")
                else:
                    st.info(f"Station rainfall: {station['rain'] or '—'} mm")

            st.link_button("Open ARSO radar precipitation", RADAR_URL)
            st.caption("Use radar for broader precipitation context; station rainfall remains the local metric.")

    elif mode == "Archived Information":
        st.markdown(
            """
            <div class="mode-card history-card">
                <div class="small-label">Archived mode</div>
                <div class="big-text">Archive of past events, documents, reports, maps, and historical resources.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            st.markdown(
                """
                <div class="mode-card history-card">
                    <div class="small-label">Archived workspace</div>
                    <div class="big-text">Archived information view</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                """
                <div class="mode-card history-card">
                    <div class="small-label">Selected archive</div>
                    <div class="big-text">Resource category</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.write(f"Selected archive type: **{history_type}**")
            st.write("Placeholder: archived resources will appear here.")
