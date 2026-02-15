# ---------------------------------------------------
# INSTALL
# pip install streamlit yfinance pandas requests bcrypt
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import bcrypt
import json
import os
from datetime import datetime


# ===================================================
# LOGIN SYSTEM (NEW ADDITION)
# ===================================================

USER_FILE = "users.json"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):

    if isinstance(hashed, str):
        hashed = hashed.encode()

    return bcrypt.checkpw(password.encode(), hashed)


def load_users():

    if not os.path.exists(USER_FILE):

        users = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "admin"
            }
        }

        with open(USER_FILE, "w") as f:
            json.dump(users, f)

    with open(USER_FILE, "r") as f:
        return json.load(f)


def save_users(users):

    with open(USER_FILE, "w") as f:
        json.dump(users, f)


if "logged" not in st.session_state:
    st.session_state.logged = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "role" not in st.session_state:
    st.session_state.role = ""


def login_page():

    st.title("🔐 Login Required")

    u = st.text_input("User ID")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        users = load_users()

        if u in users and check_password(p, users[u]["password"]):

            st.session_state.logged = True
            st.session_state.user = u
            st.session_state.role = users[u]["role"]

            st.rerun()

        else:

            st.error("Invalid Login")


def change_password():

    st.sidebar.subheader("🔑 Change Password")

    c = st.sidebar.text_input("Current", type="password")
    n = st.sidebar.text_input("New", type="password")
    cf = st.sidebar.text_input("Confirm", type="password")

    if st.sidebar.button("Update Password"):

        users = load_users()

        if check_password(c, users[st.session_state.user]["password"]):

            if n == cf:

                users[st.session_state.user]["password"] = hash_password(n)

                save_users(users)

                st.sidebar.success("Updated")

            else:
                st.sidebar.error("Mismatch")

        else:
            st.sidebar.error("Wrong Password")


def admin_panel():

    if st.session_state.role != "admin":
        return

    st.sidebar.subheader("👨‍💼 Admin Panel")

    nu = st.sidebar.text_input("New User")

    np = st.sidebar.text_input("New Password", type="password")

    if st.sidebar.button("Add User"):

        users = load_users()

        users[nu] = {
            "password": hash_password(np),
            "role": "user"
        }

        save_users(users)

        st.sidebar.success("User Added")


# ===================================================
# STOP APP IF NOT LOGGED
# ===================================================

if not st.session_state.logged:

    login_page()

    st.stop()


# Sidebar welcome
st.sidebar.write(f"Welcome **{st.session_state.user}**")

if st.sidebar.button("Logout"):

    st.session_state.logged = False
    st.rerun()

change_password()

admin_panel()


# ===================================================
# YOUR ORIGINAL CODE STARTS (NO CHANGE BELOW)
# ===================================================


st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")


# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"


# ---------------------------------------------------
# FLASHING CSS

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


# ---------------------------------------------------
# STOCKSTAR INPUT

stockstar_input = st.text_input(
    "⭐ StockStar (Comma Separated)",
    "DLF.NS, CANBK.NS"
).upper()


stockstar_list = [
    s.strip().replace(".NS", "")
    for s in stockstar_input.split(",")
    if s.strip() != ""
]


# ---------------------------------------------------
# SOUND SETTINGS

sound_alert = st.toggle("🔊 Enable Alert Sound for -5% Green Stocks", value=False)


# ---------------------------------------------------
# TELEGRAM ALERT TOGGLE

telegram_alert = st.toggle("📲 Enable Telegram Alert for Green Flashing", value=False)


# ---------------------------------------------------
# SOUND UPLOAD

st.markdown("### 🎵 Alert Sound Settings")


uploaded_sound = st.file_uploader(
    "Upload Your Custom Sound (.mp3 or .wav)",
    type=["mp3", "wav"]
)


DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"


# ---------------------------------------------------
# STOCK LIST

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


# ---------------------------------------------------
# FETCH DATA

@st.cache_data(ttl=60)
def fetch_data():

    symbols = list(stocks.keys())

    data = yf.download(
        tickers=symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True
    )

    rows = []

    for sym in symbols:

        try:

            ref_low = stocks[sym]

            price = data[sym]["Close"].iloc[-1]
            prev_close = data[sym]["Close"].iloc[-2]
            open_p = data[sym]["Open"].iloc[-1]
            high = data[sym]["High"].iloc[-1]
            low = data[sym]["Low"].iloc[-1]

            p2l = ((price - ref_low) / ref_low) * 100
            pct_chg = ((price - prev_close) / prev_close) * 100

            rows.append({
                "Stock": sym.replace(".NS", ""),
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


# ---------------------------------------------------
# BUTTONS

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

with col2:
    sort_clicked = st.button("📈 Sort by P2L")


# ---------------------------------------------------
# LOAD DATA

df = fetch_data()

if df.empty:
    st.error("⚠️ No data received from Yahoo Finance.")
    st.stop()


numeric_cols = ["P2L %", "Price", "% Chg", "Low Price", "Open", "High", "Low"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")


if sort_clicked:
    df = df.sort_values("P2L %", ascending=False)


# ---------------------------------------------------
# GREEN TRIGGER CHECK

green_trigger = False
trigger_stock = ""
trigger_price = 0
trigger_p2l = 0

for _, row in df.iterrows():

    if row["Stock"] in stockstar_list and row["P2L %"] < -5:

        green_trigger = True
        trigger_stock = row["Stock"]
        trigger_price = row["Price"]
        trigger_p2l = row["P2L %"]
        break


# ---------------------------------------------------
# ALERT MEMORY STATE

if "alert_played" not in st.session_state:
    st.session_state.alert_played = False

if not green_trigger:
    st.session_state.alert_played = False


# ---------------------------------------------------
# TELEGRAM ALERT

if telegram_alert and green_trigger and not st.session_state.alert_played:

    current_time = datetime.now().strftime("%I:%M:%S %p")

    message = f"""
🟢 GREEN FLASH ALERT

Stock: {trigger_stock}
Price: ₹{trigger_price:.2f}
P2L: {trigger_p2l:.2f}%

Time: {current_time}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })


# ---------------------------------------------------
# HTML TABLE (UNCHANGED)

def generate_html_table(dataframe):

    html = """
    <table style="width:100%; border-collapse: collapse;">
    <tr style="background-color:#111;">
    """

    for col in dataframe.columns:
        html += f"<th style='padding:8px; border:1px solid #444;'>{col}</th>"

    html += "</tr>"

    for _, row in dataframe.iterrows():

        html += "<tr>"

        for col in dataframe.columns:

            value = row[col]
            style = "padding:6px; border:1px solid #444; text-align:center;"

            if col == "Stock":

                if row["Stock"] in stockstar_list and row["P2L %"] < -5:
                    style += "color:green; font-weight:bold; animation: flash 1s infinite;"

                elif row["Stock"] in stockstar_list and row["P2L %"] < -3:
                    style += "color:orange; font-weight:bold;"

                elif row["P2L %"] < -2:
                    style += "color:hotpink; font-weight:bold;"

            if col in ["P2L %", "% Chg"]:

                if value > 0:
                    style += "color:green; font-weight:bold;"

                elif value < 0:
                    style += "color:red; font-weight:bold;"

            if isinstance(value, float):
                value = f"{value:.2f}"

            html += f"<td style='{style}'>{value}</td>"

        html += "</tr>"

    html += "</table>"

    return html


st.markdown(generate_html_table(df), unsafe_allow_html=True)


# ---------------------------------------------------
# SOUND ALERT

if sound_alert and green_trigger and not st.session_state.alert_played:

    st.session_state.alert_played = True

    if uploaded_sound is not None:

        audio_bytes = uploaded_sound.read()
        b64 = base64.b64encode(audio_bytes).decode()
        file_type = uploaded_sound.type

        st.markdown(f"""
        <audio autoplay>
            <source src="data:{file_type};base64,{b64}">
        </audio>
        """, unsafe_allow_html=True)

    else:

        st.markdown(f"""
        <audio autoplay>
            <source src="{DEFAULT_SOUND_URL}">
        </audio>
        """, unsafe_allow_html=True)


# ---------------------------------------------------
# AVERAGE

average_p2l = df["P2L %"].mean()

st.markdown(
    f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**"
)
