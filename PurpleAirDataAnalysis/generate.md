**Role:** You are an expert Python Data Scientist specializing in Geospatial Analysis (GIS). Your goal is to build a complete pipeline that visualizes the intersection of **Age Demographics (80+)** and **Air Quality (PM2.5)** in Salt Lake City.

**Project Context:**
I have a dataset of Salt Lake City census tracts and a folder of raw air quality sensor logs. I need a Python script to:

1. Map the density of the 80+ year old population.
2. Create a continuous "Heatmap" surface of PM2.5 pollution from discrete sensor points.
3. Overlay these two layers to visualize environmental inequity.

**1. File Structure & Inputs**
Assume the following directory structure. You must write code that correctly loads these paths all contained in the `Data` folder.

* `tl_2025_49_tract.shp`: The shapefile for Utah Census Tracts.
* `ACSDT5Y2023.B01001-Data.csv`: The US Census demographic data (Sex by Age).
* `master_sensor_list.csv`: A lookup table containing columns `sensor_index`, `latitude`, `longitude`.
* `/purpleair_data/`: A folder containing ~280 CSV files.
* *Content:* Columns `pm2.5_cf_1` and `pm2.5_atm`.



**2. Step-by-Step Implementation Requirements**

**Step A: Geographic Boundaries (Shapefile)**

* Load the shapefile using `geopandas`.
* **Filter:** Keep only Census Tracts in **Salt Lake County (FIPS 035)** and **Davis County (FIPS 011)**.
* *Hint:* The `GEOID` column starts with `49035` or `49011`.


* **Reprojection:** Convert the CRS to Web Mercator (`EPSG:3857`) for accurate plotting.

**Step B: Demographic Data (Census Cleaning)**

* Load the ACS CSV. Note that row 2 usually contains descriptive headers; handle this.
* **Feature Engineering:** Create a new column `pop_80_plus` by summing:
* Male: 80-84 years + 85 years and over
* Female: 80-84 years + 85 years and over


* **Join Key Fix:** The ACS `GEO_ID` column often has a prefix (e.g., `1400000US49035...`). Strip `1400000US` so it matches the Shapefile `GEOID`.
* **Merge:** Inner join the Shapefile and Census Data.

**Step C: Air Quality Processing (The Complex Part)**

* Iterate through every CSV file in `/purpleair_data/`.
* **ID Extraction:** Parse the filename to extract the integer `SENSOR_ID`.
* **Lookup Location:** Use the `SENSOR_ID` to find the corresponding `latitude` and `longitude` from `master_sensor_list.csv`. Skip the file if the ID is missing from the master list.
* **Data Aggregation:**
* Calculate the mean of `pm2.5_cf_1` for that file.
* **Apply Correction:** Use the "University of Utah Winter Inversion" formula: `Corrected PM2.5 = (0.778 * Raw_CF1) + 2.65`.


* **Result:** Create a DataFrame `air_df` with columns: `lat`, `lon`, `pm25`.

**Step D: Geospatial Interpolation (The Heatmap)**

* Convert `air_df` to a GeoDataFrame and reproject to `EPSG:3857` (matching the map).
* Use `scipy.interpolate.griddata` (linear or cubic) to create a continuous mesh/grid of PM2.5 values across the bounds of the map.
* *Constraint:* Ensure the grid resolution is high enough (e.g., 100x100 or 200x200) to look smooth.

**Step E: Visualization (Matplotlib)**

* Create a figure with `contextily` basemap (e.g., `CartoDB.Positron`).
* **Layer 1:** Plot the Interpolated PM2.5 Heatmap using `imshow`. Use a color map like `OrRd` or `plasma`. Set `alpha=0.6` so the map features show through.
* **Layer 2:** Plot the Census Tract boundaries (just the borders, `facecolor='none', edgecolor='black'`) on top of the heatmap.
* Add a colorbar labeled "PM2.5 (µg/m³)".
* Save the final plot as `final_analysis_map.png`.

**3. Code Constraints**

* Use `pandas`, `geopandas`, `matplotlib`, `scipy`, and `contextily`.
* Include error handling (try/except) in the file loop so one bad CSV doesn't crash the script.
* Print status updates (e.g., "Processed 50/279 sensors...") so I know it's working.

**Generate the complete `main.py` script.**