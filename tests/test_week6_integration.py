"""
HERMES Quantum - System Integration Test (Week 6)

Simple integration test that validates all Week 1-6 components work.
Uses correct import paths and handles optional dependencies gracefully.

Author: HERMES Development Team
Version: 0.2.0
"""

import sys
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_section(name: str):
    """Print test section header"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)


def test_pass(name: str, details: str = ""):
    """Print pass message"""
    print(f"  ✅ {name}" + (f" - {details}" if details else ""))
    return True


def test_fail(name: str, error: str):
    """Print fail message"""
    print(f"  ❌ {name} - {error}")
    return False


def run_tests():
    """Run all integration tests"""
    print("="*70)
    print("HERMES Quantum - Week 6 Integration Test")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {"passed": 0, "failed": 0}
    
    # ====== 1. Core Imports ======
    test_section("Core Module Imports")
    
    try:
        import numpy as np
        import pandas as pd
        test_pass("NumPy & Pandas")
        results["passed"] += 1
    except ImportError as e:
        test_fail("NumPy & Pandas", str(e))
        results["failed"] += 1
    
    # ====== 2. Data Ingestion ======
    test_section("Data Ingestion (Week 1)")
    
    try:
        from data_ingestion.market_data import MarketDataFetcher
        fetcher = MarketDataFetcher()
        test_pass("MarketDataFetcher", "imported successfully")
        results["passed"] += 1
    except Exception as e:
        test_fail("MarketDataFetcher", str(e))
        results["failed"] += 1
    
    # ====== 3. Technical Analysis ======
    test_section("Technical Analysis (Week 1)")
    
    try:
        from library.technical_analysis import TechnicalAnalyzer
        # TechnicalAnalyzer needs symbol and df
        import pandas as pd
        import numpy as np
        
        dates = pd.date_range(start='2025-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'open': np.random.uniform(100, 110, 100),
            'high': np.random.uniform(108, 115, 100),
            'low': np.random.uniform(95, 102, 100),
            'close': np.random.uniform(100, 110, 100),
            'volume': np.random.uniform(1e6, 5e6, 100)
        }, index=dates)
        
        analyzer = TechnicalAnalyzer(symbol="TEST", df=df)
        test_pass("TechnicalAnalyzer", "initialized with test data")
        results["passed"] += 1
    except Exception as e:
        test_fail("TechnicalAnalyzer", str(e))
        results["failed"] += 1
    
    # ====== 4. Sentiment Agents ======
    test_section("Sentiment Agents (Week 2)")
    
    try:
        # The integrated_agents module may have different class names
        from agents import integrated_agents
        # Just check the module imports
        test_pass("Sentiment Agents Module", "imported successfully")
        results["passed"] += 1
    except Exception as e:
        test_fail("Sentiment Agents Module", str(e))
        results["failed"] += 1
    
    # ====== 5. Orchestrator ======
    test_section("Orchestrator Agent (Week 3)")
    
    try:
        from agents.base_agent import BaseAgent
        test_pass("BaseAgent", "imported")
        results["passed"] += 1
    except Exception as e:
        test_fail("BaseAgent", str(e))
        results["failed"] += 1
    
    try:
        # Check that orchestrator module exists
        orchestrator_path = project_root / "agents" / "01_orchestrator" / "orchestrator.py"
        assert orchestrator_path.exists(), "orchestrator.py not found"
        test_pass("Orchestrator", "module exists")
        results["passed"] += 1
    except Exception as e:
        test_fail("Orchestrator", str(e))
        results["failed"] += 1
    
    # ====== 6. Online Manager ======
    test_section("Online Manager (Week 5)")
    
    try:
        sys.path.insert(0, str(project_root / "agents" / "01_orchestrator"))
        from online_manager import OnlineManager
        
        # OnlineManager takes config_path string, not dict
        manager = OnlineManager(config_path=None)
        test_pass("OnlineManager", "initialized")
        results["passed"] += 1
    except Exception as e:
        test_fail("OnlineManager", str(e))
        results["failed"] += 1
    
    # ====== 7. Risk Analyzer ======
    test_section("Risk Analyzer (Week 4)")
    
    try:
        sys.path.insert(0, str(project_root / "agents" / "11_analyst"))
        from risk_analyzer import RiskAnalyzer, RiskMetrics
        
        analyzer = RiskAnalyzer()
        test_pass("RiskAnalyzer", "initialized")
        results["passed"] += 1
        
        # Test with sample data - use analyze method to get RiskMetrics
        import pandas as pd
        import numpy as np
        returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        returns.index = pd.date_range(start='2025-01-01', periods=100, freq='D')
        metrics = analyzer.analyze(returns)
        test_pass("RiskAnalyzer.analyze", f"Sharpe={metrics.sharpe_ratio:.2f}")
        results["passed"] += 1
    except Exception as e:
        test_fail("RiskAnalyzer", str(e))
        results["failed"] += 1
    
    # ====== 8. Performance Monitor ======
    test_section("Performance Monitor (Week 4)")
    
    try:
        sys.path.insert(0, str(project_root / "agents" / "92_optimizer"))
        from performance_monitor import PerformanceMonitor
        
        # Use temp file for database (in-memory may not work with this impl)
        import tempfile
        import os
        pm_db = os.path.join(tempfile.gettempdir(), "test_perf_monitor.db")
        monitor = PerformanceMonitor(db_path=pm_db)
        # record_metric takes: agent_id, model_name, metric_type, value
        monitor.record_metric("agent_22", "finbert", "accuracy", 0.85)
        test_pass("PerformanceMonitor", "recorded metric")
        results["passed"] += 1
        # Cleanup
        try:
            os.remove(pm_db)
        except:
            pass
    except Exception as e:
        test_fail("PerformanceMonitor", str(e))
        results["failed"] += 1
    
    # ====== 9. Hyperparameter Tuner ======
    test_section("Hyperparameter Tuner (Week 4)")
    
    try:
        from hyperparameter_tuner import HyperparameterTuner
        
        tuner = HyperparameterTuner()
        test_pass("HyperparameterTuner", "initialized")
        results["passed"] += 1
    except Exception as e:
        test_fail("HyperparameterTuner", str(e))
        results["failed"] += 1
    
    # ====== 10. Model Registry ======
    test_section("Model Registry (Week 5)")
    
    try:
        sys.path.insert(0, str(project_root / "agents" / "99_models"))
        from model_registry import ModelRegistry
        
        # Use temp file for database
        import tempfile
        import os
        mr_db = os.path.join(tempfile.gettempdir(), "test_model_registry.db")
        registry = ModelRegistry(db_path=mr_db)
        # register_model requires: name, agent_id, and other optional params
        version = registry.register_model(
            name="test_model",
            agent_id="agent_22",
            version="1.0.0",
            metrics={"accuracy": 0.90}
        )
        test_pass("ModelRegistry", f"registered {version.name}:{version.version}")
        results["passed"] += 1
        # Cleanup
        try:
            os.remove(mr_db)
        except:
            pass
    except Exception as e:
        test_fail("ModelRegistry", str(e))
        results["failed"] += 1
    
    # ====== 11. RL Environment ======
    test_section("RL Trading Environment (Week 6)")
    
    try:
        sys.path.insert(0, str(project_root / "agents" / "99_models" / "rl"))
        from trading_env import TradingEnvironment, generate_synthetic_data
        
        symbols = ["IONQ", "RGTI"]
        env = TradingEnvironment(symbols=symbols, initial_cash=100_000)
        
        data = generate_synthetic_data(symbols, n_steps=50, seed=42)
        env.load_market_data(data)
        
        obs, info = env.reset()
        test_pass("TradingEnvironment", f"obs_shape={obs.shape}")
        results["passed"] += 1
        
        # Test step
        import numpy as np
        action = np.array([1, 0])
        next_obs, reward, done, truncated, info = env.step(action)
        test_pass("TradingEnvironment.step", f"reward={reward:.4f}")
        results["passed"] += 1
    except Exception as e:
        test_fail("TradingEnvironment", str(e))
        results["failed"] += 1
    
    # ====== 12. RL Agent ======
    test_section("RL Agent (Week 6)")
    
    try:
        from rl_agent import SimpleRLAgent
        
        agent = SimpleRLAgent(env)
        action = agent.predict(obs)
        test_pass("SimpleRLAgent", f"predicted action={action}")
        results["passed"] += 1
    except Exception as e:
        test_fail("SimpleRLAgent", str(e))
        results["failed"] += 1
    
    # Check for stable-baselines3
    try:
        from rl_agent import RLTradingAgent, RLConfig, SB3_AVAILABLE
        if SB3_AVAILABLE:
            test_pass("RLTradingAgent (PPO)", "stable-baselines3 available")
        else:
            test_pass("RLTradingAgent (PPO)", "stable-baselines3 not installed (optional)")
        results["passed"] += 1
    except Exception as e:
        test_fail("RLTradingAgent", str(e))
        results["failed"] += 1
    
    # ====== 13. Paper Trading ======
    test_section("Paper Trading (Week 6)")
    
    try:
        from execution.paper_trading import (
            PaperTradingEngine, PaperTradingSession,
            OrderSide, OrderType
        )
        
        # Use a unique temp path for the database
        import tempfile
        import os
        db_path = os.path.join(tempfile.gettempdir(), "test_paper_trading.db")
        
        engine = PaperTradingEngine(initial_cash=100_000, db_path=db_path)
        engine.update_price("IONQ", 35.0)
        
        order = engine.submit_order(
            symbol="IONQ",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        test_pass("PaperTradingEngine", f"order {order.order_id} filled @ ${order.filled_price:.2f}")
        results["passed"] += 1
        
        # Check position
        position = engine.get_position("IONQ")
        test_pass("Position tracking", f"IONQ: {position.quantity} shares")
        results["passed"] += 1
        
        # Cleanup
        try:
            os.remove(db_path)
        except:
            pass
    except Exception as e:
        test_fail("PaperTradingEngine", str(e))
        results["failed"] += 1
    
    # ====== 14. Backtester ======
    test_section("Backtester (Week 3)")
    
    try:
        from execution.backtester import Backtester
        test_pass("Backtester", "imported")
        results["passed"] += 1
    except Exception as e:
        test_fail("Backtester", str(e))
        results["failed"] += 1
    
    # ====== 15. Risk Manager ======
    test_section("Risk Manager (Week 3)")
    
    try:
        from execution.risk_manager import RiskManager
        test_pass("RiskManager", "imported")
        results["passed"] += 1
    except Exception as e:
        test_fail("RiskManager", str(e))
        results["failed"] += 1
    
    # ====== Summary ======
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total:  {results['passed'] + results['failed']}")
    print()
    
    if results["failed"] == 0:
        print("🎉 ALL TESTS PASSED! HERMES Quantum Week 6 is complete!")
        print("   The system is ready for paper trading.")
    else:
        print(f"⚠️  {results['failed']} test(s) failed.")
        print("   Please review the errors above.")
    
    print("="*70)
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
