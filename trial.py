import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io
import warnings

warnings.filterwarnings("ignore")
pd.options.display.float_format = '{:.2f}'.format

st.set_page_config(layout="wide")
st.title("NSE Index Stock Analysis")

index_urls = {
    "Nifty 50":
    "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",

    "Nifty Next 50":
    "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",

    "Nifty Midcap 50":
    "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv"
}

# -----------------------------------------------------
# NSE SESSION FIX
# -----------------------------------------------------

def get_index_stocks(url):

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(url, headers=headers)

    df = pd.read_csv(io.StringIO(response.text))
    stocks = df["Symbol"].dropna().tolist()

    return [stock + ".NS" for stock in stocks]


# -----------------------------------------------------
# COLOR FUNCTION
# -----------------------------------------------------

def get_stock_color(row):

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
    else:
        return ""


# -----------------------------------------------------
# RUN
# -----------------------------------------------------

if st.button("RUN ANALYSIS"):

    index_summary = {}

    for index_name, url in index_urls.items():

        st.markdown(f"## {index_name}")

        try:
            stocks = get_index_stocks(url)
        except:
            st.error("Could not fetch stock list")
            continue

        rows = []

        for symbol in stocks:

            try:
                data = yf.download(symbol, period="15d", progress=False).dropna()
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

                L_values = [L1, L2, L3, L4, L5, L6]

                continuous = 0
                for val in L_values:
                    if val < 0:
                        continuous += 1
                    else:
                        break

                sum_L1_L3 = L1 + L2 + L3
                sum_L1_L6 = sum(L_values)

                signal = ""

                if continuous > 4 and sum_L1_L3 < -4 and sum_L1_L6 < -8:
                    signal = "6thSense"
                elif continuous > 2 and sum_L1_L3 < -3 and sum_L1_L6 < -6:
                    signal = "Sense"
                elif continuous > 2 and sum_L1_L3 < -3 and sum_L1_L6 < -3:
                    signal = "Alert"
                elif continuous > 1 and sum_L1_L3 < -2 and sum_L1_L6 < -3:
                    signal = "Extra"

                rows.append([
                    symbol.replace(".NS",""),
                    P2L_10,
                    signal,
                    today_close,
                    Low_y, Low_py, Low_pyy,
                    Low_q, Low_qy, Low_qyy,
                    Low_r, Low_10,
                    L1,L2,L3,L4,L5,L6
                ])

            except:
                continue

        df = pd.DataFrame(rows, columns=[
            "Stock","P2L%","6th","Price",
            "Low.y","Low.py","Low.pyy",
            "Low.q","Low.qy","Low.qyy",
            "Low.r","Low.10",
            "L1","L2","L3","L4","L5","L6"
        ]).dropna()

        if df.empty:
            st.warning("No data available")
            continue

        # Sorting logic
        df["Priority"] = df.apply(
            lambda x: 0 if (x["6th"] != "" and x["L1"]<-0.5 and x["L2"]<-0.5 and x["L3"]<-0.5) else 1,
            axis=1
        )
        df = df.sort_values(by=["Priority","P2L%"], ascending=[True,True])
        df = df.drop(columns=["Priority"])

        # INDEX P2L
        avg_price = df["Price"].mean()
        avg_low   = df["Low.y"].mean()
        index_p2l = ((avg_price - avg_low) / avg_low) * 100
        index_summary[index_name] = index_p2l

        # HTML TABLE WITH COLORS
        html = df.to_html(index=False)

        for i, row in df.iterrows():
            color = get_stock_color(row)
            if color:
                text_color = "white" if row["6th"] == "6thSense" else "black"
                html = html.replace(
                    f"<td>{row['Stock']}</td>",
                    f"<td style='background-color:{color}; color:{text_color}; font-weight:bold'>{row['Stock']}</td>"
                )

        st.markdown(html, unsafe_allow_html=True)

    st.markdown("## INDEX P2L SUMMARY")
    for k,v in index_summary.items():
        st.write(f"{k} P2L: {round(v,2)} %")
