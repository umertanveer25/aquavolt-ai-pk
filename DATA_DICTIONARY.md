# AquaVolt Serverless Digital Twin - Data Dictionary

This repository captures extensive hyper-local telemetry data in the `data/` directory (e.g. `telemetry_log_YYYY_MM.csv`). This data dictionary defines the structure and physical units of each column to ensure perfect reproducibility for future research.

| Column Name | Type | Unit / Range | Description |
|---|---|---|---|
| `Timestamp` | Datetime | ISO 8601 (UTC) | The exact time of the hourly reading. |
| `FieldID` | String | F1, F2, F3, F4 | The unique identifier for the crop field. |
| `SectorID` | String | S01-S64 | The 8x8 sub-sector grid identifier within a field. |
| `CropType` | String | categorical | The type of crop planted (e.g., Alfalfa, Tomatoes). |
| `Temperature_C` | Float | °C | Air temperature at 2m above ground. |
| `Humidity_%` | Float | 0 - 100% | Relative humidity. |
| `WindSpeed_m_s` | Float | m/s | Wind speed measured at 10m height. |
| `SolarRad_W_m2` | Float | W/m² | Downward shortwave solar radiation flux. |
| `NDVI` | Float | -1.0 to 1.0 | Normalized Difference Vegetation Index (from satellite/drone). |
| `NDWI` | Float | -1.0 to 1.0 | Normalized Difference Water Index. |
| `SAVI` | Float | -1.0 to 1.0 | Soil Adjusted Vegetation Index. |
| `SoilMoisture_%` | Float | 0 - 100% | Volumetric water content in the root zone. |
| `ET0_mm` | Float | mm/day | Reference Evapotranspiration calculated via FAO-56 Penman-Monteith. |
| `Kc` | Float | 0.15 - 1.20 | Crop Coefficient, updated dynamically via PIML model. |
| `ETc_mm` | Float | mm/day | Actual Crop Evapotranspiration (`ET0 * Kc * Ks`). |
| `WaterDeficit_mm` | Float | mm | Net water deficit calculation (ETc - effective precipitation). |
| `WaterApplied_mm` | Float | mm | Irrigation applied during this hourly window. |

## Notes on ML Integration
The `Kc` value in historical logs was calculated using the PIML (Physics-Informed Machine Learning) module, mapping satellite NDVI directly to crop coefficients without the need for manual lookups.
