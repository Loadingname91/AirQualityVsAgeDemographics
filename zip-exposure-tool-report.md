# ZIP Code PM2.5 Exposure Tool: Technical Report

## 1. Overview

The ZIP Code PM2.5 Exposure Tool estimates ambient PM2.5 (particulate matter ≤2.5 µm) exposure at ZIP code locations using Inverse Distance Weighting (IDW) interpolation. Users enter one or more 5-digit ZIP codes, select a data source (PurpleAir or EPA AQS), optionally set a buffer radius, and receive interpolated PM2.5 estimates along with the contributing sensors or stations shown on a map.

## 2. Data Sources

| Source | Period | Coverage |
|--------|--------|----------|
| **PurpleAir** | Jan 1–25, 2026 | ~254 community sensors (corrected for Utah winter conditions) |
| **EPA AQS** | Jan 1–30, 2025 | 10 regulatory monitoring stations in Salt Lake & Davis counties |

Each source provides pre-aggregated mean PM2.5 values per sensor/station. The tool loads CSV files and does not query APIs directly.

## 3. ZIP Centroid Lookup

ZIP code centroids are stored in `ut_zip_centroids.csv` (lat/lon for each ZIP). When a user enters a ZIP, the tool looks up its centroid coordinates and uses that point as the location for exposure estimation.

**Example:** ZIP 84102 → centroid (40.7700, -111.8700), approximately downtown Salt Lake City.

## 4. Point Estimate (IDW at Centroid)

The PM2.5 value **at** the centroid is computed with IDW interpolation over all sensors/stations in the selected dataset.

### Formula

For a point \((lat, lon)\), the IDW estimate is:

\[
\text{PM2.5}_{IDW} = \frac{\sum_i w_i \cdot \text{PM2.5}_i}{\sum_i w_i}
\]

where the weight for each sensor \(i\) is:

\[
w_i = \frac{1}{d_i^p}
\]

- \(d_i\) = distance from the point to sensor \(i\) (meters), with a minimum of 10 m to avoid division issues  
- \(p\) = IDW power (default: 2)

Closer sensors contribute more; distant sensors contribute less. All sensors in the dataset are used, regardless of distance.

## 5. Buffer Mean

When a buffer radius is selected (e.g., 250 m, 500 m, 1 km), the tool computes a **buffer mean** as the average of IDW estimates at **9 sample points**:

1. **Center:** The ZIP centroid  
2. **Ring:** 8 points evenly spaced on a circle at the buffer radius around the centroid  

These 9 points are sampled, IDW is run at each, and the mean of the 9 values is the buffer mean.

**Important:** No sensors need to be *inside* the buffer. IDW estimates PM2.5 at each sample point by interpolating from *all* available sensors, so results are produced even when the nearest sensor is kilometers away (e.g., with sparse EPA coverage).

## 6. Contributing Sensors

The tool identifies the **top 15 sensors** that contribute most to the centroid’s IDW estimate (by weight \(w_i\)). These are shown on the map as smaller markers, color-coded by their reported PM2.5 value. Hover and click reveal sensor ID, PM2.5, and distance to the centroid.

## 7. Color Coding

All markers (centroids and sensors) use the same PM2.5 color scale:

| Color | PM2.5 Range (µg/m³) | AQI Category |
|-------|---------------------|--------------|
| Green | < 12 | Good |
| Orange | 12–35 | Moderate |
| Red | ≥ 35 | Unhealthy |

## 8. Example: ZIP 84102 with 1 km Buffer (PurpleAir)

**Inputs:**
- ZIP code: 84102
- Data source: PurpleAir (Jan 1–25, 2026)
- Buffer radius: 1 km

**Steps:**

1. **Centroid lookup:** 84102 → (40.7700, -111.8700), downtown Salt Lake City.

2. **Point estimate:** IDW at (40.77, -111.87) over all 254 PurpleAir sensors.  
   - Nearby sensors (e.g., within 2–5 km) receive high weights.  
   - Result: PM2.5 at point ≈ 6.55 µg/m³ (hypothetical; actual values depend on the loaded data).

3. **Buffer mean:**  
   - Sample points: center + 8 on a 1 km ring.  
   - IDW at each of the 9 points.  
   - Buffer mean = average of those 9 values ≈ 6.54 µg/m³.

4. **Contributing sensors:**  
   - Top 15 sensors by weight, e.g., at distances from ~0.5 km to ~5 km.  
   - Each shown as a small marker with its own PM2.5 color.

5. **Map display:**  
   - Large marker: centroid estimate (green/orange/red).  
   - Light circle: 1 km buffer.  
   - Small markers: contributing sensors (optional, toggle “Show contributing sensors”).

**Output table:**

| ZIP  | Lat   | Lon     | PM2.5 (µg/m³) at point | PM2.5 (µg/m³) buffer mean |
|------|-------|---------|-------------------------|----------------------------|
| 84102| 40.77 | -111.87 | 6.55                    | 6.54                       |

## 9. EPA vs PurpleAir: Behavior

- **PurpleAir (254 sensors):** High spatial density; IDW estimates reflect local variation; contributing sensors are usually within a few km.
- **EPA (10 stations):** Sparse network; IDW uses all 10 stations; estimates can be similar across nearby ZIPs because they share the same few stations; contributing sensors may be 5–15 km away.

The buffer mean and point estimate are computed the same way for both sources; only the underlying sensor set changes.

## 10. Implementation Notes

- **IDW power:** 2  
- **Buffer samples:** 9 (1 center + 8 on ring)  
- **Contributing sensors shown:** 15  
- **Minimum distance in IDW:** 10 m  

All calculations run client-side in JavaScript after loading the CSV data.
