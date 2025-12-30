# 🔗 Quick Links - HERMES_Quantum

**Last Updated**: December 30, 2025  
**Commit**: `98ca594`

---

## 📂 Essential Documents

### For Restart
1. **[PERFECT_RESTART_PROMPT.md](PERFECT_RESTART_PROMPT.md)** ⭐  
   → Copy-paste this entire file when restarting

2. **[RESTART_STATE_2025-12-30.md](RESTART_STATE_2025-12-30.md)**  
   → Complete session state and context

3. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**  
   → API keys, commands, troubleshooting

### Progress Reports
4. **[WEEK2_PROGRESS.md](WEEK2_PROGRESS.md)**  
   → Week 2 detailed results (+295% alpha!)

5. **[WEEK1_COMPLETE.md](WEEK1_COMPLETE.md)**  
   → Week 1 summary (data infrastructure)

### Planning
6. **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)**  
   → Full 6-week roadmap

7. **[DATA_SOURCE_ANALYSIS.md](DATA_SOURCE_ANALYSIS.md)**  
   → Free vs paid sources ($600/mo savings)

---

## 🤖 Key Agent Files

### Implemented (5/7)
- [Agent 22: Psychology](../agents/22_psychology/sentiment_analyzer.py) - 330 lines
- [Agent 23: Social](../agents/23_social/social_sentiment.py) - 380 lines
- [Agent 24: Politics](../agents/24_politics/policy_classifier.py) - 360 lines
- [Agent 25: Market](../agents/25_market/forecaster.py) - 470 lines ⭐
- [Agent 11: Portfolio](../agents/11_analyst/portfolio_optimizer.py) - 540 lines ⭐

### Pending (2/7)
- **Agent 01: Orchestrator** ← NEXT (HIGH PRIORITY)
- Agent 99: Model Registry (LOW PRIORITY)

---

## 🧪 Test Files

- [Quick Integration Test](../tests/test_quick_integration.py) - Real data (Agent 11)
- [Integration Test](../tests/test_integration_agents.py) - Agents 22, 24
- [Full Pipeline Test](../tests/test_full_pipeline.py) - All agents (deferred)

---

## 📊 Data & Tools

### Data Fetchers
- [Stock Data](../data_ingestion/stock_data.py) - yfinance wrapper
- [Data Handler](../data_ingestion/data_handler.py) - Qlib-inspired
- [News Aggregator](../agents/91_tools/news_aggregator.py) - RSS feeds
- [Reddit Collector](../agents/91_tools/reddit_collector.py) - PRAW
- [StockTwits](../agents/91_tools/stocktwits_collector.py) - Social API

### Database
- SQLite: `../outputs/data/hermes.db`
- Stock Cache: `../outputs/data/stock_cache/` (4 parquet files)

---

## 🔧 Quick Commands

### Git
```bash
git status
git log --oneline -5
git pull origin main
```

### Python Environment
```bash
source .venv/bin/activate
python -c "import torch, transformers; print('✅ OK')"
```

### Run Tests
```bash
python agents/11_analyst/portfolio_optimizer.py
python tests/test_quick_integration.py
```

### Check Disk
```bash
df -h /workspaces
du -sh .venv ~/.cache
```

---

## 📈 Latest Results

**90-Day Backtest** (Aug-Dec 2025):
- **Winner**: $QBTS (+76.43%)
- **Alpha**: +294.96% vs equal weight
- **Sharpe**: 3.268
- **Allocation**: 100% $QBTS (Max Sharpe)

---

## 🌐 GitHub

**Repository**: https://github.com/BraPil/HERMES_Quantum  
**Latest Commit**: `98ca594` (Restart docs)  
**Previous**: `3a3d49c` (Week 2 complete)

---

## 💾 Workspace Status

- **Disk**: 4.8GB free (25GB used / 32GB total)
- **Python**: 3.12.3 in `.venv`
- **PyTorch**: 2.9.1+cpu (184MB)
- **Status**: ✅ Healthy

---

## 🎯 Next Session

**Goal**: Agent 01 (Orchestrator)  
**Prompt**: [PERFECT_RESTART_PROMPT.md](PERFECT_RESTART_PROMPT.md)  
**Estimated**: 4-6 hours  
**Prerequisites**: All met ✅

---

**Quick Navigation**:
- [↑ Back to Project Root](../README.md)
- [📝 Master Plan](MASTER_PLAN.md)
- [🔬 Research Log](../research/EXPLORATION_LOG.md)
- [📊 State](../research/STATE.yaml)
