import streamlit as st
import yfinance as yf
import pandas as pd

# 1. WEB APP SETUP: Set the title and layout of the webpage
st.set_page_config(page_title="Master Hybrid Quant Dashboard", layout="wide")

st.title("🚀 Master Hybrid Quant Scanner")
st.markdown("This dashboard combines **50-Day Trend Following** with **5-Day Breakout Momentum** to scan for high-probability entries and exits.")

# 2. SIDEBAR NAVIGATION: Allow users to customize their watchlist on the fly
st.sidebar.header("Scan Configuration")
default_tickers = "AAPL, SPY, VOO"
user_input = st.sidebar.text_input("Enter Ticker Symbols (comma separated):", default_tickers)

# Clean up the user input into a proper Python list
watch_list = [ticker.strip().upper() for ticker in user_input.split(",") if ticker.strip()]

# 3. CORE PROCESSING ENGINE
if st.sidebar.button("Run Market Scan"):
    st.subheader("📊 Live Market Analysis")
    
    # Create empty columns for a clean grid layout
    for ticker_symbol in watch_list:
        with st.spinner(f"Analyzing {ticker_symbol}..."):
            stock = yf.Ticker(ticker_symbol)
            history = stock.history(period="60d")
            
            if len(history) < 51:
                st.error(f"Could not fetch enough data for {ticker_symbol}.")
                continue
                
            # Extract data points
            past_data = history.iloc[:-1]
            today = history.iloc[-1]
            current_price = today['Close']
            today_volume = today['Volume']
            
            # Mathematical Calculations
            moving_avg_50 = history['Close'].rolling(window=50).mean().iloc[-1]
            percent_from_avg = ((current_price - moving_avg_50) / moving_avg_50) * 100
            
            recent_5_days = past_data.tail(5)
            resistance_5d = recent_5_days['High'].max()
            avg_volume_50d = past_data.tail(50)['Volume'].mean()
            volume_surge = today_volume / avg_volume_50d
            
            # Create a dedicated visual section for each stock
            st.markdown(f"### {ticker_symbol}")
            col1, col2, col3, col4 = st.columns(4)
            
            # Display clean visual data cards (Metrics)
            col1.metric("Current Price", f"${current_price:.2f}")
            col2.metric("50-Day Moving Avg", f"${moving_avg_50:.2f}")
            col3.metric("Distance from Trend", f"{percent_from_avg:.1f}%")
            col4.metric("Volume Momentum", f"{volume_surge:.1f}x")
            
            # 4. HYBRID RECOMMENDATION ENGINE WITH VISUAL ALERTS
            if percent_from_avg <= -15.0:
                st.error("🚨 **SYSTEMIC RISK / PAUSE:** Severe macro crash detected. Pausing automated entries.")
                
            elif percent_from_avg <= -2.0 and current_price > resistance_5d:
                st.success("🔥 **STRONG BUY:** Asset is in a value pullback and has crossed its 5-day ceiling to confirm a turnaround!")
                
            elif percent_from_avg >= 5.0 and volume_surge < 1.0:
                st.warning("💰 **STRONG SELL:** Price is heavily extended and volume is drying up. The move is exhausted.")
                
            elif percent_from_avg >= 5.0 and volume_surge >= 1.5:
                st.info("🚀 **RIDE THE WAVE:** Price is high, but massive institutional volume is pushing it further. Let profits run.")
                
            else:
                st.info("🟡 **HOLD / NEUTRAL:** Asset is tracking normally within standard trading bands.")
                
            st.markdown("---")
else:
    st.info("👈 Click **'Run Market Scan'** in the sidebar to fetch live data and calculate signals.")