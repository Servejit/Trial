# ---------------------------------------------------
# INSTALL (Run once in terminal)
# pip install streamlit yfinance pandas
# ---------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import base64

st.set_page_config(page_title="📊 Live Stock P2L", layout="wide")
st.title("📊 Live Prices with P2L")

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
# CHECK -5% TRIGGER

green_trigger = False

for _, row in df.iterrows():
    if row["Stock"] in stockstar_list and row["P2L %"] < -5:
        green_trigger = True
        break

# ---------------------------------------------------
# GENERATE HTML TABLE

def generate_html_table(dataframe):
    html = """
    <table style="width:100%; border-collapse: collapse;">
    <tr style="background-color:#111;">
    """

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
# SOUND ALERT (-5% RULE)

if sound_alert and green_trigger:

    if uploaded_sound is not None:
        audio_bytes = uploaded_sound.read()
        b64 = base64.b64encode(audio_bytes).decode()
        file_type = uploaded_sound.type

        st.markdown(f"""
        <audio autoplay loop>
            <source src="data:{file_type};base64,{b64}" type="{file_type}">
        </audio>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <audio autoplay loop>
            <source src="{DEFAULT_SOUND_URL}" type="audio/mpeg">
        </audio>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# AVERAGE P2L

average_p2l = df["P2L %"].mean()

st.markdown(
    f"### 📊 Average P2L of All Stocks is **{average_p2l:.2f}%**"
)
