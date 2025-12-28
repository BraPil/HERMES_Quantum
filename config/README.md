# Configuration

This directory contains configuration files and settings management for the HERMES_Quantum system.

## Purpose

The config package provides:
- System configuration files
- Stock watchlist definitions
- API keys and credentials (via environment variables)
- Agent-specific settings
- Data source configurations

## Files

- `watchlist.yaml` - List of quantum computing stocks to analyze (QBTS, IONQ, RGTI, QUBT)
- `settings.yaml` - General system settings (to be created)
- `agents.yaml` - Agent-specific configurations (to be created)
- `data_sources.yaml` - Data source configurations (to be created)

## Environment Variables

Create a `.env` file in the root directory for sensitive configuration:

```
API_KEY_ALPHA_VANTAGE=your_key_here
API_KEY_TWITTER=your_key_here
DATABASE_URL=your_db_url_here
```

## Usage

```python
from config import load_watchlist, get_settings

watchlist = load_watchlist()
settings = get_settings()
```
