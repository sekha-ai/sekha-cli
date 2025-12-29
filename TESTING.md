# Testing Guide

## Test Structure
- Unit tests for CLI commands, client, and config

## Commands
```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests with coverage
./scripts/test.sh

# Run linting only
./scripts/test.sh lint

# Run tests only
./scripts/test.sh unit

Requirements
pytest, pytest-cov, ruff, black
Coverage target: >80%


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