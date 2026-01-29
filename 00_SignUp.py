import streamlit as st

st.set_page_config(page_title="EcoPackAI | Sign Up", page_icon="📝", layout="centered")

# ================= MODERN UI =================
st.markdown("""
<style>
body{
    background: linear-gradient(135deg,#e6f9f2,#eef5ff);
}

.signup-card{
    background:white;
    padding:40px;
    border-radius:22px;
    box-shadow:0 12px 30px rgba(0,0,0,.12);
    max-width:440px;
    margin:auto;
    margin-top:70px;
}

h1{
    color:#114b5f;
    text-align:center;
    margin-bottom:15px;
}

p{
    text-align:center;
    color:#4b6b63;
}

button{
    background:#1f7a5b !important;
    color:white !important;
    border-radius:14px !important;
}
</style>
""", unsafe_allow_html=True)

# ================= SIGNUP CARD =================
st.markdown("""
<div class="signup-card">
<h1>📝 Create Your EcoPackAI Account</h1>
<p>Join the sustainable packaging platform</p>
</div>
""", unsafe_allow_html=True)

with st.form("signup_form"):
    name = st.text_input("👤 Full Name")
    email = st.text_input("📧 Email Address")
    password = st.text_input("🔑 Password", type="password")
    confirm_password = st.text_input("🔐 Confirm Password", type="password")

    submit = st.form_submit_button("Create Account")

if submit:
    if not name or not email or not password:
        st.error("❌ Please fill all fields")
    elif password != confirm_password:
        st.error("❌ Passwords do not match")
    else:
        st.success("✅ Signup successful! (Auth backend can be integrated later)")
        st.info("➡ Go to Login page to continue")
