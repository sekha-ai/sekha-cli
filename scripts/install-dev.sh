#!/bin/bash
set -e

echo "🔧 Installing Sekha CLI in development mode..."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CLI_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE_DIR="$(dirname "$CLI_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_info() { echo -e "${YELLOW}→${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

cd "$WORKSPACE_DIR"

# 1. Install SDK
if [ -d "sekha-python-sdk" ]; then
    print_info "Installing sekha-python-sdk..."
    cd sekha-python-sdk
    pip install -e .
    cd ..
    print_success "SDK installed"
else
    print_error "sekha-python-sdk not found"
    exit 1
fi

# 2. Install CLI dependencies
cd sekha-cli
print_info "Installing CLI dependencies..."
pip install click>=8.0.0 rich>=13.0.0 pyyaml>=6.0
pip install pytest>=7.0 pytest-cov>=4.0 pytest-mock>=3.10.0 black>=23.0 ruff>=0.1.0 mypy>=1.5

# 3. Create convenience alias
echo ""
echo "To run tests, use:"
echo "  PYTHONPATH=. pytest tests/ -v --cov=sekha_cli"
echo ""
echo "Or add to your ~/.bashrc:"
echo "  export PYTHONPATH=\"${CLI_DIR}:\$PYTHONPATH\""
echo ""
print_success "Install complete!"