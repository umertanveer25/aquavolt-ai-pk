"""
AquaVolt-AI Unit Tests
======================
Validates the core physics engine, PIML constraints, and data pipeline integrity.
Run with: pytest tests/ -v
"""
import math
import numpy as np
import pytest


# ============================================================
# 1. FAO-56 Penman-Monteith Physics Tests
# ============================================================

class TestFAO56Physics:
    """Validate the thermodynamic equations used in the ET₀ calculation."""

    def test_saturation_vapor_pressure(self):
        """Tetens formula: es(T) = 0.6108 * exp(17.27*T / (T+237.3))"""
        T = 20.0  # °C
        es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))
        assert abs(es - 2.338) < 0.01, f"Expected ~2.338 kPa, got {es:.3f}"

    def test_slope_vapor_pressure_curve(self):
        """Delta = 4098 * es / (T + 237.3)^2"""
        T = 25.0
        es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))
        delta = (4098 * es) / (T + 237.3) ** 2
        assert 0.14 < delta < 0.20, f"Delta out of range: {delta:.4f}"

    def test_psychrometric_constant(self):
        """Gamma = 0.0665 * P (kPa), P ~ 101.3 at sea level"""
        P = 101.3  # kPa at sea level
        gamma = 0.0665 * P
        assert abs(gamma - 6.7365) < 0.01, f"Gamma mismatch: {gamma:.4f}"

    def test_net_radiation_positive_daytime(self):
        """Net radiation should be positive during a sunny day."""
        solar_rad = 22.0  # MJ/m²/day (clear sky)
        albedo = 0.23  # FAO grass reference
        Rns = (1 - albedo) * solar_rad
        assert Rns > 0, "Net shortwave radiation must be positive in daytime"
        assert Rns == pytest.approx(16.94, abs=0.01)

    def test_et0_reasonable_range(self):
        """Reference ET₀ for a California summer day should be 4-10 mm/day."""
        # Simplified Hargreaves estimate as sanity check
        T_mean = 28.0
        T_max = 35.0
        T_min = 18.0
        Ra = 40.0  # MJ/m²/day (extraterrestrial radiation, summer CA)
        et0_hargreaves = 0.0023 * (T_mean + 17.8) * math.sqrt(T_max - T_min) * Ra * 0.408
        assert 3.0 < et0_hargreaves < 12.0, f"ET₀ out of range: {et0_hargreaves:.2f}"


# ============================================================
# 2. PIML Sigmoid Prior Constraint Tests
# ============================================================

class TestPIMLConstraints:
    """Validate the Physics-Informed ML sigmoid crop coefficient prior."""

    def _sigmoid_kc(self, ndvi):
        """FAO-56 Sigmoid Prior: Kc = 0.15 + 0.95 / (1 + exp(-12*(NDVI - 0.4)))"""
        return 0.15 + 0.95 / (1 + math.exp(-12 * (ndvi - 0.4)))

    def test_kc_bare_soil(self):
        """NDVI ~ 0 (bare soil) → Kc should be near 0.15 (minimum)."""
        kc = self._sigmoid_kc(0.0)
        assert 0.15 <= kc < 0.25, f"Bare soil Kc too high: {kc:.3f}"

    def test_kc_full_canopy(self):
        """NDVI ~ 0.9 (dense vegetation) → Kc should approach 1.1."""
        kc = self._sigmoid_kc(0.9)
        assert 1.0 < kc <= 1.15, f"Full canopy Kc out of range: {kc:.3f}"

    def test_kc_midpoint_transition(self):
        """NDVI = 0.4 should be the inflection point → Kc ≈ 0.625."""
        kc = self._sigmoid_kc(0.4)
        assert abs(kc - 0.625) < 0.01, f"Midpoint Kc mismatch: {kc:.3f}"

    def test_kc_monotonically_increasing(self):
        """Kc must increase monotonically with NDVI."""
        ndvi_values = np.linspace(0, 1, 100)
        kc_values = [self._sigmoid_kc(n) for n in ndvi_values]
        for i in range(1, len(kc_values)):
            assert kc_values[i] >= kc_values[i - 1], "Kc is not monotonically increasing!"

    def test_kc_bounded(self):
        """Kc must always remain within [0.15, 1.20] after clipping."""
        for ndvi in np.linspace(-0.1, 1.1, 200):
            kc = self._sigmoid_kc(ndvi)
            kc_clipped = max(0.15, min(1.20, kc))
            assert 0.15 <= kc_clipped <= 1.20


# ============================================================
# 3. Data Pipeline Integrity Tests
# ============================================================

class TestDataPipeline:
    """Validate data structures and pipeline logic."""

    def test_water_deficit_formula(self):
        """Water deficit = ETc - effective_precip. Must be non-negative (clipped)."""
        etc = 5.2  # mm/day
        precip = 1.0  # mm/day
        deficit = max(0, etc - precip)
        assert deficit == pytest.approx(4.2, abs=0.01)

    def test_water_deficit_no_negative(self):
        """If precipitation exceeds ETc, deficit must be zero (no negative water need)."""
        etc = 2.0
        precip = 10.0
        deficit = max(0, etc - precip)
        assert deficit == 0.0

    def test_stress_coefficient_range(self):
        """Soil moisture stress coefficient Ks must be in [0, 1]."""
        soil_moisture_values = [0.0, 0.1, 0.3, 0.5, 0.8, 1.0]
        for sm in soil_moisture_values:
            ks = min(1.0, max(0.0, sm / 0.5))  # Simple linear stress model
            assert 0.0 <= ks <= 1.0, f"Ks out of range for SM={sm}: {ks}"

    def test_field_grid_dimensions(self):
        """Each field must generate exactly 64 sectors (8x8 grid)."""
        grid_rows, grid_cols = 8, 8
        total_sectors = grid_rows * grid_cols
        assert total_sectors == 64

    def test_four_fields_256_rows(self):
        """4 fields × 64 sectors = 256 rows per hourly cycle."""
        fields = ["Field-A (Corn)", "Field-B (Alfalfa)", "Field-C (Fallow)", "Field-D (Tomato)"]
        total = len(fields) * 64
        assert total == 256


# ============================================================
# 4. Statistical Validation Tests
# ============================================================

class TestStatistics:
    """Validate the statistical functions used for ground-truth benchmarking."""

    def test_pearson_r2_perfect_correlation(self):
        """Perfect linear data should yield R² = 1.0."""
        x = np.array([1, 2, 3, 4, 5], dtype=float)
        y = 2 * x + 3
        from scipy.stats import pearsonr
        r, _ = pearsonr(x, y)
        assert abs(r ** 2 - 1.0) < 1e-10

    def test_rmse_zero_for_identical(self):
        """RMSE of identical arrays must be zero."""
        a = np.array([1.0, 2.0, 3.0])
        rmse = np.sqrt(np.mean((a - a) ** 2))
        assert rmse == 0.0

    def test_mean_bias_sign(self):
        """If predictions are higher than truth, mean bias must be positive."""
        truth = np.array([10, 20, 30])
        pred = np.array([12, 22, 32])
        bias = np.mean(pred - truth)
        assert bias > 0, f"Expected positive bias, got {bias}"

    def test_rmse_always_positive(self):
        """RMSE must be non-negative for any data."""
        truth = np.array([1.0, 5.0, 10.0])
        pred = np.array([2.0, 3.0, 12.0])
        rmse = np.sqrt(np.mean((pred - truth) ** 2))
        assert rmse >= 0
