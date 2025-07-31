import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import plotly.graph_objs as go

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")
st.markdown("Live BTC/Gold Analysis + Support/Resistance + SL/TP + Elliott Wave + Trade Save")

# --- User Input ---
symbol = st.selectbox("Choose Symbol", ["BTC-USD", "XAUUSD=X"])
interval = st.selectbox("Interval", ["1h"])
period = st.selectbox("Period", ["1d"])

# --- Download Data ---
df = yf.download(tickers=symbol, interval=interval, period=period, progress=False)
if df.empty:
    st.error("❌ Data could not be loaded.")
    st.stop()

df.reset_index(inplace=True)

# --- Live Price ---
latest_price = float(df['Close'].iloc[-1])
st.markdown(f"💰 **Live Price ({symbol}):** ${latest_price:.2f}")

# --- Support & Resistance ---
support = float(df['Low'].min())
resistance = float(df['High'].max())
st.markdown(f"📉 **Support:** {support:.2f} | 📈 **Resistance:** {resistance:.2f}")

# --- Trend Detection ---
def detect_trend(data):
    data['MA20'] = data['Close'].rolling(window=20).mean()
    if len(data) < 20 or pd.isna(data['MA20'].iloc[-1]):
        return "No trend"
    last_close = data['Close'].iloc[-1]
    last_ma = data['MA20'].iloc[-1]
    if last_close > last_ma:
        return "Uptrend"
    elif last_close < last_ma:
        return "Downtrend"
    else:
        return "Sideways"

trend = detect_trend(df)
st.markdown(f"📊 **Trend:** {trend}")

# --- Plot Candlestick Chart ---
fig = go.Figure(data=[go.Candlestick(
    x=df['Datetime'] if 'Datetime' in df.columns else df['Date'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close']
)])
fig.update_layout(title=f"{symbol} Candlestick Chart", xaxis_title="Time", yaxis_title="Price", height=500)
st.plotly_chart(fig, use_container_width=True)

# --- Upload Chart Image ---
st.header("📤 Upload Chart Image")
uploaded_image = st.file_uploader("Upload chart image (PNG/JPG)", type=["png", "jpg", "jpeg"])
if uploaded_image:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Chart", use_container_width=True)

# --- Trade Input Section ---
st.header("📝 Trade Entry")
trade_reason = st.text_area("Enter reason for trade", "")
sl = st.text_input("Stop Loss (SL)")
tp = st.text_input("Take Profit (TP)")

# --- Save Trade Button ---
if st.button("💾 Save Trade"):
    if trade_reason.strip() == "":
        st.warning("⚠️ Please enter trade reason.")
    else:
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = "saved_trades.csv"
        new_entry = {
            "Time": time_now,
            "Symbol": symbol,
            "Live Price": latest_price,
            "Support": support,
            "Resistance": resistance,
            "Trend": trend,
            "SL": sl,
            "TP": tp,
            "Reason": trade_reason
        }

        # Append to CSV
        if os.path.exists(filename):
            df_existing = pd.read_csv(filename)
            df_new = pd.DataFrame([new_entry])
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(filename, index=False)
        else:
            pd.DataFrame([new_entry]).to_csv(filename, index=False)

        st.success("✅ Trade saved successfully!")

# --- Show Trade History ---
if os.path.exists("saved_trades.csv"):
    st.subheader("📁 Saved Trade History")
    saved_df = pd.read_csv("saved_trades.csv")
    st.dataframe(saved_df)
