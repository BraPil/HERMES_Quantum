"""
MLFlow Integration for HERMES_Quantum
=====================================
Centralized experiment tracking, model versioning, and performance logging.

MLFlow handles:
- Experiment tracking (predictions, signals, decisions)
- Model registry (versioning our ML models)
- Metric logging (accuracy, alpha, returns)
- Artifact storage (model weights, reports)

Created: 2025-12-30
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import MLFlow, gracefully handle if not installed
try:
    import mlflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLFlow not installed. Tracking will be disabled. Run: pip install mlflow")


@dataclass
class HermesExperiment:
    """Configuration for a HERMES experiment."""
    name: str
    description: str
    tags: Dict[str, str]


# Define standard experiments
EXPERIMENTS = {
    "predictions": HermesExperiment(
        name="hermes-predictions",
        description="Track all prediction outcomes and accuracy",
        tags={"domain": "trading", "type": "predictions"}
    ),
    "signals": HermesExperiment(
        name="hermes-signals",
        description="Track agent signals and their effectiveness",
        tags={"domain": "trading", "type": "signals"}
    ),
    "decisions": HermesExperiment(
        name="hermes-decisions",
        description="Track trading decisions and P&L",
        tags={"domain": "trading", "type": "decisions"}
    ),
    "learning": HermesExperiment(
        name="hermes-learning",
        description="Track model weight adjustments and calibration",
        tags={"domain": "ml", "type": "learning"}
    ),
    "backtesting": HermesExperiment(
        name="hermes-backtesting",
        description="Backtest runs and performance metrics",
        tags={"domain": "trading", "type": "backtesting"}
    )
}


class MLFlowTracker:
    """
    Centralized MLFlow tracking for HERMES.
    
    Provides a simple interface for logging:
    - Predictions and their outcomes
    - Agent signals and effectiveness
    - Trading decisions and P&L
    - Model weight adjustments
    - Performance metrics over time
    
    Usage:
        tracker = get_mlflow_tracker()
        
        # Log a prediction
        with tracker.start_run(experiment="predictions"):
            tracker.log_prediction("QBTS", 5.50, 5.45, 0.85)
        
        # Log model metrics
        tracker.log_metrics({
            "accuracy_1h": 0.72,
            "accuracy_24h": 0.68,
            "alpha": 0.15
        })
    """
    
    def __init__(
        self,
        tracking_uri: str = None,
        artifact_location: str = None
    ):
        """
        Initialize MLFlow tracker.
        
        Args:
            tracking_uri: MLFlow server URI or local path
            artifact_location: Where to store artifacts
        """
        self.enabled = MLFLOW_AVAILABLE
        self._active_run = None
        self._client = None
        
        if not self.enabled:
            logger.warning("MLFlow not available. All tracking calls will be no-ops.")
            return
        
        # Set tracking URI - use SQLite backend as recommended
        if tracking_uri is None:
            # Default to SQLite database in outputs
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "outputs", "data", "mlflow.db"
            )
            db_path = os.path.abspath(db_path)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            tracking_uri = f"sqlite:///{db_path}"
        
        mlflow.set_tracking_uri(tracking_uri)
        
        if artifact_location is None:
            artifact_location = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "outputs", "mlflow_artifacts"
            )
            artifact_location = os.path.abspath(artifact_location)
        os.makedirs(artifact_location, exist_ok=True)
        
        self._tracking_uri = tracking_uri
        self._artifact_location = artifact_location
        self._client = MlflowClient()
        
        # Ensure experiments exist
        self._ensure_experiments()
        
        logger.info(f"MLFlow tracker initialized. URI: {tracking_uri}")
    
    def _ensure_experiments(self) -> None:
        """Create standard experiments if they don't exist."""
        if not self.enabled:
            return
            
        for exp_key, exp_config in EXPERIMENTS.items():
            try:
                exp = mlflow.get_experiment_by_name(exp_config.name)
                if exp is None:
                    exp_id = mlflow.create_experiment(
                        exp_config.name,
                        tags=exp_config.tags
                    )
                    logger.info(f"Created experiment: {exp_config.name} (id={exp_id})")
            except Exception as e:
                logger.warning(f"Could not create experiment {exp_config.name}: {e}")
    
    @contextmanager
    def start_run(
        self,
        experiment: str = "predictions",
        run_name: str = None,
        tags: Dict[str, str] = None,
        nested: bool = False
    ):
        """
        Start an MLFlow run context.
        
        Args:
            experiment: Experiment key from EXPERIMENTS
            run_name: Optional name for this run
            tags: Additional tags for the run
            nested: Whether this is a nested run
            
        Yields:
            The active run (or None if MLFlow disabled)
        """
        if not self.enabled:
            yield None
            return
        
        exp_config = EXPERIMENTS.get(experiment)
        if exp_config is None:
            logger.warning(f"Unknown experiment: {experiment}. Using 'predictions'.")
            exp_config = EXPERIMENTS["predictions"]
        
        mlflow.set_experiment(exp_config.name)
        
        if run_name is None:
            run_name = f"{experiment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        all_tags = {**exp_config.tags, **(tags or {})}
        
        try:
            with mlflow.start_run(run_name=run_name, tags=all_tags, nested=nested) as run:
                self._active_run = run
                yield run
        finally:
            self._active_run = None
    
    def log_params(self, params: Dict[str, Any]) -> None:
        """Log parameters for the current run."""
        if not self.enabled or self._active_run is None:
            return
        
        # MLFlow params must be strings and limited in length
        for key, value in params.items():
            try:
                str_value = str(value)[:250]  # MLFlow limit
                mlflow.log_param(key, str_value)
            except Exception as e:
                logger.warning(f"Failed to log param {key}: {e}")
    
    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: int = None
    ) -> None:
        """
        Log metrics for the current run.
        
        Args:
            metrics: Dict of metric name -> value
            step: Optional step number for time series metrics
        """
        if not self.enabled:
            return
        
        for key, value in metrics.items():
            try:
                if step is not None:
                    mlflow.log_metric(key, float(value), step=step)
                else:
                    mlflow.log_metric(key, float(value))
            except Exception as e:
                logger.warning(f"Failed to log metric {key}: {e}")
    
    def log_prediction(
        self,
        ticker: str,
        predicted_value: float,
        actual_value: float = None,
        confidence: float = None,
        prediction_type: str = "price",
        model_source: str = "unknown",
        horizon_minutes: int = None,
        step: int = None
    ) -> None:
        """
        Log a prediction and optionally its outcome.
        
        Args:
            ticker: Stock ticker
            predicted_value: The predicted value
            actual_value: The actual value (if known)
            confidence: Confidence level (0-1)
            prediction_type: Type of prediction
            model_source: Which model made the prediction
            horizon_minutes: Forecast horizon
            step: Step number for time series
        """
        if not self.enabled:
            return
        
        params = {
            "ticker": ticker,
            "prediction_type": prediction_type,
            "model_source": model_source
        }
        if horizon_minutes:
            params["horizon_minutes"] = horizon_minutes
        
        metrics = {
            "predicted_value": predicted_value
        }
        if confidence is not None:
            metrics["confidence"] = confidence
        if actual_value is not None:
            metrics["actual_value"] = actual_value
            metrics["error"] = predicted_value - actual_value
            metrics["abs_error"] = abs(predicted_value - actual_value)
            if actual_value != 0:
                metrics["pct_error"] = abs(predicted_value - actual_value) / abs(actual_value)
        
        if self._active_run:
            self.log_params(params)
        self.log_metrics(metrics, step=step)
    
    def log_signal(
        self,
        ticker: str,
        signal_type: str,
        signal_value: float,
        confidence: float,
        agent_source: str,
        recommended_action: str = None,
        reasoning: str = None,
        step: int = None
    ) -> None:
        """
        Log an agent signal.
        
        Args:
            ticker: Stock ticker
            signal_type: Type of signal (sentiment, social, policy, forecast)
            signal_value: Signal value (-1 to 1 for sentiment, etc.)
            confidence: Confidence level (0-1)
            agent_source: Which agent generated the signal
            recommended_action: BUY/SELL/HOLD
            reasoning: Explanation for the signal
            step: Step number
        """
        if not self.enabled:
            return
        
        metrics = {
            f"signal_{signal_type}": signal_value,
            f"confidence_{signal_type}": confidence
        }
        
        if self._active_run:
            params = {
                "ticker": ticker,
                "signal_type": signal_type,
                "agent_source": agent_source
            }
            if recommended_action:
                params["recommended_action"] = recommended_action
            if reasoning:
                params["reasoning"] = reasoning[:250]
            self.log_params(params)
        
        self.log_metrics(metrics, step=step)
    
    def log_decision(
        self,
        ticker: str,
        action: str,
        price: float,
        quantity: int,
        confidence: float,
        reasoning: str = None,
        pnl: float = None,
        step: int = None
    ) -> None:
        """
        Log a trading decision.
        
        Args:
            ticker: Stock ticker
            action: BUY/SELL/HOLD
            price: Entry/exit price
            quantity: Number of shares
            confidence: Decision confidence
            reasoning: Explanation
            pnl: Profit/loss if known
            step: Step number
        """
        if not self.enabled:
            return
        
        metrics = {
            "decision_price": price,
            "decision_quantity": quantity,
            "decision_confidence": confidence
        }
        if pnl is not None:
            metrics["pnl"] = pnl
        
        if self._active_run:
            self.log_params({
                "ticker": ticker,
                "action": action,
                "reasoning": (reasoning or "")[:250]
            })
        
        self.log_metrics(metrics, step=step)
    
    def log_model_weights(
        self,
        model_weights: Dict[str, float],
        step: int = None
    ) -> None:
        """
        Log current model weights from the learning engine.
        
        Args:
            model_weights: Dict of model_source -> weight
            step: Step number
        """
        if not self.enabled:
            return
        
        metrics = {f"weight_{k}": v for k, v in model_weights.items()}
        self.log_metrics(metrics, step=step)
    
    def log_accuracy_metrics(
        self,
        accuracy_1h: float = None,
        accuracy_24h: float = None,
        accuracy_7d: float = None,
        accuracy_28d: float = None,
        accuracy_ytd: float = None,
        alpha: float = None,
        sharpe: float = None,
        step: int = None
    ) -> None:
        """
        Log accuracy metrics across timeframes.
        
        Args:
            accuracy_*: Accuracy for different timeframes
            alpha: Current alpha vs benchmark
            sharpe: Sharpe ratio
            step: Step number
        """
        if not self.enabled:
            return
        
        metrics = {}
        if accuracy_1h is not None:
            metrics["accuracy_1h"] = accuracy_1h
        if accuracy_24h is not None:
            metrics["accuracy_24h"] = accuracy_24h
        if accuracy_7d is not None:
            metrics["accuracy_7d"] = accuracy_7d
        if accuracy_28d is not None:
            metrics["accuracy_28d"] = accuracy_28d
        if accuracy_ytd is not None:
            metrics["accuracy_ytd"] = accuracy_ytd
        if alpha is not None:
            metrics["alpha"] = alpha
        if sharpe is not None:
            metrics["sharpe"] = sharpe
        
        self.log_metrics(metrics, step=step)
    
    def log_artifact(
        self,
        local_path: str,
        artifact_path: str = None
    ) -> None:
        """
        Log an artifact (file) to MLFlow.
        
        Args:
            local_path: Path to local file
            artifact_path: Destination path in artifact store
        """
        if not self.enabled or self._active_run is None:
            return
        
        try:
            mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.warning(f"Failed to log artifact {local_path}: {e}")
    
    def log_dict(
        self,
        dictionary: Dict[str, Any],
        artifact_file: str
    ) -> None:
        """
        Log a dictionary as JSON artifact.
        
        Args:
            dictionary: Dict to save
            artifact_file: Filename for the artifact
        """
        if not self.enabled or self._active_run is None:
            return
        
        try:
            mlflow.log_dict(dictionary, artifact_file)
        except Exception as e:
            logger.warning(f"Failed to log dict to {artifact_file}: {e}")
    
    def register_model(
        self,
        model_uri: str,
        name: str,
        tags: Dict[str, str] = None
    ) -> Optional[str]:
        """
        Register a model in the MLFlow model registry.
        
        Args:
            model_uri: URI of the logged model
            name: Name for the registered model
            tags: Optional tags
            
        Returns:
            Model version or None
        """
        if not self.enabled:
            return None
        
        try:
            result = mlflow.register_model(model_uri, name, tags=tags)
            return result.version
        except Exception as e:
            logger.warning(f"Failed to register model {name}: {e}")
            return None
    
    def get_best_run(
        self,
        experiment: str,
        metric: str,
        maximize: bool = True,
        filter_string: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best run from an experiment by metric.
        
        Args:
            experiment: Experiment key
            metric: Metric to optimize
            maximize: Whether to maximize (True) or minimize (False)
            filter_string: Optional filter
            
        Returns:
            Best run info or None
        """
        if not self.enabled or self._client is None:
            return None
        
        exp_config = EXPERIMENTS.get(experiment)
        if exp_config is None:
            return None
        
        try:
            exp = mlflow.get_experiment_by_name(exp_config.name)
            if exp is None:
                return None
            
            order = "DESC" if maximize else "ASC"
            runs = self._client.search_runs(
                experiment_ids=[exp.experiment_id],
                filter_string=filter_string,
                order_by=[f"metrics.{metric} {order}"],
                max_results=1
            )
            
            if runs:
                run = runs[0]
                return {
                    "run_id": run.info.run_id,
                    "metrics": run.data.metrics,
                    "params": run.data.params,
                    "tags": run.data.tags
                }
            return None
        except Exception as e:
            logger.warning(f"Failed to get best run: {e}")
            return None


# Singleton instance
_tracker_instance: Optional[MLFlowTracker] = None


def get_mlflow_tracker() -> MLFlowTracker:
    """Get the singleton MLFlow tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MLFlowTracker()
    return _tracker_instance


def reset_mlflow_tracker() -> None:
    """Reset the singleton tracker (mainly for testing)."""
    global _tracker_instance
    _tracker_instance = None


# Decorator for tracking function calls
def track_prediction(
    experiment: str = "predictions",
    ticker_param: str = "ticker",
    value_param: str = "predicted_value"
):
    """
    Decorator to automatically track predictions.
    
    Usage:
        @track_prediction()
        def predict_price(ticker: str) -> float:
            return 5.50
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            tracker = get_mlflow_tracker()
            if tracker.enabled:
                # Try to extract ticker and value
                ticker = kwargs.get(ticker_param, "unknown")
                
                with tracker.start_run(experiment=experiment):
                    if isinstance(result, (int, float)):
                        tracker.log_prediction(ticker, float(result))
                    elif isinstance(result, dict):
                        tracker.log_prediction(
                            ticker,
                            result.get("predicted_value", 0),
                            confidence=result.get("confidence")
                        )
            
            return result
        return wrapper
    return decorator


def track_signal(experiment: str = "signals"):
    """
    Decorator to automatically track signals.
    
    Usage:
        @track_signal()
        def analyze_sentiment(ticker: str) -> dict:
            return {"signal": 0.8, "confidence": 0.9}
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            tracker = get_mlflow_tracker()
            if tracker.enabled and isinstance(result, dict):
                with tracker.start_run(experiment=experiment):
                    tracker.log_signal(
                        ticker=result.get("ticker", "unknown"),
                        signal_type=result.get("type", "unknown"),
                        signal_value=result.get("signal", 0),
                        confidence=result.get("confidence", 0),
                        agent_source=func.__module__
                    )
            
            return result
        return wrapper
    return decorator
