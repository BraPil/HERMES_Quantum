"""
HERMES_Quantum Agent Adapters
=============================
Bridges specialist agents (22, 23, 24, 25, 11) to the orchestrator's event system.

Each adapter:
1. Wraps a specialist agent
2. Converts agent output to orchestrator Signal format
3. Publishes signals to the event bus
4. Handles errors gracefully

This module is the glue that connects:
- Agent 22 (Psychology/Sentiment) -> SIGNAL_SENTIMENT events
- Agent 23 (Social) -> SIGNAL_SOCIAL events
- Agent 24 (Politics) -> SIGNAL_POLICY events
- Agent 25 (Market Forecaster) -> SIGNAL_FORECAST events
- Agent 11 (Portfolio) -> SIGNAL_PORTFOLIO events

Created: 2026-01-01
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .event_bus import (
    Event, EventBus, EventType, EventPriority,
    get_event_bus, publish_signal
)
from .decision_maker import Signal

logger = logging.getLogger(__name__)


class AgentAdapter(ABC):
    """Base class for agent adapters."""
    
    def __init__(self, agent_id: str, event_bus: EventBus = None):
        self.agent_id = agent_id
        self.event_bus = event_bus or get_event_bus()
        self._last_run: Optional[datetime] = None
        self._error_count = 0
        self._success_count = 0
        
    @abstractmethod
    async def run(self, tickers: List[str]) -> List[Signal]:
        """Run the agent for given tickers, return signals."""
        pass
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "agent_id": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "success_rate": self._success_count / max(1, self._success_count + self._error_count)
        }


class SentimentAgentAdapter(AgentAdapter):
    """
    Adapter for Agent 22 (Psychology/Sentiment).
    
    Fetches news, analyzes sentiment with FinBERT, and publishes signals.
    """
    
    def __init__(
        self,
        agent_id: str = "agent_22_sentiment",
        news_aggregator: Any = None,
        sentiment_analyzer: Any = None,
        event_bus: EventBus = None
    ):
        super().__init__(agent_id, event_bus)
        self._news_aggregator = news_aggregator
        self._sentiment_analyzer = sentiment_analyzer
        self._lazy_loaded = False
    
    def _lazy_load(self):
        """Lazy load heavy dependencies to speed up startup."""
        if self._lazy_loaded:
            return
        
        try:
            if self._news_aggregator is None:
                import importlib
                mod = importlib.import_module('agents.91_tools.news_aggregator')
                self._news_aggregator = mod.NewsAggregator()
                logger.info("NewsAggregator loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load NewsAggregator: {e}")
        
        try:
            if self._sentiment_analyzer is None:
                import importlib
                mod = importlib.import_module('agents.22_psychology.sentiment_analyzer')
                self._sentiment_analyzer = mod.Agent22_SentimentAnalyzer()
                logger.info("Agent22_SentimentAnalyzer loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load Agent22_SentimentAnalyzer: {e}")
        
        self._lazy_loaded = True
    
    async def run(self, tickers: List[str]) -> List[Signal]:
        """
        Run sentiment analysis for tickers.
        
        1. Fetch recent news for tickers
        2. Analyze sentiment with FinBERT
        3. Aggregate per ticker
        4. Publish signals to event bus
        """
        self._last_run = datetime.now()
        signals = []
        
        try:
            self._lazy_load()
            
            if self._news_aggregator is None or self._sentiment_analyzer is None:
                logger.warning("Sentiment agent not fully loaded, using placeholder")
                # Return placeholder signals for testing
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="sentiment",
                        ticker=ticker,
                        value=0.0,
                        confidence=0.3,
                        reasoning="Agent 22 not fully loaded - placeholder signal"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                return signals
            
            # Fetch news for each ticker
            for ticker in tickers:
                try:
                    # Get recent news using correct method name
                    news_items = self._news_aggregator.get_recent_news(hours=24, ticker=ticker)
                    
                    if not news_items:
                        logger.debug(f"No news found for {ticker}")
                        continue
                    
                    # Limit to 10 most recent
                    news_items = news_items[:10]
                    
                    # Analyze sentiment
                    texts = [item.get("title", "") + " " + item.get("summary", "") 
                             for item in news_items]
                    results = self._sentiment_analyzer.analyze_batch(
                        texts, 
                        tickers=[ticker] * len(texts)
                    )
                    
                    # Aggregate
                    agg = self._sentiment_analyzer.aggregate_sentiment(results)
                    
                    # Create signal
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="sentiment",
                        ticker=ticker,
                        value=agg.get("overall_score", 0.0),
                        confidence=agg.get("confidence", 0.0),
                        reasoning=f"Sentiment analysis of {len(results)} news items: "
                                  f"{agg.get('positive_ratio', 0):.0%} positive, "
                                  f"{agg.get('negative_ratio', 0):.0%} negative, "
                                  f"{agg.get('neutral_ratio', 0):.0%} neutral",
                        metadata={
                            "num_samples": len(results),
                            "positive_ratio": agg.get("positive_ratio", 0),
                            "negative_ratio": agg.get("negative_ratio", 0),
                            "neutral_ratio": agg.get("neutral_ratio", 0)
                        }
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for {ticker}: {e}")
            
            self._success_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in sentiment adapter: {e}")
        
        return signals
    
    def _publish_signal(self, signal: Signal):
        """Publish signal to event bus."""
        # Include reasoning in metadata since publish_signal doesn't accept it directly
        meta = signal.metadata or {}
        meta["reasoning"] = signal.reasoning
        publish_signal(
            signal_type="sentiment",
            ticker=signal.ticker,
            value=signal.value,
            confidence=signal.confidence,
            source=self.agent_id,
            metadata=meta
        )


class SocialAgentAdapter(AgentAdapter):
    """
    Adapter for Agent 23 (Social Sentiment).
    
    Fetches social media data, analyzes sentiment with FinTwitBERT.
    """
    
    def __init__(
        self,
        agent_id: str = "agent_23_social",
        reddit_collector: Any = None,
        stocktwits_collector: Any = None,
        social_analyzer: Any = None,
        event_bus: EventBus = None
    ):
        super().__init__(agent_id, event_bus)
        self._reddit_collector = reddit_collector
        self._stocktwits_collector = stocktwits_collector
        self._social_analyzer = social_analyzer
        self._lazy_loaded = False
    
    def _lazy_load(self):
        """Lazy load dependencies."""
        if self._lazy_loaded:
            return
        
        try:
            if self._social_analyzer is None:
                import importlib
                mod = importlib.import_module('agents.23_social.social_sentiment')
                self._social_analyzer = mod.Agent23_SocialSentimentAnalyzer()
                logger.info("Agent23_SocialSentimentAnalyzer loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load Agent23_SocialSentiment: {e}")
        
        self._lazy_loaded = True
    
    async def run(self, tickers: List[str]) -> List[Signal]:
        """Run social sentiment analysis."""
        self._last_run = datetime.now()
        signals = []
        
        try:
            self._lazy_load()
            
            if self._social_analyzer is None:
                # Placeholder signals
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="social",
                        ticker=ticker,
                        value=0.0,
                        confidence=0.3,
                        reasoning="Agent 23 not loaded - placeholder signal"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                return signals
            
            # Run social analysis - use news as proxy for social content
            # In production, this would integrate with StockTwits/Reddit APIs
            for ticker in tickers:
                try:
                    # For now, generate placeholder social sentiment
                    # Real implementation would fetch from StockTwits/Reddit
                    # The Agent23 can analyze individual posts with analyze(text, platform, ticker)
                    
                    # Create a placeholder signal with neutral sentiment
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="social",
                        ticker=ticker,
                        value=0.0,  # Neutral - would be from actual social data
                        confidence=0.3,  # Low confidence for placeholder
                        reasoning="Social sentiment - awaiting social API integration",
                        metadata={
                            "platform": "placeholder",
                            "num_posts": 0,
                            "bullish_ratio": 0.0,
                            "bearish_ratio": 0.0
                        }
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Error analyzing social for {ticker}: {e}")
            
            self._success_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in social adapter: {e}")
        
        return signals
    
    def _publish_signal(self, signal: Signal):
        """Publish signal to event bus."""
        meta = signal.metadata or {}
        meta["reasoning"] = signal.reasoning
        publish_signal(
            signal_type="social",
            ticker=signal.ticker,
            value=signal.value,
            confidence=signal.confidence,
            source=self.agent_id,
            metadata=meta
        )


class PolicyAgentAdapter(AgentAdapter):
    """
    Adapter for Agent 24 (Politics/Policy).
    
    Analyzes regulatory and policy news using zero-shot classification.
    """
    
    def __init__(
        self,
        agent_id: str = "agent_24_policy",
        policy_classifier: Any = None,
        event_bus: EventBus = None
    ):
        super().__init__(agent_id, event_bus)
        self._policy_classifier = policy_classifier
        self._lazy_loaded = False
    
    def _lazy_load(self):
        """Lazy load dependencies."""
        if self._lazy_loaded:
            return
        
        try:
            if self._policy_classifier is None:
                import importlib
                mod = importlib.import_module('agents.24_politics.policy_classifier')
                self._policy_classifier = mod.Agent24_PolicyClassifier()
                logger.info("Agent24_PolicyClassifier loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load Agent24_PolicyClassifier: {e}")
        
        self._lazy_loaded = True
    
    async def run(self, tickers: List[str]) -> List[Signal]:
        """Run policy analysis."""
        self._last_run = datetime.now()
        signals = []
        
        try:
            self._lazy_load()
            
            if self._policy_classifier is None:
                # Placeholder signals
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="policy",
                        ticker=ticker,
                        value=0.0,
                        confidence=0.3,
                        reasoning="Agent 24 not loaded - placeholder signal"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                return signals
            
            # Run policy analysis
            for ticker in tickers:
                try:
                    # For now, generate placeholder policy signal
                    # Real implementation would analyze regulatory news
                    # The Agent24 can classify texts with classify(text, ticker)
                    
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="policy",
                        ticker=ticker,
                        value=0.0,  # Neutral policy impact
                        confidence=0.3,
                        reasoning="Policy analysis - awaiting regulatory news integration",
                        metadata={
                            "category": "neutral",
                            "risk_level": "low"
                        }
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Error analyzing policy for {ticker}: {e}")
            
            self._success_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in policy adapter: {e}")
        
        return signals
    
    def _publish_signal(self, signal: Signal):
        """Publish signal to event bus."""
        meta = signal.metadata or {}
        meta["reasoning"] = signal.reasoning
        publish_signal(
            signal_type="policy",
            ticker=signal.ticker,
            value=signal.value,
            confidence=signal.confidence,
            source=self.agent_id,
            metadata=meta
        )


class ForecastAgentAdapter(AgentAdapter):
    """
    Adapter for Agent 25 (Market Forecaster).
    
    Runs price forecasting using Chronos-T5.
    """
    
    def __init__(
        self,
        agent_id: str = "agent_25_forecast",
        forecaster: Any = None,
        stock_data_fetcher: Any = None,
        event_bus: EventBus = None
    ):
        super().__init__(agent_id, event_bus)
        self._forecaster = forecaster
        self._stock_data_fetcher = stock_data_fetcher
        self._lazy_loaded = False
    
    def _lazy_load(self):
        """Lazy load dependencies."""
        if self._lazy_loaded:
            return
        
        try:
            if self._stock_data_fetcher is None:
                from data_ingestion.stock_data import StockDataFetcher
                self._stock_data_fetcher = StockDataFetcher()
                logger.info("StockDataFetcher loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load StockDataFetcher: {e}")
        
        try:
            if self._forecaster is None:
                import importlib
                mod = importlib.import_module('agents.25_market.forecaster')
                self._forecaster = mod.Agent25_MarketForecaster()
                logger.info("Agent25_MarketForecaster loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load Agent25_MarketForecaster: {e}")
        
        self._lazy_loaded = True
    
    async def run(self, tickers: List[str]) -> List[Signal]:
        """Run market forecasting."""
        self._last_run = datetime.now()
        signals = []
        
        try:
            self._lazy_load()
            
            if self._forecaster is None:
                # Placeholder signals
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="forecast",
                        ticker=ticker,
                        value=0.0,
                        confidence=0.3,
                        reasoning="Agent 25 not loaded - placeholder signal"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                return signals
            
            # Run forecasting for each ticker
            for ticker in tickers:
                try:
                    # Fetch historical data using correct method name
                    if self._stock_data_fetcher:
                        hist_data = self._stock_data_fetcher.fetch_ohlcv(
                            ticker, period="6mo"
                        )
                        if hist_data is not None and not hist_data.empty:
                            # Column names are lowercase (close, not Close)
                            prices = hist_data["close"].values
                            current_price = float(prices[-1])
                        else:
                            current_price = self._get_default_price(ticker)
                            prices = None
                    else:
                        current_price = self._get_default_price(ticker)
                        prices = None
                    
                    # Generate forecast
                    if prices is not None and len(prices) >= 30:
                        forecast = self._forecaster.forecast(
                            ticker=ticker,
                            prices=prices,  # Correct parameter name
                            forecast_horizon=5,
                            current_price=current_price
                        )
                        
                        # Convert forecast to signal value (-1 to 1)
                        expected_return = float(forecast.expected_return)
                        signal_value = max(-1.0, min(1.0, expected_return * 10))  # Scale
                        
                        # Convert numpy arrays to Python lists of floats for JSON serialization
                        predictions = [float(x) for x in forecast.predictions.tolist()]
                        lower_bound = [float(x) for x in forecast.lower_bound.tolist()]
                        upper_bound = [float(x) for x in forecast.upper_bound.tolist()]
                        
                        signal = Signal(
                            source=self.agent_id,
                            signal_type="forecast",
                            ticker=ticker,
                            value=signal_value,
                            confidence=float(forecast.confidence),
                            reasoning=f"5-day forecast: {forecast.trend}, "
                                      f"expected return: {expected_return:.1%}",
                            metadata={
                                "predictions": predictions,
                                "lower_bound": lower_bound,
                                "upper_bound": upper_bound,
                                "trend": forecast.trend,
                                "current_price": float(current_price)
                            }
                        )
                    else:
                        signal = Signal(
                            source=self.agent_id,
                            signal_type="forecast",
                            ticker=ticker,
                            value=0.0,
                            confidence=0.2,
                            reasoning="Insufficient historical data for forecast"
                        )
                    
                    signals.append(signal)
                    self._publish_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Error forecasting {ticker}: {e}")
            
            self._success_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in forecast adapter: {e}")
        
        return signals
    
    def _get_default_price(self, ticker: str) -> float:
        """Get default price for a ticker."""
        defaults = {"QBTS": 4.27, "IONQ": 8.15, "RGTI": 2.45, "QUBT": 3.82}
        return defaults.get(ticker, 10.0)
    
    def _publish_signal(self, signal: Signal):
        """Publish signal to event bus."""
        meta = signal.metadata or {}
        meta["reasoning"] = signal.reasoning
        publish_signal(
            signal_type="forecast",
            ticker=signal.ticker,
            value=signal.value,
            confidence=signal.confidence,
            source=self.agent_id,
            metadata=meta
        )


class PortfolioAgentAdapter(AgentAdapter):
    """
    Adapter for Agent 11 (Portfolio Optimizer).
    
    Runs portfolio optimization and provides allocation signals.
    """
    
    def __init__(
        self,
        agent_id: str = "agent_11_portfolio",
        portfolio_optimizer: Any = None,
        stock_data_fetcher: Any = None,
        event_bus: EventBus = None
    ):
        super().__init__(agent_id, event_bus)
        self._portfolio_optimizer = portfolio_optimizer
        self._stock_data_fetcher = stock_data_fetcher
        self._lazy_loaded = False
    
    def _lazy_load(self):
        """Lazy load dependencies."""
        if self._lazy_loaded:
            return
        
        try:
            if self._stock_data_fetcher is None:
                from data_ingestion.stock_data import StockDataFetcher
                self._stock_data_fetcher = StockDataFetcher()
                logger.info("StockDataFetcher loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load StockDataFetcher: {e}")
        
        try:
            if self._portfolio_optimizer is None:
                import importlib
                mod = importlib.import_module('agents.11_analyst.portfolio_optimizer')
                self._portfolio_optimizer = mod.Agent11_PortfolioAnalyst()
                logger.info("Agent11_PortfolioAnalyst loaded")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not load Agent11_PortfolioAnalyst: {e}")
        
        self._lazy_loaded = True
    
    async def run(self, tickers: List[str]) -> List[Signal]:
        """Run portfolio optimization."""
        self._last_run = datetime.now()
        signals = []
        
        try:
            self._lazy_load()
            
            if self._portfolio_optimizer is None:
                # Placeholder signals
                weight = 1.0 / len(tickers)
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="portfolio",
                        ticker=ticker,
                        value=weight,
                        confidence=0.3,
                        reasoning="Agent 11 not loaded - equal weight placeholder"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
                return signals
            
            # Fetch price data for all tickers
            if self._stock_data_fetcher:
                # fetch_quantum_stocks_wide returns wide format data for all quantum tickers
                price_data = self._stock_data_fetcher.fetch_quantum_stocks_wide(
                    period="6mo"
                )
            else:
                price_data = None
            
            if price_data is not None and not price_data.empty:
                # Run optimization
                allocation = self._portfolio_optimizer.optimize_max_sharpe(price_data)
                
                # Create signals for each ticker with its weight
                for ticker in tickers:
                    weight = allocation.weights.get(ticker, 0.0)
                    
                    # Value is the weight (0 to 1)
                    # Confidence based on Sharpe ratio quality
                    confidence = min(1.0, allocation.sharpe_ratio / 3.0)
                    
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="portfolio",
                        ticker=ticker,
                        value=weight,
                        confidence=confidence,
                        reasoning=f"Max Sharpe allocation: {weight:.1%} weight, "
                                  f"Portfolio Sharpe: {allocation.sharpe_ratio:.2f}",
                        metadata={
                            "allocation_method": allocation.allocation_method,
                            "expected_return": allocation.expected_return,
                            "volatility": allocation.volatility,
                            "sharpe_ratio": allocation.sharpe_ratio,
                            "all_weights": allocation.weights
                        }
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
            else:
                # Equal weight fallback
                weight = 1.0 / len(tickers)
                for ticker in tickers:
                    signal = Signal(
                        source=self.agent_id,
                        signal_type="portfolio",
                        ticker=ticker,
                        value=weight,
                        confidence=0.3,
                        reasoning="Equal weight allocation (no historical data)"
                    )
                    signals.append(signal)
                    self._publish_signal(signal)
            
            self._success_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Error in portfolio adapter: {e}")
        
        return signals
    
    def _publish_signal(self, signal: Signal):
        """Publish signal to event bus."""
        meta = signal.metadata or {}
        meta["reasoning"] = signal.reasoning
        publish_signal(
            signal_type="portfolio",
            ticker=signal.ticker,
            value=signal.value,
            confidence=signal.confidence,
            source=self.agent_id,
            metadata=meta
        )


# =============================================================================
# Factory Function
# =============================================================================

def create_all_adapters(event_bus: EventBus = None) -> Dict[str, AgentAdapter]:
    """
    Create all agent adapters.
    
    Returns:
        Dictionary of agent_id -> adapter
    """
    adapters = {}
    
    adapters["agent_22"] = SentimentAgentAdapter(event_bus=event_bus)
    adapters["agent_23"] = SocialAgentAdapter(event_bus=event_bus)
    adapters["agent_24"] = PolicyAgentAdapter(event_bus=event_bus)
    adapters["agent_25"] = ForecastAgentAdapter(event_bus=event_bus)
    adapters["agent_11"] = PortfolioAgentAdapter(event_bus=event_bus)
    
    return adapters


# =============================================================================
# Demo
# =============================================================================

async def demo():
    """Demonstrate agent adapters."""
    print("=" * 60)
    print("HERMES Agent Adapters Demo")
    print("=" * 60)
    
    # Create adapters
    adapters = create_all_adapters()
    tickers = ["QBTS", "IONQ"]
    
    print(f"\nCreated {len(adapters)} adapters for tickers: {tickers}")
    
    # Run each adapter
    for agent_id, adapter in adapters.items():
        print(f"\n--- Running {agent_id} ---")
        try:
            signals = await adapter.run(tickers)
            print(f"Generated {len(signals)} signals:")
            for signal in signals:
                print(f"  {signal.ticker}: {signal.signal_type} = {signal.value:.2f} "
                      f"(conf: {signal.confidence:.2f})")
        except Exception as e:
            print(f"Error: {e}")
    
    # Show stats
    print("\n" + "-" * 60)
    print("Adapter Statistics:")
    for agent_id, adapter in adapters.items():
        stats = adapter.stats
        print(f"  {agent_id}: runs={stats['success_count']}, errors={stats['error_count']}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo())
