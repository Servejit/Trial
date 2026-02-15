# =========================================================
# INSTALL
# pip install streamlit yfinance pandas requests bcrypt
# =========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import bcrypt
import json
import os
import base64

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# =========================================================
# FILES
# =========================================================

USER_FILE="users.json"
SESSION_FILE="session.json"

# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# =========================================================
# USER DATABASE
# =========================================================

def load_users():

    if not os.path.exists(USER_FILE):

        users={
            "admin":{
                "password":hash_password("admin123"),
                "role":"admin"
            }
        }

        save_users(users)

    with open(USER_FILE) as f:
        return json.load(f)


def save_users(users):

    with open(USER_FILE,"w") as f:
        json.dump(users,f)

# =========================================================
# SESSION
# =========================================================

def save_session(user):

    with open(SESSION_FILE,"w") as f:
        json.dump({"user":user},f)


def load_session():

    if os.path.exists(SESSION_FILE):

        with open(SESSION_FILE) as f:
            return json.load(f)["user"]

    return None


def clear_session():

    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

# =========================================================
# LOGIN
# =========================================================

def login():

    st.title("🔐 Login")

    user=st.text_input("User ID")

    password=st.text_input("Password",type="password")

    remember=st.checkbox("Remember Me")

    if st.button("Login"):

        users=load_users()

        if user in users and check_password(password, users[user]["password"]):

            st.session_state.logged=True
            st.session_state.user=user
            st.session_state.role=users[user]["role"]

            if remember:
                save_session(user)

            st.rerun()

        else:
            st.error("Invalid Login")

# =========================================================
# AUTO LOGIN
# =========================================================

def auto_login():

    saved=load_session()

    if saved:

        users=load_users()

        if saved in users:

            st.session_state.logged=True
            st.session_state.user=saved
            st.session_state.role=users[saved]["role"]

# =========================================================
# CHANGE PASSWORD
# =========================================================

def change_password():

    st.subheader("🔑 Change Password")

    old=st.text_input("Current",type="password")

    new=st.text_input("New",type="password")

    confirm=st.text_input("Confirm",type="password")

    if st.button("Update Password"):

        users=load_users()

        if not check_password(old, users[st.session_state.user]["password"]):

            st.error("Wrong Password")

        elif new!=confirm:

            st.error("Mismatch")

        else:

            users[st.session_state.user]["password"]=hash_password(new)

            save_users(users)

            st.success("Updated")

# =========================================================
# ADMIN PANEL
# =========================================================

def admin_panel():

    st.subheader("👨‍💼 Admin Panel")

    new_user=st.text_input("New User")

    new_pass=st.text_input("Password",type="password")

    if st.button("Add User"):

        users=load_users()

        users[new_user]={
            "password":hash_password(new_pass),
            "role":"user"
        }

        save_users(users)

        st.success("User Added")

# =========================================================
# ORIGINAL STOCK DASHBOARD
# =========================================================

def dashboard():

    st.title("📊 Live Prices with P2L")

    st.write(f"Welcome **{st.session_state.user}**")

    if st.button("Logout"):

        clear_session()

        st.session_state.logged=False

        st.rerun()

    # CSS

    st.markdown("""

    <style>

    @keyframes flash {
        0% {opacity:1;}
        50% {opacity:0.2;}
        100% {opacity:1;}
    }

    table {
        background-color:#0e1117;
        color:white;
        width:100%;
        border-collapse: collapse;
    }

    th, td {
        padding:6px;
        border:1px solid #444;
        text-align:center;
    }

    </style>

    """, unsafe_allow_html=True)


    # ORIGINAL STOCKSTAR INPUT

    stockstar_input=st.text_input(

        "⭐ StockStar (Comma Separated)",
        "DLF.NS, CANBK.NS"

    ).upper()


    stockstar_list=[
        s.strip().replace(".NS","")
        for s in stockstar_input.split(",")
    ]


    sound_alert=st.toggle("🔊 Enable Alert Sound")

    telegram_alert=st.toggle("📲 Enable Telegram Alert")

    upload=st.file_uploader("Upload Sound")

    DEFAULT="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"


    # ORIGINAL STOCK LIST

    stocks={

    "CANBK.NS":142.93,
    "CHOLAFIN.NS":1690.51,
    "COALINDIA.NS":414.07,
    "DLF.NS":646.85,
    "HCLTECH.NS":1465.83,
    "IDFCFIRSTB.NS":80.84,
    "INFY.NS":1377.05,
    "MPHASIS.NS":2445.51,
    "NHPC.NS":75.78,
    "OIL.NS":468.65,
    "PAGEIND.NS":33501.65,
    "PERSISTENT.NS":5417.42,
    "PNB.NS":119.90,

    }


    BOT_TOKEN="PASTE"
    CHAT_ID="PASTE"


    @st.cache_data(ttl=60)
    def fetch():

        data=yf.download(list(stocks.keys()),period="2d",interval="1d")

        rows=[]

        for sym in stocks:

            ref=stocks[sym]

            price=data["Close"][sym].iloc[-1]

            prev=data["Close"][sym].iloc[-2]

            openp=data["Open"][sym].iloc[-1]
            high=data["High"][sym].iloc[-1]
            low=data["Low"][sym].iloc[-1]

            p2l=((price-ref)/ref)*100
            chg=((price-prev)/prev)*100

            rows.append({

                "Stock":sym.replace(".NS",""),
                "P2L %":p2l,
                "Price":price,
                "% Chg":chg,
                "Low Price":ref,
                "Open":openp,
                "High":high,
                "Low":low

            })

        return pd.DataFrame(rows)


    df=fetch()


    # ORIGINAL HTML TABLE

    html="<table><tr>"

    for col in df.columns:
        html+=f"<th>{col}</th>"

    html+="</tr>"


    trigger=False
    trigger_stock=""


    for _,row in df.iterrows():

        html+="<tr>"

        for col in df.columns:

            value=row[col]

            style=""

            if col=="Stock":

                if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                    style="color:green;font-weight:bold;animation:flash 1s infinite;"
                    trigger=True
                    trigger_stock=row["Stock"]

                elif row["Stock"] in stockstar_list and row["P2L %"]<-3:

                    style="color:orange;font-weight:bold;"

                elif row["P2L %"]<-2:

                    style="color:hotpink;font-weight:bold;"


            if isinstance(value,float):
                value=f"{value:.2f}"

            html+=f"<td style='{style}'>{value}</td>"

        html+="</tr>"

    html+="</table>"


    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# MAIN
# =========================================================

if "logged" not in st.session_state:

    st.session_state.logged=False

    auto_login()


if st.session_state.logged:

    dashboard()

    change_password()

    if st.session_state.role=="admin":

        admin_panel()

else:

    login()
