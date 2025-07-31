import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
import os
from PIL import Image

# --- Page Setup ---
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Folder Setup ---
os.makedirs("saved_charts", exist_ok=True)

# --- Sidebar Selection ---
st.sidebar.header("🔎 Select Symbol & Timeframe")
symbol = st.sidebar.selectbox("Select Symbol", ["BTC-USD", "GC=F"], index=0)
timeframes = {"1h": "1d", "15m": "5d", "5m": "1d"}
tf = st.sidebar.selectbox("Select Timeframe", list(timeframes.keys()), index=0)
period = timeframes[tf]

# --- Fetch Data ---
df = yf.download(tickers=symbol, interval=tf, period=period, progress=False, auto_adjust=True)

if df.empty:
    st.error("❌ Data not loaded. Please try a different timeframe or symbol.")
    st.stop()

df.index = df.index.tz_localize(None)

# --- Moving Average ---
if len(df) >= 20:
    df["MA"] = df["Close"].rolling(window=20).mean()
else:
    df["MA"] = None

# --- Trend Detection ---
def detect_trend(df):
    if "MA" not in df.columns or df["MA"].isna().iloc[-1]:
        return "No Trend"
    last_close = df["Close"].iloc[-1].item()
    last_ma = df["MA"].iloc[-1].item()
    if last_close > last_ma:
        return "Uptrend"
    elif last_close < last_ma:
        return "Downtrend"
    else:
        return "Sideways"

trend = detect_trend(df)
signal = "Buy Signal 📈" if trend == "Uptrend" else "Sell Signal 📉" if trend == "Downtrend" else "No Trade"

# --- Elliott Wave Breakout ---
wave1_high = st.sidebar.number_input("Wave 1 High Price", value=0.0)
current_price = df["Close"].iloc[-1].item()
breakout_status = "Not Breaking Wave 1 High"
if wave1_high > 0 and current_price > wave1_high:
    breakout_status = "Wave 1 Breakout → Wave 3 Entry ✅"

# --- Plot Chart ---
if len(df) > 1:
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles"
    ))

    # Moving Average
    if "MA" in df.columns and df["MA"].notna().any():
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA"],
            mode="lines", name="Moving Avg",
            line=dict(color="orange", width=2)
        ))

    # Wave 1 High Line
    if wave1_high > 0:
        fig.add_trace(go.Scatter(
            x=[df.index[0], df.index[-1]],
            y=[wave1_high, wave1_high],
            mode="lines",
            name="Wave 1 High",
            line=dict(color="blue", dash="dash")
        ))

    fig.update_layout(
        title=f"{symbol} Chart ({tf}) | Live Price: {current_price:.2f}",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Not enough data to plot the chart.")

# --- Trade Input ---
st.subheader("📝 Trade Details")
sl = st.text_input("Stop Loss (SL)")
tp = st.text_input("Take Profit (TP)")
reason = st.text_area("Reason for Trade")

# --- Signal Output ---
st.success(f"Trend: {trend}")
st.info(f"Signal: {signal}")
st.warning(f"Elliott Wave Status: {breakout_status}")

# --- Export Chart ---
if st.button("📸 Export Chart as Image"):
    try:
        fig.write_image("exported_chart.png")
        st.image("exported_chart.png", caption="Exported Chart")
    except Exception as e:
        st.error("Image export failed. Install kaleido:\n`pip install -U kaleido`")

# --- Upload Chart Image ---
st.subheader("📤 Upload Chart Image")
uploaded_file = st.file_uploader("Upload Chart Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
if uploaded_file:
    image_path = os.path.join("saved_charts", uploaded_file.name)
    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success("✅ Image Saved")
    st.image(image_path)

# --- Save Trade Info ---
if st.button("💾 Save Trade"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text_filename = f"saved_charts/trade_{timestamp}.txt"
    with open(text_filename, "w", encoding="utf-8") as f:
        f.write(f"Symbol: {symbol}\n")
        f.write(f"Timeframe: {tf}\n")
        f.write(f"Trend: {trend}\n")
        f.write(f"Signal: {signal}\n")
        f.write(f"Wave Status: {breakout_status}\n")
        f.write(f"SL: {sl}\nTP: {tp}\nReason: {reason}\n")
    st.success("📝 Trade Info Saved")

# --- Show Uploaded Images + Delete Option ---
st.subheader("🖼️ Saved Uploaded Images")
image_files = [f for f in os.listdir("saved_charts") if f.endswith((".png", ".jpg", ".jpeg"))]
if image_files:
    for img in image_files:
        img_path = os.path.join("saved_charts", img)
        with st.expander(f"🖼️ {img}"):
            st.image(img_path, width=300)
            if st.button(f"🗑️ Delete {img}", key=img):
                os.remove(img_path)
                st.warning(f"{img} deleted.")
                st.experimental_rerun()
else:
    st.info("No uploaded images yet.")

# --- Show Trade Info Files + Delete Option ---
st.subheader("🗂️ Saved Trade Info Files")
text_files = [f for f in os.listdir("saved_charts") if f.endswith(".txt")]
if text_files:
    for txt_file in text_files:
        file_path = os.path.join("saved_charts", txt_file)
        with st.expander(f"📄 {txt_file}"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                st.code(content, language="text")
            if st.button(f"🗑️ Delete {txt_file}", key=txt_file):
                os.remove(file_path)
                st.warning(f"{txt_file} deleted.")
                st.experimental_rerun()
else:
    st.info("No saved trade info files.")
