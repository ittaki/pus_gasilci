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

FIRMS_KEY   = os.getenv("NASA_FIRMS_KEY", "")
SOURCE_NAME = "NASA FIRMS"

# Slovenija bounding box, zadnjih 10 dana, VIIRS satelit
FIRMS_URL = (
    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{FIRMS_KEY}"
    f"/VIIRS_SNPP_NRT/13.3,45.4,16.6,46.9/10"
)


def fetch_hotspots():
    resp = requests.get(FIRMS_URL, timeout=30)
    resp.raise_for_status()
    lines = resp.text.strip().split("\n")
    if len(lines) < 2:
        return []
    headers = [h.strip() for h in lines[0].split(",")]
    rows = []
    for line in lines[1:]:
        vals = [v.strip() for v in line.split(",")]
        if len(vals) == len(headers):
            rows.append(dict(zip(headers, vals)))
    return rows


def get_source_id(cursor):
    cursor.execute("SELECT id FROM source_system WHERE name = %s", (SOURCE_NAME,))
    row = cursor.fetchone()
    return row[0] if row else None


def parse_hotspot(row, source_id):
    try:
        lat = float(row.get("latitude", 0))
        lon = float(row.get("longitude", 0))
        confidence = row.get("confidence", "0")
        confidence = int(confidence) if confidence.isdigit() else 50
        frp = float(row.get("frp", 0) or 0)
        satellite = row.get("satellite", "VIIRS")

        acq_date = row.get("acq_date", "")
        acq_time = row.get("acq_time", "0000").zfill(4)
        dt_str   = f"{acq_date} {acq_time[:2]}:{acq_time[2:]}"
        detected_at = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        detected_at = detected_at.replace(tzinfo=timezone.utc)

        external_id = f"firms_{acq_date}_{acq_time}_{lat}_{lon}"
        geom_wkt    = f"SRID=4326;POINT({lon} {lat})"

        return (source_id, detected_at, geom_wkt,
                confidence, frp, satellite, external_id, row)
    except Exception as e:
        print(f"  Parse greška: {e} | row: {row}")
        return None


def upsert_hotspots(rows, source_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    parsed = [parse_hotspot(r, source_id) for r in rows]
    parsed = [p for p in parsed if p is not None]

    sql = """
        INSERT INTO fire_hotspot
            (source_id, detected_at, geom, confidence,
             frp, satellite, raw_data)
        VALUES (%s, %s, ST_GeomFromEWKT(%s), %s, %s, %s, %s::jsonb)
    """

    data = [
        (p[0], p[1], p[2], p[3], p[4], p[5], json.dumps(p[7]))
        for p in parsed
    ]

    cur.executemany(sql, data)
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted, len(parsed)


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Dohvatam fire hotspots sa NASA FIRMS...")

    if not FIRMS_KEY:
        print("  GREŠKA: NASA_FIRMS_KEY nije postavljen u .env!")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    source_id = get_source_id(cur)
    cur.close()
    conn.close()

    if not source_id:
        print(f"  GREŠKA: '{SOURCE_NAME}' nije pronađen u source_system!")
        return

    rows = fetch_hotspots()
    print(f"  Pronađeno {len(rows)} hotspots.")

    if not rows:
        print("  Nema aktivnih požara u posljednjih 10 dana za Sloveniju.")
        return

    inserted, total = upsert_hotspots(rows, source_id)
    print(f"  Upisano: {inserted} novih / {total} parsiranih redova.")
    print("  Gotovo!")


if __name__ == "__main__":
    main()