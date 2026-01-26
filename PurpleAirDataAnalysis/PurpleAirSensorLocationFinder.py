import requests
import pandas as pd

# --- CONFIGURATION ---
API_READ_KEY = 'X'  # <--- PASTE KEY HERE

# Salt Lake & Davis Bounding Box
NW_LAT = 41.16
NW_LNG = -112.23
SE_LAT = 40.42
SE_LNG = -111.55

print("📍 Fetching sensor locations...")

url = "https://api.purpleair.com/v1/sensors"
params = {
    'api_key': API_READ_KEY,
    'fields': 'name,latitude,longitude', # We just need coordinates
    'location_type': 0, # Outdoor
    'nwlat': NW_LAT,
    'nwlng': NW_LNG,
    'selat': SE_LAT,
    'selng': SE_LNG
}

response = requests.get(url, params=params)
if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data['data'], columns=data['fields'])
    
    # Save this! We need it for the next step.
    df.to_csv('master_sensor_list.csv', index=False)
    print(f"✅ Success! Saved locations for {len(df)} sensors to 'master_sensor_list.csv'")
else:
    print("❌ Error:", response.text)