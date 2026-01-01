"""
Agent 92: Performance Monitor
==============================
Tracks agent performance over time and detects drift/degradation.

Features:
- Real-time performance metrics collection
- Statistical drift detection (KS test, PSI)
- Rolling window analysis
- Alert generation for orchestrator

Created: 2026-01-01
"""

import logging
import sqlite3
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics tracked."""
    ACCURACY = "accuracy"
    F1_SCORE = "f1_score"
    PRECISION = "precision"
    RECALL = "recall"
    MAE = "mae"
    RMSE = "rmse"
    SHARPE = "sharpe"
    DRAWDOWN = "drawdown"
    LATENCY = "latency"
    CONFIDENCE = "confidence"


@dataclass
class PerformanceMetric:
    """Single performance measurement."""
    agent_id: str
    model_name: str
    metric_type: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "model_name": self.model_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class DriftAlert:
    """Alert for detected drift or degradation."""
    agent_id: str
    metric_type: str
    level: AlertLevel
    message: str
    baseline_value: float
    current_value: float
    drift_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "metric_type": self.metric_type,
            "level": self.level.value,
            "message": self.message,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "drift_score": self.drift_score,
            "timestamp": self.timestamp.isoformat()
        }


class MetricsDatabase:
    """SQLite database for metrics storage."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "outputs" / "data" / "metrics.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    baseline_value REAL,
                    current_value REAL,
                    drift_score REAL,
                    timestamp TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_agent 
                ON metrics(agent_id, metric_type, timestamp)
            """)
            
            conn.commit()
    
    def store_metric(self, metric: PerformanceMetric):
        """Store a single metric."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (agent_id, model_name, metric_type, value, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.agent_id,
                metric.model_name,
                metric.metric_type,
                metric.value,
                metric.timestamp.isoformat(),
                json.dumps(metric.metadata)
            ))
            conn.commit()
    
    def store_alert(self, alert: DriftAlert):
        """Store an alert."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alerts (agent_id, metric_type, level, message, 
                                    baseline_value, current_value, drift_score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.agent_id,
                alert.metric_type,
                alert.level.value,
                alert.message,
                alert.baseline_value,
                alert.current_value,
                alert.drift_score,
                alert.timestamp.isoformat()
            ))
            conn.commit()
    
    def get_metrics(
        self,
        agent_id: str,
        metric_type: str,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[PerformanceMetric]:
        """Retrieve metrics for an agent."""
        query = """
            SELECT agent_id, model_name, metric_type, value, timestamp, metadata
            FROM metrics
            WHERE agent_id = ? AND metric_type = ?
        """
        params = [agent_id, metric_type]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            metrics = []
            for row in cursor:
                metrics.append(PerformanceMetric(
                    agent_id=row['agent_id'],
                    model_name=row['model_name'],
                    metric_type=row['metric_type'],
                    value=row['value'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ))
            
            return metrics
    
    def get_recent_alerts(self, agent_id: str = None, limit: int = 50) -> List[DriftAlert]:
        """Get recent alerts."""
        query = "SELECT * FROM alerts"
        params = []
        
        if agent_id:
            query += " WHERE agent_id = ?"
            params.append(agent_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            alerts = []
            for row in cursor:
                alerts.append(DriftAlert(
                    agent_id=row['agent_id'],
                    metric_type=row['metric_type'],
                    level=AlertLevel(row['level']),
                    message=row['message'],
                    baseline_value=row['baseline_value'],
                    current_value=row['current_value'],
                    drift_score=row['drift_score'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                ))
            
            return alerts


class DriftDetector:
    """Statistical drift detection algorithms."""
    
    def __init__(
        self,
        baseline_window: int = 30,  # Days for baseline
        test_window: int = 7,  # Days for recent data
        significance_level: float = 0.05
    ):
        self.baseline_window = baseline_window
        self.test_window = test_window
        self.significance_level = significance_level
    
    def ks_test(
        self,
        baseline_values: np.ndarray,
        recent_values: np.ndarray
    ) -> Tuple[float, float, bool]:
        """
        Kolmogorov-Smirnov test for distribution drift.
        
        Returns:
            (statistic, p_value, is_drifted)
        """
        if len(baseline_values) < 5 or len(recent_values) < 5:
            return 0.0, 1.0, False
        
        statistic, p_value = stats.ks_2samp(baseline_values, recent_values)
        is_drifted = p_value < self.significance_level
        
        return float(statistic), float(p_value), is_drifted
    
    def psi(
        self,
        baseline_values: np.ndarray,
        recent_values: np.ndarray,
        buckets: int = 10
    ) -> Tuple[float, bool]:
        """
        Population Stability Index (PSI).
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.2: Moderate change
        PSI >= 0.2: Significant change
        
        Returns:
            (psi_score, is_drifted)
        """
        if len(baseline_values) < 10 or len(recent_values) < 10:
            return 0.0, False
        
        # Create buckets from baseline
        breakpoints = np.percentile(
            baseline_values,
            np.linspace(0, 100, buckets + 1)
        )
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf
        
        # Calculate bucket frequencies
        baseline_bins = np.histogram(baseline_values, bins=breakpoints)[0]
        recent_bins = np.histogram(recent_values, bins=breakpoints)[0]
        
        # Convert to percentages (add small epsilon to avoid log(0))
        epsilon = 1e-10
        baseline_pct = baseline_bins / len(baseline_values) + epsilon
        recent_pct = recent_bins / len(recent_values) + epsilon
        
        # Calculate PSI
        psi_score = np.sum((recent_pct - baseline_pct) * np.log(recent_pct / baseline_pct))
        is_drifted = psi_score >= 0.2
        
        return float(psi_score), is_drifted
    
    def rolling_mean_drift(
        self,
        values: np.ndarray,
        baseline_mean: float,
        threshold_pct: float = 0.10
    ) -> Tuple[float, float, bool]:
        """
        Simple rolling mean comparison.
        
        Returns:
            (current_mean, drift_pct, is_drifted)
        """
        if len(values) == 0:
            return 0.0, 0.0, False
        
        current_mean = np.mean(values)
        
        if baseline_mean == 0:
            drift_pct = 0.0 if current_mean == 0 else 1.0
        else:
            drift_pct = (current_mean - baseline_mean) / abs(baseline_mean)
        
        is_drifted = abs(drift_pct) > threshold_pct
        
        return float(current_mean), float(drift_pct), is_drifted


class PerformanceMonitor:
    """
    Central performance monitoring for all agents.
    
    Usage:
        monitor = PerformanceMonitor()
        
        # Record a metric
        monitor.record_metric(
            agent_id="22_psychology",
            model_name="finbert",
            metric_type="accuracy",
            value=0.87
        )
        
        # Check for drift
        alerts = monitor.detect_drift("22_psychology")
    """
    
    def __init__(
        self,
        db_path: str = None,
        alert_callback: callable = None
    ):
        self.db = MetricsDatabase(db_path)
        self.drift_detector = DriftDetector()
        self.alert_callback = alert_callback
        
        # Thresholds per metric type
        self.thresholds = {
            MetricType.ACCURACY.value: {"warn": 0.05, "critical": 0.10},
            MetricType.F1_SCORE.value: {"warn": 0.05, "critical": 0.10},
            MetricType.MAE.value: {"warn": 0.15, "critical": 0.25},  # Inverted (higher is worse)
            MetricType.RMSE.value: {"warn": 0.15, "critical": 0.25},
            MetricType.SHARPE.value: {"warn": 0.20, "critical": 0.40},
            MetricType.DRAWDOWN.value: {"warn": 0.05, "critical": 0.10},
            MetricType.LATENCY.value: {"warn": 0.50, "critical": 1.00},
            MetricType.CONFIDENCE.value: {"warn": 0.10, "critical": 0.20},
        }
        
        # Baseline cache
        self._baseline_cache: Dict[str, Dict[str, float]] = {}
        
        logger.info("PerformanceMonitor initialized")
    
    def record_metric(
        self,
        agent_id: str,
        model_name: str,
        metric_type: str,
        value: float,
        metadata: Dict[str, Any] = None
    ) -> PerformanceMetric:
        """Record a performance metric."""
        metric = PerformanceMetric(
            agent_id=agent_id,
            model_name=model_name,
            metric_type=metric_type,
            value=value,
            metadata=metadata or {}
        )
        
        self.db.store_metric(metric)
        logger.debug(f"Recorded {metric_type}={value:.4f} for {agent_id}/{model_name}")
        
        return metric
    
    def get_baseline(
        self,
        agent_id: str,
        metric_type: str,
        days: int = 30
    ) -> Tuple[float, np.ndarray]:
        """Get baseline mean and values for an agent/metric."""
        cache_key = f"{agent_id}:{metric_type}"
        
        # Check cache (refresh daily)
        if cache_key in self._baseline_cache:
            cached = self._baseline_cache[cache_key]
            if (datetime.now() - cached.get("timestamp", datetime.min)).days < 1:
                return cached["mean"], cached["values"]
        
        # Query database
        start_time = datetime.now() - timedelta(days=days)
        metrics = self.db.get_metrics(
            agent_id=agent_id,
            metric_type=metric_type,
            start_time=start_time
        )
        
        if not metrics:
            return 0.0, np.array([])
        
        values = np.array([m.value for m in metrics])
        mean = float(np.mean(values))
        
        # Cache result
        self._baseline_cache[cache_key] = {
            "mean": mean,
            "values": values,
            "timestamp": datetime.now()
        }
        
        return mean, values
    
    def detect_drift(
        self,
        agent_id: str,
        metric_types: List[str] = None
    ) -> List[DriftAlert]:
        """
        Detect performance drift for an agent.
        
        Returns list of alerts for any detected drift.
        """
        if metric_types is None:
            metric_types = [m.value for m in MetricType]
        
        alerts = []
        
        for metric_type in metric_types:
            # Get baseline and recent values
            baseline_mean, baseline_values = self.get_baseline(
                agent_id, metric_type, days=30
            )
            
            if len(baseline_values) < 10:
                continue  # Not enough data
            
            # Get recent values
            recent_start = datetime.now() - timedelta(days=7)
            recent_metrics = self.db.get_metrics(
                agent_id=agent_id,
                metric_type=metric_type,
                start_time=recent_start
            )
            
            if len(recent_metrics) < 3:
                continue  # Not enough recent data
            
            recent_values = np.array([m.value for m in recent_metrics])
            recent_mean = float(np.mean(recent_values))
            
            # Run drift detection
            psi_score, psi_drifted = self.drift_detector.psi(
                baseline_values, recent_values
            )
            
            ks_stat, ks_pvalue, ks_drifted = self.drift_detector.ks_test(
                baseline_values, recent_values
            )
            
            _, drift_pct, mean_drifted = self.drift_detector.rolling_mean_drift(
                recent_values, baseline_mean
            )
            
            # Determine alert level
            thresholds = self.thresholds.get(metric_type, {"warn": 0.10, "critical": 0.20})
            
            # For metrics where higher is worse (MAE, RMSE, etc.)
            is_worse = drift_pct > 0 if metric_type in ["mae", "rmse", "drawdown", "latency"] else drift_pct < 0
            
            if psi_drifted or ks_drifted or (mean_drifted and is_worse):
                # Determine severity
                if psi_score >= 0.25 or abs(drift_pct) > thresholds["critical"]:
                    level = AlertLevel.CRITICAL
                elif psi_score >= 0.1 or abs(drift_pct) > thresholds["warn"]:
                    level = AlertLevel.WARNING
                else:
                    level = AlertLevel.INFO
                
                alert = DriftAlert(
                    agent_id=agent_id,
                    metric_type=metric_type,
                    level=level,
                    message=f"Performance drift detected: {metric_type} changed by {drift_pct:.1%} (PSI={psi_score:.3f})",
                    baseline_value=baseline_mean,
                    current_value=recent_mean,
                    drift_score=psi_score
                )
                
                alerts.append(alert)
                self.db.store_alert(alert)
                
                logger.warning(f"Drift alert: {alert.message}")
                
                # Callback if configured
                if self.alert_callback:
                    self.alert_callback(alert)
        
        return alerts
    
    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get performance summary for an agent."""
        summary = {
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {},
            "alerts": []
        }
        
        # Get latest metrics
        for metric_type in MetricType:
            metrics = self.db.get_metrics(
                agent_id=agent_id,
                metric_type=metric_type.value,
                limit=10
            )
            
            if metrics:
                values = [m.value for m in metrics]
                summary["metrics"][metric_type.value] = {
                    "latest": metrics[0].value,
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "count": len(values)
                }
        
        # Get recent alerts
        alerts = self.db.get_recent_alerts(agent_id=agent_id, limit=10)
        summary["alerts"] = [a.to_dict() for a in alerts]
        
        return summary
    
    def generate_report(self, agent_ids: List[str] = None) -> str:
        """Generate a performance report."""
        if agent_ids is None:
            agent_ids = ["22_psychology", "23_social", "24_politics", "25_market", "11_analyst"]
        
        report = f"""
========================================
AGENT PERFORMANCE REPORT
========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        for agent_id in agent_ids:
            summary = self.get_agent_summary(agent_id)
            
            report += f"""
{agent_id.upper()}
{'-' * 40}
"""
            
            if summary["metrics"]:
                for metric, data in summary["metrics"].items():
                    report += f"  {metric}: {data['latest']:.4f} (avg: {data['mean']:.4f})\n"
            else:
                report += "  No metrics recorded\n"
            
            if summary["alerts"]:
                report += f"\n  Recent Alerts ({len(summary['alerts'])}):\n"
                for alert in summary["alerts"][:3]:
                    report += f"    [{alert['level']}] {alert['message']}\n"
        
        report += "\n" + "=" * 40
        
        return report


def main():
    """Demo performance monitor functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("Agent 92 - Performance Monitor Demo")
    print("="*60)
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Simulate metrics for different agents
    agents = [
        ("22_psychology", "finbert", MetricType.ACCURACY.value),
        ("23_social", "fintwitbert", MetricType.F1_SCORE.value),
        ("24_politics", "bart-mnli", MetricType.ACCURACY.value),
        ("25_market", "chronos-t5", MetricType.MAE.value),
        ("11_analyst", "pyportfolioopt", MetricType.SHARPE.value),
    ]
    
    print("\n📊 Recording sample metrics...")
    
    # Record baseline metrics (simulating 30 days)
    np.random.seed(42)
    
    for agent_id, model, metric_type in agents:
        # Baseline values
        if metric_type in [MetricType.MAE.value, MetricType.RMSE.value]:
            base_value = 0.15  # Lower is better
            variance = 0.02
        elif metric_type == MetricType.SHARPE.value:
            base_value = 1.2
            variance = 0.3
        else:
            base_value = 0.85  # Accuracy/F1
            variance = 0.03
        
        # Simulate 30 days of baseline data
        for i in range(30):
            value = base_value + np.random.normal(0, variance)
            value = max(0, min(1, value)) if "accuracy" in metric_type or "f1" in metric_type else value
            
            monitor.record_metric(
                agent_id=agent_id,
                model_name=model,
                metric_type=metric_type,
                value=value,
                metadata={"day": i}
            )
        
        # Simulate some drift for Agent 22 (degraded performance)
        if agent_id == "22_psychology":
            for i in range(7):
                value = base_value - 0.08 + np.random.normal(0, variance)  # 8% degradation
                monitor.record_metric(
                    agent_id=agent_id,
                    model_name=model,
                    metric_type=metric_type,
                    value=value,
                    metadata={"day": 30 + i, "drift_simulation": True}
                )
        
        print(f"  ✓ {agent_id}: recorded metrics")
    
    # Check for drift
    print("\n🔍 Checking for drift...")
    
    for agent_id, _, _ in agents:
        alerts = monitor.detect_drift(agent_id)
        
        if alerts:
            for alert in alerts:
                print(f"  ⚠️ {agent_id}: {alert.level.value.upper()} - {alert.message}")
        else:
            print(f"  ✓ {agent_id}: No drift detected")
    
    # Generate report
    print("\n" + monitor.generate_report())


if __name__ == "__main__":
    main()
