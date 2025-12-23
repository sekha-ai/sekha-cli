"""Pytest configuration and shared fixtures."""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Isolate configuration for each test."""
    config_dir = tmp_path / '.sekha'
    config_dir.mkdir()
    monkeypatch.setenv('SEKHA_CONFIG_DIR', str(config_dir))
    return config_dir


@pytest.fixture
def mock_controller_url():
    """Provide mock controller URL."""
    return 'http://localhost:8080'


@pytest.fixture
def mock_api_key():
    """Provide mock API key."""
    return 'test-key-12345678901234567890123456789012'


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    monkeypatch.delenv('SEKHA_BASE_URL', raising=False)
    monkeypatch.delenv('SEKHA_API_KEY', raising=False)