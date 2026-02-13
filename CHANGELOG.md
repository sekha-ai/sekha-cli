# Changelog

All notable changes to Sekha CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-13

### Added

#### Search & Query
- **Full-text search (FTS5)**: New `sekha search fts` command for SQLite FTS5-based keyword search
- **Semantic search**: Reorganized as `sekha search semantic` (old `sekha query` still works but deprecated)
- Both search methods now support rich terminal output with better formatting

#### Conversation Management
- **Delete conversations**: `sekha conversation delete <id>` to permanently remove conversations
- **Pin conversations**: `sekha conversation pin <id>` to mark as high importance
- **Count conversations**: `sekha conversation count` with optional `--label` and `--folder` filters
- Enhanced conversation operations with confirmation prompts and better UX

#### Context & Summarization
- **Context assembly**: `sekha context <query>` to retrieve relevant memory context
  - Supports `--budget` for token limits
  - `--labels` for preferred labels (can specify multiple)
  - `--exclude-folders` to exclude specific folders
- **Hierarchical summaries**: `sekha summarize <id> --level {daily|weekly|monthly}`
  - Daily, weekly, and monthly summary generation
  - Output in text, JSON, or markdown format

#### AI-Powered Features
- **Label suggestions**: `sekha labels suggest <id>` for AI-powered label recommendations
  - Shows confidence scores
  - Indicates if labels already exist
  - Provides reasoning for suggestions
- **Enhanced pruning**: `sekha prune --yes` to execute pruning without confirmation
  - Improved dry-run output with table view
  - Shows first 10 suggestions with full metadata

#### Folder Management
- **List folders**: `sekha folder list` to see all folders in use
- **Move conversations**: `sekha folder move <id> <folder>` to organize conversations
- Folders are now first-class citizens in the CLI

#### Health & Maintenance
- **Health check**: `sekha health` to verify controller status
  - Shows version, uptime, and health status
  - Color-coded output (green=healthy, red=unhealthy)
- **Rebuild embeddings**: `sekha rebuild-embeddings` to trigger async embedding rebuild
  - Useful after bulk imports or schema changes

#### Developer Experience
- Comprehensive test coverage for all new features (80%+ maintained)
- 40+ new test cases covering all v0.2.0 functionality
- Rich terminal UI with emojis, panels, and better tables
- Better error messages with context

### Changed

- **Breaking**: `sekha query` is now deprecated in favor of `sekha search semantic`
  - Old command still works with deprecation warning
  - Will be removed in v1.0.0
- All commands now use rich console output for better UX
- Improved error handling across all endpoints
- Better handling of conversation IDs (truncated display, full UUID usage)

### Dependencies

- Added `requests>=2.31.0` for direct HTTP API calls
- Added `responses>=0.25.0` (dev) for HTTP mocking in tests
- All existing dependencies maintained

### API Coverage

**v0.1.0**: ~42% of controller API  
**v0.2.0**: ~95% of controller API

Now supports:
- ✅ All conversation CRUD operations
- ✅ Semantic + full-text search
- ✅ Context assembly
- ✅ Hierarchical summaries
- ✅ AI label suggestions
- ✅ Pruning (dry-run + execute)
- ✅ Folder management
- ✅ Health checks
- ✅ Embedding rebuild

### Migration Guide

#### For Users of `sekha query`

Old:
```bash
sekha query "embeddings" --label AI
```

New:
```bash
sekha search semantic "embeddings" --label AI
```

#### For Pruning

Old:
```bash
sekha prune --dry-run
# Then manually archive conversations
```

New:
```bash
sekha prune --dry-run  # See suggestions
sekha prune --yes      # Execute pruning
```

## [0.1.0] - 2026-02-07

### Added

- Initial release
- Basic conversation CRUD: create, read, list
- Semantic search via `sekha query`
- Label management: list labels
- Export: markdown and JSON formats
- Pruning: dry-run suggestions
- Configuration management
- Python SDK integration
- Rich terminal output
- Comprehensive test suite (80% coverage)

### Known Limitations

- No full-text search
- No context assembly
- No summarization
- No AI features (label suggestions)
- No folder management
- No health checks
- Pruning dry-run only (no execution)

---

## Upcoming

### [0.3.0] - Planned

- Shell completion (bash, zsh, fish)
- Interactive mode with TUI
- Git integration for auto-tracking commits
- Batch operations
- Import from common formats (Notion, Obsidian, etc.)
- Fuzzy finder integration (fzf)
- Conversation merging
- Advanced filtering

### [1.0.0] - Planned

- Stable API
- Remove deprecated `query` command
- Plugin system
- Cloud sync
- Encryption at rest
- Multi-user support

---

[0.2.0]: https://github.com/sekha-ai/sekha-cli/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/sekha-ai/sekha-cli/releases/tag/v0.1.0
