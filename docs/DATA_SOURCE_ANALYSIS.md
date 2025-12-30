# Data Source Analysis & Cost-Benefit Evaluation

**Analysis Date**: 2025-12-28  
**Purpose**: Evaluate data sources for HERMES_Quantum trading system  
**Conclusion**: DIY-first strategy saves $600+/month while providing equal/better coverage

---

## Executive Summary

**Key Findings**:
1. ✅ **X/Twitter API**: $100/month for only 333 posts/day → **SKIP**
2. ✅ **Benzinga News**: $500+/month → **SKIP** (use free RSS feeds)
3. ✅ **Reddit PRAW**: FREE with proper rate limiting (60 req/min)
4. ✅ **StockTwits**: FREE API (400 req/hour), financial-focused
5. ✅ **RSS Feeds**: FREE, unlimited, 5-minute updates (Yahoo, Seeking Alpha, MarketWatch)
6. ⏸️ **Options Flow**: Start with DIY CBOE delayed data, evaluate Unusual Whales ($50/mo) later

**Total Cost Savings**: $600/month (X + Benzinga avoided)  
**Coverage**: Equal or better than paid alternatives  
**Implementation**: Weeks 1-2 (free sources only)

---

## Platform Clarifications (Dec 2025)

### 1. Twitter → X Rebranding (2023)

**Current State**:
- Platform rebranded to "X" in July 2023
- API now called "X API" (formerly Twitter API v2)
- Company: X Corp. (formerly Twitter Inc.)

**API Pricing** (as of Dec 2025):
- **Free tier**: REMOVED (was 1,500 tweets/month, discontinued 2023)
- **Basic tier**: $100/month
  - 10,000 posts per month (≈333 posts/day)
  - Read-only access
  - 1 environment
- **Pro tier**: $5,000/month
  - 1,000,000 posts per month
  - Read + write access
- **Enterprise**: Custom pricing ($42,000+/year)

**Assessment for HERMES_Quantum**:
- ❌ **Poor value**: $100/month for 333 posts/day is limiting
- ❌ **No write access**: Basic tier is read-only (can't post)
- ❌ **Better alternatives exist**: Reddit + StockTwits are free
- **Verdict**: **SKIP X API entirely**

---

### 2. StockTwits (Independent Platform)

**Clarification**: StockTwits is **NOT** part of Reddit or Twitter

**Company**: StockTwits Inc. (acquired by Rocket Companies in 2023)  
**Focus**: Financial social network (stocks, crypto)  
**Users**: 6+ million retail investors and traders

**API Details**:
- **Free tier**: 400 requests/hour (with authentication)
- **Endpoints**:
  - Symbol streams: `/streams/symbol/{ticker}.json`
  - Trending stocks: `/streams/trending.json`
  - User streams: `/streams/user/{user_id}.json`
- **Data includes**: Message text, sentiment labels, timestamps, user info
- **Rate limiting**: 1 request every 9 seconds (400/hour)

**Authentication**:
1. Register app: https://stocktwits.com/developers/apps/new
2. Get access token
3. Use in headers: `Authorization: Bearer {token}`

**Assessment for HERMES_Quantum**:
- ✅ **Excellent value**: Free, financial-focused, 400 req/hour sufficient
- ✅ **Quality**: Users are investors (not general public like Twitter)
- ✅ **Sentiment labels**: Many messages have pre-labeled sentiment
- **Verdict**: **HIGH PRIORITY for Agent 23**

---

### 3. Reddit API (Proper Usage)

**Why Users Get Banned**:
- Exceeding rate limits (60 requests/minute for authenticated users)
- Missing User-Agent header
- Not using OAuth2 properly
- Making requests too fast without delays

**Solution: PRAW Library** (Python Reddit API Wrapper)

**PRAW Benefits**:
- ✅ Built-in rate limiting (prevents bans automatically)
- ✅ OAuth2 handling simplified
- ✅ Proper User-Agent management
- ✅ Request queueing (waits when limit reached)

**Setup**:
```python
import praw

reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',          # From https://www.reddit.com/prefs/apps
    client_secret='YOUR_CLIENT_SECRET',
    user_agent='HERMES_Quantum v1.0 (by u/YourUsername)'  # CRITICAL: descriptive user agent
)

# PRAW handles rate limiting automatically - no manual delays needed!
subreddit = reddit.subreddit('wallstreetbets')
for post in subreddit.search('QBTS', limit=100):
    print(post.title)  # No risk of ban - PRAW queues requests
```

**Rate Limits**:
- 60 requests per minute (authenticated)
- 10 requests per minute (unauthenticated) - DON'T USE
- PRAW enforces these automatically

**Best Subreddits for Quantum Stocks**:
- r/wallstreetbets (2.8M members) - high volume
- r/stocks (6M members) - quality discussions
- r/investing (2.5M members) - long-term views
- r/QuantumComputing (50K members) - industry insights
- r/IONQ (small but dedicated)

**Assessment for HERMES_Quantum**:
- ✅ **Free**: No API costs
- ✅ **High quality**: Better discussions than Twitter
- ✅ **No bans**: PRAW prevents rate limit issues
- **Verdict**: **HIGH PRIORITY for Agent 23**

---

### 4. News Services Comparison

#### Benzinga (Still Exists, Expensive)

**Pricing**:
- **Pro**: $55/month (delayed data, basic news)
- **Premium**: $360/month (real-time squawks, exclusive news)
- **Squawk Broadcast**: $500+/month (audio + text real-time alerts)

**Assessment**: Not worth it for small-scale bot

#### Better Alternatives

| Service | Cost | Speed | Coverage | Rate Limit | Verdict |
|---------|------|-------|----------|------------|---------|
| **RSS Feeds** | FREE | 5-15min delay | Excellent | None | **BEST** ✅ |
| **Finnhub.io** | FREE tier | Real-time | Good | 60/min | **Good** ✅ |
| **Alpha Vantage** | FREE tier | Near real-time | Limited | 25/day | **Backup** ⚠️ |
| **NewsAPI.org** | $449/mo | Real-time | Excellent | Unlimited | **Skip** ❌ |
| **Benzinga** | $500+/mo | Real-time | Excellent | Unlimited | **Skip** ❌ |

**RSS Feed Sources** (Recommended):
```python
RSS_FEEDS = {
    'yahoo_finance': 'https://finance.yahoo.com/rss/',
    'seeking_alpha': 'https://seekingalpha.com/market_currents.xml',
    'marketwatch': 'https://www.marketwatch.com/rss/topstories/',
    'marketwatch_tech': 'https://www.marketwatch.com/rss/technology/',
    'investing_news': 'https://www.investing.com/rss/news.rss',
    'investing_stock_news': 'https://www.investing.com/rss/news_285.rss',
    'sec_filings': 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=exclude&start=0&count=100&output=atom',
}
```

**RSS Advantages**:
- ✅ No rate limits
- ✅ No authentication needed
- ✅ Updates every 5-15 minutes (fast enough for trading)
- ✅ Can poll multiple sources simultaneously
- ✅ Parse with `feedparser` library (simple)

**Verdict**: **DIY RSS aggregation** saves $500+/month

---

### 5. Options Flow & Heatmap Services

#### Bookmap

**Current Status**: Still exists, pivoted to crypto focus  
**Pricing**: $49-99/month (depending on exchange data)  
**Focus**: Order flow visualization, mainly BTC/ETH now  
**Assessment**: Not ideal for stock options anymore

#### Alternatives for Stock Options

| Service | Cost | Data Type | Quality | Verdict |
|---------|------|-----------|---------|---------|
| **Unusual Whales** | $50/mo | Real-time options flow | Excellent | **Consider** ⚠️ |
| **FlowAlgo** | $167/mo | Premium options flow | Excellent | **Too expensive** ❌ |
| **CBOE Delayed** | FREE | OI, volume (15min delay) | Good | **DIY MVP** ✅ |
| **TradingView** | $60/mo | Technical + some options | Good | **Skip** ❌ |

#### DIY Options Tracker (Recommended for MVP)

**What's Possible with Free Data**:
```python
import yfinance as yf

def track_options_activity(ticker):
    """
    Track using yfinance (15-minute delayed CBOE data)
    """
    stock = yf.Ticker(ticker)
    
    # Get options chain for next 3 expiries
    options_dates = stock.options[:3]
    
    for date in options_dates:
        opt_chain = stock.option_chain(date)
        calls = opt_chain.calls
        puts = opt_chain.puts
        
        # Metrics you CAN calculate:
        # 1. Put/Call Ratio (open interest)
        # 2. Most active strikes (volume)
        # 3. OI changes day-over-day
        # 4. IV rank (compare current IV to historical)
        # 5. Max pain (strike with most OI)
        
        # What you CAN'T get (need paid service):
        # 1. Real-time flow (who's buying/selling right now)
        # 2. Block trades (large institutional orders)
        # 3. Bid/ask spread changes
        # 4. Order book depth heatmaps
```

**DIY Heatmap Example**:
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Track OI by strike and expiry
# Build heatmap showing where the "action" is
# Not real-time but identifies trends over days/weeks
```

**When to Upgrade to Paid**:
- If options flow proves highly predictive in backtests
- After validating DIY tracker provides value
- When trading live (real-time matters)
- **Recommendation**: Defer to Phase 2 (Week 4-6)

---

## Final Data Source Stack (Recommended)

### Week 1-2 Implementation (All FREE)

| Data Type | Source | Cost | Agent | Priority |
|-----------|--------|------|-------|----------|
| **Stock Prices** | yfinance | FREE | 25, 11 | **CRITICAL** |
| **News** | RSS Feeds | FREE | 22 | **CRITICAL** |
| **Social (Reddit)** | PRAW | FREE | 23 | **HIGH** |
| **Social (Financial)** | StockTwits API | FREE | 23 | **HIGH** |
| **Earnings/Filings** | SEC Edgar API | FREE | 22, 24 | **HIGH** |
| **Macro Data** | FRED API | FREE | 24, 11 | **MEDIUM** |
| **Options (Delayed)** | yfinance/CBOE | FREE | 11, 25 | **MEDIUM** |
| **Alt News** | Finnhub.io Free | FREE | 22 | **LOW** |

### Week 5-6 Evaluation (If Needed)

| Data Type | Source | Cost | Only If... |
|-----------|--------|------|------------|
| **Options Flow** | Unusual Whales | $50/mo | Options predictive in backtests |
| **Real-Time Stocks** | Polygon.io | $199/mo | Need sub-minute data (unlikely) |
| **Premium News** | NewsAPI.org | $449/mo | RSS coverage insufficient (unlikely) |

**Total Week 1-2 Cost**: $0/month  
**Potential Phase 2 Cost**: $0-50/month (only if Unusual Whales justified)  
**Cost Avoided**: $600+/month (X API + Benzinga)

---

## Implementation Checklist

### Week 1, Day 1-2: API Setup (FREE sources only)

- [ ] **Reddit PRAW**
  - [ ] Register app: https://www.reddit.com/prefs/apps
  - [ ] Get `client_id` and `client_secret`
  - [ ] Add to `.env`: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
  - [ ] Test with PRAW to verify no rate limit issues

- [ ] **StockTwits**
  - [ ] Register app: https://stocktwits.com/developers/apps/new
  - [ ] Get access token
  - [ ] Add to `.env`: `STOCKTWITS_ACCESS_TOKEN`
  - [ ] Test fetching `/streams/symbol/QBTS.json`

- [ ] **SEC Edgar** (no auth needed)
  - [ ] Set User-Agent: `HERMES_Quantum/1.0 (your-email@example.com)`
  - [ ] Test RSS feed: https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&output=atom

- [ ] **Finnhub.io** (optional)
  - [ ] Sign up: https://finnhub.io/register
  - [ ] Get free API key
  - [ ] Add to `.env`: `FINNHUB_API_KEY`
  - [ ] Test: 60 calls/min limit

- [ ] **FRED** (optional, for macro data)
  - [ ] Sign up: https://fred.stlouisfed.org/
  - [ ] Get API key
  - [ ] Add to `.env`: `FRED_API_KEY`

### Week 1, Day 3-4: Build Data Collectors

- [ ] **RSS News Aggregator** (`agents/91_tools/news_aggregator.py`)
  - [ ] Parse 5+ RSS feeds
  - [ ] Filter for quantum stock keywords
  - [ ] Store in SQLite with deduplication
  - [ ] Update every 5 minutes (cron job)

- [ ] **Reddit Collector** (`agents/91_tools/reddit_collector.py`)
  - [ ] Use PRAW (automatic rate limiting)
  - [ ] Search 5 subreddits for quantum tickers
  - [ ] Collect 100+ posts/day
  - [ ] Store in SQLite

- [ ] **StockTwits Collector** (`agents/91_tools/stocktwits_collector.py`)
  - [ ] Fetch symbol streams for 4 quantum stocks
  - [ ] Rate limit: 1 request every 9 seconds
  - [ ] Collect 100+ messages/day
  - [ ] Store in SQLite

### Week 2, Day 6-7: Sentiment Analysis

- [ ] **Agent 22**: Pass RSS news to finbert model
- [ ] **Agent 23**: Pass Reddit/StockTwits to FinTwitBERT model
- [ ] **Validate**: Manually check 50 sentiment classifications
- [ ] **Benchmark**: Compare coverage vs hypothetical X API (333 posts/day)

### Week 5-6: Evaluate Gaps (Optional Upgrades)

- [ ] **Review data coverage**: Is free data sufficient?
- [ ] **Identify gaps**: Real-time options flow? Faster news?
- [ ] **Cost-benefit**: Would $50/month Unusual Whales improve performance?
- [ ] **Decision**: Upgrade only if backtests show clear ROI

---

## Conclusion

**DIY-First Strategy Advantages**:
1. ✅ $600+/month cost savings (X + Benzinga avoided)
2. ✅ Equal or better coverage (Reddit + StockTwits + RSS)
3. ✅ No vendor lock-in (own the data pipeline)
4. ✅ Customizable (filter for quantum stocks only)
5. ✅ Learning opportunity (build data engineering skills)

**When to Consider Paid Services**:
- ⏸️ After validating free sources insufficient in backtests
- ⏸️ When trading live and milliseconds matter (unlikely for swing trading)
- ⏸️ When scaling to 100+ stocks (may hit rate limits)

**Recommendation**: Start with 100% free stack (Weeks 1-4), evaluate paid options in Week 5+ only if data gaps emerge.

---

**Last Updated**: 2025-12-28  
**Next Review**: Week 5 (evaluate if paid services needed)
