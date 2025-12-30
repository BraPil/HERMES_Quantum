#!/usr/bin/env python3
"""
Integration Test: Full Agent Pipeline with Real Data
Tests: Data Ingestion → Agents 22, 23, 24, 25, 11 → Portfolio Decision
"""

import sys
sys.path.insert(0, '/workspaces/HERMES_Quantum')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Import data modules
from data_ingestion.stock_data import StockDataFetcher
from data_ingestion.data_handler import HERMESDataHandler

# Import agents
import importlib.util

def load_agent_module(agent_num, module_name, file_path):
    """Load agent module dynamically"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load agents
agent22_mod = load_agent_module(22, "agent22", "/workspaces/HERMES_Quantum/agents/22_psychology/sentiment_analyzer.py")
agent23_mod = load_agent_module(23, "agent23", "/workspaces/HERMES_Quantum/agents/23_social/social_sentiment.py")
agent24_mod = load_agent_module(24, "agent24", "/workspaces/HERMES_Quantum/agents/24_politics/policy_classifier.py")
agent25_mod = load_agent_module(25, "agent25", "/workspaces/HERMES_Quantum/agents/25_market/forecaster.py")
agent11_mod = load_agent_module(11, "agent11", "/workspaces/HERMES_Quantum/agents/11_analyst/portfolio_optimizer.py")

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    print("\n" + "="*80)
    print("HERMES_Quantum: Full Agent Pipeline Integration Test")
    print("="*80 + "\n")
    
    # Quantum stock universe
    TICKERS = ['IONQ', 'QBTS', 'RGTI', 'QUBT']
    
    # =========================================================================
    # STEP 1: Data Ingestion
    # =========================================================================
    print("="*80)
    print("STEP 1: Data Ingestion (Real Market Data)")
    print("="*80 + "\n")
    
    fetcher = StockDataFetcher()
    
    try:
        # Fetch last 60 days of data
        print(f"Fetching data for {', '.join(TICKERS)}...")
        prices_df = fetcher.fetch_quantum_stocks(period='60d', interval='1d')
        
        print(f"✅ Data fetched: {len(prices_df)} rows")
        print(f"Date range: {prices_df.index[0].date()} to {prices_df.index[-1].date()}")
        print(f"Latest prices:")
        for ticker in TICKERS:
            if ticker in prices_df.columns:
                latest = prices_df[ticker].iloc[-1]
                print(f"  ${ticker}: ${latest:.2f}")
        print()
        
    except Exception as e:
        print(f"⚠️ Error fetching real data: {e}")
        print("Using synthetic data for testing...\n")
        
        # Generate synthetic data as fallback
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        prices_data = {}
        for i, ticker in enumerate(TICKERS):
            np.random.seed(hash(ticker) % 2**32)
            returns = np.random.randn(60) * 0.03 + 0.0005
            prices_data[ticker] = 30.0 * np.exp(np.cumsum(returns))
        prices_df = pd.DataFrame(prices_data, index=dates)
    
    # =========================================================================
    # STEP 2: Sentiment Analysis (Agent 22 + RSS News)
    # =========================================================================
    print("="*80)
    print("STEP 2: Financial Sentiment Analysis (Agent 22)")
    print("="*80 + "\n")
    
    agent22 = agent22_mod.Agent22_SentimentAnalyzer()
    
    # Simulated news headlines (in production, use NewsAggregator)
    news_headlines = [
        "Quantum computing stocks rally on breakthrough announcement",
        "IONQ secures major enterprise contract for quantum cloud services",
        "Market volatility affects quantum computing sector stocks",
        "Analysts upgrade quantum computing stocks on strong fundamentals"
    ]
    
    print("Analyzing news sentiment...")
    sentiments = agent22.analyze_batch(news_headlines)
    agg_sentiment = agent22.aggregate_sentiment(sentiments)
    
    print(f"News Sentiment Score: {agg_sentiment['overall_score']:+.3f}")
    print(f"  Positive: {agg_sentiment['positive_ratio']:.1%}")
    print(f"  Negative: {agg_sentiment['negative_ratio']:.1%}")
    print(f"  Neutral: {agg_sentiment['neutral_ratio']:.1%}")
    print(f"  Confidence: {agg_sentiment['confidence']:.3f}\n")
    
    # =========================================================================
    # STEP 3: Social Sentiment (Agent 23 + Social Media)
    # =========================================================================
    print("="*80)
    print("STEP 3: Social Sentiment Analysis (Agent 23)")
    print("="*80 + "\n")
    
    agent23 = agent23_mod.Agent23_SocialSentimentAnalyzer()
    
    # Simulated social media posts
    social_posts = [
        ("$IONQ to the moon! 🚀", "StockTwits", "IONQ"),
        ("Loading up on $QUBT before earnings", "Reddit", "QUBT"),
        ("$RGTI chart looks bullish", "Twitter", "RGTI"),
        ("Quantum stocks are the next AI", "Reddit", "GENERAL")
    ]
    
    print("Analyzing social sentiment...")
    social_sentiments = []
    for text, platform, ticker in social_posts:
        result = agent23.analyze(text, platform=platform, ticker=ticker)
        social_sentiments.append(result)
    
    social_agg = agent23.aggregate_by_ticker(social_sentiments)
    
    print("Social Sentiment by Ticker:")
    for ticker, metrics in sorted(social_agg.items()):
        if ticker != 'GENERAL' and ticker in TICKERS:
            print(f"  ${ticker}: {metrics['overall_score']:+.3f} ({metrics['num_posts']} posts)")
    print()
    
    # =========================================================================
    # STEP 4: Policy Classification (Agent 24)
    # =========================================================================
    print("="*80)
    print("STEP 4: Policy & Risk Analysis (Agent 24)")
    print("="*80 + "\n")
    
    agent24 = agent24_mod.Agent24_PolicyClassifier()
    
    # Analyze same news with policy lens
    print("Classifying news by policy category...")
    policy_results = agent24.classify_batch(news_headlines[:2])
    
    for result in policy_results:
        print(f"  {result.text[:50]}...")
        print(f"    → {result.top_label} ({result.top_score:.3f})")
    
    policy_risks = agent24.identify_policy_risks(policy_results)
    print(f"\nPolicy Risks Identified: {len(policy_risks)}\n")
    
    # =========================================================================
    # STEP 5: Price Forecasting (Agent 25)
    # =========================================================================
    print("="*80)
    print("STEP 5: Price Forecasting (Agent 25)")
    print("="*80 + "\n")
    
    try:
        agent25 = agent25_mod.Agent25_MarketForecaster(model_name="amazon/chronos-t5-small")
        
        print("Generating 5-day forecasts...")
        forecasts = {}
        for ticker in TICKERS:
            if ticker in prices_df.columns:
                prices = prices_df[ticker].dropna()
                if len(prices) > 20:
                    forecast = agent25.forecast(ticker, prices, forecast_horizon=5)
                    forecasts[ticker] = forecast
                    
                    print(f"  ${ticker}:")
                    print(f"    Current: ${forecast.current_price:.2f}")
                    print(f"    Forecast: ${forecast.predictions[-1]:.2f}")
                    print(f"    Expected Return: {forecast.expected_return:+.2%}")
                    print(f"    Signal: {forecast.signal}")
        
        # Get top opportunities
        top_signals = agent25.get_portfolio_signals(forecasts, top_n=3)
        print(f"\nTop 3 Opportunities:")
        for i, signal in enumerate(top_signals, 1):
            print(f"  {i}. ${signal['ticker']} - {signal['signal']} (Return: {signal['expected_return']:+.2%}, Confidence: {signal['confidence']:.3f})")
        print()
        
    except Exception as e:
        print(f"⚠️ Agent 25 skipped: {e}\n")
        forecasts = {}
        top_signals = []
    
    # =========================================================================
    # STEP 6: Portfolio Optimization (Agent 11)
    # =========================================================================
    print("="*80)
    print("STEP 6: Portfolio Optimization (Agent 11)")
    print("="*80 + "\n")
    
    agent11 = agent11_mod.Agent11_PortfolioAnalyst(risk_free_rate=0.05)
    
    print("Optimizing portfolio allocation...")
    
    # Max Sharpe portfolio
    max_sharpe = agent11.optimize_max_sharpe(prices_df)
    print(f"Maximum Sharpe Portfolio:")
    print(f"  Expected Return: {max_sharpe.expected_return:.2%}")
    print(f"  Volatility: {max_sharpe.volatility:.2%}")
    print(f"  Sharpe Ratio: {max_sharpe.sharpe_ratio:.3f}")
    print(f"  Allocation:")
    for ticker, weight in sorted(max_sharpe.weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0.01:
            print(f"    ${ticker}: {weight:.1%}")
    print()
    
    # Discrete allocation for $100k portfolio
    latest_prices = {ticker: prices_df[ticker].iloc[-1] for ticker in TICKERS if ticker in prices_df.columns}
    max_sharpe_discrete = agent11.calculate_discrete_allocation(max_sharpe, latest_prices, 100000)
    
    print(f"Discrete Allocation ($100,000 portfolio):")
    for ticker, shares in sorted(max_sharpe_discrete.discrete_allocation.items(), key=lambda x: x[1], reverse=True):
        value = shares * latest_prices[ticker]
        print(f"  ${ticker}: {shares:4d} shares @ ${latest_prices[ticker]:.2f} = ${value:,.2f}")
    print()
    
    # =========================================================================
    # STEP 7: Final Recommendation
    # =========================================================================
    print("="*80)
    print("FINAL HERMES_Quantum Recommendation")
    print("="*80 + "\n")
    
    print("📊 Market Analysis Summary:")
    print(f"  News Sentiment: {agg_sentiment['overall_score']:+.3f} ({'Positive' if agg_sentiment['overall_score'] > 0 else 'Negative' if agg_sentiment['overall_score'] < 0 else 'Neutral'})")
    print(f"  Social Sentiment: Mixed (varies by ticker)")
    print(f"  Policy Risks: {len(policy_risks)} identified")
    if forecasts:
        print(f"  Price Trend: {len([f for f in forecasts.values() if f.expected_return > 0])} stocks bullish, {len([f for f in forecasts.values() if f.expected_return < 0])} bearish")
    
    print(f"\n💼 Portfolio Recommendation:")
    print(f"  Strategy: Maximum Sharpe Ratio")
    print(f"  Expected Annual Return: {max_sharpe.expected_return:.2%}")
    print(f"  Portfolio Risk (Volatility): {max_sharpe.volatility:.2%}")
    print(f"  Risk-Adjusted Performance: {max_sharpe.sharpe_ratio:.3f}")
    
    print(f"\n🎯 Action Items:")
    top_holdings = max_sharpe.get_top_holdings(3)
    for i, (ticker, weight) in enumerate(top_holdings, 1):
        if weight > 0.01:
            print(f"  {i}. BUY ${ticker} - Target allocation: {weight:.1%}")
    
    print("\n" + "="*80)
    print("✅ HERMES_Quantum Agent Pipeline Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
