# ---------------------------------------------------
# INSTALL
# pip install streamlit yfinance pandas requests
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
from datetime import datetime

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# ---------------------------------------------------
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
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
stockstar_input = st.text_input(
"⭐ StockStar",
"BOSCHLTD.NS, BSE.NS"
).upper()

stockstar_list = [
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
if s.strip()
]

sound_alert = st.toggle("🔊 Sound", False)
telegram_alert = st.toggle("📲 Telegram", False)

uploaded_sound = st.file_uploader("Upload Sound", type=["mp3","wav"])

DEFAULT_SOUND_URL="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
stocks = {

"BSE.NS":2718.29,
"BOSCHLTD.NS":35043.90,
"HEROMOTOCO.NS":5419.27,
"HINDALCO.NS":878.80

}

# ---------------------------------------------------
# SESSION STATE

if "rundown_start" not in st.session_state:

    st.session_state.rundown_start={}

# ---------------------------------------------------
# FETCH (NO CACHE)

def fetch():

    data=yf.download(

    tickers=list(stocks.keys()),

    period="2d",

    interval="1d",

    group_by="ticker",

    progress=False

    )

    rows=[]

    now=datetime.now()

    for symbol in stocks:

        try:

            ref=stocks[symbol]

            price=data[symbol]["Close"].iloc[-1]

            prev=data[symbol]["Close"].iloc[-2]

            key=symbol.replace(".NS","")

            p2l=((price-ref)/ref)*100

            chg=((price-prev)/prev)*100

            # RUN DOWN REAL

            if price < ref:

                if key not in st.session_state.rundown_start:

                    st.session_state.rundown_start[key]=now

                start=st.session_state.rundown_start[key]

                minutes=int((now-start).total_seconds()/60)

                rundown=f"🟠{minutes}"

            else:

                st.session_state.rundown_start.pop(key,None)

                rundown="0"

            rows.append({

            "Stock":key,

            "P2L %":p2l,

            "Price":price,

            "% Chg":chg,

            "Low Price":ref,

            "Run Down":rundown

            })

        except:

            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# BUTTONS

col1,col2=st.columns(2)

with col1:

    if st.button("🔄 Refresh"):

        st.rerun()

with col2:

    sort=st.button("📈 Sort")

# ---------------------------------------------------

df=fetch()

if sort:

    df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# TABLE

st.dataframe(df,use_container_width=True)

# ---------------------------------------------------
# AVERAGE

st.write("Average:",round(df["P2L %"].mean(),2))
