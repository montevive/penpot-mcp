"""Configuration module for the Penpot MCP server."""

import os

from dotenv import find_dotenv, load_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Server configuration
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'true').lower() == 'true'
RESOURCES_AS_TOOLS = os.environ.get('RESOURCES_AS_TOOLS', 'true').lower() == 'true'

# HTTP server for exported images
ENABLE_HTTP_SERVER = os.environ.get('ENABLE_HTTP_SERVER', 'true').lower() == 'true'
HTTP_SERVER_HOST = os.environ.get('HTTP_SERVER_HOST', 'localhost')
HTTP_SERVER_PORT = int(os.environ.get('HTTP_SERVER_PORT', 0))

# Penpot API configuration
PENPOT_API_URL = os.environ.get('PENPOT_API_URL', 'https://design.penpot.app/api')
PENPOT_USERNAME = os.environ.get('PENPOT_USERNAME')
PENPOT_PASSWORD = os.environ.get('PENPOT_PASSWORD')

RESOURCES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources')
