# HERMES_Quantum

A multi-agent AI system for quantum computing stock analysis

## Overview

HERMES_Quantum is an intelligent, multi-agent system designed to analyze quantum computing stocks (QBTS, IONQ, RGTI, QUBT) using specialized AI agents that work together to provide comprehensive market insights.

## Key Features

- **Multi-Agent Architecture**: Specialized agents for different aspects of analysis
- **Quantum Computing Focus**: Specifically designed for quantum computing sector stocks
- **Comprehensive Analysis**: Combines technical, fundamental, sentiment, and market analysis
- **Scalable Design**: Modular architecture allows easy addition of new agents and data sources
- **Real-time Monitoring**: Continuous monitoring of market conditions and news

## Watchlist

The system monitors and analyzes the following quantum computing stocks:
- **QBTS** - D-Wave Quantum Inc.
- **IONQ** - IonQ Inc.
- **RGTI** - Rigetti Computing Inc.
- **QUBT** - Quantum Computing Inc.

## Architecture

### Agent System

The system consists of specialized agents:

1. **Orchestrator Agent (01)** - Coordinates all agents and manages workflow
2. **Analyst Agent (11)** - Performs fundamental and technical analysis
3. **Psychology Agent (22)** - Analyzes market psychology and sentiment
4. **Social Agent (23)** - Monitors social media and community discussions
5. **Politics Agent (24)** - Tracks regulations and political developments
6. **Market Agent (25)** - Analyzes broader market conditions
7. **Tools Agent (91)** - Provides utility functions and data fetching
8. **Optimizer Agent (92)** - Optimizes and fine-tunes all models continuously
9. **Models Agent (99)** - Manages ML models for predictions

### Directory Structure

```
HERMES_Quantum/
├── agents/              # Multi-agent system components
│   ├── 01_orchestrator/
│   ├── 11_analyst/
│   ├── 22_psychology/
│   ├── 23_social/
│   ├── 24_politics/
│   ├── 25_market/
│   ├── 91_tools/
│   ├── 92_optimizer/
│   └── 99_models/
├── tools/              # Utility functions and helpers
├── models/             # Machine learning models
├── library/            # Shared libraries and base classes
├── core/               # Core system functionality
├── config/             # Configuration files
│   └── watchlist.yaml  # Stock watchlist configuration
├── data_ingestion/     # Data collection and ETL
├── execution/          # Workflow execution and scheduling
├── research/           # Research notebooks and experiments
├── tests/              # Unit and integration tests
├── scripts/            # Utility scripts
├── docs/               # Documentation
├── outputs/            # Analysis results and reports
├── pyproject.toml      # Project configuration
└── requirements.txt    # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management

### Setup

1. Clone the repository:
```bash
git clone https://github.com/BraPil/HERMES_Quantum.git
cd HERMES_Quantum
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or using pip with pyproject.toml:
```bash
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

4. Verify installation:
```bash
python -m pytest tests/
```

## Usage

### Basic Analysis

```python
from agents.orchestrator import Orchestrator
from config import load_watchlist

# Load watchlist
watchlist = load_watchlist()

# Initialize orchestrator
orchestrator = Orchestrator()

# Run analysis
results = orchestrator.analyze(watchlist['stocks'])
```

### Command Line Interface

```bash
# Run analysis for all watchlist stocks
python scripts/run_analysis.py

# Run analysis for specific stocks
python scripts/run_analysis.py --stocks QBTS IONQ

# Generate report
python scripts/generate_report.py --date 2025-12-28
```

## Configuration

Edit `config/watchlist.yaml` to customize:
- Stock watchlist
- Data sources
- Analysis settings
- Agent coordination parameters
- Output preferences

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific tests
pytest tests/unit/test_analyst.py
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy .
```

### Adding New Agents

1. Create agent directory: `agents/XX_agentname/`
2. Add `__init__.py` with agent metadata
3. Implement agent functionality
4. Register with orchestrator
5. Add tests
6. Update documentation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Contact

For questions or support, please open an issue on GitHub.

## Acknowledgments

- Quantum computing companies for their innovations
- Open-source community for tools and libraries
- Financial data providers for market data access
