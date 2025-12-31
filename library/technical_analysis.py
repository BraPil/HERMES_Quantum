"""
HERMES Technical Analysis Library
=================================

Comprehensive technical analysis for trading signals including:
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Support/Resistance level detection
- Chart pattern recognition
- Limit order recommendations

Author: HERMES Project
Date: December 2025
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging
from datetime import datetime

# Import ta library for technical indicators
import ta
from ta.trend import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class TrendDirection(Enum):
    """Market trend direction"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class PatternType(Enum):
    """Chart pattern types"""
    # Bullish patterns
    ASCENDING_TRIANGLE = "ascending_triangle"
    CUP_AND_HANDLE = "cup_and_handle"
    BULL_FLAG = "bull_flag"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_BOTTOM = "triple_bottom"
    INVERSE_HEAD_SHOULDERS = "inverse_head_shoulders"
    BULLISH_ENGULFING = "bullish_engulfing"
    MORNING_STAR = "morning_star"
    ASCENDING_TRENDLINE = "ascending_trendline"
    
    # Bearish patterns
    DESCENDING_TRIANGLE = "descending_triangle"
    HEAD_SHOULDERS = "head_and_shoulders"
    BEAR_FLAG = "bear_flag"
    DOUBLE_TOP = "double_top"
    TRIPLE_TOP = "triple_top"
    BEARISH_ENGULFING = "bearish_engulfing"
    EVENING_STAR = "evening_star"
    DESCENDING_TRENDLINE = "descending_trendline"
    STEPPED_DESCENT = "stepped_descent"
    
    # Neutral patterns
    CONSOLIDATION = "consolidation"
    CHANNEL = "channel"


@dataclass
class TechnicalIndicators:
    """Container for all technical indicators"""
    # Trend indicators
    sma_20: float = 0.0
    sma_50: float = 0.0
    sma_200: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    
    # MACD
    macd_line: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    macd_crossover: str = "none"  # "bullish", "bearish", "none"
    
    # Momentum
    rsi_14: float = 50.0
    rsi_signal: str = "neutral"  # "overbought", "oversold", "neutral"
    stochastic_k: float = 50.0
    stochastic_d: float = 50.0
    
    # Volatility
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
    bollinger_width: float = 0.0
    atr_14: float = 0.0
    
    # Volume
    obv: float = 0.0
    vwap: float = 0.0
    volume_trend: str = "neutral"  # "increasing", "decreasing", "neutral"
    
    # ADX (trend strength)
    adx: float = 0.0
    trend_strength: str = "weak"  # "weak", "moderate", "strong", "very_strong"
    
    # Overall assessment
    trend: TrendDirection = TrendDirection.NEUTRAL
    signal_summary: str = ""


@dataclass
class SupportResistance:
    """Support and resistance levels"""
    price: float
    level_type: str  # "support" or "resistance"
    strength: float  # 0-100
    touches: int  # Number of times price touched this level
    last_touch: Optional[datetime] = None
    is_major: bool = False  # Major vs minor level
    
    def __repr__(self):
        return f"{self.level_type.title()} @ ${self.price:.2f} (strength: {self.strength:.0f}%, touches: {self.touches})"


@dataclass
class ChartPattern:
    """Detected chart pattern"""
    pattern_type: PatternType
    confidence: float  # 0-100
    start_date: datetime
    end_date: Optional[datetime] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    breakout_level: Optional[float] = None
    description: str = ""
    is_confirmed: bool = False


@dataclass
class LimitOrderRecommendation:
    """Limit order recommendation with entry/exit targets"""
    order_type: str  # "BUY" or "SELL"
    entry_price: float
    target_price: float
    stop_loss: float
    probability: float  # 0-100
    reasoning: str
    risk_reward_ratio: float = 0.0
    expected_return: float = 0.0  # Percentage
    timeframe: str = "short-term"  # "short-term", "medium-term", "long-term"
    
    def __post_init__(self):
        if self.order_type == "BUY":
            risk = self.entry_price - self.stop_loss
            reward = self.target_price - self.entry_price
        else:
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.target_price
        
        if risk > 0:
            self.risk_reward_ratio = reward / risk
        
        self.expected_return = ((self.target_price - self.entry_price) / self.entry_price) * 100


@dataclass
class TechnicalAnalysisResult:
    """Complete technical analysis result"""
    symbol: str
    timestamp: datetime
    current_price: float
    indicators: TechnicalIndicators
    support_levels: List[SupportResistance] = field(default_factory=list)
    resistance_levels: List[SupportResistance] = field(default_factory=list)
    patterns: List[ChartPattern] = field(default_factory=list)
    buy_recommendations: List[LimitOrderRecommendation] = field(default_factory=list)
    sell_recommendations: List[LimitOrderRecommendation] = field(default_factory=list)
    timeframe_recommendations: Dict[str, Tuple] = field(default_factory=dict)  # Multi-timeframe recs
    overall_signal: str = "HOLD"  # "BUY", "SELL", "HOLD"
    signal_strength: float = 0.0  # 0-100
    analysis_summary: str = ""


# =============================================================================
# Technical Indicator Calculator
# =============================================================================

class TechnicalIndicatorCalculator:
    """Calculate all technical indicators from OHLCV data"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume
        """
        self.df = df.copy()
        self._validate_data()
        self._calculate_all_indicators()
    
    def _validate_data(self):
        """Validate input data has required columns"""
        required = ['open', 'high', 'low', 'close', 'volume']
        # Handle case-insensitive column names
        self.df.columns = self.df.columns.str.lower()
        
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Ensure numeric types
        for col in required:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Drop NaN rows
        self.df = self.df.dropna()
        
        if len(self.df) < 20:
            logger.warning(f"Only {len(self.df)} data points - some indicators may be unreliable")
    
    def _calculate_all_indicators(self):
        """Calculate all technical indicators"""
        close = self.df['close']
        high = self.df['high']
        low = self.df['low']
        volume = self.df['volume']
        
        # --- Trend Indicators ---
        # SMAs
        self.df['sma_20'] = SMAIndicator(close, window=20).sma_indicator()
        self.df['sma_50'] = SMAIndicator(close, window=50).sma_indicator()
        self.df['sma_200'] = SMAIndicator(close, window=200).sma_indicator() if len(self.df) >= 200 else np.nan
        
        # EMAs
        self.df['ema_12'] = EMAIndicator(close, window=12).ema_indicator()
        self.df['ema_26'] = EMAIndicator(close, window=26).ema_indicator()
        
        # MACD
        macd = MACD(close)
        self.df['macd_line'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_histogram'] = macd.macd_diff()
        
        # ADX
        if len(self.df) >= 14:
            adx = ADXIndicator(high, low, close)
            self.df['adx'] = adx.adx()
        
        # --- Momentum Indicators ---
        # RSI
        self.df['rsi_14'] = RSIIndicator(close, window=14).rsi()
        
        # Stochastic
        if len(self.df) >= 14:
            stoch = StochasticOscillator(high, low, close)
            self.df['stoch_k'] = stoch.stoch()
            self.df['stoch_d'] = stoch.stoch_signal()
        
        # --- Volatility Indicators ---
        # Bollinger Bands
        bb = BollingerBands(close)
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        
        # ATR
        atr = AverageTrueRange(high, low, close)
        self.df['atr_14'] = atr.average_true_range()
        
        # --- Volume Indicators ---
        # OBV
        obv = OnBalanceVolumeIndicator(close, volume)
        self.df['obv'] = obv.on_balance_volume()
        
        # VWAP (simplified daily)
        if len(self.df) > 0:
            self.df['vwap'] = (volume * (high + low + close) / 3).cumsum() / volume.cumsum()
    
    def get_latest_indicators(self) -> TechnicalIndicators:
        """Get the most recent indicator values"""
        if len(self.df) == 0:
            return TechnicalIndicators()
        
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else latest
        
        indicators = TechnicalIndicators()
        
        # Trend
        indicators.sma_20 = latest.get('sma_20', 0.0)
        indicators.sma_50 = latest.get('sma_50', 0.0)
        indicators.sma_200 = latest.get('sma_200', 0.0) if not pd.isna(latest.get('sma_200')) else 0.0
        indicators.ema_12 = latest.get('ema_12', 0.0)
        indicators.ema_26 = latest.get('ema_26', 0.0)
        
        # MACD
        indicators.macd_line = latest.get('macd_line', 0.0)
        indicators.macd_signal = latest.get('macd_signal', 0.0)
        indicators.macd_histogram = latest.get('macd_histogram', 0.0)
        
        # Detect MACD crossover
        if not pd.isna(prev.get('macd_line')) and not pd.isna(prev.get('macd_signal')):
            prev_diff = prev['macd_line'] - prev['macd_signal']
            curr_diff = latest['macd_line'] - latest['macd_signal']
            if prev_diff < 0 and curr_diff > 0:
                indicators.macd_crossover = "bullish"
            elif prev_diff > 0 and curr_diff < 0:
                indicators.macd_crossover = "bearish"
        
        # Momentum
        indicators.rsi_14 = latest.get('rsi_14', 50.0)
        if indicators.rsi_14 > 70:
            indicators.rsi_signal = "overbought"
        elif indicators.rsi_14 < 30:
            indicators.rsi_signal = "oversold"
        else:
            indicators.rsi_signal = "neutral"
        
        indicators.stochastic_k = latest.get('stoch_k', 50.0)
        indicators.stochastic_d = latest.get('stoch_d', 50.0)
        
        # Volatility
        indicators.bollinger_upper = latest.get('bb_upper', 0.0)
        indicators.bollinger_middle = latest.get('bb_middle', 0.0)
        indicators.bollinger_lower = latest.get('bb_lower', 0.0)
        indicators.bollinger_width = latest.get('bb_width', 0.0)
        indicators.atr_14 = latest.get('atr_14', 0.0)
        
        # Volume
        indicators.obv = latest.get('obv', 0.0)
        indicators.vwap = latest.get('vwap', 0.0)
        
        # Volume trend (compare last 5 days to previous 5 days)
        if len(self.df) >= 10:
            recent_vol = self.df['volume'].iloc[-5:].mean()
            prev_vol = self.df['volume'].iloc[-10:-5].mean()
            if recent_vol > prev_vol * 1.2:
                indicators.volume_trend = "increasing"
            elif recent_vol < prev_vol * 0.8:
                indicators.volume_trend = "decreasing"
        
        # ADX and trend strength
        indicators.adx = latest.get('adx', 0.0) if not pd.isna(latest.get('adx')) else 0.0
        if indicators.adx >= 50:
            indicators.trend_strength = "very_strong"
        elif indicators.adx >= 25:
            indicators.trend_strength = "strong"
        elif indicators.adx >= 20:
            indicators.trend_strength = "moderate"
        else:
            indicators.trend_strength = "weak"
        
        # Determine overall trend
        indicators.trend = self._determine_trend(latest)
        indicators.signal_summary = self._generate_signal_summary(indicators)
        
        return indicators
    
    def _determine_trend(self, latest: pd.Series) -> TrendDirection:
        """Determine overall trend direction"""
        score = 0
        
        close = latest['close']
        
        # Price vs SMAs
        if not pd.isna(latest.get('sma_20')) and close > latest['sma_20']:
            score += 1
        elif not pd.isna(latest.get('sma_20')):
            score -= 1
            
        if not pd.isna(latest.get('sma_50')) and close > latest['sma_50']:
            score += 1
        elif not pd.isna(latest.get('sma_50')):
            score -= 1
        
        if not pd.isna(latest.get('sma_200')) and close > latest['sma_200']:
            score += 2  # 200 SMA is more significant
        elif not pd.isna(latest.get('sma_200')):
            score -= 2
        
        # MACD
        if not pd.isna(latest.get('macd_histogram')) and latest['macd_histogram'] > 0:
            score += 1
        elif not pd.isna(latest.get('macd_histogram')):
            score -= 1
        
        # RSI
        rsi = latest.get('rsi_14', 50)
        if rsi > 60:
            score += 1
        elif rsi < 40:
            score -= 1
        
        # Map score to trend
        if score >= 4:
            return TrendDirection.STRONG_BULLISH
        elif score >= 2:
            return TrendDirection.BULLISH
        elif score <= -4:
            return TrendDirection.STRONG_BEARISH
        elif score <= -2:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def _generate_signal_summary(self, ind: TechnicalIndicators) -> str:
        """Generate human-readable signal summary"""
        signals = []
        
        # MACD
        if ind.macd_crossover == "bullish":
            signals.append("MACD bullish crossover")
        elif ind.macd_crossover == "bearish":
            signals.append("MACD bearish crossover")
        
        # RSI
        if ind.rsi_signal == "overbought":
            signals.append("RSI overbought (>70)")
        elif ind.rsi_signal == "oversold":
            signals.append("RSI oversold (<30)")
        
        # Trend strength
        if ind.trend_strength in ["strong", "very_strong"]:
            signals.append(f"ADX shows {ind.trend_strength} trend")
        
        # Volume
        if ind.volume_trend == "increasing":
            signals.append("Volume increasing")
        elif ind.volume_trend == "decreasing":
            signals.append("Volume decreasing")
        
        if not signals:
            signals.append("No significant signals detected")
        
        return "; ".join(signals)


# =============================================================================
# Support/Resistance Detector
# =============================================================================

class SupportResistanceDetector:
    """Detect support and resistance levels from price data"""
    
    def __init__(self, df: pd.DataFrame, lookback: int = 60):
        """
        Initialize detector
        
        Args:
            df: OHLCV DataFrame
            lookback: Number of periods to analyze
        """
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        self.lookback = min(lookback, len(df))
        
    def detect_levels(self, num_levels: int = 5, min_touches: int = 1) -> Tuple[List[SupportResistance], List[SupportResistance]]:
        """
        Detect support and resistance levels
        
        Args:
            num_levels: Maximum number of levels to return for each type
            min_touches: Minimum touches required to consider a level valid
            
        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if len(self.df) < 10:
            return [], []
        
        # Use recent data
        data = self.df.tail(self.lookback)
        current_price = data['close'].iloc[-1]
        
        # Find pivot points (local highs and lows) with smaller window for volatile stocks
        pivots_high = self._find_pivot_points(data, 'high', is_high=True, window=3)
        pivots_low = self._find_pivot_points(data, 'low', is_high=False, window=3)
        
        # Also try larger window for major levels
        pivots_high += self._find_pivot_points(data, 'high', is_high=True, window=5)
        pivots_low += self._find_pivot_points(data, 'low', is_high=False, window=5)
        
        # Cluster nearby pivots with wider tolerance for volatile stocks
        resistance_clusters = self._cluster_levels(pivots_high, current_price, tolerance_pct=3.0)
        support_clusters = self._cluster_levels(pivots_low, current_price, tolerance_pct=3.0)
        
        # Convert to SupportResistance objects
        resistance_levels = []
        for price, touches, dates in resistance_clusters:
            if touches >= min_touches and price > current_price:
                strength = min(100, 20 * touches + 10)
                is_major = touches >= 3
                sr = SupportResistance(
                    price=price,
                    level_type="resistance",
                    strength=strength,
                    touches=touches,
                    last_touch=dates[-1] if dates else None,
                    is_major=is_major
                )
                resistance_levels.append(sr)
        
        support_levels = []
        for price, touches, dates in support_clusters:
            if touches >= min_touches and price < current_price:
                strength = min(100, 20 * touches + 10)
                is_major = touches >= 3
                sr = SupportResistance(
                    price=price,
                    level_type="support",
                    strength=strength,
                    touches=touches,
                    last_touch=dates[-1] if dates else None,
                    is_major=is_major
                )
                support_levels.append(sr)
        
        # Sort by proximity to current price and limit
        resistance_levels.sort(key=lambda x: x.price)
        support_levels.sort(key=lambda x: -x.price)  # Descending (closest first)
        
        return support_levels[:num_levels], resistance_levels[:num_levels]
    
    def _find_pivot_points(self, data: pd.DataFrame, column: str, is_high: bool, window: int = 5) -> List[Tuple[float, datetime]]:
        """Find local highs or lows"""
        pivots = []
        values = data[column].values
        
        for i in range(window, len(values) - window):
            if is_high:
                # Local high
                if all(values[i] >= values[i-j] for j in range(1, window+1)) and \
                   all(values[i] >= values[i+j] for j in range(1, window+1)):
                    date = data.index[i] if hasattr(data.index[i], 'to_pydatetime') else datetime.now()
                    pivots.append((values[i], date))
            else:
                # Local low
                if all(values[i] <= values[i-j] for j in range(1, window+1)) and \
                   all(values[i] <= values[i+j] for j in range(1, window+1)):
                    date = data.index[i] if hasattr(data.index[i], 'to_pydatetime') else datetime.now()
                    pivots.append((values[i], date))
        
        return pivots
    
    def _cluster_levels(self, pivots: List[Tuple[float, datetime]], current_price: float, 
                        tolerance_pct: float = 2.0) -> List[Tuple[float, int, List[datetime]]]:
        """Cluster nearby price levels together"""
        if not pivots:
            return []
        
        # Sort by price
        pivots.sort(key=lambda x: x[0])
        
        clusters = []
        current_cluster = [pivots[0]]
        
        for i in range(1, len(pivots)):
            prev_price = pivots[i-1][0]
            curr_price = pivots[i][0]
            
            # Check if within tolerance
            if abs(curr_price - prev_price) / prev_price * 100 <= tolerance_pct:
                current_cluster.append(pivots[i])
            else:
                # Close current cluster
                if current_cluster:
                    avg_price = np.mean([p[0] for p in current_cluster])
                    dates = [p[1] for p in current_cluster]
                    clusters.append((avg_price, len(current_cluster), dates))
                current_cluster = [pivots[i]]
        
        # Don't forget last cluster
        if current_cluster:
            avg_price = np.mean([p[0] for p in current_cluster])
            dates = [p[1] for p in current_cluster]
            clusters.append((avg_price, len(current_cluster), dates))
        
        return clusters


# =============================================================================
# Chart Pattern Detector
# =============================================================================

class ChartPatternDetector:
    """Detect chart patterns in price data"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize pattern detector
        
        Args:
            df: OHLCV DataFrame
        """
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        self.patterns: List[ChartPattern] = []
    
    def detect_all_patterns(self) -> List[ChartPattern]:
        """Detect all chart patterns"""
        self.patterns = []
        
        if len(self.df) < 20:
            return self.patterns
        
        # Detect various patterns
        self._detect_double_triple_top_bottom()  # Enhanced version
        self._detect_trendlines()  # NEW: Ascending/descending trendlines
        self._detect_stepped_patterns()  # NEW: Stepped descent/ascent
        self._detect_ascending_descending_triangle()
        self._detect_bull_bear_flags()
        self._detect_head_and_shoulders()
        self._detect_consolidation()
        self._detect_candlestick_patterns()
        
        # Sort by confidence
        self.patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        return self.patterns
    
    def _find_peaks_troughs(self, data: pd.DataFrame, window: int = 3) -> Tuple[List, List]:
        """
        Find peaks and troughs in price data with configurable sensitivity.
        
        Args:
            data: DataFrame with high/low columns
            window: Number of bars on each side to check (smaller = more sensitive)
        
        Returns:
            Tuple of (peak_indices, trough_indices) as lists of (index, price)
        """
        highs = data['high'].values
        lows = data['low'].values
        
        peak_indices = []
        trough_indices = []
        
        for i in range(window, len(highs) - window):
            # Peak: higher than surrounding bars
            is_peak = True
            for j in range(1, window + 1):
                if highs[i] < highs[i-j] or highs[i] < highs[i+j]:
                    is_peak = False
                    break
            if is_peak:
                peak_indices.append((i, highs[i]))
            
            # Trough: lower than surrounding bars
            is_trough = True
            for j in range(1, window + 1):
                if lows[i] > lows[i-j] or lows[i] > lows[i+j]:
                    is_trough = False
                    break
            if is_trough:
                trough_indices.append((i, lows[i]))
        
        return peak_indices, trough_indices
    
    def _detect_double_triple_top_bottom(self):
        """Detect double and triple top/bottom patterns with calibrated sensitivity"""
        # Use longer lookback for multi-month patterns
        data = self.df.tail(90)  # 90 days for longer patterns
        if len(data) < 20:
            return
        
        close = data['close'].iloc[-1]
        
        # Find peaks and troughs with multiple sensitivities
        for window in [2, 3, 4]:  # Try different sensitivities
            peaks, troughs = self._find_peaks_troughs(data, window=window)
            
            # === TRIPLE TOP ===
            if len(peaks) >= 3:
                # Look at last 5 peaks
                recent_peaks = peaks[-5:]
                for i in range(len(recent_peaks) - 2):
                    p1, p2, p3 = recent_peaks[i], recent_peaks[i+1], recent_peaks[i+2]
                    idx1, price1 = p1
                    idx2, price2 = p2
                    idx3, price3 = p3
                    
                    # Peaks should be at least 5 bars apart
                    if idx2 - idx1 >= 5 and idx3 - idx2 >= 5:
                        # Check if all three peaks are within 5% of each other
                        avg_peak = (price1 + price2 + price3) / 3
                        tolerance = avg_peak * 0.05  # 5% tolerance for volatile stocks
                        
                        if abs(price1 - avg_peak) < tolerance and \
                           abs(price2 - avg_peak) < tolerance and \
                           abs(price3 - avg_peak) < tolerance:
                            # Find neckline (lowest point between peaks)
                            neckline = min(data['low'].iloc[idx1:idx3+1])
                            target = neckline - (avg_peak - neckline)
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.TRIPLE_TOP,
                                confidence=75.0,
                                start_date=data.index[idx1],
                                end_date=data.index[idx3],
                                target_price=target,
                                stop_loss=avg_peak * 1.02,
                                breakout_level=neckline,
                                description=f"Triple top at ${avg_peak:.2f} (peaks: ${price1:.2f}, ${price2:.2f}, ${price3:.2f}), neckline ${neckline:.2f}",
                                is_confirmed=close < neckline
                            )
                            self.patterns.append(pattern)
                            break
            
            # === TRIPLE BOTTOM ===
            if len(troughs) >= 3:
                recent_troughs = troughs[-5:]
                for i in range(len(recent_troughs) - 2):
                    t1, t2, t3 = recent_troughs[i], recent_troughs[i+1], recent_troughs[i+2]
                    idx1, price1 = t1
                    idx2, price2 = t2
                    idx3, price3 = t3
                    
                    if idx2 - idx1 >= 5 and idx3 - idx2 >= 5:
                        avg_trough = (price1 + price2 + price3) / 3
                        tolerance = avg_trough * 0.05
                        
                        if abs(price1 - avg_trough) < tolerance and \
                           abs(price2 - avg_trough) < tolerance and \
                           abs(price3 - avg_trough) < tolerance:
                            neckline = max(data['high'].iloc[idx1:idx3+1])
                            target = neckline + (neckline - avg_trough)
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.TRIPLE_BOTTOM,
                                confidence=75.0,
                                start_date=data.index[idx1],
                                end_date=data.index[idx3],
                                target_price=target,
                                stop_loss=avg_trough * 0.98,
                                breakout_level=neckline,
                                description=f"Triple bottom at ${avg_trough:.2f} (troughs: ${price1:.2f}, ${price2:.2f}, ${price3:.2f}), neckline ${neckline:.2f}",
                                is_confirmed=close > neckline
                            )
                            self.patterns.append(pattern)
                            break
            
            # === DOUBLE TOP === (relaxed parameters)
            if len(peaks) >= 2:
                for i in range(len(peaks) - 1):
                    idx1, price1 = peaks[i]
                    idx2, price2 = peaks[i+1]
                    
                    if idx2 - idx1 >= 5:  # Reduced from 10
                        if abs(price1 - price2) / price1 < 0.05:  # 5% tolerance
                            neckline = min(data['low'].iloc[idx1:idx2+1])
                            target = neckline - (price1 - neckline)
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.DOUBLE_TOP,
                                confidence=65.0,
                                start_date=data.index[idx1],
                                end_date=data.index[idx2],
                                target_price=target,
                                stop_loss=price1 * 1.02,
                                breakout_level=neckline,
                                description=f"Double top at ${price1:.2f} and ${price2:.2f}, neckline ${neckline:.2f}",
                                is_confirmed=close < neckline
                            )
                            self.patterns.append(pattern)
            
            # === DOUBLE BOTTOM === (relaxed parameters)
            if len(troughs) >= 2:
                for i in range(len(troughs) - 1):
                    idx1, price1 = troughs[i]
                    idx2, price2 = troughs[i+1]
                    
                    if idx2 - idx1 >= 5:
                        if abs(price1 - price2) / price1 < 0.05:
                            neckline = max(data['high'].iloc[idx1:idx2+1])
                            target = neckline + (neckline - price1)
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.DOUBLE_BOTTOM,
                                confidence=65.0,
                                start_date=data.index[idx1],
                                end_date=data.index[idx2],
                                target_price=target,
                                stop_loss=price1 * 0.98,
                                breakout_level=neckline,
                                description=f"Double bottom at ${price1:.2f} and ${price2:.2f}, neckline ${neckline:.2f}",
                                is_confirmed=close > neckline
                            )
                            self.patterns.append(pattern)
        
        # Deduplicate similar patterns (keep highest confidence)
        seen = set()
        unique_patterns = []
        for p in self.patterns:
            key = (p.pattern_type.value, round(p.target_price or 0, 1))
            if key not in seen:
                seen.add(key)
                unique_patterns.append(p)
        self.patterns = unique_patterns
    
    def _detect_trendlines(self):
        """Detect ascending and descending trendlines connecting lows/highs"""
        data = self.df.tail(60)
        if len(data) < 20:
            return
        
        close = data['close'].iloc[-1]
        
        # Find significant lows and highs
        peaks, troughs = self._find_peaks_troughs(data, window=3)
        
        # === ASCENDING SUPPORT TRENDLINE ===
        if len(troughs) >= 2:
            # Try connecting the first and last troughs
            for i in range(len(troughs)):
                for j in range(i + 1, len(troughs)):
                    idx1, price1 = troughs[i]
                    idx2, price2 = troughs[j]
                    
                    # Must be ascending and at least 15 bars apart
                    if price2 > price1 and idx2 - idx1 >= 15:
                        # Calculate slope (price per bar)
                        slope = (price2 - price1) / (idx2 - idx1)
                        
                        # Check if other troughs are near this trendline
                        touches = 2  # Already have 2 points
                        for k in range(len(troughs)):
                            if k != i and k != j:
                                idx_k, price_k = troughs[k]
                                if idx1 < idx_k < idx2:
                                    expected = price1 + slope * (idx_k - idx1)
                                    if abs(price_k - expected) / expected < 0.03:
                                        touches += 1
                        
                        if touches >= 2:
                            # Project to current bar
                            bars_since = len(data) - 1 - idx1
                            projected_support = price1 + slope * bars_since
                            daily_slope = slope
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.ASCENDING_TRENDLINE,
                                confidence=min(50 + touches * 10, 85),
                                start_date=data.index[idx1],
                                end_date=data.index[idx2],
                                target_price=projected_support,
                                breakout_level=projected_support,
                                description=f"Ascending support: ${price1:.2f} → ${price2:.2f}, slope ${daily_slope:.3f}/day, current support ~${projected_support:.2f}",
                                is_confirmed=close > projected_support
                            )
                            self.patterns.append(pattern)
                            break
                else:
                    continue
                break
        
        # === DESCENDING RESISTANCE TRENDLINE ===
        if len(peaks) >= 2:
            for i in range(len(peaks)):
                for j in range(i + 1, len(peaks)):
                    idx1, price1 = peaks[i]
                    idx2, price2 = peaks[j]
                    
                    # Must be descending and at least 15 bars apart
                    if price2 < price1 and idx2 - idx1 >= 15:
                        slope = (price2 - price1) / (idx2 - idx1)
                        
                        touches = 2
                        for k in range(len(peaks)):
                            if k != i and k != j:
                                idx_k, price_k = peaks[k]
                                if idx1 < idx_k < idx2:
                                    expected = price1 + slope * (idx_k - idx1)
                                    if abs(price_k - expected) / expected < 0.03:
                                        touches += 1
                        
                        if touches >= 2:
                            bars_since = len(data) - 1 - idx1
                            projected_resistance = price1 + slope * bars_since
                            
                            pattern = ChartPattern(
                                pattern_type=PatternType.DESCENDING_TRENDLINE,
                                confidence=min(50 + touches * 10, 85),
                                start_date=data.index[idx1],
                                end_date=data.index[idx2],
                                target_price=projected_resistance,
                                breakout_level=projected_resistance,
                                description=f"Descending resistance: ${price1:.2f} → ${price2:.2f}, slope ${slope:.3f}/day, current resistance ~${projected_resistance:.2f}",
                                is_confirmed=close < projected_resistance
                            )
                            self.patterns.append(pattern)
                            break
                else:
                    continue
                break
    
    def _detect_stepped_patterns(self):
        """Detect stepped descent or ascent patterns (lower highs + lower lows sequence)"""
        data = self.df.tail(45)
        if len(data) < 20:
            return
        
        close = data['close'].iloc[-1]
        peaks, troughs = self._find_peaks_troughs(data, window=3)
        
        # === STEPPED DESCENT ===
        # Pattern: sequence of lower highs AND lower lows
        if len(peaks) >= 3 and len(troughs) >= 3:
            # Check last 4 peaks for lower highs
            recent_peaks = peaks[-4:] if len(peaks) >= 4 else peaks
            lower_highs = all(
                recent_peaks[i][1] > recent_peaks[i+1][1] 
                for i in range(len(recent_peaks) - 1)
            )
            
            # Check last 4 troughs for lower lows
            recent_troughs = troughs[-4:] if len(troughs) >= 4 else troughs
            lower_lows = all(
                recent_troughs[i][1] > recent_troughs[i+1][1] 
                for i in range(len(recent_troughs) - 1)
            )
            
            if lower_highs and lower_lows:
                first_peak = recent_peaks[0][1]
                last_peak = recent_peaks[-1][1]
                decline_pct = ((first_peak - last_peak) / first_peak) * 100
                
                # Project next step
                if len(recent_peaks) >= 2:
                    avg_step = sum(
                        recent_peaks[i][1] - recent_peaks[i+1][1] 
                        for i in range(len(recent_peaks) - 1)
                    ) / (len(recent_peaks) - 1)
                    projected_next_high = last_peak - avg_step
                else:
                    projected_next_high = last_peak * 0.95
                
                pattern = ChartPattern(
                    pattern_type=PatternType.STEPPED_DESCENT,
                    confidence=70.0,
                    start_date=data.index[recent_peaks[0][0]],
                    end_date=data.index[recent_peaks[-1][0]],
                    target_price=projected_next_high,
                    description=f"Stepped descent: {len(recent_peaks)} lower highs, {decline_pct:.1f}% decline, next resistance ~${projected_next_high:.2f}",
                    is_confirmed=True
                )
                self.patterns.append(pattern)
    
    def _detect_double_top_bottom(self):
        """Detect double top and double bottom patterns"""
        data = self.df.tail(60)
        if len(data) < 30:
            return
        
        highs = data['high'].values
        lows = data['low'].values
        close = data['close'].iloc[-1]
        
        # Find peaks and troughs
        peak_indices = []
        trough_indices = []
        
        for i in range(5, len(highs) - 5):
            # Peak
            if all(highs[i] >= highs[i-j] for j in range(1, 6)) and \
               all(highs[i] >= highs[i+j] for j in range(1, 6)):
                peak_indices.append(i)
            # Trough
            if all(lows[i] <= lows[i-j] for j in range(1, 6)) and \
               all(lows[i] <= lows[i+j] for j in range(1, 6)):
                trough_indices.append(i)
        
        # Double Top: two peaks at similar levels
        for i in range(len(peak_indices) - 1):
            idx1, idx2 = peak_indices[i], peak_indices[i+1]
            if idx2 - idx1 >= 10:  # At least 10 bars apart
                peak1, peak2 = highs[idx1], highs[idx2]
                if abs(peak1 - peak2) / peak1 < 0.03:  # Within 3%
                    # Find neckline (lowest point between peaks)
                    neckline = min(lows[idx1:idx2+1])
                    target = neckline - (peak1 - neckline)
                    
                    pattern = ChartPattern(
                        pattern_type=PatternType.DOUBLE_TOP,
                        confidence=65.0,
                        start_date=data.index[idx1],
                        end_date=data.index[idx2],
                        target_price=target,
                        stop_loss=peak1 * 1.02,
                        breakout_level=neckline,
                        description=f"Double top at ${peak1:.2f}, neckline at ${neckline:.2f}",
                        is_confirmed=close < neckline
                    )
                    self.patterns.append(pattern)
        
        # Double Bottom: two troughs at similar levels
        for i in range(len(trough_indices) - 1):
            idx1, idx2 = trough_indices[i], trough_indices[i+1]
            if idx2 - idx1 >= 10:
                trough1, trough2 = lows[idx1], lows[idx2]
                if abs(trough1 - trough2) / trough1 < 0.03:
                    # Find neckline (highest point between troughs)
                    neckline = max(highs[idx1:idx2+1])
                    target = neckline + (neckline - trough1)
                    
                    pattern = ChartPattern(
                        pattern_type=PatternType.DOUBLE_BOTTOM,
                        confidence=65.0,
                        start_date=data.index[idx1],
                        end_date=data.index[idx2],
                        target_price=target,
                        stop_loss=trough1 * 0.98,
                        breakout_level=neckline,
                        description=f"Double bottom at ${trough1:.2f}, neckline at ${neckline:.2f}",
                        is_confirmed=close > neckline
                    )
                    self.patterns.append(pattern)
    
    def _detect_ascending_descending_triangle(self):
        """Detect triangle patterns"""
        data = self.df.tail(40)
        if len(data) < 20:
            return
        
        close = data['close']
        highs = data['high']
        lows = data['low']
        
        # Linear regression on highs and lows
        x = np.arange(len(data))
        
        # Slope of highs
        high_slope, high_intercept = np.polyfit(x, highs, 1)
        # Slope of lows  
        low_slope, low_intercept = np.polyfit(x, lows, 1)
        
        current_price = close.iloc[-1]
        
        # Ascending triangle: flat resistance, rising support
        if abs(high_slope) < 0.01 * current_price and low_slope > 0.005 * current_price:
            resistance = highs.mean()
            target = resistance + (resistance - lows.iloc[-1])
            
            pattern = ChartPattern(
                pattern_type=PatternType.ASCENDING_TRIANGLE,
                confidence=60.0,
                start_date=data.index[0],
                target_price=target,
                breakout_level=resistance,
                description=f"Ascending triangle with resistance at ${resistance:.2f}",
                is_confirmed=current_price > resistance
            )
            self.patterns.append(pattern)
        
        # Descending triangle: flat support, falling resistance
        if abs(low_slope) < 0.01 * current_price and high_slope < -0.005 * current_price:
            support = lows.mean()
            target = support - (highs.iloc[-1] - support)
            
            pattern = ChartPattern(
                pattern_type=PatternType.DESCENDING_TRIANGLE,
                confidence=60.0,
                start_date=data.index[0],
                target_price=target,
                breakout_level=support,
                description=f"Descending triangle with support at ${support:.2f}",
                is_confirmed=current_price < support
            )
            self.patterns.append(pattern)
    
    def _detect_bull_bear_flags(self):
        """Detect flag patterns"""
        data = self.df.tail(30)
        if len(data) < 15:
            return
        
        close = data['close']
        current_price = close.iloc[-1]
        
        # Look for a strong move followed by consolidation
        # Strong move: first 5-10 bars
        pole_data = close.iloc[:10]
        flag_data = close.iloc[10:]
        
        if len(flag_data) < 5:
            return
        
        pole_return = (pole_data.iloc[-1] - pole_data.iloc[0]) / pole_data.iloc[0]
        flag_return = (flag_data.iloc[-1] - flag_data.iloc[0]) / flag_data.iloc[0]
        
        # Bull flag: strong up move, slight down consolidation
        if pole_return > 0.10 and -0.05 < flag_return < 0.02:
            target = current_price + abs(pole_data.iloc[-1] - pole_data.iloc[0])
            
            pattern = ChartPattern(
                pattern_type=PatternType.BULL_FLAG,
                confidence=55.0,
                start_date=data.index[0],
                target_price=target,
                description=f"Bull flag pattern, target ${target:.2f}",
            )
            self.patterns.append(pattern)
        
        # Bear flag: strong down move, slight up consolidation
        if pole_return < -0.10 and -0.02 < flag_return < 0.05:
            target = current_price - abs(pole_data.iloc[-1] - pole_data.iloc[0])
            
            pattern = ChartPattern(
                pattern_type=PatternType.BEAR_FLAG,
                confidence=55.0,
                start_date=data.index[0],
                target_price=target,
                description=f"Bear flag pattern, target ${target:.2f}",
            )
            self.patterns.append(pattern)
    
    def _detect_head_and_shoulders(self):
        """Detect head and shoulders pattern (simplified)"""
        data = self.df.tail(60)
        if len(data) < 40:
            return
        
        highs = data['high'].values
        close = data['close'].iloc[-1]
        
        # Find three peaks
        peaks = []
        for i in range(5, len(highs) - 5):
            if all(highs[i] >= highs[i-j] for j in range(1, 6)) and \
               all(highs[i] >= highs[i+j] for j in range(1, 6)):
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 3:
            # Check for H&S pattern: middle peak higher than shoulders
            for i in range(len(peaks) - 2):
                left_shoulder = peaks[i]
                head = peaks[i+1]
                right_shoulder = peaks[i+2]
                
                # Head should be higher
                if head[1] > left_shoulder[1] and head[1] > right_shoulder[1]:
                    # Shoulders should be roughly equal
                    if abs(left_shoulder[1] - right_shoulder[1]) / left_shoulder[1] < 0.05:
                        neckline = min(data['low'].iloc[left_shoulder[0]:right_shoulder[0]+1])
                        target = neckline - (head[1] - neckline)
                        
                        pattern = ChartPattern(
                            pattern_type=PatternType.HEAD_SHOULDERS,
                            confidence=70.0,
                            start_date=data.index[left_shoulder[0]],
                            target_price=target,
                            breakout_level=neckline,
                            description=f"Head and shoulders with neckline at ${neckline:.2f}",
                            is_confirmed=close < neckline
                        )
                        self.patterns.append(pattern)
                        break
    
    def _detect_consolidation(self):
        """Detect consolidation/range-bound patterns"""
        data = self.df.tail(20)
        if len(data) < 10:
            return
        
        high_range = data['high'].max()
        low_range = data['low'].min()
        range_pct = (high_range - low_range) / low_range * 100
        
        # Tight consolidation: less than 5% range
        if range_pct < 5.0:
            pattern = ChartPattern(
                pattern_type=PatternType.CONSOLIDATION,
                confidence=50.0,
                start_date=data.index[0],
                description=f"Tight consolidation ({range_pct:.1f}% range)",
            )
            self.patterns.append(pattern)
    
    def _detect_candlestick_patterns(self):
        """Detect candlestick patterns in recent data"""
        if len(self.df) < 3:
            return
        
        # Get last 3 candles
        candles = self.df.tail(3)
        
        for i in range(len(candles)):
            c = candles.iloc[i]
            body = abs(c['close'] - c['open'])
            upper_wick = c['high'] - max(c['close'], c['open'])
            lower_wick = min(c['close'], c['open']) - c['low']
            
        # Bullish engulfing (need 2 candles)
        if len(candles) >= 2:
            prev = candles.iloc[-2]
            curr = candles.iloc[-1]
            
            prev_body = prev['close'] - prev['open']
            curr_body = curr['close'] - curr['open']
            
            # Bullish engulfing: prev bearish, curr bullish and engulfs
            if prev_body < 0 and curr_body > 0:
                if curr['open'] <= prev['close'] and curr['close'] >= prev['open']:
                    pattern = ChartPattern(
                        pattern_type=PatternType.BULLISH_ENGULFING,
                        confidence=55.0,
                        start_date=candles.index[-1],
                        description="Bullish engulfing candle pattern",
                    )
                    self.patterns.append(pattern)
            
            # Bearish engulfing
            if prev_body > 0 and curr_body < 0:
                if curr['open'] >= prev['close'] and curr['close'] <= prev['open']:
                    pattern = ChartPattern(
                        pattern_type=PatternType.BEARISH_ENGULFING,
                        confidence=55.0,
                        start_date=candles.index[-1],
                        description="Bearish engulfing candle pattern",
                    )
                    self.patterns.append(pattern)


# =============================================================================
# Volume Profile Heatmap (Order Flow Analysis)
# =============================================================================

@dataclass
class VolumeNode:
    """A single price level with volume concentration"""
    price: float
    volume: float
    volume_pct: float  # Percentage of total volume
    is_high_volume_node: bool  # HVN - likely S/R zone
    is_low_volume_node: bool   # LVN - price moves quickly through here
    buy_volume_est: float = 0.0  # Estimated buy volume
    sell_volume_est: float = 0.0  # Estimated sell volume
    delta: float = 0.0  # buy - sell estimate
    
    @property
    def bias(self) -> str:
        """Estimate if buyers or sellers dominate this level"""
        if self.delta > 0.1:
            return "buyer_dominated"
        elif self.delta < -0.1:
            return "seller_dominated"
        return "balanced"


@dataclass
class VolumeProfileResult:
    """Complete volume profile analysis result"""
    price_levels: List[VolumeNode]  # All price levels with volume data
    poc: float  # Point of Control - highest volume price
    value_area_high: float  # Top of 70% volume range
    value_area_low: float  # Bottom of 70% volume range
    hvn_levels: List[float]  # High Volume Nodes (S/R zones)
    lvn_levels: List[float]  # Low Volume Nodes (breakout zones)
    total_volume: float
    num_bins: int
    
    def get_nearest_hvn(self, price: float, direction: str = "both") -> Optional[float]:
        """Get nearest high volume node above/below current price"""
        if not self.hvn_levels:
            return None
        
        above = [h for h in self.hvn_levels if h > price]
        below = [h for h in self.hvn_levels if h < price]
        
        if direction == "above" and above:
            return min(above)
        elif direction == "below" and below:
            return max(below)
        elif direction == "both":
            candidates = []
            if above:
                candidates.append(min(above))
            if below:
                candidates.append(max(below))
            if candidates:
                return min(candidates, key=lambda x: abs(x - price))
        return None


class VolumeProfileAnalyzer:
    """
    Volume Profile Heatmap Generator
    
    Creates a volume-at-price profile showing where trading activity concentrates.
    High Volume Nodes (HVN) typically act as support/resistance.
    Low Volume Nodes (LVN) are zones where price moves quickly.
    
    This is similar to bookmap.com's visualization but works with standard OHLCV data.
    """
    
    def __init__(self, df: pd.DataFrame, num_bins: int = 50):
        """
        Initialize volume profile analyzer
        
        Args:
            df: OHLCV DataFrame with columns: open, high, low, close, volume
            num_bins: Number of price bins for the profile (higher = more granular)
        """
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        self.num_bins = num_bins
        
    def calculate_profile(self) -> VolumeProfileResult:
        """
        Calculate the volume profile for the given data
        
        Returns:
            VolumeProfileResult with all volume profile data
        """
        if len(self.df) < 5:
            return self._empty_result()
        
        # Determine price range
        price_high = self.df['high'].max()
        price_low = self.df['low'].min()
        price_range = price_high - price_low
        
        if price_range <= 0:
            return self._empty_result()
        
        # Create price bins
        bin_size = price_range / self.num_bins
        bins = np.linspace(price_low, price_high, self.num_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # Distribute volume to bins based on price range of each candle
        volume_profile = np.zeros(self.num_bins)
        buy_volume_profile = np.zeros(self.num_bins)
        sell_volume_profile = np.zeros(self.num_bins)
        
        for _, row in self.df.iterrows():
            candle_low = row['low']
            candle_high = row['high']
            candle_volume = row['volume']
            candle_open = row['open']
            candle_close = row['close']
            
            # Determine which bins this candle touches
            for i, (bin_low, bin_high) in enumerate(zip(bins[:-1], bins[1:])):
                # Check if candle overlaps with this bin
                if candle_high >= bin_low and candle_low <= bin_high:
                    # Calculate overlap (how much of the candle is in this bin)
                    overlap_low = max(candle_low, bin_low)
                    overlap_high = min(candle_high, bin_high)
                    overlap_ratio = (overlap_high - overlap_low) / max(candle_high - candle_low, 0.001)
                    
                    # Distribute volume proportionally
                    volume_in_bin = candle_volume * overlap_ratio
                    volume_profile[i] += volume_in_bin
                    
                    # Estimate buy/sell volume based on candle color and position
                    # Green candle (close > open) = more buying pressure
                    # Volume in upper half of candle = more likely buying
                    # Volume in lower half = more likely selling
                    bin_center = (bin_low + bin_high) / 2
                    candle_mid = (candle_open + candle_close) / 2
                    
                    if candle_close > candle_open:  # Bullish candle
                        buy_ratio = 0.6 + 0.2 * (bin_center - candle_low) / max(candle_high - candle_low, 0.001)
                    else:  # Bearish candle
                        buy_ratio = 0.4 - 0.2 * (bin_center - candle_low) / max(candle_high - candle_low, 0.001)
                    
                    buy_ratio = max(0.2, min(0.8, buy_ratio))  # Clamp to reasonable range
                    
                    buy_volume_profile[i] += volume_in_bin * buy_ratio
                    sell_volume_profile[i] += volume_in_bin * (1 - buy_ratio)
        
        # Calculate total volume and percentages
        total_volume = volume_profile.sum()
        if total_volume == 0:
            return self._empty_result()
        
        volume_pcts = volume_profile / total_volume * 100
        
        # Find Point of Control (POC) - highest volume price
        poc_idx = np.argmax(volume_profile)
        poc = bin_centers[poc_idx]
        
        # Calculate Value Area (70% of volume)
        sorted_indices = np.argsort(volume_profile)[::-1]
        cumulative_volume = 0
        value_area_indices = []
        
        for idx in sorted_indices:
            value_area_indices.append(idx)
            cumulative_volume += volume_profile[idx]
            if cumulative_volume >= total_volume * 0.70:
                break
        
        value_area_high = bin_centers[max(value_area_indices)]
        value_area_low = bin_centers[min(value_area_indices)]
        
        # Identify HVN and LVN
        avg_volume = volume_profile.mean()
        std_volume = volume_profile.std()
        
        hvn_threshold = avg_volume + 0.5 * std_volume  # Above average
        lvn_threshold = avg_volume - 0.3 * std_volume  # Below average
        
        # Create volume nodes
        price_levels = []
        hvn_levels = []
        lvn_levels = []
        
        for i in range(self.num_bins):
            is_hvn = volume_profile[i] >= hvn_threshold
            is_lvn = volume_profile[i] <= lvn_threshold and volume_profile[i] > 0
            
            # Calculate delta (buy - sell) normalized
            total_at_level = buy_volume_profile[i] + sell_volume_profile[i]
            if total_at_level > 0:
                delta = (buy_volume_profile[i] - sell_volume_profile[i]) / total_at_level
            else:
                delta = 0
            
            node = VolumeNode(
                price=bin_centers[i],
                volume=volume_profile[i],
                volume_pct=volume_pcts[i],
                is_high_volume_node=is_hvn,
                is_low_volume_node=is_lvn,
                buy_volume_est=buy_volume_profile[i],
                sell_volume_est=sell_volume_profile[i],
                delta=delta
            )
            price_levels.append(node)
            
            if is_hvn:
                hvn_levels.append(bin_centers[i])
            if is_lvn:
                lvn_levels.append(bin_centers[i])
        
        return VolumeProfileResult(
            price_levels=price_levels,
            poc=poc,
            value_area_high=value_area_high,
            value_area_low=value_area_low,
            hvn_levels=sorted(hvn_levels),
            lvn_levels=sorted(lvn_levels),
            total_volume=total_volume,
            num_bins=self.num_bins
        )
    
    def _empty_result(self) -> VolumeProfileResult:
        """Return empty result for insufficient data"""
        return VolumeProfileResult(
            price_levels=[],
            poc=0.0,
            value_area_high=0.0,
            value_area_low=0.0,
            hvn_levels=[],
            lvn_levels=[],
            total_volume=0.0,
            num_bins=self.num_bins
        )
    
    def get_heatmap_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get data formatted for heatmap visualization
        
        Returns:
            Tuple of (prices, volumes, deltas) as numpy arrays
        """
        profile = self.calculate_profile()
        
        prices = np.array([n.price for n in profile.price_levels])
        volumes = np.array([n.volume for n in profile.price_levels])
        deltas = np.array([n.delta for n in profile.price_levels])
        
        return prices, volumes, deltas
    
    def estimate_order_walls(self, threshold_pct: float = 2.0) -> Dict[str, List[Dict]]:
        """
        Estimate where significant buy/sell walls likely exist
        based on volume concentration and delta
        
        Args:
            threshold_pct: Minimum volume % to consider as a "wall"
            
        Returns:
            Dict with 'buy_walls' and 'sell_walls' lists
        """
        profile = self.calculate_profile()
        
        buy_walls = []
        sell_walls = []
        
        for node in profile.price_levels:
            if node.volume_pct >= threshold_pct:
                wall_info = {
                    "price": node.price,
                    "volume": node.volume,
                    "volume_pct": node.volume_pct,
                    "strength": "strong" if node.volume_pct >= threshold_pct * 2 else "moderate"
                }
                
                if node.delta > 0.15:  # More buyers
                    buy_walls.append(wall_info)
                elif node.delta < -0.15:  # More sellers
                    sell_walls.append(wall_info)
                else:
                    # Balanced - add to both
                    buy_walls.append(wall_info)
                    sell_walls.append(wall_info)
        
        # Sort by volume
        buy_walls.sort(key=lambda x: x["volume"], reverse=True)
        sell_walls.sort(key=lambda x: x["volume"], reverse=True)
        
        return {
            "buy_walls": buy_walls[:10],
            "sell_walls": sell_walls[:10]
        }


# =============================================================================
# Limit Order Recommender
# =============================================================================

class LimitOrderRecommender:
    """Generate limit order recommendations based on technical analysis"""
    
    def __init__(self, current_price: float, indicators: TechnicalIndicators,
                 support_levels: List[SupportResistance], resistance_levels: List[SupportResistance],
                 patterns: List[ChartPattern], atr: float = None):
        """
        Initialize recommender
        
        Args:
            current_price: Current stock price
            indicators: Technical indicators
            support_levels: Detected support levels
            resistance_levels: Detected resistance levels
            patterns: Detected chart patterns
            atr: Average True Range for volatility-based stops
        """
        self.current_price = current_price
        self.indicators = indicators
        self.support_levels = support_levels
        self.resistance_levels = resistance_levels
        self.patterns = patterns
        self.atr = atr or current_price * 0.02  # Default 2% ATR
    
    def generate_recommendations(self) -> Tuple[List[LimitOrderRecommendation], List[LimitOrderRecommendation]]:
        """
        Generate buy and sell limit order recommendations
        
        Returns:
            Tuple of (buy_recommendations, sell_recommendations)
        """
        buy_recs = []
        sell_recs = []
        
        # 1. Support-based buy orders
        for support in self.support_levels[:3]:
            if support.price < self.current_price:
                distance_pct = (self.current_price - support.price) / self.current_price * 100
                
                # Only recommend if reasonably close (within 10%)
                if distance_pct <= 10:
                    # Target: first resistance or 5% above entry
                    if self.resistance_levels:
                        target = self.resistance_levels[0].price
                    else:
                        target = support.price * 1.05
                    
                    # Stop loss below support
                    stop = support.price * 0.97
                    
                    probability = min(75, support.strength + 10)
                    
                    rec = LimitOrderRecommendation(
                        order_type="BUY",
                        entry_price=support.price,
                        target_price=target,
                        stop_loss=stop,
                        probability=probability,
                        reasoning=f"Buy at {support} - historically strong support with {support.touches} touches",
                        timeframe="short-term"
                    )
                    buy_recs.append(rec)
        
        # 2. Resistance-based sell orders
        for resistance in self.resistance_levels[:3]:
            if resistance.price > self.current_price:
                distance_pct = (resistance.price - self.current_price) / self.current_price * 100
                
                if distance_pct <= 10:
                    # Target: first support or 5% below entry
                    if self.support_levels:
                        target = self.support_levels[0].price
                    else:
                        target = resistance.price * 0.95
                    
                    # Stop loss above resistance
                    stop = resistance.price * 1.03
                    
                    probability = min(75, resistance.strength + 10)
                    
                    rec = LimitOrderRecommendation(
                        order_type="SELL",
                        entry_price=resistance.price,
                        target_price=target,
                        stop_loss=stop,
                        probability=probability,
                        reasoning=f"Sell at {resistance} - historically strong resistance with {resistance.touches} touches",
                        timeframe="short-term"
                    )
                    sell_recs.append(rec)
        
        # 3. Pattern-based recommendations
        # Define bullish and bearish patterns explicitly
        bullish_patterns = {
            PatternType.ASCENDING_TRIANGLE, PatternType.BULL_FLAG, PatternType.DOUBLE_BOTTOM,
            PatternType.TRIPLE_BOTTOM, PatternType.INVERSE_HEAD_SHOULDERS, PatternType.BULLISH_ENGULFING,
            PatternType.MORNING_STAR, PatternType.ASCENDING_TRENDLINE
        }
        bearish_patterns = {
            PatternType.DESCENDING_TRIANGLE, PatternType.BEAR_FLAG, PatternType.DOUBLE_TOP,
            PatternType.TRIPLE_TOP, PatternType.HEAD_SHOULDERS, PatternType.BEARISH_ENGULFING,
            PatternType.EVENING_STAR, PatternType.DESCENDING_TRENDLINE, PatternType.STEPPED_DESCENT
        }
        
        for pattern in self.patterns:
            if pattern.target_price and pattern.confidence >= 55:
                # Filter out nonsensical targets (must be within 50% of current price)
                target_distance_pct = abs(pattern.target_price - self.current_price) / self.current_price * 100
                if target_distance_pct > 50 or pattern.target_price <= 0:
                    continue  # Skip unrealistic targets
                
                if pattern.pattern_type in bullish_patterns:
                    # BULLISH pattern: BUY at support/breakout, target higher
                    entry = pattern.breakout_level if pattern.breakout_level else self.current_price * 0.98
                    # For bullish, target should be ABOVE entry
                    target = max(pattern.target_price, entry * 1.05)
                    stop = entry - 2 * self.atr
                    
                    # Sanity check: entry should be <= current price for a buy
                    if entry > self.current_price * 1.1:
                        entry = self.current_price * 0.98
                    
                    rec = LimitOrderRecommendation(
                        order_type="BUY",
                        entry_price=entry,
                        target_price=target,
                        stop_loss=stop,
                        probability=pattern.confidence,
                        reasoning=f"{pattern.pattern_type.value.replace('_', ' ').title()}: {pattern.description}",
                        timeframe="medium-term"
                    )
                    buy_recs.append(rec)
                    
                elif pattern.pattern_type in bearish_patterns:
                    # BEARISH pattern: SELL at resistance/breakout, target lower
                    entry = pattern.breakout_level if pattern.breakout_level else self.current_price * 1.02
                    # For bearish (short), target should be BELOW entry
                    target = min(pattern.target_price, entry * 0.95)
                    stop = entry + 2 * self.atr
                    
                    # Sanity check: entry should be >= current price for a sell
                    if entry < self.current_price * 0.9:
                        entry = self.current_price * 1.02
                    
                    rec = LimitOrderRecommendation(
                        order_type="SELL",
                        entry_price=entry,
                        target_price=target,
                        stop_loss=stop,
                        probability=pattern.confidence,
                        reasoning=f"{pattern.pattern_type.value.replace('_', ' ').title()}: {pattern.description}",
                        timeframe="medium-term"
                    )
                    sell_recs.append(rec)
        
        # 4. Indicator-based recommendations
        # RSI oversold = buy opportunity
        if self.indicators.rsi_signal == "oversold":
            entry = self.current_price * 0.98  # Slightly below current
            target = self.indicators.sma_20 if self.indicators.sma_20 > entry else entry * 1.05
            stop = entry - 2 * self.atr
            
            rec = LimitOrderRecommendation(
                order_type="BUY",
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                probability=60.0,
                reasoning=f"RSI oversold at {self.indicators.rsi_14:.1f} - potential bounce",
                timeframe="short-term"
            )
            buy_recs.append(rec)
        
        # RSI overbought = sell opportunity
        if self.indicators.rsi_signal == "overbought":
            entry = self.current_price * 1.02  # Slightly above current
            target = self.indicators.sma_20 if self.indicators.sma_20 < entry else entry * 0.95
            stop = entry + 2 * self.atr
            
            rec = LimitOrderRecommendation(
                order_type="SELL",
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                probability=60.0,
                reasoning=f"RSI overbought at {self.indicators.rsi_14:.1f} - potential pullback",
                timeframe="short-term"
            )
            sell_recs.append(rec)
        
        # 5. Bollinger Band recommendations
        # Price near lower band = buy
        if self.current_price < self.indicators.bollinger_lower * 1.02:
            entry = self.indicators.bollinger_lower
            target = self.indicators.bollinger_middle
            stop = entry - self.atr
            
            rec = LimitOrderRecommendation(
                order_type="BUY",
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                probability=55.0,
                reasoning="Price near lower Bollinger Band - mean reversion opportunity",
                timeframe="short-term"
            )
            buy_recs.append(rec)
        
        # Price near upper band = sell
        if self.current_price > self.indicators.bollinger_upper * 0.98:
            entry = self.indicators.bollinger_upper
            target = self.indicators.bollinger_middle
            stop = entry + self.atr
            
            rec = LimitOrderRecommendation(
                order_type="SELL",
                entry_price=entry,
                target_price=target,
                stop_loss=stop,
                probability=55.0,
                reasoning="Price near upper Bollinger Band - mean reversion opportunity",
                timeframe="short-term"
            )
            sell_recs.append(rec)
        
        # Sort by probability
        buy_recs.sort(key=lambda x: x.probability, reverse=True)
        sell_recs.sort(key=lambda x: x.probability, reverse=True)
        
        return buy_recs[:5], sell_recs[:5]  # Return top 5 each
    
    def generate_timeframe_recommendations(self) -> Dict[str, Tuple[List[LimitOrderRecommendation], List[LimitOrderRecommendation]]]:
        """
        Generate recommendations for multiple timeframes: 1hr, 1day, 1week, 1month
        
        Returns:
            Dict mapping timeframe to (buy_recs, sell_recs) tuple
        """
        all_recs = {}
        
        # Timeframe multipliers for target/stop distances
        timeframe_config = {
            "1hr": {"atr_mult": 0.5, "target_mult": 0.5, "max_targets": 2, "label": "1 Hour"},
            "1day": {"atr_mult": 1.0, "target_mult": 1.0, "max_targets": 2, "label": "1 Day"},
            "1week": {"atr_mult": 2.0, "target_mult": 2.5, "max_targets": 2, "label": "1 Week"},
            "1month": {"atr_mult": 3.5, "target_mult": 5.0, "max_targets": 2, "label": "1 Month"},
        }
        
        for tf, config in timeframe_config.items():
            buy_recs = []
            sell_recs = []
            atr = self.atr * config["atr_mult"]
            
            # === BUY Recommendations for this timeframe ===
            
            # 1. Support-based buy (closest support)
            if self.support_levels:
                for support in self.support_levels[:2]:
                    if support.price < self.current_price:
                        distance_pct = (self.current_price - support.price) / self.current_price * 100
                        
                        # Adjust distance requirement by timeframe
                        max_distance = 5 * config["target_mult"]
                        if distance_pct <= max_distance:
                            # Target: scale by timeframe
                            base_target = support.price * (1 + 0.03 * config["target_mult"])
                            if self.resistance_levels:
                                target = min(self.resistance_levels[0].price, base_target * 1.5)
                            else:
                                target = base_target
                            
                            stop = support.price * (1 - 0.02 * config["atr_mult"])
                            
                            rec = LimitOrderRecommendation(
                                order_type="BUY",
                                entry_price=support.price,
                                target_price=target,
                                stop_loss=stop,
                                probability=min(75, support.strength + 10),
                                reasoning=f"Support at ${support.price:.2f} ({support.touches} touches) - {config['label']} target",
                                timeframe=tf
                            )
                            buy_recs.append(rec)
            
            # 2. Technical bounce levels (SMA, Bollinger)
            if self.indicators.sma_20 > 0 and self.indicators.sma_20 < self.current_price:
                entry = self.indicators.sma_20
                target = entry * (1 + 0.03 * config["target_mult"])
                stop = entry * (1 - 0.015 * config["atr_mult"])
                
                rec = LimitOrderRecommendation(
                    order_type="BUY",
                    entry_price=entry,
                    target_price=target,
                    stop_loss=stop,
                    probability=55.0,
                    reasoning=f"SMA20 support at ${entry:.2f} - {config['label']} bounce target",
                    timeframe=tf
                )
                buy_recs.append(rec)
            
            # 3. Bollinger lower band buy
            if self.indicators.bollinger_lower > 0:
                entry = self.indicators.bollinger_lower
                target = self.indicators.bollinger_middle * (1 + 0.01 * config["target_mult"])
                stop = entry * (1 - 0.02 * config["atr_mult"])
                
                rec = LimitOrderRecommendation(
                    order_type="BUY",
                    entry_price=entry,
                    target_price=target,
                    stop_loss=stop,
                    probability=50.0,
                    reasoning=f"Bollinger lower band ${entry:.2f} - {config['label']} mean reversion",
                    timeframe=tf
                )
                buy_recs.append(rec)
            
            # === SELL Recommendations for this timeframe ===
            
            # 1. Resistance-based sell (closest resistance)
            if self.resistance_levels:
                for resistance in self.resistance_levels[:2]:
                    if resistance.price > self.current_price:
                        distance_pct = (resistance.price - self.current_price) / self.current_price * 100
                        
                        max_distance = 5 * config["target_mult"]
                        if distance_pct <= max_distance:
                            base_target = resistance.price * (1 - 0.03 * config["target_mult"])
                            if self.support_levels:
                                target = max(self.support_levels[0].price, base_target * 0.7)
                            else:
                                target = base_target
                            
                            stop = resistance.price * (1 + 0.02 * config["atr_mult"])
                            
                            rec = LimitOrderRecommendation(
                                order_type="SELL",
                                entry_price=resistance.price,
                                target_price=target,
                                stop_loss=stop,
                                probability=min(75, resistance.strength + 10),
                                reasoning=f"Resistance at ${resistance.price:.2f} ({resistance.touches} touches) - {config['label']} target",
                                timeframe=tf
                            )
                            sell_recs.append(rec)
            
            # 2. Technical resistance levels (SMA, Bollinger)
            if self.indicators.sma_50 > 0 and self.indicators.sma_50 > self.current_price:
                entry = self.indicators.sma_50
                target = entry * (1 - 0.03 * config["target_mult"])
                stop = entry * (1 + 0.015 * config["atr_mult"])
                
                rec = LimitOrderRecommendation(
                    order_type="SELL",
                    entry_price=entry,
                    target_price=target,
                    stop_loss=stop,
                    probability=55.0,
                    reasoning=f"SMA50 resistance at ${entry:.2f} - {config['label']} pullback target",
                    timeframe=tf
                )
                sell_recs.append(rec)
            
            # 3. Bollinger upper band sell
            if self.indicators.bollinger_upper > 0:
                entry = self.indicators.bollinger_upper
                target = self.indicators.bollinger_middle * (1 - 0.01 * config["target_mult"])
                stop = entry * (1 + 0.02 * config["atr_mult"])
                
                rec = LimitOrderRecommendation(
                    order_type="SELL",
                    entry_price=entry,
                    target_price=target,
                    stop_loss=stop,
                    probability=50.0,
                    reasoning=f"Bollinger upper band ${entry:.2f} - {config['label']} mean reversion",
                    timeframe=tf
                )
                sell_recs.append(rec)
            
            # Sort and limit
            buy_recs.sort(key=lambda x: x.probability, reverse=True)
            sell_recs.sort(key=lambda x: x.probability, reverse=True)
            
            all_recs[tf] = (buy_recs[:config["max_targets"]], sell_recs[:config["max_targets"]])
        
        return all_recs


# =============================================================================
# Main Technical Analyzer
# =============================================================================

class TechnicalAnalyzer:
    """
    Main class for comprehensive technical analysis
    
    Combines all analysis components:
    - Technical indicators
    - Support/Resistance levels
    - Chart patterns
    - Limit order recommendations
    """
    
    def __init__(self, symbol: str, df: pd.DataFrame):
        """
        Initialize analyzer
        
        Args:
            symbol: Stock symbol
            df: OHLCV DataFrame with DatetimeIndex
        """
        self.symbol = symbol
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        
        # Ensure we have enough data
        if len(self.df) < 20:
            logger.warning(f"Limited data for {symbol}: only {len(self.df)} bars")
    
    def analyze(self) -> TechnicalAnalysisResult:
        """
        Perform complete technical analysis
        
        Returns:
            TechnicalAnalysisResult with all analysis
        """
        current_price = self.df['close'].iloc[-1]
        timestamp = datetime.now()
        
        # 1. Calculate indicators
        indicator_calc = TechnicalIndicatorCalculator(self.df)
        indicators = indicator_calc.get_latest_indicators()
        
        # 2. Detect support/resistance
        sr_detector = SupportResistanceDetector(self.df)
        support_levels, resistance_levels = sr_detector.detect_levels()
        
        # 3. Detect patterns
        pattern_detector = ChartPatternDetector(self.df)
        patterns = pattern_detector.detect_all_patterns()
        
        # 4. Generate limit order recommendations
        recommender = LimitOrderRecommender(
            current_price=current_price,
            indicators=indicators,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            patterns=patterns,
            atr=indicators.atr_14
        )
        buy_recs, sell_recs = recommender.generate_recommendations()
        
        # 4b. Generate multi-timeframe recommendations
        timeframe_recs = recommender.generate_timeframe_recommendations()
        
        # 5. Determine overall signal
        overall_signal, signal_strength = self._determine_overall_signal(
            indicators, patterns, support_levels, resistance_levels, current_price
        )
        
        # 6. Generate summary
        summary = self._generate_summary(indicators, patterns, support_levels, resistance_levels, overall_signal)
        
        return TechnicalAnalysisResult(
            symbol=self.symbol,
            timestamp=timestamp,
            current_price=current_price,
            indicators=indicators,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            patterns=patterns,
            buy_recommendations=buy_recs,
            sell_recommendations=sell_recs,
            timeframe_recommendations=timeframe_recs,
            overall_signal=overall_signal,
            signal_strength=signal_strength,
            analysis_summary=summary
        )
    
    def _determine_overall_signal(self, indicators: TechnicalIndicators, patterns: List[ChartPattern],
                                   supports: List[SupportResistance], resistances: List[SupportResistance],
                                   current_price: float) -> Tuple[str, float]:
        """Determine overall trading signal and strength"""
        bullish_score = 0
        bearish_score = 0
        
        # Trend contribution (weight: 30)
        if indicators.trend == TrendDirection.STRONG_BULLISH:
            bullish_score += 30
        elif indicators.trend == TrendDirection.BULLISH:
            bullish_score += 20
        elif indicators.trend == TrendDirection.STRONG_BEARISH:
            bearish_score += 30
        elif indicators.trend == TrendDirection.BEARISH:
            bearish_score += 20
        
        # MACD contribution (weight: 15)
        if indicators.macd_crossover == "bullish":
            bullish_score += 15
        elif indicators.macd_crossover == "bearish":
            bearish_score += 15
        elif indicators.macd_histogram > 0:
            bullish_score += 5
        else:
            bearish_score += 5
        
        # RSI contribution (weight: 15)
        if indicators.rsi_signal == "oversold":
            bullish_score += 15  # Contrarian
        elif indicators.rsi_signal == "overbought":
            bearish_score += 15  # Contrarian
        elif indicators.rsi_14 > 50:
            bullish_score += 5
        else:
            bearish_score += 5
        
        # Pattern contribution (weight: 25)
        for pattern in patterns[:3]:  # Top 3 patterns
            if pattern.pattern_type in [PatternType.ASCENDING_TRIANGLE, PatternType.BULL_FLAG,
                                        PatternType.DOUBLE_BOTTOM, PatternType.INVERSE_HEAD_SHOULDERS,
                                        PatternType.BULLISH_ENGULFING, PatternType.MORNING_STAR]:
                bullish_score += pattern.confidence * 0.25
            elif pattern.pattern_type in [PatternType.DESCENDING_TRIANGLE, PatternType.BEAR_FLAG,
                                          PatternType.DOUBLE_TOP, PatternType.HEAD_SHOULDERS,
                                          PatternType.BEARISH_ENGULFING, PatternType.EVENING_STAR]:
                bearish_score += pattern.confidence * 0.25
        
        # Support/Resistance proximity (weight: 15)
        if supports:
            closest_support = supports[0]
            support_distance = (current_price - closest_support.price) / current_price
            if support_distance < 0.02:  # Within 2% of support
                bullish_score += 10
        
        if resistances:
            closest_resistance = resistances[0]
            resistance_distance = (closest_resistance.price - current_price) / current_price
            if resistance_distance < 0.02:  # Within 2% of resistance
                bearish_score += 10
        
        # Determine signal
        total_score = bullish_score + bearish_score
        if total_score == 0:
            return "HOLD", 50.0
        
        bullish_pct = bullish_score / max(total_score, 1) * 100
        
        if bullish_pct >= 65:
            return "BUY", bullish_pct
        elif bullish_pct <= 35:
            return "SELL", 100 - bullish_pct
        else:
            return "HOLD", 50.0
    
    def _generate_summary(self, indicators: TechnicalIndicators, patterns: List[ChartPattern],
                          supports: List[SupportResistance], resistances: List[SupportResistance],
                          signal: str) -> str:
        """Generate human-readable analysis summary"""
        parts = []
        
        # Trend
        trend_desc = indicators.trend.value.replace("_", " ").title()
        parts.append(f"Trend: {trend_desc}")
        
        # Key indicators
        parts.append(f"RSI: {indicators.rsi_14:.1f} ({indicators.rsi_signal})")
        
        if indicators.macd_crossover != "none":
            parts.append(f"MACD: {indicators.macd_crossover} crossover")
        
        # Patterns
        if patterns:
            top_pattern = patterns[0]
            parts.append(f"Pattern: {top_pattern.pattern_type.value.replace('_', ' ').title()} ({top_pattern.confidence:.0f}%)")
        
        # Key levels
        if supports:
            parts.append(f"Support: ${supports[0].price:.2f}")
        if resistances:
            parts.append(f"Resistance: ${resistances[0].price:.2f}")
        
        return " | ".join(parts)


# =============================================================================
# Utility Functions
# =============================================================================

def analyze_symbol(symbol: str, df: pd.DataFrame) -> TechnicalAnalysisResult:
    """
    Convenience function to perform full technical analysis
    
    Args:
        symbol: Stock symbol
        df: OHLCV DataFrame
        
    Returns:
        TechnicalAnalysisResult
    """
    analyzer = TechnicalAnalyzer(symbol, df)
    return analyzer.analyze()


def format_analysis_report(result: TechnicalAnalysisResult) -> str:
    """
    Format analysis result as a readable report
    
    Args:
        result: TechnicalAnalysisResult
        
    Returns:
        Formatted string report
    """
    lines = [
        "=" * 70,
        f"TECHNICAL ANALYSIS: {result.symbol}",
        f"Price: ${result.current_price:.2f} | Signal: {result.overall_signal} ({result.signal_strength:.0f}%)",
        "=" * 70,
        "",
        "📊 INDICATORS",
        "-" * 40,
        f"  Trend: {result.indicators.trend.value.replace('_', ' ').title()}",
        f"  RSI(14): {result.indicators.rsi_14:.1f} ({result.indicators.rsi_signal})",
        f"  MACD: {result.indicators.macd_histogram:.4f} (crossover: {result.indicators.macd_crossover})",
        f"  ADX: {result.indicators.adx:.1f} ({result.indicators.trend_strength})",
        f"  Bollinger: ${result.indicators.bollinger_lower:.2f} - ${result.indicators.bollinger_upper:.2f}",
        "",
        "📍 SUPPORT/RESISTANCE",
        "-" * 40,
    ]
    
    for s in result.support_levels[:3]:
        lines.append(f"  Support:    ${s.price:.2f} (strength: {s.strength:.0f}%, touches: {s.touches})")
    for r in result.resistance_levels[:3]:
        lines.append(f"  Resistance: ${r.price:.2f} (strength: {r.strength:.0f}%, touches: {r.touches})")
    
    if result.patterns:
        lines.extend([
            "",
            "📈 PATTERNS DETECTED",
            "-" * 40,
        ])
        for p in result.patterns[:3]:
            lines.append(f"  {p.pattern_type.value.replace('_', ' ').title()} ({p.confidence:.0f}%): {p.description}")
    
    if result.buy_recommendations:
        lines.extend([
            "",
            "🟢 BUY RECOMMENDATIONS",
            "-" * 40,
        ])
        for rec in result.buy_recommendations[:3]:
            lines.append(f"  BUY @ ${rec.entry_price:.2f} → Target ${rec.target_price:.2f} (R:R {rec.risk_reward_ratio:.1f}x)")
            lines.append(f"    Stop: ${rec.stop_loss:.2f} | Probability: {rec.probability:.0f}%")
            lines.append(f"    Reason: {rec.reasoning}")
    
    if result.sell_recommendations:
        lines.extend([
            "",
            "🔴 SELL RECOMMENDATIONS",
            "-" * 40,
        ])
        for rec in result.sell_recommendations[:3]:
            lines.append(f"  SELL @ ${rec.entry_price:.2f} → Target ${rec.target_price:.2f} (R:R {rec.risk_reward_ratio:.1f}x)")
            lines.append(f"    Stop: ${rec.stop_loss:.2f} | Probability: {rec.probability:.0f}%")
            lines.append(f"    Reason: {rec.reasoning}")
    
    lines.extend([
        "",
        "=" * 70,
        f"Summary: {result.analysis_summary}",
        "=" * 70,
    ])
    
    return "\n".join(lines)


# =============================================================================
# Test/Demo
# =============================================================================

if __name__ == "__main__":
    # Demo with sample data
    import yfinance as yf
    
    print("HERMES Technical Analysis Library - Demo")
    print("=" * 50)
    
    # Fetch sample data
    symbol = "QBTS"
    print(f"\nFetching data for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo")
    
    if len(df) > 0:
        print(f"Got {len(df)} bars of data")
        
        # Run analysis
        result = analyze_symbol(symbol, df)
        
        # Print report
        print("\n" + format_analysis_report(result))
    else:
        print("Failed to fetch data")
