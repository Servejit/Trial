# ---------------------------------------------------
# INSTALL (Run once)
# pip install streamlit yfinance pandas requests openpyxl numpy
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
from datetime import datetime
import os
import numpy as np

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "YOUR BOT TOKEN"
CHAT_ID = "YOUR CHAT ID"

# ---------------------------------------------------
# FLASH CSS

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
# EXCEL UPLOAD

st.markdown("### 📂 Upload Excel for Score Analysis")

excel_file = st.file_uploader("Upload Excel File", type=["xlsx"])

EXCEL_PATH="stock_scores.xlsx"

excel_df=None

if excel_file is not None:

    if os.path.exists(EXCEL_PATH):
        os.remove(EXCEL_PATH)

    with open(EXCEL_PATH,"wb") as f:
        f.write(excel_file.read())

    excel_df=pd.read_excel(EXCEL_PATH)

    excel_df["Stock"]=(
    excel_df["Stock"]
    .astype(str)
    .str.replace(".NS","")
    .str.upper()
    )

# ---------------------------------------------------
# STOCKSTAR INPUT

stockstar_input = st.text_input(
"⭐ StockStar (Comma Separated)",
"BOSCHLTD.NS, BSE.NS, HEROMOTOCO.NS"
).upper()

stockstar_list=[
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
if s.strip()!=""
]

# ---------------------------------------------------
# SOUND ALERT

sound_alert = st.toggle("🔊 Enable Alert Sound", value=False)

telegram_alert = st.toggle("📲 Enable Telegram Alert", value=False)

uploaded_sound = st.file_uploader(
"Upload Sound",
type=["mp3","wav"]
)

DEFAULT_SOUND_URL="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST

stocks={

"RELIANCE.NS":1402.25,
"HDFCBANK.NS":896.50,
"INFY.NS":1260.94,
"TCS.NS":2578.54,
"ITC.NS":316.51,
"SBIN.NS":650.00,
"BHARTIARTL.NS":1961.15,
"LT.NS":3500.00,
"AXISBANK.NS":1309.52,
"KOTAKBANK.NS":416.16,

}

# ---------------------------------------------------
# FETCH DATA

@st.cache_data(ttl=60)

def fetch_data():

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

            price=float(data[sym]["Close"].iloc[-1])

            prev=float(data[sym]["Close"].iloc[-2])

            openp=float(data[sym]["Open"].iloc[-1])

            high=float(data[sym]["High"].iloc[-1])

            low=float(data[sym]["Low"].iloc[-1])

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

        except:

            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# SUPER BUY FUNCTION

def super_buy_signal(symbol):

    data=yf.download(
    symbol+".NS",
    period="3mo",
    interval="1d",
    progress=False
    )

    if data.empty or len(data)<50:

        return False,"",""

    close=data["Close"].astype(float)

    ema20=close.ewm(span=20).mean()

    ema50=close.ewm(span=50).mean()

    delta=close.diff()

    gain=delta.clip(lower=0)

    loss=-delta.clip(upper=0)

    avg_gain=gain.rolling(14).mean()

    avg_loss=loss.rolling(14).mean()

    rs=avg_gain/avg_loss

    rsi=100-(100/(1+rs))

    high=data["High"].astype(float)

    low=data["Low"].astype(float)

    tr=pd.concat([
    high-low,
    abs(high-close.shift()),
    abs(low-close.shift())
    ],axis=1).max(axis=1)

    atr=tr.rolling(14).mean()

    price=float(close.iloc[-1])
    ema20_last=float(ema20.iloc[-1])
    ema50_last=float(ema50.iloc[-1])
    rsi_last=float(rsi.iloc[-1])
    atr_last=float(atr.iloc[-1])

    condition=(

    price>ema20_last
    and ema20_last>ema50_last
    and 50<rsi_last<65
    and price<=ema20_last*1.02

    )

    if condition:

        target=price+(2*atr_last)

        stop=ema50_last

        return True,round(target,2),round(stop,2)

    return False,"",""

# ---------------------------------------------------
# BUTTONS

col1,col2=st.columns(2)

with col1:

    if st.button("Refresh"):

        st.cache_data.clear()

        st.rerun()

with col2:

    sort_clicked=st.button("Sort by P2L")

# ---------------------------------------------------
# LOAD DATA

df=fetch_data()

# ---------------------------------------------------
# ADD SIGNAL COLUMN

signals=[]
targets=[]
stops=[]

for stock in df["Stock"]:

    signal,target,stop=super_buy_signal(stock)

    if signal:

        signals.append("🔥 SUPER BUY")

        targets.append(target)

        stops.append(stop)

    else:

        signals.append("")
        targets.append("")
        stops.append("")

df["Signal"]=signals
df["Target"]=targets
df["StopLoss"]=stops

# ---------------------------------------------------
# SORT

if sort_clicked:

    df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# DISPLAY

st.dataframe(df,use_container_width=True)

# ---------------------------------------------------
# AVERAGE

avg=df["P2L %"].mean()

st.markdown(f"### Average P2L: {avg:.2f}%")

# ---------------------------------------------------
# SOUND ALERT

if sound_alert and "🔥 SUPER BUY" in df["Signal"].values:

    if uploaded_sound:

        audio_bytes=uploaded_sound.read()

        b64=base64.b64encode(audio_bytes).decode()

        st.markdown(f"""
        <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}">
        </audio>
        """, unsafe_allow_html=True)

    else:

        st.markdown(f"""
        <audio autoplay>
        <source src="{DEFAULT_SOUND_URL}">
        </audio>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# TELEGRAM ALERT

if telegram_alert:

    buy=df[df["Signal"]=="🔥 SUPER BUY"]

    if not buy.empty:

        row=buy.iloc[0]

        msg=f"""

SUPER BUY SIGNAL

Stock: {row['Stock']}

Price: {row['Price']}

Target: {row['Target']}

StopLoss: {row['StopLoss']}

"""

        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        requests.post(url,data={

        "chat_id":CHAT_ID,
        "text":msg

        })
