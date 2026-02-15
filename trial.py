# ====================================================
# INSTALL
# pip install streamlit yfinance pandas requests bcrypt
# ====================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import bcrypt
import json
import os

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")

# ====================================================
# LOGIN SYSTEM
# ====================================================

USER_FILE="users.json"

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def load_users():

    if not os.path.exists(USER_FILE):

        users={
            "admin":{
                "password":hash_password("admin123"),
                "role":"admin"
            }
        }

        with open(USER_FILE,"w") as f:
            json.dump(users,f)

    with open(USER_FILE) as f:
        return json.load(f)

def login():

    st.title("🔐 Login")

    user=st.text_input("User ID")

    password=st.text_input("Password",type="password")

    if st.button("Login"):

        users=load_users()

        if user in users and check_password(password, users[user]["password"]):

            st.session_state.logged=True
            st.session_state.user=user
            st.session_state.role=users[user]["role"]

            st.rerun()

        else:

            st.error("Invalid Login")

# ====================================================
# ORIGINAL DASHBOARD (UNCHANGED)
# ====================================================

def dashboard():

    st.title("📊 Live Prices with P2L")

    st.write(f"Welcome **{st.session_state.user}**")

    if st.button("Logout"):

        st.session_state.logged=False

        st.rerun()

    # ORIGINAL CSS

    st.markdown("""
    <style>
    @keyframes flash {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    table {
        background-color:#0e1117;
        color:white;
    }
    </style>
    """, unsafe_allow_html=True)

    # STOCKSTAR INPUT ORIGINAL

    stockstar_input = st.text_input(
        "⭐ StockStar (Comma Separated)",
        "DLF.NS, CANBK.NS"
    ).upper()

    stockstar_list = [
        s.strip().replace(".NS", "")
        for s in stockstar_input.split(",")
        if s.strip() != ""
    ]

    # SOUND TOGGLE

    sound_alert = st.toggle(
        "🔊 Enable Alert Sound for -5% Green Stocks",
        value=False
    )

    telegram_alert = st.toggle(
        "📲 Enable Telegram Alert for Green Flashing",
        value=False
    )

    uploaded_sound = st.file_uploader(
        "Upload Sound",
        type=["mp3","wav"]
    )

    DEFAULT_SOUND_URL="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

    # ORIGINAL STOCK LIST

    stocks = {

        "CANBK.NS": 142.93,
        "CHOLAFIN.NS": 1690.51,
        "COALINDIA.NS": 414.07,
        "DLF.NS": 646.85,
        "HCLTECH.NS": 1465.83,
        "IDFCFIRSTB.NS": 80.84,
        "INFY.NS": 1377.05,
        "MPHASIS.NS": 2445.51,
        "NHPC.NS": 75.78,
        "OIL.NS": 468.65,
        "PAGEIND.NS": 33501.65,
        "PERSISTENT.NS": 5417.42,
        "PNB.NS": 119.90,

    }

    BOT_TOKEN="PASTE"
    CHAT_ID="PASTE"

    # FETCH DATA ORIGINAL

    @st.cache_data(ttl=60)
    def fetch_data():

        symbols=list(stocks.keys())

        data=yf.download(
            tickers=symbols,
            period="2d",
            interval="1d",
            group_by="ticker",
            progress=False,
            threads=True
        )

        rows=[]

        for sym in symbols:

            try:

                ref_low=stocks[sym]

                price=data[sym]["Close"].iloc[-1]
                prev_close=data[sym]["Close"].iloc[-2]
                open_p=data[sym]["Open"].iloc[-1]
                high=data[sym]["High"].iloc[-1]
                low=data[sym]["Low"].iloc[-1]

                p2l=((price-ref_low)/ref_low)*100
                pct_chg=((price-prev_close)/prev_close)*100

                rows.append({

                    "Stock": sym.replace(".NS",""),
                    "P2L %": p2l,
                    "Price": price,
                    "% Chg": pct_chg,
                    "Low Price": ref_low,
                    "Open": open_p,
                    "High": high,
                    "Low": low

                })

            except:
                pass

        return pd.DataFrame(rows)

    df=fetch_data()

    # ====================================================
    # ORIGINAL HTML TABLE FUNCTION
    # ====================================================

    def generate_html_table(dataframe):

        html="""
        <table style="width:100%; border-collapse: collapse;">
        <tr style="background-color:#111;">
        """

        for col in dataframe.columns:

            html+=f"<th style='padding:8px; border:1px solid #444;'>{col}</th>"

        html+="</tr>"

        green_trigger=False
        trigger_stock=""

        for _,row in dataframe.iterrows():

            html+="<tr>"

            for col in dataframe.columns:

                value=row[col]

                style="padding:6px; border:1px solid #444; text-align:center;"

                if col=="Stock":

                    if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                        style+="color:green;font-weight:bold;animation:flash 1s infinite;"
                        green_trigger=True
                        trigger_stock=row["Stock"]

                    elif row["Stock"] in stockstar_list and row["P2L %"]<-3:

                        style+="color:orange;font-weight:bold;"

                    elif row["P2L %"]<-2:

                        style+="color:hotpink;font-weight:bold;"

                if col in ["P2L %","% Chg"]:

                    if value>0:
                        style+="color:green;font-weight:bold;"

                    elif value<0:
                        style+="color:red;font-weight:bold;"

                if isinstance(value,float):

                    value=f"{value:.2f}"

                html+=f"<td style='{style}'>{value}</td>"

            html+="</tr>"

        html+="</table>"

        return html,green_trigger,trigger_stock


    html,green_trigger,trigger_stock=generate_html_table(df)

    st.markdown(html, unsafe_allow_html=True)

# ====================================================
# MAIN
# ====================================================

if "logged" not in st.session_state:

    st.session_state.logged=False

if st.session_state.logged:

    dashboard()

else:

    login()
