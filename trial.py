# =====================================================
# IMPORT
# =====================================================

import streamlit as st
import pandas as pd
import yfinance as yf
import warnings
import time

warnings.filterwarnings("ignore")
pd.options.display.float_format = '{:.2f}'.format

st.set_page_config(layout="wide")
st.title("NSE Index 6th Sense Scanner")

# =====================================================
# INDEX STOCK LIST (Cloud Safe Hardcoded)
# =====================================================

index_stocks = {
    "Nifty 50": [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "ITC.NS","SBIN.NS","LT.NS","AXISBANK.NS","KOTAKBANK.NS",
        "HINDUNILVR.NS","BAJFINANCE.NS","BHARTIARTL.NS","ASIANPAINT.NS",
        "MARUTI.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS",
        "NESTLEIND.NS","WIPRO.NS"
    ],

    "Nifty Next 50": [
        "DLF.NS","GODREJCP.NS","PIDILITIND.NS","HAVELLS.NS",
        "ICICIPRULI.NS","BANKBARODA.NS","INDIGO.NS",
        "TORNTPHARM.NS","VEDL.NS","SIEMENS.NS"
    ],

    "Nifty Midcap 50": [
        "AUROPHARMA.NS","MPHASIS.NS","COFORGE.NS",
        "BALKRISIND.NS","SRF.NS","MINDTREE.NS",
        "POLYCAB.NS","PAGEIND.NS","ABB.NS","TRENT.NS"
    ]
}

# =====================================================
# ANALYSIS FUNCTION
# =====================================================

def run_analysis():

    index_summary = {}

    for index_name, stocks in index_stocks.items():

        st.markdown(f"## 🟢 {index_name}")

        rows = []
        progress = st.progress(0)
        total = len(stocks)

        for i, symbol in enumerate(stocks):

            try:
                data = yf.download(
                    symbol,
                    period="20d",
                    progress=False,
                    threads=False
                ).dropna()

                if len(data) < 12:
                    continue

                Low_y   = data["Low"].iloc[-2]
                Low_py  = data["Low"].iloc[-3]
                Low_pyy = data["Low"].iloc[-4]
                Low_q   = data["Low"].iloc[-5]
                Low_qy  = data["Low"].iloc[-6]
                Low_qyy = data["Low"].iloc[-7]
                Low_r   = data["Low"].iloc[-8]

                Low_10 = data["Low"].iloc[-11:-1].min()
                today_close = data["Close"].iloc[-1]

                P2L_10 = ((today_close - Low_10) / Low_10) * 100

                L1 = ((Low_y - Low_py) / Low_py) * 100
                L2 = ((Low_py - Low_pyy) / Low_pyy) * 100
                L3 = ((Low_pyy - Low_q) / Low_q) * 100
                L4 = ((Low_q - Low_qy) / Low_qy) * 100
                L5 = ((Low_qy - Low_qyy) / Low_qyy) * 100
                L6 = ((Low_qyy - Low_r) / Low_r) * 100

                L_values = [L1,L2,L3,L4,L5,L6]

                continuous = 0
                for val in L_values:
                    if val < 0:
                        continuous += 1
                    else:
                        break

                sum_L1_L3 = L1 + L2 + L3
                sum_L1_L6 = sum(L_values)

                signal = ""

                if  continuous > 4 and sum_L1_L3 < -4 and sum_L1_L6 < -8:
                    signal = "6thSense"
                elif continuous > 2 and sum_L1_L3 < -3 and sum_L1_L6 < -6:
                    signal = "Sense"
                elif continuous > 2 and sum_L1_L3 < -3 and sum_L1_L6 < -3:
                    signal = "Alert"
                elif continuous > 1 and sum_L1_L3 < -2 and sum_L1_L6 < -3:
                    signal = "Extra"

                rows.append([
                    symbol.replace(".NS",""),
                    round(P2L_10,2),
                    signal,
                    round(today_close,2),
                    round(L1,2), round(L2,2), round(L3,2),
                    round(L4,2), round(L5,2), round(L6,2)
                ])

                time.sleep(0.2)  # prevent rate limit

            except:
                continue

            progress.progress((i+1)/total)

        df = pd.DataFrame(
            rows,
            columns=["Stock","P2L%","6th","Price","L1","L2","L3","L4","L5","L6"]
        )

        if df.empty:
            st.warning("No data available")
            continue

        # INDEX SUMMARY
        index_summary[index_name] = round(df["P2L%"].mean(),2)

        df = df.sort_values(by="P2L%")

        st.dataframe(df, use_container_width=True)

    st.markdown("## 📊 INDEX P2L SUMMARY")
    for k,v in index_summary.items():
        st.write(f"{k}: {v}%")

# =====================================================
# BUTTON
# =====================================================

if st.button("RUN ANALYSIS"):
    run_analysis()
