import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import bcrypt
import json
import random
import time
from github import Github

# ---------------------------------------------------
# SECURE CONFIGURATION (Pulling from Streamlit Secrets)
# ---------------------------------------------------

# In Streamlit Cloud, go to Settings -> Secrets and paste:
# BOT_TOKEN = "..."
# CHAT_ID = "..."
# GITHUB_TOKEN = "..."
# REPO_NAME = "your_username/your_repo_name"

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "users.json"
except Exception as e:
    st.error("Missing Secrets! Please configure them in the Streamlit Cloud Dashboard.")
    st.stop()

# ---------------------------------------------------
# GITHUB DATA PERSISTENCE
# ---------------------------------------------------

def load_users():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        file = repo.get_contents(FILE_PATH)
        return json.loads(file.decoded_content.decode())
    except:
        # Initial admin setup if file doesn't exist
        return {"admin": {"password": hash_password("admin123"), "role": "admin"}}

def save_users(users):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    content = json.dumps(users, indent=4)
    try:
        file = repo.get_contents(FILE_PATH)
        repo.update_file(FILE_PATH, "update users", content, file.sha)
    except:
        repo.create_file(FILE_PATH, "create users", content)

# ---------------------------------------------------
# AUTHENTICATION UTILS
# ---------------------------------------------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def send_otp():
    otp = str(random.randint(100000, 999999))
    st.session_state.reset_otp = otp
    st.session_state.otp_time = time.time()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": f"🔐 Password Reset OTP: {otp}"})

# ---------------------------------------------------
# DASHBOARD LOGIC
# ---------------------------------------------------

def dashboard():
    st.title("📊 Live Stock P2L")
    
    # Static Buy Prices (Cost Basis)
    stocks_to_track = {
        "CANBK.NS": 142.93,
        "DLF.NS": 646.85
    }

    @st.cache_data(ttl=60)
    def fetch_stock_data():
        tickers = list(stocks_to_track.keys())
        # Fetching data for multiple tickers
        data = yf.download(tickers, period="1d", interval="1m", progress=False)
        
        rows = []
        for ticker in tickers:
            try:
                # Handle multi-index columns from yf.download
                if len(tickers) > 1:
                    current_price = data['Close'][ticker].iloc[-1]
                else:
                    current_price = data['Close'].iloc[-1]
                
                buy_price = stocks_to_track[ticker]
                p2l = ((current_price - buy_price) / buy_price) * 100
                
                rows.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Current Price": round(current_price, 2),
                    "Buy Price": buy_price,
                    "P2L %": round(p2l, 2)
                })
            except:
                continue
        return pd.DataFrame(rows)

    df = fetch_stock_data()

    if not df.empty:
        # Highlighting P2L
        def color_p2l(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'

        st.dataframe(df.style.applymap(color_p2l, subset=['P2L %']))
        
        avg_p2l = df["P2L %"].mean()
        st.metric("Portfolio Average P2L", f"{avg_p2l:.2f}%", delta=f"{avg_p2l:.2f}%")
    else:
        st.warning("No data found. Check your internet connection or ticker symbols.")

    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------
# MAIN ROUTING
# ---------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.title("🔐 Login")
    users = load_users()
    user_id = st.text_input("User ID")
    pwd = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user_id in users and check_password(pwd, users[user_id]["password"]):
            st.session_state.logged_in = True
            st.session_state.user = user_id
            st.session_state.role = users[user_id]["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    # --- LOGGED IN APP ---
    st.sidebar.title(f"Welcome, {st.session_state.user}")
    
    menu = ["Dashboard", "Account Settings"]
    if st.session_state.role == "admin":
        menu.append("Admin Panel")
    
    choice = st.sidebar.selectbox("Navigation", menu)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if choice == "Dashboard":
        dashboard()
    elif choice == "Account Settings":
        # Put your change_password() function here
        st.info("Password change feature active.")
    elif choice == "Admin Panel":
        # Put your admin_panel() function here
        st.info("User management active.")
