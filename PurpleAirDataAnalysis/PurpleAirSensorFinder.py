import requests

# --- CONFIGURATION ---
API_READ_KEY = 'X' # Paste your key here

# Salt Lake & Davis County Bounding Box
NW_LAT = 41.16  # North (Farmington/Ogden)
NW_LNG = -112.23 # West (Great Salt Lake)
SE_LAT = 40.42  # South (Point of the Mountain)
SE_LNG = -111.55 # East (Wasatch Mountains)

def get_sensor_ids_for_tool():
    print("🔍 Scanning Northern Utah for outdoor sensors...")
    
    url = "https://api.purpleair.com/v1/sensors"
    
    # We only need the ID (index) and location_type (to ensure they are outdoor)
    params = {
        'api_key': API_READ_KEY,
        'fields': 'location_type', 
        'location_type': 0,  # 0 = Outdoor only
        'nwlat': NW_LAT,
        'nwlng': NW_LNG,
        'selat': SE_LAT,
        'selng': SE_LNG
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        sensors = data['data']
        
        # Extract just the IDs (the first item in each row)
        # The API returns data like: [[12345, 0], [67890, 0], ...]
        id_list = [str(s[0]) for s in sensors]
        
        # Join them with commas
        formatted_string = ",".join(id_list)
        
        print(f"✅ Found {len(id_list)} sensors.")
        
        # Save to a text file
        with open("sensor_ids_for_website.txt", "w") as f:
            f.write(formatted_string)
            
        print("📁 Saved list to 'sensor_ids_for_website.txt'")
        print("👇 You can also copy it right here:")
        print("-" * 20)
        print(formatted_string)
        print("-" * 20)
        
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    get_sensor_ids_for_tool()