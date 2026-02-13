"""
EPA PM2.5 and Elderly Population (65+ and 85+) Geospatial Analysis
Salt Lake County and Davis County, Utah

This script creates visualizations combining:
1. Census tract boundaries with 65+ and 85+ age demographic data (background layer)
2. Official EPA monitoring station locations as distinct points

Generates separate maps for both 65+ and 85+ populations.
"""

import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import contextily as cx
from shapely.geometry import Point
import folium
from folium.features import GeoJsonTooltip

# =============================================================================
# Configuration
# =============================================================================
DATA_DIR = "../Data"
SHAPEFILE_PATH = os.path.join(DATA_DIR, "tl_2025_49_tract", "tl_2025_49_tract.shp")
CENSUS_DATA_PATH = os.path.join(DATA_DIR, "ACSData", "ACSDT5Y2023.B01001-Data.csv")
EPA_DATA_PATH = "epa_utah_data.csv"

OUTPUT_PNG = "epa_age_overlay_map.png"
OUTPUT_HTML = "epa_interactive_map.html"

# Counties to include (FIPS codes)
SALT_LAKE_COUNTY = "49035"
DAVIS_COUNTY = "49011"

# Date filter for inversion event (matching PurpleAir analysis period)
INVERSION_START = "2025-01-01"
INVERSION_END = "2025-01-30"

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
    Load ACS demographic data and calculate both 65+ and 85+ populations.
    Returns DataFrame with cleaned GEO_ID, pop_65_plus, pop_65_plus_pct, pop_85_plus, pop_85_plus_pct.
    """
    print("\nStep B: Processing census demographic data...")
    
    # Load CSV, skipping the descriptive header row
    df = pd.read_csv(census_path, skiprows=[1], low_memory=False)
    
    # Columns for 65+ population (12 columns total):
    # Male: B01001_020E (65-66), B01001_021E (67-69), B01001_022E (70-74), 
    #       B01001_023E (75-79), B01001_024E (80-84), B01001_025E (85+)
    # Female: B01001_044E (65-66), B01001_045E (67-69), B01001_046E (70-74),
    #         B01001_047E (75-79), B01001_048E (80-84), B01001_049E (85+)
    age_65_plus_columns = ['B01001_020E', 'B01001_021E', 'B01001_022E', 'B01001_023E', 
                           'B01001_024E', 'B01001_025E', 'B01001_044E', 'B01001_045E', 
                           'B01001_046E', 'B01001_047E', 'B01001_048E', 'B01001_049E']
    
    # Columns for 85+ population (2 columns):
    # B01001_025E: Male 85+ years
    # B01001_049E: Female 85+ years
    age_85_plus_columns = ['B01001_025E', 'B01001_049E']
    
    # Convert to numeric
    all_age_columns = age_65_plus_columns + age_85_plus_columns
    for col in all_age_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate total 65+ population
    df['pop_65_plus'] = df[age_65_plus_columns].sum(axis=1)
    
    # Calculate total 85+ population
    df['pop_85_plus'] = df[age_85_plus_columns].sum(axis=1)
    
    # Get total population (B01001_001E is the total population column)
    df['total_pop'] = pd.to_numeric(df['B01001_001E'], errors='coerce').fillna(0)
    
    # Calculate percentages
    # Avoid division by zero by replacing 0 with 1
    df['pop_65_plus_pct'] = (df['pop_65_plus'] / df['total_pop'].replace(0, 1)) * 100
    df['pop_85_plus_pct'] = (df['pop_85_plus'] / df['total_pop'].replace(0, 1)) * 100
    
    # Fix GEO_ID: strip the "1400000US" prefix to match shapefile GEOID
    df['GEOID'] = df['GEO_ID'].str.replace('1400000US', '', regex=False)
    
    # Keep necessary columns
    census_df = df[['GEOID', 'NAME', 'pop_65_plus', 'pop_65_plus_pct', 'pop_85_plus', 'pop_85_plus_pct']].copy()
    
    print(f"  Processed {len(census_df)} census tract records")
    print(f"  Total 65+ population in dataset: {census_df['pop_65_plus'].sum():,.0f}")
    print(f"  Average percentage 65+ in dataset: {census_df['pop_65_plus_pct'].mean():.2f}%")
    print(f"  Total 85+ population in dataset: {census_df['pop_85_plus'].sum():,.0f}")
    print(f"  Average percentage 85+ in dataset: {census_df['pop_85_plus_pct'].mean():.2f}%")
    
    return census_df

def merge_geo_and_census(gdf, census_df):
    """
    Inner join the shapefile GeoDataFrame with census demographic data.
    Filters out uninhabited tracts (using 65+ as the filter since it's more inclusive).
    """
    print("\nMerging shapefile with census data...")
    
    merged = gdf.merge(census_df, on='GEOID', how='inner')
    initial_count = len(merged)
    
    print(f"  Merged result: {initial_count} tracts with demographic data")
    
    # Remove uninhabited tracts (filter on 65+ since it's more inclusive)
    merged = merged[merged['pop_65_plus'] > 0].copy()
    dropped_zero = initial_count - len(merged)
    print(f"  Dropped {dropped_zero} tracts with zero 65+ population")
    
    # Remove large, sparsely-populated outlier tracts
    merged['area_m2'] = merged.geometry.area
    area_95th = merged['area_m2'].quantile(0.95)
    
    outlier_mask = (merged['pop_65_plus'] < 10) & (merged['area_m2'] > area_95th)
    outlier_tracts = merged[outlier_mask]
    
    if len(outlier_tracts) > 0:
        print(f"  Dropping {len(outlier_tracts)} large, sparsely-populated tracts")
        merged = merged[~outlier_mask].copy()
    
    merged = merged.drop(columns=['area_m2'])
    
    print(f"  Final result: {len(merged)} tracts for analysis")
    print(f"  65+ population in study area: {merged['pop_65_plus'].sum():,.0f}")
    print(f"  85+ population in study area: {merged['pop_85_plus'].sum():,.0f}")
    
    return merged

# =============================================================================
# Step C: Process EPA Air Data
# =============================================================================
def process_epa_data(epa_data_path):
    """
    Load EPA data and filter for the inversion event period (Jan 14-17, 2025).
    Aggregate by site to get one row per station with mean PM2.5.
    
    Returns:
        tuple: (epa_sites, df_filtered)
        - epa_sites: DataFrame with site_number, local_site_name, latitude, longitude, pm25_value (aggregated)
        - df_filtered: Full filtered DataFrame with all records (for analysis plots)
    """
    print("\nStep C: Processing EPA air quality data...")
    
    # Load EPA data
    df = pd.read_csv(epa_data_path)
    print(f"  Loaded {len(df)} total records from EPA data")
    
    # Convert date column to datetime
    df['date_local'] = pd.to_datetime(df['date_local'])
    
    # Filter to inversion event dates (Jan 14-17, 2025)
    mask = (df['date_local'] >= INVERSION_START) & (df['date_local'] <= INVERSION_END)
    df_filtered = df[mask].copy()
    
    print(f"  Filtered to {len(df_filtered)} records for inversion period ({INVERSION_START} to {INVERSION_END})")
    
    if len(df_filtered) == 0:
        print("  WARNING: No data found for the specified date range!")
        print(f"  Available dates: {df['date_local'].min()} to {df['date_local'].max()}")
        # Fall back to all data
        df_filtered = df.copy()
        print(f"  Using all {len(df_filtered)} records instead")
    
    # Aggregate: Group by site and calculate mean PM2.5
    epa_sites = df_filtered.groupby(['site_number', 'local_site_name', 'latitude', 'longitude']).agg({
        'pm25_value': 'mean'
    }).reset_index()
    
    print(f"  Aggregated to {len(epa_sites)} unique monitoring sites")
    print(f"  PM2.5 range: {epa_sites['pm25_value'].min():.1f} - {epa_sites['pm25_value'].max():.1f} µg/m³")
    print(f"  PM2.5 mean: {epa_sites['pm25_value'].mean():.1f} µg/m³")
    
    # Print site details
    print("\n  EPA Monitoring Sites:")
    for _, row in epa_sites.iterrows():
        print(f"    - {row['local_site_name']} (Site {row['site_number']}): {row['pm25_value']:.1f} µg/m³")
    
    return epa_sites, df_filtered

# =============================================================================
# Step C.5: Create Data Analysis Plots
# =============================================================================
def create_data_analysis_plots(df, epa_sites, output_file):
    """
    Create comprehensive statistical analysis plots for EPA data.
    
    Args:
        df: Full EPA dataframe (before aggregation) for detailed analysis
        epa_sites: Aggregated site data (for site-level plots)
        output_file: Path for output PNG
    """
    print("\nStep C.5: Creating data analysis plots...")
    
    # Convert date column to datetime if not already
    if not pd.api.types.is_datetime64_any_dtype(df['date_local']):
        df['date_local'] = pd.to_datetime(df['date_local'])
    
    # Identify inversion period
    inversion_mask = (df['date_local'] >= INVERSION_START) & (df['date_local'] <= INVERSION_END)
    df_inversion = df[inversion_mask].copy()
    
    # Create figure with 2x2 grid - improved spacing
    fig = plt.figure(figsize=(18, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.4, 
                         left=0.08, right=0.95, top=0.95, bottom=0.08)
    
    # ==========================================
    # Panel 1: PM2.5 Distribution Histogram
    # ==========================================
    ax1 = fig.add_subplot(gs[0, 0])
    
    # Histogram of all data
    ax1.hist(df['pm25_value'], bins=50, alpha=0.7, color='steelblue', 
             label='All Data', edgecolor='black', linewidth=0.5)
    
    # Overlay inversion period
    if len(df_inversion) > 0:
        ax1.hist(df_inversion['pm25_value'], bins=50, alpha=0.6, color='red', 
                 label='Inversion Period', edgecolor='black', linewidth=0.5)
    
    # Add mean and median lines
    mean_all = df['pm25_value'].mean()
    median_all = df['pm25_value'].median()
    ax1.axvline(mean_all, color='blue', linestyle='--', linewidth=2, label=f'Mean: {mean_all:.2f} µg/m³')
    ax1.axvline(median_all, color='green', linestyle='--', linewidth=2, label=f'Median: {median_all:.2f} µg/m³')
    
    ax1.set_xlabel('PM2.5 (µg/m³)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title('PM2.5 Distribution (All Data)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # ==========================================
    # Panel 2: Box Plot by Site
    # ==========================================
    ax2 = fig.add_subplot(gs[0, 1])
    
    # Prepare data for box plot
    site_data = []
    site_labels = []
    for _, row in epa_sites.iterrows():
        site_df = df[df['site_number'] == row['site_number']]
        if len(site_df) > 0:
            site_data.append(site_df['pm25_value'].values)
            site_labels.append(f"{row['local_site_name']}\n(Site {row['site_number']})")
    
    if site_data:
        # Use horizontal box plot for better readability with many sites
        bp = ax2.boxplot(site_data, tick_labels=site_labels, vert=False, patch_artist=True)
        
        # Color the boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(bp['boxes'])))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax2.set_ylabel('Monitoring Site', fontsize=12)
        ax2.set_xlabel('PM2.5 (µg/m³)', fontsize=12)
        ax2.set_title('PM2.5 Distribution by Monitoring Site', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='y', labelsize=8)
        ax2.grid(True, alpha=0.3, axis='x')
    
    # ==========================================
    # Panel 3: Time Series
    # ==========================================
    ax3 = fig.add_subplot(gs[1, 0])
    
    # Calculate daily average PM2.5 across all sites
    daily_avg = df.groupby(df['date_local'].dt.date)['pm25_value'].mean()
    
    ax3.plot(daily_avg.index, daily_avg.values, linewidth=2, color='steelblue', marker='o', markersize=4)
    
    # Highlight inversion event period
    if len(df_inversion) > 0:
        inv_start = pd.to_datetime(INVERSION_START).date()
        inv_end = pd.to_datetime(INVERSION_END).date()
        ax3.axvspan(inv_start, inv_end, alpha=0.3, color='red', label='Inversion Event Period')
    
    # Add AQI threshold lines
    ax3.axhline(12, color='green', linestyle='--', linewidth=1, alpha=0.7, label='Good/Moderate Threshold (12 µg/m³)')
    ax3.axhline(35, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='Moderate/Unhealthy Threshold (35 µg/m³)')
    
    ax3.set_xlabel('Date', fontsize=12)
    ax3.set_ylabel('Daily Average PM2.5 (µg/m³)', fontsize=12)
    ax3.set_title('Daily Average PM2.5 Over Time', fontsize=14, fontweight='bold')
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # ==========================================
    # Panel 4: Summary Statistics Table
    # ==========================================
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axis('off')
    
    # Calculate statistics
    stats_all = df['pm25_value'].describe()
    stats_inv = df_inversion['pm25_value'].describe() if len(df_inversion) > 0 else None
    
    # Prepare table data - more compact format
    table_data = []
    
    # Overall statistics
    table_data.append(['Overall Statistics', '', ''])
    table_data.append(['Count', f"{int(stats_all['count']):,}", ''])
    table_data.append(['Mean', f"{stats_all['mean']:.2f}", 'µg/m³'])
    table_data.append(['Median', f"{stats_all['50%']:.2f}", 'µg/m³'])
    table_data.append(['Std Dev', f"{stats_all['std']:.2f}", 'µg/m³'])
    table_data.append(['Min', f"{stats_all['min']:.2f}", 'µg/m³'])
    table_data.append(['25th %ile', f"{stats_all['25%']:.2f}", 'µg/m³'])
    table_data.append(['75th %ile', f"{stats_all['75%']:.2f}", 'µg/m³'])
    table_data.append(['Max', f"{stats_all['max']:.2f}", 'µg/m³'])
    
    # Inversion period statistics
    if stats_inv is not None:
        table_data.append(['', '', ''])
        table_data.append(['Inversion Period', '', ''])
        table_data.append(['Count', f"{int(stats_inv['count']):,}", ''])
        table_data.append(['Mean', f"{stats_inv['mean']:.2f}", 'µg/m³'])
        table_data.append(['Median', f"{stats_inv['50%']:.2f}", 'µg/m³'])
        table_data.append(['Std Dev', f"{stats_inv['std']:.2f}", 'µg/m³'])
        table_data.append(['Min', f"{stats_inv['min']:.2f}", 'µg/m³'])
        table_data.append(['Max', f"{stats_inv['max']:.2f}", 'µg/m³'])
    
    # Site-level statistics - limit to key stats to avoid overcrowding
    table_data.append(['', '', ''])
    table_data.append(['By Site (Mean)', '', ''])
    # Sort by mean PM2.5 for better readability
    epa_sites_sorted = epa_sites.sort_values('pm25_value', ascending=False)
    for _, row in epa_sites_sorted.iterrows():
        site_df = df[df['site_number'] == row['site_number']]
        if len(site_df) > 0:
            site_min = site_df['pm25_value'].min()
            site_max = site_df['pm25_value'].max()
            # Use site name as-is (table will handle wrapping)
            table_data.append([f"{row['local_site_name']}", 
                              f"{row['pm25_value']:.2f}", 
                              f"{site_min:.1f}-{site_max:.1f}"])
    
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
    
    ax4.set_title('Summary Statistics', fontsize=14, fontweight='bold', pad=60)
    
    # Add overall figure title
    fig.suptitle('EPA PM2.5 Data Analysis', fontsize=16, fontweight='bold', y=0.98)
    
    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  Saved analysis plots to: {output_file}")
    plt.close()

# =============================================================================
# Step D: Create Visualization
# =============================================================================
def create_visualization(merged_gdf, epa_sites, output_file, age_group="65plus"):
    """
    Create a single large map showing:
    - Layer 1: Census tracts colored by population percentage (Blues colormap)
    - Layer 2: EPA monitoring stations as scatter points colored by PM2.5
    
    Args:
        merged_gdf: GeoDataFrame with census tracts and population data
        epa_sites: DataFrame with EPA monitoring station data
        output_file: Output file path for the map
        age_group: "65plus" or "85plus" to select which age group to visualize
    """
    print(f"\nStep D: Creating visualization for {age_group}...")
    
    # Map age group to column names and labels
    age_config = {
        "65plus": {
            "pct_col": "pop_65_plus_pct",
            "count_col": "pop_65_plus",
            "label": "65+",
            "title_label": "Age 65+"
        },
        "85plus": {
            "pct_col": "pop_85_plus_pct",
            "count_col": "pop_85_plus",
            "label": "85+",
            "title_label": "Age 85+"
        }
    }
    
    config = age_config[age_group]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(15, 12))
    
    # Set bounds
    bounds = merged_gdf.total_bounds
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add basemap
    cx.add_basemap(ax, source=cx.providers.CartoDB.Positron)
    
    # ==========================================
    # LAYER 1: Population (The People)
    # ==========================================
    merged_gdf.plot(
        column=config["pct_col"],
        ax=ax,
        cmap='Blues',
        alpha=0.7,
        edgecolor='gray',
        linewidth=0.3,
        legend=True,
        legend_kwds={
            'label': f'Percentage of Residents {config["title_label"]}',
            'shrink': 0.6,
            'orientation': 'vertical'
        }
    )
    
    # ==========================================
    # LAYER 2: EPA Monitors (The Air Quality)
    # ==========================================
    # Convert EPA sites to GeoDataFrame
    geometry = [Point(lon, lat) for lon, lat in zip(epa_sites['longitude'], epa_sites['latitude'])]
    epa_gdf = gpd.GeoDataFrame(epa_sites, geometry=geometry, crs="EPSG:4326")
    epa_gdf = epa_gdf.to_crs(epsg=3857)
    
    # Plot EPA stations as scatter points
    scatter = ax.scatter(
        epa_gdf.geometry.x,
        epa_gdf.geometry.y,
        c=epa_gdf['pm25_value'],
        cmap='YlOrRd',
        s=200,
        edgecolor='black',
        linewidth=2,
        zorder=5,
        vmin=0,
        vmax=max(50, epa_gdf['pm25_value'].max())
    )
    
    # Add colorbar for PM2.5
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label('PM2.5 (µg/m³)', fontsize=12)
    
    # Add labels for each EPA station
    for idx, row in epa_gdf.iterrows():
        # Offset the label slightly to avoid overlapping with the marker
        ax.annotate(
            row['local_site_name'],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(8, 8),
            textcoords='offset points',
            fontsize=8,
            fontweight='bold',
            color='black',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.8),
            zorder=6
        )
    
    # Title
    ax.set_title(
        f'Official EPA PM2.5 Levels vs. Population {config["title_label"]}\n'
        f'Salt Lake & Davis Counties, Utah | Inversion Event: {INVERSION_START} to {INVERSION_END}',
        fontsize=16,
        fontweight='bold'
    )
    
    # Save
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n  Saved map to: {output_file}")
    plt.close()

# =============================================================================
# Step E: Create Interactive Map (Folium)
# =============================================================================
def get_pm25_color(pm25_value):
    """Return color based on EPA AQI categories for PM2.5."""
    if pm25_value < 12:
        return 'green'
    elif pm25_value < 35:
        return 'orange'
    else:
        return 'red'


def create_interactive_map(merged_gdf, epa_sites, output_file, age_group="65plus"):
    """
    Create an interactive Folium map with:
    1. Choropleth layer showing population by census tract
    2. Circle markers for EPA monitoring stations colored by PM2.5 level
    
    Args:
        merged_gdf: GeoDataFrame with census tracts and population data
        epa_sites: DataFrame with EPA monitoring station data
        output_file: Output file path for the map
        age_group: "65plus" or "85plus" to select which age group to visualize
    """
    print(f"\nStep E: Creating interactive Folium map for {age_group}...")
    
    # Map age group to column names and labels
    age_config = {
        "65plus": {
            "pct_col": "pop_65_plus_pct",
            "count_col": "pop_65_plus",
            "label": "65+",
            "title_label": "Age 65+",
            "legend_label": "Percentage of Residents Age 65+",
            "layer_name": "Population 65+ (Census Tracts)"
        },
        "85plus": {
            "pct_col": "pop_85_plus_pct",
            "count_col": "pop_85_plus",
            "label": "85+",
            "title_label": "Age 85+",
            "legend_label": "Percentage of Residents Age 85+",
            "layer_name": "Population 85+ (Census Tracts)"
        }
    }
    
    config = age_config[age_group]
    
    # Add formatted fields for tooltip display
    pct_formatted_col = f"{config['pct_col']}_formatted"
    count_formatted_col = f"{config['count_col']}_formatted"
    merged_gdf[pct_formatted_col] = merged_gdf[config['pct_col']].apply(lambda x: f"{x:.1f}%")
    merged_gdf[count_formatted_col] = merged_gdf[config['count_col']].apply(lambda x: f"{int(x):,}")
    
    # Convert to WGS84 for Folium
    gdf_wgs84 = merged_gdf.to_crs(epsg=4326)
    
    # Calculate map center
    bounds = gdf_wgs84.total_bounds
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
        columns=['GEOID', config['pct_col']],
        key_on='feature.properties.GEOID',
        fill_color='Blues',
        fill_opacity=0.6,
        line_opacity=0.3,
        line_weight=1,
        legend_name=config['legend_label'],
        name=config['layer_name'],
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
            fields=['NAMELSAD', pct_formatted_col, count_formatted_col],
            aliases=[f'Census Tract:', f'Percentage {config["label"]}:', f'Population {config["label"]} (Count):'],
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
    # LAYER 2: EPA Monitoring Stations
    # ==========================================
    print("  Adding EPA monitoring station markers...")
    
    epa_layer = folium.FeatureGroup(name='EPA Monitoring Stations (PM2.5)')
    
    for _, row in epa_sites.iterrows():
        pm25 = row['pm25_value']
        color = get_pm25_color(pm25)
        
        # Determine AQI category
        if pm25 < 12:
            status = 'Good'
        elif pm25 < 35:
            status = 'Moderate'
        else:
            status = 'Unhealthy for Sensitive Groups'
        
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 180px;">
            <b style="font-size: 14px;">{row['local_site_name']}</b><br>
            <hr style="margin: 5px 0;">
            <b>Site Number:</b> {row['site_number']}<br>
            <b>PM2.5:</b> {pm25:.1f} µg/m³<br>
            <b>AQI Status:</b> <span style="color: {color}; font-weight: bold;">{status}</span><br>
            <b>Coordinates:</b><br>
            &nbsp;&nbsp;Lat: {row['latitude']:.4f}<br>
            &nbsp;&nbsp;Lon: {row['longitude']:.4f}
        </div>
        """
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=15,
            color='black',
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['local_site_name']}: {pm25:.1f} µg/m³"
        ).add_to(epa_layer)
    
    epa_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Add legend
    legend_html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 15px; border: 2px solid gray;
                border-radius: 5px; font-family: Arial; font-size: 12px;
                box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
        <b style="font-size: 14px;">EPA PM2.5 Air Quality</b><br>
        <hr style="margin: 8px 0;">
        <i style="background: green; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Good (&lt;12 µg/m³)<br>
        <i style="background: orange; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Moderate (12-35 µg/m³)<br>
        <i style="background: red; width: 14px; height: 14px; display: inline-block; border-radius: 50%; border: 1px solid black;"></i> Unhealthy (&gt;35 µg/m³)
        <hr style="margin: 8px 0;">
        <b>Inversion Event:</b><br>
        {INVERSION_START} to {INVERSION_END}<br>
        <b>EPA Sites:</b> {len(epa_sites)}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save
    m.save(output_file)
    print(f"  Saved interactive map to: {output_file}")
    
    # Print summary
    good = len(epa_sites[epa_sites['pm25_value'] < 12])
    moderate = len(epa_sites[(epa_sites['pm25_value'] >= 12) & (epa_sites['pm25_value'] < 35)])
    unhealthy = len(epa_sites[epa_sites['pm25_value'] >= 35])
    print(f"  Site summary: {good} Good, {moderate} Moderate, {unhealthy} Unhealthy")

# =============================================================================
# Main Pipeline
# =============================================================================
def main():
    print("=" * 60)
    print("EPA PM2.5 and Elderly Population Geospatial Analysis")
    print("Salt Lake & Davis Counties, Utah")
    print("=" * 60)
    
    # Step A: Load and filter shapefile
    gdf = load_and_filter_shapefile(SHAPEFILE_PATH)
    
    # Step B: Process census demographics
    census_df = process_census_data(CENSUS_DATA_PATH)
    merged_gdf = merge_geo_and_census(gdf, census_df)
    
    # Step C: Process EPA air quality data
    epa_sites, df_filtered = process_epa_data(EPA_DATA_PATH)
    
    if len(epa_sites) == 0:
        print("\nERROR: No valid EPA data found.")
        return
    
    # Step C.5: Create data analysis plots
    create_data_analysis_plots(df_filtered, epa_sites, "epa_data_analysis.png")
    
    # Step D: Create static visualizations for both age groups
    create_visualization(merged_gdf, epa_sites, "epa_age_overlay_map_65plus.png", age_group="65plus")
    create_visualization(merged_gdf, epa_sites, "epa_age_overlay_map_85plus.png", age_group="85plus")
    
    # Step E: Create interactive maps for both age groups
    create_interactive_map(merged_gdf, epa_sites, "epa_interactive_map_65plus.html", age_group="65plus")
    create_interactive_map(merged_gdf, epa_sites, "epa_interactive_map_85plus.html", age_group="85plus")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("  65+ Maps:")
    print(f"    Static map:      epa_age_overlay_map_65plus.png")
    print(f"    Interactive map: epa_interactive_map_65plus.html")
    print("  85+ Maps:")
    print(f"    Static map:      epa_age_overlay_map_85plus.png")
    print(f"    Interactive map: epa_interactive_map_85plus.html")
    print("=" * 60)


if __name__ == "__main__":
    main()

