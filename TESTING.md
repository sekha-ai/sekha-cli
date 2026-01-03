# Sekha CLI Testing Guide

## Overview
This document describes the testing strategy and procedures for the Sekha CLI tool.

## Test Structure
- **Unit Tests**: Test individual components (client, config, commands)
- **Integration Tests**: Test full CLI workflows with mocked dependencies
- **Coverage Target**: &gt;80% (enforced by CI)

## Test Files
- `tests/test_client.py` - Tests for SekhaClient class
- `tests/test_config.py` - Tests for configuration management
- `tests/test_commands.py` - Tests for CLI commands
- `tests/conftest.py` - Pytest fixtures and configuration

## Running Tests

### Install Dependencies
```bash
pip install -e ".[dev]"```bash

# Install test dependencies
pip install -e ".[test]"

# Run all tests with coverage
./scripts/test.sh

# Run linting only
./scripts/test.sh lint

# Run tests only
./scripts/test.sh unit

# Run specific tests
pytest tests/test_client.py -v
pytest tests/test_commands.py -v
pytest tests/test_config.py -v

# Generate Coverage Report
pytest --cov=sekha_cli --cov-report=html
# Open htmlcov/index.html in browser

# Requirements
pytest, pytest-cov, ruff, black
Coverage target: >80%


** Linting **
We use Black for code formatting and Ruff for linting.

# Format code
black sekha_cli tests

# Check linting
ruff check sekha_cli tests

# Run both
./scripts/test.sh lint

** Continuous Integration **

GitHub Actions runs:
- Linting (Black + Ruff)
- Unit tests with coverage enforcement (>80%)
- Integration tests (when available)

Adding New Tests
  When adding new CLI commands:
- Add unit tests in tests/test_client.py for client methods
- Add integration tests in tests/test_commands.py for CLI command
- Ensure >80% coverage
- Update this documentation

Test Data
Use pytest fixtures in conftest.py for test data. Never commit real API keys or sensitive data.
---

#### **✅ sekha-docker**
**Current State:**
- Has `tests/test_docker_compose.rs`
- Has cloud and helm test scripts

**Missing/Needs Verification:**
- [ ] Shell script wrapper for all docker tests
- [ ] shellcheck linting script
- [ ] Integration test orchestration

**create file: `sekha-docker/scripts/test.sh`**
```bash
#!/bin/bash
set -e

echo "🐳 Running Sekha Docker Test Suite..."

TEST_TYPE=${1:-"all"}

case $TEST_TYPE in
  "shellcheck")
    echo "🔍 Running shellcheck..."
    find docker/ -name "*.sh" -exec shellcheck {} \;
    ;;
  "compose")
    echo "Testing docker-compose..."
    docker-compose -f docker/docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
    ;;
  "helm")
    echo "Testing Helm charts..."
    ./helm/tests/test_helm.sh
    ;;
  "cloud")
    echo "Testing cloud configs..."
    ./cloud/tests/test_terraform.sh
    ;;
  "all"|*)
    echo "Running all docker tests..."
    ./scripts/test.sh shellcheck
    ./scripts/test.sh compose
    ./scripts/test.sh helm
    ;;
esac

echo "✅ Docker tests complete!"