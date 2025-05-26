# Using Penpot MCP with Claude

This guide explains how to integrate the Penpot MCP server with Claude AI using the Model Context Protocol (MCP).

## Prerequisites

1. Claude Desktop application installed
2. Penpot MCP server set up and configured

## Installing the Penpot MCP Server in Claude Desktop

The easiest way to use the Penpot MCP server with Claude is to install it directly in Claude Desktop:

1. Make sure you have installed the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install the MCP server in Claude Desktop:
   ```bash
   mcp install mcp_server.py
   ```

3. Claude will ask for your permission to install the server. Click "Allow".

4. The Penpot MCP server will now appear in Claude's tool menu.

## Using Penpot in Claude

Once installed, you can interact with Penpot through Claude by:

1. Open Claude Desktop
2. Click on the "+" button in the message input area
3. Select "Penpot MCP Server" from the list
4. Claude now has access to your Penpot projects and can:
   - List your projects
   - Get project details
   - Access file information
   - View components

## Example Prompts for Claude

Here are some example prompts you can use with Claude to interact with your Penpot data:

### Listing Projects

```
Can you show me a list of my Penpot projects?
```

### Getting Project Details

```
Please show me the details of my most recent Penpot project.
```

### Working with Files

```
Can you list the files in my "Website Redesign" project?
```

### Exploring Components

```
Please show me the available UI components in Penpot.
```

## Troubleshooting

If you encounter issues:

1. Check that your Penpot access token is correctly set in the environment variables
2. Verify that the Penpot API URL is correct
3. Try reinstalling the MCP server in Claude Desktop:
   ```bash
   mcp uninstall "Penpot MCP Server"
   mcp install mcp_server.py
   ```

## Advanced: Using with Other MCP-compatible Tools

The Penpot MCP server can be used with any MCP-compatible client, not just Claude Desktop. Other integrations include:

- OpenAI Agents SDK
- PydanticAI
- Python MCP clients (see `example_client.py`)

Refer to the specific documentation for these tools for integration instructions.

## Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- [Claude Developer Documentation](https://docs.anthropic.com)
- [MCP Python SDK Documentation](https://github.com/modelcontextprotocol/python-sdk) 