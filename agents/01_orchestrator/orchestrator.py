"""
HERMES_Quantum Orchestrator (Agent 01)
======================================
The central coordinator and brain of the HERMES system.

This is the main agent that:
1. Coordinates all specialist agents (22-25)
2. Manages the event-driven workflow
3. Makes final trading decisions via DecisionMaker
4. Tracks performance via LearningEngine
5. Provides real-time data for the dashboard

The orchestrator runs as a continuous loop, processing events
and generating decisions in real-time (2-4 second updates).

Created: 2025-12-30
"""

import asyncio
import json
import logging
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading

from .event_bus import (
    Event, EventBus, EventType, EventPriority,
    get_event_bus, reset_event_bus,
    publish_signal, publish_decision, publish_prediction
)
from .prediction_tracker import (
    PredictionTracker, PredictionType, AccuracyMetrics,
    get_prediction_tracker
)
from .learning_engine import (
    LearningEngine, ModelWeight, RangeCalibration, SignalThreshold,
    get_learning_engine
)
from .decision_maker import (
    DecisionMaker, TradingDecision, Signal, ActionType,
    get_decision_maker
)

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    """States of the orchestrator."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class DashboardData:
    """
    Complete data package for the dashboard display.
    
    This is the primary output format for the UX frontend.
    Contains all information needed for real-time display.
    """
    # System status
    status: str
    last_update: datetime
    update_interval_seconds: float
    
    # Decisions by ticker
    decisions: Dict[str, Dict[str, Any]]  # ticker -> decision dict
    
    # Accuracy metrics
    accuracy: Dict[str, Dict[str, Any]]  # timeframe -> metrics dict
    
    # Model weights
    model_weights: Dict[str, Dict[str, Any]]  # model -> weight info
    
    # System stats
    stats: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "last_update": self.last_update.isoformat(),
            "update_interval_seconds": self.update_interval_seconds,
            "decisions": self.decisions,
            "accuracy": self.accuracy,
            "model_weights": self.model_weights,
            "stats": self.stats
        }
    
    def to_json(self) -> str:
        """Convert to JSON for API response."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class Orchestrator:
    """
    Main orchestrator for the HERMES system.
    
    This is Agent 01 - the central coordinator that:
    1. Initializes all components (event bus, learning engine, decision maker)
    2. Schedules and runs specialist agents
    3. Processes events in priority order
    4. Generates trading decisions
    5. Tracks and learns from outcomes
    6. Provides real-time dashboard data
    
    Features:
    - Event-driven architecture
    - Configurable update intervals
    - Graceful shutdown handling
    - Comprehensive logging
    - Real-time dashboard data generation
    
    Usage:
        orchestrator = Orchestrator()
        
        # Run forever (blocking)
        await orchestrator.run()
        
        # Or run for a specific duration
        await orchestrator.run(duration_seconds=3600)
        
        # Get dashboard data
        data = orchestrator.get_dashboard_data()
    """
    
    # Default tickers to monitor
    DEFAULT_TICKERS = ["QBTS", "IONQ", "RGTI", "QUBT"]
    
    def __init__(
        self,
        tickers: List[str] = None,
        update_interval: float = 2.0,
        log_level: int = logging.INFO
    ):
        """
        Initialize the orchestrator.
        
        Args:
            tickers: List of tickers to monitor (default: quantum computing stocks)
            update_interval: Seconds between update cycles (default: 2.0)
            log_level: Logging level
        """
        self.tickers = tickers or self.DEFAULT_TICKERS
        self.update_interval = update_interval
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )
        
        # State
        self._state = OrchestratorState.INITIALIZING
        self._start_time: Optional[datetime] = None
        self._last_update: Optional[datetime] = None
        self._cycle_count = 0
        
        # Components
        self._event_bus = get_event_bus()
        self._learning_engine = get_learning_engine()
        self._prediction_tracker = get_prediction_tracker()
        self._decision_maker = get_decision_maker()
        
        # Agent runners (to be registered)
        self._agent_runners: Dict[str, Callable] = {}
        
        # Market data cache
        self._market_data: Dict[str, Dict[str, Any]] = {}
        
        # Shutdown handling
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self._stats = {
            "cycles": 0,
            "events_processed": 0,
            "decisions_made": 0,
            "predictions_stored": 0,
            "errors": 0
        }
        
        logger.info(
            f"Orchestrator initialized for tickers: {self.tickers}, "
            f"update_interval: {self.update_interval}s"
        )
        
        self._state = OrchestratorState.STOPPED
    
    # =========================================================================
    # Agent Registration
    # =========================================================================
    
    def register_agent(
        self,
        agent_id: str,
        runner: Callable,
        interval: float = None
    ) -> None:
        """
        Register a specialist agent.
        
        Args:
            agent_id: Agent identifier (e.g., "agent_22")
            runner: Async function to run the agent
            interval: Override update interval for this agent
        """
        self._agent_runners[agent_id] = {
            "runner": runner,
            "interval": interval or self.update_interval,
            "last_run": None
        }
        logger.info(f"Registered agent: {agent_id}")
    
    def register_data_collector(
        self,
        collector_id: str,
        collector: Callable,
        interval: float = 60.0
    ) -> None:
        """
        Register a data collector.
        
        Args:
            collector_id: Collector identifier
            collector: Async function to collect data
            interval: Collection interval in seconds
        """
        self._agent_runners[collector_id] = {
            "runner": collector,
            "interval": interval,
            "last_run": None,
            "is_collector": True
        }
        logger.info(f"Registered data collector: {collector_id}")
    
    # =========================================================================
    # Lifecycle Management
    # =========================================================================
    
    async def start(self) -> None:
        """Start the orchestrator (non-blocking)."""
        if self._state == OrchestratorState.RUNNING:
            logger.warning("Orchestrator already running")
            return
        
        self._state = OrchestratorState.INITIALIZING
        self._start_time = datetime.now()
        self._shutdown_event.clear()
        
        # Subscribe to system events
        self._setup_event_handlers()
        
        # Publish start event
        self._event_bus.publish(
            event_type=EventType.SYSTEM_START,
            source="orchestrator",
            data={
                "tickers": self.tickers,
                "update_interval": self.update_interval,
                "start_time": self._start_time.isoformat()
            }
        )
        
        self._state = OrchestratorState.RUNNING
        logger.info("Orchestrator started")
    
    async def stop(self) -> None:
        """Stop the orchestrator gracefully."""
        if self._state == OrchestratorState.STOPPED:
            return
        
        self._state = OrchestratorState.STOPPING
        logger.info("Orchestrator stopping...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Publish stop event
        self._event_bus.publish(
            event_type=EventType.SYSTEM_STOP,
            source="orchestrator",
            data={
                "stop_time": datetime.now().isoformat(),
                "total_cycles": self._stats["cycles"],
                "runtime_seconds": (datetime.now() - self._start_time).total_seconds()
                    if self._start_time else 0
            }
        )
        
        # Process remaining events
        await self._event_bus.process_events()
        
        self._state = OrchestratorState.STOPPED
        logger.info("Orchestrator stopped")
    
    async def run(self, duration_seconds: float = None) -> None:
        """
        Run the orchestrator main loop.
        
        Args:
            duration_seconds: Run for this duration (None = forever)
        """
        await self.start()
        
        end_time = None
        if duration_seconds:
            end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        try:
            while self._state == OrchestratorState.RUNNING:
                # Check duration
                if end_time and datetime.now() >= end_time:
                    logger.info("Duration reached, stopping")
                    break
                
                # Check shutdown signal
                if self._shutdown_event.is_set():
                    break
                
                # Run one cycle
                await self._run_cycle()
                
                # Wait for next interval
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info("Run cancelled")
        except Exception as e:
            self._state = OrchestratorState.ERROR
            self._stats["errors"] += 1
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def _run_cycle(self) -> None:
        """Run one update cycle."""
        cycle_start = time.time()
        self._cycle_count += 1
        self._stats["cycles"] += 1
        
        try:
            # 1. Run due agents/collectors
            await self._run_due_agents()
            
            # 2. Process events
            events_processed = await self._event_bus.process_events()
            self._stats["events_processed"] += events_processed
            
            # 3. Generate/update decisions for each ticker
            for ticker in self.tickers:
                decision = await self._update_decision(ticker)
                if decision:
                    self._stats["decisions_made"] += 1
            
            # 4. Update accuracy metrics periodically
            if self._cycle_count % 30 == 0:  # Every 30 cycles (~1 minute)
                self._update_accuracy_metrics()
            
            # 5. Expire old predictions periodically
            if self._cycle_count % 300 == 0:  # Every 300 cycles (~10 minutes)
                self._prediction_tracker.expire_old_predictions()
            
            self._last_update = datetime.now()
            
            cycle_duration = time.time() - cycle_start
            if cycle_duration > self.update_interval:
                logger.warning(
                    f"Cycle {self._cycle_count} took {cycle_duration:.2f}s "
                    f"(> {self.update_interval}s interval)"
                )
                
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Error in cycle {self._cycle_count}: {e}")
            
            # Publish error event
            self._event_bus.publish(
                event_type=EventType.SYSTEM_ERROR,
                source="orchestrator",
                data={"error": str(e), "cycle": self._cycle_count},
                priority=EventPriority.CRITICAL
            )
    
    async def _run_due_agents(self) -> None:
        """Run agents that are due for execution."""
        now = datetime.now()
        
        for agent_id, config in self._agent_runners.items():
            last_run = config.get("last_run")
            interval = config.get("interval", self.update_interval)
            
            if last_run is None or (now - last_run).total_seconds() >= interval:
                try:
                    runner = config["runner"]
                    
                    # Run agent
                    if asyncio.iscoroutinefunction(runner):
                        await runner(self.tickers)
                    else:
                        runner(self.tickers)
                    
                    config["last_run"] = now
                    
                except Exception as e:
                    logger.error(f"Error running {agent_id}: {e}")
                    self._stats["errors"] += 1
    
    async def _update_decision(self, ticker: str) -> Optional[TradingDecision]:
        """Update decision for a ticker."""
        # Get current price from market data
        market_data = self._market_data.get(ticker, {})
        current_price = market_data.get("price")
        
        # For demo/testing, use a placeholder price if not available
        if current_price is None:
            # Would fetch from yfinance or cached data
            current_price = self._get_default_price(ticker)
        
        # Generate decision if we have signals
        if ticker in self._decision_maker._signals:
            decision = self._decision_maker.generate_decision(
                ticker,
                current_price=current_price
            )
            return decision
        
        return None
    
    def _get_default_price(self, ticker: str) -> float:
        """Get default/cached price for a ticker."""
        # Placeholder prices for quantum stocks
        defaults = {
            "QBTS": 4.27,
            "IONQ": 8.15,
            "RGTI": 2.45,
            "QUBT": 3.82
        }
        return defaults.get(ticker, 10.0)
    
    def _update_accuracy_metrics(self) -> None:
        """Update accuracy metrics from prediction tracker."""
        for timeframe in ["1h", "24h", "7d", "28d"]:
            metrics = self._prediction_tracker.get_accuracy_metrics(timeframe)
            
            # Could publish to event bus for dashboard
            self._event_bus.publish(
                event_type=EventType.MONITOR_ACCURACY_UPDATE,
                source="orchestrator",
                data=metrics.to_dict(),
                priority=EventPriority.LOW
            )
    
    def _setup_event_handlers(self) -> None:
        """Set up internal event handlers."""
        self._event_bus.subscribe(
            EventType.DATA_STOCK_UPDATE,
            self._handle_stock_update
        )
        
        self._event_bus.subscribe(
            EventType.MONITOR_ALERT,
            self._handle_alert
        )
    
    def _handle_stock_update(self, event: Event) -> None:
        """Handle stock price update."""
        data = event.data
        ticker = data.get("ticker")
        
        if ticker:
            self._market_data[ticker] = {
                "price": data.get("price"),
                "volume": data.get("volume"),
                "timestamp": datetime.now()
            }
    
    def _handle_alert(self, event: Event) -> None:
        """Handle system alerts."""
        logger.warning(f"ALERT: {event.data}")
    
    # =========================================================================
    # Dashboard Data
    # =========================================================================
    
    def get_dashboard_data(self) -> DashboardData:
        """
        Get complete data package for the dashboard.
        
        This is the main method called by the frontend to get
        all real-time data for display.
        
        Returns:
            DashboardData object with all current information
        """
        # Get latest decisions
        decisions = {}
        for ticker in self.tickers:
            decision = self._decision_maker.get_latest_decision(ticker)
            if decision:
                decisions[ticker] = decision.to_dict()
            else:
                # Generate a placeholder decision
                decisions[ticker] = self._get_placeholder_decision(ticker)
        
        # Get accuracy metrics for all timeframes
        accuracy = {}
        for timeframe in ["1h", "24h", "7d", "28d", "6mo", "YTD", "12mo", "all"]:
            metrics = self._prediction_tracker.get_accuracy_metrics(timeframe)
            accuracy[timeframe] = metrics.to_dict()
        
        # Get model weights
        model_weights = {
            k: v.to_dict()
            for k, v in self._learning_engine.get_all_model_weights().items()
        }
        
        # Compile stats
        stats = {
            **self._stats,
            "state": self._state.value,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds()
                if self._start_time else 0,
            "tickers_monitored": len(self.tickers),
            "event_bus": self._event_bus.get_stats(),
            "prediction_tracker": self._prediction_tracker.get_stats(),
            "learning_engine": self._learning_engine.get_stats(),
            "decision_maker": self._decision_maker.get_stats()
        }
        
        return DashboardData(
            status=self._state.value,
            last_update=self._last_update or datetime.now(),
            update_interval_seconds=self.update_interval,
            decisions=decisions,
            accuracy=accuracy,
            model_weights=model_weights,
            stats=stats
        )
    
    def _get_placeholder_decision(self, ticker: str) -> Dict[str, Any]:
        """Get placeholder decision for tickers without signals."""
        return {
            "decision_id": "pending",
            "ticker": ticker,
            "company_name": DecisionMaker.COMPANY_NAMES.get(ticker, ticker),
            "current_price": self._get_default_price(ticker),
            "action": "HOLD",
            "action_strength": "Neutral",
            "signal_strength": 50.0,
            "conviction": 0.0,
            "signal_description": "Awaiting signals from specialist agents",
            "reasoning": "No signals received yet. Agents are collecting data.",
            "contributing_signals": [],
            "buy_targets": [],
            "sell_targets": [],
            "range_analysis": {
                "current_range": {"low": 0, "high": 0},
                "expected_range": {"low": 0, "high": 0},
                "short_term_target": {"price": 0, "confidence": 0, "timeframe": "5 days"},
                "medium_term_target": {"price": 0, "confidence": 0, "timeframe": "30 days"}
            },
            "patterns": {
                "past": [],
                "current": [],
                "emerging": []
            },
            "timestamp": datetime.now().isoformat(),
            "expires_at": None,
            "metadata": {"placeholder": True}
        }
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    def add_signal(
        self,
        ticker: str,
        signal_type: str,
        value: float,
        confidence: float,
        source: str = "manual",
        reasoning: str = ""
    ) -> None:
        """
        Convenience method to add a signal manually.
        
        Useful for testing or manual overrides.
        """
        signal = Signal(
            source=source,
            signal_type=signal_type,
            ticker=ticker,
            value=value,
            confidence=confidence,
            reasoning=reasoning
        )
        self._decision_maker.add_signal(signal)
    
    def get_state(self) -> OrchestratorState:
        """Get current orchestrator state."""
        return self._state
    
    def is_running(self) -> bool:
        """Check if orchestrator is running."""
        return self._state == OrchestratorState.RUNNING
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            **self._stats,
            "state": self._state.value,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "cycle_count": self._cycle_count,
            "tickers": self.tickers,
            "update_interval": self.update_interval,
            "registered_agents": list(self._agent_runners.keys())
        }


# Singleton instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator(
    tickers: List[str] = None,
    update_interval: float = 2.0
) -> Orchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(
            tickers=tickers,
            update_interval=update_interval
        )
    return _orchestrator


def reset_orchestrator() -> None:
    """Reset the global orchestrator (useful for testing)."""
    global _orchestrator
    _orchestrator = None


# ============================================================================
# Demo and CLI
# ============================================================================

async def demo():
    """Demonstrate Orchestrator functionality."""
    print("=" * 60)
    print("HERMES Orchestrator (Agent 01) Demo")
    print("=" * 60)
    
    orchestrator = get_orchestrator(
        tickers=["QBTS", "IONQ"],
        update_interval=1.0
    )
    
    # Add some test signals
    print("\n1. Adding test signals...")
    
    orchestrator.add_signal(
        ticker="QBTS",
        signal_type="sentiment",
        value=0.72,
        confidence=0.85,
        source="agent_22_test",
        reasoning="Test signal - positive sentiment"
    )
    
    orchestrator.add_signal(
        ticker="QBTS",
        signal_type="social",
        value=0.58,
        confidence=0.78,
        source="agent_23_test",
        reasoning="Test signal - social momentum"
    )
    
    orchestrator.add_signal(
        ticker="IONQ",
        signal_type="sentiment",
        value=-0.25,
        confidence=0.65,
        source="agent_22_test",
        reasoning="Test signal - slightly negative"
    )
    
    print("   Added signals for QBTS and IONQ")
    
    # Start and run a few cycles
    print("\n2. Running orchestrator for 3 cycles...")
    
    await orchestrator.start()
    
    for i in range(3):
        await orchestrator._run_cycle()
        print(f"   Cycle {i+1} complete")
        await asyncio.sleep(0.5)
    
    # Get dashboard data
    print("\n3. Dashboard Data:")
    print("-" * 40)
    
    dashboard = orchestrator.get_dashboard_data()
    
    print(f"   Status: {dashboard.status}")
    print(f"   Last Update: {dashboard.last_update}")
    print(f"\n   Decisions:")
    
    for ticker, decision in dashboard.decisions.items():
        print(f"      {ticker}: {decision['action']} "
              f"(Conviction: {decision['conviction']:.0f}%)")
        if decision.get('signal_description'):
            print(f"         Signal: {decision['signal_description']}")
    
    print(f"\n   Accuracy (24h):")
    acc_24h = dashboard.accuracy.get("24h", {})
    print(f"      Direction: {acc_24h.get('direction_accuracy', 0):.1f}%")
    print(f"      MAPE: {acc_24h.get('mean_percentage_error', 0):.2f}%")
    
    # Get stats
    print("\n4. Orchestrator Stats:")
    stats = orchestrator.get_stats()
    for key in ["state", "cycles", "events_processed", "decisions_made"]:
        print(f"   {key}: {stats.get(key, 'N/A')}")
    
    # Stop
    await orchestrator.stop()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


def run_demo():
    """Run the demo (entry point for CLI)."""
    asyncio.run(demo())


if __name__ == "__main__":
    run_demo()
