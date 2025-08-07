import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json

# --- CONFIG ---
API_URL = "https://ai-crypto-predictor.onrender.com"
st.set_page_config(page_title="AI Crypto Predictor", page_icon="📈", layout="centered", initial_sidebar_state="collapsed")

# --- LOAD LOTTIE ANIMATION ---
def load_lottie_animation():
    url = "https://assets10.lottiefiles.com/packages/lf20_dzWAyu.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# --- SEND OTP ---
def send_otp(email):
    response = requests.post(f"{API_URL}/send-otp", json={"email": email})
    return response.json()

# --- VERIFY OTP ---
def verify_otp(email, otp):
    response = requests.post(f"{API_URL}/verify-otp", json={"email": email, "otp": otp})
    return response.json()

# --- UI STYLES ---
custom_css = """
<style>
body {
    background-color: #0d1117;
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
}
.css-1v0mbdj.ef3psqc12 {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid #30363d;
    border-radius: 1rem;
    padding: 2rem;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- PAGE LOGIC ---
st_lottie(load_lottie_animation(), height=200)
st.title("🔐 AI Crypto Login")
st.write("Enter your email to receive a one-time password (OTP)")

if "step" not in st.session_state:
    st.session_state.step = "email"

if st.session_state.step == "email":
    email = st.text_input("Email", key="email_input")
    if st.button("Send OTP"):
        if email:
            result = send_otp(email)
            if result.get("success"):
                st.session_state.email = email
                st.session_state.step = "otp"
                st.success("OTP sent! Check your inbox.")
            else:
                st.error(result.get("message", "Failed to send OTP."))
        else:
            st.warning("Please enter your email.")

elif st.session_state.step == "otp":
    st.write(f"OTP sent to: {st.session_state.email}")
    otp = st.text_input("Enter OTP", max_chars=6)
    if st.button("Verify OTP"):
        result = verify_otp(st.session_state.email, otp)
        if result.get("authenticated"):
            st.success("✅ Authentication successful!")
            # Placeholder for full app here
            st.write("You are now logged in! ✨")
        else:
            st.error("❌ Invalid OTP. Please try again.")
