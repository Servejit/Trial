# ============================================================
# INSTALL
# pip install streamlit yfinance pandas requests bcrypt
# ============================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import bcrypt
from datetime import datetime

# ============================================================
# PAGE CONFIG

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")


# ============================================================
# TELEGRAM SETTINGS

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"


# ============================================================
# MASTER PASSWORD

MASTER_PASSWORD = "9999"


# ============================================================
# USER DATABASE (Encrypted passwords)

users = {

    "admin": bcrypt.hashpw("1234".encode(), bcrypt.gensalt()),

}


# ============================================================
# SESSION STATE

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "alert_played" not in st.session_state:
    st.session_state.alert_played = False


# ============================================================
# LOGIN SYSTEM

def login():

    st.title("🔐 Secure Login")

    user = st.text_input("User ID")

    pwd = st.text_input("Password", type="password")


    col1, col2 = st.columns(2)


    with col1:

        if st.button("Login"):

            if pwd == MASTER_PASSWORD:

                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()


            elif user in users and bcrypt.checkpw(
                pwd.encode(), users[user]
            ):

                st.session_state.logged_in = True
                st.session_state.username = user
                st.rerun()

            else:

                st.error("Invalid Login")


    with col2:

        if st.button("Forgot Password"):

            time = datetime.now().strftime("%I:%M:%S %p")

            msg = f"""

PASSWORD RESET REQUEST

User: {user}

Time: {time}

"""

            requests.post(

                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

                data={
                    "chat_id": CHAT_ID,
                    "text": msg
                }
            )

            st.warning("Reset request sent")



# ============================================================
# LOGOUT

def logout():

    if st.button("🚪 Logout"):

        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()



# ============================================================
# CHANGE PASSWORD

def change_password():

    st.subheader("🔑 Change Password")

    current = st.text_input("Current Password", type="password")

    new = st.text_input("New Password", type="password")

    confirm = st.text_input("Confirm Password", type="password")


    if st.button("Update Password"):

        user = st.session_state.username

        if not bcrypt.checkpw(current.encode(), users[user]):

            st.error("Wrong current password")

        elif new != confirm:

            st.error("Password mismatch")

        else:

            users[user] = bcrypt.hashpw(
                new.encode(),
                bcrypt.gensalt()
            )

            st.success("Password changed")



# ============================================================
# ADMIN PANEL

def admin_panel():

    if st.session_state.username != "admin":
        return

    st.subheader("👨‍💼 Admin Panel")

    tab1, tab2 = st.tabs(["Add User", "Delete User"])


    with tab1:

        new_user = st.text_input("New User")

        new_pass = st.text_input(
            "New Password",
            type="password"
        )

        if st.button("Create User"):

            if new_user in users:

                st.error("User exists")

            else:

                users[new_user] = bcrypt.hashpw(
                    new_pass.encode(),
                    bcrypt.gensalt()
                )

                st.success("User created")


    with tab2:

        delete_user = st.selectbox(
            "Select User",
            list(users.keys())
        )

        if st.button("Delete User"):

            if delete_user == "admin":

                st.error("Cannot delete admin")

            else:

                del users[delete_user]

                st.success("User deleted")



# ============================================================
# LOGIN CHECK

if not st.session_state.logged_in:

    login()

    st.stop()



# ============================================================
# AFTER LOGIN

st.title(f"📊 Welcome {st.session_state.username}")


logout()

change_password()

admin_panel()



# ============================================================
# STOCK SETTINGS

stockstar_input = st.text_input(

    "⭐ StockStar",

    "DLF.NS, CANBK.NS"

).upper()


stockstar_list = [

    s.strip().replace(".NS", "")

    for s in stockstar_input.split(",")

]



sound_alert = st.toggle(

    "🔊 Sound Alert",

    False

)


telegram_alert = st.toggle(

    "📲 Telegram Alert",

    False

)



uploaded_sound = st.file_uploader(

    "Upload Sound",

    type=["mp3", "wav"]

)



DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"



# ============================================================
# STOCK LIST

stocks = {

    "CANBK.NS":142.93,

    "DLF.NS":646.85,

    "INFY.NS":1377.05,

}



# ============================================================
# FETCH DATA

@st.cache_data(ttl=60)

def fetch():

    data = yf.download(

        list(stocks.keys()),

        period="2d",

        interval="1d",

        progress=False

    )

    rows=[]


    for sym in stocks:

        price=data[sym]["Close"].iloc[-1]

        p2l=((price-stocks[sym])/stocks[sym])*100


        rows.append({

            "Stock":sym.replace(".NS",""),

            "Price":price,

            "P2L %":p2l

        })


    return pd.DataFrame(rows)



df=fetch()



# ============================================================
# TRIGGER CHECK

green=False

trigger_stock=""

trigger_price=0

trigger_p2l=0


for _,row in df.iterrows():

    if row["Stock"] in stockstar_list and row["P2L %"]<-5:

        green=True

        trigger_stock=row["Stock"]

        trigger_price=row["Price"]

        trigger_p2l=row["P2L %"]

        break



# ============================================================
# TELEGRAM ALERT

if telegram_alert and green and not st.session_state.alert_played:


    time=datetime.now().strftime("%I:%M:%S %p")


    msg=f"""

🟢 GREEN FLASH ALERT

Stock: {trigger_stock}

Price: ₹{trigger_price:.2f}

P2L: {trigger_p2l:.2f}%

Time: {time}

"""


    requests.post(

        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

        data={

            "chat_id":CHAT_ID,

            "text":msg

        }

    )



# ============================================================
# SOUND ALERT

if sound_alert and green and not st.session_state.alert_played:


    st.session_state.alert_played=True


    if uploaded_sound:


        b64=base64.b64encode(

            uploaded_sound.read()

        ).decode()


        st.markdown(

        f"""

        <audio autoplay>

        <source src="data:audio/mp3;base64,{b64}">

        </audio>

        """,

        unsafe_allow_html=True

        )


    else:


        st.markdown(

        f"""

        <audio autoplay>

        <source src="{DEFAULT_SOUND_URL}">

        </audio>

        """,

        unsafe_allow_html=True

        )



# ============================================================
# SHOW DATA

st.dataframe(df)



# ============================================================
# AVERAGE

st.write(

"Average P2L:",

round(df["P2L %"].mean(),2),

"%"

)
