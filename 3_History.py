import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="EcoPackAI | History", layout="wide")

# ================= UI THEME =================

st.markdown("""
<style>
body{
    background:linear-gradient(135deg,#eef6ff,#e6f9f2);
}

.block-container{
    padding:2.5rem;
}

h1,h2,h3{
    color:#114b5f;
}

.card{
    background:white;
    padding:26px;
    border-radius:18px;
    box-shadow:0 8px 18px rgba(0,0,0,.08);
    margin-bottom:24px;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================

st.title("🕒 Recommendation History")
st.caption("Track all eco-friendly packaging recommendations made so far")

# ================= LOAD DATA =================

try:
    res = requests.get("http://127.0.0.1:5000/history")
    history = res.json()["history"]
except:
    st.error("❌ Unable to connect to backend")
    st.stop()

if not history:
    st.info("No recommendations yet — generate one first!")
    st.stop()

df = pd.DataFrame(history)

# ================= DISPLAY =================

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("📜 Historical Recommendations")

st.dataframe(df, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
