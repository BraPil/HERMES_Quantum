# Repository Evaluation: Quantopian Zipline

## Basic Information
- **Repository**: quantopian/zipline
- **GitHub URL**: https://github.com/quantopian/zipline
- **Stars**: ⭐ 17,600+
- **Forks**: 🔱 4,700+
- **Last Updated**: 2023 (Community forks active: zipline-reloaded)
- **Created**: 2012
- **License**: Apache 2.0 (✅ Compatible with HERMES)
- **Language**: Python 3.7+
- **Size**: ~20MB core

## Relevance to HERMES_Quantum
- **Primary Value**: Event-driven architecture, Pipeline API for factor computation, data abstraction patterns
- **Applicable Agents**: 
  - **01_orchestrator**: EventManager, scheduling patterns, lifecycle management
  - **11_analyst**: Portfolio tracking, performance metrics
  - **22_psychology**: Factor pipeline patterns
  - **23_social**: Custom data source integration
  - **24_politics**: Event handling for news/policy data
  - **25_market**: Technical factor computation, data portal
  - **91_tools**: Data loaders, utility functions
  - **99_models**: Model integration via custom factors
- **Relevance Score**: 5/5 (Event-driven design is perfect for multi-agent orchestration)
- **Priority**: **HIGH** - Essential for understanding event-driven trading systems

## Technical Overview

### Purpose
Zipline is a Pythonic algorithmic trading library providing:
- Event-driven backtesting framework
- Pipeline API for computing alpha factors across securities
- Data abstraction layer (DataPortal) for multiple data sources
- Performance tracking and risk metrics
- Realistic trading simulation (slippage, commissions, splits)

### Key Features
- **Pipeline API**: Declarative factor computation across universe of assets
- **Event-Driven**: Clean separation of concerns (initialize, before_trading_start, handle_data)
- **Data Portal**: Unified interface for bars, adjustments, benchmarks
- **Trading Calendar**: International market support (US, CA, GB, etc.)
- **Realistic Simulation**: Models real-world trading constraints
- **Performance Analytics**: Sharpe, Sortino, drawdown, etc.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                TradingAlgorithm                         │
│  • initialize()      [Setup]                            │
│  • before_trading_start()  [Daily prep]                 │
│  • handle_data()     [Bar-by-bar execution]            │
│  • analyze()         [Post-simulation analysis]         │
└──────────────┬──────────────────────────┬───────────────┘
               │                          │
┌──────────────▼──────────────┐  ┌───────▼──────────────┐
│      Pipeline Engine        │  │    EventManager       │
│  (Factor Computation)       │  │  (Scheduling/Rules)   │
│  • Columns (Factors)        │  │  • date_rules         │
│  • Screen (Filter)          │  │  • time_rules         │
│  • Domain (Market)          │  │  • schedule_function  │
└──────────────┬──────────────┘  └───────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│                    Data Layer                            │
│  • DataPortal (unified data access)                      │
│  • EquityPricingLoader (bars)                            │
│  • AdjustmentReader (splits, dividends)                  │
│  • BenchmarkSource (market returns)                      │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack
- **Language**: Python 3.7+, Cython (performance-critical parts)
- **Frameworks**: 
  - NumPy/Pandas (data structures)
  - Bcolz (columnar storage)
  - trading-calendars (market calendars)
- **Dependencies**: 
  - empyrical (performance metrics)
  - pyfolio (portfolio analytics)
  - TA-Lib (technical analysis)
- **Database**: 
  - Bcolz (fast columnar storage for OHLCV data)
  - SQLite (asset metadata)
- **APIs**: 
  - Clean functional API
  - Context object pattern
  - Data abstraction via BarData

## Code Quality Assessment

### Documentation
- **README Quality**: Excellent - Comprehensive guide with examples
- **API Documentation**: Present - Full docs at zipline.io (archived)
- **Code Comments**: Comprehensive - Well-documented codebase
- **Examples**: Multiple - buy_and_hold, momentum_pipeline, dual moving average

### Code Organization
- **Structure**: Well-organized - Clear separation (finance/, pipeline/, data/)
- **Modularity**: Highly modular - Each component is independently testable
- **Naming**: Clear - Follows Python conventions, self-documenting
- **Patterns**: Follows best practices - Strategy, Template Method, Factory patterns

### Testing
- **Test Coverage**: High - Extensive test suite (thousands of tests)
- **Test Types**: Unit + Integration + System tests
- **CI/CD**: Automated - Travis CI (historical), GitHub Actions (forks)

### Maintenance Status
- **Activity Level**: Original repo stale, but **zipline-reloaded** is Very Active
- **Issue Response**: Community-driven (zipline-reloaded)
- **Community**: Large - Active forum, multiple maintained forks
- **Recent Changes**: zipline-reloaded adds Python 3.10 support, bug fixes

## Reusable Components

| Component | Description | Target Agent | Integration Effort | Value |
|-----------|-------------|--------------|-------------------|-------|
| EventManager | Schedule functions with rules | 01_orchestrator | Low | 5 |
| Pipeline API | Declarative factor computation | 22/23/24/25 | Medium | 5 |
| DataPortal | Unified data access abstraction | 91_tools | Medium | 5 |
| TradingAlgorithm lifecycle | Initialize/handle_data pattern | 01_orchestrator | Low | 5 |
| BarData | Current data access object | All agents | Low | 4 |
| Custom Factor | User-defined factors | 22/23/24/25 | Low | 5 |
| MetricsTracker | Performance tracking | 11_analyst | Medium | 4 |
| Blotter | Order management | 11_analyst | High | 3 |
| TradingCalendar | Multi-market calendar support | 91_tools | Low | 4 |
| AdjustmentReader | Handle splits/dividends | 25_market | Medium | 4 |

### Component Details

#### Component 1: EventManager
- **Location**: `zipline/utils/events.py`
- **Purpose**: Schedule functions to run at specific times (daily, weekly, intraday)
- **Dependencies**: trading_calendars
- **Integration Notes**: 
  - Supports date_rules (every_day, week_start, month_end)
  - Supports time_rules (market_open, market_close, custom times)
  - Composable rules with AND/OR/NOT logic
- **Adaptation Required**: 
  - Adapt for multi-agent coordination schedules
  - Add quantum stock-specific event types
  - Integrate with orchestrator workflow

#### Component 2: Pipeline API
- **Location**: `zipline/pipeline/`
- **Purpose**: Declarative framework for computing alpha factors across securities
- **Dependencies**: NumPy, Pandas, Bcolz
- **Integration Notes**:
  - Define factors as subclasses of Factor/Filter/Classifier
  - Automatic dependency resolution and computation order
  - Efficient windowed computations
  - Built-in factors: VWAP, RSI, Bollinger Bands, etc.
- **Adaptation Required**:
  - Create custom factors for sentiment, social, political data
  - Extend for multi-source data integration
  - Add quantum stock-specific factors

#### Component 3: DataPortal
- **Location**: `zipline/data/data_portal.py`
- **Purpose**: Unified interface for accessing historical and current data
- **Dependencies**: Asset database, bar readers
- **Integration Notes**:
  - Handles point-in-time data (prevents look-ahead bias)
  - Supports adjustments (splits, dividends)
  - Caches data for performance
- **Adaptation Required**:
  - Extend for alternative data sources (social, news)
  - Add quantum stock-specific data fields
  - Integrate with data_ingestion module

## Architecture Insights

### Design Patterns Observed

1. **Algorithm Lifecycle Pattern**
   - How it's used: initialize() → before_trading_start() → handle_data() → analyze()
   - Applicability to HERMES: Perfect template for agent lifecycle
   - Benefits: Clear phases, easy to understand, testable
   - Drawbacks: May be too rigid for complex agent interactions

2. **Context Object Pattern**
   - How it's used: `context` object passed to all lifecycle methods
   - Applicability to HERMES: Excellent for agent state management
   - Benefits: Encapsulation, no global state, easy to test
   - Drawbacks: Must manage context object carefully

3. **Event-Driven Architecture**
   - How it's used: EventManager with rules triggers callbacks
   - Applicability to HERMES: Core orchestrator pattern
   - Benefits: Decoupled, flexible scheduling, reactive
   - Drawbacks: Can be harder to trace execution flow

4. **Pipeline (Declarative Computation)**
   - How it's used: Define what to compute, engine handles when/how
   - Applicability to HERMES: Perfect for agent factor computation
   - Benefits: Automatic optimization, dependency resolution, caching
   - Drawbacks: Learning curve for declarative style

5. **Data Abstraction (Portal Pattern)**
   - How it's used: Single interface (DataPortal) for all data access
   - Applicability to HERMES: Essential for clean data layer
   - Benefits: Centralized, testable, swappable implementations
   - Drawbacks: Additional layer of abstraction

### What We Can Learn

- **Agent Coordination**: 
  - Use EventManager pattern for scheduling agent tasks
  - Implement before_trading_start equivalent for daily agent prep
  - Clear lifecycle: setup → daily_prep → continuous → teardown

- **Data Flow**: 
  - Adopt DataPortal pattern for unified data access
  - Implement point-in-time data to prevent look-ahead bias
  - Cache data strategically for performance

- **State Management**: 
  - Use context object for agent state
  - Separate algorithm state from data access
  - No global variables, everything via context

- **Error Handling**: 
  - Graceful handling of missing data (NaN)
  - Validation at API boundaries
  - Comprehensive logging with clear error messages

- **Scalability**: 
  - Pipeline API computes factors efficiently across many assets
  - Vectorized operations with NumPy
  - Lazy evaluation where possible

## Implementation Recommendations

### Immediate Adoption (Phase 1)
1. **Algorithm Lifecycle Pattern**: Structure orchestrator similarly
   ```python
   class HERMESOrchestrator:
       def initialize(self):  # One-time setup
       def before_trading_start(self):  # Daily prep (run pipelines)
       def handle_data(self):  # Bar-by-bar or continuous
       def analyze(self):  # Post-mortem analysis
   ```

2. **EventManager**: Implement scheduling for agents
   - Daily tasks: fetch data, compute factors
   - Intraday tasks: monitor prices, execute trades
   - Weekly tasks: retrain models, rebalance portfolio

3. **Context Object**: For agent state management
   ```python
   class AgentContext:
       def __init__(self):
           self.portfolio = Portfolio()
           self.models = {}
           self.signals = {}
           # Agent-specific state
   ```

### Medium-Term Adoption (Phase 2)
1. **Pipeline API**: For factor computation in agents 22-25
   - Create base Factor classes for each agent
   - Implement dependency resolution
   - Add caching and optimization

2. **DataPortal Pattern**: Unified data access
   - Single interface for all data sources
   - Point-in-time data guarantees
   - Efficient caching

3. **Custom Factors**: Extend for HERMES-specific factors
   - SentimentFactor (agent 22)
   - SocialMediaFactor (agent 23)  
   - PolicyNewsFactor (agent 24)
   - TechnicalFactor (agent 25)

### Long-Term Consideration (Phase 3+)
1. **Full Backtesting Framework**: Complete simulation
2. **Risk Analytics**: pyfolio integration
3. **Multi-Asset Support**: Beyond quantum stocks

## Specific Code References

### Event Scheduling Pattern
```python
# From zipline/algorithm.py
def schedule_function(self, func, date_rule, time_rule):
    # Brilliant pattern for orchestrating agent tasks
    self.event_manager.add_event(
        Event(ComposedRule(date_rule, time_rule), func)
    )
```

### Pipeline Computation
```python
# From zipline/pipeline/engine.py
class SimplePipelineEngine:
    def run_pipeline(self, pipeline, start_date, end_date):
        # 1. Build execution plan (topological sort)
        # 2. Load required data
        # 3. Compute terms in order
        # 4. Return DataFrame
        # This is what we need for multi-agent factor computation
```

### Data Access Pattern
```python
# From zipline/algorithm.py
def handle_data(self, context, data):
    # `data` is BarData object - clean interface
    price = data.current(asset, 'price')
    can_trade = data.can_trade(asset)
    history = data.history(asset, 'close', 20, '1d')
    # This abstraction is brilliant
```

## Integration Checklist

- [ ] Study EventManager → Design HERMES scheduling system
- [ ] Implement algorithm lifecycle → Structure orchestrator
- [ ] Adopt context object pattern → Agent state management
- [ ] Review Pipeline API → Design factor computation
- [ ] Study DataPortal → Implement unified data access
- [ ] Create custom factors → Agent-specific computations
- [ ] Test event scheduling → Verify orchestrator timing
- [ ] Implement BarData equivalent → Clean data interface
- [ ] Review trading calendar → Support market hours
- [ ] Study adjustment handling → Deal with corporate actions

## Risk Assessment

### Compatibility Risks
- **Risk**: Original Zipline development stopped
- **Mitigation**: Use zipline-reloaded fork (actively maintained)
- **Impact**: Low

### Complexity Risks  
- **Risk**: Pipeline API has learning curve
- **Mitigation**: Start with simple examples, build incrementally
- **Impact**: Medium (worth the investment)

### Dependency Risks
- **Risk**: Requires Bcolz, TA-Lib (C dependencies)
- **Mitigation**: Use pure Python alternatives where possible
- **Impact**: Low (Docker handles this)

### Integration Risks
- **Risk**: Zipline is full framework, may conflict with HERMES design
- **Mitigation**: Cherry-pick patterns, don't adopt wholesale
- **Impact**: Low (with careful selection)

## Comparison with Qlib

| Aspect | Qlib | Zipline | HERMES Preference |
|--------|------|---------|-------------------|
| Architecture | Layered (data/model/workflow) | Event-driven | **Both** (use both patterns) |
| Data Handling | DataHandler with processors | DataPortal | **Qlib** (more flexible) |
| Scheduling | OnlineManager | EventManager | **Zipline** (cleaner API) |
| Factor Computation | Custom per model | Pipeline API | **Zipline** (declarative) |
| Maintenance | Very Active | Active (fork) | **Qlib** (original) |
| Learning Curve | Steep | Moderate | **Zipline** (easier start) |
| ML Focus | Strong | Weak | **Qlib** |
| Event Handling | Adequate | Excellent | **Zipline** |

**Verdict**: Use **Zipline's event-driven patterns** + **Qlib's data/model management**

## Conclusion

**VERDICT: ADOPT (Event Architecture + Pipeline Patterns)**

Quantopian Zipline provides:
- ✅ Proven event-driven architecture for trading systems
- ✅ Excellent Pipeline API for factor computation
- ✅ Clean lifecycle pattern (initialize/before_trading_start/handle_data)
- ✅ Robust scheduling with EventManager
- ✅ Data abstraction via DataPortal
- ✅ Apache 2.0 license (fully compatible)

**Recommended Actions:**
1. **Immediate**: Structure orchestrator following Zipline lifecycle
2. **Phase 1**: Implement EventManager for agent scheduling
3. **Phase 2**: Adapt Pipeline API for factor computation
4. **Ongoing**: Study zipline-reloaded for updates

**Estimated Value**: **9/10** - Event-driven design is perfect for HERMES orchestration.

**Synergy with Qlib**: Zipline + Qlib complement each other perfectly:
- Use Zipline's **event system** for orchestration
- Use Qlib's **data handling** for ingestion
- Use Zipline's **Pipeline** for factor computation
- Use Qlib's **model management** for ML
- Use both for **online trading** workflow

---

**Evaluation Date**: 2025-12-28  
**Evaluator**: Phase 0 Research  
**Next Review**: After orchestrator design
