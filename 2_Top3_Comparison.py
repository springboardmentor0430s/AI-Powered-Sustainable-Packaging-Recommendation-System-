import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.title("🏆 Top 3 Material Comparison")

# -----------------------------
# Check if data exists
# -----------------------------
if "top3" not in st.session_state or not st.session_state["top3"]:
    st.warning("Please generate a recommendation first.")
    st.stop()

df = pd.DataFrame(st.session_state["top3"])

# -----------------------------
# Required columns check
# -----------------------------
required_cols = [
    "material_name",
    "biodegradability_score",
    "co2_emission_score",
    "cost_efficiency_index"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# -----------------------------
# Table View
# -----------------------------
st.subheader("📋 Top 3 Materials – Detailed Metrics")

st.dataframe(
    df.rename(columns={
        "material_name": "Material",
        "biodegradability_score": "Biodegradability",
        "co2_emission_score": "CO₂ Emission",
        "cost_efficiency_index": "Cost Efficiency"
    }),
    use_container_width=True
)

# -----------------------------
# Line Chart (Professional)
# -----------------------------
st.subheader("📊 Metric Comparison")

plt.figure(figsize=(9, 5))

plt.plot(df["material_name"], df["biodegradability_score"],
         marker="o", label="Biodegradability")

plt.plot(df["material_name"], df["co2_emission_score"],
         marker="o", label="CO₂ Emission")

plt.plot(df["material_name"], df["cost_efficiency_index"],
         marker="o", label="Cost Efficiency")

plt.xlabel("Material")
plt.ylabel("Score")
plt.title("Material Metric Comparison")
plt.legend()
plt.grid(alpha=0.3)

st.pyplot(plt)
