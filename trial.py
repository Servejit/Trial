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
GITHUB_TOKEN = "8371973661:AAFTOjh53yKmmgv3eXqD5wf8Ki6XXrZPq2c"
REPO_NAME = "Servejit/Trial"
FILE_PATH = "users.json"

# ---------------------------------------------------
# PAGE CONFIG
st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ---------------------------------------------------
# LOAD USERS
def load_users():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    try:
        file = repo.get_contents(FILE_PATH)
        return json.loads(file.decoded_content.decode())
    except:
        return {}

# ---------------------------------------------------
# SAVE USERS
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

# ---------------------------------------------------
# OTP FUNCTION
def send_otp():
    otp = str(random.randint(100000, 999999))
    st.session_state.reset_otp = otp
    st.session_state.otp_time = time.time()
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": f"🔐 Password Reset OTP: {otp}"}
    )

# ---------------------------------------------------
# SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# ---------------------------------------------------
# LOGIN
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

# ---------------------------------------------------
# CHANGE PASSWORD
def change_password():
    st.subheader("Change Password")
    users = load_users()
    current = st.text_input("Current Password", type="password")
    new = st.text_input("New Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Update Password"):
        if not check_password(current, users[st.session_state.user]["password"]):
            st.error("Wrong Password")
        elif new != confirm:
            st.error("Mismatch")
        else:
            users[st.session_state.user]["password"] = hash_password(new)
            save_users(users)
            st.success("Updated")

# ---------------------------------------------------
# ADMIN PANEL
def admin_panel():
    st.subheader("Admin Panel")
    users = load_users()
    st.table(list(users.keys()))

    # ADD USER
    new_user = st.text_input("New User")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Add User"):
        users[new_user] = {"password": hash_password(new_pass), "role": "user"}
        save_users(users)
        st.success("User Added")
        st.rerun()

    # DELETE USER SAFE
    delete = st.selectbox("Delete User", list(users.keys()))
    confirm = st.checkbox("Confirm Delete")
    if st.button("Delete"):
        if delete == "admin":
            st.error("Cannot delete admin")
        elif confirm:
            del users[delete]
            save_users(users)
            st.success("Deleted")
            st.rerun()

# ---------------------------------------------------
# STOCK DASHBOARD
def dashboard():
    st.title("📊 Live Prices with P2L")

    # STOCKSTAR INPUT
    stockstar_input = st.text_input("⭐ StockStar", "DLF.NS, CANBK.NS").upper()
    stockstar_list = [s.replace(".NS","").strip() for s in stockstar_input.split(",")]

    # SOUND & TELEGRAM TOGGLE
    sound = st.toggle("Sound Alert")
    telegram = st.toggle("Telegram Alert")

    # STOCK LIST
    stocks = {"CANBK.NS":142.93, "DLF.NS":646.85}

    # FETCH DATA
    @st.cache_data(ttl=60)
    def fetch():
        data = yf.download(list(stocks.keys()), period="2d", interval="1d", group_by="ticker")
        rows=[]
        for s in stocks:
            price = data[s]["Close"].iloc[-1]
            p2l = ((price-stocks[s])/stocks[s])*100
            rows.append({"Stock": s.replace(".NS",""), "Price": price, "P2L %": p2l})
        return pd.DataFrame(rows)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        sort = st.button("Sort")

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
    if st.sidebar.button("Logout"):
        st.session_state.logged_in=False
        st.rerun()
    change_password()
    if st.session_state.role=="admin":
        admin_panel()
    dashboard()
