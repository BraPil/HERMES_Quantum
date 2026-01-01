"""
HERMES Quantum - Backtesting Framework
=======================================
Event-driven backtesting for signal validation and strategy testing.

This is a lightweight backtesting framework inspired by Zipline's event-driven
architecture but tailored for HERMES Quantum's multi-agent signal system.

Features:
- Historical signal replay
- Portfolio tracking with position management
- Performance metrics calculation (Sharpe, returns, drawdown)
- Trade logging and analysis
- Comparison with buy-and-hold benchmark

Created: 2026-01-01
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class TradeAction(Enum):
    """Trade action types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Trade:
    """Individual trade record."""
    timestamp: datetime
    ticker: str
    action: TradeAction
    shares: int
    price: float
    value: float
    commission: float = 0.0
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ticker": self.ticker,
            "action": self.action.value,
            "shares": self.shares,
            "price": self.price,
            "value": self.value,
            "commission": self.commission,
            "reason": self.reason
        }


@dataclass
class Position:
    """Portfolio position for a single ticker."""
    ticker: str
    shares: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        if self.shares == 0:
            return 0.0
        return (self.current_price - self.avg_cost) * self.shares
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.avg_cost == 0:
            return 0.0
        return (self.current_price - self.avg_cost) / self.avg_cost
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "avg_cost": self.avg_cost,
            "current_price": self.current_price,
            "market_value": self.market_value,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct
        }


@dataclass
class Portfolio:
    """Portfolio state tracker."""
    initial_cash: float = 100000.0
    cash: float = 100000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    commission_rate: float = 0.001  # 0.1% commission
    
    @property
    def total_value(self) -> float:
        """Total portfolio value (cash + positions)."""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def total_pnl(self) -> float:
        """Total P&L since inception."""
        return self.total_value - self.initial_cash
    
    @property
    def total_return(self) -> float:
        """Total return percentage."""
        return (self.total_value / self.initial_cash) - 1.0
    
    def update_prices(self, prices: Dict[str, float]):
        """Update position prices."""
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].current_price = price
    
    def buy(
        self,
        ticker: str,
        price: float,
        shares: Optional[int] = None,
        value: Optional[float] = None,
        reason: str = "",
        timestamp: Optional[datetime] = None
    ) -> Optional[Trade]:
        """Execute a buy order."""
        if shares is None and value is None:
            return None
            
        if shares is None:
            shares = int(value / price)
            
        if shares <= 0:
            return None
            
        cost = shares * price
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        if total_cost > self.cash:
            # Reduce shares to fit available cash
            shares = int((self.cash - commission) / price)
            if shares <= 0:
                logger.warning(f"Insufficient cash for {ticker} buy")
                return None
            cost = shares * price
            commission = cost * self.commission_rate
            total_cost = cost + commission
        
        # Update cash
        self.cash -= total_cost
        
        # Update position
        if ticker not in self.positions:
            self.positions[ticker] = Position(ticker=ticker)
        
        pos = self.positions[ticker]
        total_shares = pos.shares + shares
        if total_shares > 0:
            pos.avg_cost = (pos.shares * pos.avg_cost + cost) / total_shares
        pos.shares = total_shares
        pos.current_price = price
        
        # Record trade
        trade = Trade(
            timestamp=timestamp or datetime.now(),
            ticker=ticker,
            action=TradeAction.BUY,
            shares=shares,
            price=price,
            value=cost,
            commission=commission,
            reason=reason
        )
        self.trades.append(trade)
        
        return trade
    
    def sell(
        self,
        ticker: str,
        price: float,
        shares: Optional[int] = None,
        reason: str = "",
        timestamp: Optional[datetime] = None
    ) -> Optional[Trade]:
        """Execute a sell order."""
        if ticker not in self.positions:
            return None
            
        pos = self.positions[ticker]
        
        if shares is None:
            shares = pos.shares  # Sell all
            
        if shares <= 0 or shares > pos.shares:
            shares = pos.shares
            
        if shares <= 0:
            return None
        
        # Calculate proceeds
        proceeds = shares * price
        commission = proceeds * self.commission_rate
        net_proceeds = proceeds - commission
        
        # Update cash
        self.cash += net_proceeds
        
        # Update position
        pos.shares -= shares
        pos.current_price = price
        
        if pos.shares == 0:
            del self.positions[ticker]
        
        # Record trade
        trade = Trade(
            timestamp=timestamp or datetime.now(),
            ticker=ticker,
            action=TradeAction.SELL,
            shares=shares,
            price=price,
            value=proceeds,
            commission=commission,
            reason=reason
        )
        self.trades.append(trade)
        
        return trade
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cash": self.cash,
            "positions": {k: v.to_dict() for k, v in self.positions.items()},
            "total_value": self.total_value,
            "total_pnl": self.total_pnl,
            "total_return": self.total_return,
            "num_trades": len(self.trades)
        }


@dataclass
class BacktestResult:
    """Backtest results and performance metrics."""
    start_date: datetime
    end_date: datetime
    initial_value: float
    final_value: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    benchmark_return: float
    alpha: float
    daily_returns: pd.Series = None
    equity_curve: pd.Series = None
    trades: List[Trade] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_value": self.initial_value,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "num_trades": self.num_trades,
            "benchmark_return": self.benchmark_return,
            "alpha": self.alpha
        }
    
    def summary(self) -> str:
        """Generate text summary."""
        return f"""
========================================
BACKTEST RESULTS
========================================
Period: {self.start_date.date()} to {self.end_date.date()}
Duration: {(self.end_date - self.start_date).days} days

PERFORMANCE
-----------
Initial Value:     ${self.initial_value:,.2f}
Final Value:       ${self.final_value:,.2f}
Total Return:      {self.total_return:.2%}
Annualized Return: {self.annualized_return:.2%}
Sharpe Ratio:      {self.sharpe_ratio:.2f}
Max Drawdown:      {self.max_drawdown:.2%}

TRADING
-------
Total Trades:      {self.num_trades}
Win Rate:          {self.win_rate:.1%}

BENCHMARK
---------
Benchmark Return:  {self.benchmark_return:.2%}
Alpha:             {self.alpha:.2%}
========================================
"""


class Backtester:
    """
    Event-driven backtester for HERMES Quantum signals.
    
    Usage:
        backtester = Backtester(
            tickers=['QBTS', 'IONQ'],
            start_date='2025-07-01',
            end_date='2025-12-31'
        )
        
        # Run with historical signals
        result = backtester.run(signals_df)
        
        # Or run with orchestrator integration
        result = await backtester.run_with_orchestrator()
    """
    
    def __init__(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        initial_capital: float = 100000.0,
        position_size_pct: float = 0.25,  # 25% of portfolio per position
        buy_threshold: float = 0.5,  # Signal > 0.5 = buy
        sell_threshold: float = -0.3,  # Signal < -0.3 = sell
        stop_loss_pct: float = 0.10,  # 10% stop loss
        take_profit_pct: float = 0.20  # 20% take profit
    ):
        self.tickers = tickers
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date) if end_date else datetime.now()
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Initialize state
        self.portfolio = Portfolio(
            initial_cash=initial_capital,
            cash=initial_capital
        )
        self.price_history: Dict[str, pd.DataFrame] = {}
        self.equity_curve: List[Tuple[datetime, float]] = []
        self._price_data_loaded = False
        
    def load_price_data(self):
        """Load historical price data for all tickers."""
        if self._price_data_loaded:
            return
            
        try:
            from data_ingestion.stock_data import StockDataFetcher
            fetcher = StockDataFetcher()
            
            for ticker in self.tickers:
                df = fetcher.fetch_ohlcv(
                    ticker,
                    start=self.start_date.strftime('%Y-%m-%d'),
                    end=self.end_date.strftime('%Y-%m-%d')
                )
                if not df.empty:
                    self.price_history[ticker] = df
                    logger.info(f"Loaded {len(df)} days of data for {ticker}")
                else:
                    logger.warning(f"No data for {ticker}")
                    
            self._price_data_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading price data: {e}")
            raise
    
    def run(
        self,
        signals: pd.DataFrame = None,
        signal_column: str = 'signal',
        confidence_column: str = 'confidence'
    ) -> BacktestResult:
        """
        Run backtest on historical signals.
        
        Args:
            signals: DataFrame with columns ['date', 'ticker', 'signal', 'confidence']
                    signal: -1 to 1 (negative = bearish, positive = bullish)
                    confidence: 0 to 1
            signal_column: Name of signal column
            confidence_column: Name of confidence column
            
        Returns:
            BacktestResult with performance metrics
        """
        self.load_price_data()
        
        # Generate simulated signals if none provided
        if signals is None:
            signals = self._generate_simulated_signals()
        
        # Get all trading dates
        all_dates = set()
        for df in self.price_history.values():
            all_dates.update(df.index.tolist())
        trading_dates = sorted(all_dates)
        
        # Filter dates to backtest period
        # Handle timezone-aware vs naive comparison
        start_ts = self.start_date
        end_ts = self.end_date
        
        filtered_dates = []
        for d in trading_dates:
            # Convert to tz-naive for comparison if needed
            d_naive = d.tz_localize(None) if hasattr(d, 'tz') and d.tz else d
            start_naive = start_ts.tz_localize(None) if hasattr(start_ts, 'tz') and start_ts.tz else start_ts
            end_naive = end_ts.tz_localize(None) if hasattr(end_ts, 'tz') and end_ts.tz else end_ts
            
            if start_naive <= d_naive <= end_naive:
                filtered_dates.append(d)
        
        trading_dates = filtered_dates
        
        logger.info(f"Running backtest from {trading_dates[0].date()} to {trading_dates[-1].date()}")
        logger.info(f"Total trading days: {len(trading_dates)}")
        
        # Run through each day
        for date in trading_dates:
            self._process_day(date, signals, signal_column, confidence_column)
            
            # Record equity curve
            self.equity_curve.append((date, self.portfolio.total_value))
        
        # Calculate results
        return self._calculate_results(trading_dates)
    
    def _process_day(
        self,
        date: datetime,
        signals: pd.DataFrame,
        signal_column: str,
        confidence_column: str
    ):
        """Process a single trading day."""
        # Get prices for today
        prices = {}
        for ticker in self.tickers:
            if ticker in self.price_history:
                df = self.price_history[ticker]
                if date in df.index:
                    prices[ticker] = float(df.loc[date, 'close'])
        
        if not prices:
            return
            
        # Update portfolio prices
        self.portfolio.update_prices(prices)
        
        # Check stop loss / take profit for existing positions
        self._check_exits(date, prices)
        
        # Get signals for today
        day_signals = signals[signals.index == date] if hasattr(signals.index, 'date') else \
                      signals[signals['date'] == date] if 'date' in signals.columns else pd.DataFrame()
        
        # Process signals for each ticker
        for ticker in self.tickers:
            if ticker not in prices:
                continue
                
            price = prices[ticker]
            
            # Get ticker signal
            ticker_signal = day_signals[day_signals['ticker'] == ticker] if not day_signals.empty else pd.DataFrame()
            
            if ticker_signal.empty:
                continue
                
            signal_value = float(ticker_signal[signal_column].iloc[0])
            confidence = float(ticker_signal[confidence_column].iloc[0]) if confidence_column in ticker_signal.columns else 0.5
            
            # Apply signal threshold logic
            position = self.portfolio.positions.get(ticker)
            
            if signal_value >= self.buy_threshold and confidence >= 0.5:
                # Buy signal
                if position is None or position.shares == 0:
                    # Calculate position size
                    position_value = self.portfolio.total_value * self.position_size_pct
                    self.portfolio.buy(
                        ticker=ticker,
                        price=price,
                        value=position_value,
                        reason=f"Signal: {signal_value:.2f}, Conf: {confidence:.2f}",
                        timestamp=date
                    )
                    
            elif signal_value <= self.sell_threshold:
                # Sell signal
                if position and position.shares > 0:
                    self.portfolio.sell(
                        ticker=ticker,
                        price=price,
                        reason=f"Signal: {signal_value:.2f}",
                        timestamp=date
                    )
    
    def _check_exits(self, date: datetime, prices: Dict[str, float]):
        """Check stop loss and take profit levels."""
        for ticker in list(self.portfolio.positions.keys()):
            if ticker not in prices:
                continue
                
            position = self.portfolio.positions[ticker]
            price = prices[ticker]
            pnl_pct = position.unrealized_pnl_pct
            
            if pnl_pct <= -self.stop_loss_pct:
                # Stop loss triggered
                self.portfolio.sell(
                    ticker=ticker,
                    price=price,
                    reason=f"Stop loss: {pnl_pct:.1%}",
                    timestamp=date
                )
            elif pnl_pct >= self.take_profit_pct:
                # Take profit triggered
                self.portfolio.sell(
                    ticker=ticker,
                    price=price,
                    reason=f"Take profit: {pnl_pct:.1%}",
                    timestamp=date
                )
    
    def _generate_simulated_signals(self) -> pd.DataFrame:
        """Generate simulated signals based on price momentum."""
        signals = []
        
        for ticker in self.tickers:
            if ticker not in self.price_history:
                continue
                
            df = self.price_history[ticker].copy()
            
            # Simple momentum signal: 5-day return
            df['return_5d'] = df['close'].pct_change(5)
            # RSI-like normalization to -1 to 1 range
            df['signal'] = df['return_5d'].clip(-0.2, 0.2) * 5
            df['confidence'] = 0.6  # Fixed confidence
            df['ticker'] = ticker
            
            signals.append(df[['signal', 'confidence', 'ticker']].dropna())
        
        if not signals:
            return pd.DataFrame()
            
        return pd.concat(signals)
    
    def _calculate_results(self, trading_dates: List[datetime]) -> BacktestResult:
        """Calculate backtest performance metrics."""
        # Build equity curve DataFrame
        equity_df = pd.DataFrame(self.equity_curve, columns=['date', 'value'])
        equity_df.set_index('date', inplace=True)
        
        # Calculate daily returns
        daily_returns = equity_df['value'].pct_change().dropna()
        
        # Calculate metrics
        total_return = (equity_df['value'].iloc[-1] / self.initial_capital) - 1
        
        # Annualized return
        days = (trading_dates[-1] - trading_dates[0]).days
        annualized_return = (1 + total_return) ** (365 / max(days, 1)) - 1
        
        # Sharpe ratio (assuming 0% risk-free rate)
        if len(daily_returns) > 1 and daily_returns.std() > 0:
            sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown
        rolling_max = equity_df['value'].cummax()
        drawdowns = (equity_df['value'] - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # Win rate
        winning_trades = sum(1 for t in self.portfolio.trades 
                           if t.action == TradeAction.SELL and 
                           self._was_winning_trade(t))
        total_sells = sum(1 for t in self.portfolio.trades if t.action == TradeAction.SELL)
        win_rate = winning_trades / total_sells if total_sells > 0 else 0.0
        
        # Benchmark return (buy and hold equal weight)
        benchmark_return = self._calculate_benchmark_return()
        
        # Alpha
        alpha = total_return - benchmark_return
        
        return BacktestResult(
            start_date=trading_dates[0],
            end_date=trading_dates[-1],
            initial_value=self.initial_capital,
            final_value=equity_df['value'].iloc[-1],
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            num_trades=len(self.portfolio.trades),
            benchmark_return=benchmark_return,
            alpha=alpha,
            daily_returns=daily_returns,
            equity_curve=equity_df['value'],
            trades=self.portfolio.trades
        )
    
    def _was_winning_trade(self, sell_trade: Trade) -> bool:
        """Check if a sell trade was profitable."""
        # Find corresponding buy trade
        for trade in reversed(self.portfolio.trades):
            if trade.ticker == sell_trade.ticker and trade.action == TradeAction.BUY:
                return sell_trade.price > trade.price
        return False
    
    def _calculate_benchmark_return(self) -> float:
        """Calculate buy-and-hold benchmark return."""
        if not self.price_history:
            return 0.0
            
        returns = []
        for ticker in self.tickers:
            if ticker in self.price_history:
                df = self.price_history[ticker]
                if len(df) >= 2:
                    start_price = df['close'].iloc[0]
                    end_price = df['close'].iloc[-1]
                    returns.append((end_price / start_price) - 1)
        
        return np.mean(returns) if returns else 0.0


def run_backtest(
    tickers: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_capital: float = 100000.0
) -> BacktestResult:
    """
    Convenience function to run a backtest.
    
    Args:
        tickers: List of tickers (default: QBTS, IONQ, RGTI, QUBT)
        start_date: Start date (default: 6 months ago)
        end_date: End date (default: today)
        initial_capital: Starting capital
        
    Returns:
        BacktestResult with performance metrics
    """
    if tickers is None:
        tickers = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
        
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
        
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    backtester = Backtester(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital
    )
    
    return backtester.run()


def main():
    """Demo backtest run."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("HERMES Quantum - Backtester Demo")
    print("="*60)
    
    # Run 6-month backtest on quantum stocks
    result = run_backtest(
        tickers=['QBTS', 'IONQ', 'RGTI', 'QUBT'],
        initial_capital=100000.0
    )
    
    print(result.summary())
    
    # Show trade log
    if result.trades:
        print("\nTRADE LOG (Last 10)")
        print("-" * 60)
        for trade in result.trades[-10:]:
            print(f"{trade.timestamp.date()} | {trade.action.value.upper():4} | "
                  f"{trade.ticker:5} | {trade.shares:4} shares @ ${trade.price:.2f}")


if __name__ == "__main__":
    main()
