import geopandas as gpd
import requests
import urllib3

# Isključujemo upozorenja
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URL za Registar prostornih enota (RPE)
wfs_url = "https://ipi.eprostor.gov.si/wfs-si-gurs-rpe/wfs"

# Parametri sa ispravnim nazivom sloja 'OBCINE'
params = {
    'service': 'WFS',
    'version': '2.0.0',
    'request': 'GetFeature',
    'typeName': 'OBCINE',      # Ovo je ispravan naziv prema dokumentaciji
    'outputFormat': 'GML3',    # GML3 je najsigurniji za eProstor
    'count': 10
}

print("Povezujem se na eProstor...")

try:
    # Preuzimanje podataka
    response = requests.get(wfs_url, params=params, timeout=30, verify=False)
    
    if response.status_code != 200:
        print("--- SERVER ERROR ---")
        # Ako server javi grešku, ispisaće nam tačan razlog
        print(response.text)
    else:
        # GeoPandas čita GML direktno iz sadržaja
        gdf = gpd.read_file(response.content)

        if not gdf.empty:
            # Izvoz u Excel
            df_for_excel = gdf.copy()
            df_for_excel['geometry'] = df_for_excel['geometry'].astype(str)
            
            # 1. Preveri, ali podatki sploh imajo določen koordinatni sistem (CRS)
            if gdf.crs is None:
                # GURS običajno uporablja slovenski EPSG:3912 ali 3794
                gdf.set_crs(epsg=3912, inplace=True)

            # 2. REPROJEKCIJA: Pretvori v WGS84 (stopinje), ki ga razume geojson.io
            gdf_gps = gdf.to_crs(epsg=4326)

            # 3. Shrani v GeoJSON
            output_geojson = "gurs_opstine_gps.geojson"
            gdf_gps.to_file(output_geojson, driver='GeoJSON')

            print(f"Uspeh! Zdaj povleci {output_geojson} na geojson.io")

            print(f"Uspeh! GeoJSON fajl je spreman: {output_geojson}")

            print(f"\nUSPEH! Preuzeto je {len(gdf)} opština.")
            print(f"Podaci su u fajlu: {output_geojson}")
            
            # Ispisujemo prva 3 reda da vidimo nazive kolona
            print("\nPregled podataka:")
            print(gdf.head(3))
        else:
            print("Server je odgovorio, ali nema podataka za ovaj sloj.")

except Exception as e:
    print(f"\nDošlo je do greške: {e}")