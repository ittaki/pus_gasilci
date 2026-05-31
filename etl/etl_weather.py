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

SOURCE_NAME = "ARSO Meteo"

STATIONS = [
    (46.0665, 14.5128, "Ljubljana"),
    (46.2397, 15.2678, "Celje"),
    (46.5547, 15.6459, "Maribor"),
    (45.5469, 13.7300, "Koper"),
    (46.3650, 13.7357, "Nova Gorica"),
    (46.4386, 14.3628, "Kranj"),
    (45.9050, 15.1739, "Novo Mesto"),
    (46.5233, 13.5647, "Bovec"),
    (46.3650, 14.1128, "Postojna"),
    (46.6597, 16.1667, "Murska Sobota"),
]

OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_station(lat, lon, name):
    params = {
        "latitude":        lat,
        "longitude":       lon,
        "current":         "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation",
        "wind_speed_unit": "ms",
        "timezone":        "Europe/Ljubljana",
    }
    resp = requests.get(OPENMETEO_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("current", {}), data.get("current_units", {})


def get_source_id(cursor):
    cursor.execute("SELECT id FROM source_system WHERE name = %s", (SOURCE_NAME,))
    row = cursor.fetchone()
    return row[0] if row else None


def insert_weather(rows):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    sql = """
        INSERT INTO weather_observation
            (source_id, station_code, station_name, observed_at,
             temp_c, wind_speed_ms, wind_dir_deg, precipitation_mm,
             humidity_pct, geom, raw_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                ST_GeomFromEWKT(%s), %s::jsonb)
    """
    cur.executemany(sql, rows)
    inserted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return inserted


def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Dohvatam meteo podatke (OpenMeteo)...")

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    source_id = get_source_id(cur)
    cur.close()
    conn.close()

    if not source_id:
        print(f"  GRESKA: '{SOURCE_NAME}' nije pronadjen u source_system!")
        return

    rows = []
    for lat, lon, name in STATIONS:
        try:
            current, units = fetch_station(lat, lon, name)
            time_str = current.get("time", "")
            try:
                obs_time = datetime.strptime(time_str[:16], "%Y-%m-%dT%H:%M")
                obs_time = obs_time.replace(tzinfo=timezone.utc)
            except Exception:
                obs_time = datetime.now(timezone.utc)

            temp     = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            wind_spd = current.get("wind_speed_10m")
            wind_dir = current.get("wind_direction_10m")
            precip   = current.get("precipitation")
            geom_wkt = f"SRID=4326;POINT({lon} {lat})"
            raw      = {**current, "station_name": name, "lat": lat, "lon": lon}

            rows.append((
                source_id,
                f"OM_{name.upper().replace(' ', '_')}",
                name, obs_time,
                temp, wind_spd, wind_dir, precip, humidity,
                geom_wkt, json.dumps(raw)
            ))
            print(f"  {name}: {temp}C, vjetar {wind_spd} m/s")
        except Exception as e:
            print(f"  GRESKA za {name}: {e}")
            continue

    if not rows:
        print("  Nema podataka.")
        return

    inserted = insert_weather(rows)
    print(f"\n  Upisano: {inserted} postaja u bazu.")
    print("  Gotovo!")


if __name__ == "__main__":
    main()