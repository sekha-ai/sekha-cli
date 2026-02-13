"""Test Sekha client functionality."""
import json
from unittest.mock import MagicMock, patch, mock_open

import pytest
import responses
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

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({"messages": [{"role": "user", "content": "Hello"}]}))
    @patch("sekha_cli.client.MemoryController")
    def test_store_success(self, mock_controller_class, mock_file):
        """Test successful store from file."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.create.return_value = {"id": "conv-123"}

        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")
        result = client.store_conversation("/path/to/file.json", "Imported")

        assert result["id"] == "conv-123"
        assert result["label"] == "Imported"

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({}))
    def test_store_invalid_file(self, mock_file):
        """Test store with invalid file."""
        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")

        with pytest.raises(ValueError, match="No messages found"):
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
        
        client = SekhaClient(base_url="http://test.com", api_key="sk-test-valid-key-1234567890")

        with pytest.raises(ValueError, match="Unsupported format"):
            client.export("test", format="invalid")


# ==================== NEW v0.2.0 TESTS ====================

class TestDeleteConversation:
    """Test delete conversation functionality."""

    @responses.activate
    def test_delete_success(self):
        """Test successful conversation deletion."""
        responses.add(
            responses.DELETE,
            "http://test.com/api/v1/conversations/conv-123",
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        client.delete_conversation("conv-123")  # Should not raise

    @responses.activate
    def test_delete_not_found(self):
        """Test delete with non-existent conversation."""
        responses.add(
            responses.DELETE,
            "http://test.com/api/v1/conversations/conv-404",
            status=404
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="not found"):
            client.delete_conversation("conv-404")


class TestPinConversation:
    """Test pin/unpin conversation functionality."""

    @responses.activate
    def test_pin_success(self):
        """Test successful conversation pinning."""
        responses.add(
            responses.PUT,
            "http://test.com/api/v1/conversations/conv-123/pin",
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        client.pin_conversation("conv-123")  # Should not raise

    @responses.activate
    def test_pin_failure(self):
        """Test pin with error."""
        responses.add(
            responses.PUT,
            "http://test.com/api/v1/conversations/conv-123/pin",
            status=500,
            body="Internal error"
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Pin failed"):
            client.pin_conversation("conv-123")

    def test_unpin_not_implemented(self):
        """Test that unpin raises NotImplementedError."""
        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(NotImplementedError, match="Unpin not yet supported"):
            client.unpin_conversation("conv-123")


class TestCountConversations:
    """Test conversation counting."""

    @responses.activate
    def test_count_all(self):
        """Test counting all conversations."""
        responses.add(
            responses.GET,
            "http://test.com/api/v1/conversations/count",
            json={"count": 42, "label": None, "folder": None},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.count_conversations()
        assert result["count"] == 42

    @responses.activate
    def test_count_by_label(self):
        """Test counting by label."""
        responses.add(
            responses.GET,
            "http://test.com/api/v1/conversations/count",
            json={"count": 15, "label": "Work", "folder": None},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.count_conversations(label="Work")
        assert result["count"] == 15
        assert result["label"] == "Work"

    def test_count_both_label_and_folder(self):
        """Test that specifying both label and folder raises error."""
        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(ValueError, match="Cannot specify both"):
            client.count_conversations(label="Work", folder="/Projects")


class TestFullTextSearch:
    """Test full-text search functionality."""

    @responses.activate
    def test_fts_success(self):
        """Test successful FTS query."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/search/fts",
            json={"results": [
                {"conversation_id": "conv-1", "content": "Test message", "role": "user"}
            ]},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        results = client.full_text_search("test query", limit=10)
        
        assert len(results) == 1
        assert results[0]["content"] == "Test message"

    @responses.activate
    def test_fts_failure(self):
        """Test FTS with error."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/search/fts",
            status=500,
            body="Search error"
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="FTS search failed"):
            client.full_text_search("test")


class TestAssembleContext:
    """Test context assembly."""

    @responses.activate
    def test_assemble_context_basic(self):
        """Test basic context assembly."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/context/assemble",
            json=[{"role": "user", "content": "Context message"}],
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.assemble_context("test query")
        
        assert len(result) == 1
        assert result[0]["content"] == "Context message"

    @responses.activate
    def test_assemble_context_with_options(self):
        """Test context assembly with all options."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/context/assemble",
            json=[],
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.assemble_context(
            query="test",
            preferred_labels=["Work", "AI"],
            context_budget=2000,
            excluded_folders=["/Archive"]
        )
        
        assert isinstance(result, list)


class TestGenerateSummary:
    """Test summary generation."""

    @responses.activate
    def test_generate_summary_daily(self):
        """Test daily summary generation."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/summarize",
            json={
                "conversation_id": "conv-123",
                "level": "daily",
                "summary": "Daily summary text",
                "generated_at": "2024-01-01T12:00:00"
            },
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.generate_summary("conv-123", "daily")
        
        assert result["summary"] == "Daily summary text"
        assert result["level"] == "daily"

    def test_generate_summary_invalid_level(self):
        """Test summary with invalid level."""
        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(ValueError, match="Invalid level"):
            client.generate_summary("conv-123", "invalid")

    @responses.activate
    def test_generate_summary_weekly(self):
        """Test weekly summary generation."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/summarize",
            json={"summary": "Weekly summary", "level": "weekly"},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.generate_summary("conv-123", "weekly")
        assert result["level"] == "weekly"


class TestSuggestLabels:
    """Test AI label suggestions."""

    @responses.activate
    def test_suggest_labels_success(self):
        """Test successful label suggestions."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/labels/suggest",
            json={"suggestions": [
                {"label": "AI", "confidence": 0.95, "is_existing": True, "reason": "AI-related"},
                {"label": "ML", "confidence": 0.85, "is_existing": False, "reason": "ML content"}
            ]},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        results = client.suggest_labels("conv-123")
        
        assert len(results) == 2
        assert results[0]["label"] == "AI"
        assert results[0]["confidence"] == 0.95

    @responses.activate
    def test_suggest_labels_failure(self):
        """Test label suggestion with error."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/labels/suggest",
            status=500,
            body="Suggestion error"
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Label suggestion failed"):
            client.suggest_labels("conv-123")


class TestExecutePruning:
    """Test pruning execution."""

    @responses.activate
    def test_execute_pruning_success(self):
        """Test successful pruning execution."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/prune/execute",
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        client.execute_pruning(["conv-1", "conv-2", "conv-3"])  # Should not raise

    @responses.activate
    def test_execute_pruning_failure(self):
        """Test pruning execution with error."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/prune/execute",
            status=500,
            body="Prune error"
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Prune execution failed"):
            client.execute_pruning(["conv-1"])


class TestFolderOperations:
    """Test folder management."""

    @patch("sekha_cli.client.MemoryController")
    def test_list_folders(self, mock_controller_class):
        """Test listing folders."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller
        mock_controller.search.return_value = [
            {"id": "1", "folder": "/Work"},
            {"id": "2", "folder": "/Personal"},
            {"id": "3", "folder": "/Work"},
            {"id": "4", "folder": None},
        ]

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        folders = client.list_folders()
        
        assert len(folders) == 2
        assert "/Work" in folders
        assert "/Personal" in folders

    @responses.activate
    def test_move_conversation(self):
        """Test moving conversation to folder."""
        responses.add(
            responses.PUT,
            "http://test.com/api/v1/conversations/conv-123/folder",
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        client.move_conversation("conv-123", "/NewFolder")  # Should not raise

    @responses.activate
    def test_move_conversation_failure(self):
        """Test move with error."""
        responses.add(
            responses.PUT,
            "http://test.com/api/v1/conversations/conv-123/folder",
            status=404,
            body="Not found"
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Move conversation failed"):
            client.move_conversation("conv-123", "/NewFolder")


class TestHealthCheck:
    """Test health check functionality."""

    @responses.activate
    def test_health_check_success(self):
        """Test successful health check."""
        responses.add(
            responses.GET,
            "http://test.com/health",
            json={"status": "healthy", "version": "0.2.0", "uptime_seconds": 12345},
            status=200
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        result = client.health_check()
        
        assert result["status"] == "healthy"
        assert result["version"] == "0.2.0"

    @responses.activate
    def test_health_check_failure(self):
        """Test health check with error."""
        responses.add(
            responses.GET,
            "http://test.com/health",
            status=500
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Health check failed"):
            client.health_check()


class TestRebuildEmbeddings:
    """Test embeddings rebuild."""

    @responses.activate
    def test_rebuild_embeddings_success(self):
        """Test successful embeddings rebuild trigger."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/rebuild-embeddings",
            status=202  # Accepted
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        client.rebuild_embeddings()  # Should not raise

    @responses.activate
    def test_rebuild_embeddings_failure(self):
        """Test embeddings rebuild with error."""
        responses.add(
            responses.POST,
            "http://test.com/api/v1/rebuild-embeddings",
            status=500
        )

        client = SekhaClient(base_url="http://test.com", api_key="test-key")
        with pytest.raises(RuntimeError, match="Rebuild embeddings failed"):
            client.rebuild_embeddings()


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
