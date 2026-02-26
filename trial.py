# ---------------------------------------------------
# INSTALL (Run once)
# pip install streamlit yfinance pandas requests openpyxl
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
from datetime import datetime
import os

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "8371973661:AAFTOjh53yKmmgv3eXqD5wf8Ki6XXrZPq2c"
CHAT_ID = "5355913841"

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
# 📂 EXCEL UPLOAD

st.markdown("### 📂 Upload Excel for Score Analysis")

excel_file = st.file_uploader(
"Upload Excel File",
type=["xlsx"]
)

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
"BOSCHLTD.NS, BSE.NS, HEROMOTOCO.NS, HINDALCO.NS, HINDZINC.NS, M&M.NS, MUTHOOTFIN.NS, PIIND.NS"
).upper()

stockstar_list=[
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
if s.strip()!=""
]

# ---------------------------------------------------
# SOUND SETTINGS

sound_alert = st.toggle(
"🔊 Enable Alert Sound for -5% Green Stocks",
value=False
)

# ---------------------------------------------------
# TELEGRAM ALERT TOGGLE

telegram_alert = st.toggle(
"📲 Enable Telegram Alert for Green Flashing",
value=False
)

# ---------------------------------------------------
# SOUND UPLOAD

st.markdown("### 🎵 Alert Sound Settings")

uploaded_sound = st.file_uploader(
"Upload Your Custom Sound (.mp3 or .wav)",
type=["mp3","wav"]
)

DEFAULT_SOUND_URL="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST

stocks={
"ADANIENT.NS": 2092.68,
"ADANIGREEN.NS": 957.19,
"ADANIPORTS.NS": 1487.82,
"AMBUJACEM.NS": 506.11,
"AXISBANK.NS": 1309.52,
"BAJAJHFL.NS": 88.23,
"BHARTIARTL.NS": 1961.15,
"BHEL.NS": 249.45,
"BOSCHLTD.NS": 35043.90,
"BPCL.NS": 367.20,
"BSE.NS": 2718.29,
"CANBK.NS": 139.45,
"COALINDIA.NS": 404.57,
"COFORGE.NS": 1195.90,
"DIXON.NS": 10294.20,
"DLF.NS": 612.92,
"DMART.NS": 3823.09,
"ETERNAL.NS": 248.83,
"GMRAIRPORT.NS": 93.06,
"GODREJCP.NS": 1165.94,
"HCLTECH.NS": 1319.19,
"HDFCAMC.NS": 2687.89,
"HDFCBANK.NS": 896.50,
"HEROMOTOCO.NS": 5419.27,
"HINDALCO.NS": 878.80,
"HINDUNILVR.NS": 2282.38,
"HINDZINC.NS": 573.56,
"IDFCFIRSTB.NS": 79.61,
"INDHOTEL.NS": 661.68,
"INDUSINDBK.NS": 907.39,
"INDUSTOWER.NS": 451.98,
"INFY.NS": 1260.94,
"IRCTC.NS": 603.12,
"IRFC.NS": 110.02,
"ITC.NS": 316.51,
"JIOFIN.NS": 258.25,
"JSWENERGY.NS": 466.51,
"JUBLFOOD.NS": 507.90,
"KOTAKBANK.NS": 416.16,
"LODHA.NS": 1052.06,
"LTIM.NS": 4454.34,
"M%26M.NS": 3444.69,
"MANKIND.NS": 2004.83,
"MAZDOCK.NS": 2219.94,
"MOTHERSON.NS": 127.84,
"MPHASIS.NS": 2205.17,
"MUTHOOTFIN.NS": 3348.18,
"NAUKRI.NS": 1003.58,
"NHPC.NS": 73.34,
"OBEROIRLTY.NS": 1486.53,
"OFSS.NS": 6367.50,
"OIL.NS": 451.02,
"PAGEIND.NS": 32302.68,
"PERSISTENT.NS": 4573.54,
"PFC.NS": 395.26,
"PHOENIXLTD.NS": 1658.76,
"PIIND.NS": 2999.93,
"PNB.NS": 116.96,
"POLYCAB.NS": 7498.32,
"PRESTIGE.NS": 1464.64,
"RECLTD.NS": 338.10,
"RELIANCE.NS": 1402.25,
"SBICARD.NS": 756.25,
"SHREECEM.NS": 25621.25,
"SOLARINDS.NS": 12787.74,
"SRF.NS": 2546.62,
"SUZLON.NS": 42.49,
"TATACONSUM.NS": 1111.51,
"TATASTEEL.NS": 199.55,
"TCS.NS": 2578.54,
"TECHM.NS": 1331.96,
"TRENT.NS": 3880.50,
"ULTRACEMCO.NS": 12515.11,
"UPL.NS": 712.82,
"VBL.NS": 443.37,
"YESBANK.NS": 20.60,
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

            price=data[sym]["Close"].iloc[-1]

            prev=data[sym]["Close"].iloc[-2]

            openp=data[sym]["Open"].iloc[-1]

            high=data[sym]["High"].iloc[-1]

            low=data[sym]["Low"].iloc[-1]

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
# SUPER BUY SIGNAL FUNCTION (ADDED ONLY)

def super_buy_signal(symbol):

    data=yf.download(
    tickers=symbol+".NS",
    period="3mo",
    interval="1d",
    progress=False
    )

    if len(data)<50:

        return False,"",""

    close=data["Close"]

    ema20=close.ewm(span=20).mean()

    ema50=close.ewm(span=50).mean()

    delta=close.diff()

    gain=delta.clip(lower=0)

    loss=-delta.clip(upper=0)

    avg_gain=gain.rolling(14).mean()

    avg_loss=loss.rolling(14).mean()

    rs=avg_gain/avg_loss

    rsi=100-(100/(1+rs))

    high=data["High"]

    low=data["Low"]

    tr=pd.concat([

    high-low,

    abs(high-close.shift()),

    abs(low-close.shift())

    ],axis=1).max(axis=1)

    atr=tr.rolling(14).mean()

    price=close.iloc[-1]

    condition=(

    price>ema20.iloc[-1]

    and ema20.iloc[-1]>ema50.iloc[-1]

    and 50<rsi.iloc[-1]<65

    and price<=ema20.iloc[-1]*1.02

    )

    if condition:

        target=price+(2*atr.iloc[-1])

        stop=ema50.iloc[-1]

        return True,round(target,2),round(stop,2)

    return False,"",""

# ---------------------------------------------------
# BUTTONS

col1,col2=st.columns(2)

with col1:

    if st.button("🔄 Refresh"):

        st.cache_data.clear()

        st.rerun()

with col2:

    sort_clicked=st.button("📈 Sort by P2L")

# ---------------------------------------------------
# LOAD DATA

df=fetch_data()

# ---------------------------------------------------
# ADD SUPER BUY COLUMN (ADDED ONLY)

signals=[]

targets=[]

stops=[]

for stock in df["Stock"]:

    s,t,sl=super_buy_signal(stock)

    if s:

        signals.append("🔥 SUPER BUY")

        targets.append(t)

        stops.append(sl)

    else:

        signals.append("")

        targets.append("")

        stops.append("")

df["Signal"]=signals

df["Target"]=targets

df["StopLoss"]=stops

# ---------------------------------------------------
# REST SAME AS YOUR ORIGINAL

st.dataframe(df)

avg=df["P2L %"].mean()

st.markdown(f"### 📊 Average P2L of All Stocks is **{avg:.2f}%**")
