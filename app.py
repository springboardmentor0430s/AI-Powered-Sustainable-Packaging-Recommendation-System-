from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"
DB_NAME = "history.db"


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            product_type TEXT,
            material_category TEXT,
            strength INTEGER,
            weight_capacity INTEGER,
            bio_score INTEGER,
            recycle_percent INTEGER,
            result TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["username"] = "Admin"
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("index.html", username=session["username"])


# ---------- PREDICTION ----------
@app.route("/predict_form", methods=["POST"])
def predict_form():
    if "username" not in session:
        return redirect("/")

    f = request.form

    # ---------- AI MOCK PREDICTIONS ----------
    predicted_cost = round(50 + int(f["Strength"]) * 0.2, 2)
    predicted_co2 = round(30 + int(f["Bio Score"]) * 0.15, 2)
    environmental_score = round(0.4 * predicted_cost + 0.6 * predicted_co2, 2)

    if environmental_score >= 80:
        grade = "A"
    elif environmental_score >= 60:
        grade = "B"
    elif environmental_score >= 40:
        grade = "C"
    else:
        grade = "D"

    # ---------- MATERIAL COMPARISON (FIXED) ----------
    materials = [
        {"name": "Plastic Packaging", "co2": 90, "cost": 80},
        {"name": "Kraft Paper", "co2": 45, "cost": 55},
        {"name": "Corrugated Box", "co2": 60, "cost": 65},
        {"name": "Biodegradable Film", "co2": 35, "cost": 70}
    ]

    # ---------- BEST MATERIAL ----------
    best_index = min(range(len(materials)), key=lambda i: materials[i]["co2"])
    recommended = materials[best_index]["name"]

    # ---------- SAVE TO HISTORY ----------
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO history
        (username, product_type, material_category, strength, weight_capacity, bio_score, recycle_percent, result, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["username"],
        f["Type"],
        f["material_category"],
        int(f["Strength"]),
        int(f["Weight Capacity"]),
        int(f["Bio Score"]),
        int(f["recycle_percent"]),
        recommended,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    # ---------- SEND DATA TO RESULT PAGE ----------
    return render_template(
        "result.html",
        type=f["Type"],
        material_category=f["material_category"],
        strength=f["Strength"],
        weight_capacity=f["Weight Capacity"],
        bio_score=f["Bio Score"],
        recycle_percent=f["recycle_percent"],
        cost=predicted_cost,
        co2=predicted_co2,
        score=environmental_score,
        sustainability_grade=grade,
        materials=materials,
        best_index=best_index
    )


# ---------- HISTORY ----------
@app.route("/history")
def history():
    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    return render_template("history.html", history=rows)


# ---------- BI DASHBOARD ----------
@app.route("/bi")
def bi():
    if "username" not in session:
        return redirect("/")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT bio_score, recycle_percent FROM history")
    rows = c.fetchall()
    conn.close()

    total = len(rows)
    avg_bio = round(sum(r[0] for r in rows) / total, 2) if total else 0
    avg_recycle = round(sum(r[1] for r in rows) / total, 2) if total else 0

    return render_template(
        "bi.html",
        total=total,
        avg_bio=avg_bio,
        avg_recycle=avg_recycle
    )


if __name__ == "__main__":
    app.run(debug=True)
