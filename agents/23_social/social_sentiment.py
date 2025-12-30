"""
Agent 23: Social Sentiment Analyzer
Uses FinTwitBERT for social media sentiment analysis

Purpose: Analyze sentiment of social media posts (Twitter/X, StockTwits, Reddit)
Output: BULLISH, BEARISH, or NEUTRAL/MIXED
"""

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SocialSentimentResult:
    """Social sentiment analysis result"""
    text: str
    label: str  # BULLISH, BEARISH, NEUTRAL
    score: float  # confidence score
    timestamp: datetime
    platform: Optional[str] = None  # Twitter, StockTwits, Reddit
    ticker: Optional[str] = None
    author: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'label': self.label,
            'score': self.score,
            'timestamp': self.timestamp.isoformat(),
            'platform': self.platform,
            'ticker': self.ticker,
            'author': self.author
        }
    
    @property
    def is_bullish(self) -> bool:
        return 'bull' in self.label.lower() or 'positive' in self.label.lower()
    
    @property
    def is_bearish(self) -> bool:
        return 'bear' in self.label.lower() or 'negative' in self.label.lower()


class Agent23_SocialSentimentAnalyzer:
    """
    Agent 23: Social Media Sentiment Analyzer
    
    Uses FinTwitBERT (fine-tuned for financial social media)
    to analyze sentiment of Twitter/X, StockTwits, Reddit posts.
    
    Model: StephanAkkerman/FinTwitBERT-sentiment
    - Trained on financial tweets and social media posts
    - Handles emojis, hashtags, cashtags ($IONQ)
    - Output: BULLISH, BEARISH, or NEUTRAL
    """
    
    def __init__(
        self,
        model_name: str = "StephanAkkerman/FinTwitBERT-sentiment",
        device: Optional[str] = None,
        batch_size: int = 16
    ):
        """
        Initialize the social sentiment analyzer.
        
        Args:
            model_name: HuggingFace model name
            device: 'cuda', 'cpu', or None (auto-detect)
            batch_size: Number of texts to process at once
        """
        self.model_name = model_name
        self.batch_size = batch_size
        
        # Auto-detect device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Initializing Agent 23 on device: {self.device}")
        
        # Load model
        self._load_model()
        
        logger.info("Agent 23 initialized successfully")
    
    def _load_model(self):
        """Load FinTwitBERT model and create pipeline"""
        try:
            logger.info(f"Loading {self.model_name}...")
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Create pipeline
            device_id = 0 if self.device == 'cuda' else -1
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device_id
            )
            
            logger.info(f"✅ {self.model_name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def analyze(
        self,
        text: Union[str, List[str]],
        platform: Optional[str] = None,
        ticker: Optional[str] = None,
        author: Optional[str] = None
    ) -> Union[SocialSentimentResult, List[SocialSentimentResult]]:
        """
        Analyze sentiment of one or more social media posts.
        
        Args:
            text: Single text string or list of texts
            platform: Platform name (Twitter, StockTwits, Reddit)
            ticker: Stock ticker mentioned
            author: Post author username
            
        Returns:
            SocialSentimentResult or list of SocialSentimentResults
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        # Run inference
        results = self.pipeline(texts)
        
        # Convert to SocialSentimentResult objects
        timestamp = datetime.now()
        sentiment_results = []
        
        for txt, result in zip(texts, results):
            sentiment_results.append(
                SocialSentimentResult(
                    text=txt,
                    label=result['label'],
                    score=result['score'],
                    timestamp=timestamp,
                    platform=platform,
                    ticker=ticker,
                    author=author
                )
            )
        
        return sentiment_results[0] if is_single else sentiment_results
    
    def analyze_batch(
        self,
        texts: List[str],
        platforms: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        authors: Optional[List[str]] = None
    ) -> List[SocialSentimentResult]:
        """
        Analyze sentiment of multiple social posts in batches.
        
        Args:
            texts: List of texts to analyze
            platforms: Optional list of platforms
            tickers: Optional list of tickers
            authors: Optional list of authors
            
        Returns:
            List of SocialSentimentResults
        """
        if platforms is None:
            platforms = [None] * len(texts)
        if tickers is None:
            tickers = [None] * len(texts)
        if authors is None:
            authors = [None] * len(texts)
        
        all_results = []
        timestamp = datetime.now()
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_platforms = platforms[i:i + self.batch_size]
            batch_tickers = tickers[i:i + self.batch_size]
            batch_authors = authors[i:i + self.batch_size]
            
            # Run inference
            batch_results = self.pipeline(batch_texts)
            
            # Convert to SocialSentimentResult objects
            for txt, result, plat, tick, auth in zip(
                batch_texts, batch_results, batch_platforms, batch_tickers, batch_authors
            ):
                all_results.append(
                    SocialSentimentResult(
                        text=txt,
                        label=result['label'],
                        score=result['score'],
                        timestamp=timestamp,
                        platform=plat,
                        ticker=tick,
                        author=auth
                    )
                )
        
        return all_results
    
    def get_sentiment_score(self, result: SocialSentimentResult) -> float:
        """
        Convert sentiment to numerical score.
        
        Args:
            result: SocialSentimentResult object
            
        Returns:
            Score in range [-1, 1]
            - Bullish: 0 to 1
            - Bearish: -1 to 0
            - Neutral: close to 0
        """
        if result.is_bullish:
            return result.score
        elif result.is_bearish:
            return -result.score
        else:  # neutral
            return 0.0
    
    def aggregate_by_ticker(
        self,
        results: List[SocialSentimentResult]
    ) -> Dict[str, Dict]:
        """
        Aggregate sentiment results by ticker.
        
        Args:
            results: List of SocialSentimentResults
            
        Returns:
            Dictionary mapping tickers to aggregated sentiment
        """
        ticker_groups = {}
        
        for result in results:
            ticker = result.ticker or 'UNKNOWN'
            if ticker not in ticker_groups:
                ticker_groups[ticker] = []
            ticker_groups[ticker].append(result)
        
        # Aggregate each ticker
        aggregated = {}
        for ticker, ticker_results in ticker_groups.items():
            scores = [self.get_sentiment_score(r) for r in ticker_results]
            labels = [r.label.upper() for r in ticker_results]
            
            total = len(labels)
            bullish_count = sum(1 for r in ticker_results if r.is_bullish)
            bearish_count = sum(1 for r in ticker_results if r.is_bearish)
            neutral_count = total - bullish_count - bearish_count
            
            aggregated[ticker] = {
                'overall_score': sum(scores) / len(scores) if scores else 0.0,
                'bullish_ratio': bullish_count / total,
                'bearish_ratio': bearish_count / total,
                'neutral_ratio': neutral_count / total,
                'avg_confidence': sum(r.score for r in ticker_results) / total,
                'num_posts': total,
                'platforms': list(set(r.platform for r in ticker_results if r.platform))
            }
        
        return aggregated
    
    def get_trending_sentiment(
        self,
        results: List[SocialSentimentResult],
        min_posts: int = 5
    ) -> List[Dict]:
        """
        Identify tickers with strong trending sentiment.
        
        Args:
            results: List of SocialSentimentResults
            min_posts: Minimum posts required to be considered trending
            
        Returns:
            List of trending tickers with sentiment data
        """
        ticker_agg = self.aggregate_by_ticker(results)
        
        trending = []
        for ticker, metrics in ticker_agg.items():
            if metrics['num_posts'] >= min_posts:
                # Calculate trend strength
                trend_strength = abs(metrics['overall_score']) * metrics['avg_confidence']
                
                trending.append({
                    'ticker': ticker,
                    'trend_strength': trend_strength,
                    'sentiment': 'BULLISH' if metrics['overall_score'] > 0 else 'BEARISH',
                    **metrics
                })
        
        # Sort by trend strength
        trending.sort(key=lambda x: x['trend_strength'], reverse=True)
        
        return trending


def main():
    """Test Agent 23 with social media posts"""
    
    # Initialize agent
    agent = Agent23_SocialSentimentAnalyzer()
    
    # Test samples (social media style)
    test_posts = [
        ("$IONQ to the moon! 🚀 Quantum computing is the future", "StockTwits", "IONQ"),
        ("$QBTS looking weak, might dump my shares before it crashes", "StockTwits", "QBTS"),
        ("Just loaded up on $RGTI calls, earnings gonna be 🔥", "Reddit", "RGTI"),
        ("$QUBT partnership announcement coming soon 👀", "Twitter", "QUBT"),
        ("Quantum stocks are overvalued, bubble gonna pop", "Reddit", "GENERAL"),
        ("D-Wave $QTEM is criminally undervalued right now", "StockTwits", "QTEM"),
        ("$IONQ new contracts keep coming, bullish af", "Twitter", "IONQ"),
        ("Sold all my $QBTS, too much volatility", "Reddit", "QBTS")
    ]
    
    print("\n" + "="*70)
    print("Agent 23: Social Sentiment Analysis Test")
    print("="*70 + "\n")
    
    all_results = []
    for text, platform, ticker in test_posts:
        result = agent.analyze(text, platform=platform, ticker=ticker)
        all_results.append(result)
        
        emoji = "📈" if result.is_bullish else "📉" if result.is_bearish else "➡️"
        print(f"{emoji} [{result.label:8s}] ({result.score:.3f}) | ${ticker:4s} | {platform:12s} | {text[:40]}...")
    
    # Aggregate by ticker
    print("\n" + "-"*70)
    print("Aggregated Sentiment by Ticker:")
    print("-"*70)
    
    ticker_sentiment = agent.aggregate_by_ticker(all_results)
    for ticker, metrics in sorted(ticker_sentiment.items()):
        if ticker != 'GENERAL':
            overall = "BULLISH 📈" if metrics['overall_score'] > 0 else "BEARISH 📉" if metrics['overall_score'] < 0 else "NEUTRAL ➡️"
            print(f"${ticker:4s} | {overall} | Score: {metrics['overall_score']:+.3f} | Posts: {metrics['num_posts']} | Confidence: {metrics['avg_confidence']:.3f}")
    
    # Trending sentiment
    print("\n" + "-"*70)
    print("Trending Tickers (by sentiment strength):")
    print("-"*70)
    
    trending = agent.get_trending_sentiment(all_results, min_posts=2)
    for i, trend in enumerate(trending[:5], 1):
        if trend['ticker'] != 'GENERAL':
            print(f"{i}. ${trend['ticker']} - {trend['sentiment']} (strength: {trend['trend_strength']:.3f}, posts: {trend['num_posts']})")
    
    print("\n" + "="*70)
    print("✅ Agent 23 test complete!")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
