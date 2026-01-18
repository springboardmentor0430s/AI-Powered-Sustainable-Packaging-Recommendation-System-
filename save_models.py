import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

# models folder ensure
os.makedirs('models', exist_ok=True)

# -------------------------
# DUMMY TRAINING DATA
# -------------------------
# 10 samples, 4 features (example)
X = np.random.rand(10, 4)

# target values
y_cost = np.random.rand(10)
y_co2  = np.random.rand(10)

# -------------------------
# TRAIN MODELS
# -------------------------
rf_cost = RandomForestRegressor(random_state=42)
rf_cost.fit(X, y_cost)

xgb_co2 = XGBRegressor(random_state=42)
xgb_co2.fit(X, y_co2)

# -------------------------
# SAVE MODELS
# -------------------------
joblib.dump(rf_cost, 'models/rf_cost_model.pkl')
joblib.dump(xgb_co2, 'models/xgb_co2_model.pkl')

print("✅ Models saved successfully in models folder")