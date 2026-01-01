"""
HERMES Quantum Trading Dashboard
================================

Full-featured trading dashboard following UX_REQUIREMENTS_V1.md specifications.

Components:
1. Signals Panel - Agent signals with strength, action, reasoning
2. Stock Ticker Info - Real-time price data
3. Limit Order Recommendations - BUY @ and SELL @ targets
4. Range & Target Analysis - Price ranges and forecasts
5. Prediction Accuracy - Multi-timeframe accuracy metrics
6. Live Charts - Interactive price charts with forecasts

Author: HERMES Project
Date: December 2025
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import HERMES modules
from data_ingestion.market_data import MarketDataFetcher, Interval
from library.technical_analysis import (
    TechnicalAnalyzer, 
    TechnicalAnalysisResult,
    VolumeProfileAnalyzer,
    format_analysis_report
)
from library.order_flow_ml import OrderFlowMLEstimator, WallType

# Try to import run_hermes for agent signals
try:
    from scripts.run_hermes import HermesOrchestrator, TradingDecision
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False

# Try to import IBKR trading module
try:
    from execution.ibkr_trading import IBKRTradingClient
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False

# Try to import trading components
try:
    from core.signal_engine import SignalGenerator, SignalType
    from core.risk_manager import KellyCalculator, RiskManager
    from data_ingestion.data_sources import DataSourceManager
    TRADING_AVAILABLE = True
except ImportError:
    TRADING_AVAILABLE = False

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="HERMES Quantum Trading",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UX styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --buy-color: #00C853;
        --sell-color: #FF1744;
        --hold-color: #FFC107;
        --bg-dark: #1E1E1E;
        --text-light: #E0E0E0;
    }
    
    /* Sidebar - narrower width */
    [data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 220px !important;
    }
    
    /* Hide sidebar fullscreen button */
    [data-testid="stSidebar"] button[title="View fullscreen"] {
        display: none !important;
    }
    
    /* Hide the expand arrow button in sidebar */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* Signal cards */
    .signal-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid;
    }
    
    .signal-buy { border-left-color: #00C853; }
    .signal-sell { border-left-color: #FF1744; }
    .signal-hold { border-left-color: #FFC107; }
    
    /* Price ticker */
    .ticker-container {
        background: #0f0f23;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    
    .price-up { color: #00C853 !important; }
    .price-down { color: #FF1744 !important; }
    
    /* Limit order boxes */
    .limit-order {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 15px;
        margin: 5px 0;
    }
    
    /* Metrics */
    .metric-card {
        background: #1e1e2e;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Hide deploy button */
    .stDeployButton {display: none;}
    
    /* Custom font sizes */
    .big-font { font-size: 24px !important; }
    .medium-font { font-size: 18px !important; }
    .small-font { font-size: 14px !important; }
    
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Crash/Peak Alert Detection
# ============================================================================

def detect_market_alert(quote, ta_result, history_df) -> tuple:
    """
    Detect extreme market conditions for alert banners.
    
    Returns: (alert_type, alert_message, alert_color)
    - alert_type: None, "CRASH", "BOTTOM", "TAKEOFF", "PEAK"
    """
    if quote is None or ta_result is None:
        return None, None, None
    
    price = quote.price if quote else 0
    change_pct = quote.change_percent if quote else 0
    rsi = ta_result.indicators.rsi_14 if ta_result else 50
    
    # Calculate recent volatility
    if history_df is not None and len(history_df) > 5:
        # Handle both uppercase and lowercase column names
        high_col = 'High' if 'High' in history_df.columns else 'high'
        low_col = 'Low' if 'Low' in history_df.columns else 'low'
        recent_high = history_df[high_col].tail(20).max()
        recent_low = history_df[low_col].tail(20).min()
        drop_from_high = ((recent_high - price) / recent_high) * 100
        rise_from_low = ((price - recent_low) / recent_low) * 100
    else:
        drop_from_high = 0
        rise_from_low = 0
    
    # CRASHING: Large single-day drop or significant drop from recent high
    if change_pct <= -8 or (drop_from_high > 20 and change_pct < -3):
        return "CRASH", "🚨 CRASHING!!! | Significant price decline detected", "#FF0000"
    
    # BOTTOM DETECTED: Oversold RSI + recent support test
    if rsi < 25 and change_pct > 0:
        return "BOTTOM", "💰 BOTTOM DETECTED: BUY! BUY! BUY! | Extreme oversold conditions", "#00FF00"
    
    # TAKING OFF: Large single-day gain or breakout
    if change_pct >= 8 or (rise_from_low > 15 and change_pct > 3):
        return "TAKEOFF", "🚀 TAKING OFF!!! | Strong upward momentum detected", "#00C853"
    
    # PEAKING: Overbought RSI + potential reversal
    if rsi > 80 and change_pct < 0:
        return "PEAK", "⚠️ PEAKING: SELL! SELL! SELL! | Extreme overbought conditions", "#FF5722"
    
    return None, None, None


def render_alert_banner(alert_type: str, alert_message: str, alert_color: str):
    """Render an eye-catching alert banner at the top of the page."""
    if alert_type is None:
        return
    
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, {alert_color}22 0%, {alert_color}44 50%, {alert_color}22 100%);
                border: 2px solid {alert_color};
                border-radius: 10px;
                padding: 15px 25px;
                margin-bottom: 20px;
                text-align: center;
                animation: pulse 1s ease-in-out infinite;">
        <span style="color: {alert_color}; font-size: 24px; font-weight: bold;">
            {alert_message}
        </span>
    </div>
    <style>
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)


def check_cross_symbol_alerts(watchlist: list) -> list:
    """
    Check all watchlist symbols for alerts (background check).
    Returns list of (symbol, alert_type, message) tuples.
    """
    alerts = []
    fetcher = MarketDataFetcher()
    
    for symbol in watchlist:
        try:
            quote = fetcher.get_quote(symbol)
            if quote and quote.change_percent:
                if quote.change_percent <= -8:
                    alerts.append((symbol, "CRASH", f"{symbol} down {quote.change_percent:.1f}%"))
                elif quote.change_percent >= 8:
                    alerts.append((symbol, "TAKEOFF", f"{symbol} up +{quote.change_percent:.1f}%"))
        except:
            pass  # Skip symbols that fail to fetch
    
    return alerts


# ============================================================================
# IBKR Trading Panel - Account & Execution
# ============================================================================

def render_trading_panel(symbol: str, current_price: float):
    """
    Render the IBKR trading panel at the top of the dashboard.
    Shows account status, positions, and quick trade buttons.
    """
    # Check if we're connected to IBKR
    ibkr_connected = False
    account_info = None
    positions = []
    open_orders = []
    
    if IBKR_AVAILABLE:
        try:
            # Initialize session state for IBKR client
            if 'ibkr_client' not in st.session_state:
                st.session_state.ibkr_client = None
            
            client = st.session_state.ibkr_client
            if client and client.is_connected():
                ibkr_connected = True
                account_info = client.get_account_summary()
                positions = client.get_positions()
                open_orders = client.get_open_orders()
        except Exception as e:
            pass  # IBKR not connected
    
    # Trading Panel Header
    with st.expander("💹 **IBKR TRADING PANEL**", expanded=True):
        # Connection status row
        status_col, account_col, action_col = st.columns([1, 2, 1])
        
        with status_col:
            if ibkr_connected:
                st.markdown("""
                <div style="background: #00C85322; border: 1px solid #00C853; border-radius: 8px; padding: 10px; text-align: center;">
                    <span style="color: #00C853; font-size: 20px;">🟢 CONNECTED</span><br>
                    <span style="color: #888; font-size: 12px;">IBKR Paper Trading</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #FF174422; border: 1px solid #FF1744; border-radius: 8px; padding: 10px; text-align: center;">
                    <span style="color: #FF1744; font-size: 20px;">🔴 DISCONNECTED</span><br>
                    <span style="color: #888; font-size: 12px;">Start TWS to connect</span>
                </div>
                """, unsafe_allow_html=True)
        
        with account_col:
            if account_info:
                net_liq = account_info.get('NetLiquidation', 0)
                available = account_info.get('AvailableFunds', 0)
                daily_pnl = account_info.get('UnrealizedPnL', 0)
                
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 8px; padding: 15px;">
                    <div style="display: flex; justify-content: space-around;">
                        <div style="text-align: center;">
                            <span style="color: #888; font-size: 11px;">NET LIQUIDATION</span><br>
                            <span style="color: #4488ff; font-size: 20px; font-weight: bold;">${net_liq:,.2f}</span>
                        </div>
                        <div style="text-align: center;">
                            <span style="color: #888; font-size: 11px;">AVAILABLE</span><br>
                            <span style="color: #00C853; font-size: 20px; font-weight: bold;">${available:,.2f}</span>
                        </div>
                        <div style="text-align: center;">
                            <span style="color: #888; font-size: 11px;">DAILY P&L</span><br>
                            <span style="color: {'#00C853' if daily_pnl >= 0 else '#FF1744'}; font-size: 20px; font-weight: bold;">${daily_pnl:+,.2f}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #1a1a2e; border-radius: 8px; padding: 15px; text-align: center;">
                    <span style="color: #888;">Account data unavailable - Connect IBKR TWS</span>
                </div>
                """, unsafe_allow_html=True)
        
        with action_col:
            # Connect/Disconnect button
            if not ibkr_connected:
                if st.button("🔌 Connect IBKR", use_container_width=True):
                    try:
                        if IBKR_AVAILABLE:
                            from execution.ibkr_trading import IBKRTradingClient
                            client = IBKRTradingClient()
                            if client.connect():
                                st.session_state.ibkr_client = client
                                st.success("Connected to IBKR!")
                                st.rerun()
                            else:
                                st.error("Failed to connect. Is TWS running?")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
            else:
                if st.button("🔌 Disconnect", use_container_width=True):
                    if st.session_state.ibkr_client:
                        st.session_state.ibkr_client.disconnect()
                        st.session_state.ibkr_client = None
                        st.rerun()
        
        st.markdown("---")
        
        # Quick Trade Row
        trade_col1, trade_col2, trade_col3, trade_col4 = st.columns([1, 1, 1, 1])
        
        with trade_col1:
            st.markdown(f"**{symbol}** @ ${current_price:.2f}")
        
        with trade_col2:
            shares = st.number_input("Shares", min_value=1, max_value=1000, value=10, key="trade_shares")
        
        with trade_col3:
            if st.button("🟢 BUY", use_container_width=True, type="primary"):
                if ibkr_connected:
                    st.info(f"Would place: BUY {shares} {symbol} @ LIMIT ${current_price:.2f}")
                    # TODO: Execute via IBKR
                else:
                    st.warning("Connect to IBKR first")
        
        with trade_col4:
            if st.button("🔴 SELL", use_container_width=True):
                if ibkr_connected:
                    st.info(f"Would place: SELL {shares} {symbol} @ LIMIT ${current_price:.2f}")
                    # TODO: Execute via IBKR
                else:
                    st.warning("Connect to IBKR first")
        
        # Positions & Orders
        if ibkr_connected and (positions or open_orders):
            pos_col, order_col = st.columns(2)
            
            with pos_col:
                st.markdown("**📊 Positions**")
                if positions:
                    for pos in positions[:5]:
                        pnl_color = "#00C853" if pos.get('unrealizedPnL', 0) >= 0 else "#FF1744"
                        st.markdown(f"""
                        <div style="background: #1a1a2e; border-radius: 5px; padding: 8px; margin: 3px 0;">
                            <span style="color: #fff;">{pos.get('symbol', 'N/A')}</span>
                            <span style="color: #888; margin-left: 10px;">{pos.get('position', 0)} shares</span>
                            <span style="color: {pnl_color}; float: right;">${pos.get('unrealizedPnL', 0):+.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No positions")
            
            with order_col:
                st.markdown("**📝 Open Orders**")
                if open_orders:
                    for order in open_orders[:5]:
                        side_color = "#00C853" if order.get('action') == 'BUY' else "#FF1744"
                        st.markdown(f"""
                        <div style="background: #1a1a2e; border-radius: 5px; padding: 8px; margin: 3px 0;">
                            <span style="color: {side_color};">{order.get('action', 'N/A')}</span>
                            <span style="color: #fff; margin-left: 5px;">{order.get('totalQuantity', 0)} {order.get('symbol', 'N/A')}</span>
                            <span style="color: #888; float: right;">@ ${order.get('lmtPrice', 0):.2f}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("No open orders")


# ============================================================================
# Data Loading Functions
# ============================================================================

# Lookback period mapping: fetch extra data for indicator warmup
LOOKBACK_PERIODS = {
    "1hr": "5d",    # Fetch 5 days for 1-hour view (1-minute bars)
    "1d": "1mo",    # Fetch 1 month for 1-day view (5-minute bars)
    "1w": "3mo",    # Fetch 3 months for 1-week view (hourly bars)
    "1mo": "6mo",   # Fetch 6 months to have 100+ days for SMA50 warmup
    "3mo": "1y",    # Fetch 1 year for 3-month view
    "1y": "2y",     # Fetch 2 years
}

# Display bars for each period
DISPLAY_BARS = {
    "1hr": 60,      # Last 60 trading minutes (1-minute bars)
    "1d": 78,       # ~1 trading day in 5-minute bars (6.5 hours * 12 = 78)
    "1w": 45,       # ~1 week of hourly bars (6.5 hours * 7 days = ~45)
    "1mo": 22,      # ~1 month of trading days
    "3mo": 65,      # ~3 months
    "1y": 252,      # ~1 year
}

# Interval for each period
PERIOD_INTERVALS = {
    "1hr": Interval.MINUTE_1,   # 1-minute bars for 1-hour view
    "1d": Interval.MINUTE_5,    # 5-minute bars for 1-day view
    "1w": Interval.HOUR_1,      # Hourly bars for 1-week view
    "1mo": Interval.DAY_1,
    "3mo": Interval.DAY_1,
    "1y": Interval.DAY_1,
}

# NO CACHING - Live mode fetches fresh data every refresh
def fetch_stock_data(symbol: str, period: str = "6mo"):
    """
    Fetch stock data with extra lookback for indicator warmup.
    
    Fetches extra historical data so that indicators (SMA20, SMA50, etc.)
    are fully calculated from the start of the display window.
    
    For 5d period, uses hourly data. For others, uses daily data.
    
    NO CACHING - Always fetches fresh data for live trading.
    """
    fetcher = MarketDataFetcher()  # Fresh fetcher each time
    
    # Get current quote
    quote = fetcher.get_quote(symbol)
    
    # Fetch extended period for indicator warmup
    fetch_period = LOOKBACK_PERIODS.get(period, "1y")
    interval = PERIOD_INTERVALS.get(period, Interval.DAY_1)
    history = fetcher.get_historical(symbol, period=fetch_period, interval=interval)
    
    # Get company info
    info = fetcher.get_company_info(symbol)
    
    return quote, history, info, period  # Return requested period for display trimming

# NO CACHING - Live mode runs fresh analysis every refresh
def run_technical_analysis(symbol: str, df: pd.DataFrame):
    """Run technical analysis - fresh each time for live trading"""
    analyzer = TechnicalAnalyzer(symbol, df)
    return analyzer.analyze()


# ============================================================================
# Component: Sidebar - Stock Selector
# ============================================================================

def render_sidebar():
    """Render sidebar with stock selection and controls"""
    import pytz
    
    with st.sidebar:
        # Dashboard title and branding
        st.markdown("### 🔮 HERMES")
        st.markdown("**Quantum Trading Dashboard**")
        
        # Live timestamp in NYC time
        nyc_tz = pytz.timezone('America/New_York')
        nyc_time = datetime.now(nyc_tz)
        st.markdown(f"#### ⏱️ `{nyc_time.strftime('%H:%M:%S')}` ET")
        st.caption("Live data - refreshing every 5s")
        
        st.divider()
        
        # Watchlist stocks
        watchlist = ["QBTS", "QUBT", "IONQ", "RGTI"]
        
        st.markdown("**📋 Watchlist**")
        selected_symbol = st.selectbox(
            "Stock",
            watchlist,
            key="symbol_selector",
            label_visibility="collapsed"
        )
        
        # Custom symbol input
        custom_symbol = st.text_input("Custom:", "", label_visibility="collapsed", placeholder="Enter symbol...")
        if custom_symbol:
            selected_symbol = custom_symbol.upper()
        
        st.divider()
        
        # Analysis settings - compact
        st.markdown("**⚙️ Period**")
        
        data_period = st.selectbox(
            "Period",
            ["1hr", "1d", "1w", "1mo", "3mo", "1y"],
            index=3,  # Default to 1mo
            format_func=lambda x: {"1hr": "1 Hour", "1d": "1 Day", "1w": "1 Week", "1mo": "1 Month", "3mo": "3 Months", "1y": "1 Year"}.get(x, x),
            label_visibility="collapsed"
        )
        
        return selected_symbol, data_period, False


# ============================================================================
# Component 1: Signals Panel
# ============================================================================

def render_signals_panel(symbol: str, ta_result: TechnicalAnalysisResult):
    """Render the main signals panel - UX Section 1: Live + Long-term side by side with narratives"""
    st.subheader("📡 Trading Signals")
    
    # Overall signal display
    signal = ta_result.overall_signal
    strength = ta_result.signal_strength
    
    # Color based on signal
    if signal == "BUY":
        signal_color = "#00C853"
        signal_emoji = "🟢"
    elif signal == "SELL":
        signal_color = "#FF1744"
        signal_emoji = "🔴"
    else:
        signal_color = "#FFC107"
        signal_emoji = "🟡"
    
    # Get indicators for analysis
    ind = ta_result.indicators
    
    # Build LIVE narrative based on current conditions
    live_bullets = []
    if ind.rsi_14 > 70:
        live_bullets.append("• RSI indicates overbought - potential pullback ahead")
    elif ind.rsi_14 < 30:
        live_bullets.append("• RSI indicates oversold - potential bounce opportunity")
    else:
        live_bullets.append(f"• RSI at {ind.rsi_14:.1f} - neutral momentum zone")
    
    if ind.macd_histogram > 0:
        live_bullets.append("• MACD histogram positive - bullish momentum")
    else:
        live_bullets.append("• MACD histogram negative - bearish pressure")
    
    if ta_result.patterns:
        top_pattern = ta_result.patterns[0]
        live_bullets.append(f"• {top_pattern.pattern_type.value.replace('_', ' ').title()} pattern detected ({top_pattern.confidence:.0f}% confidence)")
    
    live_narrative = "<br>".join(live_bullets)
    
    # Calculate LONG-TERM signal differently (more weight on trend, less on short-term RSI)
    long_term_signal = signal
    long_term_strength = strength
    long_term_bullets = []
    
    # Adjust for long-term view using trend analysis
    if ind.trend.value == "strong_bullish":
        long_term_signal = "BUY"
        long_term_strength = min(85, strength + 15)  # Different calculation
        long_term_bullets.append("• Strong uptrend established over 3 months")
    elif ind.trend.value == "strong_bearish":
        long_term_signal = "SELL"
        long_term_strength = min(85, strength + 15)
        long_term_bullets.append("• Strong downtrend pressure over 3 months")
    elif ind.trend.value == "bullish":
        long_term_signal = "BUY"
        long_term_strength = min(70, strength + 5)
        long_term_bullets.append("• Moderate uptrend supports accumulation")
    elif ind.trend.value == "bearish":
        long_term_signal = "SELL" 
        long_term_strength = min(70, strength + 5)
        long_term_bullets.append("• Moderate downtrend suggests caution")
    else:
        long_term_strength = max(40, strength - 10)  # Reduce confidence in neutral
        long_term_bullets.append("• Sideways consolidation - wait for breakout")
    
    # Add SMA analysis for long-term
    if ind.sma_50 > 0 and ind.sma_20 > 0:
        if ind.sma_20 > ind.sma_50:
            long_term_bullets.append("• SMA20 above SMA50 - bullish structure")
        else:
            long_term_bullets.append("• SMA20 below SMA50 - bearish structure")
    
    # ADX for trend strength
    if ind.adx > 25:
        long_term_bullets.append(f"• ADX at {ind.adx:.0f} - strong trend in place")
    else:
        long_term_bullets.append(f"• ADX at {ind.adx:.0f} - weak trend, choppy action")
    
    long_term_narrative = "<br>".join(long_term_bullets)
    
    # Long-term color
    if long_term_signal == "BUY":
        lt_color = "#00C853"
        lt_emoji = "🟢"
    elif long_term_signal == "SELL":
        lt_color = "#FF1744"
        lt_emoji = "🔴"
    else:
        lt_color = "#FFC107"
        lt_emoji = "🟡"
    
    # Strength explanation
    strength_desc = "Signal strength measures the confidence level based on indicator alignment, pattern reliability, and trend consistency."
    
    # Two boxes side by side: Live Signal + Long-term Signal (taller for narratives)
    live_col, longterm_col = st.columns(2)
    
    with live_col:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 12px; padding: 20px; border: 2px solid {signal_color};
                    min-height: 280px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #888; font-size: 14px;">⚡ LIVE SIGNAL</span>
                <span style="color: {signal_color}; font-size: 16px; font-weight: bold;">{strength:.0f}% Strength</span>
            </div>
            <h1 style="margin: 10px 0; color: {signal_color}; font-size: 42px;">{signal_emoji} {signal}</h1>
            <div style="color: #ccc; font-size: 13px; line-height: 1.6; margin-top: 10px;">
                {live_narrative}
            </div>
            <p style="color: #666; font-size: 11px; margin-top: 15px; font-style: italic;">{strength_desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with longterm_col:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a2e1a 0%, #162e16 100%); 
                    border-radius: 12px; padding: 20px; border: 2px solid {lt_color};
                    min-height: 280px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #888; font-size: 14px;">📈 3-MONTH OUTLOOK</span>
                <span style="color: {lt_color}; font-size: 16px; font-weight: bold;">{long_term_strength:.0f}% Strength</span>
            </div>
            <h1 style="margin: 10px 0; color: {lt_color}; font-size: 42px;">{lt_emoji} {long_term_signal}</h1>
            <div style="color: #ccc; font-size: 13px; line-height: 1.6; margin-top: 10px;">
                {long_term_narrative}
            </div>
            <p style="color: #666; font-size: 11px; margin-top: 15px; font-style: italic;">{strength_desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Spacer
    st.markdown("")
    
    # Indicator details row with descriptions
    st.markdown("#### 📊 Technical Indicator Details")
    
    pattern_col1, pattern_col2, pattern_col3, pattern_col4 = st.columns(4)
    
    with pattern_col1:
        trend = ind.trend.value.replace("_", " ").title()
        st.metric("Trend", trend, ind.trend_strength.title())
        st.caption("Direction of price movement over the analysis period. Strong trends are more reliable.")
    
    with pattern_col2:
        rsi_status = "Overbought" if ind.rsi_14 > 70 else ("Oversold" if ind.rsi_14 < 30 else "Neutral")
        st.metric("RSI (14)", f"{ind.rsi_14:.1f}", rsi_status)
        st.caption("Relative Strength Index: >70 = overbought (sell signal), <30 = oversold (buy signal).")
    
    with pattern_col3:
        macd_delta = "Bullish ↑" if ind.macd_histogram > 0 else "Bearish ↓"
        st.metric("MACD", f"{ind.macd_histogram:.4f}", macd_delta)
        st.caption("Moving Average Convergence Divergence: Positive = bullish momentum, Negative = bearish.")
    
    with pattern_col4:
        st.metric("ADX Strength", f"{ind.adx:.1f}", ind.trend_strength.title())
        st.caption("Average Directional Index: >25 = strong trend, <20 = weak/ranging market.")


# ============================================================================
# Component 2: Stock Ticker Info
# ============================================================================

def render_fixed_price_banner(symbol: str, quote, info):
    """Render a fixed price banner that stays at top-right corner while scrolling"""
    price = quote.price if quote else 0
    change = quote.change if quote else 0
    change_pct = quote.change_percent if quote else 0
    
    color = "#00C853" if change >= 0 else "#FF5252"
    arrow = "▲" if change >= 0 else "▼"
    
    # Fixed position banner in top-right corner - uses CSS position: fixed
    st.markdown(f"""
    <style>
        .fixed-price-banner {{
            position: fixed;
            top: 60px;
            right: 20px;
            z-index: 9999;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid {color};
            border-radius: 12px;
            padding: 12px 18px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            min-width: 180px;
        }}
    </style>
    <div class="fixed-price-banner">
        <div style="font-size: 14px; color: #888; margin-bottom: 4px;">📈 {symbol}</div>
        <div style="font-size: 28px; font-weight: bold; color: white;">${price:.2f}</div>
        <div style="color: {color}; font-size: 14px;">
            {arrow} {change:+.2f} ({change_pct:+.2f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_ticker_info(symbol: str, quote, info):
    """Render stock ticker information - metrics only (price is in fixed banner)"""
    st.subheader(f"📈 {symbol} - {info.name if info else symbol}")
    
    # Metrics in a single row (price is already in the fixed banner)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Day High",
            value=f"${quote.high:.2f}" if quote else "N/A"
        )
    
    with col2:
        st.metric(
            label="Day Low",
            value=f"${quote.low:.2f}" if quote else "N/A"
        )
    
    with col3:
        st.metric(
            label="Volume",
            value=f"{quote.volume:,.0f}" if quote else "N/A"
        )
    
    with col4:
        market_cap = info.market_cap if info else 0
        if market_cap >= 1e9:
            cap_str = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            cap_str = f"${market_cap/1e6:.2f}M"
        else:
            cap_str = f"${market_cap:,.0f}"
        st.metric(label="Market Cap", value=cap_str)


# ============================================================================
# Component 3: Limit Order Recommendations
# ============================================================================

def render_limit_orders(ta_result: TechnicalAnalysisResult, selected_period: str):
    """Render limit order recommendations - uses sidebar period selector"""
    st.subheader("💰 Limit Order Recommendations")
    
    # Map sidebar period to timeframe key
    period_to_timeframe = {
        "1hr": "1hr",
        "1d": "1day", 
        "1w": "1week",
        "1mo": "1month",
        "3mo": "1month",  # Use 1month recs for longer periods
        "1y": "1month",
    }
    
    tf = period_to_timeframe.get(selected_period, "1day")
    period_label = {"1hr": "1 Hour", "1d": "1 Day", "1w": "1 Week", "1mo": "1 Month", "3mo": "3 Months", "1y": "1 Year"}.get(selected_period, selected_period)
    
    st.caption(f"📊 Recommendations for {period_label} timeframe")
    
    # Get recommendations for this timeframe
    if hasattr(ta_result, 'timeframe_recommendations') and ta_result.timeframe_recommendations:
        tf_recs = ta_result.timeframe_recommendations.get(tf, ([], []))
        buy_recs, sell_recs = tf_recs
    else:
        buy_recs, sell_recs = [], []
    
    col1, col2 = st.columns(2)
    
    # BUY recommendations
    with col1:
        st.markdown("### 🟢 BUY Targets")
        
        if buy_recs:
            for rec in buy_recs[:2]:
                # Ensure positive return for buys
                expected_return = ((rec.target_price - rec.entry_price) / rec.entry_price) * 100
                risk_reward = abs(rec.target_price - rec.entry_price) / max(abs(rec.entry_price - rec.stop_loss), 0.01)
                
                # Build extended description
                desc_lines = [rec.reasoning]
                if "support" in rec.reasoning.lower():
                    desc_lines.append(f"This level has historically acted as a floor where buyers step in.")
                    desc_lines.append(f"Setting a limit order here allows you to catch a potential bounce.")
                elif "bollinger" in rec.reasoning.lower():
                    desc_lines.append(f"Price touching the lower Bollinger band often signals oversold conditions.")
                    desc_lines.append(f"Mean reversion to the middle band is a common follow-through.")
                elif "sma" in rec.reasoning.lower():
                    desc_lines.append(f"Moving averages act as dynamic support/resistance levels.")
                    desc_lines.append(f"Institutional traders often defend these levels.")
                else:
                    desc_lines.append(f"This entry provides favorable risk/reward based on current technicals.")
                
                full_desc = "<br>".join(desc_lines[:4])
                
                st.markdown(f"""
                <div style="background: #1a2e1a; border-radius: 8px; padding: 18px; margin: 8px 0; border-left: 3px solid #00C853; min-height: 200px;">
                    <h4 style="margin:0; color: #00C853;">BUY @ ${rec.entry_price:.2f}</h4>
                    <p style="margin: 8px 0; color: #888;">
                        Target: <strong style="color: #00C853;">${rec.target_price:.2f}</strong> 
                        ({expected_return:+.1f}%)
                    </p>
                    <p style="margin: 8px 0; color: #888;">
                        Stop Loss: ${rec.stop_loss:.2f} | R:R {risk_reward:.1f}x | Prob: {rec.probability:.0f}%
                    </p>
                    <div style="margin: 10px 0; color: #bbb; font-size: 12px; line-height: 1.5;">
                        {full_desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No BUY signals for {period_label}")
    
    # SELL recommendations
    with col2:
        st.markdown("### 🔴 SELL Targets")
        
        if sell_recs:
            for rec in sell_recs[:2]:
                # For sells, profit comes from price going down
                expected_return = ((rec.entry_price - rec.target_price) / rec.entry_price) * 100
                risk_reward = abs(rec.entry_price - rec.target_price) / max(abs(rec.stop_loss - rec.entry_price), 0.01)
                
                # Build extended description
                desc_lines = [rec.reasoning]
                if "resistance" in rec.reasoning.lower():
                    desc_lines.append(f"This level has historically acted as a ceiling where sellers emerge.")
                    desc_lines.append(f"Price often reverses here, making it an ideal take-profit zone.")
                elif "bollinger" in rec.reasoning.lower():
                    desc_lines.append(f"Price touching the upper Bollinger band often signals overbought conditions.")
                    desc_lines.append(f"Mean reversion back to the middle band is a common pattern.")
                elif "sma" in rec.reasoning.lower():
                    desc_lines.append(f"Moving averages often act as resistance on the way up.")
                    desc_lines.append(f"Consider scaling out of positions near these levels.")
                else:
                    desc_lines.append(f"This exit provides favorable risk/reward based on current technicals.")
                
                full_desc = "<br>".join(desc_lines[:4])
                
                st.markdown(f"""
                <div style="background: #2e1a1a; border-radius: 8px; padding: 18px; margin: 8px 0; border-left: 3px solid #FF1744; min-height: 200px;">
                    <h4 style="margin:0; color: #FF1744;">SELL @ ${rec.entry_price:.2f}</h4>
                    <p style="margin: 8px 0; color: #888;">
                        Target: <strong style="color: #FF1744;">${rec.target_price:.2f}</strong> 
                        ({expected_return:+.1f}% profit)
                    </p>
                    <p style="margin: 8px 0; color: #888;">
                        Stop Loss: ${rec.stop_loss:.2f} | R:R {risk_reward:.1f}x | Prob: {rec.probability:.0f}%
                    </p>
                    <div style="margin: 10px 0; color: #bbb; font-height: 1.5;">
                        {full_desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No SELL signals for {period_label}")


# ============================================================================
# Component 4: Range & Target Analysis
# ============================================================================

def render_range_analysis(ta_result: TechnicalAnalysisResult, history):
    """Render range and target analysis - UX Section 4"""
    st.subheader("🎯 Range & Target Analysis")
    
    current_price = ta_result.current_price
    ind = ta_result.indicators
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Current Range")
        
        # Calculate recent range
        if history is not None and len(history) > 0:
            recent = history.tail(20)
            range_high = recent['high'].max()
            range_low = recent['low'].min()
            
            st.metric("20-Day High", f"${range_high:.2f}")
            st.metric("20-Day Low", f"${range_low:.2f}")
            
            # Price position in range
            range_position = (current_price - range_low) / (range_high - range_low) * 100
            st.progress(range_position / 100, text=f"Position: {range_position:.0f}%")
    
    with col2:
        st.markdown("#### 🔮 Bollinger Bands")
        
        st.metric("Upper Band", f"${ind.bollinger_upper:.2f}")
        st.metric("Middle (SMA20)", f"${ind.bollinger_middle:.2f}")
        st.metric("Lower Band", f"${ind.bollinger_lower:.2f}")
    
    with col3:
        st.markdown("#### 📍 Key Levels")
        
        # Support levels
        if ta_result.support_levels:
            for s in ta_result.support_levels[:2]:
                st.markdown(f"**Support:** ${s.price:.2f} ({s.strength:.0f}%)")
        
        # Resistance levels
        if ta_result.resistance_levels:
            for r in ta_result.resistance_levels[:2]:
                st.markdown(f"**Resistance:** ${r.price:.2f} ({r.strength:.0f}%)")


# ============================================================================
# Component 5: Pattern Recognition
# ============================================================================

def render_patterns(ta_result: TechnicalAnalysisResult):
    """Render detected chart patterns - Vertical cards side by side"""
    st.subheader("📈 Chart Patterns")
    
    if ta_result.patterns:
        # Show top 3 patterns in vertical columns
        patterns_to_show = ta_result.patterns[:3]
        cols = st.columns(len(patterns_to_show))
        
        for idx, pattern in enumerate(patterns_to_show):
            # Determine if bullish or bearish
            bullish_patterns = ['ascending_triangle', 'bull_flag', 'double_bottom', 
                               'inverse_head_shoulders', 'bullish_engulfing', 'morning_star',
                               'ascending_trendline', 'stepped_ascent']
            
            is_bullish = pattern.pattern_type.value in bullish_patterns
            color = "#00C853" if is_bullish else "#FF1744"
            emoji = "📈" if is_bullish else "📉"
            
            # Build enhanced details with line breaks (not pipes)
            details_lines = []
            if pattern.trendline_slope is not None:
                slope_dir = "ascending" if pattern.trendline_slope > 0 else "descending"
                details_lines.append(f"Slope: ${pattern.trendline_slope:.4f}/day ({slope_dir})")
            if pattern.trendline_anchor_price is not None and pattern.trendline_anchor_date:
                anchor_date_str = pattern.trendline_anchor_date.strftime('%m/%d/%Y') if hasattr(pattern.trendline_anchor_date, 'strftime') else str(pattern.trendline_anchor_date)[:10]
                details_lines.append(f"Anchor: ${pattern.trendline_anchor_price:.2f} on {anchor_date_str}")
            if pattern.projected_current_level is not None:
                details_lines.append(f"Projected Now: ${pattern.projected_current_level:.2f}")
            if pattern.start_date:
                start_str = pattern.start_date.strftime('%m/%d/%Y') if hasattr(pattern.start_date, 'strftime') else str(pattern.start_date)[:10]
                details_lines.append(f"Started: {start_str}")
            
            extra_details = "<br>".join(details_lines) if details_lines else ""
            
            with cols[idx]:
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 8px; padding: 15px;
                            border-left: 4px solid {color}; min-height: 250px;">
                    <h4 style="margin:0; color: {color};">
                        {emoji} {pattern.pattern_type.value.replace('_', ' ').title()}
                    </h4>
                    <p style="color: #888; margin: 5px 0;">Confidence: {pattern.confidence:.0f}%</p>
                    <p style="color: #aaa; margin: 10px 0; font-size: 13px;">{pattern.description}</p>
                    <div style="color: #888; font-size: 12px; line-height: 1.6; margin: 10px 0;">
                        {extra_details}
                    </div>
                    {f'<p style="color: {color}; font-weight: bold; margin-top: 10px;">Target: ${pattern.target_price:.2f}</p>' if pattern.target_price else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No significant chart patterns detected at this time")


def render_dynamic_trendlines(ta_result: TechnicalAnalysisResult):
    """Render dynamic trendlines - 4-card grid: Live/3-Month x Support/Resistance"""
    if not hasattr(ta_result, 'dynamic_trendlines') or not ta_result.dynamic_trendlines:
        return
    
    st.subheader("📐 Dynamic Trendlines")
    
    support_trendlines = [t for t in ta_result.dynamic_trendlines if t.trendline_type == "support"]
    resistance_trendlines = [t for t in ta_result.dynamic_trendlines if t.trendline_type == "resistance"]
    
    # Sort by recency (most recent anchor date first for "Live", oldest for "3-Month")
    support_trendlines.sort(key=lambda x: x.anchor_date if x.anchor_date else datetime.min, reverse=True)
    resistance_trendlines.sort(key=lambda x: x.anchor_date if x.anchor_date else datetime.min, reverse=True)
    
    # 4-card grid: Live Support | Live Resistance | 3-Month Support | 3-Month Resistance
    st.markdown("#### ⚡ Live Trendlines")
    live_col1, live_col2 = st.columns(2)
    
    with live_col1:
        st.markdown("**🟢 Live Support**")
        if support_trendlines:
            tl = support_trendlines[0]  # Most recent
            status = "✅ INTACT" if tl.is_intact else "⚠️ BROKEN"
            status_color = "#00C853" if tl.is_intact else "#FF9800"
            
            st.markdown(f"""
            <div style="background: #1a2e1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid {status_color}; min-height: 120px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {status_color}; font-weight: bold; font-size: 1.4em;">
                        ${tl.current_level:.2f}
                    </span>
                    <span style="color: #888; font-size: 0.9em;">{status}</span>
                </div>
                <div style="color: #aaa; font-size: 0.85em; margin-top: 8px; line-height: 1.5;">
                    Slope: ${tl.slope:.4f}/day<br>
                    Touches: {tl.touches} | Conf: {tl.confidence:.0f}%<br>
                    Anchor: ${tl.anchor_price:.2f} on {tl.anchor_date.strftime('%b %d') if tl.anchor_date else 'N/A'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No live support trendline")
    
    with live_col2:
        st.markdown("**🔴 Live Resistance**")
        if resistance_trendlines:
            tl = resistance_trendlines[0]  # Most recent
            status = "✅ INTACT" if tl.is_intact else "⚠️ BROKEN"
            status_color = "#FF1744" if tl.is_intact else "#FF9800"
            
            st.markdown(f"""
            <div style="background: #2e1a1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid {status_color}; min-height: 120px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {status_color}; font-weight: bold; font-size: 1.4em;">
                        ${tl.current_level:.2f}
                    </span>
                    <span style="color: #888; font-size: 0.9em;">{status}</span>
                </div>
                <div style="color: #aaa; font-size: 0.85em; margin-top: 8px; line-height: 1.5;">
                    Slope: ${tl.slope:.4f}/day<br>
                    Touches: {tl.touches} | Conf: {tl.confidence:.0f}%<br>
                    Anchor: ${tl.anchor_price:.2f} on {tl.anchor_date.strftime('%b %d') if tl.anchor_date else 'N/A'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No live resistance trendline")
    
    # 3-Month Outlook row
    st.markdown("#### 📈 3-Month Outlook Trendlines")
    outlook_col1, outlook_col2 = st.columns(2)
    
    with outlook_col1:
        st.markdown("**🟢 3-Month Support**")
        if len(support_trendlines) > 1:
            tl = support_trendlines[-1]  # Oldest (longer-term)
            status = "✅ INTACT" if tl.is_intact else "⚠️ BROKEN"
            status_color = "#00C853" if tl.is_intact else "#FF9800"
            
            st.markdown(f"""
            <div style="background: #1a2e1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid {status_color}; min-height: 120px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {status_color}; font-weight: bold; font-size: 1.4em;">
                        ${tl.current_level:.2f}
                    </span>
                    <span style="color: #888; font-size: 0.9em;">{status}</span>
                </div>
                <div style="color: #aaa; font-size: 0.85em; margin-top: 8px; line-height: 1.5;">
                    Slope: ${tl.slope:.4f}/day<br>
                    Touches: {tl.touches} | Conf: {tl.confidence:.0f}%<br>
                    Anchor: ${tl.anchor_price:.2f} on {tl.anchor_date.strftime('%b %d') if tl.anchor_date else 'N/A'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif support_trendlines:
            # Only one support - show it as both
            tl = support_trendlines[0]
            st.markdown(f"""
            <div style="background: #1a2e1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid #00C853; min-height: 120px;">
                <span style="color: #888;">Same as Live Support</span><br>
                <span style="color: #00C853; font-weight: bold; font-size: 1.2em;">${tl.current_level:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No 3-month support trendline")
    
    with outlook_col2:
        st.markdown("**🔴 3-Month Resistance**")
        if len(resistance_trendlines) > 1:
            tl = resistance_trendlines[-1]  # Oldest (longer-term)
            status = "✅ INTACT" if tl.is_intact else "⚠️ BROKEN"
            status_color = "#FF1744" if tl.is_intact else "#FF9800"
            
            st.markdown(f"""
            <div style="background: #2e1a1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid {status_color}; min-height: 120px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: {status_color}; font-weight: bold; font-size: 1.4em;">
                        ${tl.current_level:.2f}
                    </span>
                    <span style="color: #888; font-size: 0.9em;">{status}</span>
                </div>
                <div style="color: #aaa; font-size: 0.85em; margin-top: 8px; line-height: 1.5;">
                    Slope: ${tl.slope:.4f}/day<br>
                    Touches: {tl.touches} | Conf: {tl.confidence:.0f}%<br>
                    Anchor: ${tl.anchor_price:.2f} on {tl.anchor_date.strftime('%b %d') if tl.anchor_date else 'N/A'}
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif resistance_trendlines:
            # Only one resistance - show it as both
            tl = resistance_trendlines[0]
            st.markdown(f"""
            <div style="background: #2e1a1a; border-radius: 8px; padding: 15px; 
                        border-left: 3px solid #FF1744; min-height: 120px;">
                <span style="color: #888;">Same as Live Resistance</span><br>
                <span style="color: #FF1744; font-weight: bold; font-size: 1.2em;">${tl.current_level:.2f}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No 3-month resistance trendline")


# ============================================================================
# Component 6: Prediction Accuracy
# ============================================================================

def render_accuracy_metrics():
    """Render prediction accuracy metrics - UX Section 5"""
    st.subheader("📊 Prediction Accuracy")
    
    # Timeframes as specified in UX requirements
    timeframes = ["1hr", "24hr", "7d", "28d", "6mo", "YTD", "12mo", "All Time"]
    
    # Placeholder accuracy data (would come from PredictionTracker in production)
    # TODO: Connect to actual prediction tracking database
    accuracy_data = {
        "1hr": {"direction": 52, "target": 48, "trades": 156},
        "24hr": {"direction": 58, "target": 51, "trades": 234},
        "7d": {"direction": 62, "target": 55, "trades": 45},
        "28d": {"direction": 65, "target": 58, "trades": 12},
        "6mo": {"direction": 68, "target": 61, "trades": 8},
        "YTD": {"direction": 64, "target": 57, "trades": 24},
        "12mo": {"direction": 67, "target": 59, "trades": 48},
        "All Time": {"direction": 63, "target": 56, "trades": 312},
    }
    
    # Display as tabs
    tabs = st.tabs(timeframes)
    
    for i, tf in enumerate(timeframes):
        with tabs[i]:
            data = accuracy_data.get(tf, {"direction": 50, "target": 50, "trades": 0})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Direction accuracy gauge
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=data["direction"],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Direction Accuracy", 'font': {'size': 14}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#00C853" if data["direction"] >= 55 else "#FFC107"},
                        'steps': [
                            {'range': [0, 50], 'color': "#2a2a2a"},
                            {'range': [50, 100], 'color': "#1a1a2e"}
                        ],
                        'threshold': {
                            'line': {'color': "white", 'width': 2},
                            'thickness': 0.75,
                            'value': 55
                        }
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=50, b=0, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Target hit accuracy gauge
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=data["target"],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Target Hit Rate", 'font': {'size': 14}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#00C853" if data["target"] >= 50 else "#FFC107"},
                        'steps': [
                            {'range': [0, 50], 'color': "#2a2a2a"},
                            {'range': [50, 100], 'color': "#1a1a2e"}
                        ]
                    }
                ))
                fig.update_layout(height=200, margin=dict(t=50, b=0, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                st.metric("Total Predictions", data["trades"])
                st.metric("Profitable", f"{int(data['trades'] * data['direction'] / 100)}")
                st.caption("⚠️ Past performance does not guarantee future results")


# ============================================================================
# Component 7: Live Price Chart
# ============================================================================

def render_price_chart(symbol: str, display_history, full_history, ta_result: TechnicalAnalysisResult, selected_period: str):
    """
    Render interactive price chart - UX Section 6
    
    Args:
        symbol: Stock ticker
        display_history: DataFrame to display (trimmed to user-selected period)
        full_history: Full DataFrame for indicator calculations (includes lookback)
        ta_result: Technical analysis result
        selected_period: Period from sidebar (1hr, 1d, 1w, 1mo, 3mo, 1y)
    """
    st.subheader("📉 Price Chart & Analysis")
    
    if display_history is None or len(display_history) == 0:
        st.warning("No historical data available")
        return
    
    # Chart type selector
    chart_type = st.radio(
        "Chart Type",
        ["Candlestick", "Line", "Area"],
        horizontal=True
    )
    
    # Pre-calculate indicators on FULL history, then slice to display range
    # This ensures indicators are "warmed up" from the start of visible chart
    display_start = display_history.index[0]
    display_end = display_history.index[-1]
    
    # Calculate SMAs on full data
    full_sma20 = full_history['close'].rolling(20).mean()
    full_sma50 = full_history['close'].rolling(50).mean()
    
    # Calculate Bollinger Bands on full data
    bb_middle = full_history['close'].rolling(20).mean()
    bb_std = full_history['close'].rolling(20).std()
    full_bb_upper = bb_middle + 2 * bb_std
    full_bb_lower = bb_middle - 2 * bb_std
    
    # Slice to display range
    sma20 = full_sma20.loc[display_start:display_end]
    sma50 = full_sma50.loc[display_start:display_end]
    bb_upper = full_bb_upper.loc[display_start:display_end]
    bb_lower = full_bb_lower.loc[display_start:display_end]
    
    # Create figure with secondary y-axis for volume
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{symbol} Price', 'Volume'),
        row_heights=[0.7, 0.3]
    )
    
    # Main price chart
    if chart_type == "Candlestick":
        fig.add_trace(
            go.Candlestick(
                x=display_history.index,
                open=display_history['open'],
                high=display_history['high'],
                low=display_history['low'],
                close=display_history['close'],
                name="Price",
                increasing_line_color='#00C853',
                decreasing_line_color='#FF1744'
            ),
            row=1, col=1
        )
    elif chart_type == "Line":
        fig.add_trace(
            go.Scatter(
                x=display_history.index,
                y=display_history['close'],
                mode='lines',
                name='Price',
                line=dict(color='#2196F3', width=2)
            ),
            row=1, col=1
        )
    else:  # Area
        fig.add_trace(
            go.Scatter(
                x=display_history.index,
                y=display_history['close'],
                fill='tozeroy',
                name='Price',
                line=dict(color='#2196F3'),
                fillcolor='rgba(33, 150, 243, 0.3)'
            ),
            row=1, col=1
        )
    
    # Add moving averages (pre-calculated on full data, now complete from day 1)
    ind = ta_result.indicators
    
    if ind.sma_20 > 0 and not sma20.isna().all():
        fig.add_trace(
            go.Scatter(x=sma20.index, y=sma20, name='SMA 20', 
                      line=dict(color='#FFC107', width=1, dash='dot')),
            row=1, col=1
        )
    
    if ind.sma_50 > 0 and not sma50.isna().all():
        fig.add_trace(
            go.Scatter(x=sma50.index, y=sma50, name='SMA 50',
                      line=dict(color='#9C27B0', width=1, dash='dot')),
            row=1, col=1
        )
    
    # Add Bollinger Bands (pre-calculated, now complete from day 1)
    if ind.bollinger_upper > 0 and not bb_upper.isna().all():
        fig.add_trace(
            go.Scatter(x=bb_upper.index, y=bb_upper, name='BB Upper',
                      line=dict(color='rgba(150,150,150,0.3)', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=bb_lower.index, y=bb_lower, name='BB Lower',
                      line=dict(color='rgba(150,150,150,0.3)', width=1),
                      fill='tonexty', fillcolor='rgba(150,150,150,0.1)'),
            row=1, col=1
        )
    
    # Add support/resistance lines
    # For 1hr view, only show S/R within 10% of current price to avoid scale issues
    # For 1d view, only show primary (closest) S/R
    current_price = ta_result.current_price if ta_result.current_price > 0 else display_history['close'].iloc[-1]
    
    if selected_period == "1hr":
        # Filter to S/R within 1% of current price for 1hr view
        nearby_supports = [s for s in ta_result.support_levels 
                          if abs(s.price - current_price) / current_price <= 0.01][:1]
        nearby_resistances = [r for r in ta_result.resistance_levels 
                              if abs(r.price - current_price) / current_price <= 0.01][:1]
    elif selected_period == "1d":
        # Just show primary S/R for 1d
        nearby_supports = ta_result.support_levels[:1]
        nearby_resistances = ta_result.resistance_levels[:1]
    else:
        # Show 2 levels for longer periods
        nearby_supports = ta_result.support_levels[:2]
        nearby_resistances = ta_result.resistance_levels[:2]
    
    for support in nearby_supports:
        fig.add_hline(
            y=support.price,
            line_dash="dash",
            line_color="#00C853",
            annotation_text=f"S: ${support.price:.2f}",
            row=1, col=1
        )
    
    for resistance in nearby_resistances:
        fig.add_hline(
            y=resistance.price,
            line_dash="dash",
            line_color="#FF1744",
            annotation_text=f"R: ${resistance.price:.2f}",
            row=1, col=1
        )
    
    # Volume chart
    colors = ['#00C853' if c >= o else '#FF1744' 
              for c, o in zip(display_history['close'], display_history['open'])]
    
    fig.add_trace(
        go.Bar(
            x=display_history.index,
            y=display_history['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.7
        ),
        row=2, col=1
    )
    
    # Layout
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    # Add rangebreaks to hide non-trading times
    # This removes weekends, and for hourly data, removes non-trading hours
    rangebreaks = [
        dict(bounds=["sat", "mon"]),  # Hide weekends
    ]
    
    # Detect if this is hourly data (5d view)
    time_delta = None
    if len(display_history) >= 2:
        time_delta = display_history.index[1] - display_history.index[0]
        
    # If hourly data, also hide non-trading hours (4pm-9:30am)
    if time_delta is not None and time_delta < pd.Timedelta(days=1):
        rangebreaks.append(dict(bounds=[16, 9.5], pattern="hour"))  # 4pm to 9:30am
    
    # Apply rangebreaks to x-axis
    fig.update_xaxes(rangebreaks=rangebreaks)
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Chart timeframe selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption("📊 Interactive chart - zoom, pan, and hover for details")


# ============================================================================
# Component 8: RSI Chart
# ============================================================================

def render_rsi_chart(display_history, full_history, selected_period: str):
    """
    Render RSI indicator chart - matches the selected period from sidebar
    
    Args:
        display_history: DataFrame to display (trimmed to selected period)
        full_history: Full DataFrame for RSI calculation (includes lookback)
        selected_period: The period selected in sidebar (1hr, 1d, 1w, 1mo, 3mo, 1y)
    """
    if full_history is None or len(full_history) < 14:
        return
    
    period_label = {"1hr": "1 Hour", "1d": "1 Day", "1w": "1 Week", "1mo": "1 Month", "3mo": "3 Months", "1y": "1 Year"}.get(selected_period, selected_period)
    
    st.subheader("📈 RSI Indicator")
    
    # Calculate RSI on full data for warmup
    delta = full_history['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    full_rsi = 100 - (100 / (1 + rs))
    
    # Slice RSI to match display_history date range
    display_start = display_history.index[0]
    display_end = display_history.index[-1]
    rsi_display = full_rsi.loc[display_start:display_end].dropna()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=rsi_display.index,
        y=rsi_display,
        name='RSI',
        line=dict(color='#2196F3', width=2),
        fill='tozeroy',
        fillcolor='rgba(33, 150, 243, 0.1)'
    ))
    
    # Add overbought/oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="#FF1744", 
                 annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="#00C853",
                 annotation_text="Oversold (30)")
    fig.add_hline(y=50, line_dash="dot", line_color="gray")
    
    # Add current RSI annotation
    current_rsi = rsi_display.iloc[-1] if len(rsi_display) > 0 else 50
    rsi_status = "Overbought" if current_rsi > 70 else ("Oversold" if current_rsi < 30 else "Neutral")
    
    # Add rangebreaks based on period
    rangebreaks = [dict(bounds=["sat", "mon"])]  # Hide weekends
    
    # For intraday periods, also hide non-trading hours
    if selected_period in ["1hr", "1d", "1w"]:
        rangebreaks.append(dict(bounds=[16, 9.5], pattern="hour"))
    
    fig.update_layout(
        height=400,  # Taller chart
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=30, b=30, l=50, r=50),
        yaxis=dict(range=[0, 100], title="RSI"),
        xaxis=dict(
            title=f"RSI ({period_label})",
            rangebreaks=rangebreaks
        ),
        annotations=[
            dict(
                x=rsi_display.index[-1] if len(rsi_display) > 0 else None,
                y=current_rsi,
                text=f"Current: {current_rsi:.1f} ({rsi_status})",
                showarrow=True,
                arrowhead=2,
                ax=60,   # Arrow points LEFT (from right side)
                ay=-30,
                xanchor="left"  # Anchor text to left of point (text on right)
            )
        ]
    )
    
    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# Component 9: Volume Profile Heatmap (Order Flow)
# ============================================================================

def render_volume_profile(history_df, current_price: float):
    """
    Render Volume Profile Heatmap - Shows where volume concentrates at price levels.
    
    High Volume Nodes (HVN) act as support/resistance.
    Low Volume Nodes (LVN) are zones where price moves quickly.
    
    Args:
        history_df: Historical OHLCV DataFrame
        current_price: Current stock price
    """
    if history_df is None or len(history_df) < 20:
        return
    
    st.subheader("🔥 Volume Profile Heatmap (Order Flow)")
    st.caption("📊 Volume concentration at price levels (last 60 days) - High Volume Nodes often act as S/R")
    
    # Use only last 60 days for volume profile to focus on recent price action
    # This prevents old low prices from skewing the POC
    recent_df = history_df.tail(60)
    
    # Calculate volume profile on recent data
    analyzer = VolumeProfileAnalyzer(recent_df, num_bins=40)
    profile = analyzer.calculate_profile()
    
    if not profile.price_levels:
        st.info("Insufficient data for volume profile")
        return
    
    # Create two columns: heatmap + key levels
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create horizontal bar chart (volume profile style)
        prices = [n.price for n in profile.price_levels]
        volumes = [n.volume for n in profile.price_levels]
        volume_pcts = [n.volume_pct for n in profile.price_levels]
        deltas = [n.delta for n in profile.price_levels]
        
        # Color by delta (buyers vs sellers)
        colors = []
        for node in profile.price_levels:
            if node.is_high_volume_node:
                if node.delta > 0.1:
                    colors.append('#00C853')  # Green - buyer dominated HVN
                elif node.delta < -0.1:
                    colors.append('#FF1744')  # Red - seller dominated HVN
                else:
                    colors.append('#FFC107')  # Yellow - balanced HVN
            else:
                if node.delta > 0.1:
                    colors.append('rgba(0, 200, 83, 0.4)')  # Light green
                elif node.delta < -0.1:
                    colors.append('rgba(255, 23, 68, 0.4)')  # Light red
                else:
                    colors.append('rgba(100, 100, 100, 0.4)')  # Gray
        
        fig = go.Figure()
        
        # Volume bars (horizontal)
        fig.add_trace(go.Bar(
            y=prices,
            x=volume_pcts,
            orientation='h',
            marker_color=colors,
            name='Volume %',
            hovertemplate='Price: $%{y:.2f}<br>Volume: %{x:.1f}%<extra></extra>'
        ))
        
        # Add current price line
        fig.add_hline(
            y=current_price,
            line_dash="solid",
            line_color="#2196F3",
            line_width=2,
            annotation_text=f"Current: ${current_price:.2f}",
            annotation_position="right"
        )
        
        # Add POC line
        fig.add_hline(
            y=profile.poc,
            line_dash="dash",
            line_color="#E91E63",
            annotation_text=f"POC: ${profile.poc:.2f}",
            annotation_position="left"
        )
        
        # Add Value Area
        fig.add_hrect(
            y0=profile.value_area_low,
            y1=profile.value_area_high,
            fillcolor="rgba(255, 193, 7, 0.1)",
            line_width=0,
            annotation_text="Value Area (70%)",
            annotation_position="top left"
        )
        
        fig.update_layout(
            height=400,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=80, r=20),
            xaxis_title="Volume %",
            yaxis_title="Price ($)",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Key Levels")
        
        # POC - Point of Control
        poc_distance = ((current_price - profile.poc) / profile.poc) * 100
        poc_status = "above" if current_price > profile.poc else "below"
        st.markdown(f"""
        <div style="background: #1a1a2e; padding: 12px; border-radius: 8px; margin: 5px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><span style="color: #E91E63; font-size: 18px;">●</span> <b style="font-size: 16px;">POC</b></span>
                <span style="color: #E91E63; font-size: 18px; font-weight: bold;">${profile.poc:.2f}</span>
            </div>
            <p style="margin: 8px 0 0 0; color: #888; font-size: 12px;">
                Point of Control - highest volume price<br>
                Price is {abs(poc_distance):.1f}% {poc_status} POC
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Value Area
        va_width = profile.value_area_high - profile.value_area_low
        va_width_pct = (va_width / current_price) * 100
        in_va = profile.value_area_low <= current_price <= profile.value_area_high
        st.markdown(f"""
        <div style="background: #1a1a2e; padding: 12px; border-radius: 8px; margin: 5px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><span style="color: #FFC107; font-size: 18px;">●</span> <b style="font-size: 16px;">Value Area</b></span>
                <span style="color: {'#00C853' if in_va else '#888'}; font-size: 12px;">{'✓ Inside' if in_va else 'Outside'}</span>
            </div>
            <p style="margin: 8px 0; color: #ccc;">
                <b>VAH</b>: ${profile.value_area_high:.2f} &nbsp;|&nbsp; <b>VAL</b>: ${profile.value_area_low:.2f}
            </p>
            <p style="margin: 0; color: #888; font-size: 12px;">
                70% of volume traded in ${va_width:.2f} range ({va_width_pct:.1f}% of price)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Order Walls Section - Horizontal cards layout
    st.markdown("### 🏰 Order Walls")
    st.caption("High volume nodes that may act as support/resistance barriers")
    
    # Get estimated walls
    walls = analyzer.estimate_order_walls(threshold_pct=3.0)
    
    # Show walls near current price
    relevant_walls = []
    for wall in walls["buy_walls"] + walls["sell_walls"]:
        distance = abs(wall["price"] - current_price) / current_price * 100
        if distance <= 15:  # Within 15% of current price
            wall["distance"] = distance
            wall["direction"] = "above" if wall["price"] > current_price else "below"
            wall["type"] = "Resistance" if wall["price"] > current_price else "Support"
            relevant_walls.append(wall)
    
    # Sort by proximity
    relevant_walls.sort(key=lambda x: x["distance"])
    
    if relevant_walls:
        # Create horizontal card layout
        wall_cols = st.columns(min(len(relevant_walls[:5]), 5))
        
        for i, wall in enumerate(relevant_walls[:5]):
            with wall_cols[i]:
                color = "#00C853" if wall["direction"] == "below" else "#FF1744"
                arrow = "⬇️ Support" if wall["direction"] == "below" else "⬆️ Resistance"
                distance_pct = wall["distance"]
                vol_pct = wall["volume_pct"]
                strength = wall["strength"]
                
                # Strength indicator
                strength_bars = "▰" * (3 if strength == "STRONG" else (2 if strength == "MODERATE" else 1))
                strength_bars += "▱" * (3 - len(strength_bars))
                
                st.markdown(f"""
                <div style="background: #252538; padding: 12px; border-radius: 8px; border-left: 4px solid {color}; min-height: 150px;">
                    <div style="color: {color}; font-size: 11px; margin-bottom: 5px;">{arrow}</div>
                    <div style="color: #fff; font-size: 20px; font-weight: bold; margin-bottom: 8px;">${wall['price']:.2f}</div>
                    <div style="color: #888; font-size: 11px; margin-bottom: 4px;">
                        📏 {distance_pct:.1f}% away
                    </div>
                    <div style="color: #888; font-size: 11px; margin-bottom: 4px;">
                        📊 {vol_pct:.1f}% volume
                    </div>
                    <div style="color: {color}; font-size: 11px;">
                        {strength_bars} {strength}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No significant walls within 15% of current price")
    
    # Legend
    st.markdown("""
    <div style="display: flex; gap: 20px; margin-top: 10px; font-size: 12px;">
        <span><span style="color: #00C853;">●</span> Buyer Dominated</span>
        <span><span style="color: #FF1744;">●</span> Seller Dominated</span>
        <span><span style="color: #FFC107;">●</span> Balanced (Strong S/R)</span>
        <span><span style="color: #E91E63;">---</span> POC</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Component 10: ML Order Flow Prediction
# ============================================================================

def render_ml_order_flow(history_df, current_price: float, selected_period: str):
    """
    Render ML-based Order Flow Prediction - Estimates where buy/sell walls
    are likely accumulating based on price action patterns.
    
    Args:
        history_df: Historical OHLCV DataFrame
        current_price: Current stock price
        selected_period: Selected period (1hr, 1d, 1w, 1mo, 3mo, 1y)
    """
    if history_df is None or len(history_df) < 20:
        return
    
    # For 1hr view with minute data, this section doesn't work well
    # Skip for very short timeframes
    if selected_period == "1hr":
        st.subheader("🤖 ML Order Flow Prediction")
        st.info("📊 Order flow prediction requires longer timeframes (1 day or more) for meaningful analysis.")
        return
    
    st.subheader("🤖 ML Order Flow Prediction")
    st.caption("🧠 AI-estimated order walls based on price rejection, volume patterns, and historical behavior")
    
    # Adjust lookback based on period
    if selected_period == "1d":
        lookback = min(len(history_df), 60)  # Use available bars for 1d
    else:
        lookback = 90  # Use 90 days for longer periods
    
    recent_df = history_df.tail(lookback)
    
    # Calculate ML predictions with appropriate lookback
    estimator = OrderFlowMLEstimator(recent_df, lookback_days=lookback)
    prediction = estimator.predict_order_flow()
    
    if not prediction.estimated_walls:
        st.info("Insufficient data for order flow prediction")
        return
    
    # Create layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Buy/Sell Pressure gauge
        pressure = prediction.buy_pressure_score
        if pressure > 0:
            pressure_color = "#00C853"
            pressure_label = "BUY PRESSURE"
        elif pressure < 0:
            pressure_color = "#FF1744"
            pressure_label = "SELL PRESSURE"
        else:
            pressure_color = "#FFC107"
            pressure_label = "NEUTRAL"
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pressure,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Order Flow Bias", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [-100, 100]},
                'bar': {'color': pressure_color},
                'steps': [
                    {'range': [-100, -50], 'color': "rgba(255,23,68,0.3)"},
                    {'range': [-50, 0], 'color': "rgba(255,23,68,0.1)"},
                    {'range': [0, 50], 'color': "rgba(0,200,83,0.1)"},
                    {'range': [50, 100], 'color': "rgba(0,200,83,0.3)"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': 0
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(t=50, b=0, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Direction prediction
        direction_icon = "⬆️" if prediction.predicted_direction == "up" else "⬇️" if prediction.predicted_direction == "down" else "➡️"
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; background: #1a1a2e; border-radius: 8px;">
            <h3 style="margin: 0; color: {pressure_color};">{direction_icon} {prediction.predicted_direction.upper()}</h3>
            <small style="color: #888;">Predicted Direction</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Visualize order walls as horizontal bars
        buy_walls = [w for w in prediction.estimated_walls if w.wall_type == WallType.BUY_WALL and w.price < current_price]
        sell_walls = [w for w in prediction.estimated_walls if w.wall_type == WallType.SELL_WALL and w.price > current_price]
        
        # If no sell walls above current price, look for any sell walls nearby
        if not sell_walls:
            # Also include sell walls at or slightly below current price (recent resistance)
            sell_walls = [w for w in prediction.estimated_walls if w.wall_type == WallType.SELL_WALL and w.price >= current_price * 0.95]
        
        # Combine and sort by price
        all_walls = sorted(buy_walls + sell_walls, key=lambda w: w.price)[:15]
        
        if all_walls:
            prices = [w.price for w in all_walls]
            strengths = [w.strength for w in all_walls]
            colors = ['#00C853' if w.wall_type == WallType.BUY_WALL else '#FF1744' for w in all_walls]
            
            fig = go.Figure()
            
            # Add bars
            fig.add_trace(go.Bar(
                y=prices,
                x=strengths,
                orientation='h',
                marker_color=colors,
                text=[f"{w.strength:.0f}% ({w.confidence:.0f}% conf)" for w in all_walls],
                textposition='outside',
                hovertemplate='$%{y:.2f}<br>Strength: %{x:.0f}%<extra></extra>'
            ))
            
            # Add current price line
            fig.add_hline(
                y=current_price,
                line_dash="solid",
                line_color="#2196F3",
                line_width=2,
                annotation_text=f"Current: ${current_price:.2f}"
            )
            
            fig.update_layout(
                title="Estimated Order Walls",
                height=350,
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(t=40, b=20, l=60, r=80),
                xaxis_title="Wall Strength (%)",
                yaxis_title="Price ($)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No significant walls detected near current price")
    
    with col3:
        # Key levels summary
        st.markdown("### 📍 Key Levels")
        
        # Nearest support
        if buy_walls:
            nearest_support = max(buy_walls, key=lambda w: w.price)
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #00C853;">
                <b>🟢 Support</b><br>
                ${nearest_support.price:.2f}<br>
                <small style="color: #888;">Strength: {nearest_support.strength:.0f}%</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Nearest resistance
        if sell_walls:
            nearest_resistance = min(sell_walls, key=lambda w: w.price)
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #FF1744;">
                <b>🔴 Resistance</b><br>
                ${nearest_resistance.price:.2f}<br>
                <small style="color: #888;">Strength: {nearest_resistance.strength:.0f}%</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Supporting signals
        st.markdown("#### 🔍 Signals Used")
        all_signals = set()
        for wall in prediction.estimated_walls[:10]:
            all_signals.update(wall.supporting_signals)
        
        signal_icons = {
            "price_rejection": "📉 Price Rejection",
            "volume_spike": "📊 Volume Spike",
            "round_number": "🔢 Round Number"
        }
        
        for signal in all_signals:
            st.markdown(f"• {signal_icons.get(signal, signal)}")
    
    # Summary
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 15px; border-radius: 8px; margin-top: 15px;">
        <b>📝 Analysis Summary:</b> {prediction.prediction_summary}
    </div>
    """, unsafe_allow_html=True)
    
    # Warning
    st.caption("⚠️ ML predictions are estimates based on historical price action. Actual order book may differ.")


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard entry point"""
    
    # Render sidebar and get selections
    symbol, period, run_analysis = render_sidebar()
    
    # Load data (fetches extended period for indicator warmup)
    with st.spinner(f"Loading data for {symbol}..."):
        try:
            quote, history, info, requested_period = fetch_stock_data(symbol, period)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return
    
    # Convert history to DataFrame if needed
    if history is not None and hasattr(history, 'data'):
        full_history_df = history.data  # HistoricalData has .data attribute
    elif history is not None and hasattr(history, 'df'):
        full_history_df = history.df
    elif history is not None:
        full_history_df = history
    else:
        full_history_df = None
    
    if full_history_df is None or len(full_history_df) == 0:
        st.error("Unable to fetch historical data")
        return
    
    # Calculate indicators on FULL dataset (for warmup)
    with st.spinner("Running technical analysis..."):
        ta_result = run_technical_analysis(symbol, full_history_df)
    
    # Trim to display period (keep full data for TA, but show only requested period)
    display_bars = DISPLAY_BARS.get(requested_period, 130)
    history_df = full_history_df.tail(display_bars)
    
    # For intraday views (1hr, 1d, 1w), filter to market hours only
    if requested_period in ["1hr", "1d", "1w"] and len(history_df) > 0:
        # Filter to market hours only (9:30 AM - 4:00 PM ET)
        if hasattr(history_df.index, 'hour'):
            market_hours = (history_df.index.hour >= 9) & (history_df.index.hour < 16)
            history_df = history_df[market_hours]
    
    # Pre-calculate indicators on full data, then trim for display
    # This ensures indicators are "warmed up" from the start of the visible chart
    
    # =========================================================================
    # Alert Banner (if extreme conditions detected)
    # =========================================================================
    
    # Check current symbol for alerts
    alert_type, alert_msg, alert_color = detect_market_alert(quote, ta_result, full_history_df)
    if alert_type:
        render_alert_banner(alert_type, alert_msg, alert_color)
    
    # Check cross-symbol alerts (for watchlist awareness)
    watchlist = ["QBTS", "QUBT", "IONQ", "RGTI"]
    other_symbols = [s for s in watchlist if s != symbol]
    cross_alerts = check_cross_symbol_alerts(other_symbols)
    
    if cross_alerts:
        for sym, a_type, a_msg in cross_alerts:
            color = "#FF0000" if a_type == "CRASH" else "#00C853"
            st.markdown(f"""
            <div style="background: {color}22; border: 1px solid {color}; 
                        border-radius: 5px; padding: 8px 15px; margin-bottom: 5px;">
                <span style="color: {color};">⚡ {a_msg}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # =========================================================================
    # Dashboard Layout
    # =========================================================================
    
    # IBKR Trading Panel (at the very top)
    current_price = quote.price if quote else ta_result.current_price
    render_trading_panel(symbol, current_price)
    
    st.divider()
    
    # Fixed Price Banner (stays in top-right corner while scrolling)
    render_fixed_price_banner(symbol, quote, info)
    
    # Row 1: Ticker Info (metrics only - price in fixed banner)
    render_ticker_info(symbol, quote, info)
    
    st.divider()
    
    # Row 2: Signals Panel
    render_signals_panel(symbol, ta_result)
    
    st.divider()
    
    # Row 3: Limit Orders (uses sidebar period)
    render_limit_orders(ta_result, requested_period)
    
    st.divider()
    
    # Row 4: Chart Patterns (full width - Range & Target removed as redundant)
    render_patterns(ta_result)
    
    # Row 4b: Dynamic Trendlines (live support/resistance tracking)
    render_dynamic_trendlines(ta_result)
    
    st.divider()
    
    # Row 5: Charts (pass both full_history for calculations and display_history for display)
    render_price_chart(symbol, history_df, full_history_df, ta_result, requested_period)
    render_rsi_chart(history_df, full_history_df, requested_period)
    
    # Row 6: Volume Profile Heatmap (Order Flow)
    render_volume_profile(history_df, ta_result.current_price)
    
    # Row 7: ML Order Flow Prediction
    render_ml_order_flow(history_df, ta_result.current_price, requested_period)
    
    # Footer
    st.divider()
    st.caption("""
    ⚠️ **Disclaimer**: This is an experimental trading analysis tool. 
    Past performance does not guarantee future results. 
    Always do your own research before making investment decisions.
    
    🔮 HERMES Quantum Trading | Built with Streamlit | © 2025
    """)
    
    # Auto-refresh every 5 seconds - happens AFTER page renders
    time.sleep(5)
    st.rerun()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
