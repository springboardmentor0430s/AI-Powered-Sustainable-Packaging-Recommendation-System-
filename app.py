from flask import Flask, render_template, request, jsonify, redirect, session
import pandas as pd
import joblib
import hashlib
import os
from database.db import get_conn
from functools import wraps
from dotenv import load_dotenv
load_dotenv()


# ======================================================
# APP CONFIG
# ======================================================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ecopackai_secret")


app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False
)

# ======================================================
# LOAD ML MODELS
# ======================================================
rf_cost = joblib.load("models/cost_model.pkl")
xgb_co2 = joblib.load("models/co2_model.pkl")
scaler  = joblib.load("models/scaler.pkl")

FEATURE_COLUMNS = [
    "Strength_Mpa",
    "Weight_Capacity_Kg",
    "Temperature Tolerance (°C)",
    "Shelf Life Impact Score (1-10)",
    "Moisture_Resistance_percent",
    "Biodegradability_Score",
    "Recyclability_percent",
    "Material Type",
    "Compostable (Yes/No)",
    "CO2_Emission_Score"
]

# ======================================================
# MATERIAL MAPS
# ======================================================
materials = {
    "synthetic polymer": 0,
    "natural fiber": 1,
    "paper-based": 2,
    "wood-based": 3,
    "bio-composite": 4,
    "natural polymer": 5,
    "biopolymer": 6,
    "biodegradable polymer": 7,
    "metal": 8,
    "inorganic": 9,
    "plant-based polymer": 10
}

material_reverse = {v: k.title() for k, v in materials.items()}

compostable_map = {
    "synthetic polymer": 0,
    "metal": 0,
    "inorganic": 0,
    "natural fiber": 1,
    "paper-based": 1,
    "wood-based": 1,
    "bio-composite": 1,
    "natural polymer": 1,
    "biopolymer": 1,
    "biodegradable polymer": 1,
    "plant-based polymer": 1
}

# ======================================================
# AUTH DECORATOR
# ======================================================
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrap

# ======================================================
# PAGE ROUTES
# ======================================================
@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/analytics")
def analytics():
    if "user_id" not in session:
        return redirect("/")
    return render_template("analytics.html")

@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT recommended_material,
               product_quantity,
               predicted_cost,
               predicted_co2,
               environmental_score,
               created_at
        FROM predictions
        WHERE user_id=%s
        ORDER BY created_at DESC
    """, (session["user_id"],))
    data = cur.fetchall()
    cur.close() 
    conn.close()

    return render_template("history.html", data=data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ======================================================
# AUTH API
# ======================================================
@app.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    pwd_hash = hashlib.sha256(d["password"].encode()).hexdigest()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id FROM users WHERE email=%s AND password_hash=%s",
        (d["email"], pwd_hash)
    )
    user = cur.fetchone()
    cur.close() 
    conn.close()

    if user:
        session["user_id"] = int(user[0])
        return jsonify({"status": "success"})

    return jsonify({"error": "Invalid credentials"}), 401

# ======================================================
# PREDICTION API
# ======================================================
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    d = request.json

    strength = float(d.get("strength", 50))
    weight = float(d.get("weight", 10))
    temperature = float(d.get("temperature", 25))
    co2_score = float(d.get("co2_score", 5))
    qty = int(d.get("product_quantity", 1000))

    biodegradability = 7
    recyclability = 70
    shelf_life = 6
    moisture = 60

    def build_X(code, comp):
        return pd.DataFrame({
            "Strength_Mpa": [strength],
            "Weight_Capacity_Kg": [weight],
            "Temperature Tolerance (°C)": [temperature],
            "Shelf Life Impact Score (1-10)": [shelf_life],
            "Moisture_Resistance_percent": [moisture],
            "Biodegradability_Score": [biodegradability],
            "Recyclability_percent": [recyclability],
            "Material Type": [code],
            "Compostable (Yes/No)": [comp],
            "CO2_Emission_Score": [co2_score]
        })[FEATURE_COLUMNS]

    results = []

    for name, code in materials.items():
        X = scaler.transform(build_X(code, compostable_map[name]))

        cost = float(rf_cost.predict(X)[0]) * qty
        co2  = float(xgb_co2.predict(X)[0]) * qty

        env_score = (
            (biodegradability / 10) * 0.4 +
            (recyclability / 100) * 0.4 +
            (1 - co2_score / 10) * 0.2
        )

        results.append({
            "material": material_reverse[code],
            "cost": round(cost, 2),
            "co2": round(co2, 2),
            "score": round(env_score, 3)
        })

    # TOP-5 RECOMMENDATIONS
    top5 = sorted(results, key=lambda x: (x["co2"], x["cost"]))[:5]
    best = top5[0]

    # SAVE BEST RESULT
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO predictions (
            user_id,
            material,
            product_quantity,
            strength,
            weight,
            temperature,
            co2_score,
            predicted_cost,
            predicted_co2,
            environmental_score,
            recommended_material
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        session["user_id"],
        best["material"],
        qty,
        strength,
        weight,
        temperature,
        co2_score,
        best["cost"],
        best["co2"],
        best["score"],
        best["material"]
    ))
    conn.commit()
    cur.close() 
    conn.close()

    # ✅ IMPORTANT: RESPONSE FORMAT FRONTEND EXPECTS
    return jsonify({
        "user_result": {
            "cost": best["cost"],
            "co2": best["co2"],
            "material": best["material"]
        },
        "top5": top5
    })


# ======================================================
# ANALYTICS API (FINAL – MATCHES DASHBOARD)
# ======================================================
@app.route("/api/analytics")
@login_required
def api_analytics():
    conn = get_conn()
    df = pd.read_sql("""
        SELECT predicted_cost,
               predicted_co2,
               recommended_material,
               created_at
        FROM predictions
        WHERE user_id = %s
        ORDER BY created_at
    """, conn, params=(session["user_id"],))
    conn.close()

    if df.empty:
        return jsonify({
            "labels": [],
            "cost_values": [],
            "co2_values": [],
            "materials": {},
            "avg_cost_saved": 0,
            "avg_co2_reduction": 0
        })

    base_cost = df.iloc[0]["predicted_cost"]
    base_co2  = df.iloc[0]["predicted_co2"]

    # 🔹 PER-PREDICTION VALUES (NOT CUMULATIVE)
    df["cost_saved"] = (base_cost - df["predicted_cost"]).clip(lower=0)
    df["co2_reduction"] = ((base_co2 - df["predicted_co2"]) / base_co2 * 100).clip(lower=0)

    return jsonify({
        "labels": df["created_at"].dt.strftime("%d-%m-%Y").tolist(),
        "cost_values": df["cost_saved"].round(2).tolist(),
        "co2_values": df["co2_reduction"].round(2).tolist(),
        "materials": df["recommended_material"].value_counts().to_dict(),
        "avg_cost_saved": round(df["cost_saved"].mean(), 2),
        "avg_co2_reduction": round(df["co2_reduction"].mean(), 2)
    })

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    app.run()

