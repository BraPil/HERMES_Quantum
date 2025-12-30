"""
HERMES_Quantum Event Bus
========================
Pub/sub event system for agent coordination.

This is the nervous system of HERMES - all agents communicate through events.
Supports priority queues, event filtering, and async processing.

Created: 2025-12-30
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from collections import defaultdict
import heapq
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for queue ordering."""
    CRITICAL = 1    # Market halt, system errors, risk limits
    HIGH = 2        # Buy/sell signals, price alerts
    NORMAL = 3      # Regular agent updates
    LOW = 4         # Background tasks, logging
    BACKGROUND = 5  # Cleanup, optimization


class EventType(Enum):
    """All event types in the HERMES system."""
    # System Events
    SYSTEM_START = auto()
    SYSTEM_STOP = auto()
    SYSTEM_ERROR = auto()
    SYSTEM_HEALTH = auto()
    
    # Data Events
    DATA_STOCK_UPDATE = auto()
    DATA_NEWS_UPDATE = auto()
    DATA_SOCIAL_UPDATE = auto()
    DATA_MACRO_UPDATE = auto()
    
    # Agent Signal Events
    SIGNAL_SENTIMENT = auto()      # From Agent 22
    SIGNAL_SOCIAL = auto()         # From Agent 23
    SIGNAL_POLICY = auto()         # From Agent 24
    SIGNAL_FORECAST = auto()       # From Agent 25
    SIGNAL_PORTFOLIO = auto()      # From Agent 11
    
    # Decision Events
    DECISION_BUY = auto()
    DECISION_SELL = auto()
    DECISION_HOLD = auto()
    DECISION_PENDING = auto()
    
    # Execution Events
    EXECUTION_ORDER_PLACED = auto()
    EXECUTION_ORDER_FILLED = auto()
    EXECUTION_ORDER_CANCELLED = auto()
    EXECUTION_ORDER_FAILED = auto()
    
    # Learning Events (Agent 92)
    LEARNING_PREDICTION_STORED = auto()
    LEARNING_ACTUAL_RECEIVED = auto()
    LEARNING_ERROR_CALCULATED = auto()
    LEARNING_WEIGHTS_UPDATED = auto()
    
    # Monitoring Events
    MONITOR_ACCURACY_UPDATE = auto()
    MONITOR_PERFORMANCE_UPDATE = auto()
    MONITOR_ALERT = auto()


@dataclass(order=True)
class Event:
    """
    Core event structure for the HERMES system.
    
    Events are the primary communication mechanism between agents.
    They carry data, metadata, and routing information.
    """
    # For priority queue ordering (not included in comparison by default)
    priority: int = field(compare=True)
    timestamp: float = field(compare=True, default_factory=time.time)
    
    # Core event data (not compared)
    event_id: str = field(compare=False, default_factory=lambda: str(uuid.uuid4())[:8])
    event_type: EventType = field(compare=False, default=EventType.SYSTEM_HEALTH)
    source: str = field(compare=False, default="unknown")
    data: Dict[str, Any] = field(compare=False, default_factory=dict)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)
    
    # Routing
    target: Optional[str] = field(compare=False, default=None)  # Specific agent or None for broadcast
    correlation_id: Optional[str] = field(compare=False, default=None)  # For tracking related events
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.name,
            "priority": self.priority,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())[:8]),
            event_type=EventType[data["event_type"]],
            priority=data.get("priority", EventPriority.NORMAL.value),
            source=data.get("source", "unknown"),
            target=data.get("target"),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            correlation_id=data.get("correlation_id")
        )
    
    def __str__(self) -> str:
        return f"Event({self.event_id}: {self.event_type.name} from {self.source})"


# Type alias for event handlers
EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus for HERMES agent coordination.
    
    Features:
    - Priority-based event queue
    - Topic-based subscriptions
    - Pattern matching for event filtering
    - Event history for debugging
    - Async and sync handler support
    - Event correlation tracking
    
    Usage:
        bus = EventBus()
        
        # Subscribe to events
        bus.subscribe(EventType.SIGNAL_SENTIMENT, my_handler)
        
        # Publish events
        bus.publish(Event(
            event_type=EventType.SIGNAL_SENTIMENT,
            source="agent_22",
            data={"sentiment": 0.8, "ticker": "QBTS"}
        ))
        
        # Process events
        await bus.process_events()
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize the event bus.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        # Priority queue for events
        self._queue: List[Event] = []
        
        # Subscriptions: event_type -> list of handlers
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._async_subscribers: Dict[EventType, List[AsyncEventHandler]] = defaultdict(list)
        
        # Wildcard subscribers (receive all events)
        self._wildcard_subscribers: List[EventHandler] = []
        self._async_wildcard_subscribers: List[AsyncEventHandler] = []
        
        # Pattern-based subscribers (custom filter functions)
        self._pattern_subscribers: List[tuple[Callable[[Event], bool], EventHandler]] = []
        
        # Event history for debugging and replay
        self._history: List[Event] = []
        self._max_history = max_history
        
        # Correlation tracking
        self._correlations: Dict[str, List[Event]] = defaultdict(list)
        
        # Statistics
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_dropped": 0,
            "handlers_called": 0,
            "errors": 0
        }
        
        # Control flags
        self._running = False
        self._lock = asyncio.Lock()
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        is_async: bool = False
    ) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
            is_async: Whether the handler is async
        """
        if is_async:
            self._async_subscribers[event_type].append(handler)
        else:
            self._subscribers[event_type].append(handler)
        
        logger.debug(f"Subscribed to {event_type.name}")
    
    def subscribe_all(self, handler: EventHandler, is_async: bool = False) -> None:
        """Subscribe to all events (wildcard subscription)."""
        if is_async:
            self._async_wildcard_subscribers.append(handler)
        else:
            self._wildcard_subscribers.append(handler)
        
        logger.debug("Subscribed to all events (wildcard)")
    
    def subscribe_pattern(
        self,
        pattern: Callable[[Event], bool],
        handler: EventHandler
    ) -> None:
        """
        Subscribe with a custom filter pattern.
        
        Args:
            pattern: Function that returns True if handler should be called
            handler: Handler function
        """
        self._pattern_subscribers.append((pattern, handler))
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> bool:
        """
        Unsubscribe from an event type.
        
        Returns:
            True if handler was found and removed
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            return True
        if handler in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(handler)
            return True
        return False
    
    def publish(
        self,
        event: Event = None,
        event_type: EventType = None,
        source: str = "unknown",
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        target: str = None,
        correlation_id: str = None
    ) -> Event:
        """
        Publish an event to the bus.
        
        Can either pass a pre-built Event object or build one from parameters.
        
        Args:
            event: Pre-built event (if provided, other args ignored)
            event_type: Type of event
            source: Source agent/component
            data: Event payload
            priority: Event priority
            target: Specific target agent (None for broadcast)
            correlation_id: ID to link related events
            
        Returns:
            The published event
        """
        if event is None:
            event = Event(
                priority=priority.value,
                event_type=event_type,
                source=source,
                data=data or {},
                target=target,
                correlation_id=correlation_id
            )
        
        # Add to priority queue
        heapq.heappush(self._queue, event)
        
        # Track in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Track correlations
        if event.correlation_id:
            self._correlations[event.correlation_id].append(event)
        
        self._stats["events_published"] += 1
        
        logger.debug(f"Published: {event}")
        
        return event
    
    async def process_events(self, max_events: int = None) -> int:
        """
        Process events from the queue.
        
        Args:
            max_events: Maximum events to process (None for all)
            
        Returns:
            Number of events processed
        """
        processed = 0
        
        async with self._lock:
            while self._queue:
                if max_events and processed >= max_events:
                    break
                
                event = heapq.heappop(self._queue)
                await self._dispatch_event(event)
                processed += 1
                self._stats["events_processed"] += 1
        
        return processed
    
    async def _dispatch_event(self, event: Event) -> None:
        """Dispatch an event to all matching handlers."""
        handlers_called = 0
        
        try:
            # Call type-specific sync handlers
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                    handlers_called += 1
                except Exception as e:
                    logger.error(f"Handler error for {event}: {e}")
                    self._stats["errors"] += 1
            
            # Call type-specific async handlers
            for handler in self._async_subscribers[event.event_type]:
                try:
                    await handler(event)
                    handlers_called += 1
                except Exception as e:
                    logger.error(f"Async handler error for {event}: {e}")
                    self._stats["errors"] += 1
            
            # Call wildcard handlers
            for handler in self._wildcard_subscribers:
                try:
                    handler(event)
                    handlers_called += 1
                except Exception as e:
                    logger.error(f"Wildcard handler error: {e}")
                    self._stats["errors"] += 1
            
            # Call async wildcard handlers
            for handler in self._async_wildcard_subscribers:
                try:
                    await handler(event)
                    handlers_called += 1
                except Exception as e:
                    logger.error(f"Async wildcard handler error: {e}")
                    self._stats["errors"] += 1
            
            # Call pattern-based handlers
            for pattern, handler in self._pattern_subscribers:
                try:
                    if pattern(event):
                        handler(event)
                        handlers_called += 1
                except Exception as e:
                    logger.error(f"Pattern handler error: {e}")
                    self._stats["errors"] += 1
            
            self._stats["handlers_called"] += handlers_called
            
        except Exception as e:
            logger.error(f"Error dispatching event {event}: {e}")
            self._stats["errors"] += 1
    
    def process_events_sync(self, max_events: int = None) -> int:
        """
        Synchronous version of process_events.
        
        Useful for testing or non-async contexts.
        """
        return asyncio.get_event_loop().run_until_complete(
            self.process_events(max_events)
        )
    
    async def run(self, interval: float = 0.1) -> None:
        """
        Run the event bus continuously.
        
        Args:
            interval: Time between queue checks in seconds
        """
        self._running = True
        logger.info("EventBus started")
        
        while self._running:
            await self.process_events()
            await asyncio.sleep(interval)
        
        logger.info("EventBus stopped")
    
    def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
    
    def get_correlated_events(self, correlation_id: str) -> List[Event]:
        """Get all events with the same correlation ID."""
        return self._correlations.get(correlation_id, [])
    
    def get_history(
        self,
        event_type: EventType = None,
        source: str = None,
        since: float = None,
        limit: int = None
    ) -> List[Event]:
        """
        Get events from history with optional filtering.
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            since: Only events after this timestamp
            limit: Maximum number to return
            
        Returns:
            List of matching events
        """
        events = self._history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        if since:
            events = [e for e in events if e.timestamp >= since]
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_stats(self) -> Dict[str, int]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "history_size": len(self._history),
            "subscriber_count": sum(len(s) for s in self._subscribers.values()),
            "correlation_count": len(self._correlations)
        }
    
    def clear(self) -> None:
        """Clear the event queue and history."""
        self._queue.clear()
        self._history.clear()
        self._correlations.clear()
        logger.info("EventBus cleared")


# Singleton instance for global access
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def reset_event_bus() -> None:
    """Reset the global event bus (useful for testing)."""
    global _event_bus
    _event_bus = None


# ============================================================================
# Convenience functions for common event patterns
# ============================================================================

def publish_signal(
    signal_type: str,
    source: str,
    ticker: str,
    value: float,
    confidence: float,
    metadata: Dict[str, Any] = None
) -> Event:
    """
    Convenience function to publish agent signals.
    
    Args:
        signal_type: Type of signal (sentiment, social, policy, forecast)
        source: Agent source (e.g., "agent_22")
        ticker: Stock ticker
        value: Signal value (-1 to 1 for sentiment, price for forecast)
        confidence: Confidence level (0 to 1)
        metadata: Additional metadata
    """
    event_types = {
        "sentiment": EventType.SIGNAL_SENTIMENT,
        "social": EventType.SIGNAL_SOCIAL,
        "policy": EventType.SIGNAL_POLICY,
        "forecast": EventType.SIGNAL_FORECAST,
        "portfolio": EventType.SIGNAL_PORTFOLIO
    }
    
    data = {
        "ticker": ticker,
        "value": value,
        "confidence": confidence,
        "timestamp": datetime.now().isoformat()
    }
    if metadata:
        data["metadata"] = metadata
    
    return get_event_bus().publish(
        event_type=event_types.get(signal_type, EventType.SIGNAL_SENTIMENT),
        source=source,
        data=data,
        priority=EventPriority.HIGH
    )


def publish_decision(
    action: str,
    ticker: str,
    price: float,
    quantity: int,
    reasoning: str,
    confidence: float,
    signals: List[Dict[str, Any]] = None
) -> Event:
    """
    Convenience function to publish trading decisions.
    
    Args:
        action: buy, sell, or hold
        ticker: Stock ticker
        price: Target price
        quantity: Number of shares
        reasoning: Explanation of decision
        confidence: Confidence level
        signals: Contributing signals
    """
    event_types = {
        "buy": EventType.DECISION_BUY,
        "sell": EventType.DECISION_SELL,
        "hold": EventType.DECISION_HOLD
    }
    
    correlation_id = str(uuid.uuid4())[:8]
    
    return get_event_bus().publish(
        event_type=event_types.get(action.lower(), EventType.DECISION_HOLD),
        source="agent_01",
        data={
            "action": action,
            "ticker": ticker,
            "price": price,
            "quantity": quantity,
            "reasoning": reasoning,
            "confidence": confidence,
            "signals": signals or [],
            "timestamp": datetime.now().isoformat()
        },
        priority=EventPriority.CRITICAL,
        correlation_id=correlation_id
    )


def publish_prediction(
    ticker: str,
    prediction_type: str,
    predicted_value: float,
    target_time: datetime,
    confidence: float,
    model_source: str
) -> Event:
    """
    Publish a prediction for later validation (Agent 92 learning).
    
    Args:
        ticker: Stock ticker
        prediction_type: Type of prediction (price, direction, volatility)
        predicted_value: The predicted value
        target_time: When the prediction is for
        confidence: Confidence level
        model_source: Which model made the prediction
    """
    return get_event_bus().publish(
        event_type=EventType.LEARNING_PREDICTION_STORED,
        source=model_source,
        data={
            "ticker": ticker,
            "prediction_type": prediction_type,
            "predicted_value": predicted_value,
            "target_time": target_time.isoformat(),
            "confidence": confidence,
            "created_at": datetime.now().isoformat()
        },
        priority=EventPriority.NORMAL
    )


# ============================================================================
# Demo and Testing
# ============================================================================

async def demo():
    """Demonstrate EventBus functionality."""
    print("=" * 60)
    print("HERMES EventBus Demo")
    print("=" * 60)
    
    bus = get_event_bus()
    
    # Track received events
    received = []
    
    # Define handlers
    def sentiment_handler(event: Event):
        print(f"  [Sentiment Handler] Received: {event.data}")
        received.append(event)
    
    def all_signals_handler(event: Event):
        print(f"  [All Signals] {event.event_type.name}: {event.data.get('ticker', 'N/A')}")
    
    # Subscribe
    bus.subscribe(EventType.SIGNAL_SENTIMENT, sentiment_handler)
    
    # Pattern subscription: all signal events
    bus.subscribe_pattern(
        lambda e: e.event_type.name.startswith("SIGNAL_"),
        all_signals_handler
    )
    
    # Publish some events
    print("\n1. Publishing events...")
    
    publish_signal(
        signal_type="sentiment",
        source="agent_22",
        ticker="QBTS",
        value=0.85,
        confidence=0.92
    )
    
    publish_signal(
        signal_type="social",
        source="agent_23",
        ticker="IONQ",
        value=0.45,
        confidence=0.78
    )
    
    publish_decision(
        action="buy",
        ticker="QBTS",
        price=4.25,
        quantity=100,
        reasoning="Strong sentiment + social momentum",
        confidence=0.88,
        signals=[{"type": "sentiment", "value": 0.85}]
    )
    
    # Process events
    print("\n2. Processing events...")
    processed = await bus.process_events()
    print(f"   Processed {processed} events")
    
    # Show stats
    print("\n3. Event Bus Stats:")
    stats = bus.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Show history
    print("\n4. Recent History:")
    for event in bus.get_history(limit=5):
        print(f"   {event}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo())
