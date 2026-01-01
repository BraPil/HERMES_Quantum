"""
HERMES Quantum - Risk Management Module
========================================
Position sizing, risk controls, and portfolio risk management.

Features:
- Position sizing based on risk budget (Kelly Criterion, fixed %)
- Stop-loss and take-profit automation
- Portfolio-level risk limits (max drawdown, concentration)
- Volatility-adjusted position sizing
- Risk metrics calculation

Created: 2026-01-01
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED_PERCENT = "fixed_percent"
    KELLY = "kelly"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    EQUAL_WEIGHT = "equal_weight"


@dataclass
class RiskLimits:
    """Portfolio risk limits configuration."""
    # Position limits
    max_position_pct: float = 0.25  # Max 25% in single position
    min_position_pct: float = 0.05  # Min 5% per position
    max_positions: int = 10  # Max number of positions
    
    # Loss limits
    max_daily_loss_pct: float = 0.05  # Max 5% daily loss
    max_weekly_loss_pct: float = 0.10  # Max 10% weekly loss
    max_drawdown_pct: float = 0.20  # Max 20% drawdown from peak
    
    # Trade limits
    stop_loss_pct: float = 0.10  # Default 10% stop loss
    take_profit_pct: float = 0.25  # Default 25% take profit
    trailing_stop_pct: float = 0.05  # 5% trailing stop
    
    # Volatility limits
    max_portfolio_volatility: float = 0.30  # Max 30% annualized vol
    max_position_volatility: float = 0.50  # Max 50% annualized vol for single position


@dataclass
class PositionRisk:
    """Risk metrics for a single position."""
    ticker: str
    shares: int
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    trailing_stop: Optional[float] = None
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk 95%
    
    @property
    def position_value(self) -> float:
        return self.shares * self.current_price
    
    @property
    def pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.shares
    
    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price
    
    @property
    def risk_to_stop(self) -> float:
        """Capital at risk if stop loss is hit."""
        return self.shares * (self.entry_price - self.stop_loss)
    
    @property
    def reward_to_target(self) -> float:
        """Potential profit if take profit is hit."""
        return self.shares * (self.take_profit - self.current_price)
    
    @property
    def risk_reward_ratio(self) -> float:
        """Risk/reward ratio."""
        if self.risk_to_stop <= 0:
            return 0.0
        return self.reward_to_target / self.risk_to_stop
    
    def should_stop_out(self) -> bool:
        """Check if position should be stopped out."""
        return self.current_price <= self.stop_loss
    
    def should_take_profit(self) -> bool:
        """Check if position should take profit."""
        return self.current_price >= self.take_profit
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "shares": self.shares,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "position_value": self.position_value,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_stop": self.trailing_stop,
            "volatility": self.volatility,
            "var_95": self.var_95,
            "risk_to_stop": self.risk_to_stop,
            "risk_reward_ratio": self.risk_reward_ratio
        }


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics."""
    total_value: float
    cash: float
    positions_value: float
    num_positions: int
    total_pnl: float
    total_pnl_pct: float
    daily_var_95: float
    portfolio_volatility: float
    max_drawdown: float
    current_drawdown: float
    concentration_risk: float  # Herfindahl index
    risk_level: RiskLevel
    position_risks: Dict[str, PositionRisk] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_value": self.total_value,
            "cash": self.cash,
            "positions_value": self.positions_value,
            "num_positions": self.num_positions,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "daily_var_95": self.daily_var_95,
            "portfolio_volatility": self.portfolio_volatility,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "concentration_risk": self.concentration_risk,
            "risk_level": self.risk_level.value,
            "positions": {k: v.to_dict() for k, v in self.position_risks.items()}
        }


class RiskManager:
    """
    Portfolio risk management and position sizing.
    
    Usage:
        risk_mgr = RiskManager(initial_capital=100000)
        
        # Calculate position size for a new trade
        size = risk_mgr.calculate_position_size(
            ticker='QBTS',
            signal_strength=0.8,
            current_price=4.50,
            volatility=0.45
        )
        
        # Check if trade is allowed by risk limits
        if risk_mgr.check_trade_allowed('QBTS', size.shares, size.entry_price):
            # Execute trade
            risk_mgr.add_position('QBTS', shares, entry_price)
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        limits: Optional[RiskLimits] = None,
        sizing_method: SizingMethod = SizingMethod.VOLATILITY_ADJUSTED
    ):
        self.initial_capital = initial_capital
        self.limits = limits or RiskLimits()
        self.sizing_method = sizing_method
        
        # Portfolio state
        self.cash = initial_capital
        self.positions: Dict[str, PositionRisk] = {}
        self.peak_value = initial_capital
        self.daily_pnl_history: List[Tuple[datetime, float]] = []
        
        # Historical prices for volatility calculation
        self.price_history: Dict[str, pd.Series] = {}
        
        logger.info(f"RiskManager initialized with ${initial_capital:,.2f} capital")
    
    @property
    def total_value(self) -> float:
        """Current portfolio value."""
        positions_value = sum(p.position_value for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak."""
        if self.peak_value <= 0:
            return 0.0
        return (self.peak_value - self.total_value) / self.peak_value
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions."""
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].current_price = price
                
                # Update trailing stop if applicable
                pos = self.positions[ticker]
                if pos.trailing_stop:
                    new_stop = price * (1 - self.limits.trailing_stop_pct)
                    pos.trailing_stop = max(pos.trailing_stop, new_stop)
        
        # Update peak value
        current = self.total_value
        self.peak_value = max(self.peak_value, current)
    
    def calculate_volatility(self, ticker: str, prices: pd.Series = None) -> float:
        """Calculate annualized volatility for a ticker."""
        if prices is not None:
            self.price_history[ticker] = prices
        
        if ticker not in self.price_history:
            return 0.30  # Default 30% volatility
        
        prices = self.price_history[ticker]
        if len(prices) < 20:
            return 0.30
        
        returns = prices.pct_change().dropna()
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252)
        
        return float(annualized_vol)
    
    def calculate_position_size(
        self,
        ticker: str,
        signal_strength: float,
        current_price: float,
        volatility: float = None,
        win_rate: float = 0.55
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size.
        
        Args:
            ticker: Stock ticker
            signal_strength: Signal strength (0 to 1)
            current_price: Current stock price
            volatility: Annualized volatility (optional, will calculate if not provided)
            win_rate: Historical win rate for Kelly criterion
            
        Returns:
            Dict with shares, value, stop_loss, take_profit
        """
        if volatility is None:
            volatility = self.calculate_volatility(ticker)
        
        # Base position as percentage of portfolio
        if self.sizing_method == SizingMethod.FIXED_PERCENT:
            base_pct = self.limits.max_position_pct
            
        elif self.sizing_method == SizingMethod.KELLY:
            # Kelly Criterion: f* = (p*b - q) / b
            # where p = win rate, q = loss rate, b = win/loss ratio
            avg_win = self.limits.take_profit_pct
            avg_loss = self.limits.stop_loss_pct
            b = avg_win / avg_loss if avg_loss > 0 else 1
            q = 1 - win_rate
            kelly = (win_rate * b - q) / b if b > 0 else 0
            # Use half-Kelly for safety
            base_pct = min(kelly * 0.5, self.limits.max_position_pct)
            base_pct = max(base_pct, 0)
            
        elif self.sizing_method == SizingMethod.VOLATILITY_ADJUSTED:
            # Target a fixed contribution to portfolio volatility
            target_vol_contribution = 0.05  # 5% volatility contribution
            if volatility > 0:
                base_pct = target_vol_contribution / volatility
            else:
                base_pct = self.limits.max_position_pct
            base_pct = min(base_pct, self.limits.max_position_pct)
            
        elif self.sizing_method == SizingMethod.EQUAL_WEIGHT:
            base_pct = 1.0 / max(self.limits.max_positions, 1)
        else:
            base_pct = self.limits.max_position_pct
        
        # Adjust by signal strength
        adjusted_pct = base_pct * signal_strength
        
        # Apply limits
        adjusted_pct = max(self.limits.min_position_pct, 
                          min(adjusted_pct, self.limits.max_position_pct))
        
        # Calculate position value and shares
        position_value = self.total_value * adjusted_pct
        shares = int(position_value / current_price)
        
        # Calculate stop loss and take profit
        stop_loss = current_price * (1 - self.limits.stop_loss_pct)
        take_profit = current_price * (1 + self.limits.take_profit_pct)
        
        # Calculate risk metrics
        risk_per_share = current_price - stop_loss
        total_risk = shares * risk_per_share
        
        return {
            "ticker": ticker,
            "shares": shares,
            "entry_price": current_price,
            "position_value": shares * current_price,
            "position_pct": (shares * current_price) / self.total_value,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_per_share": risk_per_share,
            "total_risk": total_risk,
            "risk_pct": total_risk / self.total_value,
            "volatility": volatility,
            "sizing_method": self.sizing_method.value
        }
    
    def check_trade_allowed(
        self,
        ticker: str,
        shares: int,
        price: float,
        is_buy: bool = True
    ) -> Tuple[bool, str]:
        """
        Check if a trade is allowed by risk limits.
        
        Returns:
            Tuple of (allowed, reason)
        """
        if is_buy:
            # Check cash availability
            cost = shares * price
            if cost > self.cash:
                return False, f"Insufficient cash: need ${cost:,.2f}, have ${self.cash:,.2f}"
            
            # Check position limits
            if len(self.positions) >= self.limits.max_positions and ticker not in self.positions:
                return False, f"Max positions reached: {self.limits.max_positions}"
            
            # Check concentration limit
            new_position_pct = (shares * price) / self.total_value
            if new_position_pct > self.limits.max_position_pct:
                return False, f"Position too large: {new_position_pct:.1%} > {self.limits.max_position_pct:.1%}"
            
            # Check drawdown limit
            if self.current_drawdown >= self.limits.max_drawdown_pct:
                return False, f"Max drawdown reached: {self.current_drawdown:.1%}"
            
            # Check daily loss limit
            daily_pnl_pct = self._get_daily_pnl_pct()
            if daily_pnl_pct <= -self.limits.max_daily_loss_pct:
                return False, f"Daily loss limit reached: {daily_pnl_pct:.1%}"
        
        return True, "Trade allowed"
    
    def _get_daily_pnl_pct(self) -> float:
        """Get today's P&L percentage."""
        today = datetime.now().date()
        today_pnl = [pnl for dt, pnl in self.daily_pnl_history 
                     if dt.date() == today]
        if not today_pnl:
            return 0.0
        return sum(today_pnl) / self.initial_capital
    
    def add_position(
        self,
        ticker: str,
        shares: int,
        entry_price: float,
        stop_loss: float = None,
        take_profit: float = None
    ) -> PositionRisk:
        """Add a new position or increase existing."""
        if stop_loss is None:
            stop_loss = entry_price * (1 - self.limits.stop_loss_pct)
        if take_profit is None:
            take_profit = entry_price * (1 + self.limits.take_profit_pct)
        
        volatility = self.calculate_volatility(ticker)
        
        # Calculate VaR
        position_value = shares * entry_price
        var_95 = position_value * volatility * 2.33 / np.sqrt(252)  # 1-day 95% VaR
        
        if ticker in self.positions:
            # Update existing position
            pos = self.positions[ticker]
            total_shares = pos.shares + shares
            total_cost = pos.shares * pos.entry_price + shares * entry_price
            pos.entry_price = total_cost / total_shares
            pos.shares = total_shares
            pos.stop_loss = stop_loss
            pos.take_profit = take_profit
            pos.volatility = volatility
            pos.var_95 = var_95
        else:
            # New position
            self.positions[ticker] = PositionRisk(
                ticker=ticker,
                shares=shares,
                entry_price=entry_price,
                current_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                volatility=volatility,
                var_95=var_95
            )
        
        # Update cash
        cost = shares * entry_price
        self.cash -= cost
        
        logger.info(f"Added position: {shares} shares of {ticker} @ ${entry_price:.2f}")
        
        return self.positions[ticker]
    
    def close_position(
        self,
        ticker: str,
        exit_price: float,
        shares: int = None
    ) -> Optional[float]:
        """Close a position (full or partial)."""
        if ticker not in self.positions:
            return None
        
        pos = self.positions[ticker]
        
        if shares is None or shares >= pos.shares:
            # Close full position
            shares = pos.shares
            del self.positions[ticker]
        else:
            # Partial close
            pos.shares -= shares
        
        # Calculate P&L
        pnl = (exit_price - pos.entry_price) * shares
        
        # Update cash
        proceeds = shares * exit_price
        self.cash += proceeds
        
        # Record daily P&L
        self.daily_pnl_history.append((datetime.now(), pnl))
        
        logger.info(f"Closed {shares} shares of {ticker} @ ${exit_price:.2f}, PnL: ${pnl:,.2f}")
        
        return pnl
    
    def check_stops(self, prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check all positions for stop-loss and take-profit triggers.
        
        Returns:
            List of positions that should be closed with reason
        """
        self.update_prices(prices)
        triggers = []
        
        for ticker, pos in list(self.positions.items()):
            if pos.should_stop_out():
                triggers.append({
                    "ticker": ticker,
                    "action": "stop_loss",
                    "price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                })
            elif pos.should_take_profit():
                triggers.append({
                    "ticker": ticker,
                    "action": "take_profit",
                    "price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                })
            elif pos.trailing_stop and pos.current_price <= pos.trailing_stop:
                triggers.append({
                    "ticker": ticker,
                    "action": "trailing_stop",
                    "price": pos.current_price,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct
                })
        
        return triggers
    
    def get_portfolio_risk(self) -> PortfolioRisk:
        """Calculate current portfolio risk metrics."""
        total_val = self.total_value
        positions_val = sum(p.position_value for p in self.positions.values())
        total_pnl = sum(p.pnl for p in self.positions.values())
        
        # Portfolio volatility (weighted average)
        if self.positions:
            weights = np.array([p.position_value / total_val for p in self.positions.values()])
            vols = np.array([p.volatility for p in self.positions.values()])
            # Simplified: assume no correlation
            port_vol = np.sqrt(np.sum((weights * vols) ** 2))
        else:
            port_vol = 0.0
        
        # Daily VaR 95%
        daily_var = total_val * port_vol * 2.33 / np.sqrt(252)
        
        # Concentration (Herfindahl index)
        if self.positions:
            weights = [p.position_value / total_val for p in self.positions.values()]
            concentration = sum(w ** 2 for w in weights)
        else:
            concentration = 0.0
        
        # Risk level
        if self.current_drawdown >= 0.15 or port_vol >= 0.40:
            risk_level = RiskLevel.EXTREME
        elif self.current_drawdown >= 0.10 or port_vol >= 0.30:
            risk_level = RiskLevel.HIGH
        elif self.current_drawdown >= 0.05 or port_vol >= 0.20:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return PortfolioRisk(
            total_value=total_val,
            cash=self.cash,
            positions_value=positions_val,
            num_positions=len(self.positions),
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl / self.initial_capital if self.initial_capital > 0 else 0,
            daily_var_95=daily_var,
            portfolio_volatility=port_vol,
            max_drawdown=self.current_drawdown,
            current_drawdown=self.current_drawdown,
            concentration_risk=concentration,
            risk_level=risk_level,
            position_risks=self.positions.copy()
        )
    
    def get_risk_report(self) -> str:
        """Generate risk report."""
        risk = self.get_portfolio_risk()
        
        report = f"""
========================================
PORTFOLIO RISK REPORT
========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PORTFOLIO OVERVIEW
------------------
Total Value:       ${risk.total_value:,.2f}
Cash:              ${risk.cash:,.2f}
Positions Value:   ${risk.positions_value:,.2f}
Positions:         {risk.num_positions}

P&L
---
Total P&L:         ${risk.total_pnl:,.2f} ({risk.total_pnl_pct:.2%})
Current Drawdown:  {risk.current_drawdown:.2%}

RISK METRICS
------------
Portfolio Vol:     {risk.portfolio_volatility:.1%} (annualized)
Daily VaR (95%):   ${risk.daily_var_95:,.2f}
Concentration:     {risk.concentration_risk:.2f}
Risk Level:        {risk.risk_level.value.upper()}

POSITIONS
---------"""
        
        for ticker, pos in risk.position_risks.items():
            report += f"""
{ticker}:
  Shares:        {pos.shares}
  Entry:         ${pos.entry_price:.2f}
  Current:       ${pos.current_price:.2f}
  P&L:           ${pos.pnl:,.2f} ({pos.pnl_pct:.2%})
  Stop Loss:     ${pos.stop_loss:.2f}
  Take Profit:   ${pos.take_profit:.2f}
  R/R Ratio:     {pos.risk_reward_ratio:.2f}"""
        
        report += "\n" + "="*40
        
        return report


def main():
    """Demo risk manager functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("HERMES Quantum - Risk Manager Demo")
    print("="*60)
    
    # Initialize risk manager
    risk_mgr = RiskManager(
        initial_capital=100000.0,
        sizing_method=SizingMethod.VOLATILITY_ADJUSTED
    )
    
    # Calculate position sizes for sample signals
    tickers = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
    prices = {'QBTS': 4.27, 'IONQ': 8.15, 'RGTI': 2.45, 'QUBT': 3.82}
    signals = {'QBTS': 0.8, 'IONQ': 0.6, 'RGTI': 0.4, 'QUBT': 0.7}
    
    print("\nPOSITION SIZING")
    print("-"*60)
    
    for ticker in tickers:
        size = risk_mgr.calculate_position_size(
            ticker=ticker,
            signal_strength=signals[ticker],
            current_price=prices[ticker],
            volatility=0.45  # 45% vol for quantum stocks
        )
        print(f"\n{ticker} (Signal: {signals[ticker]:.1f}, Price: ${prices[ticker]:.2f}):")
        print(f"  Shares: {size['shares']}")
        print(f"  Value: ${size['position_value']:,.2f} ({size['position_pct']:.1%})")
        print(f"  Stop Loss: ${size['stop_loss']:.2f}")
        print(f"  Take Profit: ${size['take_profit']:.2f}")
        print(f"  Risk: ${size['total_risk']:,.2f} ({size['risk_pct']:.2%})")
        
        # Check if trade allowed
        allowed, reason = risk_mgr.check_trade_allowed(
            ticker, size['shares'], prices[ticker]
        )
        
        if allowed:
            risk_mgr.add_position(
                ticker=ticker,
                shares=size['shares'],
                entry_price=prices[ticker],
                stop_loss=size['stop_loss'],
                take_profit=size['take_profit']
            )
    
    # Print risk report
    print(risk_mgr.get_risk_report())
    
    # Simulate price changes
    print("\nSIMULATED PRICE CHANGES")
    print("-"*60)
    
    new_prices = {'QBTS': 3.85, 'IONQ': 8.50, 'RGTI': 2.20, 'QUBT': 4.10}
    
    # Check for stop triggers
    triggers = risk_mgr.check_stops(new_prices)
    
    if triggers:
        print("\nTRIGGERS DETECTED:")
        for t in triggers:
            print(f"  {t['ticker']}: {t['action']} @ ${t['price']:.2f} (P&L: {t['pnl_pct']:.1%})")
    
    # Updated risk report
    print(risk_mgr.get_risk_report())


if __name__ == "__main__":
    main()
