"""
PM2.5 and Elderly Population (80+) Geospatial Analysis Pipeline
Salt Lake County and Davis County, Utah

This script creates a layered visualization combining:
1. Census tract boundaries with 80+ age demographic data
2. Interpolated PM2.5 heatmap from PurpleAir sensors
"""

import os
import glob
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.interpolate import griddata
import contextily as cx
from shapely.geometry import Point
from shapely.ops import unary_union
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import folium
from folium.features import GeoJsonTooltip

# =============================================================================
# Configuration
# =============================================================================
DATA_DIR = "../Data"
SHAPEFILE_PATH = os.path.join(DATA_DIR, "tl_2025_49_tract", "tl_2025_49_tract.shp")
CENSUS_DATA_PATH = os.path.join(DATA_DIR, "ACSData", "ACSDT5Y2023.B01001-Data.csv")
SENSOR_LIST_PATH = "master_sensor_list.csv"
PURPLEAIR_DIR = os.path.join(DATA_DIR, "PurpleAirData-Pm2.5Data", "PurpleAir Download 1-25-2026")
OUTPUT_FILE = "final_analysis_map.png"

# Counties to include (FIPS codes)
SALT_LAKE_COUNTY = "49035"
DAVIS_COUNTY = "49011"

# =============================================================================
# Step A: Load and Filter Shapefile
# =============================================================================
def load_and_filter_shapefile(shapefile_path):
    """
    Load Utah census tract shapefile and filter to Salt Lake and Davis counties.
    Reproject to Web Mercator (EPSG:3857).
    """
    print("Step A: Loading shapefile...")
    gdf = gpd.read_file(shapefile_path)
    
    # Filter to Salt Lake County (49035) and Davis County (49011)
    mask = gdf['GEOID'].str.startswith(SALT_LAKE_COUNTY) | gdf['GEOID'].str.startswith(DAVIS_COUNTY)
    gdf_filtered = gdf[mask].copy()
    
    print(f"  Filtered to {len(gdf_filtered)} census tracts (Salt Lake + Davis counties)")
    
    # Reproject to Web Mercator for accurate plotting
    gdf_filtered = gdf_filtered.to_crs(epsg=3857)
    print("  Reprojected to EPSG:3857 (Web Mercator)")
    
    return gdf_filtered

# =============================================================================
# Step B: Process Census Demographics
# =============================================================================
def process_census_data(census_path):
    """
    Load ACS demographic data and calculate population 80+.
    Returns DataFrame with cleaned GEO_ID, pop_80_plus (raw count), and pop_80_plus_pct (percentage).
    """
    print("\nStep B: Processing census demographic data...")
    
    # Load CSV, skipping the descriptive header row (row 2 in file)
    # Row 1 has column codes, row 2 has descriptions, data starts at row 3
    df = pd.read_csv(census_path, skiprows=[1], low_memory=False)
    
    # Columns for 80+ population:
    # B01001_024E: Male 80-84 years
    # B01001_025E: Male 85+ years
    # B01001_048E: Female 80-84 years
    # B01001_049E: Female 85+ years
    
    age_columns = ['B01001_024E', 'B01001_025E', 'B01001_048E', 'B01001_049E']
    
    # Convert to numeric (some values might be strings or have annotations)
    for col in age_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate total 80+ population
    df['pop_80_plus'] = df[age_columns].sum(axis=1)
    
    # Get total population (B01001_001E is the total population column)
    df['total_pop'] = pd.to_numeric(df['B01001_001E'], errors='coerce').fillna(0)
    
    # Calculate percentage of population 80+
    # Avoid division by zero by replacing 0 with 1
    df['pop_80_plus_pct'] = (df['pop_80_plus'] / df['total_pop'].replace(0, 1)) * 100
    
    # Fix GEO_ID: strip the "1400000US" prefix to match shapefile GEOID
    df['GEOID'] = df['GEO_ID'].str.replace('1400000US', '', regex=False)
    
    # Keep necessary columns
    census_df = df[['GEOID', 'NAME', 'pop_80_plus', 'pop_80_plus_pct']].copy()
    
    print(f"  Processed {len(census_df)} census tract records")
    print(f"  Total 80+ population in dataset: {census_df['pop_80_plus'].sum():,.0f}")
    print(f"  Average percentage 80+ in dataset: {census_df['pop_80_plus_pct'].mean():.2f}%")
    
    return census_df

def merge_geo_and_census(gdf, census_df):
    """
    Inner join the shapefile GeoDataFrame with census demographic data.
    Filters out uninhabited tracts (Great Salt Lake, Airport, industrial zones).
    """
    print("\nMerging shapefile with census data...")
    
    merged = gdf.merge(census_df, on='GEOID', how='inner')
    initial_count = len(merged)
    
    print(f"  Merged result: {initial_count} tracts with demographic data")
    
    # Remove uninhabited tracts (e.g., Great Salt Lake, Airport, Canyons)
    merged = merged[merged['pop_80_plus'] > 0].copy()
    dropped_zero = initial_count - len(merged)
    print(f"  Dropped {dropped_zero} tracts with zero 80+ population (e.g., water bodies/industrial)")
    
    # Optional: Remove tracts with tiny population but huge area (outliers)
    # These are typically rural/wilderness areas that dominate the map visually
    merged['area_m2'] = merged.geometry.area
    area_95th = merged['area_m2'].quantile(0.95)
    
    # Filter: small population (< 10) AND huge area (> 95th percentile)
    outlier_mask = (merged['pop_80_plus'] < 10) & (merged['area_m2'] > area_95th)
    outlier_tracts = merged[outlier_mask]
    
    if len(outlier_tracts) > 0:
        print(f"  Dropping {len(outlier_tracts)} large, sparsely-populated tracts:")
        for _, row in outlier_tracts.iterrows():
            print(f"    - {row['NAMELSAD']}: pop_80+={int(row['pop_80_plus'])}, area={row['area_m2']/1e6:.1f} km²")
        merged = merged[~outlier_mask].copy()
    
    # Clean up temp column
    merged = merged.drop(columns=['area_m2'])
    
    print(f"  Final result: {len(merged)} tracts for analysis")
    print(f"  80+ population in study area: {merged['pop_80_plus'].sum():,.0f}")
    
    return merged

# =============================================================================
# Step C: Process PurpleAir Sensor Data
# =============================================================================
def load_sensor_locations(sensor_list_path):
    """
    Load the master sensor list with lat/lon coordinates.
    """
    sensors = pd.read_csv(sensor_list_path)
    # Create a lookup dictionary: sensor_index -> (lat, lon)
    sensor_lookup = {}
    for _, row in sensors.iterrows():
        sensor_lookup[int(row['sensor_index'])] = (row['latitude'], row['longitude'])
    return sensor_lookup

def process_purpleair_data(purpleair_dir, sensor_lookup):
    """
    Process all PurpleAir CSV files:
    1. Extract sensor ID from filename
    2. Look up lat/lon from master list
    3. Calculate mean PM2.5 and apply correction formula
    
    Returns tuple: (DataFrame with lat, lon, pm25 columns, date_range_info dict)
    """
    print("\nStep C: Processing PurpleAir sensor data...")
    
    # Get all CSV files in the directory
    csv_pattern = os.path.join(purpleair_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)
    
    total_files = len(csv_files)
    print(f"  Found {total_files} sensor files to process")
    
    # Extract date range from first filename
    # Filename format: "100865 2026-01-01 2026-01-25 60-Minute Average.csv"
    date_range_info = {'start_date': None, 'end_date': None, 'interval': '60-Minute'}
    if csv_files:
        try:
            sample_filename = os.path.basename(csv_files[0])
            parts = sample_filename.split()
            if len(parts) >= 4:
                date_range_info['start_date'] = parts[1]  # e.g., "2026-01-01"
                date_range_info['end_date'] = parts[2]    # e.g., "2026-01-25"
                date_range_info['interval'] = parts[3]    # e.g., "60-Minute"
        except:
            pass
    
    if date_range_info['start_date'] and date_range_info['end_date']:
        print(f"  Data period: {date_range_info['start_date']} to {date_range_info['end_date']} ({date_range_info['interval']} averages)")
    
    air_data = []
    processed = 0
    skipped = 0
    
    for csv_file in csv_files:
        try:
            # Extract sensor ID from filename
            # Filename format: "100865 2026-01-01 2026-01-25 60-Minute Average.csv"
            filename = os.path.basename(csv_file)
            sensor_id = int(filename.split()[0])
            
            # Look up coordinates
            if sensor_id not in sensor_lookup:
                skipped += 1
                continue
            
            lat, lon = sensor_lookup[sensor_id]
            
            # Read sensor data
            df = pd.read_csv(csv_file)
            
            # Calculate mean of pm2.5_cf_1
            if 'pm2.5_cf_1' not in df.columns:
                skipped += 1
                continue
            
            raw_pm25 = df['pm2.5_cf_1'].mean()
            
            # Skip if no valid data
            if pd.isna(raw_pm25):
                skipped += 1
                continue
            
            # Apply University of Utah Winter Inversion correction formula
            corrected_pm25 = (0.778 * raw_pm25) + 2.65
            
            # Filter outliers: PM2.5 > 500 is physically impossible for ambient air
            if corrected_pm25 > 500:
                print(f"  WARNING: Sensor {sensor_id} dropped - PM2.5 value {corrected_pm25:.1f} exceeds 500 µg/m³ (likely sensor error)")
                skipped += 1
                continue
            
            air_data.append({
                'lat': lat,
                'lon': lon,
                'pm25': corrected_pm25,
                'sensor_id': sensor_id
            })
            
            processed += 1
            
            # Print progress every 50 sensors
            if processed % 50 == 0:
                print(f"  Processed {processed}/{total_files} sensors...")
                
        except Exception as e:
            skipped += 1
            continue
    
    print(f"  Successfully processed {processed} sensors")
    print(f"  Skipped {skipped} sensors (missing location or invalid data)")
    
    air_df = pd.DataFrame(air_data)
    
    if len(air_df) > 0:
        print(f"  PM2.5 range: {air_df['pm25'].min():.1f} - {air_df['pm25'].max():.1f} µg/m³")
        print(f"  PM2.5 mean: {air_df['pm25'].mean():.1f} µg/m³")
    
    return air_df, date_range_info

# =============================================================================
# Step C.5: Create Data Analysis Plots
# =============================================================================
def create_data_analysis_plots(air_df, date_range, output_file):
    """
    Create comprehensive statistical analysis plots for PurpleAir data.
    
    Args:
        air_df: Processed PurpleAir sensor data (with corrected PM2.5)
        date_range: Date range dictionary
        output_file: Path for output PNG
    """
    print("\nStep C.5: Creating data analysis plots...")
    
    # Create figure with 2x2 grid - improved spacing
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4,
                         left=0.08, right=0.95, top=0.95, bottom=0.08)
    
    # ==========================================
    # Panel 1: PM2.5 Distribution Histogram
    # ==========================================
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Histogram of corrected PM2.5 values
    ax1.hist(air_df['pm25'], bins=50, alpha=0.7, color='steelblue', 
             edgecolor='black', linewidth=0.5)
    
    # Add AQI category thresholds
    ax1.axvline(12, color='green', linestyle='--', linewidth=2, label='Good/Moderate (12 µg/m³)')
    ax1.axvline(35, color='orange', linestyle='--', linewidth=2, label='Moderate/Unhealthy (35 µg/m³)')
    
    # Add mean and median lines
    mean_pm25 = air_df['pm25'].mean()
    median_pm25 = air_df['pm25'].median()
    ax1.axvline(mean_pm25, color='blue', linestyle='--', linewidth=2, label=f'Mean: {mean_pm25:.2f} µg/m³')
    ax1.axvline(median_pm25, color='red', linestyle='--', linewidth=2, label=f'Median: {median_pm25:.2f} µg/m³')
    
    ax1.set_xlabel('PM2.5 (µg/m³)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('PurpleAir PM2.5 Distribution (Corrected)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # ==========================================
    # Panel 2: Box Plot by AQI Category
    # ==========================================
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Categorize sensors by AQI
    def get_aqi_category(pm25):
        if pm25 < 12:
            return 'Good'
        elif pm25 < 35:
            return 'Moderate'
        else:
            return 'Unhealthy'
    
    air_df['aqi_category'] = air_df['pm25'].apply(get_aqi_category)
    
    # Prepare data for box plot
    categories = ['Good', 'Moderate', 'Unhealthy']
    category_data = []
    category_labels = []
    
    for cat in categories:
        cat_data = air_df[air_df['aqi_category'] == cat]['pm25']
        if len(cat_data) > 0:
            category_data.append(cat_data.values)
            category_labels.append(f"{cat}\n(n={len(cat_data)})")
    
    if category_data:
        bp = ax2.boxplot(category_data, tick_labels=category_labels, patch_artist=True)
        
        # Color the boxes
        colors = ['green', 'orange', 'red']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax2.set_xlabel('AQI Category', fontsize=12)
        ax2.set_ylabel('PM2.5 (µg/m³)', fontsize=12)
        ax2.set_title('PM2.5 Distribution by AQI Category', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
    
    # ==========================================
    # Panel 3: Spatial Distribution
    # ==========================================
    ax3 = fig.add_subplot(gs[1, 0])
    
    # Scatter plot: Latitude vs Longitude, colored by PM2.5
    scatter = ax3.scatter(air_df['lon'], air_df['lat'], 
                         c=air_df['pm25'], cmap='OrRd', 
                         s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('PM2.5 (µg/m³)', fontsize=12)
    
    ax3.set_xlabel('Longitude', fontsize=12)
    ax3.set_ylabel('Latitude', fontsize=12)
    ax3.set_title('Spatial Distribution of PM2.5', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # ==========================================
    # Panel 4: Summary Statistics Table
    # ==========================================
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    
    # Calculate statistics
    stats = air_df['pm25'].describe()
    
    # AQI breakdown
    good_count = len(air_df[air_df['pm25'] < 12])
    moderate_count = len(air_df[(air_df['pm25'] >= 12) & (air_df['pm25'] < 35)])
    unhealthy_count = len(air_df[air_df['pm25'] >= 35])
    total_sensors = len(air_df)
    
    # Prepare table data - more compact format
    table_data = []
    
    # Sensor network summary
    table_data.append(['Sensor Network Summary', '', ''])
    table_data.append(['Total Sensors', f"{total_sensors:,}", ''])
    table_data.append(['Valid Sensors', f"{total_sensors:,}", ''])
    
    # PM2.5 statistics
    table_data.append(['', '', ''])
    table_data.append(['PM2.5 Statistics', '', ''])
    table_data.append(['Count', f"{int(stats['count']):,}", ''])
    table_data.append(['Mean', f"{stats['mean']:.2f}", 'µg/m³'])
    table_data.append(['Median', f"{stats['50%']:.2f}", 'µg/m³'])
    table_data.append(['Std Dev', f"{stats['std']:.2f}", 'µg/m³'])
    table_data.append(['Min', f"{stats['min']:.2f}", 'µg/m³'])
    table_data.append(['25th %ile', f"{stats['25%']:.2f}", 'µg/m³'])
    table_data.append(['75th %ile', f"{stats['75%']:.2f}", 'µg/m³'])
    table_data.append(['Max', f"{stats['max']:.2f}", 'µg/m³'])
    
    # AQI breakdown
    table_data.append(['', '', ''])
    table_data.append(['AQI Category Breakdown', '', ''])
    table_data.append(['Good (<12)', f"{good_count:,}", f"{good_count/total_sensors*100:.1f}%"])
    table_data.append(['Moderate (12-35)', f"{moderate_count:,}", f"{moderate_count/total_sensors*100:.1f}%"])
    table_data.append(['Unhealthy (>35)', f"{unhealthy_count:,}", f"{unhealthy_count/total_sensors*100:.1f}%"])
    
    # Create table with better formatting
    table = ax4.table(cellText=table_data, cellLoc='left', loc='center',
                     colWidths=[0.35, 0.25, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.3)
    
    # Style header rows
    for i in range(len(table_data)):
        if table_data[i][1] == '' and table_data[i][2] == '':
            for j in range(3):
                table[(i, j)].set_facecolor('#4472C4')
                table[(i, j)].set_text_props(weight='bold', color='white')
    
    ax4.set_title('Summary Statistics', fontsize=14, fontweight='bold', pad=15)
    
    # Add overall figure title
    fig.suptitle('PurpleAir PM2.5 Data Analysis', fontsize=16, fontweight='bold', y=0.98)
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  Saved analysis plots to: {output_file}")
    plt.close()

# =============================================================================
# Step D: Spatial Interpolation
# =============================================================================
def create_pm25_heatmap(air_df, bounds, resolution=200):
    """
    Create interpolated PM2.5 surface using scipy.griddata.
    
    Args:
        air_df: DataFrame with lat, lon, pm25 columns (WGS84)
        bounds: (minx, miny, maxx, maxy) in EPSG:3857
        resolution: Grid resolution (default 200x200)
    
    Returns:
        grid_x, grid_y, grid_pm25 for plotting with imshow
    """
    print("\nStep D: Creating PM2.5 interpolation grid...")
    
    # Convert air_df to GeoDataFrame in WGS84, then reproject to EPSG:3857
    geometry = [Point(lon, lat) for lon, lat in zip(air_df['lon'], air_df['lat'])]
    air_gdf = gpd.GeoDataFrame(air_df, geometry=geometry, crs="EPSG:4326")
    air_gdf = air_gdf.to_crs(epsg=3857)
    
    # Extract projected coordinates
    x_coords = air_gdf.geometry.x.values
    y_coords = air_gdf.geometry.y.values
    pm25_values = air_gdf['pm25'].values
    
    # Create interpolation grid
    minx, miny, maxx, maxy = bounds
    grid_x = np.linspace(minx, maxx, resolution)
    grid_y = np.linspace(miny, maxy, resolution)
    grid_xx, grid_yy = np.meshgrid(grid_x, grid_y)
    
    # Interpolate using linear method
    points = np.column_stack((x_coords, y_coords))
    grid_pm25 = griddata(points, pm25_values, (grid_xx, grid_yy), method='linear')
    
    print(f"  Created {resolution}x{resolution} interpolation grid")
    print(f"  Grid bounds: x=[{minx:.0f}, {maxx:.0f}], y=[{miny:.0f}, {maxy:.0f}]")
    
    return grid_x, grid_y, grid_pm25

# =============================================================================
# Step E: Visualization
# =============================================================================
def geometry_to_path(geometry):
    """
    Convert a shapely geometry to a matplotlib Path for clipping.
    Handles both Polygon and MultiPolygon geometries.
    """
    from shapely.geometry import MultiPolygon, Polygon
    
    vertices = []
    codes = []
    
    # Handle MultiPolygon by iterating through all polygons
    if isinstance(geometry, MultiPolygon):
        polygons = list(geometry.geoms)
    elif isinstance(geometry, Polygon):
        polygons = [geometry]
    else:
        polygons = []
    
    for polygon in polygons:
        # Exterior ring
        ext_coords = list(polygon.exterior.coords)
        vertices.extend(ext_coords)
        codes.append(Path.MOVETO)
        codes.extend([Path.LINETO] * (len(ext_coords) - 2))
        codes.append(Path.CLOSEPOLY)
        
        # Interior rings (holes)
        for interior in polygon.interiors:
            int_coords = list(interior.coords)
            vertices.extend(int_coords)
            codes.append(Path.MOVETO)
            codes.extend([Path.LINETO] * (len(int_coords) - 2))
            codes.append(Path.CLOSEPOLY)
    
    return Path(vertices, codes)


def create_visualization(merged_gdf, grid_x, grid_y, grid_pm25, air_df, date_range, output_file):
    """
    Creates side-by-side maps:
    - Left: 80+ Population choropleth
    - Right: PM2.5 heatmap with sensor verification points
    
    Args:
        date_range: dict with 'start_date', 'end_date', 'interval' keys
    """
    print("\nStep E: Creating mirrored visualization...")
    
    # Format date range for titles
    date_str = ""
    if date_range.get('start_date') and date_range.get('end_date'):
        date_str = f"\nData: {date_range['start_date']} to {date_range['end_date']}"
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 12))
    
    # Shared Bounds
    bounds = merged_gdf.total_bounds
    for ax in [ax1, ax2]:
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.set_xticks([])
        ax.set_yticks([])
        cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)

    # LEFT MAP: Population
    merged_gdf.plot(column='pop_80_plus_pct', ax=ax1, cmap='Blues', alpha=0.8, 
                   edgecolor='black', linewidth=0.3, legend=True,
                   legend_kwds={'label': 'Percentage of Residents Age 80+'})
    ax1.set_title(f'Distribution of Residents Age 80+\nSalt Lake & Davis Counties', fontsize=16)

    # RIGHT MAP: Air Quality
    # 1. Heatmap
    im = ax2.imshow(grid_pm25, extent=[grid_x.min(), grid_x.max(), grid_y.min(), grid_y.max()],
                   origin='lower', cmap='OrRd', alpha=0.7, vmin=0, vmax=80, zorder=2)
    
    # 2. Clipping
    from shapely.ops import unary_union
    from matplotlib.patches import PathPatch
    county_union = unary_union(merged_gdf.geometry)
    clip_path = geometry_to_path(county_union)
    patch = PathPatch(clip_path, transform=ax2.transData)
    im.set_clip_path(patch)
    
    # 3. VERIFICATION LAYER: Plot the actual sensor points
    # We need to convert air_df lat/lon to Map coordinates (EPSG:3857)
    from shapely.geometry import Point
    geometry = [Point(xy) for xy in zip(air_df.lon, air_df.lat)]
    air_geo = gpd.GeoDataFrame(air_df, geometry=geometry, crs="EPSG:4326").to_crs(epsg=3857)
    
    air_geo.plot(ax=ax2, color='black', markersize=10, alpha=0.5, zorder=4, label='Sensor Location')
    
    # 4. Outlines
    merged_gdf.plot(ax=ax2, facecolor='none', edgecolor='black', linewidth=0.3, zorder=3)
    
    plt.colorbar(im, ax=ax2, label='PM2.5 (µg/m³)', shrink=0.7)
    ax2.legend(loc='upper right')
    ax2.set_title(f'PM2.5 Air Quality (Interpolated from {len(air_df)} Sensors){date_str}', fontsize=16)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n  Saved mirrored map to: {output_file}")
    plt.close()


# =============================================================================
# Step F: Interactive Map (Folium)
# =============================================================================
def get_pm25_color(pm25_value):
    """
    Return color based on EPA AQI categories for PM2.5:
    - Green: Good (0-12 µg/m³)
    - Yellow: Moderate (12.1-35.4 µg/m³)  
    - Red: Unhealthy for Sensitive Groups (35.5+ µg/m³)
    """
    if pm25_value < 12:
        return 'green'
    elif pm25_value < 35:
        return 'orange'
    else:
        return 'red'


def create_interactive_map(merged_gdf, air_df, date_range, output_file="slc_analysis_interactive.html"):
    """
    Create an interactive Folium map with:
    1. Choropleth layer showing 80+ population by census tract
    2. Circle markers for PurpleAir sensors colored by PM2.5 level
    3. Layer control to toggle layers on/off
    
    Args:
        merged_gdf: GeoDataFrame with census tracts and pop_80_plus column (EPSG:3857)
        air_df: DataFrame with lat, lon, pm25, sensor_id columns
        date_range: dict with 'start_date', 'end_date', 'interval' keys
        output_file: Output HTML filename
    """
    print("\nStep F: Creating interactive Folium map...")
    
    # Add formatted fields for tooltip display
    merged_gdf['pop_80_plus_pct_formatted'] = merged_gdf['pop_80_plus_pct'].apply(lambda x: f"{x:.1f}%")
    merged_gdf['pop_80_plus_formatted'] = merged_gdf['pop_80_plus'].apply(lambda x: f"{int(x):,}")
    
    # Convert merged_gdf to WGS84 (EPSG:4326) for Folium
    gdf_wgs84 = merged_gdf.to_crs(epsg=4326)
    
    # Calculate map center using bounds (avoids centroid warning)
    bounds = gdf_wgs84.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    print(f"  Map center: ({center_lat:.4f}, {center_lon:.4f})")
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=10,
        tiles='CartoDB positron'
    )
    
    # ==========================================
    # LAYER 1: Population Choropleth
    # ==========================================
    print("  Adding population choropleth layer...")
    
    # Add choropleth directly to map (required by folium)
    choropleth = folium.Choropleth(
        geo_data=gdf_wgs84.__geo_interface__,
        data=gdf_wgs84,
        columns=['GEOID', 'pop_80_plus_pct'],
        key_on='feature.properties.GEOID',
        fill_color='Blues',
        fill_opacity=0.6,
        line_opacity=0.3,
        line_weight=1,
        legend_name='Percentage of Residents Age 80+',
        name='Population 80+ (Census Tracts)',
        highlight=True
    ).add_to(m)
    
    # Add tooltips via GeoJson overlay (transparent, just for interaction)
    # This layer sits on top to capture hover events
    folium.GeoJson(
        gdf_wgs84,
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'transparent',
            'weight': 0,
            'fillOpacity': 0
        },
        highlight_function=lambda x: {
            'weight': 3,
            'color': 'black',
            'fillOpacity': 0.1
        },
        tooltip=GeoJsonTooltip(
            fields=['NAMELSAD', 'pop_80_plus_pct_formatted', 'pop_80_plus_formatted'],
            aliases=['Census Tract:', 'Percentage 80+:', 'Population 80+ (Count):'],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: white;
                border: 2px solid black;
                border-radius: 3px;
                box-shadow: 3px 3px 3px rgba(0,0,0,0.3);
                font-size: 14px;
                padding: 10px;
            """
        ),
        name='Tract Tooltips'
    ).add_to(m)
    
    # ==========================================
    # LAYER 2: Air Quality Sensors
    # ==========================================
    print("  Adding air quality sensor markers...")
    
    # Create a FeatureGroup for air quality markers
    air_layer = folium.FeatureGroup(name='PurpleAir Sensors (PM2.5)')
    
    # Add circle markers for each sensor
    for _, row in air_df.iterrows():
        pm25 = row['pm25']
        color = get_pm25_color(pm25)
        
        # Determine AQI category
        if pm25 < 12:
            status = 'Good'
        elif pm25 < 35:
            status = 'Moderate'
        else:
            status = 'Unhealthy for Sensitive Groups'
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 180px;">
            <b style="font-size: 14px;">PurpleAir Sensor {int(row['sensor_id'])}</b><br>
            <hr style="margin: 5px 0;">
            <b>Sensor ID:</b> {int(row['sensor_id'])}<br>
            <b>PM2.5:</b> {pm25:.1f} µg/m³<br>
            <b>AQI Status:</b> <span style="color: {color}; font-weight: bold;">{status}</span><br>
            <b>Coordinates:</b><br>
            &nbsp;&nbsp;Lat: {row['lat']:.4f}<br>
            &nbsp;&nbsp;Lon: {row['lon']:.4f}
        </div>
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=15,
            color='black',
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"PM2.5: {pm25:.1f} µg/m³"
        ).add_to(air_layer)
    
    air_layer.add_to(m)
    
    # ==========================================
    # Add Layer Control
    # ==========================================
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add legend for air quality colors with date range
    date_info = ""
    if date_range.get('start_date') and date_range.get('end_date'):
        date_info = f"<hr style=\"margin: 8px 0;\"><b>Data Period:</b><br>{date_range['start_date']} to {date_range['end_date']}<br>({date_range.get('interval', '60-Minute')} averages)"
    
    legend_html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 15px; border: 2px solid gray;
                border-radius: 5px; font-family: Arial; font-size: 12px;
                box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
        <b style="font-size: 14px;">PM2.5 Air Quality</b><br>
        <hr style="margin: 8px 0;">
        <i style="background: green; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Good (&lt;12 µg/m³)<br>
        <i style="background: orange; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Moderate (12-35 µg/m³)<br>
        <i style="background: red; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Unhealthy (&gt;35 µg/m³)
        {date_info}
        <br><b>Sensors:</b> {len(air_df)}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    m.save(output_file)
    print(f"  Saved interactive map to: {output_file}")
    
    # Print sensor summary by category
    good = len(air_df[air_df['pm25'] < 12])
    moderate = len(air_df[(air_df['pm25'] >= 12) & (air_df['pm25'] < 35)])
    unhealthy = len(air_df[air_df['pm25'] >= 35])
    print(f"  Sensor summary: {good} Good, {moderate} Moderate, {unhealthy} Unhealthy")


# =============================================================================
# Main Pipeline
# =============================================================================
def main():
    print("=" * 60)
    print("PM2.5 and Elderly Population Geospatial Analysis")
    print("Salt Lake & Davis Counties, Utah")
    print("=" * 60)
    
    # Step A: Load and filter shapefile
    gdf = load_and_filter_shapefile(SHAPEFILE_PATH)
    
    # Step B: Process census demographics
    census_df = process_census_data(CENSUS_DATA_PATH)
    merged_gdf = merge_geo_and_census(gdf, census_df)
    
    # Step C: Process PurpleAir sensor data
    sensor_lookup = load_sensor_locations(SENSOR_LIST_PATH)
    air_df, date_range = process_purpleair_data(PURPLEAIR_DIR, sensor_lookup)
    
    if len(air_df) == 0:
        print("\nERROR: No valid sensor data found. Cannot create heatmap.")
        return
    
    # Step C.5: Create data analysis plots
    create_data_analysis_plots(air_df, date_range, "purpleair_data_analysis.png")
    
    # Step D: Create interpolation grid
    bounds = merged_gdf.total_bounds
    grid_x, grid_y, grid_pm25 = create_pm25_heatmap(air_df, bounds, resolution=200)
    
    # Step E: Create visualization (now includes air_df for sensor markers and date range)
    create_visualization(merged_gdf, grid_x, grid_y, grid_pm25, air_df, date_range, OUTPUT_FILE)
    
    # Step F: Create interactive map
    create_interactive_map(merged_gdf, air_df, date_range, "slc_analysis_interactive.html")
    
    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

