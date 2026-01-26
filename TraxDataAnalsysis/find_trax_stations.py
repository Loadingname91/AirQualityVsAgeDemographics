import requests
import json

API_TOKEN = '137c0900b54241d492a06f5af60d254a'

print("🔍 Searching for TRAX stations in Utah...")

# Try different search methods
search_url = "https://api.synopticdata.com/v2/stations/search"

# Method 1: Search by state and look for TRAX in name
print("\n1. Searching Utah stations for 'TRAX' or 'TRX' in name...")
params1 = {
    'token': API_TOKEN,
    'state': 'UT',
    'output': 'json'
}

try:
    response = requests.get(search_url, params=params1)
    response.raise_for_status()
    data = response.json()
    
    if 'STATION' in data:
        trax_stations = []
        for station in data['STATION']:
            name = station.get('NAME', '').upper()
            stid = station.get('STID', '').upper()
            if 'TRX' in stid or 'TRAX' in name or 'TRANSIT' in name:
                trax_stations.append(station)
        
        if trax_stations:
            print(f"   ✅ Found {len(trax_stations)} potential TRAX stations:")
            for s in trax_stations:
                print(f"      - {s.get('NAME')} (ID: {s.get('STID')})")
                print(f"        Location: {s.get('LATITUDE')}, {s.get('LONGITUDE')}")
                sensors = s.get('SENSOR_VARIABLES', {})
                if sensors:
                    pm_vars = [k for k in sensors.keys() if 'pm' in k.lower() or '25' in k.lower()]
                    if pm_vars:
                        print(f"        PM2.5 variables: {pm_vars}")
        else:
            print(f"   ⚠️ No TRAX stations found in {len(data['STATION'])} Utah stations")
            print(f"   Showing first 10 Utah stations for reference:")
            for s in data['STATION'][:10]:
                print(f"      - {s.get('NAME')} (ID: {s.get('STID')})")
    else:
        print(f"   Response: {data}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Method 2: Try searching by network
print("\n2. Searching by network...")
params2 = {
    'token': API_TOKEN,
    'network': '1,2,3,4,5,6,7,8,9,10',
    'state': 'UT',
    'output': 'json'
}

try:
    response = requests.get(search_url, params=params2)
    if response.status_code == 200:
        data = response.json()
        if 'STATION' in data:
            print(f"   Found {len(data['STATION'])} stations in networks")
except:
    pass

# Method 3: List all available networks
print("\n3. Checking available networks...")
networks_url = "https://api.synopticdata.com/v2/networks"
params3 = {
    'token': API_TOKEN,
    'output': 'json'
}

try:
    response = requests.get(networks_url, params=params3)
    if response.status_code == 200:
        data = response.json()
        if 'NETWORKS' in data:
            print(f"   Available networks:")
            for net in data['NETWORKS'][:20]:  # Show first 20
                print(f"      - {net.get('NAME')} (ID: {net.get('ID')})")
except Exception as e:
    print(f"   ⚠️ Could not fetch networks: {e}")

print("\n" + "="*60)
print("💡 Tip: If TRAX stations aren't found, you may need to:")
print("   1. Contact Synoptic support to get access")
print("   2. Use different station IDs")
print("   3. Check if TRAX data is under a different network")
print("="*60)

