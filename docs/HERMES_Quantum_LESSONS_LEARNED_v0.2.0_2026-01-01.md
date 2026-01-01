# HERMES_Quantum Lessons Learned - v0.2.0

**Date**: January 1, 2026  
**Version**: v0.2.0  
**Focus Area**: Dashboard UX, Charting, Intraday Data Handling

---

## Executive Summary

Version 0.2.0 development provided significant insights into Streamlit-based dashboard development, Plotly charting configurations, and the challenges of multi-timeframe financial data visualization. This document captures technical discoveries, patterns that worked well, anti-patterns to avoid, and recommendations for future development.

---

## Technical Discoveries

### 1. Plotly Rangebreaks Are Powerful But Limited

**Discovery**: Plotly's `rangebreaks` feature can hide weekends and non-trading hours from time series charts.

**Syntax**:
```python
rangebreaks = [
    dict(bounds=["sat", "mon"]),  # Hide Saturday through Sunday
    dict(bounds=[16, 9.5], pattern="hour"),  # Hide 4pm to 9:30am
]
fig.update_xaxes(rangebreaks=rangebreaks)
```

**Limitations Discovered**:
- Does NOT handle market holidays (requires manual holiday calendar)
- The hour pattern uses 24-hour format: `16` = 4pm, `9.5` = 9:30am
- Bounds are exclusive on the start, inclusive on the end
- Performance can degrade with many rangebreaks

**Recommendation**: For future work, integrate a market holiday calendar (pandas_market_calendars or similar) to generate complete rangebreaks.

---

### 2. CSS Position: Fixed vs Sticky in Streamlit

**Discovery**: Streamlit's container model makes `position: sticky` unreliable.

**The Problem**:
- `position: sticky` requires a containing element with defined height/overflow
- Streamlit's internal divs don't provide predictable container context
- Sticky elements often don't "stick" as expected

**The Solution**:
```css
.fixed-price-banner {
    position: fixed;  /* NOT sticky */
    top: 60px;
    right: 20px;
    z-index: 9999;  /* High enough to stay on top */
}
```

**Why Fixed Works**:
- Fixed positioning is relative to the viewport, not a container
- Explicit coordinates (top, right) give predictable placement
- High z-index ensures visibility over Streamlit's elements

**Gotcha**: Streamlit has its own header (~56px), so `top: 60px` accounts for this.

---

### 3. Indicator Warmup Period Handling

**Discovery**: Technical indicators (SMA, RSI, etc.) require warmup periods that produce NaN values.

**The Problem**:
- RSI-14 needs 14+ periods before producing valid values
- SMA-50 needs 50 periods
- If you `.tail(90)` directly, you might include warmup NaNs

**Incorrect Approach**:
```python
rsi_values = full_rsi.tail(90)  # May include NaN at the start
```

**Correct Approach**:
```python
valid_rsi = full_rsi.dropna()   # Remove warmup NaNs first
rsi_values = valid_rsi.tail(90)  # Then take the last 90 valid values
```

**Recommendation**: Always `dropna()` before slicing indicator series for display.

---

### 4. Multi-Timeframe Data Resolution

**Discovery**: Different timeframes require different data resolutions for meaningful analysis.

**Optimal Configuration Discovered**:
| Display Period | Data Interval | Lookback Fetch | Display Bars |
|---------------|---------------|----------------|--------------|
| 1 Hour | 1-minute | 5 days | 60 |
| 1 Day | 5-minute | 1 month | 78 |
| 1 Week | 1-hour | 3 months | 45 |
| 1 Month+ | Daily | Extended | Varies |

**Why These Work**:
- 1-hour view: 60 one-minute bars = exactly 1 hour of trading
- 1-day view: 78 five-minute bars = 6.5 hours (trading day)
- 1-week view: ~45 hourly bars = ~7 trading days

**Key Insight**: The lookback period must be LONGER than the display period to provide warmup for indicators.

---

### 5. Trendline Direction Confusion

**Discovery**: "Ascending resistance" and "descending resistance" have opposite meanings that can be confused.

**Clarification**:
- **Ascending Resistance**: Price making HIGHER highs → resistance line slopes UP
- **Descending Resistance**: Price making LOWER highs → resistance line slopes DOWN

**The Bug**: Original code detected descending resistance (lower highs) when ascending was needed.

**Visual Example**:
```
Ascending Resistance:    Descending Resistance:
     /                        \
    /                          \
   /                            \
```

**Recommendation**: Always document the expected price direction explicitly in code comments.

---

### 6. yfinance Interval Availability

**Discovery**: yfinance has restrictions on what intervals are available for what lookback periods.

**Limitations**:
- 1-minute data: max ~7 days
- 5-minute data: max ~60 days
- Hourly data: max ~730 days
- Daily data: decades

**Error Pattern**: If you request too much historical data for a given interval, yfinance returns empty or truncated data.

**Workaround**: Map the lookback to safe values:
```python
LOOKBACK_PERIODS = {
    "1hr": "5d",   # 1-min data safely available for 5 days
    "1d": "1mo",   # 5-min data safely available for 1 month
    ...
}
```

---

### 7. Streamlit Auto-Refresh Implementation

**Discovery**: Streamlit doesn't have built-in auto-refresh, but `time.sleep()` + `st.rerun()` works.

**Implementation**:
```python
# At the END of main(), after all content is rendered:
time.sleep(5)  # Wait 5 seconds
st.rerun()     # Trigger full re-render
```

**Important**: Put this AFTER all content is rendered, or the page will never fully display.

**Gotcha**: The sleep blocks the Python thread - with many users, this could be resource-intensive.

---

## Patterns That Worked Well

### 1. Period Configuration Dictionaries

**Pattern**: Centralize all period-related configuration in top-level dictionaries.

```python
LOOKBACK_PERIODS = {"1hr": "5d", "1d": "1mo", ...}
DISPLAY_BARS = {"1hr": 60, "1d": 78, ...}
PERIOD_INTERVALS = {"1hr": Interval.MINUTE_1, ...}
PERIOD_LABELS = {"1hr": "1 Hour", ...}
```

**Benefits**:
- Single source of truth for period settings
- Easy to add/remove periods
- Clear documentation of intent
- Avoids magic numbers in code

---

### 2. Modular Render Functions

**Pattern**: Each dashboard section has its own `render_*()` function.

```python
def render_sidebar() -> tuple:
def render_fixed_price_banner(symbol, quote, info):
def render_ticker_info(symbol, quote, info):
def render_price_chart(symbol, display_history, full_history, ta_result, period):
def render_rsi_chart(display_history, full_history, period):
...
```

**Benefits**:
- Easy to reorder or disable sections
- Clear responsibility for each component
- Easier debugging (isolate to one function)
- Reusable in future dashboards

---

### 3. Graceful Degradation for Unsupported Timeframes

**Pattern**: When a feature doesn't work for a timeframe, show an informative message instead of crashing.

```python
if selected_period == "1hr":
    st.info("📊 Order flow prediction requires longer timeframes...")
    return
```

**Benefits**:
- Never crashes or shows errors
- User understands why feature is unavailable
- Maintains clean UI

---

### 4. Period Parameter Propagation

**Pattern**: Pass `selected_period` through the render chain so each component can adapt.

```python
# main()
requested_period = render_sidebar()
render_price_chart(..., requested_period)
render_rsi_chart(..., requested_period)
render_ml_order_flow(..., requested_period)
```

**Benefits**:
- Each component can filter/adapt based on period
- Consistent behavior across dashboard
- Easy to add period-specific logic

---

## Anti-Patterns to Avoid

### 1. ❌ Magic Numbers in Display Logic

**Bad**:
```python
if time_delta < pd.Timedelta(hours=1):  # What is this checking?
    # do something
```

**Good**:
```python
INTRADAY_PERIODS = ["1hr", "1d"]
if selected_period in INTRADAY_PERIODS:
    # apply intraday logic
```

---

### 2. ❌ Hardcoding Time Ranges Without Context

**Bad**:
```python
history = yf.download(symbol, period="5d", interval="1m")
```

**Good**:
```python
lookback = LOOKBACK_PERIODS[selected_period]
interval = PERIOD_INTERVALS[selected_period]
history = yf.download(symbol, period=lookback, interval=interval.value)
```

---

### 3. ❌ Displaying Raw Indicator Values With Warmup

**Bad**:
```python
st.line_chart(full_rsi.tail(90))  # May show NaN gaps
```

**Good**:
```python
valid_rsi = full_rsi.dropna()
st.line_chart(valid_rsi.tail(90))
```

---

### 4. ❌ Assuming CSS Works Like Regular Web Pages

**Bad**: Expecting Streamlit to behave like a standard web framework.

**Reality**: Streamlit injects its own CSS, has its own container structure, and doesn't expose full DOM control.

**Approach**: Use `st.markdown()` with `unsafe_allow_html=True` for custom styling, but expect limitations.

---

### 5. ❌ One-Size-Fits-All S/R Display

**Bad**:
```python
# Always show 3 support and 3 resistance levels
for support in ta_result.support_levels[:3]:
    draw_support_line(support)
```

**Good**:
```python
# Adapt based on timeframe
if period == "1hr":
    # Very tight filter - only show nearby levels
    nearby = [s for s in supports if within_1_percent(s.price, current)][:1]
elif period == "1d":
    nearby = supports[:1]  # Primary only
else:
    nearby = supports[:2]  # Show more for zoomed-out views
```

---

## Library/Framework Learnings

### Streamlit

1. **Session State**: Use `st.session_state` for values that need to persist across reruns
2. **Layout Columns**: `st.columns([1, 2, 1])` creates columns with relative widths
3. **Custom CSS**: Always use `unsafe_allow_html=True` for Markdown with HTML/CSS
4. **Sidebar Width**: Can be controlled with CSS: `[data-testid="stSidebar"] { max-width: 220px; }`
5. **Hide Elements**: Use CSS `display: none` to hide Streamlit's built-in elements (deploy button, hamburger menu)

### Plotly

1. **Dark Theme**: Use `template="plotly_dark"` for dark mode charts
2. **Transparent Background**: `paper_bgcolor='rgba(0,0,0,0)'` for transparent
3. **Rangebreaks**: Powerful but requires careful bounds specification
4. **Annotations**: Use `ax`/`ay` for arrow direction, `xanchor`/`yanchor` for text position
5. **Subplots**: Use `make_subplots()` for multi-chart layouts with shared x-axis

### yfinance

1. **Interval Limits**: Different intervals have different maximum lookback periods
2. **Column Names**: Can be uppercase ('Close') or lowercase ('close') depending on version
3. **Real-time Data**: Data may be delayed 15+ minutes for some sources
4. **Error Handling**: Always check if DataFrame is empty before processing

### pytz

1. **Timezone Conversion**: `datetime.now(pytz.timezone('America/New_York'))`
2. **DST Handling**: pytz handles daylight saving time automatically
3. **Display Format**: `.strftime('%H:%M:%S')` for time, add "ET" manually

---

## Architecture Insights

### 1. Two-DataFrame Pattern

**Insight**: Maintain separate DataFrames for calculation vs display.

```python
full_history_df = fetch_extended_data(...)  # For indicator warmup
display_history_df = full_history_df.tail(DISPLAY_BARS[period])  # For display

# Indicators calculated on full_history, displayed on display_history
```

**Why**: Indicators need lookback data, but display should only show the requested period.

---

### 2. Period as First-Class Concept

**Insight**: The selected time period is a core parameter that affects almost everything.

**Affected by Period**:
- Data interval and lookback
- Display bar count
- Rangebreak configuration
- S/R level filtering
- Indicator calculations
- Chart annotations

**Recommendation**: Create a `PeriodConfig` class that encapsulates all period-related settings.

---

### 3. Layered Filtering

**Insight**: Apply filters progressively based on context.

```
Raw S/R Levels (many)
    ↓ Filter by relevance score
Relevant S/R Levels (fewer)
    ↓ Filter by distance from price
Nearby S/R Levels (1-2)
    ↓ Filter by period constraints
Display S/R Levels (0-2)
```

---

## Performance Observations

### 1. Dashboard Render Time
- Initial load: ~3-5 seconds (fetching data)
- Subsequent renders: ~1-2 seconds (data cached)
- Auto-refresh: 5-second cycle works well for active trading

### 2. Memory Usage
- Dashboard stays under 500MB with single ticker
- Multiple tickers would need memory optimization

### 3. API Rate Limits
- yfinance has implicit rate limits
- 5-second refresh seems sustainable for single ticker
- Multiple tickers would need staggered fetching

---

## Debugging Techniques Learned

### 1. Print to Streamlit Console
```python
st.write("DEBUG:", variable)  # Visible in dashboard
print("DEBUG:", variable)     # Visible in terminal
```

### 2. Inspect DataFrame Shape
```python
st.write(f"DataFrame shape: {df.shape}, columns: {df.columns.tolist()}")
```

### 3. Check for NaN
```python
st.write(f"NaN count: {df.isna().sum().sum()}")
```

### 4. Verify Date Ranges
```python
st.write(f"Date range: {df.index.min()} to {df.index.max()}")
```

---

## Recommendations for v0.3.0

### High Priority
1. **Create PeriodConfig class** to centralize period settings
2. **Add NYSE holiday calendar** for complete rangebreak coverage
3. **Implement caching** with `@st.cache_data` for API calls

### Medium Priority
4. **Add error boundaries** around each render function
5. **Create unit tests** for indicator calculations
6. **Document all CSS classes** for maintainability

### Low Priority
7. **Consider TypeScript-based charting** for more control
8. **Evaluate TradingView widget** as alternative to Plotly
9. **Add user preferences persistence** via session state

---

## Conclusion

Version 0.2.0 development provided deep insights into building financial dashboards with Streamlit and Plotly. The key learnings around multi-timeframe handling, CSS positioning in Streamlit, and indicator warmup management will be invaluable for future development. The patterns established (modular renders, period configuration dictionaries, graceful degradation) should be continued and refined in v0.3.0.
