import streamlit as st
import requests
import pandas as pd
from streamlit_cookies_manager import EncryptedCookieManager

# ------------------ CONFIG ------------------
API_URL = st.secrets.get("BACKEND_URL", "https://ai-crypto-predictor.onrender.com")

st.set_page_config(
    page_title="AI Crypto Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------ COOKIES (persist auth on refresh) ------------------
cookies = EncryptedCookieManager(prefix="crypto_", password=None)
if not cookies.ready():
    st.stop()

# ------------------ SESSION / THEME ------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "step" not in st.session_state:
    st.session_state.step = "email"
if "email" not in st.session_state:
    st.session_state.email = ""

# If cookie says authed, skip login
if cookies.get("authed") == "1" and st.session_state.step != "dashboard":
    st.session_state.step = "dashboard"
    st.session_state.email = cookies.get("email", st.session_state.email or "")

# ------------------ SIDEBAR ------------------
with st.sidebar:
    st.markdown("### Appearance")
    theme_choice = st.radio("Theme", ["🌙 Dark", "☀️ Light"], index=0 if st.session_state.theme=="dark" else 1)
    st.session_state.theme = "dark" if theme_choice == "🌙 Dark" else "light"
    st.divider()
    if st.button("🚪 Log out"):
        if "authed" in cookies:
            del cookies["authed"]
        if "email" in cookies:
            del cookies["email"]
        cookies.save()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.session_state.theme = "dark"
        st.session_state.step = "email"
        st.rerun()

# ------------------ STYLES ------------------
DARK_CSS = """
<style>
body { background-color: #0d1117; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
.glass { background-color: rgba(255,255,255,0.05); border: 1px solid #30363d; border-radius: 14px;
         padding: 1.2rem; box-shadow: 0 4px 30px rgba(0,0,0,0.15); backdrop-filter: blur(10px); margin-bottom: 1rem; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.metric-tile { background: rgba(255,255,255,0.06); border: 1px solid #2c313a; border-radius: 12px; padding: 0.9rem 1rem; }
.metric-sym { font-weight: 700; font-size: 1.05rem; margin-bottom: 6px; }
.metric-val { font-size: 1.1rem; }
.badge-up { color: #00e676; font-weight: 700; }
.badge-down { color: #ff5252; font-weight: 700; }
.conf { opacity: 0.8; font-size: 0.9rem; }
.stButton>button { background:#00c853; color:#fff; border-radius:8px; border:0; padding:0.5rem 0.9rem; }
</style>
"""
LIGHT_CSS = """
<style>
body { background-color: #f6f8fa; color: #0d1117; font-family: 'Segoe UI', sans-serif; }
.glass { background-color: #ffffff; border: 1px solid #d0d7de; border-radius: 14px;
         padding: 1.2rem; box-shadow: 0 2px 20px rgba(0,0,0,0.05); margin-bottom: 1rem; }
.metric-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.metric-tile { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 0.9rem 1rem; }
.metric-sym { font-weight: 700; font-size: 1.05rem; margin-bottom: 6px; }
.metric-val { font-size: 1.1rem; }
.badge-up { color: #0f9d58; font-weight: 700; }
.badge-down { color: #d93025; font-weight: 700; }
.conf { opacity: 0.8; font-size: 0.9rem; }
.stButton>button { background:#0f9d58; color:#fff; border-radius:8px; border:0; padding:0.5rem 0.9rem; }
</style>
"""
st.markdown(DARK_CSS if st.session_state.theme == "dark" else LIGHT_CSS, unsafe_allow_html=True)

# ------------------ HELPERS ------------------
def send_otp(email: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/send-otp", json={"email": email}, timeout=15)
        return r.json() if r.ok else {"success": False, "message": r.text}
    except Exception as e:
        return {"success": False, "message": str(e)}

def verify_otp(email: str, otp: str) -> dict:
    try:
        r = requests.post(f"{API_URL}/verify-otp", json={"email": email, "otp": otp}, timeout=15)
        return r.json() if r.ok else {"authenticated": False, "message": r.text}
    except Exception as e:
        return {"authenticated": False, "message": str(e)}

def fetch_predictions(email: str) -> dict:
    try:
        r = requests.get(f"{API_URL}/predict", params={"email": email}, timeout=20)
        return r.json() if r.ok else {"error": r.text}
    except Exception as e:
        return {"error": str(e)}

def list_alerts_api(email: str) -> dict:
    try:
        r = requests.get(f"{API_URL}/alerts", params={"email": email}, timeout=15)
        return r.json() if r.ok else {"alerts": []}
    except Exception as e:
        return {"alerts": [], "error": str(e)}

def add_alert_api(email: str, symbol: str, direction: str, percent: float) -> dict:
    try:
        payload = {"email": email, "symbol": symbol, "direction": direction, "percent": float(percent)}
        r = requests.post(f"{API_URL}/alerts", json=payload, timeout=15)
        return r.json() if r.ok else {"success": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_alert_api(email: str, symbol: str, direction: str, percent: float) -> dict:
    try:
        params = {"email": email, "symbol": symbol, "direction": direction, "percent": float(percent)}
        r = requests.delete(f"{API_URL}/alerts", params=params, timeout=15)
        return r.json() if r.ok else {"success": False}
    except Exception as e:
        return {"success": False, "error": str(e)}

def render_metrics(coins: list[dict]):
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    for c in coins:
        sym = c.get("symbol","")
        price = float(c.get("price",0.0))
        delta = float(c.get("change",0.0))
        pred = c.get("prediction","")
        conf = float(c.get("confidence",0.0))
        cls = "badge-up" if pred == "UP" else "badge-down"
        badge = f"↑ {pred}" if pred == "UP" else f"↓ {pred}"
        st.markdown(f"""
        <div class="metric-tile">
          <div class="metric-sym">{sym}</div>
          <div class="metric-val">${price:,.2f}</div>
          <div class="{cls}">{delta:+.2f}%</div>
          <div class="conf">{badge} • {conf:.1f}%</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ UI FLOW ------------------
st.title("📈 AI Crypto Predictor")

if st.session_state.step == "email":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    email = st.text_input("Email", key="email_input", placeholder="you@example.com")
    stay = st.checkbox("Stay logged in", value=True)
    if st.button("📩 Send OTP", type="primary"):
        if not email:
            st.warning("Please enter your email.")
        else:
            with st.spinner("Sending OTP..."):
                resp = send_otp(email)
            if resp.get("success"):
                st.session_state.email = email
                st.session_state.step = "otp"
                st.session_state.stay = stay
                st.success("OTP sent! Check your inbox (and spam).")
                st.rerun()
            else:
                st.error(f"Failed to send OTP: {resp.get('message','unknown error')}")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.step == "otp":
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.write(f"OTP sent to: **{st.session_state.email}**")
    col1, col2 = st.columns([1,1])
    with col1:
        otp = st.text_input("Enter 6-digit OTP", max_chars=6)
        if st.button("🔓 Verify OTP", type="primary"):
            with st.spinner("Verifying..."):
                resp = verify_otp(st.session_state.email, otp)
            if resp.get("authenticated"):
                if st.session_state.get("stay", True):
                    cookies["authed"] = "1"
                    cookies["email"] = st.session_state.email
                    cookies.save()
                st.session_state.step = "dashboard"
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error(resp.get("message", "❌ Invalid OTP. Please try again."))
    with col2:
        if st.button("🔁 Resend OTP"):
            with st.spinner("Resending..."):
                resp = send_otp(st.session_state.email)
            if resp.get("success"):
                st.success("New OTP sent. Check your inbox.")
            else:
                st.error(resp.get("message","Please wait before requesting another OTP."))
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.step == "dashboard":
    # Header
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    left, right = st.columns([3,1])
    with left:
        st.subheader("📊 AI Crypto Market Dashboard")
        st.caption(f"Logged in as: {st.session_state.email}")
    with right:
        refresh = st.button("🔄 Refresh")
    st.markdown("</div>", unsafe_allow_html=True)

    # Prices/Predictions
    st.markdown('<div class="glass">', unsafe_allow_html=True)
    if refresh:
        pass  # hook for cache clear later
    with st.spinner("Fetching latest prices..."):
        data = fetch_predictions(st.session_state.email)

    if "error" in data:
        st.error(f"Error loading predictions: {data['error']}")
    else:
        ts = data.get("timestamp")
        if ts:
            st.caption(f"Data timestamp (UTC): {ts}")
        coins = data.get("coins", [])
        if coins:
            render_metrics(coins)
            st.markdown("### Details")
            df = pd.DataFrame(coins)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No coins returned yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Alerts Panel
    st.markdown("### 🔔 Price Alerts")
    colA, colB, colC, colD, colE = st.columns([2,1.5,1.5,2,1])
    with colA:
        coin = st.selectbox("Coin", ["BTC","ETH","SOL","ADA","XRP","BNB","DOGE","AVAX","MATIC","LTC"])
    with colB:
        direction = st.selectbox("Direction", ["UP","DOWN"])
    with colC:
        preset = st.selectbox("Percent preset", ["1","2","5","10","Custom"])
    with colD:
        custom = st.number_input("Custom %", min_value=0.1, value=3.0, step=0.1)
    with colE:
        st.write("")  # spacer
        create = st.button("Add Alert")

    pct = float(preset) if preset != "Custom" else float(custom)

    if create:
        with st.spinner("Saving alert..."):
            resp = add_alert_api(st.session_state.email, coin, direction, pct)
        if resp.get("success"):
            st.success(f"Added alert: {coin} {direction} {pct:.2f}%")
            st.rerun()
        else:
            st.error("Failed to save alert.")

    alerts_resp = list_alerts_api(st.session_state.email)
    alerts = alerts_resp.get("alerts", [])
    if alerts:
        st.write("**Your alerts:**")
        for i, a in enumerate(alerts, start=1):
            c1, c2, c3, c4 = st.columns([2,2,2,1])
            c1.write(a["symbol"])
            c2.write(a["direction"])
            c3.write(f'{float(a["percent"]):.2f}%')
            if c4.button("Delete", key=f"del_{i}"):
                with st.spinner("Removing..."):
                    delete_alert_api(st.session_state.email, a["symbol"], a["direction"], float(a["percent"]))
                st.rerun()
    else:
        st.caption("You have no alerts yet.")

else:
    st.session_state.step = "email"
    st.rerun()
