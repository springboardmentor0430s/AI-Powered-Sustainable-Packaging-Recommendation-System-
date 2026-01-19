from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from recommendation import get_top_recommendations

app = Flask(__name__)
CORS(app)

# ---------------- DATABASE CONNECTION ----------------
conn = psycopg2.connect(
    dbname="ecopackai",
    user="postgres",
    password="anits",   # change if needed
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# ---------------- RECOMMEND API ----------------
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()

        result = get_top_recommendations(
            product_weight=data["product_weight"],
            fragility_level=data["fragility_level"],
            is_liquid=data["is_liquid"],
            premium_level=data["premium_level"],
            eco_priority=data["eco_priority"],
            top_k=3
        )

        best = result["best_material"]
        top3 = result["top_3_materials"]

        # Save history safely
        cursor.execute("""
            INSERT INTO recommendation_history
            (product_form, fragility_level, eco_priority,
             premium_level, best_material, top_3_materials)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data.get("product_form", "Unknown"),
            data["fragility_level"],
            data["eco_priority"],
            data["premium_level"],
            best["material_name"],
            ", ".join([m["material_name"] for m in top3])
        ))
        conn.commit()

        return jsonify({
            "best_material": best,
            "top_3_materials": top3
        })

    except Exception as e:
        print("❌ BACKEND ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ---------------- HISTORY API ----------------
@app.route("/history", methods=["GET"])
def history():
    try:
        cursor.execute("""
            SELECT product_form, fragility_level, eco_priority,
                   premium_level, best_material,
                   top_3_materials, created_at
            FROM recommendation_history
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        history_data = []
        for r in rows:
            history_data.append({
                "product_form": r[0],
                "fragility_level": r[1],
                "eco_priority": r[2],
                "premium_level": r[3],
                "best_material": r[4],
                "top_3_materials": r[5],
                "time": r[6].strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({"history": history_data})

    except Exception as e:
        print("❌ HISTORY ERROR:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
