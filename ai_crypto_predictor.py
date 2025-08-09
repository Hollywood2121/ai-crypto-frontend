import streamlit as st
import requests
import json
from typing import Optional
from streamlit_cookies_manager import EncryptedCookieManager

# =========================
# Brand & Config
# =========================
BRAND_NAME = st.secrets.get("BRAND_NAME", "Cryptonyk")
BRAND_URL  = st.secrets.get("BRAND_URL",  "https://cryptonyk.com")
API_URL    = st.secrets.get("BACKEND_URL", "https://ai-crypto-predictor.onrender.com")
COOKIE_PASSWORD = st.secrets.get("COOKIE_PASSWORD", "")

st.set_page_config(
    page_title=f"{BRAND_NAME} — AI Crypto Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# Cookies (login persistence)
# =========================
cookies = EncryptedCookieManager(
    prefix=f"{BRAND_NAME.lower()}_",
    password=COOKIE_PASSWORD or None,   # if empty, library will still work (unencrypted)
)
if not cookies.ready():
    st.stop()

# =========================
# Styles (dark-first)
# =========================
st.markdown("""
<style>
:root { --brand-accent: #00d09c; }
html, body, [data-testid="stAppViewContainer"] {
  background: #0d1117;
  color: #e6edf3;
}
a { color: var(--brand-accent); text-decoration: none; }
.block { background: rgba(255,255,255,.05); border: 1px solid #30363d; border-radius: 16px; padding: 16px; }
.brand { font-weight: 700; letter-spacing: .3px; }
.header {
  display:flex; justify-content:space-between; align-items:center; gap:12px;
  padding: 8px 0 16px 0; border-bottom: 1px solid #222;
}
.pill { background: rgba(0,208,156,.12); color:#8ff4dc; border: 1px solid #1b574b; padding: 4px 10px; border-radius: 999px; font-size: 12px;}
.price-card { display:flex; flex-direction:column; gap:6px; }
.symbol { font-weight:600; font-size: 18px; }
.price  { font-variant-numeric: tabular-nums; font-size: 20px; }
.delta-up { color: #28d07f; }
.delta-down { color: #ff6b6b; }
.footer { opacity:.7; font-size: 12px; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Backend helpers
# =========================
def send_otp(email: str) -> dict:
    r = requests.post(f"{API_URL}/send-otp", json={"email": email}, timeout=15)
    return r.json()

def verify_otp(email: str, otp: str) -> dict:
    r = requests.post(f"{API_URL}/verify-otp", json={"email": email, "otp": otp}, timeout=15)
    return r.json()

def get_predictions(email: str, window: str = "24h") -> dict:
    r = requests.get(f"{API_URL}/predict", params={"email": email, "window": window}, timeout=20)
    r.raise_for_status()
    return r.json()

def list_alerts(email: str) -> dict:
    r = requests.get(f"{API_URL}/alerts", params={"email": email}, timeout=15)
    r.raise_for_status()
    return r.json()

def add_alert(email: str, symbol: str, direction: str, percent: float) -> dict:
    r = requests.get(f"{API_URL}/alerts/add", params={
        "email": email, "symbol": symbol, "direction": direction, "percent": percent
    }, timeout=15)
    r.raise_for_status()
    return r.json()

def delete_alert(email: str, symbol: str, direction: str, percent: float) -> dict:
    r = requests.delete(f"{API_URL}/alerts", params={
        "email": email, "symbol": symbol, "direction": direction, "percent": percent
    }, timeout=15)
    r.raise_for_status()
    return r.json()

# =========================
# Header
# =========================
colA, colB = st.columns([1,1])
with colA:
    st.markdown(f"""
    <div class="header">
      <div class="brand" style="font-size:22px;">{BRAND_NAME}</div>
      <div class="pill">AI Signals • OTP Login</div>
    </div>
    """, unsafe_allow_html=True)
with colB:
    st.write("")

# =========================
# Auth state
# =========================
if "authed" not in cookies:
    cookies["authed"] = "0"
if "email" not in cookies:
    cookies["email"] = ""

authed = cookies.get("authed") == "1"
user_email = cookies.get("email")

# =========================
# Login UI
# =========================
def render_login():
    with st.container():
        st.subheader("Sign in")
        email = st.text_input("Email", value=user_email or "", placeholder="you@example.com")
        if st.button("Send OTP"):
            if not email:
                st.warning("Enter your email first.")
            else:
                res = send_otp(email.strip().lower())
                if res.get("success"):
                    st.success("OTP sent. Check your inbox (and Spam).")
                    st.session_state["login_email"] = email.strip().lower()
                    st.session_state["otp_stage"] = True
                else:
                    st.error(res.get("message", "Failed to send OTP."))

        if st.session_state.get("otp_stage"):
            otp = st.text_input("Enter 6-digit OTP", max_chars=6)
            if st.button("Verify OTP"):
                res = verify_otp(st.session_state["login_email"], otp.strip())
                if res.get("authenticated"):
                    cookies["authed"] = "1"
                    cookies["email"] = st.session_state["login_email"]
                    cookies.save()
                    st.success("You're in ✅")
                    st.rerun()
                else:
                    st.error(res.get("message", "Invalid OTP."))

    st.markdown(f'<div class="footer">By continuing you agree to {BRAND_NAME} terms. Visit <a href="{BRAND_URL}" target="_blank">{BRAND_URL}</a>.</div>', unsafe_allow_html=True)

# =========================
# App (after login)
# =========================
def render_app():
    st.caption(f"Logged in as **{user_email}** · Backend: {API_URL}")

    # Controls
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        window = st.selectbox("Prediction Window", ["15m","1h","12h","24h"], index=3)
    with c2:
        if st.button("Refresh Now"):
            st.rerun()
    with c3:
        if st.button("Log out"):
            cookies["authed"] = "0"
            cookies["email"] = ""
            cookies.save()
            st.rerun()

    # Predictions
    try:
        data = get_predictions(user_email, window=window)
        if data.get("error"):
            st.error(f"Backend error: {data['error']}")
        coins = data.get("coins", [])
    except Exception as e:
        st.error(f"Error loading predictions: {e}")
        coins = []

    st.markdown("### Markets")
    grid = st.columns(5)
    for i, c in enumerate(coins):
        col = grid[i % 5]
        with col:
            change = float(c.get("change", 0.0))
            price = float(c.get("price", 0.0))
            pred  = c.get("prediction", "UP")
            conf  = c.get("confidence", 50.0)
            col.markdown(f"""
            <div class="block price-card">
                <div class="symbol">{c['symbol']}</div>
                <div class="price">${price:,.2f}</div>
                <div class="{'delta-up' if change>=0 else 'delta-down'}">{change:+.2f}% {pred} · {conf:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### Alerts")
    # Existing alerts
    try:
        current = list_alerts(user_email).get("alerts", [])
    except Exception as e:
        st.error(f"Failed to load alerts: {e}")
        current = []

    if current:
        for a in current:
            cols = st.columns([1,1,1,1])
            cols[0].write(a["symbol"])
            cols[1].write(a["direction"])
            cols[2].write(f"{float(a['percent']):.2f}%")
            if cols[3].button("Delete", key=f"del_{a['symbol']}_{a['direction']}_{a['percent']}"):
                try:
                    delete_alert(user_email, a["symbol"], a["direction"], float(a["percent"]))
                    st.success("Deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")
    else:
        st.info("No alerts yet.")

    st.divider()
    st.subheader("Add alert")
    ac1, ac2, ac3, ac4 = st.columns([1,1,1,1])
    with ac1:
        symbol = st.selectbox("Symbol", ["BTC","ETH","SOL","ADA","XRP","BNB","DOGE","AVAX","MATIC","LTC"])
    with ac2:
        direction = st.selectbox("Direction", ["UP","DOWN"])
    with ac3:
        percent = st.number_input("Percent move", min_value=0.1, max_value=50.0, value=1.0, step=0.1)
    with ac4:
        if st.button("Save alert"):
            try:
                add_alert(user_email, symbol, direction, float(percent))
                st.success("Saved ✔")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save alert: {e}")

    st.markdown(f'<div class="footer">© {BRAND_NAME} · <a href="{BRAND_URL}" target="_blank">{BRAND_URL}</a></div>', unsafe_allow_html=True)

# =========================
# Router
# =========================
if cookies.get("authed") == "1" and cookies.get("email"):
    render_app()
else:
    render_login()
