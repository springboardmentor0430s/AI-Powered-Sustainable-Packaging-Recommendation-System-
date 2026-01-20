import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# -----------------------------------
# STEP 1: Define column names
# -----------------------------------
numeric_features = [
    "Strength",
    "Weight Capacity",
    "Bio Score"
]

categorical_features = [
    "Type",
    "Material Category"
]

# -----------------------------------
# STEP 2: Create Preprocessor
# -----------------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features)
    ]
)

# -----------------------------------
# STEP 3: Dummy data (REQUIRED for fitting)
# -----------------------------------
dummy_data = pd.DataFrame({
    "Strength": [50, 70, 90],
    "Weight Capacity": [20, 40, 60],
    "Bio Score": [30, 60, 90],
    "Type": ["Packaging", "Construction", "Automotive"],
    "Material Category": ["Plastic", "Metal", "Composite"]
})

# -----------------------------------
# STEP 4: Fit preprocessor
# -----------------------------------
preprocessor.fit(dummy_data)

# -----------------------------------
# STEP 5: Save preprocessor
# -----------------------------------
joblib.dump(preprocessor, "preprocessor.pkl")

print("✅ preprocessor.pkl created successfully!")
