"""
Analyst Agent (11)

Performs fundamental and technical analysis of quantum computing stocks.
Analyzes financial statements, market trends, and valuation metrics.
Includes comprehensive risk analysis with pyfolio integration.
"""

__version__ = "0.2.0"
__agent_id__ = "11"
__agent_name__ = "Analyst"
__agent_type__ = "specialist"

from .risk_analyzer import (
    RiskAnalyzer,
    RiskMetrics
)

__all__ = [
    'RiskAnalyzer',
    'RiskMetrics'
]
