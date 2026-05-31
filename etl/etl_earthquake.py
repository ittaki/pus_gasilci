import os
import requests
import psycopg2
from datetime import datetime, timezone
import json
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "dbname":   os.getenv("DB_NAME", "gasilci_dev"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# EMSC SeismicPortal - pokriva Sloveniju, koristi ARSO podatke
EMSC_URL = (
    "https://www.seismicportal.eu/fdsnws/event/1/query"
    "?format=json&limit=100"
    "&minlat=45.4&maxlat=46.9"
    "&minlon=13.3&maxlon=16.6"
    "&orderby=time"
)
SOURCE_NAME = "EMSC SeismicPortal"


def fetch_earthquakes():
    resp = requests.get(EMSC_URL, timeout=15)
    resp.raise_for_status()
    return resp.json().get("features", [])


def get_source_id(cursor):
    cursor.execute("SELECT id FROM source_system WHERE name = %s", (SOURCE_NAME,))
    row = cursor.fetchone()
    if not row:
        # Dodaj automatski ako ne postoji
        cursor.execute("""
            INSERT INTO source_system (name, category, spatial_level, format, access_type, freq, description, url)
            VALUES (%s, 'seismic', 'european', 'API/GeoJSON', 'open', 'real-time',
                    'European Mediterranean Seismological Centre – pokriva SI sa ARSO podacima',
                    'https://www.seismicportal.eu/fdsnws/event/1/')
            RETURNING id
        """, (SOURCE_NAME,))
        return cursor.fetchone()[0]
    return row[0]


def parse_event(event, source_id):
    props  = event.get("properties", {})
    coords = event.get("geometry", {}).get("coordinates", [0, 0, 0])

    lon   = float(coords[0])
    lat   = float(coords[1])
    depth = float(coords[2]) if len(coords) > 2 else 0.0

    time_str = props.get("time", "")
    try:
        event_time = datetime.strptime(time_str[:19], "%Y-%m-%dT%H:%M:%S")
        event_time = event_time.replace(tzinfo=timezone.utc)
    except Exception:
        event_time = None

    mag         = float(props.get("mag", 0) or 0)
    region      = props.get("flynn_region", "")
    external_id = event.get("id", "")
    geom_wkt    = f"SRID=4326;POINT({lon} {lat})" if lat and lon else None

    return (source_id, external_id, event_time, mag or None,
            depth or None, geom_wkt, region, False, props)


def upsert_earthquakes(events, source_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    rows = [parse_event(e, source_id) for e in events]
    rows = [r for r in rows if r[2] is not None]

    sql = """
        INSERT INTO earthquake_event
            (source_id, external_id, event_time, magnitude, depth_km,
             geom, region, felt, raw_data)
        VALUES (%s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s, %s, %s::jsonb)
        ON CONFLICT (external_id) DO NOTHING
    """

    rows_json = [
        (r[0], r[1], r[2], r[3], r[4],
         r[5], r[6], r[7], json.dumps(r[8]))
        for r in rows
    ]

    cur.executemany(sql, rows_json)
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted, len(rows)


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Dohvatam potrese sa EMSC...")

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    source_id = get_source_id(cur)
    conn.commit()
    cur.close()
    conn.close()

    events = fetch_earthquakes()
    print(f"  Pronađeno {len(events)} potresa u API odgovoru.")

    if not events:
        print("  Nema podataka.")
        return

    inserted, total = upsert_earthquakes(events, source_id)
    print(f"  Upisano: {inserted} novih / {total} parsiranih redova.")
    print("  Gotovo!")


if __name__ == "__main__":
    main()