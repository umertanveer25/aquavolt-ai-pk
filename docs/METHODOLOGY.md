# Scientific Methodology — AquaVolt-AI

This document describes the mathematical equations, scientific standards, and machine learning models integrated into the AquaVolt-AI precision agricultural water management pipeline.

---

## 1. Reference Evapotranspiration ($ET_0$) — FAO-56 Penman-Monteith

The reference crop evapotranspiration ($ET_0$) is computed using the globally standardized FAO-56 Penman-Monteith equation (Allen et al., 1998):

$$ET_0 = \frac{0.408 \Delta (R_n - G) + \gamma \frac{900}{T + 273} u_2 (e_s - e_a)}{\Delta + \gamma (1 + 0.34 u_2)}$$

### Parameter Definitions & Units:
- $ET_0$: Reference evapotranspiration [$\text{mm/day}$]
- $R_n$: Net radiation at the crop surface [$\text{MJ/m}^2\text{/day}$]
- $G$: Soil heat flux density [$\text{MJ/m}^2\text{/day}$] (assumed negligible for daily calculation intervals, i.e., $G \approx 0$)
- $T$: Mean daily air temperature at 2m height [$^\circ\text{C}$]
- $u_2$: Wind speed at 2m height [$\text{m/s}$]
- $e_s$: Saturation vapour pressure [$\text{kPa}$]
- $e_a$: Actual vapour pressure [$\text{kPa}$]
- $e_s - e_a$: Vapour pressure deficit (VPD) [$\text{kPa}$]
- $\Delta$: Slope of the saturation vapour pressure-temperature curve [$\text{kPa/}^\circ\text{C}$]
- $\gamma$: Psychrometric constant [$\text{kPa/}^\circ\text{C}$] ($\approx 0.0674\text{ kPa/}^\circ\text{C}$ at sea level)

### Data Ingestion:
Meteorological variables are fetched hourly from the **Open-Meteo API** (using point coordinates corresponding to the center of UC Davis Russell Ranch).

---

## 2. Physics-Informed Machine Learning (PIML) — Crop Coefficient Estimation

AquaVolt-AI avoids pure black-box machine learning by grounding its neural network inside a physical prior framework. A multi-layer perceptron (MLP) architecture (with a 4 $\rightarrow$ 16 $\rightarrow$ 8 $\rightarrow$ 2 structure) predicts the crop coefficient ($K_c$) and water-stress factor ($K_s$).

### Input Feature Matrix:
$$\mathbf{X} = [\text{NDVI}, \text{NDWI}, \text{SAVI}, \text{LST}]$$

### 1. Crop Coefficient ($K_c$) Prior (FAO-56 Curve Fit):
The physical prior for $K_c$ is modeled using a sigmoid function fitted to the standard FAO-56 agricultural development stages:

$$K_{c,\text{prior}} = 0.15 + \frac{0.95}{1 + e^{-12(\text{NDVI} - 0.4)}}$$

### 2. Water Stress ($K_s$) Prior:
The prior for water-stress response is defined dynamically using the Normalized Difference Water Index (NDWI):

$$K_{s,\text{prior}} = \begin{cases} 
1.0 & \text{if } \text{NDWI} \ge -0.1 \\
\max(0.0, 1.0 + (\text{NDWI} + 0.1) \times 2.0) & \text{if } \text{NDWI} < -0.1 
\end{cases}$$

### 3. Neural Network Residual Correction:
The network outputs residual corrections $r_1$ and $r_2$, bounded strictly to $\pm15\%$ of the theoretical physical scale, preventing physically impossible outputs:

$$K_c = \text{clip}\left(K_{c,\text{prior}} + \text{clip}(r_1 \times 0.15, -0.15, 0.15), 0.15, 1.20\right)$$
$$K_s = \text{clip}\left(K_{s,\text{prior}} + \text{clip}(r_2 \times 0.15, -0.15, 0.15), 0.0, 1.0\right)$$

---

## 3. FAO-56 Root-Zone Soil Water Balance

To determine the final net irrigation scheduling recommendation, the model computes the daily root-zone soil water depletion ($D_r$) for a **sandy loam** soil profile.

### Physical Constants:
- **Root Zone Depth ($Z_r$):** $0.6\text{ m}$
- **Field Capacity ($\theta_{\text{fc}}$):** $0.22\text{ m}^3\text{/m}^3$
- **Wilting Point ($\theta_{\text{wp}}$):** $0.10\text{ m}^3\text{/m}^3$
- **Depletion Fraction ($p$):** $0.5$
- **Total Available Water ($TAW$):** $72.0\text{ mm}$ (derived via $1000 (\theta_{\text{fc}} - \theta_{\text{wp}}) Z_r$)
- **Readily Available Water ($RAW$):** $36.0\text{ mm}$ (derived via $p \times TAW$)

### Depletion Calculation:
$$ET_c = K_s \cdot K_c \cdot ET_0 \qquad \text{[Crop Evapotranspiration under Stress]}$$
$$P_{\text{eff}} = 0.8 \cdot P \qquad \text{[Effective Precipitation (80\% efficiency)]}$$
$$D_r(t) = D_r(t-1) - P_{\text{eff}} + ET_c$$

### Irrigation Recommendation:
$$\text{Water Need} = \begin{cases}
D_r & \text{if } D_r > RAW \\
0.0 & \text{if } D_r \le RAW
\end{cases}$$

---

## 4. Astronomical Solar & Growth Model

To simulate dynamic crop growth curves during periods without real-time satellite updates, the system utilizes an astronomical model based on latitude and Julian calendar date:

### 1. Solar Declination ($\delta$):
$$\delta = 0.409 \sin\left(\frac{2\pi}{365} J - 1.39\right)$$
*Where $J$ is the Julian day number [1–365].*

### 2. Sunset Hour Angle ($\omega_s$):
$$\omega_s = \arccos\left(-\tan(\phi) \tan(\delta)\right)$$
*Where $\phi$ is the latitude in radians.*

### 3. Day Length ($DL$):
$$DL = \frac{24}{\pi} \omega_s$$

### 4. Season & Thermal Growth Multipliers:
$$\text{season\_factor} = \text{clip}\left(\frac{DL - 8}{8}, 0.0, 1.0\right)$$
$$\text{temp\_factor} = e^{-0.02 (T - 24)^2}$$
$$\text{growth\_multiplier} = \text{season\_factor} \times \text{temp\_factor}$$

---

## 5. Telemetry Schema — `telemetry_log` (29 Columns)

The processed dataset contains 29 columns per sector record:

| Column | Type | Unit | Description |
|---|---|---|---|
| `timestamp` | TEXT | ISO 8601 | Datetime stamp of the telemetry record [UTC] |
| `latitude` | REAL | Decimal degrees | Sector centroid latitude |
| `longitude` | REAL | Decimal degrees | Sector centroid longitude |
| `sector_row` | INTEGER | Index | Grid row index [0–7] |
| `sector_col` | INTEGER | Index | Grid column index [0–7] |
| `ndvi` | REAL | Ratio | Sentinel-2 NDVI spectral value [0.0 - 1.0] |
| `ndwi` | REAL | Ratio | Simulated astronomical NDWI value |
| `ndwi_real` | REAL | Ratio | Real-time NDWI computed directly from Sentinel-2 bands |
| `savi` | REAL | Ratio | Soil-Adjusted Vegetation Index |
| `lai` | REAL | $m^2/m^2$ | Leaf Area Index calculated from crop coefficient |
| `fcover` | REAL | Ratio | Fraction of Vegetation Cover [0.0 - 1.0] |
| `lst` | REAL | $^\circ\text{C}$ | Soil-temperature derived canopy temperature proxy |
| `lst_modis` | REAL | $^\circ\text{C}$ | Land Surface Temperature from MODIS (Planetary Computer) |
| `Kc` | REAL | Ratio | Physics-Informed ML Crop Coefficient |
| `Ks` | REAL | Ratio | Soil moisture stress coefficient [0.0 - 1.0] |
| `Dr` | REAL | mm | Root-zone soil water depletion |
| `TAW` | REAL | mm | Total Available Water capacity of root profile |
| `RAW` | REAL | mm | Readily Available Water threshold |
| `ETc` | REAL | mm/day | Crop evapotranspiration under stress |
| `water_need` | REAL | mm/day | Suggested net irrigation depth |
| `air_temp` | REAL | $^\circ\text{C}$ | Air temperature |
| `humidity` | REAL | % | Relative humidity |
| `solar_rad` | REAL | $W/m^2$ | Shortwave solar radiation |
| `precip` | REAL | mm | Hourly precipitation |
| `soil_temp` | REAL | $^\circ\text{C}$ | Soil temperature at 0–7cm |
| `soil_moisture` | REAL | $m^3/m^3$ | Soil moisture content at 0–1cm |
| `et0_deficit_7d` | REAL | mm | Cumulative reference evapotranspiration deficit |
| `scene_id` | TEXT | String | Sentinel-2 source scene ID |
| `field_name` | TEXT | String | Crop crop label (Field-A, Field-B, etc.) |
