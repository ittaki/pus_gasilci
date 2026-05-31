import osmium
import psycopg2
import requests
import os


CONN = os.environ.get("NEON_CONN", "postgresql://neondb_owner:npg_bgdEuH3PKUo5@ep-green-tooth-ab7n0h1e-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
PBF_URL = "https://download.geofabrik.de/europe/slovenia-latest.osm.pbf"
PBF_FILE = "slovenia-latest.osm.pbf"


AMENITY_MAP = {
    "hospital": "Bolnica",
    "fire_station": "Gasilski dom",
    "police": "Policija",
    "kindergarten": "Vrtic",
    "school": "Sola",
    "nursing_home": "Staracki dom",
    "social_facility": "Staracki dom",
    "pharmacy": "Apoteka",
    "fuel": "Benzinska pumpa",
    "clinic": "Klinika",
    "doctors": "Zdravnik",
    "assembly_point": "Zbirno mesto",
}
HEALTHCARE_MAP = {
    "hospital": "Bolnica",
    "clinic": "Klinika",
    "centre": "Klinika",
    "doctor": "Zdravnik",
    "general_practitioner": "Zdravnik",
    "pharmacy": "Apoteka",
    "nursing_home": "Staracki dom",
}
SOCIAL_MAP = {
    "nursing_home": "Staracki dom",
    "assisted_living": "Staracki dom",
    "group_home": "Staracki dom",
}
POWER_MAP = {
    "substation": "Trafo stanica",
    "transformer": "Trafo stanica",
}
EMERGENCY_MAP = {
    "fire_hydrant": "Hidrant",
    "assembly_point": "Zbirno mesto",
}
BUILDING_MAP = {
    "hospital": "Bolnica",
    "fire_station": "Gasilski dom",
    "police": "Policija",
    "school": "Sola",
    "kindergarten": "Vrtic",
}


class OSMHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.objects = []

    def _process(self, obj, lat, lon):
        tags = {t.k: t.v for t in obj.tags}
        kategorija = (
            AMENITY_MAP.get(tags.get("amenity", "")) or
            HEALTHCARE_MAP.get(tags.get("healthcare", "")) or
            SOCIAL_MAP.get(tags.get("social_facility", "")) or
            POWER_MAP.get(tags.get("power", "")) or
            EMERGENCY_MAP.get(tags.get("emergency", "")) or
            BUILDING_MAP.get(tags.get("building", ""))
        )
        if not kategorija and tags.get("social_facility:for") in ("senior", "elderly"):
            kategorija = "Staracki dom"
        if kategorija:
            ime = tags.get("name") or tags.get("name:sl") or tags.get("name:en") or ""
            naslov = (tags.get("addr:street", "") + " " + tags.get("addr:housenumber", "")).strip()
            self.objects.append((kategorija, ime, naslov, lat, lon))

    def node(self, n):
        if n.location.valid():
            self._process(n, n.location.lat, n.location.lon)

    def way(self, w):
        try:
            lats = [nd.location.lat for nd in w.nodes if nd.location.valid()]
            lons = [nd.location.lon for nd in w.nodes if nd.location.valid()]
            if lats:
                lat = sum(lats) / len(lats)
                lon = sum(lons) / len(lons)
                self._process(w, lat, lon)
        except Exception:
            pass


def download_pbf():
    if os.path.exists(PBF_FILE):
        print(f"PBF vec postoji: {PBF_FILE}")
        return
    print("Preuzimam .pbf...")
    r = requests.get(PBF_URL, stream=True, timeout=300)
    with open(PBF_FILE, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024*1024):
            f.write(chunk)
    print("Download gotov.")


def main():
    download_pbf()
    print("Parsiram OSM podatke...")
    handler = OSMHandler()
    handler.apply_file(PBF_FILE, locations=True, idx='flex_mem')
    print(f"Pronadjeno: {len(handler.objects)} objekata.")

    conn = psycopg2.connect(CONN)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS kriticna_infrastruktura (
            id SERIAL PRIMARY KEY,
            kategorija VARCHAR(100),
            ime VARCHAR(255),
            naslov VARCHAR(255),
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION
        );
    """)
    cur.execute("TRUNCATE TABLE kriticna_infrastruktura RESTART IDENTITY;")
    conn.commit()
    print("Tabela ociscena. Upisujem u batch-ovima...")

    BATCH = 500
    total = len(handler.objects)
    for i in range(0, total, BATCH):
        batch = handler.objects[i:i+BATCH]
        cur.executemany("""
            INSERT INTO kriticna_infrastruktura (kategorija, ime, naslov, lat, lon)
            VALUES (%s, %s, %s, %s, %s)
        """, batch)
        conn.commit()
        print(f"  Upisano {min(i+BATCH, total)}/{total}...")

    conn.close()
    print("GOTOVO!")


if __name__ == "__main__":
    main()