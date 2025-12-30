"""
Agent 22: Psychology/Sentiment Analyzer
Uses ProsusAI/finbert for financial news sentiment analysis

Purpose: Analyze sentiment of financial news, earnings reports, and announcements
Output: positive, negative, neutral with confidence scores
"""

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    label: str  # positive, negative, neutral
    score: float  # confidence score
    timestamp: datetime
    source: Optional[str] = None
    ticker: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'label': self.label,
            'score': self.score,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'ticker': self.ticker
        }


class Agent22_SentimentAnalyzer:
    """
    Agent 22: Financial News Sentiment Analyzer
    
    Uses FinBERT (fine-tuned BERT for financial sentiment)
    to analyze sentiment of financial news and reports.
    
    Model: ProsusAI/finbert
    - Trained on financial phrasebank and earnings call transcripts
    - 3-class classification: positive, negative, neutral
    - ~110M parameters
    """
    
    def __init__(
        self,
        model_name: str = "ProsusAI/finbert",
        device: Optional[str] = None,
        batch_size: int = 8
    ):
        """
        Initialize the sentiment analyzer.
        
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
        
        logger.info(f"Initializing Agent 22 on device: {self.device}")
        
        # Load model and tokenizer
        self._load_model()
        
        logger.info("Agent 22 initialized successfully")
    
    def _load_model(self):
        """Load FinBERT model and create pipeline"""
        try:
            logger.info(f"Loading {self.model_name}...")
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Create pipeline for easy inference
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
        source: Optional[str] = None,
        ticker: Optional[str] = None
    ) -> Union[SentimentResult, List[SentimentResult]]:
        """
        Analyze sentiment of one or more texts.
        
        Args:
            text: Single text string or list of texts
            source: Source of the text (e.g., 'MarketWatch', 'Yahoo Finance')
            ticker: Stock ticker associated with the text
            
        Returns:
            SentimentResult or list of SentimentResults
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        # Run inference
        results = self.pipeline(texts)
        
        # Convert to SentimentResult objects
        timestamp = datetime.now()
        sentiment_results = []
        
        for txt, result in zip(texts, results):
            sentiment_results.append(
                SentimentResult(
                    text=txt,
                    label=result['label'],
                    score=result['score'],
                    timestamp=timestamp,
                    source=source,
                    ticker=ticker
                )
            )
        
        return sentiment_results[0] if is_single else sentiment_results
    
    def analyze_batch(
        self,
        texts: List[str],
        sources: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None
    ) -> List[SentimentResult]:
        """
        Analyze sentiment of multiple texts in batches.
        
        Args:
            texts: List of texts to analyze
            sources: Optional list of sources (same length as texts)
            tickers: Optional list of tickers (same length as texts)
            
        Returns:
            List of SentimentResults
        """
        if sources is None:
            sources = [None] * len(texts)
        if tickers is None:
            tickers = [None] * len(texts)
        
        all_results = []
        timestamp = datetime.now()
        
        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_sources = sources[i:i + self.batch_size]
            batch_tickers = tickers[i:i + self.batch_size]
            
            # Run inference
            batch_results = self.pipeline(batch_texts)
            
            # Convert to SentimentResult objects
            for txt, result, src, tick in zip(
                batch_texts, batch_results, batch_sources, batch_tickers
            ):
                all_results.append(
                    SentimentResult(
                        text=txt,
                        label=result['label'],
                        score=result['score'],
                        timestamp=timestamp,
                        source=src,
                        ticker=tick
                    )
                )
        
        return all_results
    
    def get_sentiment_score(self, label: str, confidence: float) -> float:
        """
        Convert sentiment label to numerical score.
        
        Args:
            label: Sentiment label (positive, negative, neutral)
            confidence: Model confidence score
            
        Returns:
            Score in range [-1, 1]
            - Positive: 0 to 1
            - Negative: -1 to 0
            - Neutral: close to 0
        """
        if label.lower() == 'positive':
            return confidence
        elif label.lower() == 'negative':
            return -confidence
        else:  # neutral
            return 0.0
    
    def aggregate_sentiment(
        self,
        results: List[SentimentResult],
        method: str = 'weighted_mean'
    ) -> Dict[str, float]:
        """
        Aggregate multiple sentiment results into overall score.
        
        Args:
            results: List of SentimentResults
            method: Aggregation method ('weighted_mean', 'majority_vote')
            
        Returns:
            Dictionary with aggregated sentiment metrics
        """
        if not results:
            return {
                'overall_score': 0.0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'confidence': 0.0
            }
        
        scores = [
            self.get_sentiment_score(r.label, r.score) for r in results
        ]
        
        # Calculate ratios
        labels = [r.label.lower() for r in results]
        total = len(labels)
        positive_ratio = labels.count('positive') / total
        negative_ratio = labels.count('negative') / total
        neutral_ratio = labels.count('neutral') / total
        
        if method == 'weighted_mean':
            # Weighted by confidence
            overall_score = sum(scores) / len(scores)
            avg_confidence = sum(r.score for r in results) / len(results)
        else:  # majority_vote
            # Use most common label
            from collections import Counter
            most_common = Counter(labels).most_common(1)[0][0]
            overall_score = 1.0 if most_common == 'positive' else -1.0 if most_common == 'negative' else 0.0
            avg_confidence = sum(r.score for r in results if r.label.lower() == most_common) / labels.count(most_common)
        
        return {
            'overall_score': overall_score,
            'positive_ratio': positive_ratio,
            'negative_ratio': negative_ratio,
            'neutral_ratio': neutral_ratio,
            'confidence': avg_confidence,
            'num_samples': len(results)
        }


def main():
    """Test Agent 22 with quantum computing news"""
    
    # Initialize agent
    agent = Agent22_SentimentAnalyzer()
    
    # Test samples
    test_news = [
        ("IONQ announced breakthrough in quantum error correction, stock surges 15%", "IONQ"),
        ("QBTS stock plummets 20% after disappointing earnings report", "QBTS"),
        ("Quantum Computing Inc to present at industry conference next week", "QUBT"),
        ("D-Wave Quantum secures major contract with government agency", "QTEM"),
        ("Rigetti reports mixed quarterly results, shares flat", "RGTI")
    ]
    
    print("\n" + "="*70)
    print("Agent 22: Sentiment Analysis Test")
    print("="*70 + "\n")
    
    all_results = []
    for text, ticker in test_news:
        result = agent.analyze(text, source="Test", ticker=ticker)
        all_results.append(result)
        
        emoji = "✅" if result.label == "positive" else "❌" if result.label == "negative" else "⚪"
        print(f"{emoji} [{result.label:8s}] ({result.score:.3f}) | ${ticker} | {text[:50]}...")
    
    # Aggregate sentiment
    print("\n" + "-"*70)
    print("Aggregated Sentiment Metrics:")
    print("-"*70)
    
    agg = agent.aggregate_sentiment(all_results)
    print(f"Overall Score: {agg['overall_score']:+.3f} (range: -1 to +1)")
    print(f"Positive Ratio: {agg['positive_ratio']:.1%}")
    print(f"Negative Ratio: {agg['negative_ratio']:.1%}")
    print(f"Neutral Ratio: {agg['neutral_ratio']:.1%}")
    print(f"Average Confidence: {agg['confidence']:.3f}")
    print(f"Number of Samples: {agg['num_samples']}")
    
    print("\n" + "="*70)
    print("✅ Agent 22 test complete!")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
