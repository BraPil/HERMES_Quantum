"""
HERMES Market Data Fetcher
==========================
Unified interface for fetching real-time and historical market data.

Data Sources:
- Yahoo Finance (yfinance): Real-time quotes, historical data, financials
- Alpha Vantage: Intraday data, technical indicators, news sentiment
- Fallback caching for rate limit handling

Created: 2025-12-30
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import sqlite3
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed. Run: pip install yfinance")

try:
    from alpha_vantage.timeseries import TimeSeries
    from alpha_vantage.techindicators import TechIndicators
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False
    logger.warning("alpha_vantage not installed. Run: pip install alpha_vantage")


class DataSource(Enum):
    """Available data sources."""
    YAHOO_FINANCE = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    CACHE = "cache"


class Interval(Enum):
    """Data intervals for historical data."""
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    DAY_1 = "1d"
    WEEK_1 = "1wk"
    MONTH_1 = "1mo"


@dataclass
class Quote:
    """Real-time quote data."""
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    prev_close: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: DataSource = DataSource.YAHOO_FINANCE
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['source'] = self.source.value
        return result


@dataclass
class HistoricalData:
    """Historical OHLCV data."""
    ticker: str
    interval: Interval
    data: pd.DataFrame  # columns: open, high, low, close, volume
    start_date: datetime
    end_date: datetime
    source: DataSource = DataSource.YAHOO_FINANCE
    
    @property
    def prices(self) -> np.ndarray:
        """Get closing prices as numpy array."""
        return self.data['close'].values if 'close' in self.data.columns else np.array([])
    
    @property
    def latest_price(self) -> float:
        """Get most recent closing price."""
        if len(self.data) > 0:
            return float(self.data['close'].iloc[-1])
        return 0.0
    
    @property
    def returns(self) -> np.ndarray:
        """Calculate daily returns."""
        if 'close' in self.data.columns and len(self.data) > 1:
            return self.data['close'].pct_change().dropna().values
        return np.array([])


@dataclass
class CompanyInfo:
    """Company fundamental data."""
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    avg_volume: Optional[int] = None
    description: Optional[str] = None
    website: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseDataFetcher(ABC):
    """Base class for data fetchers."""
    
    @abstractmethod
    def get_quote(self, ticker: str) -> Optional[Quote]:
        """Get real-time quote."""
        pass
    
    @abstractmethod
    def get_historical(
        self,
        ticker: str,
        period: str = "1mo",
        interval: Interval = Interval.DAY_1
    ) -> Optional[HistoricalData]:
        """Get historical OHLCV data."""
        pass
    
    @abstractmethod
    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Get company fundamental data."""
        pass


class YahooFinanceFetcher(BaseDataFetcher):
    """
    Yahoo Finance data fetcher.
    
    Features:
    - Real-time quotes
    - Historical data (1m to 1mo intervals)
    - Company fundamentals
    - No API key required
    - Rate limited to ~2000 requests/hour
    """
    
    def __init__(self, cache_ttl_seconds: int = 60):
        """
        Initialize Yahoo Finance fetcher.
        
        Args:
            cache_ttl_seconds: How long to cache quotes (default 60s)
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance not installed. Run: pip install yfinance")
        
        self.cache_ttl = cache_ttl_seconds
        self._quote_cache: Dict[str, Tuple[Quote, datetime]] = {}
        self._ticker_cache: Dict[str, yf.Ticker] = {}
        
        logger.info("YahooFinanceFetcher initialized")
    
    def _get_ticker(self, ticker: str) -> yf.Ticker:
        """Get or create cached Ticker object."""
        if ticker not in self._ticker_cache:
            self._ticker_cache[ticker] = yf.Ticker(ticker)
        return self._ticker_cache[ticker]
    
    def get_quote(self, ticker: str) -> Optional[Quote]:
        """
        Get real-time quote for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Quote object or None on error
        """
        # Check cache
        if ticker in self._quote_cache:
            cached, cached_time = self._quote_cache[ticker]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                return cached
        
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            
            # Get fast info for real-time data
            fast_info = stock.fast_info if hasattr(stock, 'fast_info') else {}
            
            quote = Quote(
                ticker=ticker,
                price=fast_info.get('lastPrice', info.get('regularMarketPrice', 0)),
                change=info.get('regularMarketChange', 0),
                change_percent=info.get('regularMarketChangePercent', 0),
                volume=int(info.get('regularMarketVolume', 0)),
                bid=info.get('bid'),
                ask=info.get('ask'),
                high=info.get('regularMarketDayHigh'),
                low=info.get('regularMarketDayLow'),
                open=info.get('regularMarketOpen'),
                prev_close=info.get('regularMarketPreviousClose'),
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE'),
                source=DataSource.YAHOO_FINANCE
            )
            
            # Cache the result
            self._quote_cache[ticker] = (quote, datetime.now())
            
            return quote
            
        except Exception as e:
            logger.error(f"Failed to get quote for {ticker}: {e}")
            return None
    
    def get_historical(
        self,
        ticker: str,
        period: str = "1mo",
        interval: Interval = Interval.DAY_1
    ) -> Optional[HistoricalData]:
        """
        Get historical OHLCV data.
        
        Args:
            ticker: Stock ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval
            
        Returns:
            HistoricalData object or None on error
        """
        try:
            stock = self._get_ticker(ticker)
            
            # yfinance uses different interval strings
            yf_interval = interval.value
            
            # Download historical data
            df = stock.history(period=period, interval=yf_interval)
            
            if df.empty:
                logger.warning(f"No historical data for {ticker}")
                return None
            
            # Normalize column names to lowercase
            df.columns = [c.lower() for c in df.columns]
            
            # Ensure we have required columns
            required = ['open', 'high', 'low', 'close', 'volume']
            for col in required:
                if col not in df.columns:
                    df[col] = 0
            
            return HistoricalData(
                ticker=ticker,
                interval=interval,
                data=df[required],
                start_date=df.index[0].to_pydatetime() if hasattr(df.index[0], 'to_pydatetime') else df.index[0],
                end_date=df.index[-1].to_pydatetime() if hasattr(df.index[-1], 'to_pydatetime') else df.index[-1],
                source=DataSource.YAHOO_FINANCE
            )
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {ticker}: {e}")
            return None
    
    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """
        Get company fundamental data.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CompanyInfo object or None on error
        """
        try:
            stock = self._get_ticker(ticker)
            info = stock.info
            
            return CompanyInfo(
                ticker=ticker,
                name=info.get('longName', info.get('shortName', ticker)),
                sector=info.get('sector'),
                industry=info.get('industry'),
                market_cap=info.get('marketCap'),
                pe_ratio=info.get('trailingPE'),
                eps=info.get('trailingEps'),
                dividend_yield=info.get('dividendYield'),
                beta=info.get('beta'),
                fifty_two_week_high=info.get('fiftyTwoWeekHigh'),
                fifty_two_week_low=info.get('fiftyTwoWeekLow'),
                avg_volume=info.get('averageVolume'),
                description=info.get('longBusinessSummary'),
                website=info.get('website')
            )
            
        except Exception as e:
            logger.error(f"Failed to get company info for {ticker}: {e}")
            return None
    
    def get_multiple_quotes(self, tickers: List[str]) -> Dict[str, Quote]:
        """
        Get quotes for multiple tickers efficiently.
        
        Args:
            tickers: List of stock ticker symbols
            
        Returns:
            Dict of ticker -> Quote
        """
        results = {}
        
        # Use batch download for efficiency
        try:
            # Download all at once
            data = yf.download(
                tickers,
                period="1d",
                interval="1m",
                progress=False,
                threads=True
            )
            
            # Also get individual info for each
            for ticker in tickers:
                quote = self.get_quote(ticker)
                if quote:
                    results[ticker] = quote
                    
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            # Fall back to individual fetches
            for ticker in tickers:
                quote = self.get_quote(ticker)
                if quote:
                    results[ticker] = quote
        
        return results


class AlphaVantageFetcher(BaseDataFetcher):
    """
    Alpha Vantage data fetcher.
    
    Features:
    - Intraday data (1min, 5min, 15min, 30min, 60min)
    - Technical indicators (SMA, EMA, RSI, MACD, etc.)
    - News sentiment data
    - Requires API key (free tier: 25 requests/day)
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize Alpha Vantage fetcher.
        
        Args:
            api_key: Alpha Vantage API key (or set ALPHA_VANTAGE_API_KEY env var)
        """
        if not ALPHA_VANTAGE_AVAILABLE:
            raise ImportError("alpha_vantage not installed. Run: pip install alpha_vantage")
        
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        
        if not self.api_key:
            logger.warning("No Alpha Vantage API key provided. Set ALPHA_VANTAGE_API_KEY env var.")
            self.ts = None
            self.ti = None
        else:
            self.ts = TimeSeries(key=self.api_key, output_format='pandas')
            self.ti = TechIndicators(key=self.api_key, output_format='pandas')
        
        self._last_request_time = 0
        self._min_request_interval = 12  # Free tier: 5 requests/minute
        
        logger.info("AlphaVantageFetcher initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def get_quote(self, ticker: str) -> Optional[Quote]:
        """Get real-time quote (uses intraday data)."""
        if not self.ts:
            return None
        
        try:
            self._rate_limit()
            data, meta = self.ts.get_quote_endpoint(ticker)
            
            return Quote(
                ticker=ticker,
                price=float(data['05. price'].iloc[0]),
                change=float(data['09. change'].iloc[0]),
                change_percent=float(data['10. change percent'].iloc[0].rstrip('%')),
                volume=int(data['06. volume'].iloc[0]),
                high=float(data['03. high'].iloc[0]),
                low=float(data['04. low'].iloc[0]),
                open=float(data['02. open'].iloc[0]),
                prev_close=float(data['08. previous close'].iloc[0]),
                source=DataSource.ALPHA_VANTAGE
            )
            
        except Exception as e:
            logger.error(f"Alpha Vantage quote failed for {ticker}: {e}")
            return None
    
    def get_historical(
        self,
        ticker: str,
        period: str = "1mo",
        interval: Interval = Interval.DAY_1
    ) -> Optional[HistoricalData]:
        """Get historical data."""
        if not self.ts:
            return None
        
        try:
            self._rate_limit()
            
            # Map intervals
            if interval in [Interval.MINUTE_1, Interval.MINUTE_5, Interval.MINUTE_15, 
                           Interval.MINUTE_30, Interval.HOUR_1]:
                # Intraday
                av_interval = {
                    Interval.MINUTE_1: '1min',
                    Interval.MINUTE_5: '5min',
                    Interval.MINUTE_15: '15min',
                    Interval.MINUTE_30: '30min',
                    Interval.HOUR_1: '60min'
                }[interval]
                
                data, meta = self.ts.get_intraday(ticker, interval=av_interval, outputsize='full')
            else:
                # Daily
                data, meta = self.ts.get_daily(ticker, outputsize='full')
            
            # Rename columns
            data.columns = ['open', 'high', 'low', 'close', 'volume']
            data = data.sort_index()
            
            return HistoricalData(
                ticker=ticker,
                interval=interval,
                data=data,
                start_date=data.index[0].to_pydatetime(),
                end_date=data.index[-1].to_pydatetime(),
                source=DataSource.ALPHA_VANTAGE
            )
            
        except Exception as e:
            logger.error(f"Alpha Vantage historical failed for {ticker}: {e}")
            return None
    
    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Get company info (limited in Alpha Vantage free tier)."""
        # Alpha Vantage company overview requires premium
        return None
    
    def get_rsi(self, ticker: str, period: int = 14) -> Optional[pd.DataFrame]:
        """Get RSI technical indicator."""
        if not self.ti:
            return None
        
        try:
            self._rate_limit()
            data, meta = self.ti.get_rsi(ticker, interval='daily', time_period=period)
            return data
        except Exception as e:
            logger.error(f"Alpha Vantage RSI failed for {ticker}: {e}")
            return None
    
    def get_macd(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get MACD technical indicator."""
        if not self.ti:
            return None
        
        try:
            self._rate_limit()
            data, meta = self.ti.get_macd(ticker, interval='daily')
            return data
        except Exception as e:
            logger.error(f"Alpha Vantage MACD failed for {ticker}: {e}")
            return None


class MarketDataFetcher:
    """
    Unified market data fetcher with fallback support.
    
    Prioritizes data sources:
    1. Yahoo Finance (no API key required, fast)
    2. Alpha Vantage (fallback, has rate limits)
    3. Cache (if all sources fail)
    
    Usage:
        fetcher = get_market_data_fetcher()
        
        # Get single quote
        quote = fetcher.get_quote("QBTS")
        
        # Get multiple quotes
        quotes = fetcher.get_quotes(["QBTS", "IONQ", "RGTI"])
        
        # Get historical data for forecasting
        history = fetcher.get_historical("QBTS", period="1mo")
        prices = history.prices  # numpy array for models
    """
    
    def __init__(
        self,
        use_yahoo: bool = True,
        use_alpha_vantage: bool = False,  # Disabled by default - Yahoo is faster and more current
        alpha_vantage_key: str = None,
        cache_path: str = None,
        cache_ttl_seconds: int = 60
    ):
        """
        Initialize unified data fetcher.
        
        Args:
            use_yahoo: Enable Yahoo Finance
            use_alpha_vantage: Enable Alpha Vantage (disabled by default - slower, rate limited)
            alpha_vantage_key: API key for Alpha Vantage
            cache_path: Path to SQLite cache
            cache_ttl_seconds: Quote cache TTL
        """
        self.fetchers: List[BaseDataFetcher] = []
        
        # Initialize Yahoo Finance (primary)
        if use_yahoo and YFINANCE_AVAILABLE:
            try:
                self.yahoo = YahooFinanceFetcher(cache_ttl_seconds=cache_ttl_seconds)
                self.fetchers.append(self.yahoo)
                logger.info("Yahoo Finance enabled")
            except Exception as e:
                logger.warning(f"Failed to init Yahoo Finance: {e}")
                self.yahoo = None
        else:
            self.yahoo = None
        
        # Initialize Alpha Vantage (secondary)
        if use_alpha_vantage and ALPHA_VANTAGE_AVAILABLE:
            try:
                self.alpha_vantage = AlphaVantageFetcher(api_key=alpha_vantage_key)
                self.fetchers.append(self.alpha_vantage)
                logger.info("Alpha Vantage enabled")
            except Exception as e:
                logger.warning(f"Failed to init Alpha Vantage: {e}")
                self.alpha_vantage = None
        else:
            self.alpha_vantage = None
        
        # Initialize cache
        if cache_path is None:
            cache_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "outputs", "data", "market_cache.db"
            )
        self.cache_path = os.path.abspath(cache_path)
        self._init_cache()
        
        # Default tickers (quantum computing stocks)
        self.default_tickers = ["QBTS", "IONQ", "RGTI", "QUBT"]
        
        logger.info(f"MarketDataFetcher initialized with {len(self.fetchers)} sources")
    
    def _init_cache(self):
        """Initialize SQLite cache."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quote_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_cache (
                ticker TEXT,
                interval TEXT,
                period TEXT,
                data TEXT,
                timestamp TEXT,
                PRIMARY KEY (ticker, interval, period)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _cache_quote(self, quote: Quote):
        """Cache a quote."""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO quote_cache (ticker, data, timestamp)
            VALUES (?, ?, ?)
        ''', (quote.ticker, json.dumps(quote.to_dict()), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def _get_cached_quote(self, ticker: str, max_age_seconds: int = 300) -> Optional[Quote]:
        """Get cached quote if fresh enough."""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT data, timestamp FROM quote_cache WHERE ticker = ?',
            (ticker,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            cached_time = datetime.fromisoformat(row[1])
            if (datetime.now() - cached_time).total_seconds() < max_age_seconds:
                data = json.loads(row[0])
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                data['source'] = DataSource.CACHE
                return Quote(**{k: v for k, v in data.items() if k != 'source'}, source=DataSource.CACHE)
        
        return None
    
    def get_quote(self, ticker: str, use_cache: bool = True) -> Optional[Quote]:
        """
        Get real-time quote for a ticker.
        
        Tries sources in order: Yahoo Finance -> Alpha Vantage -> Cache
        
        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use cache as fallback
            
        Returns:
            Quote object or None
        """
        # Try each fetcher in order
        for fetcher in self.fetchers:
            try:
                quote = fetcher.get_quote(ticker)
                if quote:
                    self._cache_quote(quote)
                    return quote
            except Exception as e:
                logger.warning(f"Fetcher {type(fetcher).__name__} failed for {ticker}: {e}")
                continue
        
        # Fall back to cache
        if use_cache:
            cached = self._get_cached_quote(ticker)
            if cached:
                logger.info(f"Using cached quote for {ticker}")
                return cached
        
        logger.error(f"All sources failed for {ticker}")
        return None
    
    def get_quotes(self, tickers: List[str] = None) -> Dict[str, Quote]:
        """
        Get quotes for multiple tickers.
        
        Args:
            tickers: List of tickers (defaults to quantum stocks)
            
        Returns:
            Dict of ticker -> Quote
        """
        tickers = tickers or self.default_tickers
        results = {}
        
        # Try Yahoo Finance batch first
        if self.yahoo:
            results = self.yahoo.get_multiple_quotes(tickers)
        
        # Fill in missing with individual fetches
        for ticker in tickers:
            if ticker not in results:
                quote = self.get_quote(ticker)
                if quote:
                    results[ticker] = quote
        
        return results
    
    def get_historical(
        self,
        ticker: str,
        period: str = "1mo",
        interval: Interval = Interval.DAY_1
    ) -> Optional[HistoricalData]:
        """
        Get historical OHLCV data.
        
        Args:
            ticker: Stock ticker symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
            interval: Data interval
            
        Returns:
            HistoricalData object or None
        """
        for fetcher in self.fetchers:
            try:
                data = fetcher.get_historical(ticker, period=period, interval=interval)
                if data:
                    return data
            except Exception as e:
                logger.warning(f"Historical fetch failed: {e}")
                continue
        
        return None
    
    def get_prices_for_forecast(
        self,
        ticker: str,
        period: str = "3mo",
        interval: Interval = Interval.DAY_1
    ) -> Tuple[np.ndarray, float]:
        """
        Get price data formatted for forecasting models.
        
        Args:
            ticker: Stock ticker symbol
            period: Historical period
            interval: Data interval
            
        Returns:
            Tuple of (prices array, current price)
        """
        history = self.get_historical(ticker, period=period, interval=interval)
        
        if history is None:
            return np.array([]), 0.0
        
        return history.prices, history.latest_price
    
    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Get company fundamental data."""
        for fetcher in self.fetchers:
            try:
                info = fetcher.get_company_info(ticker)
                if info:
                    return info
            except Exception as e:
                continue
        return None
    
    def get_all_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get all available data for a ticker.
        
        Returns dict with:
        - quote: Real-time quote
        - history_1d: 1-day intraday data
        - history_1mo: 1-month daily data
        - company: Company info
        """
        return {
            "ticker": ticker,
            "quote": self.get_quote(ticker),
            "history_1d": self.get_historical(ticker, period="1d", interval=Interval.MINUTE_5),
            "history_1mo": self.get_historical(ticker, period="1mo", interval=Interval.DAY_1),
            "company": self.get_company_info(ticker)
        }


# Singleton instance
_fetcher_instance: Optional[MarketDataFetcher] = None


def get_market_data_fetcher() -> MarketDataFetcher:
    """Get the singleton MarketDataFetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = MarketDataFetcher()
    return _fetcher_instance


def reset_market_data_fetcher() -> None:
    """Reset the singleton (for testing)."""
    global _fetcher_instance
    _fetcher_instance = None


# Demo function
def demo():
    """Demonstrate market data fetching."""
    print("=" * 60)
    print("HERMES Market Data Fetcher Demo")
    print("=" * 60)
    
    fetcher = get_market_data_fetcher()
    tickers = ["QBTS", "IONQ", "RGTI", "QUBT"]
    
    print("\n📊 Real-Time Quotes:")
    print("-" * 60)
    
    quotes = fetcher.get_quotes(tickers)
    for ticker, quote in quotes.items():
        if quote:
            emoji = "🟢" if quote.change >= 0 else "🔴"
            print(f"{emoji} {ticker}: ${quote.price:.2f} ({quote.change_percent:+.2f}%) | Vol: {quote.volume:,}")
        else:
            print(f"❌ {ticker}: No data")
    
    print("\n📈 Historical Data (QBTS - 1 month):")
    print("-" * 60)
    
    history = fetcher.get_historical("QBTS", period="1mo", interval=Interval.DAY_1)
    if history:
        print(f"Date range: {history.start_date.date()} to {history.end_date.date()}")
        print(f"Data points: {len(history.data)}")
        print(f"Latest price: ${history.latest_price:.2f}")
        print(f"Price range: ${history.data['low'].min():.2f} - ${history.data['high'].max():.2f}")
    
    print("\n🏢 Company Info (IONQ):")
    print("-" * 60)
    
    info = fetcher.get_company_info("IONQ")
    if info:
        print(f"Name: {info.name}")
        print(f"Sector: {info.sector}")
        print(f"Industry: {info.industry}")
        print(f"Market Cap: ${info.market_cap:,.0f}" if info.market_cap else "Market Cap: N/A")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
