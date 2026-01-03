"""Test Sekha client functionality."""
import json
from unittest.mock import MagicMock, patch

import pytest
from sekha_cli.client import SekhaClient


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_params(self):
        """Test initialization with parameters."""
        client = SekhaClient(base_url="http://example.com", api_key="sk-test-valid-key-1234567890")
        assert client.base_url == "http://example.com"
        assert client.api_key == "sk-test-valid-key-1234567890"
        assert client.headers["Authorization"] == "Bearer sk-test-valid-key-1234567890"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        client = SekhaClient(base_url="http://localhost:8080/", api_key="sk-test-valid-key-1234567890")
        assert client.base_url == "http://localhost:8080"


class TestQueryOperations:
    """Test query/search operations."""

    @patch("sekha_cli.client.MemoryController")
    def test_query_success(self, mock_controller_class):
        """Test successful query."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.search.return_value = [
            {"id": "conv-1", "label": "Test", "preview": "Test preview"}
        ]

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")
        results = client.query("test query", label="Work", limit=5)

        assert len(results) == 1
        assert results[0]["id"] == "conv-1"
        mock_controller.search.assert_called_once_with(
            "test query", label="Work", limit=5
        )

    @patch("sekha_cli.client.MemoryController")
    def test_query_with_error(self, mock_controller_class):
        """Test query with error."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.search.side_effect = Exception("Search failed")

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")

        with pytest.raises(RuntimeError, match="Query failed"):
            client.query("test")


class TestStoreOperations:
    """Test store operations."""

    @patch("builtins.open", create=True)
    @patch("sekha_cli.client.MemoryController")
    def test_store_success(self, mock_controller_class, mock_open):
        """Test successful store from file."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.create.return_value = {"id": "conv-123"}

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(
            {"messages": [{"role": "user", "content": "Hello"}]}
        )
        mock_open.return_value = mock_file

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")
        result = client.store_conversation("/path/to/file.json", "Imported")

        assert result["id"] == "conv-123"
        assert result["label"] == "Imported"

    def test_store_invalid_file(self):
        """Test store with invalid file."""
        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")

        with pytest.raises(ValueError, match="No messages found"):
            # This would fail because file doesn't exist,
            # but we test the error path
            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.__enter__.return_value.read.return_value = json.dumps({})
                mock_open.return_value = mock_file

                client.store_conversation("/path/to/file.json", "Test")


class TestLabelOperations:
    """Test label operations."""

    @patch("sekha_cli.client.MemoryController")
    def test_list_labels(self, mock_controller_class):
        """Test listing labels."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.search.return_value = [
            {"id": "1", "label": "Work"},
            {"id": "2", "label": "Personal"},
            {"id": "3", "label": "Work"},
        ]

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")
        labels = client.list_labels()

        assert len(labels) == 2  # Two unique labels
        work_label = next(label for label in labels if label["name"] == "Work")
        assert work_label["count"] == 2


class TestExportOperations:
    """Test export operations."""

    @patch("sekha_cli.client.MemoryController")
    def test_export_markdown(self, mock_controller_class):
        """Test markdown export."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        
        # Mock search() not list()
        mock_controller.search.return_value = [
            {
                "id": "conv-1",
                "label": "Project:AI",
                "created_at": "2024-01-01",
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"},
                ],
            }
        ]
        
        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")
        content = client.export("Project:AI", format="markdown")
        
        assert "# Project:AI" in content
        assert "**User:** Hello" in content
        assert "**Assistant:** Hi there" in content

        @patch("sekha_cli.client.MemoryController")
        def test_export_invalid_format(self, mock_controller_class):
            """Test export with invalid format."""
            mock_controller = MagicMock()
            mock_controller_class.return_value = mock_controller
            mock_controller.search.return_value = []
            
            client = SekhaClient(base_url="http://test.com ", api_key="sk-test-valid-key-1234567890")

            with pytest.raises(ValueError, match="Unsupported format"):
                client.export("test", format="invalid")


class TestErrorHandling:
    """Test error handling."""

    @patch("sekha_cli.client.MemoryController")
    def test_get_conversation_error(self, mock_controller_class):
        """Test error handling in get_conversation."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.get.side_effect = RuntimeError("Not found")

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")

        with pytest.raises(RuntimeError):
            client.get_conversation("nonexistent")
