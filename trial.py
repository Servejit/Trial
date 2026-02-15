# ============================================================
# FINAL PRO STOCK APP
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import bcrypt
import json
import os
import time

st.set_page_config(page_title="Stock App", layout="wide")

# ============================================================
# USER DATABASE
# ============================================================

USER_FILE = "users.json"


def load_users():

    if not os.path.exists(USER_FILE):

        default = {

            "admin": {

                "password": hash_password("admin123"),
                "role": "admin"
            }

        }

        save_users(default)

    with open(USER_FILE, "r") as f:
        return json.load(f)


def save_users(users):

    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def hash_password(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def check_password(password, hashed):

    if isinstance(hashed, str):
        hashed = hashed.encode()

    return bcrypt.checkpw(
        password.encode(),
        hashed
    )


# ============================================================
# SESSION INIT
# ============================================================

if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "role" not in st.session_state:
    st.session_state.role = ""


# ============================================================
# LOGIN
# ============================================================

def login():

    st.title("🔐 Login")

    username = st.text_input("User ID")

    password = st.text_input("Password", type="password")

    if st.button("Login"):

        users = load_users()

        if username in users and check_password(password, users[username]["password"]):

            st.session_state.logged = True
            st.session_state.user = username
            st.session_state.role = users[username]["role"]

            st.rerun()

        else:

            st.error("Invalid Login")


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password():

    st.subheader("Change Password")

    current = st.text_input("Current Password", type="password", key="c1")

    new = st.text_input("New Password", type="password", key="c2")

    confirm = st.text_input("Confirm Password", type="password", key="c3")

    if st.button("Update Password"):

        users = load_users()

        if check_password(current, users[st.session_state.user]["password"]):

            if new == confirm:

                users[st.session_state.user]["password"] = hash_password(new)

                save_users(users)

                st.success("Password Updated")

            else:

                st.error("Mismatch")

        else:

            st.error("Wrong Password")


# ============================================================
# ADMIN PANEL
# ============================================================

def admin_panel():

    st.subheader("Admin Panel")

    new_user = st.text_input("New User", key="newuser")

    new_pass = st.text_input("New Password", type="password", key="newpass")

    if st.button("Add User"):

        users = load_users()

        users[new_user] = {

            "password": hash_password(new_pass),
            "role": "user"

        }

        save_users(users)

        st.success("User Added")


# ============================================================
# STOCK LIST (YOUR ORIGINAL)
# ============================================================

stocks = {

"RELIANCE.NS": 2450,
"HDFCBANK.NS": 1520,
"INFY.NS": 1450,
"ICICIBANK.NS": 950,

}

stockstar = [

"RELIANCE.NS",
"INFY.NS"

]


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.title("📊 Live Stock Dashboard")

    col1, col2 = st.columns(2)

    if col1.button("🔄 Refresh"):
        st.rerun()

    sort = col2.selectbox("Sort", ["None", "P2L %"])

    data = []

    for s, price in stocks.items():

        try:

            live = yf.download(
                s,
                period="1d",
                interval="1m",
                progress=False
            )["Close"].iloc[-1]

        except:

            live = price

        pnl = live - price

        pnl_pct = pnl / price * 100

        data.append([

            s,
            price,
            live,
            round(pnl, 2),
            round(pnl_pct, 2)

        ])

    df = pd.DataFrame(

        data,
        columns=[
            "Stock",
            "Buy",
            "Live",
            "P2L",
            "P2L %"
        ]

    )

    if sort == "P2L %":

        df = df.sort_values("P2L %")

    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )

    avg = df["P2L %"].mean()

    st.subheader(f"Average P2L : {round(avg,2)} %")

    st.subheader("⭐ StockStar")

    st.write(stockstar)


# ============================================================
# MAIN
# ============================================================

if not st.session_state.logged:

    login()

else:

    st.sidebar.write(f"Welcome {st.session_state.user}")

    if st.sidebar.button("Logout"):

        st.session_state.logged = False

        st.rerun()

    change_password()

    if st.session_state.role == "admin":

        admin_panel()

    dashboard()
