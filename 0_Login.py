import streamlit as st

st.set_page_config(page_title="EcoPackAI | Login", page_icon="🔐")

st.markdown("## 🔐 Login to EcoPackAI")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    login = st.form_submit_button("Login")

if login:
    if email and password:
        st.session_state["authenticated"] = True
        st.success("Login successful!")
        st.info("Please select a page from the sidebar.")
    else:
        st.error("Please enter valid credentials")
