# HERMES_Quantum Work Log - v0.2.0

**Date Range**: December 31, 2025 - January 1, 2026  
**Version**: v0.1.1 → v0.2.0  
**Total Sessions**: 1 extended session with 4 UAT rounds

---

## Session Overview

This work log documents all changes made during the v0.2.0 development cycle. The session focused on intensive user acceptance testing with real-time feedback and iteration.

---

## Chronological Work Log

### 2025-12-31: Initial v0.1.1 Fixes

#### Change 1: Ascending Resistance Trendlines
**Time**: Session start  
**Files Modified**: `library/technical_analysis.py`

**Problem**: Resistance trendlines were detecting descending peaks (highs going DOWN) instead of ascending resistance (higher highs).

**Root Cause**: The detection logic checked for `price2 < price1`, which finds descending patterns rather than ascending.

**Solution**:
```python
# BEFORE (line ~814)
if price2 < price1:
    direction = "descending"

# AFTER
if price2 > price1:
    direction = "ascending"
```

**Additional Changes**:
- Added `ASCENDING_RESISTANCE = "ascending_resistance"` to `PatternType` enum (line 67)
- Updated `get_dynamic_trendlines()` to recognize `ASCENDING_RESISTANCE` as resistance type

---

#### Change 2: Chart Rangebreaks (Non-Trading Hours)
**Time**: After Change 1  
**Files Modified**: `scripts/dashboard.py`

**Problem**: 5-day hourly chart showed all 24 hours including overnight (4pm-9:30am), and all charts showed weekend gaps.

**Solution**: Implemented Plotly rangebreaks:
```python
# In render_price_chart():
rangebreaks = [
    dict(bounds=["sat", "mon"]),  # Hide weekends
]

# Detect hourly/intraday data
if time_delta is not None and time_delta < pd.Timedelta(days=1):
    rangebreaks.append(dict(bounds=[16, 9.5], pattern="hour"))

fig.update_xaxes(rangebreaks=rangebreaks)
```

**Notes**: NYSE holidays are NOT currently filtered - only weekends.

---

#### Change 3: RSI Chart Fixes
**Time**: After Change 2  
**Files Modified**: `scripts/dashboard.py`

**Problems**:
1. First 20 days of RSI were missing (warmup NaN values counted against 90-day display)
2. "Current" annotation appeared on left side instead of right

**Solutions**:
```python
# Problem 1: Drop NaN first, then tail
valid_rsi = full_rsi.dropna()
rsi_90d = valid_rsi.tail(90)

# Problem 2: Move annotation to right side
ax=60,   # Arrow points LEFT (from right side)
xanchor="left"  # Anchor text to left of point (text on right)
```

---

### 2026-01-01: UAT Round 2

#### Change 4: Add 1-Hour and 1-Day Periods
**Time**: UAT Round 2 start  
**Files Modified**: `scripts/dashboard.py`

**Request**: Add 1-hour and 1-day periods, remove 6-month option.

**Implementation**:
```python
LOOKBACK_PERIODS = {
    "1hr": "5d",    # 1-minute bars, 5 days of data
    "1d": "1mo",    # 5-minute bars, 1 month of data
    "1w": "3mo",    # Hourly bars
    "1mo": "6mo",   # Daily bars (increased from 3mo for SMA warmup)
    "3mo": "1y",    # Daily bars
    "1y": "2y"      # Daily bars
}

DISPLAY_BARS = {
    "1hr": 60,   # 1 hour of 1-min bars
    "1d": 78,    # 1 day of 5-min bars (6.5 hours)
    "1w": 45,    # ~1 week of hourly bars
    "1mo": 22,   # 1 month of trading days
    "3mo": 65,   # 3 months of trading days
    "1y": 252    # 1 year of trading days
}

PERIOD_INTERVALS = {
    "1hr": Interval.MINUTE_1,
    "1d": Interval.MINUTE_5,
    "1w": Interval.HOUR_1,
    # Others use Interval.DAY_1
}
```

**Notes**: The `Interval` enum comes from `data_ingestion.market_data`.

---

#### Change 5: SMA 50 Warmup Fix
**Time**: During Round 2  
**Files Modified**: `scripts/dashboard.py`

**Problem**: SMA 50 wasn't showing on 1-month chart because lookback was only 3 months (~65 days), less than 100 days needed for warmup.

**Solution**: Changed `"1mo": "3mo"` to `"1mo": "6mo"` in `LOOKBACK_PERIODS`.

---

#### Change 6: Limit Orders Period Unification
**Time**: During Round 2  
**Files Modified**: `scripts/dashboard.py`

**Problem**: Limit Orders had internal timeframe tabs, but should use sidebar period.

**Solution**: Removed internal tabs, added period mapping:
```python
period_to_timeframe = {
    "1hr": "1hr",
    "1d": "1day",
    "1w": "1week",
    "1mo": "1month",
    "3mo": "3month",
    "1y": "1year"
}
selected_timeframe = period_to_timeframe.get(selected_period, "1day")
```

---

#### Change 7: 5d → 1 Week Renaming
**Time**: During Round 2  
**Files Modified**: `scripts/dashboard.py`

**Problem**: Inconsistent naming - "5d" used in some places, "1 Week" in others.

**Solution**: 
- Renamed key from "5d" to "1w" in all dictionaries
- Added `format_func` to sidebar selectbox for display labels:
```python
PERIOD_LABELS = {
    "1hr": "1 Hour", "1d": "1 Day", "1w": "1 Week",
    "1mo": "1 Month", "3mo": "3 Months", "1y": "1 Year"
}

st.selectbox(..., format_func=lambda x: PERIOD_LABELS.get(x, x))
```

---

#### Change 8: Volume Profile Horizontal Order Walls
**Time**: During Round 2  
**Files Modified**: `scripts/dashboard.py`

**Problem**: Order Walls display not ideal - requested horizontal card layout.

**Solution**: Redesigned using Streamlit columns with colored cards:
```python
# For each wall type (buy/sell)
for wall in walls:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div style="background: {bg_color}; border-left: 3px solid {border_color}; ...">
            <b>${wall.price:.2f}</b> - {wall.strength:.0f}% strength
        </div>
        """, unsafe_allow_html=True)
```

---

### 2026-01-01: UAT Round 3

#### Change 9: Move Branding to Sidebar
**Time**: UAT Round 3 start  
**Files Modified**: `scripts/dashboard.py`

**Request**: Move dashboard title and branding to sidebar.

**Solution**: Added to `render_sidebar()`:
```python
st.sidebar.markdown("# 🔮 HERMES")
st.sidebar.markdown("### Quantum Trading Dashboard")
st.sidebar.markdown("---")
```

---

#### Change 10: NYC Timezone Display
**Time**: During Round 3  
**Files Modified**: `scripts/dashboard.py`

**Request**: Add time display in sidebar using NYC timezone.

**Solution**:
```python
import pytz

# In render_sidebar():
nyc_tz = pytz.timezone('America/New_York')
nyc_time = datetime.now(nyc_tz)
st.sidebar.markdown(f"**🕐 {nyc_time.strftime('%H:%M:%S')} ET**")
```

---

#### Change 11: Sticky Ticker Info (Initial)
**Time**: During Round 3  
**Files Modified**: `scripts/dashboard.py`

**Request**: Create sticky/fixed ticker info that doesn't move while scrolling.

**Initial Solution**: Created sticky header using `position: sticky`:
```css
.sticky-header {
    position: sticky;
    top: 0;
    z-index: 999;
    ...
}
```

**Note**: This was refined in Round 4 to use `position: fixed`.

---

#### Change 12: Remove Secondary S/R for Short Timeframes
**Time**: During Round 3  
**Files Modified**: `scripts/dashboard.py`

**Request**: 1hr/1d views have scale issues with multiple S/R levels.

**Solution**: Added period-aware S/R filtering:
```python
if selected_period == "1hr":
    nearby_supports = ta_result.support_levels[:1]
    nearby_resistances = ta_result.resistance_levels[:1]
elif selected_period == "1d":
    nearby_supports = ta_result.support_levels[:1]
    nearby_resistances = ta_result.resistance_levels[:1]
else:
    # Show 2 levels for longer periods
    nearby_supports = ta_result.support_levels[:2]
    nearby_resistances = ta_result.resistance_levels[:2]
```

---

### 2026-01-01: UAT Round 4

#### Change 13: Fixed Position Price Banner
**Time**: UAT Round 4 start  
**Files Modified**: `scripts/dashboard.py`

**Problem**: Sticky header wasn't truly fixed - needed `position: fixed` in top-right corner.

**Solution**: Created new `render_fixed_price_banner()` function:
```python
def render_fixed_price_banner(symbol: str, quote, info):
    color = "#00C853" if quote.change_percent >= 0 else "#FF1744"
    change_arrow = "▲" if quote.change_percent >= 0 else "▼"
    
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
        }}
    </style>
    <div class="fixed-price-banner">
        <span style="color: #888; font-size: 0.9em;">{symbol}</span><br>
        <span style="color: {color}; font-size: 1.5em; font-weight: bold;">
            ${quote.price:.2f}
        </span>
        <span style="color: {color}; font-size: 0.9em;">
            {change_arrow} {abs(quote.change_percent):.2f}% (${abs(quote.change):.2f})
        </span>
    </div>
    """, unsafe_allow_html=True)
```

**Also**: Simplified `render_ticker_info()` to just show metrics (price moved to fixed banner).

---

#### Change 14: 1% S/R Filter for 1-Hour View
**Time**: During Round 4  
**Files Modified**: `scripts/dashboard.py`

**Problem**: Initial filter was 10%, but should be 1% for 1-hour view (much tighter).

**Solution**:
```python
if selected_period == "1hr":
    # Filter to S/R within 1% of current price for 1hr view
    nearby_supports = [s for s in ta_result.support_levels 
                      if abs(s.price - current_price) / current_price <= 0.01][:1]
    nearby_resistances = [r for r in ta_result.resistance_levels 
                          if abs(r.price - current_price) / current_price <= 0.01][:1]
```

---

#### Change 15: Remove Duplicate Prediction Accuracy Section
**Time**: During Round 4  
**Files Modified**: `scripts/dashboard.py`

**Problem**: "Prediction Accuracy" section appeared duplicated at bottom.

**Root Cause Analysis**: There was only one `render_accuracy_metrics()` call, but the ML Order Flow section also has accuracy gauges which may have looked similar.

**Solution**: Removed the standalone Prediction Accuracy section call from main layout:
```python
# REMOVED:
# Row 8: Prediction Accuracy
# render_accuracy_metrics()
```

---

#### Change 16: ML Order Flow Period Handling
**Time**: During Round 4  
**Files Modified**: `scripts/dashboard.py`

**Problem**: ML Order Flow was broken for 1-hour view with minute data.

**Solution**: Added period parameter and graceful handling:
```python
def render_ml_order_flow(history_df, current_price, selected_period):
    # For 1hr view with minute data, skip analysis
    if selected_period == "1hr":
        st.subheader("🤖 ML Order Flow Prediction")
        st.info("📊 Order flow prediction requires longer timeframes...")
        return
    
    # Adjust lookback based on period
    if selected_period == "1d":
        lookback = min(len(history_df), 60)
    else:
        lookback = 90
```

---

## Bug Fixes Summary

| Bug | Root Cause | Fix | Files |
|-----|------------|-----|-------|
| Descending resistance | Wrong comparison operator | Changed to `price2 > price1` | technical_analysis.py |
| Weekend gaps in charts | No rangebreaks | Added Plotly rangebreaks | dashboard.py |
| Non-trading hours shown | No hour filtering | Added hour rangebreaks | dashboard.py |
| RSI missing first 20 days | Warmup NaN counted | `.dropna()` before `.tail()` | dashboard.py |
| RSI annotation on left | Wrong ax/xanchor | `ax=60, xanchor="left"` | dashboard.py |
| SMA 50 not showing 1mo | Insufficient lookback | Changed to 6mo lookback | dashboard.py |
| S/R cluttering 1hr chart | No period filtering | Added 1% distance filter | dashboard.py |
| ML Order Flow broken 1hr | Minute data incompatible | Early return with info msg | dashboard.py |

---

## Refactoring Decisions

### 1. Period Configuration Centralization
**Decision**: Create top-level dictionaries for all period-related configuration.

**Rationale**: Avoids magic numbers scattered throughout code, makes it easy to add/remove periods.

**Implementation**:
```python
LOOKBACK_PERIODS = {...}
DISPLAY_BARS = {...}
PERIOD_INTERVALS = {...}
PERIOD_LABELS = {...}
```

### 2. Component Parameter Extension
**Decision**: Add `selected_period` parameter to all chart/render functions.

**Rationale**: Each component needs to know the current period for proper filtering and display.

**Affected Functions**:
- `render_price_chart()`
- `render_rsi_chart()`
- `render_ml_order_flow()`
- `render_limit_orders()`

### 3. Fixed vs Sticky Positioning
**Decision**: Use `position: fixed` instead of `position: sticky` for price banner.

**Rationale**: Sticky requires a container context and doesn't work reliably in Streamlit's layout. Fixed positioning with explicit coordinates is more predictable.

---

## Files Modified Summary

| File | Changes | Key Functions Affected |
|------|---------|----------------------|
| `library/technical_analysis.py` | +240/-20 | `_detect_trendlines()`, `PatternType` enum |
| `scripts/dashboard.py` | +1400/-500 | All render functions, main layout |
| `docs/CHECKPOINT_v0.1.1_UX_REFINEMENT.md` | +229 | N/A (new file) |
| `scripts/live_logger.py` | +271 | N/A (new file) |

---

## Testing Notes

### Manual Testing Performed
- ✅ All 6 periods render correctly
- ✅ Intraday charts show trading hours only
- ✅ Weekend gaps removed from all charts
- ✅ Fixed price banner stays visible while scrolling
- ✅ S/R levels properly filtered for each period
- ✅ ML Order Flow shows info message for 1hr
- ✅ Dashboard auto-refreshes every 5 seconds

### Known Issues Not Fixed
- Deprecation warning for `use_container_width` parameter
- NYSE holidays not filtered (only weekends)
- ML Order Flow not adapted for minute data (just disabled)
