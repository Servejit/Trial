# pip install streamlit yfinance pandas requests

import streamlit as st
import yfinance as yf
import pandas as pd
import base64
import requests
import threading
import time

# ---------------------------------------------------
# TELEGRAM SETTINGS

BOT_TOKEN = "PASTE_NEW_TOKEN"
CHAT_ID = "PASTE_CHAT_ID"

# ---------------------------------------------------

st.set_page_config(page_title="Live P2L", layout="wide")

# ---------------------------------------------------
# CSS

st.markdown("""

<style>

.block-container
{
padding-top:3rem;
}

@keyframes flash {
0% {opacity:1;}
50% {opacity:0.2;}
100% {opacity:1;}
}

.scroll-container {

overflow-x: auto;
white-space: nowrap;
border:1px solid #333;

}

table {

border-collapse: collapse;
min-width:700px;
width:100%;

}

th, td {

padding:8px;
text-align:center;
border:1px solid #444;

}

</style>

""", unsafe_allow_html=True)

# ---------------------------------------------------
# HEADING

st.markdown("## 📊 Live Price with P2L")

# ---------------------------------------------------
# CONTROL BAR

col1,col2,col3,col4,col5 = st.columns([1,1,1,1,4])

with col1:
    refresh = st.button("🔄 Refresh", use_container_width=True)

with col2:
    sort_clicked = st.button("📈 Sort", use_container_width=True)

with col3:
    sound_alert = st.toggle("🔊 Sound", False)

with col4:
    telegram_alert = st.toggle("📲 Alert", False)

with col5:
    stockstar_input = st.text_input(
        "StockStar",
        "DLF.NS, CANBK.NS"
    ).upper()

stockstar_list = [
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
]

# ---------------------------------------------------
# SOUND UPLOAD

uploaded_sound = st.file_uploader(
"",
type=["mp3","wav"],
label_visibility="collapsed"
)

DEFAULT_SOUND="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST

stocks={

"CANBK.NS":142.93,
"DLF.NS":646.85,
"INFY.NS":1377.05,
"HCLTECH.NS":1465.83,
"OIL.NS":468.65,
"PNB.NS":119.90,

}

# ---------------------------------------------------
# FETCH

@st.cache_data(ttl=60)

def fetch():

    symbols=list(stocks.keys())

    data=yf.download(

        tickers=symbols,
        period="2d",
        interval="1d",
        group_by="ticker",
        progress=False

    )

    rows=[]

    for sym in symbols:

        try:

            ref=stocks[sym]

            price=data[sym]["Close"].iloc[-1]
            prev=data[sym]["Close"].iloc[-2]

            p2l=((price-ref)/ref)*100
            chg=((price-prev)/prev)*100

            rows.append({

                "Stock":sym.replace(".NS",""),
                "P2L %":p2l,
                "Price":price,
                "%Chg":chg

            })

        except:
            pass

    return pd.DataFrame(rows)

# ---------------------------------------------------
# REFRESH

if refresh:
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------
# LOAD

df=fetch()

# SORT

if sort_clicked:
    df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# TELEGRAM ALERT

def send_telegram(msg):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url,data={

        "chat_id":CHAT_ID,
        "text":msg

    })

def background():

    while True:

        df=fetch()

        for _,row in df.iterrows():

            if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                msg=f"""

ALERT

{row['Stock']}

P2L: {row['P2L %']:.2f}%

"""

                send_telegram(msg)

        time.sleep(60)

if telegram_alert:

    threading.Thread(
        target=background,
        daemon=True
    ).start()

# ---------------------------------------------------
# BUILD TABLE

green=False

html="""

<div class="scroll-container">

<table>

<tr>

<th>Stock</th>
<th>P2L%</th>
<th>Price</th>
<th>%Chg</th>

</tr>

"""

for _,row in df.iterrows():

    stock=row["Stock"]
    p2l=row["P2L %"]

    style=""

    if stock in stockstar_list and p2l<-5:

        style="color:lime;font-weight:bold;animation:flash 1s infinite;"
        green=True

    elif stock in stockstar_list and p2l<-3:

        style="color:orange;font-weight:bold;"

    elif p2l<-2:

        style="color:hotpink;font-weight:bold;"

    html+=f"""

<tr>

<td style='{style}'>{stock}</td>

<td>{p2l:.2f}</td>

<td>{row['Price']:.2f}</td>

<td>{row['%Chg']:.2f}</td>

</tr>

"""

html+="</table></div>"

st.markdown(html,unsafe_allow_html=True)

# ---------------------------------------------------
# SOUND ALERT

if sound_alert and green:

    if uploaded_sound:

        audio=uploaded_sound.read()

        b64=base64.b64encode(audio).decode()

        st.markdown(f"""

<audio autoplay loop>
<source src="data:audio/mp3;base64,{b64}">
</audio>

""",unsafe_allow_html=True)

    else:

        st.markdown(f"""

<audio autoplay loop>
<source src="{DEFAULT_SOUND}">
</audio>

""",unsafe_allow_html=True)

# ---------------------------------------------------
# AVERAGE

st.write(

"Average P2L:",
round(df["P2L %"].mean(),2),
"%"

)
