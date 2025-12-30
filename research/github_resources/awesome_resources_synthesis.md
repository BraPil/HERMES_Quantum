# Awesome Resources Synthesis: Key Tools for HERMES

## Overview

This document synthesizes findings from two major curated lists:
- **wilsonfreitas/awesome-quant**: 200+ quantitative finance tools (17.5K stars)
- **georgezouq/awesome-ai-in-finance**: AI-focused finance resources (3K+ stars)

Rather than detailed evaluations (like Qlib and Zipline), this provides a **tool inventory** organized by HERMES agent needs.

---

## High-Priority Tools by Category

### Portfolio Optimization (Agent 11: Analyst)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| PyPortfolioOpt | Portfolio optimization (Efficient Frontier, risk parity) | **HIGH** |
| skfolio | sklearn-compatible portfolio tools | **HIGH** |
| Riskfolio-Lib | Modern portfolio theory + advanced methods | MEDIUM |
| Eiten | Statistical/algorithmic strategies (Eigen, min variance) | MEDIUM |
| riskparity.py | TensorFlow-based risk parity | LOW |

**Recommendation**: Start with **PyPortfolioOpt** - simple API, well-documented.

---

### Sentiment Analysis (Agent 22: Psychology)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| Asset News Sentiment Analyzer | GPT-based sentiment analysis | **HIGH** |
| FinBERT variants (ProsusAI, yiyanghkust) | Already evaluated in Phase 0 | **ADOPTED** |
| TextBlob/VADER | Simple baseline sentiment | LOW (baseline only) |

**Status**: Already addressed with ProsusAI/finbert in Phase 0. Consider GPT-based analyzer for enhanced capabilities.

---

### Social Media Analysis (Agent 23: Social)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| StephanAkkerman/FinTwitBERT-sentiment | Twitter sentiment (adopted Phase 0) | **ADOPTED** |
| Reddit WallstreetBets API | Reddit sentiment data | **HIGH** |
| CryptoInscriber | Historical crypto social data | LOW (crypto focus) |

**Status**: FinTwitBERT adopted. Add Reddit API for broader social coverage.

---

### Technical Analysis (Agent 25: Market)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| TA-Lib | 150+ technical indicators (C library) | **HIGH** |
| pandas_ta | 115+ indicators (pure Python) | **HIGH** |
| finta | Common TA indicators in Pandas | MEDIUM |
| Tulipy | 100+ indicators (Python bindings) | MEDIUM |
| talipp | Incremental TA library | LOW |

**Recommendation**: Use **pandas_ta** (pure Python, easy install) + TA-Lib (for advanced indicators).

---

### Time Series Forecasting (Agent 25: Market)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| amazon/chronos-t5-large | Adopted in Phase 0 | **ADOPTED** |
| mlforecast | Scalable ML time series | MEDIUM |
| statsmodels | Classical time series (ARIMA, etc.) | MEDIUM |
| prophet | Facebook's forecasting tool | LOW (not finance-specific) |

**Status**: Chronos adopted. Consider mlforecast for ensemble methods.

---

### Factor Analysis (All Analytical Agents)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| alphalens-reloaded | Alpha factor performance analysis | **HIGH** |
| Spectre | GPU-accelerated factor analysis | MEDIUM |
| FactorAnalytics (R) | Traditional factor models | LOW (R dependency) |

**Recommendation**: **alphalens-reloaded** - essential for validating agent-generated factors.

---

### Risk Management (Agent 11: Analyst)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| empyrical-reloaded | Risk/performance metrics | **HIGH** |
| pyfolio-reloaded | Portfolio analytics | **HIGH** |
| fortitudo.tech | CVaR optimization | MEDIUM |
| QuantLibRisks | Fast QuantLib risks | MEDIUM |

**Recommendation**: **empyrical-reloaded** + **pyfolio-reloaded** (active forks of Quantopian tools).

---

### Data Sources (Agent 91: Tools)

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| yfinance | Yahoo Finance API | **HIGH** |
| Quandl | Financial/economic datasets | **HIGH** |
| Financial Data API | Stock market data | MEDIUM |
| alpha_vantage | Free financial data API | MEDIUM |
| FinanceDatabase | 300K+ symbols database | MEDIUM |
| finagg | Aggregate multiple APIs | LOW |

**Recommendation**: Start with **yfinance** (free, reliable) + **Quandl** (macro data).

---

### Backtesting Frameworks

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| Zipline | Quantopian's backtester (evaluated) | **ADOPTED** |
| backtrader | Python backtesting library | MEDIUM |
| vectorbt | Vectorized backtesting | MEDIUM |
| bt | Flexible backtesting framework | LOW |

**Status**: Zipline event architecture adopted. Consider vectorbt for fast strategy testing.

---

### Machine Learning for Trading

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| Qlib (Microsoft) | Full ML pipeline (evaluated) | **ADOPTED** |
| mlfinlab | Advances in Financial ML (Lopez de Prado) | **HIGH** |
| FinRL | Deep RL for trading | MEDIUM |
| machine-learning-for-trading | Book resources + code | MEDIUM |

**Status**: Qlib adopted. **mlfinlab** implements de Prado's methods (essential reading).

---

### Multi-Agent & Reinforcement Learning

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| TensorTrade | RL trading with TensorFlow | **HIGH** |
| FinRL-Library | Deep RL library | MEDIUM |
| btgym | Event-driven RL backtesting | MEDIUM |
| TradzQAI | RL training environment | LOW |

**Recommendation**: **TensorTrade** for agent 99 model experimentation.

---

### Research & Analysis Tools

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| Jupyter Quant | Dockerized quant environment | **HIGH** |
| OpenBB Terminal | AI-powered research workspace | MEDIUM |
| Synthical | AI research collaboration | LOW |

**Recommendation**: **Jupyter Quant** provides complete research environment (statsmodels, pymc, arch, zipline-reloaded, PyPortfolioOpt).

---

### Visualization

| Tool | Description | Integration Priority |
|------|-------------|---------------------|
| matplotlib/seaborn | Python standard | **HIGH** |
| plotly/dash | Interactive dashboards | **HIGH** |
| mplfinance | Finance-specific charts | MEDIUM |
| KLineChart | Customizable financial charts | LOW |

**Recommendation**: **plotly/dash** for interactive HERMES dashboards.

---

## Tools NOT Recommended

### Avoid (Stale/Archived)
- pyalgotrade (archived)
- pyfin (archived)
- fecon235 (unmaintained)
- gekko (crypto bot, inactive)

### Avoid (Scope Mismatch)
- Crypto-specific tools (zenbot, catalyst, magic8bot)
- Options pricing (FinancePy, vollib) - not relevant for stocks
- HFT tools - not applicable to HERMES strategy

---

## Implementation Roadmap

### Phase 1: Essential Infrastructure (Weeks 1-2)
1. **Data Layer**:
   - yfinance for price data
   - Quandl for macro/fundamental data
   - FinanceDatabase for stock universe

2. **Analysis Tools**:
   - pandas_ta for technical indicators
   - PyPortfolioOpt for optimization
   - empyrical-reloaded for metrics

3. **Framework**:
   - Zipline patterns (from evaluation)
   - Qlib DataHandler (from evaluation)

### Phase 2: Advanced Analytics (Weeks 3-4)
1. **Factor Analysis**:
   - alphalens-reloaded for validation
   - Implement custom factors per agent

2. **Risk Management**:
   - pyfolio-reloaded for reporting
   - fortitudo.tech for CVaR

3. **ML Pipeline**:
   - mlfinlab for feature engineering
   - Qlib patterns for model management

### Phase 3: RL & Optimization (Weeks 5-6)
1. **Reinforcement Learning**:
   - TensorTrade for agent training
   - Custom gym environments

2. **Multi-Agent**:
   - Implement OnlineManager (from Qlib)
   - Event coordination (from Zipline)

3. **Backtesting**:
   - Full Zipline integration
   - vectorbt for fast iteration

---

## Integration Priorities by Agent

### 01_orchestrator
- EventManager (Zipline) ✓ Evaluated
- OnlineManager (Qlib) ✓ Evaluated
- Scheduling patterns
- Multi-agent coordination

### 11_analyst
- **PyPortfolioOpt** (portfolio construction)
- **empyrical-reloaded** (performance metrics)
- **pyfolio-reloaded** (reporting)
- **alphalens-reloaded** (signal validation)

### 22_psychology (Sentiment)
- ProsusAI/finbert ✓ Adopted Phase 0
- Asset News Sentiment Analyzer (GPT-based)
- Pipeline API (Zipline) for factor computation

### 23_social (Social Media)
- StephanAkkerman/FinTwitBERT ✓ Adopted Phase 0
- Reddit WallstreetBets API
- Pipeline API for aggregation

### 24_politics (Policy/News)
- facebook/bart-large-mnli ✓ Adopted Phase 0
- Custom NLP pipeline
- Event-driven news processing

### 25_market (Technical)
- amazon/chronos-t5-large ✓ Adopted Phase 0
- **pandas_ta** (technical indicators)
- **mlforecast** (ML forecasting)
- RollingGen (Qlib) for time series ✓ Evaluated

### 91_tools (Utilities)
- **yfinance** (data ingestion)
- **Quandl** (macro data)
- DataPortal (Zipline) ✓ Evaluated
- DataHandler (Qlib) ✓ Evaluated

### 99_models (Model Management)
- Qlib model registry ✓ Evaluated
- Recorder (Qlib) ✓ Evaluated
- **TensorTrade** (RL training)
- MLflow integration

---

## Critical Dependencies

### Must Install First
```bash
# Core numerical
pip install numpy pandas scipy

# Data sources
pip install yfinance quandl

# Technical analysis
pip install pandas-ta

# Portfolio optimization
pip install PyPortfolioOpt

# Performance analytics
pip install empyrical-reloaded pyfolio-reloaded

# Factor analysis
pip install alphalens-reloaded

# ML/RL
pip install tensorflow torch scikit-learn

# Backtesting (if using full Zipline)
pip install zipline-reloaded
```

### Optional (Phase 2+)
```bash
# Advanced ML
pip install mlfinlab

# RL training
pip install tensortrade

# Fast backtesting
pip install vectorbt

# Advanced risk
pip install fortitudo-tech

# Visualization
pip install plotly dash mplfinance
```

---

## Comparison: Qlib vs Awesome Tools

| Category | Qlib Provides | Awesome Tools Add |
|----------|---------------|-------------------|
| Data Handling | DataHandler, processors | yfinance, Quandl (sources) |
| ML Pipeline | Full pipeline | mlfinlab (de Prado methods) |
| Backtesting | Strategy execution | Zipline (event-driven) |
| Portfolio | Basic optimization | PyPortfolioOpt (advanced) |
| Risk | Basic metrics | empyrical/pyfolio (comprehensive) |
| RL | Meta-learning | TensorTrade (full RL framework) |
| Factors | Custom factors | alphalens (validation) |

**Verdict**: Qlib + Awesome Tools are **complementary**. Qlib provides architecture, Awesome Tools provide specialized components.

---

## Resources for Learning

### Essential Reading
1. **Advances in Financial Machine Learning** (Lopez de Prado)
   - Implementation: mlfinlab library
   - Topics: Feature engineering, meta-labeling, backtesting

2. **Machine Learning for Algorithmic Trading** (Jansen)
   - Repo: machine-learning-for-trading
   - Comprehensive ML trading guide

3. **Quantitative Trading** (Chan)
   - Classic strategies
   - Mean reversion, momentum

### Online Courses
- NYU: Advanced Methods of RL in Finance
- Udacity: AI for Trading
- Coursera: Machine Learning for Trading

### Communities
- Quantopian Forums (archived, read-only)
- QuantConnect Community
- Reddit: r/algotrading, r/quant

---

## Key Takeaways

1. **Architecture from Qlib + Zipline** ✓ Already evaluated
2. **Data from yfinance + Quandl** → Immediate implementation
3. **Analytics from PyPortfolioOpt + pandas_ta** → Week 1
4. **Validation from alphalens + empyrical** → Week 2
5. **RL from TensorTrade** → Phase 3

**Next Steps**:
1. Install core dependencies (yfinance, pandas_ta, PyPortfolioOpt)
2. Create data_ingestion module using Qlib DataHandler pattern
3. Implement technical indicators with pandas_ta in agent 25
4. Set up portfolio optimization with PyPortfolioOpt in agent 11
5. Integrate empyrical metrics for performance tracking

---

**Synthesis Date**: 2025-12-28  
**Phase**: 0 (Research)  
**Status**: Complete - Ready for Phase 1 implementation  
**Resources Evaluated**: 3 repositories (Qlib, Zipline, Awesome Lists)
