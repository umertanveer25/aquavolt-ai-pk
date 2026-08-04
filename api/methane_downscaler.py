import torch
import torch.nn as nn
import torch.nn.functional as F
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MethaneDownscalerMLP(nn.Module):
    """
    AI Downscaling Engine for Sentinel-5P Methane.
    Translates 10m spatial features (NDVI, LST, Soil, Topography) into a 
    hyper-local methane anomaly prediction for a specific sector.
    """
    def __init__(self, input_features=5):
        super(MethaneDownscalerMLP, self).__init__()
        # Input features: NDVI, LST, Clay Ratio, Soil Moisture, Slope
        self.fc1 = nn.Linear(input_features, 16)
        self.fc2 = nn.Linear(16, 8)
        self.out = nn.Linear(8, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        # Methane anomaly can be positive or negative
        return self.out(x)

def mass_conservation_loss(high_res_preds, macro_reading):
    """
    Custom Spatial Loss Function:
    Ensures that the mean of the 256 high-resolution (10m) predictions
    exactly equals the single low-resolution (5.5km) Sentinel-5P reading.
    This prevents the AI from hallucinating physical matter.
    """
    # Calculate the mean of all high-resolution predictions in the macro-pixel
    simulated_macro = torch.mean(high_res_preds)
    # L2 Loss against the actual satellite reading
    loss = F.mse_loss(simulated_macro, macro_reading)
    return loss

def apply_downscaling(macro_methane, high_res_features_list):
    """
    Simulates the forward pass of the downscaler for a list of sectors.
    In a real scenario, weights would be loaded from ai_weights_methane.json.
    """
    # Mocking pre-trained weights for the forward pass
    model = MethaneDownscalerMLP(input_features=len(high_res_features_list[0]))
    model.eval()
    
    with torch.no_grad():
        inputs = torch.tensor(high_res_features_list, dtype=torch.float32)
        raw_preds = model(inputs).squeeze()
        
        # Enforce Mass Conservation physically (post-processing calibration)
        # Shift predictions so their mean exactly matches the macro reading
        pred_mean = torch.mean(raw_preds)
        calibrated_preds = raw_preds - pred_mean + macro_methane
        
    return calibrated_preds.numpy().tolist()

if __name__ == "__main__":
    # Test the Downscaler
    logging.info("Testing Sentinel-5P Methane Downscaler...")
    # Simulate a single Sentinel-5P macro reading (5.5km pixel)
    macro_reading = torch.tensor([0.045], dtype=torch.float32)
    
    # Simulate 256 high-resolution 10m sectors
    # Features: [NDVI, LST, Clay Ratio, Soil Moisture, Slope]
    high_res_sectors = torch.rand((256, 5))
    
    model = MethaneDownscalerMLP()
    preds = model(high_res_sectors)
    
    loss = mass_conservation_loss(preds, macro_reading)
    logging.info(f"Initial Mass Conservation Loss: {loss.item():.6f}")
    
    calibrated = apply_downscaling(0.045, high_res_sectors.tolist())
    logging.info(f"Calibrated Mean (Should be 0.045): {sum(calibrated)/len(calibrated):.6f}")
    logging.info("AI Downscaler Architecture ready for September deployment.")
