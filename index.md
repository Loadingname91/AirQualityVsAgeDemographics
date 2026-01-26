---
layout: default
title: "Project Report"
description: "Spatial Analysis of Environmental Inequity in Salt Lake City - Visualizing the Intersection of Senior Populations (80+) and PM2.5 Air Pollution"
---

# Project Report: Spatial Analysis of Environmental Inequity in Salt Lake City

### *Visualizing the Intersection of Senior Populations (80+) and PM2.5 Air Pollution*

---

## 1. Project Overview

### Research Question
This project investigates the spatial correlation between vulnerable demographic groups (specifically residents aged 80+) and exposure to PM2.5 particulate matter during winter inversion events in the Salt Lake Valley. 

### Study Area
- **Counties:** Salt Lake County (FIPS 49035) and Davis County (FIPS 49011), Utah

### Proof-of-Concept Approach
This report presents a **proof-of-concept demonstration** of geospatial analysis capabilities using two independent air quality data sources:

1. **EPA AQS Analysis (January 1-30, 2025):** Regulatory-grade monitoring data from 10 official EPA stations
2. **PurpleAir Analysis (January 1-25, 2026):** Community sensor network data from 254 validated sensors

**Important Note:** These analyses are **independent** and cannot be directly compared due to different time periods. The purpose is to demonstrate technical capability with different data sources and methodologies. The final analysis will use a consistent time period based on advisor feedback.

### Key Findings Preview
- **Demographic Distribution:** 36,524 residents aged 80+ across 301 inhabited census tracts
- **EPA Analysis (2025):** PM2.5 levels ranged from 0.30 to 30.24 µg/m³ across 10 monitoring stations (4,880 measurements)
- **PurpleAir Analysis (2026):** 254 sensors provided dense spatial coverage with PM2.5 values ranging from 2.65 to 275.45 µg/m³
- **Spatial Pattern:** Both analyses reveal spatial variation in air quality across the study area, with initial observations suggesting correlations between demographic distribution and pollution exposure

---

## 2. Data Acquisition Strategy

I explored three distinct datasets to find the best balance between **coverage** (spatial density) and **accuracy** (scientific rigor).

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

**Data Quality:**
- **Measurement Method:** FRM/FEM (Federal Reference/Equivalent Method)
- **Quality Assurance:** EPA-certified, regulatory-grade instruments
- **PM2.5 Range (Jan 1-30, 2025):** 0.30 - 30.24 µg/m³
- **Mean PM2.5:** 7.36 µg/m³
- **Median PM2.5:** 5.40 µg/m³
- **Air Quality Status:** 82.4% "Good" (<12 µg/m³), 17.6% "Moderate" (12-35 µg/m³), 0% "Unhealthy" (>35 µg/m³)

**For detailed EPA analysis, see:** [EPA Analysis Page]({{ '/epa-analysis' | relative_url }})

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
- **Sensors Filtered:** 25 sensors removed due to outlier values >500 µg/m³

**Quality Assurance:**
- **Correction Formula:** Applied University of Utah Winter Inversion correction:
  ```
  Corrected PM2.5 = (0.778 × Raw_CF1) + 2.65
  ```
- **Outlier Filtering:** Removed sensor readings >500 µg/m³ (physically impossible for ambient air, indicating hardware failure)

**For detailed PurpleAir analysis, see:** [PurpleAir Analysis Page]({{ '/purpleair-analysis' | relative_url }})

---

## 3. Technical Methodology Overview

### Coordinate System Standardization
- **Target CRS:** Web Mercator (EPSG:3857)
- **Rationale:** Standard web mapping projection ensures accurate overlay on basemaps and compatibility with web visualization libraries
- **Reprojection:** All spatial data (census tracts, monitoring station locations) converted from WGS84 (EPSG:4326) to EPSG:3857

### EPA Data Analysis Approach
- **Method:** Point-based visualization with monitoring stations as discrete locations
- **Statistical Method:** Mean PM2.5 calculated across all dates in the analysis period (January 1-30, 2025)
- **Visualization:** Color-coded stations overlaid on census tract choropleth

**For detailed EPA methodology, see:** [EPA Analysis Page]({{ '/epa-analysis' | relative_url }})

### PurpleAir Data Analysis Approach
- **Method:** Continuous surface visualization via spatial interpolation (IDW)
- **Data Correction:** University of Utah Winter Inversion formula applied to all sensors
- **Spatial Interpolation:** 200×200 grid with Inverse Distance Weighting
- **Visualization:** Heatmap surface with sensor locations as points

**For detailed PurpleAir methodology, see:** [PurpleAir Analysis Page]({{ '/purpleair-analysis' | relative_url }})

---

## 4. Key Findings and Insights

### 4.1. Demographic Distribution

- **Total Elderly Population (80+):** 36,524 residents across 301 inhabited census tracts
- **Spatial Pattern:** Higher concentrations observed on:
  - **East Bench:** Elevated areas with historically cleaner air
  - **Specific Valley Neighborhoods:** Some valley floor areas also show high elderly populations

### 4.2. EPA Analysis Findings (January 1-30, 2025)

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

**For detailed EPA findings and visualizations, see:** [EPA Analysis Page]({{ '/epa-analysis' | relative_url }})

### 4.3. PurpleAir Analysis Findings (January 1-25, 2026)

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

**For detailed PurpleAir findings and visualizations, see:** [PurpleAir Analysis Page]({{ '/purpleair-analysis' | relative_url }})

---

## 5. Technical Specifications

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

## 6. Future Roadmap

### Short-Term Enhancements

1. **Acquire TRAX Mobile Data:**
   - Contact Synoptic Data support for Enterprise API access
   - Alternative: Direct contact with University of Utah Atmospheric Sciences Department (U-ATAQ project)
   - Goal: Obtain Red Line, Green Line, and Blue Line sensor data

2. **TRAX Visualization:**
   - Plot GPS path line showing PM2.5 variation
   - Explicitly visualize elevation gradient (University of Utah bench → I-15 valley floor)
   - Create animated time-series showing pollution accumulation during inversion events

---

## 7. Reproducibility and Data Availability

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

## 8. Acknowledgments

- **Data Sources:**
  - US Census Bureau (demographic data)
  - EPA AQS API (regulatory air quality data)
  - PurpleAir Community Network (sensor data)
  - University of Utah (correction formula methodology)

- **Technical Support:**
  - Synoptic Data API documentation
  - GeoPandas and Folium communities

---

## 9. Descriptive Statistics Summary

This section provides a summary of comprehensive descriptive statistics for all datasets used in this analysis. Statistics were calculated from the processed data files and verified against execution logs.

**Important Note:** EPA and PurpleAir statistics are from different time periods and cannot be directly compared. Each analysis is independent.

### 9.1. EPA Data Summary (January 1-30, 2025)

- **Records:** 4,880 measurements
- **Mean PM2.5:** 7.36 µg/m³
- **Median PM2.5:** 5.40 µg/m³
- **Standard Deviation:** 5.81 µg/m³
- **Range:** 0.30 to 30.24 µg/m³
- **AQI Category Breakdown:**
  - Good (<12 µg/m³): 4,022 records (82.4%)
  - Moderate (12-35 µg/m³): 858 records (17.6%)
  - Unhealthy (>35 µg/m³): 0 records (0.0%)

**For complete EPA statistics, see:** [EPA Analysis Page]({{ '/epa-analysis' | relative_url }})

### 9.2. PurpleAir Data Summary (January 1-25, 2026)

- **Valid Sensors:** 254 (after quality control)
- **Mean PM2.5:** 20.93 µg/m³
- **Median PM2.5:** 16.61 µg/m³
- **Standard Deviation:** 29.83 µg/m³
- **Range:** 2.65 to 275.45 µg/m³
- **AQI Category Breakdown:**
  - Good (<12 µg/m³): 57 sensors (22.4%)
  - Moderate (12-35 µg/m³): 187 sensors (73.6%)
  - Unhealthy (>35 µg/m³): 10 sensors (3.9%)

**For complete PurpleAir statistics, see:** [PurpleAir Analysis Page]({{ '/purpleair-analysis' | relative_url }})

### 9.3. Census Data Summary

- **Total Tracts in Study Area:** 317 (Salt Lake + Davis counties)
- **Inhabited Tracts (pop_80+ > 0):** 301
- **Total 80+ Population:** 36,524 residents
- **Mean per Tract:** 121.3 residents
- **Median per Tract:** 102.0 residents

---

## 10. References and Methodology Notes

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

