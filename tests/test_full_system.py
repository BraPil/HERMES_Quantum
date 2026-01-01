"""
HERMES Quantum - Full System Integration Test

Tests the complete HERMES system from data ingestion through execution.
Validates Week 1-6 implementation.

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import numpy as np
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
)
logger = logging.getLogger("HERMES.IntegrationTest")


class TestResult:
    """Test result container"""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: str = ""
        self.details: Dict[str, Any] = {}
        self.duration: float = 0.0
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} | {self.name} ({self.duration:.2f}s)"


class IntegrationTestSuite:
    """Full integration test suite for HERMES Quantum"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time: datetime = None
    
    def run_all(self) -> bool:
        """Run all integration tests"""
        print("=" * 70)
        print("HERMES Quantum - Full System Integration Test")
        print("=" * 70)
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        self.start_time = datetime.now()
        
        # Run each test
        tests = [
            self.test_data_ingestion,
            self.test_sentiment_agents,
            self.test_technical_analysis,
            self.test_risk_analyzer,
            self.test_orchestrator,
            self.test_backtester,
            self.test_risk_manager,
            self.test_online_manager,
            self.test_performance_monitor,
            self.test_hyperparameter_tuner,
            self.test_model_registry,
            self.test_rl_environment,
            self.test_paper_trading,
        ]
        
        for test in tests:
            result = self._run_test(test)
            self.results.append(result)
        
        # Print summary
        self._print_summary()
        
        # Return True if all tests passed
        return all(r.passed for r in self.results)
    
    def _run_test(self, test_func) -> TestResult:
        """Run a single test"""
        result = TestResult(test_func.__name__.replace("test_", "").replace("_", " ").title())
        
        start = datetime.now()
        try:
            details = test_func()
            result.passed = True
            result.details = details or {}
        except Exception as e:
            result.passed = False
            result.error = str(e)
            logger.error(f"Test {test_func.__name__} failed: {e}")
        
        result.duration = (datetime.now() - start).total_seconds()
        
        # Print result
        print(result)
        
        return result
    
    def _print_summary(self):
        """Print test summary"""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Duration: {total_duration:.2f}s")
        print()
        
        if failed > 0:
            print("Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name}: {r.error}")
            print()
        
        if passed == len(self.results):
            print("🎉 ALL TESTS PASSED! HERMES Quantum is fully operational.")
        else:
            print(f"⚠️ {failed} test(s) failed. Please review the errors above.")
        
        print("=" * 70)
    
    # Test Methods
    
    def test_data_ingestion(self) -> Dict:
        """Test data ingestion module"""
        from data_ingestion import MarketDataFetcher
        
        fetcher = MarketDataFetcher(cache_dir="outputs/data/cache")
        
        # Test fetching
        df = fetcher.fetch_ohlcv("AAPL", period="5d")
        
        assert df is not None, "Failed to fetch data"
        assert len(df) > 0, "Empty dataframe returned"
        assert "close" in df.columns, "Missing close column"
        
        return {
            "rows": len(df),
            "columns": list(df.columns),
        }
    
    def test_sentiment_agents(self) -> Dict:
        """Test sentiment analysis agents"""
        from agents.integrated_agents import IntegratedAnalysisEngine
        
        engine = IntegratedAnalysisEngine()
        
        # Test text analysis
        text = "Quantum computing stocks surge on breakthrough news. IONQ up 15%!"
        
        result = engine.analyze_text(text)
        
        assert "sentiment" in result or "error" not in result, "Analysis failed"
        
        return result
    
    def test_technical_analysis(self) -> Dict:
        """Test technical analysis library"""
        from library.technical_analysis import TechnicalAnalyzer
        import pandas as pd
        
        # Create sample data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(108, 115, 100),
            'low': np.random.uniform(95, 102, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
        
        analyzer = TechnicalAnalyzer()
        result = analyzer.analyze(data)
        
        assert "rsi" in result, "Missing RSI"
        assert "macd" in result, "Missing MACD"
        
        return {
            "indicators": list(result.keys()),
        }
    
    def test_risk_analyzer(self) -> Dict:
        """Test risk analyzer"""
        from agents.agent_11_analyst import RiskAnalyzer
        import pandas as pd
        
        # Sample returns
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        
        analyzer = RiskAnalyzer()
        report = analyzer.generate_risk_report(returns)
        
        assert "sharpe_ratio" in report, "Missing Sharpe ratio"
        assert "max_drawdown" in report, "Missing max drawdown"
        
        return {
            "sharpe": report.get("sharpe_ratio", 0),
            "max_dd": report.get("max_drawdown", 0),
        }
    
    def test_orchestrator(self) -> Dict:
        """Test Agent 01 Orchestrator"""
        from agents.agent_01_orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        # Check methods exist
        assert hasattr(orch, "register_agent"), "Missing register_agent"
        assert hasattr(orch, "run"), "Missing run method"
        
        return {"status": "initialized"}
    
    def test_backtester(self) -> Dict:
        """Test backtesting framework"""
        from execution.backtester import Backtester
        import pandas as pd
        
        # Create sample signals and prices
        dates = pd.date_range(start='2025-01-01', periods=50, freq='D')
        prices = pd.DataFrame({
            'IONQ': np.cumsum(np.random.normal(0, 1, 50)) + 30,
            'RGTI': np.cumsum(np.random.normal(0, 0.5, 50)) + 10,
        }, index=dates)
        
        signals = pd.DataFrame({
            'IONQ': np.random.choice([1, 0, -1], 50),
            'RGTI': np.random.choice([1, 0, -1], 50),
        }, index=dates)
        
        backtester = Backtester(initial_capital=100_000)
        result = backtester.run(prices, signals)
        
        assert result is not None, "Backtest failed"
        assert hasattr(result, "total_return"), "Missing total_return"
        
        return {
            "total_return": result.total_return,
            "n_trades": result.n_trades,
        }
    
    def test_risk_manager(self) -> Dict:
        """Test risk manager"""
        from execution.risk_manager import RiskManager
        
        rm = RiskManager(max_position_pct=0.20, max_portfolio_risk=0.05)
        
        # Test position sizing
        size = rm.calculate_position_size(
            symbol="IONQ",
            price=35.0,
            portfolio_value=100_000,
            signal_strength=0.8
        )
        
        assert size > 0, "Invalid position size"
        assert size <= 100_000 * 0.20, "Position too large"
        
        return {"position_size": size}
    
    def test_online_manager(self) -> Dict:
        """Test online manager workflow"""
        from agents.agent_01_orchestrator import OnlineManager
        
        # Create simple workflow config
        config = {
            "name": "test_workflow",
            "stages": [
                {
                    "name": "test_stage",
                    "tasks": [
                        {"name": "test_task", "agent": "test"}
                    ]
                }
            ]
        }
        
        manager = OnlineManager(config)
        
        assert manager is not None, "Failed to create manager"
        
        return {"status": "initialized"}
    
    def test_performance_monitor(self) -> Dict:
        """Test performance monitor"""
        from agents.agent_92_optimizer import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Record some metrics
        monitor.record_metric("agent_22", "accuracy", 0.85)
        monitor.record_metric("agent_22", "f1_score", 0.82)
        
        # Get summary
        summary = monitor.get_agent_summary("agent_22")
        
        assert summary is not None, "No summary returned"
        
        return {"metrics_recorded": 2}
    
    def test_hyperparameter_tuner(self) -> Dict:
        """Test hyperparameter tuner"""
        from agents.agent_92_optimizer import HyperparameterTuner
        
        tuner = HyperparameterTuner()
        
        # Check initialization
        assert tuner is not None, "Failed to create tuner"
        
        return {"status": "initialized"}
    
    def test_model_registry(self) -> Dict:
        """Test model registry"""
        from agents.agent_99_models import ModelRegistry
        
        registry = ModelRegistry(db_path=":memory:")
        
        # Register a model
        version = registry.register_model(
            name="test_model",
            version="1.0.0",
            metrics={"accuracy": 0.90}
        )
        
        assert version is not None, "Failed to register model"
        
        # List models
        models = registry.list_models()
        
        assert len(models) > 0, "No models found"
        
        return {"models_registered": len(models)}
    
    def test_rl_environment(self) -> Dict:
        """Test RL trading environment"""
        from agents.agent_99_models.rl import TradingEnvironment, generate_synthetic_data
        
        symbols = ["IONQ", "RGTI"]
        env = TradingEnvironment(symbols=symbols, initial_cash=100_000)
        
        # Generate data
        data = generate_synthetic_data(symbols, n_steps=50, seed=42)
        env.load_market_data(data)
        
        # Run episode
        obs, info = env.reset()
        
        assert obs is not None, "No observation returned"
        assert len(obs) > 0, "Empty observation"
        
        # Take a step
        action = np.array([1, 0])  # Buy first, hold second
        next_obs, reward, done, truncated, info = env.step(action)
        
        assert next_obs is not None, "Step failed"
        
        stats = env.get_episode_stats()
        
        return {
            "obs_size": len(obs),
            "step_worked": True,
        }
    
    def test_paper_trading(self) -> Dict:
        """Test paper trading engine"""
        from execution.paper_trading import PaperTradingEngine, OrderSide, OrderType
        
        engine = PaperTradingEngine(initial_cash=100_000)
        
        # Update price
        engine.update_price("IONQ", 35.0)
        
        # Submit order
        order = engine.submit_order(
            symbol="IONQ",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        assert order is not None, "Order failed"
        assert order.status.value == "FILLED", "Order not filled"
        
        # Check position
        position = engine.get_position("IONQ")
        
        assert position is not None, "No position created"
        assert position.quantity == 100, "Wrong quantity"
        
        return {
            "order_id": order.order_id,
            "position_qty": position.quantity,
        }


# Simplified import test (for quick validation)
def test_imports() -> bool:
    """Test that all major modules can be imported"""
    print("Testing imports...")
    
    imports = [
        ("data_ingestion.market_data", ["MarketDataFetcher"]),
        ("library.technical_analysis", ["TechnicalAnalyzer"]),
        ("agents.integrated_agents", ["IntegratedSentimentAnalyzer"]),
        ("agents.01_orchestrator", ["Orchestrator", "OnlineManager"]),
        ("agents.11_analyst", ["RiskAnalyzer"]),
        ("agents.92_optimizer", ["PerformanceMonitor", "HyperparameterTuner"]),
        ("agents.99_models", ["ModelRegistry"]),
        ("execution.backtester", ["Backtester"]),
        ("execution.risk_manager", ["RiskManager"]),
        ("execution.paper_trading", ["PaperTradingEngine"]),
    ]
    
    all_passed = True
    
    for module_name, classes in imports:
        try:
            module = __import__(module_name, fromlist=classes)
            for cls in classes:
                if hasattr(module, cls):
                    print(f"  ✅ {module_name}.{cls}")
                else:
                    print(f"  ❌ {module_name}.{cls} - not found")
                    all_passed = False
        except ImportError as e:
            print(f"  ❌ {module_name} - {e}")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    # Quick import test first
    print("=" * 70)
    print("Quick Import Test")
    print("=" * 70)
    
    imports_ok = test_imports()
    print()
    
    if not imports_ok:
        print("⚠️ Some imports failed. Running available tests...")
        print()
    
    # Run full test suite
    suite = IntegrationTestSuite()
    success = suite.run_all()
    
    # Exit code
    sys.exit(0 if success else 1)
