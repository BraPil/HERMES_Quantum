#!/usr/bin/env python3
"""
Execution Bridge
=================
Bridges trading signals to IBKR execution.

Features:
- Converts signals to orders
- Manages order lifecycle
- Tracks fills and P&L
- Integrates with risk manager

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Any, Callable, Optional
import json
from pathlib import Path

# Python 3.14+ compatibility
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

class ExecutionMode(Enum):
    """Execution modes"""
    PAPER = "paper"    # Paper trading only
    LIVE = "live"      # Live trading (use with caution!)
    SIMULATED = "simulated"  # Local simulation (no IBKR)


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    mode: ExecutionMode = ExecutionMode.PAPER
    host: str = "127.0.0.1"
    port: int = 7497  # 7497 for paper, 7496 for live
    client_id: int = 1
    min_confidence: float = 85.0
    use_limit_orders: bool = True
    limit_offset_pct: float = 0.5  # Limit price offset from last
    
    # Trading hours (ET)
    market_open: time = time(9, 30)
    market_close: time = time(16, 0)


@dataclass
class OrderRequest:
    """Order request from signal"""
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    order_type: str  # "MARKET" or "LIMIT"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    confidence: float = 0.0
    signal_reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of order execution"""
    order_id: int
    symbol: str
    side: str
    quantity: int
    status: str
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_filled(self) -> bool:
        return self.status == "Filled"
    
    @property
    def total_value(self) -> float:
        return self.filled_quantity * self.avg_fill_price


# =============================================================================
# EXECUTION BRIDGE
# =============================================================================

class ExecutionBridge:
    """
    Bridges trading signals to IBKR execution.
    
    Usage:
        bridge = ExecutionBridge(config)
        bridge.connect()
        
        # From signal
        result = bridge.execute_signal(signal, sizing)
        
        bridge.disconnect()
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self._connected = False
        self._ib = None
        self._orders: dict[int, ExecutionResult] = {}
        self._callbacks: list[Callable[[ExecutionResult], None]] = []
        
        # Track P&L
        self._realized_pnl = 0.0
        self._trade_count = 0
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    @property
    def is_paper_trading(self) -> bool:
        return self.config.mode == ExecutionMode.PAPER
    
    def on_execution(self, callback: Callable[[ExecutionResult], None]):
        """Register callback for execution updates"""
        self._callbacks.append(callback)
    
    def _notify_execution(self, result: ExecutionResult):
        """Notify callbacks of execution"""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Execution callback error: {e}")
    
    def connect(self) -> bool:
        """Connect to IBKR"""
        if self.config.mode == ExecutionMode.SIMULATED:
            self._connected = True
            logger.info("✅ Execution bridge: Simulated mode (no IBKR)")
            return True
        
        try:
            from ib_insync import IB
            
            self._ib = IB()
            self._ib.connect(
                self.config.host,
                self.config.port,
                clientId=self.config.client_id,
                timeout=30
            )
            
            self._connected = True
            mode_str = "PAPER" if self.is_paper_trading else "LIVE"
            logger.info(f"✅ Execution bridge connected ({mode_str} mode)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Execution bridge connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self._ib and self._connected:
            self._ib.disconnect()
        self._connected = False
        logger.info("📴 Execution bridge disconnected")
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        current_time = now.time()
        weekday = now.weekday()
        
        # Market closed on weekends
        if weekday >= 5:
            return False
        
        # Check trading hours
        return self.config.market_open <= current_time <= self.config.market_close
    
    def _create_order(self, request: OrderRequest):
        """Create IBKR order object"""
        from ib_insync import LimitOrder, MarketOrder, Stock
        
        contract = Stock(request.symbol, 'SMART', 'USD')
        self._ib.qualifyContracts(contract)
        
        if request.order_type == "LIMIT" and request.limit_price:
            order = LimitOrder(request.side, request.quantity, request.limit_price)
            order.tif = 'GTC'  # Good till cancelled
        else:
            order = MarketOrder(request.side, request.quantity)
            order.tif = 'DAY' if self.is_market_open() else 'GTC'
        
        return contract, order
    
    def execute_order(self, request: OrderRequest) -> ExecutionResult:
        """
        Execute an order request.
        
        Args:
            request: OrderRequest with trade details
            
        Returns:
            ExecutionResult with fill info
        """
        if not self._connected:
            return ExecutionResult(
                order_id=0,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status="Rejected",
                message="Not connected to IBKR"
            )
        
        # Simulated mode - just log
        if self.config.mode == ExecutionMode.SIMULATED:
            result = ExecutionResult(
                order_id=self._trade_count + 1,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status="Simulated",
                filled_quantity=request.quantity,
                avg_fill_price=request.limit_price or 0.0,
                message="Simulated execution"
            )
            self._trade_count += 1
            logger.info(f"🎮 Simulated: {request.side} {request.quantity} {request.symbol}")
            self._notify_execution(result)
            return result
        
        try:
            # Create and place order
            contract, order = self._create_order(request)
            
            logger.info(f"📝 Placing order: {request.side} {request.quantity} {request.symbol} @ {request.order_type}")
            
            trade = self._ib.placeOrder(contract, order)
            
            # Wait for initial status
            self._ib.sleep(1)
            
            # Wait for fill (up to 30 seconds)
            if self.is_market_open():
                for _ in range(30):
                    self._ib.sleep(1)
                    if trade.orderStatus.status in ['Filled', 'Cancelled', 'ApiCancelled']:
                        break
            
            result = ExecutionResult(
                order_id=trade.order.orderId,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status=trade.orderStatus.status,
                filled_quantity=int(trade.orderStatus.filled),
                avg_fill_price=trade.orderStatus.avgFillPrice,
                commission=0.0,  # Would need to query fills
                message=str(trade.log[-1]) if trade.log else ""
            )
            
            # Track
            self._orders[result.order_id] = result
            self._trade_count += 1
            
            # Log result
            if result.is_filled:
                value = result.total_value
                logger.info(f"✅ Filled: {result.side} {result.filled_quantity} {result.symbol} @ ${result.avg_fill_price:.2f} (${value:.2f})")
            else:
                logger.info(f"📋 Order status: {result.status}")
            
            self._notify_execution(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Order execution error: {e}")
            return ExecutionResult(
                order_id=0,
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                status="Error",
                message=str(e)
            )
    
    def execute_signal(
        self,
        symbol: str,
        side: str,
        shares: int,
        current_price: float,
        confidence: float,
        reason: str = ""
    ) -> ExecutionResult:
        """
        Execute a trading signal.
        
        Args:
            symbol: Stock symbol
            side: "BUY" or "SELL"
            shares: Number of shares
            current_price: Current market price
            confidence: Signal confidence
            reason: Signal reason
            
        Returns:
            ExecutionResult
        """
        # Check confidence
        if confidence < self.config.min_confidence:
            return ExecutionResult(
                order_id=0,
                symbol=symbol,
                side=side,
                quantity=shares,
                status="Rejected",
                message=f"Confidence {confidence:.0f}% below {self.config.min_confidence}%"
            )
        
        # Calculate limit price
        if self.config.use_limit_orders:
            offset = current_price * (self.config.limit_offset_pct / 100)
            if side == "BUY":
                limit_price = current_price + offset  # Pay slightly above
            else:
                limit_price = current_price - offset  # Sell slightly below
            order_type = "LIMIT"
        else:
            limit_price = None
            order_type = "MARKET"
        
        request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=shares,
            order_type=order_type,
            limit_price=limit_price,
            confidence=confidence,
            signal_reason=reason
        )
        
        return self.execute_order(request)
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an open order"""
        if not self._connected or not self._ib:
            return False
        
        try:
            for trade in self._ib.openTrades():
                if trade.order.orderId == order_id:
                    self._ib.cancelOrder(trade.order)
                    logger.info(f"🚫 Cancelled order {order_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Cancel error: {e}")
            return False
    
    def cancel_all_orders(self) -> int:
        """Cancel all open orders"""
        if not self._connected or not self._ib:
            return 0
        
        count = 0
        for trade in self._ib.openTrades():
            self._ib.cancelOrder(trade.order)
            count += 1
        
        logger.info(f"🚫 Cancelled {count} orders")
        return count
    
    def get_open_orders(self) -> list[dict]:
        """Get all open orders"""
        if not self._connected or not self._ib:
            return []
        
        orders = []
        for trade in self._ib.openTrades():
            orders.append({
                "order_id": trade.order.orderId,
                "symbol": trade.contract.symbol,
                "side": trade.order.action,
                "quantity": trade.order.totalQuantity,
                "status": trade.orderStatus.status,
                "filled": trade.orderStatus.filled
            })
        return orders
    
    def get_positions(self) -> list[dict]:
        """Get current positions"""
        if not self._connected or not self._ib:
            return []
        
        positions = []
        for pos in self._ib.positions():
            positions.append({
                "symbol": pos.contract.symbol,
                "quantity": pos.position,
                "avg_cost": pos.avgCost,
                "market_value": 0  # Would need market data
            })
        return positions
    
    def get_account_summary(self) -> dict:
        """Get account summary"""
        if not self._connected or not self._ib:
            return {}
        
        summary = {}
        for av in self._ib.accountSummary():
            if av.tag in ['NetLiquidation', 'TotalCashValue', 'AvailableFunds', 'BuyingPower']:
                summary[av.tag] = float(av.value)
        return summary


# =============================================================================
# TRADING ORCHESTRATOR
# =============================================================================

class TradingOrchestrator:
    """
    Orchestrates the full trading pipeline:
    Data → Signals → Risk → Execution
    
    Usage:
        orchestrator = TradingOrchestrator()
        orchestrator.start()
        
        # ... trades execute automatically ...
        
        orchestrator.stop()
    """
    
    def __init__(
        self,
        execution_config: Optional[ExecutionConfig] = None,
        watchlist: Optional[list[str]] = None
    ):
        self.watchlist = watchlist or ["QBTS", "IONQ", "RGTI", "QUBT"]
        
        # Components (lazy loaded)
        self._data_manager = None
        self._signal_generator = None
        self._risk_manager = None
        self._execution_bridge = None
        
        self._execution_config = execution_config or ExecutionConfig()
        self._running = False
        
        # Callbacks
        self._on_signal: list[Callable] = []
        self._on_trade: list[Callable] = []
    
    def on_signal(self, callback: Callable):
        """Register signal callback"""
        self._on_signal.append(callback)
    
    def on_trade(self, callback: Callable):
        """Register trade callback"""
        self._on_trade.append(callback)
    
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Import components
            from data_ingestion.data_sources import DataSourceManager
            from core.signal_engine import SignalGenerator
            from core.risk_manager import RiskManager
            
            # Initialize data manager (YFinance for now)
            self._data_manager = DataSourceManager()
            self._data_manager.connect()
            
            # Initialize signal generator
            self._signal_generator = SignalGenerator(watchlist=self.watchlist)
            
            # Initialize risk manager (get capital from IBKR if connected)
            self._risk_manager = RiskManager(capital=100_000)
            
            # Initialize execution bridge
            self._execution_bridge = ExecutionBridge(self._execution_config)
            
            if self._execution_config.mode != ExecutionMode.SIMULATED:
                if not self._execution_bridge.connect():
                    logger.warning("Execution bridge not connected, using simulated mode")
                    self._execution_config.mode = ExecutionMode.SIMULATED
            else:
                self._execution_bridge.connect()
            
            # Update capital from IBKR
            if self._execution_bridge.connected:
                summary = self._execution_bridge.get_account_summary()
                if 'AvailableFunds' in summary:
                    self._risk_manager.available_cash = summary['AvailableFunds']
                    self._risk_manager.total_capital = summary.get('NetLiquidation', summary['AvailableFunds'])
                    logger.info(f"💰 Capital from IBKR: ${self._risk_manager.total_capital:,.2f}")
            
            logger.info("✅ Trading orchestrator initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_symbol(self, symbol: str) -> Optional[ExecutionResult]:
        """
        Process a single symbol through the pipeline.
        
        Returns ExecutionResult if a trade was executed.
        """
        try:
            # Get historical data
            df = self._data_manager.get_historical(symbol, period="5d", interval="5m")
            if df is None or len(df) < 30:
                logger.debug(f"Insufficient data for {symbol}")
                return None
            
            # Get current quote
            quote = self._data_manager.get_quote(symbol)
            current_price = quote.last if quote else df['close'].iloc[-1]
            
            # Generate signal
            signal = self._signal_generator.generate_signal(symbol, df, current_price)
            
            # Notify signal callbacks
            for callback in self._on_signal:
                callback(signal)
            
            # Check if actionable
            if not signal.is_actionable:
                logger.debug(f"{symbol}: {signal.signal_type.value} ({signal.confidence:.0f}%) - not actionable")
                return None
            
            logger.info(f"{signal}")
            
            # Determine side
            side = "BUY" if signal.signal_type.value in ["BUY", "STRONG_BUY"] else "SELL"
            is_buy = side == "BUY"
            
            # Calculate position size
            sizing = self._risk_manager.calculate_order_size(
                symbol=symbol,
                price=current_price,
                confidence=signal.confidence,
                is_buy=is_buy
            )
            
            if not sizing.approved:
                logger.info(f"  ❌ Sizing rejected: {sizing.reason}")
                return None
            
            logger.info(f"  📊 Sizing approved: {sizing.shares} shares @ ${current_price:.2f}")
            
            # Execute
            result = self._execution_bridge.execute_signal(
                symbol=symbol,
                side=side,
                shares=sizing.shares,
                current_price=current_price,
                confidence=signal.confidence,
                reason=signal.reason
            )
            
            # Notify trade callbacks
            for callback in self._on_trade:
                callback(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            return None
    
    def scan_watchlist(self) -> list[ExecutionResult]:
        """Scan all watchlist symbols for trading opportunities"""
        results = []
        for symbol in self.watchlist:
            result = self.process_symbol(symbol)
            if result:
                results.append(result)
        return results
    
    def get_status(self) -> dict:
        """Get current orchestrator status"""
        status = {
            "running": self._running,
            "mode": self._execution_config.mode.value,
            "watchlist": self.watchlist,
            "market_open": self._execution_bridge.is_market_open() if self._execution_bridge else False
        }
        
        if self._risk_manager:
            status["portfolio"] = self._risk_manager.get_portfolio_summary()
        
        if self._execution_bridge:
            status["connected"] = self._execution_bridge.connected
            status["positions"] = self._execution_bridge.get_positions()
            status["open_orders"] = self._execution_bridge.get_open_orders()
        
        return status
    
    def shutdown(self):
        """Shutdown all components"""
        if self._execution_bridge:
            self._execution_bridge.disconnect()
        if self._data_manager:
            self._data_manager.disconnect()
        self._running = False
        logger.info("📴 Trading orchestrator shutdown")


# =============================================================================
# MAIN - TEST THE MODULE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Execution Bridge Test")
    print("=" * 60)
    
    # Test in simulated mode (no IBKR needed)
    config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
    bridge = ExecutionBridge(config)
    
    print("\n🔌 Connecting (simulated mode)...")
    bridge.connect()
    
    print("\n📝 Testing order execution...")
    result = bridge.execute_signal(
        symbol="QBTS",
        side="BUY",
        shares=100,
        current_price=7.50,
        confidence=90,
        reason="Test signal"
    )
    
    print(f"\n📋 Result:")
    print(f"  Order ID: {result.order_id}")
    print(f"  Status: {result.status}")
    print(f"  Filled: {result.filled_quantity} @ ${result.avg_fill_price:.2f}")
    
    print("\n📴 Disconnecting...")
    bridge.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Execution bridge test complete!")
    print("=" * 60)
