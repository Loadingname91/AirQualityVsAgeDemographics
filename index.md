---
layout: default
title: "Project Report"
description: "Visualizing the Intersection of Senior Populations (80+) and PM2.5 Air Pollution"
permalink: /
---

# Project Report: *Visualizing the Intersection of Senior Populations (80+) and PM2.5 Air Pollution*

---

## 1. Project Overview

This project investigates the spatial correlation between vulnerable demographic groups (specifically residents aged 80+) and exposure to PM2.5 particulate matter in the Salt Lake and surrounding counties. 

### Study Area
- **Counties:** Salt Lake County (FIPS 49035), Davis County (FIPS 49011), and Utah County (FIPS 49053), Utah

### Proof-of-Concept Approach
This report presents a demonstration of geospatial analysis capabilities using two independent air quality data sources:

1. **EPA AQS Analysis (January 1-30, 2025):** Regulatory-grade monitoring data from 10 official EPA stations
2. **PurpleAir Analysis (January 1-25, 2026):** Community sensor network data from 254 validated sensors

**Important Note:** I did this analysis as a proof of concept to see how we can use the data to visualize the correlation between the demographic distribution and the air quality. The time period is not consistent between the two datasets, since the EPA data is from 2025 and the PurpleAir data is from 2026 , this is because the EPA data is not available for the year 2026.

### Key Findings Preview
- **Demographic Distribution:** 36,524 residents aged 80+ across 301 inhabited census tracts
- **EPA Analysis (2025):** PM2.5 levels ranged from 0.30 to 30.24 µg/m³ across 10 monitoring stations (4,880 measurements)
- **PurpleAir Analysis (2026):** 254 sensors provided dense spatial coverage with PM2.5 values ranging from 2.65 to 275.45 µg/m³
- **Spatial Pattern:** Both analyses reveal spatial variation in air quality across the study area, with initial observations suggesting correlations between demographic distribution and pollution exposure

---

## 2. Data Acquisition Strategy (The "Iterative" Process)

I explored three distinct datasets 

### A. Demographic Data (The "People" Layer)

#### Source and Acquisition
* **Source:** US Census Bureau (American Community Survey 5-Year Estimates, 2023)
* **Table:** `B01001` (Sex by Age)
* **Geographic Unit:** Census Tracts
* **Download Method:** Direct CSV download from Census Bureau website

#### Data Processing Pipeline
1. **Age Group Aggregation:**
   - Extracted columns: `B01001_024E` (Male 80-84), `B01001_025E` (Male 85+), `B01001_048E` (Female 80-84), `B01001_049E` (Female 85+)
   - Calculated total population aged 80+ per census tract
   - Converted GEO_ID format (removed "1400000US" prefix) to match shapefile GEOID

2. **Geographic Integration:**
   - Joined demographic data with `tl_2025_49_tract.shp` (Census Tract Shapefiles)
   - Filtered to Salt Lake County (FIPS 49035) and Davis County (FIPS 49011)
   - Reprojected to Web Mercator (EPSG:3857) for web mapping compatibility

3. **Data Refinement:**
   - **Filtered out uninhabited tracts:** Removed 16 tracts with zero 80+ population (e.g., Great Salt Lake, Airport, industrial zones)
   - **Outlier removal:** Dropped large, sparsely-populated tracts (>95th percentile area with <10 residents aged 80+) that would visually dominate the map
   - **Final dataset:** 301 inhabited census tracts with valid demographic data

#### Final Statistics
- **Total 80+ Population:** 36,524 residents
- **Tract Coverage:** 301 census tracts
- **Spatial Distribution:** Concentrated on East Bench (higher elevation) and specific valley neighborhoods

---

### B. Air Quality Data (The "Environment" Layer)


This proof-of-concept demonstrates analysis capabilities with two independent air quality data sources. Each source has distinct characteristics and is analyzed separately.
|
#### B.1. EPA AQS Analysis (January 1-30, 2025)

**Data Source:**
- **API:** EPA AQS Data API (https://aqs.epa.gov/data/api)
- **Endpoint:** `/dailyData/byCounty`
- **Parameter Code:** 88101 (PM2.5 FRM/FEM Mass)
- **Authentication:** Email-based API key system

**Data Characteristics:**
- **Total Monitoring Sites:** 10 official EPA stations
- **Geographic Coverage:** 
  - Salt Lake County: 9 stations
  - Davis County: 1 station (Bountiful Viewmont)
- **Temporal Resolution:** Daily 24-hour averages
- **Analysis Period:** January 1-30, 2025
- **Records in Analysis Period:** 4,880 measurements
- **Full Dataset Available:** 57,639 records (January 1 - December 31, 2025)

**Monitoring Stations:**
1. Bountiful Viewmont (Site 4) - Davis County
2. Copper View (Site 2005) - Salt Lake County
3. Hawthorne (Site 3006) - Salt Lake County
4. ROSE PARK (Site 3010) - Salt Lake County
5. Herriman #3 (Site 3013) - Salt Lake County
6. Lake Park (Site 3014) - Salt Lake County
7. Utah Technical Center (Site 3015) - Salt Lake County
8. Inland Port (Site 3016) - Salt Lake County
9. Red Butte (Site 3018) - Salt Lake County
10. Near Road (Site 4002) - Salt Lake County

**Data Quality:**
- **Measurement Method:** FRM/FEM (Federal Reference/Equivalent Method)
- **Quality Assurance:** EPA-certified, regulatory-grade instruments
- **PM2.5 Range (Jan 1-30, 2025):** 0.30 - 30.24 µg/m³
- **Mean PM2.5:** 7.36 µg/m³
- **Median PM2.5:** 5.40 µg/m³
- **Air Quality Status:** 82.4% "Good" (<12 µg/m³), 17.6% "Moderate" (12-35 µg/m³), 0% "Unhealthy" (>35 µg/m³)

**Advantages:**
- Regulatory-grade accuracy and precision
- Official data accepted for compliance reporting
- Long-term historical records available
- Consistent measurement methodology

**Limitations:**
- Low spatial density (10 sites for entire study area)
- Data availability lag (2-4 weeks after collection)
- Insufficient for neighborhood-level interpolation with heatmap visualization

#### B.2. PurpleAir Analysis (January 1-25, 2026)

**Data Source:**
- **Platform:** PurpleAir Community Sensor Network
- **Sensor Model:** Plantower PMS5003/PMS6003 optical particle counters
- **Data Format:** CSV files with 60-minute averages
- **Access Method:** Direct CSV download from PurpleAir website

**Data Characteristics:**
- **Total Sensors:** 279 sensors in master sensor list
- **Spatial Distribution:** Dense urban coverage, with sensors distributed across residential, commercial, and institutional locations
- **Temporal Coverage:** January 1-25, 2026 (60-minute averages)
- **Valid Sensors Processed:** 254 sensors with valid data after quality control (91.0% data completeness)
- **Sensors Filtered:** 25 sensors removed due to outlier values >500 µg/m³ might be due to sensor errors or maintenance issues.

**Quality Assurance:**
- **Correction Formula:** Applied University of Utah Winter Inversion correction:
  ```
  Corrected PM2.5 = (0.778 × Raw_CF1) + 2.65
  ```
- **Outlier Filtering:** Removed sensor readings >500 µg/m³ (physically impossible for ambient air, indicating hardware failure)
- **Rationale:** PurpleAir sensors are optical particle counters that tend to overestimate PM2.5 in high-humidity conditions. The correction formula was derived from co-location studies comparing PurpleAir sensors with EPA FRM monitors under Utah winter conditions.

**Advantages:**
- High spatial density enables detailed neighborhood-level analysis
- Near real-time data availability
- Community-maintained network provides extensive coverage
- Enables spatial interpolation for continuous surface mapping

**Limitations:**
- Requires calibration correction for accuracy
- Variable sensor maintenance quality
- Potential data gaps if sensors go offline
- Different temporal resolution (hourly) compared to EPA daily averages

#### B.3. TRAX Mobile Sensor Data (Not Available)

**Data Source:**
- **Platform:** Synoptic Data API (U-ATAQ project)
- **Sensor Type:** Mobile PM2.5 sensors mounted on TRAX light rail trains
- **Coverage:** Linear paths along Red Line, Green Line, and Blue Line routes

**Potential Value:**
- Captures the elevation gradient explicitly as trains travel from University of Utah (bench elevation ~4,800 ft) to valley floor (~4,200 ft)
- Continuous measurements along transit corridors
- Represents real-world exposure for transit-dependent populations

**Access Status:**
- **Data Source Unavailable:** The website at https://atmos.utah.edu/air_quality/trax/ referenced in the TRAX Light-Rail Train Air Quality Observation Project (Mendoza et al.) from the University of Utah Atmospheric Sciences Department is no longer accessible
- **Attempted Access:** Attempted access during project development period but could not retrieve data as noted in the paper 
The TRAX Light-Rail Train Air Quality Observation Project  
Authors: Daniel L. Mendoza¹²*, Erik T. Crosman³, Logan E. Mitchell¹,  
Benjamin Fasoli¹, Andrew M. Park¹, John C. Lin¹, Alexander A. Jacques¹,  
and John D. Horel¹
- **Analysis Status:** This data source was skipped for this analysis due to unavailability

---

## 3. Technical Methodology

### 3.A. EPA Data Analysis Methodology (January 1-30, 2025)

#### Coordinate System Standardization
- **Target CRS:** Web Mercator (EPSG:3857)
- **Rationale:** Standard web mapping projection ensures accurate overlay on basemaps and compatibility with web visualization libraries
- **Reprojection:** All spatial data (census tracts, monitoring station locations) converted from WGS84 (EPSG:4326) to EPSG:3857

#### Data Processing
- **Temporal Aggregation:** Daily 24-hour average PM2.5 values aggregated by monitoring station
- **Statistical Method:** Mean PM2.5 calculated across all dates in the analysis period (January 1-30, 2025)
- **Result:** One representative PM2.5 value per monitoring station for point-based visualization
- **Rationale:** Provides single representative value per station that captures the overall air quality pattern during the analysis period

#### Visualization Approach
- **Method:** Point-based visualization with monitoring stations as discrete locations
- **Color Coding:** Stations color-coded by PM2.5 value using YlOrRd colormap
- **Demographic Context:** Overlaid on census tract choropleth showing population 80+ distribution
- **Output:** High-resolution static maps (300 DPI) and interactive web maps

### 3.B. PurpleAir Data Analysis Methodology (January 1-25, 2026)

#### Coordinate System Standardization
- **Target CRS:** Web Mercator (EPSG:3857)
- **Rationale:** Standard web mapping projection ensures accurate overlay on basemaps and compatibility with web visualization libraries
- **Reprojection:** All spatial data (census tracts, sensor locations) converted from WGS84 (EPSG:4326) to EPSG:3857

#### Data Correction
**Correction Formula (University of Utah Winter Inversion):**
```
Corrected PM2.5 = (0.778 × Raw_CF1) + 2.65
```

**Rationale:**
- PurpleAir sensors are optical particle counters that tend to overestimate PM2.5 in high-humidity conditions
- Winter inversions in Salt Lake Valley create high-humidity environments
- University of Utah researchers developed this correction formula specifically for Utah winter conditions
- Formula derived from co-location studies comparing PurpleAir sensors with EPA FRM monitors

**Application:**
- Applied to all raw sensor readings before aggregation
- Correction applied before any spatial analysis or visualization

#### Quality Assurance
**Outlier Detection:**
- **Physical Impossibility Threshold:** PM2.5 > 500 µg/m³
- **Rationale:** Ambient PM2.5 levels above 500 µg/m³ are physically impossible in urban environments
- **Action:** Automatically filtered as hardware sensor errors
- **Impact:** 25 sensors (9.0%) removed from analysis

**Visualization Range:**
- Color scale capped at 80 µg/m³ to prevent extreme outliers from dominating visualization
- Data preserved for analysis but visually constrained for clarity

#### Spatial Interpolation
**Method:** Inverse Distance Weighting (IDW) interpolation

**Process:**
1. **Input Data:** Discrete PurpleAir sensor points with corrected PM2.5 values
2. **Grid Creation:** 200×200 interpolation grid covering study area bounds
3. **Interpolation Method:** Linear interpolation to create continuous PM2.5 surface
4. **Output:** Continuous PM2.5 surface as 2D array for heatmap visualization

**Spatial Clipping:**
- **Mask Layer:** Census tract boundaries (merged union)
- **Purpose:** Restrict heatmap visualization to inhabited land areas only
- **Result:** Clean visualization without pollution data over water bodies, mountains, or uninhabited areas

#### Data Aggregation
- **Temporal Aggregation:** Mean PM2.5 per sensor across entire study period (January 1-25, 2026)
- **Spatial Representation:** Each sensor represented as single point with aggregated value
- **Rationale:** Enables interpolation between sensors while maintaining individual sensor accuracy

#### Visualization Approach
- **Method:** Continuous surface visualization via spatial interpolation
- **Color Mapping:** OrRd colormap (yellow = low, red = high PM2.5)
- **Demographic Context:** Side-by-side with census tract choropleth showing population 80+ distribution
- **Output:** High-resolution static maps (300 DPI) and interactive web maps

---

## 4. Current Deliverables

### 4.A. EPA Analysis Deliverables (January 1-30, 2025)

#### Static Visualization
**File:** `EPADataAnalysis/epa_age_overlay_map.png`

**Layout:**
- **Single Combined Map:**
  - **Background Layer:** Census tracts colored by 80+ population (Blues colormap)
  - **Overlay Layer:** EPA monitoring stations as large scatter points
    - Color-coded by PM2.5 value (YlOrRd colormap)
    - Black edges for visibility
    - Labeled with station names

**Purpose:** Focus on official regulatory data with demographic context, using point-based visualization without interpolation assumptions.

#### Data Analysis Plots
**File:** `EPADataAnalysis/epa_data_analysis.png`

**Content:**
- Panel 1: PM2.5 Distribution Histogram (all data vs. inversion period)
- Panel 2: Box Plot by Monitoring Site (horizontal layout)
- Panel 3: Time Series (Daily Average PM2.5 Over Time)
- Panel 4: Summary Statistics Table

#### Interactive Web Map
**File:** `EPADataAnalysis/epa_interactive_map.html`

**Features:**
- Choropleth layer for population demographics (toggleable)
- Circle markers for EPA monitoring stations (color-coded by PM2.5 level)
- Hover tooltips showing census tract information
- Clickable popups with detailed station information
- Layer control panel for toggling visibility
- Legend with data period (January 1-30, 2025) and station counts
- Responsive design for desktop and mobile viewing

### 4.B. PurpleAir Analysis Deliverables (January 1-25, 2026)

#### Static Visualization
**File:** `PurpleAirDataAnalysis/final_analysis_map.png`

**Layout:**
1. **Left Panel:** Choropleth map of **Age 80+ Population Density**
   - Colormap: Blues (light = low, dark = high)
   - Clearly shows concentration of seniors on East Bench and specific valley neighborhoods
   - Legend: Population count per census tract (1-548 residents aged 80+)

2. **Right Panel:** **PM2.5 Heatmap**
   - Interpolated surface from 254 PurpleAir sensors
   - Colormap: OrRd (yellow = low, red = high)
   - Sensor locations shown as black dots for transparency
   - Spatial interpolation enables continuous surface mapping

**Purpose:** Demonstrate high-density sensor network capability for detailed neighborhood-level air quality visualization.

#### Data Analysis Plots
**File:** `PurpleAirDataAnalysis/purpleair_data_analysis.png`

**Content:**
- Panel 1: PM2.5 Distribution Histogram (corrected values)
- Panel 2: Box Plot by AQI Category
- Panel 3: Spatial Distribution (Latitude vs. Longitude colored by PM2.5)
- Panel 4: Summary Statistics Table

#### Interactive Web Map
**File:** `PurpleAirDataAnalysis/slc_analysis_interactive.html`

**Features:**
- Choropleth layer for population demographics (toggleable)
- Circle markers for PurpleAir sensors (color-coded by PM2.5 level)
- Hover tooltips showing census tract information
- Clickable popups with detailed sensor information
- Layer control panel for toggling visibility
- Color-coded sensors by AQI category (Good/Moderate/Unhealthy)
- Legend with data period (January 1-25, 2026) and sensor counts
- Responsive design for desktop and mobile viewing

## 5. Key Findings and Insights

### 5.1. Demographic Distribution

- **Total Elderly Population (80+):** 36,524 residents across 301 inhabited census tracts
- **Spatial Pattern:** Higher concentrations observed on:
  - **East Bench:** Elevated areas with historically cleaner air
  - **Specific Valley Neighborhoods:** Some valley floor areas also show high elderly populations

### 5.A. EPA Analysis Findings (January 1-30, 2025)

#### Air Quality Patterns
- **Analysis Period:** January 1-30, 2025
- **Total Records:** 4,880 measurements across 10 monitoring stations
- **Mean PM2.5:** 7.36 µg/m³
- **Median PM2.5:** 5.40 µg/m³
- **Range:** 0.30 - 30.24 µg/m³
- **Standard Deviation:** 5.81 µg/m³

#### Air Quality Status Distribution
- **Good (<12 µg/m³):** 4,022 records (82.4%)
- **Moderate (12-35 µg/m³):** 858 records (17.6%)
- **Unhealthy (>35 µg/m³):** 0 records (0.0%)

#### Site-Level Observations
- **Red Butte (Site 3018):** Lowest mean PM2.5 (4.22 µg/m³), consistent with elevated bench location
- **Near Road (Site 4002):** Highest mean PM2.5 (9.63 µg/m³), reflecting proximity to traffic emissions
- **Spatial Variation:** PM2.5 values range from 4.22 to 9.63 µg/m³ across sites, showing clear spatial heterogeneity

#### Preliminary Observations
- Regulatory-grade data provides reliable point measurements but limited spatial coverage
- Site-level differences suggest elevation and proximity to traffic sources influence PM2.5 concentrations
- Further analysis needed to quantify correlation between elderly population density and PM2.5 exposure at monitoring station locations

### 5.B. PurpleAir Analysis Findings (January 1-25, 2026)

#### Air Quality Patterns
- **Analysis Period:** January 1-25, 2026
- **Valid Sensors:** 254 sensors with quality-controlled data
- **Mean PM2.5:** 20.93 µg/m³
- **Median PM2.5:** 16.61 µg/m³
- **Range:** 2.65 to 275.45 µg/m³
- **Standard Deviation:** 29.83 µg/m³

#### Air Quality Status Distribution
- **Good (<12 µg/m³):** 57 sensors (22.4%)
- **Moderate (12-35 µg/m³):** 187 sensors (73.6%)
- **Unhealthy (>35 µg/m³):** 10 sensors (3.9%)

#### Spatial Variation
- High-density sensor network reveals neighborhood-level variations
- Some areas show 2-3x PM2.5 differences between nearby neighborhoods
- Valley floor generally shows higher concentrations than bench areas
- Wide standard deviation (29.83 µg/m³) indicates significant spatial heterogeneity

---

## 7. Technical Specifications

### Software and Libraries

**Python Environment:**
- Python 3.x
- Key libraries:
  - `geopandas` - Geospatial data manipulation
  - `pandas` - Data analysis
  - `matplotlib` - Static visualization
  - `folium` - Interactive web maps
  - `scipy` - Spatial interpolation
  - `contextily` - Basemap tiles
  - `requests` - API data access

**Data Formats:**
- Shapefiles (.shp) - Census tract boundaries
- CSV - Tabular data (demographics, sensor data)
- JSON - API responses
- PNG - Static map outputs (300 DPI)
- HTML - Interactive map outputs
---

## 8. Future Roadmap

### Short-Term Enhancements

1. **Acquire TRAX Mobile Data:**
   - Contact University of Utah Atmospheric Sciences Department for alternative access to TRAX mobile data
   - The original data portal (https://atmos.utah.edu/air_quality/trax/) is no longer accessible
   - Goal: Obtain Red Line, Green Line, and Blue Line sensor data if alternative access becomes available

2. **TRAX Visualization (if data becomes available):**
   - Plot GPS path line showing PM2.5 variation
   - Explicitly visualize elevation gradient (University of Utah bench → I-15 valley floor)
   - Create animated time-series showing pollution accumulation during inversion events



## 9. Reproducibility and Data Availability

### Reproducibility
- All analysis scripts are documented and commented
- Configuration parameters clearly defined at top of each script
- Data processing steps are sequential and traceable
- Visualization code is modular and reusable

### Data Availability
- **EPA Data:** Publicly available via EPA AQS API (requires free account)
- **PurpleAir Data:** Publicly available via PurpleAir website
- **Census Data:** Publicly available via US Census Bureau
- **Processed Data:** CSV files included in repository


---

## 10. Acknowledgments

- **Data Sources:**
  - US Census Bureau (demographic data)
  - EPA AQS API (regulatory air quality data)
  - PurpleAir Community Network (sensor data)
  - University of Utah (correction formula methodology)

- **Technical Support:**
  - Synoptic Data API documentation
  - GeoPandas and Folium communities

---

## 11. Descriptive Statistics

This section provides comprehensive descriptive statistics for all datasets used in this analysis. Statistics were calculated from the processed data files and verified against execution logs.

**Important Note:** EPA and PurpleAir statistics are from different time periods and cannot be directly compared. Each analysis is independent.

### 11.1. EPA Data Descriptive Statistics (January 1-30, 2025)

#### Analysis Period Statistics
- **Analysis Period:** January 1-30, 2025
- **Records:** 4,880 measurements
- **Mean PM2.5:** 7.36 µg/m³
- **Median PM2.5:** 5.40 µg/m³
- **Standard Deviation:** 5.81 µg/m³
- **Range:** 0.30 to 30.24 µg/m³
- **25th Percentile:** 3.40 µg/m³
- **75th Percentile:** 9.20 µg/m³
- **AQI Category Breakdown:**
  - Good (<12 µg/m³): 4,022 records (82.4%)
  - Moderate (12-35 µg/m³): 858 records (17.6%)
  - Unhealthy (>35 µg/m³): 0 records (0.0%)

#### Overall Dataset Statistics (Full Year 2025)
- **Total Records:** 57,639 (January 1 - December 31, 2025)
- **Monitoring Sites:** 10
- **Mean PM2.5:** 6.65 µg/m³
- **Median PM2.5:** 5.80 µg/m³
- **Standard Deviation:** 4.16 µg/m³
- **Range:** -0.16 to 38.41 µg/m³
- **25th Percentile:** 3.90 µg/m³
- **75th Percentile:** 8.30 µg/m³

#### Site-Level Statistics (Analysis Period: January 1-30, 2025)
| Site Number | Site Name | Count | Mean (µg/m³) | Min (µg/m³) | Max (µg/m³) | Std Dev |
|-------------|-----------|-------|---------------|-------------|-------------|---------|
| 4 | Bountiful Viewmont | 478 | 6.90 | 1.0 | 22.70 | 5.68 |
| 2005 | Copper View | 510 | 8.43 | 2.1 | 25.35 | 5.87 |
| 3006 | Hawthorne | 772 | 7.65 | 1.4 | 23.10 | 5.79 |
| 3010 | ROSE PARK | 750 | 8.01 | 1.6 | 26.70 | 6.42 |
| 3013 | Herriman #3 | 540 | 5.37 | 0.9 | 14.45 | 3.79 |
| 3014 | Lake Park | 270 | 6.41 | 1.5 | 20.18 | 4.84 |
| 3015 | Utah Technical Center | 510 | 7.88 | 1.7 | 25.90 | 6.13 |
| 3016 | Inland Port | 270 | 6.28 | 0.4 | 22.64 | 5.25 |
| 3018 | Red Butte | 270 | 4.22 | 0.3 | 10.24 | 3.14 |
| 4002 | Near Road | 510 | 9.63 | 2.4 | 30.24 | 6.65 |

**Note:** Red Butte (Site 3018) shows the lowest mean PM2.5 (4.22 µg/m³), consistent with its elevated bench location. Near Road (Site 4002) shows the highest mean (9.63 µg/m³), reflecting proximity to traffic emissions.

### 11.2. PurpleAir Data Descriptive Statistics (January 1-25, 2026)

#### Sensor Network Summary
- **Analysis Period:** January 1-25, 2026
- **Total Sensor Files:** 279
- **Sensors in Master List:** 279
- **Valid Sensors Processed:** 254 (after quality control)
- **Sensors Filtered (Outliers >500 µg/m³):** 25

#### PM2.5 Distribution Statistics (Corrected Values)
- **Count:** 254 sensors
- **Mean PM2.5:** 20.93 µg/m³
- **Median PM2.5:** 16.61 µg/m³
- **Standard Deviation:** 29.83 µg/m³
- **Range:** 2.65 to 275.45 µg/m³
- **25th Percentile:** 12.37 µg/m³
- **75th Percentile:** 20.25 µg/m³

#### AQI Category Breakdown
- **Good (<12 µg/m³):** 57 sensors (22.4%)
- **Moderate (12-35 µg/m³):** 187 sensors (73.6%)
- **Unhealthy (>35 µg/m³):** 10 sensors (3.9%)

#### Spatial Distribution
- **Latitude Range:** 40.4245° to 41.1540°
- **Longitude Range:** -112.1160° to -111.5722°

**Observations:**
- The wide standard deviation (29.83 µg/m³) indicates significant spatial heterogeneity in PM2.5 concentrations across the study area
- High spatial density enables capture of neighborhood-level variations not possible with sparse regulatory network
- Some sensors located in microenvironments with elevated concentrations contribute to the wide range

### 11.3. Census Data Descriptive Statistics

#### Population 80+ Summary
- **Total Tracts in Study Area:** 317 (Salt Lake + Davis counties)
- **Inhabited Tracts (pop_80+ > 0):** 301
- **Total 80+ Population:** 36,524 residents

#### Tract-Level Distribution
- **Mean per Tract:** 121.3 residents
- **Median per Tract:** 102.0 residents
- **Standard Deviation:** 95.6 residents
- **Range:** 1 to 548 residents
- **25th Percentile:** 50.0 residents
- **75th Percentile:** 167.0 residents

#### Population Distribution by County
**Salt Lake County:**
- Tracts: 240
- Total 80+ Population: 28,562 (78.2% of study area total)

**Davis County:**
- Tracts: 61
- Total 80+ Population: 7,962 (21.8% of study area total)

### 11.4. Data Quality Metrics

#### EPA Data Quality (January 1-30, 2025)
- **Data Completeness:** 100% for all 10 monitoring sites during analysis period
- **Temporal Coverage:** Continuous daily measurements
- **Outlier Detection:** No values exceeded 500 µg/m³ (all values within physically reasonable range)
- **Negative Values:** 1 record with -0.16 µg/m³ (likely measurement artifact, represents <0.1% of data)

#### PurpleAir Data Quality (January 1-25, 2026)
- **Data Completeness:** 91.0% (254 of 279 sensors with valid data)
- **Outlier Filtering:** 25 sensors (9.0%) filtered due to values >500 µg/m³
- **Correction Applied:** University of Utah Winter Inversion formula applied to all sensors
- **Spatial Coverage:** Dense urban coverage with sensors distributed across residential, commercial, and institutional locations
- **Temporal Resolution:** 60-minute averages (hourly data)

#### Census Data Quality
- **Geographic Coverage:** Complete coverage of all census tracts in study area
- **Data Completeness:** 100% for demographic variables
- **Tract Filtering:** 16 tracts (5.0%) excluded due to zero 80+ population (water bodies, airports, industrial zones)

### 11.5. Analysis Plot Outputs

The following statistical analysis plots were generated as part of this analysis:

1. **EPA Data Analysis Plots** (`EPADataAnalysis/epa_data_analysis.png`)
   - Panel 1: PM2.5 Distribution Histogram (all data vs. inversion period)
   - Panel 2: Box Plot by Monitoring Site
   - Panel 3: Time Series (Daily Average PM2.5 Over Time)
   - Panel 4: Summary Statistics Table

2. **PurpleAir Data Analysis Plots** (`PurpleAirDataAnalysis/purpleair_data_analysis.png`)
   - Panel 1: PM2.5 Distribution Histogram (corrected values)
   - Panel 2: Box Plot by AQI Category
   - Panel 3: Spatial Distribution (Latitude vs. Longitude colored by PM2.5)
   - Panel 4: Summary Statistics Table

These plots provide comprehensive visual summaries of the data distributions, temporal patterns, and spatial characteristics, complementing the numerical statistics presented above.

---

## 12. References and Methodology Notes

### Correction Formula Source
- University of Utah Winter Inversion correction formula for PurpleAir sensors
- Derived from co-location studies with EPA FRM monitors
- Specific to Utah winter high-humidity conditions

### EPA AQI Categories (PM2.5)
- **Good:** 0-12 µg/m³
- **Moderate:** 12.1-35.4 µg/m³
- **Unhealthy for Sensitive Groups:** 35.5-55.4 µg/m³
- **Unhealthy:** 55.5-150.4 µg/m³
- **Very Unhealthy:** 150.5-250.4 µg/m³
- **Hazardous:** >250.4 µg/m³

### Census Data Notes
- ACS 5-Year Estimates provide most stable demographic estimates
- 2023 data represents 2019-2023 period
- Margin of error increases for small population groups (like 80+)