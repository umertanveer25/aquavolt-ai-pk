"""
AquaVolt-AI: High-Performance Multi-Spectral U-Net Training Suite
==================================================================
This script loads, pre-processes, and trains a custom U-Net segmentation model 
on the 169,471-row agricultural database. 
Features:
1. Reshapes spatiotemporal tabular logs into 5-channel 8x8 image tensors.
2. Implements a custom Shallow U-Net optimized for micro-grids (8x8 pixels).
3. Leverages PyTorch AMP (Automatic Mixed Precision) and CUDA GPU acceleration.
4. Uses multi-threaded dataloaders for maximum execution speed.
"""
import os
import time
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader


# Setup device and optimization flags
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.backends.cudnn.benchmark = True  # Auto-tunes conv algorithms for max speed

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
CSV_PATH = os.path.join(DATA_DIR, 'telemetry_log_2026_06_to_08.csv')
MODEL_PATH = os.path.join(DATA_DIR, 'unet_segmentation_weights.pth')

# =====================================================================
# 1. Custom Shallow U-Net Architecture (Optimized for 8x8 micro-grids)
# =====================================================================
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DoubleConv, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    def forward(self, x):
        return self.conv(x)

class ShallowUNet(nn.Module):
    def __init__(self, in_channels=5, num_classes=4):
        super(ShallowUNet, self).__init__()
        # Encoder (Down)
        self.enc1 = DoubleConv(in_channels, 32)
        self.pool1 = nn.MaxPool2d(2, 2) # Down to 4x4
        self.enc2 = DoubleConv(32, 64)
        
        # Bottleneck
        self.bottleneck = DoubleConv(64, 128)
        
        # Decoder (Up)
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2) # Up to 8x8
        self.dec1 = DoubleConv(96, 32) # Concat: 64 + 32 = 96 channels
        
        # Final Classifier
        self.final_conv = nn.Conv2d(32, num_classes, 1)

    def forward(self, x):
        # Encoder
        x1 = self.enc1(x)
        p1 = self.pool1(x1)
        x2 = self.enc2(p1)
        
        # Bottleneck (run in bottleneck)
        b = self.bottleneck(x2)
        
        # Decoder
        u1 = self.up1(b)
        # Skip connection concat along channel dimension
        c1 = torch.cat([u1, x1], dim=1)
        d1 = self.dec1(c1)
        
        return self.final_conv(d1)

# =====================================================================
# 2. Optimized Dataset Generator
# =====================================================================
class MicroGridDataset(Dataset):
    def __init__(self, inputs, targets):
        self.inputs = torch.tensor(inputs, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.long)
        
    def __len__(self):
        return len(self.inputs)
        
    def __getitem__(self, idx):
        return self.inputs[idx], self.targets[idx]

def extract_and_reshape_data():
    """Load the telemetry database and transform it into 8x8 image tensors."""
    print("[PRE-PROCESS] Ingesting telemetry database from CSV...")
    t0 = time.time()
    
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Database not found at {CSV_PATH}")
        
    df = pd.read_csv(CSV_PATH)
    
    # Sort to guarantee exact spatial ordering of the 8x8 grid sectors
    df = df.sort_values(by=['timestamp', 'field_name', 'sector_row', 'sector_col'])
    
    # Check for complete hours (64 rows per group)
    group_size = 64
    num_samples = len(df) // group_size
    trimmed_len = num_samples * group_size
    df = df.iloc[:trimmed_len]
    
    print(f"  - Extracted {num_samples} spatiotemporal image matrices.")
    
    # Input channels: NDVI, NDWI_real, SAVI, LST, Soil_moisture
    feature_cols = ['ndvi', 'ndwi_real', 'savi', 'lst', 'soil_moisture']
    
    # Normalize features vectorially for fast computation
    for col in feature_cols:
        df[col] = (df[col] - df[col].mean()) / (df[col].std() + 1e-8)
        
    # Convert dataframe columns to numpy matrices directly (max speed)
    features_np = df[feature_cols].values # shape: (num_samples*64, 5)
    
    # Target Class Binning based on methane anomalies (Minimal, Low, Medium, High)
    # Target percentile boundaries
    ch4_values = df['methane_anomaly'].fillna(1.95).values
    targets_np = np.zeros_like(ch4_values, dtype=np.int64)
    targets_np[ch4_values >= 1.95] = 1
    targets_np[ch4_values >= 2.10] = 2
    targets_np[ch4_values >= 2.30] = 3
    
    # Reshape features to (N, 8, 8, 5) and then transpose to PyTorch format: (N, 5, 8, 8)
    X = features_np.reshape(num_samples, 8, 8, 5).transpose(0, 3, 1, 2)
    # Reshape targets to (N, 8, 8)
    y = targets_np.reshape(num_samples, 8, 8)
    
    # Extract month of each sample to do temporal block splitting
    df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
    months_np = df['timestamp_dt'].dt.month.values
    months = months_np.reshape(num_samples, group_size)[:, 0]
    
    print(f"  - Vectorized reshape completed in {time.time() - t0:.2f} seconds.")
    return X, y, months

# =====================================================================
# 3. Training Loop
# =====================================================================
def main():
    print("=" * 80)
    print("  AquaVolt-AI: High-Performance Shallow U-Net Training Suite")
    print("  Task: 5-Channel Semantic Hotspot Segmentation")
    print("=" * 80)
    
    # Ingest and format data
    X, y, months = extract_and_reshape_data()
    
    # Temporal Block Splitting:
    # Train on June (month 6) and July (month 7)
    # Test strictly on August (month 8)
    train_idx = np.where(months != 8)[0]
    test_idx = np.where(months == 8)[0]
    
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    
    # Create dataloaders
    train_dataset = MicroGridDataset(X_train, y_train)
    test_dataset = MicroGridDataset(X_test, y_test)
    
    # Max speed: large batch size + pinning memory + multi-threaded workers
    batch_size = 256
    num_workers = 2 if os.name == 'nt' else 4
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        pin_memory=True, 
        num_workers=num_workers,
        persistent_workers=True if num_workers > 0 else False
    )
    
    test_loader = DataLoader(
        test_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        pin_memory=True, 
        num_workers=num_workers
    )
    
    # Initialize network, optimizer, and AMP scaler
    model = ShallowUNet(in_channels=5, num_classes=4).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
    scaler = torch.cuda.amp.GradScaler() # Mixed precision scaler
    
    print(f"\n[DEVICE] Training running on: {device.type.upper()}")
    print(f"  - Training samples (June/July): {len(X_train)} images")
    print(f"  - Testing samples (August):    {len(X_test)} images")
    print("-" * 80)
    
    num_epochs = 20
    t_start = time.time()
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device, non_blocking=True), targets.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True) # Optimized gradient clearing
            
            # Add Gaussian noise (only during training) to simulate sensor noise and prevent overfitting
            noise = torch.randn_like(inputs) * 0.15 # 15% sensor noise
            noisy_inputs = inputs + noise
            
            # Forward pass with Automatic Mixed Precision
            with torch.cuda.amp.autocast(enabled=(device.type == 'cuda')):
                outputs = model(noisy_inputs)
                loss = criterion(outputs, targets)
                
            # Backward pass and step
            if device.type == 'cuda':
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
                
            running_loss += loss.item() * inputs.size(0)
            
        epoch_loss = running_loss / len(X_train)
        
        # Validation evaluation
        model.eval()
        correct = 0
        total_pixels = 0
        with torch.no_grad():
            for inputs, targets in test_loader:
                inputs, targets = inputs.to(device, non_blocking=True), targets.to(device, non_blocking=True)
                outputs = model(inputs)
                preds = torch.argmax(outputs, dim=1)
                correct += (preds == targets).sum().item()
                total_pixels += targets.numel()
                
        val_accuracy = (correct / total_pixels) * 100.0
        print(f"Epoch {epoch+1:02d}/{num_epochs:02d} | Train Loss: {epoch_loss:.4f} | Pixel Accuracy: {val_accuracy:.2f}%")
        
    print("-" * 80)
    print(f"[COMPLETE] Model training finished in {time.time() - t_start:.2f} seconds.")
    
    # Save the trained parameters
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"[SAVED] Calibration weights saved to: {MODEL_PATH}")
    print("=" * 80)

# Helper function to perform train/test split since sklearn may not be installed
def train_split(X, y, test_size=0.2, random_state=42):
    np.random.seed(random_state)
    indices = np.arange(len(X))
    np.random.shuffle(indices)
    split_idx = int(len(X) * (1 - test_size))
    
    train_idx, test_idx = indices[:split_idx], indices[split_idx:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]

if __name__ == "__main__":
    main()
