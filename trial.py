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
    "DLF.NS": 620.45,
    "DMART.NS": 3823.09,
    "GMRAIRPORT.NS": 93.06,
    "GODREJCP.NS": 1165.94,
    "HCLTECH.NS": 1392.51,
    "HDFCBANK.NS": 896.50,
    "HEROMOTOCO.NS": 5419.27,
    "HINDALCO.NS": 878.80,
    "HINDUNILVR.NS": 2282.38,
    "HINDZINC.NS": 573.56,
    "IDFCFIRSTB.NS": 79.61,
    "INFY.NS": 1278.30,
    "IRCTC.NS": 603.12,
    "IRFC.NS": 110.02,
    "JIOFIN.NS": 258.25,
    "JSWENERGY.NS": 466.51,
    "JUBLFOOD.NS": 522.62,
    "KOTAKBANK.NS": 416.16,
    "LTIM.NS": 4975.53,
    "M&M.NS": 3444.69,
    "MPHASIS.NS": 2349.31,
    "MUTHOOTFIN.NS": 3431.50,
    "NAUKRI.NS": 1098.68,
    "NHPC.NS": 74.28,
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
    "SRF.NS": 2682.32,
    "SUZLON.NS": 45.11,
    "TATACONSUM.NS": 1111.51,
    "TATASTEEL.NS": 199.55,
    "TCS.NS": 2578.54,
    "UPL.NS": 712.82,
    "VBL.NS": 443.37,
    "YESBANK.NS": 20.60,
}

# ---------------------------------------------------
# ALERT MEMORY FOR RUN DOWN
if "rundown_times" not in st.session_state:
    st.session_state.rundown_times = {s.replace(".NS",""): None for s in stocks.keys()}

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
    current_time = datetime.now()

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

            # -------------------------
            # RUN DOWN LOGIC
            stock_key = sym.replace(".NS","")
            if price < ref_low:
                if st.session_state.rundown_times[stock_key] is None:
                    st.session_state.rundown_times[stock_key] = current_time
                down_time = (current_time - st.session_state.rundown_times[stock_key]).seconds // 60
            else:
                st.session_state.rundown_times[stock_key] = None
                down_time = 0

            # Format Run Down column
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
# TELEGRAM ALERT
if telegram_alert and green_trigger and not st.session_state.alert_played:
    current_time = datetime.now().strftime("%I:%M:%S %p")
    message = f"""
🟢 GREEN FLASH ALERT

Stock: {trigger_stock}
Price: ₹{trigger_price:.2f}
P2L: {trigger_p2l:.2f}%

Time: {current_time}
"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})

# ---------------------------------------------------
# HTML TABLE
def generate_html_table(dataframe):
    html = "<table style='width:100%; border-collapse: collapse;'><tr style='background-color:#111;'>"
    for col in dataframe.columns:
        html += f"<th style='padding:8px; border:1px solid #444;'>{col}</th>"
    html += "</tr>"

    for _, row in dataframe.iterrows():
        html += "<tr>"
        for col in dataframe.columns:
            value = row[col]
            style = "padding:6px; border:1px solid #444; text-align:center;"

            if col == "Stock":
                if row["Stock"] in stockstar_list and row["P2L %"] < -5:
                    style += "color:green; font-weight:bold; animation: flash 1s infinite;"
                elif row["Stock"] in stockstar_list and row["P2L %"] < -3:
                    style += "color:orange; font-weight:bold;"
                elif row["P2L %"] < -2:
                    style += "color:hotpink; font-weight:bold;"

            if col in ["P2L %", "% Chg"]:
                if value > 0:
                    style += "color:green; font-weight:bold;"
                elif value < 0:
                    style += "color:red; font-weight:bold;"

            if isinstance(value, float):
                value = f"{value:.2f}"

            html += f"<td style='{style}'>{value}</td>"

        html += "</tr>"
    html += "</table>"
    return html

st.markdown(generate_html_table(df), unsafe_allow_html=True)

# ---------------------------------------------------
# SOUND ALERT
if sound_alert and green_trigger and not st.session_state.alert_played:
    st.session_state.alert_played = True
    if uploaded_sound is not None:
        audio_bytes = uploaded_sound.read()
        b64 = base64.b64encode(audio_bytes).decode()
        file_type = uploaded_sound.type
        st.markdown(f"<audio autoplay><source src='data:{file_type};base64,{b64}'></audio>", unsafe_allow_html=True)
    else:
        st.markdown(f"<audio autoplay><source src='{DEFAULT_SOUND_URL}'></audio>", unsafe_allow_html=True)

# ---------------------------------------------------
# AVERAGE
average_p2l = df["P2L %"].mean()
st.markdown(f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**")
