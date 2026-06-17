import streamlit as st
import yfinance as yf
import pandas as pd

# 1. PAGE SETUP
st.set_page_config(page_title="Master Hybrid Quant Dashboard", layout="wide")
st.title("🚀 Master Hybrid Quant Platform")

# 2. FAILSAFE DATA PIPELINE: Scrape S&P 500 or fallback to massive watch list if lxml fails
@st.cache_data(ttl=86400)
def get_sp500_tickers():
    fallback_pool = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "JPM", 
                     "TSLA", "UNH", "V", "XOM", "MA", "HD", "PG", "COST", "AMD", "CRM", "INTC", "MU", "NFLX", "QCOM", "TXN"]
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # We specify html5lib or standard string parsing to avoid lxml dependencies
        tables = pd.read_html(url, flavor='html5lib')
        df = tables[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return tickers
    except Exception:
        # If the server lacks lxml/html5lib, seamlessly drop back to the large pool instead of crashing
        return fallback_pool

all_tickers = get_sp500_tickers()

# 3. SIDEBAR NAVIGATION & DUAL-MODE SELECTION
st.sidebar.header("Navigation Controls")
app_mode = st.sidebar.radio("Choose App Functionality:", ["Single Ticker Lookup", "Automated Market Screener"])

# --- MODE 1: SINGLE TICKER LOOKUP ---
if app_mode == "Single Ticker Lookup":
    st.subheader("🔍 Specific Asset Deep-Dive")
    st.markdown("Type any stock ticker below to analyze its live position relative to our dual-filter logic.")
    
    ticker_input = st.text_input("Enter Ticker Symbol (e.g., CRM, AMD, SPY):", "CRM").strip().upper()
    
    if st.button("Analyze Stock"):
        with st.spinner(f"Fetching live data for {ticker_input}..."):
            try:
                stock = yf.Ticker(ticker_input)
                history = stock.history(period="60d")
                
                if len(history) < 51:
                    st.error(f"Insufficient trading history found for ticker: {ticker_input}")
                else:
                    past_data = history.iloc[:-1]
                    today = history.iloc[-1]
                    current_price = today['Close']
                    today_volume = today['Volume']
                    
                    moving_avg_50 = history['Close'].rolling(window=50).mean().iloc[-1]
                    percent_from_avg = ((current_price - moving_avg_50) / moving_avg_50) * 100
                    
                    recent_5_days = past_data.tail(5)
                    resistance_5d = recent_5_days['High'].max()
                    avg_volume_50d = past_data.tail(50)['Volume'].mean()
                    volume_surge = today_volume / avg_volume_50d
                    
                    # Layout formatting
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Current Price", f"${current_price:.2f}")
                    col2.metric("50-Day Moving Avg", f"${moving_avg_50:.2f}")
                    col3.metric("Distance from Trend", f"{percent_from_avg:.1f}%")
                    col4.metric("Volume Momentum", f"{volume_surge:.1f}x")
                    
                    st.markdown("### System Recommendation")
                    if percent_from_avg <= -15.0:
                        st.error("🚨 **SYSTEMIC RISK / PAUSE:** Severe macro drop detected. Do not buy blindly.")
                    elif percent_from_avg <= -2.0 and current_price > resistance_5d:
                        st.success("🔥 **STRONG BUY:** Asset is in a value pullback and crossed its 5-day ceiling to confirm a turnaround!")
                    elif percent_from_avg >= 5.0 and volume_surge < 1.0:
                        st.warning("💰 **STRONG SELL:** Price is extended and volume is drying up. The move is exhausted.")
                    elif percent_from_avg >= 5.0 and volume_surge >= 1.5:
                        st.info("🚀 **RIDE THE WAVE:** Price is extended but massive institutional volume is backing the move. Hold.")
                    else:
                        st.info("🟡 **HOLD / NEUTRAL:** Asset is tracking normally within its standard structural bands.")
            except Exception as e:
                st.error(f"Error loading ticker {ticker_input}: {e}")

# --- MODE 2: AUTOMATED MARKET SCREENER ---
elif app_mode == "Automated Market Screener":
    st.subheader("🕵️‍♂️ Automated Signals Scanner")
    st.markdown("This mode loops through our index pool and isolates active tactical entry and exit triggers.")
    
    scan_pool_selection = st.sidebar.selectbox("Select Scan Range:", ["Top 25 Large Caps", "Full Index Pool"])
    scan_pool = all_tickers if scan_pool_selection == "Full Index Pool" else all_tickers[:25]
    
    if st.button("Launch Market-Wide Scan"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for index, ticker_symbol in enumerate(scan_pool):
            progress = (index + 1) / len(scan_pool)
            progress_bar.progress(progress)
            status_text.text(f"Scanning {index+1}/{len(scan_pool)}: {ticker_symbol}")
            
            try:
                stock = yf.Ticker(ticker_symbol)
                history = stock.history(period="60d")
                if len(history) < 51:
                    continue
                    
                past_data = history.iloc[:-1]
                today = history.iloc[-1]
                current_price = today['Close']
                today_volume = today['Volume']
                
                moving_avg_50 = history['Close'].rolling(window=50).mean().iloc[-1]
                percent_from_avg = ((current_price - moving_avg_50) / moving_avg_50) * 100
                
                recent_5_days = past_data.tail(5)
                resistance_5d = recent_5_days['High'].max()
                avg_volume_50d = past_data.tail(50)['Volume'].mean()
                volume_surge = today_volume / avg_volume_50d
                
                signal = "HOLD / NEUTRAL"
                reason = "Tracking within standard bands."
                
                if percent_from_avg <= -15.0:
                    signal = "⚠️ RISK CRASH WARNING"
                    reason = "Severe drop below historical average trend line."
                elif percent_from_avg <= -2.0 and current_price > resistance_5d:
                    signal = "🟢 STRONG BUY"
                    reason = "Value pullback with confirmed 5-day breakout turnaround."
                elif percent_from_avg >= 5.0 and volume_surge < 1.0:
                    signal = "🔴 STRONG SELL"
                    reason = "Extended price rally matching dying trading volume."
                elif percent_from_avg >= 5.0 and volume_surge >= 1.5:
                    signal = "🚀 MOMENTUM RIDE"
                    reason = "Extended trend line backed by deep institutional volume."
                    
                if signal != "HOLD / NEUTRAL":
                    results.append({
                        "Ticker": ticker_symbol,
                        "Current Price": f"${current_price:.2f}",
                        "Position vs 50-MA": f"{percent_from_avg:.1f}%",
                        "Volume Surge": f"{volume_surge:.1f}x",
                        "System Signal": signal,
                        "Technical Context": reason
                    })
            except Exception:
                continue
                
        progress_bar.empty()
        status_text.empty()
        
        if len(results) > 0:
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            buys_found = len(df_results[df_results['System Signal'] == "🟢 STRONG BUY"])
            sells_found = len(df_results[df_results['System Signal'] == "🔴 STRONG SELL"])
            
            col1, col2 = st.columns(2)
            col1.metric("Total Pullback Buys Isolated", buys_found)
            col2.metric("Total Exhaustion Sells Isolated", sells_found)
        else:
            st.success("Scan complete! No major anomalies found. Every asset is currently trading within normal limits.")
