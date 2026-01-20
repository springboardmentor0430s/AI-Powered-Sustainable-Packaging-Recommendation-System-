import os
import io
import datetime
from flask import Flask, request, jsonify, render_template, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import joblib
import matplotlib.pyplot as plt

# ===================== APP =====================
app = Flask(__name__)
app.secret_key = os.environ.get("ECOPACK_SECRET_KEY", "ecopack_secret_key")

# ===================== DB CONFIG =====================
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:sanika06@localhost/ecopackai"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===================== LOAD MODELS =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# Load models safely with helpful error messages
try:
    rf_cost = joblib.load(os.path.join(MODEL_DIR, "rf_cost.pkl"))
    rf_co2 = joblib.load(os.path.join(MODEL_DIR, "rf_co2.pkl"))
except Exception as e:
    # If models are missing, raise a clear error on startup
    raise RuntimeError(f"Failed to load models from {MODEL_DIR}: {e}")

# ===================== DB MODELS =====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class PredictionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # User inputs
    food_category = db.Column(db.String(100))
    food_name = db.Column(db.String(100))
    strength = db.Column(db.Float)
    weight_capacity = db.Column(db.Float)
    moisture_resistance = db.Column(db.Float)
    shelf_life = db.Column(db.Float)
    food_safety = db.Column(db.Integer)
    transport_mode = db.Column(db.String(50))
    packaging_weight = db.Column(db.Float)

    # AI outputs
    material = db.Column(db.String(100))
    predicted_cost = db.Column(db.Float)
    predicted_co2 = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


print("CONNECTED TO:", app.config["SQLALCHEMY_DATABASE_URI"])

# ===================== PAGES =====================
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("register.html")

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")

    records = PredictionHistory.query.order_by(PredictionHistory.created_at.desc()).all()
    print("HISTORY RECORDS:", records)   # 👈 ADD THIS LINE

    return render_template("history.html", records=records)

@app.route("/delete/<int:record_id>", methods=["POST"])
def delete_record(record_id):
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    record = PredictionHistory.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")


@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/")
    return render_template("analytics.html")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===================== AUTH =====================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    required = ["username", "email", "password"]
    if not all(k in data and data[k] for k in required):
        return jsonify({"error": "Missing registration fields"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400

    hashed = generate_password_hash(data["password"])
    user = User(username=data["username"], email=data["email"], password_hash=hashed)
    db.session.add(user)
    db.session.commit()
    session["user"] = user.username
    return jsonify({"redirect": "/dashboard"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    if "username" not in data or "password" not in data:
        return jsonify({"error": "Missing credentials"}), 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user"] = user.username
    return jsonify({"redirect": "/dashboard"})


# ===================== HELPERS =====================
def _ensure_number(d, key, default=None):
    v = d.get(key, default)
    try:
        if v is None or v == "":
            return default
        return float(v)
    except Exception:
        return default


# ===================== AI RECOMMEND =====================
@app.route("/recommend", methods=["POST"])
def recommend():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json() or {}

    required = ["food_category", "strength", "weight_capacity", "shelf_life",
                "moisture_resistance", "food_safety", "transport_mode"]
    missing = [k for k in required if k not in payload or payload[k] == ""]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        food_category = payload["food_category"].lower()
        strength = float(payload["strength"])
        weight_capacity = float(payload["weight_capacity"])
        shelf_life = float(payload["shelf_life"])
        moisture_resistance = float(payload["moisture_resistance"])
        food_safety = int(float(payload["food_safety"]))
        transport_mode = payload["transport_mode"].lower()
        packaging_weight = payload.get("packaging_weight")
        packaging_weight = float(packaging_weight) if packaging_weight not in ("", None) else None
    except Exception as e:
        return jsonify({"error": f"Invalid input types: {e}"}), 400

    MATERIALS = {
        "Paperboard": (8, 85, 110),
        "PLA Bioplastic": (7, 65, 95),
        "Bagasse": (9, 60, 60),
        "Corrugated Cardboard": (8, 70, 140),
        "Multilayer Plastic": (2, 20, 90),
        "Glass": (3, 90, 350),
        "Aluminum": (2, 75, 200),
        "Recycled PET": (5, 80, 50)
    }

    results = []

    for material, (biodeg, recyc, default_pack_w) in MATERIALS.items():
        pack_w = packaging_weight if packaging_weight not in (None, 0) else default_pack_w

        X = pd.DataFrame([{
            "Material_Type": material,
            "Food_Category": food_category,
            "Strength": strength,
            "Weight_Capacity_kg": weight_capacity,
            "Biodegradability_Score": biodeg,
            "Recyclability_Percent": recyc,
            "Shelf_Life_Days": shelf_life,
            "Moisture_Resistance": moisture_resistance,
            "Packaging_Weight_g": pack_w,
            "Food_Safety_Compliance": food_safety
        }])

        try:
            cost = float(rf_cost.predict(X)[0])
            co2 = float(rf_co2.predict(X)[0])
        except:
            cost, co2 = 10.0, 3.5

        # ---- Base model score ----
        final_score = cost * 0.55 + co2 * 0.45

        # ---- Bakery rules ----
        if food_category == "bakery":
            if material in ("Paperboard", "Corrugated Cardboard", "Bagasse"):
                final_score -= 6
            if material == "Recycled PET":
                final_score -= 3
            if material in ("Multilayer Plastic", "Aluminum"):
                final_score += 5
            if material == "Glass":
                final_score += 4

        # ---- Beverage rules ----
        if food_category == "beverages":
            if material == "Recycled PET":
                final_score -= 4
            if material == "Aluminum":
                final_score -= 3
            if material == "Glass":
                final_score += 1
            if material in ("Paperboard", "Bagasse"):
                final_score += 6

        # ---- Meat & Ready-to-eat ----
        if food_category in ("meat and seafood", "ready to eat"):
            if material in ("Multilayer Plastic", "Aluminum"):
                final_score -= 4
            if material in ("Glass", "Paperboard"):
                final_score += 4

        # ---- Export transport ----
        if transport_mode == "export":
            if material == "Glass":
                final_score += 2
            if material == "Recycled PET":
                final_score -= 1

        results.append({
            "material": material,
            "cost": round(cost, 2),
            "co2": round(co2, 2),
            "final_score": round(final_score, 3)
        })

    ranking = sorted(results, key=lambda x: x["final_score"])
    best = ranking[0]
    top_choices = ranking[:4]

    try:
        db.session.add(PredictionHistory(
            food_category=food_category,
            food_name=payload.get("food_name"),
            strength=strength,
            weight_capacity=weight_capacity,
            moisture_resistance=moisture_resistance,
            shelf_life=shelf_life,
            food_safety=food_safety,
            transport_mode=transport_mode,
            packaging_weight=packaging_weight,
            material=best["material"],
            predicted_cost=best["cost"],
            predicted_co2=best["co2"]
        ))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("DB Error:", e)

    return jsonify({
        "recommended_material": best["material"],
        "predicted_cost": best["cost"],
        "predicted_co2": best["co2"],
        "alternatives": top_choices,
        "ranking": ranking
    })


# ===================== ANALYTICS =====================



@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")

@app.route("/analytics/data")
def analytics_data():
    records = PredictionHistory.query.all()
    data = {}
    for r in records:
        if r.material not in data:
            data[r.material] = {"cost": [], "co2": []}
        data[r.material]["cost"].append(r.predicted_cost)
        data[r.material]["co2"].append(r.predicted_co2)

    # Optionally return averages and counts for convenience
    summary = {}
    for material, vals in data.items():
        summary[material] = {
            "count": len(vals["cost"]),
            "avg_cost": float(pd.Series(vals["cost"]).mean()) if vals["cost"] else None,
            "avg_co2": float(pd.Series(vals["co2"]).mean()) if vals["co2"] else None,
            "costs": vals["cost"],
            "co2s": vals["co2"],
        }
    return jsonify(summary)


@app.route("/analytics/export/excel")
def export_excel():
    records = PredictionHistory.query.all()
    df = pd.DataFrame(
        [
            {
                "Material": r.material,
                "Cost": r.predicted_cost,
                "CO2": r.predicted_co2,
                "Time": r.created_at,
            }
            for r in records
        ]
    )

    # Write to BytesIO instead of disk
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Predictions")
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="sustainability_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/analytics/export/pdf")
def export_pdf():
    # Create a simple aggregated bar chart (avg CO2 per material)
    records = PredictionHistory.query.all()
    if not records:
        # return empty PDF with message
        buf = io.BytesIO()
        plt.figure(figsize=(6, 2))
        plt.text(0.5, 0.5, "No prediction history available", ha="center", va="center")
        plt.axis("off")
        plt.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        plt.close()
        return send_file(buf, download_name="report.pdf", as_attachment=True, mimetype="application/pdf")

    df = pd.DataFrame(
        [
            {"material": r.material, "co2": r.predicted_co2, "cost": r.predicted_cost}
            for r in records
        ]
    )
    agg = df.groupby("material").mean().reset_index()

    plt.figure(figsize=(8, 4))
    plt.bar(agg["material"], agg["co2"], color="#ef4444")
    plt.title("Average Predicted CO₂ by Material")
    plt.ylabel("CO₂ (g)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="pdf")
    buf.seek(0)
    plt.close()
    return send_file(buf, download_name="report.pdf", as_attachment=True, mimetype="application/pdf")


@app.route("/debug_insert")
def debug_insert():
    r = PredictionHistory(
        food_category="TEST",
        food_name="TEST",
        strength=1,
        weight_capacity=1,
        moisture_resistance=1,
        shelf_life=1,
        food_safety=1,
        transport_mode="local",
        packaging_weight=1,
        material="TEST",
        predicted_cost=1,
        predicted_co2=1
    )
    db.session.add(r)
    db.session.commit()
    return "Inserted"


# ===================== RUN =====================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)