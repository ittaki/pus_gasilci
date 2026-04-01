import geopandas as gpd
import requests
import urllib3
import os


# FETCHING THE BUILDINGS FROM GURS WFS SOURCE - GetCapabilities request

# Disable SSL warnings for government servers
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. THE VERIFIED ENDPOINT
wfs_url = "https://ipi.eprostor.gov.si/wfs-si-gurs-ins/bu-core2d/wfs"

# 2. AREA OF INTEREST (Ljubljana Center)
# We use EPSG:3794 (Slovenian national grid in meters)
center_x, center_y = 462000, 101000
buffer = 500  # 500 meters radius
bbox_coords = f"{center_x-buffer},{center_y-buffer},{center_x+buffer},{center_y+buffer},EPSG:3794"

# 3. WFS PARAMETERS
# based on the GetCapabilities XML you provided
params = {
    'service': 'WFS',
    'version': '2.0.0',
    'request': 'GetFeature',
    'typeName': 'bu-core2d:Building',  # The official layer name
    'outputFormat': 'application/gml+xml; version=3.2', # Specific GML version for INSPIRE
    'srsName': 'EPSG:3794',
    'bbox': bbox_coords,
    'count': 1000  # Limiting to 100 features for the test
}

print(f"Connecting to: {wfs_url}...")

try:
    # Perform the request
    response = requests.get(wfs_url, params=params, timeout=60, verify=False)
    
    if response.status_code == 200:
        # Check if the response is actually XML/GML and not an error page
        if b"ExceptionReport" in response.content:
            print("--- SERVER ERROR REPORT ---")
            print(response.text)
        else:
            # Read GML data into a GeoDataFrame
            gdf = gpd.read_file(response.content)

            if not gdf.empty:
                # REPROJECTION: Convert from Meters (3794) to GPS Degrees (4326)
                # mandatory for viewing on geojson.io
                gdf_gps = gdf.to_crs(epsg=4326)
                
                output_filename = "ljubljana_buildings_core2d.geojson"
                gdf_gps.to_file(output_filename, driver='GeoJSON')

                print(f"SUCCESS! Fetched {len(gdf)} buildings.")
                print(f"File saved to: {os.path.abspath(output_filename)}")
                
                # Preview the first few rows of data
                print("\nData Preview (Attributes):")
                print(gdf_gps[['id', 'geometry']].head())
            else:
                print("Request successful, but no buildings were found in this area.")
    else:
        print(f"HTTP Error {response.status_code}: {response.reason}")

except Exception as e:
    print(f"An unexpected error occurred: {e}")



try:
    response = requests.get(wfs_url, params=params, timeout=60, verify=False)
    
    if response.status_code == 200:
        gdf = gpd.read_file(response.content)

        if not gdf.empty:
            # --- THE SMART ID CHECK ---
            print("\n--- STEP 1: INSPECTING ORIGINAL COLUMNS ---")
            original_columns = gdf.columns.tolist()
            print(f"Original names from GURS: {original_columns}")

            # Usually, the ID is in 'gml_id' or it is the very first column (index 0)
            # grab the name of the first column dynamically
            original_id_name = original_columns[0] 
            print(f"Detected ID column: '{original_id_name}'")

            # --- STEP 2: DYNAMIC RENAMING ---
            gdf = gdf.rename(columns={original_id_name: 'Building_ID'})
            print(f"Renamed '{original_id_name}' -> 'Building_ID'")

            # --- STEP 3: REPROJECTION & SAVING ---
            gdf_gps = gdf.to_crs(epsg=4326)
            gdf_gps.to_file("ljubljana_stavbe_inspected.geojson", driver='GeoJSON')

            print("\nSUCCESS! Check your console above to see the original name.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")