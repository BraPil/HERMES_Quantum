# Agent 92: Optimizer/Tuner

## Overview

Agent 92 is responsible for **continuous improvement** of all models used across the HERMES_Quantum system. While Agent 99 manages model deployment and versioning, Agent 92 ensures those models perform optimally through systematic optimization, validation, and fine-tuning.

## Core Responsibilities

### 1. Hyperparameter Optimization
- **Framework**: Optuna, Ray Tune, Hyperopt
- **Scope**: All models in agents 22-25
- **Method**: Bayesian optimization with early stopping
- **Output**: Optimal hyperparameters for each model

### 2. Cross-Validation
- **Time Series CV**: Walk-forward validation (no look-ahead bias)
- **Stratified CV**: For classification models with imbalanced classes
- **Custom CV**: Financial market-specific validation strategies
- **Output**: Robust performance estimates

### 3. Performance Monitoring
- **Drift Detection**: Alert when model accuracy degrades
- **Metric Tracking**: Track accuracy, F1, MAE, RMSE over time
- **Threshold Alerts**: Trigger retraining when thresholds breached
- **Output**: Performance dashboards and alerts

### 4. Model Fine-Tuning
- **Incremental Learning**: Update models with recent data
- **Domain Adaptation**: Specialize models for quantum stocks
- **Transfer Learning**: Leverage pre-trained models
- **Output**: Fine-tuned model checkpoints

### 5. AutoML Suggestions
- **Model Search**: Evaluate alternative architectures
- **Ensemble Methods**: Suggest model combinations
- **Cost-Benefit**: Balance accuracy vs inference speed
- **Output**: Recommendations for model improvements

## Agent Integration

### Agent 22 (Psychology - Sentiment Analysis)
**Current Model**: ProsusAI/finbert
- **92 monitors**: Sentiment accuracy on recent quantum stock news
- **92 tunes**: Learning rate, dropout, batch size
- **92 fine-tunes**: On manually labeled quantum stock news
- **92 suggests**: Consider DeBERTa-v3 for 2% gain (evaluate trade-offs)

### Agent 23 (Social Media)
**Current Model**: StephanAkkerman/FinTwitBERT-sentiment
- **92 monitors**: Tweet sentiment accuracy (especially on $QBTS, $IONQ, etc.)
- **92 tunes**: Model hyperparameters for social media text
- **92 fine-tunes**: On quantum computing community tweets
- **92 suggests**: Ensemble with base finbert for robustness

### Agent 24 (Politics)
**Current Model**: facebook/bart-large-mnli
- **Current Model**: facebook/bart-large-mnli
- **92 monitors**: Zero-shot classification accuracy on policy news
- **92 tunes**: Classification thresholds and label mappings
- **92 fine-tunes**: On quantum computing policy documents
- **92 suggests**: Add few-shot examples for better performance

### Agent 25 (Market - Forecasting)
**Current Model**: amazon/chronos-t5-large
- **92 monitors**: Forecast MAE/RMSE on quantum stock prices
- **92 tunes**: Context length, prediction horizon, temperature
- **92 fine-tunes**: On quantum stock price patterns
- **92 suggests**: Ensemble Chronos + statistical models (ARIMA, etc.)

### Agent 99 (Models Registry)
- **99 provides**: Model checkpoints, metadata, versions
- **92 evaluates**: Performance of each version
- **92 recommends**: Which version to deploy
- **99 deploys**: What 92 recommends

## Workflow

### Daily Monitoring
```
09:00 - Collect performance metrics from all agents
09:30 - Check for drift or degradation
10:00 - Generate daily performance report
```

### Weekly Optimization
```
Saturday - Run hyperparameter optimization on underperforming models
Sunday - Fine-tune models on previous week's data
```

### On-Demand Optimization
```
Triggered by:
- Agent 99 deployment of new model (validate before production)
- Agent 01 request (manual optimization trigger)
- Performance alert (accuracy drops below threshold)
```

## Key Technologies

### Optimization Frameworks
- **Optuna**: Hyperparameter optimization with pruning
- **Ray Tune**: Distributed tuning at scale
- **Hyperopt**: Tree-structured Parzen estimators

### Cross-Validation
- **scikit-learn**: Standard CV methods
- **mlfinlab**: Financial ML cross-validation
- **Custom**: Time series walk-forward validation

### Experiment Tracking
- **Weights & Biases**: Visual experiment tracking
- **MLflow**: Model versioning and metrics
- **Integration**: Shares data with Agent 99

### Fine-Tuning
- **HuggingFace Transformers**: Fine-tune NLP models
- **PyTorch Lightning**: Training optimization
- **PEFT/LoRA**: Parameter-efficient fine-tuning

## Module Structure

```
92_optimizer/
├── __init__.py                    # Agent metadata
├── README.md                      # This file
├── hyperparameter_tuner.py        # Optuna-based tuning
├── cross_validator.py             # Financial CV strategies
├── performance_monitor.py         # Drift detection & alerts
├── finetuner.py                   # Incremental learning
├── automl_suggester.py            # Alternative model evaluation
├── config/
│   ├── optimization_config.yaml   # Tuning parameters
│   └── thresholds.yaml            # Performance thresholds
├── notebooks/
│   ├── 01_agent22_optimization.ipynb
│   ├── 02_agent23_optimization.ipynb
│   ├── 03_agent25_optimization.ipynb
│   └── 04_drift_detection_demo.ipynb
└── tests/
    ├── test_tuner.py
    ├── test_validator.py
    └── test_monitor.py
```

## Example Usage

### Hyperparameter Tuning
```python
from agents.optimizer_92.hyperparameter_tuner import OptunaHyperTuner

# Tune finbert for agent 22
tuner = OptunaHyperTuner(
    model_name="ProsusAI/finbert",
    agent_id=22,
    n_trials=100
)

best_params = tuner.optimize(
    train_data=quantum_news_data,
    val_data=validation_data,
    metrics=["accuracy", "f1"]
)
```

### Performance Monitoring
```python
from agents.optimizer_92.performance_monitor import DriftDetector

# Monitor agent 22 sentiment model
monitor = DriftDetector(agent_id=22, model_name="finbert")

# Check daily performance
drift_detected = monitor.check_drift(
    recent_predictions=last_7_days_predictions,
    threshold=0.05  # 5% accuracy drop
)

if drift_detected:
    monitor.alert_orchestrator("Agent 22 sentiment accuracy dropped")
    monitor.trigger_retraining()
```

### Cross-Validation
```python
from agents.optimizer_92.cross_validator import TimeSeriesCV

# Validate agent 25 forecasting model
cv = TimeSeriesCV(
    model=chronos_model,
    n_splits=5,
    gap=1,  # 1-day gap to prevent look-ahead
    method="walk_forward"
)

scores = cv.validate(
    data=quantum_stock_prices,
    metrics=["mae", "rmse", "mape"]
)
```

### Fine-Tuning
```python
from agents.optimizer_92.finetuner import ModelFineTuner

# Fine-tune finbert on quantum stock news
finetuner = ModelFineTuner(
    base_model="ProsusAI/finbert",
    agent_id=22
)

finetuned_model = finetuner.train(
    train_data=labeled_quantum_news,
    epochs=3,
    learning_rate=2e-5,
    strategy="lora"  # Parameter-efficient
)

# A/B test before deployment
performance = finetuner.ab_test(
    model_a=current_finbert,
    model_b=finetuned_model,
    test_data=holdout_data
)
```

## Performance Metrics

### Agent 22 (Sentiment)
- Accuracy: Target >85%
- F1 Score: Target >0.83
- Response time: <500ms per article

### Agent 23 (Social)
- Accuracy: Target >80% (social text is noisy)
- F1 Score: Target >0.78
- Response time: <300ms per tweet

### Agent 24 (Politics)
- Zero-shot accuracy: Target >75%
- Recall: Target >0.80 (don't miss critical policy)
- Response time: <800ms per document

### Agent 25 (Forecasting)
- MAE: Target <$0.50 (daily price forecast)
- RMSE: Target <$0.75
- MAPE: Target <5%

## Optimization Schedule

### Immediate (Phase 1)
1. Set up performance monitoring for all models
2. Implement basic drift detection
3. Create optimization workflows

### Medium-term (Phase 2)
1. Hyperparameter tuning for all adopted models
2. Fine-tune on quantum computing domain data
3. Implement time series cross-validation

### Long-term (Phase 3)
1. AutoML model search and evaluation
2. Ensemble method optimization
3. Continuous learning pipeline

## Dependencies

```bash
# Core optimization
pip install optuna ray[tune] hyperopt

# Cross-validation
pip install scikit-learn mlfinlab

# Experiment tracking
pip install wandb mlflow

# Fine-tuning
pip install transformers[torch] pytorch-lightning peft

# AutoML (optional)
pip install autogluon
```

## Status

- **Phase**: 0 (Design & Documentation)
- **Priority**: HIGH (enables continuous improvement)
- **Dependencies**: Agent 99 (models), Agents 22-25 (consumers)
- **Next Steps**: 
  1. Implement performance monitoring
  2. Set up Optuna hyperparameter tuning
  3. Create cross-validation framework
  4. Integrate with Agent 99 registry

---

**Agent 92 Mission**: *Never settle for "good enough" - continuously optimize every model in the system for peak performance.*
