"""
Agent 11: Portfolio Analyst & Optimizer
Uses PyPortfolioOpt and empyrical for portfolio optimization

Purpose: Optimize portfolio allocation, risk management, performance analysis
Output: Portfolio weights, risk metrics, rebalancing recommendations
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging

# Portfolio optimization
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt import objective_functions
from pypfopt.discrete_allocation import DiscreteAllocation

# Performance metrics
import empyrical as ep

logger = logging.getLogger(__name__)


@dataclass
class PortfolioAllocation:
    """Portfolio allocation result"""
    weights: Dict[str, float]  # Ticker -> weight
    expected_return: float
    volatility: float
    sharpe_ratio: float
    allocation_method: str
    timestamp: datetime
    total_value: Optional[float] = None
    discrete_allocation: Optional[Dict[str, int]] = None  # Ticker -> shares
    
    def to_dict(self) -> Dict:
        return {
            'weights': self.weights,
            'expected_return': self.expected_return,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'allocation_method': self.allocation_method,
            'timestamp': self.timestamp.isoformat(),
            'total_value': self.total_value,
            'discrete_allocation': self.discrete_allocation
        }
    
    def get_top_holdings(self, n: int = 5) -> List[Tuple[str, float]]:
        """Get top N holdings by weight"""
        sorted_weights = sorted(self.weights.items(), key=lambda x: x[1], reverse=True)
        return sorted_weights[:n]


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics"""
    ticker: Optional[str] = None
    total_return: float = 0.0
    annual_return: float = 0.0
    annual_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    omega_ratio: float = 0.0
    alpha: Optional[float] = None
    beta: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'total_return': self.total_return,
            'annual_return': self.annual_return,
            'annual_volatility': self.annual_volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'calmar_ratio': self.calmar_ratio,
            'omega_ratio': self.omega_ratio,
            'alpha': self.alpha,
            'beta': self.beta
        }


class Agent11_PortfolioAnalyst:
    """
    Agent 11: Portfolio Analyst & Optimizer
    
    Performs portfolio optimization using Modern Portfolio Theory (MPT)
    and calculates comprehensive performance metrics.
    
    Capabilities:
    - Mean-variance optimization
    - Maximum Sharpe ratio portfolios
    - Minimum volatility portfolios
    - Risk parity
    - Performance analysis with empyrical
    - Discrete allocation for real trading
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.05,  # 5% risk-free rate
        target_return: Optional[float] = None
    ):
        """
        Initialize portfolio analyst.
        
        Args:
            risk_free_rate: Annual risk-free rate (for Sharpe calculation)
            target_return: Target annual return (optional)
        """
        self.risk_free_rate = risk_free_rate
        self.target_return = target_return
        
        logger.info("Agent 11 initialized successfully")
    
    def optimize_max_sharpe(
        self,
        prices: pd.DataFrame,
        method: str = "mean_historical_return"
    ) -> PortfolioAllocation:
        """
        Optimize portfolio for maximum Sharpe ratio.
        
        Args:
            prices: DataFrame with date index and ticker columns
            method: Expected return estimation method
            
        Returns:
            PortfolioAllocation with optimized weights
        """
        # Calculate expected returns and covariance
        if method == "mean_historical_return":
            mu = expected_returns.mean_historical_return(prices)
        elif method == "ema_historical_return":
            mu = expected_returns.ema_historical_return(prices)
        elif method == "capm_return":
            mu = expected_returns.capm_return(prices)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        S = risk_models.sample_cov(prices)
        
        # Optimize
        ef = EfficientFrontier(mu, S)
        weights = ef.max_sharpe(risk_free_rate=self.risk_free_rate)
        cleaned_weights = ef.clean_weights()
        
        # Calculate performance
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        
        return PortfolioAllocation(
            weights=cleaned_weights,
            expected_return=perf[0],
            volatility=perf[1],
            sharpe_ratio=perf[2],
            allocation_method="max_sharpe",
            timestamp=datetime.now()
        )
    
    def optimize_min_volatility(
        self,
        prices: pd.DataFrame
    ) -> PortfolioAllocation:
        """
        Optimize portfolio for minimum volatility.
        
        Args:
            prices: DataFrame with date index and ticker columns
            
        Returns:
            PortfolioAllocation with optimized weights
        """
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.sample_cov(prices)
        
        ef = EfficientFrontier(mu, S)
        weights = ef.min_volatility()
        cleaned_weights = ef.clean_weights()
        
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        
        return PortfolioAllocation(
            weights=cleaned_weights,
            expected_return=perf[0],
            volatility=perf[1],
            sharpe_ratio=perf[2],
            allocation_method="min_volatility",
            timestamp=datetime.now()
        )
    
    def optimize_efficient_return(
        self,
        prices: pd.DataFrame,
        target_return: Optional[float] = None
    ) -> PortfolioAllocation:
        """
        Optimize portfolio for efficient return (minimize risk for target return).
        
        Args:
            prices: DataFrame with date index and ticker columns
            target_return: Target annual return (uses self.target_return if None)
            
        Returns:
            PortfolioAllocation with optimized weights
        """
        if target_return is None:
            target_return = self.target_return
        
        if target_return is None:
            raise ValueError("Target return must be specified")
        
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.sample_cov(prices)
        
        ef = EfficientFrontier(mu, S)
        weights = ef.efficient_return(target_return)
        cleaned_weights = ef.clean_weights()
        
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        
        return PortfolioAllocation(
            weights=cleaned_weights,
            expected_return=perf[0],
            volatility=perf[1],
            sharpe_ratio=perf[2],
            allocation_method=f"efficient_return_{target_return:.1%}",
            timestamp=datetime.now()
        )
    
    def optimize_equal_weight(
        self,
        prices: pd.DataFrame
    ) -> PortfolioAllocation:
        """
        Create equal-weight portfolio (baseline).
        
        Args:
            prices: DataFrame with date index and ticker columns
            
        Returns:
            PortfolioAllocation with equal weights
        """
        tickers = prices.columns.tolist()
        n = len(tickers)
        weights = {ticker: 1.0 / n for ticker in tickers}
        
        # Calculate performance
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.sample_cov(prices)
        
        ef = EfficientFrontier(mu, S)
        ef.set_weights(weights)
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        
        return PortfolioAllocation(
            weights=weights,
            expected_return=perf[0],
            volatility=perf[1],
            sharpe_ratio=perf[2],
            allocation_method="equal_weight",
            timestamp=datetime.now()
        )
    
    def calculate_discrete_allocation(
        self,
        allocation: PortfolioAllocation,
        latest_prices: Union[Dict[str, float], pd.Series],
        total_value: float
    ) -> PortfolioAllocation:
        """
        Convert percentage weights to discrete share quantities.
        
        Args:
            allocation: PortfolioAllocation with percentage weights
            latest_prices: Dictionary or Series of current prices
            total_value: Total portfolio value in dollars
            
        Returns:
            Updated PortfolioAllocation with discrete allocation
        """
        # Convert dict to Series if needed
        if isinstance(latest_prices, dict):
            latest_prices = pd.Series(latest_prices)
        
        da = DiscreteAllocation(
            allocation.weights,
            latest_prices,
            total_portfolio_value=total_value
        )
        
        discrete_allocation, leftover = da.greedy_portfolio()
        
        # Update allocation
        allocation.total_value = total_value
        allocation.discrete_allocation = discrete_allocation
        
        logger.info(f"Discrete allocation: {discrete_allocation}, Leftover: ${leftover:.2f}")
        
        return allocation
    
    def calculate_performance(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            returns: Series of returns (daily)
            benchmark_returns: Optional benchmark returns for alpha/beta
            
        Returns:
            PerformanceMetrics object
        """
        metrics = PerformanceMetrics()
        
        # Basic metrics
        metrics.total_return = ep.cum_returns_final(returns)
        metrics.annual_return = ep.annual_return(returns)
        metrics.annual_volatility = ep.annual_volatility(returns)
        
        # Risk-adjusted metrics
        metrics.sharpe_ratio = ep.sharpe_ratio(returns, risk_free=self.risk_free_rate)
        metrics.sortino_ratio = ep.sortino_ratio(returns, required_return=0)
        metrics.max_drawdown = ep.max_drawdown(returns)
        metrics.calmar_ratio = ep.calmar_ratio(returns)
        
        try:
            metrics.omega_ratio = ep.omega_ratio(returns, risk_free=self.risk_free_rate)
        except:
            metrics.omega_ratio = 0.0
        
        # Alpha and beta (if benchmark provided)
        if benchmark_returns is not None:
            metrics.alpha = ep.alpha(returns, benchmark_returns, risk_free=self.risk_free_rate)
            metrics.beta = ep.beta(returns, benchmark_returns)
        
        return metrics
    
    def backtest_portfolio(
        self,
        weights: Dict[str, float],
        prices: pd.DataFrame,
        rebalance_frequency: Optional[int] = None
    ) -> Tuple[pd.Series, PerformanceMetrics]:
        """
        Backtest a portfolio allocation strategy.
        
        Args:
            weights: Portfolio weights
            prices: Historical prices DataFrame
            rebalance_frequency: Rebalance every N days (None = buy & hold)
            
        Returns:
            Tuple of (portfolio_returns, performance_metrics)
        """
        returns = prices.pct_change().dropna()
        
        if rebalance_frequency is None:
            # Buy and hold
            portfolio_returns = returns @ pd.Series(weights)
        else:
            # Periodic rebalancing
            portfolio_returns = pd.Series(index=returns.index, dtype=float)
            
            for i in range(len(returns)):
                if i % rebalance_frequency == 0:
                    # Rebalance: recalculate weights
                    recent_prices = prices.iloc[:i+1]
                    if len(recent_prices) > 20:  # Need enough data
                        try:
                            alloc = self.optimize_max_sharpe(recent_prices)
                            current_weights = pd.Series(alloc.weights)
                        except:
                            current_weights = pd.Series(weights)
                    else:
                        current_weights = pd.Series(weights)
                else:
                    # Use existing weights
                    pass
                
                portfolio_returns.iloc[i] = returns.iloc[i] @ current_weights
        
        # Calculate metrics
        metrics = self.calculate_performance(portfolio_returns)
        
        return portfolio_returns, metrics
    
    def compare_strategies(
        self,
        prices: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compare multiple portfolio strategies.
        
        Args:
            prices: Historical prices DataFrame
            
        Returns:
            DataFrame with comparison metrics
        """
        strategies = {
            'Equal Weight': self.optimize_equal_weight(prices),
            'Max Sharpe': self.optimize_max_sharpe(prices),
            'Min Volatility': self.optimize_min_volatility(prices)
        }
        
        results = []
        
        for name, allocation in strategies.items():
            portfolio_returns, metrics = self.backtest_portfolio(
                allocation.weights,
                prices
            )
            
            results.append({
                'Strategy': name,
                'Expected Return': allocation.expected_return,
                'Volatility': allocation.volatility,
                'Sharpe Ratio': allocation.sharpe_ratio,
                'Actual Return': metrics.annual_return,
                'Max Drawdown': metrics.max_drawdown,
                'Sortino Ratio': metrics.sortino_ratio
            })
        
        return pd.DataFrame(results)


def main():
    """Test Agent 11 with quantum stock data"""
    
    print("\n" + "="*70)
    print("Agent 11: Portfolio Analyst Test")
    print("="*70 + "\n")
    
    # Initialize agent
    agent = Agent11_PortfolioAnalyst(risk_free_rate=0.05)
    
    # Generate synthetic price data for quantum stocks
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', '2024-12-29', freq='D')
    tickers = ['IONQ', 'QBTS', 'RGTI', 'QUBT']
    
    prices_data = {}
    for i, ticker in enumerate(tickers):
        np.random.seed(hash(ticker) % 2**32)
        # Different expected returns for each stock (annualized: 8%, 12%, 15%, 20%)
        annual_return = [0.08, 0.12, 0.15, 0.20][i]
        daily_return = annual_return / 252
        returns = np.random.randn(len(dates)) * 0.03 + daily_return  # 3% vol
        prices_data[ticker] = 30.0 * np.exp(np.cumsum(returns))
    
    prices = pd.DataFrame(prices_data, index=dates)
    
    print("Historical Data:")
    print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Days: {len(prices)}\n")
    
    # Test different optimization strategies
    print("-"*70)
    print("Portfolio Optimization Strategies:")
    print("-"*70 + "\n")
    
    # 1. Max Sharpe
    max_sharpe = agent.optimize_max_sharpe(prices)
    print("1. Maximum Sharpe Ratio Portfolio:")
    print(f"   Expected Return: {max_sharpe.expected_return:.2%}")
    print(f"   Volatility: {max_sharpe.volatility:.2%}")
    print(f"   Sharpe Ratio: {max_sharpe.sharpe_ratio:.3f}")
    print(f"   Weights:")
    for ticker, weight in sorted(max_sharpe.weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0.01:
            print(f"     {ticker}: {weight:.1%}")
    print()
    
    # 2. Min Volatility
    min_vol = agent.optimize_min_volatility(prices)
    print("2. Minimum Volatility Portfolio:")
    print(f"   Expected Return: {min_vol.expected_return:.2%}")
    print(f"   Volatility: {min_vol.volatility:.2%}")
    print(f"   Sharpe Ratio: {min_vol.sharpe_ratio:.3f}")
    print(f"   Weights:")
    for ticker, weight in sorted(min_vol.weights.items(), key=lambda x: x[1], reverse=True):
        if weight > 0.01:
            print(f"     {ticker}: {weight:.1%}")
    print()
    
    # 3. Equal Weight
    equal = agent.optimize_equal_weight(prices)
    print("3. Equal Weight Portfolio (Baseline):")
    print(f"   Expected Return: {equal.expected_return:.2%}")
    print(f"   Volatility: {equal.volatility:.2%}")
    print(f"   Sharpe Ratio: {equal.sharpe_ratio:.3f}")
    print()
    
    # Discrete allocation
    print("-"*70)
    print("Discrete Allocation (Real Trading):")
    print("-"*70 + "\n")
    
    latest_prices = {ticker: prices[ticker].iloc[-1] for ticker in tickers}
    total_value = 100000  # $100k portfolio
    
    max_sharpe_discrete = agent.calculate_discrete_allocation(
        max_sharpe,
        latest_prices,
        total_value
    )
    
    print(f"Portfolio Value: ${total_value:,.0f}")
    print(f"Allocation (Max Sharpe):")
    total_invested = 0
    for ticker, shares in sorted(max_sharpe_discrete.discrete_allocation.items(), key=lambda x: x[1], reverse=True):
        value = shares * latest_prices[ticker]
        total_invested += value
        print(f"  {ticker}: {shares:3d} shares @ ${latest_prices[ticker]:.2f} = ${value:,.2f}")
    
    leftover = total_value - total_invested
    print(f"  Cash: ${leftover:,.2f}")
    print()
    
    # Strategy comparison
    print("-"*70)
    print("Strategy Comparison (Backtest):")
    print("-"*70 + "\n")
    
    comparison = agent.compare_strategies(prices)
    print(comparison.to_string(index=False))
    
    print("\n" + "="*70)
    print("✅ Agent 11 test complete!")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
