# Data Ingestion

This directory contains data collection, ETL processes, and data source integration for the HERMES_Quantum system.

## Purpose

The data_ingestion package provides:
- Data collection from various sources (financial APIs, news, social media)
- ETL (Extract, Transform, Load) pipelines
- Data cleaning and preprocessing
- Data storage and caching
- API rate limiting and retry logic

## Data Sources

- Financial market data (prices, volumes, fundamentals)
- News articles and press releases
- Social media posts and discussions
- Regulatory filings and government data
- Analyst reports and ratings

## Usage

```python
from data_ingestion import fetch_stock_data, fetch_news, fetch_social_media

stock_data = fetch_stock_data(symbols=["QBTS", "IONQ", "RGTI", "QUBT"])
news = fetch_news(topic="quantum computing")
social = fetch_social_media(keywords=["quantum", "IONQ"])
```

## Structure

- `financial_data.py` - Financial market data collection
- `news_data.py` - News article collection
- `social_data.py` - Social media data collection
- `etl_pipeline.py` - ETL orchestration
- `data_storage.py` - Data persistence layer
