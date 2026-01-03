#!/bin/bash
set -e

echo "🚀 Setting up Sekha development environment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$WORKSPACE_DIR"

echo -e "${YELLOW}→ Installing sekha-python-sdk...${NC}"
cd sekha-python-sdk
pip install -e .

echo -e "${YELLOW}→ Installing sekha-cli...${NC}"
cd ../sekha-cli
pip install -e ".[dev]"

echo -e "${GREEN}✅ Development environment ready!${NC}"
echo ""
echo "You can now run tests:"
echo "  cd sekha-cli && ./scripts/test.sh"