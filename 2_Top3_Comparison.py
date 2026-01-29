import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="EcoPackAI | Top 3 Comparison", layout="wide")

# ================= UI STYLING =================
st.markdown("""
<style>
body{background:#f6f9f7;}
h1,h2,h3{color:#1f7a5b}

.card{
    background:white;
    padding:22px;
    border-radius:16px;
    box-shadow:0 6px 15px rgba(0,0,0,.08);
    margin-bottom:20px;
}

.highlight{
    background:#e8f5f0;
    padding:14px;
    border-left:6px solid #1f7a5b;
    border-radius:10px;
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("## 🏆 Top 3 Sustainable Material Comparison")
st.caption("Visual performance analysis of recommended packaging materials")
st.divider()

# ================= DATA CHECK =================
if "top3" not in st.session_state:
    st.warning("⚠ Please generate a recommendation first.")
    st.stop()

top3 = st.session_state["top3"]

if not top3:
    st.warning("⚠ Recommendation data empty.")
    st.stop()

df = pd.DataFrame(top3)

# ================= REQUIRED COLUMNS =================
required_cols = [
    "material_name",
    "biodegradability_score",
    "co2_emission_score",
    "cost_efficiency_index"
]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing column: {col}")
        st.stop()

# ================= TABLE =================
st.markdown("### 📋 Material Performance Overview")

pretty_df = df[required_cols].rename(columns={
    "material_name": "Material",
    "biodegradability_score": "Biodegradability",
    "co2_emission_score": "CO₂ Emission",
    "cost_efficiency_index": "Cost Efficiency"
})

st.dataframe(pretty_df, use_container_width=True)

# ================= CHART =================
st.markdown("### 📊 Metric Comparison")

fig, ax = plt.subplots(figsize=(10,5))

materials = df["material_name"]

ax.plot(materials, df["biodegradability_score"], marker="o", linewidth=3, label="Biodegradability")
ax.plot(materials, df["co2_emission_score"], marker="o", linewidth=3, label="CO₂ Emission")
ax.plot(materials, df["cost_efficiency_index"], marker="o", linewidth=3, label="Cost Efficiency")

ax.set_xlabel("Material")
ax.set_ylabel("Score")
ax.set_title("Sustainability & Cost Performance")
ax.grid(alpha=0.3)
ax.legend()

st.pyplot(fig)

# ================= INSIGHT =================
best_material = df.iloc[0]["material_name"]

st.markdown(f"""
<div class="highlight">
<strong>🏆 Best Overall Choice:</strong> {best_material} delivers the best balance of sustainability and cost efficiency.
</div>
""", unsafe_allow_html=True)
