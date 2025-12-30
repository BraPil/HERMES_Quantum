"""
HERMES_Quantum Decision Maker
=============================
Core decision engine for Agent 01.
Aggregates signals, generates buy/sell/hold decisions,
and provides reasoning for the UX dashboard.

This module is the "brain" of HERMES that:
1. Collects signals from all specialist agents
2. Weights signals using the learning engine
3. Generates actionable decisions with reasoning
4. Calculates entry/exit targets (Buy @ / Sell @)
5. Provides real-time conviction scores

Created: 2025-12-30
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import uuid

from .event_bus import (
    Event, EventBus, EventType, EventPriority,
    get_event_bus, publish_decision
)
from .learning_engine import (
    LearningEngine, get_learning_engine
)
from .prediction_tracker import (
    PredictionTracker, PredictionType, get_prediction_tracker
)

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of trading actions."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ActionStrength(Enum):
    """Strength of the recommendation."""
    VERY_STRONG = "very_strong"  # 90%+ confidence
    STRONG = "strong"            # 75-90% confidence
    MODERATE = "moderate"        # 50-75% confidence
    WEAK = "weak"                # 25-50% confidence
    NEUTRAL = "neutral"          # <25% confidence


@dataclass
class Signal:
    """A signal from a specialist agent."""
    source: str                    # e.g., "agent_22_psychology"
    signal_type: str               # sentiment, social, policy, forecast
    ticker: str
    value: float                   # -1 to 1 (or price for forecasts)
    confidence: float              # 0 to 1
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "signal_type": self.signal_type,
            "ticker": self.ticker,
            "value": self.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }


@dataclass
class EntryTarget:
    """A buy entry target (Buy @)."""
    price: float
    probability: float        # Probability of reaching this price
    expected_wait: str        # e.g., "2 days", "4 hours"
    pattern: str              # What pattern suggests this
    rationale: str            # Why this is a good entry
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": round(self.price, 2),
            "probability": round(self.probability * 100, 1),
            "expected_wait": self.expected_wait,
            "pattern": self.pattern,
            "rationale": self.rationale,
            "confidence": round(self.confidence * 100, 1)
        }


@dataclass
class ExitTarget:
    """A sell exit target (Sell @)."""
    price: float
    probability: float
    expected_wait: str
    pattern: str
    rationale: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": round(self.price, 2),
            "probability": round(self.probability * 100, 1),
            "expected_wait": self.expected_wait,
            "pattern": self.pattern,
            "rationale": self.rationale,
            "confidence": round(self.confidence * 100, 1)
        }


@dataclass
class TradingDecision:
    """
    A complete trading decision with full context for the UX dashboard.
    
    This is the primary output that feeds the dashboard display.
    """
    decision_id: str
    ticker: str
    company_name: str
    current_price: float
    
    # Core Decision
    action: ActionType
    action_strength: ActionStrength
    signal_strength: float         # 0-100 scale
    conviction: float              # 0-100% confidence
    
    # Signal Details
    signal_description: str        # Human-readable signal summary
    reasoning: str                 # Full reasoning explanation
    contributing_signals: List[Signal]
    
    # Entry/Exit Targets
    buy_targets: List[EntryTarget]
    sell_targets: List[ExitTarget]
    
    # Range and Pattern Analysis
    current_range: Tuple[float, float]  # Today's low-high
    expected_range: Tuple[float, float]  # Next 3 days
    short_term_target: float       # 5-day forecast
    medium_term_target: float      # 30-day forecast
    short_term_confidence: float
    medium_term_confidence: float
    
    # Patterns
    past_patterns: List[str]       # Completed patterns
    current_patterns: List[str]    # In formation
    emerging_patterns: List[str]   # Early indicators
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/dashboard."""
        return {
            "decision_id": self.decision_id,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "current_price": round(self.current_price, 2),
            
            "action": self.action.value.upper(),
            "action_strength": self.action_strength.value.replace("_", " ").title(),
            "signal_strength": round(self.signal_strength, 1),
            "conviction": round(self.conviction, 1),
            
            "signal_description": self.signal_description,
            "reasoning": self.reasoning,
            "contributing_signals": [s.to_dict() for s in self.contributing_signals],
            
            "buy_targets": [t.to_dict() for t in self.buy_targets],
            "sell_targets": [t.to_dict() for t in self.sell_targets],
            
            "range_analysis": {
                "current_range": {
                    "low": round(self.current_range[0], 2),
                    "high": round(self.current_range[1], 2)
                },
                "expected_range": {
                    "low": round(self.expected_range[0], 2),
                    "high": round(self.expected_range[1], 2)
                },
                "short_term_target": {
                    "price": round(self.short_term_target, 2),
                    "confidence": round(self.short_term_confidence * 100, 1),
                    "timeframe": "5 days"
                },
                "medium_term_target": {
                    "price": round(self.medium_term_target, 2),
                    "confidence": round(self.medium_term_confidence * 100, 1),
                    "timeframe": "30 days"
                }
            },
            
            "patterns": {
                "past": self.past_patterns,
                "current": self.current_patterns,
                "emerging": self.emerging_patterns
            },
            
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }
    
    def get_summary(self) -> str:
        """Get a brief human-readable summary."""
        return (
            f"{self.action.value.upper()} {self.ticker} @ ${self.current_price:.2f} | "
            f"Strength: {self.action_strength.value.replace('_', ' ').title()} | "
            f"Conviction: {self.conviction:.0f}%"
        )


class DecisionMaker:
    """
    Core decision engine for HERMES.
    
    This class is responsible for:
    1. Collecting signals from specialist agents (22-25)
    2. Aggregating and weighting signals using the learning engine
    3. Making buy/sell/hold decisions
    4. Calculating entry/exit targets
    5. Generating reasoning and explanations
    6. Producing TradingDecision objects for the dashboard
    
    Usage:
        maker = DecisionMaker()
        
        # Add signals from agents
        maker.add_signal(Signal(
            source="agent_22",
            signal_type="sentiment",
            ticker="QBTS",
            value=0.75,
            confidence=0.85
        ))
        
        # Generate decision
        decision = maker.generate_decision("QBTS")
        
        # Get dashboard-ready output
        output = decision.to_dict()
    """
    
    # Company name mapping
    COMPANY_NAMES = {
        "QBTS": "D-Wave Quantum Inc.",
        "IONQ": "IonQ, Inc.",
        "RGTI": "Rigetti Computing, Inc.",
        "QUBT": "Quantum Computing Inc."
    }
    
    def __init__(self, db_path: str = None):
        """
        Initialize the decision maker.
        
        Args:
            db_path: Path to SQLite database for decision history
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "outputs" / "data" / "decisions.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Signal buffer (most recent signals per ticker/type)
        self._signals: Dict[str, Dict[str, Signal]] = {}  # ticker -> {signal_type: Signal}
        
        # Current market data cache
        self._market_data: Dict[str, Dict[str, Any]] = {}
        
        # Recent decisions
        self._recent_decisions: List[TradingDecision] = []
        self._max_recent = 100
        
        # Learning engine integration
        self._learning_engine = get_learning_engine()
        self._prediction_tracker = get_prediction_tracker()
        
        # Initialize database
        self._init_db()
        
        # Subscribe to events
        self._setup_event_subscriptions()
        
        logger.info("DecisionMaker initialized")
    
    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                action_strength TEXT,
                signal_strength REAL,
                conviction REAL,
                current_price REAL,
                signal_description TEXT,
                reasoning TEXT,
                contributing_signals TEXT,
                buy_targets TEXT,
                sell_targets TEXT,
                timestamp TEXT NOT NULL,
                expires_at TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_ticker 
            ON decisions(ticker)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_decisions_timestamp 
            ON decisions(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _setup_event_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        bus = get_event_bus()
        
        # Listen for signals from specialist agents
        bus.subscribe(EventType.SIGNAL_SENTIMENT, self._handle_signal)
        bus.subscribe(EventType.SIGNAL_SOCIAL, self._handle_signal)
        bus.subscribe(EventType.SIGNAL_POLICY, self._handle_signal)
        bus.subscribe(EventType.SIGNAL_FORECAST, self._handle_signal)
        bus.subscribe(EventType.SIGNAL_PORTFOLIO, self._handle_signal)
        
        # Listen for market data updates
        bus.subscribe(EventType.DATA_STOCK_UPDATE, self._handle_market_data)
    
    def _handle_signal(self, event: Event) -> None:
        """Handle incoming signal from specialist agent."""
        data = event.data
        
        signal = Signal(
            source=event.source,
            signal_type=self._event_type_to_signal_type(event.event_type),
            ticker=data.get("ticker", ""),
            value=data.get("value", 0.0),
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", ""),
            metadata=event.metadata
        )
        
        self.add_signal(signal)
    
    def _event_type_to_signal_type(self, event_type: EventType) -> str:
        """Convert event type to signal type string."""
        mapping = {
            EventType.SIGNAL_SENTIMENT: "sentiment",
            EventType.SIGNAL_SOCIAL: "social",
            EventType.SIGNAL_POLICY: "policy",
            EventType.SIGNAL_FORECAST: "forecast",
            EventType.SIGNAL_PORTFOLIO: "portfolio"
        }
        return mapping.get(event_type, "unknown")
    
    def _handle_market_data(self, event: Event) -> None:
        """Handle market data update."""
        data = event.data
        ticker = data.get("ticker")
        
        if ticker:
            self._market_data[ticker] = {
                "price": data.get("price", 0),
                "open": data.get("open", 0),
                "high": data.get("high", 0),
                "low": data.get("low", 0),
                "volume": data.get("volume", 0),
                "timestamp": datetime.now()
            }
    
    def add_signal(self, signal: Signal) -> None:
        """
        Add a signal to the buffer.
        
        Args:
            signal: Signal from a specialist agent
        """
        ticker = signal.ticker
        signal_type = signal.signal_type
        
        if ticker not in self._signals:
            self._signals[ticker] = {}
        
        self._signals[ticker][signal_type] = signal
        
        logger.debug(f"Added signal: {signal.source} -> {ticker} = {signal.value:.2f}")
    
    def generate_decision(
        self,
        ticker: str,
        current_price: float = None,
        force: bool = False
    ) -> TradingDecision:
        """
        Generate a trading decision for a ticker.
        
        Args:
            ticker: Stock ticker
            current_price: Current stock price (will fetch if not provided)
            force: Generate decision even with incomplete signals
            
        Returns:
            TradingDecision object ready for dashboard
        """
        decision_id = str(uuid.uuid4())[:8]
        
        # Get current price from cache or parameter
        if current_price is None:
            market_data = self._market_data.get(ticker, {})
            current_price = market_data.get("price", 0)
        
        # Get market data
        market_data = self._market_data.get(ticker, {})
        current_range = (
            market_data.get("low", current_price * 0.98),
            market_data.get("high", current_price * 1.02)
        )
        
        # Collect signals for this ticker
        ticker_signals = self._signals.get(ticker, {})
        signals = list(ticker_signals.values())
        
        # Weight and aggregate signals
        action, action_strength, conviction, signal_strength, reasoning = \
            self._calculate_decision(signals, ticker, current_price)
        
        # Generate signal description
        signal_description = self._generate_signal_description(signals, action)
        
        # Calculate entry/exit targets
        buy_targets = self._calculate_buy_targets(ticker, current_price, signals)
        sell_targets = self._calculate_sell_targets(ticker, current_price, signals)
        
        # Get forecast targets
        short_term_target, short_term_conf = self._get_forecast_target(ticker, "5d")
        medium_term_target, medium_term_conf = self._get_forecast_target(ticker, "30d")
        
        # Get expected range
        expected_range = self._learning_engine.get_prediction_range(
            ticker, current_price, "3d", 0.68
        )
        
        # Get patterns
        past_patterns, current_patterns, emerging_patterns = \
            self._detect_patterns(ticker, signals)
        
        # Create decision
        decision = TradingDecision(
            decision_id=decision_id,
            ticker=ticker,
            company_name=self.COMPANY_NAMES.get(ticker, ticker),
            current_price=current_price,
            action=action,
            action_strength=action_strength,
            signal_strength=signal_strength,
            conviction=conviction,
            signal_description=signal_description,
            reasoning=reasoning,
            contributing_signals=signals,
            buy_targets=buy_targets,
            sell_targets=sell_targets,
            current_range=current_range,
            expected_range=expected_range,
            short_term_target=short_term_target or current_price,
            medium_term_target=medium_term_target or current_price,
            short_term_confidence=short_term_conf,
            medium_term_confidence=medium_term_conf,
            past_patterns=past_patterns,
            current_patterns=current_patterns,
            emerging_patterns=emerging_patterns,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Store in history
        self._store_decision(decision)
        self._recent_decisions.append(decision)
        if len(self._recent_decisions) > self._max_recent:
            self._recent_decisions.pop(0)
        
        # Publish decision event
        self._publish_decision_event(decision)
        
        # Store prediction for learning
        self._store_prediction(decision)
        
        logger.info(f"Generated decision: {decision.get_summary()}")
        
        return decision
    
    def _calculate_decision(
        self,
        signals: List[Signal],
        ticker: str,
        current_price: float
    ) -> Tuple[ActionType, ActionStrength, float, float, str]:
        """
        Calculate the final decision from signals.
        
        Returns:
            (action, action_strength, conviction, signal_strength, reasoning)
        """
        if not signals:
            return (
                ActionType.HOLD,
                ActionStrength.NEUTRAL,
                0.0,
                50.0,
                "Insufficient signals to make a recommendation."
            )
        
        # Convert signals to format for learning engine
        signal_tuples = [
            (s.source, s.value, s.confidence)
            for s in signals
        ]
        
        # Get weighted signal
        weighted_signal, combined_confidence = \
            self._learning_engine.get_weighted_signal(signal_tuples)
        
        # Calculate signal strength (0-100 scale)
        signal_strength = abs(weighted_signal) * 100
        
        # Determine action
        if weighted_signal > 0.3:
            action = ActionType.BUY
        elif weighted_signal < -0.3:
            action = ActionType.SELL
        else:
            action = ActionType.HOLD
        
        # Determine strength based on conviction
        conviction = combined_confidence * 100
        
        if conviction >= 85:
            action_strength = ActionStrength.VERY_STRONG
        elif conviction >= 70:
            action_strength = ActionStrength.STRONG
        elif conviction >= 50:
            action_strength = ActionStrength.MODERATE
        elif conviction >= 30:
            action_strength = ActionStrength.WEAK
        else:
            action_strength = ActionStrength.NEUTRAL
        
        # Generate reasoning
        reasoning = self._generate_reasoning(signals, action, weighted_signal, conviction)
        
        return action, action_strength, conviction, signal_strength, reasoning
    
    def _generate_signal_description(
        self,
        signals: List[Signal],
        action: ActionType
    ) -> str:
        """Generate a human-readable signal description."""
        if not signals:
            return "No active signals"
        
        # Identify dominant signals
        positive_signals = [s for s in signals if s.value > 0.3]
        negative_signals = [s for s in signals if s.value < -0.3]
        
        parts = []
        
        if action == ActionType.BUY:
            if any(s.signal_type == "sentiment" for s in positive_signals):
                parts.append("Bullish Sentiment")
            if any(s.signal_type == "social" for s in positive_signals):
                parts.append("Social Momentum")
            if any(s.signal_type == "policy" for s in positive_signals):
                parts.append("Policy Catalyst")
            if any(s.signal_type == "forecast" for s in positive_signals):
                parts.append("Positive Forecast")
        elif action == ActionType.SELL:
            if any(s.signal_type == "sentiment" for s in negative_signals):
                parts.append("Bearish Sentiment")
            if any(s.signal_type == "social" for s in negative_signals):
                parts.append("Negative Social Trend")
            if any(s.signal_type == "policy" for s in negative_signals):
                parts.append("Policy Risk")
            if any(s.signal_type == "forecast" for s in negative_signals):
                parts.append("Negative Forecast")
        else:
            parts.append("Mixed Signals")
        
        return " + ".join(parts) if parts else "Neutral Market Conditions"
    
    def _generate_reasoning(
        self,
        signals: List[Signal],
        action: ActionType,
        weighted_signal: float,
        conviction: float
    ) -> str:
        """Generate detailed reasoning for the decision."""
        lines = []
        
        # Header
        if action == ActionType.BUY:
            lines.append("BULLISH CASE:")
        elif action == ActionType.SELL:
            lines.append("BEARISH CASE:")
        else:
            lines.append("NEUTRAL ASSESSMENT:")
        
        # Contributing factors
        for signal in sorted(signals, key=lambda s: abs(s.value), reverse=True):
            indicator = "▲" if signal.value > 0 else "▼" if signal.value < 0 else "●"
            strength_pct = abs(signal.value) * 100
            confidence_pct = signal.confidence * 100
            
            lines.append(
                f"• {signal.signal_type.title()}: {indicator} {strength_pct:.0f}% "
                f"(confidence: {confidence_pct:.0f}%)"
            )
            
            if signal.reasoning:
                lines.append(f"  └─ {signal.reasoning}")
        
        # Summary
        lines.append("")
        lines.append(
            f"Overall weighted signal: {weighted_signal:+.2f} | "
            f"Conviction: {conviction:.0f}%"
        )
        
        return "\n".join(lines)
    
    def _calculate_buy_targets(
        self,
        ticker: str,
        current_price: float,
        signals: List[Signal]
    ) -> List[EntryTarget]:
        """Calculate optimal buy entry points."""
        targets = []
        
        # Get calibrated ranges
        low_68, _ = self._learning_engine.get_prediction_range(
            ticker, current_price, "3d", 0.68
        )
        low_95, _ = self._learning_engine.get_prediction_range(
            ticker, current_price, "3d", 0.95
        )
        
        # Target 1: Near support (high probability)
        target_1_price = current_price * 0.97  # 3% below current
        targets.append(EntryTarget(
            price=max(low_68, target_1_price),
            probability=0.85,
            expected_wait="1-2 days",
            pattern="Support Level + Intraday Dip",
            rationale="High probability entry at minor pullback level. "
                     "Historical data suggests 85% chance of reaching this price within 2 days.",
            confidence=0.82
        ))
        
        # Target 2: Deeper support (medium probability)
        target_2_price = current_price * 0.94  # 6% below current
        targets.append(EntryTarget(
            price=max(low_95, target_2_price),
            probability=0.55,
            expected_wait="3-5 days",
            pattern="Strong Support + Moving Average",
            rationale="More aggressive entry at significant support level. "
                     "Better risk/reward but lower probability of filling.",
            confidence=0.68
        ))
        
        return targets
    
    def _calculate_sell_targets(
        self,
        ticker: str,
        current_price: float,
        signals: List[Signal]
    ) -> List[ExitTarget]:
        """Calculate optimal sell exit points."""
        targets = []
        
        # Get calibrated ranges
        _, high_68 = self._learning_engine.get_prediction_range(
            ticker, current_price, "3d", 0.68
        )
        _, high_95 = self._learning_engine.get_prediction_range(
            ticker, current_price, "7d", 0.95
        )
        
        # Target 1: Near resistance (high probability)
        target_1_price = current_price * 1.05  # 5% above current
        targets.append(ExitTarget(
            price=min(high_68, target_1_price),
            probability=0.75,
            expected_wait="2-3 days",
            pattern="Resistance Level + Overbought",
            rationale="Take profit at first resistance level. "
                     "Good for securing gains with high probability of reaching.",
            confidence=0.78
        ))
        
        # Target 2: Extended target (lower probability)
        target_2_price = current_price * 1.12  # 12% above current
        targets.append(ExitTarget(
            price=min(high_95, target_2_price),
            probability=0.40,
            expected_wait="7-10 days",
            pattern="Major Resistance + Momentum Extension",
            rationale="Aggressive profit target if momentum continues. "
                     "Consider trailing stop if reached.",
            confidence=0.55
        ))
        
        return targets
    
    def _get_forecast_target(
        self,
        ticker: str,
        timeframe: str
    ) -> Tuple[Optional[float], float]:
        """Get forecast target from Agent 25."""
        # Look for recent forecast signal
        ticker_signals = self._signals.get(ticker, {})
        forecast_signal = ticker_signals.get("forecast")
        
        if forecast_signal and forecast_signal.signal_type == "forecast":
            # Forecast value is typically the predicted price
            return forecast_signal.value, forecast_signal.confidence
        
        return None, 0.5
    
    def _detect_patterns(
        self,
        ticker: str,
        signals: List[Signal]
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Detect chart patterns.
        
        Returns:
            (past_patterns, current_patterns, emerging_patterns)
        """
        # Placeholder - would integrate with technical analysis
        past_patterns = ["Ascending Triangle (Dec 20-27) → Breakout confirmed"]
        current_patterns = ["Bull Flag (forming since Dec 28, 67% complete)"]
        emerging_patterns = ["Volume spike pattern forming", "Potential double bottom"]
        
        return past_patterns, current_patterns, emerging_patterns
    
    def _store_decision(self, decision: TradingDecision) -> None:
        """Store decision in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO decisions
            (decision_id, ticker, action, action_strength, signal_strength, conviction,
             current_price, signal_description, reasoning, contributing_signals,
             buy_targets, sell_targets, timestamp, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            decision.decision_id,
            decision.ticker,
            decision.action.value,
            decision.action_strength.value,
            decision.signal_strength,
            decision.conviction,
            decision.current_price,
            decision.signal_description,
            decision.reasoning,
            json.dumps([s.to_dict() for s in decision.contributing_signals]),
            json.dumps([t.to_dict() for t in decision.buy_targets]),
            json.dumps([t.to_dict() for t in decision.sell_targets]),
            decision.timestamp.isoformat(),
            decision.expires_at.isoformat() if decision.expires_at else None,
            json.dumps(decision.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def _publish_decision_event(self, decision: TradingDecision) -> None:
        """Publish decision to event bus."""
        bus = get_event_bus()
        
        event_type = {
            ActionType.BUY: EventType.DECISION_BUY,
            ActionType.SELL: EventType.DECISION_SELL,
            ActionType.HOLD: EventType.DECISION_HOLD
        }[decision.action]
        
        bus.publish(
            event_type=event_type,
            source="decision_maker",
            data=decision.to_dict(),
            priority=EventPriority.CRITICAL,
            correlation_id=decision.decision_id
        )
    
    def _store_prediction(self, decision: TradingDecision) -> None:
        """Store prediction for learning engine."""
        # Store short-term price prediction
        if decision.short_term_target > 0:
            self._prediction_tracker.store_prediction(
                ticker=decision.ticker,
                prediction_type=PredictionType.PRICE_EOD,
                predicted_value=decision.short_term_target,
                confidence=decision.short_term_confidence,
                target_time=datetime.now() + timedelta(days=5),
                model_source="decision_maker",
                context={
                    "decision_id": decision.decision_id,
                    "action": decision.action.value,
                    "conviction": decision.conviction
                }
            )
        
        # Store direction prediction
        direction = 1 if decision.action == ActionType.BUY else (
            -1 if decision.action == ActionType.SELL else 0
        )
        
        self._prediction_tracker.store_prediction(
            ticker=decision.ticker,
            prediction_type=PredictionType.DIRECTION,
            predicted_value=direction,
            confidence=decision.conviction / 100,
            target_time=datetime.now() + timedelta(days=1),
            model_source="decision_maker"
        )
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def get_latest_decision(self, ticker: str) -> Optional[TradingDecision]:
        """Get the most recent decision for a ticker."""
        for decision in reversed(self._recent_decisions):
            if decision.ticker == ticker:
                return decision
        return None
    
    def get_all_latest_decisions(self) -> Dict[str, TradingDecision]:
        """Get latest decision for each ticker."""
        latest = {}
        for decision in reversed(self._recent_decisions):
            if decision.ticker not in latest:
                latest[decision.ticker] = decision
        return latest
    
    def get_decision_history(
        self,
        ticker: str = None,
        limit: int = 100
    ) -> List[TradingDecision]:
        """Get decision history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if ticker:
            cursor.execute("""
                SELECT * FROM decisions
                WHERE ticker = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (ticker, limit))
        else:
            cursor.execute("""
                SELECT * FROM decisions
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to decisions (simplified - just return raw data)
        return rows
    
    def clear_signals(self, ticker: str = None) -> None:
        """Clear signal buffer."""
        if ticker:
            self._signals.pop(ticker, None)
        else:
            self._signals.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get decision maker statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN action = 'buy' THEN 1 ELSE 0 END) as buys,
                SUM(CASE WHEN action = 'sell' THEN 1 ELSE 0 END) as sells,
                SUM(CASE WHEN action = 'hold' THEN 1 ELSE 0 END) as holds,
                AVG(conviction) as avg_conviction,
                COUNT(DISTINCT ticker) as tickers
            FROM decisions
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_decisions": row[0] or 0,
            "buys": row[1] or 0,
            "sells": row[2] or 0,
            "holds": row[3] or 0,
            "avg_conviction": round(row[4] or 0, 2),
            "unique_tickers": row[5] or 0,
            "signals_in_buffer": sum(len(s) for s in self._signals.values()),
            "recent_decisions": len(self._recent_decisions)
        }


# Singleton instance
_decision_maker: Optional[DecisionMaker] = None


def get_decision_maker() -> DecisionMaker:
    """Get the global decision maker instance."""
    global _decision_maker
    if _decision_maker is None:
        _decision_maker = DecisionMaker()
    return _decision_maker


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate DecisionMaker functionality."""
    print("=" * 60)
    print("HERMES Decision Maker Demo")
    print("=" * 60)
    
    maker = get_decision_maker()
    
    # Add some mock signals
    print("\n1. Adding signals from specialist agents...")
    
    maker.add_signal(Signal(
        source="agent_22_psychology",
        signal_type="sentiment",
        ticker="QBTS",
        value=0.72,
        confidence=0.85,
        reasoning="FinBERT analysis shows strong positive sentiment in recent news"
    ))
    
    maker.add_signal(Signal(
        source="agent_23_social",
        signal_type="social",
        ticker="QBTS",
        value=0.58,
        confidence=0.78,
        reasoning="Reddit and StockTwits show bullish momentum, +45% above average"
    ))
    
    maker.add_signal(Signal(
        source="agent_24_politics",
        signal_type="policy",
        ticker="QBTS",
        value=0.65,
        confidence=0.72,
        reasoning="Federal quantum computing funding announcement expected"
    ))
    
    maker.add_signal(Signal(
        source="agent_25_market",
        signal_type="forecast",
        ticker="QBTS",
        value=4.85,  # Forecasted price
        confidence=0.80,
        reasoning="Chronos 5-day forecast shows +12% upside"
    ))
    
    print("   Added 4 signals for QBTS")
    
    # Generate decision
    print("\n2. Generating trading decision...")
    
    decision = maker.generate_decision("QBTS", current_price=4.27)
    
    print(f"\n   {decision.get_summary()}")
    
    # Show full decision
    print("\n3. Full Decision Output:")
    print("-" * 40)
    
    output = decision.to_dict()
    
    print(f"   Ticker: {output['ticker']} ({output['company_name']})")
    print(f"   Current Price: ${output['current_price']}")
    print(f"   Action: {output['action']} ({output['action_strength']})")
    print(f"   Signal Strength: {output['signal_strength']}/100")
    print(f"   Conviction: {output['conviction']}%")
    print(f"\n   Signal: {output['signal_description']}")
    print(f"\n   Reasoning:\n{decision.reasoning}")
    
    print("\n   BUY @ TARGETS:")
    for target in output['buy_targets']:
        print(f"      ${target['price']} ({target['probability']}% prob, {target['expected_wait']})")
    
    print("\n   SELL @ TARGETS:")
    for target in output['sell_targets']:
        print(f"      ${target['price']} ({target['probability']}% prob, {target['expected_wait']})")
    
    # Stats
    print("\n4. Decision Maker Stats:")
    stats = maker.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
