import requests
import json

def test_awdb_rest():
    url = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stationElements?stationTriplets=2001:NE:SCAN"
    try:
        res = requests.get(url)
        print(res.status_code)
        print(res.text[:2000].encode('ascii', errors='ignore').decode('ascii'))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_awdb_rest()
