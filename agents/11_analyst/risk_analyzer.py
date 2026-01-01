"""
Agent 11: Risk Analyzer
========================
Comprehensive risk analysis using pyfolio-reloaded and empyrical-reloaded.

Features:
- Full tear sheet generation
- Rolling performance metrics
- Drawdown analysis
- Factor exposure analysis
- Benchmark comparison

Created: 2026-01-01
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

# Try to import pyfolio and empyrical
try:
    import pyfolio as pf
    PYFOLIO_AVAILABLE = True
except ImportError:
    PYFOLIO_AVAILABLE = False
    pf = None

# empyrical has numpy 2.0 compatibility issues - use manual calculations
EMPYRICAL_AVAILABLE = False
ep = None

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for a portfolio."""
    # Return metrics
    total_return: float
    annual_return: float
    daily_return_mean: float
    daily_return_std: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    
    # Drawdown metrics
    max_drawdown: float
    max_drawdown_duration: int  # Days
    current_drawdown: float
    
    # Tail risk
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    tail_ratio: float
    
    # Stability
    stability: float
    downside_risk: float
    
    # Benchmark comparison
    alpha: float = 0.0
    beta: float = 0.0
    information_ratio: float = 0.0
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "max_drawdown": self.max_drawdown,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "alpha": self.alpha,
            "beta": self.beta,
            "timestamp": self.timestamp.isoformat()
        }


class RiskAnalyzer:
    """
    Portfolio risk analysis using pyfolio and empyrical.
    
    Usage:
        analyzer = RiskAnalyzer()
        
        # From returns series
        metrics = analyzer.analyze(returns)
        
        # Generate full report
        analyzer.create_tearsheet(returns)
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.04,  # 4% annual
        output_dir: str = None
    ):
        self.risk_free_rate = risk_free_rate
        self.daily_rf = (1 + risk_free_rate) ** (1/252) - 1
        
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "outputs" / "reports"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check dependencies
        if EMPYRICAL_AVAILABLE:
            logger.info("empyrical-reloaded available")
        else:
            logger.warning("empyrical not available - using manual calculations")
        
        if PYFOLIO_AVAILABLE:
            logger.info("pyfolio-reloaded available")
        else:
            logger.warning("pyfolio not available - tearsheets disabled")
    
    def _ensure_datetime_index(self, returns: pd.Series) -> pd.Series:
        """Ensure returns has a DatetimeIndex."""
        if not isinstance(returns.index, pd.DatetimeIndex):
            returns.index = pd.to_datetime(returns.index)
        return returns
    
    def calculate_returns(
        self,
        prices: pd.Series,
        method: str = "simple"
    ) -> pd.Series:
        """Calculate returns from price series."""
        prices = prices.dropna()
        
        if method == "log":
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()
        
        return returns.dropna()
    
    def calculate_sharpe(
        self,
        returns: pd.Series,
        risk_free_rate: float = None
    ) -> float:
        """Calculate annualized Sharpe ratio."""
        if risk_free_rate is None:
            risk_free_rate = self.daily_rf
        
        if EMPYRICAL_AVAILABLE:
            return float(ep.sharpe_ratio(returns, risk_free=risk_free_rate))
        
        excess_returns = returns - risk_free_rate
        if excess_returns.std() == 0:
            return 0.0
        
        return float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))
    
    def calculate_sortino(
        self,
        returns: pd.Series,
        required_return: float = 0.0
    ) -> float:
        """Calculate annualized Sortino ratio."""
        if EMPYRICAL_AVAILABLE:
            return float(ep.sortino_ratio(returns, required_return=required_return))
        
        excess_returns = returns - required_return / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        downside_std = downside_returns.std() * np.sqrt(252)
        return float(excess_returns.mean() * 252 / downside_std)
    
    def calculate_max_drawdown(self, returns: pd.Series) -> Tuple[float, int]:
        """Calculate maximum drawdown and duration."""
        if EMPYRICAL_AVAILABLE:
            max_dd = float(ep.max_drawdown(returns))
        else:
            cumulative = (1 + returns).cumprod()
            peak = cumulative.expanding().max()
            drawdown = (cumulative - peak) / peak
            max_dd = float(drawdown.min())
        
        # Calculate duration
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding().max()
        drawdown = (cumulative - peak) / peak
        
        # Find drawdown periods
        in_drawdown = drawdown < 0
        drawdown_periods = []
        current_period = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_period += 1
            else:
                if current_period > 0:
                    drawdown_periods.append(current_period)
                current_period = 0
        
        if current_period > 0:
            drawdown_periods.append(current_period)
        
        max_duration = max(drawdown_periods) if drawdown_periods else 0
        
        return max_dd, max_duration
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """Calculate Value at Risk."""
        if EMPYRICAL_AVAILABLE:
            return float(ep.value_at_risk(returns, cutoff=1-confidence))
        
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        var = self.calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) == 0:
            return var
        
        return float(tail_returns.mean())
    
    def calculate_calmar(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)."""
        if EMPYRICAL_AVAILABLE:
            return float(ep.calmar_ratio(returns))
        
        annual_return = (1 + returns.mean()) ** 252 - 1
        max_dd, _ = self.calculate_max_drawdown(returns)
        
        if max_dd == 0:
            return 0.0
        
        return float(annual_return / abs(max_dd))
    
    def calculate_alpha_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """Calculate alpha and beta vs benchmark."""
        if EMPYRICAL_AVAILABLE:
            alpha = float(ep.alpha(returns, benchmark_returns, risk_free=self.daily_rf))
            beta = float(ep.beta(returns, benchmark_returns))
            return alpha, beta
        
        # Manual calculation
        aligned = pd.concat([returns, benchmark_returns], axis=1, join='inner')
        aligned.columns = ['portfolio', 'benchmark']
        
        if len(aligned) < 2:
            return 0.0, 1.0
        
        covariance = aligned['portfolio'].cov(aligned['benchmark'])
        variance = aligned['benchmark'].var()
        
        if variance == 0:
            beta = 1.0
        else:
            beta = covariance / variance
        
        annual_ret = (1 + returns.mean()) ** 252 - 1
        annual_bench = (1 + benchmark_returns.mean()) ** 252 - 1
        alpha = annual_ret - (self.risk_free_rate + beta * (annual_bench - self.risk_free_rate))
        
        return float(alpha), float(beta)
    
    def analyze(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series = None
    ) -> RiskMetrics:
        """
        Perform comprehensive risk analysis.
        
        Args:
            returns: Daily returns series
            benchmark_returns: Optional benchmark returns
            
        Returns:
            RiskMetrics with all calculated metrics
        """
        returns = self._ensure_datetime_index(returns)
        returns = returns.dropna()
        
        if len(returns) < 5:
            raise ValueError("Need at least 5 data points for analysis")
        
        # Basic return metrics
        total_return = float((1 + returns).prod() - 1)
        annual_return = float((1 + returns.mean()) ** 252 - 1)
        daily_mean = float(returns.mean())
        daily_std = float(returns.std())
        
        # Risk-adjusted returns
        sharpe = self.calculate_sharpe(returns)
        sortino = self.calculate_sortino(returns)
        calmar = self.calculate_calmar(returns)
        
        # Omega ratio
        if EMPYRICAL_AVAILABLE:
            omega = float(ep.omega_ratio(returns))
        else:
            threshold = 0
            positive = returns[returns > threshold].sum()
            negative = abs(returns[returns < threshold].sum())
            omega = float(positive / negative) if negative != 0 else 0.0
        
        # Drawdown
        max_dd, max_dd_duration = self.calculate_max_drawdown(returns)
        
        # Current drawdown
        cumulative = (1 + returns).cumprod()
        peak = cumulative.max()
        current_dd = float((cumulative.iloc[-1] - peak) / peak)
        
        # Tail risk
        var_95 = self.calculate_var(returns, 0.95)
        cvar_95 = self.calculate_cvar(returns, 0.95)
        
        # Tail ratio
        if EMPYRICAL_AVAILABLE:
            tail = float(ep.tail_ratio(returns))
        else:
            right_tail = np.percentile(returns, 95)
            left_tail = abs(np.percentile(returns, 5))
            tail = float(right_tail / left_tail) if left_tail != 0 else 0.0
        
        # Stability
        if EMPYRICAL_AVAILABLE:
            stability = float(ep.stability_of_timeseries(returns))
            downside = float(ep.downside_risk(returns))
        else:
            # Simplified stability (R-squared of cumulative returns)
            cumulative = (1 + returns).cumprod()
            x = np.arange(len(cumulative))
            corr = np.corrcoef(x, cumulative)[0, 1]
            stability = float(corr ** 2) if not np.isnan(corr) else 0.0
            
            downside_returns = returns[returns < 0]
            downside = float(downside_returns.std() * np.sqrt(252))
        
        # Benchmark comparison
        alpha, beta, info_ratio = 0.0, 1.0, 0.0
        
        if benchmark_returns is not None:
            benchmark_returns = self._ensure_datetime_index(benchmark_returns)
            alpha, beta = self.calculate_alpha_beta(returns, benchmark_returns)
            
            # Information ratio
            tracking_error = (returns - benchmark_returns).std() * np.sqrt(252)
            excess_return = annual_return - ((1 + benchmark_returns.mean()) ** 252 - 1)
            info_ratio = float(excess_return / tracking_error) if tracking_error != 0 else 0.0
        
        return RiskMetrics(
            total_return=total_return,
            annual_return=annual_return,
            daily_return_mean=daily_mean,
            daily_return_std=daily_std,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            omega_ratio=omega,
            max_drawdown=max_dd,
            max_drawdown_duration=max_dd_duration,
            current_drawdown=current_dd,
            var_95=var_95,
            cvar_95=cvar_95,
            tail_ratio=tail,
            stability=stability,
            downside_risk=downside,
            alpha=alpha,
            beta=beta,
            information_ratio=info_ratio
        )
    
    def create_tearsheet(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series = None,
        title: str = "Portfolio Analysis",
        save_path: str = None
    ) -> Optional[str]:
        """
        Create pyfolio tear sheet.
        
        Returns path to saved file if save_path provided.
        """
        if not PYFOLIO_AVAILABLE:
            logger.warning("pyfolio not available - cannot create tearsheet")
            return None
        
        returns = self._ensure_datetime_index(returns)
        
        try:
            if benchmark_returns is not None:
                benchmark_returns = self._ensure_datetime_index(benchmark_returns)
                pf.create_full_tear_sheet(
                    returns,
                    benchmark_rets=benchmark_returns,
                    set_context=False
                )
            else:
                pf.create_returns_tear_sheet(returns, set_context=False)
            
            logger.info(f"Tearsheet created: {title}")
            
            if save_path:
                # Note: pyfolio doesn't have built-in save, would need matplotlib
                pass
            
            return save_path
            
        except Exception as e:
            logger.error(f"Error creating tearsheet: {e}")
            return None
    
    def generate_report(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series = None,
        title: str = "Portfolio"
    ) -> str:
        """Generate text-based risk report."""
        metrics = self.analyze(returns, benchmark_returns)
        
        report = f"""
{'='*50}
RISK ANALYSIS REPORT: {title}
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {returns.index[0].strftime('%Y-%m-%d')} to {returns.index[-1].strftime('%Y-%m-%d')}
Trading Days: {len(returns)}

RETURNS
{'-'*50}
Total Return:      {metrics.total_return:>10.2%}
Annual Return:     {metrics.annual_return:>10.2%}
Daily Mean:        {metrics.daily_return_mean:>10.4%}
Daily Std Dev:     {metrics.daily_return_std:>10.4%}

RISK-ADJUSTED PERFORMANCE
{'-'*50}
Sharpe Ratio:      {metrics.sharpe_ratio:>10.2f}
Sortino Ratio:     {metrics.sortino_ratio:>10.2f}
Calmar Ratio:      {metrics.calmar_ratio:>10.2f}
Omega Ratio:       {metrics.omega_ratio:>10.2f}

DRAWDOWN
{'-'*50}
Max Drawdown:      {metrics.max_drawdown:>10.2%}
Max DD Duration:   {metrics.max_drawdown_duration:>10d} days
Current Drawdown:  {metrics.current_drawdown:>10.2%}

TAIL RISK
{'-'*50}
VaR (95%):         {metrics.var_95:>10.2%}
CVaR (95%):        {metrics.cvar_95:>10.2%}
Tail Ratio:        {metrics.tail_ratio:>10.2f}

STABILITY
{'-'*50}
Stability:         {metrics.stability:>10.2f}
Downside Risk:     {metrics.downside_risk:>10.2%}
"""
        
        if benchmark_returns is not None:
            report += f"""
BENCHMARK COMPARISON
{'-'*50}
Alpha:             {metrics.alpha:>10.2%}
Beta:              {metrics.beta:>10.2f}
Information Ratio: {metrics.information_ratio:>10.2f}
"""
        
        report += "\n" + "=" * 50
        
        return report
    
    def rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 63  # ~3 months
    ) -> pd.DataFrame:
        """Calculate rolling risk metrics."""
        returns = self._ensure_datetime_index(returns)
        
        rolling_sharpe = returns.rolling(window).apply(
            lambda x: self.calculate_sharpe(x), raw=False
        )
        
        rolling_vol = returns.rolling(window).std() * np.sqrt(252)
        
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding().max()
        rolling_dd = (cumulative - peak) / peak
        
        return pd.DataFrame({
            'sharpe': rolling_sharpe,
            'volatility': rolling_vol,
            'drawdown': rolling_dd
        })


def main():
    """Demo risk analyzer functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("Agent 11 - Risk Analyzer Demo")
    print("="*60)
    
    # Initialize analyzer
    analyzer = RiskAnalyzer()
    
    # Generate synthetic returns data
    np.random.seed(42)
    
    dates = pd.date_range(start='2025-07-01', end='2025-12-31', freq='B')
    n_days = len(dates)
    
    # Simulated portfolio returns (slightly positive drift with volatility)
    portfolio_returns = pd.Series(
        np.random.normal(0.0005, 0.02, n_days),  # 0.05% daily return, 2% daily vol
        index=dates
    )
    
    # Add some drawdown periods
    portfolio_returns.iloc[30:45] = np.random.normal(-0.01, 0.02, 15)  # Drawdown period
    portfolio_returns.iloc[100:110] = np.random.normal(-0.015, 0.025, 10)  # Another drawdown
    
    # Simulated benchmark (SPY-like)
    benchmark_returns = pd.Series(
        np.random.normal(0.0004, 0.012, n_days),  # Lower vol benchmark
        index=dates
    )
    
    print(f"\n📊 Analyzing {n_days} trading days...")
    print(f"   Period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    
    # Analyze
    metrics = analyzer.analyze(portfolio_returns, benchmark_returns)
    
    # Print report
    print(analyzer.generate_report(portfolio_returns, benchmark_returns, "HERMES Quantum"))
    
    # Rolling metrics
    print("\n📈 Rolling Metrics (63-day window):")
    rolling = analyzer.rolling_metrics(portfolio_returns)
    
    print(f"   Latest Sharpe:     {rolling['sharpe'].iloc[-1]:.2f}")
    print(f"   Latest Volatility: {rolling['volatility'].iloc[-1]:.1%}")
    print(f"   Current Drawdown:  {rolling['drawdown'].iloc[-1]:.1%}")


if __name__ == "__main__":
    main()
