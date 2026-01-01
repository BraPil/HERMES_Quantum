#!/usr/bin/env python3
"""
Risk Manager with Kelly Sizing
===============================
Manages position sizing, risk controls, and capital allocation.

Features:
- Kelly criterion position sizing
- Dynamic allocation based on market regime
- Cash account T+1 settlement awareness
- Daily loss limits (2% halt)
- Symbol weight optimization (70% QBTS, 20% IONQ, etc.)

Author: HERMES Development Team
Version: 0.1.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Any, Optional
import json

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class MarketRegime(Enum):
    """Market regime classification"""
    RISING = "rising"
    FALLING = "falling"
    SIDEWAYS = "sideways"


@dataclass
class AllocationConfig:
    """Allocation configuration per market regime"""
    # Percentage of capital to keep invested (not for trading)
    invested_pct: float
    # Percentage available for intraday buys
    buy_reserve_pct: float
    # Percentage available for intraday sells
    sell_reserve_pct: float
    
    def validate(self):
        """Validate allocation sums to 100%"""
        total = self.invested_pct + self.buy_reserve_pct + self.sell_reserve_pct
        assert abs(total - 100) < 0.01, f"Allocation must sum to 100%, got {total}%"


@dataclass
class SymbolWeight:
    """Weight allocation for a symbol"""
    symbol: str
    weight: float  # 0-1 (e.g., 0.7 for 70%)
    min_weight: float = 0.0
    max_weight: float = 1.0


@dataclass
class Position:
    """Current position in a symbol"""
    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.quantity * self.avg_cost
    
    @property
    def unrealized_pnl(self) -> float:
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis > 0:
            return (self.unrealized_pnl / self.cost_basis) * 100
        return 0.0


@dataclass
class DailyPnL:
    """Daily P&L tracking"""
    date: date
    starting_balance: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    trades_count: int = 0
    
    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def pnl_pct(self) -> float:
        if self.starting_balance > 0:
            return (self.total_pnl / self.starting_balance) * 100
        return 0.0


@dataclass
class OrderSizing:
    """Result of position sizing calculation"""
    symbol: str
    shares: int
    dollar_amount: float
    risk_amount: float
    confidence: float
    kelly_fraction: float
    approved: bool
    reason: str = ""


# =============================================================================
# KELLY CRITERION CALCULATOR
# =============================================================================

class KellyCalculator:
    """
    Kelly Criterion position sizing.
    
    Kelly formula: f* = (p * b - q) / b
    Where:
        p = probability of winning
        b = win/loss ratio
        q = probability of losing (1 - p)
        f* = fraction of bankroll to bet
    
    We use fractional Kelly (typically 25-50%) for safety.
    """
    
    DEFAULT_KELLY_FRACTION = 0.25  # Use 25% of full Kelly
    
    def __init__(self, kelly_fraction: float = DEFAULT_KELLY_FRACTION):
        self.kelly_fraction = kelly_fraction
        self._trade_history: list[dict] = []
    
    def record_trade(self, symbol: str, pnl: float, entry_price: float):
        """Record a trade for Kelly calculation"""
        self._trade_history.append({
            "symbol": symbol,
            "pnl": pnl,
            "pnl_pct": pnl / entry_price if entry_price > 0 else 0,
            "win": pnl > 0,
            "timestamp": datetime.now()
        })
    
    def calculate_kelly(
        self,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        symbol: Optional[str] = None
    ) -> float:
        """
        Calculate Kelly fraction.
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount
            symbol: Optional symbol to filter history
            
        Returns:
            Optimal Kelly fraction (0-1)
        """
        # Use historical data if not provided
        if win_rate is None or avg_win is None or avg_loss is None:
            history = self._trade_history
            if symbol:
                history = [t for t in history if t["symbol"] == symbol]
            
            if len(history) < 10:
                # Not enough history, use conservative defaults
                return 0.1  # 10% position size
            
            wins = [t for t in history if t["win"]]
            losses = [t for t in history if not t["win"]]
            
            win_rate = len(wins) / len(history)
            avg_win = np.mean([t["pnl_pct"] for t in wins]) if wins else 0.05
            avg_loss = abs(np.mean([t["pnl_pct"] for t in losses])) if losses else 0.03
        
        # Kelly formula
        if avg_loss == 0:
            return 0.1  # Avoid division by zero
        
        b = avg_win / avg_loss  # Win/loss ratio
        q = 1 - win_rate
        
        kelly = (win_rate * b - q) / b
        
        # Apply fractional Kelly
        kelly = max(0, kelly) * self.kelly_fraction
        
        # Clamp to reasonable range
        kelly = min(0.5, max(0, kelly))  # Max 50% of capital
        
        return kelly
    
    def calculate_position_size(
        self,
        capital: float,
        price: float,
        confidence: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> OrderSizing:
        """
        Calculate position size using Kelly criterion.
        
        Args:
            capital: Available capital
            price: Current stock price
            confidence: Signal confidence (0-100)
            
        Returns:
            OrderSizing with recommended shares
        """
        # Adjust win rate based on confidence
        if win_rate is None:
            win_rate = confidence / 100 * 0.6 + 0.2  # Scale confidence to 20-80% win rate
        
        kelly = self.calculate_kelly(win_rate, avg_win, avg_loss)
        
        # Further scale by confidence
        adjusted_kelly = kelly * (confidence / 100)
        
        # Calculate dollar amount
        dollar_amount = capital * adjusted_kelly
        
        # Calculate shares
        shares = int(dollar_amount / price) if price > 0 else 0
        
        # Risk amount (assume 2% stop loss)
        risk_amount = shares * price * 0.02
        
        return OrderSizing(
            symbol="",
            shares=shares,
            dollar_amount=shares * price,
            risk_amount=risk_amount,
            confidence=confidence,
            kelly_fraction=adjusted_kelly,
            approved=shares > 0,
            reason=f"Kelly={kelly:.2%}, Adjusted={adjusted_kelly:.2%}"
        )


# =============================================================================
# RISK MANAGER
# =============================================================================

class RiskManager:
    """
    Manages risk and position sizing for trading.
    
    Features:
    - Dynamic allocation based on market regime
    - Cash account T+1 settlement tracking
    - Daily loss limits
    - Symbol weight management
    
    Usage:
        rm = RiskManager(capital=100000)
        rm.set_market_regime(MarketRegime.RISING)
        
        sizing = rm.calculate_order_size("QBTS", 7.50, confidence=90)
        if sizing.approved:
            # Execute order for sizing.shares
    """
    
    # Default regime allocations (from your requirements)
    DEFAULT_ALLOCATIONS = {
        MarketRegime.RISING: AllocationConfig(
            invested_pct=60,      # 60-80% sitting in positions
            buy_reserve_pct=20,   # 10-20% for intraday buys
            sell_reserve_pct=20   # 10-20% for intraday sells
        ),
        MarketRegime.FALLING: AllocationConfig(
            invested_pct=10,      # Very little invested
            buy_reserve_pct=45,   # 40-50% for intraday buys
            sell_reserve_pct=45   # 40-50% for intraday sells
        ),
        MarketRegime.SIDEWAYS: AllocationConfig(
            invested_pct=33,      # Balanced
            buy_reserve_pct=33,   # ~33% for intraday buys
            sell_reserve_pct=34   # ~33% for intraday sells
        )
    }
    
    # Default symbol weights (from your requirements)
    DEFAULT_WEIGHTS = [
        SymbolWeight("QBTS", 0.70, min_weight=0.4, max_weight=0.9),
        SymbolWeight("IONQ", 0.20, min_weight=0.1, max_weight=0.4),
        SymbolWeight("RGTI", 0.05, min_weight=0.0, max_weight=0.2),
        SymbolWeight("QUBT", 0.05, min_weight=0.0, max_weight=0.2),
    ]
    
    # Risk limits
    MAX_DAILY_LOSS_PCT = 2.0  # 2% daily loss limit
    MIN_CONFIDENCE = 85.0     # Minimum confidence to trade
    MIN_RESERVE_TRADES = 2    # Keep reserve for at least 2 more trades
    
    def __init__(
        self,
        capital: float,
        weights: Optional[list[SymbolWeight]] = None,
        allocations: Optional[dict[MarketRegime, AllocationConfig]] = None
    ):
        self.total_capital = capital
        self.available_cash = capital
        self.weights = {w.symbol: w for w in (weights or self.DEFAULT_WEIGHTS)}
        self.allocations = allocations or self.DEFAULT_ALLOCATIONS
        
        # State
        self._regime = MarketRegime.SIDEWAYS
        self._positions: dict[str, Position] = {}
        self._daily_pnl = DailyPnL(date=date.today(), starting_balance=capital)
        self._kelly = KellyCalculator()
        
        # T+1 settlement tracking
        self._unsettled_funds: dict[date, float] = {}  # date -> amount
        
        # Trading controls
        self._halted = False
        self._halt_reason = ""
    
    @property
    def market_regime(self) -> MarketRegime:
        return self._regime
    
    @property
    def is_halted(self) -> bool:
        return self._halted
    
    @property
    def current_allocation(self) -> AllocationConfig:
        return self.allocations[self._regime]
    
    @property
    def settled_cash(self) -> float:
        """Cash available for trading (excludes unsettled T+1 funds)"""
        unsettled = sum(self._unsettled_funds.values())
        return max(0, self.available_cash - unsettled)
    
    @property
    def invested_value(self) -> float:
        """Total value of current positions"""
        return sum(p.market_value for p in self._positions.values())
    
    @property
    def total_equity(self) -> float:
        """Total account value (cash + positions)"""
        return self.available_cash + self.invested_value
    
    @property
    def daily_pnl_pct(self) -> float:
        """Current daily P&L percentage"""
        return self._daily_pnl.pnl_pct
    
    def set_market_regime(self, regime: MarketRegime):
        """Set the current market regime"""
        old_regime = self._regime
        self._regime = regime
        logger.info(f"📊 Market regime: {old_regime.value} → {regime.value}")
        logger.info(f"   Allocation: {self.current_allocation}")
    
    def update_position(self, symbol: str, quantity: int, avg_cost: float, current_price: float):
        """Update or create a position"""
        if quantity > 0:
            self._positions[symbol] = Position(symbol, quantity, avg_cost, current_price)
        elif symbol in self._positions:
            del self._positions[symbol]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol"""
        return self._positions.get(symbol)
    
    def record_trade(self, symbol: str, pnl: float, settlement_date: Optional[date] = None):
        """
        Record a trade for tracking.
        
        Args:
            symbol: Stock symbol
            pnl: Realized P&L from trade
            settlement_date: When funds settle (T+1 for US stocks)
        """
        self._daily_pnl.realized_pnl += pnl
        self._daily_pnl.trades_count += 1
        
        # Track for Kelly
        self._kelly.record_trade(symbol, pnl, 0)  # entry_price not tracked here
        
        # Track unsettled funds (T+1)
        if settlement_date is None:
            settlement_date = date.today() + timedelta(days=1)
        
        if settlement_date not in self._unsettled_funds:
            self._unsettled_funds[settlement_date] = 0
        self._unsettled_funds[settlement_date] += abs(pnl)
        
        # Check daily loss limit
        self._check_loss_limit()
        
        logger.info(f"💰 Trade recorded: {symbol} P&L=${pnl:.2f}, Daily P&L={self._daily_pnl.pnl_pct:.2f}%")
    
    def settle_funds(self):
        """Settle funds that have reached T+1"""
        today = date.today()
        settled = []
        for settle_date, amount in list(self._unsettled_funds.items()):
            if settle_date <= today:
                settled.append(settle_date)
                logger.info(f"💵 Funds settled: ${amount:.2f}")
        
        for d in settled:
            del self._unsettled_funds[d]
    
    def _check_loss_limit(self):
        """Check if daily loss limit hit"""
        if self._daily_pnl.pnl_pct <= -self.MAX_DAILY_LOSS_PCT:
            self._halted = True
            self._halt_reason = f"Daily loss limit ({self.MAX_DAILY_LOSS_PCT}%) reached"
            logger.warning(f"🛑 TRADING HALTED: {self._halt_reason}")
    
    def reset_daily(self):
        """Reset daily tracking (call at market open)"""
        self._daily_pnl = DailyPnL(
            date=date.today(),
            starting_balance=self.total_equity
        )
        self._halted = False
        self._halt_reason = ""
        self.settle_funds()
        logger.info("🌅 Daily reset complete")
    
    def get_symbol_weight(self, symbol: str) -> float:
        """Get weight allocation for a symbol"""
        if symbol in self.weights:
            return self.weights[symbol].weight
        return 0.0
    
    def get_available_capital_for_symbol(self, symbol: str) -> float:
        """
        Calculate available capital for a specific symbol.
        
        Takes into account:
        - Market regime allocation
        - Symbol weight
        - Settled cash
        - Existing positions
        """
        allocation = self.current_allocation
        weight = self.get_symbol_weight(symbol)
        
        # Total available for new buys
        buy_capital = self.settled_cash * (allocation.buy_reserve_pct / 100)
        
        # Weight-adjusted capital
        symbol_capital = buy_capital * weight
        
        # Reserve for other opportunities
        min_reserve = buy_capital / (self.MIN_RESERVE_TRADES + 1)
        symbol_capital = min(symbol_capital, buy_capital - min_reserve)
        
        return max(0, symbol_capital)
    
    def calculate_order_size(
        self,
        symbol: str,
        price: float,
        confidence: float,
        is_buy: bool = True
    ) -> OrderSizing:
        """
        Calculate order size using Kelly criterion and risk rules.
        
        Args:
            symbol: Stock symbol
            price: Current price
            confidence: Signal confidence (0-100)
            is_buy: True for buy, False for sell
            
        Returns:
            OrderSizing with approval and reasoning
        """
        # Check if halted
        if self._halted:
            return OrderSizing(
                symbol=symbol,
                shares=0,
                dollar_amount=0,
                risk_amount=0,
                confidence=confidence,
                kelly_fraction=0,
                approved=False,
                reason=f"Trading halted: {self._halt_reason}"
            )
        
        # Check confidence threshold
        if confidence < self.MIN_CONFIDENCE:
            return OrderSizing(
                symbol=symbol,
                shares=0,
                dollar_amount=0,
                risk_amount=0,
                confidence=confidence,
                kelly_fraction=0,
                approved=False,
                reason=f"Confidence {confidence:.0f}% below threshold {self.MIN_CONFIDENCE}%"
            )
        
        if is_buy:
            # Get available capital for this symbol
            available = self.get_available_capital_for_symbol(symbol)
            
            if available <= 0:
                return OrderSizing(
                    symbol=symbol,
                    shares=0,
                    dollar_amount=0,
                    risk_amount=0,
                    confidence=confidence,
                    kelly_fraction=0,
                    approved=False,
                    reason="No capital available for this symbol"
                )
            
            # Calculate Kelly-based sizing
            sizing = self._kelly.calculate_position_size(
                capital=available,
                price=price,
                confidence=confidence
            )
            sizing.symbol = symbol
            
            # Ensure we can afford at least 1 share
            if sizing.shares < 1 and available >= price:
                sizing.shares = 1
                sizing.dollar_amount = price
                sizing.approved = True
                sizing.reason = "Minimum 1 share"
            
            return sizing
            
        else:
            # Sell - check position
            position = self.get_position(symbol)
            if not position or position.quantity <= 0:
                return OrderSizing(
                    symbol=symbol,
                    shares=0,
                    dollar_amount=0,
                    risk_amount=0,
                    confidence=confidence,
                    kelly_fraction=0,
                    approved=False,
                    reason="No position to sell"
                )
            
            # Calculate sell size (can sell partial or full position)
            kelly = self._kelly.calculate_kelly()
            sell_pct = min(1.0, kelly * (confidence / 100))
            shares = max(1, int(position.quantity * sell_pct))
            
            return OrderSizing(
                symbol=symbol,
                shares=shares,
                dollar_amount=shares * price,
                risk_amount=0,
                confidence=confidence,
                kelly_fraction=sell_pct,
                approved=True,
                reason=f"Selling {sell_pct:.0%} of position"
            )
    
    def get_portfolio_summary(self) -> dict:
        """Get complete portfolio summary"""
        return {
            "total_equity": self.total_equity,
            "available_cash": self.available_cash,
            "settled_cash": self.settled_cash,
            "invested_value": self.invested_value,
            "market_regime": self._regime.value,
            "allocation": {
                "invested_pct": self.current_allocation.invested_pct,
                "buy_reserve_pct": self.current_allocation.buy_reserve_pct,
                "sell_reserve_pct": self.current_allocation.sell_reserve_pct
            },
            "positions": {
                s: {
                    "quantity": p.quantity,
                    "avg_cost": p.avg_cost,
                    "current_price": p.current_price,
                    "market_value": p.market_value,
                    "unrealized_pnl": p.unrealized_pnl,
                    "unrealized_pnl_pct": p.unrealized_pnl_pct
                }
                for s, p in self._positions.items()
            },
            "daily_pnl": {
                "realized": self._daily_pnl.realized_pnl,
                "unrealized": self._daily_pnl.unrealized_pnl,
                "total": self._daily_pnl.total_pnl,
                "pct": self._daily_pnl.pnl_pct,
                "trades": self._daily_pnl.trades_count
            },
            "weights": {s: w.weight for s, w in self.weights.items()},
            "halted": self._halted,
            "halt_reason": self._halt_reason
        }


# =============================================================================
# MAIN - TEST THE MODULE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Risk Manager Test")
    print("=" * 60)
    
    # Create risk manager with $100,000 capital
    rm = RiskManager(capital=100_000)
    
    print("\n📊 Portfolio Summary (Initial)")
    print("-" * 40)
    summary = rm.get_portfolio_summary()
    print(f"  Total Equity: ${summary['total_equity']:,.2f}")
    print(f"  Market Regime: {summary['market_regime']}")
    print(f"  Symbol Weights: {summary['weights']}")
    
    # Test different market regimes
    print("\n🔄 Testing Market Regimes")
    print("-" * 40)
    
    for regime in MarketRegime:
        rm.set_market_regime(regime)
        alloc = rm.current_allocation
        print(f"\n  {regime.value.upper()}:")
        print(f"    Invested: {alloc.invested_pct}%")
        print(f"    Buy Reserve: {alloc.buy_reserve_pct}%")
        print(f"    Sell Reserve: {alloc.sell_reserve_pct}%")
    
    # Test order sizing
    rm.set_market_regime(MarketRegime.RISING)
    
    print("\n📈 Order Sizing Test (RISING market)")
    print("-" * 40)
    
    test_cases = [
        ("QBTS", 7.50, 90),   # High confidence, main focus
        ("IONQ", 45.00, 85),  # At threshold
        ("RGTI", 12.00, 75),  # Below threshold
        ("QUBT", 8.00, 95),   # High confidence, small weight
    ]
    
    for symbol, price, confidence in test_cases:
        sizing = rm.calculate_order_size(symbol, price, confidence)
        status = "✅" if sizing.approved else "❌"
        print(f"\n  {status} {symbol} @ ${price:.2f} ({confidence}% conf)")
        print(f"      Shares: {sizing.shares}")
        print(f"      Amount: ${sizing.dollar_amount:.2f}")
        print(f"      Kelly: {sizing.kelly_fraction:.2%}")
        print(f"      Reason: {sizing.reason}")
    
    # Test loss limit
    print("\n🛑 Testing Daily Loss Limit")
    print("-" * 40)
    
    # Simulate losses
    rm.record_trade("QBTS", -500)  # $500 loss
    print(f"  Daily P&L after -$500: {rm.daily_pnl_pct:.2f}%")
    
    rm.record_trade("QBTS", -1500)  # $1500 more loss (total -$2000 = -2%)
    print(f"  Daily P&L after -$1500 more: {rm.daily_pnl_pct:.2f}%")
    print(f"  Halted: {rm.is_halted}")
    
    # Try to trade while halted
    sizing = rm.calculate_order_size("QBTS", 7.50, 95)
    print(f"  Order attempt while halted: {sizing.reason}")
    
    print("\n" + "=" * 60)
    print("✅ Risk manager test complete!")
    print("=" * 60)
