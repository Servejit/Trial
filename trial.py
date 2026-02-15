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
from github import Github

# ---------------------------------------------------
# TELEGRAM SETTINGS
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"

# ---------------------------------------------------
# GITHUB SETTINGS
GITHUB_TOKEN = "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"
REPO_NAME = "Servejit/Trial"
FILE_PATH = "users.json"

# ---------------------------------------------------
# PAGE CONFIG
st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ---------------------------------------------------
# SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# ---------------------------------------------------
# LOAD & SAVE USERS
def load_users():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        file = repo.get_contents(FILE_PATH)
        return json.loads(file.decoded_content.decode())
    except:
        return {}

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
# PASSWORD FUNCTIONS
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
# LOGIN
def login():
    st.title("🔐 Login")
    users = load_users()
    username = st.text_input("User ID", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):
        if username in users and check_password(password, users[username]["password"]):
            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.role = users[username]["role"]
            st.rerun()
        else:
            st.error("Invalid Login")

    st.markdown("---")
    st.subheader("Forgot Password")
    reset_user = st.text_input("User ID", key="reset_user_input")
    if st.button("Send OTP", key="send_otp_btn"):
        if reset_user in users:
            send_otp()
            st.success("OTP sent to Telegram")
        else:
            st.error("User not found")

    otp = st.text_input("Enter OTP", key="otp_input")
    new_pass = st.text_input("New Password", type="password", key="otp_new_pass")
    if st.button("Reset Password", key="reset_pass_btn"):
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
            st.session_state["otp_input"] = ""
            st.session_state["otp_new_pass"] = ""

# ---------------------------------------------------
# CHANGE PASSWORD
def change_password():
    st.subheader("Change Password")
    users = load_users()
    
    current = st.text_input("Current Password", type="password", key="change_curr_pass")
    new = st.text_input("New Password", type="password", key="change_new_pass")
    confirm = st.text_input("Confirm Password", type="password", key="change_conf_pass")
    
    if st.button("Update Password", key="change_update_btn"):
        if not check_password(current, users[st.session_state.user]["password"]):
            st.error("Wrong Password")
        elif new != confirm:
            st.error("Mismatch")
        else:
            users[st.session_state.user]["password"] = hash_password(new)
            save_users(users)
            st.success("Password Updated")
            # Clear input fields
            st.session_state["change_curr_pass"] = ""
            st.session_state["change_new_pass"] = ""
            st.session_state["change_conf_pass"] = ""

# ---------------------------------------------------
# ADMIN PANEL
def admin_panel():
    st.subheader("Admin Panel")
    users = load_users()
    st.table(list(users.keys()))

    # ADD USER
    new_user = st.text_input("New User", key="admin_new_user_input")
    new_pass = st.text_input("New Password", type="password", key="admin_new_pass_input")
    if st.button("Add User", key="admin_add_user_btn"):
        if new_user and new_pass:
            users[new_user] = {"password": hash_password(new_pass), "role": "user"}
            save_users(users)
            st.success(f"User '{new_user}' Added")
            st.session_state["admin_new_user_input"] = ""
            st.session_state["admin_new_pass_input"] = ""
            st.rerun()

    # DELETE USER SAFE
    delete = st.selectbox("Delete User", [u for u in users.keys() if u != "admin"], key="admin_delete_select")
    confirm = st.checkbox("Confirm Delete", key="admin_delete_confirm")
    if st.button("Delete User", key="admin_delete_btn"):
        if confirm:
            del users[delete]
            save_users(users)
            st.success(f"User '{delete}' Deleted")
            st.rerun()

# ---------------------------------------------------
# STOCK DASHBOARD
def dashboard():
    st.title("📊 Live Prices with P2L")

    stockstar_input = st.text_input("⭐ StockStar", "DLF.NS, CANBK.NS", key="stockstar_input").upper()
    stockstar_list = [s.replace(".NS","").strip() for s in stockstar_input.split(",")]

    sound = st.toggle("Sound Alert", key="sound_toggle")
    telegram = st.toggle("Telegram Alert", key="telegram_toggle")

    stocks = {"CANBK.NS":142.93, "DLF.NS":646.85}

    @st.cache_data(ttl=60)
    def fetch():
        data = yf.download(list(stocks.keys()), period="2d", interval="1d", group_by="ticker")
        rows=[]
        for s in stocks:
            price = data[s]["Close"].iloc[-1]
            p2l = ((price-stocks[s])/stocks[s])*100
            rows.append({"Stock": s.replace(".NS",""), "Price": price, "P2L %": round(p2l,2)})
        return pd.DataFrame(rows)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh", key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        sort = st.button("Sort", key="sort_btn")

    df = fetch()
    if sort:
        df = df.sort_values("P2L %")
    
    st.dataframe(df)
    st.write("Average:", round(df["P2L %"].mean(),2))

# ---------------------------------------------------
# MAIN
if not st.session_state.logged_in:
    login()
else:
    st.sidebar.write("Welcome", st.session_state.user)
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.logged_in=False
        st.rerun()
    change_password()
    if st.session_state.role=="admin":
        admin_panel()
    dashboard()
