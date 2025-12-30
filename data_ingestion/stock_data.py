"""
HERMES_Quantum - Stock Data Fetcher
Data Ingestion Module - yfinance wrapper

Fetches OHLCV data, fundamentals, and options data for quantum stocks.
Uses yfinance (free, 15-minute delay, no API key needed).

Features:
- OHLCV historical data
- Intraday data (1min to 1h intervals)
- Fundamentals (P/E, market cap, etc.)
- Options chains (for Agent 11 analysis)
- Earnings calendar
- Caching with Parquet format

Cost: $0/month (yfinance is free)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataFetcher:
    """
    Fetches stock data using yfinance.
    
    Usage:
        fetcher = StockDataFetcher()
        
        # Get quantum stocks OHLCV
        df = fetcher.fetch_quantum_stocks(period='6mo')
        
        # Get single stock
        df = fetcher.fetch_ohlcv('IONQ', start='2024-01-01', end='2024-12-31')
        
        # Get fundamentals
        info = fetcher.fetch_fundamentals('QBTS')
    """
    
    # Our quantum computing stock universe
    QUANTUM_TICKERS = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
    
    # Cache directory
    CACHE_DIR = 'outputs/data/stock_cache'
    
    def __init__(self, cache_enabled: bool = True):
        """
        Initialize the stock data fetcher.
        
        Args:
            cache_enabled: Whether to cache data locally
        """
        self.cache_enabled = cache_enabled
        if cache_enabled:
            Path(self.CACHE_DIR).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, ticker: str, data_type: str = 'ohlcv') -> str:
        """Get cache file path for a ticker"""
        return os.path.join(self.CACHE_DIR, f"{ticker}_{data_type}.parquet")
    
    def _load_from_cache(self, ticker: str, data_type: str = 'ohlcv') -> Optional[pd.DataFrame]:
        """Load data from cache if exists and fresh"""
        cache_path = self._get_cache_path(ticker, data_type)
        
        if not os.path.exists(cache_path):
            return None
        
        # Check if cache is fresh (less than 1 hour old)
        mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
        if datetime.now() - mtime > timedelta(hours=1):
            return None
        
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Cache read error for {ticker}: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame, ticker: str, data_type: str = 'ohlcv'):
        """Save data to cache"""
        if not self.cache_enabled or df is None or df.empty:
            return
        
        try:
            cache_path = self._get_cache_path(ticker, data_type)
            df.to_parquet(cache_path)
            logger.debug(f"Cached {ticker} {data_type} data")
        except Exception as e:
            logger.warning(f"Cache write error for {ticker}: {e}")
    
    def fetch_ohlcv(
        self,
        ticker: str,
        start: str = None,
        end: str = None,
        period: str = None,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            period: Alternative to start/end (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            
            if period:
                df = stock.history(period=period, interval=interval)
            elif start and end:
                df = stock.history(start=start, end=end, interval=interval)
            else:
                # Default to 6 months
                df = stock.history(period='6mo', interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()
            
            # Add ticker column
            df['ticker'] = ticker
            
            # Clean column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Ensure index is datetime
            df.index = pd.to_datetime(df.index)
            df.index.name = 'date'
            
            logger.info(f"Fetched {len(df)} rows for {ticker} ({interval} interval)")
            
            # Cache daily data
            if interval == '1d':
                self._save_to_cache(df, ticker, 'ohlcv')
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            return pd.DataFrame()
    
    def fetch_quantum_stocks(
        self,
        period: str = '6mo',
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for all quantum stocks.
        
        Args:
            period: Time period (1mo, 3mo, 6mo, 1y, etc.)
            interval: Data interval
            
        Returns:
            Combined DataFrame with all stocks
        """
        all_data = []
        
        for ticker in self.QUANTUM_TICKERS:
            df = self.fetch_ohlcv(ticker, period=period, interval=interval)
            if not df.empty:
                all_data.append(df)
        
        if not all_data:
            return pd.DataFrame()
        
        combined = pd.concat(all_data)
        logger.info(f"Fetched {len(combined)} total rows for {len(self.QUANTUM_TICKERS)} quantum stocks")
        
        return combined
    
    def fetch_quantum_stocks_wide(
        self,
        period: str = "3mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch quantum stock data in wide format (tickers as columns).
        
        Args:
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with date index and ticker columns (close prices)
        """
        long_data = self.fetch_quantum_stocks(period, interval)
        
        if long_data.empty:
            return pd.DataFrame()
        
        # Pivot to wide format: use 'close' prices with tickers as columns
        wide_data = long_data.pivot_table(
            index=long_data.index,
            columns='ticker',
            values='close'
        )
        
        return wide_data
    
    def fetch_fundamentals(self, ticker: str) -> Dict:
        """
        Fetch fundamental data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with fundamental metrics
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract key fundamentals
            fundamentals = {
                'ticker': ticker,
                'name': info.get('shortName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'trailing_pe': info.get('trailingPE', None),
                'forward_pe': info.get('forwardPE', None),
                'price_to_book': info.get('priceToBook', None),
                'price_to_sales': info.get('priceToSalesTrailing12Months', None),
                'revenue': info.get('totalRevenue', 0),
                'revenue_growth': info.get('revenueGrowth', None),
                'gross_margins': info.get('grossMargins', None),
                'operating_margins': info.get('operatingMargins', None),
                'profit_margins': info.get('profitMargins', None),
                'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'beta': info.get('beta', None),
                'shares_outstanding': info.get('sharesOutstanding', 0),
                'short_ratio': info.get('shortRatio', None),
                'short_percent_of_float': info.get('shortPercentOfFloat', None),
                'institutional_ownership': info.get('heldPercentInstitutions', None),
                'fetched_at': datetime.now().isoformat(),
            }
            
            logger.info(f"Fetched fundamentals for {ticker}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def fetch_all_fundamentals(self) -> pd.DataFrame:
        """
        Fetch fundamentals for all quantum stocks.
        
        Returns:
            DataFrame with fundamentals for all tickers
        """
        all_fundamentals = []
        
        for ticker in self.QUANTUM_TICKERS:
            fund = self.fetch_fundamentals(ticker)
            all_fundamentals.append(fund)
        
        return pd.DataFrame(all_fundamentals)
    
    def fetch_options_chain(self, ticker: str, expiry_index: int = 0) -> Dict[str, pd.DataFrame]:
        """
        Fetch options chain for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            expiry_index: Which expiry to fetch (0 = nearest)
            
        Returns:
            Dict with 'calls' and 'puts' DataFrames
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get available expiries
            expiries = stock.options
            if not expiries:
                logger.warning(f"No options data for {ticker}")
                return {'calls': pd.DataFrame(), 'puts': pd.DataFrame()}
            
            # Get the requested expiry
            if expiry_index >= len(expiries):
                expiry_index = 0
            
            expiry = expiries[expiry_index]
            opt_chain = stock.option_chain(expiry)
            
            logger.info(f"Fetched options chain for {ticker} expiring {expiry}")
            
            return {
                'calls': opt_chain.calls,
                'puts': opt_chain.puts,
                'expiry': expiry,
            }
            
        except Exception as e:
            logger.error(f"Error fetching options for {ticker}: {e}")
            return {'calls': pd.DataFrame(), 'puts': pd.DataFrame()}
    
    def fetch_options_metrics(self, ticker: str) -> Dict:
        """
        Calculate options metrics (put/call ratio, max pain, etc.)
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with options metrics
        """
        try:
            stock = yf.Ticker(ticker)
            expiries = stock.options
            
            if not expiries or len(expiries) < 1:
                return {'ticker': ticker, 'error': 'No options data'}
            
            # Get next 3 expiries
            metrics = []
            
            for expiry in expiries[:3]:
                chain = stock.option_chain(expiry)
                calls = chain.calls
                puts = chain.puts
                
                # Calculate metrics
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                total_call_vol = calls['volume'].sum()
                total_put_vol = puts['volume'].sum()
                
                put_call_ratio_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                put_call_ratio_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0
                
                # Max pain calculation (simplified)
                # Strike with highest combined OI
                all_strikes = set(calls['strike'].tolist() + puts['strike'].tolist())
                max_pain_strike = None
                max_pain_oi = 0
                
                for strike in all_strikes:
                    call_oi = calls[calls['strike'] == strike]['openInterest'].sum()
                    put_oi = puts[puts['strike'] == strike]['openInterest'].sum()
                    total_oi = call_oi + put_oi
                    if total_oi > max_pain_oi:
                        max_pain_oi = total_oi
                        max_pain_strike = strike
                
                metrics.append({
                    'expiry': expiry,
                    'total_call_oi': int(total_call_oi),
                    'total_put_oi': int(total_put_oi),
                    'put_call_ratio_oi': round(put_call_ratio_oi, 3),
                    'total_call_volume': int(total_call_vol) if not pd.isna(total_call_vol) else 0,
                    'total_put_volume': int(total_put_vol) if not pd.isna(total_put_vol) else 0,
                    'put_call_ratio_volume': round(put_call_ratio_vol, 3),
                    'max_pain_strike': max_pain_strike,
                })
            
            logger.info(f"Calculated options metrics for {ticker}")
            return {
                'ticker': ticker,
                'expiries': metrics,
                'fetched_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error calculating options metrics for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def fetch_earnings_calendar(self, ticker: str) -> Dict:
        """
        Fetch earnings calendar for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with earnings dates and estimates
        """
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            if calendar is None:
                return {'ticker': ticker, 'error': 'No calendar data'}
            
            # Convert to dict
            if isinstance(calendar, pd.DataFrame):
                calendar_dict = calendar.to_dict()
            else:
                calendar_dict = dict(calendar) if calendar else {}
            
            return {
                'ticker': ticker,
                'calendar': calendar_dict,
                'fetched_at': datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error fetching calendar for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def get_latest_prices(self) -> pd.DataFrame:
        """
        Get latest prices for all quantum stocks (quick check).
        
        Returns:
            DataFrame with latest price info
        """
        data = []
        
        for ticker in self.QUANTUM_TICKERS:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                data.append({
                    'ticker': ticker,
                    'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                    'change': info.get('regularMarketChange', 0),
                    'change_pct': info.get('regularMarketChangePercent', 0),
                    'volume': info.get('regularMarketVolume', 0),
                    'market_cap': info.get('marketCap', 0),
                })
            except Exception as e:
                logger.error(f"Error getting price for {ticker}: {e}")
                data.append({'ticker': ticker, 'error': str(e)})
        
        return pd.DataFrame(data)
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and report issues.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Dict with quality metrics
        """
        if df.empty:
            return {'valid': False, 'error': 'Empty DataFrame'}
        
        issues = []
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            issues.append(f"Missing values: {missing[missing > 0].to_dict()}")
        
        # Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            issues.append(f"Duplicate rows: {duplicates}")
        
        # Check date range
        if 'date' in df.index.names or isinstance(df.index, pd.DatetimeIndex):
            date_range = (df.index.min(), df.index.max())
            trading_days = len(df)
        else:
            date_range = None
            trading_days = len(df)
        
        return {
            'valid': len(issues) == 0,
            'rows': len(df),
            'columns': list(df.columns),
            'date_range': date_range,
            'trading_days': trading_days,
            'issues': issues,
        }


def run_demo():
    """Demo the stock data fetcher"""
    fetcher = StockDataFetcher()
    
    print("\n=== HERMES_Quantum Stock Data Fetcher Demo ===\n")
    
    # Fetch quantum stocks
    print("Fetching 6-month data for quantum stocks...")
    df = fetcher.fetch_quantum_stocks(period='6mo')
    print(f"Retrieved {len(df)} rows")
    print(f"Tickers: {df['ticker'].unique().tolist()}")
    print(f"\nSample data:")
    print(df.head(10))
    
    # Validate data
    print("\n--- Data Quality ---")
    quality = fetcher.validate_data_quality(df)
    print(f"Valid: {quality['valid']}")
    print(f"Rows: {quality['rows']}")
    print(f"Issues: {quality['issues']}")
    
    # Latest prices
    print("\n--- Latest Prices ---")
    prices = fetcher.get_latest_prices()
    print(prices.to_string(index=False))
    
    # Fundamentals
    print("\n--- Fundamentals (IONQ) ---")
    fund = fetcher.fetch_fundamentals('IONQ')
    for key in ['name', 'market_cap', 'trailing_pe', 'revenue', 'revenue_growth']:
        print(f"  {key}: {fund.get(key)}")
    
    # Options metrics
    print("\n--- Options Metrics (IONQ) ---")
    opts = fetcher.fetch_options_metrics('IONQ')
    if 'expiries' in opts:
        for exp in opts['expiries'][:2]:
            print(f"  {exp['expiry']}: P/C Ratio (OI) = {exp['put_call_ratio_oi']}")
    
    return df


if __name__ == "__main__":
    run_demo()
