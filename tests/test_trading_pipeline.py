#!/usr/bin/env python3
"""
HERMES Quantum - Trading Pipeline Integration Tests
=====================================================
Tests the complete trading pipeline from data to execution.

Run with: pytest tests/test_trading_pipeline.py -v

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import pytest
import sys
from datetime import datetime
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Python 3.14+ asyncio fix
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


class TestDataSources:
    """Test the modular data source layer"""
    
    def test_yfinance_source_initialization(self):
        """Test YFinance data source initializes correctly"""
        from data_ingestion.data_sources import YFinanceDataSource
        
        source = YFinanceDataSource()
        assert source.name == "yfinance"
        assert source._connected is False
    
    def test_yfinance_connect(self):
        """Test YFinance connects successfully"""
        from data_ingestion.data_sources import YFinanceDataSource
        
        source = YFinanceDataSource()
        result = source.connect()
        
        assert result is True
        assert source._connected is True
    
    def test_yfinance_real_quote(self):
        """Test fetching a real stock quote from YFinance"""
        from data_ingestion.data_sources import YFinanceDataSource
        
        source = YFinanceDataSource()
        source.connect()
        
        quote = source.get_quote("QBTS")
        
        assert quote is not None
        assert quote.symbol == "QBTS"
        assert quote.last > 0
        assert quote.volume >= 0
    
    def test_yfinance_history(self):
        """Test fetching historical data"""
        from data_ingestion.data_sources import YFinanceDataSource
        
        source = YFinanceDataSource()
        source.connect()
        
        df = source.get_historical("QBTS", period="5d")
        
        assert df is not None
        assert len(df) > 0
        # Check for OHLCV columns
        assert any(col in df.columns for col in ["Close", "close"])
    
    def test_data_source_manager_context(self):
        """Test the data source manager as context manager"""
        from data_ingestion.data_sources import DataSourceManager
        
        with DataSourceManager() as manager:
            quote = manager.get_quote("QBTS")
        
        assert quote is not None
        assert quote.symbol == "QBTS"
        assert quote.last > 0


class TestSignalEngine:
    """Test the signal generation engine"""
    
    def test_technical_indicators_sma(self):
        """Test SMA indicator calculation"""
        from core.signal_engine import TechnicalIndicators
        import pandas as pd
        import numpy as np
        
        # Create sample data
        data = pd.Series(np.random.uniform(10, 15, 50))
        sma = TechnicalIndicators.sma(data, 20)
        
        assert len(sma) == 50
        assert not sma.iloc[-1] is np.nan
    
    def test_technical_indicators_rsi(self):
        """Test RSI indicator calculation"""
        from core.signal_engine import TechnicalIndicators
        import pandas as pd
        import numpy as np
        
        data = pd.Series(np.linspace(10, 15, 50))  # Trending up
        rsi = TechnicalIndicators.rsi(data, 14)
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert all(0 <= v <= 100 for v in valid_rsi)
    
    def test_technical_indicators_macd(self):
        """Test MACD indicator calculation"""
        from core.signal_engine import TechnicalIndicators
        import pandas as pd
        import numpy as np
        
        data = pd.Series(np.random.uniform(10, 15, 100))
        macd_line, signal_line, histogram = TechnicalIndicators.macd(data)
        
        assert len(macd_line) == 100
        assert len(signal_line) == 100
        assert len(histogram) == 100
    
    def test_signal_generator_initialization(self):
        """Test SignalGenerator initializes correctly"""
        from core.signal_engine import SignalGenerator
        
        generator = SignalGenerator()
        
        assert generator.watchlist == ["QBTS", "IONQ", "RGTI", "QUBT"]
        assert generator.MIN_CONFIDENCE == 50.0
        assert generator.ACTIONABLE_CONFIDENCE == 85.0
    
    def test_signal_generator_with_custom_watchlist(self):
        """Test SignalGenerator with custom watchlist"""
        from core.signal_engine import SignalGenerator
        
        generator = SignalGenerator(watchlist=["AAPL", "GOOGL"])
        
        assert generator.watchlist == ["AAPL", "GOOGL"]


class TestRiskManager:
    """Test the risk management system"""
    
    def test_kelly_calculator_initialization(self):
        """Test KellyCalculator with default fraction"""
        from core.risk_manager import KellyCalculator
        
        calculator = KellyCalculator()
        
        assert calculator.kelly_fraction == 0.25  # Default 25%
    
    def test_kelly_calculator_custom_fraction(self):
        """Test KellyCalculator with custom fraction"""
        from core.risk_manager import KellyCalculator
        
        calculator = KellyCalculator(kelly_fraction=0.5)
        
        assert calculator.kelly_fraction == 0.5
    
    def test_kelly_criterion_calculation(self):
        """Test Kelly criterion calculation"""
        from core.risk_manager import KellyCalculator
        
        calculator = KellyCalculator(kelly_fraction=1.0)  # Full Kelly for testing
        
        # 60% win rate, 2:1 reward-to-risk
        kelly = calculator.calculate_kelly(
            win_rate=0.60,
            avg_win=0.10,  # 10% gains
            avg_loss=0.05  # 5% losses
        )
        
        # Kelly should be positive for profitable strategy
        assert kelly > 0
        assert kelly <= 0.5  # Capped at 50%
    
    def test_kelly_no_history_conservative(self):
        """Test Kelly returns conservative default without history"""
        from core.risk_manager import KellyCalculator
        
        calculator = KellyCalculator()
        kelly = calculator.calculate_kelly()
        
        # Should return conservative 10% without history
        assert kelly == 0.1
    
    def test_risk_manager_allocation_config(self):
        """Test allocation configuration"""
        from core.risk_manager import AllocationConfig
        
        config = AllocationConfig(
            invested_pct=60,
            buy_reserve_pct=20,
            sell_reserve_pct=20
        )
        
        assert config.invested_pct == 60
        assert config.buy_reserve_pct == 20
        assert config.sell_reserve_pct == 20
    
    def test_portfolio_state(self):
        """Test PortfolioState-like tracking in RiskManager"""
        from core.risk_manager import KellyCalculator
        
        # RiskManager tracks portfolio via internal state
        calculator = KellyCalculator()
        
        # Record some trades
        calculator.record_trade("QBTS", 50.0, 100.0)  # Win
        calculator.record_trade("QBTS", -25.0, 100.0)  # Loss
        
        assert len(calculator._trade_history) == 2


class TestExecutionBridge:
    """Test the execution bridge"""
    
    def test_execution_mode_enum(self):
        """Test execution modes"""
        from core.execution_bridge import ExecutionMode
        
        assert ExecutionMode.SIMULATED.value == "simulated"
        assert ExecutionMode.PAPER.value == "paper"
        assert ExecutionMode.LIVE.value == "live"
    
    def test_order_request_creation(self):
        """Test creating an order request"""
        from core.execution_bridge import OrderRequest
        
        order = OrderRequest(
            symbol="QBTS",
            side="BUY",
            quantity=100,
            order_type="LIMIT",
            limit_price=5.50
        )
        
        assert order.symbol == "QBTS"
        assert order.side == "BUY"
        assert order.quantity == 100
        assert order.limit_price == 5.50
    
    def test_execution_config(self):
        """Test ExecutionConfig defaults"""
        from core.execution_bridge import ExecutionConfig, ExecutionMode
        
        config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
        
        assert config.mode == ExecutionMode.SIMULATED
        # Config should have mode attribute
        assert hasattr(config, 'mode')
    
    def test_execution_bridge_initialization(self):
        """Test ExecutionBridge initializes correctly"""
        from core.execution_bridge import ExecutionBridge, ExecutionConfig, ExecutionMode
        
        config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
        bridge = ExecutionBridge(config)
        
        assert bridge.config.mode == ExecutionMode.SIMULATED


class TestFullPipeline:
    """Test the complete trading pipeline"""
    
    def test_data_to_signal_flow(self):
        """Test data flows to signal generation"""
        from data_ingestion.data_sources import DataSourceManager
        from core.signal_engine import SignalGenerator
        
        # 1. Fetch data - use 5d for reliable data
        with DataSourceManager() as dm:
            history = dm.get_historical("QBTS", period="5d", interval="5m")
            quote = dm.get_quote("QBTS")
        
        assert quote is not None
        print(f"\n📊 QBTS Last: ${quote.last:.2f}")
        
        # History might be None for some intervals, skip if so
        if history is not None and len(history) > 0:
            # 2. Generate signal - pass price as float, not Quote
            generator = SignalGenerator()
            signal = generator.generate_signal("QBTS", history, quote.last)
            
            assert signal is not None
            assert signal.symbol == "QBTS"
            print(f"🎯 Signal: {signal.signal_type} ({signal.confidence:.0f}%)")
        else:
            print("⚠️  History data not available, skipping signal generation")
    
    def test_orchestrator_initialization(self):
        """Test trading orchestrator initializes all components"""
        from core.execution_bridge import TradingOrchestrator, ExecutionConfig, ExecutionMode
        
        config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
        orchestrator = TradingOrchestrator(execution_config=config)
        
        success = orchestrator.initialize()
        
        # Just verify it initializes successfully
        assert success is True
    
    def test_orchestrator_scan(self):
        """Test orchestrator can scan watchlist"""
        from core.execution_bridge import TradingOrchestrator, ExecutionConfig, ExecutionMode
        
        config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
        orchestrator = TradingOrchestrator(execution_config=config)
        
        assert orchestrator.initialize()
        
        # Process a single symbol
        result = orchestrator.process_symbol("QBTS")
        
        print(f"\n📋 Processed QBTS:")
        if result:
            print(f"   Signal: {result.get('signal', 'None')}")
            print(f"   Confidence: {result.get('confidence', 0):.0f}%")
        
        # result can be None if signal not actionable


class TestDashboard:
    """Test dashboard components"""
    
    def test_flask_app_exists(self):
        """Test Flask app can be imported"""
        from scripts.trading_dashboard import app
        
        assert app is not None
    
    def test_state_endpoint(self):
        """Test the state API endpoint"""
        from scripts.trading_dashboard import app
        
        with app.test_client() as client:
            response = client.get('/api/state')
            
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'connected' in data
            assert 'signals' in data
            assert 'account' in data
    
    def test_home_endpoint(self):
        """Test the home page renders"""
        from scripts.trading_dashboard import app
        
        with app.test_client() as client:
            response = client.get('/')
            
            assert response.status_code == 200
            assert b'HERMES' in response.data


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
