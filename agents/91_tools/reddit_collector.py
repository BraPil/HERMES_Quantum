"""
HERMES_Quantum - Reddit Social Sentiment Collector
Agent 91 (Tools) - Social Data Collection Module

Collects Reddit posts and comments about quantum computing stocks
using PRAW library with built-in rate limiting to prevent bans.

Features:
- PRAW library with automatic rate limiting (60 req/min)
- Multiple subreddit monitoring (wsb, stocks, investing, QuantumComputing)
- Keyword search for quantum tickers (QBTS, IONQ, RGTI, QUBT)
- SQLite storage for Agent 23 (Social) sentiment analysis
- No ban risk with proper implementation

Cost: $0/month (Reddit API is free)
Rate Limit: 60 requests/minute (PRAW handles automatically)

Setup:
1. Register app at https://www.reddit.com/prefs/apps (choose "script")
2. Add credentials to .env file
"""

import praw
import sqlite3
import hashlib
import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Represents a Reddit post or comment"""
    post_id: str
    subreddit: str
    title: str
    text: str
    author: str
    score: int
    num_comments: int
    url: str
    created_utc: datetime
    tickers: List[str]
    post_type: str  # 'submission' or 'comment'
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class RedditCollector:
    """
    Collects Reddit posts about quantum computing stocks.
    Uses PRAW with built-in rate limiting to prevent bans.
    
    Usage:
        collector = RedditCollector()
        posts = collector.fetch_quantum_mentions()
        collector.store_posts(posts)
    """
    
    # Subreddits to monitor (ordered by relevance)
    SUBREDDITS = [
        'wallstreetbets',      # 15M+ members, high volume
        'stocks',              # 6M+ members, quality discussions
        'investing',           # 2.5M+ members, long-term views
        'QuantumComputing',    # 50K+ members, industry insights
        'options',             # Options trading
        'stockmarket',         # General stock market
        'pennystocks',         # Speculative plays
    ]
    
    # Quantum stock tickers and search terms
    SEARCH_TERMS = {
        'QBTS': ['QBTS', '$QBTS', 'D-Wave', 'DWave'],
        'IONQ': ['IONQ', '$IONQ', 'IonQ'],
        'RGTI': ['RGTI', '$RGTI', 'Rigetti'],
        'QUBT': ['QUBT', '$QUBT', 'Quantum Computing Inc'],
    }
    
    def __init__(self, db_path: str = None):
        """
        Initialize Reddit collector with PRAW.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path or os.getenv('DATABASE_PATH', 'outputs/data/hermes.db')
        self.reddit = self._init_reddit()
        self._init_database()
    
    def _init_reddit(self) -> Optional[praw.Reddit]:
        """
        Initialize PRAW Reddit instance with credentials.
        
        Returns:
            praw.Reddit instance or None if credentials missing
        """
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        user_agent = os.getenv('REDDIT_USER_AGENT', 'HERMES_Quantum/1.0')
        
        if not client_id or not client_secret or client_id == 'your_client_id_here':
            logger.warning("Reddit API credentials not configured. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
            return None
        
        try:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent,
            )
            # Test connection
            reddit.user.me()  # Will be None for script apps but tests auth
            logger.info("Reddit PRAW initialized successfully")
            return reddit
        except Exception as e:
            logger.error(f"Failed to initialize Reddit: {e}")
            return None
    
    def _init_database(self):
        """Initialize SQLite database with reddit_posts table"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reddit_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT UNIQUE,
                subreddit TEXT,
                title TEXT,
                text TEXT,
                author TEXT,
                score INTEGER,
                num_comments INTEGER,
                url TEXT,
                created_utc TIMESTAMP,
                tickers TEXT,
                post_type TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reddit_created ON reddit_posts(created_utc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reddit_subreddit ON reddit_posts(subreddit)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_reddit_tickers ON reddit_posts(tickers)')
        
        conn.commit()
        conn.close()
        logger.info("Reddit database table initialized")
    
    def _extract_tickers(self, text: str) -> List[str]:
        """Extract quantum stock tickers from text"""
        tickers = []
        text_upper = text.upper() if text else ''
        
        for ticker, keywords in self.SEARCH_TERMS.items():
            for kw in keywords:
                if kw.upper() in text_upper:
                    if ticker not in tickers:
                        tickers.append(ticker)
                    break
        
        return tickers
    
    def fetch_subreddit_mentions(
        self, 
        subreddit_name: str, 
        search_term: str,
        limit: int = 50,
        time_filter: str = 'week'
    ) -> List[RedditPost]:
        """
        Fetch posts mentioning a search term from a subreddit.
        PRAW handles rate limiting automatically - no manual delays needed.
        
        Args:
            subreddit_name: Subreddit to search
            search_term: Term to search for
            limit: Maximum posts to fetch
            time_filter: Time filter (hour, day, week, month, year, all)
            
        Returns:
            List of RedditPost objects
        """
        if not self.reddit:
            logger.warning("Reddit not initialized, skipping")
            return []
        
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search posts - PRAW handles rate limiting automatically
            for submission in subreddit.search(
                search_term, 
                limit=limit, 
                time_filter=time_filter,
                sort='new'
            ):
                tickers = self._extract_tickers(f"{submission.title} {submission.selftext}")
                
                post = RedditPost(
                    post_id=submission.id,
                    subreddit=subreddit_name,
                    title=submission.title,
                    text=submission.selftext[:2000] if submission.selftext else '',
                    author=str(submission.author) if submission.author else '[deleted]',
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=f"https://reddit.com{submission.permalink}",
                    created_utc=datetime.fromtimestamp(submission.created_utc),
                    tickers=tickers,
                    post_type='submission',
                )
                
                posts.append(post)
            
            logger.info(f"Fetched {len(posts)} posts for '{search_term}' from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error fetching from r/{subreddit_name}: {e}")
        
        return posts
    
    def fetch_quantum_mentions(
        self, 
        subreddits: List[str] = None,
        limit_per_sub: int = 25,
        time_filter: str = 'week'
    ) -> List[RedditPost]:
        """
        Fetch all quantum stock mentions across multiple subreddits.
        
        Args:
            subreddits: List of subreddits to search (defaults to all)
            limit_per_sub: Limit per subreddit per search term
            time_filter: Time filter for search
            
        Returns:
            List of all RedditPost objects
        """
        if not self.reddit:
            logger.error("Reddit not initialized. Configure credentials in .env")
            return []
        
        subreddits = subreddits or self.SUBREDDITS
        all_posts = []
        seen_ids = set()  # Deduplicate
        
        for subreddit_name in subreddits:
            for ticker, search_terms in self.SEARCH_TERMS.items():
                # Use first search term for each ticker
                search_term = search_terms[0]
                
                posts = self.fetch_subreddit_mentions(
                    subreddit_name=subreddit_name,
                    search_term=search_term,
                    limit=limit_per_sub,
                    time_filter=time_filter,
                )
                
                for post in posts:
                    if post.post_id not in seen_ids:
                        seen_ids.add(post.post_id)
                        all_posts.append(post)
        
        logger.info(f"Total unique posts collected: {len(all_posts)}")
        return all_posts
    
    def fetch_hot_posts(self, subreddit_name: str, limit: int = 25) -> List[RedditPost]:
        """
        Fetch hot posts from a subreddit and filter for quantum mentions.
        Good for catching trending discussions.
        
        Args:
            subreddit_name: Subreddit to fetch from
            limit: Maximum posts to check
            
        Returns:
            List of RedditPost objects with quantum mentions
        """
        if not self.reddit:
            return []
        
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            for submission in subreddit.hot(limit=limit):
                combined_text = f"{submission.title} {submission.selftext}"
                tickers = self._extract_tickers(combined_text)
                
                # Only include if it mentions quantum stocks
                if not tickers:
                    continue
                
                post = RedditPost(
                    post_id=submission.id,
                    subreddit=subreddit_name,
                    title=submission.title,
                    text=submission.selftext[:2000] if submission.selftext else '',
                    author=str(submission.author) if submission.author else '[deleted]',
                    score=submission.score,
                    num_comments=submission.num_comments,
                    url=f"https://reddit.com{submission.permalink}",
                    created_utc=datetime.fromtimestamp(submission.created_utc),
                    tickers=tickers,
                    post_type='submission',
                )
                
                posts.append(post)
            
            logger.info(f"Found {len(posts)} quantum-related hot posts from r/{subreddit_name}")
            
        except Exception as e:
            logger.error(f"Error fetching hot posts from r/{subreddit_name}: {e}")
        
        return posts
    
    def store_posts(self, posts: List[RedditPost]) -> int:
        """
        Store posts in SQLite with deduplication.
        
        Args:
            posts: List of RedditPost objects
            
        Returns:
            Number of new posts stored
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_count = 0
        
        for post in posts:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO reddit_posts 
                    (post_id, subreddit, title, text, author, score, num_comments, 
                     url, created_utc, tickers, post_type, sentiment_score, sentiment_label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.post_id,
                    post.subreddit,
                    post.title,
                    post.text,
                    post.author,
                    post.score,
                    post.num_comments,
                    post.url,
                    post.created_utc.isoformat(),
                    json.dumps(post.tickers),
                    post.post_type,
                    post.sentiment_score,
                    post.sentiment_label,
                ))
                
                if cursor.rowcount > 0:
                    new_count += 1
                    
            except Exception as e:
                logger.error(f"Error storing post {post.post_id}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {new_count} new posts (out of {len(posts)} total)")
        return new_count
    
    def get_recent_posts(self, hours: int = 24, ticker: str = None) -> List[Dict]:
        """
        Get recent posts from database.
        
        Args:
            hours: Hours to look back
            ticker: Optional ticker filter
            
        Returns:
            List of post dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
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
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        for post in posts:
            if post.get('tickers'):
                post['tickers'] = json.loads(post['tickers'])
        
        return posts
    
    def get_unanalyzed_posts(self, limit: int = 100) -> List[Dict]:
        """Get posts without sentiment analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reddit_posts 
            WHERE sentiment_score IS NULL
            ORDER BY created_utc DESC
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        posts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        for post in posts:
            if post.get('tickers'):
                post['tickers'] = json.loads(post['tickers'])
        
        return posts
    
    def update_sentiment(self, post_id: str, score: float, label: str):
        """Update sentiment for a post"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE reddit_posts 
            SET sentiment_score = ?, sentiment_label = ?
            WHERE post_id = ?
        ''', (score, label, post_id))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM reddit_posts')
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT subreddit, COUNT(*) as count 
            FROM reddit_posts 
            GROUP BY subreddit 
            ORDER BY count DESC
        ''')
        by_subreddit = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM reddit_posts WHERE sentiment_score IS NOT NULL')
        analyzed = cursor.fetchone()[0]
        
        # Average score
        cursor.execute('SELECT AVG(score) FROM reddit_posts')
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_posts': total,
            'by_subreddit': by_subreddit,
            'analyzed': analyzed,
            'unanalyzed': total - analyzed,
            'avg_score': round(avg_score, 1),
        }


def run_collection():
    """Run a single collection cycle"""
    collector = RedditCollector()
    
    if not collector.reddit:
        print("\n⚠️  Reddit not configured!")
        print("1. Register app at https://www.reddit.com/prefs/apps")
        print("2. Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env")
        return None
    
    # Fetch all quantum mentions
    posts = collector.fetch_quantum_mentions(
        limit_per_sub=25,
        time_filter='week'
    )
    
    # Store posts
    new_count = collector.store_posts(posts)
    
    # Print stats
    stats = collector.get_stats()
    print(f"\n=== Reddit Collection Complete ===")
    print(f"New posts: {new_count}")
    print(f"Total in database: {stats['total_posts']}")
    print(f"Analyzed: {stats['analyzed']}")
    print(f"Pending analysis: {stats['unanalyzed']}")
    print(f"Average score: {stats['avg_score']}")
    print(f"\nBy subreddit: {stats['by_subreddit']}")
    
    return stats


if __name__ == "__main__":
    run_collection()
