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
    if s.strip()
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
    "BOSCHLTD.NS": 35043.90,
    "BSE.NS": 2718.29,
    "HEROMOTOCO.NS": 5419.27,
    "HINDALCO.NS": 878.80,
    "HINDZINC.NS": 573.56,
    "M%26M.NS": 3444.69,
    "MUTHOOTFIN.NS": 3431.50,
    "PIIND.NS": 2999.93,
}

# ---------------------------------------------------
# SESSION MEMORY

if "rundown_times" not in st.session_state:

    st.session_state.rundown_times = {}

# ---------------------------------------------------
# FETCH DATA (FINAL FIXED)

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

    for sym in symbols:

        try:

            df_sym = data[sym].dropna()

            ref_low = stocks[sym]

            price = df_sym["Close"].iloc[-1]

            prev_close = df_sym["Close"].iloc[0]

            open_p = df_sym["Open"].iloc[0]

            high = df_sym["High"].max()

            low = df_sym["Low"].min()

            # ✅ USE CANDLE TIME
            candle_time = df_sym.index[-1].to_pydatetime()

            p2l = ((price - ref_low) / ref_low) * 100

            pct_chg = ((price - prev_close) / prev_close) * 100

            stock_key = sym.replace(".NS","")

            start_time = st.session_state.rundown_times.get(stock_key)

            if price < ref_low:

                if start_time is None:

                    st.session_state.rundown_times[stock_key] = candle_time

                    down_time = 0

                else:

                    down_time = int(
                        (candle_time - start_time).total_seconds() / 60
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
# REFRESH BUTTON

if st.button("🔄 Refresh"):

    st.rerun()

# ---------------------------------------------------
# LOAD DATA

df = fetch_data()

if df.empty:

    st.error("No data")

else:

    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# AVERAGE

average = df["P2L %"].mean()

st.markdown(f"### 📊 Average P2L: {average:.2f}%")
