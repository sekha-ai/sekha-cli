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
    return MOCK_CLIENT_INSTANCE


def cleanup():
    """Cleanup module-level mocks."""
    sekha_client_patcher.stop()
    sekha.utils.validate_api_key = original_validate


# Register cleanup
import atexit
atexit.register(cleanup)


class TestQueryCommand:
    """Test query command."""

    def test_query_basic(self, runner, mock_client):
        """Test basic query."""
        mock_client.query.return_value = [
            {"id": "conv-123", "label": "Work", "preview": "Test preview"}
        ]

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test query"])

        assert result.exit_code == 0
        assert "conv-123" in result.output
        assert "Work" in result.output

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
        output = json.loads(result.output)
        assert output[0]["id"] == "conv-123"

    def test_query_no_results(self, runner, mock_client):
        """Test query with no results."""
        mock_client.query.return_value = []

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "query", "test"])

        assert result.exit_code == 0
        assert "No results found" in result.output


class TestStoreCommand:
    """Test store command."""

    @patch("pathlib.Path.exists", return_value=True)
    def test_store_success(self, mock_exists, runner, mock_client, tmp_path):
        """Test successful store."""
        mock_client.store_conversation.return_value = {"id": "conv-123"}

        # Create a temporary JSON file
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


class TestLabelsCommand:
    """Test labels command."""

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


class TestConversationCommand:
    """Test conversation command."""

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

    def test_conversation_show_json(self, runner, mock_client):
        """Test showing conversation in JSON format."""
        mock_client.get_conversation.return_value = {"id": "conv-123", "label": "Test"}

        result = runner.invoke(
            cli,
            [
                "--api-key",
                "sk-test-valid-key-1234567890",
                "conversation",
                "show",
                "conv-123",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["id"] == "conv-123"

    def test_conversation_show_markdown(self, runner, mock_client):
        """Test showing conversation in markdown format."""
        mock_client.get_conversation.return_value = {
            "id": "conv-123",
            "label": "Test",
            "messages": [{"role": "user", "content": "Hello"}],
        }

        result = runner.invoke(
            cli,
            [
                "--api-key",
                "sk-test-valid-key-1234567890",
                "conversation",
                "show",
                "conv-123",
                "--format",
                "markdown",
            ],
        )

        assert result.exit_code == 0
        assert "# Test" in result.output
        assert "**User:** Hello" in result.output


class TestPruneCommand:
    """Test prune command."""

    def test_prune_dry_run(self, runner, mock_client):
        """Test prune with dry-run."""
        mock_client.get_pruning_suggestions.return_value = [
            {"id": "conv-1", "reason": "Low importance"}
        ]

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "prune", "--dry-run"])

        assert result.exit_code == 0
        assert "Would prune 1 conversations" in result.output

    def test_prune_no_dry_run(self, runner, mock_client):
        """Test prune without dry-run flag - should prompt for confirmation."""
        mock_client.get_pruning_suggestions.return_value = [
            {"id": "conv-1", "reason": "Low importance"}
        ]

        # Provide "y" for confirmation
        result = runner.invoke(
            cli,
            ["--api-key", "sk-test-valid-key-1234567890", "prune"],
            input="y\n"
        )

        assert result.exit_code == 0
        # Should show confirmation prompt and success message
        assert "Prune 1 conversations?" in result.output
        assert "Pruning complete." in result.output
        # Verify archive was called
        mock_client.archive.assert_called_once_with("conv-1")

    def test_prune_confirm(self, runner, mock_client):
        """Test prune with confirmation."""
        mock_client.get_pruning_suggestions.return_value = [
            {"id": "conv-1", "reason": "Low importance"}
        ]

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "prune"], input="y\n")

        assert result.exit_code == 0
        mock_client.archive.assert_called_once_with("conv-1")

    def test_prune_no_suggestions(self, runner, mock_client):
        """Test prune when no suggestions exist."""
        mock_client.get_pruning_suggestions.return_value = []

        result = runner.invoke(cli, ["--api-key", "sk-test-valid-key-1234567890", "prune"])

        assert result.exit_code == 0
        assert "No conversations need pruning" in result.output


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
        assert "# Test Label" in output_file.read_text()

    def test_export_json(self, runner, mock_client, tmp_path):
        """Test export in JSON format."""
        mock_client.export.return_value = '[{"id": "conv-123"}]'

        output_file = tmp_path / "export.json"

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
                "json",
            ],
        )

        assert result.exit_code == 0
        output = json.loads(output_file.read_text())
        assert output[0]["id"] == "conv-123"


class TestConfigCommand:
    """Test config command."""

    @patch("sekha_cli.main.Config")
    def test_config_sets_values(self, mock_config_class, runner):
        """Test config sets values."""
        mock_config = mock_config_class.return_value

        # Move --api-key to after 'config' command
        result = runner.invoke(
            cli,
            [
                "config",  # command first
                "--api-url", "http://example.com:8080",
                "--api-key", "sk-test-valid-key-1234567890"  # then its options
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