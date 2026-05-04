from flask import Flask, render_template, request, redirect, session
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.secret_key = "secret123"

# ===== LOGIN =====
VALID_EMAIL = "mishrayashashree@gmail.com"
VALID_PASSWORD = "Mishra@123"

# ===== MEMORY =====
history_data = []

# ===== ML MODEL =====
X = np.array([[500,25,70],[1000,50,60],[200,10,90]])
y_cost = np.array([88,120,60])
y_co2 = np.array([34,50,20])

cost_model = LinearRegression().fit(X, y_cost)
co2_model = LinearRegression().fit(X, y_co2)

# ===== LOGIN =====
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["email"] == VALID_EMAIL and request.form["password"] == VALID_PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)


# ===== DASHBOARD =====
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not session.get("logged_in"):
        return redirect("/")

    result = None
    error = None
    form_data = session.get("last_input", {})

    if request.method == "POST":
        try:
            qty = float(request.form["quantity"])
            wt = float(request.form["weight"])
            rec = float(request.form["recycle"])

            material = request.form["material"]
            shape = request.form["shape"]
            strength = request.form["strength"]
            food = request.form["food"]

            # SAVE INPUT
            form_data = request.form.to_dict()
            session["last_input"] = form_data

            # ===== ML PREDICTION =====
            arr = np.array([[qty, wt, rec]])
            base_cost = cost_model.predict(arr)[0]
            base_co2 = co2_model.predict(arr)[0]

            # ===== FACTORS =====
            material_factor = {"Plastic":1.2,"Glass":1.5,"Paper":0.8,"Metal":1.3}.get(material,1)
            shape_factor = {"Box":1,"Bottle":1.2,"Can":1.1,"Pouch":0.9}.get(shape,1)
            strength_factor = {"Low":0.8,"Medium":1,"High":1.3}.get(strength,1)

            cost = base_cost * material_factor * shape_factor * strength_factor
            co2 = base_co2 * material_factor

            # ===== IMPACT ANALYSIS =====
            impact = []

            if wt > 100:
                impact.append("📦 Higher weight increased cost")

            if rec < 50:
                impact.append("♻️ Low recyclability increased environmental impact")

            if material == "Plastic":
                impact.append("🧴 Plastic increased CO₂ emissions")

            if strength == "High":
                impact.append("💪 High strength requirement increased cost")

            if not impact:
                impact.append("✅ Efficient packaging selection")

            # ===== SMART RECOMMENDATION =====
            if rec >= 80:
                best = "Recycled Paper"
                reason = "High recyclability → eco-friendly paper works best"

            elif material == "Plastic" and rec < 50:
                best = "Bioplastic"
                reason = "Low recyclability plastic → switch to biodegradable option"

            elif wt > 150:
                best = "Reinforced Cardboard"
                reason = "Heavy packaging needs strong but sustainable material"

            elif strength == "High":
                best = "Metal Packaging"
                reason = "High strength requirement → durable metal preferred"

            elif food in ["Frozen", "Meat", "Seafood"]:
                best = "Insulated Paper + Bio-layer"
                reason = "Food safety + temperature control needed"

            else:
                best = "Molded Pulp"
                reason = "General sustainable packaging solution"

            # ===== RESULT =====
            result = {
                "cost": round(cost, 2),
                "co2": round(co2, 2),
                "best": best,
                "reason": reason,
                "impact": impact,
                "input": {
                    "material": material,
                    "shape": shape,
                    "strength": strength,
                    "food": food,
                    "quantity": qty,
                    "weight": wt,
                    "recycle": rec
                }
            }

            # ===== SAVE HISTORY =====
            history_data.append({
                "cost": round(cost,2),
                "co2": round(co2,2),
                "material": material,
                "shape": shape,
                "strength": strength,
                "food": food,
                "quantity": qty,
                "weight": wt,
                "recycle": rec
            })

        except:
            error = "Invalid input"

    # ===== GRAPH DATA =====
    costs = [h["cost"] for h in history_data]
    co2_vals = [h["co2"] for h in history_data]

    best_cost = min(costs) if costs else 0
    worst_cost = max(costs) if costs else 0
    avg_cost = sum(costs)/len(costs) if costs else 0

    best_co2 = min(co2_vals) if co2_vals else 0
    worst_co2 = max(co2_vals) if co2_vals else 0
    avg_co2 = sum(co2_vals)/len(co2_vals) if co2_vals else 0

    return render_template(
        "dashboard.html",
        result=result,
        error=error,
        costs=costs,
        co2_vals=co2_vals,
        best_cost=best_cost,
        avg_cost=avg_cost,
        worst_cost=worst_cost,
        best_co2=best_co2,
        avg_co2=avg_co2,
        worst_co2=worst_co2,
        form_data=form_data
    )


# ===== IMPACT =====
@app.route("/impact")
def impact():
    if not session.get("logged_in"):
        return redirect("/")

    if not history_data:
        return render_template("impact.html", empty=True, costs=[], co2=[])

    costs = [h["cost"] for h in history_data]
    co2 = [h["co2"] for h in history_data]

    best_cost = min(costs)
    worst_cost = max(costs)
    avg_cost = sum(costs)/len(costs)

    best_co2 = min(co2)
    worst_co2 = max(co2)
    avg_co2 = sum(co2)/len(co2)

    return render_template(
        "impact.html",
        empty=False,
        total=len(costs),
        avg_cost=avg_cost,
        avg_co2=avg_co2,
        costs=costs,
        co2=co2,
        best_cost=best_cost,
        avg_cost_val=avg_cost,
        worst_cost=worst_cost,
        best_co2=best_co2,
        avg_co2_val=avg_co2,
        worst_co2=worst_co2
    )


# ===== HISTORY =====
@app.route("/history")
def history():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("history.html", data=history_data)


# ===== LOAD FROM HISTORY =====
@app.route("/load/<int:index>")
def load(index):
    if index < len(history_data):
        session["last_input"] = history_data[index]
    return redirect("/dashboard")


# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ===== RUN =====
if __name__ == "__main__":
    app.run(debug=True)
