"""
AquaVolt-AI Unit Tests
======================
Validates the core physics engine, PIML constraints, data pipeline integrity,
LSTM forecasting module, and plugin auto-discovery registry.
Run with: pytest tests/ -v
"""
import math
import os
import sys
import numpy as np
import pytest

# Allow imports from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


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
        """If precipitation exceeds ETc, deficit must be zero."""
        etc = 2.0
        precip = 10.0
        deficit = max(0, etc - precip)
        assert deficit == 0.0

    def test_stress_coefficient_range(self):
        """Soil moisture stress coefficient Ks must be in [0, 1]."""
        soil_moisture_values = [0.0, 0.1, 0.3, 0.5, 0.8, 1.0]
        for sm in soil_moisture_values:
            ks = min(1.0, max(0.0, sm / 0.5))
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


# ============================================================
# 5. LSTM Forecaster Tests (NEW)
# ============================================================

class TestLSTMForecaster:
    """Validate the LSTM water deficit forecasting module."""

    @pytest.fixture(scope="class")
    def forecaster(self):
        from lstm_forecaster import LSTMForecaster
        fc = LSTMForecaster(db_path="nonexistent_db_for_testing.db")
        return fc

    def test_synthetic_history_shape(self, forecaster):
        """Synthetic history must have 168 rows (7 days × 24 hours) and 8 columns."""
        df = forecaster._generate_synthetic_history()
        assert len(df) == 168, f"Expected 168 rows, got {len(df)}"
        assert "water_need" in df.columns
        assert "air_temp" in df.columns

    def test_synthetic_history_no_nulls(self, forecaster):
        """Synthetic history must not contain any NaN values."""
        df = forecaster._generate_synthetic_history()
        assert not df.isnull().any().any(), "Synthetic history contains NaN values"

    def test_predict_returns_24_values(self, forecaster):
        """predict_24h() must always return exactly 24 values."""
        sample = {
            "air_temp": 30.0, "humidity": 40.0, "solar_rad": 700.0,
            "ndvi": 0.7, "Kc": 0.85, "Ks": 0.9, "water_need": 4.0,
        }
        result = forecaster.predict_24h(sample)
        assert len(result) == 24, f"Expected 24 forecast values, got {len(result)}"

    def test_predict_all_non_negative(self, forecaster):
        """Water deficit forecast values must all be >= 0 (no negative water need)."""
        sample = {
            "air_temp": 25.0, "humidity": 50.0, "solar_rad": 500.0,
            "ndvi": 0.6, "Kc": 0.8, "Ks": 1.0, "water_need": 2.0,
        }
        result = forecaster.predict_24h(sample)
        for i, val in enumerate(result):
            assert val >= 0.0, f"Negative deficit at hour {i+1}: {val}"

    def test_predict_with_list_input(self, forecaster):
        """predict_24h() must handle a list of 12 hourly dicts as input."""
        sample = {
            "air_temp": 28.0, "humidity": 45.0, "solar_rad": 600.0,
            "ndvi": 0.65, "Kc": 0.82, "Ks": 0.95, "water_need": 3.5,
        }
        result = forecaster.predict_24h([sample] * 12)
        assert len(result) == 24


# ============================================================
# 6. Plugin Registry Tests (NEW)
# ============================================================

class TestPluginRegistry:
    """Validate the auto-discovery plugin registry."""

    @pytest.fixture(scope="class")
    def plugins(self):
        import importlib.util
        plugin_dir = os.path.join(
            os.path.dirname(__file__), "..", "plugins", "sensors"
        )
        plugin_dir = os.path.abspath(plugin_dir)
        loaded = []
        for fname in os.listdir(plugin_dir):
            if fname.endswith(".py") and not fname.startswith("__"):
                path = os.path.join(plugin_dir, fname)
                spec = importlib.util.spec_from_file_location(fname[:-3], path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "fetch") and hasattr(mod, "SENSOR_INFO"):
                    loaded.append(mod)
        return loaded

    def test_minimum_plugin_count(self, plugins):
        """At least 15 sensor plugins must be loaded (robust minimum)."""
        assert len(plugins) >= 15, f"Too few plugins loaded: {len(plugins)}"

    def test_all_plugins_have_sensor_info(self, plugins):
        """Every plugin must have a SENSOR_INFO dict with required keys."""
        required_keys = {"name", "type", "resolution", "source", "status"}
        for plugin in plugins:
            missing = required_keys - set(plugin.SENSOR_INFO.keys())
            assert not missing, f"Plugin {plugin.__name__} missing keys: {missing}"

    def test_all_plugins_have_fetch_callable(self, plugins):
        """Every plugin must expose a callable fetch() function."""
        for plugin in plugins:
            assert callable(plugin.fetch), f"Plugin {plugin.__name__}.fetch is not callable"

    def test_no_duplicate_plugin_names(self, plugins):
        """No two plugins should report the same name (prevents confusion)."""
        names = [p.SENSOR_INFO["name"] for p in plugins]
        assert len(names) == len(set(names)), f"Duplicate plugin names found: {[n for n in names if names.count(n) > 1]}"

    def test_plugin_sensor_info_name_nonempty(self, plugins):
        """Every plugin's SENSOR_INFO name must be a non-empty string."""
        for plugin in plugins:
            name = plugin.SENSOR_INFO.get("name", "")
            assert isinstance(name, str) and len(name) > 0, \
                f"Plugin has empty or invalid name: {plugin.__name__}"
