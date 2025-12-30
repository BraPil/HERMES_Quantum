"""
HERMES_Quantum - RSS News Aggregator
Agent 91 (Tools) - News Collection Module

Aggregates financial news from free RSS feeds, filters for quantum stock
mentions, and stores in SQLite for Agent 22 (Psychology) sentiment analysis.

Features:
- Multiple RSS sources (Yahoo Finance, Seeking Alpha, MarketWatch, Investing.com)
- Keyword filtering for quantum computing stocks (QBTS, IONQ, RGTI, QUBT)
- SQLite storage with deduplication
- Rate-limit friendly (RSS has no limits)
- Scheduled updates (configurable interval)

Cost: $0/month (100% free RSS feeds)
"""

import feedparser
import sqlite3
import hashlib
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Represents a news article from RSS feed"""
    url: str
    title: str
    summary: str
    source: str
    published: datetime
    tickers: List[str]
    url_hash: str = ""
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if not self.url_hash:
            self.url_hash = hashlib.md5(self.url.encode()).hexdigest()
        if not self.created_at:
            self.created_at = datetime.now()


class NewsAggregator:
    """
    Aggregates news from multiple RSS feeds and filters for quantum stocks.
    
    Usage:
        aggregator = NewsAggregator()
        articles = aggregator.fetch_all_feeds()
        aggregator.store_articles(articles)
        recent = aggregator.get_recent_news(hours=24)
    """
    
    # RSS Feed sources (all FREE, no rate limits)
    RSS_FEEDS = {
        'yahoo_finance': 'https://finance.yahoo.com/rss/',
        'yahoo_tech': 'https://finance.yahoo.com/news/tech/',
        'seeking_alpha': 'https://seekingalpha.com/market_currents.xml',
        'marketwatch': 'https://www.marketwatch.com/rss/topstories',
        'marketwatch_tech': 'https://www.marketwatch.com/rss/technology',
        'investing_news': 'https://www.investing.com/rss/news.rss',
        'investing_stock': 'https://www.investing.com/rss/stock_stock_news.rss',
    }
    
    # Keywords to filter for (quantum computing stocks + related terms)
    QUANTUM_KEYWORDS = [
        # Ticker symbols
        'QBTS', 'IONQ', 'RGTI', 'QUBT',
        '$QBTS', '$IONQ', '$RGTI', '$QUBT',
        
        # Company names
        'D-Wave', 'D-Wave Quantum', 'DWave',
        'IonQ',
        'Rigetti', 'Rigetti Computing',
        'Quantum Computing Inc',
        
        # Industry terms
        'quantum computing',
        'quantum computer',
        'quantum technology',
        'quantum stock',
        'quantum processor',
        'qubit',
        'quantum supremacy',
        'quantum advantage',
    ]
    
    def __init__(self, db_path: str = None):
        """
        Initialize the news aggregator.
        
        Args:
            db_path: Path to SQLite database. Defaults to outputs/data/hermes.db
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'outputs/data/hermes.db')
        self._ensure_db_exists()
        self._init_database()
    
    def _ensure_db_exists(self):
        """Create database directory if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _init_database(self):
        """Initialize SQLite database with news table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE,
                url TEXT,
                title TEXT,
                summary TEXT,
                source TEXT,
                published TIMESTAMP,
                tickers TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_published ON news_articles(published)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON news_articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickers ON news_articles(tickers)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _extract_tickers(self, text: str) -> List[str]:
        """
        Extract ticker symbols from text.
        
        Args:
            text: Article title or summary
            
        Returns:
            List of detected ticker symbols
        """
        tickers = []
        text_upper = text.upper()
        
        # Check for each quantum ticker
        ticker_map = {
            'QBTS': ['QBTS', '$QBTS', 'D-WAVE', 'DWAVE'],
            'IONQ': ['IONQ', '$IONQ'],
            'RGTI': ['RGTI', '$RGTI', 'RIGETTI'],
            'QUBT': ['QUBT', '$QUBT', 'QUANTUM COMPUTING INC'],
        }
        
        for ticker, keywords in ticker_map.items():
            for kw in keywords:
                if kw.upper() in text_upper:
                    if ticker not in tickers:
                        tickers.append(ticker)
                    break
        
        return tickers
    
    def _is_quantum_related(self, title: str, summary: str) -> bool:
        """
        Check if article is related to quantum computing stocks.
        
        Args:
            title: Article title
            summary: Article summary
            
        Returns:
            True if article mentions quantum keywords
        """
        combined = f"{title} {summary}".lower()
        
        for keyword in self.QUANTUM_KEYWORDS:
            if keyword.lower() in combined:
                return True
        
        return False
    
    def fetch_feed(self, source: str, url: str) -> List[NewsArticle]:
        """
        Fetch and parse a single RSS feed.
        
        Args:
            source: Name of the source (e.g., 'yahoo_finance')
            url: RSS feed URL
            
        Returns:
            List of NewsArticle objects
        """
        articles = []
        
        try:
            logger.info(f"Fetching RSS feed: {source}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.warning(f"Feed parse warning for {source}: {feed.bozo_exception}")
            
            for entry in feed.entries:
                title = entry.get('title', '')
                summary = entry.get('summary', entry.get('description', ''))
                
                # Filter for quantum-related articles
                if not self._is_quantum_related(title, summary):
                    continue
                
                # Parse published date
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])
                else:
                    published = datetime.now()
                
                # Extract tickers mentioned
                tickers = self._extract_tickers(f"{title} {summary}")
                
                article = NewsArticle(
                    url=entry.get('link', ''),
                    title=title,
                    summary=summary[:1000],  # Limit summary length
                    source=source,
                    published=published,
                    tickers=tickers,
                )
                
                articles.append(article)
                logger.debug(f"Found quantum article: {title[:50]}...")
            
            logger.info(f"Found {len(articles)} quantum-related articles from {source}")
            
        except Exception as e:
            logger.error(f"Error fetching {source}: {e}")
        
        return articles
    
    def fetch_all_feeds(self) -> List[NewsArticle]:
        """
        Fetch all configured RSS feeds.
        
        Returns:
            List of all NewsArticle objects from all sources
        """
        all_articles = []
        
        for source, url in self.RSS_FEEDS.items():
            articles = self.fetch_feed(source, url)
            all_articles.extend(articles)
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def store_articles(self, articles: List[NewsArticle]) -> int:
        """
        Store articles in SQLite database with deduplication.
        
        Args:
            articles: List of NewsArticle objects
            
        Returns:
            Number of new articles stored
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_count = 0
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO news_articles 
                    (url_hash, url, title, summary, source, published, tickers, sentiment_score, sentiment_label, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.url_hash,
                    article.url,
                    article.title,
                    article.summary,
                    article.source,
                    article.published.isoformat() if article.published else None,
                    json.dumps(article.tickers),
                    article.sentiment_score,
                    article.sentiment_label,
                    article.created_at.isoformat() if article.created_at else None,
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing article: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {new_count} new articles (out of {len(articles)} total)")
        return new_count
    
    def get_recent_news(self, hours: int = 24, ticker: str = None) -> List[Dict]:
        """
        Get recent news articles from database.
        
        Args:
            hours: Number of hours to look back
            ticker: Optional ticker to filter by
            
        Returns:
            List of article dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
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
        
        conn.close()
        
        # Parse tickers JSON
        for article in articles:
            if article.get('tickers'):
                article['tickers'] = json.loads(article['tickers'])
        
        return articles
    
    def get_unanalyzed_articles(self, limit: int = 100) -> List[Dict]:
        """
        Get articles that haven't been analyzed for sentiment yet.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries without sentiment scores
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM news_articles 
            WHERE sentiment_score IS NULL
            ORDER BY published DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        for article in articles:
            if article.get('tickers'):
                article['tickers'] = json.loads(article['tickers'])
        
        return articles
    
    def update_sentiment(self, url_hash: str, score: float, label: str):
        """
        Update sentiment score for an article.
        
        Args:
            url_hash: Article's URL hash
            score: Sentiment score (-1 to 1)
            label: Sentiment label (positive/negative/neutral)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE news_articles 
            SET sentiment_score = ?, sentiment_label = ?
            WHERE url_hash = ?
        ''', (score, label, url_hash))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """
        Get statistics about stored articles.
        
        Returns:
            Dictionary with article counts by source, ticker, etc.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM news_articles')
        total = cursor.fetchone()[0]
        
        # Count by source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM news_articles 
            GROUP BY source 
            ORDER BY count DESC
        ''')
        by_source = dict(cursor.fetchall())
        
        # Count by date (last 7 days)
        cursor.execute('''
            SELECT DATE(published) as date, COUNT(*) as count 
            FROM news_articles 
            WHERE published > datetime('now', '-7 days')
            GROUP BY DATE(published) 
            ORDER BY date DESC
        ''')
        by_date = dict(cursor.fetchall())
        
        # Articles with sentiment
        cursor.execute('SELECT COUNT(*) FROM news_articles WHERE sentiment_score IS NOT NULL')
        analyzed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_articles': total,
            'by_source': by_source,
            'by_date': by_date,
            'analyzed': analyzed,
            'unanalyzed': total - analyzed,
        }


def run_aggregation():
    """
    Run a single aggregation cycle.
    Can be called from scheduler or manually.
    """
    aggregator = NewsAggregator()
    
    # Fetch all feeds
    articles = aggregator.fetch_all_feeds()
    
    # Store with deduplication
    new_count = aggregator.store_articles(articles)
    
    # Print stats
    stats = aggregator.get_stats()
    print(f"\n=== News Aggregation Complete ===")
    print(f"New articles: {new_count}")
    print(f"Total in database: {stats['total_articles']}")
    print(f"Analyzed: {stats['analyzed']}")
    print(f"Pending analysis: {stats['unanalyzed']}")
    print(f"\nBy source: {stats['by_source']}")
    
    return stats


if __name__ == "__main__":
    # Run aggregation when script is executed directly
    run_aggregation()
