from flask import Flask, request, jsonify, make_response, redirect
from flask_cors import CORS
import pandas as pd
import joblib
import os
import jwt
import datetime
import requests
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timedelta

MATERIAL_BASELINES = {
    "Glass": {
        "Cost_Per_Unit_USD": 0.45,
        "CO2_Emission": 6.0,
        "Strength_MPa": 70,
        "Recyclability": 9,
        "Biodegradability": 1
    },
    "Recycled Paper": {
        "Cost_Per_Unit_USD": 0.30,
        "CO2_Emission": 3.5,
        "Strength_MPa": 25,
        "Recyclability": 8,
        "Biodegradability": 8
    },
    "Bio-Plastic": {
        "Cost_Per_Unit_USD": 0.40,
        "CO2_Emission": 4.0,
        "Strength_MPa": 40,
        "Recyclability": 6,
        "Biodegradability": 7
    },
    "Aluminum": {
        "Cost_Per_Unit_USD": 0.50,
        "CO2_Emission": 8.0,
        "Strength_MPa": 80,
        "Recyclability": 9,
        "Biodegradability": 0
    }
}

cost_model = joblib.load("models/best_rf_cost.pkl")
co2_model = joblib.load("models/best_xgb_co2.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = list(scaler.feature_names_in_)

materials_df = pd.read_csv("data/EcoPackAI_Final_Model_Output.csv")


load_dotenv()

# --- APP INIT ---
app = Flask(__name__)

# ✅ SINGLE CORS CONFIG (FIXES OPTIONS 404)
# ✅ SINGLE CORS CONFIG (FIXES OPTIONS 404)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# --- JWT CONFIG ---
JWT_SECRET = "super-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXP_MINUTES = 60

APP_URI = os.getenv("APP_URI", "http://localhost:5173")

# Google Config
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
print("CLIENT ID USED BY BACKEND:", GOOGLE_CLIENT_ID)
print("REDIRECT URI USED BY BACKEND:", GOOGLE_REDIRECT_URI)

# Microsoft Config
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# def init_db():
#     conn = get_db_connection()
#     if conn:
#         try:
#             cur = conn.cursor()
#             cur.execute("""
#             """)
#             conn.commit()
#             print("✅ Predictions table ensured.")
#             cur.close()
#             conn.close()
#         except Exception as e:
#             print("❌ DB Init Error:", e)


# --- DB HELPERS ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print("❌ DB CONNECTION ERROR:", e)
        raise e   # 🔥 IMPORTANT: do NOT return None

def get_user_by_email(email):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def create_user(name, email, password_hash=None, auth_provider='local', provider_id=None):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, auth_provider, provider_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *;
            """,
            (name, email, password_hash, auth_provider, provider_id)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"DB Error: {e}")
        if conn: conn.rollback()
        return None

from functools import wraps

# --- DECORATOR ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization token missing"}), 401

        token = auth_header.split(" ")[1]

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            current_user_id = data["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"message": "Token is invalid!", "error": str(e)}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# 3. GET CURRENT USER (Protected)
@app.route("/auth/me", methods=["GET"])
@token_required
def me(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, name, email FROM users WHERE id = %s", (current_user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
         return jsonify({"authenticated": False}), 401
    
    return jsonify({"authenticated": True, "user": user})

# --- LOGIN (EMAIL + PASSWORD) ---
@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash FROM users WHERE email = %s AND auth_provider = 'local'",
        (email,)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_id, password_hash = user

    if not check_password(password, password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    # 🔐 CREATE JWT
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200

@app.route("/auth/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    existing = get_user_by_email(email)
    if existing:
        return jsonify({"error": "User already exists"}), 409

    password_hash = hash_password(password)
    user = create_user(name, email, password_hash, "local")

    return jsonify({
        "message": "Signup successful",
        "user_id": user["id"]
    }), 201

# 4. LOGOUT
@app.route("/auth/logout", methods=["POST"])
def logout():
    response = make_response(jsonify({"message": "Logged out"}))
    response.set_cookie("auth_token", "", expires=0)
    return response

# --- GOOGLE OAUTH ---
@app.route("/auth/google")
def google_login():
    print("DEBUG GOOGLE_REDIRECT_URI:", GOOGLE_REDIRECT_URI)

    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = requests.Request(
        "GET",
        authorization_endpoint,
        params={
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": "openid email profile",
            "response_type": "code"
        }
    ).prepare().url

    print("DEBUG AUTH URL:", request_uri)
    return redirect(request_uri)

@app.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # # Get Tokens
    # token_url, headers, body = requests.Request(
    #     "POST",
    #     token_endpoint,
    #     data={
    #         "code": code,
    #         "client_id": GOOGLE_CLIENT_ID,
    #         "client_secret": GOOGLE_CLIENT_SECRET,
    #         "redirect_uri": GOOGLE_REDIRECT_URI,
    #         "grant_type": "authorization_code",
    #     },
    # ).prepare().url, None, None # This simple way works better with 'requests.post'
    
    token_response = requests.post(
    token_endpoint,
    data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    tokens = token_response.json()

    id_token = tokens.get("id_token")
    
    # Helper to decode without verification for simplicity in demo
    # In production use library verification
    user_info = jwt.decode(id_token, options={"verify_signature": False})
    
    email = user_info["email"]
    name = user_info.get("name", email.split("@")[0])
    sub = user_info["sub"] # Google ID
    
    user = get_user_by_email(email)
    if not user:
        user = create_user(name, email, None, "google", sub)
    
    # Create Session
    app_token = create_token(user['id'])
    
    # Redirect to Frontend Dashboard with token in query param (so frontend can extract and store in localStorage)
    # Note: In production, consider a secure cookie or a temporary code exchange to avoid token in URL.
    # For this request "Merge Google login + manual login" and "localStorage", passing via URL is the simplest bridge.
    frontend_url = f"{APP_URI}/dashboard?token={app_token}"
    response = make_response(redirect(frontend_url))
    # We also set the cookie as backup/hybrid
    response.set_cookie("auth_token", app_token, httponly=True, secure=False, samesite="Lax", max_age=60*60*24*7)
    return response

# --- MICROSOFT OAUTH ---
@app.route("/auth/microsoft")
def microsoft_login():
    if not MICROSOFT_CLIENT_ID:
        print("Error: MICROSOFT_CLIENT_ID is missing. Please check backend/.env")
        return jsonify({"error": "Microsoft Auth not configured. Missing MICROSOFT_CLIENT_ID in .env"}), 500
        
    auth_url = f"{MICROSOFT_AUTHORITY}/oauth2/v2.0/authorize"
    params = {
        "client_id": MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "scope": "User.Read openid profile email",
        "response_mode": "query"
    }
    url = requests.Request('GET', auth_url, params=params).prepare().url
    return redirect(url)

@app.route("/auth/microsoft/callback")
def microsoft_callback():
    code = request.args.get("code")
    token_url = f"{MICROSOFT_AUTHORITY}/oauth2/v2.0/token"
    
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": MICROSOFT_REDIRECT_URI,
        "client_id": MICROSOFT_CLIENT_ID,
        "client_secret": MICROSOFT_CLIENT_SECRET,
    }
    
    r = requests.post(token_url, data=token_data)
    tokens = r.json()
    access_token = tokens.get("access_token")
    
    # Get Profile
    profile_r = requests.get("https://graph.microsoft.com/v1.0/me", headers={'Authorization': 'Bearer ' + access_token})
    profile = profile_r.json()
    
    email = profile.get("mail") or profile.get("userPrincipalName")
    name = profile.get("displayName")
    ms_id = profile.get("id")
    
    user = get_user_by_email(email)
    if not user:
        user = create_user(name, email, None, "microsoft", ms_id)
        
    app_token = create_token(user['id'])
    
    # Redirect with token
    frontend_url = f"{APP_URI}/dashboard?token={app_token}"
    response = make_response(redirect(frontend_url))
    response.set_cookie("auth_token", app_token, httponly=True, secure=False, samesite="Lax", max_age=60*60*24*7)
    return response

@app.route("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        return "Database connected successfully!"
    except Exception as e:
        return f"Database connection failed: {e}", 500

def map_inputs(data):
    return {
        "Product_Weight": float(data["product_weight"]),
        "Strength": float(data["strength_required"]),
        "Moisture_Level": {
            "low": 0,
            "medium": 1,
            "high": 2
        }[data["moisture_level"]],
        "Budget_Level": {
            "low": 0,
            "medium": 1,
            "high": 2
        }[data["budget_level"]],
        "Durability": float(data["durability_score"])
    }

def prepare_ml_features(input_data, material):
    features = {col: 0 for col in feature_columns}

    # ---------- STRONG USER SIGNALS ----------
    units = float(input_data.get("No_of_Units", 1))
    quantity = float(input_data.get("Product_Quantity", 1))
    strength = float(input_data.get("Strength", 50))
    moisture = float(input_data.get("Moisture_Barrier", 5))

    # amplify effect (THIS is key)
    features["No_of_Units"] = units
    features["Product_Quantity"] = quantity
    features["Strength_MPa"] = strength * units
    features["Moisture_Barrier"] = moisture * quantity

    # ---------- MATERIAL DIFFERENTIATION ----------
    material_profile = {
        "Glass": (1.2, 1.4),
        "Recycled Paper": (0.6, 0.5),
        "Bio-Plastic": (0.9, 0.7),
        "Aluminum": (1.1, 1.3)
    }

    cost_mult, co2_mult = material_profile.get(material, (1.0, 1.0))

    if "Cost_Efficiency_Index" in features:
        features["Cost_Efficiency_Index"] = quantity * cost_mult
    if "Sustainability_Score" in features:
        features["Sustainability_Score"] = (strength / 10) * co2_mult

    # ---------- ONE-HOT ----------
    country = input_data.get("Country_Tag", "india").lower()
    country_col = f"Countries_Tags_en:{country}"
    if country_col in features:
        features[country_col] = 1

    shape = input_data.get("Shape", "").capitalize()
    shape_col = f"Shape_{shape}"
    if shape_col in features:
        features[shape_col] = 1

    material_col = f"Material_{material}"
    if material_col in features:
        features[material_col] = 1

    return features

# --- PREDICTION ---
@app.route("/predict", methods=["POST"])
@token_required
def predict(current_user_id):
    try:
        input_data = request.get_json()
        print("🔍 INPUT DATA RECEIVED:", input_data)

        candidate_materials = [
            "Glass",
            "Recycled Paper",
            "Bio-Plastic",
            "Aluminum"
        ]

        results = []

        for material in candidate_materials:
            # 1️⃣ Prepare ML features from FRONTEND input
            feature_dict = prepare_ml_features(input_data, material)

            X = pd.DataFrame([feature_dict])
            X_scaled = scaler.transform(X)

            # 2️⃣ ML predictions
            predicted_cost = float(cost_model.predict(X_scaled)[0])
            predicted_co2 = float(co2_model.predict(X_scaled)[0])

            results.append({
                "Material": material,
                "Predicted_Cost": predicted_cost,
                "Predicted_CO2": predicted_co2,
                "AI_Recommendation": "ML-based Recommendation"
            })

        # 3️⃣ COMPOSITE DECISION SCORE (CRITICAL FIX)
        for r in results:
            r["Decision_Score"] = (
                0.6 * r["Predicted_CO2"] +
                0.4 * r["Predicted_Cost"]
            )

        # 4️⃣ USE-CASE LOGIC (optional but powerful)
        shape = input_data.get("Shape", "")
        strength = float(input_data.get("Strength", 50))
        quantity = float(input_data.get("Product_Quantity", 1))

        if shape == "Box" and strength < 30:
            results = [r for r in results if r["Material"] != "Glass"]

        if quantity > 800:
            for r in results:
                if r["Material"] == "Recycled Paper":
                    r["Decision_Score"] *= 0.85  # reward paper at scale

        # 5️⃣ FINAL SORTING
        results.sort(key=lambda x: x["Decision_Score"])

        # 6️⃣ ADD RANK
        for i, r in enumerate(results):
            r["Rank"] = i + 1

        top_result = results[0]

        # --- SAVE TO DB (HISTORY) ---
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO predictions (
                    user_id,
                    product_name,
                    shape,
                    country,
                    product_quantity,
                    no_of_units,
                    strength_mpa,
                    moisture_barrier,
                    recommended_material,
                    predicted_cost,
                    predicted_co2,
                    ai_recommendation
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                current_user_id,
                input_data.get("Product_Name"),
                input_data.get("Shape"),
                input_data.get("Country_Tag", "").lower(),
                input_data.get("Product_Quantity"),
                input_data.get("No_of_Units"),
                input_data.get("Strength"),
                input_data.get("Moisture_Barrier"),
                top_result["Material"],
                top_result["Predicted_Cost"],
                top_result["Predicted_CO2"],
                "Highly Recommended"
            ))

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print("❌ DB CONNECTION ERROR:", e)
            return None

            # Don't fail the request just because history save failed, but log it.

        # 7️⃣ RESPONSE TO FRONTEND
        return jsonify({
            "recommended_material": top_result["Material"],
            "predicted_cost": round(top_result["Predicted_Cost"], 2),
            "predicted_co2": round(top_result["Predicted_CO2"], 2),
            "ai_recommendation": "Highly Recommended",
            "top_3_alternatives": [
                {
                    "Material": r["Material"],
                    "Predicted_Cost": round(r["Predicted_Cost"], 2),
                    "Predicted_CO2": round(r["Predicted_CO2"], 2),
                    "Rank": r["Rank"],
                    "AI_Recommendation": r["AI_Recommendation"]
                }
                for r in results[:3]
            ]
        })

    except Exception as e:
        print("PREDICTION ERROR:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/history", methods=["GET"])
@token_required
def get_history(current_user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT * FROM predictions
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (current_user_id,))
        history = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(history)
    except Exception as e:
        print("History Fetch Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/predictions", methods=["GET"])
@token_required
def get_predictions(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            product_name,
            shape,
            country,
            product_quantity,
            no_of_units,
            strength_mpa,
            moisture_barrier,
            recommended_material,
            predicted_cost,
            predicted_co2,
            created_at
        FROM predictions
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (current_user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    predictions = []
    for r in rows:
        predictions.append({
            "product_name": r[0],
            "shape": r[1],
            "country": r[2],
            "product_quantity": r[3],
            "no_of_units": r[4],
            "strength_mpa": r[5],
            "moisture_barrier": r[6],
            "recommended_material": r[7],
            "predicted_cost": float(r[8]),
            "predicted_co2": float(r[9]),
            "created_at": r[10].isoformat()
        })

    return jsonify(predictions)

@app.route("/api/analytics/material-summary", methods=["GET"])
@token_required
def material_summary(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            recommended_material,
            COUNT(*) AS total_predictions,
            AVG(predicted_co2) AS avg_co2,
            AVG(predicted_cost) AS avg_cost
        FROM predictions
        WHERE user_id = %s
        GROUP BY recommended_material
        ORDER BY total_predictions DESC
    """, (current_user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "material": r[0],
            "count": r[1],
            "avg_co2": round(float(r[2]), 2),
            "avg_cost": round(float(r[3]), 2)
        })

    return jsonify(result)

@app.route("/api/analytics/co2-trend", methods=["GET"])
@token_required
def co2_trend(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            DATE(created_at) AS date,
            AVG(predicted_co2) AS avg_co2
        FROM predictions
        WHERE user_id = %s
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """, (current_user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "date": r[0].isoformat(),
            "avg_co2": round(float(r[1]), 2)
        }
        for r in rows
    ])

@app.route("/api/analytics/cost-summary", methods=["GET"])
@token_required
def cost_summary(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            recommended_material,
            AVG(predicted_cost) AS avg_cost
        FROM predictions
        WHERE user_id = %s
        GROUP BY recommended_material
    """, (current_user_id,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify([
        {
            "material": r[0],
            "avg_cost": round(float(r[1]), 2)
        }
        for r in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
