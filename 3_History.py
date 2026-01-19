import streamlit as st
import pandas as pd
import requests

st.title("🕒 Recommendation History")

try:
    res = requests.get("http://127.0.0.1:5000/history")
    history = res.json()["history"]
except:
    st.error("Unable to connect to backend")
    st.stop()

if not history:
    st.info("No history available yet.")
    st.stop()

df = pd.DataFrame(history)

st.dataframe(df, use_container_width=True)
