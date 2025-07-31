import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image
import os

# Page setup
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("📊 Divesh Market Zone - BTC & Gold Analysis")

# Create folder to save uploaded images
UPLOAD_FOLDER = "saved_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Image upload section
st.subheader("🖼️ Upload Chart Image")
uploaded_image = st.file_uploader("Upload a chart image (optional)", type=["jpg", "jpeg", "png"])
if uploaded_image:
    img = Image.open(uploaded_image)
    filename = os.path.join(UPLOAD_FOLDER, uploaded_image.name)
    img.save(filename)
    st.image(filename, caption="Uploaded Chart", use_container_width=True)

# Show all uploaded images
st.subheader("🗂️ All Uploaded Images (Temporary View)")
image_files = os.listdir(UPLOAD_FOLDER)
if image_files:
    for fname in image_files:
        st.image(os.path.join(UPLOAD_FOLDER, fname), use_container_width=True)
else:
    st.info("No images uploaded yet.")

# Asset selection and data fetch
st.subheader("📈 Live Market Analysis")
symbol = st.selectbox("Select Asset", ["BTC-USD", "GC=F"])
df = yf.download(symbol, period="5d", interval="1h")

if df.empty or len(df) < 1:
    st.error("❌ Failed to fetch market data.")
else:
    # Extract values safely
    support = float(df["Low"].min())
    resistance = float(df["High"].max())
    close_price = float(df["Close"].iloc[-1])
    open_price = float(df["Open"].iloc[-1])

    # Candle and signal logic
    candle_type = "Bullish" if close_price > open_price else "Bearish"
    signal = "BUY" if candle_type == "Bullish" and abs(close_price - support) < 10 else \
             "SELL" if candle_type == "Bearish" and abs(close_price - resistance) < 10 else \
             "NO TRADE ZONE"

    # Show metrics and signal
    st.metric("Live Price", f"${close_price:.2f}")
    st.write(f"🟢 **Support:** `{support:.2f}`")
    st.write(f"🔴 **Resistance:** `{resistance:.2f}`")
    st.write(f"🕯️ **Candle Type:** `{candle_type}`")
    st.write(f"📢 **Signal:** **{signal}**")

    # Candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.add_hline(y=support, line_color="green", line_dash="dot", annotation_text="Support", annotation_position="bottom right")
    fig.add_hline(y=resistance, line_color="red", line_dash="dot", annotation_text="Resistance", annotation_position="top right")
    st.plotly_chart(fig, use_container_width=True)
