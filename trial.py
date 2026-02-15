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

# =========================================================
# CONFIG FILES
# =========================================================

USER_FILE = "users.json"
SESSION_FILE = "session.json"

# =========================================================
# PASSWORD FUNCTIONS
# =========================================================

def hash_password(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def check_password(password, hashed):

    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )

# =========================================================
# USER DATABASE
# =========================================================

def load_users():

    if not os.path.exists(USER_FILE):

        users = {
            "admin": {
                "password": hash_password("admin123"),
                "role": "admin"
            }
        }

        save_users(users)

    with open(USER_FILE,"r") as f:

        return json.load(f)


def save_users(users):

    with open(USER_FILE,"w") as f:

        json.dump(users,f)

# =========================================================
# SESSION SAVE (REMEMBER LOGIN)
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
# LOGIN SYSTEM
# =========================================================

def login():

    st.title("🔐 Login")

    user = st.text_input("User ID")

    password = st.text_input("Password", type="password")

    remember = st.checkbox("Remember Me")

    if st.button("Login"):

        users = load_users()

        if user in users and check_password(password, users[user]["password"]):

            st.session_state.user = user
            st.session_state.role = users[user]["role"]
            st.session_state.logged = True

            if remember:
                save_session(user)

            st.rerun()

        else:

            st.error("Invalid login")

# =========================================================
# AUTO LOGIN
# =========================================================

def auto_login():

    saved = load_session()

    if saved:

        users = load_users()

        if saved in users:

            st.session_state.user = saved
            st.session_state.role = users[saved]["role"]
            st.session_state.logged = True

# =========================================================
# CHANGE PASSWORD
# =========================================================

def change_password():

    st.subheader("Change Password")

    old = st.text_input("Current", type="password")

    new = st.text_input("New", type="password")

    confirm = st.text_input("Confirm", type="password")

    if st.button("Update"):

        users = load_users()

        if not check_password(old, users[st.session_state.user]["password"]):

            st.error("Wrong password")

        elif new != confirm:

            st.error("Mismatch")

        else:

            users[st.session_state.user]["password"] = hash_password(new)

            save_users(users)

            st.success("Updated")

# =========================================================
# ADMIN PANEL
# =========================================================

def admin_panel():

    st.subheader("Admin Panel")

    new_user = st.text_input("New User")

    new_pass = st.text_input("Password", type="password")

    if st.button("Add User"):

        users = load_users()

        users[new_user] = {

            "password": hash_password(new_pass),
            "role": "user"

        }

        save_users(users)

        st.success("User added")

    st.divider()

    users = load_users()

    delete = st.selectbox("Delete User", list(users.keys()))

    if st.button("Delete"):

        if delete == "admin":

            st.error("Cannot delete admin")

        else:

            users.pop(delete)

            save_users(users)

            st.success("Deleted")

# =========================================================
# STOCK DASHBOARD (SAME UI)
# =========================================================

def dashboard():

    st.title("📊 Live Prices with P2L")

    st.write(f"Welcome **{st.session_state.user}**")

    if st.button("Logout"):

        clear_session()

        st.session_state.logged = False

        st.rerun()

    BOT_TOKEN="PASTE"
    CHAT_ID="PASTE"

    stocks = {

        "CANBK.NS":142.93,
        "DLF.NS":646.85,
        "INFY.NS":1377.05

    }

    stockstar = st.text_input("StockStar","CANBK.NS")

    sound = st.toggle("Sound Alert")

    telegram = st.toggle("Telegram Alert")

    upload = st.file_uploader("Sound")

    DEFAULT="https://assets.mixkit.co/active_storage/sfx/2869-preview.mp3"

    @st.cache_data(ttl=60)
    def fetch():

        data=yf.download(list(stocks.keys()),period="2d")

        rows=[]

        for s in stocks:

            price=data["Close"][s].iloc[-1]

            ref=stocks[s]

            p2l=((price-ref)/ref)*100

            rows.append({

                "Stock":s.replace(".NS",""),
                "Price":price,
                "P2L %":p2l

            })

        return pd.DataFrame(rows)

    df=fetch()

    st.dataframe(df,use_container_width=True)

    trigger=df[df["P2L %"]<-5]

    if not trigger.empty:

        stock=trigger.iloc[0]["Stock"]

        if telegram:

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id":CHAT_ID,"text":stock}
            )

        if sound:

            src=DEFAULT

            if upload:

                b64=base64.b64encode(upload.read()).decode()

                src=f"data:audio/mp3;base64,{b64}"

            st.markdown(f"""

            <audio autoplay>
            <source src="{src}">
            </audio>

            <script>

            let a=document.querySelector("audio");

            let c=0;

            a.onended=function(){{

            c++;

            if(c<2)a.play();

            }}

            </script>

            """,unsafe_allow_html=True)

# =========================================================
# MAIN CONTROL
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
