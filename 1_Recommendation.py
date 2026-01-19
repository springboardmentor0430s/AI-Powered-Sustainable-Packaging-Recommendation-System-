import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.title("📦 Sustainable Packaging Recommendation")

if "history" not in st.session_state:
    st.session_state["history"] = []

product_form = st.selectbox(
    "Cosmetic Product Form",
    ["Cream", "Lotion", "Gel", "Serum", "Powder", "Solid Stick", "Perfume", "Liquid"]
)

fragility = st.selectbox("Product Fragility", ["Low", "Medium", "High"])

product_weight = st.slider("Product Weight (kg)", 0.1, 2.0, 0.3)

brand_positioning = st.selectbox(
    "Brand Positioning", ["Budget", "Standard", "Premium"]
)

sustainability_priority = st.selectbox(
    "Sustainability Priority", ["Low", "Medium", "High"]
)

is_liquid = st.checkbox("Is Liquid?")

budget = st.slider("Budget per unit (₹)", 5, 100, 25)

if st.button("🚀 Get Recommendation"):
    payload = {
        "product_form": product_form,
        "fragility_level": fragility,
        "product_weight": product_weight,
        "premium_level": brand_positioning,
        "eco_priority": sustainability_priority,
        "is_liquid": is_liquid,
        "budget": budget
    }

    try:
        res = requests.post("http://127.0.0.1:5000/recommend", json=payload)
        data = res.json()

        best = data["best_material"]
        top3 = data["top_3_materials"]

        st.session_state["top3"] = top3

        st.success(f"✅ Best Material: **{best['material_name']}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("🌱 Sustainability", f"{best['biodegradability_score']:.2f}")
        c2.metric("🏭 CO₂ Emission", f"{best['co2_emission_score']:.2f}")
        c3.metric("💰 Cost Efficiency", f"{best['cost_efficiency_index']:.2f}")

        st.subheader("🏆 Top 3 Recommended Materials")
        df = pd.DataFrame(top3)
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Connection error: {e}")
