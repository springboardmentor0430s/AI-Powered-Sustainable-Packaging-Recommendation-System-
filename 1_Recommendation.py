import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="EcoPackAI Recommendation", layout="wide")

# ==================== UI THEME ====================

st.markdown("""
<style>
body{
    background:linear-gradient(135deg,#e6f9f2,#eef5ff);
}

.block-container{
    padding:2.5rem;
}

h1,h2,h3{
    color:#114b5f;
}

.input-card{
    background:white;
    padding:26px;
    border-radius:18px;
    box-shadow:0 8px 18px rgba(0,0,0,.08);
    margin-bottom:28px;
}

.result-card{
    background:white;
    padding:24px;
    border-radius:18px;
    box-shadow:0 10px 22px rgba(0,0,0,.1);
    margin-top:20px;
}

.stButton>button{
    background:#1f7a5b;
    color:white;
    border-radius:14px;
    padding:10px 26px;
    font-size:16px;
    border:none;
}

.stButton>button:hover{
    background:#17614a;
}
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================

st.title("🌱 EcoPackAI Sustainable Packaging Recommendation")
st.caption("AI-powered eco-friendly packaging material selection for cosmetic products")

# ==================== INPUT SECTION ====================

st.markdown("<div class='input-card'>", unsafe_allow_html=True)
st.subheader("🔧 Product Details")

col1, col2 = st.columns(2)

with col1:
    product_form = st.selectbox(
        "💄 Cosmetic Product Form",
        ["Cream","Lotion","Gel","Serum","Powder","Solid Stick","Perfume","Liquid"]
    )

    fragility = st.selectbox("⚠ Product Fragility", ["Low","Medium","High"])

    product_weight = st.slider("📦 Product Weight (kg)", 0.1, 2.0, 0.3)

with col2:
    brand_positioning = st.selectbox(
        "💎 Brand Positioning",
        ["Budget","Standard","Premium"]
    )

    sustainability_priority = st.selectbox(
        "🌱 Sustainability Priority",
        ["Low","Medium","High"]
    )

    is_liquid = st.checkbox("💧 Is Liquid Product")

    budget = st.slider("💰 Budget per unit (₹)", 5, 100, 25)

st.markdown("</div>", unsafe_allow_html=True)

# ==================== SUBMIT ====================

if st.button("🚀 Get Smart Recommendation", use_container_width=True):

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
        res = requests.post(
            "http://127.0.0.1:5000/recommend",
            json=payload,
            timeout=10
        )

        if res.status_code != 200:
            st.error("❌ Backend error. Please check Flask server.")
            st.stop()

        data = res.json()

        best = data["best_material"]
        top3 = data["top_3_materials"]
        st.session_state["top3"] = top3


        # ==================== BEST RESULT ====================

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.markdown(f"## 🥇 Best Recommended Material")
        st.markdown(f"### {best['material_name']}")
        st.markdown("</div>", unsafe_allow_html=True)

        # ==================== METRICS ====================

        c1, c2, c3 = st.columns(3)

        c1.metric("🌱 Sustainability Score", round(best["biodegradability_score"],2))
        c2.metric("🏭 CO₂ Emission Score", round(best["co2_emission_score"],2))
        c3.metric("💰 Cost Efficiency Index", round(best["cost_efficiency_index"],2))

        # ==================== TOP 3 TABLE ====================

        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
        st.subheader("🏆 Top 3 Recommended Materials")

        df_top3 = pd.DataFrame(top3)[[
            "material_name",
            "biodegradability_score",
            "co2_emission_score",
            "cost_efficiency_index"
        ]]

        df_top3.columns = [
            "Material",
            "Biodegradability Score",
            "CO₂ Emission Score",
            "Cost Efficiency Index"
        ]

        st.dataframe(df_top3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Connection error: {e}")
