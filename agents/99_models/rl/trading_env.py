"""
HERMES Quantum - Custom Trading Environment for RL

Gym-compatible trading environment for training RL agents
on quantum/speculative stock trading strategies.

Author: HERMES Development Team
Version: 0.1.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import IntEnum
import logging
from datetime import datetime
import json

# Try to import gymnasium (preferred) or gym
try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_VERSION = "gymnasium"
except ImportError:
    try:
        import gym
        from gym import spaces
        GYM_VERSION = "gym"
    except ImportError:
        gym = None
        spaces = None
        GYM_VERSION = None

logger = logging.getLogger(__name__)


class Action(IntEnum):
    """Trading actions"""
    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class MarketState:
    """Represents the current market state"""
    timestamp: datetime
    prices: Dict[str, float]  # symbol -> price
    volumes: Dict[str, float]  # symbol -> volume
    
    # Technical indicators
    rsi: Dict[str, float] = field(default_factory=dict)
    macd: Dict[str, float] = field(default_factory=dict)
    bollinger_position: Dict[str, float] = field(default_factory=dict)  # -1 to 1
    sma_20: Dict[str, float] = field(default_factory=dict)
    sma_50: Dict[str, float] = field(default_factory=dict)
    
    # Sentiment scores from HERMES agents
    sentiment_scores: Dict[str, float] = field(default_factory=dict)  # symbol -> [-1, 1]
    social_sentiment: Dict[str, float] = field(default_factory=dict)
    news_sentiment: Dict[str, float] = field(default_factory=dict)
    
    # Volatility and risk
    volatility: Dict[str, float] = field(default_factory=dict)
    beta: Dict[str, float] = field(default_factory=dict)
    
    def to_array(self, symbols: List[str]) -> np.ndarray:
        """Convert market state to flat observation array"""
        features = []
        
        for symbol in symbols:
            # Price-related (normalized)
            features.append(self.prices.get(symbol, 0))
            features.append(np.log1p(self.volumes.get(symbol, 0)) / 20)  # Log normalize
            
            # Technical indicators
            features.append(self.rsi.get(symbol, 50) / 100)  # Normalize RSI to [0, 1]
            features.append(self.macd.get(symbol, 0))
            features.append(self.bollinger_position.get(symbol, 0))  # Already [-1, 1]
            
            # Sentiment
            features.append(self.sentiment_scores.get(symbol, 0))
            features.append(self.social_sentiment.get(symbol, 0))
            features.append(self.news_sentiment.get(symbol, 0))
            
            # Risk metrics
            features.append(self.volatility.get(symbol, 0.02) * 10)  # Scale volatility
            features.append(self.beta.get(symbol, 1.0))
        
        return np.array(features, dtype=np.float32)


@dataclass
class Portfolio:
    """Portfolio state"""
    cash: float
    positions: Dict[str, int]  # symbol -> shares
    entry_prices: Dict[str, float]  # symbol -> avg entry price
    
    def get_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            shares * prices.get(symbol, 0)
            for symbol, shares in self.positions.items()
        )
        return self.cash + position_value
    
    def get_position_value(self, symbol: str, price: float) -> float:
        """Get value of a specific position"""
        return self.positions.get(symbol, 0) * price
    
    def get_unrealized_pnl(self, prices: Dict[str, float]) -> float:
        """Calculate unrealized P&L"""
        pnl = 0
        for symbol, shares in self.positions.items():
            if shares > 0 and symbol in self.entry_prices:
                current_price = prices.get(symbol, 0)
                entry_price = self.entry_prices[symbol]
                pnl += shares * (current_price - entry_price)
        return pnl


# Base class for environment
if gym is not None:
    _EnvBase = gym.Env
else:
    _EnvBase = object


class TradingEnvironment(_EnvBase):
    """
    Custom trading environment for RL agents.
    Inherits from gymnasium.Env for stable-baselines3 compatibility.
    
    Features:
    - Multi-asset trading
    - Continuous observation space with technical + sentiment features
    - Discrete action space: HOLD, BUY, SELL per asset
    - Realistic transaction costs and slippage
    - Position sizing based on portfolio value
    """
    
    # For gymnasium compatibility
    metadata = {"render_modes": ["human", "ansi"]}
    
    def __init__(
        self,
        symbols: List[str],
        initial_cash: float = 100_000.0,
        max_position_pct: float = 0.20,  # Max 20% in single position
        transaction_cost: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005,  # 0.05% slippage
        max_steps: int = 252,  # Trading days in a year
        reward_scaling: float = 100.0,
        lookback_window: int = 10,
        render_mode: Optional[str] = None,
    ):
        """
        Initialize trading environment.
        
        Args:
            symbols: List of stock symbols to trade
            initial_cash: Starting cash amount
            max_position_pct: Maximum portfolio % in single position
            transaction_cost: Transaction cost as fraction
            slippage: Slippage as fraction of price
            max_steps: Maximum steps per episode
            reward_scaling: Scale factor for rewards
            lookback_window: Number of past states to include
            render_mode: Rendering mode for gymnasium
        """
        # Call parent __init__ if available
        if gym is not None:
            super().__init__()
        
        self.render_mode = render_mode
        self.symbols = symbols
        self.n_assets = len(symbols)
        self.initial_cash = initial_cash
        self.max_position_pct = max_position_pct
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        self.max_steps = max_steps
        self.reward_scaling = reward_scaling
        self.lookback_window = lookback_window
        
        # Features per asset: price, volume, rsi, macd, bollinger, 
        # sentiment (3), volatility, beta = 10 features
        self.features_per_asset = 10
        
        # Additional portfolio features: cash_ratio, total_value_pct, per-asset positions
        self.portfolio_features = 2 + self.n_assets
        
        # Total observation size
        self.obs_size = (
            self.features_per_asset * self.n_assets + 
            self.portfolio_features
        )
        
        # Define spaces
        if spaces is not None:
            # Observation: market features + portfolio state
            self.observation_space = spaces.Box(
                low=-np.inf,
                high=np.inf,
                shape=(self.obs_size,),
                dtype=np.float32
            )
            
            # Action: 0=HOLD, 1=BUY, 2=SELL for each asset
            self.action_space = spaces.MultiDiscrete([3] * self.n_assets)
        else:
            self.observation_space = None
            self.action_space = None
        
        # State tracking
        self.portfolio: Optional[Portfolio] = None
        self.market_data: List[MarketState] = []
        self.current_step = 0
        self.episode_trades: List[Dict] = []
        self.episode_rewards: List[float] = []
        
        # Price history for returns calculation
        self.price_history: Dict[str, List[float]] = {s: [] for s in symbols}
        
        logger.info(f"TradingEnvironment initialized: {self.n_assets} assets, "
                   f"obs_size={self.obs_size}")
    
    def load_market_data(self, data: List[MarketState]) -> None:
        """Load historical market data for training"""
        self.market_data = data
        logger.info(f"Loaded {len(data)} market states")
    
    def reset(
        self, 
        seed: Optional[int] = None,
        options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Reset environment to initial state"""
        if seed is not None:
            np.random.seed(seed)
        
        # Reset portfolio
        self.portfolio = Portfolio(
            cash=self.initial_cash,
            positions={s: 0 for s in self.symbols},
            entry_prices={s: 0 for s in self.symbols}
        )
        
        # Reset tracking
        self.current_step = 0
        self.episode_trades = []
        self.episode_rewards = []
        self.price_history = {s: [] for s in self.symbols}
        
        # Get initial observation
        obs = self._get_observation()
        info = {"portfolio_value": self.initial_cash}
        
        return obs, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Array of actions per asset (0=HOLD, 1=BUY, 2=SELL)
            
        Returns:
            observation, reward, terminated, truncated, info
        """
        if self.current_step >= len(self.market_data) - 1:
            return self._get_observation(), 0.0, True, False, {}
        
        # Get current market state
        current_state = self.market_data[self.current_step]
        current_prices = current_state.prices
        
        # Store pre-action portfolio value
        pre_value = self.portfolio.get_value(current_prices)
        
        # Store prices for return calculation
        for symbol in self.symbols:
            self.price_history[symbol].append(current_prices.get(symbol, 0))
        
        # Execute actions
        for i, symbol in enumerate(self.symbols):
            action_type = Action(action[i])
            self._execute_action(symbol, action_type, current_prices)
        
        # Move to next step
        self.current_step += 1
        
        # Get new market state and calculate reward
        if self.current_step < len(self.market_data):
            next_state = self.market_data[self.current_step]
            next_prices = next_state.prices
            post_value = self.portfolio.get_value(next_prices)
            
            # Calculate reward (portfolio return)
            returns = (post_value - pre_value) / pre_value if pre_value > 0 else 0
            reward = returns * self.reward_scaling
            
            # Add risk-adjusted component (penalize high volatility)
            reward -= self._calculate_risk_penalty()
            
        else:
            reward = 0.0
            post_value = pre_value
        
        self.episode_rewards.append(reward)
        
        # Check termination
        terminated = self.current_step >= len(self.market_data) - 1
        truncated = self.current_step >= self.max_steps
        
        # Check for bankruptcy
        if post_value < self.initial_cash * 0.5:  # Lost 50%
            terminated = True
            reward -= 10.0  # Penalty for bankruptcy
        
        # Build info dict
        info = {
            "portfolio_value": post_value,
            "cash": self.portfolio.cash,
            "positions": dict(self.portfolio.positions),
            "unrealized_pnl": self.portfolio.get_unrealized_pnl(
                self.market_data[self.current_step].prices if self.current_step < len(self.market_data) else {}
            ),
            "step": self.current_step,
            "n_trades": len(self.episode_trades),
        }
        
        obs = self._get_observation()
        
        return obs, reward, terminated, truncated, info
    
    def _execute_action(
        self, 
        symbol: str, 
        action: Action, 
        prices: Dict[str, float]
    ) -> None:
        """Execute a trading action for a symbol"""
        price = prices.get(symbol, 0)
        if price <= 0:
            return
        
        current_shares = self.portfolio.positions.get(symbol, 0)
        portfolio_value = self.portfolio.get_value(prices)
        
        if action == Action.BUY and self.portfolio.cash > 0:
            # Calculate position size (max 20% of portfolio)
            max_position_value = portfolio_value * self.max_position_pct
            current_position_value = current_shares * price
            available_to_buy = max_position_value - current_position_value
            
            if available_to_buy > 0:
                # Apply slippage (buy at higher price)
                buy_price = price * (1 + self.slippage)
                
                # Calculate shares to buy
                shares_to_buy = min(
                    available_to_buy / buy_price,
                    self.portfolio.cash / buy_price
                )
                shares_to_buy = int(shares_to_buy)
                
                if shares_to_buy > 0:
                    cost = shares_to_buy * buy_price
                    transaction_fee = cost * self.transaction_cost
                    total_cost = cost + transaction_fee
                    
                    if total_cost <= self.portfolio.cash:
                        # Update portfolio
                        self.portfolio.cash -= total_cost
                        
                        # Update average entry price
                        old_shares = self.portfolio.positions[symbol]
                        old_avg = self.portfolio.entry_prices.get(symbol, 0)
                        new_shares = old_shares + shares_to_buy
                        
                        if new_shares > 0:
                            new_avg = (
                                (old_shares * old_avg + shares_to_buy * buy_price) 
                                / new_shares
                            )
                            self.portfolio.entry_prices[symbol] = new_avg
                        
                        self.portfolio.positions[symbol] = new_shares
                        
                        # Log trade
                        self.episode_trades.append({
                            "step": self.current_step,
                            "symbol": symbol,
                            "action": "BUY",
                            "shares": shares_to_buy,
                            "price": buy_price,
                            "cost": total_cost,
                        })
        
        elif action == Action.SELL and current_shares > 0:
            # Sell all shares
            sell_price = price * (1 - self.slippage)  # Slippage
            proceeds = current_shares * sell_price
            transaction_fee = proceeds * self.transaction_cost
            net_proceeds = proceeds - transaction_fee
            
            self.portfolio.cash += net_proceeds
            self.portfolio.positions[symbol] = 0
            self.portfolio.entry_prices[symbol] = 0
            
            # Log trade
            self.episode_trades.append({
                "step": self.current_step,
                "symbol": symbol,
                "action": "SELL",
                "shares": current_shares,
                "price": sell_price,
                "proceeds": net_proceeds,
            })
    
    def _get_observation(self) -> np.ndarray:
        """Build observation array from current state"""
        if self.current_step >= len(self.market_data):
            return np.zeros(self.obs_size, dtype=np.float32)
        
        current_state = self.market_data[self.current_step]
        prices = current_state.prices
        
        # Market features
        market_features = current_state.to_array(self.symbols)
        
        # Portfolio features
        portfolio_value = self.portfolio.get_value(prices)
        cash_ratio = self.portfolio.cash / portfolio_value if portfolio_value > 0 else 1.0
        value_pct = portfolio_value / self.initial_cash
        
        # Position ratios per asset
        position_ratios = []
        for symbol in self.symbols:
            pos_value = self.portfolio.get_position_value(symbol, prices.get(symbol, 0))
            pos_ratio = pos_value / portfolio_value if portfolio_value > 0 else 0
            position_ratios.append(pos_ratio)
        
        portfolio_features = np.array(
            [cash_ratio, value_pct] + position_ratios,
            dtype=np.float32
        )
        
        # Combine all features
        obs = np.concatenate([market_features, portfolio_features])
        
        return obs
    
    def _calculate_risk_penalty(self) -> float:
        """Calculate risk-adjusted penalty based on portfolio volatility"""
        if len(self.episode_rewards) < 5:
            return 0.0
        
        recent_rewards = self.episode_rewards[-20:]
        volatility = np.std(recent_rewards) if len(recent_rewards) > 1 else 0
        
        # Penalize high volatility
        return volatility * 0.1
    
    def get_episode_stats(self) -> Dict[str, Any]:
        """Get statistics for the current episode"""
        if not self.market_data or self.portfolio is None:
            return {}
        
        final_prices = self.market_data[min(self.current_step, len(self.market_data) - 1)].prices
        final_value = self.portfolio.get_value(final_prices)
        
        total_return = (final_value - self.initial_cash) / self.initial_cash
        
        # Calculate Sharpe-like metric
        if self.episode_rewards:
            avg_reward = np.mean(self.episode_rewards)
            std_reward = np.std(self.episode_rewards) if len(self.episode_rewards) > 1 else 1
            sharpe = avg_reward / std_reward if std_reward > 0 else 0
        else:
            sharpe = 0
        
        # Trade statistics
        buy_trades = [t for t in self.episode_trades if t["action"] == "BUY"]
        sell_trades = [t for t in self.episode_trades if t["action"] == "SELL"]
        
        return {
            "final_value": final_value,
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "sharpe_ratio": sharpe,
            "n_steps": self.current_step,
            "n_trades": len(self.episode_trades),
            "n_buys": len(buy_trades),
            "n_sells": len(sell_trades),
            "avg_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0,
        }
    
    def render(self, mode: str = "human") -> Optional[str]:
        """Render current state"""
        if self.portfolio is None or not self.market_data:
            return None
        
        current_state = self.market_data[min(self.current_step, len(self.market_data) - 1)]
        prices = current_state.prices
        value = self.portfolio.get_value(prices)
        
        output = [
            f"\n{'='*60}",
            f"Step: {self.current_step}/{len(self.market_data)}",
            f"Portfolio Value: ${value:,.2f}",
            f"Cash: ${self.portfolio.cash:,.2f}",
            f"Positions:"
        ]
        
        for symbol in self.symbols:
            shares = self.portfolio.positions.get(symbol, 0)
            if shares > 0:
                pos_value = shares * prices.get(symbol, 0)
                entry = self.portfolio.entry_prices.get(symbol, 0)
                pnl = shares * (prices.get(symbol, 0) - entry)
                output.append(f"  {symbol}: {shares} shares @ ${entry:.2f} "
                            f"(Value: ${pos_value:.2f}, P&L: ${pnl:.2f})")
        
        output.append(f"Total Trades: {len(self.episode_trades)}")
        output.append(f"{'='*60}")
        
        result = "\n".join(output)
        if mode == "human":
            print(result)
        return result
    
    def close(self) -> None:
        """Clean up environment"""
        pass


def generate_synthetic_data(
    symbols: List[str],
    n_steps: int = 252,
    seed: Optional[int] = None
) -> List[MarketState]:
    """
    Generate synthetic market data for testing.
    
    Args:
        symbols: List of stock symbols
        n_steps: Number of time steps to generate
        seed: Random seed
        
    Returns:
        List of MarketState objects
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Initial prices
    prices = {s: np.random.uniform(50, 200) for s in symbols}
    
    data = []
    base_time = datetime(2025, 1, 1)
    
    for step in range(n_steps):
        # Simulate price movement (geometric Brownian motion)
        for symbol in symbols:
            drift = 0.0002  # Small positive drift
            volatility = np.random.uniform(0.01, 0.03)
            shock = np.random.normal(0, volatility)
            prices[symbol] *= (1 + drift + shock)
            prices[symbol] = max(prices[symbol], 1.0)  # Floor at $1
        
        # Generate market state
        state = MarketState(
            timestamp=base_time.replace(day=1 + step % 28, month=1 + step // 28 % 12),
            prices=dict(prices),
            volumes={s: np.random.uniform(1e6, 10e6) for s in symbols},
            rsi={s: np.random.uniform(30, 70) for s in symbols},
            macd={s: np.random.uniform(-2, 2) for s in symbols},
            bollinger_position={s: np.random.uniform(-1, 1) for s in symbols},
            sentiment_scores={s: np.random.uniform(-0.5, 0.5) for s in symbols},
            social_sentiment={s: np.random.uniform(-0.5, 0.5) for s in symbols},
            news_sentiment={s: np.random.uniform(-0.5, 0.5) for s in symbols},
            volatility={s: np.random.uniform(0.01, 0.05) for s in symbols},
            beta={s: np.random.uniform(0.8, 1.5) for s in symbols},
        )
        data.append(state)
    
    return data


# Demo / Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("HERMES Quantum - Trading Environment Demo")
    print("=" * 60)
    
    # Create environment
    symbols = ["IONQ", "RGTI", "QUBT", "QBTS"]
    env = TradingEnvironment(
        symbols=symbols,
        initial_cash=100_000,
        max_position_pct=0.25,
        transaction_cost=0.001,
    )
    
    print(f"\nEnvironment created:")
    print(f"  Symbols: {symbols}")
    print(f"  Observation space: {env.obs_size} features")
    print(f"  Action space: {len(symbols)} assets × 3 actions")
    
    # Generate synthetic data
    print("\nGenerating synthetic market data...")
    market_data = generate_synthetic_data(symbols, n_steps=100, seed=42)
    env.load_market_data(market_data)
    
    # Reset and run episode
    print("\nRunning episode with random actions...")
    obs, info = env.reset(seed=42)
    print(f"Initial observation shape: {obs.shape}")
    print(f"Initial portfolio value: ${info['portfolio_value']:,.2f}")
    
    total_reward = 0
    done = False
    step_count = 0
    
    while not done and step_count < 50:
        # Random action
        action = np.random.randint(0, 3, size=len(symbols))
        
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
        step_count += 1
        
        if step_count % 10 == 0:
            print(f"  Step {step_count}: Value=${info['portfolio_value']:,.2f}, "
                  f"Reward={reward:.4f}, Trades={info['n_trades']}")
    
    # Final statistics
    stats = env.get_episode_stats()
    print("\n" + "=" * 60)
    print("Episode Complete!")
    print("=" * 60)
    print(f"  Final Value: ${stats['final_value']:,.2f}")
    print(f"  Total Return: {stats['total_return_pct']:.2f}%")
    print(f"  Sharpe Ratio: {stats['sharpe_ratio']:.4f}")
    print(f"  Total Trades: {stats['n_trades']} ({stats['n_buys']} buys, {stats['n_sells']} sells)")
    print(f"  Average Reward: {stats['avg_reward']:.4f}")
    
    # Render final state
    env.render()
    
    print("\n✅ Trading Environment working correctly!")
