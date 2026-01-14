[![CI Status](https://github.com/sekha-ai/sekha-cli/workflows/CI/badge.svg)](https://github.com/sekha-ai/sekha-cli/actions)
[![codecov](https://codecov.io/gh/sekha-ai/sekha-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/sekha-ai/sekha-cli)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org)
[![PyPI](https://img.shields.io/pypi/v/sekha-cli.svg)](https://pypi.org/project/sekha-cli/)

# Sekha CLI

Command-line interface for the Sekha AI Memory Controller - store, search, and manage AI conversation memories from your terminal.

## Installation

```bash
pip install sekha-cli


For development (from workspace root):

./sekha-cli/scripts/install-dev.sh


## Configuration
Set your API credentials via environment variables or command-line options:

# Option 1: Environment variables
export SEKHA_API_URL="http://localhost:8080"
export SEKHA_API_KEY="your-api-key"

# Option 2: Configuration file
sekha config --api-url http://localhost:8080 --api-key your-api-key

# Option 3: Command-line flags (per command)
sekha --api-key your-api-key query "memory limits"


## Usage
- Search Conversations

# Basic search
sekha query "token limits"

# Search with label filter
sekha query "performance" --label Work --limit 10

# JSON output
sekha query "context window" --format json


- Store Conversations

# Store from JSON file
sekha store --file conversation.json --label "Imported"


- Manage Labels

# List all labels with counts
sekha labels list

- View Conversations

# Show conversation details
sekha conversation show <conversation-id>

# Show as markdown
sekha conversation show <conversation-id> --format markdown

# Show as JSON
sekha conversation show <conversation-id> --format json


- Prune Old Conversations

# Preview what would be pruned
sekha prune --dry-run

# Actually prune (with confirmation)
sekha prune


- Export Conversations

# Export by label as markdown
sekha export --label "Project:AI" --output backup.md

# Export as JSON
sekha export --label "Work" --output work.json --format json


## Commands

query - Search conversations with semantic search
store - Store conversation from JSON file
labels - Manage conversation labels
conversation - View conversation details
prune - Prune low-importance conversations
export - Export conversations by label
config - Configure default connection settings


## Development

# Install dependencies
cd sekha-cli
./scripts/install-dev.sh

# Run tests
./scripts/test.sh

# Run linting only
./scripts/test.sh lint

# Run tests only
./scripts/test.sh unit


## Requirements
Python 3.8+
Sekha Controller API (running instance)
API key from Sekha Controller


## License
AGPL-3.0 - See LICENSE file for details.


## Project Links
Sekha Controller - https://github.com/sekha-ai/sekha-controller
Sekha Python SDK - https://github.com/sekha-ai/sekha-python-sdk
Sekha Documentation - https://github.com/sekha-ai/sekha-docs 
