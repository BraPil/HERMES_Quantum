"""
Agent 25: Market Forecaster
Uses amazon/chronos-t5 for time series forecasting

Purpose: Forecast stock prices and generate trading signals
Output: Price predictions, confidence intervals, trend analysis
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Time series forecast result"""
    ticker: str
    forecast_horizon: int  # Number of periods ahead
    predictions: np.ndarray  # Shape: (horizon,) - median predictions
    lower_bound: np.ndarray  # 10th percentile
    upper_bound: np.ndarray  # 90th percentile
    confidence: float  # Confidence score [0, 1]
    context_length: int  # Historical data points used
    timestamp: datetime
    current_price: float
    signal: str  # BUY, SELL, HOLD
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'forecast_horizon': self.forecast_horizon,
            'predictions': self.predictions.tolist(),
            'lower_bound': self.lower_bound.tolist(),
            'upper_bound': self.upper_bound.tolist(),
            'confidence': self.confidence,
            'context_length': self.context_length,
            'timestamp': self.timestamp.isoformat(),
            'current_price': self.current_price,
            'signal': self.signal,
            'expected_return': self.expected_return,
            'trend': self.trend
        }
    
    @property
    def expected_return(self) -> float:
        """Calculate expected return from current price to final prediction"""
        if self.current_price == 0:
            return 0.0
        return (self.predictions[-1] - self.current_price) / self.current_price
    
    @property
    def trend(self) -> str:
        """Determine overall trend direction"""
        if len(self.predictions) < 2:
            return "FLAT"
        
        # Calculate trend strength
        returns = np.diff(self.predictions) / self.predictions[:-1]
        avg_return = np.mean(returns)
        
        if avg_return > 0.01:  # >1% average daily return
            return "STRONG_UPTREND"
        elif avg_return > 0.002:  # >0.2% average daily return
            return "UPTREND"
        elif avg_return < -0.01:
            return "STRONG_DOWNTREND"
        elif avg_return < -0.002:
            return "DOWNTREND"
        else:
            return "FLAT"


class Agent25_MarketForecaster:
    """
    Agent 25: Market Time Series Forecaster
    
    Uses Amazon Chronos-T5 for probabilistic time series forecasting
    of stock prices.
    
    Model: amazon/chronos-t5-large (or t5-small for testing)
    - Pretrained on diverse time series datasets
    - Probabilistic forecasts with confidence intervals
    - Supports multiple prediction horizons
    """
    
    def __init__(
        self,
        model_name: str = "amazon/chronos-t5-small",  # Use 'large' in production
        device: Optional[str] = None,
        num_samples: int = 50  # Number of samples for probabilistic forecast
    ):
        """
        Initialize the market forecaster.
        
        Args:
            model_name: Chronos model variant (small, base, large)
            device: 'cuda', 'cpu', or None (auto-detect)
            num_samples: Number of Monte Carlo samples for uncertainty
        """
        self.model_name = model_name
        self.num_samples = num_samples
        
        # Auto-detect device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Initializing Agent 25 on device: {self.device}")
        
        # Load model
        self._load_model()
        
        logger.info("Agent 25 initialized successfully")
    
    def _load_model(self):
        """Load Chronos model"""
        try:
            # Chronos requires special import
            try:
                from chronos import ChronosPipeline
            except ImportError:
                logger.error("chronos-forecasting not installed. Run: pip install chronos-forecasting")
                raise
            
            logger.info(f"Loading {self.model_name}...")
            
            self.pipeline = ChronosPipeline.from_pretrained(
                self.model_name,
                device_map=self.device,
                torch_dtype=torch.float32
            )
            
            logger.info(f"✅ {self.model_name} loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def forecast(
        self,
        ticker: str,
        prices: Union[pd.Series, np.ndarray, List[float]],
        forecast_horizon: int = 5,
        current_price: Optional[float] = None
    ) -> ForecastResult:
        """
        Generate probabilistic forecast for a stock.
        
        Args:
            ticker: Stock ticker symbol
            prices: Historical prices (most recent last)
            forecast_horizon: Number of periods to forecast
            current_price: Current price (uses last price if None)
            
        Returns:
            ForecastResult with predictions and metadata
        """
        # Convert to tensor
        if isinstance(prices, pd.Series):
            prices_array = prices.values
        elif isinstance(prices, list):
            prices_array = np.array(prices)
        else:
            prices_array = prices
        
        if current_price is None:
            current_price = float(prices_array[-1])
        
        context = torch.tensor([prices_array]).float()
        
        # Generate forecast
        forecast = self.pipeline.predict(
            context,
            prediction_length=forecast_horizon,
            num_samples=self.num_samples
        )
        
        # Extract statistics
        predictions = torch.median(forecast, dim=1).values[0].numpy()
        lower_bound = torch.quantile(forecast, 0.1, dim=1)[0].numpy()
        upper_bound = torch.quantile(forecast, 0.9, dim=1)[0].numpy()
        
        # Calculate confidence (inverse of normalized uncertainty)
        uncertainty = np.mean((upper_bound - lower_bound) / predictions)
        confidence = 1.0 / (1.0 + uncertainty)
        
        # Generate trading signal
        signal = self._generate_signal(current_price, predictions, confidence)
        
        return ForecastResult(
            ticker=ticker,
            forecast_horizon=forecast_horizon,
            predictions=predictions,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence=confidence,
            context_length=len(prices_array),
            timestamp=datetime.now(),
            current_price=current_price,
            signal=signal
        )
    
    def _generate_signal(
        self,
        current_price: float,
        predictions: np.ndarray,
        confidence: float
    ) -> str:
        """
        Generate trading signal based on forecast.
        
        Args:
            current_price: Current stock price
            predictions: Forecasted prices
            confidence: Model confidence
            
        Returns:
            Trading signal: BUY, SELL, or HOLD
        """
        # Calculate expected return
        expected_return = (predictions[-1] - current_price) / current_price
        
        # Thresholds (adjust based on risk tolerance)
        BUY_THRESHOLD = 0.03  # 3% expected gain
        SELL_THRESHOLD = -0.02  # 2% expected loss
        MIN_CONFIDENCE = 0.6
        
        if confidence < MIN_CONFIDENCE:
            return "HOLD"  # Low confidence, stay neutral
        
        if expected_return > BUY_THRESHOLD:
            return "BUY"
        elif expected_return < SELL_THRESHOLD:
            return "SELL"
        else:
            return "HOLD"
    
    def forecast_batch(
        self,
        tickers: List[str],
        prices_dict: Dict[str, Union[pd.Series, np.ndarray]],
        forecast_horizon: int = 5
    ) -> Dict[str, ForecastResult]:
        """
        Forecast multiple stocks.
        
        Args:
            tickers: List of ticker symbols
            prices_dict: Dictionary mapping tickers to price series
            forecast_horizon: Number of periods to forecast
            
        Returns:
            Dictionary mapping tickers to ForecastResults
        """
        results = {}
        
        for ticker in tickers:
            if ticker not in prices_dict:
                logger.warning(f"No price data for {ticker}, skipping")
                continue
            
            try:
                results[ticker] = self.forecast(
                    ticker,
                    prices_dict[ticker],
                    forecast_horizon
                )
            except Exception as e:
                logger.error(f"Error forecasting {ticker}: {e}")
        
        return results
    
    def get_portfolio_signals(
        self,
        forecast_results: Dict[str, ForecastResult],
        top_n: int = 3
    ) -> List[Dict]:
        """
        Rank stocks by expected return and confidence.
        
        Args:
            forecast_results: Dictionary of ForecastResults
            top_n: Number of top stocks to return
            
        Returns:
            List of top stock signals with metrics
        """
        signals = []
        
        for ticker, result in forecast_results.items():
            signals.append({
                'ticker': ticker,
                'signal': result.signal,
                'expected_return': result.expected_return,
                'confidence': result.confidence,
                'trend': result.trend,
                'current_price': result.current_price,
                'forecast_price': result.predictions[-1],
                'score': result.expected_return * result.confidence  # Risk-adjusted score
            })
        
        # Sort by score (expected return * confidence)
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        return signals[:top_n]
    
    def backtest_accuracy(
        self,
        ticker: str,
        historical_prices: pd.Series,
        test_days: int = 30,
        forecast_horizon: int = 5
    ) -> Dict[str, float]:
        """
        Backtest forecast accuracy on historical data.
        
        Args:
            ticker: Stock ticker
            historical_prices: Full historical price series
            test_days: Number of days to backtest
            forecast_horizon: Forecast horizon
            
        Returns:
            Dictionary with accuracy metrics
        """
        errors = []
        
        for i in range(len(historical_prices) - test_days - forecast_horizon, len(historical_prices) - forecast_horizon):
            # Use data up to day i
            context = historical_prices[:i]
            
            # Forecast next `forecast_horizon` days
            result = self.forecast(ticker, context, forecast_horizon)
            
            # Compare with actual prices
            actual = historical_prices[i:i+forecast_horizon].values
            predicted = result.predictions
            
            # Calculate error
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            errors.append(mape)
        
        return {
            'mean_mape': np.mean(errors),
            'std_mape': np.std(errors),
            'median_mape': np.median(errors),
            'num_tests': len(errors)
        }


def main():
    """Test Agent 25 with quantum stock data"""
    
    # Initialize agent
    print("\n" + "="*70)
    print("Agent 25: Market Forecaster Test")
    print("="*70 + "\n")
    
    try:
        agent = Agent25_MarketForecaster(model_name="amazon/chronos-t5-small")
    except ImportError:
        print("⚠️ chronos-forecasting not installed")
        print("Run: pip install chronos-forecasting")
        return
    
    # Generate synthetic price data (simulating quantum stock)
    np.random.seed(42)
    days = 60
    base_price = 50.0
    returns = np.random.randn(days) * 0.03  # 3% daily volatility
    prices = base_price * np.exp(np.cumsum(returns))
    
    print(f"Historical Data: {days} days of price data")
    print(f"Current Price: ${prices[-1]:.2f}")
    print(f"Price Range: ${prices.min():.2f} - ${prices.max():.2f}\n")
    
    # Forecast next 5 days
    result = agent.forecast(
        ticker="TEST",
        prices=prices,
        forecast_horizon=5
    )
    
    print("-"*70)
    print("5-Day Forecast:")
    print("-"*70)
    
    for i, (pred, lower, upper) in enumerate(zip(result.predictions, result.lower_bound, result.upper_bound), 1):
        direction = "📈" if pred > result.current_price else "📉"
        print(f"Day {i}: ${pred:.2f} {direction} (80% CI: ${lower:.2f} - ${upper:.2f})")
    
    print("\n" + "-"*70)
    print("Analysis:")
    print("-"*70)
    print(f"Signal: {result.signal}")
    print(f"Expected Return: {result.expected_return:+.2%}")
    print(f"Trend: {result.trend}")
    print(f"Confidence: {result.confidence:.3f}")
    
    # Test with quantum stock tickers
    print("\n" + "="*70)
    print("Quantum Stock Universe Test")
    print("="*70 + "\n")
    
    tickers = ['IONQ', 'QBTS', 'RGTI', 'QUBT']
    prices_dict = {}
    
    # Generate synthetic data for each ticker
    for ticker in tickers:
        np.random.seed(hash(ticker) % 2**32)
        returns = np.random.randn(60) * 0.04
        prices_dict[ticker] = 30.0 * np.exp(np.cumsum(returns))
    
    # Batch forecast
    results = agent.forecast_batch(tickers, prices_dict, forecast_horizon=5)
    
    # Get top signals
    top_signals = agent.get_portfolio_signals(results, top_n=3)
    
    print("Top 3 Trading Opportunities:")
    print("-"*70)
    
    for i, signal in enumerate(top_signals, 1):
        emoji = "🟢" if signal['signal'] == 'BUY' else "🔴" if signal['signal'] == 'SELL' else "🟡"
        print(f"{i}. {emoji} ${signal['ticker']:4s} | {signal['signal']:4s} | Return: {signal['expected_return']:+.2%} | Confidence: {signal['confidence']:.3f} | Score: {signal['score']:+.4f}")
    
    print("\n" + "="*70)
    print("✅ Agent 25 test complete!")
    print("="*70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
