import geopandas as gpd
import pandas as pd
import requests
import urllib3
import os
from shapely import wkt


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url_geometrija = "https://ipi.eprostor.gov.si/wfs-si-gurs-ins/us-net-common/wfs"
bbox_ljubljana = "46.045,14.495,46.055,14.515"

params = {
    'service': 'WFS',
    'version': '1.1.0',
    'request': 'GetFeature',
    'typeName': 'us-net-common:UtilityLink',
    'srsName': 'EPSG:4258',
    'bbox': bbox_ljubljana,
    'count': 500 
}

def main():
    print(f"Povezujem se na GURS...")
    
    try:
        response = requests.get(url_geometrija, params=params, verify=False, timeout=30)
        
        if response.status_code != 200:
            print(f"Napaka strežnika: {response.status_code}")
            return

        temp_filename = "voda_temp.gml"
        with open(temp_filename, "wb") as f:
            f.write(response.content)
        
        print("Podatki prejeti. Pretvarjam besedilne koordinate v črte...")

        # Preberemo kot navadno tabelo najprej
        df = gpd.read_file(temp_filename)

        if df.empty:
            print("Napaka: Prejeti podatki so prazni.")
            return

        # KLJUČNI POPRAVEK: Prisila pretvorbe stolpca v geometrijo
        target_col = 'centrelineGeometry'
        
        if target_col in df.columns:
            # Če je stolpcu besedilo (WKT), ga pretvorimo v Shape objekti
            if not hasattr(df[target_col], 'geom_type'):
                print("Pretvarjam WKT nize v geometrijske objekte...")
                df[target_col] = df[target_col].apply(wkt.loads)
            
            # Ustvarimo pravi GeoDataFrame
            gdf = gpd.GeoDataFrame(df, geometry=target_col, crs="EPSG:4258")
            print(f"Uspešno aktivirana geometrija.")
        else:
            print(f"Napaka: Stolpec '{target_col}' ni bil najden.")
            return

        # Izvoz v GeoJSON
        output_file = "koncne_cevi.geojson"
        gdf.to_crs(epsg=4326).to_file(output_file, driver='GeoJSON')

        print("-" * 40)
        print(f"ZMAGA! Datoteka je pripravljena: {output_file}")
        print("-" * 40)

        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    except Exception as e:
        # Če se koda ustavi tukaj, poskusi še s tem 'brutalnim' popravkom:
        print(f"Prišlo je do napake, poskušam sekundarno metodo...")
        try:
            # Nekatere verzije geopandasa potrebujejo tole:
            df['geometry'] = gpd.GeoSeries.from_wkt(df['centrelineGeometry'])
            gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4258")
            gdf.to_crs(epsg=4326).to_file("koncne_cevi.geojson", driver='GeoJSON')
            print("Sekundarna metoda uspela!")
        except:
            print(f"Končna napaka: {e}")


if __name__ == "__main__":
    main()