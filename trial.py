# ---------------------------------------------------
# INSTALL
# pip install streamlit yfinance pandas
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="📊 Live Prices with P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
# REFRESH BUTTON
# ---------------------------------------------------

col1, col2 = st.columns([1,1])

with col1:
    if st.button("🔄 Refresh"):
        st.rerun()

# ---------------------------------------------------
# SORT
# ---------------------------------------------------

sort_option = col2.selectbox(
    "Sort By",
    ["Default", "Run Down 🔽", "Change % 🔽"]
)

# ---------------------------------------------------
# STOCK LIST
# ---------------------------------------------------

stocks = {
    "RELIANCE.NS": 2950,
    "HDFCBANK.NS": 1600,
    "INFY.NS": 1400,
    "ICICIBANK.NS": 950,
    "TCS.NS": 3500
}

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------

if "rundown_start" not in st.session_state:
    st.session_state.rundown_start = {}

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

data = []
now = datetime.now()

for symbol, ref_price in stocks.items():

    ticker = yf.Ticker(symbol)
    live_price = ticker.history(period="1d", interval="1m")["Close"].iloc[-1]

    change = live_price - ref_price
    change_percent = (change / ref_price) * 100

    # -----------------------------
    # RUN DOWN CALCULATION
    # -----------------------------

    if live_price < ref_price:

        if symbol not in st.session_state.rundown_start:

            st.session_state.rundown_start[symbol] = now

        start_time = st.session_state.rundown_start[symbol]

        minutes = int((now - start_time).total_seconds() / 60)

    else:

        st.session_state.rundown_start[symbol] = now
        minutes = 0

    # -----------------------------
    # DISPLAY LOGIC (YOUR EXACT RULE)
    # -----------------------------

    if live_price < ref_price:

        if minutes < 15:

            rundown_display = "12"

        else:

            rundown_display = f"🟠{minutes}"

    else:

        rundown_display = "0"

    # -----------------------------
    # COLOR
    # -----------------------------

    if change > 0:
        color = "🟢"
    elif change < 0:
        color = "🔴"
    else:
        color = "⚪"

    # -----------------------------
    # STORE
    # -----------------------------

    data.append({
        "Stock": symbol,
        "Live": round(live_price,2),
        "Reference": ref_price,
        "Change": f"{color} {round(change,2)}",
        "Change %": round(change_percent,2),
        "Run Down": minutes,
        "Run Down Display": rundown_display
    })

# ---------------------------------------------------
# DATAFRAME
# ---------------------------------------------------

df = pd.DataFrame(data)

# ---------------------------------------------------
# SORT
# ---------------------------------------------------

if sort_option == "Run Down 🔽":

    df = df.sort_values("Run Down", ascending=False)

elif sort_option == "Change % 🔽":

    df = df.sort_values("Change %", ascending=False)

# ---------------------------------------------------
# DISPLAY
# ---------------------------------------------------

df_display = df[
    ["Stock","Live","Reference","Change","Change %","Run Down Display"]
]

df_display.columns = [
    "Stock",
    "Live",
    "Reference",
    "Change",
    "Change %",
    "Run Down"
]

st.dataframe(df_display, use_container_width=True, hide_index=True)
