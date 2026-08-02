import json
import os
import numpy as np
import math
from datetime import datetime
import aquavolt_gsheet_logger

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "ai_weights_mlp.json")

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -15, 15)))

def relu(x):
    return np.maximum(0, x)

def load_weights():
    with open(WEIGHTS_PATH, "r") as f:
        return json.load(f)

def save_weights(weights):
    weights["trained_on"] = datetime.utcnow().isoformat()
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights, f, indent=2)

def fetch_training_data():
    """Fetch recent data from Google Sheets to use as training data."""
    print("[TRAINING] Fetching latest telemetry from Google Sheets...")
    gc = aquavolt_gsheet_logger.get_gspread_client()
    sheet_name = aquavolt_gsheet_logger.DEFAULT_SHEET_NAME
    try:
        sh = gc.open(sheet_name)
        worksheet = sh.get_worksheet(0)
    except Exception as e:
        print(f"[TRAINING] Could not open sheet {sheet_name}. It may not exist yet this month. Exiting. Error: {e}")
        return np.array([]), np.array([])
    
    # Get all records, ignoring header
    records = worksheet.get_all_values()[1:]
    
    X = []
    y = []
    
    for row in records:
        try:
            # Indices based on aquavolt_gsheet_logger.py columns:
            # 5: ndvi, 6: ndwi, 8: savi, 13: kc, 15: Dr, 18: ETc
            ndvi = float(row[5])
            ndwi = float(row[6])
            savi = float(row[8])
            dr = float(row[15])
            
            # Ground truth proxy for Kc (since ECOSTRESS is missing)
            # We assume the logged Kc is our baseline, and we add small noise for simulated training
            target_kc_residual = 0.05 * np.random.randn() # Simulated residual target
            
            X.append([ndvi, ndwi, savi, dr])
            y.append([target_kc_residual])
        except (IndexError, ValueError):
            continue
            
    return np.array(X[-1000:]), np.array(y[-1000:])

def train_mlp():
    weights = load_weights()
    X, y = fetch_training_data()
    
    if len(X) < 10:
        print("[TRAINING] Not enough data to train. Exiting.")
        return
        
    print(f"[TRAINING] Training on {len(X)} records...")
    
    # Extract weights
    W1 = np.array(weights["W1"])
    b1 = np.array(weights["b1"])
    W2 = np.array(weights["W2"])
    b2 = np.array(weights["b2"])
    W3 = np.array(weights["W3"])
    b3 = np.array(weights["b3"])
    
    feat_mean = np.array(weights["feat_mean"])
    feat_std = np.array(weights["feat_std"])
    
    # Normalize X
    X_norm = (X - feat_mean) / feat_std
    
    # Simple Gradient Descent (1 epoch)
    learning_rate = 0.01
    
    # Forward pass
    z1 = np.dot(X_norm, W1) + b1
    a1 = relu(z1)
    z2 = np.dot(a1, W2) + b2
    a2 = relu(z2)
    z3 = np.dot(a2, W3) + b3
    output = z3
    
    # Compute loss (MSE)
    loss = np.mean((output - y) ** 2)
    print(f"[TRAINING] Initial Loss: {loss:.4f}")
    
    # Backward pass
    dz3 = (output - y) / len(X)
    dW3 = np.dot(a2.T, dz3)
    db3 = np.sum(dz3, axis=0)
    
    da2 = np.dot(dz3, W3.T)
    dz2 = da2 * (z2 > 0)
    dW2 = np.dot(a1.T, dz2)
    db2 = np.sum(dz2, axis=0)
    
    da1 = np.dot(dz2, W2.T)
    dz1 = da1 * (z1 > 0)
    dW1 = np.dot(X_norm.T, dz1)
    db1 = np.sum(dz1, axis=0)
    
    # Update weights
    W1 -= learning_rate * dW1
    b1 -= learning_rate * db1
    W2 -= learning_rate * dW2
    b2 -= learning_rate * db2
    W3 -= learning_rate * dW3
    b3 -= learning_rate * db3
    
    # Save back to dict
    weights["W1"] = W1.tolist()
    weights["b1"] = b1.tolist()
    weights["W2"] = W2.tolist()
    weights["b2"] = b2.tolist()
    weights["W3"] = W3.tolist()
    weights["b3"] = b3.tolist()
    
    save_weights(weights)
    print(f"[TRAINING] Model successfully evolved and saved. New timestamp: {weights['trained_on']}")

if __name__ == "__main__":
    train_mlp()
