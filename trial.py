# ---------------------------------------------------
# INSTALL (Run once in terminal)
# pip install streamlit yfinance pandas
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

# ---------------------------------------------------
# STOCKSTAR INPUT BOX (Supports Multiple Symbols)

stockstar_input = st.text_input(
    "⭐ StockStar (Comma Separated)",
    "DLF.NS, CANBK.NS"
).upper()

# Convert input into clean list like ["DLF", "CANBK"]
stockstar_list = [
    s.strip().replace(".NS", "")
    for s in stockstar_input.split(",")
    if s.strip() != ""
]

# ---------------------------------------------------
# STOCK LIST (Stock : Reference Low Price)

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
# COLOR STYLING

def highlight_p2l(val):
    if pd.isna(val):
        return ""
    elif val > 0:
        return "color: green; font-weight: bold"
    elif val < 0:
        return "color: red; font-weight: bold"
    else:
        return ""

styled_df = df.style.format("{:.2f}", subset=numeric_cols)

# Green/Red styling
styled_df = styled_df.applymap(highlight_p2l, subset=["P2L %", "% Chg"])

# Stock Name Styling (Priority Logic)

def stock_color(row):
    styles = []
    for col in df.columns:
        if col == "Stock":

            # 🟠 Highest Priority: In StockStar list AND P2L < -2%
            if row["Stock"] in stockstar_list and row["P2L %"] < -2:
                styles.append("color: orange; font-weight: bold")

            # 💗 Pink rule
            elif row["P2L %"] < -1.5:
                styles.append("color: hotpink; font-weight: bold")

            else:
                styles.append("")
        else:
            styles.append("")
    return styles

styled_df = styled_df.apply(stock_color, axis=1)

# ---------------------------------------------------
# DISPLAY TABLE

st.dataframe(styled_df, use_container_width=True)

# ---------------------------------------------------
# AVERAGE P2L LINE

average_p2l = df["P2L %"].mean()

st.markdown(
    f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**"
)
