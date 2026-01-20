import pandas as pd
import plotly.express as px
from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

from models import Recommendation

analytics_bp = Blueprint("analytics", __name__)

# ======================================================
# DASHBOARD API
# ======================================================
@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    user_id = int(get_jwt_identity())
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    if not recs:
        return jsonify({
            "metrics": {
                "total_recommendations": 0,
                "avg_co2_reduction": 0,
                "avg_cost_savings": 0,
                "top_material": "N/A"
            },
            "charts": {}
        }), 200

    data = []
    for r in recs:
        data.append({
            "material": r.material.material_name if r.material else "Unknown",
            "co2": float(r.co2_reduction_percent or 0),
            "cost": float(r.cost_savings_percent or 0),
            "date": r.created_at.strftime("%Y-%m-%d")
        })

    df = pd.DataFrame(data)

    usage = df["material"].value_counts().reset_index()
    usage.columns = ["material", "count"]

    metrics = {
        "total_recommendations": int(len(df)),
        "avg_co2_reduction": round(float(df["co2"].mean() or 0), 1),
        "avg_cost_savings": round(float(df["cost"].mean() or 0), 1),
        "top_material": usage.iloc[0]["material"] if not usage.empty else "N/A"
    }

    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#444"}
    }

    charts = {
        "material_usage": px.pie(
            usage, names="material", values="count",
            title="Material Usage Distribution"
        ).update_layout(**layout).to_dict(),

        "co2_trend": px.line(
            df, x="date", y="co2",
            title="CO₂ Reduction Trend"
        ).update_layout(**layout).to_dict(),

        "cost_trend": px.line(
            df, x="date", y="cost",
            title="Cost Savings Trend"
        ).update_layout(**layout).to_dict()
    }

    return jsonify({"metrics": metrics, "charts": charts}), 200


# ======================================================
# EXPORT CSV
# ======================================================
@analytics_bp.route("/export/csv", methods=["GET"])
@jwt_required()
def export_csv():
    user_id = int(get_jwt_identity())
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    if not recs:
        return jsonify({"error": "No data"}), 400

    df = pd.DataFrame([{
        "Material": r.material.material_name if r.material else "Unknown",
        "CO2 Reduction (%)": r.co2_reduction_percent or 0,
        "Cost Savings (%)": r.cost_savings_percent or 0,
        "Date": r.created_at.strftime("%Y-%m-%d")
    } for r in recs])

    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    return send_file(buf, as_attachment=True,
                     download_name="EcoPackAI_Report.csv",
                     mimetype="text/csv")


# ======================================================
# EXPORT EXCEL
# ======================================================
@analytics_bp.route("/export/excel", methods=["GET"])
@jwt_required()
def export_excel():
    user_id = int(get_jwt_identity())
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    if not recs:
        return jsonify({"error": "No data"}), 400

    df = pd.DataFrame([{
        "Material": r.material.material_name if r.material else "Unknown",
        "CO2 Reduction (%)": r.co2_reduction_percent or 0,
        "Cost Savings (%)": r.cost_savings_percent or 0,
        "Date": r.created_at.strftime("%Y-%m-%d")
    } for r in recs])

    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)

    return send_file(buf, as_attachment=True,
                     download_name="EcoPackAI_Report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ======================================================
# EXPORT PDF (POLISHED)
# ======================================================
@analytics_bp.route("/export/pdf", methods=["GET"])
@jwt_required()
def export_pdf():
    user_id = int(get_jwt_identity())
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    if not recs:
        return jsonify({"error": "No data"}), 400

    buf = io.BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("EcoPackAI – Sustainability Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    summary = Table([
        ["Total Recommendations", len(recs)],
        ["Average CO₂ Reduction (%)",
         round(sum(r.co2_reduction_percent or 0 for r in recs)/len(recs), 2)],
        ["Average Cost Savings (%)",
         round(sum(r.cost_savings_percent or 0 for r in recs)/len(recs), 2)]
    ])

    summary.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER")
    ]))

    elements.append(summary)
    elements.append(Spacer(1, 20))

    table_data = [["Material", "CO₂ Reduction (%)", "Cost Savings (%)", "Date"]]
    for r in recs:
        table_data.append([
            r.material.material_name if r.material else "Unknown",
            round(r.co2_reduction_percent or 0, 2),
            round(r.cost_savings_percent or 0, 2),
            r.created_at.strftime("%Y-%m-%d")
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#198754")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER")
    ]))

    elements.append(table)
    pdf.build(elements)
    buf.seek(0)

    return send_file(buf, as_attachment=True,
                     download_name="EcoPackAI_Report.pdf",
                     mimetype="application/pdf")


# ======================================================
# MATERIAL INSIGHTS
# ======================================================
@analytics_bp.route("/insights/materials", methods=["GET"])
@jwt_required()
def material_insights():
    user_id = int(get_jwt_identity())
    recs = Recommendation.query.filter_by(user_id=user_id).all()

    stats = {}

    for r in recs:
        name = r.material.material_name if r.material else "Unknown"
        stats.setdefault(name, {"count": 0, "co2": 0, "cost": 0, "score": []})
        stats[name]["count"] += 1
        stats[name]["co2"] += r.co2_reduction_percent or 0
        stats[name]["cost"] += r.cost_savings_percent or 0

        score = r.recommendation_score or 0
        if score > 10:
            score /= 10
        elif score <= 1:
            score *= 10

        stats[name]["score"].append(score)

    insights = [{
        "material": k,
        "usage_count": v["count"],
        "avg_co2_reduction": round(v["co2"]/v["count"], 2),
        "avg_cost_savings": round(v["cost"]/v["count"], 2),
        "avg_score": round(sum(v["score"])/len(v["score"]), 2)
    } for k, v in stats.items()]

    insights.sort(key=lambda x: x["usage_count"], reverse=True)
    return jsonify({"insights": insights}), 200
