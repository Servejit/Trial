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

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    FILE_PATH = "users.json"
except Exception:
    st.error("Missing Secrets! Check BOT_TOKEN, CHAT_ID, GITHUB_TOKEN, REPO_NAME in Streamlit Settings.")
    st.stop()

# ---------------------------------------------------
# PAGE CONFIG
st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ---------------------------------------------------
# DATA PERSISTENCE

def load_users():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        file = repo.get_contents(FILE_PATH)
        return json.loads(file.decoded_content.decode())
    except:
        # Default fallback
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
# AUTH FUNCTIONS

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
# ORIGINAL STOCK DASHBOARD RESTORED

def dashboard():
    st.title("📊 Live Prices with P2L")

    # STOCKSTAR INPUT
    stockstar_input = st.text_input(
        "⭐ StockStar",
        "DLF.NS, CANBK.NS"
    ).upper()

    stockstar_list = [
        s.replace(".NS","").strip()
        for s in stockstar_input.split(",")
    ]

    # TOGGLES
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        sound = st.toggle("Sound Alert")
    with col_t2:
        telegram = st.toggle("Telegram Alert")

    # STOCK LIST (Buy Prices)
    stocks = {
        "CANBK.NS": 142.93,
        "DLF.NS": 646.85
    }

    # FETCH FUNCTION
    @st.cache_data(ttl=60)
    def fetch():
        data = yf.download(
            list(stocks.keys()),
            period="2d",
            interval="1d",
            group_by="ticker",
            progress=False
        )
        rows = []
        for s in stocks:
            try:
                price = data[s]["Close"].iloc[-1]
                p2l = ((price - stocks[s]) / stocks[s]) * 100
                rows.append({
                    "Stock": s.replace(".NS",""),
                    "Price": round(price, 2),
                    "P2L %": round(p2l, 2)
                })
            except:
                continue
        return pd.DataFrame(rows)

    # BUTTONS
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        sort = st.button("Sort")

    # LOAD & SHOW DATA
    df = fetch()

    if sort:
        df = df.sort_values("P2L %")

    # Display using the original dataframe format
    st.dataframe(df, use_container_width=True)

    # AVERAGE
    st.write(
        "**Average P2L%:**",
        round(df["P2L %"].mean(), 2)
    )

# ---------------------------------------------------
# LOGIN & ADMIN UI

def login_page():
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
    reset_user = st.text_input("User ID", key="reset_user")
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
    st.subheader("Change Password")
    users = load_users()
    current = st.text_input("Current Password", type="password", key="cp1")
    new = st.text_input("New Password", type="password", key="cp2")
    confirm = st.text_input("Confirm Password", type="password", key="cp3")
    if st.button("Update Password"):
        if not check_password(current, users[st.session_state.user]["password"]):
            st.error("Wrong Password")
        elif new != confirm:
            st.error("Mismatch")
        else:
            users[st.session_state.user]["password"] = hash_password(new)
            save_users(users)
            st.success("Updated")

def admin_panel():
    st.markdown("---")
    st.subheader("Admin Panel")
    users = load_users()
    st.table(list(users.keys()))
    
    new_user = st.text_input("New User")
    new_pass = st.text_input("New Password", type="password", key="np")
    if st.button("Add User"):
        users[new_user] = {"password": hash_password(new_pass), "role": "user"}
        save_users(users)
        st.success("User Added")
        st.rerun()

    delete = st.selectbox("Delete User", list(users.keys()))
    confirm_del = st.checkbox("Confirm Delete")
    if st.button("Delete"):
        if delete == "admin":
            st.error("Cannot delete admin")
        elif confirm_del:
            del users[delete]
            save_users(users)
            st.success("Deleted")
            st.rerun()

# ---------------------------------------------------
# MAIN LOGIC

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.write("Welcome", st.session_state.user)
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    dashboard()
    st.markdown("---")
    change_password()
    
    if st.session_state.role == "admin":
        admin_panel()
