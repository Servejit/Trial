# ---------------------------------------------------
# INSTALL REQUIREMENTS
# pip install streamlit yfinance pandas bcrypt
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import bcrypt
import json
import time

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ---------------------------------------------------
# USER FILE
# ---------------------------------------------------

USER_FILE = "users.json"


# ---------------------------------------------------
# LOAD USERS
# ---------------------------------------------------

def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


# ---------------------------------------------------
# PASSWORD HASH
# ---------------------------------------------------

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------
# SESSION INIT
# ---------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "page" not in st.session_state:
    st.session_state.page = "login"


# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------

def login():

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        users = load_users()

        if username in users and check_password(password, users[username]):

            st.session_state.logged_in = True
            st.session_state.user = username
            st.session_state.page = "dashboard"

            st.rerun()

        else:
            st.error("Invalid Login")


# ---------------------------------------------------
# REGISTER
# ---------------------------------------------------

def register():

    st.title("📝 Register")

    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")

    if st.button("Create Account"):

        users = load_users()

        if username in users:
            st.error("User exists")
        else:

            users[username] = hash_password(password)
            save_users(users)

            st.success("Created")


# ---------------------------------------------------
# CHANGE PASSWORD
# ---------------------------------------------------

def change_password():

    st.title("🔑 Change Password")

    old = st.text_input("Old Password", type="password")
    new = st.text_input("New Password", type="password")

    if st.button("Change"):

        users = load_users()

        if check_password(old, users[st.session_state.user]):

            users[st.session_state.user] = hash_password(new)
            save_users(users)

            st.success("Changed")

        else:
            st.error("Wrong password")


# ---------------------------------------------------
# STOCK LIST (SAME)
# ---------------------------------------------------

stocks = {

"RELIANCE.NS": 2500,
"HDFCBANK.NS": 1500,
"ICICIBANK.NS": 900,
"INFY.NS": 1400,
"TCS.NS": 3300,

}


stockstar = {

"RELIANCE.NS": 2400,
"HDFCBANK.NS": 1400,

}


# ---------------------------------------------------
# DATA FETCH
# ---------------------------------------------------

def get_data():

    data = []

    for s, buy in stocks.items():

        price = yf.Ticker(s).history(period="1d")["Close"].iloc[-1]

        pnl = price - buy
        percent = pnl / buy * 100

        data.append([s, buy, price, pnl, percent])

    df = pd.DataFrame(data, columns=["Stock","Buy","Price","P2L","%"])

    return df


# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------

def stock_dashboard():

    st.title("📊 Live Prices with P2L")

    st.write(f"Welcome **{st.session_state.user}**")

    col1,col2,col3 = st.columns(3)

    refresh = col1.button("🔄 Refresh")

    sort = col2.button("Sort by P2L")

    logout = col3.button("Logout")


    if logout:

        st.session_state.logged_in=False
        st.rerun()


    df = get_data()


    if sort:
        df = df.sort_values("P2L", ascending=False)


    st.dataframe(df, use_container_width=True)


    # Bottom Average

    avg = df["P2L"].mean()

    st.write("")

    st.subheader(f"Average P2L : {avg:.2f}")


# ---------------------------------------------------
# MAIN CONTROL
# ---------------------------------------------------

if st.session_state.logged_in:

    menu = st.sidebar.selectbox("Menu",

    ["Dashboard","Change Password"])

    if menu=="Dashboard":
        stock_dashboard()

    if menu=="Change Password":
        change_password()

else:

    menu = st.sidebar.selectbox("Menu",

    ["Login","Register"])

    if menu=="Login":
        login()

    if menu=="Register":
        register()
