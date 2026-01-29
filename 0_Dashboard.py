import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="EcoPackAI | Dashboard", layout="wide")

# ================= COLORFUL PROFESSIONAL UI =================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #e6f9f2, #eef5ff);
}

.block-container {
    padding: 2.5rem 3rem;
}

h1, h2, h3 {
    color: #114b5f;
    font-weight: 700;
}

/* KPI Cards */
.card {
    background: linear-gradient(135deg, #ffffff, #f4fdf9);
    padding: 28px;
    border-radius: 20px;
    box-shadow: 0 12px 26px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    text-align: center;
    transition: transform 0.2s ease;
}

.card:hover {
    transform: scale(1.04);
}

/* Insight box */
.insight {
    background: linear-gradient(90deg, #d1f5ea, #dbe9ff);
    padding: 18px;
    border-left: 6px solid #1f7a5b;
    border-radius: 12px;
    font-weight: 600;
    margin-top: 20px;
}

/* Section spacing */
.section {
    margin-top: 35px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("## 🌱 EcoPackAI Executive Dashboard")
st.caption("High-level system overview and usage performance")

st.divider()

# ================= LOAD DATA =================
res = requests.get("http://127.0.0.1:5000/history")
data = res.json()

if "history" not in data or len(data["history"]) == 0:
    st.warning("No data yet — generate recommendations first")
    st.stop()

df = pd.DataFrame(data["history"])
df.columns = df.columns.str.strip()

material_col = next(c for c in df.columns if "material" in c.lower())
time_col = next(c for c in df.columns if "time" in c.lower())

df[time_col] = pd.to_datetime(df[time_col])

# ================= KPI CARDS =================
st.markdown("### 📊 System Health")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        f'<div class="card"><h3>Total Requests</h3><h1 style="color:#1f7a5b;">{len(df)}</h1></div>',
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f'<div class="card"><h3>Active Days</h3><h1 style="color:#3a86ff;">{df[time_col].dt.date.nunique()}</h1></div>',
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f'<div class="card"><h3>Materials Used</h3><h1 style="color:#2a9d8f;">{df[material_col].nunique()}</h1></div>',
        unsafe_allow_html=True
    )

# ================= USAGE TREND =================
st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("### ⏱ System Usage Trend")

usage = df.groupby(df[time_col].dt.date).size()
st.line_chart(usage)

# ================= INSIGHT =================
st.markdown("""
<div class="insight">
🌿 <strong>Key Insight:</strong> The recommendation engine shows consistent usage with diverse material evaluation, indicating strong sustainability adoption.
</div>
""", unsafe_allow_html=True)

# ================= RAW =================
with st.expander("📄 View system data"):
    st.dataframe(df[[material_col, time_col]])
