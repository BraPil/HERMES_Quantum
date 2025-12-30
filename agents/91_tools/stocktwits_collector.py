"""
HERMES_Quantum - StockTwits Social Sentiment Collector
Agent 91 (Tools) - Social Data Collection Module

Collects StockTwits messages about quantum computing stocks.
StockTwits is a financial-focused social network (NOT part of Reddit).

Features:
- Free API (400 requests/hour with authentication)
- Financial-focused users (investors, traders)
- Pre-labeled sentiment on some messages
- Ticker streams for QBTS, IONQ, RGTI, QUBT
- SQLite storage for Agent 23 sentiment analysis

Cost: $0/month (StockTwits API is free)
Rate Limit: 400 requests/hour = 1 request every 9 seconds

Setup:
1. Register app at https://stocktwits.com/developers/apps/new
2. Add STOCKTWITS_ACCESS_TOKEN to .env
"""

import requests
import sqlite3
import logging
import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class StockTwitsMessage:
    """Represents a StockTwits message"""
    message_id: int
    body: str
    created_at: datetime
    username: str
    user_followers: int
    tickers: List[str]
    user_sentiment: Optional[str]  # StockTwits user-selected sentiment
    sentiment_score: Optional[float] = None  # Our model's sentiment
    sentiment_label: Optional[str] = None


class StockTwitsCollector:
    """
    Collects StockTwits messages about quantum computing stocks.
    
    StockTwits is NOT part of Reddit - it's a separate financial social network
    with 6+ million users focused on stocks and trading.
    
    Usage:
        collector = StockTwitsCollector()
        messages = collector.fetch_all_quantum_messages()
        collector.store_messages(messages)
    """
    
    BASE_URL = 'https://api.stocktwits.com/api/2'
    
    # Our quantum stock tickers
    QUANTUM_TICKERS = ['QBTS', 'IONQ', 'RGTI', 'QUBT']
    
    # Rate limiting: 400 requests/hour = 1 every 9 seconds
    REQUEST_DELAY = 9.0
    
    def __init__(self, db_path: str = None):
        """
        Initialize StockTwits collector.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'outputs/data/hermes.db')
        self.access_token = os.getenv('STOCKTWITS_ACCESS_TOKEN')
        self._last_request_time = 0
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with stocktwits table"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocktwits_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE,
                body TEXT,
                created_at TIMESTAMP,
                username TEXT,
                user_followers INTEGER,
                tickers TEXT,
                user_sentiment TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_st_created ON stocktwits_messages(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_st_tickers ON stocktwits_messages(tickers)')
        
        conn.commit()
        conn.close()
        logger.info("StockTwits database table initialized")
    
    def _rate_limit(self):
        """
        Enforce rate limiting: 400 requests/hour = 1 every 9 seconds.
        Call this before each API request.
        """
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            wait_time = self.REQUEST_DELAY - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make an API request with rate limiting.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters
            
        Returns:
            JSON response or None on error
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {}
        
        if self.access_token and self.access_token != 'your_access_token_here':
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited by StockTwits. Waiting 60 seconds...")
                time.sleep(60)
                return None
            else:
                logger.error(f"StockTwits API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    def fetch_ticker_stream(self, ticker: str, limit: int = 30) -> List[StockTwitsMessage]:
        """
        Fetch recent messages for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'IONQ')
            limit: Maximum messages to fetch (max 30 per request)
            
        Returns:
            List of StockTwitsMessage objects
        """
        messages = []
        
        data = self._make_request(f'streams/symbol/{ticker}.json', {'limit': min(limit, 30)})
        
        if not data or 'messages' not in data:
            logger.warning(f"No messages returned for {ticker}")
            return messages
        
        for msg in data['messages']:
            try:
                # Extract user sentiment if available
                user_sentiment = None
                if msg.get('entities') and msg['entities'].get('sentiment'):
                    user_sentiment = msg['entities']['sentiment'].get('basic')
                
                # Extract mentioned tickers
                tickers = [ticker]  # At minimum, includes the searched ticker
                if msg.get('symbols'):
                    for sym in msg['symbols']:
                        if sym.get('symbol') and sym['symbol'] not in tickers:
                            tickers.append(sym['symbol'])
                
                message = StockTwitsMessage(
                    message_id=msg['id'],
                    body=msg.get('body', ''),
                    created_at=datetime.strptime(
                        msg['created_at'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    ),
                    username=msg.get('user', {}).get('username', 'unknown'),
                    user_followers=msg.get('user', {}).get('followers', 0),
                    tickers=tickers,
                    user_sentiment=user_sentiment,
                )
                
                messages.append(message)
                
            except Exception as e:
                logger.error(f"Error parsing message: {e}")
                continue
        
        logger.info(f"Fetched {len(messages)} messages for ${ticker}")
        return messages
    
    def fetch_all_quantum_messages(self, limit_per_ticker: int = 30) -> List[StockTwitsMessage]:
        """
        Fetch messages for all quantum stock tickers.
        
        Args:
            limit_per_ticker: Messages per ticker (max 30)
            
        Returns:
            List of all StockTwitsMessage objects
        """
        all_messages = []
        seen_ids = set()
        
        for ticker in self.QUANTUM_TICKERS:
            messages = self.fetch_ticker_stream(ticker, limit_per_ticker)
            
            for msg in messages:
                if msg.message_id not in seen_ids:
                    seen_ids.add(msg.message_id)
                    all_messages.append(msg)
        
        logger.info(f"Total unique messages collected: {len(all_messages)}")
        return all_messages
    
    def fetch_trending(self) -> List[Dict]:
        """
        Fetch trending symbols on StockTwits.
        Check if any quantum stocks are trending.
        
        Returns:
            List of trending symbols
        """
        data = self._make_request('trending/symbols.json')
        
        if not data or 'symbols' not in data:
            return []
        
        trending = data['symbols']
        
        # Check if any quantum stocks are trending
        quantum_trending = [
            sym for sym in trending 
            if sym.get('symbol') in self.QUANTUM_TICKERS
        ]
        
        if quantum_trending:
            logger.info(f"Quantum stocks trending: {[s['symbol'] for s in quantum_trending]}")
        
        return trending
    
    def store_messages(self, messages: List[StockTwitsMessage]) -> int:
        """
        Store messages in SQLite with deduplication.
        
        Args:
            messages: List of StockTwitsMessage objects
            
        Returns:
            Number of new messages stored
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_count = 0
        
        for msg in messages:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO stocktwits_messages 
                    (message_id, body, created_at, username, user_followers, 
                     tickers, user_sentiment, sentiment_score, sentiment_label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    msg.message_id,
                    msg.body,
                    msg.created_at.isoformat(),
                    msg.username,
                    msg.user_followers,
                    json.dumps(msg.tickers),
                    msg.user_sentiment,
                    msg.sentiment_score,
                    msg.sentiment_label,
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing message {msg.message_id}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {new_count} new messages (out of {len(messages)} total)")
        return new_count
    
    def get_recent_messages(self, hours: int = 24, ticker: str = None) -> List[Dict]:
        """
        Get recent messages from database.
        
        Args:
            hours: Hours to look back
            ticker: Optional ticker filter
            
        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
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
        messages = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        for msg in messages:
            if msg.get('tickers'):
                msg['tickers'] = json.loads(msg['tickers'])
        
        return messages
    
    def get_unanalyzed_messages(self, limit: int = 100) -> List[Dict]:
        """Get messages without sentiment analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM stocktwits_messages 
            WHERE sentiment_score IS NULL
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        messages = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        for msg in messages:
            if msg.get('tickers'):
                msg['tickers'] = json.loads(msg['tickers'])
        
        return messages
    
    def update_sentiment(self, message_id: int, score: float, label: str):
        """Update sentiment for a message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE stocktwits_messages 
            SET sentiment_score = ?, sentiment_label = ?
            WHERE message_id = ?
        ''', (score, label, message_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM stocktwits_messages')
        total = cursor.fetchone()[0]
        
        # User sentiment distribution
        cursor.execute('''
            SELECT user_sentiment, COUNT(*) as count 
            FROM stocktwits_messages 
            WHERE user_sentiment IS NOT NULL
            GROUP BY user_sentiment
        ''')
        user_sentiment_dist = dict(cursor.fetchall())
        
        # Messages by ticker
        cursor.execute('SELECT tickers FROM stocktwits_messages')
        ticker_counts = {}
        for row in cursor.fetchall():
            if row[0]:
                for ticker in json.loads(row[0]):
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
        
        cursor.execute('SELECT COUNT(*) FROM stocktwits_messages WHERE sentiment_score IS NOT NULL')
        analyzed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_messages': total,
            'by_ticker': ticker_counts,
            'user_sentiment': user_sentiment_dist,
            'analyzed': analyzed,
            'unanalyzed': total - analyzed,
        }


def run_collection():
    """Run a single collection cycle"""
    collector = StockTwitsCollector()
    
    # Fetch all quantum stock messages
    print("\nFetching StockTwits messages for quantum stocks...")
    print("Rate limiting: 1 request every 9 seconds (4 tickers = ~36 seconds)")
    
    messages = collector.fetch_all_quantum_messages(limit_per_ticker=30)
    
    # Store messages
    new_count = collector.store_messages(messages)
    
    # Check trending
    print("\nChecking trending symbols...")
    trending = collector.fetch_trending()
    quantum_trending = [t for t in trending if t.get('symbol') in collector.QUANTUM_TICKERS]
    
    # Print stats
    stats = collector.get_stats()
    print(f"\n=== StockTwits Collection Complete ===")
    print(f"New messages: {new_count}")
    print(f"Total in database: {stats['total_messages']}")
    print(f"Analyzed: {stats['analyzed']}")
    print(f"Pending analysis: {stats['unanalyzed']}")
    print(f"\nBy ticker: {stats['by_ticker']}")
    print(f"User sentiment: {stats['user_sentiment']}")
    
    if quantum_trending:
        print(f"\n🔥 Quantum stocks trending: {[t['symbol'] for t in quantum_trending]}")
    
    return stats


if __name__ == "__main__":
    run_collection()
