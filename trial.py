# ============================================================
# INSTALL REQUIREMENTS
# pip install streamlit yfinance pandas requests
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import json
import hashlib
import requests
import base64
import os

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(page_title="Stock Alert App", layout="wide")

# ============================================================
# FILE PATH
# ============================================================

USER_FILE = "users.json"

# ============================================================
# TELEGRAM SETTINGS
# ============================================================

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"

# ============================================================
# PASSWORD HASH
# ============================================================

def hash_password(password):

    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
# LOAD USERS
# ============================================================

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


# ============================================================
# SAVE USERS
# ============================================================

def save_users(users):

    with open(USER_FILE, "w") as f:

        json.dump(users, f)


# ============================================================
# LOGIN
# ============================================================

def login():

    st.title("🔐 Login")

    username = st.text_input("User ID", key="login_user")

    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login", key="login_btn"):

        users = load_users()

        if username in users and users[username]["password"] == hash_password(password):

            st.session_state.logged = True

            st.session_state.username = username

            st.session_state.role = users[username]["role"]

            st.success("Login successful")

            st.rerun()

        else:

            st.error("Invalid login")


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password():

    st.subheader("🔑 Change Password")

    current = st.text_input("Current Password", type="password", key="cp1")

    new = st.text_input("New Password", type="password", key="cp2")

    confirm = st.text_input("Confirm Password", type="password", key="cp3")

    if st.button("Change Password", key="cpbtn"):

        users = load_users()

        user = st.session_state.username

        if users[user]["password"] != hash_password(current):

            st.error("Wrong password")

            return

        if new != confirm:

            st.error("Passwords do not match")

            return

        users[user]["password"] = hash_password(new)

        save_users(users)

        st.success("Password changed")


# ============================================================
# ADMIN PANEL
# ============================================================

def admin_panel():

    st.subheader("👨‍💼 Admin Panel")

    users = load_users()

    new_user = st.text_input("New User", key="new_user")

    new_pass = st.text_input("New Password", type="password", key="new_pass")

    if st.button("Add User"):

        users[new_user] = {

            "password": hash_password(new_pass),

            "role": "user"

        }

        save_users(users)

        st.success("User added")


    delete_user = st.selectbox("Delete User", list(users.keys()))

    if st.button("Delete User"):

        if delete_user != "admin":

            del users[delete_user]

            save_users(users)

            st.success("Deleted")


# ============================================================
# STOCK DATA
# ============================================================

stocks = {

    "CANBK.NS": 142.93,
    "DLF.NS": 646.85,
    "INFY.NS": 1377.05,
    "HCLTECH.NS": 1465.83

}


@st.cache_data(ttl=60)
def fetch():

    data = yf.download(

        list(stocks.keys()),
        period="2d",
        interval="1d",
        progress=False

    )

    rows = []

    for s in stocks:

        try:

            price = data["Close"][s].iloc[-1]

            ref = stocks[s]

            p2l = ((price - ref) / ref) * 100

            rows.append({

                "Stock": s.replace(".NS", ""),
                "Price": price,
                "P2L %": p2l

            })

        except:

            pass

    return pd.DataFrame(rows)


# ============================================================
# TELEGRAM ALERT MEMORY
# ============================================================

if "alert_sent" not in st.session_state:

    st.session_state.alert_sent = False


# ============================================================
# SOUND MEMORY
# ============================================================

if "sound_played" not in st.session_state:

    st.session_state.sound_played = False


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.title(f"📊 Welcome {st.session_state.username}")

    if st.button("Logout"):

        st.session_state.logged = False

        st.rerun()


    df = fetch()

    st.dataframe(df, use_container_width=True)


    trigger = df[df["P2L %"] < -5]


    # TELEGRAM ONCE

    if not trigger.empty:

        if not st.session_state.alert_sent:

            stock = trigger.iloc[0]["Stock"]

            msg = f"GREEN FLASH ALERT\nStock: {stock}\nBelow -5%"

            requests.post(

                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

                data={

                    "chat_id": CHAT_ID,
                    "text": msg

                }

            )

            st.session_state.alert_sent = True

            st.success("Telegram Sent")

    else:

        st.session_state.alert_sent = False


    # SOUND PLAY TWICE ONLY

    if not trigger.empty:

        if not st.session_state.sound_played:

            sound_url = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

            st.markdown(f"""

            <audio id="alertaudio">

            <source src="{sound_url}" type="audio/mpeg">

            </audio>

            <script>

            var audio = document.getElementById("alertaudio");

            var count = 0;

            audio.play();

            audio.onended = function() {{

                count++;

                if(count < 2){{audio.play();}}

            }};

            </script>

            """, unsafe_allow_html=True)

            st.session_state.sound_played = True

    else:

        st.session_state.sound_played = False


    change_password()


    if st.session_state.role == "admin":

        admin_panel()


# ============================================================
# MAIN
# ============================================================

if "logged" not in st.session_state:

    st.session_state.logged = False


if st.session_state.logged:

    dashboard()

else:

    login()
