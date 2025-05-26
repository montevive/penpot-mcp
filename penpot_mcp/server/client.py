"""Client for connecting to the Penpot MCP server."""

import asyncio
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class PenpotMCPClient:
    """Client for interacting with the Penpot MCP server."""

    def __init__(self, server_command="python", server_args=None, env=None):
        """
        Initialize the Penpot MCP client.

        Args:
            server_command: The command to run the server
            server_args: Arguments to pass to the server command
            env: Environment variables for the server process
        """
        self.server_command = server_command
        self.server_args = server_args or ["-m", "penpot_mcp.server.mcp_server"]
        self.env = env
        self.session = None

    async def connect(self):
        """
        Connect to the MCP server.

        Returns:
            The client session
        """
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command=self.server_command,
            args=self.server_args,
            env=self.env,
        )

        # Connect to the server
        read, write = await stdio_client(server_params).__aenter__()
        self.session = await ClientSession(read, write).__aenter__()

        # Initialize the connection
        await self.session.initialize()

        return self.session

    async def disconnect(self):
        """Disconnect from the server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources from the server.

        Returns:
            List of resource information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        return await self.session.list_resources()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the server.

        Returns:
            List of tool information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        return await self.session.list_tools()

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.

        Returns:
            Server information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        info, _ = await self.session.read_resource("server://info")
        return info

    async def list_projects(self) -> Dict[str, Any]:
        """
        List Penpot projects.

        Returns:
            Project information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        return await self.session.call_tool("list_projects")

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get details for a specific project.

        Args:
            project_id: The project ID

        Returns:
            Project information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        return await self.session.call_tool("get_project", {"project_id": project_id})

    async def get_project_files(self, project_id: str) -> Dict[str, Any]:
        """
        Get files for a specific project.

        Args:
            project_id: The project ID

        Returns:
            File information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        return await self.session.call_tool("get_project_files", {"project_id": project_id})

    async def get_file(self, file_id: str, features: Optional[List[str]] = None,
                       project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details for a specific file.

        Args:
            file_id: The file ID
            features: List of features to include
            project_id: Optional project ID

        Returns:
            File information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        params = {"file_id": file_id}
        if features:
            params["features"] = features
        if project_id:
            params["project_id"] = project_id

        return await self.session.call_tool("get_file", params)

    async def get_components(self) -> Dict[str, Any]:
        """
        Get components from the server.

        Returns:
            Component information
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        components, _ = await self.session.read_resource("content://components")
        return components

    async def export_object(self, file_id: str, page_id: str, object_id: str,
                            export_type: str = "png", scale: int = 1,
                            save_to_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Export an object from a Penpot file.

        Args:
            file_id: The ID of the file containing the object
            page_id: The ID of the page containing the object
            object_id: The ID of the object to export
            export_type: Export format (png, svg, pdf)
            scale: Scale factor for the export
            save_to_file: Optional path to save the exported file

        Returns:
            If save_to_file is None: Dictionary with the exported image data
            If save_to_file is provided: Dictionary with the saved file path
        """
        if not self.session:
            raise RuntimeError("Not connected to server")

        params = {
            "file_id": file_id,
            "page_id": page_id,
            "object_id": object_id,
            "export_type": export_type,
            "scale": scale
        }

        result = await self.session.call_tool("export_object", params)

        # The result is now directly an Image object which has 'data' and 'format' fields

        # If the client wants to save the file
        if save_to_file:
            import os

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_to_file)), exist_ok=True)

            # Save to file
            with open(save_to_file, "wb") as f:
                f.write(result["data"])

            return {"file_path": save_to_file, "format": result.get("format")}

        # Otherwise return the result as is
        return result


async def run_client_example():
    """Run a simple example using the client."""
    # Create and connect the client
    client = PenpotMCPClient()
    await client.connect()

    try:
        # Get server info
        print("Getting server info...")
        server_info = await client.get_server_info()
        print(f"Server info: {server_info}")

        # List projects
        print("\nListing projects...")
        projects_result = await client.list_projects()
        if "error" in projects_result:
            print(f"Error: {projects_result['error']}")
        else:
            projects = projects_result.get("projects", [])
            print(f"Found {len(projects)} projects:")
            for project in projects[:5]:  # Show first 5 projects
                print(f"- {project.get('name', 'Unknown')} (ID: {project.get('id', 'N/A')})")

        # Example of exporting an object (uncomment and update with actual IDs to test)
        """
        print("\nExporting object...")
        # Replace with actual IDs from your Penpot account
        export_result = await client.export_object(
            file_id="your-file-id",
            page_id="your-page-id",
            object_id="your-object-id",
            export_type="png",
            scale=2,
            save_to_file="exported_object.png"
        )
        print(f"Export saved to: {export_result.get('file_path')}")

        # Or get the image data directly without saving
        image_data = await client.export_object(
            file_id="your-file-id",
            page_id="your-page-id",
            object_id="your-object-id"
        )
        print(f"Received image in format: {image_data.get('format')}")
        print(f"Image size: {len(image_data.get('data'))} bytes")
        """
    finally:
        # Disconnect from the server
        await client.disconnect()


def main():
    """Run the client example."""
    asyncio.run(run_client_example())


if __name__ == "__main__":
    main()
