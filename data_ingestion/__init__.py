"""
HERMES_Quantum - Data Ingestion Package
Qlib-inspired DataHandler pattern for unified data access

This module provides:
- Stock data fetching (yfinance)
- News aggregation (RSS feeds)  
- Social sentiment (Reddit, StockTwits)
- Macro data (FRED)
- Unified DataHandler interface

Cost: $0/month (all free data sources)
"""

from .stock_data import StockDataFetcher
from .data_handler import HERMESDataHandler

__all__ = [
    'StockDataFetcher',
    'HERMESDataHandler',
]

__version__ = '0.1.0'

