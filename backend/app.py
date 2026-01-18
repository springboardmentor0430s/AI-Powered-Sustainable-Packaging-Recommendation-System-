from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import pickle
import os
import numpy as np
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["*"])

#import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="ecopackai",
        user="postgres",
        password="Reshma@project",
        port=5432
    )

# Load model files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "reg_model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "feature_scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "feature_columns.pkl")

try:
    reg_model = pickle.load(open(MODEL_PATH, "rb"))
    scaler = pickle.load(open(SCALER_PATH, "rb"))
    feature_columns = pickle.load(open(FEATURES_PATH, "rb"))
    print("✅ Model loaded -", len(feature_columns), "features")
except:
    reg_model = None
    print("❌ Model files missing")



# Initialize database with USERS + HISTORY tables
def init_db():
    conn = get_db_connection()
    if not conn:
        print("❌ Database connection failed")
        return
    
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Prediction history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        username VARCHAR(100) NOT NULL,
        toy_weight FLOAT NOT NULL,
        toy_cost FLOAT NOT NULL,
        toy_material VARCHAR(50) NOT NULL,
        recommended_packaging VARCHAR(100) NOT NULL,
        co2_emission FLOAT NOT NULL,
        packaging_cost FLOAT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ PostgreSQL: Users + History tables created!")

init_db()

PACKAGING_OPTIONS = ["Box", "Plastic Case", "Blister Pack", "Recycled Box", "Recycled Bag", "Metal Tin"]

def predict_for_packaging(toy_weight, toy_cost, toy_material, packaging_type):
    """Dynamic predictions based on input values"""
    input_data = {col: 0.0 for col in feature_columns}
    
    weight_factor = min(toy_weight / 1000.0, 10.0)
    cost_factor = min(toy_cost / 100.0, 10.0)
    
    material_scores = {
        "Plastic": 3.5, "Wood": 7.0, "ABS Plastic": 4.5,
        "Fabric": 2.0, "Metal": 9.5, "Cardboard": 1.5
    }
    material_strength = material_scores.get(toy_material, 3.0)
    
    for col in feature_columns:
        if col == "weight_capacity":
            input_data[col] = weight_factor * 1.2
        elif col == "fragility_level":
            input_data[col] = max(1.0, 10.0 - weight_factor)
        elif col == "strength":
            input_data[col] = material_strength
        elif col == "packaging_cost_estimate":
            input_data[col] = cost_factor
        elif col.startswith("recommended_packaging_"):
            col_name = col.replace("recommended_packaging_", "")
            input_data[col] = 1.0 if packaging_type == col_name else 0.0
        elif col.startswith("toy_material_"):
            col_name = col.replace("toy_material_", "")
            input_data[col] = 1.0 if toy_material == col_name else 0.0
    
    input_df = pd.DataFrame([input_data])
    scaler_features = scaler.feature_names_in_ if hasattr(scaler, 'feature_names_in_') else feature_columns
    existing_numeric = [col for col in scaler_features if col in input_df.columns]
    
    if len(existing_numeric) > 0:
        input_df[existing_numeric] = scaler.transform(input_df[existing_numeric])
    
    try:
        prediction = reg_model.predict(input_df)[0]
        base_co2 = max(0.1, float(prediction[0]) if len(prediction) > 0 else 1.0)
        base_cost = max(10, float(prediction[1]) if len(prediction) > 1 else 50.0)
        
        co2 = base_co2 * (1 + (weight_factor / 20.0)) * (1 + (5 - material_strength) / 10.0)
        cost = base_cost * (1 + (cost_factor / 20.0))
        
        return round(co2, 2), round(cost, 0)
    except:
        return round(1.0 + (toy_weight/10000), 2), round(50 + (toy_cost*0.1), 0)

# API Routes
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": reg_model is not None,
        "database": "PostgreSQL",
        "features": len(feature_columns) if feature_columns else 0
    })

@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        print(f"✅ New user: {username} (ID: {user_id})")
        return jsonify({"message": "Account created successfully!"})
    except Exception as e:
        conn.close()
        print(f"Signup error: {e}")
        return jsonify({"error": "Username already exists"}), 400

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[2], password):
        print(f"✅ Login: {username} (ID: {user[0]})")
        return jsonify({
            "message": "Login successful", 
            "user_id": user[0],
            "username": user[1]
        })
    return jsonify({"error": "Invalid username or password"}), 401

@app.route("/api/predict", methods=["POST"])
def predict():
    if not reg_model:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.get_json() or {}
    toy_weight = float(data.get("toy_weight", 500))
    toy_cost = float(data.get("toy_cost", 50))
    toy_material = data.get("toy_material", "Plastic")
    username = data.get("username", "anonymous")
    user_id = data.get("user_id")  # can be None

    print(f"🔮 Predicting: {toy_weight}g {toy_material}, ₹{toy_cost} by {username}")

    all_results = []
    for packaging in PACKAGING_OPTIONS:
        co2, cost = predict_for_packaging(toy_weight, toy_cost, toy_material, packaging)
        eco_score = (co2 * 0.7) + (cost * 0.3)
        all_results.append({
            "packaging": packaging,
            "co2_emission": co2,
            "cost": cost,
            "eco_score": round(eco_score, 2)
        })

    all_results.sort(key=lambda x: x["eco_score"])
    top_3 = all_results[:3]
    best = top_3[0]

    # ✅ SAVE TO prediction_history
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prediction_history 
                (user_id, username, toy_weight, toy_cost, toy_material, recommended_packaging, 
                 co2_emission, packaging_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, username, toy_weight, toy_cost, toy_material, 
                  best["packaging"], best["co2_emission"], best["cost"]))
            conn.commit()
            print(f"✅ History saved for {username}")
        except Exception as e:
            print(f"❌ History save error: {e}")
        
        # ✅ ALSO SAVE TO predictions TABLE
        try:
            cursor.execute("""
                INSERT INTO predictions (
                    user_id,
                    username,
                    toy_material,
                    toy_weight,
                    toy_cost,
                    recommended_packaging,
                    co2_emission,
                    packaging_cost
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, username, toy_material, toy_weight, toy_cost,
                  best["packaging"], best["co2_emission"], best["cost"]))
            conn.commit()
            print(f"✅ Prediction saved to predictions table for {username}")
        except Exception as e:
            print(f"❌ Error saving prediction: {e}")
        finally:
            conn.close()

    return jsonify({
        "recommended_packaging": best["packaging"],
        "co2_emission": best["co2_emission"],
        "packaging_cost": best["cost"],
        "toy_material": toy_material,
        "top_3": top_3
    })


# NEW: View all users
@app.route("/api/users", methods=["GET"])
def get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, created_at FROM users ORDER BY created_at DESC")
    users = [{"id": row[0], "username": row[1], "created_at": row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"users": users})

# NEW: View prediction history
@app.route("/api/history", methods=["GET"])
def get_history():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, toy_weight, toy_cost, toy_material, recommended_packaging, 
               co2_emission, packaging_cost, created_at 
        FROM prediction_history 
        ORDER BY created_at DESC LIMIT 50
    """)
    history = []
    for row in cursor.fetchall():
        history.append({
            "username": row[0],
            "toy_weight": row[1],
            "toy_cost": row[2],
            "toy_material": row[3],
            "recommended_packaging": row[4],
            "co2_emission": row[5],
            "packaging_cost": row[6],
            "created_at": row[7]
        })
    conn.close()
    return jsonify({"history": history})

if __name__ == "__main__":
    print("🚀 EcoPackAI Backend - POSTGRESQL + HISTORY")
    print("📊 New endpoints: /api/users, /api/history")
    app.run(debug=True, host="0.0.0.0", port=5000)
