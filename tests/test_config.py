"""Test configuration management."""
import pytest
import os
import tempfile
from pathlib import Path
from sekha_cli.config import Config


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestConfigLoading:
    """Test configuration loading."""

    def test_load_config(self, temp_config_dir):
        """Test loading configuration file."""
        config_file = temp_config_dir / 'config.toml'
        config_file.write_text('''
[sekha]
base_url = "http://localhost:8080"
api_key = "test-key"
''')

        config = Config.load(config_file)
        assert config.base_url == "http://localhost:8080"
        assert config.api_key == "test-key"

    def test_load_nonexistent_config(self, temp_config_dir):
        """Test loading nonexistent configuration."""
        config_file = temp_config_dir / 'nonexistent.toml'

        with pytest.raises(FileNotFoundError):
            Config.load(config_file)

    def test_create_default_config(self, temp_config_dir):
        """Test creating default configuration."""
        config_file = temp_config_dir / 'config.toml'

        Config.create_default(config_file)

        assert config_file.exists()
        config = Config.load(config_file)
        assert config.base_url is not None


class TestConfigSaving:
    """Test configuration saving."""

    def test_save_config(self, temp_config_dir):
        """Test saving configuration."""
        config_file = temp_config_dir / 'config.toml'

        config = Config(
            base_url='http://example.com',
            api_key='new-key-123'
        )
        config.save(config_file)

        assert config_file.exists()
        loaded = Config.load(config_file)
        assert loaded.base_url == 'http://example.com'
        assert loaded.api_key == 'new-key-123'

    def test_update_config(self, temp_config_dir):
        """Test updating existing configuration."""
        config_file = temp_config_dir / 'config.toml'

        # Create initial config
        config = Config(base_url='http://localhost:8080', api_key='key1')
        config.save(config_file)

        # Update config
        config.api_key = 'key2'
        config.save(config_file)

        # Verify update
        loaded = Config.load(config_file)
        assert loaded.api_key == 'key2'


class TestConfigValidation:
    """Test configuration validation."""

    def test_valid_url(self):
        """Test valid URL validation."""
        config = Config(
            base_url='http://localhost:8080',
            api_key='key'
        )
        assert config.is_valid()

    def test_invalid_url(self):
        """Test invalid URL validation."""
        with pytest.raises(ValueError):
            Config(base_url='not-a-url', api_key='key')

    def test_missing_api_key(self):
        """Test missing API key validation."""
        config = Config(base_url='http://localhost:8080', api_key='')
        assert not config.is_valid()