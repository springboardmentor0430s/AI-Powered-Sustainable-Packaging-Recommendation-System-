import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="EcoPackAI | Visual Analytics", layout="wide")

# ================= COLORFUL PROFESSIONAL UI =================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg,#eef5ff,#e6f9f2);
}

.block-container {
    padding: 2.5rem 3rem;
}

h1,h2,h3 {
    color:#114b5f;
    font-weight:700;
}

.section {
    margin-top:35px;
}

/* Card Style */
.card {
    background: linear-gradient(135deg,#ffffff,#f2fbf8);
    padding:24px;
    border-radius:20px;
    box-shadow:0 12px 26px rgba(0,0,0,.1);
    margin-bottom:22px;
}

/* Insight */
.insight {
    background: linear-gradient(90deg,#d1f5ea,#dbe9ff);
    padding:18px;
    border-left:6px solid #1f7a5b;
    border-radius:12px;
    font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
st.markdown("## 📈 Sustainability Decision Analytics")
st.caption("Understanding eco-driven packaging choices")

st.divider()

# ================= LOAD DATA =================
res = requests.get("http://127.0.0.1:5000/history")
data = res.json()

if "history" not in data or len(data["history"]) == 0:
    st.warning("No data yet")
    st.stop()

df = pd.DataFrame(data["history"])
df.columns = df.columns.str.strip()

material_col = next(c for c in df.columns if "material" in c.lower())
eco_col = next(c for c in df.columns if "eco" in c.lower())
frag_col = next(c for c in df.columns if "fragility" in c.lower())

# ================= ECO VS MATERIAL =================
st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("### 🌱 Sustainability Influence")

st.markdown('<div class="card">', unsafe_allow_html=True)
eco_matrix = pd.crosstab(df[eco_col], df[material_col])
st.dataframe(eco_matrix, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight">
🌿 Higher sustainability priorities result in stronger selection of eco-friendly materials.
</div>
""", unsafe_allow_html=True)

# ================= MATERIAL STABILITY =================
st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("### 🧱 Material Robustness")

st.markdown('<div class="card">', unsafe_allow_html=True)
material_freq = df[material_col].value_counts()
st.bar_chart(material_freq)
st.markdown('</div>', unsafe_allow_html=True)

# ================= FRAGILITY IMPACT =================
st.markdown('<div class="section"></div>', unsafe_allow_html=True)
st.markdown("### 📦 Fragility Impact")

st.markdown('<div class="card">', unsafe_allow_html=True)
frag_matrix = pd.crosstab(df[frag_col], df[material_col])
st.dataframe(frag_matrix, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="insight">
📦 Fragile products push selection toward stronger protective materials.
</div>
""", unsafe_allow_html=True)

# ================= RAW =================
with st.expander("📄 View analytics data"):
    st.dataframe(df[[eco_col, material_col, frag_col]])
