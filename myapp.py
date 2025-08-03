import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import os
import uuid
import html
import time
from PIL import Image

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

SAVE_DIR = "saved_charts"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

now = time.time()
for file in os.listdir(SAVE_DIR):
    path = os.path.join(SAVE_DIR, file)
    if os.path.isfile(path) and os.stat(path).st_mtime < now - 7 * 86400:
        os.remove(path)

symbols = {"Bitcoin (BTC)": "BTC-USD", "Gold (XAU)": "GC=F"}
symbol = st.selectbox("Select Asset", list(symbols.keys()))
symbol_yf = symbols[symbol]
timeframes = {"1H": "1h", "15M": "15m", "5M": "5m"}

def get_data(symbol, interval, period='5d'):
    df = yf.download(symbol, interval=interval, period=period)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

def detect_trend(df):
    return "Uptrend" if df["Close"].iloc[-1] > df["Close"].iloc[-2] else "Downtrend"

def generate_signal(df):
    df['EMA10'] = df['Close'].ewm(span=10).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Signal'] = 0
    trend = detect_trend(df)
    if trend == "Uptrend":
        df.loc[df['EMA10'] > df['EMA20'], 'Signal'] = 1
    elif trend == "Downtrend":
        df.loc[df['EMA10'] < df['EMA20'], 'Signal'] = -1
    return df

def detect_support_resistance(df, window=20):
    support = df['Low'][::-1].rolling(window=window).min().dropna().iloc[-1]
    resistance = df['High'][::-1].rolling(window=window).max().dropna().iloc[-1]
    return round(support, 2), round(resistance, 2)

def is_sideways(price, support, resistance, threshold=0.01):
    return (resistance - support) / price < threshold

def enhanced_signal(df):
    df = generate_signal(df)
    trend = detect_trend(df)
    support, resistance = detect_support_resistance(df)
    price = df['Close'].iloc[-1]
    signal = df['Signal'].iloc[-1]
    scalping = False

    if is_sideways(price, support, resistance):
        trend = "Sideways"
        if signal != 0:
            scalping = True
    return df, signal, trend, support, resistance, scalping

def generate_sl_tp(price, signal, trend):
    atr = 0.015 if trend == "Uptrend" else 0.02
    rr = 2.0
    if signal == 1:
        sl = price * (1 - atr)
        tp = price + (price - sl) * rr
    elif signal == -1:
        sl = price * (1 + atr)
        tp = price - (sl - price) * rr
    else:
        sl = tp = price
    return round(sl, 2), round(tp, 2)

def backtest_accuracy(df):
    df['Return'] = df['Close'].pct_change().shift(-1)
    df['StrategyReturn'] = df['Signal'].shift(1) * df['Return']
    total = df[df['Signal'] != 0]
    correct = df[df['StrategyReturn'] > 0]
    return round(len(correct) / len(total) * 100, 2) if len(total) else 0

def detect_elliott_wave_breakout(df):
    if len(df) < 6:
        return False, ""
    wave1_end = df['High'].iloc[-5]
    wave2 = df['Low'].iloc[-4]
    current_price = df['Close'].iloc[-1]
    trend = detect_trend(df)
    if trend == "Uptrend" and current_price > wave1_end:
        return True, "🌀 Elliott Wave 3 Uptrend Breakout Detected!"
    elif trend == "Downtrend" and current_price < wave2:
        return True, "🌀 Elliott Wave 3 Downtrend Breakout Detected!"
    return False, ""

uploaded_image = st.file_uploader("📸 Upload Chart", type=["png", "jpg", "jpeg"])
trade_reason = st.text_area("📝 Enter Trade Reason")

if st.button("💾 Save Chart & Reason"):
    if uploaded_image is not None:
        if uploaded_image.size > 3 * 1024 * 1024:
            st.error("🚫 File too large! Max size: 3MB")
            st.stop()
        ext = uploaded_image.name.split('.')[-1]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"
        filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_image.read())
        safe_reason = html.escape(trade_reason)
        with open(filepath + ".txt", "w", encoding="utf-8") as f:
            f.write(safe_reason)
        st.success("✅ Chart and Reason Saved!")

st.subheader("📁 Saved Charts")
for file in sorted(os.listdir(SAVE_DIR), reverse=True):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        st.image(os.path.join(SAVE_DIR, file), width=350)
        txt_file = os.path.join(SAVE_DIR, file + ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                reason = f.read()
            st.caption(f"📝 Reason: {reason}")

for tf_label, tf_code in timeframes.items():
    st.markdown("---")
    st.subheader(f"🕒 Timeframe: {tf_label}")
    df = get_data(symbol_yf, tf_code)
    df, signal, trend, support, resistance, scalping = enhanced_signal(df)
    acc = backtest_accuracy(df)
    price = round(df["Close"].iloc[-1], 2)
    sl, tp = generate_sl_tp(price, signal, trend)
    reward = abs(tp - price)
    risk = abs(price - sl)
    rr_ratio = round(reward / risk, 2) if risk != 0 else "∞"
    signal_text = "Buy" if signal == 1 else "Sell" if signal == -1 else "No Signal"
    st.write(f"**Trend:** `{trend}`")
    st.write(f"**Signal:** `{signal_text}`")
    st.write(f"**Accuracy:** `{acc}%`")
    st.write(f"**Entry Price:** `{price}`")
    st.write(f"**Support:** `{support}` | **Resistance:** `{resistance}`")
    st.write(f"**SL:** `{sl}` | **TP:** `{tp}`")
    st.write(f"📊 **Risk/Reward Ratio:** `{rr_ratio}`")
    if scalping:
        st.info("💡 Sideways Market Detected — Scalping Opportunity")
    breakout, message = detect_elliott_wave_breakout(df)
    if breakout:
        st.warning(message)
    st.line_chart(df[['Close']])
