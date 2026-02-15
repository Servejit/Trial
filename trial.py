# ---------------------------------------------------
# INSTALL (Run once in terminal)
# pip install streamlit yfinance pandas requests pytz
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"
CHAT_ID = "PASTE_YOUR_CHAT_ID"

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
    "DLF.NS, CANBK.NS"
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
    "CANBK.NS": 142.93,
    "CHOLAFIN.NS": 1690.51,
    "COALINDIA.NS": 414.07,
    "DLF.NS": 646.85,
    "HCLTECH.NS": 1465.83,
    "IDFCFIRSTB.NS": 80.84,
    "INFY.NS": 1377.05,
    "MPHASIS.NS": 2445.51,
    "NHPC.NS": 75.78,
    "OIL.NS": 468.65,
    "PAGEIND.NS": 33501.65,
    "PERSISTENT.NS": 5417.42,
    "PNB.NS": 119.90,
}

# ---------------------------------------------------
# FETCH DATA

@st.cache_data(ttl=60)
def fetch_data():

    symbols = list(stocks.keys())

    data = yf.download(
        tickers=symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True
    )

    rows = []

    for sym in symbols:

        try:

            ref_low = stocks[sym]

            price = data[sym]["Close"].iloc[-1]
            prev_close = data[sym]["Close"].iloc[-2]
            open_p = data[sym]["Open"].iloc[-1]
            high = data[sym]["High"].iloc[-1]
            low = data[sym]["Low"].iloc[-1]

            p2l = ((price - ref_low) / ref_low) * 100
            pct_chg = ((price - prev_close) / prev_close) * 100

            rows.append({
                "Stock": sym.replace(".NS", ""),
                "P2L %": p2l,
                "Price": price,
                "% Chg": pct_chg,
                "Low Price": ref_low,
                "Open": open_p,
                "High": high,
                "Low": low
            })

        except:
            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# BUTTONS

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

with col2:
    sort_clicked = st.button("📈 Sort by P2L")

# ---------------------------------------------------
# LOAD DATA

df = fetch_data()

if df.empty:
    st.error("⚠️ No data received from Yahoo Finance.")
    st.stop()

numeric_cols = ["P2L %", "Price", "% Chg", "Low Price", "Open", "High", "Low"]

for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

if sort_clicked:
    df = df.sort_values("P2L %", ascending=False)

# ---------------------------------------------------
# GREEN TRIGGER CHECK

green_trigger = False
trigger_stock = ""
trigger_price = 0
trigger_p2l = 0

for _, row in df.iterrows():

    if row["Stock"] in stockstar_list and row["P2L %"] < -5:

        green_trigger = True
        trigger_stock = row["Stock"]
        trigger_price = row["Price"]
        trigger_p2l = row["P2L %"]

        break

# ---------------------------------------------------
# ALERT MEMORY STATE

if "alert_played" not in st.session_state:
    st.session_state.alert_played = False

if not green_trigger:
    st.session_state.alert_played = False

# ---------------------------------------------------
# TELEGRAM ALERT (UPGRADED)

if telegram_alert and green_trigger and not st.session_state.alert_played:

    ist = pytz.timezone('Asia/Kolkata')
    time_now = datetime.now(ist).strftime("%I:%M:%S %p")

    message = f"""
🟢 GREEN FLASH ALERT

Stock: {trigger_stock}
Price: ₹{trigger_price:.2f}
P2L: {trigger_p2l:.2f}%

Time: {time_now}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={

        "chat_id": CHAT_ID,
        "text": message

    })

# ---------------------------------------------------
# SOUND ALERT (UNCHANGED)

if sound_alert and green_trigger and not st.session_state.alert_played:

    st.session_state.alert_played = True

    if uploaded_sound is not None:

        audio_bytes = uploaded_sound.read()
        b64 = base64.b64encode(audio_bytes).decode()

        st.markdown(f"""
        <audio autoplay>
            <source src="data:{uploaded_sound.type};base64,{b64}">
        </audio>
        """, unsafe_allow_html=True)

    else:

        st.markdown(f"""
        <audio autoplay>
            <source src="{DEFAULT_SOUND_URL}">
        </audio>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# TABLE

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# AVERAGE

average_p2l = df["P2L %"].mean()

st.markdown(
    f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**"
)
