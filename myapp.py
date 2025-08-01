import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from PIL import Image
import os
import plotly.graph_objs as go

# --- Page Setup ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("💹 Divesh Market Zone")
st.markdown("**Live BTC/Gold Chart + Signal + Support/Resistance + Elliott Wave + SL/TP + Trade Save**")

# --- Select Symbol & Timeframe ---
col1, col2 = st.columns(2)
with col1:
    symbol = st.selectbox("📊 Select Symbol", ["BTC-USD", "GC=F"], index=0)
with col2:
    interval = st.selectbox("⏱️ Timeframe", ["1h", "15m", "5m"])

period = "5d"

# --- Download Live Data ---
df = yf.download(symbol, interval=interval, period=period)
if df.empty or len(df) < 2:
    st.warning("⚠️ Not enough data to display chart.")
    st.stop()

# --- Show Interactive Chart ---
st.subheader("🕹️ Price Chart")
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name="Candles"
)])
fig.update_layout(
    xaxis_title="Time",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    template="plotly_dark",
    height=500
)
st.plotly_chart(fig, use_container_width=True)

# --- Detect Trend ---
def detect_trend(df):
    last = df["Close"].iloc[-1].item()
    prev = df["Close"].iloc[-2].item()
    if last > prev:
        return "Uptrend"
    elif last < prev:
        return "Downtrend"
    else:
        return "Sideways"

trend = detect_trend(df)
st.subheader(f"📉 Current Trend: `{trend}`")

# --- Support/Resistance Calculation ---
def calculate_sr(data):
    support = round(data["Low"].rolling(20).min().iloc[-1], 2)
    resistance = round(data["High"].rolling(20).max().iloc[-1], 2)
    return support, resistance

support, resistance = calculate_sr(df)
st.write(f"🟢 **Support:** `{support}`")
st.write(f"🔴 **Resistance:** `{resistance}`")

# --- Elliott Wave Breakout ---
wave1_high = st.number_input("🌊 Wave 1 High Price", value=0.0)
signal = "No Signal"
last_price = df["Close"].iloc[-1].item()

if wave1_high > 0:
    if trend == "Uptrend" and last_price > wave1_high:
        signal = "📈 Buy Signal (Wave 3 Breakout)"
    elif trend == "Downtrend" and last_price < wave1_high:
        signal = "📉 Sell Signal (Wave 3 Breakdown)"

st.subheader(f"📍 Signal: `{signal}`")

# --- SL/TP Auto Calculation ---
sl_auto = round(support if trend == "Uptrend" else resistance, 2)
tp_auto = round(resistance if trend == "Uptrend" else support, 2)

st.write(f"🛡️ **Auto SL:** `{sl_auto}`")
st.write(f"🎯 **Auto TP:** `{tp_auto}`")

# --- Trade Reason Input ---
reason = st.text_area("📋 Trade Reason", placeholder="Enter your analysis or reason here...")

# --- Upload Chart Image ---
st.header("📤 Upload Chart Image")
uploaded_image = st.file_uploader("Upload chart image (JPG/PNG)", type=["png", "jpg", "jpeg"])
save_folder = "saved_charts"
os.makedirs(save_folder, exist_ok=True)

# --- Save Trade ---
if st.button("💾 Save Trade"):
    if uploaded_image is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{symbol.replace('=', '').replace('-', '')}.png"
        file_path = os.path.join(save_folder, filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_image.read())

        # Save accompanying text
        txt_path = file_path.replace(".png", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Signal: {signal}\n")
            f.write(f"SL: {sl_auto}\n")
            f.write(f"TP: {tp_auto}\n")
            f.write(f"Reason: {reason}")

        st.success("✅ Trade saved successfully!")
    else:
        st.warning("⚠️ Please upload a chart image first.")

# --- Display Saved Trades ---
st.header("🗂️ Saved Trades")
image_files = [f for f in os.listdir(save_folder) if f.endswith(".png")]
for i in image_files:
    st.image(os.path.join(save_folder, i), width=400, caption=i)
    txt_file = i.replace(".png", ".txt")
    txt_path = os.path.join(save_folder, txt_file)
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            st.code(f.read())
    if st.button(f"🗑️ Delete {i}"):
        os.remove(os.path.join(save_folder, i))
        if os.path.exists(txt_path):
            os.remove(txt_path)
        st.rerun()
