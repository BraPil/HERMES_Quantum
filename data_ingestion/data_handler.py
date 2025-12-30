"""
HERMES_Quantum - Unified Data Handler
Qlib-inspired DataHandler pattern for unified data access

This handler provides a unified interface to all data sources:
- Stock data (yfinance)
- News (RSS aggregator)
- Social sentiment (Reddit, StockTwits)
- Macro data (FRED - future)

Implements Qlib patterns:
- Processors for data transformation
- Selectors for data filtering
- Caching for performance
"""

import pandas as pd
import numpy as np
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Callable
from pathlib import Path

from .stock_data import StockDataFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Base class for data processors (Qlib-inspired).
    Processors transform data in a pipeline.
    """
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process the DataFrame"""
        raise NotImplementedError


class FillNAProcessor(DataProcessor):
    """Fill missing values"""
    
    def __init__(self, method: str = 'ffill', fill_value: float = None):
        self.method = method
        self.fill_value = fill_value
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.fill_value is not None:
            return df.fillna(self.fill_value)
        return df.fillna(method=self.method)


class NormalizeProcessor(DataProcessor):
    """Min-max normalization"""
    
    def __init__(self, columns: List[str] = None):
        self.columns = columns
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = self.columns or df.select_dtypes(include=[np.number]).columns
        result = df.copy()
        for col in cols:
            if col in result.columns:
                min_val = result[col].min()
                max_val = result[col].max()
                if max_val > min_val:
                    result[col] = (result[col] - min_val) / (max_val - min_val)
        return result


class RobustZScoreProcessor(DataProcessor):
    """Robust Z-score using median and MAD"""
    
    def __init__(self, columns: List[str] = None):
        self.columns = columns
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = self.columns or df.select_dtypes(include=[np.number]).columns
        result = df.copy()
        for col in cols:
            if col in result.columns:
                median = result[col].median()
                mad = (result[col] - median).abs().median()
                if mad > 0:
                    result[col] = (result[col] - median) / (mad * 1.4826)
        return result


class ReturnProcessor(DataProcessor):
    """Calculate returns from prices"""
    
    def __init__(self, price_col: str = 'close', periods: int = 1):
        self.price_col = price_col
        self.periods = periods
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        if self.price_col in result.columns:
            result[f'return_{self.periods}d'] = result[self.price_col].pct_change(self.periods)
        return result


class VolatilityProcessor(DataProcessor):
    """Calculate rolling volatility"""
    
    def __init__(self, price_col: str = 'close', window: int = 20):
        self.price_col = price_col
        self.window = window
    
    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        if self.price_col in result.columns:
            returns = result[self.price_col].pct_change()
            result[f'volatility_{self.window}d'] = returns.rolling(self.window).std() * np.sqrt(252)
        return result


class HERMESDataHandler:
    """
    Unified data handler for HERMES_Quantum.
    Qlib-inspired pattern for consistent data access.
    
    Usage:
        handler = HERMESDataHandler()
        
        # Fetch stock data with processing
        df = handler.fetch_stocks(
            tickers=['IONQ', 'QBTS'],
            period='6mo',
            processors=[
                FillNAProcessor(),
                ReturnProcessor(),
                VolatilityProcessor(),
            ]
        )
        
        # Fetch all data sources
        data = handler.fetch_all(period='3mo')
    """
    
    # Quantum stock universe
    QUANTUM_TICKERS = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
    
    def __init__(self, db_path: str = None, cache_enabled: bool = True):
        """
        Initialize the data handler.
        
        Args:
            db_path: Path to SQLite database for news/social data
            cache_enabled: Whether to enable caching
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'outputs/data/hermes.db')
        self.cache_enabled = cache_enabled
        
        # Initialize sub-fetchers
        self.stock_fetcher = StockDataFetcher(cache_enabled=cache_enabled)
        
        # Ensure database exists
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)
    
    def fetch_stocks(
        self,
        tickers: List[str] = None,
        start: str = None,
        end: str = None,
        period: str = '6mo',
        interval: str = '1d',
        processors: List[DataProcessor] = None
    ) -> pd.DataFrame:
        """
        Fetch stock data with optional processing.
        
        Args:
            tickers: List of tickers (default: quantum stocks)
            start: Start date
            end: End date
            period: Time period
            interval: Data interval
            processors: List of DataProcessor objects
            
        Returns:
            Processed DataFrame
        """
        tickers = tickers or self.QUANTUM_TICKERS
        
        all_data = []
        for ticker in tickers:
            df = self.stock_fetcher.fetch_ohlcv(
                ticker=ticker,
                start=start,
                end=end,
                period=period,
                interval=interval
            )
            if not df.empty:
                all_data.append(df)
        
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data)
        
        # Apply processors
        if processors:
            for processor in processors:
                result = processor(result)
        
        return result
    
    def fetch_news(self, hours: int = 24, ticker: str = None) -> List[Dict]:
        """
        Fetch news articles from database.
        
        Args:
            hours: Hours to look back
            ticker: Optional ticker filter
            
        Returns:
            List of news article dictionaries
        """
        if not os.path.exists(self.db_path):
            logger.warning("Database not found. Run news aggregator first.")
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        try:
            if ticker:
                cursor.execute('''
                    SELECT * FROM news_articles 
                    WHERE published > ? AND tickers LIKE ?
                    ORDER BY published DESC
                ''', (since, f'%{ticker}%'))
            else:
                cursor.execute('''
                    SELECT * FROM news_articles 
                    WHERE published > ?
                    ORDER BY published DESC
                ''', (since,))
            
            columns = [desc[0] for desc in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except sqlite3.OperationalError:
            logger.warning("News table not found. Run news aggregator first.")
            articles = []
        
        conn.close()
        return articles
    
    def fetch_social(
        self, 
        hours: int = 24, 
        ticker: str = None,
        source: str = 'all'
    ) -> Dict[str, List[Dict]]:
        """
        Fetch social sentiment data from database.
        
        Args:
            hours: Hours to look back
            ticker: Optional ticker filter
            source: 'reddit', 'stocktwits', or 'all'
            
        Returns:
            Dict with 'reddit' and 'stocktwits' lists
        """
        if not os.path.exists(self.db_path):
            logger.warning("Database not found. Run collectors first.")
            return {'reddit': [], 'stocktwits': []}
        
        conn = sqlite3.connect(self.db_path)
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        result = {'reddit': [], 'stocktwits': []}
        
        # Reddit
        if source in ['reddit', 'all']:
            try:
                cursor = conn.cursor()
                if ticker:
                    cursor.execute('''
                        SELECT * FROM reddit_posts 
                        WHERE created_utc > ? AND tickers LIKE ?
                        ORDER BY score DESC
                    ''', (since, f'%{ticker}%'))
                else:
                    cursor.execute('''
                        SELECT * FROM reddit_posts 
                        WHERE created_utc > ?
                        ORDER BY score DESC
                    ''', (since,))
                
                columns = [desc[0] for desc in cursor.description]
                result['reddit'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            except sqlite3.OperationalError:
                logger.debug("Reddit table not found")
        
        # StockTwits
        if source in ['stocktwits', 'all']:
            try:
                cursor = conn.cursor()
                if ticker:
                    cursor.execute('''
                        SELECT * FROM stocktwits_messages 
                        WHERE created_at > ? AND tickers LIKE ?
                        ORDER BY created_at DESC
                    ''', (since, f'%{ticker}%'))
                else:
                    cursor.execute('''
                        SELECT * FROM stocktwits_messages 
                        WHERE created_at > ?
                        ORDER BY created_at DESC
                    ''', (since,))
                
                columns = [desc[0] for desc in cursor.description]
                result['stocktwits'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            except sqlite3.OperationalError:
                logger.debug("StockTwits table not found")
        
        conn.close()
        return result
    
    def fetch_all(
        self,
        period: str = '3mo',
        news_hours: int = 48,
        social_hours: int = 48,
        processors: List[DataProcessor] = None
    ) -> Dict:
        """
        Fetch all data sources in one call.
        
        Args:
            period: Stock data period
            news_hours: News lookback hours
            social_hours: Social lookback hours
            processors: Stock data processors
            
        Returns:
            Dict with all data sources
        """
        return {
            'stocks': self.fetch_stocks(period=period, processors=processors),
            'news': self.fetch_news(hours=news_hours),
            'social': self.fetch_social(hours=social_hours),
            'fetched_at': datetime.now().isoformat(),
        }
    
    def get_ticker_summary(self, ticker: str) -> Dict:
        """
        Get a complete summary for a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with stock data, news, social, fundamentals
        """
        # Stock data
        stocks = self.fetch_stocks(
            tickers=[ticker],
            period='3mo',
            processors=[ReturnProcessor(), VolatilityProcessor()]
        )
        
        # Latest price
        latest_price = None
        if not stocks.empty:
            latest = stocks.iloc[-1]
            latest_price = {
                'close': latest.get('close'),
                'volume': latest.get('volume'),
                'return_1d': latest.get('return_1d'),
            }
        
        # Fundamentals
        fundamentals = self.stock_fetcher.fetch_fundamentals(ticker)
        
        # News
        news = self.fetch_news(hours=48, ticker=ticker)
        
        # Social
        social = self.fetch_social(hours=48, ticker=ticker)
        
        # Options
        options = self.stock_fetcher.fetch_options_metrics(ticker)
        
        return {
            'ticker': ticker,
            'latest_price': latest_price,
            'fundamentals': fundamentals,
            'news_count': len(news),
            'recent_news': news[:5],
            'reddit_posts': len(social.get('reddit', [])),
            'stocktwits_messages': len(social.get('stocktwits', [])),
            'options': options,
            'fetched_at': datetime.now().isoformat(),
        }
    
    def get_sentiment_summary(self, hours: int = 24) -> Dict:
        """
        Get aggregated sentiment across all sources.
        
        Args:
            hours: Hours to aggregate
            
        Returns:
            Dict with sentiment stats by ticker
        """
        news = self.fetch_news(hours=hours)
        social = self.fetch_social(hours=hours)
        
        # Aggregate by ticker
        ticker_sentiment = {}
        
        for ticker in self.QUANTUM_TICKERS:
            ticker_sentiment[ticker] = {
                'news_count': 0,
                'news_positive': 0,
                'news_negative': 0,
                'reddit_count': 0,
                'reddit_avg_score': 0,
                'stocktwits_count': 0,
                'stocktwits_bullish': 0,
                'stocktwits_bearish': 0,
            }
        
        # Count news by ticker
        for article in news:
            tickers = article.get('tickers', '[]')
            if isinstance(tickers, str):
                import json
                tickers = json.loads(tickers) if tickers else []
            
            for ticker in tickers:
                if ticker in ticker_sentiment:
                    ticker_sentiment[ticker]['news_count'] += 1
                    sentiment = article.get('sentiment_label', '')
                    if sentiment == 'positive':
                        ticker_sentiment[ticker]['news_positive'] += 1
                    elif sentiment == 'negative':
                        ticker_sentiment[ticker]['news_negative'] += 1
        
        # Count social by ticker
        for post in social.get('reddit', []):
            tickers = post.get('tickers', '[]')
            if isinstance(tickers, str):
                import json
                tickers = json.loads(tickers) if tickers else []
            
            for ticker in tickers:
                if ticker in ticker_sentiment:
                    ticker_sentiment[ticker]['reddit_count'] += 1
        
        for msg in social.get('stocktwits', []):
            tickers = msg.get('tickers', '[]')
            if isinstance(tickers, str):
                import json
                tickers = json.loads(tickers) if tickers else []
            
            user_sentiment = msg.get('user_sentiment', '')
            for ticker in tickers:
                if ticker in ticker_sentiment:
                    ticker_sentiment[ticker]['stocktwits_count'] += 1
                    if user_sentiment == 'Bullish':
                        ticker_sentiment[ticker]['stocktwits_bullish'] += 1
                    elif user_sentiment == 'Bearish':
                        ticker_sentiment[ticker]['stocktwits_bearish'] += 1
        
        return {
            'period_hours': hours,
            'by_ticker': ticker_sentiment,
            'total_news': len(news),
            'total_reddit': len(social.get('reddit', [])),
            'total_stocktwits': len(social.get('stocktwits', [])),
            'fetched_at': datetime.now().isoformat(),
        }


def run_demo():
    """Demo the data handler"""
    handler = HERMESDataHandler()
    
    print("\n=== HERMES_Quantum Data Handler Demo ===\n")
    
    # Fetch stocks with processors
    print("Fetching quantum stocks with processing...")
    df = handler.fetch_stocks(
        period='3mo',
        processors=[
            FillNAProcessor(),
            ReturnProcessor(),
            VolatilityProcessor(window=20),
        ]
    )
    
    print(f"Retrieved {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"\nSample (IONQ):")
    ionq = df[df['ticker'] == 'IONQ'].tail(5)
    print(ionq[['close', 'volume', 'return_1d', 'volatility_20d']].to_string())
    
    # Ticker summary
    print("\n--- Ticker Summary (IONQ) ---")
    summary = handler.get_ticker_summary('IONQ')
    print(f"Latest Price: {summary['latest_price']}")
    print(f"Market Cap: {summary['fundamentals'].get('market_cap', 0):,}")
    print(f"News Articles: {summary['news_count']}")
    print(f"Reddit Posts: {summary['reddit_posts']}")
    print(f"StockTwits Messages: {summary['stocktwits_messages']}")
    
    # Sentiment summary
    print("\n--- Sentiment Summary (24h) ---")
    sentiment = handler.get_sentiment_summary(hours=24)
    print(f"Total News: {sentiment['total_news']}")
    print(f"Total Reddit: {sentiment['total_reddit']}")
    print(f"Total StockTwits: {sentiment['total_stocktwits']}")
    
    for ticker, stats in sentiment['by_ticker'].items():
        print(f"  {ticker}: News={stats['news_count']}, Reddit={stats['reddit_count']}, ST={stats['stocktwits_count']}")


if __name__ == "__main__":
    run_demo()
