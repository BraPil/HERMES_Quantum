#!/usr/bin/env python3
"""
HERMES Quantum - Agent 01 Orchestrator Runner
==============================================
Runs the event-driven orchestrator with all specialist agents.

This is the new orchestrator implementation using:
- Event bus for async communication
- Agent adapters for specialist agent integration
- Decision maker with signal aggregation
- Prediction tracker with SQLite storage
- Learning engine for weight adjustment

Usage:
    python scripts/run_orchestrator.py
    python scripts/run_orchestrator.py --tickers QBTS,IONQ,RGTI
    python scripts/run_orchestrator.py --cycles 5
    python scripts/run_orchestrator.py --continuous
    
Created: 2026-01-01
"""

import asyncio
import argparse
import logging
import sys
import os
import signal
from datetime import datetime
from typing import List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Must use importlib for numeric-prefixed module
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger('yfinance').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)


# Default quantum computing tickers
DEFAULT_TICKERS = ["QBTS", "IONQ", "RGTI", "QUBT"]


class OrchestratorRunner:
    """
    Runner for the Agent 01 Orchestrator with all specialist agents.
    """
    
    def __init__(
        self,
        tickers: Optional[List[str]] = None,
        update_interval: float = 60.0
    ):
        self.tickers = tickers or DEFAULT_TICKERS
        self.update_interval = update_interval
        self.orchestrator = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize the orchestrator and all agent adapters."""
        logger.info("="*60)
        logger.info("HERMES Quantum Orchestrator - Initializing")
        logger.info("="*60)
        
        # Import orchestrator module
        orchestrator_mod = importlib.import_module('agents.01_orchestrator.orchestrator')
        adapters_mod = importlib.import_module('agents.01_orchestrator.agent_adapters')
        
        # Create orchestrator
        self.orchestrator = orchestrator_mod.Orchestrator(
            tickers=self.tickers,
            update_interval=self.update_interval
        )
        
        # Create and register all adapters
        logger.info("Creating agent adapters...")
        adapters = adapters_mod.create_all_adapters()
        
        for name, adapter in adapters.items():
            # Create runner closure that captures the adapter
            def make_runner(adpt):
                async def run(tickers_arg):
                    return await adpt.run(tickers_arg)
                return run
            
            runner = make_runner(adapter)
            self.orchestrator.register_agent(name, runner)
            logger.info(f"  Registered: {name}")
        
        logger.info(f"Initialized with {len(adapters)} agents for {len(self.tickers)} tickers")
        logger.info("="*60)
        
    async def run_single_cycle(self):
        """Run a single orchestration cycle."""
        if not self.orchestrator:
            await self.initialize()
            
        await self.orchestrator.start()
        await self.orchestrator._run_cycle()
        
        # Get and display results
        dashboard = self.orchestrator.get_dashboard_data()
        self._print_dashboard(dashboard)
        
        await self.orchestrator.stop()
        
    async def run_cycles(self, num_cycles: int):
        """Run a specific number of cycles."""
        if not self.orchestrator:
            await self.initialize()
            
        await self.orchestrator.start()
        
        for i in range(num_cycles):
            logger.info(f"\n--- Cycle {i+1}/{num_cycles} ---")
            await self.orchestrator._run_cycle()
            
            # Short delay between cycles
            if i < num_cycles - 1:
                await asyncio.sleep(2)
        
        dashboard = self.orchestrator.get_dashboard_data()
        self._print_dashboard(dashboard)
        
        await self.orchestrator.stop()
        
    async def run_continuous(self):
        """Run continuously until interrupted."""
        if not self.orchestrator:
            await self.initialize()
        
        logger.info("\nStarting continuous operation (Ctrl+C to stop)...")
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig, 
                lambda: asyncio.create_task(self._handle_shutdown())
            )
        
        self._running = True
        await self.orchestrator.start()
        
        try:
            while self._running and not self._shutdown_event.is_set():
                await self.orchestrator._run_cycle()
                
                # Print status every 5 cycles
                if self.orchestrator._cycle_count % 5 == 0:
                    dashboard = self.orchestrator.get_dashboard_data()
                    self._print_summary(dashboard)
                
                # Wait for next cycle
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            logger.info("Received shutdown signal")
        finally:
            await self.orchestrator.stop()
            
        # Final report
        dashboard = self.orchestrator.get_dashboard_data()
        self._print_dashboard(dashboard)
        
    async def _handle_shutdown(self):
        """Handle shutdown signal."""
        logger.info("\nShutting down...")
        self._running = False
        self._shutdown_event.set()
        
    def _print_summary(self, dashboard):
        """Print a brief status summary."""
        print(f"\n[Cycle {dashboard.stats.get('cycles', 0)}] "
              f"Decisions: {dashboard.stats.get('decisions_made', 0)} | "
              f"Events: {dashboard.stats.get('events_processed', 0)} | "
              f"Errors: {dashboard.stats.get('errors', 0)}")
        
    def _print_dashboard(self, dashboard):
        """Print formatted dashboard data."""
        print("\n" + "="*60)
        print("HERMES QUANTUM - Trading Dashboard")
        print("="*60)
        
        print(f"\nStatus: {dashboard.status}")
        print(f"Last Update: {dashboard.last_update}")
        
        stats = dashboard.stats
        print(f"\nStatistics:")
        print(f"  Cycles: {stats.get('cycles', 0)}")
        print(f"  Decisions Made: {stats.get('decisions_made', 0)}")
        print(f"  Events Processed: {stats.get('events_processed', 0)}")
        print(f"  Predictions Stored: {stats.get('predictions_stored', 0)}")
        print(f"  Errors: {stats.get('errors', 0)}")
        
        if dashboard.decisions:
            print(f"\n{'='*60}")
            print("TRADING DECISIONS")
            print("="*60)
            
            for ticker, decision in dashboard.decisions.items():
                action = decision.get('action', 'UNKNOWN')
                strength = decision.get('action_strength', 'N/A')
                conviction = decision.get('conviction', 0)
                price = decision.get('current_price', 0)
                
                # Normalize conviction if it's > 1 (already a percentage)
                if conviction > 1:
                    conviction = conviction / 100.0
                
                # Action color
                if action == 'BUY':
                    icon = '🟢'
                elif action == 'SELL':
                    icon = '🔴'
                else:
                    icon = '⚪'
                
                print(f"\n{icon} {ticker}: {action} ({strength})")
                print(f"   Current Price: ${price:.2f}")
                print(f"   Conviction: {conviction:.0%}")
                
                # Buy/Sell targets
                buy_targets = decision.get('buy_targets', [])
                sell_targets = decision.get('sell_targets', [])
                
                if buy_targets:
                    print(f"   Buy Targets:")
                    for t in buy_targets[:2]:
                        print(f"      ${t.get('price', 0):.2f} ({t.get('label', 'N/A')})")
                        
                if sell_targets:
                    print(f"   Sell Targets:")
                    for t in sell_targets[:2]:
                        print(f"      ${t.get('price', 0):.2f} ({t.get('label', 'N/A')})")
                
                # Contributing signals
                signals = decision.get('contributing_signals', [])
                if signals:
                    print(f"   Contributing Signals: {len(signals)}")
                    for s in signals[:3]:
                        src = s.get('source', 'N/A')
                        val = s.get('value', 0)
                        conf = s.get('confidence', 0)
                        print(f"      - {src}: {val:+.2f} (conf: {conf:.0%})")
        
        if dashboard.accuracy:
            print(f"\n{'='*60}")
            print("ACCURACY METRICS")
            print("="*60)
            
            # Show key timeframes
            for timeframe in ['24h', '7d', '28d']:
                if timeframe in dashboard.accuracy:
                    metrics = dashboard.accuracy[timeframe]
                    total = metrics.get('total_predictions', 0)
                    validated = metrics.get('validated_predictions', 0)
                    accuracy = metrics.get('direction_accuracy', 0)
                    
                    if total > 0:
                        print(f"\n{timeframe}: {validated}/{total} validated ({accuracy:.0%} accuracy)")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="HERMES Quantum Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--tickers',
        type=str,
        default=','.join(DEFAULT_TICKERS),
        help=f'Comma-separated list of tickers (default: {",".join(DEFAULT_TICKERS)})'
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=1,
        help='Number of cycles to run (default: 1)'
    )
    
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously until interrupted'
    )
    
    parser.add_argument(
        '--interval',
        type=float,
        default=60.0,
        help='Update interval in seconds (default: 60)'
    )
    
    args = parser.parse_args()
    
    # Parse tickers
    tickers = [t.strip().upper() for t in args.tickers.split(',')]
    
    # Create runner
    runner = OrchestratorRunner(
        tickers=tickers,
        update_interval=args.interval
    )
    
    # Run
    if args.continuous:
        asyncio.run(runner.run_continuous())
    elif args.cycles == 1:
        asyncio.run(runner.run_single_cycle())
    else:
        asyncio.run(runner.run_cycles(args.cycles))


if __name__ == "__main__":
    main()
