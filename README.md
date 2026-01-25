# Sekha CLI

> **Terminal Memory Management for Sekha**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)]()

---

## What is Sekha CLI?

Command-line tool for managing Sekha memory:

- ✅ Store conversations from terminal
- ✅ Search your memory
- ✅ View stats and insights
- ✅ Import/export conversations
- ✅ Manage labels and folders

**Status:** Beta - Seeking testers!

---

## 📚 Documentation

**Complete guide: [docs.sekha.dev/integrations/cli](https://docs.sekha.dev/integrations/cli/)**

- [CLI Tool Guide](https://docs.sekha.dev/integrations/cli/)
- [Getting Started](https://docs.sekha.dev/getting-started/quickstart/)
- [API Reference](https://docs.sekha.dev/api-reference/rest-api/)

---

## 🚀 Quick Start

### Installation

```bash
# From PyPI (coming soon)
pip install sekha-cli

# From source
git clone https://github.com/sekha-ai/sekha-cli.git
cd sekha-cli
pip install -e .
```

### Configuration

```bash
# Set API endpoint
sekha config set api_url http://localhost:8080
sekha config set api_key your-api-key
```

### Basic Usage

```bash
# Store a conversation
sekha store --label "Terminal Session" --message "Working on memory system"

# Search your memory
sekha search "what did I do yesterday?"

# View stats
sekha stats

# List conversations
sekha list --limit 10

# Export to JSON
sekha export --format json > backup.json
```

---

## 📚 Commands

### Conversations

```bash
sekha store [--label LABEL] [--folder FOLDER] [--message TEXT]
sekha list [--limit N] [--folder FOLDER]
sekha get <conversation-id>
sekha delete <conversation-id>
```

### Search

```bash
sekha search <query> [--limit N]
sekha fts <keywords> [--limit N]  # Full-text search
```

### Organization

```bash
sekha label <conversation-id> <new-label>
sekha move <conversation-id> <new-folder>
sekha archive <conversation-id>
```

### Context & Summarization

```bash
sekha context <query> [--budget TOKENS]
sekha summarize <conversation-id> [--level daily|weekly|monthly]
```

### Import/Export

```bash
sekha export [--format json|markdown] [--output FILE]
sekha import <file>
```

### Stats

```bash
sekha stats              # Overall statistics
sekha health            # Server health check
```

---

## ✨ Features

### Current (Beta)

- ✅ Full conversation CRUD
- ✅ Semantic + full-text search
- ✅ JSON/Markdown export
- ✅ Interactive prompts
- ✅ Pretty terminal output

### Roadmap

- [ ] Auto-save terminal sessions
- [ ] Git integration
- [ ] Fuzzy finder (fzf integration)
- [ ] Batch operations
- [ ] Shell completion

---

## 🧪 Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type check
mypy sekha_cli/

# Lint
ruff check .
```

---

## 🔗 Links

- **Main Repo:** [sekha-controller](https://github.com/sekha-ai/sekha-controller)
- **Docs:** [docs.sekha.dev](https://docs.sekha.dev)
- **Website:** [sekha.dev](https://sekha.dev)
- **Discord:** [discord.gg/sekha](https://discord.gg/sekha)

---

## 📄 License

AGPL-3.0 - **[License Details](https://docs.sekha.dev/about/license/)**
