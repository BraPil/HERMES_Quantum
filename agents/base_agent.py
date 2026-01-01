"""
HERMES Agent Base Class
=======================
Foundation for all HERMES agents with integrated:
- EventBus publishing/subscribing
- MLFlow tracking
- Standardized signal output
- Async execution support

All agents (22, 23, 24, 25, 11) inherit from this class.

Created: 2025-12-30
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1
    NEUTRAL = 0


class ActionRecommendation(Enum):
    """Recommended trading actions."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class AgentSignal:
    """
    Standardized signal output from any agent.
    
    This is the common format that all agents output and the
    Orchestrator consumes.
    """
    # Required fields
    ticker: str
    agent_id: str  # e.g., "agent_22", "agent_25"
    signal_type: str  # sentiment, social, policy, forecast, portfolio
    
    # Signal values
    value: float  # Primary signal value (-1 to 1 for sentiment, price for forecast)
    confidence: float  # 0 to 1
    strength: SignalStrength = SignalStrength.MODERATE
    
    # Recommendation
    action: ActionRecommendation = ActionRecommendation.HOLD
    action_confidence: float = 0.5
    
    # Context
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    
    # Predictions (if applicable)
    price_target: Optional[float] = None
    target_timeframe: Optional[str] = None  # "1h", "24h", "7d"
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    data_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "agent_id": self.agent_id,
            "signal_type": self.signal_type,
            "value": self.value,
            "confidence": self.confidence,
            "strength": self.strength.name,
            "action": self.action.value,
            "action_confidence": self.action_confidence,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "price_target": self.price_target,
            "target_timeframe": self.target_timeframe,
            "timestamp": self.timestamp.isoformat(),
            "data_sources": self.data_sources,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentSignal":
        """Create from dictionary."""
        data = data.copy()
        data["strength"] = SignalStrength[data.get("strength", "MODERATE")]
        data["action"] = ActionRecommendation(data.get("action", "HOLD"))
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class BaseAgent(ABC):
    """
    Base class for all HERMES agents.
    
    Provides:
    - EventBus integration for publishing signals
    - MLFlow tracking for experiment logging
    - Standardized signal format
    - Async execution support
    - Health monitoring
    
    Usage:
        class MyAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="agent_22",
                    signal_type="sentiment",
                    name="Sentiment Analyzer"
                )
            
            async def analyze(self, ticker: str, data: dict) -> AgentSignal:
                # Your analysis logic here
                return AgentSignal(
                    ticker=ticker,
                    agent_id=self.agent_id,
                    signal_type=self.signal_type,
                    value=0.8,
                    confidence=0.9
                )
    """
    
    def __init__(
        self,
        agent_id: str,
        signal_type: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: bool = True
    ):
        """
        Initialize base agent.
        
        Args:
            agent_id: Unique agent identifier (e.g., "agent_22")
            signal_type: Type of signals this agent produces
            name: Human-readable name
            description: Agent description
            enabled: Whether agent is active
        """
        self.agent_id = agent_id
        self.signal_type = signal_type
        self.name = name or agent_id
        self.description = description or ""
        self.enabled = enabled
        
        # State tracking
        self._last_run: Optional[datetime] = None
        self._run_count: int = 0
        self._error_count: int = 0
        self._last_error: Optional[str] = None
        
        # Lazy-loaded components
        self._event_bus = None
        self._mlflow_tracker = None
        
        logger.info(f"Initialized {self.name} ({self.agent_id})")
    
    @property
    def event_bus(self):
        """Lazy-load EventBus."""
        if self._event_bus is None:
            try:
                import importlib
                event_bus_mod = importlib.import_module('agents.01_orchestrator.event_bus')
                self._event_bus = event_bus_mod.get_event_bus()
            except ImportError:
                logger.warning(f"{self.agent_id}: EventBus not available")
        return self._event_bus
    
    @property
    def mlflow_tracker(self):
        """Lazy-load MLFlow tracker."""
        if self._mlflow_tracker is None:
            try:
                import importlib
                mlflow_mod = importlib.import_module('agents.91_tools.mlflow_tracking')
                self._mlflow_tracker = mlflow_mod.get_mlflow_tracker()
            except ImportError:
                logger.debug(f"{self.agent_id}: MLFlow tracking not available")
        return self._mlflow_tracker
    
    @abstractmethod
    async def analyze(
        self,
        ticker: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentSignal]:
        """
        Perform analysis and generate a signal.
        
        This is the main method each agent must implement.
        
        Args:
            ticker: Stock ticker to analyze
            data: Optional input data (varies by agent)
            
        Returns:
            AgentSignal with analysis results, or None if analysis failed
        """
        pass
    
    async def run(
        self,
        ticker: str,
        data: Optional[Dict[str, Any]] = None,
        publish: bool = True,
        track: bool = True
    ) -> Optional[AgentSignal]:
        """
        Run the agent analysis with full integration.
        
        Args:
            ticker: Stock ticker to analyze
            data: Optional input data
            publish: Whether to publish to EventBus
            track: Whether to track in MLFlow
            
        Returns:
            AgentSignal or None on error
        """
        if not self.enabled:
            logger.debug(f"{self.agent_id} is disabled, skipping")
            return None
        
        try:
            # Run analysis
            signal = await self.analyze(ticker, data)
            
            if signal is None:
                return None
            
            # Update state
            self._last_run = datetime.now()
            self._run_count += 1
            
            # Publish to EventBus
            if publish and self.event_bus:
                self._publish_signal(signal)
            
            # Track in MLFlow
            if track and self.mlflow_tracker:
                self._track_signal(signal)
            
            return signal
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"{self.agent_id} error analyzing {ticker}: {e}")
            return None
    
    def _publish_signal(self, signal: AgentSignal) -> None:
        """Publish signal to EventBus."""
        try:
            import importlib
            event_bus_mod = importlib.import_module('agents.01_orchestrator.event_bus')
            
            event_bus_mod.publish_signal(
                signal_type=self.signal_type,
                source=self.agent_id,
                ticker=signal.ticker,
                value=signal.value,
                confidence=signal.confidence,
                metadata=signal.to_dict()
            )
            logger.debug(f"{self.agent_id} published signal for {signal.ticker}")
        except Exception as e:
            logger.warning(f"{self.agent_id} failed to publish signal: {e}")
    
    def _track_signal(self, signal: AgentSignal) -> None:
        """Track signal in MLFlow."""
        if not self.mlflow_tracker:
            return
        
        try:
            self.mlflow_tracker.log_signal(
                ticker=signal.ticker,
                signal_type=self.signal_type,
                signal_value=signal.value,
                confidence=signal.confidence,
                agent_source=self.agent_id,
                recommended_action=signal.action.value,
                reasoning=signal.reasoning
            )
        except Exception as e:
            logger.debug(f"{self.agent_id} failed to track signal: {e}")
    
    async def run_batch(
        self,
        tickers: List[str],
        data: Optional[Dict[str, Dict[str, Any]]] = None,
        parallel: bool = True
    ) -> Dict[str, AgentSignal]:
        """
        Run analysis on multiple tickers.
        
        Args:
            tickers: List of stock tickers
            data: Optional dict of ticker -> data
            parallel: Whether to run in parallel
            
        Returns:
            Dict of ticker -> AgentSignal
        """
        data = data or {}
        results = {}
        
        if parallel:
            # Run all in parallel
            tasks = [
                self.run(ticker, data.get(ticker))
                for ticker in tickers
            ]
            signals = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ticker, signal in zip(tickers, signals):
                if isinstance(signal, AgentSignal):
                    results[ticker] = signal
                elif isinstance(signal, Exception):
                    logger.error(f"{self.agent_id} error on {ticker}: {signal}")
        else:
            # Run sequentially
            for ticker in tickers:
                signal = await self.run(ticker, data.get(ticker))
                if signal:
                    results[ticker] = signal
        
        return results
    
    def get_health(self) -> Dict[str, Any]:
        """Get agent health status."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "enabled": self.enabled,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "run_count": self._run_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "error_rate": self._error_count / max(1, self._run_count)
        }
    
    def subscribe_to_events(
        self,
        event_types: List[str],
        handler: Callable
    ) -> None:
        """
        Subscribe to EventBus events.
        
        Args:
            event_types: List of event type names
            handler: Callback function for events
        """
        if not self.event_bus:
            logger.warning(f"{self.agent_id}: Cannot subscribe, no EventBus")
            return
        
        try:
            import importlib
            event_bus_mod = importlib.import_module('agents.01_orchestrator.event_bus')
            
            for event_type_name in event_types:
                try:
                    event_type = event_bus_mod.EventType[event_type_name]
                    self.event_bus.subscribe(event_type, handler)
                    logger.debug(f"{self.agent_id} subscribed to {event_type_name}")
                except KeyError:
                    logger.warning(f"Unknown event type: {event_type_name}")
        except Exception as e:
            logger.warning(f"{self.agent_id} subscription failed: {e}")


class SyncAgentWrapper:
    """
    Wrapper to run async agents synchronously.
    
    Usage:
        agent = MyAgent()
        sync_agent = SyncAgentWrapper(agent)
        signal = sync_agent.run("QBTS")
    """
    
    def __init__(self, agent: BaseAgent):
        self.agent = agent
    
    def run(
        self,
        ticker: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[AgentSignal]:
        """Run agent synchronously."""
        return asyncio.get_event_loop().run_until_complete(
            self.agent.run(ticker, data, **kwargs)
        )
    
    def run_batch(
        self,
        tickers: List[str],
        data: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, AgentSignal]:
        """Run batch synchronously."""
        return asyncio.get_event_loop().run_until_complete(
            self.agent.run_batch(tickers, data, **kwargs)
        )


# Agent registry for discovery
_agent_registry: Dict[str, BaseAgent] = {}


def register_agent(agent: BaseAgent) -> None:
    """Register an agent for discovery."""
    _agent_registry[agent.agent_id] = agent
    logger.info(f"Registered agent: {agent.agent_id}")


def get_agent(agent_id: str) -> Optional[BaseAgent]:
    """Get a registered agent by ID."""
    return _agent_registry.get(agent_id)


def get_all_agents() -> Dict[str, BaseAgent]:
    """Get all registered agents."""
    return _agent_registry.copy()


def unregister_agent(agent_id: str) -> None:
    """Unregister an agent."""
    if agent_id in _agent_registry:
        del _agent_registry[agent_id]
