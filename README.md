# Spatial Analysis of Environmental Inequity in Salt Lake City

### Visualizing the Intersection of Senior Populations (80+) and PM2.5 Air Pollution

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://Loadingname91.github.io/AirQualityVsAgeDemographics/)

This project investigates the spatial correlation between vulnerable demographic groups (specifically residents aged 80+) and exposure to PM2.5 particulate matter during winter inversion events in the Salt Lake Valley, Utah.

##  Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Deliverables](#deliverables)
- [GitHub Pages](#github-pages)
- [Technical Specifications](#technical-specifications)
- [Contributing](#contributing)
- [License](#license)

##  Overview

This project presents a **proof-of-concept demonstration** of geospatial analysis capabilities using two independent air quality data sources:

1. **EPA AQS Analysis (January 1-30, 2025):** Regulatory-grade monitoring data from 10 official EPA stations
2. **PurpleAir Analysis (January 1-25, 2026):** Community sensor network data from 254 validated sensors

**Important Note:** These analyses are **independent** and cannot be directly compared due to different time periods. The purpose is to demonstrate technical capability with different data sources and methodologies.

### Study Area
- **Counties:** Salt Lake County (FIPS 49035) and Davis County (FIPS 49011), Utah
- **Demographic Focus:** Residents aged 80+ (36,524 residents across 301 inhabited census tracts)

##  Features

- **Dual Data Source Analysis:**
  - EPA regulatory-grade monitoring stations (10 sites)
  - PurpleAir community sensor network (254 validated sensors)

- **Comprehensive Visualizations:**
  - Static high-resolution maps (300 DPI)
  - Interactive web maps with Folium
  - Statistical analysis plots (histograms, box plots, time series)
  - Spatial interpolation heatmaps

- **Geospatial Integration:**
  - Census tract demographic overlays
  - Coordinate system standardization (EPSG:3857)
  - Spatial interpolation (IDW) for continuous surfaces

- **Data Quality Assurance:**
  - EPA-certified regulatory data
  - PurpleAir correction formulas (University of Utah Winter Inversion)
  - Outlier detection and filtering

##  Project Structure

```
GeoSpatialDataProject/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── _config.yml                       # Jekyll configuration for GitHub Pages
├── index.md                          # Homepage for GitHub Pages
├── epa-analysis.md                   # EPA analysis page
├── purpleair-analysis.md             # PurpleAir analysis page
├── Report.md                         # Full project report
│
├── _layouts/                         # Jekyll layout templates
│   └── default.html
├── _includes/                        # Jekyll includes
│   ├── navigation.html
│   └── interactive_map.html
├── assets/                           # Static assets for GitHub Pages
│   ├── images/                       # PNG visualizations
│   └── maps/                         # Interactive HTML maps
│
├── EPADataAnalysis/                  # EPA data analysis scripts
│   ├── main.py                       # Main EPA analysis pipeline
│   ├── get_epa_data.py              # EPA API data retrieval
│   ├── epa_utah_data.csv            # Processed EPA data
│   ├── epa_age_overlay_map.png      # Static visualization
│   ├── epa_data_analysis.png        # Statistical plots
│   └── epa_interactive_map.html     # Interactive map
│
├── PurpleAirDataAnalysis/            # PurpleAir data analysis scripts
│   ├── main.py                       # Main PurpleAir analysis pipeline
│   ├── master_sensor_list.csv        # Sensor location data
│   ├── final_analysis_map.png       # Static visualization
│   ├── purpleair_data_analysis.png  # Statistical plots
│   └── slc_analysis_interactive.html # Interactive map
│
├── Data/                             # Raw data files (not in git)
│   ├── PurpleAirData-Pm2.5Data/     # PurpleAir CSV files
│   └── tl_2025_49_tract/           # Census tract shapefiles
│
└── calculate_statistics.py          # Descriptive statistics calculator
```

##  Installation

### Prerequisites

- Python 3.8 or higher
- Git
- (Optional) Jekyll for local GitHub Pages preview

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Loadingname91/GeoSpatialDataProject.git
   cd GeoSpatialDataProject
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Jekyll (for local GitHub Pages preview, optional):**
   ```bash
   gem install bundler jekyll
   ```

##  Usage

### Running EPA Analysis

```bash
cd EPADataAnalysis
python main.py
```

This will:
- Load and process EPA AQS data
- Generate static visualizations
- Create interactive web maps
- Output analysis plots

### Running PurpleAir Analysis

```bash
cd PurpleAirDataAnalysis
python main.py
```

This will:
- Process PurpleAir sensor data
- Apply correction formulas
- Perform spatial interpolation
- Generate visualizations

### Calculating Descriptive Statistics

```bash
python calculate_statistics.py
```

This generates comprehensive statistics for EPA, PurpleAir, and Census data.

### Local GitHub Pages Preview

```bash
jekyll serve
```

Then visit `http://localhost:4000` in your browser.

##  Data Sources

### Demographic Data
- **Source:** US Census Bureau (American Community Survey 5-Year Estimates, 2023)
- **Table:** `B01001` (Sex by Age)
- **Geographic Unit:** Census Tracts
- **Focus:** Population aged 80+ in Salt Lake and Davis counties

### EPA AQS Data
- **Source:** EPA AQS Data API (https://aqs.epa.gov/data/api)
- **Parameter:** PM2.5 FRM/FEM Mass (Code 88101)
- **Coverage:** 10 monitoring stations in Salt Lake and Davis counties
- **Period:** January 1-30, 2025 (4,880 measurements)
- **Access:** Requires free EPA API account

### PurpleAir Data
- **Source:** PurpleAir Community Sensor Network
- **Sensors:** 279 sensors in master list, 254 validated after quality control
- **Period:** January 1-25, 2026 (60-minute averages)
- **Correction:** University of Utah Winter Inversion formula applied
- **Access:** Direct CSV download from PurpleAir website

##  Deliverables

### EPA Analysis
- **Static Map:** `EPADataAnalysis/epa_age_overlay_map.png`
- **Analysis Plots:** `EPADataAnalysis/epa_data_analysis.png`
- **Interactive Map:** `EPADataAnalysis/epa_interactive_map.html`

### PurpleAir Analysis
- **Static Map:** `PurpleAirDataAnalysis/final_analysis_map.png`
- **Analysis Plots:** `PurpleAirDataAnalysis/purpleair_data_analysis.png`
- **Interactive Map:** `PurpleAirDataAnalysis/slc_analysis_interactive.html`

### Documentation
- **Full Report:** `Report.md`
- **GitHub Pages Site:** Live documentation with embedded visualizations

##  GitHub Pages

This project includes a Jekyll-based GitHub Pages site with:

- **Homepage:** Project overview and key findings
- **EPA Analysis Page:** Detailed EPA methodology, results, and visualizations
- **PurpleAir Analysis Page:** Detailed PurpleAir methodology, results, and visualizations

### Enabling GitHub Pages

**Important:** This repository uses GitHub Actions to build and deploy the site. Follow these steps:

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **"GitHub Actions"** (NOT "Deploy from a branch")
4. The workflow will automatically run when you push to the `master` or `main` branch
5. You can also manually trigger it from the **Actions** tab → **Deploy Jekyll with GitHub Pages dependencies preinstalled** → **Run workflow**

**Note:** If you see "There isn't a GitHub Pages site here", make sure:
- The source is set to **"GitHub Actions"** (not a branch)
- The workflow has run successfully (check the Actions tab)
- The workflow completed without errors

Your site will be available at: `https://Loadingname91.github.io/AirQualityVsAgeDemographics/`

##  Technical Specifications

### Python Libraries
- `geopandas` - Geospatial data manipulation
- `pandas` - Data analysis
- `matplotlib` - Static visualization
- `folium` - Interactive web maps
- `scipy` - Spatial interpolation
- `contextily` - Basemap tiles
- `requests` - API data access

### Coordinate Systems
- **Target CRS:** Web Mercator (EPSG:3857)
- **Source CRS:** WGS84 (EPSG:4326)

### Data Processing
- **EPA:** Daily 24-hour averages aggregated by monitoring station
- **PurpleAir:** 60-minute averages with spatial interpolation (IDW)
- **Census:** Tract-level aggregation of population 80+

##  Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

##  License

This project is open source and available for educational and research purposes.

##  Acknowledgments

- **Data Sources:**
  - US Census Bureau (demographic data)
  - EPA AQS API (regulatory air quality data)
  - PurpleAir Community Network (sensor data)
  - University of Utah (correction formula methodology)

- **Technical Support:**
  - Synoptic Data API documentation
  - GeoPandas and Folium communities

##  Contact

For questions or inquiries, please open an issue in the repository.

---

**Note:** This is a proof-of-concept project. EPA and PurpleAir analyses are from different time periods (2025 vs 2026) and are presented as independent demonstrations of technical capability.

