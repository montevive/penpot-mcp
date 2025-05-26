"""Test configuration for Penpot MCP tests."""

import os
from unittest.mock import MagicMock

import pytest

from penpot_mcp.api.penpot_api import PenpotAPI
from penpot_mcp.server.mcp_server import PenpotMCPServer

# Add the project root directory to the Python path
os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def mock_penpot_api(monkeypatch):
    """Create a mock PenpotAPI object."""
    mock_api = MagicMock(spec=PenpotAPI)
    # Add default behavior to the mock
    mock_api.list_projects.return_value = [
        {"id": "project1", "name": "Test Project 1"},
        {"id": "project2", "name": "Test Project 2"}
    ]
    mock_api.get_project_files.return_value = [
        {"id": "file1", "name": "Test File 1"},
        {"id": "file2", "name": "Test File 2"}
    ]
    mock_api.get_file.return_value = {
        "id": "file1",
        "name": "Test File",
        "data": {
            "pages": [
                {
                    "id": "page1",
                    "name": "Page 1",
                    "objects": {
                        "obj1": {"id": "obj1", "name": "Object 1", "type": "frame"},
                        "obj2": {"id": "obj2", "name": "Object 2", "type": "text"}
                    }
                }
            ]
        }
    }
    return mock_api


@pytest.fixture
def mock_server(mock_penpot_api):
    """Create a mock PenpotMCPServer with a mock API."""
    server = PenpotMCPServer(name="Test Server")
    server.api = mock_penpot_api
    return server
