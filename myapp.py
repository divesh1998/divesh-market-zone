import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from PIL import Image
import os

# Page setup
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("Divesh Market Zone - BTC & Gold Analysis")

# Create folder for saving images
UPLOAD_FOLDER = "saved_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Image upload section
st.subheader("Upload Chart Image")
uploaded_image = st.file_uploader("Upload a chart image (optional)", type=["jpg", "jpeg", "png"])
if uploaded_image:
    img = Image.open(uploaded_image)
    filename = os.path.join(UPLOAD_FOLDER, uploaded_image.name)
    img.save(filename)
    st.image(filename, caption="Uploaded Chart", use_container_width=True)

# Show all uploaded images (temporary)
st.subheader("All Uploaded Images (temporary)")
image_files = os.listdir(UPLOAD_FOLDER)
if image_files:
    for fname in image_files:
        st.image(os.path.join(UPLOAD_FOLDER, fname), use_container_width=True)
else:
    st.info("No images uploaded yet.")

# Asset selection and data download
symbol = st.selectbox("Select Asset", ["BTC-USD", "GC=F"])
df = yf.download(symbol, period="5d", interval="1h")

if df.empty:
    st.error("❌ Failed to fetch data. Please try again later.")
else:
    support = df["Low"].min()
    resistance = df["High"].max()
    close_price = df["Close"].iloc[-1]
    open_price = df["Open"].iloc[-1]

    candle_type = "Bullish" if close_price > open_price else "Bearish"
    signal = "BUY" if candle_type == "Bullish" and abs(close_price - support) < 10 else \
             "SELL" if candle_type == "Bearish" and abs(close_price - resistance) < 10 else \
             "NO TRADE ZONE"

    st.metric("Live Price", f"${close_price:.2f}")
    st.write(f"Support: `{support:.2f}` | Resistance: `{resistance:.2f}` | Candle: `{candle_type}` | Signal: **{signal}**")

    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"]
    )])
    fig.add_hline(y=support, line_color="green")
    fig.add_hline(y=resistance, line_color="red")
    st.plotly_chart(fig, use_container_width=True)
