"""Tests for config module."""

from penpot_mcp.utils import config


def test_config_values():
    """Test that config has the expected values and types."""
    assert isinstance(config.PORT, int)
    assert isinstance(config.DEBUG, bool)
    assert isinstance(config.PENPOT_API_URL, str)
    assert config.RESOURCES_PATH is not None


def test_environment_variable_override(monkeypatch):
    """Test that environment variables override default config values."""
    # Save original values
    original_port = config.PORT
    original_debug = config.DEBUG
    original_api_url = config.PENPOT_API_URL

    # Override with environment variables
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("PENPOT_API_URL", "https://test.example.com/api")

    # Reload the config module to apply the environment variables
    import importlib
    importlib.reload(config)

    # Check the new values
    assert config.PORT == 8080
    assert config.DEBUG is False
    assert config.PENPOT_API_URL == "https://test.example.com/api"

    # Restore original values
    monkeypatch.setattr(config, "PORT", original_port)
    monkeypatch.setattr(config, "DEBUG", original_debug)
    monkeypatch.setattr(config, "PENPOT_API_URL", original_api_url)
