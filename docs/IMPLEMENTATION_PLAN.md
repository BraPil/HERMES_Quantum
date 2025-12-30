# HERMES_Quantum: Comprehensive Project Analysis & Implementation Plan

**Analysis Date**: 2025-12-28  
**Phase**: 0 → 1 Transition  
**Status**: Research Complete, Implementation Planning

---

## PART 1: CURRENT PROJECT STATE

### What We Have Built (Phase 0)

#### 1. **Agent Architecture** (9 Agents)
- ✅ **01_orchestrator**: Designed (Zipline EventManager pattern)
- ✅ **11_analyst**: Designed (PyPortfolioOpt, empyrical-reloaded)
- ✅ **22_psychology**: Designed + Model (ProsusAI/finbert)
- ✅ **23_social**: Designed + Model (FinTwitBERT-sentiment)
- ✅ **24_politics**: Designed + Model (facebook/bart-large-mnli)
- ✅ **25_market**: Designed + Model (amazon/chronos-t5-large)
- ✅ **91_tools**: Designed (yfinance, pandas_ta, Quandl)
- ✅ **92_optimizer**: Designed (Optuna, Ray Tune, cross-validation)
- ✅ **99_models**: Designed (Qlib Recorder + Registry)

#### 2. **Research Documentation** (17,500+ lines)
- 5 HuggingFace model evaluations
- 3 GitHub framework evaluations  
- 2 comprehensive summaries
- Agent 92 design docs

#### 3. **Key Decisions Made**
- **Architecture**: Dual framework (Qlib data/models + Zipline events/factors)
- **Models**: 4 production-ready models adopted
- **Tools**: 200+ tools cataloged, 10+ prioritized
- **Optimization**: Agent 92 for continuous improvement

#### 4. **Target Stocks**
- QBTS (D-Wave Quantum)
- IONQ (IonQ Inc.)
- RGTI (Rigetti Computing)
- QUBT (Quantum Computing Inc.)

---

## PART 2: TOOLS & RESOURCE ENVIRONMENT ANALYSIS

### CRITICAL UPDATES (2025-12-28 Evening)

**Data Source Clarifications**:

1. **Twitter → X API Reality Check**:
   - Rebranded to "X API" in 2023
   - **Basic tier**: $100/month for 10,000 posts/month (≈333 posts/day)
   - **Pro tier**: $5,000/month for 1M posts/month
   - **Assessment**: Poor value for small-scale trading bot
   - **Recommendation**: **SKIP** - use free alternatives

2. **StockTwits (NOT Reddit)**:
   - Separate company (StockTwits Inc.), NOT part of Reddit
   - **Free API**: 400 requests/hour with authentication
   - API Docs: https://api.stocktwits.com/developers/docs
   - **Assessment**: Excellent free alternative to X API
   - **Recommendation**: **HIGH PRIORITY** for Agent 23

3. **Reddit API (Proper Usage)**:
   - Free with OAuth2, strict rate limits (60 requests/minute)
   - **Use PRAW library**: Built-in rate limiting prevents bans
   - **Subreddits**: r/wallstreetbets, r/stocks, r/investing, r/QuantumComputing
   - **Assessment**: Free, high-quality social sentiment
   - **Recommendation**: **HIGH PRIORITY** with proper rate limiting

4. **News Services**:
   - **Benzinga**: Still exists but $500+/month (too expensive)
   - **Better alternatives**:
     - **Finnhub.io**: FREE tier (60 calls/min, real-time news)
     - **Alpha Vantage News**: FREE tier (25 requests/day)
     - **DIY RSS Feeds**: Yahoo Finance, Seeking Alpha, MarketWatch (FREE!)
   - **Recommendation**: **DIY RSS aggregation** for Week 1-2

5. **Options Flow/Heatmaps**:
   - **Bookmap**: $49-99/month, mostly crypto focus now
   - **Unusual Whales**: $50/month, excellent options flow data
   - **FlowAlgo**: $167/month, premium options flow
   - **DIY Option**: CBOE delayed quotes (15min delay, free)
   - **Reality**: Real-time options flow requires expensive exchange data
   - **Recommendation**: **DEFER** to Phase 2, start with DIY CBOE tracker

### DIY vs Paid Services - Decision Matrix

| Data Type | DIY Feasible? | DIY Method | Paid Alternative | Cost | Recommendation |
|-----------|---------------|------------|------------------|------|----------------|
| **Stock Prices** | ✅ YES | yfinance (15min delay) | Polygon.io | $199/mo | **DIY** |
| **News Headlines** | ✅ YES | RSS feeds (Y!, SA, MW) | Benzinga | $500+/mo | **DIY** |
| **Social Sentiment** | ✅ YES | Reddit PRAW + StockTwits API | X API | $100/mo | **DIY** |
| **Options Flow** | ⚠️ LIMITED | CBOE delayed (15min) | Unusual Whales | $50/mo | **DIY MVP, evaluate** |
| **Earnings Data** | ✅ YES | SEC Edgar API | FactSet | $$$$ | **DIY** |
| **Technical Indicators** | ✅ YES | pandas_ta | TradingView | $60/mo | **DIY** |
| **Macro Data** | ✅ YES | FRED API | Bloomberg | $$$$ | **DIY** |

**Cost-Benefit Analysis**:

| Service | Cost/Month | Benefit | ROI Score | Week 1-2 Priority |
|---------|-----------|---------|-----------|-------------------|
| **yfinance** | $0 | Stock data, fundamentals | ∞ | **CRITICAL** |
| **RSS Feeds** | $0 | News (fast, comprehensive) | ∞ | **CRITICAL** |
| **Reddit PRAW** | $0 | Social sentiment (with proper rate limiting) | ∞ | **HIGH** |
| **StockTwits API** | $0 | Financial social sentiment | ∞ | **HIGH** |
| **SEC Edgar API** | $0 | Earnings, filings, 10-Ks | ∞ | **HIGH** |
| **FRED API** | $0 | Macro data (Fed policy) | ∞ | **MEDIUM** |
| **Finnhub.io Free** | $0 | Real-time news (60/min) | ∞ | **MEDIUM** |
| **CBOE Delayed** | $0 | Options OI/volume (15min delay) | High | **MEDIUM** |
| **X API Basic** | $100 | Social (333 posts/day limit) | **Low** | **SKIP** ❌ |
| **Unusual Whales** | $50 | Options flow (real-time) | Medium | **DEFER** ⏸️ |
| **Polygon.io** | $199 | Real-time stocks + news | Low | **DEFER** ⏸️ |
| **Benzinga** | $500+ | Real-time news | **Very Low** | **SKIP** ❌ |

**DECISION: DIY-First Strategy**

✅ **Weeks 1-2**: Build FREE data pipelines  
✅ **Weeks 3-4**: Evaluate data quality and coverage gaps  
⏸️ **Week 5+**: Consider paid services ONLY if critical gaps exist  
❌ **Never**: X API ($100/mo for 333 posts), Benzinga ($500+/mo)  

### DIY Data Collection Implementation Plan

**1. RSS News Aggregator** (Week 1, Day 3-4):
```python
# agents/91_tools/news_aggregator.py
import feedparser
import sqlite3
from datetime import datetime

RSS_FEEDS = [
    'https://finance.yahoo.com/rss/',           # Yahoo Finance
    'https://seekingalpha.com/market_currents.xml',  # Seeking Alpha
    'https://www.marketwatch.com/rss/topstories/',   # MarketWatch
    'https://www.investing.com/rss/news.rss',   # Investing.com
]

QUANTUM_KEYWORDS = ['QBTS', 'IONQ', 'RGTI', 'QUBT', 'quantum computing', 'quantum stock']

def fetch_news():
    """Fetch RSS feeds every 5 minutes, filter for quantum stocks"""
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if any(kw in entry.title or kw in entry.summary for kw in QUANTUM_KEYWORDS):
                # Store in SQLite, deduplicate by URL
                # Pass to Agent 22 (finbert) for sentiment
                pass
```

**2. Social Sentiment Collector** (Week 2, Day 8-10):
```python
# agents/91_tools/social_collector.py
import praw  # Reddit
import requests  # StockTwits
import time

# Reddit (60 requests/min with PRAW's built-in rate limiting)
reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_SECRET',
    user_agent='HERMES_Quantum v1.0'
)

SUBREDDITS = ['wallstreetbets', 'stocks', 'investing', 'QuantumComputing', 'IONQ']
TICKERS = ['QBTS', 'IONQ', 'RGTI', 'QUBT']

def fetch_reddit_sentiment():
    """Search subreddits for quantum stock mentions"""
    for subreddit_name in SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        for ticker in TICKERS:
            # PRAW handles rate limiting automatically
            for post in subreddit.search(ticker, limit=10, time_filter='day'):
                # Pass to Agent 23 (FinTwitBERT) for sentiment
                pass

# StockTwits (400 requests/hour = 1 request every 9 seconds)
def fetch_stocktwits_sentiment():
    """Fetch StockTwits streams for quantum stocks"""
    for ticker in TICKERS:
        url = f'https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json'
        response = requests.get(url)
        if response.status_code == 200:
            # Parse messages, pass to Agent 23
            time.sleep(10)  # Rate limiting: 400/hour = 1 every 9 sec
```

**3. Custom Options Tracker** (Week 3-4, MVP):
```python
# agents/91_tools/options_tracker.py
import yfinance as yf
import matplotlib.pyplot as plt

def track_options_activity(ticker):
    """Track OI changes, Put/Call ratio, IV rank (15min delayed)"""
    stock = yf.Ticker(ticker)
    
    # Get options chain (free, delayed 15min)
    options_dates = stock.options
    for date in options_dates[:3]:  # Next 3 expiries
        opt_chain = stock.option_chain(date)
        calls = opt_chain.calls
        puts = opt_chain.puts
        
        # Calculate metrics
        total_call_oi = calls['openInterest'].sum()
        total_put_oi = puts['openInterest'].sum()
        put_call_ratio = total_put_oi / total_call_oi
        
        # Build simple heatmap (matplotlib)
        # Not real-time but identifies trends over days/weeks
        
    # Upgrade to Unusual Whales ($50/mo) if real-time critical
```

### A. Current MCP Integrations (Active)

| MCP Server | Purpose | Usage in HERMES | Priority |
|------------|---------|-----------------|----------|
| **HuggingFace** | Model discovery, evaluation | Phase 0 research, future model updates | HIGH |
| **Microsoft Playwright** | Web automation, browser control | Data scraping, news monitoring | MEDIUM |
| **GitHub** | Code search, repo analysis | Framework research, open source tools | HIGH |

**Status**: All 3 MCPs operational and well-utilized in Phase 0.

### B. Recommended NEW MCPs to Add (REVISED)

#### 1. **Financial Data MCPs** (HIGH PRIORITY)

**SKIP X/Twitter API MCP** ❌
- **Why**: $100/month for only 333 posts/day is poor value
- **Alternative**: Use FREE StockTwits API + Reddit PRAW
- **Savings**: $100/month

**yfinance MCP** (if exists) or **Alpha Vantage MCP**
- **Purpose**: Real-time stock data for QBTS, IONQ, RGTI, QUBT
- **Why**: Core data for Agent 25 (market) and Agent 11 (analyst)
- **Alternative**: Build custom data ingestion using yfinance library
- **Action**: Research if MCP exists, else use yfinance directly

**Quandl/NASDAQ Data Link MCP**
- **Purpose**: Macro/fundamental data, economic indicators
- **Why**: Agent 24 (politics) and Agent 11 (analyst) need macro context
- **Action**: Check for existing MCP integration

#### 2. **Social Media MCPs** (HIGH PRIORITY - FREE ALTERNATIVES)

**StockTwits API** (NEW RECOMMENDATION)
- **Purpose**: Financial social sentiment (free, 400 req/hour)
- **Why**: Agent 23 (social) core functionality, better than X API
- **Cost**: FREE with authentication
- **Action**: **CRITICAL** - Implement in Week 2

**Reddit API (PRAW)** (PROPER IMPLEMENTATION)
- **Purpose**: r/wallstreetbets, r/stocks, r/QuantumComputing discussions
- **Why**: Agent 23 (social) primary data source
- **Implementation**: Use PRAW library with built-in rate limiting (60/min)
- **Cost**: FREE
- **Action**: **CRITICAL** - Implement in Week 2

#### 3. **News & Sentiment MCPs** (MEDIUM PRIORITY - DIY FIRST)

**DIY RSS Aggregator** (RECOMMENDED)
- **Purpose**: Financial news from Yahoo, Seeking Alpha, MarketWatch
- **Why**: Agent 22 (psychology) and Agent 24 (politics) input
- **Cost**: FREE, no rate limits, fast updates (5min intervals)
- **Action**: Build in Week 1, Day 3-4

**Finnhub.io MCP** (if exists)
- **Purpose**: Real-time news (60 calls/min free tier)
- **Why**: Supplement RSS feeds for comprehensive coverage
- **Action**: Research MCP availability, implement Week 2

**SKIP News API.org** (unless free tier sufficient)
- **Why**: $449/month for live news, RSS feeds are free and fast enough
- **Action**: Evaluate free tier (100 requests/day), likely skip

#### 4. **Experiment Tracking MCPs** (MEDIUM PRIORITY)

**Weights & Biases MCP**
- **Purpose**: ML experiment tracking for Agent 92
- **Why**: Track optimization runs, model performance
- **Action**: Set up W&B account and integration

**MLflow MCP** (if exists)
- **Purpose**: Model versioning for Agent 99
- **Why**: Production model management
- **Action**: Research or use MLflow directly

#### 5. **Development & Productivity MCPs** (LOW PRIORITY)

**Notion MCP** (already might exist)
- **Purpose**: Project documentation and knowledge base
- **Why**: Team collaboration if scaling
- **Action**: Defer until team grows

**Slack/Discord MCP**
- **Purpose**: Real-time alerts and notifications
- **Why**: Agent 01 (orchestrator) alerts
- **Action**: Phase 2 if needed

### C. SDKs & Libraries Assessment

#### **Currently Used** ✅
| Library | Purpose | Status |
|---------|---------|--------|
| transformers | NLP models | Installed |
| torch | Model inference | Installed |
| optuna | Hyperparameter tuning | Installed |
| ray[tune] | Distributed optimization | Installed |

#### **Need to Install** ⏳
| Library | Purpose | Priority | Command |
|---------|---------|----------|---------|
| yfinance | Stock data | **HIGH** | `pip install yfinance` |
| pandas_ta | Technical indicators | **HIGH** | `pip install pandas-ta` |
| PyPortfolioOpt | Portfolio optimization | **HIGH** | `pip install PyPortfolioOpt` |
| empyrical-reloaded | Performance metrics | **HIGH** | `pip install empyrical-reloaded` |
| pyfolio-reloaded | Portfolio analytics | MEDIUM | `pip install pyfolio-reloaded` |
| alphalens-reloaded | Factor analysis | MEDIUM | `pip install alphalens-reloaded` |
| mlfinlab | Financial ML | MEDIUM | `pip install mlfinlab` |
| quandl | Macro data | MEDIUM | `pip install quandl` |
| praw | Reddit API | MEDIUM | `pip install praw` |
| tweepy | Twitter API | MEDIUM | `pip install tweepy` |
| wandb | Experiment tracking | LOW | `pip install wandb` |
| mlflow | Model management | LOW | `pip install mlflow` |

### D. External Resources & Websites

#### **Financial Data Sources**
1. **Yahoo Finance** (free, via yfinance)
   - Stock prices, volume, historical data
   - Real-time quotes (15-min delay free tier)
   
2. **Quandl/NASDAQ Data Link** (free tier available)
   - Macro indicators, Fed data
   - Alternative data sources

3. **Alpha Vantage** (free tier: 5 calls/min)
   - Alternative to yfinance
   - More reliable for some metrics

4. **FRED (Federal Reserve)** (free)
   - Economic indicators
   - Interest rates, inflation

#### **News Sources**
1. **NewsAPI.org** (free tier: 100 requests/day)
   - Financial news aggregation
   - Quantum computing news

2. **Google News RSS**
   - Free, no API key
   - Can scrape with Playwright

3. **Seeking Alpha** (paid, but high quality)
   - Analyst articles
   - Earnings transcripts

#### **Social Media**
1. **Twitter/X API** (paid $100/month for basic tier)
   - Real-time tweets
   - Historical search

2. **Reddit API** (free)
   - Subreddit monitoring
   - Community sentiment

3. **StockTwits** (free API)
   - Dedicated stock discussions
   - Retail sentiment

#### **Reference & Research**
1. **arXiv.org**
   - Quantum computing papers
   - ML/finance research

2. **Qlib Documentation**
   - Implementation examples
   - Best practices

3. **Zipline Documentation**
   - Event-driven patterns
   - Pipeline API examples

---

## PART 3: PRIORITIZED IMPLEMENTATION PLAN

### Overview: 6-Week Roadmap

**Weeks 1-2**: Core Infrastructure (Phase 1)  
**Weeks 3-4**: Advanced Analytics (Phase 2)  
**Weeks 5-6**: Multi-Agent & RL (Phase 3)

---

## PHASE 1: Core Infrastructure (Weeks 1-2)

### WEEK 1: Data Layer & Model Integration

#### Day 1-2: Environment Setup
**Goal**: Install dependencies and set up development environment

**Tasks**:
1. ✅ Install core data libraries
   ```bash
   pip install yfinance pandas-ta PyPortfolioOpt empyrical-reloaded
   pip install praw  # Reddit API (proper rate limiting)
   pip install feedparser  # RSS parsing (news aggregation)
   pip install requests beautifulsoup4  # StockTwits + web scraping
   ```

2. ✅ Set up API keys (`.env` file) - **FREE SOURCES ONLY**
   - ❌ ~~Twitter API~~ (SKIP: $100/month for 333 posts/day)
   - ✅ Reddit API credentials (FREE, 60 req/min with PRAW)
   - ✅ StockTwits access token (FREE, 400 req/hour)
   - ✅ Finnhub.io key (FREE tier, 60 calls/min)
   - ✅ Alpha Vantage key (FREE tier, 25 req/day)
   - ✅ SEC Edgar User-Agent (FREE, unlimited with rate limiting)

3. ✅ Download adopted models
   ```python
   # Download models locally for faster inference
   - ProsusAI/finbert
   - StephanAkkerman/FinTwitBERT-sentiment
   - facebook/bart-large-mnli
   - amazon/chronos-t5-large
   ```

4. ✅ Test all model imports
   - Create notebook: `research/notebooks/00_model_validation.ipynb`
   - Load each model
   - Test inference on sample data

**Deliverables**:
- [ ] All dependencies installed
- [ ] API keys configured (FREE sources only)
- [ ] Models downloaded and tested
- [ ] Validation notebook complete

**Blockers**: ~~None - all data sources are FREE~~ ✅

**Cost Savings**: $100/month (skipped X API) + $500/month (skipped Benzinga) = **$600/month saved**

---

#### Day 3-4: DIY News Aggregator (FREE RSS Feeds)
**Goal**: Build custom RSS news aggregator - **NO PAID SERVICES**

**Tasks**:
1. ✅ Create `agents/91_tools/news_aggregator.py`
   ```python
   import feedparser
   import sqlite3
   from datetime import datetime
   
   RSS_FEEDS = {
       'yahoo': 'https://finance.yahoo.com/rss/',
       'seeking_alpha': 'https://seekingalpha.com/market_currents.xml',
       'marketwatch': 'https://www.marketwatch.com/rss/topstories/',
       'investing': 'https://www.investing.com/rss/news.rss',
   }
   
   QUANTUM_KEYWORDS = ['QBTS', 'IONQ', 'RGTI', 'QUBT', 'quantum computing']
   
   class NewsAggregator:
       def fetch_all_feeds(self):
           """Fetch all RSS feeds every 5 minutes"""
       
       def filter_quantum_news(self, entries):
           """Filter for quantum stock mentions"""
       
       def store_articles(self, articles):
           """Store in SQLite, deduplicate by URL"""
       
       def get_recent_news(self, hours=24):
           """Retrieve news from last N hours"""
   ```

2. ✅ Set up SQLite database
   ```sql
   CREATE TABLE news_articles (
       id INTEGER PRIMARY KEY,
       url TEXT UNIQUE,
       title TEXT,
       summary TEXT,
       source TEXT,
       published TIMESTAMP,
       tickers TEXT,  -- JSON array: ["QBTS", "IONQ"]
       sentiment_score REAL,  -- From Agent 22 (finbert)
       created_at TIMESTAMP
   );
   ```

3. ✅ Test RSS aggregator
   - Fetch last 24 hours of news
   - Validate 50+ articles captured
   - Confirm quantum stock mentions detected

**Deliverables**:
- [ ] `news_aggregator.py` complete
- [ ] SQLite database schema created
- [ ] Successfully fetching 50+ articles/day
- [ ] Zero cost (100% free RSS feeds)

**Advantage**: Updates every 5 minutes, no rate limits, no cost!

---

#### Day 4-5: Data Ingestion Module
**Goal**: Create `data_ingestion/` module using Qlib DataHandler pattern

**Tasks**:
1. ✅ Create module structure
   ```
   data_ingestion/
   ├── __init__.py
   ├── data_handler.py          # Qlib DataHandler pattern
   ├── stock_data.py             # yfinance wrapper
   ├── news_data.py              # RSS aggregator integration
   ├── social_data.py            # Reddit PRAW + StockTwits
   ├── macro_data.py             # FRED integration
   ├── processors/               # Data processors (Qlib style)
   │   ├── __init__.py
   │   ├── normalize.py
   │   ├── fillna.py
   │   └── robust_zscore.py
   └── tests/
       └── test_data_handler.py
   ```

2. ✅ Implement `stock_data.py`
   ```python
   class StockDataFetcher:
       def fetch_ohlcv(self, ticker, start_date, end_date):
           """Fetch OHLCV data for ticker using yfinance"""
       
       def fetch_quantum_stocks(self, start_date, end_date):
           """Fetch all 4 quantum stocks (QBTS, IONQ, RGTI, QUBT)"""
   ```

3. ✅ Implement `data_handler.py` (Qlib pattern)
   ```python
   class HERMESDataHandler:
       def __init__(self, instruments, processors):
           """Initialize with stock list and processors"""
       
       def fetch(self, selector):
           """Fetch data using selector pattern"""
       
       def process(self, data):
           """Apply processor chain"""
   ```

4. ✅ Test with quantum stocks
   - Fetch last 6 months of QBTS, IONQ, RGTI, QUBT
   - Validate data quality (no gaps, correct OHLCV)
   - Store in cache (Parquet format)

**Deliverables**:
- [ ] `data_ingestion/` module complete
- [ ] Successfully fetched quantum stock data
- [ ] Data cached locally
- [ ] Unit tests passing

**Blockers**: None (yfinance is free)

---

#### Day 6-7: Agent 22 & 23 Integration
**Goal**: Integrate sentiment models into agent modules

**Tasks**:
1. ✅ Create Agent 22 (Psychology) inference module
   ```python
   # agents/22_psychology/sentiment_analyzer.py
   class FinBERTSentiment:
       def __init__(self):
           self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
           self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
       
       def analyze_news(self, text):
           """Return sentiment: positive/negative/neutral with score"""
   ```

2. ✅ Create Agent 23 (Social) inference module - **FREE DATA SOURCES**
   ```python
   # agents/23_social/social_sentiment.py
   class FinTwitBERTSentiment:
       def __init__(self):
           self.model = AutoModelForSequenceClassification.from_pretrained("StephanAkkerman/FinTwitBERT-sentiment")
           self.tokenizer = AutoTokenizer.from_pretrained("StephanAkkerman/FinTwitBERT-sentiment")
       
       def analyze_reddit_post(self, post_text):
           """Analyze Reddit post sentiment (via PRAW)"""
       
       def analyze_stocktwits_message(self, message):
           """Analyze StockTwits message (via free API)"""
       
       def aggregate_sentiment(self, messages):
           """Aggregate sentiment from multiple messages"""
   ```

3. ✅ Test on real data (FREE SOURCES ONLY)
   - Agent 22: Test on 10 recent RSS news articles (Yahoo Finance)
   - Agent 23: Test on 50 Reddit posts (r/wallstreetbets, r/stocks)
   - Agent 23: Test on 50 StockTwits messages ($QBTS, $IONQ)
   - Validate sentiment accuracy manually

4. ✅ Create notebook
   - `research/notebooks/01_sentiment_validation.ipynb`
   - Compare Agent 22 vs 23 on same text
   - Visualize sentiment distributions
   - Benchmark: RSS vs Reddit vs StockTwits coverage

**Deliverables**:
- [ ] Agent 22 sentiment module working (RSS news)
- [ ] Agent 23 sentiment module working (Reddit + StockTwits)
- [ ] Validation notebook complete
- [ ] Performance benchmarks documented

**Blockers**: None - all data sources free

**Data Sources Used**:
- ✅ RSS feeds (free, no limits)
- ✅ Reddit PRAW (free, 60 req/min)
- ✅ StockTwits API (free, 400 req/hour)
- ❌ ~~X/Twitter~~ (skipped: $100/month)

---

### WEEK 2: Social Data Collection & Orchestration

#### Day 8-10: DIY Social Sentiment Collector (FREE)
**Goal**: Build Reddit + StockTwits data collectors with proper rate limiting

**Tasks**:
1. ✅ Implement Reddit collector with PRAW
   ```python
   # agents/91_tools/reddit_collector.py
   import praw
   import time
   
   class RedditCollector:
       def __init__(self):
           self.reddit = praw.Reddit(
               client_id=os.getenv('REDDIT_CLIENT_ID'),
               client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
               user_agent='HERMES_Quantum v1.0 (by u/YourUsername)'
           )
       
       def fetch_subreddit_mentions(self, ticker, subreddit_name, limit=100):
           """
           Fetch posts mentioning ticker from subreddit
           PRAW handles rate limiting automatically (60 req/min)
           """
           subreddit = self.reddit.subreddit(subreddit_name)
           mentions = []
           
           for post in subreddit.search(ticker, limit=limit, time_filter='day'):
               mentions.append({
                   'title': post.title,
                   'text': post.selftext,
                   'score': post.score,
                   'num_comments': post.num_comments,
                   'created_utc': post.created_utc,
                   'url': post.url
               })
           
           return mentions
       
       def fetch_all_quantum_mentions(self):
           """Fetch mentions of QBTS, IONQ, RGTI, QUBT across multiple subreddits"""
           subreddits = ['wallstreetbets', 'stocks', 'investing', 'QuantumComputing']
           tickers = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
           # ... implementation
   ```

2. ✅ Implement StockTwits collector
   ```python
   # agents/91_tools/stocktwits_collector.py
   import requests
   import time
   
   class StockTwitsCollector:
       def __init__(self):
           self.base_url = 'https://api.stocktwits.com/api/2'
           self.access_token = os.getenv('STOCKTWITS_ACCESS_TOKEN')
       
       def fetch_ticker_stream(self, ticker, limit=30):
           """
           Fetch recent messages for ticker
           Rate limit: 400 requests/hour = 1 request every 9 seconds
           """
           url = f'{self.base_url}/streams/symbol/{ticker}.json'
           headers = {'Authorization': f'Bearer {self.access_token}'}
           
           response = requests.get(url, headers=headers)
           time.sleep(9)  # Rate limiting: 400/hour
           
           if response.status_code == 200:
               messages = response.json()['messages']
               return [{
                   'body': msg['body'],
                   'created_at': msg['created_at'],
                   'sentiment': msg.get('entities', {}).get('sentiment'),
                   'user': msg['user']['username']
               } for msg in messages]
           
           return []
   ```

3. ✅ Set up proper API authentication
   - Reddit: Register app at https://www.reddit.com/prefs/apps
   - StockTwits: Register at https://stocktwits.com/developers/apps/new
   - Store credentials in `.env`

4. ✅ Test data collection
   - Fetch 100 Reddit posts about quantum stocks
   - Fetch 100 StockTwits messages about quantum stocks
   - Verify rate limiting working (no bans)
   - Store in SQLite database

**Deliverables**:
- [ ] `reddit_collector.py` complete with rate limiting
- [ ] `stocktwits_collector.py` complete
- [ ] API credentials configured
- [ ] 200+ social messages collected and stored
- [ ] Zero cost (100% free APIs)

**Advantages**:
- No Twitter/X API cost ($100/month saved)
- Reddit PRAW prevents bans with built-in rate limiting
- StockTwits is financial-focused (better than general Twitter)
- Combined coverage likely better than 333 tweets/day from X

---

#### Day 10-12: Orchestrator Skeleton
**Goal**: Implement Agent 01 using Zipline EventManager pattern

**Tasks**:
1. ✅ Create orchestrator structure
   ```python
   # agents/01_orchestrator/orchestrator.py
   class HERMESOrchestrator:
       def initialize(self):
           """One-time setup (load agents, models)"""
       
       def before_trading_start(self):
           """Daily prep: fetch data, compute factors"""
       
       def handle_data(self, context, data):
           """Real-time: react to market events"""
       
       def analyze(self):
           """Post-mortem: review performance"""
   ```

2. ✅ Implement EventManager
   ```python
   # agents/01_orchestrator/event_manager.py
   class EventManager:
       def schedule_function(self, func, date_rule, time_rule):
           """Schedule agent tasks (Zipline pattern)"""
       
       # Example schedules:
       # - Daily 9:00 AM: Fetch news, run sentiment
       # - Daily 9:30 AM: Compute technical indicators
       # - Daily 3:30 PM: Generate trading signals
       # - Weekly Saturday: Optimize models (Agent 92)
   ```

3. ✅ Create simple workflow
   ```
   1. Fetch data (Agent 91)
   2. Run sentiment (Agents 22, 23)
   3. Compute indicators (Agent 25)
   4. Aggregate signals (Agent 11)
   5. Make decision (Agent 01)
   ```

4. ✅ Test end-to-end
   - Run orchestrator for 1 day
   - Verify all agents called
   - Check output format

**Deliverables**:
- [ ] Orchestrator skeleton complete
- [ ] EventManager working
- [ ] Simple workflow tested
- [ ] Logging and monitoring set up

**Blockers**: None

---

#### Day 11-12: Agent 25 (Market - Technical Analysis)
**Goal**: Integrate Chronos forecaster and pandas_ta indicators

**Tasks**:
1. ✅ Implement technical indicators
   ```python
   # agents/25_market/technical_indicators.py
   import pandas_ta as ta
   
   class TechnicalAnalyzer:
       def compute_indicators(self, ohlcv):
           """Compute 20+ indicators: RSI, MACD, Bollinger, etc."""
           df = ta.add_all_ta_features(ohlcv, ...)
           return df
   ```

2. ✅ Integrate Chronos forecaster
   ```python
   # agents/25_market/price_forecaster.py
   class ChronosForecaster:
       def __init__(self):
           self.model = ChronosPipeline.from_pretrained("amazon/chronos-t5-large")
       
       def forecast(self, historical_prices, horizon=5):
           """Forecast next 5 days of prices"""
   ```

3. ✅ Create RollingGen (Qlib pattern)
   ```python
   # agents/25_market/rolling_gen.py
   class RollingDataGenerator:
       def generate_rolling_features(self, data, window=20):
           """Generate rolling window features"""
   ```

4. ✅ Test on quantum stocks
   - Compute indicators for last 6 months
   - Generate 5-day forecasts
   - Compare forecast vs actual (last week)

**Deliverables**:
- [ ] Technical indicators working
- [ ] Chronos forecaster integrated
- [ ] Rolling features implemented
- [ ] Forecast accuracy measured

**Blockers**: Chronos model is large (~2GB) - ensure enough memory

---

#### Day 13-14: Agent 11 (Analyst - Portfolio)
**Goal**: Integrate PyPortfolioOpt and empyrical-reloaded

**Tasks**:
1. ✅ Implement portfolio optimizer
   ```python
   # agents/11_analyst/portfolio_optimizer.py
   from pypfopt import EfficientFrontier, risk_models, expected_returns
   
   class PortfolioOptimizer:
       def optimize(self, prices):
           """Generate optimal weights for quantum stocks"""
           mu = expected_returns.mean_historical_return(prices)
           S = risk_models.sample_cov(prices)
           ef = EfficientFrontier(mu, S)
           weights = ef.max_sharpe()
           return weights
   ```

2. ✅ Implement performance metrics
   ```python
   # agents/11_analyst/performance_metrics.py
   from empyrical import max_drawdown, sharpe_ratio, sortino_ratio
   
   class PerformanceAnalyzer:
       def compute_metrics(self, returns):
           """Compute Sharpe, Sortino, max drawdown, etc."""
   ```

3. ✅ Create signal aggregator
   ```python
   # agents/11_analyst/signal_aggregator.py
   class SignalAggregator:
       def aggregate(self, signals):
           """Combine signals from agents 22-25"""
           # Weight by agent confidence
           # Resolve conflicts
           # Return buy/sell/hold for each stock
   ```

4. ✅ Test portfolio generation
   - Use last 6 months of data
   - Generate optimal weights
   - Compute expected metrics

**Deliverables**:
- [ ] Portfolio optimizer working
- [ ] Performance metrics implemented
- [ ] Signal aggregation tested
- [ ] Sample portfolio generated

**Blockers**: None

---

## PHASE 2: Advanced Analytics (Weeks 3-4)

### WEEK 3: Factor Analysis & Agent 24

#### Day 15-17: Pipeline API Implementation
**Goal**: Implement Zipline Pipeline pattern for factor computation

**Tasks**:
1. ✅ Create Pipeline engine
   ```python
   # core/pipeline_engine.py
   class PipelineEngine:
       def run_pipeline(self, pipeline, start, end):
           """Execute factor computation pipeline"""
   ```

2. ✅ Create base Factor classes
   ```python
   # library/factors/base.py
   class Factor:
       def compute(self, data):
           """Abstract method for factor computation"""
   
   # Agent-specific factors:
   class SentimentFactor(Factor):       # Agent 22
   class SocialSentimentFactor(Factor): # Agent 23
   class PolicyFactor(Factor):          # Agent 24
   class TechnicalFactor(Factor):       # Agent 25
   ```

3. ✅ Implement agent factors
   - Agent 22: News sentiment factor
   - Agent 23: Social media sentiment factor
   - Agent 24: Policy risk factor
   - Agent 25: Technical momentum factor

4. ✅ Create factor validation notebook
   - Compute factors for last 6 months
   - Analyze factor correlations
   - Visualize factor evolution

**Deliverables**:
- [ ] Pipeline engine working
- [ ] All agent factors implemented
- [ ] Factor validation complete
- [ ] Correlation analysis done

---

#### Day 18-19: Agent 24 (Politics) Integration
**Goal**: Integrate BART zero-shot classifier for policy news

**Tasks**:
1. ✅ Implement BART classifier
   ```python
   # agents/24_politics/policy_classifier.py
   class BARTPolicyClassifier:
       def __init__(self):
           self.model = pipeline("zero-shot-classification", 
                                 model="facebook/bart-large-mnli")
       
       def classify_news(self, text, labels):
           """Classify news into policy categories"""
   ```

2. ✅ Define policy categories
   - Government funding announcements
   - Export controls / national security
   - Regulatory changes
   - Research grants
   - International competition

3. ✅ Create policy risk scorer
   ```python
   class PolicyRiskScorer:
       def score_risk(self, classifications):
           """Convert classifications to risk score"""
   ```

4. ✅ Test on policy news
   - Collect 20 policy-related articles
   - Classify using BART
   - Validate classifications manually

**Deliverables**:
- [ ] BART classifier working
- [ ] Policy categories defined
- [ ] Risk scorer implemented
- [ ] Classification accuracy validated

---

#### Day 20-21: alphalens Integration
**Goal**: Integrate alphalens-reloaded for factor validation

**Tasks**:
1. ✅ Install and configure
   ```bash
   pip install alphalens-reloaded
   ```

2. ✅ Create factor validation pipeline
   ```python
   # library/factors/validator.py
   from alphalens import tears
   
   class FactorValidator:
       def validate_factor(self, factor_data, prices):
           """Run alphalens analysis on factor"""
           tears.create_full_tear_sheet(factor_data, prices)
   ```

3. ✅ Validate all agent factors
   - Agent 22 sentiment factor
   - Agent 23 social factor
   - Agent 24 policy factor
   - Agent 25 technical factors

4. ✅ Generate factor reports
   - IC (information coefficient)
   - Returns analysis
   - Turnover analysis

**Deliverables**:
- [ ] alphalens integration complete
- [ ] All factors validated
- [ ] Factor performance reports generated
- [ ] Poor factors identified for improvement

---

### WEEK 4: Agent 92 & Risk Management

#### Day 22-24: Agent 92 Implementation (Part 1)
**Goal**: Implement performance monitoring and drift detection

**Tasks**:
1. ✅ Create performance monitor
   ```python
   # agents/92_optimizer/performance_monitor.py
   class PerformanceMonitor:
       def monitor_agent(self, agent_id, metrics):
           """Track agent performance over time"""
       
       def detect_drift(self, agent_id):
           """Detect performance degradation"""
       
       def alert(self, agent_id, issue):
           """Alert orchestrator of issues"""
   ```

2. ✅ Set up metrics database
   - SQLite or PostgreSQL
   - Schema: agent_id, model_name, metric, value, timestamp
   - Store daily performance

3. ✅ Implement drift detection
   - Statistical tests (KS test, PSI)
   - Rolling window comparison
   - Threshold-based alerts

4. ✅ Create monitoring dashboard
   - Jupyter notebook or Streamlit app
   - Visualize agent performance
   - Show drift alerts

**Deliverables**:
- [ ] Performance monitor working
- [ ] Metrics stored in database
- [ ] Drift detection functional
- [ ] Dashboard created

---

#### Day 25-26: Agent 92 Implementation (Part 2)
**Goal**: Implement hyperparameter tuning with Optuna

**Tasks**:
1. ✅ Create Optuna tuner
   ```python
   # agents/92_optimizer/hyperparameter_tuner.py
   import optuna
   
   class OptunaHyperTuner:
       def optimize(self, model, train_data, val_data):
           """Run Optuna optimization"""
   ```

2. ✅ Define search spaces
   - Agent 22 finbert: learning_rate, dropout, batch_size
   - Agent 23 FinTwitBERT: similar
   - Agent 25 Chronos: context_length, temperature

3. ✅ Run optimization for Agent 22
   - 100 trials
   - Early stopping
   - Track with W&B (optional)

4. ✅ Test optimized model
   - Compare baseline vs optimized
   - Measure performance improvement

**Deliverables**:
- [ ] Optuna tuner working
- [ ] Agent 22 optimized
- [ ] Performance improvement documented
- [ ] Optimization framework reusable

---

#### Day 27-28: Risk Management & pyfolio
**Goal**: Integrate pyfolio-reloaded for comprehensive risk analysis

**Tasks**:
1. ✅ Install and configure
   ```bash
   pip install pyfolio-reloaded
   ```

2. ✅ Create risk analyzer
   ```python
   # agents/11_analyst/risk_analyzer.py
   import pyfolio as pf
   
   class RiskAnalyzer:
       def create_tearsheet(self, returns):
           """Generate pyfolio tearsheet"""
           pf.create_full_tear_sheet(returns)
   ```

3. ✅ Simulate portfolio performance
   - Use last 6 months
   - Apply Agent 11 portfolio weights
   - Compute returns

4. ✅ Generate risk reports
   - Drawdown analysis
   - Rolling metrics
   - Factor exposures

**Deliverables**:
- [ ] pyfolio integrated
- [ ] Risk analyzer working
- [ ] Portfolio simulation complete
- [ ] Risk reports generated

---

## PHASE 3: Multi-Agent & RL (Weeks 5-6)

### WEEK 5: OnlineManager & Coordination

#### Day 29-31: OnlineManager Implementation
**Goal**: Implement Qlib OnlineManager for multi-agent coordination

**Tasks**:
1. ✅ Create OnlineManager
   ```python
   # agents/01_orchestrator/online_manager.py
   class OnlineManager:
       def __init__(self, workflow_config):
           """Initialize with workflow DAG"""
       
       def run(self):
           """Execute multi-agent workflow"""
       
       def handle_task_failure(self, task_id):
           """Graceful degradation"""
   ```

2. ✅ Define workflow DAG
   ```yaml
   # config/workflow.yaml
   workflow:
     - stage: data_collection
       agents: [91]
     - stage: sentiment_analysis
       agents: [22, 23, 24]
       parallel: true
     - stage: technical_analysis
       agents: [25]
     - stage: aggregation
       agents: [11]
     - stage: decision
       agents: [01]
   ```

3. ✅ Implement task queue
   - Redis or in-memory queue
   - Retry logic
   - Error handling

4. ✅ Test full workflow
   - Run end-to-end
   - Verify agent coordination
   - Check error handling

**Deliverables**:
- [ ] OnlineManager working
- [ ] Workflow DAG defined
- [ ] Task queue operational
- [ ] Full workflow tested

---

#### Day 32-33: Inter-Agent Communication
**Goal**: Implement message passing and shared library

**Tasks**:
1. ✅ Create shared library (context pool)
   ```python
   # library/shared_library.py
   class SharedLibrary:
       def put(self, agent_id, key, value):
           """Agent writes to library"""
       
       def get(self, key):
           """Agent reads from library"""
   ```

2. ✅ Implement message passing
   ```python
   # core/message_bus.py
   class MessageBus:
       def publish(self, topic, message):
           """Publish message to topic"""
       
       def subscribe(self, topic, callback):
           """Subscribe to topic"""
   ```

3. ✅ Update agents to use shared library
   - Agent 22-25 write to library
   - Agent 11 reads from library
   - Agent 01 coordinates

4. ✅ Test communication
   - Verify data flow
   - Check for race conditions
   - Measure latency

**Deliverables**:
- [ ] Shared library working
- [ ] Message bus operational
- [ ] Agents updated
- [ ] Communication tested

---

#### Day 34-35: Agent 99 Registry Implementation
**Goal**: Implement Qlib-style model registry

**Tasks**:
1. ✅ Create model registry
   ```python
   # agents/99_models/model_registry.py
   class ModelRegistry:
       def register_model(self, name, version, metadata):
           """Register model version"""
       
       def get_model(self, name, version=None):
           """Retrieve model (latest if version=None)"""
       
       def list_models(self):
           """List all registered models"""
   ```

2. ✅ Integrate with Agent 92
   - Agent 92 optimizes and uploads
   - Agent 99 stores and versions
   - Orchestrator deploys from registry

3. ✅ Implement model metadata
   - Performance metrics
   - Training data info
   - Hyperparameters used

4. ✅ Create registry UI (optional)
   - Web interface to browse models
   - Compare model versions

**Deliverables**:
- [ ] Model registry working
- [ ] Integration with Agent 92 complete
- [ ] Metadata stored
- [ ] All 4 models registered

---

### WEEK 6: RL Training & Backtesting

#### Day 36-38: TensorTrade Integration
**Goal**: Integrate TensorTrade for RL training

**Tasks**:
1. ✅ Install TensorTrade
   ```bash
   pip install tensortrade
   ```

2. ✅ Create trading environment
   ```python
   # agents/99_models/rl/trading_env.py
   from tensortrade.env import TradingEnv
   
   class QuantumStockEnv(TradingEnv):
       """Custom env for quantum stocks"""
   ```

3. ✅ Implement RL agent
   - PPO or A2C algorithm
   - Observation space: technical indicators + sentiment
   - Action space: buy/sell/hold for each stock

4. ✅ Train RL agent
   - Use last 6 months as training data
   - Train for 100k steps
   - Save checkpoints

**Deliverables**:
- [ ] TensorTrade environment created
- [ ] RL agent implemented
- [ ] Training complete
- [ ] Trained model saved

---

#### Day 39-40: Zipline Backtesting
**Goal**: Full Zipline backtesting integration

**Tasks**:
1. ✅ Set up Zipline environment
   ```bash
   pip install zipline-reloaded
   ```

2. ✅ Create backtest script
   ```python
   # scripts/backtest.py
   from zipline.api import order_target_percent, record
   
   def initialize(context):
       """Set up backtest"""
   
   def handle_data(context, data):
       """Run HERMES agents, execute trades"""
   ```

3. ✅ Run backtest
   - Last 6 months
   - HERMES system vs buy-and-hold
   - Compute performance metrics

4. ✅ Generate backtest report
   - pyfolio tearsheet
   - Trade log
   - Performance summary

**Deliverables**:
- [ ] Zipline backtest working
- [ ] Backtest results documented
- [ ] Performance comparison complete
- [ ] Report generated

---

#### Day 41-42: Final Integration & Testing
**Goal**: End-to-end system test and documentation

**Tasks**:
1. ✅ Full system test
   - Run HERMES for 1 week simulation
   - Verify all agents working
   - Check performance

2. ✅ Create system documentation
   - Architecture diagram
   - API documentation
   - User guide

3. ✅ Performance benchmarking
   - Measure latency per agent
   - Memory usage
   - Bottleneck identification

4. ✅ Deploy Phase 1 version
   - Tag git release
   - Create Docker image
   - Deploy to production (paper trading)

**Deliverables**:
- [ ] Full system tested
- [ ] Documentation complete
- [ ] Benchmarks documented
- [ ] Phase 1 deployed

---

## PART 4: PRIORITY SUMMARY

### Critical Path (Must Complete)

1. **Week 1**: Data ingestion + Model integration (Agents 22, 23, 25)
2. **Week 2**: Orchestrator + Agent 11 portfolio
3. **Week 3**: Factor validation + Agent 24
4. **Week 4**: Agent 92 monitoring + Risk management
5. **Week 5**: Multi-agent coordination
6. **Week 6**: Backtesting & deployment

### High Priority (Should Complete)

- All 9 agents functional
- End-to-end workflow tested
- Backtesting validated
- Agent 92 monitoring operational

### Medium Priority (Nice to Have)

- RL training (can defer to Phase 4)
- Advanced AutoML (Agent 92 Phase 2)
- Extensive factor library

### Low Priority (Future Phases)

- Live trading (start with paper)
- Mobile/web dashboard
- Multi-portfolio support

---

## PART 5: RISK MITIGATION

### Technical Risks

1. **Twitter API Cost** ($100/month)
   - **Mitigation**: Start with free alternatives (Reddit, StockTwits)
   - **Fallback**: Use cached historical tweets for testing

2. **Model Inference Speed**
   - **Risk**: Chronos is large (2GB), slow inference
   - **Mitigation**: Optimize with quantization, caching
   - **Fallback**: Use smaller chronos-t5-base

3. **Data Quality**
   - **Risk**: yfinance may have gaps or delays
   - **Mitigation**: Validate data, use multiple sources
   - **Fallback**: Alpha Vantage as backup

### Operational Risks

1. **Scope Creep**
   - **Mitigation**: Strict adherence to 6-week plan
   - **Strategy**: Defer non-critical features to Phase 4

2. **Agent Coordination Complexity**
   - **Risk**: Multi-agent workflows hard to debug
   - **Mitigation**: Extensive logging, monitoring dashboards
   - **Strategy**: Build incrementally, test each agent independently

3. **Performance Issues**
   - **Risk**: System too slow for real-time trading
   - **Mitigation**: Profile early, optimize hot paths
   - **Strategy**: Start with daily updates, scale to intraday later

---

## PART 6: SUCCESS METRICS

### Phase 1 (Weeks 1-2)
- ✅ All 4 models integrated and tested
- ✅ Data ingestion working for all quantum stocks
- ✅ Orchestrator coordinates 2+ agents
- ✅ Portfolio optimizer generates valid weights

### Phase 2 (Weeks 3-4)
- ✅ Pipeline API computes factors
- ✅ Agent 92 detects model drift
- ✅ Risk analysis reports generated
- ✅ Agent 24 classifies policy news

### Phase 3 (Weeks 5-6)
- ✅ All 9 agents operational
- ✅ Backtest shows positive returns
- ✅ System runs end-to-end
- ✅ Ready for paper trading

### Long-term (6 months)
- System beats buy-and-hold on quantum stocks
- Agent 92 improves model performance by 5%+
- Zero critical bugs in production
- Expand to additional stocks

---

## CONCLUSION

**Current Status**: Phase 0 complete with excellent foundation  
**Next Action**: Begin Week 1, Day 1 - Install dependencies  
**Confidence Level**: HIGH - Clear plan, proven tools, solid research

**Key Strengths**:
1. Thorough Phase 0 research (17,500+ lines)
2. Production-ready models adopted
3. Dual framework approach (Qlib + Zipline)
4. Agent 92 for continuous improvement

**Key Challenges**:
1. Twitter API cost
2. Multi-agent coordination complexity
3. Model inference performance

**Recommendation**: **PROCEED** with Phase 1 implementation following this plan.

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-28  
**Next Review**: After Week 2 completion
