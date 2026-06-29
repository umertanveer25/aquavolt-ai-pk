import requests
import pandas as pd
import io

def test_awdb_csv():
    # URL for station 2001:CA:SCAN (Adams Sanctuary, CA) for Soil Temp (STO) and Air Temp (TOBS)
    url = "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/2001:CA:SCAN%7Cid=%22%22%7Cname/2024-01-01,2024-01-05/TOBS::value,STO:-2:value"
    try:
        res = requests.get(url)
        print(res.text[:500])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_awdb_csv()
