import requests
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# 1. PASTE YOUR TOKEN HERE
API_TOKEN = '137c0900b54241d492a06f5af60d254a' 

# 2. SELECT DATES (The Inversion Event)
# Format: YYYYMMDDHHMM (UTC Time)
# Note: API token may only have access to recent data (last 1 year)
# For 2025 data, you may need Enterprise access
# Suggestion: Try recent dates or contact Synoptic for historical access
START_TIME = '202512010000'
END_TIME   = '202512310000'

# Alternative: Try more recent dates if 2025 data isn't accessible
# START_TIME = '202412140000'  # Dec 14, 2024
# END_TIME   = '202412170000'  # Dec 17, 2024

# ==========================================
# 3. STATION IDs (TRAX Mobile Sensors)
# ==========================================
# TRX01: Red/Green Line Train (Car 1136)
# TRX02: Red/Green Line Train (Car 1104)
# TRX03: Blue Line Train (Car 1034)
# TRX04: Newer Train (if active)

STATION_IDS = 'TRX01,TRX02,TRX03'

def check_available_variables():
    """First, check what variables are available for these stations"""
    print("🔍 Checking available variables for TRAX stations...")
    url = "https://api.synopticdata.com/v2/stations/metadata"
    params = {
        'token': API_TOKEN,
        'stid': STATION_IDS,
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"📊 Metadata Response Keys: {list(data.keys())}")
        if 'SUMMARY' in data:
            print(f"   Summary: {data['SUMMARY']}")
        
        if 'STATION' in data and len(data['STATION']) > 0:
            for station in data['STATION']:
                print(f"\n📡 Station: {station.get('NAME', 'Unknown')} ({station.get('STID', 'Unknown')})")
                sensors = station.get('SENSOR_VARIABLES', {})
                if sensors:
                    print(f"   Available variables:")
                    for var, info in sensors.items():
                        desc = info.get('description', 'No description') if isinstance(info, dict) else str(info)
                        print(f"     - {var}: {desc}")
                else:
                    print(f"   ⚠️ No sensor variables found in metadata")
                    print(f"   Station keys: {list(station.keys())}")
        else:
            print(f"   ⚠️ No stations found. Trying to search for TRAX stations...")
            # Try searching for TRAX stations
            search_params = {
                'token': API_TOKEN,
                'network': '1,2,3,4,5,6,7,8,9,10',  # Try common networks
                'state': 'UT',
                'output': 'json'
            }
            search_url = "https://api.synopticdata.com/v2/stations/search"
            search_response = requests.get(search_url, params=search_params)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if 'STATION' in search_data:
                    trax_stations = [s for s in search_data['STATION'] if 'TRX' in s.get('STID', '') or 'TRAX' in s.get('NAME', '').upper()]
                    if trax_stations:
                        print(f"   Found {len(trax_stations)} potential TRAX stations:")
                        for s in trax_stations[:5]:  # Show first 5
                            print(f"     - {s.get('NAME')} ({s.get('STID')})")
    except Exception as e:
        print(f"❌ Error checking variables: {e}")
        import traceback
        traceback.print_exc()

def fetch_trax_history():
    print(f"🚆 Fetching Synoptic Data ({START_TIME} to {END_TIME})...")
    print(f"   Note: These are EPA monitoring stations (not TRAX mobile sensors)")
    print(f"   Stations: {STATION_IDS}")
    
    url = "https://api.synopticdata.com/v2/stations/timeseries"
    
    # First, try without specifying vars to see what's available
    print("   Step 1: Checking what data is available (no variable filter)...")
    params_no_var = {
        'token': API_TOKEN,
        'stid': STATION_IDS,
        'start': START_TIME,
        'end': END_TIME,
        'obtimezone': 'utc',
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params_no_var)
        response.raise_for_status()
        data = response.json()
        
        if 'STATION' in data and len(data['STATION']) > 0:
            print(f"   ✅ Found {len(data['STATION'])} station(s) with data!")
            pm_keys_found = []
            for station in data['STATION']:
                obs = station.get('OBSERVATIONS', {})
                print(f"   Station {station.get('STID')} ({station.get('NAME')}) observation keys: {list(obs.keys())}")
                # Look for any PM2.5 related keys
                pm_keys = [k for k in obs.keys() if 'pm' in k.lower() or '25' in k.lower()]
                if pm_keys:
                    print(f"      ✅ Potential PM2.5 keys: {pm_keys}")
                    pm_keys_found.extend(pm_keys)
                # Also check for any data keys
                if obs:
                    print(f"      All observation keys: {list(obs.keys())[:10]}")  # Show first 10
            
            # If we found PM2.5 keys, try processing with the first one
            if pm_keys_found:
                pm_var = list(set(pm_keys_found))[0]  # Get unique first key
                print(f"\n   🎯 Attempting to process data with variable: {pm_var}")
                process_trax_data(data, pm_var)
                return
        elif 'SUMMARY' in data:
            print(f"   Response: {data['SUMMARY']}")
    except Exception as e:
        print(f"   ⚠️ Error checking available data: {e}")
        import traceback
        traceback.print_exc()
    
    # Try common PM2.5 variable names
    print("\n   Step 2: Trying specific PM2.5 variable names...")
    pm25_vars = ['PM_25', 'PM25', 'pm25', 'PM25_concentration_set_1', 'PM25_QC', 'pm25_concentration']
    
    for var_name in pm25_vars:
        print(f"\n   Trying variable: {var_name}")
        params = {
            'token': API_TOKEN,
            'stid': STATION_IDS,
            'start': START_TIME,
            'end': END_TIME,
            'vars': var_name,
            'obtimezone': 'utc',
            'output': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check if we got data
            if 'STATION' in data and len(data['STATION']) > 0:
                print(f"   ✅ Found data with variable: {var_name}")
                # Process the data with this variable
                process_trax_data(data, var_name)
                return
            elif 'SUMMARY' in data:
                msg = data['SUMMARY'].get('RESPONSE_MESSAGE', '')
                if 'not a valid variable' not in msg.lower():
                    print(f"   ⚠️ {msg}")
        except Exception as e:
            print(f"   ❌ Error with {var_name}: {e}")
            continue
    
    print("\n❌ Could not find valid PM2.5 variable. Check available variables above.")

def process_trax_data(data, pm25_var):
    """Process the TRAX data from API response"""
    all_rows = []
    
    # Debug: Print API response structure
    print(f"\n📊 API Response Keys: {list(data.keys())}")
    if 'SUMMARY' in data:
        print(f"   Summary: {data['SUMMARY']}")
    
    # Parse the nested JSON structure
    if 'STATION' in data:
        print(f"   Found {len(data['STATION'])} station(s)")
        for station in data['STATION']:
            name = station.get('NAME', 'Unknown')
            id_ = station.get('STID', 'Unknown')
            print(f"   Processing: {name} ({id_})")
            
            # The 'OBSERVATIONS' block contains the lists
            obs = station.get('OBSERVATIONS', {})
            print(f"   Observation keys: {list(obs.keys())}")
            
            # Check if we have data
            if 'date_time' not in obs:
                print(f"   ⚠️ No timeline data for {name}")
                if obs:
                    print(f"   Available keys: {list(obs.keys())}")
                continue
                
            times = obs['date_time']
            print(f"   Found {len(times)} time points")
            
            # CRITICAL: Mobile data often has position INSIDE the observation list
            # We need to check where lat/lon are stored
            if 'position' in obs:
                # If position is dynamic (moving train)
                positions = obs['position']
                lats = [p[0] if isinstance(p, (list, tuple)) and len(p) > 0 else None for p in positions]
                lons = [p[1] if isinstance(p, (list, tuple)) and len(p) > 1 else None for p in positions]
                print(f"   Using dynamic position data")
            elif 'latitude' in obs and 'longitude' in obs:
                # Alternative: separate lat/lon arrays
                lats = obs['latitude']
                lons = obs['longitude']
                print(f"   Using separate lat/lon arrays")
            else:
                # Fallback to static station lat/lon
                lat = float(station.get('LATITUDE', 0))
                lon = float(station.get('LONGITUDE', 0))
                lats = [lat] * len(times)
                lons = [lon] * len(times)
                print(f"   Using static station location: ({lat}, {lon})")

            # Get PM2.5 values - try the provided variable name first
            pm_key = None
            if pm25_var in obs:
                pm_key = pm25_var
            else:
                # Find any key that contains pm25 (case insensitive)
                pm_key = next((k for k in obs.keys() if 'pm25' in k.lower() or 'pm_25' in k.lower()), None)
            
            if pm_key:
                vals = obs[pm_key]
                print(f"   Using PM2.5 key: {pm_key}, found {len(vals)} values")
                
                # Combine into rows
                for i, (t, pm) in enumerate(zip(times, vals)):
                    if pm is not None and i < len(lats) and i < len(lons): # Skip missing readings
                        all_rows.append({
                            'train_id': id_,
                            'time': t,
                            'lat': lats[i] if lats[i] is not None else None,
                            'lon': lons[i] if lons[i] is not None else None,
                            'pm25': pm
                        })
            else:
                print(f"   ⚠️ Could not find PM2.5 data in observations")
                print(f"   Available observation keys: {list(obs.keys())}")
    
    # Save to CSV
    if all_rows:
        df = pd.DataFrame(all_rows)
        # Remove rows with missing coordinates
        df = df.dropna(subset=['lat', 'lon'])
        output_filename = 'trax_mobile_data.csv'
        df.to_csv(output_filename, index=False)
        print(f"\n✅ Success! Saved {len(df)} GPS points to '{output_filename}'")
        print(f"\n📊 Data Summary:")
        print(f"   Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"   PM2.5 range: {df['pm25'].min():.2f} - {df['pm25'].max():.2f} µg/m³")
        print(f"   PM2.5 mean: {df['pm25'].mean():.2f} µg/m³")
        print(f"\n   First few rows:")
        print(df.head())
    else:
        print("\n❌ No valid data rows found after processing.")

if __name__ == "__main__":
    # First check what variables are available
    check_available_variables()
    print("\n" + "="*60 + "\n")
    # Then fetch the data
    fetch_trax_history()