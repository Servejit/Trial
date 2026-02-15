# ---------------------------------------------------
# INSTALL
# pip install streamlit yfinance pandas requests bcrypt PyGithub
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import bcrypt
import json
import random
import time
from datetime import datetime
from github import Github

# ---------------------------------------------------
# CONFIGURATION (Using Secrets for Security)
# ---------------------------------------------------

# Set these in your Streamlit Cloud "Secrets" panel
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]  # e.g., "yourname/your-repo"
    FILE_PATH = "users.json"
except Exception:
    st.error("Please configure Secrets (BOT_TOKEN, CHAT_ID, GITHUB_TOKEN, REPO_NAME) in Streamlit.")
    st.stop()

# ---------------------------------------------------
# PAGE CONFIG
st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ---------------------------------------------------
# SECURITY FUNCTIONS

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def send_otp():
    otp = str(random.randint(100000, 999999))
    st.session_state.reset_otp = otp
    st.session_state.otp_time = time.time()
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": f"🔐 Password Reset OTP: {otp}"}
    )

# ---------------------------------------------------
# DATA PERSISTENCE (GITHUB)

def load_users():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        file = repo.get_contents(FILE_PATH)
        return json.loads(file.decoded_content.decode())
    except:
        # Default admin if file doesn't exist
        # Password: admin
        return {"admin": {"password": hash_password("admin"), "role": "admin"}}

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
# UI COMPONENTS

def login():
    st.title("🔐 Login")
    users = load_users()
    username = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in users and check_password(password, users[username]["password"]):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid Login")

    st.markdown("---")
    st.subheader("Forgot Password")
    reset_user = st.text_input("User ID for Reset", key="reset_user")
    if st.button("Send OTP"):
        if reset_user in users:
            send_otp()
            st.success("OTP sent to Telegram")
        else:
            st.error("User not found")

    otp = st.text_input("Enter OTP")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Reset Password"):
        if "reset_otp" not in st.session_state:
            st.error("Send OTP first")
        elif time.time() - st.session_state.otp_time > 300:
            st.error("OTP expired")
        elif otp != st.session_state.reset_otp:
            st.error("Wrong OTP")
        else:
            users[reset_user]["password"] = hash_password(new_pass)
            save_users(users)
            st.success("Password Reset Successful")

def change_password():
    with st.expander("🔑 Change My Password"):
        users = load_users()
        current = st.text_input("Current Password", type="password", key="curr_p")
        new = st.text_input("New Password", type="password", key="new_p")
        confirm = st.text_input("Confirm Password", type="password", key="conf_p")
        if st.button("Update Password"):
            if not check_password(current, users[st.session_state.user]["password"]):
                st.error("Wrong Current Password")
            elif new != confirm:
                st.error("Passwords do not match")
            else:
                users[st.session_state.user]["password"] = hash_password(new)
                save_users(users)
                st.success("Updated successfully")

def admin_panel():
    st.markdown("---")
    st.subheader("🛠️ Admin Panel")
    users = load_users()
    
    # Display Users
    st.write("**Current Users:**")
    st.table(pd.DataFrame([{"User ID": k, "Role": v["role"]} for k, v in users.items()]))

    # Add User
    col1, col2 = st.columns(2)
    with col1:
        new_user = st.text_input("New User ID")
        new_pass = st.text_input("Initial Password", type="password")
        if st.button("Add User"):
            if new_user and new_pass:
                users[new_user] = {"password": hash_password(new_pass), "role": "user"}
                save_users(users)
                st.success(f"Added {new_user}")
                st.rerun()

    # Delete User
    with col2:
        delete = st.selectbox("Select User to Delete", [u for u in users.keys() if u != 'admin'])
        confirm = st.checkbox("I am sure")
        if st.button("Delete User"):
            if confirm:
                del users[delete]
                save_users(users)
                st.success("Deleted")
                st.rerun()

# ---------------------------------------------------
# STOCK DASHBOARD

def dashboard():
    st.title("📊 Live Prices with P2L")
    
    stocks = {"CANBK.NS": 142.93, "DLF.NS": 646.85}

    @st.cache_data(ttl=60)
    def fetch():
        data = yf.download(list(stocks.keys()), period="2d", interval="1d", group_by="ticker", progress=False)
        rows = []
        for s in stocks:
            price = data[s]["Close"].iloc[-1]
            p2l = ((price - stocks[s]) / stocks[s]) * 100
            rows.append({
                "Stock": s.replace(".NS",""),
                "Price": round(price, 2),
                "Buy Price": stocks[s],
                "P2L %": round(p2l, 2)
            })
        return pd.DataFrame(rows)

    df = fetch()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Display table
    st.table(df)
    
    avg_p2l = df["P2L %"].mean()
    st.metric("Total Average P2L", f"{avg_p2l:.2f}%")

# ---------------------------------------------------
# MAIN EXECUTION FLOW

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    # Sidebar
    st.sidebar.title(f"👤 {st.session_state.user}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # Layout
    dashboard()
    change_password()
    
    if st.session_state.role == "admin":
        admin_panel()
