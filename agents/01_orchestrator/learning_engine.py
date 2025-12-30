"""
HERMES_Quantum Learning Engine (Agent 92 Integration)
======================================================
Real-time ML learning from predictions vs actuals.
Adjusts signal weights, ranges, and thresholds based on performance.

This is the "brain" that makes HERMES smarter over time.

Key Features:
- Real-time error analysis
- Dynamic weight adjustment (which agents to trust more)
- Confidence calibration
- Range and target optimization
- Pattern learning from mistakes

Created: 2025-12-30
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import statistics
import math

from .event_bus import (
    Event, EventBus, EventType, EventPriority,
    get_event_bus
)
from .prediction_tracker import (
    PredictionTracker, PredictionType, AccuracyMetrics,
    get_prediction_tracker
)

logger = logging.getLogger(__name__)


@dataclass
class ModelWeight:
    """Dynamic weight for a model/signal source."""
    model_source: str
    weight: float = 1.0
    accuracy_1h: float = 0.5
    accuracy_24h: float = 0.5
    accuracy_7d: float = 0.5
    accuracy_28d: float = 0.5
    total_predictions: int = 0
    successful_predictions: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Learning parameters
    learning_rate: float = 0.1
    momentum: float = 0.0  # For smoothing weight changes
    
    def update_from_prediction(
        self,
        was_correct: bool,
        confidence: float,
        prediction_error: float
    ) -> float:
        """
        Update weight based on a new validated prediction.
        
        Args:
            was_correct: Whether direction was correct
            confidence: The confidence of the prediction
            prediction_error: Percentage error
            
        Returns:
            New weight value
        """
        self.total_predictions += 1
        if was_correct:
            self.successful_predictions += 1
        
        # Calculate performance signal
        # Reward: correct + high confidence + low error
        # Penalize: incorrect + high confidence
        
        if was_correct:
            # Correct prediction: reward based on confidence alignment
            reward = confidence * (1 - min(prediction_error / 100, 1))
            weight_delta = self.learning_rate * reward
        else:
            # Wrong prediction: penalize more if confident
            penalty = confidence * 0.5
            weight_delta = -self.learning_rate * penalty
        
        # Apply momentum (smooth the changes)
        self.momentum = 0.9 * self.momentum + 0.1 * weight_delta
        
        # Update weight with bounds
        self.weight = max(0.1, min(2.0, self.weight + self.momentum))
        self.last_updated = datetime.now()
        
        return self.weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_source": self.model_source,
            "weight": round(self.weight, 4),
            "accuracy_1h": round(self.accuracy_1h, 2),
            "accuracy_24h": round(self.accuracy_24h, 2),
            "accuracy_7d": round(self.accuracy_7d, 2),
            "accuracy_28d": round(self.accuracy_28d, 2),
            "total_predictions": self.total_predictions,
            "successful_predictions": self.successful_predictions,
            "success_rate": round(
                self.successful_predictions / max(1, self.total_predictions) * 100, 2
            ),
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class RangeCalibration:
    """Calibrated price ranges based on historical accuracy."""
    ticker: str
    timeframe: str  # e.g., "1min", "30min", "2hour", "eod"
    
    # Learned parameters
    typical_error: float = 0.05  # 5% typical error
    error_std: float = 0.02  # Standard deviation
    bias: float = 0.0  # Systematic over/under prediction
    
    # Confidence intervals
    ci_68: float = 0.05  # 68% of predictions within this range
    ci_95: float = 0.10  # 95% of predictions within this range
    ci_99: float = 0.15  # 99% of predictions within this range
    
    sample_size: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def update_from_errors(self, errors: List[float]) -> None:
        """Update calibration from a list of prediction errors."""
        if len(errors) < 5:
            return
        
        self.sample_size = len(errors)
        
        # Calculate statistics
        self.typical_error = statistics.mean([abs(e) for e in errors])
        self.error_std = statistics.stdev(errors) if len(errors) > 1 else 0.02
        self.bias = statistics.mean(errors)  # Positive = over-predicting
        
        # Calculate confidence intervals from percentiles
        sorted_abs_errors = sorted([abs(e) for e in errors])
        n = len(sorted_abs_errors)
        
        self.ci_68 = sorted_abs_errors[int(n * 0.68)] if n > 0 else 0.05
        self.ci_95 = sorted_abs_errors[int(n * 0.95)] if n > 0 else 0.10
        self.ci_99 = sorted_abs_errors[min(int(n * 0.99), n-1)] if n > 0 else 0.15
        
        self.last_updated = datetime.now()
    
    def get_prediction_range(
        self,
        predicted_price: float,
        confidence_level: float = 0.68
    ) -> Tuple[float, float]:
        """
        Get the expected price range given a prediction.
        
        Args:
            predicted_price: The predicted price
            confidence_level: 0.68, 0.95, or 0.99
            
        Returns:
            (low, high) price range
        """
        # Adjust for bias
        corrected_prediction = predicted_price - (self.bias * predicted_price)
        
        # Select appropriate confidence interval
        if confidence_level >= 0.99:
            margin = self.ci_99
        elif confidence_level >= 0.95:
            margin = self.ci_95
        else:
            margin = self.ci_68
        
        low = corrected_prediction * (1 - margin)
        high = corrected_prediction * (1 + margin)
        
        return (round(low, 2), round(high, 2))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "timeframe": self.timeframe,
            "typical_error": f"{self.typical_error*100:.2f}%",
            "error_std": f"{self.error_std*100:.2f}%",
            "bias": f"{self.bias*100:+.2f}%",
            "ci_68": f"±{self.ci_68*100:.1f}%",
            "ci_95": f"±{self.ci_95*100:.1f}%",
            "ci_99": f"±{self.ci_99*100:.1f}%",
            "sample_size": self.sample_size,
            "last_updated": self.last_updated.isoformat()
        }


@dataclass
class SignalThreshold:
    """Adaptive thresholds for signal-to-action conversion."""
    signal_type: str  # sentiment, social, policy, forecast
    
    # Buy thresholds (above these = buy signal)
    buy_strong: float = 0.8
    buy_moderate: float = 0.6
    buy_weak: float = 0.4
    
    # Sell thresholds (below these = sell signal)
    sell_strong: float = -0.8
    sell_moderate: float = -0.6
    sell_weak: float = -0.4
    
    # Minimum confidence required
    min_confidence_strong: float = 0.8
    min_confidence_moderate: float = 0.6
    min_confidence_weak: float = 0.4
    
    # Learned adjustments
    buy_bias: float = 0.0  # Adjust if we're buying too early/late
    sell_bias: float = 0.0  # Adjust if we're selling too early/late
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    def should_buy(
        self,
        signal_value: float,
        confidence: float
    ) -> Tuple[bool, str]:
        """
        Determine if signal indicates a buy.
        
        Returns:
            (should_buy, strength) where strength is "strong", "moderate", "weak", or None
        """
        adjusted_value = signal_value + self.buy_bias
        
        if adjusted_value >= self.buy_strong and confidence >= self.min_confidence_strong:
            return True, "strong"
        elif adjusted_value >= self.buy_moderate and confidence >= self.min_confidence_moderate:
            return True, "moderate"
        elif adjusted_value >= self.buy_weak and confidence >= self.min_confidence_weak:
            return True, "weak"
        
        return False, None
    
    def should_sell(
        self,
        signal_value: float,
        confidence: float
    ) -> Tuple[bool, str]:
        """
        Determine if signal indicates a sell.
        
        Returns:
            (should_sell, strength) where strength is "strong", "moderate", "weak", or None
        """
        adjusted_value = signal_value + self.sell_bias
        
        if adjusted_value <= self.sell_strong and confidence >= self.min_confidence_strong:
            return True, "strong"
        elif adjusted_value <= self.sell_moderate and confidence >= self.min_confidence_moderate:
            return True, "moderate"
        elif adjusted_value <= self.sell_weak and confidence >= self.min_confidence_weak:
            return True, "weak"
        
        return False, None
    
    def adjust_from_outcome(
        self,
        signal_value: float,
        action_taken: str,
        was_profitable: bool,
        profit_pct: float,
        learning_rate: float = 0.05
    ) -> None:
        """
        Adjust thresholds based on trade outcome.
        
        Args:
            signal_value: The signal that triggered the action
            action_taken: "buy" or "sell"
            was_profitable: Whether the trade was profitable
            profit_pct: Profit/loss percentage
            learning_rate: How much to adjust
        """
        if action_taken == "buy":
            if was_profitable:
                # Good buy - maybe lower threshold slightly (buy earlier)
                adjustment = -learning_rate * abs(profit_pct) / 100
            else:
                # Bad buy - raise threshold (be more conservative)
                adjustment = learning_rate * abs(profit_pct) / 100
            
            self.buy_bias += adjustment
            self.buy_bias = max(-0.2, min(0.2, self.buy_bias))  # Clamp
            
        elif action_taken == "sell":
            if was_profitable:
                # Good sell - maybe raise threshold slightly (sell earlier)
                adjustment = learning_rate * abs(profit_pct) / 100
            else:
                # Bad sell - lower threshold (hold longer)
                adjustment = -learning_rate * abs(profit_pct) / 100
            
            self.sell_bias += adjustment
            self.sell_bias = max(-0.2, min(0.2, self.sell_bias))
        
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "buy_thresholds": {
                "strong": self.buy_strong,
                "moderate": self.buy_moderate,
                "weak": self.buy_weak,
                "bias": f"{self.buy_bias:+.3f}"
            },
            "sell_thresholds": {
                "strong": self.sell_strong,
                "moderate": self.sell_moderate,
                "weak": self.sell_weak,
                "bias": f"{self.sell_bias:+.3f}"
            },
            "last_updated": self.last_updated.isoformat()
        }


class LearningEngine:
    """
    Real-time learning engine for HERMES.
    
    This engine continuously improves the system by:
    1. Tracking prediction accuracy
    2. Adjusting model weights (which signals to trust)
    3. Calibrating price ranges (confidence intervals)
    4. Optimizing signal thresholds
    5. Learning from trading outcomes
    
    Features:
    - Online learning (updates in real-time)
    - Multi-timeframe analysis
    - Explainable adjustments
    - Persistent storage
    
    Usage:
        engine = LearningEngine()
        
        # Register a prediction
        engine.on_prediction(
            ticker="QBTS",
            model_source="agent_25_chronos",
            predicted_value=4.50,
            confidence=0.85
        )
        
        # Later, when actual is known
        engine.on_actual(
            ticker="QBTS",
            model_source="agent_25_chronos",
            actual_value=4.42
        )
        
        # Get adjusted weights
        weights = engine.get_model_weights()
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the learning engine.
        
        Args:
            db_path: Path to SQLite database for persistence
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "outputs" / "data" / "learning.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory state
        self._model_weights: Dict[str, ModelWeight] = {}
        self._range_calibrations: Dict[str, RangeCalibration] = {}
        self._signal_thresholds: Dict[str, SignalThreshold] = {}
        
        # Prediction tracker integration
        self._prediction_tracker = get_prediction_tracker()
        
        # Error history for learning
        self._error_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self._max_error_history = 1000
        
        # Learning parameters
        self.learning_rate = 0.1
        self.min_samples_for_adjustment = 10
        self.recalibration_interval = timedelta(hours=1)
        self._last_recalibration: Dict[str, datetime] = {}
        
        # Initialize database
        self._init_db()
        
        # Load existing state
        self._load_state()
        
        # Subscribe to events
        self._setup_event_subscriptions()
        
        logger.info("LearningEngine initialized")
    
    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Model weights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_weights (
                model_source TEXT PRIMARY KEY,
                weight REAL NOT NULL DEFAULT 1.0,
                accuracy_1h REAL,
                accuracy_24h REAL,
                accuracy_7d REAL,
                accuracy_28d REAL,
                total_predictions INTEGER DEFAULT 0,
                successful_predictions INTEGER DEFAULT 0,
                learning_rate REAL DEFAULT 0.1,
                momentum REAL DEFAULT 0.0,
                last_updated TEXT
            )
        """)
        
        # Range calibrations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS range_calibrations (
                ticker TEXT,
                timeframe TEXT,
                typical_error REAL,
                error_std REAL,
                bias REAL,
                ci_68 REAL,
                ci_95 REAL,
                ci_99 REAL,
                sample_size INTEGER,
                last_updated TEXT,
                PRIMARY KEY (ticker, timeframe)
            )
        """)
        
        # Signal thresholds table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signal_thresholds (
                signal_type TEXT PRIMARY KEY,
                buy_strong REAL,
                buy_moderate REAL,
                buy_weak REAL,
                sell_strong REAL,
                sell_moderate REAL,
                sell_weak REAL,
                min_confidence_strong REAL,
                min_confidence_moderate REAL,
                min_confidence_weak REAL,
                buy_bias REAL,
                sell_bias REAL,
                last_updated TEXT
            )
        """)
        
        # Learning history (for analysis)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                model_source TEXT,
                ticker TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_state(self) -> None:
        """Load existing state from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load model weights
        cursor.execute("SELECT * FROM model_weights")
        for row in cursor.fetchall():
            self._model_weights[row[0]] = ModelWeight(
                model_source=row[0],
                weight=row[1],
                accuracy_1h=row[2] or 0.5,
                accuracy_24h=row[3] or 0.5,
                accuracy_7d=row[4] or 0.5,
                accuracy_28d=row[5] or 0.5,
                total_predictions=row[6] or 0,
                successful_predictions=row[7] or 0,
                learning_rate=row[8] or 0.1,
                momentum=row[9] or 0.0,
                last_updated=datetime.fromisoformat(row[10]) if row[10] else datetime.now()
            )
        
        # Load range calibrations
        cursor.execute("SELECT * FROM range_calibrations")
        for row in cursor.fetchall():
            key = f"{row[0]}_{row[1]}"
            self._range_calibrations[key] = RangeCalibration(
                ticker=row[0],
                timeframe=row[1],
                typical_error=row[2] or 0.05,
                error_std=row[3] or 0.02,
                bias=row[4] or 0.0,
                ci_68=row[5] or 0.05,
                ci_95=row[6] or 0.10,
                ci_99=row[7] or 0.15,
                sample_size=row[8] or 0,
                last_updated=datetime.fromisoformat(row[9]) if row[9] else datetime.now()
            )
        
        # Load signal thresholds
        cursor.execute("SELECT * FROM signal_thresholds")
        for row in cursor.fetchall():
            self._signal_thresholds[row[0]] = SignalThreshold(
                signal_type=row[0],
                buy_strong=row[1] or 0.8,
                buy_moderate=row[2] or 0.6,
                buy_weak=row[3] or 0.4,
                sell_strong=row[4] or -0.8,
                sell_moderate=row[5] or -0.6,
                sell_weak=row[6] or -0.4,
                min_confidence_strong=row[7] or 0.8,
                min_confidence_moderate=row[8] or 0.6,
                min_confidence_weak=row[9] or 0.4,
                buy_bias=row[10] or 0.0,
                sell_bias=row[11] or 0.0,
                last_updated=datetime.fromisoformat(row[12]) if row[12] else datetime.now()
            )
        
        conn.close()
        
        # Initialize default thresholds if not present
        for signal_type in ["sentiment", "social", "policy", "forecast"]:
            if signal_type not in self._signal_thresholds:
                self._signal_thresholds[signal_type] = SignalThreshold(signal_type=signal_type)
        
        logger.info(
            f"Loaded state: {len(self._model_weights)} models, "
            f"{len(self._range_calibrations)} calibrations, "
            f"{len(self._signal_thresholds)} thresholds"
        )
    
    def _save_state(self) -> None:
        """Persist current state to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Save model weights
        for mw in self._model_weights.values():
            cursor.execute("""
                INSERT OR REPLACE INTO model_weights
                (model_source, weight, accuracy_1h, accuracy_24h, accuracy_7d, accuracy_28d,
                 total_predictions, successful_predictions, learning_rate, momentum, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mw.model_source, mw.weight, mw.accuracy_1h, mw.accuracy_24h,
                mw.accuracy_7d, mw.accuracy_28d, mw.total_predictions,
                mw.successful_predictions, mw.learning_rate, mw.momentum,
                mw.last_updated.isoformat()
            ))
        
        # Save range calibrations
        for rc in self._range_calibrations.values():
            cursor.execute("""
                INSERT OR REPLACE INTO range_calibrations
                (ticker, timeframe, typical_error, error_std, bias, ci_68, ci_95, ci_99,
                 sample_size, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rc.ticker, rc.timeframe, rc.typical_error, rc.error_std, rc.bias,
                rc.ci_68, rc.ci_95, rc.ci_99, rc.sample_size, rc.last_updated.isoformat()
            ))
        
        # Save signal thresholds
        for st in self._signal_thresholds.values():
            cursor.execute("""
                INSERT OR REPLACE INTO signal_thresholds
                (signal_type, buy_strong, buy_moderate, buy_weak, sell_strong, sell_moderate,
                 sell_weak, min_confidence_strong, min_confidence_moderate, min_confidence_weak,
                 buy_bias, sell_bias, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                st.signal_type, st.buy_strong, st.buy_moderate, st.buy_weak,
                st.sell_strong, st.sell_moderate, st.sell_weak,
                st.min_confidence_strong, st.min_confidence_moderate, st.min_confidence_weak,
                st.buy_bias, st.sell_bias, st.last_updated.isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    def _setup_event_subscriptions(self) -> None:
        """Subscribe to relevant events."""
        bus = get_event_bus()
        
        # Listen for validated predictions
        bus.subscribe(EventType.LEARNING_ERROR_CALCULATED, self._handle_error_event)
        
        # Listen for execution outcomes
        bus.subscribe(EventType.EXECUTION_ORDER_FILLED, self._handle_execution_event)
    
    def _handle_error_event(self, event: Event) -> None:
        """Handle prediction error calculation event."""
        data = event.data
        
        model_source = data.get("model_source")
        error = data.get("error")
        percentage_error = data.get("percentage_error")
        direction_correct = data.get("direction_correct")
        ticker = data.get("ticker")
        
        if model_source and direction_correct is not None:
            # Get or create model weight
            if model_source not in self._model_weights:
                self._model_weights[model_source] = ModelWeight(model_source=model_source)
            
            mw = self._model_weights[model_source]
            
            # Get confidence from prediction tracker
            confidence = 0.7  # Default
            
            # Update weight
            old_weight = mw.weight
            new_weight = mw.update_from_prediction(
                was_correct=direction_correct,
                confidence=confidence,
                prediction_error=abs(percentage_error) if percentage_error else 5.0
            )
            
            # Track error for range calibration
            if ticker and percentage_error is not None:
                key = f"{ticker}_eod"  # Default timeframe
                if key not in self._error_history:
                    self._error_history[key] = []
                
                self._error_history[key].append((datetime.now(), percentage_error / 100))
                
                # Trim history
                if len(self._error_history[key]) > self._max_error_history:
                    self._error_history[key] = self._error_history[key][-self._max_error_history:]
                
                # Trigger recalibration if needed
                self._maybe_recalibrate(ticker, "eod")
            
            # Log significant changes
            if abs(new_weight - old_weight) > 0.01:
                logger.info(
                    f"Weight updated for {model_source}: "
                    f"{old_weight:.3f} -> {new_weight:.3f} "
                    f"(direction_correct={direction_correct})"
                )
                
                self._log_learning_event(
                    event_type="weight_update",
                    model_source=model_source,
                    ticker=ticker,
                    old_value=str(old_weight),
                    new_value=str(new_weight),
                    reason=f"direction_correct={direction_correct}, error={percentage_error:.2f}%"
                )
            
            # Publish weight update event
            bus = get_event_bus()
            bus.publish(
                event_type=EventType.LEARNING_WEIGHTS_UPDATED,
                source="learning_engine",
                data={
                    "model_source": model_source,
                    "old_weight": old_weight,
                    "new_weight": new_weight,
                    "total_predictions": mw.total_predictions,
                    "success_rate": mw.successful_predictions / max(1, mw.total_predictions)
                },
                priority=EventPriority.LOW
            )
            
            # Save state periodically
            if mw.total_predictions % 10 == 0:
                self._save_state()
    
    def _handle_execution_event(self, event: Event) -> None:
        """Handle trade execution event for outcome learning."""
        data = event.data
        
        ticker = data.get("ticker")
        action = data.get("action")
        signal_type = data.get("signal_type")
        signal_value = data.get("signal_value")
        was_profitable = data.get("was_profitable")
        profit_pct = data.get("profit_pct", 0)
        
        if signal_type and signal_type in self._signal_thresholds:
            threshold = self._signal_thresholds[signal_type]
            
            old_buy_bias = threshold.buy_bias
            old_sell_bias = threshold.sell_bias
            
            threshold.adjust_from_outcome(
                signal_value=signal_value or 0,
                action_taken=action or "hold",
                was_profitable=was_profitable or False,
                profit_pct=profit_pct,
                learning_rate=self.learning_rate
            )
            
            # Log if significant change
            if abs(threshold.buy_bias - old_buy_bias) > 0.005 or \
               abs(threshold.sell_bias - old_sell_bias) > 0.005:
                self._log_learning_event(
                    event_type="threshold_update",
                    model_source=signal_type,
                    ticker=ticker,
                    old_value=f"buy_bias={old_buy_bias:.3f}, sell_bias={old_sell_bias:.3f}",
                    new_value=f"buy_bias={threshold.buy_bias:.3f}, sell_bias={threshold.sell_bias:.3f}",
                    reason=f"action={action}, profitable={was_profitable}, profit={profit_pct:.2f}%"
                )
            
            self._save_state()
    
    def _maybe_recalibrate(self, ticker: str, timeframe: str) -> None:
        """Check if range recalibration is needed."""
        key = f"{ticker}_{timeframe}"
        last = self._last_recalibration.get(key)
        
        if last is None or datetime.now() - last > self.recalibration_interval:
            errors = self._error_history.get(key, [])
            
            if len(errors) >= self.min_samples_for_adjustment:
                # Get recent errors
                recent_errors = [e for t, e in errors if datetime.now() - t < timedelta(days=7)]
                
                if len(recent_errors) >= self.min_samples_for_adjustment:
                    # Create or update calibration
                    if key not in self._range_calibrations:
                        self._range_calibrations[key] = RangeCalibration(
                            ticker=ticker,
                            timeframe=timeframe
                        )
                    
                    old_typical = self._range_calibrations[key].typical_error
                    self._range_calibrations[key].update_from_errors(recent_errors)
                    new_typical = self._range_calibrations[key].typical_error
                    
                    if abs(new_typical - old_typical) > 0.005:
                        logger.info(
                            f"Range recalibrated for {key}: "
                            f"typical_error {old_typical*100:.2f}% -> {new_typical*100:.2f}%"
                        )
                        
                        self._log_learning_event(
                            event_type="range_recalibration",
                            model_source="range_calibrator",
                            ticker=ticker,
                            old_value=f"{old_typical*100:.2f}%",
                            new_value=f"{new_typical*100:.2f}%",
                            reason=f"Based on {len(recent_errors)} recent predictions"
                        )
                    
                    self._last_recalibration[key] = datetime.now()
                    self._save_state()
    
    def _log_learning_event(
        self,
        event_type: str,
        model_source: str,
        ticker: str,
        old_value: str,
        new_value: str,
        reason: str
    ) -> None:
        """Log a learning event for analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO learning_history
            (timestamp, event_type, model_source, ticker, old_value, new_value, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            model_source,
            ticker,
            old_value,
            new_value,
            reason
        ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def get_model_weight(self, model_source: str) -> float:
        """Get the current weight for a model."""
        if model_source in self._model_weights:
            return self._model_weights[model_source].weight
        return 1.0  # Default
    
    def get_all_model_weights(self) -> Dict[str, ModelWeight]:
        """Get all model weights."""
        return dict(self._model_weights)
    
    def get_weighted_signal(
        self,
        signals: List[Tuple[str, float, float]]
    ) -> Tuple[float, float]:
        """
        Calculate weighted signal from multiple sources.
        
        Args:
            signals: List of (model_source, signal_value, confidence)
            
        Returns:
            (weighted_signal, combined_confidence)
        """
        if not signals:
            return 0.0, 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        confidence_sum = 0.0
        
        for model_source, signal_value, confidence in signals:
            weight = self.get_model_weight(model_source)
            
            weighted_sum += signal_value * weight * confidence
            confidence_sum += confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0, 0.0
        
        weighted_signal = weighted_sum / total_weight
        combined_confidence = confidence_sum / total_weight
        
        return weighted_signal, combined_confidence
    
    def get_prediction_range(
        self,
        ticker: str,
        predicted_price: float,
        timeframe: str = "eod",
        confidence_level: float = 0.68
    ) -> Tuple[float, float]:
        """
        Get calibrated prediction range.
        
        Args:
            ticker: Stock ticker
            predicted_price: The predicted price
            timeframe: Prediction timeframe
            confidence_level: Confidence level (0.68, 0.95, or 0.99)
            
        Returns:
            (low, high) price range
        """
        key = f"{ticker}_{timeframe}"
        
        if key in self._range_calibrations:
            return self._range_calibrations[key].get_prediction_range(
                predicted_price,
                confidence_level
            )
        
        # Default: ±5% for 68%, ±10% for 95%, ±15% for 99%
        if confidence_level >= 0.99:
            margin = 0.15
        elif confidence_level >= 0.95:
            margin = 0.10
        else:
            margin = 0.05
        
        low = predicted_price * (1 - margin)
        high = predicted_price * (1 + margin)
        
        return (round(low, 2), round(high, 2))
    
    def should_take_action(
        self,
        signal_type: str,
        signal_value: float,
        confidence: float
    ) -> Tuple[str, str, float]:
        """
        Determine if action should be taken based on signal.
        
        Args:
            signal_type: Type of signal (sentiment, social, policy, forecast)
            signal_value: Signal value (-1 to 1)
            confidence: Confidence level (0 to 1)
            
        Returns:
            (action, strength, adjusted_confidence)
            action: "buy", "sell", or "hold"
            strength: "strong", "moderate", "weak", or None
            adjusted_confidence: Confidence adjusted by model weight
        """
        threshold = self._signal_thresholds.get(signal_type, SignalThreshold(signal_type))
        
        # Adjust confidence by model weight
        model_weight = self.get_model_weight(f"agent_{signal_type}")
        adjusted_confidence = confidence * model_weight
        
        # Check buy
        should_buy, buy_strength = threshold.should_buy(signal_value, adjusted_confidence)
        if should_buy:
            return "buy", buy_strength, adjusted_confidence
        
        # Check sell
        should_sell, sell_strength = threshold.should_sell(signal_value, adjusted_confidence)
        if should_sell:
            return "sell", sell_strength, adjusted_confidence
        
        return "hold", None, adjusted_confidence
    
    def get_accuracy_summary(self) -> Dict[str, Any]:
        """Get summary of all accuracy metrics."""
        tracker = self._prediction_tracker
        
        return {
            "timeframes": {
                tf: tracker.get_accuracy_metrics(tf).to_dict()
                for tf in ["1h", "24h", "7d", "28d", "6mo", "YTD", "12mo", "all"]
            },
            "model_weights": {
                k: v.to_dict() for k, v in self._model_weights.items()
            },
            "range_calibrations": {
                k: v.to_dict() for k, v in self._range_calibrations.items()
            },
            "signal_thresholds": {
                k: v.to_dict() for k, v in self._signal_thresholds.items()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning engine statistics."""
        return {
            "model_weights": len(self._model_weights),
            "range_calibrations": len(self._range_calibrations),
            "signal_thresholds": len(self._signal_thresholds),
            "error_history_entries": sum(len(v) for v in self._error_history.values()),
            "learning_rate": self.learning_rate,
            "min_samples_for_adjustment": self.min_samples_for_adjustment
        }


# Singleton instance
_learning_engine: Optional[LearningEngine] = None


def get_learning_engine() -> LearningEngine:
    """Get the global learning engine instance."""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = LearningEngine()
    return _learning_engine


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate LearningEngine functionality."""
    print("=" * 60)
    print("HERMES Learning Engine Demo")
    print("=" * 60)
    
    engine = get_learning_engine()
    
    # Simulate some predictions and outcomes
    print("\n1. Simulating predictions and learning...")
    
    # Create model weight
    if "agent_25_chronos" not in engine._model_weights:
        engine._model_weights["agent_25_chronos"] = ModelWeight(model_source="agent_25_chronos")
    
    mw = engine._model_weights["agent_25_chronos"]
    
    # Simulate good predictions
    for i in range(5):
        old_weight = mw.weight
        mw.update_from_prediction(
            was_correct=True,
            confidence=0.8,
            prediction_error=3.0 + i * 0.5
        )
        print(f"   Correct prediction {i+1}: weight {old_weight:.3f} -> {mw.weight:.3f}")
    
    # Simulate some bad predictions
    for i in range(2):
        old_weight = mw.weight
        mw.update_from_prediction(
            was_correct=False,
            confidence=0.7,
            prediction_error=8.0
        )
        print(f"   Wrong prediction: weight {old_weight:.3f} -> {mw.weight:.3f}")
    
    # Test weighted signal
    print("\n2. Weighted Signal Calculation:")
    signals = [
        ("agent_22_sentiment", 0.7, 0.85),
        ("agent_23_social", 0.4, 0.72),
        ("agent_25_chronos", 0.8, 0.90),
    ]
    
    # Add default weights for other agents
    for source, _, _ in signals:
        if source not in engine._model_weights:
            engine._model_weights[source] = ModelWeight(model_source=source)
    
    weighted_signal, combined_conf = engine.get_weighted_signal(signals)
    print(f"   Input signals: {signals}")
    print(f"   Weighted signal: {weighted_signal:.3f}")
    print(f"   Combined confidence: {combined_conf:.3f}")
    
    # Test prediction range
    print("\n3. Prediction Range Calibration:")
    low, high = engine.get_prediction_range("QBTS", 4.50, "eod", 0.68)
    print(f"   Predicted price: $4.50")
    print(f"   68% confidence range: ${low:.2f} - ${high:.2f}")
    
    low95, high95 = engine.get_prediction_range("QBTS", 4.50, "eod", 0.95)
    print(f"   95% confidence range: ${low95:.2f} - ${high95:.2f}")
    
    # Test action decision
    print("\n4. Action Decision:")
    action, strength, adj_conf = engine.should_take_action("sentiment", 0.75, 0.85)
    print(f"   Signal: sentiment=0.75, confidence=0.85")
    print(f"   Decision: {action} ({strength}), adjusted_conf={adj_conf:.3f}")
    
    # Stats
    print("\n5. Learning Engine Stats:")
    stats = engine.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Save state
    engine._save_state()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
