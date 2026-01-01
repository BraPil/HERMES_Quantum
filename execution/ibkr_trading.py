#!/usr/bin/env python3
"""
IBKR Trading Integration Module
================================
Integrates HERMES Quantum with Interactive Brokers TWS API.

Provides:
- IBKRConnection: Connection management
- IBKRDataFeed: Market data streaming (delayed)
- IBKROrderManager: Order placement and management
- IBKRAccount: Position and account tracking

Configuration:
- Paper Trading: Port 7497
- Live Trading: Port 7496 (use with caution!)

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
import threading
import time

# Python 3.14+ compatibility
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Stock, LimitOrder, MarketOrder, StopOrder, Contract, Order, Trade, Ticker, util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class OrderSide(Enum):
    """Order side (buy/sell)"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order types supported"""
    MARKET = "MKT"
    LIMIT = "LMT"
    STOP = "STP"
    STOP_LIMIT = "STP_LMT"


class TimeInForce(Enum):
    """Time in force options"""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class IBKRConfig:
    """IBKR connection configuration"""
    host: str = "127.0.0.1"
    port: int = 7497  # 7497 for paper, 7496 for live
    client_id: int = 1
    readonly: bool = False
    timeout: int = 30
    
    # Our quantum stocks watchlist
    watchlist: list = field(default_factory=lambda: ["QBTS", "IONQ", "RGTI", "QUBT"])
    
    @property
    def is_paper_trading(self) -> bool:
        """Check if connected to paper trading"""
        return self.port == 7497


@dataclass
class Position:
    """Represents a position in a security"""
    symbol: str
    quantity: float
    avg_cost: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def total_cost(self) -> float:
        return self.quantity * self.avg_cost


@dataclass
class OrderResult:
    """Result of an order submission"""
    order_id: int
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: Optional[float]
    status: str
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketData:
    """Market data snapshot"""
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def mid(self) -> float:
        """Mid price"""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return self.last
    
    @property
    def spread(self) -> float:
        """Bid-ask spread"""
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return 0.0


# =============================================================================
# IBKR CONNECTION
# =============================================================================

class IBKRConnection:
    """
    Manages connection to IBKR TWS.
    
    Usage:
        conn = IBKRConnection(IBKRConfig())
        conn.connect()
        # ... do stuff ...
        conn.disconnect()
    
    Or with context manager:
        with IBKRConnection(IBKRConfig()) as conn:
            # ... do stuff ...
    """
    
    def __init__(self, config: Optional[IBKRConfig] = None):
        self.config = config or IBKRConfig()
        self.ib = IB()
        self._connected = False
        self._callbacks: dict[str, list[Callable]] = {}
        
    @property
    def connected(self) -> bool:
        """Check if connected to TWS"""
        return self._connected and self.ib.isConnected()
    
    def connect(self) -> bool:
        """Connect to TWS"""
        try:
            logger.info(f"Connecting to TWS at {self.config.host}:{self.config.port}...")
            self.ib.connect(
                self.config.host,
                self.config.port,
                clientId=self.config.client_id,
                readonly=self.config.readonly,
                timeout=self.config.timeout
            )
            self._connected = True
            logger.info("✅ Connected to TWS")
            
            # Log account info
            accounts = self.ib.managedAccounts()
            logger.info(f"Managed accounts: {accounts}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Disconnect from TWS"""
        if self._connected:
            self.ib.disconnect()
            self._connected = False
            logger.info("📴 Disconnected from TWS")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def sleep(self, seconds: float):
        """Sleep while processing messages"""
        self.ib.sleep(seconds)


# =============================================================================
# IBKR DATA FEED
# =============================================================================

class IBKRDataFeed:
    """
    Provides market data for securities.
    Uses delayed data (15-min) to avoid subscription costs.
    
    Usage:
        feed = IBKRDataFeed(connection)
        data = feed.get_quote("QBTS")
        print(f"QBTS Last: ${data.last}")
    """
    
    def __init__(self, connection: IBKRConnection):
        self.conn = connection
        self.ib = connection.ib
        self._contracts: dict[str, Contract] = {}
        self._tickers: dict[str, Ticker] = {}
        
        # Request delayed market data (free)
        self.ib.reqMarketDataType(3)  # 3 = Delayed
        logger.info("📊 Using delayed market data (15-min)")
    
    def _get_contract(self, symbol: str) -> Contract:
        """Get or create a qualified contract"""
        if symbol not in self._contracts:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            self._contracts[symbol] = contract
            logger.debug(f"Qualified contract: {symbol} (conId={contract.conId})")
        return self._contracts[symbol]
    
    def get_quote(self, symbol: str, timeout: float = 5.0) -> MarketData:
        """
        Get current quote for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "QBTS")
            timeout: Seconds to wait for data
            
        Returns:
            MarketData object with current prices
        """
        contract = self._get_contract(symbol)
        
        # Request market data
        ticker = self.ib.reqMktData(contract, '', False, False)
        
        # Wait for data
        start = time.time()
        while time.time() - start < timeout:
            self.ib.sleep(0.5)
            if ticker.last or ticker.bid or ticker.ask:
                break
        
        # Build market data object
        data = MarketData(
            symbol=symbol,
            bid=ticker.bid if ticker.bid and ticker.bid > 0 else 0.0,
            ask=ticker.ask if ticker.ask and ticker.ask > 0 else 0.0,
            last=ticker.last if ticker.last and ticker.last > 0 else (ticker.close if ticker.close else 0.0),
            volume=int(ticker.volume) if ticker.volume else 0,
            timestamp=datetime.now()
        )
        
        # Cancel subscription
        self.ib.cancelMktData(contract)
        
        return data
    
    def get_quotes(self, symbols: list[str]) -> dict[str, MarketData]:
        """Get quotes for multiple symbols"""
        return {symbol: self.get_quote(symbol) for symbol in symbols}
    
    def get_watchlist_quotes(self) -> dict[str, MarketData]:
        """Get quotes for all watchlist symbols"""
        return self.get_quotes(self.conn.config.watchlist)


# =============================================================================
# IBKR ORDER MANAGER
# =============================================================================

class IBKROrderManager:
    """
    Manages order placement and tracking.
    
    Usage:
        orders = IBKROrderManager(connection)
        result = orders.buy("QBTS", 10, limit_price=8.00)
        print(f"Order status: {result.status}")
    """
    
    def __init__(self, connection: IBKRConnection):
        self.conn = connection
        self.ib = connection.ib
        self._orders: dict[int, OrderResult] = {}
        self._contracts: dict[str, Contract] = {}
    
    def _get_contract(self, symbol: str) -> Contract:
        """Get or create a qualified contract"""
        if symbol not in self._contracts:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            self._contracts[symbol] = contract
        return self._contracts[symbol]
    
    def _create_order(
        self,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.LIMIT,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        tif: TimeInForce = TimeInForce.GTC
    ) -> Order:
        """Create an IB order object"""
        
        if order_type == OrderType.MARKET:
            order = MarketOrder(side.value, quantity)
        elif order_type == OrderType.LIMIT:
            if limit_price is None:
                raise ValueError("Limit price required for limit orders")
            order = LimitOrder(side.value, quantity, limit_price)
        elif order_type == OrderType.STOP:
            if stop_price is None:
                raise ValueError("Stop price required for stop orders")
            order = StopOrder(side.value, quantity, stop_price)
        else:
            raise ValueError(f"Unsupported order type: {order_type}")
        
        order.tif = tif.value
        return order
    
    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.LIMIT,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        tif: TimeInForce = TimeInForce.GTC,
        wait_for_fill: bool = False,
        timeout: float = 30.0
    ) -> OrderResult:
        """
        Submit an order.
        
        Args:
            symbol: Stock symbol
            side: BUY or SELL
            quantity: Number of shares
            order_type: MARKET, LIMIT, or STOP
            limit_price: Limit price (required for LIMIT orders)
            stop_price: Stop price (required for STOP orders)
            tif: Time in force (DAY, GTC, etc.)
            wait_for_fill: If True, wait for order to fill
            timeout: Seconds to wait for fill
            
        Returns:
            OrderResult with status and fill info
        """
        contract = self._get_contract(symbol)
        order = self._create_order(side, quantity, order_type, limit_price, stop_price, tif)
        
        logger.info(f"📝 Submitting: {side.value} {quantity} {symbol} @ {order_type.value}" +
                   (f" ${limit_price:.2f}" if limit_price else ""))
        
        # Place order
        trade = self.ib.placeOrder(contract, order)
        
        # Wait for initial status
        self.ib.sleep(1)
        
        # Wait for fill if requested
        if wait_for_fill:
            start = time.time()
            while time.time() - start < timeout:
                self.ib.sleep(1)
                if trade.orderStatus.status in ['Filled', 'Cancelled', 'ApiCancelled']:
                    break
        
        # Build result
        result = OrderResult(
            order_id=trade.order.orderId,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            status=trade.orderStatus.status,
            filled_quantity=trade.orderStatus.filled,
            avg_fill_price=trade.orderStatus.avgFillPrice,
            message=str(trade.log[-1]) if trade.log else ""
        )
        
        self._orders[result.order_id] = result
        logger.info(f"   Order {result.order_id}: {result.status}")
        
        return result
    
    def buy(
        self,
        symbol: str,
        quantity: float,
        limit_price: Optional[float] = None,
        tif: TimeInForce = TimeInForce.GTC
    ) -> OrderResult:
        """
        Place a buy order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            limit_price: Limit price (uses LIMIT order if provided, else MARKET)
            tif: Time in force
            
        Returns:
            OrderResult
        """
        order_type = OrderType.LIMIT if limit_price else OrderType.MARKET
        return self.submit_order(symbol, OrderSide.BUY, quantity, order_type, limit_price, tif=tif)
    
    def sell(
        self,
        symbol: str,
        quantity: float,
        limit_price: Optional[float] = None,
        tif: TimeInForce = TimeInForce.GTC
    ) -> OrderResult:
        """
        Place a sell order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            limit_price: Limit price (uses LIMIT order if provided, else MARKET)
            tif: Time in force
            
        Returns:
            OrderResult
        """
        order_type = OrderType.LIMIT if limit_price else OrderType.MARKET
        return self.submit_order(symbol, OrderSide.SELL, quantity, order_type, limit_price, tif=tif)
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an open order"""
        for trade in self.ib.openTrades():
            if trade.order.orderId == order_id:
                self.ib.cancelOrder(trade.order)
                logger.info(f"🚫 Cancelled order {order_id}")
                return True
        logger.warning(f"Order {order_id} not found")
        return False
    
    def cancel_all_orders(self) -> int:
        """Cancel all open orders"""
        count = 0
        for trade in self.ib.openTrades():
            self.ib.cancelOrder(trade.order)
            count += 1
        logger.info(f"🚫 Cancelled {count} orders")
        return count
    
    def get_open_orders(self) -> list[OrderResult]:
        """Get all open orders"""
        orders = []
        for trade in self.ib.openTrades():
            orders.append(OrderResult(
                order_id=trade.order.orderId,
                symbol=trade.contract.symbol,
                side=OrderSide.BUY if trade.order.action == 'BUY' else OrderSide.SELL,
                quantity=trade.order.totalQuantity,
                order_type=OrderType.LIMIT,  # Simplified
                limit_price=getattr(trade.order, 'lmtPrice', None),
                status=trade.orderStatus.status,
                filled_quantity=trade.orderStatus.filled,
                avg_fill_price=trade.orderStatus.avgFillPrice
            ))
        return orders


# =============================================================================
# IBKR ACCOUNT
# =============================================================================

class IBKRAccount:
    """
    Tracks account information and positions.
    
    Usage:
        account = IBKRAccount(connection)
        print(f"Cash: ${account.cash:,.2f}")
        print(f"Net Liq: ${account.net_liquidation:,.2f}")
        
        for pos in account.positions:
            print(f"{pos.symbol}: {pos.quantity} shares")
    """
    
    def __init__(self, connection: IBKRConnection):
        self.conn = connection
        self.ib = connection.ib
        self._account_id: Optional[str] = None
    
    @property
    def account_id(self) -> str:
        """Get the account ID"""
        if not self._account_id:
            accounts = self.ib.managedAccounts()
            self._account_id = accounts[0] if accounts else ""
        return self._account_id
    
    def _get_account_value(self, tag: str) -> float:
        """Get a specific account value"""
        for av in self.ib.accountSummary():
            if av.tag == tag:
                return float(av.value)
        return 0.0
    
    @property
    def net_liquidation(self) -> float:
        """Net liquidation value"""
        return self._get_account_value('NetLiquidation')
    
    @property
    def cash(self) -> float:
        """Total cash balance"""
        return self._get_account_value('TotalCashValue')
    
    @property
    def available_funds(self) -> float:
        """Available funds for trading"""
        return self._get_account_value('AvailableFunds')
    
    @property
    def buying_power(self) -> float:
        """Buying power"""
        return self._get_account_value('BuyingPower')
    
    @property
    def positions(self) -> list[Position]:
        """Get all positions"""
        positions = []
        for pos in self.ib.positions():
            positions.append(Position(
                symbol=pos.contract.symbol,
                quantity=pos.position,
                avg_cost=pos.avgCost,
                market_value=0.0,  # Would need market data to calculate
                unrealized_pnl=0.0,
                realized_pnl=0.0
            ))
        return positions
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol"""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    def get_summary(self) -> dict:
        """Get account summary"""
        return {
            'account_id': self.account_id,
            'net_liquidation': self.net_liquidation,
            'cash': self.cash,
            'available_funds': self.available_funds,
            'buying_power': self.buying_power,
            'positions': len(self.positions),
            'is_paper': self.conn.config.is_paper_trading
        }


# =============================================================================
# IBKR TRADING CLIENT (UNIFIED INTERFACE)
# =============================================================================

class IBKRTradingClient:
    """
    Unified interface for IBKR trading.
    Combines connection, data, orders, and account management.
    
    Usage:
        client = IBKRTradingClient()
        client.connect()
        
        # Get quote
        quote = client.get_quote("QBTS")
        print(f"QBTS: ${quote.last:.2f}")
        
        # Place order
        result = client.buy("QBTS", 10, limit_price=8.00)
        
        # Check account
        print(f"Cash: ${client.account.cash:,.2f}")
        
        client.disconnect()
    """
    
    def __init__(self, config: Optional[IBKRConfig] = None):
        self.config = config or IBKRConfig()
        self.connection = IBKRConnection(self.config)
        
        # These are initialized after connection
        self._data_feed: Optional[IBKRDataFeed] = None
        self._order_manager: Optional[IBKROrderManager] = None
        self._account: Optional[IBKRAccount] = None
    
    def connect(self) -> bool:
        """Connect to TWS"""
        if self.connection.connect():
            self._data_feed = IBKRDataFeed(self.connection)
            self._order_manager = IBKROrderManager(self.connection)
            self._account = IBKRAccount(self.connection)
            return True
        return False
    
    def disconnect(self):
        """Disconnect from TWS"""
        self.connection.disconnect()
    
    @property
    def connected(self) -> bool:
        """Check if connected"""
        return self.connection.connected
    
    @property
    def data(self) -> IBKRDataFeed:
        """Data feed access"""
        if not self._data_feed:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._data_feed
    
    @property
    def orders(self) -> IBKROrderManager:
        """Order manager access"""
        if not self._order_manager:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._order_manager
    
    @property
    def account(self) -> IBKRAccount:
        """Account access"""
        if not self._account:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._account
    
    # Convenience methods
    def get_quote(self, symbol: str) -> MarketData:
        """Get quote for a symbol"""
        return self.data.get_quote(symbol)
    
    def buy(self, symbol: str, quantity: float, limit_price: Optional[float] = None) -> OrderResult:
        """Place a buy order"""
        return self.orders.buy(symbol, quantity, limit_price)
    
    def sell(self, symbol: str, quantity: float, limit_price: Optional[float] = None) -> OrderResult:
        """Place a sell order"""
        return self.orders.sell(symbol, quantity, limit_price)
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self.account.get_position(symbol)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# =============================================================================
# MAIN - TEST THE MODULE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("IBKR Trading Module Test")
    print("=" * 60)
    
    # Use the unified client
    with IBKRTradingClient() as client:
        print("\n📊 ACCOUNT SUMMARY")
        print("-" * 40)
        summary = client.account.get_summary()
        for key, value in summary.items():
            if isinstance(value, float):
                print(f"  {key}: ${value:,.2f}")
            else:
                print(f"  {key}: {value}")
        
        print("\n📈 MARKET DATA (Delayed)")
        print("-" * 40)
        for symbol in ["QBTS", "IONQ"]:
            quote = client.get_quote(symbol)
            print(f"  {symbol}: Last=${quote.last:.2f}, Bid=${quote.bid:.2f}, Ask=${quote.ask:.2f}")
        
        print("\n📋 POSITIONS")
        print("-" * 40)
        positions = client.account.positions
        if positions:
            for pos in positions:
                print(f"  {pos.symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")
        else:
            print("  No positions")
        
        print("\n📝 OPEN ORDERS")
        print("-" * 40)
        orders = client.orders.get_open_orders()
        if orders:
            for order in orders:
                print(f"  {order.order_id}: {order.side.value} {order.quantity} {order.symbol} - {order.status}")
        else:
            print("  No open orders")
    
    print("\n" + "=" * 60)
    print("✅ Module test complete!")
    print("=" * 60)
