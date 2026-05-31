import streamlit as st
import folium
from streamlit_folium import st_folium
import psycopg2

CONN = "postgresql://neondb_owner:npg_bgdEuH3PKUo5@ep-green-tooth-ab7n0h1e-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

KATEGORIJE_BOJA = {
    "Bolnica": "red",
    "Gasilski dom": "orange",
    "Policija": "blue",
    "Vrtic": "green",
    "Sola": "darkgreen",
    "Staracki dom": "purple",
    "Apoteka": "lightred",
    "Benzinska pumpa": "gray",
    "Trafo stanica": "black",
    "Hidrant": "cadetblue",
    "Klinika": "pink",
    "Zdravnik": "lightblue",
}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_from_db(lat, lon, radius_m, kategorije_tuple):
    results = {}
    try:
        conn = psycopg2.connect(CONN)
        cur = conn.cursor()
        for naziv in kategorije_tuple:
            cur.execute("""
                SELECT ime, naslov, lat, lon,
                    ROUND(
                        earth_distance(
                            ll_to_earth(%s, %s),
                            ll_to_earth(lat, lon)
                        )::numeric, 0
                    ) AS razdalja_m
                FROM kriticna_infrastruktura
                WHERE kategorija = %s
                AND earth_box(ll_to_earth(%s, %s), %s) @> ll_to_earth(lat, lon)
                ORDER BY razdalja_m ASC
                LIMIT 100
            """, (lat, lon, naziv, lat, lon, radius_m))
            rows = cur.fetchall()
            results[naziv] = [
                {"ime": r[0] or "Neznano", "naslov": r[1] or "", "lat": r[2], "lon": r[3], "razdalja_m": int(r[4])}
                for r in rows
            ]
        conn.close()
    except Exception as e:
        st.error(f"DB greska: {e}")
    return results

def render():
    st.title("Nacrtovanje intervencije")
    st.caption("Kliknite na kartu ili unesite koordinate rucno da biste izabrali lokaciju nesrece.")

    # ── SIDEBAR KONTROLE ───────────────────────────────────────
    with st.sidebar:
        st.header("Podesavanja")
        radius = st.number_input("Radijus (m)", min_value=100, max_value=10000, value=1000, step=100)
        izbrane = st.multiselect(
            "Kategorije objekata",
            list(KATEGORIJE_BOJA.keys()),
            default=["Bolnica", "Gasilski dom", "Hidrant", "Staracki dom", "Sola"]
        )
        st.markdown("---")
        st.subheader("Rucni unos koordinata")
        manual_lat = st.number_input("Latitude", value=46.0569, format="%.5f")
        manual_lon = st.number_input("Longitude", value=14.5058, format="%.5f")
        use_manual = st.button("Primeni koordinate", use_container_width=True)

    # ── STANJE SESIJE ──────────────────────────────────────────
    if "sel_lat" not in st.session_state:
        st.session_state.sel_lat = None
        st.session_state.sel_lon = None

    if use_manual:
        st.session_state.sel_lat = manual_lat
        st.session_state.sel_lon = manual_lon

    # ── KARTA ZA KLIK ──────────────────────────────────────────
    st.subheader("Kliknite na kartu da odaberete lokaciju")

    center = [st.session_state.sel_lat or 46.1, st.session_state.sel_lon or 14.8]
    m = folium.Map(location=center, zoom_start=10, tiles="OpenStreetMap")

    if st.session_state.sel_lat:
        folium.Marker(
            [st.session_state.sel_lat, st.session_state.sel_lon],
            popup="Lokacija nesrece",
            tooltip="Lokacija nesrece",
            icon=folium.Icon(color="red", icon="exclamation-sign", prefix="glyphicon")
        ).add_to(m)
        folium.Circle(
            [st.session_state.sel_lat, st.session_state.sel_lon],
            radius=radius,
            color="red",
            fill=True,
            fill_opacity=0.05,
            weight=2,
            tooltip=f"Radijus {radius}m"
        ).add_to(m)

    map_data = st_folium(m, width=900, height=480, returned_objects=["last_clicked"])

    if map_data and map_data.get("last_clicked"):
        st.session_state.sel_lat = map_data["last_clicked"]["lat"]
        st.session_state.sel_lon = map_data["last_clicked"]["lng"]
        st.rerun()

    # ── PRIKAZ REZULTATA ───────────────────────────────────────
    if st.session_state.sel_lat:
        lat = st.session_state.sel_lat
        lon = st.session_state.sel_lon

        st.success(f"Izabrana lokacija: {lat:.5f}, {lon:.5f} | Radijus: {radius}m")

        if not izbrane:
            st.warning("Izaberite bar jednu kategoriju u sidebaru.")
            return

        with st.spinner("Pretrazujem bazu..."):
            rezultati = fetch_from_db(lat, lon, radius, tuple(izbrane))

        ukupno = sum(len(v) for v in rezultati.values())
        st.markdown(f"### Pronadjeno: {ukupno} objekata u radijusu {radius}m")

        cols = st.columns(min(len(izbrane), 4))
        for i, naziv in enumerate(izbrane):
            cols[i % 4].metric(naziv, len(rezultati.get(naziv, [])))

        st.markdown("---")

        # Rezultatna karta
        m2 = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
        folium.Marker(
            [lat, lon],
            popup="Lokacija nesrece",
            icon=folium.Icon(color="red", icon="exclamation-sign", prefix="glyphicon")
        ).add_to(m2)
        folium.Circle([lat, lon], radius=radius, color="red", fill=True,
                      fill_opacity=0.05, weight=2).add_to(m2)

        for naziv in izbrane:
            objekti = rezultati.get(naziv, [])
            boja = KATEGORIJE_BOJA.get(naziv, "blue")
            st.subheader(f"{naziv} ({len(objekti)})")
            if not objekti:
                st.info(f"Nema '{naziv}' u radijusu.")
            else:
                for obj in objekti:
                    folium.Marker(
                        [obj["lat"], obj["lon"]],
                        popup=folium.Popup(
                            f"<b>{obj['ime']}</b><br>{obj['naslov']}<br><b>Udaljenost:</b> {obj['razdalja_m']}m",
                            max_width=250
                        ),
                        icon=folium.Icon(color=boja, prefix="glyphicon", icon="map-marker"),
                        tooltip=f"{naziv}: {obj['ime']} ({obj['razdalja_m']}m)"
                    ).add_to(m2)
                for obj in objekti[:5]:
                    st.markdown(f"- **{obj['ime']}** | {obj['naslov'] or 'bez adrese'} | {obj['razdalja_m']}m")
                if len(objekti) > 5:
                    st.caption(f"... i jos {len(objekti)-5} objekata")
            st.markdown("---")

        st.subheader("Karta svih objekata u radijusu")
        st_folium(m2, width=900, height=550)

    else:
        st.info("Kliknite na kartu gore ili unesite koordinate u sidebaru.")

if __name__ == "__main__":
    render()

    