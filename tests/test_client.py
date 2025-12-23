"""Test Sekha client functionality."""
import pytest
from unittest.mock import Mock, patch
from sekha_cli.client import SekhaClient


@pytest.fixture
def client():
    """Create test client."""
    return SekhaClient(
        base_url='http://localhost:8080',
        api_key='test-key-123'
    )


class TestClientInitialization:
    """Test client initialization."""

    def test_init_with_params(self):
        """Test initialization with parameters."""
        client = SekhaClient(
            base_url='http://example.com',
            api_key='key-123'
        )
        assert client.base_url == 'http://example.com'
        assert client.api_key == 'key-123'

    def test_init_default_url(self):
        """Test initialization with default URL."""
        client = SekhaClient(api_key='key-123')
        assert 'localhost' in client.base_url or client.base_url


class TestConversationOperations:
    """Test conversation operations."""

    @patch('requests.post')
    def test_create_conversation(self, mock_post, client):
        """Test creating a conversation."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {'id': 'conv-123', 'label': 'Test'}
        )

        result = client.conversations.create(
            label='Test Conversation',
            messages=[{'role': 'user', 'content': 'Hello'}]
        )

        assert result['id'] == 'conv-123'
        mock_post.assert_called_once()

    @patch('requests.get')
    def test_list_conversations(self, mock_get, client):
        """Test listing conversations."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'conversations': [
                    {'id': 'conv-1', 'label': 'Conv 1'},
                    {'id': 'conv-2', 'label': 'Conv 2'}
                ]
            }
        )

        result = client.conversations.list(limit=10)

        assert len(result) == 2
        assert result[0]['id'] == 'conv-1'
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_get_conversation(self, mock_get, client):
        """Test getting a specific conversation."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {'id': 'conv-123', 'label': 'Test'}
        )

        result = client.conversations.get('conv-123')

        assert result['id'] == 'conv-123'
        mock_get.assert_called_once()


class TestSearchOperations:
    """Test search operations."""

    @patch('requests.post')
    def test_query(self, mock_post, client):
        """Test semantic search query."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'results': [
                    {'conversation_id': 'conv-1', 'content': 'Result 1'}
                ]
            }
        )

        result = client.query('test search', limit=5)

        assert 'results' in result
        assert len(result['results']) == 1
        mock_post.assert_called_once()


class TestErrorHandling:
    """Test error handling."""

    @patch('requests.get')
    def test_404_error(self, mock_get, client):
        """Test handling 404 errors."""
        mock_get.return_value = Mock(status_code=404)

        with pytest.raises(Exception):
            client.conversations.get('nonexistent')

    @patch('requests.post')
    def test_connection_error(self, mock_post, client):
        """Test handling connection errors."""
        mock_post.side_effect = ConnectionError('Connection failed')

        with pytest.raises(ConnectionError):
            client.conversations.create(
                label='Test',
                messages=[{'role': 'user', 'content': 'Hi'}]
            )

    @patch('requests.get')
    def test_auth_error(self, mock_get, client):
        """Test handling authentication errors."""
        mock_get.return_value = Mock(status_code=401)

        with pytest.raises(Exception):
            client.conversations.list()
