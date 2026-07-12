import numpy as np
import pandas as pd
import sqlite3
import os
import math
from datetime import datetime, timedelta

class LSTMForecaster:
    def __init__(self, db_path='aquavolt.db'):
        self.db_path = db_path
        self.tf_available = False
        self.model = None
        self.scaler = None
        self._check_tensorflow()

    def _check_tensorflow(self):
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            from sklearn.preprocessing import MinMaxScaler
            self.tf_available = True
            print("[FORECASTER] TensorFlow and Keras imported successfully.")
        except ImportError:
            print("[FORECASTER] TensorFlow or scikit-learn not available. Falling back to analytical physics-based forecast.")

    def fetch_historical_data(self):
        """Loads historical weather and crop telemetry from database or returns simulated series if empty."""
        if not os.path.exists(self.db_path):
            print(f"[FORECASTER] Database {self.db_path} not found. Generating synthetic history for training.")
            return self._generate_synthetic_history()
        
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT timestamp, air_temp, humidity, solar_rad, ndvi, Kc, Ks, water_need 
                FROM telemetry_log 
                ORDER BY timestamp ASC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) < 48:
                print(f"[FORECASTER] Insufficient database rows ({len(df)}/48). Supplementing with synthetic data.")
                return self._generate_synthetic_history()
            return df
        except Exception as e:
            print(f"[FORECASTER] Database error: {e}. Supplementing with synthetic data.")
            return self._generate_synthetic_history()

    def _generate_synthetic_history(self):
        """Generates 7 days (168 hours) of hourly agricultural and weather logs for training."""
        np.random.seed(42)
        base_time = datetime.now() - timedelta(days=7)
        timestamps = [ (base_time + timedelta(hours=i)).isoformat() for i in range(168) ]
        
        # Diurnal weather curves
        hours = np.arange(168)
        temp = 25.0 + 10.0 * np.sin(2.0 * np.pi * hours / 24.0) + np.random.normal(0, 1.0, 168)
        humidity = 50.0 - 20.0 * np.sin(2.0 * np.pi * hours / 24.0) + np.random.normal(0, 2.0, 168)
        solar = np.maximum(0, 800.0 * np.sin(2.0 * np.pi * hours / 24.0) + np.random.normal(0, 20.0, 168))
        
        # Crop variables (semi-stable NDVI/Kc/Ks)
        ndvi = 0.65 + np.random.normal(0, 0.01, 168)
        kc = 0.82 + np.random.normal(0, 0.01, 168)
        ks = 1.0 - 0.5 * np.maximum(0, np.sin(2.0 * np.pi * hours / 48.0)) # periodic stress
        
        # Deficit calculation: deficit accumulates when solar and temp are high
        water_need = np.maximum(0, 0.5 * temp + 0.005 * solar - 5 * ks + np.random.normal(0, 0.5, 168))
        
        return pd.DataFrame({
            'timestamp': timestamps,
            'air_temp': temp,
            'humidity': humidity,
            'solar_rad': solar,
            'ndvi': ndvi,
            'Kc': kc,
            'Ks': ks,
            'water_need': water_need
        })

    def train(self, epochs=10, batch_size=16):
        """Trains the LSTM network if TensorFlow is available, otherwise prepares analytical forecast parameters."""
        df = self.fetch_historical_data()
        features = ['air_temp', 'humidity', 'solar_rad', 'ndvi', 'Kc', 'Ks', 'water_need']
        data = df[features].values.astype(np.float32)
        
        if not self.tf_available:
            print("[FORECASTER] Skipping neural network training. Analytical model initialized.")
            return False
            
        try:
            from sklearn.preprocessing import MinMaxScaler
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout
            
            self.scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = self.scaler.fit_transform(data)
            
            # Form sliding window sequences (12-hour lookback to predict next hour deficit)
            lookback = 12
            X, y = [], []
            for i in range(lookback, len(scaled_data)):
                X.append(scaled_data[i-lookback:i])
                y.append(scaled_data[i, -1]) # Target is water_need (last column)
                
            X, y = np.array(X), np.array(y)
            
            model = Sequential([
                LSTM(32, input_shape=(X.shape[1], X.shape[2]), return_sequences=True),
                Dropout(0.1),
                LSTM(16),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
            self.model = model
            print("[FORECASTER] LSTM neural network trained successfully.")
            return True
        except Exception as e:
            print(f"[FORECASTER] Training error: {e}. Falling back to analytical methods.")
            self.tf_available = False
            return False

    def predict_24h(self, current_readings):
        """Predicts the next 24 hours of crop water deficit.
        current_readings: list of 12 dicts containing recent hourly logs or a single dict to project.
        """
        # Ensure we have a list of hourly dicts
        if isinstance(current_readings, dict):
            current_readings = [current_readings] * 12
            
        features = ['air_temp', 'humidity', 'solar_rad', 'ndvi', 'Kc', 'Ks', 'water_need']
        
        # If LSTM model is active, attempt neural prediction
        if self.tf_available and self.model is not None and self.scaler is not None:
            try:
                # Convert input log list to array
                input_data = []
                for log in current_readings[-12:]:
                    input_data.append([log.get(f, 0.0) for f in features])
                
                # If short, pad
                while len(input_data) < 12:
                    input_data.insert(0, input_data[0])
                    
                input_arr = np.array(input_data).astype(np.float32)
                scaled_input = self.scaler.transform(input_arr)
                
                # Autoregressive 24-step forecast
                forecast = []
                current_window = scaled_input.copy()
                
                for _ in range(24):
                    pred = self.model.predict(current_window.reshape(1, 12, len(features)), verbose=0)
                    forecast_val = pred[0, 0]
                    forecast.append(forecast_val)
                    
                    # Roll window and update weather variables with simulated diurnal shift
                    next_row = current_window[-1].copy()
                    # target is index -1
                    next_row[-1] = forecast_val
                    # Simple diurnal cycle adjustments to keep features realistic
                    next_row[0] = next_row[0] + 0.05 * math.sin(len(forecast) * math.pi / 12)
                    next_row[1] = next_row[1] - 0.05 * math.sin(len(forecast) * math.pi / 12)
                    
                    current_window = np.vstack([current_window[1:], next_row])
                
                # Inverse scale back
                dummy = np.zeros((24, len(features)))
                dummy[:, -1] = forecast
                unscaled = self.scaler.inverse_transform(dummy)
                return np.maximum(0.0, unscaled[:, -1]).tolist()
            except Exception as e:
                print(f"[FORECASTER] Inference error: {e}. Falling back to analytical projection.")
        
        # Fallback Analytical Projection
        # Project water need using a simple diurnal model matching FAO-56 logic
        latest = current_readings[-1]
        base_deficit = latest.get('water_need', 2.5)
        temp = latest.get('air_temp', 25.0)
        solar = latest.get('solar_rad', 500.0)
        ks = latest.get('Ks', 1.0)
        
        forecast = []
        for hour in range(24):
            # Diurnal solar and temp multiplier
            diurnal_mult = math.sin((hour + 12) * math.pi / 12)
            projected_temp = temp + 8.0 * diurnal_mult
            projected_solar = max(0.0, solar + 400.0 * diurnal_mult)
            
            # Projected ET under diurnal weather
            proj_et = (0.15 * projected_temp + 0.002 * projected_solar) * ks
            # Deficit accumulation
            base_deficit = max(0.0, base_deficit + proj_et - (0.5 if hour % 12 == 0 else 0.0))
            forecast.append(round(base_deficit, 2))
            
        return forecast

if __name__ == "__main__":
    # Self-test training and prediction
    forecaster = LSTMForecaster()
    forecaster.train(epochs=2)
    sample_log = {
        'air_temp': 28.0,
        'humidity': 45.0,
        'solar_rad': 600.0,
        'ndvi': 0.7,
        'Kc': 0.85,
        'Ks': 0.9,
        'water_need': 3.2
    }
    pred = forecaster.predict_24h(sample_log)
    print("24-Hour Predicted Water Deficit Curve:", pred)
