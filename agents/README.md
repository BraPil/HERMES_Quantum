# Agents

This directory contains all specialized agents in the HERMES_Quantum system.

## Agent Structure

### 01_orchestrator
The orchestrator agent coordinates all other agents and manages the overall analysis workflow. It distributes tasks, aggregates results, and ensures coherent system operation.

### 11_analyst
The analyst agent performs fundamental and technical analysis of quantum computing stocks. It analyzes financial statements, market trends, and valuation metrics.

### 22_psychology
The psychology agent analyzes market psychology, investor sentiment, and behavioral patterns. It monitors fear/greed indicators and emotional drivers in the quantum computing sector.

### 23_social
The social agent monitors social media, forums, and online communities for quantum computing discussions. It analyzes sentiment, trending topics, and community engagement.

### 24_politics
The politics agent tracks political developments, regulations, and government policies affecting quantum computing. It monitors funding initiatives, export controls, and national security implications.

### 25_market
The market agent analyzes broader market conditions, sector trends, and competitive landscape. It monitors market indices, sector ETFs, and macroeconomic indicators.

### 91_tools
The tools agent provides utility functions and tools used by other agents. It includes data fetching, processing, and common helper functions.

### 99_models
The models agent manages machine learning models for predictions and classifications. It handles model training, inference, and performance monitoring.

## Agent Communication

Agents communicate through a message-passing system coordinated by the orchestrator. Each agent operates independently but can request information or services from other agents through the orchestrator.

## Adding New Agents

To add a new agent:
1. Create a new directory with a numeric prefix (e.g., `26_newagent`)
2. Add an `__init__.py` file with agent metadata
3. Implement the agent's core functionality
4. Register the agent with the orchestrator
