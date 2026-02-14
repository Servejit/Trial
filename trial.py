# pip install streamlit yfinance pandas requests

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import time
import threading

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "8371973661:AAFTOjh53yKmmgv3eXqD5wf8Ki6XXrZPq2c"
CHAT_ID = "5355913841"

# ---------------------------------------------------

st.set_page_config(layout="wide")

st.markdown("## 📊 Live Price P2L")

# ---------------------------------------------------
# CSS

st.markdown("""
<style>

.block-container
{
padding-top:1rem;
}

@keyframes flash {
0% {opacity:1;}
50% {opacity:0.2;}
100% {opacity:1;}
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# INPUT

col1,col2,col3 = st.columns([4,2,2])

with col1:

    stockstar_input = st.text_input(
        "⭐ StockStar",
        "DLF.NS, CANBK.NS"
    ).upper()

with col2:

    sound_alert = st.toggle("🔊 Sound", False)

with col3:

    telegram_alert = st.toggle("📲 Telegram", False)


stockstar_list = [
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
]

# ---------------------------------------------------
# SOUND UPLOAD

uploaded_sound = st.file_uploader(
"",
type=["mp3","wav"],
label_visibility="collapsed"
)

DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST

stocks = {

"CANBK.NS":142.93,
"DLF.NS":646.85,
"INFY.NS":1377.05,
"HCLTECH.NS":1465.83,
"OIL.NS":468.65,
"PNB.NS":119.90,

}

# ---------------------------------------------------
# FETCH FUNCTION

@st.cache_data(ttl=60)

def fetch():

    symbols=list(stocks.keys())

    data=yf.download(

        tickers=symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        progress=False

    )

    rows=[]

    for sym in symbols:

        try:

            ref=stocks[sym]

            price=data[sym]["Close"].iloc[-1]
            prev=data[sym]["Close"].iloc[-2]

            p2l=((price-ref)/ref)*100
            chg=((price-prev)/prev)*100

            rows.append({

                "Stock":sym.replace(".NS",""),
                "P2L %":p2l,
                "Price":price,
                "%Chg":chg

            })

        except:

            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# TELEGRAM SEND

def send_telegram(msg):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(

        url,
        data={

            "chat_id":CHAT_ID,
            "text":msg

        }

    )

# ---------------------------------------------------
# BACKGROUND

def background():

    while True:

        df=fetch()

        for _,row in df.iterrows():

            if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                msg=f"""

ALERT

{row['Stock']}

P2L = {row['P2L %']:.2f}%
Price = {row['Price']:.2f}

"""

                send_telegram(msg)

        time.sleep(60)


# START THREAD

if telegram_alert:

    threading.Thread(

        target=background,
        daemon=True

    ).start()

# ---------------------------------------------------
# DISPLAY

df=fetch()

# ---------------------------------------------------
# TABLE

green_trigger=False

html="<table width=100% border=1>"

html+="<tr>"

for c in df.columns:

    html+=f"<th>{c}</th>"

html+="</tr>"

for _,row in df.iterrows():

    html+="<tr>"

    for c in df.columns:

        val=row[c]

        style=""

        if c=="Stock":

            if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                style="color:green;font-weight:bold;animation:flash 1s infinite;"
                green_trigger=True

        if isinstance(val,float):

            val=f"{val:.2f}"

        html+=f"<td style='{style}'>{val}</td>"

    html+="</tr>"

html+="</table>"

st.markdown(html,unsafe_allow_html=True)

# ---------------------------------------------------
# SOUND

if sound_alert and green_trigger:

    if uploaded_sound:

        audio=uploaded_sound.read()

        b64=base64.b64encode(audio).decode()

        st.markdown(f"""

<audio autoplay loop>
<source src="data:audio/mp3;base64,{b64}">
</audio>

""",unsafe_allow_html=True)

    else:

        st.markdown(f"""

<audio autoplay loop>
<source src="{DEFAULT_SOUND_URL}">
</audio>

""",unsafe_allow_html=True)

# ---------------------------------------------------
# AVERAGE

st.write(

"Average P2L:",
round(df["P2L %"].mean(),2),
"%"

)

# ---------------------------------------------------
# REFRESH

if st.button("Refresh"):

    st.cache_data.clear()
    st.rerun()
