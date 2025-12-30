"""
HERMES_Quantum Prediction Tracker
=================================
Stores predictions for later comparison with actuals.
Enables the real-time learning component (Agent 92).

This module tracks:
- Price predictions (5-min, 30-min, 2-hour, end-of-day)
- Direction predictions (up/down)
- Signal accuracy (buy/sell success rate)
- Confidence calibration

Created: 2025-12-30
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .event_bus import (
    Event, EventBus, EventType, EventPriority,
    get_event_bus, publish_prediction
)

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of predictions we track."""
    PRICE_1MIN = "price_1min"
    PRICE_5MIN = "price_5min"
    PRICE_30MIN = "price_30min"
    PRICE_2HOUR = "price_2hour"
    PRICE_EOD = "price_eod"
    DIRECTION = "direction"          # Up/Down prediction
    SIGNAL_ACTION = "signal_action"  # Buy/Sell/Hold recommendation
    SENTIMENT = "sentiment"          # Sentiment prediction
    VOLATILITY = "volatility"        # Volatility prediction


class PredictionStatus(Enum):
    """Status of a prediction."""
    PENDING = "pending"      # Waiting for target time
    VALIDATED = "validated"  # Actual value received, error calculated
    EXPIRED = "expired"      # No actual value received in time
    CANCELLED = "cancelled"  # Prediction cancelled (e.g., market closed)


@dataclass
class Prediction:
    """A single prediction to be tracked and validated."""
    prediction_id: str
    ticker: str
    prediction_type: PredictionType
    predicted_value: float
    confidence: float
    target_time: datetime
    model_source: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Filled after validation
    actual_value: Optional[float] = None
    error: Optional[float] = None
    absolute_error: Optional[float] = None
    percentage_error: Optional[float] = None
    direction_correct: Optional[bool] = None
    validated_at: Optional[datetime] = None
    status: PredictionStatus = PredictionStatus.PENDING
    
    # Context at prediction time (for learning)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, actual_value: float, reference_value: float = None) -> None:
        """
        Validate the prediction against actual value.
        
        Args:
            actual_value: The actual observed value
            reference_value: Reference value for direction (e.g., price at prediction time)
        """
        self.actual_value = actual_value
        self.validated_at = datetime.now()
        self.status = PredictionStatus.VALIDATED
        
        # Calculate errors
        self.error = actual_value - self.predicted_value
        self.absolute_error = abs(self.error)
        
        if self.predicted_value != 0:
            self.percentage_error = (self.absolute_error / abs(self.predicted_value)) * 100
        else:
            self.percentage_error = 0.0
        
        # Direction accuracy (if we have reference)
        if reference_value is not None:
            predicted_direction = self.predicted_value > reference_value
            actual_direction = actual_value > reference_value
            self.direction_correct = predicted_direction == actual_direction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "prediction_id": self.prediction_id,
            "ticker": self.ticker,
            "prediction_type": self.prediction_type.value,
            "predicted_value": self.predicted_value,
            "confidence": self.confidence,
            "target_time": self.target_time.isoformat(),
            "model_source": self.model_source,
            "created_at": self.created_at.isoformat(),
            "actual_value": self.actual_value,
            "error": self.error,
            "absolute_error": self.absolute_error,
            "percentage_error": self.percentage_error,
            "direction_correct": self.direction_correct,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "status": self.status.value,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Prediction':
        """Create from dictionary."""
        pred = cls(
            prediction_id=data["prediction_id"],
            ticker=data["ticker"],
            prediction_type=PredictionType(data["prediction_type"]),
            predicted_value=data["predicted_value"],
            confidence=data["confidence"],
            target_time=datetime.fromisoformat(data["target_time"]),
            model_source=data["model_source"],
            created_at=datetime.fromisoformat(data["created_at"]),
            context=data.get("context", {})
        )
        
        # Fill validation data if present
        if data.get("actual_value") is not None:
            pred.actual_value = data["actual_value"]
            pred.error = data.get("error")
            pred.absolute_error = data.get("absolute_error")
            pred.percentage_error = data.get("percentage_error")
            pred.direction_correct = data.get("direction_correct")
            pred.status = PredictionStatus(data.get("status", "validated"))
            if data.get("validated_at"):
                pred.validated_at = datetime.fromisoformat(data["validated_at"])
        
        return pred


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for a specific timeframe."""
    timeframe: str
    total_predictions: int
    validated_predictions: int
    direction_accuracy: float  # % of correct up/down predictions
    mean_absolute_error: float  # MAPE
    mean_percentage_error: float
    confidence_calibration: float  # How well confidence matches accuracy
    signal_win_rate: float  # % of profitable signals
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "total_predictions": self.total_predictions,
            "validated_predictions": self.validated_predictions,
            "direction_accuracy": round(self.direction_accuracy, 2),
            "mean_absolute_error": round(self.mean_absolute_error, 4),
            "mean_percentage_error": round(self.mean_percentage_error, 2),
            "confidence_calibration": round(self.confidence_calibration, 2),
            "signal_win_rate": round(self.signal_win_rate, 2)
        }


class PredictionTracker:
    """
    Tracks predictions and calculates accuracy metrics.
    
    This is the core component for the real-time learning system.
    It stores predictions, validates them against actuals, and
    provides accuracy metrics across multiple timeframes.
    
    Features:
    - SQLite storage for persistence
    - Real-time accuracy calculation
    - Multi-timeframe metrics (1h, 24h, 7d, 28d, 6mo, YTD, 12mo, all-time)
    - Confidence calibration tracking
    - Model-specific performance tracking
    
    Usage:
        tracker = PredictionTracker()
        
        # Store a prediction
        pred_id = tracker.store_prediction(
            ticker="QBTS",
            prediction_type=PredictionType.PRICE_EOD,
            predicted_value=4.50,
            confidence=0.85,
            target_time=datetime.now() + timedelta(hours=4),
            model_source="agent_25_chronos"
        )
        
        # Later, validate against actual
        tracker.validate_prediction(pred_id, actual_value=4.42)
        
        # Get accuracy metrics
        metrics = tracker.get_accuracy_metrics("24h")
    """
    
    TIMEFRAMES = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "28d": timedelta(days=28),
        "6mo": timedelta(days=180),
        "YTD": None,  # Special handling
        "12mo": timedelta(days=365),
        "all": None  # No limit
    }
    
    def __init__(self, db_path: str = None):
        """
        Initialize the prediction tracker.
        
        Args:
            db_path: Path to SQLite database (default: outputs/data/predictions.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "outputs" / "data" / "predictions.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache for fast access
        self._pending_predictions: Dict[str, Prediction] = {}
        self._recent_validations: List[Prediction] = []
        self._max_recent = 1000
        
        # Initialize database
        self._init_db()
        
        # Subscribe to events
        self._setup_event_subscriptions()
        
        logger.info(f"PredictionTracker initialized with DB at {self.db_path}")
    
    def _init_db(self) -> None:
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                prediction_type TEXT NOT NULL,
                predicted_value REAL NOT NULL,
                confidence REAL NOT NULL,
                target_time TEXT NOT NULL,
                model_source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                actual_value REAL,
                error REAL,
                absolute_error REAL,
                percentage_error REAL,
                direction_correct INTEGER,
                validated_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                context TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_ticker 
            ON predictions(ticker)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_status 
            ON predictions(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_created 
            ON predictions(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_predictions_model 
            ON predictions(model_source)
        """)
        
        # Table for tracking model weights (for learning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_weights (
                model_source TEXT PRIMARY KEY,
                weight REAL NOT NULL DEFAULT 1.0,
                accuracy_7d REAL,
                accuracy_28d REAL,
                accuracy_all REAL,
                last_updated TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _setup_event_subscriptions(self) -> None:
        """Subscribe to relevant events from the event bus."""
        bus = get_event_bus()
        
        # Listen for prediction events
        bus.subscribe(EventType.LEARNING_PREDICTION_STORED, self._handle_prediction_event)
        bus.subscribe(EventType.LEARNING_ACTUAL_RECEIVED, self._handle_actual_event)
        
        # Listen for stock data updates (to validate predictions)
        bus.subscribe(EventType.DATA_STOCK_UPDATE, self._handle_stock_update)
    
    def _handle_prediction_event(self, event: Event) -> None:
        """Handle incoming prediction event."""
        data = event.data
        self.store_prediction(
            ticker=data["ticker"],
            prediction_type=PredictionType(data["prediction_type"]),
            predicted_value=data["predicted_value"],
            confidence=data["confidence"],
            target_time=datetime.fromisoformat(data["target_time"]),
            model_source=data.get("model_source", event.source),
            context=event.metadata
        )
    
    def _handle_actual_event(self, event: Event) -> None:
        """Handle incoming actual value event."""
        data = event.data
        prediction_id = data.get("prediction_id")
        if prediction_id:
            self.validate_prediction(
                prediction_id=prediction_id,
                actual_value=data["actual_value"],
                reference_value=data.get("reference_value")
            )
    
    def _handle_stock_update(self, event: Event) -> None:
        """Handle stock data update - validate any due predictions."""
        data = event.data
        ticker = data.get("ticker")
        current_price = data.get("price")
        
        if ticker and current_price:
            self._validate_due_predictions(ticker, current_price)
    
    def store_prediction(
        self,
        ticker: str,
        prediction_type: PredictionType,
        predicted_value: float,
        confidence: float,
        target_time: datetime,
        model_source: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Store a new prediction.
        
        Args:
            ticker: Stock ticker
            prediction_type: Type of prediction
            predicted_value: The predicted value
            confidence: Confidence level (0-1)
            target_time: When the prediction is for
            model_source: Which model made the prediction
            context: Additional context for learning
            
        Returns:
            prediction_id for later reference
        """
        import uuid
        prediction_id = str(uuid.uuid4())[:12]
        
        prediction = Prediction(
            prediction_id=prediction_id,
            ticker=ticker,
            prediction_type=prediction_type,
            predicted_value=predicted_value,
            confidence=confidence,
            target_time=target_time,
            model_source=model_source,
            context=context or {}
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions 
            (prediction_id, ticker, prediction_type, predicted_value, confidence,
             target_time, model_source, created_at, status, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction.prediction_id,
            prediction.ticker,
            prediction.prediction_type.value,
            prediction.predicted_value,
            prediction.confidence,
            prediction.target_time.isoformat(),
            prediction.model_source,
            prediction.created_at.isoformat(),
            prediction.status.value,
            json.dumps(prediction.context)
        ))
        
        conn.commit()
        conn.close()
        
        # Add to pending cache
        self._pending_predictions[prediction_id] = prediction
        
        logger.debug(f"Stored prediction {prediction_id} for {ticker}")
        
        return prediction_id
    
    def validate_prediction(
        self,
        prediction_id: str,
        actual_value: float,
        reference_value: float = None
    ) -> Optional[Prediction]:
        """
        Validate a prediction against the actual value.
        
        Args:
            prediction_id: ID of the prediction to validate
            actual_value: The actual observed value
            reference_value: Reference for direction calculation
            
        Returns:
            Validated prediction or None if not found
        """
        # Get prediction
        prediction = self._pending_predictions.get(prediction_id)
        
        if prediction is None:
            # Try loading from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM predictions WHERE prediction_id = ?",
                (prediction_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                logger.warning(f"Prediction {prediction_id} not found")
                return None
            
            prediction = self._row_to_prediction(row)
        
        # Validate
        prediction.validate(actual_value, reference_value)
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE predictions SET
                actual_value = ?,
                error = ?,
                absolute_error = ?,
                percentage_error = ?,
                direction_correct = ?,
                validated_at = ?,
                status = ?
            WHERE prediction_id = ?
        """, (
            prediction.actual_value,
            prediction.error,
            prediction.absolute_error,
            prediction.percentage_error,
            1 if prediction.direction_correct else 0 if prediction.direction_correct is not None else None,
            prediction.validated_at.isoformat() if prediction.validated_at else None,
            prediction.status.value,
            prediction_id
        ))
        
        conn.commit()
        conn.close()
        
        # Remove from pending, add to recent
        if prediction_id in self._pending_predictions:
            del self._pending_predictions[prediction_id]
        
        self._recent_validations.append(prediction)
        if len(self._recent_validations) > self._max_recent:
            self._recent_validations.pop(0)
        
        # Publish learning event
        get_event_bus().publish(
            event_type=EventType.LEARNING_ERROR_CALCULATED,
            source="prediction_tracker",
            data={
                "prediction_id": prediction_id,
                "ticker": prediction.ticker,
                "model_source": prediction.model_source,
                "error": prediction.error,
                "percentage_error": prediction.percentage_error,
                "direction_correct": prediction.direction_correct
            },
            priority=EventPriority.NORMAL
        )
        
        logger.debug(
            f"Validated prediction {prediction_id}: "
            f"predicted={prediction.predicted_value:.2f}, "
            f"actual={actual_value:.2f}, "
            f"error={prediction.percentage_error:.2f}%"
        )
        
        return prediction
    
    def _validate_due_predictions(self, ticker: str, current_price: float) -> int:
        """Validate all predictions that are due for a ticker."""
        now = datetime.now()
        validated = 0
        
        # Get pending predictions for this ticker that are due
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT prediction_id FROM predictions
            WHERE ticker = ? 
            AND status = 'pending'
            AND target_time <= ?
        """, (ticker, now.isoformat()))
        
        due_predictions = cursor.fetchall()
        conn.close()
        
        for (prediction_id,) in due_predictions:
            self.validate_prediction(prediction_id, current_price)
            validated += 1
        
        return validated
    
    def get_accuracy_metrics(
        self,
        timeframe: str = "24h",
        ticker: str = None,
        model_source: str = None,
        prediction_type: PredictionType = None
    ) -> AccuracyMetrics:
        """
        Calculate accuracy metrics for a specific timeframe.
        
        Args:
            timeframe: One of 1h, 24h, 7d, 28d, 6mo, YTD, 12mo, all
            ticker: Filter by ticker (optional)
            model_source: Filter by model (optional)
            prediction_type: Filter by type (optional)
            
        Returns:
            AccuracyMetrics object
        """
        # Calculate time range
        now = datetime.now()
        
        if timeframe == "YTD":
            start_time = datetime(now.year, 1, 1)
        elif timeframe == "all":
            start_time = datetime(2000, 1, 1)  # Effectively no limit
        else:
            delta = self.TIMEFRAMES.get(timeframe)
            if delta is None:
                delta = timedelta(hours=24)  # Default
            start_time = now - delta
        
        # Build query
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'validated' THEN 1 ELSE 0 END) as validated,
                AVG(CASE WHEN direction_correct = 1 THEN 100.0 ELSE 0.0 END) as direction_acc,
                AVG(absolute_error) as mae,
                AVG(percentage_error) as mape,
                AVG(confidence) as avg_confidence,
                AVG(CASE WHEN direction_correct = 1 THEN confidence ELSE NULL END) as confidence_when_right
            FROM predictions
            WHERE created_at >= ?
        """
        params = [start_time.isoformat()]
        
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)
        
        if model_source:
            query += " AND model_source = ?"
            params.append(model_source)
        
        if prediction_type:
            query += " AND prediction_type = ?"
            params.append(prediction_type.value)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        
        total = row[0] or 0
        validated = row[1] or 0
        direction_acc = row[2] or 0.0
        mae = row[3] or 0.0
        mape = row[4] or 0.0
        avg_confidence = row[5] or 0.0
        confidence_when_right = row[6] or 0.0
        
        # Confidence calibration: how well confidence matches actual accuracy
        # Perfect calibration = 1.0 (high confidence on correct predictions)
        if avg_confidence > 0 and direction_acc > 0:
            calibration = min(1.0, confidence_when_right / avg_confidence)
        else:
            calibration = 0.0
        
        # Signal win rate (placeholder - needs trading data)
        # For now, use direction accuracy as proxy
        signal_win_rate = direction_acc
        
        return AccuracyMetrics(
            timeframe=timeframe,
            total_predictions=total,
            validated_predictions=validated,
            direction_accuracy=direction_acc,
            mean_absolute_error=mae,
            mean_percentage_error=mape,
            confidence_calibration=calibration,
            signal_win_rate=signal_win_rate
        )
    
    def get_all_timeframe_metrics(
        self,
        ticker: str = None,
        model_source: str = None
    ) -> Dict[str, AccuracyMetrics]:
        """Get accuracy metrics for all standard timeframes."""
        return {
            tf: self.get_accuracy_metrics(tf, ticker, model_source)
            for tf in self.TIMEFRAMES.keys()
        }
    
    def get_model_performance(self) -> Dict[str, Dict[str, Any]]:
        """Get performance metrics for each model source."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT model_source FROM predictions
        """)
        models = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return {
            model: self.get_accuracy_metrics("28d", model_source=model).to_dict()
            for model in models
        }
    
    def get_pending_predictions(
        self,
        ticker: str = None,
        limit: int = 100
    ) -> List[Prediction]:
        """Get pending predictions awaiting validation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if ticker:
            cursor.execute("""
                SELECT * FROM predictions 
                WHERE status = 'pending' AND ticker = ?
                ORDER BY target_time ASC
                LIMIT ?
            """, (ticker, limit))
        else:
            cursor.execute("""
                SELECT * FROM predictions 
                WHERE status = 'pending'
                ORDER BY target_time ASC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_prediction(row) for row in rows]
    
    def _row_to_prediction(self, row: tuple) -> Prediction:
        """Convert database row to Prediction object."""
        return Prediction(
            prediction_id=row[0],
            ticker=row[1],
            prediction_type=PredictionType(row[2]),
            predicted_value=row[3],
            confidence=row[4],
            target_time=datetime.fromisoformat(row[5]),
            model_source=row[6],
            created_at=datetime.fromisoformat(row[7]),
            actual_value=row[8],
            error=row[9],
            absolute_error=row[10],
            percentage_error=row[11],
            direction_correct=bool(row[12]) if row[12] is not None else None,
            validated_at=datetime.fromisoformat(row[13]) if row[13] else None,
            status=PredictionStatus(row[14]),
            context=json.loads(row[15]) if row[15] else {}
        )
    
    def expire_old_predictions(self, hours_old: int = 24) -> int:
        """Mark old pending predictions as expired."""
        cutoff = datetime.now() - timedelta(hours=hours_old)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE predictions
            SET status = 'expired'
            WHERE status = 'pending'
            AND target_time < ?
        """, (cutoff.isoformat(),))
        
        expired = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Expired {expired} old predictions")
        return expired
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tracker statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'validated' THEN 1 ELSE 0 END) as validated,
                SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired,
                COUNT(DISTINCT ticker) as tickers,
                COUNT(DISTINCT model_source) as models
            FROM predictions
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            "total_predictions": row[0] or 0,
            "pending": row[1] or 0,
            "validated": row[2] or 0,
            "expired": row[3] or 0,
            "unique_tickers": row[4] or 0,
            "unique_models": row[5] or 0,
            "in_memory_pending": len(self._pending_predictions),
            "recent_validations": len(self._recent_validations)
        }


# Singleton instance
_tracker: Optional[PredictionTracker] = None


def get_prediction_tracker() -> PredictionTracker:
    """Get the global prediction tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = PredictionTracker()
    return _tracker


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate PredictionTracker functionality."""
    print("=" * 60)
    print("HERMES Prediction Tracker Demo")
    print("=" * 60)
    
    tracker = get_prediction_tracker()
    
    # Store some predictions
    print("\n1. Storing predictions...")
    
    pred1 = tracker.store_prediction(
        ticker="QBTS",
        prediction_type=PredictionType.PRICE_EOD,
        predicted_value=4.50,
        confidence=0.85,
        target_time=datetime.now() + timedelta(hours=4),
        model_source="agent_25_chronos",
        context={"market_regime": "bullish"}
    )
    print(f"   Stored prediction: {pred1}")
    
    pred2 = tracker.store_prediction(
        ticker="IONQ",
        prediction_type=PredictionType.DIRECTION,
        predicted_value=1.0,  # Up
        confidence=0.72,
        target_time=datetime.now() + timedelta(hours=1),
        model_source="agent_22_sentiment"
    )
    print(f"   Stored prediction: {pred2}")
    
    # Simulate validation
    print("\n2. Validating predictions...")
    
    validated = tracker.validate_prediction(pred1, actual_value=4.42, reference_value=4.30)
    if validated:
        print(f"   Validated {pred1}:")
        print(f"      Predicted: ${validated.predicted_value:.2f}")
        print(f"      Actual: ${validated.actual_value:.2f}")
        print(f"      Error: {validated.percentage_error:.2f}%")
        print(f"      Direction correct: {validated.direction_correct}")
    
    # Get metrics
    print("\n3. Accuracy Metrics (24h):")
    metrics = tracker.get_accuracy_metrics("24h")
    for key, value in metrics.to_dict().items():
        print(f"   {key}: {value}")
    
    # Get stats
    print("\n4. Tracker Stats:")
    stats = tracker.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
