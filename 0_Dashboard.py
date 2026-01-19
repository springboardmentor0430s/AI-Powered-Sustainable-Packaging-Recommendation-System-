import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="EcoPackAI Dashboard", layout="wide")

st.title("📊 EcoPackAI – Dashboard")
st.caption("Basic overview of recommendation usage")

# -----------------------------
# Load history from backend
# -----------------------------
try:
    res = requests.get("http://127.0.0.1:5000/history", timeout=10)

    if res.status_code != 200:
        st.warning("Backend is running, but no history data available.")
        st.stop()

    history = res.json().get("history", [])

    if not history:
        st.info("No recommendations made yet.")
        st.stop()

    df = pd.DataFrame(history)

except Exception as e:
    st.error(f"Unable to connect to backend: {e}")
    st.stop()

# -----------------------------
# Key Metrics
# -----------------------------
st.subheader("🔑 Key Metrics")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "📦 Total Recommendations",
        len(df)
    )

with c2:
    st.metric(
        "🌱 Sustainability Levels Used",
        df["Eco Priority"].nunique() if "Eco Priority" in df.columns else df["Eco Priority".lower()].nunique()
        if "eco priority" in df.columns else df["eco_priority"].nunique()
    )

with c3:
    st.metric(
        "🏆 Unique Materials Recommended",
        df["Best Material"].nunique() if "Best Material" in df.columns else df["best_material"].nunique()
    )

st.divider()

# -----------------------------
# Recent Recommendations Table
# -----------------------------
st.subheader("🕒 Recent Recommendations")

display_cols = []

if "Time" in df.columns:
    display_cols.append("Time")
elif "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"])
    display_cols.append("created_at")

if "Best Material" in df.columns:
    display_cols.append("Best Material")
else:
    display_cols.append("best_material")

if "Eco Priority" in df.columns:
    display_cols.append("Eco Priority")
else:
    display_cols.append("eco_priority")

if "Premium Level" in df.columns:
    display_cols.append("Premium Level")
else:
    display_cols.append("premium_level")

st.dataframe(
    df[display_cols].sort_values(display_cols[0], ascending=False).head(10),
    use_container_width=True
)
