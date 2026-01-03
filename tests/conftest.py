"""Pytest configuration and shared fixtures."""
import pytest


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    monkeypatch.delenv("SEKHA_BASE_URL", raising=False)
    monkeypatch.delenv("SEKHA_API_KEY", raising=False)
