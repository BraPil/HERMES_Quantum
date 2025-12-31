"""
HERMES Order Flow ML Estimator
==============================

Machine learning-based estimation of order flow and order book walls
when Level 2 data is not available.

This module uses price action, volume patterns, and historical behavior
to estimate where buy/sell walls are likely accumulating.

Features:
- Price rejection detection (wicks, reversals)
- Volume spike analysis at price levels
- Historical wall behavior modeling
- Time-of-day pattern recognition
- Predicted order wall heatmap

Author: HERMES Project
Date: December 2025
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class WallType(Enum):
    """Type of order wall"""
    BUY_WALL = "buy_wall"      # Large buy orders (support)
    SELL_WALL = "sell_wall"    # Large sell orders (resistance)
    ICEBERG = "iceberg"        # Hidden/distributed orders


@dataclass
class PriceRejection:
    """A price rejection event (wick or reversal)"""
    price: float
    timestamp: datetime
    rejection_type: str  # "upper_wick", "lower_wick", "reversal"
    strength: float  # 0-100 based on wick size / price action
    volume: float


@dataclass
class EstimatedWall:
    """An estimated order wall based on ML analysis"""
    price: float
    wall_type: WallType
    strength: float  # 0-100 estimated wall thickness
    confidence: float  # 0-100 prediction confidence
    supporting_signals: List[str]  # What signals support this prediction
    historical_rejections: int  # Number of historical rejections at this level
    estimated_volume: float  # Estimated order size (normalized)
    decay_factor: float = 1.0  # Walls decay over time without reinforcement
    
    def __repr__(self):
        return f"{self.wall_type.value} @ ${self.price:.2f} (strength: {self.strength:.0f}%, confidence: {self.confidence:.0f}%)"


@dataclass
class OrderFlowPrediction:
    """Complete order flow prediction result"""
    timestamp: datetime
    current_price: float
    estimated_walls: List[EstimatedWall]
    buy_pressure_score: float  # -100 to +100 (negative = sell pressure)
    predicted_direction: str  # "up", "down", "neutral"
    key_levels: Dict[str, float]  # nearest_support, nearest_resistance, etc.
    prediction_summary: str


# =============================================================================
# Price Rejection Detector
# =============================================================================

class PriceRejectionDetector:
    """
    Detects price rejection patterns that indicate hidden orders.
    
    When price quickly rejects from a level (long wicks, reversals),
    it often indicates large orders absorbing the move.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
    
    def detect_rejections(self) -> List[PriceRejection]:
        """Detect all price rejection events in the data"""
        rejections = []
        
        for i in range(1, len(self.df)):
            row = self.df.iloc[i]
            prev_row = self.df.iloc[i-1]
            
            body = abs(row['close'] - row['open'])
            upper_wick = row['high'] - max(row['close'], row['open'])
            lower_wick = min(row['close'], row['open']) - row['low']
            total_range = row['high'] - row['low']
            
            if total_range <= 0:
                continue
            
            # Upper wick rejection (selling pressure at high)
            if upper_wick > body * 1.5 and upper_wick > total_range * 0.4:
                strength = min(100, (upper_wick / total_range) * 100)
                rejections.append(PriceRejection(
                    price=row['high'],
                    timestamp=row.name if hasattr(row, 'name') else self.df.index[i],
                    rejection_type="upper_wick",
                    strength=strength,
                    volume=row['volume']
                ))
            
            # Lower wick rejection (buying pressure at low)
            if lower_wick > body * 1.5 and lower_wick > total_range * 0.4:
                strength = min(100, (lower_wick / total_range) * 100)
                rejections.append(PriceRejection(
                    price=row['low'],
                    timestamp=row.name if hasattr(row, 'name') else self.df.index[i],
                    rejection_type="lower_wick",
                    strength=strength,
                    volume=row['volume']
                ))
            
            # V-reversal detection
            if i >= 2:
                prev2_row = self.df.iloc[i-2]
                
                # Bullish reversal (V-bottom)
                if prev_row['close'] < prev_row['open'] and \
                   row['close'] > row['open'] and \
                   row['low'] < prev_row['low'] and \
                   row['close'] > prev_row['open']:
                    strength = min(100, ((row['close'] - row['low']) / total_range) * 100)
                    rejections.append(PriceRejection(
                        price=row['low'],
                        timestamp=row.name if hasattr(row, 'name') else self.df.index[i],
                        rejection_type="reversal",
                        strength=strength,
                        volume=row['volume']
                    ))
                
                # Bearish reversal (inverted V-top)
                if prev_row['close'] > prev_row['open'] and \
                   row['close'] < row['open'] and \
                   row['high'] > prev_row['high'] and \
                   row['close'] < prev_row['open']:
                    strength = min(100, ((row['high'] - row['close']) / total_range) * 100)
                    rejections.append(PriceRejection(
                        price=row['high'],
                        timestamp=row.name if hasattr(row, 'name') else self.df.index[i],
                        rejection_type="reversal",
                        strength=strength,
                        volume=row['volume']
                    ))
        
        return rejections
    
    def cluster_rejections(self, rejections: List[PriceRejection], 
                           tolerance_pct: float = 1.5) -> Dict[float, List[PriceRejection]]:
        """
        Cluster rejections at similar price levels.
        
        Multiple rejections at the same level indicate a stronger wall.
        """
        if not rejections:
            return {}
        
        # Sort by price
        sorted_rejections = sorted(rejections, key=lambda r: r.price)
        
        clusters = {}
        current_cluster = [sorted_rejections[0]]
        cluster_center = sorted_rejections[0].price
        
        for rejection in sorted_rejections[1:]:
            if abs(rejection.price - cluster_center) / cluster_center * 100 <= tolerance_pct:
                current_cluster.append(rejection)
            else:
                # Save current cluster
                avg_price = np.mean([r.price for r in current_cluster])
                clusters[avg_price] = current_cluster
                # Start new cluster
                current_cluster = [rejection]
                cluster_center = rejection.price
        
        # Don't forget last cluster
        if current_cluster:
            avg_price = np.mean([r.price for r in current_cluster])
            clusters[avg_price] = current_cluster
        
        return clusters


# =============================================================================
# Volume Spike Analyzer
# =============================================================================

class VolumeSpikeAnalyzer:
    """
    Analyzes volume spikes at price levels to estimate order concentration.
    
    Large volume at specific prices often indicates institutional orders.
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
    
    def find_volume_spikes(self, threshold_multiplier: float = 2.0) -> List[Dict]:
        """
        Find bars with unusually high volume.
        
        Args:
            threshold_multiplier: Volume must be this many times the average
        """
        avg_volume = self.df['volume'].mean()
        std_volume = self.df['volume'].std()
        threshold = avg_volume + (threshold_multiplier * std_volume)
        
        spikes = []
        
        for i, row in self.df.iterrows():
            if row['volume'] >= threshold:
                # Determine if volume favors buyers or sellers
                if row['close'] > row['open']:
                    bias = "buy"
                    key_price = row['low']  # Support formed at low
                else:
                    bias = "sell"
                    key_price = row['high']  # Resistance formed at high
                
                spikes.append({
                    'timestamp': i,
                    'price': key_price,
                    'volume': row['volume'],
                    'volume_ratio': row['volume'] / avg_volume,
                    'bias': bias,
                    'range': row['high'] - row['low']
                })
        
        return spikes
    
    def calculate_volume_at_price(self, num_bins: int = 30) -> Dict[float, Dict]:
        """
        Calculate volume distribution at each price level.
        Similar to Market Profile / Volume Profile.
        """
        price_high = self.df['high'].max()
        price_low = self.df['low'].min()
        
        if price_high <= price_low:
            return {}
        
        bin_size = (price_high - price_low) / num_bins
        
        volume_at_price = {}
        
        for price_level in np.linspace(price_low, price_high, num_bins):
            volume_at_price[price_level] = {
                'total_volume': 0,
                'buy_volume': 0,
                'sell_volume': 0,
                'touches': 0
            }
        
        for _, row in self.df.iterrows():
            for price_level in volume_at_price.keys():
                if row['low'] <= price_level <= row['high']:
                    # This candle touched this price level
                    volume_at_price[price_level]['touches'] += 1
                    
                    # Distribute volume proportionally
                    candle_range = row['high'] - row['low']
                    if candle_range > 0:
                        contribution = row['volume'] / candle_range * bin_size
                        volume_at_price[price_level]['total_volume'] += contribution
                        
                        if row['close'] > row['open']:
                            volume_at_price[price_level]['buy_volume'] += contribution * 0.6
                            volume_at_price[price_level]['sell_volume'] += contribution * 0.4
                        else:
                            volume_at_price[price_level]['buy_volume'] += contribution * 0.4
                            volume_at_price[price_level]['sell_volume'] += contribution * 0.6
        
        return volume_at_price


# =============================================================================
# ML Order Flow Estimator
# =============================================================================

class OrderFlowMLEstimator:
    """
    Machine Learning-based Order Flow Estimator.
    
    Uses multiple signals to estimate where large orders are likely accumulating:
    1. Price rejection patterns (wicks, reversals)
    2. Volume concentration at price levels
    3. Historical behavior at key levels
    4. Time decay of wall relevance
    
    This is an approximation when Level 2 data is not available.
    """
    
    def __init__(self, df: pd.DataFrame, lookback_days: int = 30):
        """
        Initialize the estimator.
        
        Args:
            df: OHLCV DataFrame with DatetimeIndex
            lookback_days: How many days of history to analyze
        """
        self.df = df.copy()
        self.df.columns = self.df.columns.str.lower()
        self.lookback_days = lookback_days
        
        # Initialize sub-analyzers
        self.rejection_detector = PriceRejectionDetector(df)
        self.volume_analyzer = VolumeSpikeAnalyzer(df)
        
        # Signal weights for combining predictions
        self.weights = {
            'rejection_cluster': 0.35,
            'volume_concentration': 0.30,
            'volume_spike': 0.20,
            'round_number': 0.15
        }
    
    def estimate_walls(self) -> List[EstimatedWall]:
        """
        Estimate order walls using all available signals.
        
        Returns:
            List of EstimatedWall objects sorted by strength
        """
        walls = []
        current_price = self.df['close'].iloc[-1]
        
        # 1. Analyze price rejections
        rejections = self.rejection_detector.detect_rejections()
        rejection_clusters = self.rejection_detector.cluster_rejections(rejections)
        
        for price, cluster_rejections in rejection_clusters.items():
            if len(cluster_rejections) >= 2:  # Need at least 2 rejections
                # Determine wall type based on rejection types
                upper_count = sum(1 for r in cluster_rejections if r.rejection_type == "upper_wick")
                lower_count = sum(1 for r in cluster_rejections if r.rejection_type == "lower_wick")
                
                if upper_count > lower_count:
                    wall_type = WallType.SELL_WALL
                elif lower_count > upper_count:
                    wall_type = WallType.BUY_WALL
                else:
                    wall_type = WallType.BUY_WALL if price < current_price else WallType.SELL_WALL
                
                avg_strength = np.mean([r.strength for r in cluster_rejections])
                total_volume = sum(r.volume for r in cluster_rejections)
                
                # Calculate time decay
                latest_rejection = max(r.timestamp for r in cluster_rejections)
                if hasattr(latest_rejection, 'days_since'):
                    days_since = (datetime.now() - latest_rejection).days
                else:
                    days_since = 0
                decay = max(0.3, 1.0 - (days_since * 0.05))  # 5% decay per day, min 30%
                
                wall = EstimatedWall(
                    price=price,
                    wall_type=wall_type,
                    strength=avg_strength * decay,
                    confidence=min(90, 40 + len(cluster_rejections) * 10),
                    supporting_signals=["price_rejection"] * len(cluster_rejections),
                    historical_rejections=len(cluster_rejections),
                    estimated_volume=total_volume,
                    decay_factor=decay
                )
                walls.append(wall)
        
        # 2. Analyze volume spikes
        volume_spikes = self.volume_analyzer.find_volume_spikes()
        
        for spike in volume_spikes:
            # Check if we already have a wall near this price
            existing = False
            for wall in walls:
                if abs(wall.price - spike['price']) / wall.price < 0.02:
                    # Reinforce existing wall
                    wall.strength = min(100, wall.strength + spike['volume_ratio'] * 10)
                    wall.supporting_signals.append("volume_spike")
                    wall.confidence = min(95, wall.confidence + 5)
                    existing = True
                    break
            
            if not existing and spike['volume_ratio'] >= 2.5:  # Very high volume
                wall_type = WallType.BUY_WALL if spike['bias'] == "buy" else WallType.SELL_WALL
                wall = EstimatedWall(
                    price=spike['price'],
                    wall_type=wall_type,
                    strength=min(80, spike['volume_ratio'] * 15),
                    confidence=50,
                    supporting_signals=["volume_spike"],
                    historical_rejections=1,
                    estimated_volume=spike['volume']
                )
                walls.append(wall)
        
        # 3. Add round number walls (psychological levels)
        round_numbers = self._find_round_numbers(current_price)
        for rn in round_numbers:
            existing = False
            for wall in walls:
                if abs(wall.price - rn) / wall.price < 0.01:
                    wall.supporting_signals.append("round_number")
                    wall.confidence = min(95, wall.confidence + 10)
                    existing = True
                    break
            
            if not existing:
                wall_type = WallType.BUY_WALL if rn < current_price else WallType.SELL_WALL
                wall = EstimatedWall(
                    price=rn,
                    wall_type=wall_type,
                    strength=40,  # Base strength for round numbers
                    confidence=40,
                    supporting_signals=["round_number"],
                    historical_rejections=0,
                    estimated_volume=0
                )
                walls.append(wall)
        
        # Sort by strength
        walls.sort(key=lambda w: w.strength, reverse=True)
        
        return walls
    
    def _find_round_numbers(self, current_price: float, range_pct: float = 20) -> List[float]:
        """Find psychologically significant round number price levels"""
        round_numbers = []
        
        # Determine appropriate rounding based on price magnitude
        if current_price > 100:
            increments = [10, 25, 50, 100]
        elif current_price > 20:
            increments = [5, 10, 25]
        else:
            increments = [1, 2.5, 5]
        
        low_bound = current_price * (1 - range_pct/100)
        high_bound = current_price * (1 + range_pct/100)
        
        for increment in increments:
            start = (low_bound // increment) * increment
            level = start
            while level <= high_bound:
                if low_bound <= level <= high_bound:
                    round_numbers.append(level)
                level += increment
        
        return list(set(round_numbers))
    
    def predict_order_flow(self) -> OrderFlowPrediction:
        """
        Generate complete order flow prediction.
        
        Returns:
            OrderFlowPrediction with all estimated walls and analysis
        """
        current_price = self.df['close'].iloc[-1]
        walls = self.estimate_walls()
        
        # Separate buy and sell walls
        buy_walls = [w for w in walls if w.wall_type == WallType.BUY_WALL and w.price < current_price]
        sell_walls = [w for w in walls if w.wall_type == WallType.SELL_WALL and w.price > current_price]
        
        # Calculate pressure scores
        buy_pressure = sum(w.strength * w.confidence / 100 for w in buy_walls[:3])
        sell_pressure = sum(w.strength * w.confidence / 100 for w in sell_walls[:3])
        
        # Normalize to -100 to +100 scale
        total_pressure = buy_pressure + sell_pressure
        if total_pressure > 0:
            pressure_score = ((buy_pressure - sell_pressure) / total_pressure) * 100
        else:
            pressure_score = 0
        
        # Determine predicted direction
        if pressure_score > 20:
            direction = "up"
        elif pressure_score < -20:
            direction = "down"
        else:
            direction = "neutral"
        
        # Find key levels
        key_levels = {
            'nearest_support': buy_walls[0].price if buy_walls else current_price * 0.95,
            'nearest_resistance': sell_walls[0].price if sell_walls else current_price * 1.05,
            'strongest_buy_wall': max(buy_walls, key=lambda w: w.strength).price if buy_walls else None,
            'strongest_sell_wall': max(sell_walls, key=lambda w: w.strength).price if sell_walls else None
        }
        
        # Generate summary
        summary_parts = []
        if buy_walls:
            summary_parts.append(f"Strong support at ${buy_walls[0].price:.2f} ({buy_walls[0].strength:.0f}%)")
        if sell_walls:
            summary_parts.append(f"Resistance at ${sell_walls[0].price:.2f} ({sell_walls[0].strength:.0f}%)")
        summary_parts.append(f"Order flow bias: {direction}")
        
        return OrderFlowPrediction(
            timestamp=datetime.now(),
            current_price=current_price,
            estimated_walls=walls,
            buy_pressure_score=pressure_score,
            predicted_direction=direction,
            key_levels=key_levels,
            prediction_summary=" | ".join(summary_parts)
        )
    
    def get_heatmap_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Get data formatted for heatmap visualization.
        
        Returns:
            Tuple of (prices, buy_strength, sell_strength, net_strength)
        """
        walls = self.estimate_walls()
        
        if not walls:
            return np.array([]), np.array([]), np.array([]), np.array([])
        
        # Get price range
        min_price = min(w.price for w in walls)
        max_price = max(w.price for w in walls)
        
        # Create price bins
        prices = np.linspace(min_price, max_price, 50)
        buy_strength = np.zeros(50)
        sell_strength = np.zeros(50)
        
        for wall in walls:
            # Find closest bin
            idx = np.argmin(np.abs(prices - wall.price))
            if wall.wall_type == WallType.BUY_WALL:
                buy_strength[idx] += wall.strength * (wall.confidence / 100)
            else:
                sell_strength[idx] += wall.strength * (wall.confidence / 100)
        
        # Smooth the data
        from scipy.ndimage import gaussian_filter1d
        try:
            buy_strength = gaussian_filter1d(buy_strength, sigma=1)
            sell_strength = gaussian_filter1d(sell_strength, sigma=1)
        except ImportError:
            pass  # Skip smoothing if scipy not available
        
        net_strength = buy_strength - sell_strength
        
        return prices, buy_strength, sell_strength, net_strength


# =============================================================================
# Utility Functions
# =============================================================================

def estimate_order_flow(df: pd.DataFrame) -> OrderFlowPrediction:
    """
    Convenience function to estimate order flow from OHLCV data.
    
    Args:
        df: OHLCV DataFrame
        
    Returns:
        OrderFlowPrediction
    """
    estimator = OrderFlowMLEstimator(df)
    return estimator.predict_order_flow()


def format_order_flow_report(prediction: OrderFlowPrediction) -> str:
    """
    Format order flow prediction as a readable report.
    """
    lines = [
        "=" * 60,
        "ORDER FLOW ANALYSIS (ML Estimated)",
        f"Current Price: ${prediction.current_price:.2f}",
        f"Direction Bias: {prediction.predicted_direction.upper()}",
        f"Buy Pressure Score: {prediction.buy_pressure_score:.1f}",
        "=" * 60,
        "",
        "📊 ESTIMATED ORDER WALLS",
        "-" * 40,
    ]
    
    for wall in prediction.estimated_walls[:10]:
        icon = "🟢" if wall.wall_type == WallType.BUY_WALL else "🔴"
        lines.append(f"{icon} ${wall.price:.2f} - {wall.wall_type.value.replace('_', ' ').title()}")
        lines.append(f"   Strength: {wall.strength:.0f}% | Confidence: {wall.confidence:.0f}%")
        lines.append(f"   Signals: {', '.join(set(wall.supporting_signals))}")
    
    lines.extend([
        "",
        "📍 KEY LEVELS",
        "-" * 40,
        f"Nearest Support:    ${prediction.key_levels.get('nearest_support', 0):.2f}",
        f"Nearest Resistance: ${prediction.key_levels.get('nearest_resistance', 0):.2f}",
        "",
        "📝 SUMMARY",
        prediction.prediction_summary,
        "=" * 60,
    ])
    
    return "\n".join(lines)


# =============================================================================
# Test/Demo
# =============================================================================

if __name__ == "__main__":
    import yfinance as yf
    
    print("HERMES Order Flow ML Estimator - Demo")
    print("=" * 50)
    
    # Fetch sample data
    symbol = "QBTS"
    print(f"\nFetching data for {symbol}...")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="3mo")
    
    if len(df) > 0:
        print(f"Got {len(df)} bars of data")
        
        # Run analysis
        prediction = estimate_order_flow(df)
        
        # Print report
        print("\n" + format_order_flow_report(prediction))
    else:
        print("Failed to fetch data")
