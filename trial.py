# =====================================================
# IMPORT
# =====================================================

import streamlit as st
import pandas as pd
import yfinance as yf
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(layout="wide")
st.title("NSE Index 6th Sense Scanner")

# =====================================================
# INDEX STOCKS (Bulk Safe)
# =====================================================

index_stocks = {
    "Nifty 50": [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "ITC.NS","SBIN.NS","LT.NS","AXISBANK.NS","KOTAKBANK.NS",
        "HINDUNILVR.NS","BAJFINANCE.NS","BHARTIARTL.NS","ASIANPAINT.NS",
        "MARUTI.NS","TITAN.NS","SUNPHARMA.NS","ULTRACEMCO.NS",
        "NESTLEIND.NS","WIPRO.NS"
    ]
}

# =====================================================
# COLOR LOGIC (Original Rules Preserved)
# =====================================================

def get_color(row):

    if row["6th"] == "":
        return ""

    if row["L1"] < -1.50 and row["L2"] < -1.50 and row["L3"] < -1.50:
        return "green"
    elif row["L1"] < -1.00 and row["L2"] < -1.00 and row["L3"] < -1.00:
        return "orange"
    elif row["L1"] < -0.75 and row["L2"] < -0.75 and row["L3"] < -0.75:
        return "hotpink"
    elif row["L1"] < -0.50 and row["L2"] < -0.50 and row["L3"] < -0.50:
        return "yellow"

    return ""

# =====================================================
# ANALYSIS
# =====================================================

def run_analysis():

    for index_name, stocks in index_stocks.items():

        st.markdown(f"## 🟢 {index_name}")

        data = yf.download(
            tickers=stocks,
            period="20d",
            group_by='ticker',
            threads=False,
            progress=False
        )

        rows = []

        for symbol in stocks:

            try:
                df = data[symbol].dropna()
                if len(df) < 12:
                    continue

                Low_y   = df["Low"].iloc[-2]
                Low_py  = df["Low"].iloc[-3]
                Low_pyy = df["Low"].iloc[-4]
                Low_q   = df["Low"].iloc[-5]
                Low_qy  = df["Low"].iloc[-6]
                Low_qyy = df["Low"].iloc[-7]
                Low_r   = df["Low"].iloc[-8]

                Low_10 = df["Low"].iloc[-11:-1].min()
                today_close = df["Close"].iloc[-1]

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
                    round(Low_y,2),
                    round(Low_py,2),
                    round(Low_pyy,2),
                    round(Low_q,2),
                    round(Low_qy,2),
                    round(Low_qyy,2),
                    round(Low_r,2),
                    round(Low_10,2),
                    round(L1,2),round(L2,2),round(L3,2),
                    round(L4,2),round(L5,2),round(L6,2)
                ])

            except:
                continue

        df_result = pd.DataFrame(
            rows,
            columns=[
                "Stock","P2L%","6th","Price",
                "Low.y","Low.py","Low.pyy",
                "Low.q","Low.qy","Low.qyy",
                "Low.r","Low.10",
                "L1","L2","L3","L4","L5","L6"
            ]
        )

        if df_result.empty:
            st.warning("No data available")
            continue

        # SORTING (Original Priority Logic)
        df_result["Color"] = df_result.apply(get_color, axis=1)

        df_result = df_result.sort_values(by=["P2L%"])

        # DISPLAY WITH ROW COLORS
        def highlight_row(row):
            color = row["Color"]
            if color == "":
                return [""] * len(row)
            return [f"background-color:{color}"] * len(row)

        st.dataframe(
            df_result.style.apply(highlight_row, axis=1),
            use_container_width=True
        )

# =====================================================
# BUTTON
# =====================================================

if st.button("RUN ANALYSIS"):
    run_analysis()
