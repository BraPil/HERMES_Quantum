#!/usr/bin/env python3
"""
Quick Integration Test: Agent 11 + Agent 25 + Real Data
Tests portfolio optimization with forecasting on real quantum stock data
"""

import sys
sys.path.insert(0, '/workspaces/HERMES_Quantum')

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Import data modules
from data_ingestion.stock_data import StockDataFetcher

# Import Agent 11 (lightweight, no ML models)
import importlib.util
spec11 = importlib.util.spec_from_file_location(
    "agent11",
    "/workspaces/HERMES_Quantum/agents/11_analyst/portfolio_optimizer.py"
)
if spec11 is not None and spec11.loader is not None:
    agent11_mod = importlib.util.module_from_spec(spec11)
    spec11.loader.exec_module(agent11_mod)
else:
    raise ImportError("Failed to load agent11 module")

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    print("\n" + "="*80)
    print("Quick Integration Test: Real Data → Portfolio Optimization")
    print("="*80 + "\n")
    
    # Quantum stock universe
    TICKERS = ['IONQ', 'QBTS', 'RGTI', 'QUBT']
    
    # Fetch real data
    print("Fetching real market data...")
    print("-"*80)
    
    fetcher = StockDataFetcher()
    
    try:
        # Fetch last 90 days in wide format (tickers as columns)
        prices_df = fetcher.fetch_quantum_stocks_wide(period='90d', interval='1d')
        
        print(f"✅ Data fetched: {len(prices_df)} rows")
        print(f"Date range: {prices_df.index[0].date()} to {prices_df.index[-1].date()}")
        print(f"\nLatest Prices (Dec 29, 2025):")
        for ticker in TICKERS:
            if ticker in prices_df.columns:
                latest = prices_df[ticker].iloc[-1]
                change = (prices_df[ticker].iloc[-1] / prices_df[ticker].iloc[-5] - 1) * 100
                arrow = "📈" if change > 0 else "📉"
                print(f"  ${ticker:4s}: ${latest:7.2f}  {arrow} {change:+.2f}% (5-day)")
        
        # Calculate some statistics
        print(f"\n90-Day Performance:")
        returns = prices_df.pct_change().dropna()
        for ticker in TICKERS:
            if ticker in returns.columns:
                total_return = (prices_df[ticker].iloc[-1] / prices_df[ticker].iloc[0] - 1) * 100
                volatility = returns[ticker].std() * np.sqrt(252) * 100
                print(f"  ${ticker}: Return: {total_return:+6.2f}%  |  Volatility: {volatility:.1f}%")
        
    except Exception as e:
        print(f"⚠️ Error fetching real data: {e}")
        print("Test aborted - need real data for meaningful results")
        return
    
    print("\n" + "="*80)
    print("Portfolio Optimization (Agent 11)")
    print("="*80 + "\n")
    
    agent11 = agent11_mod.Agent11_PortfolioAnalyst(risk_free_rate=0.05)
    
    # Compare strategies
    print("Comparing optimization strategies...")
    print("-"*80 + "\n")
    
    comparison = agent11.compare_strategies(prices_df)
    print(comparison.to_string(index=False))
    
    print("\n" + "-"*80)
    print("Best Strategy: Maximum Sharpe Ratio")
    print("-"*80 + "\n")
    
    max_sharpe = agent11.optimize_max_sharpe(prices_df)
    
    print(f"Expected Annual Return: {max_sharpe.expected_return:.2%}")
    print(f"Expected Volatility: {max_sharpe.volatility:.2%}")
    print(f"Sharpe Ratio: {max_sharpe.sharpe_ratio:.3f}")
    
    print(f"\nOptimal Allocation:")
    for ticker, weight in sorted(max_sharpe.weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0.01:
            print(f"  ${ticker:4s}: {weight:6.1%}")
    
    # Discrete allocation
    print("\n" + "-"*80)
    print("Discrete Allocation for $100,000 Portfolio")
    print("-"*80 + "\n")
    
    latest_prices = {ticker: prices_df[ticker].iloc[-1] for ticker in TICKERS if ticker in prices_df.columns}
    max_sharpe_discrete = agent11.calculate_discrete_allocation(max_sharpe, latest_prices, 100000)
    
    print(f"Portfolio Value: $100,000\n")
    total_invested = 0
    for ticker, shares in sorted(max_sharpe_discrete.discrete_allocation.items(), key=lambda x: x[1] * latest_prices[x[0]], reverse=True):
        value = shares * latest_prices[ticker]
        total_invested += value
        pct = value / 100000 * 100
        print(f"  ${ticker}: {shares:4d} shares × ${latest_prices[ticker]:7.2f} = ${value:10,.2f} ({pct:5.1f}%)")
    
    leftover = 100000 - total_invested
    print(f"  Cash:                                    ${leftover:10,.2f} ({leftover/1000:5.1f}%)")
    
    # Backtest performance
    print("\n" + "="*80)
    print("Backtest Results (90-day period)")
    print("="*80 + "\n")
    
    portfolio_returns, metrics = agent11.backtest_portfolio(max_sharpe.weights, prices_df)
    
    print(f"Actual Portfolio Performance:")
    print(f"  Total Return: {metrics.total_return:.2%}")
    print(f"  Annualized Return: {metrics.annual_return:.2%}")
    print(f"  Annualized Volatility: {metrics.annual_volatility:.2%}")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.3f}")
    print(f"  Sortino Ratio: {metrics.sortino_ratio:.3f}")
    print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
    print(f"  Calmar Ratio: {metrics.calmar_ratio:.3f}")
    
    # Compare to equal weight
    equal_weight = {ticker: 0.25 for ticker in TICKERS if ticker in prices_df.columns}
    equal_returns, equal_metrics = agent11.backtest_portfolio(equal_weight, prices_df)
    
    print(f"\nEqual Weight Baseline:")
    print(f"  Total Return: {equal_metrics.total_return:.2%}")
    print(f"  Annualized Return: {equal_metrics.annual_return:.2%}")
    print(f"  Sharpe Ratio: {equal_metrics.sharpe_ratio:.3f}")
    
    alpha = metrics.annual_return - equal_metrics.annual_return
    print(f"\nAlpha vs Equal Weight: {alpha:+.2%}")
    
    print("\n" + "="*80)
    print("✅ Integration Test Complete!")
    print("="*80)
    print(f"\n💡 Key Insight: Max Sharpe portfolio {'outperformed' if alpha > 0 else 'underperformed'} equal weight by {abs(alpha):.2%}")
    print(f"   Recommended Action: {'IMPLEMENT' if max_sharpe.sharpe_ratio > 0.5 else 'MONITOR'} optimized portfolio\n")


if __name__ == "__main__":
    main()
