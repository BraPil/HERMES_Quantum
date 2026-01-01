"""
HERMES Quantum - RL Trading Agent

Deep Reinforcement Learning agent for trading decisions.
Supports PPO and A2C algorithms via stable-baselines3.

Author: HERMES Development Team
Version: 0.1.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from datetime import datetime
import logging
import json
import pickle

# Optional: stable-baselines3
try:
    from stable_baselines3 import PPO, A2C
    from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
    from stable_baselines3.common.vec_env import DummyVecEnv
    from stable_baselines3.common.monitor import Monitor
    SB3_AVAILABLE = True
except ImportError:
    PPO = None
    A2C = None
    SB3_AVAILABLE = False

# Handle both module and standalone imports
try:
    from .trading_env import TradingEnvironment, MarketState, generate_synthetic_data
except ImportError:
    from trading_env import TradingEnvironment, MarketState, generate_synthetic_data

logger = logging.getLogger(__name__)


@dataclass
class RLConfig:
    """Configuration for RL agent training"""
    
    # Algorithm selection
    algorithm: str = "PPO"  # "PPO" or "A2C"
    
    # Network architecture
    policy: str = "MlpPolicy"
    hidden_layers: List[int] = field(default_factory=lambda: [256, 256])
    
    # Training hyperparameters
    learning_rate: float = 3e-4
    n_steps: int = 2048  # Steps per update
    batch_size: int = 64
    n_epochs: int = 10  # PPO epochs per update
    gamma: float = 0.99  # Discount factor
    gae_lambda: float = 0.95  # GAE lambda
    clip_range: float = 0.2  # PPO clip range
    ent_coef: float = 0.01  # Entropy coefficient
    vf_coef: float = 0.5  # Value function coefficient
    max_grad_norm: float = 0.5
    
    # Training schedule
    total_timesteps: int = 100_000
    eval_freq: int = 5000
    n_eval_episodes: int = 5
    
    # Logging
    verbose: int = 1
    log_interval: int = 100
    
    # Saving
    save_freq: int = 10_000
    model_dir: str = "outputs/models/rl"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "algorithm": self.algorithm,
            "policy": self.policy,
            "hidden_layers": self.hidden_layers,
            "learning_rate": self.learning_rate,
            "n_steps": self.n_steps,
            "batch_size": self.batch_size,
            "n_epochs": self.n_epochs,
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "clip_range": self.clip_range,
            "ent_coef": self.ent_coef,
            "vf_coef": self.vf_coef,
            "max_grad_norm": self.max_grad_norm,
            "total_timesteps": self.total_timesteps,
        }


class TradingCallback(BaseCallback if SB3_AVAILABLE else object):
    """
    Custom callback for tracking trading performance during training.
    """
    
    def __init__(
        self,
        eval_env: Optional[TradingEnvironment] = None,
        eval_freq: int = 5000,
        log_dir: Optional[str] = None,
        verbose: int = 1,
    ):
        if SB3_AVAILABLE:
            super().__init__(verbose)
        self.eval_env = eval_env
        self.eval_freq = eval_freq
        self.log_dir = Path(log_dir) if log_dir else None
        
        # Tracking
        self.episode_returns: List[float] = []
        self.episode_lengths: List[int] = []
        self.best_return = -np.inf
        self.training_history: List[Dict] = []
    
    def _on_step(self) -> bool:
        """Called at each step"""
        # Log episode info if available
        if len(self.model.ep_info_buffer) > 0:
            for info in self.model.ep_info_buffer:
                if 'r' in info:
                    self.episode_returns.append(info['r'])
                if 'l' in info:
                    self.episode_lengths.append(info['l'])
        
        # Periodic evaluation
        if self.n_calls % self.eval_freq == 0 and self.eval_env is not None:
            self._evaluate()
        
        return True
    
    def _evaluate(self) -> Dict:
        """Run evaluation episode"""
        obs, info = self.eval_env.reset()
        total_reward = 0
        done = False
        
        while not done:
            action, _ = self.model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = self.eval_env.step(action)
            total_reward += reward
            done = terminated or truncated
        
        stats = self.eval_env.get_episode_stats()
        
        # Log
        self.training_history.append({
            "timestep": self.n_calls,
            "eval_return": stats.get("total_return_pct", 0),
            "eval_sharpe": stats.get("sharpe_ratio", 0),
            "eval_trades": stats.get("n_trades", 0),
        })
        
        if self.verbose >= 1:
            logger.info(f"Eval @ {self.n_calls}: Return={stats.get('total_return_pct', 0):.2f}%, "
                       f"Sharpe={stats.get('sharpe_ratio', 0):.4f}")
        
        # Track best
        if stats.get("total_return_pct", 0) > self.best_return:
            self.best_return = stats.get("total_return_pct", 0)
            if self.verbose >= 1:
                logger.info(f"New best return: {self.best_return:.2f}%")
        
        return stats
    
    def _on_training_end(self) -> None:
        """Called at end of training"""
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Save training history
            history_path = self.log_dir / "training_history.json"
            with open(history_path, 'w') as f:
                json.dump(self.training_history, f, indent=2)
            
            logger.info(f"Training history saved to {history_path}")


class RLTradingAgent:
    """
    Reinforcement Learning agent for trading.
    
    Features:
    - PPO and A2C algorithm support
    - Custom trading environment integration
    - Model saving/loading
    - Training with callbacks
    - Inference for live trading
    """
    
    def __init__(
        self,
        env: TradingEnvironment,
        config: Optional[RLConfig] = None,
    ):
        """
        Initialize RL agent.
        
        Args:
            env: Trading environment
            config: Training configuration
        """
        self.env = env
        self.config = config or RLConfig()
        self.model = None
        self.is_trained = False
        
        # Create model directory
        self.model_dir = Path(self.config.model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Training history
        self.training_history: List[Dict] = []
        
        if not SB3_AVAILABLE:
            logger.warning("stable-baselines3 not available. Training disabled.")
        
        logger.info(f"RLTradingAgent initialized with {self.config.algorithm}")
    
    def _create_model(self, env) -> Any:
        """Create the RL model based on config"""
        if not SB3_AVAILABLE:
            raise RuntimeError("stable-baselines3 not installed")
        
        # Policy kwargs for custom architecture
        policy_kwargs = {
            "net_arch": self.config.hidden_layers,
        }
        
        if self.config.algorithm == "PPO":
            model = PPO(
                policy=self.config.policy,
                env=env,
                learning_rate=self.config.learning_rate,
                n_steps=self.config.n_steps,
                batch_size=self.config.batch_size,
                n_epochs=self.config.n_epochs,
                gamma=self.config.gamma,
                gae_lambda=self.config.gae_lambda,
                clip_range=self.config.clip_range,
                ent_coef=self.config.ent_coef,
                vf_coef=self.config.vf_coef,
                max_grad_norm=self.config.max_grad_norm,
                policy_kwargs=policy_kwargs,
                verbose=self.config.verbose,
            )
        elif self.config.algorithm == "A2C":
            model = A2C(
                policy=self.config.policy,
                env=env,
                learning_rate=self.config.learning_rate,
                n_steps=self.config.n_steps,
                gamma=self.config.gamma,
                gae_lambda=self.config.gae_lambda,
                ent_coef=self.config.ent_coef,
                vf_coef=self.config.vf_coef,
                max_grad_norm=self.config.max_grad_norm,
                policy_kwargs=policy_kwargs,
                verbose=self.config.verbose,
            )
        else:
            raise ValueError(f"Unknown algorithm: {self.config.algorithm}")
        
        return model
    
    def train(
        self,
        market_data: List[MarketState],
        eval_data: Optional[List[MarketState]] = None,
        callbacks: Optional[List] = None,
    ) -> Dict[str, Any]:
        """
        Train the RL agent.
        
        Args:
            market_data: Training market data
            eval_data: Optional evaluation data
            callbacks: Optional list of callbacks
            
        Returns:
            Training results dictionary
        """
        if not SB3_AVAILABLE:
            logger.error("stable-baselines3 not installed. Cannot train.")
            return {"error": "stable-baselines3 not installed"}
        
        logger.info(f"Starting training: {self.config.total_timesteps} timesteps")
        start_time = datetime.now()
        
        # Load data into environment
        self.env.load_market_data(market_data)
        
        # Wrap environment
        def make_env():
            return self.env
        
        vec_env = DummyVecEnv([make_env])
        
        # Create model
        self.model = self._create_model(vec_env)
        
        # Set up evaluation environment
        eval_env = None
        if eval_data:
            eval_env = TradingEnvironment(
                symbols=self.env.symbols,
                initial_cash=self.env.initial_cash,
                max_position_pct=self.env.max_position_pct,
            )
            eval_env.load_market_data(eval_data)
        
        # Create callbacks
        all_callbacks = callbacks or []
        
        trading_callback = TradingCallback(
            eval_env=eval_env,
            eval_freq=self.config.eval_freq,
            log_dir=str(self.model_dir / "logs"),
            verbose=self.config.verbose,
        )
        all_callbacks.append(trading_callback)
        
        # Train
        try:
            self.model.learn(
                total_timesteps=self.config.total_timesteps,
                callback=all_callbacks,
                log_interval=self.config.log_interval,
            )
            self.is_trained = True
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"error": str(e)}
        
        # Collect results
        duration = (datetime.now() - start_time).total_seconds()
        
        results = {
            "algorithm": self.config.algorithm,
            "total_timesteps": self.config.total_timesteps,
            "training_duration_seconds": duration,
            "training_history": trading_callback.training_history,
            "best_return": trading_callback.best_return,
            "n_episodes": len(trading_callback.episode_returns),
            "avg_episode_return": np.mean(trading_callback.episode_returns) if trading_callback.episode_returns else 0,
        }
        
        logger.info(f"Training complete in {duration:.1f}s")
        logger.info(f"Best evaluation return: {trading_callback.best_return:.2f}%")
        
        return results
    
    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> np.ndarray:
        """
        Get action for observation.
        
        Args:
            observation: Environment observation
            deterministic: Use deterministic policy
            
        Returns:
            Action array
        """
        if self.model is None:
            # Return random action if no model
            return np.random.randint(0, 3, size=self.env.n_assets)
        
        action, _ = self.model.predict(observation, deterministic=deterministic)
        return action
    
    def evaluate(
        self,
        market_data: List[MarketState],
        n_episodes: int = 10,
    ) -> Dict[str, Any]:
        """
        Evaluate agent on test data.
        
        Args:
            market_data: Test market data
            n_episodes: Number of evaluation episodes
            
        Returns:
            Evaluation results
        """
        logger.info(f"Evaluating agent for {n_episodes} episodes")
        
        self.env.load_market_data(market_data)
        
        results = []
        for ep in range(n_episodes):
            obs, info = self.env.reset(seed=ep)
            total_reward = 0
            done = False
            
            while not done:
                action = self.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = self.env.step(action)
                total_reward += reward
                done = terminated or truncated
            
            stats = self.env.get_episode_stats()
            results.append(stats)
        
        # Aggregate results
        avg_return = np.mean([r["total_return_pct"] for r in results])
        avg_sharpe = np.mean([r["sharpe_ratio"] for r in results])
        avg_trades = np.mean([r["n_trades"] for r in results])
        
        summary = {
            "n_episodes": n_episodes,
            "avg_return_pct": avg_return,
            "std_return_pct": np.std([r["total_return_pct"] for r in results]),
            "avg_sharpe_ratio": avg_sharpe,
            "avg_trades": avg_trades,
            "min_return_pct": min([r["total_return_pct"] for r in results]),
            "max_return_pct": max([r["total_return_pct"] for r in results]),
            "episodes": results,
        }
        
        logger.info(f"Evaluation: Avg Return={avg_return:.2f}%, Avg Sharpe={avg_sharpe:.4f}")
        
        return summary
    
    def save(self, path: Optional[str] = None) -> str:
        """
        Save the model.
        
        Args:
            path: Save path (optional)
            
        Returns:
            Path where model was saved
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(self.model_dir / f"rl_agent_{self.config.algorithm}_{timestamp}")
        
        # Save model
        self.model.save(path)
        
        # Save config
        config_path = f"{path}_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        logger.info(f"Model saved to {path}")
        return path
    
    def load(self, path: str) -> None:
        """
        Load a saved model.
        
        Args:
            path: Model path
        """
        if not SB3_AVAILABLE:
            raise RuntimeError("stable-baselines3 not installed")
        
        # Determine algorithm from path or config
        if self.config.algorithm == "PPO":
            self.model = PPO.load(path)
        elif self.config.algorithm == "A2C":
            self.model = A2C.load(path)
        else:
            # Try to load config
            config_path = f"{path}_config.json"
            if Path(config_path).exists():
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                if config_dict.get("algorithm") == "PPO":
                    self.model = PPO.load(path)
                else:
                    self.model = A2C.load(path)
            else:
                # Default to PPO
                self.model = PPO.load(path)
        
        self.is_trained = True
        logger.info(f"Model loaded from {path}")
    
    def get_action_distribution(
        self,
        observation: np.ndarray,
    ) -> Dict[str, np.ndarray]:
        """
        Get action probability distribution.
        
        Args:
            observation: Environment observation
            
        Returns:
            Dictionary with action probabilities per asset
        """
        if self.model is None:
            # Return uniform distribution
            return {
                symbol: np.array([0.33, 0.33, 0.34])
                for symbol in self.env.symbols
            }
        
        # Get policy distribution
        obs_tensor = self.model.policy.obs_to_tensor(observation.reshape(1, -1))[0]
        
        with self.model.policy.no_grad():
            distribution = self.model.policy.get_distribution(obs_tensor)
            probs = distribution.distribution.probs.cpu().numpy()[0]
        
        # Map to symbols (assuming multi-discrete action space)
        result = {}
        for i, symbol in enumerate(self.env.symbols):
            if i < len(probs):
                result[symbol] = probs[i] if len(probs.shape) > 1 else probs
            else:
                result[symbol] = np.array([0.33, 0.33, 0.34])
        
        return result


class SimpleRLAgent:
    """
    Simple RL agent without stable-baselines3 dependency.
    Uses basic Q-learning for demonstration purposes.
    """
    
    def __init__(
        self,
        env: TradingEnvironment,
        learning_rate: float = 0.1,
        discount_factor: float = 0.99,
        epsilon: float = 0.1,
    ):
        """
        Initialize simple RL agent.
        
        Args:
            env: Trading environment
            learning_rate: Learning rate
            discount_factor: Discount factor (gamma)
            epsilon: Exploration rate
        """
        self.env = env
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        
        # Simple state discretization
        self.n_actions = 3 ** env.n_assets
        
        # Q-table (simplified - uses hash of discretized state)
        self.q_table: Dict[str, np.ndarray] = {}
        
        logger.info("SimpleRLAgent initialized (Q-learning)")
    
    def _discretize_state(self, observation: np.ndarray) -> str:
        """Convert continuous observation to discrete state key"""
        # Simple discretization: bin each feature
        bins = np.digitize(observation, np.linspace(-2, 2, 10))
        return str(tuple(bins))
    
    def _get_q_values(self, state_key: str) -> np.ndarray:
        """Get Q-values for state"""
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.n_actions)
        return self.q_table[state_key]
    
    def _action_to_array(self, action_idx: int) -> np.ndarray:
        """Convert action index to array of per-asset actions"""
        actions = []
        remaining = action_idx
        for _ in range(self.env.n_assets):
            actions.append(remaining % 3)
            remaining //= 3
        return np.array(actions)
    
    def _array_to_action(self, action_array: np.ndarray) -> int:
        """Convert action array to index"""
        idx = 0
        for i, a in enumerate(action_array):
            idx += int(a) * (3 ** i)
        return idx
    
    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> np.ndarray:
        """Get action for observation"""
        state_key = self._discretize_state(observation)
        q_values = self._get_q_values(state_key)
        
        if not deterministic and np.random.random() < self.epsilon:
            # Explore
            action_idx = np.random.randint(self.n_actions)
        else:
            # Exploit
            action_idx = np.argmax(q_values)
        
        return self._action_to_array(action_idx)
    
    def train(
        self,
        market_data: List[MarketState],
        n_episodes: int = 100,
    ) -> Dict[str, Any]:
        """Train using Q-learning"""
        logger.info(f"Training SimpleRLAgent for {n_episodes} episodes")
        
        self.env.load_market_data(market_data)
        episode_returns = []
        
        for ep in range(n_episodes):
            obs, info = self.env.reset()
            total_reward = 0
            done = False
            
            while not done:
                state_key = self._discretize_state(obs)
                action = self.predict(obs, deterministic=False)
                action_idx = self._array_to_action(action)
                
                next_obs, reward, terminated, truncated, info = self.env.step(action)
                total_reward += reward
                done = terminated or truncated
                
                # Q-learning update
                next_state_key = self._discretize_state(next_obs)
                next_q = self._get_q_values(next_state_key)
                current_q = self._get_q_values(state_key)
                
                target = reward + self.gamma * np.max(next_q) * (not done)
                current_q[action_idx] += self.lr * (target - current_q[action_idx])
                
                obs = next_obs
            
            episode_returns.append(total_reward)
            
            if (ep + 1) % 10 == 0:
                avg_return = np.mean(episode_returns[-10:])
                logger.info(f"Episode {ep + 1}: Avg Return (last 10) = {avg_return:.2f}")
        
        return {
            "n_episodes": n_episodes,
            "avg_return": np.mean(episode_returns),
            "final_avg_return": np.mean(episode_returns[-10:]),
            "n_states_visited": len(self.q_table),
        }


# Demo
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("HERMES Quantum - RL Agent Demo")
    print("=" * 60)
    
    # Create environment
    symbols = ["IONQ", "RGTI", "QUBT", "QBTS"]
    env = TradingEnvironment(
        symbols=symbols,
        initial_cash=100_000,
        max_position_pct=0.25,
    )
    
    # Generate data
    print("\nGenerating synthetic market data...")
    train_data = generate_synthetic_data(symbols, n_steps=200, seed=42)
    eval_data = generate_synthetic_data(symbols, n_steps=50, seed=123)
    
    if SB3_AVAILABLE:
        print("\n✅ stable-baselines3 available - using PPO agent")
        
        # Create and train agent
        config = RLConfig(
            algorithm="PPO",
            total_timesteps=5000,  # Small for demo
            n_steps=256,
            batch_size=32,
            eval_freq=1000,
            verbose=1,
        )
        
        agent = RLTradingAgent(env, config)
        
        print("\nTraining PPO agent...")
        results = agent.train(train_data, eval_data)
        
        print("\n" + "-" * 40)
        print("Training Results:")
        print(f"  Duration: {results.get('training_duration_seconds', 0):.1f}s")
        print(f"  Best Return: {results.get('best_return', 0):.2f}%")
        print(f"  Episodes: {results.get('n_episodes', 0)}")
        
        # Evaluate
        print("\nEvaluating trained agent...")
        eval_results = agent.evaluate(eval_data, n_episodes=5)
        
        print("\nEvaluation Results:")
        print(f"  Avg Return: {eval_results['avg_return_pct']:.2f}%")
        print(f"  Avg Sharpe: {eval_results['avg_sharpe_ratio']:.4f}")
        print(f"  Avg Trades: {eval_results['avg_trades']:.1f}")
        
        # Save model
        save_path = agent.save()
        print(f"\nModel saved to: {save_path}")
        
    else:
        print("\n⚠️ stable-baselines3 not available - using SimpleRLAgent")
        
        # Use simple Q-learning agent
        agent = SimpleRLAgent(env, epsilon=0.2)
        
        print("\nTraining SimpleRLAgent...")
        results = agent.train(train_data, n_episodes=50)
        
        print("\nTraining Results:")
        print(f"  Episodes: {results['n_episodes']}")
        print(f"  Avg Return: {results['avg_return']:.2f}")
        print(f"  States Visited: {results['n_states_visited']}")
        
        # Test agent
        print("\nTesting trained agent...")
        env.load_market_data(eval_data)
        obs, info = env.reset()
        
        total_reward = 0
        done = False
        
        while not done:
            action = agent.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            done = terminated or truncated
        
        stats = env.get_episode_stats()
        print(f"  Final Value: ${stats['final_value']:,.2f}")
        print(f"  Return: {stats['total_return_pct']:.2f}%")
        print(f"  Trades: {stats['n_trades']}")
    
    print("\n✅ RL Agent demo complete!")
