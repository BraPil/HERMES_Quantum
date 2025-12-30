"""
Agent 24: Policy/Politics Classifier
Uses facebook/bart-large-mnli for zero-shot classification

Purpose: Classify news into policy/political categories (Fed policy, government contracts, regulations, geopolitical events)
Output: Category classification with confidence scores
"""

import torch
from transformers import pipeline
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PolicyClassificationResult:
    """Policy classification result"""
    text: str
    labels: List[str]  # Ordered by confidence
    scores: List[float]  # Confidence scores for each label
    top_label: str
    top_score: float
    timestamp: datetime
    source: Optional[str] = None
    ticker: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'labels': self.labels,
            'scores': self.scores,
            'top_label': self.top_label,
            'top_score': self.top_score,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'ticker': self.ticker
        }


class Agent24_PolicyClassifier:
    """
    Agent 24: Policy and Political Event Classifier
    
    Uses BART-MNLI for zero-shot classification of financial news
    into policy-relevant categories.
    
    Model: facebook/bart-large-mnli
    - Zero-shot classification (no fine-tuning needed)
    - Can classify into any custom categories
    - ~400M parameters
    
    Default Categories:
    - Federal Reserve policy (interest rates, monetary policy)
    - Government contract (defense, research funding)
    - Technology regulation (export controls, antitrust)
    - Geopolitical tension (US-China, international trade)
    - Earnings report (quarterly results, guidance)
    - Industry partnership (collaborations, acquisitions)
    - Market sentiment (general market conditions)
    """
    
    # Default policy categories for quantum computing / tech stocks
    DEFAULT_CATEGORIES = [
        "Federal Reserve policy",
        "government contract",
        "technology regulation",
        "geopolitical tension",
        "earnings report",
        "industry partnership",
        "market sentiment",
        "funding announcement",
        "executive change",
        "product launch"
    ]
    
    def __init__(
        self,
        model_name: str = "facebook/bart-large-mnli",
        device: Optional[str] = None,
        categories: Optional[List[str]] = None
    ):
        """
        Initialize the policy classifier.
        
        Args:
            model_name: HuggingFace model name
            device: 'cuda', 'cpu', or None (auto-detect)
            categories: Custom categories (uses DEFAULT_CATEGORIES if None)
        """
        self.model_name = model_name
        self.categories = categories or self.DEFAULT_CATEGORIES
        
        # Auto-detect device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Initializing Agent 24 on device: {self.device}")
        logger.info(f"Categories: {self.categories}")
        
        # Load model
        self._load_model()
        
        logger.info("Agent 24 initialized successfully")
    
    def _load_model(self):
        """Load BART-MNLI model and create pipeline"""
        try:
            logger.info(f"Loading {self.model_name}...")
            
            device_id = 0 if self.device == 'cuda' else -1
            self.pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=device_id
            )
            
            logger.info(f"✅ {self.model_name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def classify(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        source: Optional[str] = None,
        ticker: Optional[str] = None,
        multi_label: bool = False
    ) -> PolicyClassificationResult:
        """
        Classify a text into policy categories.
        
        Args:
            text: Text to classify
            categories: Custom categories (uses default if None)
            source: Source of the text
            ticker: Associated stock ticker
            multi_label: Whether to allow multiple labels (vs single label)
            
        Returns:
            PolicyClassificationResult
        """
        cats = categories or self.categories
        
        # Run classification
        result = self.pipeline(text, cats, multi_label=multi_label)
        
        return PolicyClassificationResult(
            text=text,
            labels=result['labels'],
            scores=result['scores'],
            top_label=result['labels'][0],
            top_score=result['scores'][0],
            timestamp=datetime.now(),
            source=source,
            ticker=ticker
        )
    
    def classify_batch(
        self,
        texts: List[str],
        categories: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        multi_label: bool = False
    ) -> List[PolicyClassificationResult]:
        """
        Classify multiple texts.
        
        Args:
            texts: List of texts to classify
            categories: Custom categories (uses default if None)
            sources: Optional list of sources
            tickers: Optional list of tickers
            multi_label: Whether to allow multiple labels
            
        Returns:
            List of PolicyClassificationResults
        """
        if sources is None:
            sources = [None] * len(texts)
        if tickers is None:
            tickers = [None] * len(texts)
        
        cats = categories or self.categories
        results = []
        timestamp = datetime.now()
        
        for text, src, tick in zip(texts, sources, tickers):
            result = self.pipeline(text, cats, multi_label=multi_label)
            
            results.append(
                PolicyClassificationResult(
                    text=text,
                    labels=result['labels'],
                    scores=result['scores'],
                    top_label=result['labels'][0],
                    top_score=result['scores'][0],
                    timestamp=timestamp,
                    source=src,
                    ticker=tick
                )
            )
        
        return results
    
    def get_category_distribution(
        self,
        results: List[PolicyClassificationResult],
        threshold: float = 0.5
    ) -> Dict[str, Dict]:
        """
        Get distribution of categories across multiple results.
        
        Args:
            results: List of PolicyClassificationResults
            threshold: Minimum confidence threshold
            
        Returns:
            Dictionary with category counts and percentages
        """
        category_counts = {cat: 0 for cat in self.categories}
        high_conf_counts = {cat: 0 for cat in self.categories}
        
        for result in results:
            # Count top label
            category_counts[result.top_label] += 1
            
            # Count high-confidence predictions
            if result.top_score >= threshold:
                high_conf_counts[result.top_label] += 1
        
        total = len(results)
        distribution = {}
        
        for cat in self.categories:
            distribution[cat] = {
                'count': category_counts[cat],
                'percentage': category_counts[cat] / total * 100 if total > 0 else 0,
                'high_confidence_count': high_conf_counts[cat],
                'avg_confidence': 0.0  # Will calculate below
            }
        
        # Calculate average confidence per category
        for result in results:
            idx = result.labels.index(result.top_label)
            distribution[result.top_label]['avg_confidence'] += result.scores[idx]
        
        for cat in self.categories:
            if category_counts[cat] > 0:
                distribution[cat]['avg_confidence'] /= category_counts[cat]
        
        return distribution
    
    def identify_policy_risks(
        self,
        results: List[PolicyClassificationResult],
        risk_categories: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Identify potential policy risks from classification results.
        
        Args:
            results: List of PolicyClassificationResults
            risk_categories: Categories to monitor (defaults to regulatory/geopolitical)
            
        Returns:
            List of risk events with details
        """
        if risk_categories is None:
            risk_categories = [
                "technology regulation",
                "geopolitical tension",
                "Federal Reserve policy"
            ]
        
        risks = []
        
        for result in results:
            if result.top_label in risk_categories and result.top_score > 0.7:
                risks.append({
                    'category': result.top_label,
                    'confidence': result.top_score,
                    'text': result.text[:200],  # Truncate
                    'source': result.source,
                    'ticker': result.ticker,
                    'timestamp': result.timestamp.isoformat()
                })
        
        # Sort by confidence
        risks.sort(key=lambda x: x['confidence'], reverse=True)
        
        return risks


def main():
    """Test Agent 24 with policy-relevant news"""
    
    # Initialize agent
    agent = Agent24_PolicyClassifier()
    
    # Test samples
    test_news = [
        ("The Federal Reserve announced interest rate decision impacting tech stocks", None, "GENERAL"),
        ("D-Wave secures $100M contract with Department of Defense for quantum research", None, "QTEM"),
        ("New quantum computing export restrictions target China amid tech tensions", None, "GENERAL"),
        ("IONQ partners with AWS for quantum cloud services expansion", None, "IONQ"),
        ("Rigetti reports Q3 earnings, beats revenue expectations but misses EPS", None, "RGTI"),
        ("Biden administration announces $5B quantum computing initiative", None, "GENERAL"),
        ("Quantum Computing Inc appoints new CEO from tech sector", None, "QUBT"),
        ("Market volatility continues as investors await Fed decision", None, "GENERAL")
    ]
    
    print("\n" + "="*70)
    print("Agent 24: Policy Classification Test")
    print("="*70 + "\n")
    
    all_results = []
    for text, source, ticker in test_news:
        result = agent.classify(text, source=source, ticker=ticker)
        all_results.append(result)
        
        # Show top 3 classifications
        top3 = list(zip(result.labels[:3], result.scores[:3]))
        print(f"📋 {text[:55]}...")
        print(f"   1. {top3[0][0]:25s} ({top3[0][1]:.3f})")
        print(f"   2. {top3[1][0]:25s} ({top3[1][1]:.3f})")
        print(f"   3. {top3[2][0]:25s} ({top3[2][1]:.3f})")
        print()
    
    # Category distribution
    print("-"*70)
    print("Category Distribution:")
    print("-"*70)
    
    dist = agent.get_category_distribution(all_results)
    for cat, metrics in sorted(dist.items(), key=lambda x: x[1]['count'], reverse=True):
        if metrics['count'] > 0:
            print(f"{cat:30s} | Count: {metrics['count']:2d} | {metrics['percentage']:5.1f}% | Avg Conf: {metrics['avg_confidence']:.3f}")
    
    # Policy risks
    print("\n" + "-"*70)
    print("Identified Policy Risks:")
    print("-"*70)
    
    risks = agent.identify_policy_risks(all_results)
    for i, risk in enumerate(risks, 1):
        print(f"{i}. [{risk['category']}] ({risk['confidence']:.3f})")
        print(f"   {risk['text'][:60]}...")
        print()
    
    print("="*70)
    print("✅ Agent 24 test complete!")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
