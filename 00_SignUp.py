import streamlit as st

st.set_page_config(page_title="EcoPackAI | Sign Up", page_icon="📝")

st.markdown("## 📝 Create an Account")
st.write("Register to access EcoPackAI features.")

with st.form("signup_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    submit = st.form_submit_button("Sign Up")

if submit:
    if password != confirm_password:
        st.error("Passwords do not match")
    else:
        st.success("Signup successful! (Backend integration pending)")
