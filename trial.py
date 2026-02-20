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
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# ---------------------------------------------------
# FLASH CSS
st.markdown("""
<style>
@keyframes flash {
0% {opacity:1;}
50% {opacity:0.2;}
100% {opacity:1;}
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
"BOSCHLTD.NS, BSE.NS"
).upper()

stockstar_list = [
s.strip().replace(".NS","")
for s in stockstar_input.split(",")
if s.strip()
]

# ---------------------------------------------------
# SOUND
sound_alert = st.toggle("🔊 Enable Sound", value=False)

# ---------------------------------------------------
# TELEGRAM
telegram_alert = st.toggle("📲 Enable Telegram", value=False)

# ---------------------------------------------------
# SOUND UPLOAD
uploaded_sound = st.file_uploader(
"Upload Sound",
type=["mp3","wav"]
)

DEFAULT_SOUND_URL = "https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3"

# ---------------------------------------------------
# STOCK LIST
stocks = {

"BSE.NS":2718.29,
"BOSCHLTD.NS":35043.90,
"HEROMOTOCO.NS":5419.27,
"HINDALCO.NS":878.80,
"HINDZINC.NS":573.56,
"MUTHOOTFIN.NS":3431.50,
"PIIND.NS":2999.93

}

# ---------------------------------------------------
# SESSION STATE
if "rundown_start" not in st.session_state:

st.session_state.rundown_start = {}

# ---------------------------------------------------
# FETCH DATA
@st.cache_data(ttl=60)
def fetch():

data = yf.download(
tickers=list(stocks.keys()),
period="2d",
interval="1d",
group_by="ticker",
progress=False
)

rows=[]

now = datetime.now()

for symbol in stocks:

try:

ref = stocks[symbol]

price = data[symbol]["Close"].iloc[-1]

prev = data[symbol]["Close"].iloc[-2]

openp = data[symbol]["Open"].iloc[-1]

high = data[symbol]["High"].iloc[-1]

low = data[symbol]["Low"].iloc[-1]

p2l=((price-ref)/ref)*100

chg=((price-prev)/prev)*100

key=symbol.replace(".NS","")

# -------- RUN DOWN REAL --------

if price < ref:

if key not in st.session_state.rundown_start:

st.session_state.rundown_start[key]=now

start=st.session_state.rundown_start[key]

minutes=int((now-start).total_seconds()/60)

rundown=f"🟠{minutes}"

else:

st.session_state.rundown_start[key]=now

rundown="0"

rows.append({

"Stock":key,

"P2L %":p2l,

"Price":price,

"% Chg":chg,

"Low Price":ref,

"Open":openp,

"High":high,

"Low":low,

"Run Down":rundown

})

except:

pass

return pd.DataFrame(rows)

# ---------------------------------------------------
# BUTTONS
col1,col2=st.columns(2)

with col1:

if st.button("🔄 Refresh"):

st.cache_data.clear()

st.rerun()

with col2:

sort=st.button("📈 Sort by P2L")

# ---------------------------------------------------
# LOAD

df=fetch()

if sort:

df=df.sort_values("P2L %",ascending=False)

# ---------------------------------------------------
# ALERT CHECK
trigger=False

for _,row in df.iterrows():

if row["Stock"] in stockstar_list and row["P2L %"]<-5:

trigger=True

stock=row["Stock"]

price=row["Price"]

p2l=row["P2L %"]

break

# ---------------------------------------------------
# TELEGRAM ALERT

if telegram_alert and trigger:

msg=f"""

GREEN ALERT

{stock}

Price {price}

P2L {p2l:.2f}

"""

requests.post(

f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",

data={"chat_id":CHAT_ID,"text":msg}

)

# ---------------------------------------------------
# TABLE

def table(df):

html="<table><tr>"

for col in df.columns:

html+=f"<th>{col}</th>"

html+="</tr>"

for _,row in df.iterrows():

html+="<tr>"

for col in df.columns:

val=row[col]

style="padding:6px;text-align:center;"

if col=="Stock":

if row["Stock"] in stockstar_list and row["P2L %"]<-5:

style+="color:green;font-weight:bold;animation:flash 1s infinite;"

elif row["Stock"] in stockstar_list and row["P2L %"]<-3:

style+="color:orange;font-weight:bold;"

elif row["P2L %"]<-2:

style+="color:hotpink;font-weight:bold;"

if col in ["P2L %","% Chg"]:

if val>0:

style+="color:green;font-weight:bold;"

elif val<0:

style+="color:red;font-weight:bold;"

if isinstance(val,float):

val=f"{val:.2f}"

html+=f"<td style='{style}'>{val}</td>"

html+="</tr>"

html+="</table>"

return html

st.markdown(table(df),unsafe_allow_html=True)

# ---------------------------------------------------
# SOUND ALERT

if sound_alert and trigger:

if uploaded_sound:

audio=base64.b64encode(uploaded_sound.read()).decode()

st.markdown(

f"<audio autoplay src='data:audio/mp3;base64,{audio}'></audio>",

unsafe_allow_html=True

)

else:

st.markdown(

f"<audio autoplay src='{DEFAULT_SOUND_URL}'></audio>",

unsafe_allow_html=True

)

# ---------------------------------------------------
# AVERAGE

avg=df["P2L %"].mean()

st.markdown(f"### Average P2L {avg:.2f}%")
