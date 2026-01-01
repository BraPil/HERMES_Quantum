"""
Agent 99: Model Registry
=========================
Qlib-style model registry for versioning and deployment.

Features:
- Model versioning and metadata storage
- Artifact management
- Performance tracking integration
- Deployment recommendations

Created: 2026-01-01
"""

import logging
import sqlite3
import json
import hashlib
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model deployment status."""
    REGISTERED = "registered"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    """Model version metadata."""
    name: str
    version: str
    agent_id: str
    status: ModelStatus
    created_at: datetime
    updated_at: datetime
    
    # Model info
    model_type: str  # "transformer", "statistical", "ensemble"
    framework: str  # "huggingface", "sklearn", "pytorch"
    
    # Artifact paths
    artifact_path: Optional[str] = None
    config_path: Optional[str] = None
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Training info
    training_data: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        return f"{self.name}:{self.version}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "model_type": self.model_type,
            "framework": self.framework,
            "artifact_path": self.artifact_path,
            "config_path": self.config_path,
            "metrics": self.metrics,
            "training_data": self.training_data,
            "hyperparameters": self.hyperparameters,
            "description": self.description,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVersion":
        return cls(
            name=data["name"],
            version=data["version"],
            agent_id=data["agent_id"],
            status=ModelStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            model_type=data.get("model_type", "unknown"),
            framework=data.get("framework", "unknown"),
            artifact_path=data.get("artifact_path"),
            config_path=data.get("config_path"),
            metrics=data.get("metrics", {}),
            training_data=data.get("training_data", {}),
            hyperparameters=data.get("hyperparameters", {}),
            description=data.get("description", ""),
            tags=data.get("tags", [])
        )


class ModelRegistry:
    """
    Model version registry with artifact management.
    
    Usage:
        registry = ModelRegistry()
        
        # Register a new model
        version = registry.register_model(
            name="finbert",
            agent_id="22_psychology",
            model_type="transformer",
            framework="huggingface",
            metrics={"accuracy": 0.87, "f1": 0.85}
        )
        
        # Get latest model
        model = registry.get_model("finbert")
        
        # Promote to production
        registry.promote_model("finbert", version.version)
    """
    
    def __init__(
        self,
        db_path: str = None,
        artifact_dir: str = None
    ):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "outputs" / "data" / "model_registry.db"
        
        if artifact_dir is None:
            artifact_dir = Path(__file__).parent.parent.parent / "outputs" / "models"
        
        self.db_path = Path(db_path)
        self.artifact_dir = Path(artifact_dir)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_db()
        logger.info(f"ModelRegistry initialized at {self.db_path}")
    
    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'registered',
                    model_type TEXT,
                    framework TEXT,
                    artifact_path TEXT,
                    config_path TEXT,
                    metrics TEXT,
                    training_data TEXT,
                    hyperparameters TEXT,
                    description TEXT,
                    tags TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(name, version)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_name_version
                ON models(name, version)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_status
                ON models(status)
            """)
            
            conn.commit()
    
    def _generate_version(self, name: str) -> str:
        """Generate next version number."""
        versions = self.list_versions(name)
        
        if not versions:
            return "1.0.0"
        
        # Parse latest version
        latest = versions[0].version
        parts = latest.split(".")
        
        if len(parts) == 3:
            major, minor, patch = map(int, parts)
            return f"{major}.{minor}.{patch + 1}"
        
        return f"{latest}.1"
    
    def register_model(
        self,
        name: str,
        agent_id: str,
        model_type: str = "unknown",
        framework: str = "unknown",
        version: str = None,
        artifact_path: str = None,
        config_path: str = None,
        metrics: Dict[str, float] = None,
        training_data: Dict[str, Any] = None,
        hyperparameters: Dict[str, Any] = None,
        description: str = "",
        tags: List[str] = None
    ) -> ModelVersion:
        """Register a new model version."""
        if version is None:
            version = self._generate_version(name)
        
        now = datetime.now()
        
        model_version = ModelVersion(
            name=name,
            version=version,
            agent_id=agent_id,
            status=ModelStatus.REGISTERED,
            created_at=now,
            updated_at=now,
            model_type=model_type,
            framework=framework,
            artifact_path=artifact_path,
            config_path=config_path,
            metrics=metrics or {},
            training_data=training_data or {},
            hyperparameters=hyperparameters or {},
            description=description,
            tags=tags or []
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO models 
                (name, version, agent_id, status, model_type, framework,
                 artifact_path, config_path, metrics, training_data,
                 hyperparameters, description, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, version, agent_id, model_version.status.value,
                model_type, framework, artifact_path, config_path,
                json.dumps(metrics or {}),
                json.dumps(training_data or {}),
                json.dumps(hyperparameters or {}),
                description, json.dumps(tags or []),
                now.isoformat(), now.isoformat()
            ))
            conn.commit()
        
        logger.info(f"Registered model {name}:{version}")
        
        return model_version
    
    def get_model(
        self,
        name: str,
        version: str = None,
        status: ModelStatus = None
    ) -> Optional[ModelVersion]:
        """
        Get a specific model version.
        
        If version is None, returns latest version.
        If status is specified, returns latest version with that status.
        """
        query = "SELECT * FROM models WHERE name = ?"
        params = [name]
        
        if version:
            query += " AND version = ?"
            params.append(version)
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC LIMIT 1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_model(row)
    
    def _row_to_model(self, row: sqlite3.Row) -> ModelVersion:
        """Convert database row to ModelVersion."""
        return ModelVersion(
            name=row['name'],
            version=row['version'],
            agent_id=row['agent_id'],
            status=ModelStatus(row['status']),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            model_type=row['model_type'],
            framework=row['framework'],
            artifact_path=row['artifact_path'],
            config_path=row['config_path'],
            metrics=json.loads(row['metrics']) if row['metrics'] else {},
            training_data=json.loads(row['training_data']) if row['training_data'] else {},
            hyperparameters=json.loads(row['hyperparameters']) if row['hyperparameters'] else {},
            description=row['description'] or "",
            tags=json.loads(row['tags']) if row['tags'] else []
        )
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT DISTINCT name FROM models ORDER BY name")
            return [row[0] for row in cursor]
    
    def list_versions(
        self,
        name: str,
        status: ModelStatus = None
    ) -> List[ModelVersion]:
        """List all versions of a model."""
        query = "SELECT * FROM models WHERE name = ?"
        params = [name]
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            return [self._row_to_model(row) for row in cursor]
    
    def update_metrics(
        self,
        name: str,
        version: str,
        metrics: Dict[str, float]
    ):
        """Update performance metrics for a model version."""
        model = self.get_model(name, version)
        
        if not model:
            raise ValueError(f"Model {name}:{version} not found")
        
        # Merge metrics
        updated_metrics = {**model.metrics, **metrics}
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE models SET metrics = ?, updated_at = ?
                WHERE name = ? AND version = ?
            """, (
                json.dumps(updated_metrics),
                datetime.now().isoformat(),
                name, version
            ))
            conn.commit()
        
        logger.info(f"Updated metrics for {name}:{version}")
    
    def promote_model(
        self,
        name: str,
        version: str,
        target_status: ModelStatus = ModelStatus.PRODUCTION
    ):
        """Promote a model to staging or production."""
        # Demote current production version
        if target_status == ModelStatus.PRODUCTION:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE models SET status = ?, updated_at = ?
                    WHERE name = ? AND status = ?
                """, (
                    ModelStatus.ARCHIVED.value,
                    datetime.now().isoformat(),
                    name, ModelStatus.PRODUCTION.value
                ))
                conn.commit()
        
        # Promote specified version
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE models SET status = ?, updated_at = ?
                WHERE name = ? AND version = ?
            """, (
                target_status.value,
                datetime.now().isoformat(),
                name, version
            ))
            conn.commit()
        
        logger.info(f"Promoted {name}:{version} to {target_status.value}")
    
    def archive_model(self, name: str, version: str):
        """Archive a model version."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE models SET status = ?, updated_at = ?
                WHERE name = ? AND version = ?
            """, (
                ModelStatus.ARCHIVED.value,
                datetime.now().isoformat(),
                name, version
            ))
            conn.commit()
        
        logger.info(f"Archived {name}:{version}")
    
    def save_artifact(
        self,
        name: str,
        version: str,
        artifact_data: bytes,
        artifact_name: str = "model.bin"
    ) -> str:
        """Save model artifact to storage."""
        artifact_dir = self.artifact_dir / name / version
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_path = artifact_dir / artifact_name
        
        with open(artifact_path, 'wb') as f:
            f.write(artifact_data)
        
        # Update database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE models SET artifact_path = ?, updated_at = ?
                WHERE name = ? AND version = ?
            """, (
                str(artifact_path),
                datetime.now().isoformat(),
                name, version
            ))
            conn.commit()
        
        logger.info(f"Saved artifact for {name}:{version}")
        
        return str(artifact_path)
    
    def get_production_models(self) -> Dict[str, ModelVersion]:
        """Get all models currently in production."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM models WHERE status = ?
            """, (ModelStatus.PRODUCTION.value,))
            
            return {
                row['name']: self._row_to_model(row)
                for row in cursor
            }
    
    def compare_versions(
        self,
        name: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two model versions."""
        m1 = self.get_model(name, version1)
        m2 = self.get_model(name, version2)
        
        if not m1 or not m2:
            raise ValueError("One or both versions not found")
        
        comparison = {
            "name": name,
            "version1": version1,
            "version2": version2,
            "metrics_diff": {},
            "hyperparameters_diff": {}
        }
        
        # Compare metrics
        all_metrics = set(m1.metrics.keys()) | set(m2.metrics.keys())
        for metric in all_metrics:
            v1 = m1.metrics.get(metric, 0)
            v2 = m2.metrics.get(metric, 0)
            diff = v2 - v1
            pct = (diff / v1 * 100) if v1 != 0 else 0
            comparison["metrics_diff"][metric] = {
                "version1": v1,
                "version2": v2,
                "diff": diff,
                "pct_change": pct
            }
        
        # Compare hyperparameters
        all_hparams = set(m1.hyperparameters.keys()) | set(m2.hyperparameters.keys())
        for param in all_hparams:
            v1 = m1.hyperparameters.get(param)
            v2 = m2.hyperparameters.get(param)
            if v1 != v2:
                comparison["hyperparameters_diff"][param] = {
                    "version1": v1,
                    "version2": v2
                }
        
        return comparison
    
    def generate_report(self) -> str:
        """Generate registry status report."""
        models = self.list_models()
        
        report = f"""
{'='*50}
MODEL REGISTRY REPORT
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Models: {len(models)}

PRODUCTION MODELS
{'-'*50}"""
        
        production = self.get_production_models()
        if production:
            for name, model in production.items():
                report += f"""
{name}:{model.version}
  Agent: {model.agent_id}
  Framework: {model.framework}
  Metrics: {json.dumps(model.metrics, indent=4)}"""
        else:
            report += "\nNo models in production"
        
        report += f"""

ALL MODELS
{'-'*50}"""
        
        for name in models:
            versions = self.list_versions(name)
            report += f"\n{name}: {len(versions)} version(s)"
            for v in versions[:3]:  # Show latest 3
                status_icon = "🟢" if v.status == ModelStatus.PRODUCTION else (
                    "🟡" if v.status == ModelStatus.STAGING else "⚪"
                )
                report += f"\n  {status_icon} {v.version} ({v.status.value})"
        
        report += "\n" + "=" * 50
        
        return report


def main():
    """Demo model registry functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("="*60)
    print("Agent 99 - Model Registry Demo")
    print("="*60)
    
    # Initialize registry
    registry = ModelRegistry()
    
    # Register models for each agent
    print("\n📦 Registering models...")
    
    # Agent 22 - finBERT
    v1 = registry.register_model(
        name="finbert",
        agent_id="22_psychology",
        model_type="transformer",
        framework="huggingface",
        metrics={"accuracy": 0.85, "f1": 0.83},
        hyperparameters={"learning_rate": 2e-5, "batch_size": 16},
        description="ProsusAI/finbert for financial sentiment",
        tags=["sentiment", "nlp", "transformer"]
    )
    print(f"  ✓ Registered {v1.full_name}")
    
    # Register improved version
    v2 = registry.register_model(
        name="finbert",
        agent_id="22_psychology",
        model_type="transformer",
        framework="huggingface",
        metrics={"accuracy": 0.87, "f1": 0.86},
        hyperparameters={"learning_rate": 3e-5, "batch_size": 32},
        description="Fine-tuned finBERT for quantum stocks"
    )
    print(f"  ✓ Registered {v2.full_name}")
    
    # Agent 23 - FinTwitBERT
    registry.register_model(
        name="fintwitbert",
        agent_id="23_social",
        model_type="transformer",
        framework="huggingface",
        metrics={"accuracy": 0.82, "f1": 0.80},
        description="FinTwitBERT for social media sentiment"
    )
    print(f"  ✓ Registered fintwitbert:1.0.0")
    
    # Agent 25 - Chronos
    registry.register_model(
        name="chronos-t5",
        agent_id="25_market",
        model_type="transformer",
        framework="huggingface",
        metrics={"mae": 0.12, "rmse": 0.18},
        hyperparameters={"context_length": 256, "prediction_horizon": 5},
        description="Chronos-T5 for price forecasting"
    )
    print(f"  ✓ Registered chronos-t5:1.0.0")
    
    # Promote v2 to production
    print("\n🚀 Promoting finbert:1.0.1 to production...")
    registry.promote_model("finbert", "1.0.1")
    
    # Compare versions
    print("\n📊 Comparing finbert versions...")
    comparison = registry.compare_versions("finbert", "1.0.0", "1.0.1")
    print(f"   Accuracy: {comparison['metrics_diff']['accuracy']['pct_change']:+.1f}%")
    print(f"   F1 Score: {comparison['metrics_diff']['f1']['pct_change']:+.1f}%")
    
    # Print report
    print("\n" + registry.generate_report())


if __name__ == "__main__":
    main()
