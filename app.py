from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import psycopg2
import os


app = Flask(__name__)
CORS(app)


cost_model = joblib.load("cost_model.pkl")
co2_model  = joblib.load("co2_model.pkl")
scaler     = joblib.load("scaler.pkl")
features   = joblib.load("features.pkl")


DB_CONFIG = {
    "host": "localhost",
    "database": "ml_db",
    "user": "postgres",
    "password": "postgres",   
    "port": 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def predict_material_safety(row):
    """
    Simple rule-based inference.
    This is NOT stored in DB (by your requirement),
    only returned to frontend.
    """
    if (
        row["co2_emission_score"] <= 2.0 and
        row["recyclability_percent"] >= 60 and
        row["biodegradability_score"] >= 4.0
    ):
        return "Safe"
    return "Moderate"


def preprocess_input(data):
    df = pd.DataFrame([data])

    
    df = pd.get_dummies(
        df,
        columns=["material_category", "material_safety"],
        drop_first=True
    )

    
    df = df.reindex(columns=features, fill_value=0)

    
    num_cols = [
        "strength_mpa",
        "weight_capacity_kg",
        "cost_efficiency_index",
        "material_suitability_score",
        "co2_emission_score",
        "recyclability_percent",
        "biodegradability_score"
    ]

    df[num_cols] = scaler.transform(df[num_cols])
    return df


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Flask API running"})


@app.route("/predict", methods=["POST"])
def predict():
    try:
        
        input_data = request.get_json()

        
        predicted_safety = predict_material_safety(input_data)
        input_data["material_safety"] = predicted_safety

        
        X = preprocess_input(input_data)
        cost_pred = float(cost_model.predict(X)[0])
        co2_pred  = float(co2_model.predict(X)[0])

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO ml_predictions (
                material_category,
                strength_mpa,
                weight_capacity_kg,
                cost_efficiency_index,
                material_suitability_score,
                co2_emission_score,
                recyclability_percent,
                biodegradability_score,
                predicted_cost_usd,
                predicted_co2_impact
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            input_data["material_category"],
            input_data["strength_mpa"],
            input_data["weight_capacity_kg"],
            input_data["cost_efficiency_index"],
            input_data["material_suitability_score"],
            input_data["co2_emission_score"],
            input_data["recyclability_percent"],
            input_data["biodegradability_score"],
            cost_pred,
            co2_pred
        ))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "predicted_cost_usd": round(cost_pred, 2),
            "predicted_co2_impact": round(co2_pred, 2),
            "predicted_material_safety": predicted_safety
        })

    except psycopg2.Error as db_err:
        return jsonify({
            "error": "Database error",
            "details": str(db_err)
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Prediction failed",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
