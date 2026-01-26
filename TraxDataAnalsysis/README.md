# TRAX Mobile Sensor Data Analysis

## Current Status

The script `sensorDataFinder.py` is set up to fetch TRAX mobile PM2.5 data from the Synoptic Data API, but we're encountering access issues.

## Issue

The API returns: "No stations found for this request, or your account does not have access to the requested station(s)."

## Possible Solutions

1. **Verify Station IDs**: The current station IDs are:
   - `TRX01` (Red Line)
   - `TRX02` (Green Line)`
   
   These may need to be verified with Synoptic Data support.

2. **Check API Token Access**: Your token may need special permissions for TRAX mobile data. Contact:
   - Email: support@synopticdata.com
   - Website: https://developers.synopticdata.com/

3. **Alternative Station IDs**: TRAX stations might use different naming conventions such as:
   - `UTAH_TRX01`, `UTAH_TRX02`
   - `SLC_TRX01`, `SLC_TRX02`
   - Network-specific IDs

4. **Check Network**: TRAX data might be under a specific network that needs to be specified.

## Next Steps

1. Contact Synoptic Data support to:
   - Verify TRAX station IDs
   - Request access to mobile sensor data
   - Get the correct variable names for PM2.5

2. Once you have the correct station IDs, update `sensorDataFinder.py`:
   ```python
   STATION_IDS = 'CORRECT_ID_1,CORRECT_ID_2'
   ```

3. The script will automatically:
   - Check available variables
   - Try multiple PM2.5 variable names
   - Fetch and save data to `trax_mobile_data.csv`

## Script Features

- ✅ Automatic variable detection
- ✅ Multiple PM2.5 variable name attempts
- ✅ GPS coordinate extraction (mobile data)
- ✅ CSV export with lat/lon/pm25 columns
- ✅ Date range filtering (currently set to Jan 14-17, 2025)

## Configuration

Edit `sensorDataFinder.py` to update:
- `API_TOKEN`: Your Synoptic API token
- `START_TIME`: Start date (format: YYYYMMDDHHMM)
- `END_TIME`: End date (format: YYYYMMDDHHMM)
- `STATION_IDS`: Comma-separated station IDs

