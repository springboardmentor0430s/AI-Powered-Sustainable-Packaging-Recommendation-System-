import pandas as pd
import numpy as np
import pickle
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score

def train_and_save_models():
    print("Loading data...")
    try:
        df = pd.read_csv("Ecopack.csv")
    except FileNotFoundError:
        print("Error: Ecopack.csv not found!")
        return

    # Feature Engineering: Cost
    print("Feature Engineering...")
    df["Cost_Per_Package"] = (
        df["Weight_Capacity_kg"] * 10 +
        df["Tensile_Strength_MPa"] * 2 +
        df["Moisture_Barrier_Grade"] * 5
    )

    # Features
    # Note: 'AI_Recommendation' is excluded from features to avoid data leak/circular dependency
    features = [
        "Material_Type",
        "Tensile_Strength_MPa",
        "Weight_Capacity_kg",
        "Biodegradability_Score",
        "Recyclability_Percent",
        "Moisture_Barrier_Grade"
    ]

    numeric_features = [
        "Tensile_Strength_MPa",
        "Weight_Capacity_kg",
        "Biodegradability_Score",
        "Recyclability_Percent",
        "Moisture_Barrier_Grade"
    ]
    categorical_features = ["Material_Type"]

    # Preprocessing
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    # Splitting Data for Evaluation
    print("Splitting data for evaluation...")
    X = df[features]
    
    # 1. CO2 Model
    y_co2 = df["CO2_Emission_Score"]
    X_train_co2, X_test_co2, y_train_co2, y_test_co2 = train_test_split(X, y_co2, test_size=0.2, random_state=42)

    print("Training and Evaluating CO2 Model...")
    co2_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))
    ])
    co2_model.fit(X_train_co2, y_train_co2)
    y_pred_co2 = co2_model.predict(X_test_co2)
    print(f"  CO2 Model R2 Score: {r2_score(y_test_co2, y_pred_co2):.4f}")
    print(f"  CO2 Model RMSE: {np.sqrt(mean_squared_error(y_test_co2, y_pred_co2)):.4f}")

    # Retrain on full data for production
    co2_model.fit(X, y_co2)


    # 2. Cost Model
    y_cost = df["Cost_Per_Package"]
    X_train_cost, X_test_cost, y_train_cost, y_test_cost = train_test_split(X, y_cost, test_size=0.2, random_state=42)

    print("Training and Evaluating Cost Model...")
    cost_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=50, random_state=42))
    ])
    cost_model.fit(X_train_cost, y_train_cost)
    y_pred_cost = cost_model.predict(X_test_cost)
    print(f"  Cost Model R2 Score: {r2_score(y_test_cost, y_pred_cost):.4f}")
    print(f"  Cost Model RMSE: {np.sqrt(mean_squared_error(y_test_cost, y_pred_cost)):.4f}")
    
    # Retrain on full data for production
    cost_model.fit(X, y_cost)


    # 3. Recommendation Classifier
    y_rec = df["AI_Recommendation"]
    X_train_rec, X_test_rec, y_train_rec, y_test_rec = train_test_split(X, y_rec, test_size=0.2, random_state=42)

    print("Training and Evaluating Recommendation Classifier...")
    rec_model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=50, random_state=42))
    ])
    rec_model.fit(X_train_rec, y_train_rec)
    y_pred_rec = rec_model.predict(X_test_rec)
    print(f"  Recommendation Model Accuracy: {accuracy_score(y_test_rec, y_pred_rec):.4f}")

    # Retrain on full data for production
    rec_model.fit(X, y_rec)

    # Save Models
    print("Saving models...")
    pickle.dump(co2_model, open('src/models/co2_model.pkl', 'wb'))
    pickle.dump(cost_model, open('src/models/cost_model.pkl', 'wb'))
    pickle.dump(rec_model, open('src/models/recommendation_model.pkl', 'wb'))

    print("Done! Models saved to src/models/")

if __name__ == "__main__":
    train_and_save_models()
