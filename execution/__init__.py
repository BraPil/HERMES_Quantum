"""
HERMES_Quantum Execution Package

Workflow execution, task scheduling, and system orchestration.

Components:
- backtester: Historical signal replay and performance testing
- risk_manager: Position sizing and risk controls
- paper_trading: Simulated live trading without real money
"""

__version__ = "0.4.0"

from .backtester import (
    Backtester,
    BacktestResult,
    Portfolio,
    Trade,
    run_backtest
)

from .risk_manager import (
    RiskManager,
    RiskLimits,
    RiskLevel,
    SizingMethod,
    PositionRisk,
    PortfolioRisk
)

from .paper_trading import (
    PaperTradingEngine,
    PaperTradingSession,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position,
    AccountState,
)

__all__ = [
    # Backtester
    'Backtester',
    'BacktestResult',
    'Portfolio',
    'Trade',
    'run_backtest',
    # Risk Manager
    'RiskManager',
    'RiskLimits',
    'RiskLevel',
    'SizingMethod',
    'PositionRisk',
    'PortfolioRisk',
    # Paper Trading
    'PaperTradingEngine',
    'PaperTradingSession',
    'Order',
    'OrderType',
    'OrderSide',
    'OrderStatus',
    'Position',
    'AccountState',
]
