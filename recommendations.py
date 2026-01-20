from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Material, Product, Recommendation
import traceback

recommendations_bp = Blueprint("recommendations", __name__)

# ================= AI SCORING ================= #
def calculate_score(material, product):
    """
    Dynamic score (0–10) based on product attributes.
    """
    # Default Weights (Balanced)
    w_bio = 0.20
    w_recyc = 0.20
    w_strength = 0.20
    w_co2 = 0.20
    w_cost = 0.20

    # Adjust based on Fragility (1-10)
    if product.fragility_level >= 7:
        w_strength = 0.40  # Critical for fragile items
        w_cost = 0.10
        w_co2 = 0.10
    elif product.fragility_level <= 3:
        w_strength = 0.05  # Not important
        w_cost = 0.35      # Prioritize cost
        w_co2 = 0.20

    # Normalize sub-scores to 0-10 scale
    s_bio = material.biodegradability_score
    s_recyc = material.recyclability_percent / 10.0
    s_strength = material.strength_rating
    
    # Inverse metrics (Lower is better)
    s_co2 = max(0, 10 - (material.co2_emission_score * 3.3)) # 3.0 co2 -> 0 score
    s_cost = max(0, 10 - (material.cost_per_kg * 1.25))      # 8.0 cost -> 0 score

    score = (
        s_bio * w_bio + s_recyc * w_recyc + s_strength * w_strength +
        s_co2 * w_co2 + s_cost * w_cost
    )
    return max(0, min(score, 10))


def normalize_score(score_10):
    """
    Convert 0–10 → 0–1 (frontend multiplies by 100)
    """
    return round(score_10 / 10, 3)


# ================= ENVIRONMENTAL IMPACT ================= #
def calculate_environmental_impact(material):
    baseline_co2 = 3.0
    baseline_cost = 3.5

    co2_reduction = max(
        0, ((baseline_co2 - material.co2_emission_score) / baseline_co2) * 100
    )

    cost_savings = max(
        0, ((baseline_cost - material.cost_per_kg) / baseline_cost) * 100
    )

    return round(co2_reduction, 2), round(cost_savings, 2)


# ================= RECOMMEND ================= #
@recommendations_bp.route("/recommend", methods=["POST"])
@jwt_required()
def recommend_materials():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        product = Product(
            user_id=user_id,
            product_name=data["product_name"].strip(),
            category=data["category"].strip(),
            weight_kg=float(data["weight_kg"]),
            fragility_level=int(data["fragility_level"]),
            temperature_sensitive=bool(data.get("temperature_sensitive", False))
        )

        db.session.add(product)
        db.session.flush()

        materials = Material.query.all()
        results = []

        for m in materials:
            raw_score = calculate_score(m, product)
            score = normalize_score(raw_score)
            co2, cost = calculate_environmental_impact(m)

            results.append({
                "material_id": m.id,
                "material_name": m.material_name,
                "score": score,                      # ✅ 0–1
                "co2": co2,
                "cost": cost,
                "recyclability": m.recyclability_percent,
                "strength": m.strength_rating,
                "costkg": m.cost_per_kg
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        top = results[0]

        db.session.add(Recommendation(
            user_id=user_id,
            product_id=product.id,
            material_id=top["material_id"],
            recommendation_score=top["score"],      # ✅ stored normalized
            co2_reduction_percent=top["co2"],
            cost_savings_percent=top["cost"]
        ))

        db.session.commit()

        return jsonify({
            "product_id": product.id,
            "recommendations": results
        }), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ================= HISTORY (FIXED) ================= #
@recommendations_bp.route("/history", methods=["GET"])
@jwt_required()
def recommendation_history():
    user_id = int(get_jwt_identity())

    recs = Recommendation.query.filter_by(
        user_id=user_id
    ).order_by(Recommendation.created_at.desc()).all()

    history = []
    for r in recs:
        history.append({
            "material_name": r.material.material_name,
            "date": r.created_at.strftime("%Y-%m-%d"),
            "recommendation_score": r.recommendation_score,   # ✅ frontend expects this
            "co2_reduction_percent": r.co2_reduction_percent,
            "cost_savings_percent": r.cost_savings_percent,
            "material_details": {                              # ✅ REQUIRED
                "recyclability_percent": r.material.recyclability_percent,
                "strength_rating": r.material.strength_rating,
                "cost_per_kg": r.material.cost_per_kg
            }
        })

    return jsonify({
        "total": len(history),
        "recommendations": history
    }), 200


# ================= COMPARE MATERIALS ================= #
@recommendations_bp.route("/compare", methods=["POST"])
@jwt_required()
def compare_materials():
    data = request.get_json()
    material_ids = data.get("material_ids", [])
    
    if not material_ids:
        return jsonify({"error": "No material IDs provided"}), 400
        
    materials = Material.query.filter(Material.id.in_(material_ids)).all()
    
    comparison = []
    for m in materials:
        comparison.append({
            "id": m.id,
            "name": m.material_name,
            "eco_score": m.calculate_eco_score(),
            "co2_emission": m.co2_emission_score,
            "recyclability": m.recyclability_percent,
            "cost_per_kg": m.cost_per_kg,
            "strength": m.strength_rating
        })
        
    return jsonify({"comparison": comparison}), 200


# ================= ENV SCORE DETAILS ================= #
@recommendations_bp.route("/environmental-score", methods=["POST"])
@jwt_required()
def environmental_score_details():
    # Returns the formula/weights used for calculation
    return jsonify({
        "formula": "Weighted average of 5 key sustainability factors",
        "weights": {
            "biodegradability": 0.30,
            "recyclability": 0.25,
            "strength": 0.25,
            "co2_emission": -0.10,
            "cost": -0.10
        },
        "scale": "0-10 (Normalized to 0-100%)"
    }), 200


# ================= MATERIAL LIST ================= #
@recommendations_bp.route("/materials", methods=["GET"])
def list_materials():
    materials = Material.query.all()

    return jsonify({
        "materials": [
            {
                "id": m.id,
                "material_name": m.material_name,
                "eco_score": m.calculate_eco_score(),
                "cost_per_kg": m.cost_per_kg
            } for m in materials
        ],
        "total": len(materials)
    }), 200
