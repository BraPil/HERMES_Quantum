#!/usr/bin/env python3
"""
HERMES Live Trading Session Logger
===================================

Monitors quantum stocks and logs key trading signals to the terminal
and to a timestamped log file for later analysis.

Usage:
    python scripts/live_logger.py --symbols QBTS IONQ --interval 30

Author: HERMES Project
Date: December 2025
"""

import sys
import os
import time
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_ingestion.market_data import MarketDataFetcher
from library.technical_analysis import TechnicalAnalyzer
from library.order_flow_ml import OrderFlowMLEstimator

# Configure logging
def setup_logging(log_file: Optional[str] = None):
    """Set up console and file logging"""
    
    # Suppress noisy third-party loggers FIRST
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('peewee').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('data_ingestion').setLevel(logging.WARNING)
    
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    if log_file is None:
        log_file = os.path.join(log_dir, f"trading_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging format
    log_format = "%(asctime)s | %(message)s"
    date_format = "%H:%M:%S"
    
    # Console handler with colors - only show our messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(log_format, date_format))
    
    # File handler - capture more for post-session review
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Only configure our logger, not the root
    logger = logging.getLogger('__main__')
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Clear any existing
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False  # Don't propagate to root
    
    return logger, log_file


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for terminal output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[37m',     # White
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
        'BUY': '\033[32m',      # Green
        'SELL': '\033[31m',     # Red
        'HOLD': '\033[33m',     # Yellow
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color based on level or signal type
        if hasattr(record, 'signal'):
            color = self.COLORS.get(record.signal, self.COLORS['INFO'])
        else:
            color = self.COLORS.get(record.levelname, self.COLORS['INFO'])
        
        message = super().format(record)
        return f"{color}{message}{self.RESET}"


class LiveTradingLogger:
    """Live trading session monitor and logger"""
    
    def __init__(self, symbols: list, interval: int = 30):
        """
        Initialize the logger
        
        Args:
            symbols: List of stock symbols to monitor
            interval: Refresh interval in seconds
        """
        self.symbols = symbols
        self.interval = interval
        self.fetcher = MarketDataFetcher()
        self.logger = logging.getLogger(__name__)
        
        # Track previous signals to detect changes
        self.previous_signals: Dict[str, Any] = {}
        self.previous_prices: Dict[str, float] = {}
        
    def run(self):
        """Run the live monitoring loop"""
        self.logger.info("=" * 70)
        self.logger.info("🔮 HERMES QUANTUM LIVE TRADING SESSION STARTED")
        self.logger.info(f"📊 Monitoring: {', '.join(self.symbols)}")
        self.logger.info(f"⏱️  Refresh: {self.interval} seconds")
        self.logger.info("=" * 70)
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                self.logger.info(f"\n{'─' * 50}")
                self.logger.info(f"📡 Scan #{iteration} at {datetime.now().strftime('%H:%M:%S')}")
                self.logger.info(f"{'─' * 50}")
                
                for symbol in self.symbols:
                    self._analyze_symbol(symbol)
                
                # Wait for next interval
                self.logger.debug(f"Sleeping {self.interval}s until next scan...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n" + "=" * 70)
            self.logger.info("🛑 LIVE SESSION ENDED BY USER")
            self.logger.info("=" * 70)
    
    def _analyze_symbol(self, symbol: str):
        """Analyze a single symbol and log findings"""
        try:
            # Fetch data
            quote = self.fetcher.get_quote(symbol)
            history = self.fetcher.get_historical(symbol, period="3mo")
            
            if history is None or len(history.data) == 0:
                self.logger.warning(f"{symbol}: No data available")
                return
            
            df = history.data
            current_price = df['close'].iloc[-1]
            
            # Run technical analysis
            analyzer = TechnicalAnalyzer(symbol, df)
            result = analyzer.analyze()
            
            # Run order flow analysis
            of_estimator = OrderFlowMLEstimator(df)
            of_prediction = of_estimator.predict_order_flow()
            
            # Check for signal changes
            prev_signal = self.previous_signals.get(symbol)
            prev_price = self.previous_prices.get(symbol)
            
            signal_changed = prev_signal != result.overall_signal
            
            # Calculate price change
            if prev_price:
                price_change = ((current_price - prev_price) / prev_price) * 100
                price_arrow = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
            else:
                price_change = 0
                price_arrow = "🆕"
            
            # Log the analysis
            signal_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(result.overall_signal, "⚪")
            
            self.logger.info(
                f"{signal_emoji} {symbol}: ${current_price:.2f} {price_arrow} ({price_change:+.2f}%) | "
                f"Signal: {result.overall_signal} ({result.signal_strength:.0f}%) | "
                f"RSI: {result.indicators.rsi_14:.1f} | "
                f"Flow: {of_prediction.predicted_direction.upper()}"
            )
            
            # Log signal change alert
            if signal_changed and prev_signal is not None:
                self.logger.warning(
                    f"⚠️  SIGNAL CHANGE: {symbol} {prev_signal} → {result.overall_signal}"
                )
            
            # Log key support/resistance levels
            if result.support_levels:
                nearest_support = result.support_levels[0].price
                support_dist = ((current_price - nearest_support) / current_price) * 100
                if support_dist < 3:  # Within 3% of support
                    self.logger.info(f"   📍 Near support: ${nearest_support:.2f} ({support_dist:.1f}% away)")
            
            if result.resistance_levels:
                nearest_resist = result.resistance_levels[0].price
                resist_dist = ((nearest_resist - current_price) / current_price) * 100
                if resist_dist < 3:  # Within 3% of resistance
                    self.logger.info(f"   📍 Near resistance: ${nearest_resist:.2f} ({resist_dist:.1f}% away)")
            
            # Log active patterns
            for pattern in result.patterns[:2]:  # Top 2 patterns
                self.logger.debug(
                    f"   📐 Pattern: {pattern.pattern_type.value.replace('_', ' ').title()} "
                    f"({pattern.confidence:.0f}%)"
                )
            
            # Log order flow walls
            buy_walls = [w for w in of_prediction.estimated_walls[:3] if w.wall_type.value == "buy_wall"]
            sell_walls = [w for w in of_prediction.estimated_walls[:3] if w.wall_type.value == "sell_wall"]
            
            if buy_walls:
                self.logger.debug(f"   🏰 Buy wall: ${buy_walls[0].price:.2f} ({buy_walls[0].strength:.0f}%)")
            if sell_walls:
                self.logger.debug(f"   🏰 Sell wall: ${sell_walls[0].price:.2f} ({sell_walls[0].strength:.0f}%)")
            
            # Update tracking
            self.previous_signals[symbol] = result.overall_signal
            self.previous_prices[symbol] = current_price
            
        except Exception as e:
            self.logger.error(f"{symbol}: Analysis failed - {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="HERMES Live Trading Logger")
    parser.add_argument(
        "--symbols", "-s",
        nargs="+",
        default=["QBTS", "IONQ", "RGTI"],
        help="Stock symbols to monitor"
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="Refresh interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--log-file", "-l",
        help="Custom log file path"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    logger, log_file = setup_logging(args.log_file)
    logger.info(f"📁 Logging to: {log_file}")
    
    # Create and run the logger
    live_logger = LiveTradingLogger(
        symbols=args.symbols,
        interval=args.interval
    )
    live_logger.run()


if __name__ == "__main__":
    main()
