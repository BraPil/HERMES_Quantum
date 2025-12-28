# Tests

This directory contains unit tests, integration tests, and test utilities for the HERMES_Quantum system.

## Purpose

The tests package ensures:
- Code correctness and reliability
- Regression prevention
- Documentation of expected behavior
- Confidence in system changes

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for component interactions
- `fixtures/` - Test data and fixtures
- `conftest.py` - Pytest configuration and shared fixtures

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_analyst.py

# Run tests matching a pattern
pytest -k "test_sentiment"
```

## Writing Tests

Follow these conventions:
- Test files should be named `test_*.py`
- Test classes should be named `Test*`
- Test functions should be named `test_*`
- Use descriptive test names
- Include docstrings explaining what is being tested

## Test Coverage

Aim for high test coverage, especially for:
- Core functionality
- Agent logic
- Data processing pipelines
- API integrations
- Error handling
