# Scientific Methodology — AquaVolt-AI

## 1. Reference Evapotranspiration (ET₀) — FAO-56 Penman-Monteith

The reference evapotranspiration is computed using the standard FAO-56 Penman-Monteith equation:

`
ET₀ = [0.408 · Δ · Rn + γ · (900 / (T + 273)) · u₂ · (eₛ - eₐ)] / [Δ + γ · (1 + 0.34 · u₂)]
`

Where:
- Δ = slope of saturation vapour pressure curve (kPa/°C)
- Rn = net radiation at crop surface (MJ/m²/day)
- γ = psychrometric constant (≈ 0.0674 kPa/°C at sea level)
- T = mean daily air temperature (°C)
- u₂ = wind speed at 2m height (m/s)
- eₛ = saturation vapour pressure (kPa)
- eₐ = actual vapour pressure (kPa)

**Data Source:** Open-Meteo API (updated every 15 minutes)

---

## 2. Physics-Informed Neural Network — Kc/Ks Estimator

A 3-layer MLP (4→16→8→2) estimates the crop coefficient (Kc) and water-stress factor (Ks) 
using spectral indices as inputs:

**Input features:** [NDVI, NDWI, SAVI, LST]

**Physics priors (FAO-56):**
`
Kc_prior = 0.15 + 0.95 / (1 + exp(-12 · (NDVI - 0.4)))   [logistic NDVI curve]
Ks_prior = 1.0                           if NDWI ≥ -0.1
         = max(0, 1 + (NDWI + 0.1) · 2)  otherwise
`

**Residual learning:** Neural output is bounded to ±15% correction on top of the physical prior:
`
Kc = clip(Kc_prior + clip(residual[0] × 0.15, -0.15, +0.15), 0.15, 1.20)
Ks = clip(Ks_prior + clip(residual[1] × 0.15, -0.15, +0.15), 0.0,  1.0)
`

---

## 3. FAO-56 Root-Zone Soil Water Balance

**Soil parameters (Sandy Loam):**
| Parameter | Symbol | Value |
|---|---|---|
| Field Capacity | θ_fc | 0.22 m³/m³ |
| Wilting Point | θ_wp | 0.10 m³/m³ |
| Root Zone Depth | Zr | 0.6 m |
| Depletion Fraction | p | 0.5 |
| Total Available Water | TAW | 72 mm |
| Readily Available Water | RAW | 36 mm |

**Daily water balance:**
`
ETc = Ks · Kc · ET₀            [crop evapotranspiration under stress]
Peff = 0.8 · P                  [effective precipitation (80% efficiency)]
Dr(t) = Dr(t-1) - Peff + ETc   [depletion update]
Irrigation = Dr  if Dr > RAW else 0
`

---

## 4. Dynamic Crop Growth Model

NDVI baseline is dynamically computed using astronomical solar physics and temperature response:

**Step 1 — Solar Declination (FAO-56 Eq. 24):**
`
δ = 0.409 · sin(2π/365 · J - 1.39)
`

**Step 2 — Sunset Hour Angle:**
`
ωs = arccos(-tan(φ) · tan(δ))
`

**Step 3 — Day Length:**
`
DL = (24/π) · ωs
`

**Step 4 — Season Factor:**
`
season_factor = clip((DL - 8) / 8, 0, 1)
`

**Step 5 — Temperature Growth Response:**
`
temp_factor = exp(-0.02 · (T - 24)²)
`

**Step 6 — Dynamic NDVI range:**
`
growth_multiplier = season_factor × temp_factor
NDVI_max = 0.35 + 0.50 · growth_multiplier
NDVI_min = 0.15 + 0.15 · growth_multiplier
`

This formula automatically handles Northern/Southern Hemisphere seasonal inversion and 
responds dynamically to real-time temperature anomalies.

---

## 5. Data Sources (All Open-Access, No API Keys Required)

| Source | Variable | Resolution | Update Frequency |
|---|---|---|---|
| Open-Meteo API | T, RH, wind, solar, soil temp/moisture, ET₀ | Point | 15 min |
| NASA GIBS WMTS | MODIS Terra NDVI | 250m | 8-day composite |
| NASA POWER | Historical solar radiation, temperature, precipitation | 0.5° | Daily |

---

## 6. Data Schema — telemetry_log

| Column | Type | Description |
|---|---|---|
| timestamp | TEXT | ISO 8601 datetime of record |
| latitude | REAL | Farm latitude (°N) |
| longitude | REAL | Farm longitude (°E) |
| sector_row | INTEGER | Grid row (0–7) |
| sector_col | INTEGER | Grid column (0–7) |
| ndvi | REAL | Normalized Difference Vegetation Index |
| ndwi | REAL | Normalized Difference Water Index proxy |
| savi | REAL | Soil-Adjusted Vegetation Index proxy |
| lst | REAL | Land Surface Temperature proxy (°C) |
| Kc | REAL | Dynamic crop coefficient (PIML neural estimate) |
| Ks | REAL | Water-stress factor (0–1) |
| Dr | REAL | Root-zone soil water depletion (mm) |
| TAW | REAL | Total Available Water (mm) |
| RAW | REAL | Readily Available Water threshold (mm) |
| ETc | REAL | Crop evapotranspiration under stress (mm/day) |
| water_need | REAL | Net irrigation recommendation (mm/day) |
| air_temp | REAL | Air temperature (°C) |
| humidity | REAL | Relative humidity (%) |
| solar_rad | REAL | Shortwave solar radiation (W/m²) |
| precip | REAL | Current precipitation (mm) |
| soil_temp | REAL | Soil temperature 0–7cm (°C) |
| soil_moisture | REAL | Volumetric soil water content (m³/m³) |
