#!/bin/bash
set -e

echo "🧪 Running Sekha CLI Test Suite..."

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TEST_TYPE=${1:-"all"}

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

run_lint() {
    print_info "Running linting checks..."
    
    # Run ruff
    if command -v ruff &> /dev/null; then
        ruff check sekha_cli tests
        print_success "Ruff checks passed"
    else
        print_error "ruff not found, install with: pip install ruff"
        exit 1
    fi
    
    # Run black check
    if command -v black &> /dev/null; then
        black --check sekha_cli tests
        print_success "Black format check passed"
    else
        print_error "black not found, install with: pip install black"
        exit 1
    fi
}

run_unit_tests() {
    print_info "Running unit tests with coverage..."
    
    if python -m pytest --version &> /dev/null; then
        python -m pytest -v --cov=sekha_cli --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=80
        print_success "Unit tests passed with >80% coverage"
    else
        print_error "pytest not found, install with: pip install pytest pytest-cov"
        exit 1
    fi
}

case $TEST_TYPE in
    "lint")
        run_lint
        ;;
    "unit")
        run_unit_tests
        ;;
    "all"|*)
        run_lint
        echo ""
        run_unit_tests
        ;;
esac

echo ""
print_success "All tests completed successfully!"