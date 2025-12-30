#!/usr/bin/env python3
"""
Integration Test: Agent 22 + Agent 24 with Real RSS News
Test sentiment analysis and policy classification on live news
"""

import sys
sys.path.append('/workspaces/HERMES_Quantum')

# Import news aggregator using importlib due to numeric prefix
import importlib.util

spec_news = importlib.util.spec_from_file_location(
    "news_aggregator",
    "/workspaces/HERMES_Quantum/agents/91_tools/news_aggregator.py"
)
news_module = importlib.util.module_from_spec(spec_news)
spec_news.loader.exec_module(news_module)
NewsAggregator = news_module.NewsAggregator

import logging

# Import agents with proper module paths
import importlib.util

# Load Agent 22
spec22 = importlib.util.spec_from_file_location(
    "agent22", 
    "/workspaces/HERMES_Quantum/agents/22_psychology/sentiment_analyzer.py"
)
agent22_module = importlib.util.module_from_spec(spec22)
spec22.loader.exec_module(agent22_module)
Agent22_SentimentAnalyzer = agent22_module.Agent22_SentimentAnalyzer

# Load Agent 24
spec24 = importlib.util.spec_from_file_location(
    "agent24",
    "/workspaces/HERMES_Quantum/agents/24_politics/policy_classifier.py"
)
agent24_module = importlib.util.module_from_spec(spec24)
spec24.loader.exec_module(agent24_module)
Agent24_PolicyClassifier = agent24_module.Agent24_PolicyClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("Integration Test: RSS News → Agent 22 + Agent 24")
    print("="*70 + "\n")
    
    # Step 1: Fetch RSS news
    print("Step 1: Fetching RSS news for quantum stocks...")
    print("-"*70)
    
    aggregator = NewsAggregator()
    articles = aggregator.fetch_all_feeds()
    
    print(f"✅ Found {len(articles)} articles\n")
    
    if not articles:
        print("❌ No articles found. Using sample data...")
        # Use sample data
        from datetime import datetime
        
        # Create simple article objects
        class Article:
            def __init__(self, title, description, link, source):
                self.title = title
                self.description = description
                self.link = link
                self.source = source
                self.published_date = datetime.now()
        
        articles = [
            Article(
                "IONQ announces major quantum breakthrough",
                "IonQ has achieved a significant milestone in quantum error correction",
                "https://example.com/1",
                "Yahoo Finance"
            ),
            Article(
                "Federal Reserve signals tech sector concerns",
                "Fed officials express worries about overheated tech valuations",
                "https://example.com/2",
                "MarketWatch"
            )
        ]
    
    # Step 2: Initialize agents
    print("Step 2: Initializing Agent 22 (Sentiment) and Agent 24 (Policy)...")
    print("-"*70)
    
    agent22 = Agent22_SentimentAnalyzer()
    agent24 = Agent24_PolicyClassifier()
    
    print("✅ Agents ready\n")
    
    # Step 3: Analyze articles
    print("Step 3: Analyzing articles...")
    print("="*70 + "\n")
    
    for i, article in enumerate(articles[:5], 1):  # Limit to 5 for demo
        text = f"{article.title}. {article.summary or ''}"
        
        print(f"Article {i}: {article.title[:60]}...")
        print(f"Source: {article.source}")
        print()
        
        # Sentiment analysis (Agent 22)
        sentiment = agent22.analyze(text, source=article.source)
        emoji = "✅" if sentiment.label == "positive" else "❌" if sentiment.label == "negative" else "⚪"
        print(f"  {emoji} Sentiment: {sentiment.label.upper()} (confidence: {sentiment.score:.3f})")
        
        # Policy classification (Agent 24)
        policy = agent24.classify(text, source=article.source)
        print(f"  📋 Category: {policy.top_label} (confidence: {policy.top_score:.3f})")
        print(f"     Other: {policy.labels[1]} ({policy.scores[1]:.2f}), {policy.labels[2]} ({policy.scores[2]:.2f})")
        
        print(f"  🔗 Link: {article.url}")
        print()
    
    # Step 4: Aggregate results
    print("="*70)
    print("Aggregated Results:")
    print("="*70 + "\n")
    
    # Sentiment aggregation
    texts = [f"{a.title}. {a.summary or ''}" for a in articles[:5]]
    sentiments = agent22.analyze_batch(texts)
    agg_sentiment = agent22.aggregate_sentiment(sentiments)
    
    print("Sentiment Overview:")
    print(f"  Overall Score: {agg_sentiment['overall_score']:+.3f}")
    print(f"  Positive: {agg_sentiment['positive_ratio']:.1%}")
    print(f"  Negative: {agg_sentiment['negative_ratio']:.1%}")
    print(f"  Neutral: {agg_sentiment['neutral_ratio']:.1%}")
    print()
    
    # Policy distribution
    policies = agent24.classify_batch(texts)
    dist = agent24.get_category_distribution(policies)
    
    print("Policy Category Distribution:")
    for cat, metrics in sorted(dist.items(), key=lambda x: x[1]['count'], reverse=True):
        if metrics['count'] > 0:
            print(f"  {cat}: {metrics['count']} ({metrics['percentage']:.0f}%)")
    
    print("\n" + "="*70)
    print("✅ Integration test complete!")
    print("="*70)


if __name__ == "__main__":
    main()
