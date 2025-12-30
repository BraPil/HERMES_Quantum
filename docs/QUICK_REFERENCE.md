# Quick Reference: Environment Variables & API Keys

**Repository**: BraPil/HERMES_Quantum  
**Last Updated**: December 30, 2025

---

## 🔑 Required API Keys (All FREE)

### Reddit API (PRAW)
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=HERMES_Quantum v1.0 (by u/YourUsername)
```

**Setup**:
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" → "script"
3. Copy `client_id` and `client_secret`

**Rate Limit**: 60 requests/minute (PRAW handles automatically)

---

### StockTwits API
```bash
STOCKTWITS_ACCESS_TOKEN=your_access_token
```

**Setup**:
1. Go to https://stocktwits.com/developers/apps/new
2. Register app
3. Copy access token

**Rate Limit**: 400 requests/hour

---

### SEC Edgar (No Auth Required)
```bash
SEC_USER_AGENT=HERMES_Quantum/1.0 (your-email@example.com)
```

**Note**: Only needs User-Agent header for rate limit compliance

---

### Finnhub.io (Optional)
```bash
FINNHUB_API_KEY=your_api_key
```

**Setup**:
1. Sign up at https://finnhub.io/register
2. Free tier: 60 calls/min

**Status**: Optional backup for news

---

### FRED (Optional, Macro Data)
```bash
FRED_API_KEY=your_api_key
```

**Setup**:
1. Sign up at https://fred.stlouisfed.org/
2. Free unlimited API access

**Status**: For Agent 24 (politics) macro indicators

---

## 🚫 Not Using (Cost Savings)

### X/Twitter API - $100/month
**Why Skipped**: Only 333 posts/day on Basic tier  
**Alternative**: Reddit PRAW (free, better discussions)

### Benzinga - $500+/month
**Why Skipped**: Expensive for small-scale bot  
**Alternative**: RSS feeds (Yahoo, MarketWatch, SeekingAlpha)

### NewsAPI.org - $449/month
**Why Skipped**: Free tier only 100 requests/day  
**Alternative**: RSS feeds (unlimited, free)

**Total Savings**: $600+/month

---

## 📦 Python Packages (Week 2 Setup)

### Core ML
```bash
torch==2.9.1+cpu          # Use +cu121 for CUDA after cleanup
transformers==4.57.3
chronos-forecasting==2.2.2
scikit-learn==1.8.0
```

### Data & Finance
```bash
yfinance==1.0
pandas==2.3.3
numpy==2.2.6
scipy==1.16.3
pandas-ta==0.4.71b0
```

### Portfolio Optimization
```bash
PyPortfolioOpt==1.5.6
empyrical-reloaded==0.5.12
cvxpy==1.7.5
```

### Data Collection
```bash
feedparser==6.0.12
praw==7.8.1
requests==2.32.5
beautifulsoup4==4.14.3
```

### Install Command (After Cleanup)
```bash
# CPU-only (current, 184MB)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# CUDA (recommended after cleanup, 900MB)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# All other packages
pip install transformers yfinance pandas-ta PyPortfolioOpt empyrical-reloaded feedparser praw chronos-forecasting
```

---

## 🗂️ .env.example Template

```bash
# ============================================
# HERMES_Quantum Environment Variables
# ============================================
# Copy to .env and fill in your values

# ---------- Reddit API (PRAW) ----------
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=HERMES_Quantum v1.0 (by u/YourUsername)

# ---------- StockTwits API ----------
STOCKTWITS_ACCESS_TOKEN=your_access_token_here

# ---------- SEC Edgar ----------
SEC_USER_AGENT=HERMES_Quantum/1.0 (your-email@example.com)

# ---------- Optional APIs ----------
# Finnhub (News backup, optional)
# FINNHUB_API_KEY=your_api_key_here

# FRED (Macro data, optional)
# FRED_API_KEY=your_api_key_here

# ---------- Database ----------
DATABASE_PATH=outputs/data/hermes.db

# ---------- Logging ----------
LOG_LEVEL=INFO
LOG_PATH=logs/

# ---------- Trading (Future) ----------
# TRADING_MODE=paper  # paper or live
# BROKER_API_KEY=your_broker_api_key_here
```

---

## 🔧 Quick Setup Commands

### 1. Clone Repo Locally
```powershell
# Windows PowerShell
cd C:\Users\kidsg\Documents
git clone https://github.com/BraPil/HERMES_Quantum.git
cd HERMES_Quantum
```

### 2. Setup Python Environment (Local)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create .env File
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Verify Installation
```bash
python -c "import torch, transformers, yfinance; print('All packages working!')"
```

---

## 📊 Database Schema (SQLite)

### news_articles Table
```sql
CREATE TABLE news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    published TIMESTAMP,
    source TEXT,
    summary TEXT,
    content TEXT,
    tickers TEXT,  -- JSON array of mentioned tickers
    sentiment REAL,  -- -1 to 1
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### social_posts Table
```sql
CREATE TABLE social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT,  -- 'reddit' or 'stocktwits'
    post_id TEXT UNIQUE,
    author TEXT,
    content TEXT,
    ticker TEXT,
    sentiment TEXT,  -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    confidence REAL,
    created_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 Quick Test Commands

### Test Agent 22 (Sentiment)
```bash
python agents/22_psychology/sentiment_analyzer.py
```

### Test Agent 25 (Forecasting)
```bash
python agents/25_market/forecaster.py
```

### Test Agent 11 (Portfolio)
```bash
python agents/11_analyst/portfolio_optimizer.py
```

### Integration Test (Real Data)
```bash
python tests/test_quick_integration.py
```

### Fetch Latest News
```bash
python agents/91_tools/news_aggregator.py
```

---

## 🐛 Troubleshooting

### Import Errors After pip install
```bash
# Reload VS Code window
# Ctrl+Shift+P → "Developer: Reload Window"
```

### Disk Space Full
```bash
# Check usage
df -h /workspaces

# Clean up
rm -rf .venv
rm -rf ~/.cache/pip
rm -rf outputs/data/stock_cache/*
```

### yfinance Rate Limit
```python
# Use delays between requests
import time
for ticker in tickers:
    data = yf.download(ticker)
    time.sleep(1)  # Avoid rate limits
```

### PyTorch CPU Too Slow
```bash
# Reinstall with CUDA (needs 900MB free space)
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 📝 Notes

- All API keys listed are FREE tier
- No credit card required for any service
- Total cost: $0/month
- Data latency: 5-15 minutes (acceptable for swing trading)
- Storage: ~1GB (local), ~30GB (codespace with ML models)

---

**Status**: Ready for Agent 01 implementation  
**Last Verified**: December 30, 2025
