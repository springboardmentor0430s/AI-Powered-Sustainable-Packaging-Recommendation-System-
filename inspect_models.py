import joblib
import numpy as np
import sys
import os

model_dir = "model"

try:
    print("Loading models...")
    scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))
    co2_model = joblib.load(os.path.join(model_dir, "xgb_co2_model.pkl"))
    cost_model = joblib.load(os.path.join(model_dir, "rf_cost_model.pkl"))
    
    print(f"Scaler expected features: {scaler.n_features_in_}")
    
    # XGBoost and RF usually have n_features_in_
    if hasattr(co2_model, "n_features_in_"):
        print(f"CO2 Model expected features: {co2_model.n_features_in_}")
    else:
         print(f"CO2 Model type: {type(co2_model)}")

    if hasattr(cost_model, "n_features_in_"):
        print(f"Cost Model expected features: {cost_model.n_features_in_}")
    else:
        print(f"Cost Model type: {type(cost_model)}")
    
except Exception as e:
    print(f"Error inspecting models: {e}")
