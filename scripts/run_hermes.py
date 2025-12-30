#!/usr/bin/env python3
"""
HERMES Quantum - End-to-End Trading Analysis Demo
==================================================
Runs all agents on real market data and produces unified trading decisions.

Usage:
    python scripts/run_hermes.py
    python scripts/run_hermes.py --ticker QBTS
    python scripts/run_hermes.py --all-tickers
    
Created: 2025-12-30
"""

import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion.market_data import get_market_data_fetcher, reset_market_data_fetcher
from agents.integrated_agents import (
    IntegratedSentimentAgent,
    IntegratedSocialAgent,
    IntegratedPolicyAgent,
    IntegratedForecastAgent,
    IntegratedPortfolioAgent,
    create_all_agents
)
from agents.base_agent import AgentSignal, SignalStrength, ActionRecommendation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


@dataclass
class TradingDecision:
    """Final trading decision with full reasoning."""
    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    current_price: float
    target_price: Optional[float]
    expected_return: Optional[float]
    reasoning: str
    agent_signals: Dict[str, Dict[str, Any]]
    risk_level: str  # LOW, MEDIUM, HIGH
    position_size_pct: float  # Recommended position size as % of portfolio
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "confidence": self.confidence,
            "current_price": self.current_price,
            "target_price": self.target_price,
            "expected_return": self.expected_return,
            "reasoning": self.reasoning,
            "agent_signals": self.agent_signals,
            "risk_level": self.risk_level,
            "position_size_pct": self.position_size_pct,
            "timestamp": self.timestamp.isoformat()
        }


class HermesOrchestrator:
    """
    Main orchestrator that coordinates all agents and produces trading decisions.
    """
    
    # Agent weights for signal aggregation
    AGENT_WEIGHTS = {
        "agent_25": 0.35,  # Forecast - highest weight (price prediction)
        "agent_22": 0.20,  # Psychology/Sentiment
        "agent_23": 0.15,  # Social media
        "agent_24": 0.15,  # Politics/Policy
        "agent_11": 0.15,  # Portfolio optimization
    }
    
    # Thresholds for decision making
    BUY_THRESHOLD = 0.15   # Need 15% positive signal to buy
    SELL_THRESHOLD = -0.10  # Need 10% negative signal to sell
    HIGH_CONFIDENCE = 0.75
    MEDIUM_CONFIDENCE = 0.50
    
    def __init__(self):
        """Initialize orchestrator with all agents."""
        self.agents = {}
        self.market_data = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all components."""
        if self._initialized:
            return
            
        logger.info("Initializing HERMES Orchestrator...")
        
        # Initialize market data fetcher
        reset_market_data_fetcher()
        self.market_data = get_market_data_fetcher()
        
        # Initialize agents
        self.agents = {
            "agent_22": IntegratedSentimentAgent(lazy_load=True),
            "agent_23": IntegratedSocialAgent(lazy_load=True),
            "agent_24": IntegratedPolicyAgent(lazy_load=True),
            "agent_25": IntegratedForecastAgent(lazy_load=True),
            "agent_11": IntegratedPortfolioAgent(lazy_load=True),
        }
        
        self._initialized = True
        logger.info(f"Initialized {len(self.agents)} agents")
    
    async def analyze_ticker(self, ticker: str) -> TradingDecision:
        """
        Run full analysis on a single ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            TradingDecision with action, confidence, and reasoning
        """
        await self.initialize()
        
        logger.info(f"=" * 60)
        logger.info(f"Analyzing {ticker}...")
        logger.info(f"=" * 60)
        
        # Get real-time market data
        quote = self.market_data.get_quote(ticker)
        if not quote:
            raise ValueError(f"Could not fetch data for {ticker}")
        
        logger.info(f"Current price: ${quote.price:.2f} ({quote.change_percent:+.2f}%)")
        
        # Collect signals from all agents
        signals: Dict[str, AgentSignal] = {}
        
        for agent_id, agent in self.agents.items():
            try:
                signal = await agent.analyze(ticker)
                if signal:
                    signals[agent_id] = signal
                    action_emoji = "🟢" if signal.action.value == "buy" else "🔴" if signal.action.value == "sell" else "⚪"
                    logger.info(f"  {action_emoji} {agent.name}: {signal.action.value.upper()} ({signal.confidence:.0%}) - {signal.reasoning[:50]}...")
            except Exception as e:
                logger.warning(f"  ⚠️ {agent_id} failed: {e}")
        
        # Aggregate signals into final decision
        decision = self._aggregate_signals(ticker, quote, signals)
        
        # Log decision
        self._log_decision(decision)
        
        return decision
    
    def _aggregate_signals(
        self, 
        ticker: str, 
        quote: Any, 
        signals: Dict[str, AgentSignal]
    ) -> TradingDecision:
        """
        Aggregate all agent signals into a unified trading decision.
        
        Uses weighted voting with confidence adjustment.
        """
        if not signals:
            return TradingDecision(
                ticker=ticker,
                action="HOLD",
                confidence=0.0,
                current_price=quote.price,
                target_price=None,
                expected_return=None,
                reasoning="No agent signals available",
                agent_signals={},
                risk_level="HIGH",
                position_size_pct=0.0
            )
        
        # Calculate weighted score
        total_weight = 0.0
        weighted_score = 0.0
        weighted_confidence = 0.0
        
        agent_summaries = {}
        
        for agent_id, signal in signals.items():
            weight = self.AGENT_WEIGHTS.get(agent_id, 0.1)
            
            # Convert action to numeric score
            if signal.action == ActionRecommendation.STRONG_BUY:
                action_score = 1.0
            elif signal.action == ActionRecommendation.BUY:
                action_score = 0.6
            elif signal.action == ActionRecommendation.HOLD:
                action_score = 0.0
            elif signal.action == ActionRecommendation.SELL:
                action_score = -0.6
            elif signal.action == ActionRecommendation.STRONG_SELL:
                action_score = -1.0
            else:
                action_score = 0.0
            
            # Weight by confidence
            effective_weight = weight * signal.confidence
            weighted_score += action_score * effective_weight
            weighted_confidence += signal.confidence * weight
            total_weight += weight
            
            # Store summary
            agent_summaries[agent_id] = {
                "action": signal.action.value,
                "confidence": signal.confidence,
                "value": signal.value,
                "reasoning": signal.reasoning,
                "weight": weight
            }
        
        # Normalize
        if total_weight > 0:
            weighted_score /= total_weight
            weighted_confidence /= total_weight
        
        # Determine final action
        if weighted_score >= self.BUY_THRESHOLD:
            if weighted_score >= 0.5 and weighted_confidence >= self.HIGH_CONFIDENCE:
                action = "STRONG_BUY"
            else:
                action = "BUY"
        elif weighted_score <= self.SELL_THRESHOLD:
            if weighted_score <= -0.5 and weighted_confidence >= self.HIGH_CONFIDENCE:
                action = "STRONG_SELL"
            else:
                action = "SELL"
        else:
            action = "HOLD"
        
        # Get forecast data for target price
        forecast_signal = signals.get("agent_25")
        target_price = forecast_signal.price_target if forecast_signal else None
        expected_return = forecast_signal.value if forecast_signal else None
        
        # Determine risk level
        volatility = abs(quote.change_percent) if quote.change_percent else 0
        if volatility > 5 or weighted_confidence < 0.5:
            risk_level = "HIGH"
        elif volatility > 2 or weighted_confidence < 0.7:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Calculate position size based on confidence and risk
        if action in ["STRONG_BUY", "STRONG_SELL"]:
            base_size = 10.0
        elif action in ["BUY", "SELL"]:
            base_size = 5.0
        else:
            base_size = 0.0
        
        # Adjust for confidence and risk
        position_size = base_size * weighted_confidence
        if risk_level == "HIGH":
            position_size *= 0.5
        elif risk_level == "MEDIUM":
            position_size *= 0.75
        
        # Build reasoning
        reasoning_parts = []
        
        # Count votes
        buy_votes = sum(1 for s in signals.values() if s.action.value in ["buy", "strong_buy"])
        sell_votes = sum(1 for s in signals.values() if s.action.value in ["sell", "strong_sell"])
        hold_votes = len(signals) - buy_votes - sell_votes
        
        reasoning_parts.append(f"Agent consensus: {buy_votes} BUY, {hold_votes} HOLD, {sell_votes} SELL")
        reasoning_parts.append(f"Weighted signal: {weighted_score:+.2f}")
        reasoning_parts.append(f"Average confidence: {weighted_confidence:.0%}")
        
        if forecast_signal and target_price:
            reasoning_parts.append(f"Price target: ${target_price:.2f} ({expected_return:+.1%})")
        
        # Add top agent insights
        for agent_id, summary in sorted(agent_summaries.items(), 
                                         key=lambda x: x[1]["weight"], reverse=True)[:2]:
            agent_name = self.agents[agent_id].name
            reasoning_parts.append(f"{agent_name}: {summary['reasoning'][:60]}...")
        
        return TradingDecision(
            ticker=ticker,
            action=action,
            confidence=weighted_confidence,
            current_price=quote.price,
            target_price=target_price,
            expected_return=expected_return,
            reasoning=" | ".join(reasoning_parts),
            agent_signals=agent_summaries,
            risk_level=risk_level,
            position_size_pct=position_size
        )
    
    def _log_decision(self, decision: TradingDecision):
        """Log decision to MLFlow if available."""
        try:
            import importlib
            mlflow_mod = importlib.import_module('agents.91_tools.mlflow_tracking')
            tracker = mlflow_mod.get_mlflow_tracker()
            
            tracker.log_decision(
                ticker=decision.ticker,
                decision=decision.action,
                confidence=decision.confidence,
                price=decision.current_price,
                target_price=decision.target_price,
                reasoning=decision.reasoning,
                agent_signals=decision.agent_signals
            )
            logger.info("Decision logged to MLFlow")
        except Exception as e:
            logger.debug(f"MLFlow logging skipped: {e}")
    
    async def analyze_all(self, tickers: List[str] = None) -> List[TradingDecision]:
        """
        Analyze all tickers and return ranked decisions.
        
        Args:
            tickers: List of tickers (defaults to quantum stocks)
            
        Returns:
            List of TradingDecisions sorted by opportunity score
        """
        tickers = tickers or ["QBTS", "IONQ", "RGTI", "QUBT"]
        
        decisions = []
        for ticker in tickers:
            try:
                decision = await self.analyze_ticker(ticker)
                decisions.append(decision)
            except Exception as e:
                logger.error(f"Failed to analyze {ticker}: {e}")
        
        # Sort by opportunity (buy signals first, then by expected return)
        def sort_key(d):
            action_score = {"STRONG_BUY": 4, "BUY": 3, "HOLD": 2, "SELL": 1, "STRONG_SELL": 0}
            return (action_score.get(d.action, 2), d.expected_return or 0)
        
        decisions.sort(key=sort_key, reverse=True)
        
        return decisions


def print_decision(decision: TradingDecision):
    """Pretty print a trading decision."""
    # Action emoji and color
    action_display = {
        "STRONG_BUY": "🟢🟢 STRONG BUY",
        "BUY": "🟢 BUY",
        "HOLD": "⚪ HOLD",
        "SELL": "🔴 SELL",
        "STRONG_SELL": "🔴🔴 STRONG SELL"
    }
    
    print()
    print("=" * 70)
    print(f"  {decision.ticker} - {action_display.get(decision.action, decision.action)}")
    print("=" * 70)
    print(f"  Current Price:    ${decision.current_price:.2f}")
    if decision.target_price:
        print(f"  Target Price:     ${decision.target_price:.2f} ({decision.expected_return:+.1%})")
    print(f"  Confidence:       {decision.confidence:.0%}")
    print(f"  Risk Level:       {decision.risk_level}")
    print(f"  Position Size:    {decision.position_size_pct:.1f}% of portfolio")
    print()
    print(f"  Reasoning:")
    for part in decision.reasoning.split(" | "):
        print(f"    • {part}")
    print()
    print("  Agent Signals:")
    for agent_id, signal in decision.agent_signals.items():
        action_emoji = "🟢" if signal["action"] in ["buy", "strong_buy"] else "🔴" if signal["action"] in ["sell", "strong_sell"] else "⚪"
        print(f"    {action_emoji} {agent_id}: {signal['action'].upper()} ({signal['confidence']:.0%})")
    print()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="HERMES Quantum Trading Analysis")
    parser.add_argument("--ticker", "-t", type=str, help="Analyze specific ticker")
    parser.add_argument("--all-tickers", "-a", action="store_true", help="Analyze all quantum stocks")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + "  HERMES QUANTUM - Autonomous Trading Analysis System  ".center(68) + "║")
    print("║" + f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    orchestrator = HermesOrchestrator()
    
    if args.ticker:
        # Single ticker analysis
        decision = await orchestrator.analyze_ticker(args.ticker.upper())
        if args.json:
            print(json.dumps(decision.to_dict(), indent=2))
        else:
            print_decision(decision)
    else:
        # All tickers
        tickers = ["QBTS", "IONQ", "RGTI", "QUBT"]
        decisions = await orchestrator.analyze_all(tickers)
        
        if args.json:
            print(json.dumps([d.to_dict() for d in decisions], indent=2))
        else:
            print("\n" + "=" * 70)
            print("  TRADING RECOMMENDATIONS (Ranked by Opportunity)")
            print("=" * 70)
            
            for decision in decisions:
                print_decision(decision)
            
            # Summary
            print("=" * 70)
            print("  SUMMARY")
            print("=" * 70)
            print()
            buy_count = sum(1 for d in decisions if d.action in ["BUY", "STRONG_BUY"])
            sell_count = sum(1 for d in decisions if d.action in ["SELL", "STRONG_SELL"])
            hold_count = len(decisions) - buy_count - sell_count
            
            print(f"  Total analyzed: {len(decisions)} tickers")
            print(f"  🟢 Buy signals:  {buy_count}")
            print(f"  ⚪ Hold signals: {hold_count}")
            print(f"  🔴 Sell signals: {sell_count}")
            
            if buy_count > 0:
                top_pick = next((d for d in decisions if d.action in ["BUY", "STRONG_BUY"]), None)
                if top_pick:
                    print()
                    print(f"  🏆 Top Pick: {top_pick.ticker} - {top_pick.action}")
                    print(f"     Expected Return: {top_pick.expected_return:+.1%}" if top_pick.expected_return else "")
            
            print()


if __name__ == "__main__":
    asyncio.run(main())
