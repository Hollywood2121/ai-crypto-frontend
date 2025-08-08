import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json

# --- CONFIG ---
API_URL = "https://ai-crypto-predictor.onrender.com"
st.set_page_config(page_title="AI Crypto Predictor", page_icon="📈", layout="wide")

# --- LOTTIE ANIMATION ---
def load_lottie_animation():
    url = "https://assets10.lottiefiles.com/packages/lf20_dzWAyu.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# --- API CALLS ---
def send_otp(email):
    response = requests.post(f"{API_URL}/send-otp", json={"email": email})
    return response.json()

def verify_otp(email, otp):
    response = requests.post(f"{API_URL}/verify-otp", json={"email": email, "otp": otp})
    return response.json()

def get_predictions(email):
    response = requests.get(f"{API_URL}/predict", params={"email": email})
    return response.json()

def get_alerts():
    response = requests.get(f"{API_URL}/alerts")
    return response.json()

# --- STYLES ---
custom_css = """
<style>
body {
    background-color: #0d1117;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
.css-1v0mbdj {
    background-color: rgba(255,255,255,0.05);
    padding: 2rem;
    border-radius: 1rem;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- LOGIN STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "email" not in st.session_state:
    st.session_state.email = ""
if "step" not in st.session_state:
    st.session_state.step = "email"

# --- LOGIN FLOW ---
if not st.session_state.authenticated:
    st_lottie(load_lottie_animation(), height=200)
    st.title("🔐 AI Crypto Login")

    if st.session_state.step == "email":
        email = st.text_input("Enter your email")
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
                st.session_state.authenticated = True
                st.session_state.step = "dashboard"
                st.success("✅ Login successful!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid OTP. Please try again.")

# --- DASHBOARD ---
if st.session_state.authenticated:
    st.title("📊 AI Crypto Predictor Dashboard")
    st.subheader(f"Welcome, {st.session_state.email}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔮 Predictions")
        predictions = get_predictions(st.session_state.email)
        if "coins" in predictions:
            for coin in predictions["coins"]:
                change_color = "green" if coin["change"] > 0 else "red"
                st.markdown(f"**{coin['symbol']}** — ${coin['price']} — <span style='color:{change_color}'>{coin['change']}%</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🚨 Alerts")
        alerts = get_alerts()
        if "alerts" in alerts:
            for alert in alerts["alerts"]:
                st.markdown(f"**{alert['symbol']}** — {alert['alert']}")

    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.session_state.step = "email"
        st.experimental_rerun()
