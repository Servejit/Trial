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

st.set_page_config(layout="wide")

# ---------------------------------------------------
# CSS

st.markdown("""

<style>

.block-container
{
padding-top:1rem;
padding-bottom:0rem;
}

.heading
{
background:black;
color:white;
padding:6px;
font-size:18px;
font-weight:bold;
}

.upload
{
font-size:12px;
}

.table-container
{
overflow-x:auto;
}

table
{
min-width:900px;
border-collapse:collapse;
}

th, td
{
padding:6px;
border:1px solid #444;
text-align:center;
}

@keyframes flash
{
0%{opacity:1;}
50%{opacity:0.2;}
100%{opacity:1;}
}

</style>

""", unsafe_allow_html=True)

# ---------------------------------------------------
# CONTROL ROW

c1,c2,c3,c4,c5 = st.columns([1,1,1,1,4])

with c1:
    refresh = st.button("Refresh")

with c2:
    sort = st.button("Sort")

with c3:
    sound_alert = st.toggle("Sound")

with c4:
    telegram_alert = st.toggle("Alert")

with c5:
    stockstar_input = st.text_input(
        "StockStar",
        "DLF.NS, CANBK.NS",
        label_visibility="collapsed"
    ).upper()

stockstar_list = [
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
]

# ---------------------------------------------------
# SMALL UPLOAD

uploaded_sound = st.file_uploader(
"",
type=["mp3","wav"],
label_visibility="collapsed"
)

DEFAULT_SOUND_URL="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# HEADING ABOVE OUTPUT

st.markdown(

'<div class="heading">Live Price with P2L</div>',

unsafe_allow_html=True

)

# ---------------------------------------------------
# STOCK LIST

stocks = {

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

            open_p=data[sym]["Open"].iloc[-1]
            high=data[sym]["High"].iloc[-1]
            low=data[sym]["Low"].iloc[-1]

            p2l=((price-ref)/ref)*100
            chg=((price-prev)/prev)*100

            rows.append({

                "Stock":sym.replace(".NS",""),
                "P2L %":p2l,
                "Price":price,
                "%Chg":chg,
                "Open":open_p,
                "High":high,
                "Low":low

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

# ---------------------------------------------------
# SORT

if sort:

    df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# TELEGRAM

def send_telegram(msg):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url,data={

        "chat_id":CHAT_ID,
        "text":msg

    })

# ---------------------------------------------------
# BACKGROUND

def background():

    while True:

        df=fetch()

        for _,row in df.iterrows():

            if row["Stock"] in stockstar_list and row["P2L %"]<-5:

                msg=f"{row['Stock']} Alert P2L {row['P2L %']:.2f}%"

                send_telegram(msg)

        time.sleep(60)

if telegram_alert:

    threading.Thread(
        target=background,
        daemon=True
    ).start()

# ---------------------------------------------------
# TABLE

green_trigger=False

html='<div class="table-container"><table>'

html+="<tr>"

for col in df.columns:

    html+=f"<th>{col}</th>"

html+="</tr>"

for _,row in df.iterrows():

    html+="<tr>"

    stock=row["Stock"]
    p2l=row["P2L %"]

    for col in df.columns:

        value=row[col]

        style=""

        if col=="Stock":

            if stock in stockstar_list and p2l<-5:

                style="color:lime;font-weight:bold;animation:flash 1s infinite;"
                green_trigger=True

            elif stock in stockstar_list and p2l<-3:

                style="color:orange;font-weight:bold;"

            elif p2l<-2:

                style="color:hotpink;font-weight:bold;"

        if isinstance(value,float):

            value=f"{value:.2f}"

        html+=f"<td style='{style}'>{value}</td>"

    html+="</tr>"

html+="</table></div>"

st.markdown(html,unsafe_allow_html=True)

# ---------------------------------------------------
# SOUND

if sound_alert and green_trigger:

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
<source src="{DEFAULT_SOUND_URL}">
</audio>

""",unsafe_allow_html=True)

# ---------------------------------------------------
# AVG

st.write(

"Average P2L:",
round(df["P2L %"].mean(),2),
"%"

)
