#!/usr/bin/env python3
"""
Modular Data Sources Layer
===========================
Provides a unified interface for market data from multiple sources.
Supports hot-swapping between IBKR realtime, YFinance, and IBKR delayed.

Priority Order (configurable):
1. IBKR Realtime (production)
2. YFinance (development/fallback)
3. IBKR Delayed (backup)

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
import time

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Quote:
    """Real-time quote data"""
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    volume: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    
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
    
    @property
    def spread_pct(self) -> float:
        """Spread as percentage of mid"""
        if self.mid > 0:
            return (self.spread / self.mid) * 100
        return 0.0
    
    def is_valid(self) -> bool:
        """Check if quote has valid data"""
        return self.last > 0 or (self.bid > 0 and self.ask > 0)


@dataclass
class OHLCV:
    """OHLCV bar data"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "unknown"


class DataSourceType(Enum):
    """Available data sources"""
    IBKR_REALTIME = "ibkr_realtime"
    YFINANCE = "yfinance"
    IBKR_DELAYED = "ibkr_delayed"


# =============================================================================
# ABSTRACT BASE CLASS
# =============================================================================

class DataSource(ABC):
    """Abstract base class for data sources"""
    
    def __init__(self, name: str):
        self.name = name
        self._connected = False
        self._last_error: Optional[str] = None
    
    @property
    def connected(self) -> bool:
        return self._connected
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from data source"""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get real-time quote for a symbol"""
        pass
    
    @abstractmethod
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Get quotes for multiple symbols"""
        pass
    
    @abstractmethod
    def get_historical(
        self, 
        symbol: str, 
        period: str = "1d",
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data"""
        pass


# =============================================================================
# YFINANCE DATA SOURCE
# =============================================================================

class YFinanceDataSource(DataSource):
    """
    YFinance data source - fast and reliable for development.
    
    Usage:
        source = YFinanceDataSource()
        source.connect()
        quote = source.get_quote("QBTS")
        print(f"QBTS: ${quote.last:.2f}")
    """
    
    def __init__(self):
        super().__init__("yfinance")
        self._yf = None
    
    def connect(self) -> bool:
        """Initialize yfinance (no connection needed)"""
        try:
            import yfinance as yf
            self._yf = yf
            self._connected = True
            logger.info(f"✅ {self.name}: Ready")
            return True
        except ImportError:
            self._last_error = "yfinance not installed"
            logger.error(f"❌ {self.name}: {self._last_error}")
            return False
    
    def disconnect(self):
        """No disconnect needed for yfinance"""
        self._connected = False
        logger.info(f"📴 {self.name}: Disconnected")
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get real-time quote from yfinance"""
        if not self._connected:
            return None
        
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.fast_info
            
            # Get latest price
            last = getattr(info, 'last_price', None)
            if last is None:
                # Fallback to history
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    last = hist['Close'].iloc[-1]
                else:
                    last = 0.0
            
            return Quote(
                symbol=symbol,
                bid=0.0,  # yfinance doesn't provide real-time bid/ask
                ask=0.0,
                last=float(last) if last else 0.0,
                volume=int(getattr(info, 'last_volume', 0) or 0),
                timestamp=datetime.now(),
                source=self.name
            )
            
        except Exception as e:
            logger.warning(f"{self.name}: Error getting quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        return quotes
    
    def get_historical(
        self, 
        symbol: str, 
        period: str = "1d",
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Get historical data from yfinance"""
        if not self._connected:
            return None
        
        try:
            ticker = self._yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            # Normalize column names
            df.columns = [c.lower() for c in df.columns]
            df['symbol'] = symbol
            df['source'] = self.name
            
            return df
            
        except Exception as e:
            logger.warning(f"{self.name}: Error getting history for {symbol}: {e}")
            return None


# =============================================================================
# IBKR DATA SOURCE (DELAYED)
# =============================================================================

class IBKRDelayedDataSource(DataSource):
    """
    IBKR delayed data source (15-minute delay, free).
    Requires TWS running locally.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 10):
        super().__init__("ibkr_delayed")
        self.host = host
        self.port = port
        self.client_id = client_id
        self._ib = None
        self._contracts: dict[str, Any] = {}
    
    def connect(self) -> bool:
        """Connect to TWS"""
        try:
            # Python 3.14+ compatibility
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                asyncio.set_event_loop(asyncio.new_event_loop())
            
            from ib_insync import IB, Stock
            
            self._ib = IB()
            self._ib.connect(self.host, self.port, clientId=self.client_id, timeout=10)
            
            # Request delayed data (free)
            self._ib.reqMarketDataType(3)
            
            self._connected = True
            logger.info(f"✅ {self.name}: Connected to TWS (delayed data)")
            return True
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"❌ {self.name}: {self._last_error}")
            return False
    
    def disconnect(self):
        """Disconnect from TWS"""
        if self._ib and self._connected:
            self._ib.disconnect()
        self._connected = False
        logger.info(f"📴 {self.name}: Disconnected")
    
    def _get_contract(self, symbol: str):
        """Get or create a qualified contract"""
        from ib_insync import Stock
        
        if symbol not in self._contracts:
            contract = Stock(symbol, 'SMART', 'USD')
            self._ib.qualifyContracts(contract)
            self._contracts[symbol] = contract
        return self._contracts[symbol]
    
    def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get delayed quote from IBKR"""
        if not self._connected:
            return None
        
        try:
            import math
            
            contract = self._get_contract(symbol)
            ticker = self._ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            for _ in range(10):
                self._ib.sleep(0.5)
                if ticker.last or ticker.bid or ticker.ask:
                    break
            
            # Cancel subscription
            self._ib.cancelMktData(contract)
            
            # Helper for NaN handling
            def safe_float(val, default=0.0):
                if val is None:
                    return default
                try:
                    f = float(val)
                    return default if math.isnan(f) else f
                except:
                    return default
            
            return Quote(
                symbol=symbol,
                bid=safe_float(ticker.bid),
                ask=safe_float(ticker.ask),
                last=safe_float(ticker.last) or safe_float(ticker.close),
                volume=int(safe_float(ticker.volume)),
                timestamp=datetime.now(),
                source=self.name
            )
            
        except Exception as e:
            logger.warning(f"{self.name}: Error getting quote for {symbol}: {e}")
            return None
    
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Get quotes for multiple symbols"""
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        return quotes
    
    def get_historical(
        self, 
        symbol: str, 
        period: str = "1d",
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Get historical data from IBKR"""
        # IBKR historical data requires more complex handling
        # For now, return None and let fallback to YFinance
        logger.warning(f"{self.name}: Historical data not implemented, use YFinance")
        return None


# =============================================================================
# IBKR REALTIME DATA SOURCE
# =============================================================================

class IBKRRealtimeDataSource(IBKRDelayedDataSource):
    """
    IBKR real-time data source (requires subscription).
    Same as delayed but requests live data.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 11):
        super().__init__(host, port, client_id)
        self.name = "ibkr_realtime"
    
    def connect(self) -> bool:
        """Connect to TWS with real-time data"""
        result = super().connect()
        if result and self._ib:
            # Request live data (requires subscription)
            self._ib.reqMarketDataType(1)
            logger.info(f"✅ {self.name}: Switched to real-time data")
        return result


# =============================================================================
# DATA SOURCE MANAGER (UNIFIED INTERFACE)
# =============================================================================

class DataSourceManager:
    """
    Manages multiple data sources with automatic fallback.
    
    Usage:
        manager = DataSourceManager()
        manager.connect()
        
        quote = manager.get_quote("QBTS")  # Uses primary source, falls back if needed
        
        # Switch primary source
        manager.set_primary(DataSourceType.IBKR_REALTIME)
    """
    
    # Default priority order
    DEFAULT_PRIORITY = [
        DataSourceType.IBKR_REALTIME,
        DataSourceType.YFINANCE,
        DataSourceType.IBKR_DELAYED
    ]
    
    # Quantum stocks watchlist
    WATCHLIST = ["QBTS", "IONQ", "RGTI", "QUBT"]
    
    def __init__(
        self, 
        priority: Optional[list[DataSourceType]] = None,
        ibkr_host: str = "127.0.0.1",
        ibkr_port: int = 7497
    ):
        self.priority = priority or self.DEFAULT_PRIORITY
        self.ibkr_host = ibkr_host
        self.ibkr_port = ibkr_port
        
        self._sources: dict[DataSourceType, DataSource] = {}
        self._primary: Optional[DataSourceType] = None
        self._quote_cache: dict[str, tuple[Quote, datetime]] = {}
        self._cache_ttl = timedelta(seconds=5)  # Cache quotes for 5 seconds
    
    def _create_source(self, source_type: DataSourceType) -> DataSource:
        """Create a data source instance"""
        if source_type == DataSourceType.YFINANCE:
            return YFinanceDataSource()
        elif source_type == DataSourceType.IBKR_DELAYED:
            return IBKRDelayedDataSource(self.ibkr_host, self.ibkr_port)
        elif source_type == DataSourceType.IBKR_REALTIME:
            return IBKRRealtimeDataSource(self.ibkr_host, self.ibkr_port)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
    
    def connect(self, source_types: Optional[list[DataSourceType]] = None) -> bool:
        """
        Connect to data sources.
        
        Args:
            source_types: Which sources to connect (default: just YFinance for safety)
        
        Returns:
            True if at least one source connected
        """
        if source_types is None:
            # Default: just YFinance (always available)
            source_types = [DataSourceType.YFINANCE]
        
        connected_any = False
        
        for source_type in source_types:
            try:
                source = self._create_source(source_type)
                if source.connect():
                    self._sources[source_type] = source
                    connected_any = True
                    
                    # Set as primary if it's first in priority
                    if self._primary is None:
                        self._primary = source_type
            except Exception as e:
                logger.warning(f"Failed to connect {source_type.value}: {e}")
        
        return connected_any
    
    def disconnect(self):
        """Disconnect all sources"""
        for source in self._sources.values():
            source.disconnect()
        self._sources.clear()
        self._primary = None
    
    def set_primary(self, source_type: DataSourceType) -> bool:
        """Set the primary data source"""
        if source_type in self._sources:
            self._primary = source_type
            logger.info(f"🎯 Primary data source: {source_type.value}")
            return True
        return False
    
    @property
    def primary_source(self) -> Optional[DataSource]:
        """Get the primary data source"""
        if self._primary and self._primary in self._sources:
            return self._sources[self._primary]
        return None
    
    def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Quote]:
        """
        Get quote with automatic fallback.
        
        Args:
            symbol: Stock symbol
            use_cache: Use cached quote if fresh (default: True)
            
        Returns:
            Quote or None if all sources fail
        """
        # Check cache
        if use_cache and symbol in self._quote_cache:
            quote, cached_at = self._quote_cache[symbol]
            if datetime.now() - cached_at < self._cache_ttl:
                return quote
        
        # Try sources in priority order
        for source_type in self.priority:
            if source_type not in self._sources:
                continue
            
            source = self._sources[source_type]
            if not source.connected:
                continue
            
            quote = source.get_quote(symbol)
            if quote and quote.is_valid():
                # Cache the quote
                self._quote_cache[symbol] = (quote, datetime.now())
                return quote
        
        logger.warning(f"No data available for {symbol} from any source")
        return None
    
    def get_quotes(self, symbols: Optional[list[str]] = None) -> dict[str, Quote]:
        """Get quotes for multiple symbols (default: watchlist)"""
        symbols = symbols or self.WATCHLIST
        quotes = {}
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quotes[symbol] = quote
        return quotes
    
    def get_watchlist_quotes(self) -> dict[str, Quote]:
        """Get quotes for all watchlist symbols"""
        return self.get_quotes(self.WATCHLIST)
    
    def get_historical(
        self, 
        symbol: str, 
        period: str = "1d",
        interval: str = "1m"
    ) -> Optional[pd.DataFrame]:
        """Get historical data with fallback"""
        for source_type in self.priority:
            if source_type not in self._sources:
                continue
            
            source = self._sources[source_type]
            if not source.connected:
                continue
            
            df = source.get_historical(symbol, period, interval)
            if df is not None and not df.empty:
                return df
        
        return None
    
    def status(self) -> dict:
        """Get status of all data sources"""
        return {
            "primary": self._primary.value if self._primary else None,
            "sources": {
                st.value: {
                    "connected": source.connected,
                    "name": source.name
                }
                for st, source in self._sources.items()
            },
            "cache_size": len(self._quote_cache),
            "priority": [p.value for p in self.priority]
        }
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_live_quotes(symbols: Optional[list[str]] = None) -> dict[str, Quote]:
    """
    Quick function to get live quotes.
    Uses YFinance by default.
    
    Usage:
        quotes = get_live_quotes(["QBTS", "IONQ"])
        print(f"QBTS: ${quotes['QBTS'].last:.2f}")
    """
    with DataSourceManager() as manager:
        return manager.get_quotes(symbols)


def get_quote(symbol: str) -> Optional[Quote]:
    """Get a single quote"""
    with DataSourceManager() as manager:
        return manager.get_quote(symbol)


# =============================================================================
# MAIN - TEST THE MODULE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Data Sources Module Test")
    print("=" * 60)
    
    # Test YFinance (always available)
    print("\n📊 Testing YFinance Data Source")
    print("-" * 40)
    
    with DataSourceManager() as manager:
        print(f"Status: {manager.status()}")
        
        print("\nWatchlist Quotes:")
        quotes = manager.get_watchlist_quotes()
        for symbol, quote in quotes.items():
            print(f"  {symbol}: ${quote.last:.2f} (source: {quote.source})")
        
        print("\nHistorical Data (QBTS, 1d, 5m):")
        df = manager.get_historical("QBTS", period="1d", interval="5m")
        if df is not None:
            print(f"  Rows: {len(df)}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Last close: ${df['close'].iloc[-1]:.2f}")
        else:
            print("  No data available")
    
    print("\n" + "=" * 60)
    print("✅ Data sources test complete!")
    print("=" * 60)
