# ---------------------------------------------------
# INSTALL (Run once in terminal)
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
# STOCKSTAR INPUT
stockstar_input = st.text_input(
    "⭐ StockStar (Comma Separated)",
    "BOSCHLTD.NS, BSE.NS, HEROMOTOCO.NS, HINDALCO.NS, HINDZINC.NS, M&M.NS, MUTHOOTFIN.NS, PIIND.NS"
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
    "ADANIENT.NS": 2092.68,
    "ADANIPORTS.NS": 1487.82,
    "AMBUJACEM.NS": 510.63,
    "AXISBANK.NS": 1309.52,
    "BAJAJHFL.NS": 88.23,
    "BHEL.NS": 251.74,
    "BOSCHLTD.NS": 35043.90,
    "BPCL.NS": 367.20,
    "BSE.NS": 2718.29,
    "CANBK.NS": 139.45,
    "COALINDIA.NS": 404.57,
    "COFORGE.NS": 1330.67,
    "DIXON.NS": 11070.37,
    "DLF.NS": 620.45,
    "DMART.NS": 3823.09,
    "ETERNAL.NS": 268.50,
    "GMRAIRPORT.NS": 93.06,
    "GODREJCP.NS": 1165.94,
    "HCLTECH.NS": 1392.51,
    "HDFCAMC.NS": 2711.38,
    "HDFCBANK.NS": 896.50,
    "HEROMOTOCO.NS": 5419.27,
    "HINDALCO.NS": 878.80,
    "HINDUNILVR.NS": 2282.38,
    "HINDZINC.NS": 573.56,
    "IDFCFIRSTB.NS": 79.61,
    "INDHOTEL.NS": 664.76,
    "INFY.NS": 1278.30,
    "IRCTC.NS": 603.12,
    "IRFC.NS": 110.02,
    "JIOFIN.NS": 258.25,
    "JSWENERGY.NS": 466.51,
    "JUBLFOOD.NS": 522.62,
    "KOTAKBANK.NS": 416.16,
    "LTIM.NS": 4896.40,
    "M%26M.NS": 3444.69,
    "MPHASIS.NS": 2349.31,
    "MUTHOOTFIN.NS": 3431.50,
    "NAUKRI.NS": 1084.55,
    "NHPC.NS": 74.28,
    "OBEROIRLTY.NS": 1487.03,
    "OFSS.NS": 6384.00,
    "OIL.NS": 451.02,
    "PAGEIND.NS": 33063.85,
    "PERSISTENT.NS": 5196.98,
    "PFC.NS": 395.26,
    "PIIND.NS": 2999.93,
    "PNB.NS": 116.96,
    "POLYCAB.NS": 7498.32,
    "PRESTIGE.NS": 1474.69,
    "RECLTD.NS": 338.10,
    "RELIANCE.NS": 1402.25,
    "SHREECEM.NS": 25621.25,
    "SOLARINDS.NS": 12787.74,
    "SRF.NS": 2650.58,
    "SUZLON.NS": 45.11,
    "TATACONSUM.NS": 1111.51,
    "TATASTEEL.NS": 199.55,
    "TCS.NS": 2578.54,
    "UPL.NS": 712.82,
    "VBL.NS": 443.37,
    "YESBANK.NS": 20.60,
}

# ---------------------------------------------------
# RUN DOWN MEMORY
if "rundown_times" not in st.session_state:
    st.session_state.rundown_times = {s.replace(".NS",""): None for s in stocks.keys()}

# ---------------------------------------------------
# FETCH LIVE DATA (FIXED)
def fetch_data():

    symbols = list(stocks.keys())

    data = yf.download(
        tickers=symbols,
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True
    )

    rows = []
    current_time = datetime.now()

    for sym in symbols:

        try:

            ref_low = stocks[sym]

            price = data[sym]["Close"].dropna().iloc[-1]
            prev_close = data[sym]["Close"].dropna().iloc[0]
            open_p = data[sym]["Open"].dropna().iloc[0]
            high = data[sym]["High"].max()
            low = data[sym]["Low"].min()

            p2l = ((price - ref_low) / ref_low) * 100
            pct_chg = ((price - prev_close) / prev_close) * 100

            stock_key = sym.replace(".NS","")

            if price < ref_low:

                if st.session_state.rundown_times[stock_key] is None:

                    st.session_state.rundown_times[stock_key] = current_time

                down_time = int(
                    (current_time - st.session_state.rundown_times[stock_key]).total_seconds() // 60
                )

            else:

                st.session_state.rundown_times[stock_key] = None
                down_time = 0

            if down_time > 15:
                run_down_display = f"🟠{down_time}"
            else:
                run_down_display = f"{down_time}"

            rows.append({
                "Stock": stock_key,
                "P2L %": p2l,
                "Price": price,
                "% Chg": pct_chg,
                "Low Price": ref_low,
                "Open": open_p,
                "High": high,
                "Low": low,
                "Run Down": run_down_display
            })

        except:
            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# BUTTONS
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh"):
        st.rerun()

with col2:
    sort_clicked = st.button("📈 Sort by P2L")

# ---------------------------------------------------
# LOAD DATA
df = fetch_data()

if df.empty:
    st.error("⚠️ No data received.")
    st.stop()

numeric_cols = ["P2L %", "Price", "% Chg", "Low Price", "Open", "High", "Low"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if sort_clicked:
    df = df.sort_values("P2L %", ascending=False)

# ---------------------------------------------------
# TABLE DISPLAY
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# AVERAGE
average_p2l = df["P2L %"].mean()

st.markdown(f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**")
