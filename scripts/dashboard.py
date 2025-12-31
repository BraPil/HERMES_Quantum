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
    
    /* Custom font sizes */
    .big-font { font-size: 24px !important; }
    .medium-font { font-size: 18px !important; }
    .small-font { font-size: 14px !important; }
    
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Data Loading Functions
# ============================================================================

# Lookback period mapping: fetch extra data for indicator warmup
LOOKBACK_PERIODS = {
    "1mo": "3mo",   # Fetch 3 months to have 50+ days for SMA50
    "3mo": "6mo",   # Fetch 6 months
    "6mo": "1y",    # Fetch 1 year
    "1y": "2y",     # Fetch 2 years
    "3y": "5y",     # Fetch 5 years for 3 year display
}

# Display days for each period
DISPLAY_DAYS = {
    "1mo": 22,      # ~1 month of trading days
    "3mo": 65,      # ~3 months
    "6mo": 130,     # ~6 months
    "1y": 252,      # ~1 year
    "3y": 756,      # ~3 years
}

@st.cache_resource
def get_market_data_fetcher():
    """Get cached market data fetcher"""
    return MarketDataFetcher()

@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_stock_data(symbol: str, period: str = "6mo"):
    """
    Fetch stock data with extra lookback for indicator warmup.
    
    Fetches extra historical data so that indicators (SMA20, SMA50, etc.)
    are fully calculated from the start of the display window.
    """
    fetcher = get_market_data_fetcher()
    
    # Get current quote
    quote = fetcher.get_quote(symbol)
    
    # Fetch extended period for indicator warmup
    fetch_period = LOOKBACK_PERIODS.get(period, "1y")
    history = fetcher.get_historical(symbol, period=fetch_period, interval=Interval.DAY_1)
    
    # Get company info
    info = fetcher.get_company_info(symbol)
    
    return quote, history, info, period  # Return requested period for display trimming

@st.cache_data(ttl=120)  # Cache for 2 minutes  
def run_technical_analysis(symbol: str, df: pd.DataFrame):
    """Run technical analysis with caching"""
    analyzer = TechnicalAnalyzer(symbol, df)
    return analyzer.analyze()


# ============================================================================
# Component: Sidebar - Stock Selector
# ============================================================================

def render_sidebar():
    """Render sidebar with stock selection and controls"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50?text=HERMES", width=150)
        st.title("🔮 HERMES")
        st.caption("Quantum Trading Intelligence")
        
        st.divider()
        
        # Watchlist stocks
        watchlist = ["QBTS", "QUBT", "IONQ", "RGTI"]
        
        st.subheader("📋 Watchlist")
        selected_symbol = st.selectbox(
            "Select Stock",
            watchlist,
            key="symbol_selector"
        )
        
        # Custom symbol input
        custom_symbol = st.text_input("Or enter symbol:", "")
        if custom_symbol:
            selected_symbol = custom_symbol.upper()
        
        st.divider()
        
        # Analysis settings
        st.subheader("⚙️ Settings")
        
        data_period = st.selectbox(
            "Historical Period",
            ["1mo", "3mo", "6mo", "1y", "3y"],
            index=4  # Default to 3 years
        )
        
        auto_refresh = st.checkbox("Auto-refresh (60s)", value=False)
        
        # Run full analysis button
        run_analysis = st.button("🔄 Run Full Analysis", type="primary", use_container_width=True)
        
        st.divider()
        
        # Status
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        return selected_symbol, data_period, auto_refresh, run_analysis


# ============================================================================
# Component 1: Signals Panel
# ============================================================================

def render_signals_panel(symbol: str, ta_result: TechnicalAnalysisResult):
    """Render the main signals panel - UX Section 1"""
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
    
    # Main signal card
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 10px; padding: 20px; border-left: 4px solid {signal_color};">
            <h2 style="margin:0; color: {signal_color};">{signal_emoji} {signal}</h2>
            <p style="color: #888; margin: 10px 0 0 0;">{ta_result.analysis_summary}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric(
            label="Signal Strength",
            value=f"{strength:.0f}%",
            delta=None
        )
    
    with col3:
        # Trend indicator
        trend = ta_result.indicators.trend.value.replace("_", " ").title()
        st.metric(
            label="Trend",
            value=trend,
            delta=ta_result.indicators.trend_strength.title()
        )
    
    # Indicator details in expander
    with st.expander("📊 Indicator Details", expanded=False):
        ind = ta_result.indicators
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # RSI gauge
            rsi_color = "#FF1744" if ind.rsi_14 > 70 else ("#00C853" if ind.rsi_14 < 30 else "#FFC107")
            st.metric("RSI (14)", f"{ind.rsi_14:.1f}", ind.rsi_signal.upper())
            
        with col2:
            # MACD
            macd_delta = "Bullish ↑" if ind.macd_histogram > 0 else "Bearish ↓"
            st.metric("MACD", f"{ind.macd_histogram:.4f}", macd_delta)
            
        with col3:
            # ADX
            st.metric("ADX", f"{ind.adx:.1f}", ind.trend_strength.title())
            
        with col4:
            # Volume
            st.metric("Volume Trend", ind.volume_trend.title())


# ============================================================================
# Component 2: Stock Ticker Info
# ============================================================================

def render_ticker_info(symbol: str, quote, info):
    """Render stock ticker information - UX Section 2"""
    st.subheader(f"📈 {symbol} - {info.name if info else symbol}")
    
    # Price and change
    price = quote.price if quote else 0
    change = quote.change if quote else 0
    change_pct = quote.change_percent if quote else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Current Price",
            value=f"${price:.2f}",
            delta=f"{change:+.2f} ({change_pct:+.2f}%)"
        )
    
    with col2:
        st.metric(
            label="Day High",
            value=f"${quote.high:.2f}" if quote else "N/A"
        )
    
    with col3:
        st.metric(
            label="Day Low",
            value=f"${quote.low:.2f}" if quote else "N/A"
        )
    
    with col4:
        st.metric(
            label="Volume",
            value=f"{quote.volume:,.0f}" if quote else "N/A"
        )
    
    with col5:
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

def render_limit_orders(ta_result: TechnicalAnalysisResult):
    """Render limit order recommendations - UX Section 3 with multi-timeframe targets"""
    st.subheader("💰 Limit Order Recommendations")
    
    # Timeframe tabs
    timeframes = ["1hr", "1day", "1week", "1month"]
    timeframe_labels = {"1hr": "⏱️ 1 Hour", "1day": "📅 1 Day", "1week": "📆 1 Week", "1month": "🗓️ 1 Month"}
    
    tabs = st.tabs([timeframe_labels[tf] for tf in timeframes])
    
    for i, tf in enumerate(timeframes):
        with tabs[i]:
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
                        
                        st.markdown(f"""
                        <div style="background: #1a2e1a; border-radius: 8px; padding: 15px; margin: 5px 0; border-left: 3px solid #00C853;">
                            <h4 style="margin:0; color: #00C853;">BUY @ ${rec.entry_price:.2f}</h4>
                            <p style="margin: 5px 0; color: #888;">
                                Target: <strong style="color: #00C853;">${rec.target_price:.2f}</strong> 
                                ({expected_return:+.1f}%)
                            </p>
                            <p style="margin: 5px 0; color: #888;">
                                Stop Loss: ${rec.stop_loss:.2f} | R:R {risk_reward:.1f}x
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 12px;">
                                Probability: {rec.probability:.0f}%
                            </p>
                            <p style="margin: 5px 0; color: #aaa; font-size: 11px;">
                                {rec.reasoning[:120]}...
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"No BUY signals for {timeframe_labels[tf]}")
            
            # SELL recommendations
            with col2:
                st.markdown("### 🔴 SELL Targets")
                
                if sell_recs:
                    for rec in sell_recs[:2]:
                        # For sells, profit comes from price going down
                        expected_return = ((rec.entry_price - rec.target_price) / rec.entry_price) * 100
                        risk_reward = abs(rec.entry_price - rec.target_price) / max(abs(rec.stop_loss - rec.entry_price), 0.01)
                        
                        st.markdown(f"""
                        <div style="background: #2e1a1a; border-radius: 8px; padding: 15px; margin: 5px 0; border-left: 3px solid #FF1744;">
                            <h4 style="margin:0; color: #FF1744;">SELL @ ${rec.entry_price:.2f}</h4>
                            <p style="margin: 5px 0; color: #888;">
                                Target: <strong style="color: #FF1744;">${rec.target_price:.2f}</strong> 
                                ({expected_return:+.1f}% profit)
                            </p>
                            <p style="margin: 5px 0; color: #888;">
                                Stop Loss: ${rec.stop_loss:.2f} | R:R {risk_reward:.1f}x
                            </p>
                            <p style="margin: 5px 0; color: #666; font-size: 12px;">
                                Probability: {rec.probability:.0f}%
                            </p>
                            <p style="margin: 5px 0; color: #aaa; font-size: 11px;">
                                {rec.reasoning[:120]}...
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(f"No SELL signals for {timeframe_labels[tf]}")
    
    # Also show pattern-based recommendations (from the original analysis)
    if ta_result.buy_recommendations or ta_result.sell_recommendations:
        with st.expander("📈 Pattern-Based Signals", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🟢 Pattern BUY Signals")
                for rec in ta_result.buy_recommendations[:3]:
                    expected_return = ((rec.target_price - rec.entry_price) / rec.entry_price) * 100
                    st.markdown(f"""
                    <div style="background: #1a2e1a; border-radius: 6px; padding: 10px; margin: 3px 0; border-left: 2px solid #00C853;">
                        <b style="color: #00C853;">BUY @ ${rec.entry_price:.2f}</b> → ${rec.target_price:.2f} ({expected_return:+.1f}%)
                        <br><small style="color: #888;">{rec.reasoning[:80]}...</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🔴 Pattern SELL Signals")
                for rec in ta_result.sell_recommendations[:3]:
                    expected_return = ((rec.entry_price - rec.target_price) / rec.entry_price) * 100
                    st.markdown(f"""
                    <div style="background: #2e1a1a; border-radius: 6px; padding: 10px; margin: 3px 0; border-left: 2px solid #FF1744;">
                        <b style="color: #FF1744;">SELL @ ${rec.entry_price:.2f}</b> → ${rec.target_price:.2f} ({expected_return:+.1f}%)
                        <br><small style="color: #888;">{rec.reasoning[:80]}...</small>
                    </div>
                    """, unsafe_allow_html=True)


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
    """Render detected chart patterns - UX Section 4b"""
    st.subheader("📈 Chart Patterns")
    
    if ta_result.patterns:
        cols = st.columns(min(len(ta_result.patterns), 3))
        
        for i, pattern in enumerate(ta_result.patterns[:3]):
            with cols[i % 3]:
                # Determine if bullish or bearish
                bullish_patterns = ['ascending_triangle', 'bull_flag', 'double_bottom', 
                                   'inverse_head_shoulders', 'bullish_engulfing', 'morning_star']
                
                is_bullish = pattern.pattern_type.value in bullish_patterns
                color = "#00C853" if is_bullish else "#FF1744"
                emoji = "📈" if is_bullish else "📉"
                
                st.markdown(f"""
                <div style="background: #1a1a2e; border-radius: 8px; padding: 15px; 
                            border-top: 3px solid {color};">
                    <h4 style="margin:0; color: {color};">
                        {emoji} {pattern.pattern_type.value.replace('_', ' ').title()}
                    </h4>
                    <p style="color: #888; margin: 10px 0;">Confidence: {pattern.confidence:.0f}%</p>
                    <p style="color: #666; font-size: 12px;">{pattern.description}</p>
                    {f'<p style="color: #00C853;">Target: ${pattern.target_price:.2f}</p>' if pattern.target_price else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No significant chart patterns detected at this time")


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

def render_price_chart(symbol: str, display_history, full_history, ta_result: TechnicalAnalysisResult):
    """
    Render interactive price chart - UX Section 6
    
    Args:
        symbol: Stock ticker
        display_history: DataFrame to display (trimmed to user-selected period)
        full_history: Full DataFrame for indicator calculations (includes lookback)
        ta_result: Technical analysis result
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
    for support in ta_result.support_levels[:2]:
        fig.add_hline(
            y=support.price,
            line_dash="dash",
            line_color="#00C853",
            annotation_text=f"S: ${support.price:.2f}",
            row=1, col=1
        )
    
    for resistance in ta_result.resistance_levels[:2]:
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

def render_rsi_chart(display_history, full_history):
    """
    Render RSI indicator chart
    
    Args:
        display_history: DataFrame to display (trimmed period)
        full_history: Full DataFrame for RSI calculation (includes lookback)
    """
    if full_history is None or len(full_history) < 14:
        return
    
    with st.expander("📈 RSI Indicator", expanded=False):
        # Calculate RSI on full data for warmup
        delta = full_history['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        full_rsi = 100 - (100 / (1 + rs))
        
        # Slice to display range
        display_start = display_history.index[0]
        display_end = display_history.index[-1]
        rsi = full_rsi.loc[display_start:display_end]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=rsi.index,
            y=rsi,
            name='RSI',
            line=dict(color='#2196F3', width=2)
        ))
        
        # Add overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="#FF1744", 
                     annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="#00C853",
                     annotation_text="Oversold (30)")
        fig.add_hline(y=50, line_dash="dot", line_color="gray")
        
        fig.update_layout(
            height=250,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=50, r=50),
            yaxis=dict(range=[0, 100])
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
    
    with st.expander("🔥 Volume Profile Heatmap (Order Flow)", expanded=True):
        st.caption("📊 Volume concentration at price levels - High Volume Nodes often act as S/R")
        
        # Calculate volume profile
        analyzer = VolumeProfileAnalyzer(history_df, num_bins=40)
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
            
            # POC
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0;">
                <span style="color: #E91E63;">●</span> <b>POC</b>: ${profile.poc:.2f}
                <br><small style="color: #888;">Point of Control</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Value Area
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0;">
                <span style="color: #FFC107;">●</span> <b>VAH</b>: ${profile.value_area_high:.2f}
                <br><span style="color: #FFC107;">●</span> <b>VAL</b>: ${profile.value_area_low:.2f}
                <br><small style="color: #888;">70% of volume</small>
            </div>
            """, unsafe_allow_html=True)
            
            # High Volume Nodes (potential S/R)
            st.markdown("#### 🏰 Order Walls")
            
            # Get estimated walls
            walls = analyzer.estimate_order_walls(threshold_pct=3.0)
            
            # Show walls near current price
            relevant_walls = []
            for wall in walls["buy_walls"] + walls["sell_walls"]:
                distance = abs(wall["price"] - current_price) / current_price * 100
                if distance <= 15:  # Within 15% of current price
                    wall["distance"] = distance
                    wall["direction"] = "above" if wall["price"] > current_price else "below"
                    relevant_walls.append(wall)
            
            # Sort by proximity
            relevant_walls.sort(key=lambda x: x["distance"])
            
            for wall in relevant_walls[:5]:
                color = "#00C853" if wall["direction"] == "below" else "#FF1744"
                arrow = "⬇️" if wall["direction"] == "below" else "⬆️"
                st.markdown(f"""
                <div style="background: #252538; padding: 8px; border-radius: 5px; margin: 3px 0; border-left: 3px solid {color};">
                    {arrow} <b>${wall['price']:.2f}</b>
                    <br><small style="color: #888;">{wall['volume_pct']:.1f}% vol | {wall['strength']}</small>
                </div>
                """, unsafe_allow_html=True)
            
            if not relevant_walls:
                st.caption("No significant walls within 15% of price")
        
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

def render_ml_order_flow(history_df, current_price: float):
    """
    Render ML-based Order Flow Prediction - Estimates where buy/sell walls
    are likely accumulating based on price action patterns.
    
    Args:
        history_df: Historical OHLCV DataFrame
        current_price: Current stock price
    """
    if history_df is None or len(history_df) < 20:
        return
    
    with st.expander("🤖 ML Order Flow Prediction", expanded=False):
        st.caption("🧠 AI-estimated order walls based on price rejection, volume patterns, and historical behavior")
        
        # Calculate ML predictions
        estimator = OrderFlowMLEstimator(history_df)
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
    symbol, period, auto_refresh, run_analysis = render_sidebar()
    
    # Header
    st.title(f"🔮 HERMES Quantum Trading Dashboard")
    st.caption(f"Real-time analysis for {symbol} | Quantum Computing Stocks")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(0.1)  # Small delay to prevent rapid refreshes
        st.rerun()
    
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
    display_days = DISPLAY_DAYS.get(requested_period, 130)
    history_df = full_history_df.tail(display_days)
    
    # Pre-calculate indicators on full data, then trim for display
    # This ensures indicators are "warmed up" from the start of the visible chart
    
    # =========================================================================
    # Dashboard Layout
    # =========================================================================
    
    # Row 1: Ticker Info
    render_ticker_info(symbol, quote, info)
    
    st.divider()
    
    # Row 2: Signals Panel
    render_signals_panel(symbol, ta_result)
    
    st.divider()
    
    # Row 3: Limit Orders
    render_limit_orders(ta_result)
    
    st.divider()
    
    # Row 4: Range & Patterns
    col1, col2 = st.columns(2)
    
    with col1:
        render_range_analysis(ta_result, history_df)
    
    with col2:
        render_patterns(ta_result)
    
    st.divider()
    
    # Row 5: Charts (pass both full_history for calculations and display_history for display)
    render_price_chart(symbol, history_df, full_history_df, ta_result)
    render_rsi_chart(history_df, full_history_df)
    
    # Row 6: Volume Profile Heatmap (Order Flow)
    render_volume_profile(history_df, ta_result.current_price)
    
    # Row 7: ML Order Flow Prediction
    render_ml_order_flow(history_df, ta_result.current_price)
    
    st.divider()
    
    # Row 8: Prediction Accuracy
    render_accuracy_metrics()
    
    # Footer
    st.divider()
    st.caption("""
    ⚠️ **Disclaimer**: This is an experimental trading analysis tool. 
    Past performance does not guarantee future results. 
    Always do your own research before making investment decisions.
    
    🔮 HERMES Quantum Trading | Built with Streamlit | © 2025
    """)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
