#!/usr/bin/env python3
"""
EPA AQS API Data Fetcher for PM2.5 Data
Fetches daily PM2.5 data for Salt Lake County, Utah from the EPA AQS API.
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

# EPA AQS API Base URL
BASE_URL = "https://aqs.epa.gov/data/api"

# Default credentials (can be overridden by .env)
DEFAULT_EMAIL = "x"
DEFAULT_KEY = "x"

# Query parameters
STATE_CODE = "49"        # Utah
COUNTY_CODES = ["035", "011"]  # Salt Lake County, Davis County
PARAM_CODE = "88101"     # PM2.5 FRM/FEM Mass
BEGIN_DATE = "20250101"  # Jan 1, 2025
END_DATE = "20251231"    # Dec 31, 2025

# County name mapping
COUNTY_NAMES = {
    "035": "Salt Lake County",
    "011": "Davis County"
}


def load_credentials():
    """
    Load EPA credentials from .env file or use defaults.
    Returns tuple of (email, key).
    """
    load_dotenv()
    
    email = os.getenv("EPA_EMAIL", DEFAULT_EMAIL)
    key = os.getenv("EPA_KEY", DEFAULT_KEY)
    
    return email, key


def signup_for_api(email):
    """
    Sign up for EPA AQS API key.
    Sends request to signup endpoint.
    """
    signup_url = f"{BASE_URL}/signup?email={email}"
    
    print(f"Signing up for EPA AQS API with email: {email}")
    response = requests.get(signup_url)
    
    if response.status_code == 200:
        result = response.json()
        print("Signup request sent!")
        print("Please check your email inbox for the API key.")
        print(f"Response: {result}")
        return True
    else:
        print(f"Signup failed with status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def verify_credentials(email, key):
    """
    Verify that credentials are valid by making a test API call.
    Returns True if valid, False otherwise.
    """
    # Use a simple list endpoint to verify credentials
    test_url = f"{BASE_URL}/list/states?email={email}&key={key}"
    
    try:
        response = requests.get(test_url)
        if response.status_code == 200:
            data = response.json()
            # Check if the response indicates success
            if data.get("Header", [{}])[0].get("status") == "Success":
                return True
        return False
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return False


def fetch_pm25_data(email, key):
    """
    Fetch daily PM2.5 data from EPA AQS API for multiple counties.
    Returns combined data from all counties.
    """
    endpoint = f"{BASE_URL}/dailyData/byCounty"
    all_data = []
    
    print(f"\nFetching PM2.5 data from EPA AQS API...")
    print(f"  State: {STATE_CODE} (Utah)")
    counties_str = ', '.join([f"{c} ({COUNTY_NAMES.get(c, 'Unknown')})" for c in COUNTY_CODES])
    print(f"  Counties: {counties_str}")
    print(f"  Parameter: {PARAM_CODE} (PM2.5 FRM/FEM Mass)")
    print(f"  Date Range: {BEGIN_DATE} to {END_DATE}")
    
    for county_code in COUNTY_CODES:
        county_name = COUNTY_NAMES.get(county_code, "Unknown")
        print(f"\n  Fetching {county_name} ({county_code})...")
        
        params = {
            "email": email,
            "key": key,
            "param": PARAM_CODE,
            "bdate": BEGIN_DATE,
            "edate": END_DATE,
            "state": STATE_CODE,
            "county": county_code
        }
        
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            json_data = response.json()
            header = json_data.get("Header", [{}])[0]
            data = json_data.get("Data", [])
            
            print(f"    Status: {header.get('status', 'Unknown')}")
            print(f"    Records: {header.get('rows', 0)}")
            
            if data:
                # Add county name to each record for clarity
                for record in data:
                    record['county_name'] = county_name
                all_data.extend(data)
        else:
            print(f"    API request failed with status code: {response.status_code}")
    
    if all_data:
        return {"Data": all_data, "Header": [{"status": "Success", "rows": len(all_data)}]}
    return None


def process_and_save_data(json_data, output_file="epa_utah_data.csv"):
    """
    Process JSON response into DataFrame and save to CSV.
    Filters for useful columns.
    """
    # Check if we have data
    if not json_data:
        print("No data to process.")
        return None
    
    # Extract the data from the response
    header = json_data.get("Header", [{}])[0]
    data = json_data.get("Data", [])
    
    print(f"\nAPI Response Status: {header.get('status', 'Unknown')}")
    print(f"Records returned: {header.get('rows', 0)}")
    
    if not data:
        print("No data records found in the response.")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Define columns to keep
    columns_to_keep = [
        "county_name",
        "site_number",
        "local_site_name", 
        "latitude",
        "longitude",
        "date_local",
        "arithmetic_mean"
    ]
    
    # Filter for available columns (in case some are missing)
    available_columns = [col for col in columns_to_keep if col in df.columns]
    
    if not available_columns:
        print("Warning: None of the expected columns found in data.")
        print(f"Available columns: {list(df.columns)}")
        # Save all data anyway
        df.to_csv(output_file, index=False)
        return df
    
    df_filtered = df[available_columns].copy()
    
    # Rename arithmetic_mean to pm25_value for clarity (optional)
    if "arithmetic_mean" in df_filtered.columns:
        df_filtered = df_filtered.rename(columns={"arithmetic_mean": "pm25_value"})
    
    # Save to CSV
    df_filtered.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}")
    
    return df_filtered


def main():
    """Main execution function."""
    print("=" * 60)
    print("EPA AQS API - PM2.5 Data Fetcher")
    print("Salt Lake County, Utah")
    print("=" * 60)
    
    # Load credentials
    email, key = load_credentials()
    print(f"\nUsing credentials:")
    print(f"  Email: {email}")
    print(f"  Key: {'*' * len(key)}")  # Mask the key
    
    # Check if credentials exist
    if not email or not key:
        print("\nNo credentials found!")
        user_email = input("Enter your email address: ").strip()
        
        if signup_for_api(user_email):
            print("\nPlease add your credentials to a .env file:")
            print("  EPA_EMAIL=your_email@example.com")
            print("  EPA_KEY=your_api_key")
            print("\nThen run this script again.")
        return
    
    # Verify credentials
    print("\nVerifying credentials...")
    if verify_credentials(email, key):
        print("Credentials verified successfully!")
    else:
        print("Warning: Could not verify credentials. Attempting to fetch data anyway...")
    
    # Fetch data
    json_data = fetch_pm25_data(email, key)
    
    if json_data:
        # Process and save
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "epa_utah_data.csv")
        
        df = process_and_save_data(json_data, output_path)
        
        if df is not None and not df.empty:
            # Print summary statistics
            print("\n" + "=" * 60)
            print("DATA SUMMARY")
            print("=" * 60)
            
            # Count unique monitoring sites
            if "site_number" in df.columns:
                unique_sites = df["site_number"].nunique()
                print(f"\nUnique monitoring sites found: {unique_sites}")
                
                # List the sites grouped by county
                if "local_site_name" in df.columns and "county_name" in df.columns:
                    print("\nMonitoring Sites by County:")
                    sites = df[["county_name", "site_number", "local_site_name"]].drop_duplicates()
                    for county in sites["county_name"].unique():
                        county_sites = sites[sites["county_name"] == county]
                        print(f"\n  {county} ({len(county_sites)} sites):")
                        for _, row in county_sites.iterrows():
                            print(f"    - Site {row['site_number']}: {row['local_site_name']}")
            
            print(f"\nTotal records: {len(df)}")
            print(f"\nFirst few records:")
            print(df.head().to_string())
        else:
            print("\nNo data was retrieved or processed.")
    else:
        print("\nFailed to fetch data from EPA API.")


if __name__ == "__main__":
    main()

