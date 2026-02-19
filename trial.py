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
# TELEGRAM SETTINGS

BOT_TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# ---------------------------------------------------
# STOCKSTAR INPUT

stockstar_input = st.text_input(
    "⭐ StockStar",
    "OIL.NS, BSE.NS, HEROMOTOCO.NS, HINDALCO.NS"
).upper()

stockstar_list = [
    s.strip().replace(".NS", "")
    for s in stockstar_input.split(",")
    if s.strip()
]

# ---------------------------------------------------
# SOUND SETTINGS

sound_alert = st.toggle("🔊 Sound Alert", False)
telegram_alert = st.toggle("📲 Telegram Alert", False)

uploaded_sound = st.file_uploader(
    "Upload Sound",
    type=["mp3", "wav"]
)

DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST

stocks = {

    "OIL.NS": 451.02,
    "BSE.NS": 2718.29,
    "HEROMOTOCO.NS": 5419.27,
    "HINDALCO.NS": 878.80

}

# ---------------------------------------------------
# FETCH DATA FUNCTION

@st.cache_data(ttl=60)
def fetch_data():

    symbols = list(stocks.keys())

    daily = yf.download(
        symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        progress=False,
        threads=True
    )

    minute = yf.download(
        symbols,
        period="1d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True
    )

    rows = []

    for sym in symbols:

        try:

            ref = stocks[sym]

            price = daily[sym]["Close"].iloc[-1]
            prev = daily[sym]["Close"].iloc[-2]

            openp = daily[sym]["Open"].iloc[-1]
            high = daily[sym]["High"].iloc[-1]
            low = daily[sym]["Low"].iloc[-1]

            p2l = ((price - ref) / ref) * 100
            chg = ((price - prev) / prev) * 100

            # -----------------------------------
            # RunDown calculation
            # -----------------------------------

            rundown = ""

            if sym in minute:

                cl = minute[sym]["Close"].dropna()

                if len(cl) > 5:

                    peak_time = cl.idxmax()
                    peak_price = cl.max()

                    if price < peak_price:

                        mins = int(
                            (datetime.now(peak_time.tzinfo) - peak_time
                            ).total_seconds() / 60
                        )

                        if mins > 15:

                            rundown = f"🟠{mins}"

                        else:

                            rundown = str(mins)

            rows.append({

                "Stock": sym.replace(".NS", ""),

                "P2L %": p2l,

                "Price": price,

                "RunDown": rundown,

                "% Chg": chg,

                "Low Price": ref,

                "Open": openp,

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

    sort_clicked = st.button("📈 Sort")

# ---------------------------------------------------
# LOAD DATA

df = fetch_data()

if sort_clicked:

    df = df.sort_values("P2L %", ascending=False)

# ---------------------------------------------------
# DISPLAY TABLE

st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# AVERAGE

avg = df["P2L %"].mean()

st.markdown(f"### Average P2L : {avg:.2f}%")

# ---------------------------------------------------
# ALERT CHECK

green = False

for _, r in df.iterrows():

    if r["Stock"] in stockstar_list and r["P2L %"] < -5:

        green = True

        stock = r["Stock"]
        price = r["Price"]
        p2l = r["P2L %"]

# ---------------------------------------------------
# TELEGRAM ALERT

if telegram_alert and green:

    msg = f"""

GREEN ALERT

{stock}

₹{price:.2f}

{p2l:.2f}%

"""

    requests.post(

        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

        data={"chat_id": CHAT_ID, "text": msg}

    )

# ---------------------------------------------------
# SOUND ALERT

if sound_alert and green:

    if uploaded_sound:

        audio = uploaded_sound.read()

        b64 = base64.b64encode(audio).decode()

        st.markdown(

            f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>',

            unsafe_allow_html=True

        )

    else:

        st.markdown(

            f'<audio autoplay src="{DEFAULT_SOUND_URL}"></audio>',

            unsafe_allow_html=True

        )
