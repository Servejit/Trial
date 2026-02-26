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

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

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
# ⭐ STOCKSTAR INPUT

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
# TELEGRAM ALERT

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
"RELIANCE.NS":1402.25,
"HDFCBANK.NS":896.50,
"INFY.NS":1260.94,
"TCS.NS":2578.54,
"ITC.NS":316.51,
}

# ---------------------------------------------------
# ✅ NEW ADDITION
# FETCH VWAP FROM NSE

@st.cache_data(ttl=60)
def fetch_vwap():

    url="https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"

    headers={
    "User-Agent":"Mozilla/5.0",
    "Accept":"application/json"
    }

    session=requests.Session()

    session.get("https://www.nseindia.com",headers=headers)

    data=session.get(url,headers=headers).json()

    vwap_dict={}

    for item in data["data"]:

        symbol=item["symbol"]

        if "vwap" in item:

            vwap_dict[symbol]=item["vwap"]

    return vwap_dict


# ---------------------------------------------------
# FETCH DATA

@st.cache_data(ttl=60)

def fetch_data():

    vwap_data=fetch_vwap()

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

            symbol_clean=sym.replace(".NS","")

            vwap=vwap_data.get(symbol_clean,"")

            rows.append({

            "Stock":symbol_clean,

            "P2L %":p2l,

            "Price":price,

            "VWAP":vwap,   # ✅ ADDED

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
# BUTTONS

col1,col2=st.columns(2)

with col1:

    if st.button("🔄 Refresh"):

        st.cache_data.clear()

        st.rerun()

with col2:

    sort_clicked=st.button("📈 Sort by P2L")

# ---------------------------------------------------

df=fetch_data()

# ---------------------------------------------------

if sort_clicked:

    df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# TABLE

def generate_html_table(dataframe):

    html="<table style='width:100%;border-collapse:collapse;'>"

    html+="<tr style='background-color:#111;'>"

    for col in dataframe.columns:

        html+=f"<th style='padding:8px;border:1px solid #444'>{col}</th>"

    html+="</tr>"

    for _,row in dataframe.iterrows():

        html+="<tr>"

        for col in dataframe.columns:

            value=row[col]

            style="padding:6px;border:1px solid #444;text-align:center;"

            # ✅ VWAP COLOR ADDITION ONLY

            if col=="VWAP":

                style+="color:lightgrey;"

            if isinstance(value,float):

                value=f"{value:.2f}"

            html+=f"<td style='{style}'>{value}</td>"

        html+="</tr>"

    html+="</table>"

    return html

st.markdown(generate_html_table(df),unsafe_allow_html=True)

# ---------------------------------------------------

avg=df["P2L %"].mean()

st.markdown(f"### 📊 Average P2L of All Stocks is **{avg:.2f}%**")
