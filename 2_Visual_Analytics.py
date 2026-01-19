import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests

st.title("📊 Visual Analytics & Insights")

# -----------------------------
# Load history from backend
# -----------------------------
try:
    res = requests.get("http://127.0.0.1:5000/history")
    history = res.json()["history"]
except Exception as e:
    st.error(f"Analytics load failed: {e}")
    st.stop()

if not history:
    st.warning("No analytics data available yet.")
    st.stop()

# -----------------------------
# Create DataFrame
# -----------------------------
df = pd.DataFrame(history)

# -----------------------------
# 🔥 CRITICAL FIX: Rename columns
# -----------------------------
df = df.rename(columns={
    "Eco Priority": "eco_priority",
    "Best Material": "best_material"
})

# -----------------------------
# Recommendation Trend
# -----------------------------
st.subheader("⏱ Recommendation Trend by Sustainability Priority")

plt.figure(figsize=(6, 4))
sns.countplot(
    data=df,
    x="eco_priority",
    order=["Low", "Medium", "High"],
    palette="viridis"
)

plt.xlabel("Sustainability Priority")
plt.ylabel("Recommendation Count")
plt.title("User Sustainability Preference Trend")

st.pyplot(plt)

# -----------------------------
# Most Recommended Materials
# -----------------------------
st.subheader("🏅 Most Recommended Materials")

plt.figure(figsize=(7, 4))
sns.countplot(
    data=df,
    y="best_material",
    order=df["best_material"].value_counts().index,
    palette="magma"
)

plt.xlabel("Count")
plt.ylabel("Material")
plt.title("Most Recommended Packaging Materials")

st.pyplot(plt)
