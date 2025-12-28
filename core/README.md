# Core

This directory contains core functionality and base classes for the HERMES_Quantum multi-agent system.

## Purpose

The core package provides:
- System initialization and configuration
- Agent lifecycle management
- Message passing and communication protocols
- Event handling and logging
- State management

## Usage

```python
from core import System, MessageBus, EventHandler
```

## Components

- `system.py` - Main system initialization and management
- `message_bus.py` - Message passing between agents
- `event_handler.py` - Event processing and handling
- `state_manager.py` - System state management
- `logger.py` - Centralized logging configuration

## Architecture

The core module implements the foundational architecture that enables the multi-agent system to function cohesively. All agents and components interact through the core system.
