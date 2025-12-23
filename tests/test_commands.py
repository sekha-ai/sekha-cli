"""Test CLI command functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from sekha_cli.cli import cli
from sekha_cli.client import SekhaClient


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Mock Sekha client."""
    with patch('sekha_cli.cli.SekhaClient') as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestConfigCommands:
    """Test configuration commands."""

    def test_config_set_url(self, runner):
        """Test setting controller URL."""
        result = runner.invoke(cli, ['config', 'set', 'url', 'http://localhost:8080'])
        assert result.exit_code == 0
        assert 'URL set to' in result.output

    def test_config_set_api_key(self, runner):
        """Test setting API key."""
        result = runner.invoke(cli, ['config', 'set', 'api_key', 'test-key-123'])
        assert result.exit_code == 0
        assert 'API key set' in result.output

    def test_config_show(self, runner):
        """Test showing configuration."""
        result = runner.invoke(cli, ['config', 'show'])
        assert result.exit_code == 0


class TestMemoryCommands:
    """Test memory management commands."""

    def test_memory_add(self, runner, mock_client):
        """Test adding a memory."""
        mock_client.conversations.create.return_value = Mock(id='conv-123')

        result = runner.invoke(cli, ['memory', 'add', 'Test memory content'])
        assert result.exit_code == 0
        assert 'conv-123' in result.output or 'added' in result.output.lower()

    def test_memory_list(self, runner, mock_client):
        """Test listing memories."""
        mock_client.conversations.list.return_value = [
            Mock(id='conv-1', label='Memory 1'),
            Mock(id='conv-2', label='Memory 2')
        ]

        result = runner.invoke(cli, ['memory', 'list'])
        assert result.exit_code == 0

    def test_memory_list_with_limit(self, runner, mock_client):
        """Test listing memories with limit."""
        mock_client.conversations.list.return_value = []

        result = runner.invoke(cli, ['memory', 'list', '--limit', '5'])
        assert result.exit_code == 0
        mock_client.conversations.list.assert_called_once()


class TestSearchCommands:
    """Test search commands."""

    def test_search(self, runner, mock_client):
        """Test searching memories."""
        mock_client.query.return_value = {
            'results': [
                {'conversation_id': 'conv-1', 'content': 'Result 1'},
                {'conversation_id': 'conv-2', 'content': 'Result 2'}
            ]
        }

        result = runner.invoke(cli, ['search', 'test query'])
        assert result.exit_code == 0

    def test_search_with_limit(self, runner, mock_client):
        """Test search with limit parameter."""
        mock_client.query.return_value = {'results': []}

        result = runner.invoke(cli, ['search', 'test', '--limit', '10'])
        assert result.exit_code == 0
        mock_client.query.assert_called_once()


class TestVersionCommand:
    """Test version command."""

    def test_version(self, runner):
        """Test version display."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'version' in result.output.lower()


class TestErrorHandling:
    """Test error handling."""

    def test_missing_config(self, runner):
        """Test behavior with missing configuration."""
        with patch('sekha_cli.config.Config.load') as mock_load:
            mock_load.side_effect = FileNotFoundError()
            result = runner.invoke(cli, ['memory', 'list'])
            # Should either create default config or show error
            assert result.exit_code in [0, 1]

    def test_connection_error(self, runner, mock_client):
        """Test handling of connection errors."""
        mock_client.conversations.list.side_effect = ConnectionError('Cannot connect')

        result = runner.invoke(cli, ['memory', 'list'])
        assert result.exit_code != 0
        assert 'connect' in result.output.lower() or 'error' in result.output.lower()