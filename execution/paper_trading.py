"""
HERMES Quantum - Paper Trading Module

Simulated live trading without real money.
Connects to live market data but executes paper trades only.

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import logging
import json
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(str, Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class Order:
    """Paper trading order"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None  # Limit price
    stop_price: Optional[float] = None  # Stop trigger price
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "created_at": self.created_at.isoformat(),
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Order":
        """Create from dictionary"""
        return cls(
            order_id=data["order_id"],
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            quantity=data["quantity"],
            price=data.get("price"),
            stop_price=data.get("stop_price"),
            status=OrderStatus(data["status"]),
            filled_quantity=data.get("filled_quantity", 0),
            filled_price=data.get("filled_price", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]),
            filled_at=datetime.fromisoformat(data["filled_at"]) if data.get("filled_at") else None,
            notes=data.get("notes", ""),
        )


@dataclass
class Position:
    """Paper trading position"""
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    
    @property
    def market_value(self) -> float:
        """Current market value"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Total cost basis"""
        return self.quantity * self.avg_entry_price
    
    def update_price(self, price: float) -> None:
        """Update current price and unrealized P&L"""
        self.current_price = price
        self.unrealized_pnl = self.quantity * (price - self.avg_entry_price)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "avg_entry_price": self.avg_entry_price,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "opened_at": self.opened_at.isoformat(),
        }


@dataclass
class AccountState:
    """Paper trading account state"""
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    
    @property
    def equity(self) -> float:
        """Total account equity"""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value
    
    @property
    def buying_power(self) -> float:
        """Available buying power (no margin)"""
        return self.cash
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions"""
        return sum(p.unrealized_pnl for p in self.positions.values())
    
    @property
    def total_realized_pnl(self) -> float:
        """Total realized P&L"""
        return sum(p.realized_pnl for p in self.positions.values())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "cash": self.cash,
            "equity": self.equity,
            "buying_power": self.buying_power,
            "positions": {s: p.to_dict() for s, p in self.positions.items()},
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_realized_pnl": self.total_realized_pnl,
        }


class PaperTradingEngine:
    """
    Paper trading engine for simulated trading.
    
    Features:
    - Realistic order execution
    - Position tracking
    - P&L calculation
    - Transaction history
    - Persistence to SQLite
    """
    
    def __init__(
        self,
        initial_cash: float = 100_000.0,
        slippage: float = 0.0005,  # 0.05% slippage
        commission: float = 0.0,  # Commission per trade
        commission_per_share: float = 0.005,  # $0.005 per share
        min_commission: float = 1.0,
        db_path: Optional[str] = None,
    ):
        """
        Initialize paper trading engine.
        
        Args:
            initial_cash: Starting cash balance
            slippage: Simulated slippage fraction
            commission: Fixed commission per trade
            commission_per_share: Commission per share
            min_commission: Minimum commission
            db_path: Path to SQLite database for persistence
        """
        self.slippage = slippage
        self.commission = commission
        self.commission_per_share = commission_per_share
        self.min_commission = min_commission
        
        # Account state
        self.account = AccountState(cash=initial_cash, total_deposits=initial_cash)
        
        # Order tracking
        self.orders: Dict[str, Order] = {}
        self.order_counter = 0
        
        # Trade history
        self.trades: List[Dict] = []
        
        # Database
        self.db_path = db_path or "outputs/data/paper_trading.db"
        self._init_database()
        
        # Price feed callback
        self._price_callbacks: List[Callable] = []
        
        # Current prices (simulated or from live feed)
        self.current_prices: Dict[str, float] = {}
        
        logger.info(f"PaperTradingEngine initialized with ${initial_cash:,.2f}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_db() as conn:
            cursor = conn.cursor()
            
            # Orders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    order_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL,
                    stop_price REAL,
                    status TEXT NOT NULL,
                    filled_quantity INTEGER DEFAULT 0,
                    filled_price REAL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    filled_at TEXT,
                    notes TEXT
                )
            """)
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    commission REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    pnl REAL DEFAULT 0
                )
            """)
            
            # Account snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cash REAL NOT NULL,
                    equity REAL NOT NULL,
                    positions_json TEXT,
                    unrealized_pnl REAL,
                    realized_pnl REAL
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self.order_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ORD-{timestamp}-{self.order_counter:04d}"
    
    def _calculate_commission(self, quantity: int) -> float:
        """Calculate commission for a trade"""
        per_share = quantity * self.commission_per_share
        return max(self.commission + per_share, self.min_commission)
    
    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        """Apply slippage to price"""
        if side == OrderSide.BUY:
            return price * (1 + self.slippage)
        else:
            return price * (1 - self.slippage)
    
    def update_price(self, symbol: str, price: float) -> None:
        """Update current price for a symbol"""
        self.current_prices[symbol] = price
        
        # Update position prices
        if symbol in self.account.positions:
            self.account.positions[symbol].update_price(price)
        
        # Check pending orders
        self._check_pending_orders(symbol, price)
        
        # Notify callbacks
        for callback in self._price_callbacks:
            try:
                callback(symbol, price)
            except Exception as e:
                logger.error(f"Price callback error: {e}")
    
    def _check_pending_orders(self, symbol: str, price: float) -> None:
        """Check if any pending orders should be filled"""
        for order in list(self.orders.values()):
            if order.symbol != symbol or order.status != OrderStatus.PENDING:
                continue
            
            should_fill = False
            fill_price = price
            
            if order.order_type == OrderType.MARKET:
                should_fill = True
                fill_price = self._apply_slippage(price, order.side)
                
            elif order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and price <= order.price:
                    should_fill = True
                    fill_price = order.price
                elif order.side == OrderSide.SELL and price >= order.price:
                    should_fill = True
                    fill_price = order.price
                    
            elif order.order_type == OrderType.STOP:
                if order.side == OrderSide.BUY and price >= order.stop_price:
                    should_fill = True
                    fill_price = self._apply_slippage(price, order.side)
                elif order.side == OrderSide.SELL and price <= order.stop_price:
                    should_fill = True
                    fill_price = self._apply_slippage(price, order.side)
            
            if should_fill:
                self._fill_order(order, fill_price)
    
    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType = OrderType.MARKET,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """
        Submit a paper trading order.
        
        Args:
            symbol: Stock symbol
            side: BUY or SELL
            quantity: Number of shares
            order_type: Order type
            price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            
        Returns:
            Created order
        """
        # Validate
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if order_type == OrderType.LIMIT and price is None:
            raise ValueError("Limit price required for LIMIT orders")
        
        if order_type in (OrderType.STOP, OrderType.STOP_LIMIT) and stop_price is None:
            raise ValueError("Stop price required for STOP orders")
        
        # Check buying power for buy orders
        if side == OrderSide.BUY:
            estimated_cost = quantity * (price or self.current_prices.get(symbol, 100))
            commission = self._calculate_commission(quantity)
            if estimated_cost + commission > self.account.buying_power:
                raise ValueError(f"Insufficient buying power: ${self.account.buying_power:,.2f}")
        
        # Check position for sell orders
        if side == OrderSide.SELL:
            position = self.account.positions.get(symbol)
            if not position or position.quantity < quantity:
                available = position.quantity if position else 0
                raise ValueError(f"Insufficient shares: {available} available")
        
        # Create order
        order = Order(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
        
        self.orders[order.order_id] = order
        
        # Save to database
        self._save_order(order)
        
        logger.info(f"Order submitted: {order.order_id} - {side.value} {quantity} {symbol} @ {order_type.value}")
        
        # Try to fill market orders immediately
        if order_type == OrderType.MARKET and symbol in self.current_prices:
            fill_price = self._apply_slippage(self.current_prices[symbol], side)
            self._fill_order(order, fill_price)
        
        return order
    
    def _fill_order(self, order: Order, fill_price: float) -> None:
        """Fill an order"""
        commission = self._calculate_commission(order.quantity)
        
        if order.side == OrderSide.BUY:
            total_cost = order.quantity * fill_price + commission
            
            if total_cost > self.account.cash:
                order.status = OrderStatus.REJECTED
                order.notes = "Insufficient funds"
                self._save_order(order)
                return
            
            # Deduct cash
            self.account.cash -= total_cost
            
            # Update or create position
            if order.symbol in self.account.positions:
                pos = self.account.positions[order.symbol]
                total_qty = pos.quantity + order.quantity
                avg_price = (
                    (pos.quantity * pos.avg_entry_price + order.quantity * fill_price)
                    / total_qty
                )
                pos.quantity = total_qty
                pos.avg_entry_price = avg_price
            else:
                self.account.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_entry_price=fill_price,
                    current_price=fill_price,
                )
        
        elif order.side == OrderSide.SELL:
            proceeds = order.quantity * fill_price - commission
            
            # Calculate realized P&L
            pos = self.account.positions[order.symbol]
            cost_basis = order.quantity * pos.avg_entry_price
            realized_pnl = proceeds - cost_basis + commission  # Add back commission for P&L calc
            
            # Update position
            pos.quantity -= order.quantity
            pos.realized_pnl += realized_pnl
            
            # Remove position if fully closed
            if pos.quantity <= 0:
                del self.account.positions[order.symbol]
            
            # Add cash
            self.account.cash += proceeds
        
        # Update order
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.filled_at = datetime.now()
        
        # Record trade
        trade = {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": fill_price,
            "commission": commission,
            "timestamp": datetime.now().isoformat(),
        }
        self.trades.append(trade)
        
        # Save
        self._save_order(order)
        self._save_trade(trade)
        
        logger.info(f"Order filled: {order.order_id} - {order.quantity} {order.symbol} @ ${fill_price:.2f}")
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.status != OrderStatus.PENDING:
            return False
        
        order.status = OrderStatus.CANCELLED
        self._save_order(order)
        
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    def _save_order(self, order: Order) -> None:
        """Save order to database"""
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO orders 
                (order_id, symbol, side, order_type, quantity, price, stop_price,
                 status, filled_quantity, filled_price, created_at, filled_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.order_id, order.symbol, order.side.value, order.order_type.value,
                order.quantity, order.price, order.stop_price, order.status.value,
                order.filled_quantity, order.filled_price, order.created_at.isoformat(),
                order.filled_at.isoformat() if order.filled_at else None, order.notes
            ))
            conn.commit()
    
    def _save_trade(self, trade: Dict) -> None:
        """Save trade to database"""
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (order_id, symbol, side, quantity, price, commission, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                trade["order_id"], trade["symbol"], trade["side"],
                trade["quantity"], trade["price"], trade["commission"], trade["timestamp"]
            ))
            conn.commit()
    
    def save_snapshot(self) -> None:
        """Save current account snapshot"""
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO account_snapshots 
                (timestamp, cash, equity, positions_json, unrealized_pnl, realized_pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                self.account.cash,
                self.account.equity,
                json.dumps({s: p.to_dict() for s, p in self.account.positions.items()}),
                self.account.total_unrealized_pnl,
                self.account.total_realized_pnl,
            ))
            conn.commit()
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_pending_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all pending orders"""
        orders = [o for o in self.orders.values() if o.status == OrderStatus.PENDING]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return self.account.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all positions"""
        return dict(self.account.positions)
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "account": self.account.to_dict(),
            "n_positions": len(self.account.positions),
            "n_pending_orders": len(self.get_pending_orders()),
            "n_total_trades": len(self.trades),
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        return self.trades[-limit:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Calculate performance statistics"""
        if not self.trades:
            return {"error": "No trades yet"}
        
        # Calculate returns
        total_return = (self.account.equity - self.account.total_deposits) / self.account.total_deposits
        
        # Win rate
        profitable_trades = sum(1 for t in self.trades if t.get("pnl", 0) > 0)
        win_rate = profitable_trades / len(self.trades) if self.trades else 0
        
        # Average trade
        avg_trade_value = np.mean([t["quantity"] * t["price"] for t in self.trades])
        
        return {
            "total_return_pct": total_return * 100,
            "equity": self.account.equity,
            "cash": self.account.cash,
            "unrealized_pnl": self.account.total_unrealized_pnl,
            "realized_pnl": self.account.total_realized_pnl,
            "n_trades": len(self.trades),
            "win_rate": win_rate,
            "avg_trade_value": avg_trade_value,
        }


class PaperTradingSession:
    """
    Paper trading session that integrates with HERMES agents.
    
    Connects the paper trading engine with:
    - Market data feeds
    - HERMES trading signals
    - Position management
    - Risk controls
    """
    
    def __init__(
        self,
        symbols: List[str],
        initial_cash: float = 100_000.0,
        max_position_pct: float = 0.20,
        signal_callback: Optional[Callable] = None,
    ):
        """
        Initialize paper trading session.
        
        Args:
            symbols: Symbols to trade
            initial_cash: Starting cash
            max_position_pct: Max position size as % of equity
            signal_callback: Callback for trade signals
        """
        self.symbols = symbols
        self.max_position_pct = max_position_pct
        
        # Create trading engine
        self.engine = PaperTradingEngine(initial_cash=initial_cash)
        
        # Callbacks
        self.signal_callback = signal_callback
        
        # Session state
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.signals_received = 0
        self.signals_executed = 0
        
        logger.info(f"PaperTradingSession initialized for {len(symbols)} symbols")
    
    async def start(self) -> None:
        """Start the paper trading session"""
        self.is_running = True
        self.start_time = datetime.now()
        logger.info("Paper trading session started")
    
    async def stop(self) -> None:
        """Stop the paper trading session"""
        self.is_running = False
        
        # Save final snapshot
        self.engine.save_snapshot()
        
        # Log summary
        stats = self.engine.get_performance_stats()
        logger.info(f"Paper trading session stopped. Return: {stats.get('total_return_pct', 0):.2f}%")
    
    def process_signal(
        self,
        symbol: str,
        action: str,  # "BUY", "SELL", "HOLD"
        confidence: float,
        source: str = "HERMES",
    ) -> Optional[Order]:
        """
        Process a trading signal from HERMES.
        
        Args:
            symbol: Stock symbol
            action: Trading action
            confidence: Signal confidence [0, 1]
            source: Signal source
            
        Returns:
            Order if executed, None otherwise
        """
        self.signals_received += 1
        
        if not self.is_running:
            logger.warning("Session not running, signal ignored")
            return None
        
        if symbol not in self.symbols:
            logger.warning(f"Symbol {symbol} not in trading list")
            return None
        
        if action == "HOLD":
            return None
        
        # Get current price
        price = self.engine.current_prices.get(symbol)
        if not price:
            logger.warning(f"No price for {symbol}")
            return None
        
        try:
            order = None
            
            if action == "BUY":
                # Calculate position size based on confidence
                equity = self.engine.account.equity
                max_position_value = equity * self.max_position_pct * confidence
                
                # Check existing position
                existing = self.engine.get_position(symbol)
                if existing:
                    current_value = existing.market_value
                    available = max_position_value - current_value
                else:
                    available = max_position_value
                
                if available > 0:
                    quantity = int(available / price)
                    if quantity > 0:
                        order = self.engine.submit_order(
                            symbol=symbol,
                            side=OrderSide.BUY,
                            quantity=quantity,
                            order_type=OrderType.MARKET,
                        )
            
            elif action == "SELL":
                position = self.engine.get_position(symbol)
                if position and position.quantity > 0:
                    # Sell proportional to confidence
                    sell_qty = int(position.quantity * confidence)
                    sell_qty = max(sell_qty, 1)  # Sell at least 1 share
                    
                    order = self.engine.submit_order(
                        symbol=symbol,
                        side=OrderSide.SELL,
                        quantity=sell_qty,
                        order_type=OrderType.MARKET,
                    )
            
            if order:
                self.signals_executed += 1
                if self.signal_callback:
                    self.signal_callback(symbol, action, order)
            
            return order
            
        except Exception as e:
            logger.error(f"Error processing signal: {e}")
            return None
    
    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update current prices"""
        for symbol, price in prices.items():
            self.engine.update_price(symbol, price)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        account = self.engine.get_account_summary()
        stats = self.engine.get_performance_stats()
        
        duration = None
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_seconds": duration,
            "signals_received": self.signals_received,
            "signals_executed": self.signals_executed,
            "execution_rate": self.signals_executed / self.signals_received if self.signals_received > 0 else 0,
            "account": account,
            "performance": stats,
        }


# Demo
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("HERMES Quantum - Paper Trading Demo")
    print("=" * 60)
    
    # Create session
    symbols = ["IONQ", "RGTI", "QUBT", "QBTS"]
    session = PaperTradingSession(
        symbols=symbols,
        initial_cash=100_000,
        max_position_pct=0.25,
    )
    
    # Simulate market data
    print("\nSimulating market data...")
    prices = {
        "IONQ": 35.50,
        "RGTI": 12.75,
        "QUBT": 8.20,
        "QBTS": 5.60,
    }
    session.update_prices(prices)
    
    # Start session
    async def run_demo():
        await session.start()
        
        print("\nProcessing trading signals...")
        
        # Simulate signals
        signals = [
            ("IONQ", "BUY", 0.85),
            ("RGTI", "BUY", 0.72),
            ("QUBT", "BUY", 0.68),
            ("IONQ", "HOLD", 0.50),
            ("RGTI", "SELL", 0.80),
            ("QBTS", "BUY", 0.90),
        ]
        
        for symbol, action, confidence in signals:
            print(f"  Signal: {action} {symbol} (confidence={confidence:.2f})")
            order = session.process_signal(symbol, action, confidence)
            if order:
                print(f"    -> Order {order.order_id}: {order.status.value}")
            
            # Small delay
            await asyncio.sleep(0.1)
        
        # Update prices (simulate market movement)
        new_prices = {
            "IONQ": 36.20,  # +2%
            "RGTI": 12.50,  # -2%
            "QUBT": 8.50,   # +3.7%
            "QBTS": 5.80,   # +3.6%
        }
        session.update_prices(new_prices)
        
        # Stop session
        await session.stop()
        
        # Print summary
        summary = session.get_session_summary()
        
        print("\n" + "=" * 60)
        print("Session Summary")
        print("=" * 60)
        print(f"  Signals Received: {summary['signals_received']}")
        print(f"  Signals Executed: {summary['signals_executed']}")
        print(f"  Execution Rate: {summary['execution_rate']*100:.1f}%")
        print(f"\nAccount:")
        print(f"  Cash: ${summary['account']['account']['cash']:,.2f}")
        print(f"  Equity: ${summary['account']['account']['equity']:,.2f}")
        print(f"  Positions: {summary['account']['n_positions']}")
        print(f"\nPerformance:")
        perf = summary['performance']
        print(f"  Return: {perf.get('total_return_pct', 0):.2f}%")
        print(f"  Trades: {perf.get('n_trades', 0)}")
        print(f"  Unrealized P&L: ${perf.get('unrealized_pnl', 0):,.2f}")
        
        # Show positions
        print("\nPositions:")
        for symbol, pos in session.engine.account.positions.items():
            print(f"  {symbol}: {pos.quantity} shares @ ${pos.avg_entry_price:.2f}")
            print(f"    Current: ${pos.current_price:.2f}, P&L: ${pos.unrealized_pnl:,.2f}")
    
    asyncio.run(run_demo())
    
    print("\n✅ Paper Trading demo complete!")
