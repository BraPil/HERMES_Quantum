# HERMES_Quantum UX Requirements - Version 1.0

**Created**: 2025-12-30  
**Status**: Reference Document for Future Development  
**Priority**: Post-Agent 01 Implementation

---

## 📊 Dashboard Overview

**Purpose**: Real-time monitoring interface for autonomous trading signals and performance  
**Update Frequency**: 2-4 seconds (near real-time)  
**Target Users**: Active traders, system operators, portfolio managers

---

## 🎯 Core Display Components (Priority Order)

### 1. **Signals Panel** (HIGHEST PRIORITY)

Real-time signal generation and action recommendations.

**Display Fields**:
- **Signal Description**: What triggered the signal (e.g., "Sentiment spike + positive earnings")
- **Signal Strength**: 0-100 scale or categorical (Weak/Moderate/Strong/Very Strong)
- **Recommended Action**: BUY / SELL / HOLD
- **Action Strength**: Confidence level in recommendation (0-100%)
- **Reasoning**: Natural language explanation of decision factors
- **Conviction**: How confident the system is in this recommendation

**Example Display**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIGNAL: Bullish Social Momentum + Policy Catalyst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Signal Strength:    ████████░░  82/100
Recommended Action: BUY
Action Strength:    ████████░░  78%
Conviction:         High

REASONING:
• Social sentiment +47% above 7-day average (Reddit, StockTwits)
• Federal funding announcement for quantum research ($2B)
• Technical: RSI oversold (31), support level confirmed
• Forecast: 5-day prediction shows +12% upside
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 2. **Stock Ticker & Company Info**

**Display Fields**:
- **Ticker Symbol**: Large, prominent (e.g., QBTS, IONQ)
- **Company Name**: Full name below ticker
- **Current Price**: Real-time price with change
- **Market Cap**: For context

**Example**:
```
┌─────────────────────────────────┐
│  QBTS                           │
│  D-Wave Quantum Inc.            │
│  $4.27  ▲ $0.23 (+5.7%)        │
│  Market Cap: $1.2B              │
└─────────────────────────────────┘
```

---

### 3. **Limit Order Recommendations**

Smart entry/exit price targets based on pattern recognition.

#### a. **BUY @ (Entry Targets)**

**Purpose**: Identify exceptional opportunities to buy low  
**Logic**: Support levels, oversold conditions, bullish reversals

**Display Fields**:
- **Target Price**: Specific price to set limit buy order
- **Probability**: Likelihood of hitting this price
- **Expected Wait**: Time estimate to reach target
- **Pattern**: What pattern/signal triggered this
- **Rationale**: Why this is a good entry point

**Example**:
```
BUY @ TARGETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target 1:  $4.15  (92% probability in next 2 days)
Pattern:   Support level + Fibonacci 0.618 retracement
Rationale: Strong historical support, RSI oversold,
           social sentiment bottoming

Target 2:  $4.05  (67% probability in next 5 days)
Pattern:   Gap fill + 50-day moving average
Rationale: Unfilled gap from Dec 15, MA support aligns
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### b. **SELL @ (Exit Targets)**

**Purpose**: Identify exceptional opportunities to sell high  
**Logic**: Resistance levels, overbought conditions, bearish reversals

**Display Fields**:
- **Target Price**: Specific price to set limit sell order
- **Probability**: Likelihood of hitting this price
- **Expected Wait**: Time estimate to reach target
- **Pattern**: What pattern/signal triggered this
- **Rationale**: Why this is a good exit point

**Example**:
```
SELL @ TARGETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target 1:  $4.85  (78% probability in next 3 days)
Pattern:   Resistance level + Bollinger Band upper limit
Rationale: Strong resistance at $4.85, overbought RSI (72),
           profit-taking expected

Target 2:  $5.20  (45% probability in next 10 days)
Pattern:   Psychological resistance ($5) + 200-day MA
Rationale: Round number resistance, long-term MA rejection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 4. **Range & Target Analysis**

**Display Fields**:
- **Current Range**: Day's low-high
- **Expected Range**: Forecasted range for next period
- **Target Price**: Short-term (5-day) and medium-term (30-day)
- **Past Patterns**: Recently completed patterns
- **Current Patterns**: Patterns in formation
- **Emerging Patterns**: Early indicators of new patterns

**Example**:
```
RANGE & PATTERN ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Range:     $4.05 - $4.32  (Today)
Expected Range:    $4.10 - $4.50  (Next 3 days)

Short-Term Target: $4.65  (5-day forecast, 72% confidence)
Medium-Term Target: $5.20  (30-day forecast, 58% confidence)

PAST PATTERNS (Completed):
  ✓ Ascending Triangle (Dec 20-27) → Breakout confirmed
  ✓ Cup & Handle (Dec 10-25) → +18% realized

CURRENT PATTERNS (In Formation):
  ◆ Bull Flag (forming since Dec 28, 67% complete)
  ◆ Golden Cross approaching (50/200 MA convergence)

EMERGING PATTERNS (Early Indicators):
  • Volume spike pattern forming (2 days)
  • Potential double bottom at $4.05
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 5. **Prediction Accuracy Metrics**

Real-time performance tracking across multiple timeframes.

**Display Fields** (all with visual progress bars):
- **Last Hour**: Immediate accuracy
- **Last 24 Hours**: Daily performance
- **Last 7 Days**: Weekly trend
- **Last 28 Days**: Monthly performance
- **Last 6 Months**: Long-term trend
- **Year to Date**: Annual performance
- **Last 12 Months**: Rolling annual
- **All Time**: Historical since inception

**Metrics Tracked**:
- **Direction Accuracy**: % of correct up/down predictions
- **Price Accuracy**: MAPE (Mean Absolute Percentage Error)
- **Signal Win Rate**: % of profitable signals
- **Sharpe Ratio**: Risk-adjusted returns

**Example**:
```
PREDICTION ACCURACY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timeframe       Direction    Price (MAPE)   Signal Win Rate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Last Hour       ████████░░ 82%    2.3%      N/A (too short)
Last 24 Hours   ███████░░░ 74%    3.8%      ████████░░ 80% (4/5)
Last 7 Days     ████████░░ 78%    4.2%      ████████░░ 83% (10/12)
Last 28 Days    ███████░░░ 71%    5.1%      ███████░░░ 76% (19/25)
Last 6 Months   ██████░░░░ 68%    6.4%      ███████░░░ 72% (58/81)
Year to Date    ███████░░░ 69%    6.2%      ███████░░░ 71% (142/200)
Last 12 Months  ██████░░░░ 67%    6.8%      ██████░░░░ 69% (165/240)
All Time        ██████░░░░ 66%    7.1%      ██████░░░░ 68% (203/300)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Trend: ▲ Improving  |  Last Updated: 2025-12-30 14:32:18
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 6. **Live Price Charts with Forecasts** (FUTURE)

**Purpose**: Visual representation of historical performance + predictions  
**Priority**: End of development (nice-to-have)  
**Update Frequency**: 2-4 seconds

**Chart Components**:
- **Historical Price**: Candlestick or line chart
- **Forecast Lines**: Multiple timeframes with confidence intervals
  - 1-minute projection (very short-term)
  - 30-minute projection (intraday)
  - 2-hour projection (session trend)
  - End of day projection (daily close target)
- **Confidence Intervals**: Shaded bands showing uncertainty
- **Support/Resistance**: Key levels overlaid
- **Indicator Overlays**: Volume, RSI, MACD, etc.

**Focus Tickers**:
- QBTS (primary)
- IONQ (primary)
- RGTI (secondary)
- QUBT (secondary)

**Example Visualization**:
```
┌────────────────────────────────────────────────────────────┐
│ QBTS - Live Performance + Forecasts                       │
├────────────────────────────────────────────────────────────┤
│  $5.00 ┤                                  ╱━━━━ EOD Forecast
│        │                              ╱━━━  ($4.85 ±$0.15)
│  $4.75 ┤                          ╱━━━
│        │                      ╱━━━  ← 2hr Forecast
│  $4.50 ┤                  ╱━━━
│        │ Confidence  ╱━━━  ← 30min Forecast
│  $4.25 ┤  Band   ╱━━━ ← 1min Forecast
│        │      ▓▓▓ ← Current Price: $4.27
│  $4.00 ┤   ▓▓▓
│        │ ▓▓
│  $3.75 ┼────────────────────────────────────────────────────
│          9:30  10:30  11:30  12:30  13:30  14:30  16:00
│
│  Volume: ████░░░░ (Above Average +23%)
│  RSI:    ████████░░ 72 (Approaching Overbought)
└────────────────────────────────────────────────────────────┘
```

---

## 🎨 UI/UX Design Principles

### Layout Strategy

**Multi-Panel Dashboard**:
```
┌──────────────────────────────────────────────────────────────┐
│  HERMES_Quantum - Live Trading Dashboard    [Last Update: 2s]│
├─────────────────────────┬────────────────────────────────────┤
│  SIGNALS (Priority 1)   │  STOCK INFO (Priority 2)           │
│  [Large panel - 40%]    │  [Medium panel - 20%]              │
│                         │                                    │
│  • Signal strength      │  QBTS: $4.27 ▲5.7%                │
│  • Recommended action   │  IONQ: $8.15 ▼2.3%                │
│  • Reasoning            │                                    │
│  • Conviction           ├────────────────────────────────────┤
│                         │  BUY @ TARGETS (Priority 3a)       │
│                         │  [Medium panel - 20%]              │
│                         │                                    │
│                         │  $4.15 (92% prob)                  │
├─────────────────────────┤  $4.05 (67% prob)                  │
│  SELL @ TARGETS (3b)    │                                    │
│  [Medium panel - 20%]   ├────────────────────────────────────┤
│                         │  PATTERNS & RANGE (Priority 4)     │
│  $4.85 (78% prob)       │  [Medium panel - 20%]              │
│  $5.20 (45% prob)       │                                    │
│                         │  Range: $4.05-$4.32                │
├─────────────────────────┴────────────────────────────────────┤
│  PREDICTION ACCURACY (Priority 5)                            │
│  [Full width panel - 15%]                                    │
│                                                              │
│  1h: 82% | 24h: 74% | 7d: 78% | 28d: 71% | YTD: 69% ...    │
├──────────────────────────────────────────────────────────────┤
│  LIVE CHARTS (Priority 6 - Future)                          │
│  [Optional full width panel]                                │
│                                                              │
│  [Price chart with forecast lines and confidence intervals] │
└──────────────────────────────────────────────────────────────┘
```

### Design Guidelines

**Visual Hierarchy**:
1. Color coding for signal strength (green=bullish, red=bearish, yellow=neutral)
2. Progress bars for percentages and confidence levels
3. Bold typography for critical information (prices, actions)
4. Consistent spacing and alignment

**Accessibility**:
- High contrast mode available
- Colorblind-friendly palette
- Screen reader compatible
- Keyboard navigation

**Responsiveness**:
- Adaptive layout for different screen sizes
- Mobile-friendly (stacked panels)
- Desktop-optimized (multi-column)

**Real-Time Updates**:
- WebSocket connection for live data
- Visual flash on update (subtle highlight)
- Timestamp on every update
- Connection status indicator

---

## 🔧 Technical Implementation Notes

### Data Flow

```
Data Sources → Agent Processing → Agent 01 Orchestrator
                                        ↓
                              Decision Engine
                                        ↓
                        Dashboard WebSocket Server
                                        ↓
                              Frontend UI
```

### Technology Stack Recommendations

**Backend**:
- FastAPI for REST endpoints
- WebSocket for real-time push
- Redis for caching
- PostgreSQL for signal history

**Frontend**:
- React or Vue.js for UI
- D3.js or Chart.js for visualizations
- TailwindCSS for styling
- Socket.io for WebSocket client

**Deployment**:
- Docker containers
- NGINX reverse proxy
- SSL/TLS encryption
- Rate limiting

---

## 📈 Success Metrics

**User Experience**:
- Update latency < 5 seconds
- Dashboard load time < 2 seconds
- Zero data loss during updates
- 99.9% uptime

**Accuracy Tracking**:
- All timeframes calculated correctly
- Historical accuracy preserved
- Rolling calculations efficient

**Usability**:
- User can make buy/sell decision in < 30 seconds
- Signal reasoning clearly understood
- Confidence in system recommendations

---

## 🚀 Development Phases

### Phase 1: Core Signals (Week 4)
- Implement signal panel
- Basic ticker display
- Simple accuracy metrics

### Phase 2: Order Recommendations (Week 5)
- Buy @ logic and display
- Sell @ logic and display
- Pattern recognition

### Phase 3: Advanced Metrics (Week 6)
- Multi-timeframe accuracy
- Range analysis
- Pattern tracking

### Phase 4: Live Charts (Week 7-8)
- Historical price charts
- Forecast overlays
- Confidence intervals
- Interactive features

---

## 📝 Notes for Development

**Key Considerations**:
1. Performance: Dashboard must not slow down Agent 01 operations
2. Separation of Concerns: Display logic separate from trading logic
3. Testing: Mock data for UI development
4. Security: No sensitive API keys in frontend
5. Logging: Track which signals users act on vs ignore

**Future Enhancements**:
- Mobile app
- Alert notifications (email, SMS, push)
- Historical signal playback
- Backtesting visualization
- Multi-portfolio support
- Customizable dashboard layouts

---

**End of Document**
