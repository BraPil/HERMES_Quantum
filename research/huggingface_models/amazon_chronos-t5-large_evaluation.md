# amazon/chronos-t5-large - Model Evaluation

**Evaluation Date**: 2025-12-28  
**Evaluator**: HERMES_Quantum Research Team  
**Phase**: 0 - Deep Learning from Open Sources  
**Model URL**: https://huggingface.co/amazon/chronos-t5-large

---

## Executive Summary

**DECISION**: ✅ **ADOPT**  
**Target Agent**: `25_market` (Market Intelligence & Time Series Agent)  
**Priority**: HIGH - Foundation model for time series forecasting

Amazon Chronos-T5-Large is a breakthrough pretrained time series forecasting model that treats time series as a "language" and uses T5 transformer architecture for probabilistic predictions. With 709M parameters and training on massive public + synthetic datasets, it achieves strong zero-shot performance on unseen data. This is Amazon's production-grade model with 7.1M downloads, Apache 2.0 license, and proven real-world usage in stock prediction platforms.

**Critical Discovery**: A newer version **amazon/chronos-2** (Chronos-Bolt) was released Nov 2024, offering 5% lower error, 250x faster inference, and 20x better memory efficiency. However, chronos-t5-large remains more widely adopted and better documented.

**Key Innovation**: First major foundation model to successfully apply language model pretraining to time series, enabling transfer learning across domains.

---

## Model Overview

### Basic Information
- **Model ID**: `amazon/chronos-t5-large`
- **Author**: Amazon (Amazon Science)
- **License**: Apache 2.0 (permissive, commercial use allowed)
- **Architecture**: T5 (Text-to-Text Transfer Transformer) adapted for time series
- **Parameters**: 709M (0.7B)
- **Task**: Time Series Forecasting
- **Library**: chronos-forecasting (custom package)
- **Last Updated**: November 21, 2025

### Popularity Metrics
- **Downloads**: 7.1M total
- **Monthly Downloads**: 315,167 (high production usage)
- **Likes**: 168
- **Spaces Using**: 10 (including stock prediction platforms)
- **Paper**: Published TMLR 2024, 47 upvotes, 5 discussion comments
- **Collection**: Part of "Chronos Models & Datasets" (16 items, 52 likes)

### Technical Specifications
- **Model Size**: 709M parameters (0.7B)
- **Tensor Type**: F32
- **Format**: Safetensors
- **Based On**: google/t5-efficient-large
- **Vocabulary**: 4096 tokens (vs 32128 in original T5)
- **Input**: Time series values (univariate or multivariate)
- **Output**: Probabilistic forecasts with uncertainty quantification

### Newer Version Available
⚠️ **Important**: amazon/chronos-2 (Chronos-Bolt⚡️) released Nov 27, 2024
- 5% lower forecasting error
- 250x faster inference
- 20x more memory efficient
- Available on Amazon SageMaker JumpStart

**Recommendation**: Evaluate chronos-t5-large first (more mature), consider chronos-2 for production optimization.

---

## Training Data & Methodology

### Training Corpus
**Massive multi-domain time series dataset**:
1. **Public Datasets**: Large collection of publicly available time series
   - Financial markets data
   - Economic indicators
   - Energy consumption
   - Traffic patterns
   - Weather data
   - And many more domains

2. **Synthetic Data**: Generated via Gaussian processes
   - Improves generalization to unseen patterns
   - Covers distribution gaps in public data
   - Enables robust zero-shot performance

**Total**: Exact size not disclosed, but described as "large corpus"

### Training Methodology: "Learning the Language of Time Series"

#### 1. Tokenization Process
```
Time Series → Scaling → Quantization → Token Sequence
```
- **Scaling**: Normalize time series values
- **Quantization**: Map to discrete vocabulary (4096 tokens)
- **Result**: Time series becomes "text" for language model

#### 2. Model Training
- **Architecture**: T5 encoder-decoder transformer
- **Loss Function**: Cross-entropy (same as language modeling)
- **Objective**: Predict next token given context
- **Training**: Autoregressive sequence modeling

#### 3. Inference Process
```
Context → Model → Sample Tokens → Dequantize → Numerical Forecasts
```
- **Autoregressive Sampling**: Generate future tokens step-by-step
- **Multiple Trajectories**: Sample many futures for uncertainty
- **Probabilistic Output**: Full predictive distribution

### Key Innovation
**Treats time series forecasting as a translation task**: Past → Future, leveraging transformer's sequence-to-sequence capabilities.

---

## Model Capabilities

### Strengths

#### 1. Zero-Shot Forecasting
- **Cross-Domain Transfer**: Learns from diverse time series
- **No Fine-tuning Required**: Works on unseen data immediately
- **Generalization**: Synthetic data training improves robustness
- **Domain Agnostic**: Can forecast financial, weather, energy, traffic, etc.

#### 2. Probabilistic Forecasts
- **Uncertainty Quantification**: Provides prediction intervals
- **Multiple Scenarios**: Samples different future trajectories
- **Risk Assessment**: Quantiles (10%, 50%, 90%) for decision-making
- **Confidence Estimation**: Know when model is uncertain

#### 3. Foundation Model Benefits
- **Transfer Learning**: Leverages knowledge from thousands of time series
- **Scale Advantages**: 709M parameters capture complex patterns
- **Pretrained**: No need for large-scale training infrastructure
- **Continuously Improved**: Amazon actively maintains and updates

#### 4. Production-Ready
- **Apache 2.0 License**: No restrictions for commercial use
- **7.1M Downloads**: Heavily battle-tested
- **SageMaker Integration**: One-click deployment (Feb 2025 update)
- **Active Community**: 168 likes, 10 Spaces, active discussions

### Limitations

#### 1. Resource Requirements
- **Model Size**: 709M parameters = ~2.8GB memory (F32)
- **Inference Speed**: Slower than specialized models (but Chronos-Bolt⚡️ fixes this)
- **GPU Recommended**: CPU inference possible but slow
- **Memory**: Needs sufficient RAM/VRAM for large model

#### 2. Custom Library Required
- **Not Standard Transformers**: Uses chronos-forecasting package
- **Installation**: Requires git clone from Amazon Science repo
- **Dependencies**: May conflict with other libraries
- **Documentation**: Less extensive than mainstream transformers

#### 3. Interpretability Challenges
- **Black Box**: Transformer internals are opaque
- **No Explainability**: Hard to understand why specific forecast
- **Feature Importance**: Cannot easily identify key drivers
- **Debugging**: Difficult to diagnose poor predictions

#### 4. Context Length Limits
- **Maximum Context**: Limited by T5 architecture (~512-1024 tokens)
- **Long History**: May need summarization for very long series
- **Frequency Agnostic**: Must manually handle different time scales

---

## Use Cases for HERMES_Quantum

### Primary Use Case: 25_market Agent Time Series Forecasting

#### Quantum Stock Price Prediction
```python
import pandas as pd
import torch
from chronos import ChronosPipeline

# Load model
pipeline = ChronosPipeline.from_pretrained(
    "amazon/chronos-t5-large",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
)

# Historical quantum stock prices
qbts_history = torch.tensor([...])  # Last 90 days of $QBTS prices
ionq_history = torch.tensor([...])  # Last 90 days of $IONQ prices

# Forecast next 30 days
prediction_length = 30

qbts_forecast = pipeline.predict(qbts_history, prediction_length)
ionq_forecast = pipeline.predict(ionq_history, prediction_length)

# Get prediction intervals
low_10, median, high_90 = np.quantile(qbts_forecast[0].numpy(), [0.1, 0.5, 0.9], axis=0)
```

#### Use Cases for Quantum Stocks

1. **Price Forecasting**
   - Predict $QBTS, $IONQ, $RGTI, $QUBT prices 1-30 days ahead
   - Generate probabilistic scenarios (bull/base/bear)
   - Confidence intervals for risk management

2. **Volatility Prediction**
   - Forecast price volatility (historical volatility series)
   - Identify periods of high uncertainty
   - Risk-adjusted position sizing

3. **Volume Forecasting**
   - Predict trading volume patterns
   - Identify liquidity windows
   - Detect unusual volume spikes

4. **Earnings Reaction Patterns**
   - Learn historical earnings reaction patterns
   - Forecast post-earnings price movements
   - Compare across quantum stocks

5. **Correlation Analysis**
   - Forecast correlation between quantum stocks
   - Sector rotation predictions
   - Portfolio diversification optimization

6. **Technical Indicators**
   - Forecast RSI, MACD, Bollinger Bands
   - Predict indicator crossovers
   - Time series of technical signals

### Secondary Use Cases

#### 1. Sentiment Time Series
```python
# Forecast sentiment trends
sentiment_history = torch.tensor([...])  # Daily sentiment scores
sentiment_forecast = pipeline.predict(sentiment_history, 7)
# "Will positive sentiment continue?"
```

#### 2. News Volume Prediction
```python
# Forecast news coverage
news_count_history = torch.tensor([...])  # Daily news article counts
news_forecast = pipeline.predict(news_count_history, 14)
# "Will quantum stocks get more media attention?"
```

#### 3. Social Media Mentions
```python
# Forecast Twitter/Reddit mention volume
mentions_history = torch.tensor([...])  # Daily $QBTS mentions
mentions_forecast = pipeline.predict(mentions_history, 7)
# "Is social buzz increasing?"
```

#### 4. Macro Indicators
```python
# Forecast relevant economic indicators
vix_history = torch.tensor([...])  # VIX (market fear index)
vix_forecast = pipeline.predict(vix_history, 30)
# "Will market volatility impact quantum stocks?"
```

### Integration Strategy

#### Phase 1: Core Price Forecasting
```python
# agents/25_market/forecasting_engine.py
from chronos import ChronosPipeline
import torch
import numpy as np

class MarketForecastingEngine:
    """Time series forecasting for 25_market agent"""
    
    def __init__(self):
        self.model = ChronosPipeline.from_pretrained(
            "amazon/chronos-t5-large",
            device_map="cuda",
            torch_dtype=torch.bfloat16,
        )
        self.tickers = ["QBTS", "IONQ", "RGTI", "QUBT"]
    
    def forecast_price(self, ticker: str, history: np.array, 
                      days_ahead: int = 30) -> dict:
        """Generate probabilistic price forecast"""
        context = torch.tensor(history)
        forecast = self.model.predict(context, days_ahead)
        
        # Extract quantiles
        quantiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
        forecast_quantiles = np.quantile(
            forecast[0].numpy(), 
            quantiles, 
            axis=0
        )
        
        return {
            'ticker': ticker,
            'horizon': days_ahead,
            'median_forecast': forecast_quantiles[3],  # 50th percentile
            'confidence_intervals': {
                '90%': (forecast_quantiles[0], forecast_quantiles[6]),
                '80%': (forecast_quantiles[1], forecast_quantiles[5]),
                '50%': (forecast_quantiles[2], forecast_quantiles[4]),
            },
            'all_trajectories': forecast[0].numpy()  # For scenario analysis
        }
    
    def detect_trend_change(self, ticker: str, history: np.array) -> dict:
        """Detect if trend is changing"""
        # Forecast short-term vs long-term
        short_forecast = self.forecast_price(ticker, history, days_ahead=7)
        long_forecast = self.forecast_price(ticker, history, days_ahead=30)
        
        # Compare slopes
        current_price = history[-1]
        short_change = (short_forecast['median_forecast'][-1] - current_price) / current_price
        long_change = (long_forecast['median_forecast'][-1] - current_price) / current_price
        
        return {
            'ticker': ticker,
            'short_term_trend': short_change,
            'long_term_trend': long_change,
            'trend_reversal': (short_change * long_change) < 0,  # Opposite signs
            'signal': 'bullish' if long_change > 0 else 'bearish'
        }
```

#### Phase 2: Multi-Variable Forecasting
```python
class AdvancedMarketForecaster:
    """Multi-variable forecasting with context"""
    
    def forecast_with_context(self, ticker: str, 
                              price_history: np.array,
                              volume_history: np.array,
                              sentiment_history: np.array) -> dict:
        """Forecast price considering volume and sentiment"""
        
        # Forecast each series independently
        price_forecast = self.model.predict(
            torch.tensor(price_history), 30
        )
        volume_forecast = self.model.predict(
            torch.tensor(volume_history), 30
        )
        sentiment_forecast = self.model.predict(
            torch.tensor(sentiment_history), 30
        )
        
        # Analyze joint probabilities
        scenarios = self.analyze_scenarios(
            price_forecast, volume_forecast, sentiment_forecast
        )
        
        return {
            'ticker': ticker,
            'price_scenarios': scenarios,
            'risk_assessment': self.assess_risk(scenarios),
            'recommended_action': self.generate_signal(scenarios)
        }
```

---

## Comparison with Other Models

### vs Traditional Time Series Models

| Feature | Chronos-T5-Large | ARIMA | Prophet | LSTM |
|---------|------------------|-------|---------|------|
| **Zero-Shot** | ✅ Excellent | ❌ No | ⚠️ Limited | ❌ No |
| **Uncertainty** | ✅ Full distribution | ⚠️ Point + CI | ⚠️ Point + CI | ⚠️ Limited |
| **Training Data** | Pretrained (millions) | Per-series | Per-series | Per-series |
| **Setup Time** | Instant | Fast | Fast | Slow (training) |
| **Adaptability** | High (cross-domain) | Low | Medium | Low |
| **Interpretability** | Low | High | Medium | Low |
| **Resource Needs** | High (GPU) | Low | Low | Medium |

### vs Other Foundation Models

**TimeGPT** (Nixtla):
- Similar concept (time series foundation model)
- Proprietary/closed-source
- API-based (pricing)
- Chronos advantage: Open-source, Apache 2.0

**Lag-Llama**:
- Open-source alternative
- Similar performance
- Less adoption (fewer downloads)
- Chronos advantage: Amazon backing, better documentation

### Why Chronos for HERMES_Quantum

1. **Zero-Shot Performance**: Works immediately on quantum stocks
2. **Probabilistic**: Provides uncertainty (critical for trading)
3. **Open Source**: Apache 2.0, no restrictions
4. **Proven**: 7.1M downloads, production usage
5. **Flexible**: Works for prices, volume, sentiment, any time series
6. **Scalable**: Pre-trained foundation model approach

---

## Model Card Analysis

### Documentation Quality
- ✅ **Excellent**: Clear README with mathematical details
- ✅ **Academic**: Published TMLR 2024 paper (peer-reviewed)
- ✅ **Code Examples**: Complete usage examples provided
- ✅ **Citation**: BibTeX available
- ✅ **GitHub**: Active repo with additional resources
- ✅ **Updates**: Regular updates (Chronos-Bolt announcement)
- ⚠️ **Custom Library**: Requires separate package installation

### Code Example (from Model Card)
```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from chronos import ChronosPipeline

pipeline = ChronosPipeline.from_pretrained(
    "amazon/chronos-t5-large",
    device_map="cuda",
    torch_dtype=torch.bfloat16,
)

# Load air passengers dataset
df = pd.read_csv(
    "https://raw.githubusercontent.com/AileenNielsen/TimeSeriesAnalysisWithPython/master/data/AirPassengers.csv"
)

# Prepare context
context = torch.tensor(df["#Passengers"])
prediction_length = 12

# Generate forecast
forecast = pipeline.predict(context, prediction_length)

# Visualize with uncertainty
forecast_index = range(len(df), len(df) + prediction_length)
low, median, high = np.quantile(forecast[0].numpy(), [0.1, 0.5, 0.9], axis=0)

plt.figure(figsize=(8, 4))
plt.plot(df["#Passengers"], color="royalblue", label="historical data")
plt.plot(forecast_index, median, color="tomato", label="median forecast")
plt.fill_between(
    forecast_index, low, high, 
    color="tomato", alpha=0.3, 
    label="80% prediction interval"
)
plt.legend()
plt.grid()
plt.show()
```

### Citation
```bibtex
@article{ansari2024chronos,
  title={Chronos: Learning the Language of Time Series},
  author={Ansari, Abdul Fatir and Stella, Lorenzo and Turkmen, Caner and 
          Zhang, Xiyuan and Mercado, Pedro and Shen, Huibin and 
          Shchur, Oleksandr and Rangapuram, Syama Syndar and 
          Pineda Arango, Sebastian and Kapoor, Shubham and 
          Zschiegner, Jasper and Maddix, Danielle C. and 
          Mahoney, Michael W. and Torkkola, Kari and 
          Gordon Wilson, Andrew and Bohlke-Schneider, Michael and 
          Wang, Yuyang},
  journal={Transactions on Machine Learning Research},
  issn={2835-8856},
  year={2024},
  url={https://openreview.net/forum?id=gerNCVqqtR}
}
```

---

## Integration Recommendations

### Implementation Priority: HIGH

#### Phase 1 (Immediate - Current)
- [x] Complete model evaluation
- [ ] Install chronos-forecasting package
- [ ] Test on quantum stock historical data ($QBTS, $IONQ, $RGTI, $QUBT)
- [ ] Validate forecasting accuracy on recent history
- [ ] Compare with baseline (simple moving average)
- [ ] Test GPU vs CPU performance

#### Phase 2 (Near-term)
- [ ] Integrate into 25_market agent architecture
- [ ] Build historical price database for context
- [ ] Implement probabilistic forecast pipeline
- [ ] Create visualization dashboard
- [ ] Set up forecast vs actuals tracking
- [ ] Develop forecast evaluation metrics

#### Phase 3 (Medium-term)
- [ ] Extend to volume, volatility forecasting
- [ ] Integrate with sentiment forecasts (from ProsusAI/FinTwitBERT)
- [ ] Build multi-variable scenario analysis
- [ ] Create trading signals from forecasts
- [ ] Implement risk management based on uncertainty
- [ ] Evaluate chronos-2 (Chronos-Bolt) for production optimization

#### Phase 4 (Long-term)
- [ ] Fine-tune on quantum stock specific patterns (if beneficial)
- [ ] Ensemble with traditional models (ARIMA, Prophet)
- [ ] Build forecast confidence calibration
- [ ] Develop automated backtesting framework
- [ ] Create forecast-driven trading strategies

### Technical Setup

#### Installation
```bash
# Install chronos-forecasting package
pip install git+https://github.com/amazon-science/chronos-forecasting.git

# Additional dependencies
pip install torch pandas matplotlib numpy
```

#### Configuration
```yaml
# config/models/chronos_t5_large.yaml
model:
  name: "amazon/chronos-t5-large"
  task: "time-series-forecasting"
  agent: "25_market"
  
inference:
  device: "cuda"  # or "cpu"
  dtype: "bfloat16"  # or "float32"
  
forecasting:
  default_horizon: 30  # days
  quantiles: [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
  num_samples: 100  # trajectories to sample
  
tickers:
  - "QBTS"
  - "IONQ"
  - "RGTI"
  - "QUBT"
  
context:
  min_history: 60  # minimum 60 days context
  max_history: 365  # maximum 1 year context
  
evaluation:
  backtest_days: 90
  metrics: ["MAE", "RMSE", "MAPE", "coverage_90%"]
```

---

## Risk Assessment

### Technical Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| Large model size (709M) | Medium | Use GPU, consider chronos-2 for optimization |
| Custom library dependency | Low | Pin version, maintain local fork if needed |
| Inference latency | Medium | Batch processing, consider chronos-bolt |
| Context length limits | Low | Summarize very long history if needed |

### Operational Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| GPU availability/cost | Medium | Hybrid CPU/GPU, SageMaker deployment option |
| Model staleness | Low | Amazon actively maintains, easy to update |
| Integration complexity | Low | Well-documented API, clear examples |
| Library conflicts | Low | Virtual environment, containerization |

### Strategic Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| Zero-shot may underperform | Medium | Validate on historical data, ensemble with traditional |
| Black box predictions | Medium | Track forecast accuracy, combine with explainable models |
| Overconfidence in forecasts | High | Always show uncertainty, risk management rules |
| Model drift | Low | Monitor forecast accuracy over time |

---

## Performance Expectations

### Benchmark Results (from paper)
**42-dataset comprehensive benchmark**:
- **In-domain**: Significantly outperforms baselines (datasets in training)
- **Zero-shot**: Comparable or superior to specialized models on new data
- **Consistent**: Strong performance across diverse domains

### Expected Performance for Quantum Stocks
- **Accuracy**: Moderate to good (financial markets are inherently noisy)
- **Uncertainty Calibration**: Good (probabilistic forecasts well-calibrated in paper)
- **Horizon**: Best for short-to-medium term (7-30 days)
- **Volatility**: Will capture but may lag extreme regime changes

### Resource Requirements
- **Memory**: ~3GB GPU RAM (bfloat16) or ~6GB (float32)
- **Inference Time**: ~1-5 seconds per forecast (GPU), ~10-30 seconds (CPU)
- **Disk Space**: ~1.5GB model weights
- **Context**: 512-1024 time steps (flexible)

---

## Decision Rationale

### Why ADOPT for 25_market Agent

#### ✅ Foundation Model Advantages
- **Zero-shot**: Works immediately on quantum stocks
- **Cross-domain knowledge**: Learns from diverse time series
- **No training needed**: Pretrained on massive data
- **Continuous improvement**: Amazon actively maintains

#### ✅ Production-Grade Quality
- 7.1M downloads (battle-tested)
- Apache 2.0 license (no restrictions)
- Active in stock prediction Spaces
- SageMaker integration for enterprise deployment

#### ✅ Probabilistic Forecasting
- Full uncertainty quantification
- Multiple scenario generation
- Risk-aware predictions
- Confidence intervals for decision-making

#### ✅ Strategic Fit
- Perfect for 25_market agent's forecasting needs
- Handles all time series (price, volume, sentiment, etc.)
- Complements sentiment models (ProsusAI, FinTwitBERT)
- Enables multi-modal analysis (prices + sentiment + volume)

#### ✅ Future-Proof
- Foundation model paradigm (cutting-edge)
- Newer version available (chronos-2) for optimization
- Active research community
- Peer-reviewed publication

### Comparison with Alternatives

**vs Training Custom LSTM**:
- Chronos: Zero-shot, no training, leverages cross-domain knowledge
- LSTM: Requires lots of data per stock, narrow expertise
- **Winner**: Chronos (faster, more robust)

**vs ARIMA/Prophet**:
- Chronos: Probabilistic, zero-shot, handles complex patterns
- ARIMA/Prophet: Fast, interpretable, simple patterns
- **Winner**: Chronos for primary, ARIMA/Prophet for ensemble

**vs TimeGPT**:
- Chronos: Open-source, Apache 2.0, self-hosted
- TimeGPT: Proprietary, API costs
- **Winner**: Chronos (cost, control, transparency)

### Implementation Plan
1. **Immediate**: Install and test on historical quantum stock data
2. **Near-term**: Integrate into 25_market agent, build forecast pipeline
3. **Medium-term**: Extend to multi-variable forecasting, combine with sentiment
4. **Long-term**: Optimize with chronos-2, ensemble with traditional models, deploy production strategies

---

## Conclusion

**DECISION**: ✅ **ADOPT** for 25_market agent

Amazon Chronos-T5-Large is a **strong ADOPT** for the HERMES_Quantum 25_market agent. It represents a paradigm shift in time series forecasting - leveraging foundation model pretraining to achieve robust zero-shot performance across domains. With 709M parameters trained on diverse time series, it brings cross-domain knowledge to quantum stock forecasting.

**Key Value Proposition**:
- Works immediately on $QBTS, $IONQ, $RGTI, $QUBT without training
- Provides probabilistic forecasts with uncertainty quantification
- Production-grade (7.1M downloads, Apache 2.0, SageMaker integration)
- Complements sentiment models for comprehensive market intelligence
- Future-proof with active Amazon maintenance and Chronos-2 upgrade path

**Next Steps**:
1. Install chronos-forecasting package
2. Test on 90-day quantum stock historical data
3. Validate forecast accuracy vs simple baselines
4. Create forecast visualization dashboard
5. Integrate into 25_market agent architecture
6. Combine with sentiment forecasts for trading signals
7. Evaluate Chronos-2 (Chronos-Bolt) for production optimization

**Confidence Level**: HIGH - This is the state-of-the-art open-source time series foundation model, backed by Amazon, with peer-reviewed research and proven production usage.

---

## Related Resources

### Model Resources
- **HuggingFace Model**: https://huggingface.co/amazon/chronos-t5-large
- **Paper (TMLR 2024)**: https://hf.co/papers/2403.07815
- **ArXiv**: https://arxiv.org/abs/2403.07815
- **GitHub Repository**: https://github.com/amazon-science/chronos-forecasting
- **SageMaker Tutorial**: https://github.com/amazon-science/chronos-forecasting/blob/main/notebooks/deploy-chronos-to-amazon-sagemaker.ipynb
- **Newer Version**: https://huggingface.co/amazon/chronos-2 (Chronos-Bolt⚡️)

### Model Family
- **chronos-t5-tiny** (8M params): Fast prototyping
- **chronos-t5-mini** (20M params): Lightweight deployment
- **chronos-t5-small** (46M params): Balanced
- **chronos-t5-base** (200M params): Good performance
- **chronos-t5-large** (710M params): Best accuracy ✅
- **chronos-bolt** (2024): Faster, more efficient version

### Production Examples
- **Stock Predictions**: https://hf.co/spaces/Agents-MCP-Hackathon/stock-predictions
- **Volatility Predictor**: https://hf.co/spaces/Gilette/volatilitypredictor
- **FEV-Bench**: https://hf.co/spaces/autogluon/fev-bench
- **TSF-EM**: https://hf.co/spaces/JavadBayazi/TSF-EM

### HERMES_Quantum Integration
- **Target Agent**: `agents/25_market/`
- **Configuration**: `config/models/chronos_t5_large.yaml` (to be created)
- **Testing**: `research/notebooks/test_chronos_quantum_stocks.ipynb` (to be created)
- **Integration**: `agents/25_market/forecasting_engine.py` (to be created)

---

**Evaluation Complete** | **Status**: ADOPT | **Agent**: 25_market | **Priority**: HIGH
