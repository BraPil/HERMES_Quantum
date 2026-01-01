# HERMES_Quantum State Savepoint - v0.2.0

**Created**: January 1, 2026, 23:45 UTC  
**Git SHA**: dfe24eed1f8043ce38bce64fa617a232a5a3a2e1  
**Branch**: main  
**Version**: v0.2.0

---

## Quick Restart

### Start Dashboard
```bash
cd /workspaces/HERMES_Quantum
python -m streamlit run scripts/dashboard.py --server.port 8501 --server.headless true
```

### Access Dashboard
- URL: http://localhost:8501
- Default Ticker: QBTS
- Auto-refresh: 5 seconds

### Key Commands
```bash
# Check dashboard status
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501

# Kill and restart dashboard
pkill -f streamlit
python -m streamlit run scripts/dashboard.py --server.port 8501 &

# Run tests (minimal)
pytest tests/ -v

# View logs
cat /tmp/streamlit.log
```

---

## Project State

### Architecture Overview

```
HERMES_Quantum/
├── agents/           # 9 agents (stubs, not integrated)
│   ├── 01_orchestrator/   # Decision maker
│   ├── 11_analyst/        # Integration & analysis
│   ├── 22_psychology/     # Market sentiment
│   ├── 23_social/         # Social media
│   ├── 24_politics/       # Regulatory/political
│   ├── 25_market/         # Technical analysis
│   ├── 91_tools/          # Shared utilities
│   ├── 92_optimizer/      # Model optimization (planned)
│   └── 99_models/         # Model registry
├── config/           # Configuration files
│   └── watchlist.yaml     # Target stocks
├── core/             # Core system (planned)
├── data_ingestion/   # Market data fetching
│   └── market_data.py     # yfinance wrapper
├── docs/             # Documentation (comprehensive)
├── library/          # Analysis libraries
│   ├── technical_analysis.py   # TA indicators, patterns
│   └── order_flow_ml.py        # ML order flow estimation
├── outputs/          # Generated outputs
├── research/         # Research phase docs
├── scripts/          # Executable scripts
│   ├── dashboard.py       # Main dashboard (1927 lines)
│   └── run_hermes.py      # Orchestrator entry point
└── tests/            # Test files (minimal)
```

### Key Files

| File | Purpose | Lines | State |
|------|---------|-------|-------|
| [scripts/dashboard.py](scripts/dashboard.py) | Main Streamlit dashboard | 1,927 | Production |
| [library/technical_analysis.py](library/technical_analysis.py) | TA library | 2,421 | Production |
| [library/order_flow_ml.py](library/order_flow_ml.py) | ML order flow | 655 | Production |
| [data_ingestion/market_data.py](data_ingestion/market_data.py) | Data fetcher | ~300 | Production |
| [config/watchlist.yaml](config/watchlist.yaml) | Stock watchlist | ~50 | Active |
| [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) | Project master plan | 759 | Active |

### Dashboard Components

| Component | Function | Status | Notes |
|-----------|----------|--------|-------|
| `render_sidebar()` | Period/ticker selection | ✅ | Has NYC time, branding |
| `render_fixed_price_banner()` | Floating price display | ✅ | position:fixed CSS |
| `render_ticker_info()` | Day metrics | ✅ | High/Low/Volume/Cap |
| `render_signals_panel()` | Trading signals | 🔄 | Uses placeholder data |
| `render_limit_orders()` | Buy/Sell targets | ✅ | Period-aware |
| `render_patterns()` | Chart patterns | ✅ | From TA library |
| `render_dynamic_trendlines()` | S/R trendlines | ✅ | 4-card layout |
| `render_price_chart()` | Main price chart | ✅ | Multi-period, rangebreaks |
| `render_rsi_chart()` | RSI indicator | ✅ | Period-aware, rangebreaks |
| `render_volume_profile()` | Volume analysis | ✅ | Order Walls cards |
| `render_ml_order_flow()` | ML predictions | ✅ | Graceful degradation |

### Period Configuration

```python
LOOKBACK_PERIODS = {
    "1hr": "5d",    # Fetch 5 days for 1-hour display
    "1d": "1mo",    # Fetch 1 month for 1-day display
    "1w": "3mo",    # Fetch 3 months for 1-week display
    "1mo": "6mo",   # Fetch 6 months for 1-month display
    "3mo": "1y",    # Fetch 1 year for 3-month display
    "1y": "2y"      # Fetch 2 years for 1-year display
}

DISPLAY_BARS = {
    "1hr": 60, "1d": 78, "1w": 45, "1mo": 22, "3mo": 65, "1y": 252
}

PERIOD_INTERVALS = {
    "1hr": Interval.MINUTE_1,
    "1d": Interval.MINUTE_5,
    "1w": Interval.HOUR_1,
    # Longer periods use Interval.DAY_1
}
```

---

## Environment

### Python
- **Version**: Python 3.11.14
- **Environment**: Dev container (Debian trixie)

### Key Packages
| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | 1.52.2 | Dashboard framework |
| plotly | 6.5.0 | Interactive charts |
| pandas | 2.3.3 | Data manipulation |
| numpy | 2.4.0 | Numerical operations |
| yfinance | 1.0 | Market data |
| pytz | 2025.2 | Timezone handling |

### Full Requirements
See [requirements.txt](requirements.txt) for complete list.

---

## Running Services

### Dashboard
- **Port**: 8501
- **Process**: `python -m streamlit run scripts/dashboard.py`
- **Auto-refresh**: 5 seconds
- **Background**: Should run in background with `nohup` or `&`

### No Other Services Required
- No database (planned for v0.3)
- No message queue (planned for v0.3)
- No external APIs active (yfinance is passive)

---

## Git State

### Current Position
- **Branch**: main
- **Commit**: dfe24ee (v0.1.1 commit)
- **Tag**: v0.1.0 exists (at 986fbf5)
- **v0.2.0 tag**: To be created with this wrapup

### Recent History
```
dfe24ee v0.1.1: UX refinement - ascending resistance, chart rangebreaks, RSI fixes
986fbf5 v0.1.0: HERMES Quantum Trading System - First Light
7f9aea7 feat: Add full technical analysis library and Streamlit dashboard
8705c4a feat: End-to-end trading analysis demo
```

### Uncommitted Changes
- All v0.2.0 documentation being created in this session
- Dashboard fixes (1% S/R filter, removed duplicate section)

---

## Known Issues

### Active Issues
| Issue | Severity | Workaround | Planned Fix |
|-------|----------|------------|-------------|
| Deprecation warning for `use_container_width` | Low | Ignore | Update after Dec 2025 |
| NYSE holidays not filtered | Low | Only weekends hidden | Add holiday calendar v0.3 |
| ML Order Flow disabled for 1hr | Low | Shows info message | Adapt algorithm v0.4 |
| Signal panels use placeholder data | Medium | N/A | Agent integration v0.3 |

### Resolved in v0.2.0
- ✅ Ascending resistance detection
- ✅ RSI warmup NaN handling
- ✅ Non-trading hours in charts
- ✅ S/R level scaling for intraday
- ✅ Fixed price banner positioning

---

## Configuration

### watchlist.yaml
```yaml
primary_stocks:
  - QBTS  # D-Wave Quantum
  - IONQ  # IonQ
  - RGTI  # Rigetti
  - QUBT  # Quantum Computing Inc.

default_ticker: QBTS
```

### Dashboard Settings (in code)
```python
# Page config
page_title = "HERMES Quantum Trading"
page_icon = "🔮"
layout = "wide"

# Refresh interval
AUTO_REFRESH_SECONDS = 5

# Sidebar width (CSS)
min_width = "180px"
max_width = "220px"
```

---

## Critical Path Through Codebase

### To Understand the Dashboard
1. Start at [scripts/dashboard.py](scripts/dashboard.py) `main()` function (line ~1800)
2. Follow the render chain: sidebar → banner → info → signals → charts
3. Data flows from `MarketDataFetcher` → `TechnicalAnalyzer` → render functions

### To Understand Technical Analysis
1. [library/technical_analysis.py](library/technical_analysis.py) `TechnicalAnalyzer` class
2. Key methods: `calculate_indicators()`, `detect_patterns()`, `get_dynamic_trendlines()`
3. Results returned as `TechnicalAnalysisResult` dataclass

### To Understand ML Order Flow
1. [library/order_flow_ml.py](library/order_flow_ml.py) `OrderFlowMLEstimator` class
2. Uses price action to estimate order walls
3. Returns `OrderFlowPrediction` with `estimated_walls` and `predicted_direction`

### To Add New Agent
1. Create directory under `agents/XX_name/`
2. Add `__init__.py` and `agent.py`
3. Define data sources and processing pipeline
4. Emit signals to event bus (to be created in v0.3)

---

## API Keys and Credentials

### Currently Used
- **None** - yfinance doesn't require API key

### Needed for v0.3
- Finnhub.io API key (free tier)
- StockTwits OAuth credentials
- Reddit PRAW app credentials

### Storage
- Will use environment variables or `.env` file
- Add to `.gitignore` to prevent commits

---

## Session Context

### What Was Accomplished This Session
1. Fixed ascending resistance trendline detection
2. Added rangebreaks for weekends and non-trading hours
3. Fixed RSI chart (warmup handling, annotation position)
4. Added 1-hour and 1-day period options
5. Increased lookback for SMA-50 warmup
6. Made limit orders use sidebar period
7. Renamed 5d to 1 Week consistently
8. Created Volume Profile Order Walls as cards
9. Moved branding and NYC time to sidebar
10. Created fixed-position price banner
11. Added 1% S/R filter for 1-hour view
12. Removed duplicate Prediction Accuracy section
13. Added graceful handling for ML Order Flow on 1hr

### User Preferences Noted
- Prefers explicit fixes over suggested approaches
- Values comprehensive documentation
- Interested in live UAT with rapid iteration
- Focus on trader-relevant information

### Communication Style
- Detailed feedback with specific line items
- Numbered lists for multiple issues
- Immediate testing after changes

---

## Restart Instructions

### New Session Checklist
1. [ ] Review this state savepoint
2. [ ] Review [HERMES_Quantum_ANALYSIS_AND_PLAN_v0.3.0_2026-01-01.md](HERMES_Quantum_ANALYSIS_AND_PLAN_v0.3.0_2026-01-01.md)
3. [ ] Start dashboard: `python -m streamlit run scripts/dashboard.py --server.port 8501 &`
4. [ ] Verify running: `curl http://localhost:8501`
5. [ ] Check git status: `git status`
6. [ ] Begin v0.3.0 work on the v0.3 branch

### Context Transfer Prompt
Use this to brief a new session:

> "I'm continuing work on HERMES_Quantum, a multi-agent trading analysis system. 
> We just completed v0.2.0 which focused on dashboard UX refinement.
> The dashboard runs on Streamlit port 8501 with 6 time periods (1hr to 1yr).
> Key files are scripts/dashboard.py and library/technical_analysis.py.
> v0.3.0 will focus on integrating sentiment agents (22_psychology, 23_social).
> Review the state savepoint at docs/HERMES_Quantum_STATE_SAVEPOINT_v0.2.0_2026-01-01.md"

---

## Appendix: File Checksums

For verification of state integrity:

```
Dashboard:     1927 lines - scripts/dashboard.py
Tech Analysis: 2421 lines - library/technical_analysis.py
Order Flow ML:  655 lines - library/order_flow_ml.py
Total Core:    5003 lines
```

---

## Appendix: Documentation Index

### Created This Session
| Document | Purpose |
|----------|---------|
| [BRANCH_WRAPUP_PROTOCOL.md](protocols/BRANCH_WRAPUP_PROTOCOL.md) | Standard wrapup process |
| [HERMES_Quantum_ACCOMPLISHMENTS_v0.2.0_2026-01-01.md](HERMES_Quantum_ACCOMPLISHMENTS_v0.2.0_2026-01-01.md) | Version achievements |
| [HERMES_Quantum_WORK_LOG_v0.2.0_2026-01-01.md](HERMES_Quantum_WORK_LOG_v0.2.0_2026-01-01.md) | Detailed change log |
| [HERMES_Quantum_LESSONS_LEARNED_v0.2.0_2026-01-01.md](HERMES_Quantum_LESSONS_LEARNED_v0.2.0_2026-01-01.md) | Technical insights |
| [HERMES_Quantum_ANALYSIS_AND_PLAN_v0.3.0_2026-01-01.md](HERMES_Quantum_ANALYSIS_AND_PLAN_v0.3.0_2026-01-01.md) | Next version plan |
| [HERMES_Quantum_STATE_SAVEPOINT_v0.2.0_2026-01-01.md](HERMES_Quantum_STATE_SAVEPOINT_v0.2.0_2026-01-01.md) | This document |

### Pre-Existing Key Docs
| Document | Purpose |
|----------|---------|
| [MASTER_PLAN.md](MASTER_PLAN.md) | Overall project vision |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Technical implementation guide |
| [UX_REQUIREMENTS_V1.md](UX_REQUIREMENTS_V1.md) | Dashboard UX specification |
| [VERSION_0.1_RELEASE.md](VERSION_0.1_RELEASE.md) | First release notes |

---

**End of State Savepoint v0.2.0**
