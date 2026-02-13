"""
Calculate comprehensive descriptive statistics for all datasets.
"""

import pandas as pd
import numpy as np
import os

# =============================================================================
# EPA Data Statistics
# =============================================================================
print("=" * 60)
print("EPA Data Descriptive Statistics")
print("=" * 60)

epa_data_path = "EPADataAnalysis/epa_utah_data.csv"
df_epa = pd.read_csv(epa_data_path)
df_epa['date_local'] = pd.to_datetime(df_epa['date_local'])

# Overall statistics (all dates)
print("\n1. Overall Statistics (All Dates):")
print(f"   Total Records: {len(df_epa):,}")
print(f"   Date Range: {df_epa['date_local'].min().date()} to {df_epa['date_local'].max().date()}")
print(f"   Monitoring Sites: {df_epa['site_number'].nunique()}")
stats_all = df_epa['pm25_value'].describe()
print(f"   Mean PM2.5: {stats_all['mean']:.2f} µg/m³")
print(f"   Median PM2.5: {stats_all['50%']:.2f} µg/m³")
print(f"   Std Dev: {stats_all['std']:.2f} µg/m³")
print(f"   Min: {stats_all['min']:.2f} µg/m³")
print(f"   Max: {stats_all['max']:.2f} µg/m³")
print(f"   25th Percentile: {stats_all['25%']:.2f} µg/m³")
print(f"   75th Percentile: {stats_all['75%']:.2f} µg/m³")

# January 1-25, 2025 period
jan_mask = (df_epa['date_local'] >= '2025-01-01') & (df_epa['date_local'] <= '2025-01-25')
df_jan = df_epa[jan_mask].copy()
print("\n2. January 1-25, 2025 Period:")
print(f"   Records: {len(df_jan):,}")
stats_jan = df_jan['pm25_value'].describe()
print(f"   Mean PM2.5: {stats_jan['mean']:.2f} µg/m³")
print(f"   Median PM2.5: {stats_jan['50%']:.2f} µg/m³")
print(f"   Std Dev: {stats_jan['std']:.2f} µg/m³")
print(f"   Min: {stats_jan['min']:.2f} µg/m³")
print(f"   Max: {stats_jan['max']:.2f} µg/m³")

# Inversion event (Jan 14-30, 2025)
inv_mask = (df_epa['date_local'] >= '2025-01-14') & (df_epa['date_local'] <= '2025-01-30')
df_inv = df_epa[inv_mask].copy()
print("\n3. Inversion Event (Jan 14-30, 2025):")
print(f"   Records: {len(df_inv):,}")
stats_inv = df_inv['pm25_value'].describe()
print(f"   Mean PM2.5: {stats_inv['mean']:.2f} µg/m³")
print(f"   Median PM2.5: {stats_inv['50%']:.2f} µg/m³")
print(f"   Std Dev: {stats_inv['std']:.2f} µg/m³")
print(f"   Min: {stats_inv['min']:.2f} µg/m³")
print(f"   Max: {stats_inv['max']:.2f} µg/m³")

# By site statistics
print("\n4. By Site Statistics (Inversion Period):")
site_stats = df_inv.groupby(['site_number', 'local_site_name']).agg({
    'pm25_value': ['count', 'mean', 'min', 'max', 'std']
}).round(2)
site_stats.columns = ['Count', 'Mean', 'Min', 'Max', 'Std']
print(site_stats.to_string())

# AQI category breakdown for inversion period
print("\n5. AQI Category Breakdown (Inversion Period):")
good = len(df_inv[df_inv['pm25_value'] < 12])
moderate = len(df_inv[(df_inv['pm25_value'] >= 12) & (df_inv['pm25_value'] < 35)])
unhealthy = len(df_inv[df_inv['pm25_value'] >= 35])
total = len(df_inv)
print(f"   Good (<12 µg/m³): {good:,} ({good/total*100:.1f}%)")
print(f"   Moderate (12-35 µg/m³): {moderate:,} ({moderate/total*100:.1f}%)")
print(f"   Unhealthy (>35 µg/m³): {unhealthy:,} ({unhealthy/total*100:.1f}%)")

# =============================================================================
# PurpleAir Data Statistics
# =============================================================================
print("\n" + "=" * 60)
print("PurpleAir Data Descriptive Statistics")
print("=" * 60)

# We need to process PurpleAir data similar to the main script
import glob
sensor_list_path = "PurpleAirDataAnalysis/master_sensor_list.csv"
purpleair_dir = "Data/PurpleAirData-Pm2.5Data/PurpleAir Download 1-25-2026"

sensors = pd.read_csv(sensor_list_path)
sensor_lookup = {}
for _, row in sensors.iterrows():
    sensor_lookup[int(row['sensor_index'])] = (row['latitude'], row['longitude'])

csv_files = glob.glob(os.path.join(purpleair_dir, "*.csv"))
print(f"\n1. Sensor Network Summary:")
print(f"   Total Sensor Files: {len(csv_files)}")
print(f"   Sensors in Master List: {len(sensors)}")

air_data = []
for csv_file in csv_files:
    try:
        filename = os.path.basename(csv_file)
        sensor_id = int(filename.split()[0])
        
        if sensor_id not in sensor_lookup:
            continue
        
        lat, lon = sensor_lookup[sensor_id]
        df = pd.read_csv(csv_file)
        
        if 'pm2.5_cf_1' not in df.columns:
            continue
        
        raw_pm25 = df['pm2.5_cf_1'].mean()
        
        if pd.isna(raw_pm25):
            continue
        
        # Apply correction formula
        corrected_pm25 = (0.778 * raw_pm25) + 2.65
        
        # Filter outliers
        if corrected_pm25 > 500:
            continue
        
        air_data.append({
            'lat': lat,
            'lon': lon,
            'pm25': corrected_pm25,
            'sensor_id': sensor_id
        })
    except:
        continue

air_df = pd.DataFrame(air_data)
print(f"   Valid Sensors Processed: {len(air_df)}")

if len(air_df) > 0:
    print("\n2. PM2.5 Distribution Statistics:")
    stats_pa = air_df['pm25'].describe()
    print(f"   Count: {int(stats_pa['count']):,}")
    print(f"   Mean: {stats_pa['mean']:.2f} µg/m³")
    print(f"   Median: {stats_pa['50%']:.2f} µg/m³")
    print(f"   Std Dev: {stats_pa['std']:.2f} µg/m³")
    print(f"   Min: {stats_pa['min']:.2f} µg/m³")
    print(f"   Max: {stats_pa['max']:.2f} µg/m³")
    print(f"   25th Percentile: {stats_pa['25%']:.2f} µg/m³")
    print(f"   75th Percentile: {stats_pa['75%']:.2f} µg/m³")
    
    print("\n3. AQI Category Breakdown:")
    good_pa = len(air_df[air_df['pm25'] < 12])
    moderate_pa = len(air_df[(air_df['pm25'] >= 12) & (air_df['pm25'] < 35)])
    unhealthy_pa = len(air_df[air_df['pm25'] >= 35])
    total_pa = len(air_df)
    print(f"   Good (<12 µg/m³): {good_pa} ({good_pa/total_pa*100:.1f}%)")
    print(f"   Moderate (12-35 µg/m³): {moderate_pa} ({moderate_pa/total_pa*100:.1f}%)")
    print(f"   Unhealthy (>35 µg/m³): {unhealthy_pa} ({unhealthy_pa/total_pa*100:.1f}%)")
    
    print("\n4. Spatial Distribution:")
    print(f"   Latitude Range: {air_df['lat'].min():.4f} to {air_df['lat'].max():.4f}")
    print(f"   Longitude Range: {air_df['lon'].min():.4f} to {air_df['lon'].max():.4f}")

# =============================================================================
# Census Data Statistics
# =============================================================================
print("\n" + "=" * 60)
print("Census Data Descriptive Statistics")
print("=" * 60)

census_path = "Data/ACSData/ACSDT5Y2023.B01001-Data.csv"
df_census = pd.read_csv(census_path, skiprows=[1], low_memory=False)

# Columns for 65+ population (Male 65-85+, Female 65-85+)
age_columns = ['B01001_020E', 'B01001_021E', 'B01001_022E', 'B01001_023E', 'B01001_024E', 'B01001_025E',
               'B01001_044E', 'B01001_045E', 'B01001_046E', 'B01001_047E', 'B01001_048E', 'B01001_049E']
for col in age_columns:
    df_census[col] = pd.to_numeric(df_census[col], errors='coerce').fillna(0)

df_census['pop_65_plus'] = df_census[age_columns].sum(axis=1)
df_census['GEOID'] = df_census['GEO_ID'].str.replace('1400000US', '', regex=False)

# Filter to Salt Lake and Davis counties
salt_lake_mask = df_census['GEOID'].str.startswith('49035')
davis_mask = df_census['GEOID'].str.startswith('49011')
study_area = df_census[salt_lake_mask | davis_mask].copy()

# Filter to inhabited tracts
inhabited = study_area[study_area['pop_80_plus'] > 0].copy()

print("\n1. Population 80+ Summary:")
print(f"   Total Tracts in Study Area: {len(study_area)}")
print(f"   Inhabited Tracts (pop_80+ > 0): {len(inhabited)}")
print(f"   Total 80+ Population: {inhabited['pop_80_plus'].sum():,.0f}")

print("\n2. Tract-Level Distribution:")
stats_tract = inhabited['pop_80_plus'].describe()
print(f"   Mean per Tract: {stats_tract['mean']:.1f}")
print(f"   Median per Tract: {stats_tract['50%']:.1f}")
print(f"   Std Dev: {stats_tract['std']:.1f}")
print(f"   Min: {stats_tract['min']:.0f}")
print(f"   Max: {stats_tract['max']:.0f}")
print(f"   25th Percentile: {stats_tract['25%']:.1f}")
print(f"   75th Percentile: {stats_tract['75%']:.1f}")

print("\n3. Population Distribution by County:")
salt_lake_tracts = inhabited[inhabited['GEOID'].str.startswith('49035')]
davis_tracts = inhabited[inhabited['GEOID'].str.startswith('49011')]
print(f"   Salt Lake County:")
print(f"     Tracts: {len(salt_lake_tracts)}")
print(f"     Total 80+ Population: {salt_lake_tracts['pop_80_plus'].sum():,.0f}")
print(f"   Davis County:")
print(f"     Tracts: {len(davis_tracts)}")
print(f"     Total 80+ Population: {davis_tracts['pop_80_plus'].sum():,.0f}")

print("\n" + "=" * 60)
print("Statistics Calculation Complete")
print("=" * 60)

