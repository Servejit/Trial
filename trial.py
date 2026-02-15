# ---------------------------------------------------
# INSTALL REQUIREMENTS
# pip install streamlit yfinance pandas requests bcrypt
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import json
import bcrypt
import os

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")


# ===================================================
# LOGIN SYSTEM
# ===================================================

USER_FILE = "users.json"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def load_users():

    if not os.path.exists(USER_FILE):

        users = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "admin"
            }
        }

        save_users(users)

    with open(USER_FILE, "r") as f:
        return json.load(f)


def save_users(users):

    with open(USER_FILE, "w") as f:
        json.dump(users, f)


# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------

def login():

    st.title("🔐 Login")

    user = st.text_input("User ID", key="login_user")

    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):

        users = load_users()

        if user in users and check_password(password, users[user]["password"]):

            st.session_state.logged = True
            st.session_state.user = user
            st.session_state.role = users[user]["role"]

            st.rerun()

        else:

            st.error("Invalid ID or Password")


# ---------------------------------------------------
# CHANGE PASSWORD
# ---------------------------------------------------

def change_password():

    st.subheader("🔑 Change Password")

    current = st.text_input("Current Password", type="password", key="cp1")

    new = st.text_input("New Password", type="password", key="cp2")

    confirm = st.text_input("Confirm Password", type="password", key="cp3")

    if st.button("Update Password"):

        users = load_users()

        if not check_password(current, users[st.session_state.user]["password"]):

            st.error("Wrong Password")

        elif new != confirm:

            st.error("Passwords not match")

        else:

            users[st.session_state.user]["password"] = hash_password(new)

            save_users(users)

            st.success("Password Updated")


# ---------------------------------------------------
# ADMIN PANEL
# ---------------------------------------------------

def admin_panel():

    st.subheader("👨‍💼 Admin Panel")

    tab1, tab2 = st.tabs(["Add User", "Delete User"])

    with tab1:

        new_user = st.text_input("New User", key="add_user")

        new_pass = st.text_input("New Password", type="password", key="add_pass")

        if st.button("Create User"):

            users = load_users()

            if new_user in users:

                st.error("User exists")

            else:

                users[new_user] = {

                    "password": hash_password(new_pass),
                    "role": "user"
                }

                save_users(users)

                st.success("User Created")

    with tab2:

        users = load_users()

        delete_user = st.selectbox("Select User", list(users.keys()))

        if st.button("Delete User"):

            if delete_user == "admin":

                st.error("Cannot delete admin")

            else:

                users.pop(delete_user)

                save_users(users)

                st.success("Deleted")


# ===================================================
# STOCK DASHBOARD (YOUR ORIGINAL UI)
# ===================================================

def stock_dashboard():

    st.title("📊 Live Prices with P2L")

    st.write(f"Welcome **{st.session_state.user}**")

    if st.button("Logout"):

        st.session_state.logged = False
        st.rerun()

    # ---------------------------------------------------
    # TELEGRAM SETTINGS

    BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
    CHAT_ID = "PASTE_YOUR_CHAT_ID"

    # ---------------------------------------------------
    # CSS

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

    stockstar_input = st.text_input(
        "⭐ StockStar",
        "DLF.NS, CANBK.NS"
    ).upper()

    stockstar_list = [
        s.strip().replace(".NS", "")
        for s in stockstar_input.split(",")
    ]

    sound_alert = st.toggle("🔊 Sound Alert")

    telegram_alert = st.toggle("📲 Telegram Alert")

    uploaded_sound = st.file_uploader("Upload Sound")

    DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

    # ---------------------------------------------------

    stocks = {

        "CANBK.NS": 142.93,
        "DLF.NS": 646.85,
        "INFY.NS": 1377.05,
        "PNB.NS": 119.90,

    }

    # ---------------------------------------------------

    @st.cache_data(ttl=60)
    def fetch():

        data = yf.download(list(stocks.keys()), period="2d", interval="1d")

        rows = []

        for sym in stocks:

            price = data["Close"][sym].iloc[-1]

            ref = stocks[sym]

            p2l = ((price - ref) / ref) * 100

            rows.append({

                "Stock": sym.replace(".NS", ""),
                "Price": price,
                "P2L %": p2l

            })

        return pd.DataFrame(rows)

    df = fetch()

    st.dataframe(df, use_container_width=True)

    # ---------------------------------------------------
    # TRIGGER

    trigger = df[df["P2L %"] < -5]

    if not trigger.empty:

        stock = trigger.iloc[0]["Stock"]

        # TELEGRAM

        if telegram_alert:

            msg = f"GREEN FLASH ALERT\nStock: {stock}"

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

        # SOUND TWICE ONLY

        if sound_alert:

            if uploaded_sound:

                audio_bytes = uploaded_sound.read()

                b64 = base64.b64encode(audio_bytes).decode()

                src = f"data:audio/mp3;base64,{b64}"

            else:

                src = DEFAULT_SOUND_URL

            st.markdown(f"""

            <audio autoplay>
            <source src="{src}">
            </audio>

            <script>

            let audio = document.querySelector("audio");

            let count = 0;

            audio.onended = function(){{

                count++;

                if(count < 2) audio.play();

            }}

            </script>

            """, unsafe_allow_html=True)


# ===================================================
# MAIN CONTROL
# ===================================================

if "logged" not in st.session_state:

    st.session_state.logged = False


if st.session_state.logged:

    stock_dashboard()

    st.divider()

    change_password()

    if st.session_state.role == "admin":

        admin_panel()

else:

    login()
