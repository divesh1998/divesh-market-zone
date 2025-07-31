import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone - BTC & Gold Analysis")

# 📤 Upload Chart Image Section
st.header("📤 Upload Chart Image")
uploaded_image = st.file_uploader("Upload a chart image (optional)", type=["jpg", "jpeg", "png"])
if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Chart", use_container_width=True)  # ✅ fixed here

# 📊 Live Market Analysis Section
st.header("📊 Live Market Analysis")
symbol = st.selectbox("Select Asset", ["BTC-USD", "GC=F"])

# Download market data
df = yf.download(symbol, period="5d", interval="1h")

if df.empty:
    st.error("❌ Failed to fetch data. Please try again later.")
else:
    try:
        # Extract last open/close values
        last_open = df["Open"].iloc[-1].item()
        last_close = df["Close"].iloc[-1].item()

        # Calculate support and resistance
        support = float(df["Low"].min())
        resistance = float(df["High"].max())

        # Determine candle type
        candle_type = "Bullish" if last_close > last_open else "Bearish"

        # Generate signal
        if candle_type == "Bullish" and abs(last_close - support) < 10:
            signal = "BUY"
        elif candle_type == "Bearish" and abs(last_close - resistance) < 10:
            signal = "SELL"
        else:
            signal = "NO TRADE ZONE"

    except Exception as e:
        candle_type = "Unknown"
        signal = f"Error: {e}"
        support = resistance = last_close = 0

    # Display results
    st.metric("Live Price", f"${last_close:.2f}")
    st.write(f"Support: `{support:.2f}` | Resistance: `{resistance:.2f}` | Candle: `{candle_type}` | Signal: **{signal}**")

    # 📈 Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"]
    )])
    fig.add_hline(y=support, line_color="green", line_dash="dot", annotation_text="Support")
    fig.add_hline(y=resistance, line_color="red", line_dash="dot", annotation_text="Resistance")

    st.plotly_chart(fig, use_container_width=True)
