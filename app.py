from flask import (
    Flask, render_template, request,
    redirect, session, flash,
    jsonify, send_file
)
import os, io, base64, csv, warnings
import numpy as np
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from psycopg2.extras import RealDictCursor
from db import create_user, authenticate_user, get_db_connection

warnings.filterwarnings("ignore")

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key")

MODEL_PATH = "model"

# ---------------- MATERIAL RULES ----------------
MATERIAL_RULES = {
    "Kraft Paper Foam": {"cost_per_kg": 59.0, "co2_per_kg": 7.53},
    "Recycled Plastic": {"cost_per_kg": 51.4, "co2_per_kg": 7.62},
    "Reinforced Fiber": {"cost_per_kg": 51.8, "co2_per_kg": 7.11},
    "Honeycomb Paperboard": {"cost_per_kg": 57.3, "co2_per_kg": 7.18},
    "Molded Pulp": {"cost_per_kg": 53.2, "co2_per_kg": 7.47},
    "Bio-based Plastic": {"cost_per_kg": 51.4, "co2_per_kg": 7.62},
    "Eco-Board Plastic": {"cost_per_kg": 51.4, "co2_per_kg": 7.62},
    "Reinforced Pulp": {"cost_per_kg": 51.8, "co2_per_kg": 7.11}
}

# ---------------- RECOMMENDATION LOGIC ----------------
def get_recommendation(weight, fragility, dimensions, strength):
    scores = {m: 0.4 for m in MATERIAL_RULES}

    for material in scores:
        if fragility >= 8 and "Foam" in material:
            scores[material] += 0.2
        if weight > 1000 and "Paperboard" in material:
            scores[material] += 0.15
        if strength >= 8 and "Reinforced" in material:
            scores[material] += 0.2

    return max(scores, key=scores.get)

# ---------------- CHARTS ----------------
def create_material_chart(history):
    materials = [h["recommended_material"] for h in history]
    counts = Counter(materials)

    plt.figure(figsize=(6, 4))
    plt.pie(counts.values(), labels=counts.keys(), autopct="%1.1f%%")
    img = io.BytesIO()
    plt.savefig(img, format="png")
    plt.close()
    img.seek(0)

    return base64.b64encode(img.getvalue()).decode()

def create_cost_chart(history):
    costs = [float(h["predicted_cost"]) for h in history]

    plt.figure(figsize=(6, 4))
    plt.plot(costs, marker="o")
    plt.xlabel("Prediction Count")
    plt.ylabel("Cost (₹)")
    plt.grid(True)
    img = io.BytesIO()
    plt.savefig(img, format="png")
    plt.close()
    img.seek(0)

    return base64.b64encode(img.getvalue()).decode()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- AUTH ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = authenticate_user(
            request.form["username_or_email"],
            request.form["password"]
        )
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")
        flash("Invalid credentials")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        success = create_user(
            request.form["username"],
            request.form["email"],
            request.form["password"]
        )
        if success:
            return redirect("/login")
        flash("User already exists")

    return render_template("signup.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    if not conn:
        return render_template(
            "dashboard.html",
            stats={"total": 0, "avg_cost": 0, "avg_co2": 0, "materials": []},
            material_chart=None,
            cost_chart=None
        )

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM predictions WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    history = cur.fetchall()
    cur.close()
    conn.close()

    stats = {
        "total": len(history),
        "avg_cost": np.mean([h["predicted_cost"] for h in history]) if history else 0,
        "avg_co2": np.mean([h["predicted_co2"] for h in history]) if history else 0,
        "materials": [h["recommended_material"] for h in history]
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        material_chart=create_material_chart(history) if history else None,
        cost_chart=create_cost_chart(history) if history else None
    )

# ---------------- PREDICTION ----------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        weight = float(request.form["weight"])
        fragility = float(request.form["fragility"])
        dimensions = float(request.form["dimensions"])
        strength = float(request.form["strength"])
        product = request.form["product"]

        material = get_recommendation(weight, fragility, dimensions, strength)
        cost = MATERIAL_RULES[material]["cost_per_kg"] * (weight / 1000)
        co2 = MATERIAL_RULES[material]["co2_per_kg"] * (weight / 1000)

        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO predictions
                (user_id, product_category, weight_g, fragility_level,
                 dimensions_cm, strength, predicted_cost,
                 predicted_co2, recommended_material)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                session["user_id"], product, weight, fragility,
                dimensions, strength, cost, co2, material
            ))
            conn.commit()
            cur.close()
            conn.close()

        return render_template("result.html", prediction={
            "product": product,
            "weight_g": weight,
            "fragility_level": fragility,
            "dimensions_cm": dimensions,
            "strength": strength,
            "recommended_material": material,
            "predicted_cost": f"{cost:.2f}",
            "predicted_co2": f"{co2:.2f}"
        })

    return render_template("predict.html")

# ---------------- API ----------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json
    material = get_recommendation(
        data["weight"],
        data["fragility"],
        data["dimensions"],
        data["strength"]
    )
    return jsonify({
        "recommended_material": material,
        "predicted_cost": MATERIAL_RULES[material]["cost_per_kg"],
        "predicted_co2": MATERIAL_RULES[material]["co2_per_kg"]
    })

# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    if not conn:
        return render_template("history.html", history=[])

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT * FROM predictions WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for r in rows:
        r["created_at"] = r["created_at"].strftime("%Y-%m-%d %H:%M")

    return render_template("history.html", history=rows)

# ---------------- CSV EXPORT ----------------
@app.route("/export/csv")
def export_csv():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    if not conn:
        return redirect("/history")

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM predictions WHERE user_id=%s", (session["user_id"],))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return redirect("/history")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys())
    for row in rows:
        writer.writerow(row.values())

    mem = io.BytesIO(output.getvalue().encode())
    mem.seek(0)

    return send_file(
        mem,
        as_attachment=True,
        download_name="EcoPackAI_Report.csv",
        mimetype="text/csv"
    )

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- ENTRY ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)