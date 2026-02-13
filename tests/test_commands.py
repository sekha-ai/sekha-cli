"""Test CLI command functionality."""
import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Mock SDK validation to prevent API key format errors
import sekha.utils
original_validate = sekha.utils.validate_api_key
sekha.utils.validate_api_key = lambda key: True

# Mock SekhaClient class before import
sekha_client_patcher = patch("sekha_cli.main.SekhaClient")
mock_sekha_client_class = sekha_client_patcher.start()
MOCK_CLIENT_INSTANCE = MagicMock()

# Configure defaults that work for all tests
MOCK_CLIENT_INSTANCE.query.return_value = []
MOCK_CLIENT_INSTANCE.list_labels.return_value = []
MOCK_CLIENT_INSTANCE.get_conversation.return_value = {}
MOCK_CLIENT_INSTANCE.get_pruning_suggestions.return_value = []
MOCK_CLIENT_INSTANCE.export.return_value = ""
MOCK_CLIENT_INSTANCE.store_conversation.return_value = {"id": "conv-123"}
# NEW v0.2.0 defaults
MOCK_CLIENT_INSTANCE.delete_conversation.return_value = None
MOCK_CLIENT_INSTANCE.pin_conversation.return_value = None
MOCK_CLIENT_INSTANCE.count_conversations.return_value = {"count": 0}
MOCK_CLIENT_INSTANCE.full_text_search.return_value = []
MOCK_CLIENT_INSTANCE.assemble_context.return_value = []
MOCK_CLIENT_INSTANCE.generate_summary.return_value = {"summary": "Test summary"}
MOCK_CLIENT_INSTANCE.suggest_labels.return_value = []
MOCK_CLIENT_INSTANCE.execute_pruning.return_value = None
MOCK_CLIENT_INSTANCE.list_folders.return_value = []
MOCK_CLIENT_INSTANCE.move_conversation.return_value = None
MOCK_CLIENT_INSTANCE.health_check.return_value = {"status": "healthy"}
MOCK_CLIENT_INSTANCE.rebuild_embeddings.return_value = None

mock_sekha_client_class.return_value = MOCK_CLIENT_INSTANCE

# NOW safe to import the CLI (it will use the mocked client)
from sekha_cli.main import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Reset and configure mock for each test."""
    MOCK_CLIENT_INSTANCE.reset_mock()
    # Reset to safe defaults
    MOCK_CLIENT_INSTANCE.query.return_value = []
    MOCK_CLIENT_INSTANCE.list_labels.return_value = []
    MOCK_CLIENT_INSTANCE.get_conversation.return_value = {}
    MOCK_CLIENT_INSTANCE.get_pruning_suggestions.return_value = []
    MOCK_CLIENT_INSTANCE.export.return_value = ""
    MOCK_CLIENT_INSTANCE.store_conversation.return_value = {"id": "conv-123"}
    # NEW v0.2.0 defaults
    MOCK_CLIENT_INSTANCE.delete_conversation.return_value = None
    MOCK_CLIENT_INSTANCE.pin_conversation.return_value = None
    MOCK_CLIENT_INSTANCE.count_conversations.return_value = {"count": 0}
    MOCK_CLIENT_INSTANCE.full_text_search.return_value = []
    MOCK_CLIENT_INSTANCE.assemble_context.return_value = []
    MOCK_CLIENT_INSTANCE.generate_summary.return_value = {"summary": "Test summary", "level": "daily"}
    MOCK_CLIENT_INSTANCE.suggest_labels.return_value = []
    MOCK_CLIENT_INSTANCE.execute_pruning.return_value = None
    MOCK_CLIENT_INSTANCE.list_folders.return_value = []
    MOCK_CLIENT_INSTANCE.move_conversation.return_value = None
    MOCK_CLIENT_INSTANCE.health_check.return_value = {"status": "healthy", "version": "0.2.0", "uptime_seconds": 100}
    MOCK_CLIENT_INSTANCE.rebuild_embeddings.return_value = None
    return MOCK_CLIENT_INSTANCE


def cleanup():
    """Cleanup module-level mocks."""
    sekha_client_patcher.stop()
    sekha.utils.validate_api_key = original_validate


# Register cleanup
import atexit
atexit.register(cleanup)


class TestQueryCommand:
    """Test query command (deprecated)."""

    def test_query_basic(self, runner, mock_client):
        """Test basic query shows deprecation warning."""
        mock_client.query.return_value = [
            {"id": "conv-123", "label": "Work", "preview": "Test preview", "content": "Test content"}
        ]

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test query"])

        assert result.exit_code == 0
        assert "deprecated" in result.output.lower()
        assert "conv-123" in result.output

    def test_query_with_label(self, runner, mock_client):
        """Test query with label filter."""
        mock_client.query.return_value = []

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test", "--label", "Work"]
        )

        assert result.exit_code == 0
        mock_client.query.assert_called_once_with("test", label="Work", limit=10)

    def test_query_json_format(self, runner, mock_client):
        """Test query with JSON output."""
        mock_client.query.return_value = [{"id": "conv-123"}]

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test", "--format", "json"]
        )

        assert result.exit_code == 0
        assert "deprecated" in result.output.lower()


# ==================== NEW v0.2.0 COMMAND TESTS ====================

class TestSearchCommands:
    """Test new search commands."""

    def test_search_semantic_basic(self, runner, mock_client):
        """Test semantic search."""
        mock_client.query.return_value = [
            {"id": "conv-123", "conversation_id": "conv-123", "label": "AI", "content": "Test content"}
        ]

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "search", "semantic", "embeddings"]
        )

        assert result.exit_code == 0
        assert "Semantic Search" in result.output
        mock_client.query.assert_called_once()

    def test_search_fts_basic(self, runner, mock_client):
        """Test full-text search."""
        mock_client.full_text_search.return_value = [
            {"conversation_id": "conv-1", "role": "user", "content": "test message"}
        ]

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "search", "fts", "test keywords"]
        )

        assert result.exit_code == 0
        assert "Full-Text Search" in result.output
        mock_client.full_text_search.assert_called_once_with("test keywords", limit=10)

    def test_search_fts_json_format(self, runner, mock_client):
        """Test FTS with JSON output."""
        mock_client.full_text_search.return_value = [{"content": "test"}]

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "search", "fts", "test", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1


class TestConversationCRUD:
    """Test conversation CRUD commands."""

    def test_conversation_delete_with_confirmation(self, runner, mock_client):
        """Test conversation deletion with user confirmation."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "delete", "conv-123"],
            input="y\n"
        )

        assert result.exit_code == 0
        assert "Delete conversation" in result.output
        mock_client.delete_conversation.assert_called_once_with("conv-123")

    def test_conversation_delete_with_yes_flag(self, runner, mock_client):
        """Test conversation deletion with --yes flag."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "delete", "conv-123", "--yes"]
        )

        assert result.exit_code == 0
        mock_client.delete_conversation.assert_called_once_with("conv-123")

    def test_conversation_delete_cancelled(self, runner, mock_client):
        """Test conversation deletion cancelled."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "delete", "conv-123"],
            input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output
        mock_client.delete_conversation.assert_not_called()

    def test_conversation_pin(self, runner, mock_client):
        """Test conversation pinning."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "pin", "conv-123"]
        )

        assert result.exit_code == 0
        assert "Pinned" in result.output
        mock_client.pin_conversation.assert_called_once_with("conv-123")

    def test_conversation_archive(self, runner, mock_client):
        """Test conversation archiving."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "archive", "conv-123"]
        )

        assert result.exit_code == 0
        assert "Archived" in result.output
        mock_client.archive.assert_called_once_with("conv-123")

    def test_conversation_count_all(self, runner, mock_client):
        """Test counting all conversations."""
        mock_client.count_conversations.return_value = {"count": 42}

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "count"]
        )

        assert result.exit_code == 0
        assert "42" in result.output
        mock_client.count_conversations.assert_called_once_with(label=None, folder=None)

    def test_conversation_count_by_label(self, runner, mock_client):
        """Test counting conversations by label."""
        mock_client.count_conversations.return_value = {"count": 15, "label": "Work"}

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "conversation", "count", "--label", "Work"]
        )

        assert result.exit_code == 0
        assert "15" in result.output
        mock_client.count_conversations.assert_called_once_with(label="Work", folder=None)


class TestLabelCommands:
    """Test label management commands."""

    def test_labels_suggest(self, runner, mock_client):
        """Test AI label suggestions."""
        mock_client.suggest_labels.return_value = [
            {"label": "AI", "confidence": 0.95, "is_existing": True, "reason": "AI content"},
            {"label": "ML", "confidence": 0.85, "is_existing": False, "reason": "ML topics"}
        ]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "labels", "suggest", "conv-123"]
        )

        assert result.exit_code == 0
        assert "AI Label Suggestions" in result.output
        assert "AI" in result.output
        assert "0.95" in result.output
        mock_client.suggest_labels.assert_called_once_with("conv-123")

    def test_labels_suggest_json(self, runner, mock_client):
        """Test label suggestions JSON output."""
        mock_client.suggest_labels.return_value = [{"label": "Test", "confidence": 0.9}]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "labels", "suggest", "conv-123", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data[0]["label"] == "Test"


class TestFolderCommands:
    """Test folder management commands."""

    def test_folder_list(self, runner, mock_client):
        """Test listing folders."""
        mock_client.list_folders.return_value = ["/Work", "/Personal", "/Archive"]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "folder", "list"]
        )

        assert result.exit_code == 0
        assert "/Work" in result.output
        assert "/Personal" in result.output
        mock_client.list_folders.assert_called_once()

    def test_folder_list_empty(self, runner, mock_client):
        """Test listing folders when none exist."""
        mock_client.list_folders.return_value = []

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "folder", "list"]
        )

        assert result.exit_code == 0
        assert "No folders found" in result.output

    def test_folder_move(self, runner, mock_client):
        """Test moving conversation to folder."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "folder", "move", "conv-123", "/NewFolder"]
        )

        assert result.exit_code == 0
        assert "Moved" in result.output
        mock_client.move_conversation.assert_called_once_with("conv-123", "/NewFolder")


class TestContextCommand:
    """Test context assembly command."""

    def test_context_basic(self, runner, mock_client):
        """Test basic context assembly."""
        mock_client.assemble_context.return_value = [
            {"role": "user", "content": "Context message 1"},
            {"role": "assistant", "content": "Context message 2"}
        ]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "context", "explain embeddings"]
        )

        assert result.exit_code == 0
        assert "relevant messages" in result.output
        mock_client.assemble_context.assert_called_once()

    def test_context_with_options(self, runner, mock_client):
        """Test context assembly with all options."""
        mock_client.assemble_context.return_value = []

        result = runner.invoke(
            cli,
            [
                "--api-key", "sk-test-valid-key-1234567890",
                "context", "test query",
                "--budget", "2000",
                "--labels", "AI",
                "--labels", "ML",
                "--exclude-folders", "/Archive"
            ]
        )

        assert result.exit_code == 0
        call_args = mock_client.assemble_context.call_args
        assert call_args[1]["query"] == "test query"
        assert call_args[1]["context_budget"] == 2000
        assert "AI" in call_args[1]["preferred_labels"]

    def test_context_json_format(self, runner, mock_client):
        """Test context with JSON output."""
        mock_client.assemble_context.return_value = [{"role": "user", "content": "test"}]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "context", "test", "--format", "json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1


class TestSummarizeCommand:
    """Test summarization command."""

    def test_summarize_daily(self, runner, mock_client):
        """Test daily summary generation."""
        mock_client.generate_summary.return_value = {
            "summary": "Daily summary text",
            "level": "daily"
        }

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "summarize", "conv-123", "--level", "daily"]
        )

        assert result.exit_code == 0
        assert "summary" in result.output.lower()
        mock_client.generate_summary.assert_called_once_with("conv-123", "daily")

    def test_summarize_weekly(self, runner, mock_client):
        """Test weekly summary generation."""
        mock_client.generate_summary.return_value = {"summary": "Weekly summary", "level": "weekly"}

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "summarize", "conv-123", "--level", "weekly"]
        )

        assert result.exit_code == 0
        mock_client.generate_summary.assert_called_once_with("conv-123", "weekly")

    def test_summarize_json_format(self, runner, mock_client):
        """Test summary with JSON output."""
        mock_client.generate_summary.return_value = {"summary": "Test", "level": "daily"}

        result = runner.invoke(
            cli,
            [
                "--api-key", "sk-test-valid-key-1234567890",
                "summarize", "conv-123",
                "--level", "monthly",
                "--format", "json"
            ]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "summary" in data


class TestPruneCommandEnhanced:
    """Test enhanced prune command."""

    def test_prune_with_yes_flag(self, runner, mock_client):
        """Test prune with --yes flag."""
        mock_client.get_pruning_suggestions.return_value = [
            {"conversation_id": "conv-1", "conversation_label": "Old", "recommendation": "archive"},
            {"conversation_id": "conv-2", "conversation_label": "Stale", "recommendation": "archive"}
        ]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "prune", "--yes"]
        )

        assert result.exit_code == 0
        assert "Pruned 2 conversations" in result.output
        mock_client.execute_pruning.assert_called_once()
        call_args = mock_client.execute_pruning.call_args[0][0]
        assert "conv-1" in call_args
        assert "conv-2" in call_args

    def test_prune_dry_run_with_table(self, runner, mock_client):
        """Test prune dry-run shows table."""
        mock_client.get_pruning_suggestions.return_value = [
            {"conversation_id": "conv-1", "conversation_label": "Test", "recommendation": "archive"}
        ]

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "prune", "--dry-run"]
        )

        assert result.exit_code == 0
        assert "Would prune 1 conversations" in result.output
        mock_client.execute_pruning.assert_not_called()


class TestHealthCommand:
    """Test health check command."""

    def test_health_check_healthy(self, runner, mock_client):
        """Test health check with healthy status."""
        mock_client.health_check.return_value = {
            "status": "healthy",
            "version": "0.2.0",
            "uptime_seconds": 12345
        }

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "health"]
        )

        assert result.exit_code == 0
        assert "healthy" in result.output.lower()
        assert "0.2.0" in result.output
        mock_client.health_check.assert_called_once()

    def test_health_check_failure(self, runner, mock_client):
        """Test health check with failure."""
        mock_client.health_check.side_effect = RuntimeError("Connection failed")

        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "health"]
        )

        assert result.exit_code != 0
        assert "failed" in result.output.lower()


class TestRebuildEmbeddingsCommand:
    """Test embeddings rebuild command."""

    def test_rebuild_embeddings_with_yes(self, runner, mock_client):
        """Test rebuild with --yes flag."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "rebuild-embeddings", "--yes"]
        )

        assert result.exit_code == 0
        assert "rebuild started" in result.output.lower()
        mock_client.rebuild_embeddings.assert_called_once()

    def test_rebuild_embeddings_with_confirmation(self, runner, mock_client):
        """Test rebuild with user confirmation."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "rebuild-embeddings"],
            input="y\n"
        )

        assert result.exit_code == 0
        mock_client.rebuild_embeddings.assert_called_once()

    def test_rebuild_embeddings_cancelled(self, runner, mock_client):
        """Test rebuild cancelled."""
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "rebuild-embeddings"],
            input="n\n"
        )

        assert result.exit_code == 0
        assert "Cancelled" in result.output
        mock_client.rebuild_embeddings.assert_not_called()


# ==================== EXISTING TESTS (UPDATED) ====================

class TestStoreCommand:
    """Test store command."""

    @patch("pathlib.Path.exists", return_value=True)
    def test_store_success(self, mock_exists, runner, mock_client, tmp_path):
        """Test successful store."""
        mock_client.store_conversation.return_value = {"id": "conv-123"}

        test_file = tmp_path / "test.json"
        test_file.write_text(
            json.dumps({"messages": [{"role": "user", "content": "Hello"}]})
        )

        result = runner.invoke(
            cli,
            [
                "--api-key",
                "sk-test-valid-key-1234567890",
                "store",
                "--file",
                str(test_file),
                "--label",
                "Imported",
            ],
        )

        assert result.exit_code == 0
        assert "conv-123" in result.output

    def test_store_missing_file(self, runner):
        """Test store with missing file."""
        result = runner.invoke(
            cli,
            [
                "--api-key",
                "sk-test-valid-key-1234567890",
                "store",
                "--file",
                "/nonexistent.json",
                "--label",
                "Test",
            ],
        )

        assert result.exit_code != 0


class TestLabelsListCommand:
    """Test labels list command."""

    def test_labels_list(self, runner, mock_client):
        """Test listing labels."""
        mock_client.list_labels.return_value = [
            {"name": "Work", "count": 5},
            {"name": "Personal", "count": 3},
        ]

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "labels", "list"])

        assert result.exit_code == 0
        assert "Work" in result.output
        assert "5" in result.output

    def test_labels_list_empty(self, runner, mock_client):
        """Test listing labels when none exist."""
        mock_client.list_labels.return_value = []

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "labels", "list"])

        assert result.exit_code == 0
        assert "No labels found" in result.output


class TestConversationShowCommand:
    """Test conversation show command."""

    def test_conversation_show_text(self, runner, mock_client):
        """Test showing conversation in text format."""
        mock_client.get_conversation.return_value = {
            "id": "conv-123",
            "label": "Test",
            "created_at": "2024-01-01",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
        }

        result = runner.invoke(
            cli, ["--api-key", "sk-test-valid-key-1234567890", "conversation", "show", "conv-123"]
        )

        assert result.exit_code == 0
        assert "Test" in result.output
        assert "user:" in result.output


class TestExportCommand:
    """Test export command."""

    def test_export_markdown(self, runner, mock_client, tmp_path):
        """Test export in markdown format."""
        mock_client.export.return_value = "# Test Label\n\n**User:** Hello\n\n"

        output_file = tmp_path / "export.md"

        result = runner.invoke(
            cli,
            [
                "--api-key",
                "sk-test-valid-key-1234567890",
                "export",
                "--label",
                "Test",
                "--output",
                str(output_file),
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()


class TestConfigCommand:
    """Test config command."""

    @patch("sekha_cli.main.Config")
    def test_config_sets_values(self, mock_config_class, runner):
        """Test config sets values."""
        mock_config = mock_config_class.return_value

        result = runner.invoke(
            cli,
            [
                "config",
                "--api-url", "http://example.com:8080",
                "--api-key", "sk-test-valid-key-1234567890"
            ],
        )

        assert result.exit_code == 0
        mock_config_class.assert_called_once_with(
            base_url="http://example.com:8080",
            api_key="sk-test-valid-key-1234567890"
        )
        mock_config.save.assert_called_once()


class TestErrorHandling:
    """Test error handling."""

    def test_missing_api_key(self, runner):
        """Test error when API key not provided."""
        result = runner.invoke(cli, ["query", "test"])

        assert result.exit_code != 0
        assert "API key required" in result.output

    def test_client_error_propagation(self, runner, mock_client):
        """Test that client errors are handled gracefully."""
        mock_client.query.side_effect = RuntimeError("Connection failed")

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test"])

        assert result.exit_code != 0
        assert "Search failed" in result.output
