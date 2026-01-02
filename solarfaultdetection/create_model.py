"""
Script to create a valid PyTorch model file for solar fault detection.
Run this once to generate model/solar_model.pth
"""

import torch
from torchvision import models
from torch import nn
from pathlib import Path

# Create model directory if it doesn't exist
Path("model").mkdir(exist_ok=True)

# Create the model architecture
# Update number of classes based on fault types in predict.py
NUM_CLASSES = 8  # Healthy + 7 fault types
model = models.resnet18(pretrained=False)
model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)

# Initialize with random weights (for testing/demo purposes)
# In production, you would load trained weights here
print("Creating model with random weights...")
print("Note: This is a placeholder model for testing. Train with your data for real predictions.")

# Save the model state_dict (correct way)
model_path = Path("model/solar_model.pth")
torch.save(model.state_dict(), model_path)

# Verify the file was created
file_size = model_path.stat().st_size / (1024 * 1024)  # Size in MB
print(f"Model saved successfully!")
print(f"   Location: {model_path}")
print(f"   Size: {file_size:.2f} MB")
print(f"\nYou can now run: streamlit run app.py")

