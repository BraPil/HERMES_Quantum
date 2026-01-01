# HERMES_Quantum Analysis and Plan - v0.3.0

**Created**: January 1, 2026  
**For Version**: v0.3.0  
**Previous Version**: v0.2.0 (Dashboard UX Refinement)  
**Target Duration**: 1-2 weeks

---

## Executive Summary

With v0.2.0 completing the dashboard UX refinement phase, the HERMES_Quantum project is at a strategic inflection point. We have a polished, trader-ready dashboard that displays real-time price data, technical analysis, and ML-based predictions. However, the core agent system remains largely unintegrated - the dashboard runs independently of the multi-agent architecture defined in our Master Plan.

**v0.3.0 Focus**: Bridge the gap between the presentation layer (dashboard) and the intelligence layer (agents).

---

## Part 1: Current State Assessment

### What We Have (End of v0.2.0)

#### Dashboard (Functional)
| Component | Status | Quality |
|-----------|--------|---------|
| Price Chart | ✅ Complete | High |
| RSI Chart | ✅ Complete | High |
| S/R Levels | ✅ Complete | High |
| Dynamic Trendlines | ✅ Complete | Medium |
| Volume Profile | ✅ Complete | Medium |
| ML Order Flow | ✅ Complete | Medium |
| Limit Orders | ✅ Complete | Medium |
| Signal Panels | 🔄 Basic | Low |
| Fixed Price Banner | ✅ Complete | High |
| Multi-Timeframe | ✅ Complete | High |

#### Agents (Designed, Not Integrated)
| Agent | Design | Implementation | Dashboard Integration |
|-------|--------|----------------|----------------------|
| 01_orchestrator | ✅ | ⚠️ Partial | ❌ None |
| 11_analyst | ✅ | ⚠️ Partial | ❌ None |
| 22_psychology | ✅ | ❌ Stub | ❌ None |
| 23_social | ✅ | ❌ Stub | ❌ None |
| 24_politics | ✅ | ❌ Stub | ❌ None |
| 25_market | ✅ | ⚠️ Partial | 🔄 Indirect (TA) |
| 91_tools | ✅ | ⚠️ Partial | 🔄 Partial |
| 92_optimizer | ✅ | ❌ Stub | ❌ None |
| 99_models | ✅ | ❌ Stub | ❌ None |

#### Data Layer (Mixed)
| Data Source | Status | Used By |
|-------------|--------|---------|
| yfinance | ✅ Active | Dashboard, TA |
| Technical Analysis Library | ✅ Active | Dashboard |
| ML Order Flow | ✅ Active | Dashboard |
| RSS Feeds | ❌ Not Started | Agent 22/23 |
| StockTwits API | ❌ Not Started | Agent 23 |
| Reddit PRAW | ❌ Not Started | Agent 23 |
| SEC Edgar | ❌ Not Started | Agent 24 |

#### Code Metrics
| Category | Files | Lines | Status |
|----------|-------|-------|--------|
| Dashboard | 2 | ~2,200 | Production |
| Library | 4 | ~3,500 | Production |
| Agents | 18 | ~500 | Stubs only |
| Tests | 3 | ~150 | Minimal |
| Docs | 20+ | ~10,000+ | Comprehensive |

---

## Part 2: Gap Analysis

### Critical Gaps (Must Address for v0.3)

#### 1. No Agent-Dashboard Communication
**Current State**: Dashboard runs independently, no agent signals displayed.  
**Impact**: Core value proposition of multi-agent analysis not realized.  
**Gap Size**: Large - requires event bus or API layer.

#### 2. No Real Sentiment Analysis
**Current State**: Placeholder data in signal panels.  
**Impact**: "Psychology" and "Social" signals are fake.  
**Gap Size**: Large - requires API integrations.

#### 3. No Persistent Storage
**Current State**: All state lost on restart.  
**Impact**: Cannot track prediction accuracy, learn from history.  
**Gap Size**: Medium - requires database layer.

#### 4. Limited Error Handling
**Current State**: Basic try/except, crashes on some edge cases.  
**Impact**: Dashboard can fail during market volatility.  
**Gap Size**: Medium - requires systematic error boundaries.

### Secondary Gaps (Can Defer to v0.4+)

1. **No Paper Trading Integration** - IBKR API not connected
2. **No Multi-Ticker Support** - One ticker at a time
3. **No User Authentication** - Anyone can access
4. **No Mobile Responsiveness** - Desktop only
5. **No Alerting System** - No push notifications

---

## Part 3: v0.3.0 Objectives

### Primary Objective
**Integrate at least one specialist agent with the dashboard** to provide real, actionable signals.

### Secondary Objectives
1. Implement basic persistence layer for tracking predictions
2. Add proper error boundaries and logging
3. Create agent health monitoring
4. Improve code organization and testing

---

## Part 4: Feature Specifications

### Feature 1: Sentiment Agent Integration (Agent 22 + 23)

#### 1.1 News Sentiment Pipeline
**Goal**: Fetch and analyze news for target stocks.

**Data Sources**:
- Yahoo Finance RSS (free, real-time)
- Seeking Alpha RSS (free, with delay)
- Finnhub.io Free Tier (60 calls/min)

**Processing Pipeline**:
```
RSS Feeds → Fetch (every 15 min)
    ↓
Filter by Ticker Relevance
    ↓
ProsusAI/finbert Sentiment Analysis
    ↓
Aggregate Score (weighted by recency)
    ↓
Store in DB + Send to Dashboard
```

**Dashboard Integration**:
- Real sentiment score in "Psychology" signal panel
- News headline list with sentiment colors
- Trend indicator (sentiment improving/declining)

#### 1.2 Social Sentiment Pipeline
**Goal**: Monitor social media for stock mentions.

**Data Sources**:
- StockTwits API (400 req/hour)
- Reddit PRAW (r/stocks, r/investing)

**Processing Pipeline**:
```
StockTwits/Reddit → Fetch (every 30 min)
    ↓
Filter by Ticker + Relevance
    ↓
FinTwitBERT Sentiment Analysis
    ↓
Aggregate Score (volume-weighted)
    ↓
Store in DB + Send to Dashboard
```

**Dashboard Integration**:
- Real social sentiment in "Social" signal panel
- Top mentions list
- Mention volume indicator

---

### Feature 2: Persistence Layer

#### 2.1 Database Schema
**Technology**: SQLite (simple, no server required)

**Tables**:
```sql
-- Price snapshots for tracking predictions
CREATE TABLE price_snapshots (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    timestamp DATETIME,
    price REAL,
    volume INTEGER
);

-- Agent signals for accuracy tracking
CREATE TABLE agent_signals (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    symbol TEXT,
    timestamp DATETIME,
    signal_type TEXT,  -- BUY, SELL, HOLD
    confidence REAL,
    reasoning TEXT
);

-- Prediction tracking
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    signal_id INTEGER,
    predicted_direction TEXT,
    predicted_price_target REAL,
    expiry_timestamp DATETIME,
    actual_direction TEXT,
    actual_price REAL,
    was_correct BOOLEAN,
    FOREIGN KEY (signal_id) REFERENCES agent_signals(id)
);

-- News/Social items for audit trail
CREATE TABLE news_items (
    id INTEGER PRIMARY KEY,
    source TEXT,
    symbol TEXT,
    headline TEXT,
    timestamp DATETIME,
    sentiment_score REAL,
    url TEXT
);
```

#### 2.2 Data Access Layer
**Pattern**: Repository pattern for clean separation.

```python
class SignalRepository:
    def save_signal(self, agent_id, symbol, signal_type, confidence, reasoning)
    def get_recent_signals(self, symbol, limit=10)
    def get_accuracy_stats(self, agent_id, timeframe)

class PredictionRepository:
    def create_prediction(self, signal_id, direction, target, expiry)
    def resolve_prediction(self, prediction_id, actual_direction, actual_price)
    def get_accuracy_by_timeframe(self)
```

---

### Feature 3: Agent Communication Bus

#### 3.1 Event Bus Architecture
**Technology**: Python queue + asyncio

**Events**:
```python
@dataclass
class SignalEvent:
    event_type: str  # "SIGNAL", "ALERT", "HEALTH"
    agent_id: str
    symbol: str
    timestamp: datetime
    payload: dict

# Example payloads:
# SIGNAL: {"type": "BUY", "confidence": 0.75, "reasoning": "..."}
# ALERT: {"level": "WARNING", "message": "..."}
# HEALTH: {"status": "HEALTHY", "last_run": "..."}
```

**Flow**:
```
Agent 22 → EventBus → Aggregator → Dashboard
Agent 23 ↗
Agent 24 ↗
Agent 25 ↗
```

#### 3.2 Dashboard Subscription
**Pattern**: Polling (Streamlit limitation) or WebSocket (if upgrading framework).

For Streamlit (polling):
```python
def get_latest_signals(symbol: str) -> List[SignalEvent]:
    """Poll event bus for latest signals."""
    # Read from shared state or database
    pass
```

---

### Feature 4: Error Boundaries and Logging

#### 4.1 Structured Logging
**Technology**: Python `logging` with JSON formatter

**Log Levels**:
- DEBUG: Detailed debugging info
- INFO: Normal operations
- WARNING: Recoverable issues
- ERROR: Failures requiring attention
- CRITICAL: System failures

**Log Format**:
```json
{
    "timestamp": "2026-01-01T10:30:45",
    "level": "INFO",
    "component": "dashboard",
    "function": "render_price_chart",
    "symbol": "QBTS",
    "message": "Chart rendered successfully",
    "duration_ms": 234
}
```

#### 4.2 Error Boundaries
**Pattern**: Decorator-based error catching

```python
def error_boundary(component_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {component_name}: {e}")
                st.error(f"⚠️ {component_name} temporarily unavailable")
                return None
        return wrapper
    return decorator

@error_boundary("Price Chart")
def render_price_chart(...):
    ...
```

---

## Part 5: Technical Tasks Breakdown

### Week 1: Foundation

#### Day 1-2: Persistence Layer
- [ ] Create SQLite database schema
- [ ] Implement SignalRepository class
- [ ] Implement PredictionRepository class
- [ ] Add database initialization on startup
- [ ] Write unit tests for repositories

#### Day 3-4: Logging and Error Handling
- [ ] Set up structured logging with JSON format
- [ ] Create log rotation configuration
- [ ] Implement error boundary decorator
- [ ] Apply error boundaries to all render functions
- [ ] Add component timing logs

#### Day 5: Event Bus
- [ ] Design event bus interface
- [ ] Implement simple queue-based event bus
- [ ] Create signal aggregator
- [ ] Add dashboard polling mechanism

### Week 2: Sentiment Integration

#### Day 6-7: News Sentiment (Agent 22)
- [ ] Implement RSS feed fetcher
- [ ] Set up Finnhub.io integration
- [ ] Integrate ProsusAI/finbert model
- [ ] Create news sentiment aggregation
- [ ] Store results in database

#### Day 8-9: Social Sentiment (Agent 23)
- [ ] Implement StockTwits API client
- [ ] Implement Reddit PRAW fetcher
- [ ] Integrate FinTwitBERT model
- [ ] Create social sentiment aggregation
- [ ] Store results in database

#### Day 10: Dashboard Integration
- [ ] Update signal panels with real data
- [ ] Add news headline list
- [ ] Add social mention list
- [ ] Create sentiment trend indicators
- [ ] Test full pipeline end-to-end

---

## Part 6: Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Model inference too slow | Medium | High | Batch processing, caching |
| API rate limits hit | High | Medium | Implement backoff, queue requests |
| Database corruption | Low | High | Regular backups, WAL mode |
| Memory issues with models | Medium | Medium | Lazy loading, model pooling |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API integration delays | High | Medium | Start with mock data |
| Model download issues | Low | Low | Pre-download, cache locally |
| Scope creep | Medium | High | Strict feature freeze |

---

## Part 7: Success Criteria

### Minimum Viable Product (MVP)
- [ ] At least one agent producing real signals
- [ ] Signals displayed in dashboard
- [ ] Basic persistence working
- [ ] Error boundaries preventing crashes

### Stretch Goals
- [ ] Two agents integrated (22 + 23)
- [ ] Prediction tracking with accuracy stats
- [ ] Agent health monitoring dashboard

### Definition of Done
1. Code reviewed and tested
2. Documentation updated
3. Dashboard stable for 24+ hours
4. No critical bugs
5. Performance acceptable (<5s page load)

---

## Part 8: Dependencies and Prerequisites

### External Dependencies
- **Finnhub.io API Key**: Sign up at finnhub.io (free tier)
- **StockTwits OAuth**: Register app at stocktwits.com/developers
- **Reddit PRAW**: Register app at reddit.com/prefs/apps

### Model Downloads
- ProsusAI/finbert (~440MB)
- FinTwitBERT (~440MB)

### Python Packages to Add
```
finnhub-python
praw
feedparser  # For RSS
sqlalchemy  # For ORM
alembic     # For migrations (optional)
```

---

## Part 9: Documentation Plan

### New Documents to Create
1. `HERMES_AGENT_INTEGRATION_GUIDE.md` - How agents communicate
2. `HERMES_DATABASE_SCHEMA.md` - Database design
3. `HERMES_API_SETUP_GUIDE.md` - External API configuration

### Documents to Update
- `MASTER_PLAN.md` - Add v0.3 to version history
- `EXPLORATION_LOG.md` - Log v0.2 completion
- `STATE.yaml` - Update phase status

---

## Part 10: Timeline

```
v0.3.0 Development Timeline (10 days)
======================================

Week 1:
  Day 1-2: Persistence Layer ████████░░
  Day 3-4: Logging & Errors ████████░░
  Day 5:   Event Bus        ████░░░░░░

Week 2:
  Day 6-7: News Sentiment   ████████░░
  Day 8-9: Social Sentiment ████████░░
  Day 10:  Integration      ████░░░░░░

v0.3.0 Release: ~January 11, 2026
```

---

## Conclusion

Version 0.3.0 represents the transition from "demonstration" to "functional prototype." By integrating real sentiment analysis and establishing proper persistence, we transform the dashboard from a pretty display into a genuine trading intelligence tool.

The key risks are API integration complexity and model inference performance. We mitigate these by starting with mock data and implementing proper caching.

Success in v0.3.0 sets the stage for v0.4.0's focus on the full agent orchestra - bringing all 9 agents online and coordinating their signals through the orchestrator.

---

## Appendix: Quick Reference

### File Structure After v0.3.0
```
HERMES_Quantum/
├── agents/
│   ├── 22_psychology/
│   │   ├── news_fetcher.py      # NEW
│   │   ├── sentiment_analyzer.py # NEW
│   │   └── agent.py             # Updated
│   ├── 23_social/
│   │   ├── stocktwits_client.py # NEW
│   │   ├── reddit_client.py     # NEW
│   │   └── agent.py             # Updated
│   └── shared/
│       └── event_bus.py         # NEW
├── core/
│   ├── database.py              # NEW
│   ├── repositories.py          # NEW
│   └── logging_config.py        # NEW
├── data/
│   └── hermes.db                # NEW (SQLite)
├── scripts/
│   └── dashboard.py             # Updated
└── tests/
    ├── test_repositories.py     # NEW
    └── test_sentiment.py        # NEW
```

### Key Metrics to Track
- Signal generation rate (signals/hour)
- Sentiment accuracy (after 24hr)
- Dashboard uptime (%)
- API call success rate (%)
- Model inference time (ms)
