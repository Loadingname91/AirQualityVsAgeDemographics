"""
PurpleAir PM2.5 Analysis Script
Analyzes PM2.5 data from PurpleAir sensors alongside 80+ population demographics.

This script uses the reusable lib/ modules and adds PurpleAir-specific data loading.
"""

import os
import glob
import pandas as pd

# Import reusable library modules
from lib.census import load_shapefile, load_census_data, merge_geo_census
from lib.interpolation import create_pm25_grid
from lib.visualization import create_static_map, create_interactive_map


# =============================================================================
# Configuration
# =============================================================================
DATA_DIR = "Data"
SHAPEFILE_PATH = os.path.join(DATA_DIR, "tl_2025_49_tract", "tl_2025_49_tract.shp")
CENSUS_DATA_PATH = os.path.join(DATA_DIR, "ACSData", "ACSDT5Y2023.B01001-Data.csv")
SENSOR_LIST_PATH = "master_sensor_list.csv"
PURPLEAIR_DIR = os.path.join(DATA_DIR, "Pm2.5Data", "PurpleAir Download 1-25-2026")

# Output files
OUTPUT_PNG = "output/purpleair_analysis_map.png"
OUTPUT_HTML = "output/purpleair_analysis_interactive.html"

# Counties: Salt Lake (49035) and Davis (49011)
COUNTY_FIPS = ["49035", "49011"]

# PM2.5 Correction Formula (University of Utah Winter Inversion)
# Corrected PM2.5 = (0.778 * Raw_CF1) + 2.65
PM25_CORRECTION_SLOPE = 0.778
PM25_CORRECTION_INTERCEPT = 2.65

# Outlier threshold (physically impossible ambient PM2.5)
PM25_OUTLIER_THRESHOLD = 500


# =============================================================================
# PurpleAir-Specific Data Loading
# =============================================================================
def load_sensor_locations(sensor_list_path):
    """Load master sensor list with lat/lon coordinates."""
    sensors = pd.read_csv(sensor_list_path)
    sensor_lookup = {}
    for _, row in sensors.iterrows():
        sensor_lookup[int(row['sensor_index'])] = (row['latitude'], row['longitude'])
    return sensor_lookup


def process_purpleair_data(purpleair_dir, sensor_lookup):
    """
    Process PurpleAir CSV files and apply correction formula.
    
    Returns:
        tuple: (air_df DataFrame, date_range dict)
    """
    print("\nProcessing PurpleAir sensor data...")
    
    csv_pattern = os.path.join(purpleair_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)
    total_files = len(csv_files)
    print(f"  Found {total_files} sensor files")
    
    # Extract date range from filename
    date_range = {'start_date': None, 'end_date': None, 'interval': '60-Minute'}
    if csv_files:
        try:
            sample = os.path.basename(csv_files[0]).split()
            if len(sample) >= 4:
                date_range['start_date'] = sample[1]
                date_range['end_date'] = sample[2]
                date_range['interval'] = sample[3]
        except:
            pass
    
    if date_range['start_date']:
        print(f"  Data period: {date_range['start_date']} to {date_range['end_date']} ({date_range['interval']} averages)")
    
    air_data = []
    processed = 0
    skipped = 0
    outliers = 0
    
    for csv_file in csv_files:
        try:
            filename = os.path.basename(csv_file)
            sensor_id = int(filename.split()[0])
            
            if sensor_id not in sensor_lookup:
                skipped += 1
                continue
            
            lat, lon = sensor_lookup[sensor_id]
            df = pd.read_csv(csv_file)
            
            if 'pm2.5_cf_1' not in df.columns:
                skipped += 1
                continue
            
            raw_pm25 = df['pm2.5_cf_1'].mean()
            if pd.isna(raw_pm25):
                skipped += 1
                continue
            
            # Apply correction formula
            corrected_pm25 = (PM25_CORRECTION_SLOPE * raw_pm25) + PM25_CORRECTION_INTERCEPT
            
            # Filter outliers
            if corrected_pm25 > PM25_OUTLIER_THRESHOLD:
                print(f"  WARNING: Sensor {sensor_id} dropped - PM2.5 {corrected_pm25:.1f} exceeds {PM25_OUTLIER_THRESHOLD} µg/m³")
                outliers += 1
                continue
            
            air_data.append({
                'lat': lat, 'lon': lon,
                'pm25': corrected_pm25,
                'sensor_id': sensor_id
            })
            processed += 1
            
            if processed % 50 == 0:
                print(f"  Processed {processed}/{total_files} sensors...")
                
        except Exception as e:
            skipped += 1
            continue
    
    print(f"  Successfully processed: {processed} sensors")
    print(f"  Skipped (missing data): {skipped}")
    print(f"  Dropped (outliers): {outliers}")
    
    air_df = pd.DataFrame(air_data)
    
    if len(air_df) > 0:
        print(f"  PM2.5 range: {air_df['pm25'].min():.1f} - {air_df['pm25'].max():.1f} µg/m³")
        print(f"  PM2.5 mean: {air_df['pm25'].mean():.1f} µg/m³")
    
    return air_df, date_range


# =============================================================================
# Main Pipeline
# =============================================================================
def main():
    print("=" * 60)
    print("PurpleAir PM2.5 Analysis")
    print("Salt Lake & Davis Counties, Utah")
    print("=" * 60)
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Step 1: Load and filter census tract shapefile
    gdf = load_shapefile(SHAPEFILE_PATH, COUNTY_FIPS)
    
    # Step 2: Load census demographics
    census_df = load_census_data(CENSUS_DATA_PATH)
    merged_gdf = merge_geo_census(gdf, census_df)
    
    # Step 3: Load PurpleAir sensor data
    sensor_lookup = load_sensor_locations(SENSOR_LIST_PATH)
    air_df, date_range = process_purpleair_data(PURPLEAIR_DIR, sensor_lookup)
    
    if len(air_df) == 0:
        print("\nERROR: No valid sensor data found.")
        return
    
    # Step 4: Create PM2.5 interpolation grid
    bounds = merged_gdf.total_bounds
    grid_x, grid_y, grid_pm25 = create_pm25_grid(air_df, bounds, resolution=200)
    
    # Step 5: Generate visualizations
    create_static_map(
        merged_gdf, grid_x, grid_y, grid_pm25, air_df,
        date_range=date_range,
        output_file=OUTPUT_PNG,
        title_suffix="\n(PurpleAir Sensors)"
    )
    
    create_interactive_map(
        merged_gdf, air_df,
        date_range=date_range,
        output_file=OUTPUT_HTML,
        title_suffix=" (PurpleAir)"
    )
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"  Static map:      {OUTPUT_PNG}")
    print(f"  Interactive map: {OUTPUT_HTML}")
    print("=" * 60)


if __name__ == "__main__":
    main()

