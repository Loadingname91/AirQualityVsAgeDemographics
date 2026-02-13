Context: I need to download official PM2.5 data from the EPA AQS API for Salt Lake County (State 49, County 035) to verify the data density against my PurpleAir dataset.

Task: Write a robust Python script (get_epa_data.py) that interacts with the https://aqs.epa.gov/data/api endpoints.

Refer : 
https://aqs.epa.gov/aqsweb/documents/data_api.htm for the API documentation.

Functional Requirements:

User Authentication (The "Key" Check):

The script should check if the user already has an EPA_EMAIL and EPA_KEY stored in a .env file or variable.
use - hiteshbalegar@gmail.com as the email address.
 - key - tealheron54

If NOT: It should prompt the user for their email address, run the "Sign Up" endpoint (/signup?email=...), and tell them to check their inbox for the key before proceeding.

Data Download (The "Fetch"):

Once authorized, fetch Daily Summary Data (/dailyData/byCounty).

Parameters:

email / key: User's credentials.

param: 88101 (PM2.5 FRM/FEM Mass).

bdate: 20260101 (Start Date: Jan 1, 2026).

edate: 20260125 (End Date: Jan 25, 2026).

state: 49 (Utah).

county: 035 (Salt Lake County).

Output:

Convert the JSON response into a Pandas DataFrame.

Filter for useful columns: site_number, local_site_name, latitude, longitude, date_local, arithmetic_mean (the PM2.5 value).

Save to epa_slc_data.csv.

Print the count of unique monitoring sites found in the file 