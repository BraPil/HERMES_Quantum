#!/usr/bin/env python3
"""
Trading Signal Engine
======================
Generates BUY/SELL signals with confidence scores for quantum stocks.

Features:
- Multi-factor signal generation (technical, momentum, volatility)
- Confidence scoring (0-100%)
- Breaking news alert detection
- Signal history tracking

Author: HERMES Development Team
Version: 0.1.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
import json

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class SignalType(Enum):
    """Signal type"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalUrgency(Enum):
    """Signal urgency level"""
    LOW = "low"           # Can wait, limit order
    MEDIUM = "medium"     # Execute soon
    HIGH = "high"         # Execute now
    BREAKING = "breaking" # Manual popup needed!


@dataclass
class Signal:
    """Trading signal with confidence"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 0-100%
    urgency: SignalUrgency
    price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reason: str = ""
    factors: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_actionable(self) -> bool:
        """Check if signal meets confidence threshold (85%)"""
        return self.confidence >= 85.0 and self.signal_type != SignalType.HOLD
    
    @property
    def is_breaking(self) -> bool:
        """Check if this is a breaking news alert"""
        return self.urgency == SignalUrgency.BREAKING
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "signal": self.signal_type.value,
            "confidence": round(self.confidence, 1),
            "urgency": self.urgency.value,
            "price": self.price,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "reason": self.reason,
            "factors": self.factors,
            "timestamp": self.timestamp.isoformat(),
            "actionable": self.is_actionable
        }
    
    def __str__(self) -> str:
        emoji = {
            SignalType.STRONG_BUY: "🚀",
            SignalType.BUY: "📈",
            SignalType.HOLD: "⏸️",
            SignalType.SELL: "📉",
            SignalType.STRONG_SELL: "🔻"
        }
        return (
            f"{emoji.get(self.signal_type, '?')} {self.symbol}: "
            f"{self.signal_type.value} @ ${self.price:.2f} "
            f"({self.confidence:.0f}% confidence)"
        )


@dataclass
class MarketRegime:
    """Market regime classification"""
    trend: str  # "rising", "falling", "sideways"
    strength: float  # 0-100%
    volatility: str  # "low", "normal", "high"
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================

class TechnicalIndicators:
    """Calculate technical indicators for signal generation"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        """MACD indicator"""
        ema12 = data.ewm(span=12, adjust=False).mean()
        ema26 = data.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
        """Volume ratio vs average"""
        avg_volume = volume.rolling(window=period).mean()
        return volume / avg_volume


# =============================================================================
# SIGNAL GENERATOR
# =============================================================================

class SignalGenerator:
    """
    Generates trading signals based on multiple factors.
    
    Usage:
        generator = SignalGenerator()
        signal = generator.generate_signal("QBTS", df)
        if signal.is_actionable:
            print(f"Execute: {signal}")
    """
    
    # Confidence thresholds
    MIN_CONFIDENCE = 50.0
    ACTIONABLE_CONFIDENCE = 85.0
    
    # Signal weights
    WEIGHTS = {
        "trend": 0.25,
        "momentum": 0.25,
        "mean_reversion": 0.20,
        "volume": 0.15,
        "volatility": 0.15
    }
    
    def __init__(self, watchlist: Optional[list[str]] = None):
        self.watchlist = watchlist or ["QBTS", "IONQ", "RGTI", "QUBT"]
        self.signal_history: list[Signal] = []
        self._callbacks: list[Callable[[Signal], None]] = []
    
    def on_signal(self, callback: Callable[[Signal], None]):
        """Register a callback for new signals"""
        self._callbacks.append(callback)
    
    def _notify_signal(self, signal: Signal):
        """Notify all callbacks of a new signal"""
        for callback in self._callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
    
    def _analyze_trend(self, df: pd.DataFrame) -> dict:
        """
        Analyze price trend.
        Returns: {score: -100 to 100, signal: BUY/SELL/HOLD}
        """
        close = df['close']
        
        # Short and long term EMAs
        ema_short = TechnicalIndicators.ema(close, 9).iloc[-1]
        ema_long = TechnicalIndicators.ema(close, 21).iloc[-1]
        current_price = close.iloc[-1]
        
        # Price position relative to EMAs
        above_short = current_price > ema_short
        above_long = current_price > ema_long
        ema_bullish = ema_short > ema_long
        
        # Calculate score
        score = 0
        if above_short:
            score += 25
        else:
            score -= 25
        
        if above_long:
            score += 25
        else:
            score -= 25
        
        if ema_bullish:
            score += 50
        else:
            score -= 50
        
        return {
            "score": score,
            "signal": SignalType.BUY if score > 30 else (SignalType.SELL if score < -30 else SignalType.HOLD),
            "ema_short": ema_short,
            "ema_long": ema_long,
            "price": current_price
        }
    
    def _analyze_momentum(self, df: pd.DataFrame) -> dict:
        """
        Analyze momentum using RSI and MACD.
        Returns: {score: -100 to 100, signal: BUY/SELL/HOLD}
        """
        close = df['close']
        
        # RSI
        rsi = TechnicalIndicators.rsi(close).iloc[-1]
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(close)
        macd_current = histogram.iloc[-1]
        macd_prev = histogram.iloc[-2] if len(histogram) > 1 else 0
        macd_rising = macd_current > macd_prev
        
        # Score based on RSI
        if rsi < 30:
            rsi_score = 50  # Oversold = bullish
        elif rsi > 70:
            rsi_score = -50  # Overbought = bearish
        else:
            rsi_score = (50 - rsi) * 1  # Neutral zone
        
        # Score based on MACD
        macd_score = 25 if macd_current > 0 else -25
        macd_score += 25 if macd_rising else -25
        
        total_score = (rsi_score + macd_score) / 2
        
        return {
            "score": total_score,
            "signal": SignalType.BUY if total_score > 30 else (SignalType.SELL if total_score < -30 else SignalType.HOLD),
            "rsi": rsi,
            "macd": macd_current,
            "macd_rising": macd_rising
        }
    
    def _analyze_mean_reversion(self, df: pd.DataFrame) -> dict:
        """
        Analyze mean reversion using Bollinger Bands.
        Returns: {score: -100 to 100, signal: BUY/SELL/HOLD}
        """
        close = df['close']
        current_price = close.iloc[-1]
        
        upper, middle, lower = TechnicalIndicators.bollinger_bands(close)
        upper_val = upper.iloc[-1]
        middle_val = middle.iloc[-1]
        lower_val = lower.iloc[-1]
        
        # Calculate position within bands (0 = lower, 1 = upper)
        band_width = upper_val - lower_val
        if band_width > 0:
            position = (current_price - lower_val) / band_width
        else:
            position = 0.5
        
        # Score: near lower band = bullish, near upper = bearish
        score = (0.5 - position) * 200  # Scale to -100 to 100
        
        # Clamp score
        score = max(-100, min(100, score))
        
        return {
            "score": score,
            "signal": SignalType.BUY if score > 30 else (SignalType.SELL if score < -30 else SignalType.HOLD),
            "bb_position": position,
            "bb_upper": upper_val,
            "bb_lower": lower_val
        }
    
    def _analyze_volume(self, df: pd.DataFrame) -> dict:
        """
        Analyze volume patterns.
        Returns: {score: -100 to 100, signal: BUY/SELL/HOLD}
        """
        close = df['close']
        volume = df['volume']
        
        # Volume ratio
        vol_ratio = TechnicalIndicators.volume_ratio(volume).iloc[-1]
        
        # Price change
        price_change = (close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        
        # High volume + rising price = bullish
        # High volume + falling price = bearish
        if vol_ratio > 1.5:  # Above average volume
            if price_change > 0:
                score = min(50 + (vol_ratio - 1) * 25, 100)
            else:
                score = max(-50 - (vol_ratio - 1) * 25, -100)
        else:
            score = price_change * 5  # Low volume, follow price
        
        return {
            "score": score,
            "signal": SignalType.BUY if score > 30 else (SignalType.SELL if score < -30 else SignalType.HOLD),
            "volume_ratio": vol_ratio,
            "price_change": price_change
        }
    
    def _analyze_volatility(self, df: pd.DataFrame) -> dict:
        """
        Analyze volatility for opportunity detection.
        Returns: {score: -100 to 100, signal: BUY/SELL/HOLD}
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # ATR
        atr = TechnicalIndicators.atr(high, low, close).iloc[-1]
        atr_pct = (atr / close.iloc[-1]) * 100
        
        # Volatility assessment
        if atr_pct > 5:
            volatility = "high"
            vol_score = 0  # High volatility = cautious
        elif atr_pct > 2:
            volatility = "normal"
            vol_score = 25
        else:
            volatility = "low"
            vol_score = 50  # Low volatility = good entry
        
        # Combine with recent momentum
        recent_move = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] * 100 if len(close) >= 5 else 0
        
        score = vol_score * (1 if recent_move > 0 else -1)
        
        return {
            "score": score,
            "signal": SignalType.HOLD,  # Volatility alone doesn't drive direction
            "atr_pct": atr_pct,
            "volatility": volatility,
            "recent_move": recent_move
        }
    
    def generate_signal(self, symbol: str, df: pd.DataFrame, current_price: Optional[float] = None) -> Signal:
        """
        Generate trading signal for a symbol.
        
        Args:
            symbol: Stock symbol
            df: OHLCV DataFrame with columns: open, high, low, close, volume
            current_price: Override price (if real-time differs from df)
            
        Returns:
            Signal with confidence and recommendation
        """
        if len(df) < 30:
            return Signal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                confidence=0,
                urgency=SignalUrgency.LOW,
                price=current_price or df['close'].iloc[-1],
                reason="Insufficient data for analysis"
            )
        
        # Run all analyses
        trend = self._analyze_trend(df)
        momentum = self._analyze_momentum(df)
        mean_rev = self._analyze_mean_reversion(df)
        volume = self._analyze_volume(df)
        volatility = self._analyze_volatility(df)
        
        # Calculate weighted score
        weighted_score = (
            trend["score"] * self.WEIGHTS["trend"] +
            momentum["score"] * self.WEIGHTS["momentum"] +
            mean_rev["score"] * self.WEIGHTS["mean_reversion"] +
            volume["score"] * self.WEIGHTS["volume"] +
            volatility["score"] * self.WEIGHTS["volatility"]
        )
        
        # Determine signal type
        if weighted_score > 50:
            signal_type = SignalType.STRONG_BUY
        elif weighted_score > 25:
            signal_type = SignalType.BUY
        elif weighted_score < -50:
            signal_type = SignalType.STRONG_SELL
        elif weighted_score < -25:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # Calculate confidence (normalize score to 0-100)
        confidence = min(100, max(0, abs(weighted_score) + 50))
        
        # Determine urgency
        if abs(weighted_score) > 75 and volatility["volatility"] == "high":
            urgency = SignalUrgency.HIGH
        elif abs(weighted_score) > 50:
            urgency = SignalUrgency.MEDIUM
        else:
            urgency = SignalUrgency.LOW
        
        price = current_price or df['close'].iloc[-1]
        
        # Calculate target and stop loss
        atr = volatility.get("atr_pct", 2) / 100 * price
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            target_price = price + (atr * 2)
            stop_loss = price - (atr * 1.5)
        elif signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            target_price = price - (atr * 2)
            stop_loss = price + (atr * 1.5)
        else:
            target_price = None
            stop_loss = None
        
        # Build reason
        reasons = []
        if trend["score"] > 30:
            reasons.append("Strong uptrend")
        elif trend["score"] < -30:
            reasons.append("Downtrend")
        
        if momentum["rsi"] < 30:
            reasons.append(f"Oversold (RSI={momentum['rsi']:.0f})")
        elif momentum["rsi"] > 70:
            reasons.append(f"Overbought (RSI={momentum['rsi']:.0f})")
        
        if mean_rev["bb_position"] < 0.2:
            reasons.append("Near lower Bollinger Band")
        elif mean_rev["bb_position"] > 0.8:
            reasons.append("Near upper Bollinger Band")
        
        if volume["volume_ratio"] > 1.5:
            reasons.append(f"High volume ({volume['volume_ratio']:.1f}x avg)")
        
        signal = Signal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            urgency=urgency,
            price=price,
            target_price=target_price,
            stop_loss=stop_loss,
            reason="; ".join(reasons) if reasons else "Mixed signals",
            factors={
                "trend": trend,
                "momentum": momentum,
                "mean_reversion": mean_rev,
                "volume": volume,
                "volatility": volatility,
                "weighted_score": weighted_score
            }
        )
        
        # Track history
        self.signal_history.append(signal)
        
        # Notify callbacks
        if signal.is_actionable:
            self._notify_signal(signal)
        
        return signal
    
    def generate_signals(self, data: dict[str, pd.DataFrame]) -> dict[str, Signal]:
        """
        Generate signals for multiple symbols.
        
        Args:
            data: Dict of symbol -> OHLCV DataFrame
            
        Returns:
            Dict of symbol -> Signal
        """
        signals = {}
        for symbol, df in data.items():
            signals[symbol] = self.generate_signal(symbol, df)
        return signals
    
    def get_actionable_signals(self) -> list[Signal]:
        """Get signals that meet the 85% confidence threshold"""
        return [s for s in self.signal_history if s.is_actionable]
    
    def classify_market_regime(self, df: pd.DataFrame) -> MarketRegime:
        """
        Classify current market regime.
        
        Args:
            df: Market index or aggregate data
            
        Returns:
            MarketRegime with trend and volatility assessment
        """
        close = df['close']
        
        # Trend analysis
        sma20 = TechnicalIndicators.sma(close, 20).iloc[-1]
        sma50 = TechnicalIndicators.sma(close, 50).iloc[-1]
        current = close.iloc[-1]
        
        # Determine trend
        if current > sma20 > sma50:
            trend = "rising"
            strength = min(100, ((current - sma50) / sma50) * 200)
        elif current < sma20 < sma50:
            trend = "falling"
            strength = min(100, ((sma50 - current) / sma50) * 200)
        else:
            trend = "sideways"
            strength = 50
        
        # Volatility analysis
        atr = TechnicalIndicators.atr(df['high'], df['low'], close).iloc[-1]
        atr_pct = (atr / current) * 100
        
        if atr_pct > 4:
            volatility = "high"
        elif atr_pct > 2:
            volatility = "normal"
        else:
            volatility = "low"
        
        return MarketRegime(
            trend=trend,
            strength=strength,
            volatility=volatility
        )


# =============================================================================
# BREAKING NEWS DETECTOR (PLACEHOLDER)
# =============================================================================

class BreakingNewsDetector:
    """
    Detects breaking news that requires immediate action.
    This is a placeholder - would integrate with news APIs in production.
    """
    
    def __init__(self, watchlist: Optional[list[str]] = None):
        self.watchlist = watchlist or ["QBTS", "IONQ", "RGTI", "QUBT"]
        self._callbacks: list[Callable[[Signal], None]] = []
    
    def on_breaking_news(self, callback: Callable[[Signal], None]):
        """Register callback for breaking news alerts"""
        self._callbacks.append(callback)
    
    def check_for_breaking_news(self) -> Optional[Signal]:
        """
        Check for breaking news events.
        Returns Signal with BREAKING urgency if found.
        
        TODO: Integrate with news APIs:
        - Alpha Vantage News
        - Finnhub
        - Twitter/X API
        - SEC EDGAR
        """
        # Placeholder - would check real news sources
        return None
    
    def simulate_breaking_news(self, symbol: str, event: str, effect: str, confidence: float) -> Signal:
        """
        Simulate a breaking news event for testing.
        
        Args:
            symbol: Stock symbol
            event: News event description
            effect: Expected market effect
            confidence: Confidence level
            
        Returns:
            Signal with BREAKING urgency
        """
        signal = Signal(
            symbol=symbol,
            signal_type=SignalType.STRONG_BUY if "positive" in effect.lower() else SignalType.STRONG_SELL,
            confidence=confidence,
            urgency=SignalUrgency.BREAKING,
            price=0.0,  # Would get from data source
            reason=f"BREAKING: {event} - {effect}"
        )
        
        # Notify callbacks
        for callback in self._callbacks:
            callback(signal)
        
        return signal


# =============================================================================
# MAIN - TEST THE MODULE
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Signal Engine Test")
    print("=" * 60)
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start='2025-12-01', periods=100, freq='1h')
    
    # Simulate QBTS price movement
    price = 7.0
    prices = [price]
    for _ in range(99):
        change = np.random.normal(0.001, 0.02)
        price *= (1 + change)
        prices.append(price)
    
    df = pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': [int(np.random.uniform(1e6, 5e6)) for _ in prices]
    }, index=dates)
    
    # Test signal generator
    print("\n📊 Generating signal for QBTS...")
    generator = SignalGenerator()
    signal = generator.generate_signal("QBTS", df)
    
    print(f"\n{signal}")
    print(f"Actionable: {signal.is_actionable}")
    print(f"Target: ${signal.target_price:.2f}" if signal.target_price else "No target")
    print(f"Stop Loss: ${signal.stop_loss:.2f}" if signal.stop_loss else "No stop loss")
    print(f"Reason: {signal.reason}")
    
    print("\n📈 Market Regime:")
    regime = generator.classify_market_regime(df)
    print(f"  Trend: {regime.trend} (strength: {regime.strength:.0f}%)")
    print(f"  Volatility: {regime.volatility}")
    
    print("\n" + "=" * 60)
    print("✅ Signal engine test complete!")
    print("=" * 60)
