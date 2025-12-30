"""
Agent 01: Orchestrator
======================
The central coordinator of the HERMES system.

Components:
- EventBus: Pub/sub event system for agent coordination
- PredictionTracker: Stores predictions for validation
- LearningEngine: Real-time ML learning from outcomes
- DecisionMaker: Generates trading decisions with reasoning
- Orchestrator: Main coordinator that ties everything together

Usage:
    from agents.orchestrator import get_orchestrator
    
    orchestrator = get_orchestrator()
    await orchestrator.run()

Created: 2025-12-30
"""

__version__ = "0.2.0"

from .event_bus import (
    EventBus,
    Event,
    EventType,
    EventPriority,
    get_event_bus,
    reset_event_bus,
    publish_signal,
    publish_decision,
    publish_prediction
)

from .prediction_tracker import (
    PredictionTracker,
    Prediction,
    PredictionType,
    PredictionStatus,
    AccuracyMetrics,
    get_prediction_tracker
)

from .learning_engine import (
    LearningEngine,
    ModelWeight,
    RangeCalibration,
    SignalThreshold,
    get_learning_engine
)

from .decision_maker import (
    DecisionMaker,
    TradingDecision,
    Signal,
    EntryTarget,
    ExitTarget,
    ActionType,
    ActionStrength,
    get_decision_maker
)

from .orchestrator import (
    Orchestrator,
    OrchestratorState,
    DashboardData,
    get_orchestrator,
    reset_orchestrator
)

__all__ = [
    # Event Bus
    "EventBus",
    "Event",
    "EventType",
    "EventPriority",
    "get_event_bus",
    "reset_event_bus",
    "publish_signal",
    "publish_decision",
    "publish_prediction",
    
    # Prediction Tracker
    "PredictionTracker",
    "Prediction",
    "PredictionType",
    "PredictionStatus",
    "AccuracyMetrics",
    "get_prediction_tracker",
    
    # Learning Engine
    "LearningEngine",
    "ModelWeight",
    "RangeCalibration",
    "SignalThreshold",
    "get_learning_engine",
    
    # Decision Maker
    "DecisionMaker",
    "TradingDecision",
    "Signal",
    "EntryTarget",
    "ExitTarget",
    "ActionType",
    "ActionStrength",
    "get_decision_maker",
    
    # Orchestrator
    "Orchestrator",
    "OrchestratorState",
    "DashboardData",
    "get_orchestrator",
    "reset_orchestrator"
]
