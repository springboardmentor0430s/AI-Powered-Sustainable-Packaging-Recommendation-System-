from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from database import get_db_connection, init_db
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load ML models
try:
    co2_model = joblib.load('models/co2_model.pkl')
    cost_model = joblib.load('models/cost_model.pkl')
    print("✅ Models loaded successfully!")
except Exception as e:
    print(f"⚠️ Error loading models: {e}")
    co2_model = None
    cost_model = None

# Material database for recommendations
MATERIALS_DB = [
    {"name": "Recycled Cardboard", "co2_range": (50, 150), "cost_range": (30, 50)},
    {"name": "Biodegradable Plastic", "co2_range": (80, 200), "cost_range": (60, 90)},
    {"name": "Kraft Paper", "co2_range": (40, 120), "cost_range": (25, 45)},
    {"name": "Mushroom Packaging", "co2_range": (20, 80), "cost_range": (70, 110)},
    {"name": "Cornstarch Foam", "co2_range": (60, 140), "cost_range": (50, 80)},
    {"name": "Bamboo Fiber", "co2_range": (30, 100), "cost_range": (55, 85)},
    {"name": "Seaweed Packaging", "co2_range": (15, 70), "cost_range": (80, 120)},
]

def get_material_recommendation(co2, cost):
    """Find best matching material based on predictions"""
    scores = []
    for material in MATERIALS_DB:
        co2_score = 1 - (abs(co2 - np.mean(material["co2_range"])) / 200)
        cost_score = 1 - (abs(cost - np.mean(material["cost_range"])) / 100)
        total_score = (co2_score * 0.6) + (cost_score * 0.4)
        scores.append({"material": material["name"], "score": total_score, 
                      "co2": np.mean(material["co2_range"]), 
                      "cost": np.mean(material["cost_range"])})
    
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:3]

@app.route('/')
def home():
    return jsonify({"status": "EcoPackAI API Running", "version": "1.0"})

@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    data = request.json
    print("GOOGLE AUTH PAYLOAD:", data)

    if not data:
        return jsonify({"error": "No data received"}), 400

    token = data.get("credential")  # 👈 THIS IS THE KEY FIX

    if not token:
        return jsonify({"error": "Google token missing"}), 400

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )

        email = idinfo.get("email")
        name = idinfo.get("name")

        print("GOOGLE USER:", email, name)

        return jsonify({
            "email": email,
            "name": name
        }), 200

    except Exception as e:
        print("GOOGLE VERIFY ERROR:", e)
        return jsonify({"error": "Invalid Google token"}), 401


@app.route('/api/predict', methods=['POST'])
def predict():
    """Make predictions for packaging"""
    try:
        data = request.json
        
        # Extract features
        features = np.array([[
            float(data['strength_mpa']),
            float(data['weight_capacity_kg']),
            float(data['biodegradability_pct']),
            float(data['recyclability_pct'])
        ]])
        
        # Make predictions
        if co2_model and cost_model:
            predicted_co2 = float(co2_model.predict(features)[0])
            predicted_cost = float(cost_model.predict(features)[0])
        else:
            # Fallback calculation if models not loaded
            predicted_co2 = 100 - (float(data['biodegradability_pct']) * 0.5)
            predicted_cost = 50 + (float(data['strength_mpa']) * 0.2)
        
        # Get material recommendations
        recommendations = get_material_recommendation(predicted_co2, predicted_cost)
        
        # Save to database
        user_id = data.get('user_id', 1)
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO predictions 
            (user_id, strength_mpa, weight_capacity_kg, biodegradability_pct, 
             recyclability_pct, predicted_co2, predicted_cost, recommended_material)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, features[0][0], features[0][1], features[0][2], 
              features[0][3], predicted_co2, predicted_cost, recommendations[0]['material']))
        
        prediction_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "prediction_id": prediction_id,
            "predicted_co2": round(predicted_co2, 2),
            "predicted_cost": round(predicted_cost, 2),
            "recommendations": recommendations
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """Get prediction history for a user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, strength_mpa, weight_capacity_kg, biodegradability_pct,
                   recyclability_pct, predicted_co2, predicted_cost, 
                   recommended_material, created_at
            FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        predictions = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "predictions": predictions})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard(user_id):
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get statistics
        cur.execute('''
            SELECT 
                COUNT(*) as total_predictions,
                AVG(predicted_co2) as avg_co2,
                AVG(predicted_cost) as avg_cost,
                MIN(predicted_co2) as min_co2,
                MAX(predicted_co2) as max_co2
            FROM predictions
            WHERE user_id = %s
        ''', (user_id,))
        
        stats = cur.fetchone()
        
        # Get material distribution
        cur.execute('''
            SELECT recommended_material, COUNT(*) as count
            FROM predictions
            WHERE user_id = %s
            GROUP BY recommended_material
            ORDER BY count DESC
        ''', (user_id,))
        
        materials = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": stats,
            "material_distribution": materials
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)