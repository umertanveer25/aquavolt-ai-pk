import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timezone

def force_dashboard():
    print("Fetching latest hour data from Google Sheet...")
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = r"c:\Users\umert\aquavolt-ai-pk\service_account.json"
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open("AquaVolt-AI Telemetry Log").sheet1
    
    # Get last 256 rows
    all_data = sheet.get_all_values()
    if len(all_data) < 257:
        print("Not enough data.")
        return
        
    latest_rows = all_data[-256:]
    now_str = latest_rows[0][0] # Timestamp
    
    temp = latest_rows[0][20]
    humidity = latest_rows[0][21]
    solar_rad = latest_rows[0][22]
    soil_moist = float(latest_rows[0][25]) * 100
    daily_et0 = sum([float(r[18]) for r in latest_rows]) / 256 * 24 # rough approx or just hide
    
    field_summaries = {}
    for row in latest_rows:
        fname = row[28]
        if fname not in field_summaries:
            field_summaries[fname] = {"ndvi": [], "ndwi": [], "etc": [], "irr": []}
        field_summaries[fname]["ndvi"].append(float(row[5]))
        field_summaries[fname]["ndwi"].append(float(row[7]))
        field_summaries[fname]["etc"].append(float(row[18]))
        field_summaries[fname]["irr"].append(float(row[19]))
        
    md_content = f"# 📡 AquaVolt-AI Live Telemetry\n\n"
    md_content += f"**Latest Update:** `{now_str}`\n"
    md_content += f"> This dashboard updates automatically every hour via GitHub Actions.\n\n"
    
    md_content += f"### ⛅ Current Weather (Russell Ranch)\n\n"
    md_content += f"- **Air Temp:** {temp}°C\n"
    md_content += f"- **Humidity:** {humidity}%\n"
    md_content += f"- **Solar Radiation:** {solar_rad} W/m²\n"
    md_content += f"- **Soil Moisture (Proxy):** {soil_moist:.1f}%\n\n"
    
    md_content += f"### 🌱 Field Averages (Current Hour)\n\n"
    md_content += f"| Field Name | Avg NDVI | Avg NDWI | Avg ETc (mm/hr) | Avg Water Deficit (mm) |\n"
    md_content += f"|---|---|---|---|---|\n"
    
    for fname, data in field_summaries.items():
        avg_ndvi = sum(data["ndvi"]) / len(data["ndvi"])
        avg_ndwi = sum(data["ndwi"]) / len(data["ndwi"])
        avg_etc = sum(data["etc"]) / len(data["etc"])
        avg_irr = sum(data["irr"]) / len(data["irr"])
        md_content += f"| **{fname}** | {avg_ndvi:.3f} | {avg_ndwi:.3f} | {avg_etc:.2f} | **{avg_irr:.2f}** |\n"
        
    md_content += f"\n---\n*Powered by Python, Planetary Computer STAC APIs, and FAO-56 Thermodynamics.*\n"
    
    # Inject into README.md
    readme_path = r"c:\Users\umert\aquavolt-ai-pk\README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()
        
        import re
        pattern = r"(<!-- LIVE_TELEMETRY_START -->)(.*?)(<!-- LIVE_TELEMETRY_END -->)"
        replacement = r"\1\n" + md_content + r"\n\3"
        new_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("Generated README.md dashboard!")
    else:
        print("README.md not found.")

if __name__ == "__main__":
    force_dashboard()
