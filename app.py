import streamlit as st
import yfinance as yf
import pandas as pd

# 1. PAGE SETUP
st.set_page_config(page_title="Master S&P 500 Hybrid Scanner", layout="wide")
st.title("🕵️‍♂️ Automated S&P 500 Hybrid Screener")
st.markdown("This system scrapes all components of the S&P 500, processes their trend data, and isolates active tactical entry and exit signals.")

# 2. AUTOMATED DATA PIPELINE: Scrape S&P 500 tickers directly from Wikipedia
@st.cache_data(ttl=86400) # Cache the list for 24 hours so it stays fast
def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        # Clean tickers (replace dots with hyphens for yfinance compatibility, like BRK.B -> BRK-B)
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return tickers
    except Exception as e:
        st.error(f"Error scraping S&P 500 list: {e}")
        return ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "SPY", "VOO"]

# Pull the complete list
all_tickers = get_sp500_tickers()

# 3. SIDEBAR CONFIGURATION
st.sidebar.header("Screener Controls")
st.sidebar.write(f"Total assets loaded in index pool: **{len(all_tickers)}**")

# Let the user choose to scan a smaller subset first or go full scale
scan_mode = st.sidebar.selectbox("Select Scan Range:", ["Top 25 Tech & Large Caps", "Full S&P 500 Index (Takes ~2 mins)"])

if scan_mode == "Top 25 Tech & Large Caps":
    # A pre-curated high-volume list for lightning-fast testing
    scan_pool = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "JPM", 
                 "TSLA", "UNH", "V", "XOM", "MA", "HD", "PG", "COST", "AMD", "CRM", "INTC", "MU", "NFLX", "QCOM", "TXN"]
else:
    scan_pool = all_tickers

# 4. EXECUTION MATRIX
if st.sidebar.button("Launch Market-Wide Scan"):
    st.subheader(f"🔍 Active Signals Found Across Pool")
    
    # Setup empty data lists to build a clean final report table
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for index, ticker_symbol in enumerate(scan_pool):
        # Update visual loading indicators
        progress = (index + 1) / len(scan_pool)
        progress_bar.progress(progress)
        status_text.text(f"Processing {index+1}/{len(scan_pool)}: {ticker_symbol}")
        
        try:
            stock = yf.Ticker(ticker_symbol)
            # Pull 60 days of data
            history = stock.history(period="60d")
            
            if len(history) < 51:
                continue
                
            past_data = history.iloc[:-1]
            today = history.iloc[-1]
            current_price = today['Close']
            today_volume = today['Volume']
            
            # Hybrid Indicator Formulas
            moving_avg_50 = history['Close'].rolling(window=50).mean().iloc[-1]
            percent_from_avg = ((current_price - moving_avg_50) / moving_avg_50) * 100
            
            recent_5_days = past_data.tail(5)
            resistance_5d = recent_5_days['High'].max()
            avg_volume_50d = past_data.tail(50)['Volume'].mean()
            volume_surge = today_volume / avg_volume_50d
            
            # Signal Classification
            signal = "HOLD / NEUTRAL"
            reason = "Tracking within standard bands."
            
            if percent_from_avg <= -15.0:
                signal = "⚠️ RISK CRASH WARNING"
                reason = "Severe drop below historical average trend line."
            elif percent_from_avg <= -2.0 and current_price > resistance_5d:
                signal = "🟢 STRONG BUY"
                reason = "Value pullback territory with confirmed 5-day price breakout breakout turnaround."
            elif percent_from_avg >= 5.0 and volume_surge < 1.0:
                signal = "🔴 STRONG SELL"
                reason = "Overextended price rally matching dying trading volume."
            elif percent_from_avg >= 5.0 and volume_surge >= 1.5:
                signal = "🚀 MOMENTUM RIDE"
                reason = "Overextended trend line backed by deep institutional volume."
                
            # Only record assets that are doing something highly actionable
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
            continue # If yfinance hits a network glitch on a specific stock, skip it silently
            
    # Clean up loaders when done
    progress_bar.empty()
    status_text.empty()
    
    # 5. RENDER LOGGED RESULTS
    if len(results) > 0:
        df_results = pd.DataFrame(results)
        
        # Style the dashboard layout dynamically
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # Quick Summary Cards
        buys_found = len(df_results[df_results['System Signal'] == "🟢 STRONG BUY"])
        sells_found = len(df_results[df_results['System Signal'] == "🔴 STRONG SELL"])
        
        col1, col2 = st.columns(2)
        col1.metric("Total Pullback Turnaround Buys isolated", buys_found)
        col2.metric("Total Exhaustion Sells isolated", sells_found)
    else:
        st.success("Scan complete! No severe anomalies found. Every asset is currently trading safely within standard neutral ranges.")
else:
    st.info("👈 Use the sidebar configuration menu to pick your target search range and click **'Launch Market-Wide Scan'**.")
