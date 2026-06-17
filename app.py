import streamlit as st
import yfinance as yf
import pandas as pd

# 1. PAGE SETUP
st.set_page_config(page_title="Master Hybrid Quant Dashboard", layout="wide")
st.title("🚀 Master Hybrid Quant Platform")

# 2. FAILSAFE DATA INDEX PIPELINE
@st.cache_data(ttl=86400)
def get_sp500_tickers():
    fallback_pool = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "JPM", 
                     "TSLA", "UNH", "V", "XOM", "MA", "HD", "PG", "COST", "AMD", "CRM", "INTC", "MU", "NFLX", "QCOM", "TXN"]
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url, flavor='html5lib')
        df = tables[0]
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return tickers
    except Exception:
        return fallback_pool

all_tickers = get_sp500_tickers()

# 3. SIDEBAR NAVIGATION
st.sidebar.header("Navigation Controls")
app_mode = st.sidebar.radio("Choose App Functionality:", ["Single Asset Lookup", "Automated Market Screener", "🔥 Top 10 Active Leaderboard"])

# --- CORE MATH FUNCTION (Reusable across all parts of the app) ---
def process_hybrid_math(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    history = stock.history(period="60d")
    if len(history) < 51:
        return None
        
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
    
    # Calculate how close the asset is to snapping over its 5-day ceiling (0% means it broke out today)
    distance_to_breakout = ((resistance_5d - current_price) / current_price) * 100
    
    return {
        "Ticker": ticker_symbol,
        "Price": current_price,
        "Dist_50MA": percent_from_avg,
        "Vol_Surge": volume_surge,
        "Dist_5d_Ceiling": distance_to_breakout,
        "5d_Ceiling": resistance_5d
    }

# --- MODE 1: SINGLE ASSET LOOKUP ---
if app_mode == "Single Asset Lookup":
    st.subheader("🔍 Intelligent Asset Lookup")
    user_search = st.text_input("Search Company or Ticker:", "Salesforce").strip()
    
    if st.button("Analyze Asset"):
        with st.spinner("Searching..."):
            ticker_to_analyze = user_search.upper()
            try:
                search_results = yf.Search(user_search, max_results=1).quotes
                if search_results:
                    ticker_to_analyze = search_results[0]['symbol']
            except Exception:
                pass
                
            metrics = process_hybrid_math(ticker_to_analyze)
            if metrics:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Current Price", f"${metrics['Price']:.2f}")
                col2.metric("Distance from 50-MA", f"{metrics['Dist_50MA']:.1f}%")
                col3.metric("5-Day Ceiling", f"${metrics['5d_Ceiling']:.2f}")
                col4.metric("Volume Momentum", f"{metrics['Vol_Surge']:.1f}x")
                
                st.markdown("### System Recommendation")
                if metrics['Dist_50MA'] <= -15.0:
                    st.error("🚨 **SYSTEMIC RISK / PAUSE:** Deep structural crash detected.")
                elif metrics['Dist_50MA'] <= -2.0 and metrics['Dist_5d_Ceiling'] <= 0:
                    st.success("🔥 **STRONG BUY:** Value pullback verified with a live 5-day breakout turnaround!")
                elif metrics['Dist_50MA'] <= -2.0:
                    st.info(f"🟡 **VALUE WATCHLIST:** Asset is cheap ({metrics['Dist_50MA']:.1f}% below trend), but still dropping. Needs to clear ${metrics['5d_Ceiling']:.2f} to trigger buy.")
                elif metrics['Dist_50MA'] >= 5.0 and metrics['Vol_Surge'] < 1.0:
                    st.warning("💰 **STRONG SELL:** Price is extended and volume is dying out.")
                else:
                    st.info("🟡 **HOLD / NEUTRAL:** Trading within normal parameters.")

# --- MODE 2: AUTOMATED MARKET SCREENER ---
elif app_mode == "Automated Market Screener":
    st.subheader("🕵️‍♂️ Automated Signals Scanner")
    scan_pool_selection = st.sidebar.selectbox("Select Scan Range:", ["Top 25 Large Caps", "Full Index Pool"])
    scan_pool = all_tickers if scan_pool_selection == "Full Index Pool" else all_tickers[:25]
    
    if st.button("Launch Market-Wide Scan"):
        results = []
        for ticker in scan_pool:
            try:
                m = process_hybrid_math(ticker)
                if m:
                    signal = "HOLD"
                    if m['Dist_50MA'] <= -15.0: signal = "⚠️ RISK WARNING"
                    elif m['Dist_50MA'] <= -2.0 and m['Dist_5d_Ceiling'] <= 0: signal = "🟢 STRONG BUY"
                    elif m['Dist_50MA'] >= 5.0 and m['Vol_Surge'] < 1.0: signal = "🔴 STRONG SELL"
                    elif m['Dist_50MA'] >= 5.0 and m['Vol_Surge'] >= 1.5: signal = "🚀 MOMENTUM RIDE"
                    
                    if signal != "HOLD":
                        results.append({"Ticker": ticker, "Price": f"${m['Price']:.2f}", "vs 50-MA": f"{m['Dist_50MA']:.1f}%", "Vol Surge": f"{m['Vol_Surge']:.1f}x", "Signal": signal})
            except Exception: continue
        if results: st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
        else: st.success("Scan complete! No anomalies triggered.")

# --- MODE 3: 🔥 TOP 10 ACTIVE LEADERBOARD ---
elif app_mode == "🔥 Top 10 Active Leaderboard":
    st.subheader("🔥 Top 10 Tactical Research Targets")
    st.markdown("This menu ranks companies currently sitting inside our **Value Pullback Zone**, sorted by how close they are to breaking their 5-day resistance ceiling.")
    
    if st.button("Generate Tactical Leaderboard"):
        leaderboard_data = []
        progress_bar = st.progress(0)
        
        # Pull from our core large-cap research pool for processing speed
        search_pool = all_tickers[:35] 
        
        for idx, ticker in enumerate(search_pool):
            progress_bar.progress((idx + 1) / len(search_pool))
            try:
                m = process_hybrid_math(ticker)
                # Filter: Must be trading below its 50-day moving average (Value Zone)
                if m and m['Dist_50MA'] < 0:
                    leaderboard_data.append(m)
            except Exception: continue
            
        progress_bar.empty()
        
        if leaderboard_data:
            df_leader = pd.DataFrame(leaderboard_data)
            
            # SORT LOGIC: Rank by who is closest to breaking out above their 5-day ceiling
            df_leader = df_leader.sort_values(by="Dist_5d_Ceiling", ascending=True).head(10)
            
            # Format the columns for clean user viewing
            report_table = pd.DataFrame({
                "Rank": range(1, len(df_leader) + 1),
                "Ticker": df_leader["Ticker"],
                "Current Price": df_leader["Price"].map("${:.2f}".format),
                "Discount vs 50-MA": df_leader["Dist_50MA"].map("{:.1f}%".format),
                "5-Day Resistance Line": df_leader["5d_Ceiling"].map("${:.2f}".format),
                "Distance to Buy Trigger": df_leader["Dist_5d_Ceiling"].map("{:.2f}%".format),
                "Volume Pace": df_leader["Vol_Surge"].map("{:.1f}x".format)
            })
            
            st.dataframe(report_table, use_container_width=True, hide_index=True)
            st.caption("💡 *Tip: Targets with a 'Distance to Buy Trigger' of 0.00% or less have actively breached their resistance lines today and are flagging strong turnaround entries.*")
        else:
            st.info("No companies are currently trading below their 50-day trends across the core tracking pool.")
