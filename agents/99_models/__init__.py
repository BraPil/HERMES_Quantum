"""
Models Agent (99)

Manages machine learning models for predictions and classifications.
Handles model training, inference, and performance monitoring.

Components:
- ModelRegistry: Version control and deployment management
- RL Module: Reinforcement learning for trading decisions
"""

__version__ = "0.3.0"
__agent_id__ = "99"
__agent_name__ = "Models"
__agent_type__ = "support"

from .model_registry import (
    ModelRegistry,
    ModelVersion,
    ModelStatus
)

# RL Module imports
try:
    from .rl import (
        TradingEnvironment,
        MarketState,
        RLTradingAgent,
        RLConfig,
    )
    RL_AVAILABLE = True
except ImportError:
    TradingEnvironment = None
    MarketState = None
    RLTradingAgent = None
    RLConfig = None
    RL_AVAILABLE = False

__all__ = [
    'ModelRegistry',
    'ModelVersion',
    'ModelStatus',
    # RL
    'TradingEnvironment',
    'MarketState',
    'RLTradingAgent',
    'RLConfig',
    'RL_AVAILABLE',
]
