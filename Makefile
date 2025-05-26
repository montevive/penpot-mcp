# Makefile for Penpot MCP
.PHONY: mcp-server mcp-inspector mcp-server-sse

# Default port for MCP server
PORT ?= 5000
# Default mode is stdio (can be overridden by environment variable MODE)
MODE ?= stdio

# Launch MCP server with configurable mode (stdio or sse)
mcp-server:
	python -m penpot_mcp.server.mcp_server --mode $(MODE)

# Launch MCP server specifically in SSE mode
mcp-server-sse:
	MODE=sse python -m penpot_mcp.server.mcp_server

# Launch MCP inspector - requires the server to be running in sse mode
mcp-inspector:
	npx @modelcontextprotocol/inspector

# Run both server (in sse mode) and inspector (server in background)
all:
	MODE=sse python -m penpot_mcp.server.mcp_server & \
	npx @modelcontextprotocol/inspector 