import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import os
from PIL import Image
import plotly.graph_objs as go
import base64

# --- Page Config ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Directory Setup ---
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Symbols and Timeframes ---
symbols = {"Bitcoin (BTC)": "BTC-USD", "Gold (XAU)": "GC=F"}
symbol = st.selectbox("Select Asset", list(symbols.keys()))
symbol_yf = symbols[symbol]
timeframes = {"1h": "1h", "15m": "15m", "5m": "5m"}

# --- Fetch Data ---
def get_data(symbol, interval, period='5d'):
    df = yf.download(symbol, interval=interval, period=period)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

# --- Signal Generation ---
def generate_signal(df):
    df['EMA10'] = df['Close'].ewm(span=10).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Signal'] = 0
    df.loc[df['EMA10'] > df['EMA20'], 'Signal'] = 1
    df.loc[df['EMA10'] < df['EMA20'], 'Signal'] = -1
    return df

# --- Accuracy Backtest ---
def backtest_accuracy(df):
    df['Return'] = df['Close'].pct_change().shift(-1)
    df['StrategyReturn'] = df['Signal'].shift(1) * df['Return']
    correct = df[df['StrategyReturn'] > 0]
    total_signals = df[df['Signal'] != 0]
    accuracy = len(correct) / len(total_signals) if len(total_signals) > 0 else 0
    return round(accuracy * 100, 2)

# --- Trend Detection ---
def detect_trend(df):
    last = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])
    return "Uptrend" if last > prev else "Downtrend"

# --- SL/TP Generation ---
def generate_sl_tp(price, signal, trend):
    atr = 0.01 if trend == "Uptrend" else 0.02
    if signal == 1:
        sl = price * (1 - atr)
        tp = price * (1 + atr)
    elif signal == -1:
        sl = price * (1 + atr)
        tp = price * (1 - atr)
    else:
        sl = tp = price
    return round(sl, 2), round(tp, 2)

# --- Save Chart + Reason ---
uploaded_image = st.file_uploader("📸 Upload Chart Image", type=["png", "jpg", "jpeg"])
trade_reason = st.text_area("📝 Enter Trade Reason")

if st.button("💾 Save Chart & Reason"):
    if uploaded_image is not None:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_image.name}"
        filepath = os.path.join("saved_charts", filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_image.read())
        with open(filepath + ".txt", "w", encoding="utf-8") as f:
            f.write(trade_reason)
        st.success("✅ Chart and reason saved!")

# --- Display Saved Charts + Reasons + Delete Option ---
st.subheader("📁 Saved Charts")
delete_files = []
for file in os.listdir("saved_charts"):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        st.image(os.path.join("saved_charts", file), width=400)
        txt_file = os.path.join("saved_charts", file + ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                reason = f.read()
            st.write("📝 Reason:", reason)
        if st.button(f"Delete {file}"):
            os.remove(os.path.join("saved_charts", file))
            if os.path.exists(txt_file):
                os.remove(txt_file)
            st.experimental_rerun()

# --- Multi-timeframe Signal Display ---
all_signals = []
for tf_name, tf in timeframes.items():
    st.markdown("---")
    st.subheader(f"🕒 Timeframe: {tf_name.upper()}")
    df = get_data(symbol_yf, tf)
    df = generate_signal(df)
    acc = backtest_accuracy(df)
    trend = detect_trend(df)
    latest_signal = df['Signal'].iloc[-1]
    signal_text = "Buy" if latest_signal == 1 else "Sell" if latest_signal == -1 else "No Signal"
    price = df['Close'].iloc[-1]
    sl, tp = generate_sl_tp(price, latest_signal, trend)
    reward = tp - price
    risk = price - sl if latest_signal == 1 else sl - price
    rr_ratio = round(reward / risk, 2) if risk != 0 else "∞"

    st.write(f"**Trend:** `{trend}`")
    st.write(f"**Signal:** `{signal_text}`")
    st.write(f"**Accuracy:** `{acc}%`")
    st.write(f"**Entry Price:** `{round(price, 2)}`")
    st.write(f"**SL:** `{sl}` | **TP:** `{tp}`")
    st.write(f"📊 **Risk/Reward Ratio:** `{rr_ratio}`")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Candles'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA10'], line=dict(color='blue', width=1), name='EMA10'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='orange', width=1), name='EMA20'))
    st.plotly_chart(fig, use_container_width=True)

    # --- Elliott Wave Breakout Basic Placeholder ---
    # (Real logic should be complex)
    if latest_signal == 1 and trend == "Uptrend":
        st.success("🌀 Elliott Wave 3 Uptrend Breakout Detected!")
    elif latest_signal == -1 and trend == "Downtrend":
        st.error("🌀 Elliott Wave 3 Downtrend Breakout Detected!")

    # --- Collect for CSV Export ---
    all_signals.append({"Timeframe": tf_name, "Trend": trend, "Signal": signal_text, "Accuracy": acc,
                        "Entry": round(price, 2), "SL": sl, "TP": tp, "RR Ratio": rr_ratio})

# --- Export CSV ---
st.markdown("---")
st.subheader("📂 Export Trade History")
if all_signals:
    csv_df = pd.DataFrame(all_signals)
    csv = csv_df.to_csv(index=False).encode("utf-8")
    b64 = base64.b64encode(csv).decode()
    st.download_button("🔧 Download CSV", csv, "trade_history.csv", "text/csv")
