"""
Main MCP server implementation for Penpot.

This module defines the MCP server with resources and tools for interacting with
the Penpot design platform.
"""

import hashlib
import json
import os
import re
import argparse
import sys
from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP, Image

from penpot_mcp.api.penpot_api import PenpotAPI
from penpot_mcp.tools.penpot_tree import get_object_subtree_with_fields
from penpot_mcp.utils import config
from penpot_mcp.utils.cache import MemoryCache
from penpot_mcp.utils.http_server import ImageServer


class PenpotMCPServer:
    """Penpot MCP Server implementation."""

    def __init__(self, name="Penpot MCP Server", test_mode=False):
        """
        Initialize the Penpot MCP Server.

        Args:
            name: Server name
            test_mode: If True, certain features like HTTP server will be disabled for testing
        """
        # Initialize the MCP server
        self.mcp = FastMCP(name, instructions="""
I can help you generate code from your Penpot UI designs. My primary aim is to convert Penpot design components into functional code.

The typical workflow for code generation from Penpot designs is:

1. List your projects using 'list_projects' to find the project containing your designs
2. List files within the project using 'get_project_files' to locate the specific design file
3. Search for the target component within the file using 'search_object' to find the component you want to convert
4. Retrieve the Penpot tree schema using 'penpot_tree_schema' to understand which fields are available in the object tree
5. Get a cropped version of the object tree with a screenshot using 'get_object_tree' to see the component structure and visual representation
6. Get the full screenshot of the object using 'get_rendered_component' for detailed visual reference

For complex designs, you may need multiple iterations of 'get_object_tree' and 'get_rendered_component' due to LLM context limits.

Use the resources to access schemas, cached files, and rendered objects (screenshots) as needed.

Let me know which Penpot design you'd like to convert to code, and I'll guide you through the process!
""")

        # Initialize the Penpot API
        self.api = PenpotAPI(
            base_url=config.PENPOT_API_URL,
            debug=config.DEBUG
        )

        # Initialize memory cache
        self.file_cache = MemoryCache(ttl_seconds=600)  # 10 minutes

        # Storage for rendered component images
        self.rendered_components: Dict[str, Image] = {}
        
        # Initialize HTTP server for images if enabled and not in test mode
        self.image_server = None
        self.image_server_url = None
        
        # Detect if running in a test environment
        is_test_env = test_mode or 'pytest' in sys.modules
        
        if config.ENABLE_HTTP_SERVER and not is_test_env:
            try:
                self.image_server = ImageServer(
                    host=config.HTTP_SERVER_HOST,
                    port=config.HTTP_SERVER_PORT
                )
                # Start the server and get the URL with actual port assigned
                self.image_server_url = self.image_server.start()
                print(f"Image server started at {self.image_server_url}")
            except Exception as e:
                print(f"Warning: Failed to start image server: {str(e)}")

        # Register resources and tools
        if config.RESOURCES_AS_TOOLS:
            self._register_resources(resources_only=True)
            self._register_tools(include_resource_tools=True)
        else:
            self._register_resources(resources_only=False)
            self._register_tools(include_resource_tools=False)

    def _register_resources(self, resources_only=False):
        """Register all MCP resources. If resources_only is True, only register server://info as a resource."""
        @self.mcp.resource("server://info")
        def server_info() -> dict:
            """Provide information about the server."""
            info = {
                "status": "online",
                "name": "Penpot MCP Server",
                "description": "Model Context Provider for Penpot",
                "api_url": config.PENPOT_API_URL
            }
            
            if self.image_server and self.image_server.is_running:
                info["image_server"] = self.image_server_url
                
            return info
        if resources_only:
            return
        @self.mcp.resource("penpot://schema", mime_type="application/schema+json")
        def penpot_schema() -> dict:
            """Provide the Penpot API schema as JSON."""
            schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-schema.json')
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Failed to load schema: {str(e)}"}
        @self.mcp.resource("penpot://tree-schema", mime_type="application/schema+json")
        def penpot_tree_schema() -> dict:
            """Provide the Penpot object tree schema as JSON."""
            schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-tree-schema.json')
            try:
                with open(schema_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Failed to load tree schema: {str(e)}"}
        @self.mcp.resource("rendered-component://{component_id}", mime_type="image/png")
        def get_rendered_component(component_id: str) -> Image:
            """Return a rendered component image by its ID."""
            if component_id in self.rendered_components:
                return self.rendered_components[component_id]
            raise Exception(f"Component with ID {component_id} not found")
        @self.mcp.resource("penpot://cached-files")
        def get_cached_files() -> dict:
            """List all files currently stored in the cache."""
            return self.file_cache.get_all_cached_files()

    def _register_tools(self, include_resource_tools=False):
        """Register all MCP tools. If include_resource_tools is True, also register resource logic as tools."""
        @self.mcp.tool()
        def list_projects() -> dict:
            """Retrieve a list of all available Penpot projects."""
            try:
                projects = self.api.list_projects()
                return {"projects": projects}
            except Exception as e:
                return {"error": str(e)}
        @self.mcp.tool()
        def get_project_files(project_id: str) -> dict:
            """Get all files contained within a specific Penpot project.
            
            Args:
                project_id: The ID of the Penpot project
            """
            try:
                files = self.api.get_project_files(project_id)
                return {"files": files}
            except Exception as e:
                return {"error": str(e)}
        def get_cached_file(file_id: str) -> dict:
            """Internal helper to retrieve a file, using cache if available.
            
            Args:
                file_id: The ID of the Penpot file
            """
            cached_data = self.file_cache.get(file_id)
            if cached_data is not None:
                return cached_data
            try:
                file_data = self.api.get_file(file_id=file_id)
                self.file_cache.set(file_id, file_data)
                return file_data
            except Exception as e:
                return {"error": str(e)}
        @self.mcp.tool()
        def get_file(file_id: str) -> dict:
            """Retrieve a Penpot file by its ID and cache it. Don't use this tool for code generation, use 'get_object_tree' instead.
            
            Args:
                file_id: The ID of the Penpot file
            """
            try:
                file_data = self.api.get_file(file_id=file_id)
                self.file_cache.set(file_id, file_data)
                return file_data
            except Exception as e:
                return {"error": str(e)}
        @self.mcp.tool()
        def export_object(
                file_id: str,
                page_id: str,
                object_id: str,
                export_type: str = "png",
                scale: int = 1) -> Image:
            """Export a Penpot design object as an image.
            
            Args:
                file_id: The ID of the Penpot file
                page_id: The ID of the page containing the object
                object_id: The ID of the object to export
                export_type: Image format (png, svg, etc.)
                scale: Scale factor for the exported image
            """
            temp_filename = None
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                temp_filename = os.path.join(temp_dir, f"{object_id}.{export_type}")
                output_path = self.api.export_and_download(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id,
                    export_type=export_type,
                    scale=scale,
                    save_to_file=temp_filename
                )
                with open(output_path, "rb") as f:
                    file_content = f.read()
                    
                image = Image(data=file_content, format=export_type)
                
                # If HTTP server is enabled, add the image to the server
                if self.image_server and self.image_server.is_running:
                    image_id = hashlib.md5(f"{file_id}:{page_id}:{object_id}".encode()).hexdigest()
                    # Use the current image_server_url to ensure the correct port
                    image_url = self.image_server.add_image(image_id, file_content, export_type)
                    # Add HTTP URL to the image metadata
                    image.http_url = image_url
                    
                return image
            except Exception as e:
                raise Exception(f"Export failed: {str(e)}")
            finally:
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except Exception as e:
                        print(f"Warning: Failed to delete temporary file {temp_filename}: {str(e)}")
        @self.mcp.tool()
        def get_object_tree(
            file_id: str, 
            object_id: str, 
            fields: List[str],
            depth: int = -1,
            format: str = "json"
        ) -> dict:
            """Get the object tree structure for a Penpot object ("tree" field) with rendered screenshot image of the object ("image.mcp_uri" field).
            Args:
                file_id: The ID of the Penpot file
                object_id: The ID of the object to retrieve
                fields: Specific fields to include in the tree (call "penpot_tree_schema" resource/tool for available fields)
                depth: How deep to traverse the object tree (-1 for full depth)
                format: Output format ('json' or 'yaml')
            """
            try:
                file_data = get_cached_file(file_id)
                if "error" in file_data:
                    return file_data
                result = get_object_subtree_with_fields(
                    file_data, 
                    object_id, 
                    include_fields=fields,
                    depth=depth
                )
                if "error" in result:
                    return result
                simplified_tree = result["tree"]
                page_id = result["page_id"]
                final_result = {"tree": simplified_tree}
                
                try:
                    image = export_object(
                        file_id=file_id,
                        page_id=page_id,
                        object_id=object_id
                    )
                    image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                    self.rendered_components[image_id] = image
                    
                    # Image URI preferences:
                    # 1. HTTP server URL if available
                    # 2. Fallback to MCP resource URI
                    image_uri = f"render_component://{image_id}"
                    if hasattr(image, 'http_url'):
                        final_result["image"] = {
                            "uri": image.http_url,
                            "mcp_uri": image_uri,
                            "format": image.format if hasattr(image, 'format') else "png"
                        }
                    else:
                        final_result["image"] = {
                            "uri": image_uri,
                            "format": image.format if hasattr(image, 'format') else "png"
                        }
                except Exception as e:
                    final_result["image_error"] = str(e)
                if format.lower() == "yaml":
                    try:
                        import yaml
                        yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                        return {"yaml_result": yaml_result}
                    except ImportError:
                        return {"format_error": "YAML format requested but PyYAML package is not installed"}
                    except Exception as e:
                        return {"format_error": f"Error formatting as YAML: {str(e)}"}
                return final_result
            except Exception as e:
                return {"error": str(e)}
        @self.mcp.tool()
        def search_object(file_id: str, query: str) -> dict:
            """Search for objects within a Penpot file by name.
            
            Args:
                file_id: The ID of the Penpot file to search in
                query: Search string (supports regex patterns)
            """
            try:
                file_data = get_cached_file(file_id)
                if "error" in file_data:
                    return file_data
                pattern = re.compile(query, re.IGNORECASE)
                matches = []
                data = file_data.get('data', {})
                for page_id, page_data in data.get('pagesIndex', {}).items():
                    page_name = page_data.get('name', 'Unnamed')
                    for obj_id, obj_data in page_data.get('objects', {}).items():
                        obj_name = obj_data.get('name', '')
                        if pattern.search(obj_name):
                            matches.append({
                                'id': obj_id,
                                'name': obj_name,
                                'page_id': page_id,
                                'page_name': page_name,
                                'object_type': obj_data.get('type', 'unknown')
                            })
                return {'objects': matches}
            except Exception as e:
                return {"error": str(e)}
        if include_resource_tools:
            @self.mcp.tool()
            def penpot_schema() -> dict:
                """Provide the Penpot API schema as JSON."""
                schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-schema.json')
                try:
                    with open(schema_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    return {"error": f"Failed to load schema: {str(e)}"}
            @self.mcp.tool()
            def penpot_tree_schema() -> dict:
                """Provide the Penpot object tree schema as JSON."""
                schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-tree-schema.json')
                try:
                    with open(schema_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    return {"error": f"Failed to load tree schema: {str(e)}"}
            @self.mcp.tool()
            def get_rendered_component(component_id: str) -> Image:
                """Return a rendered component image by its ID."""
                if component_id in self.rendered_components:
                    return self.rendered_components[component_id]
                raise Exception(f"Component with ID {component_id} not found")
            @self.mcp.tool()
            def get_cached_files() -> dict:
                """List all files currently stored in the cache."""
                return self.file_cache.get_all_cached_files()

    def run(self, port=None, debug=None, mode=None):
        """
        Run the MCP server.

        Args:
            port: Port to run on (overrides config) - only used in 'sse' mode
            debug: Debug mode (overrides config)
            mode: MCP mode ('stdio' or 'sse', overrides config)
        """
        # Use provided values or fall back to config
        debug = debug if debug is not None else config.DEBUG
        
        # Get mode from parameter, environment variable, or default to stdio
        mode = mode or os.environ.get('MODE', 'stdio')
        
        # Validate mode
        if mode not in ['stdio', 'sse']:
            print(f"Invalid mode: {mode}. Using stdio mode.")
            mode = 'stdio'

        if mode == 'sse':
            print(f"Starting Penpot MCP Server on port {port} (debug={debug}, mode={mode})")
        else:
            print(f"Starting Penpot MCP Server (debug={debug}, mode={mode})")
            
        # Start HTTP server if enabled and not already running
        if config.ENABLE_HTTP_SERVER and self.image_server and not self.image_server.is_running:
            try:
                self.image_server_url = self.image_server.start()
            except Exception as e:
                print(f"Warning: Failed to start image server: {str(e)}")
            
        self.mcp.run(mode)


def create_server():
    """Create and configure a new server instance."""
    # Detect if running in a test environment
    is_test_env = 'pytest' in sys.modules
    return PenpotMCPServer(test_mode=is_test_env)


# Create a global server instance with a standard name for the MCP tool
server = create_server()


def main():
    """Entry point for the console script."""
    parser = argparse.ArgumentParser(description='Run the Penpot MCP Server')
    parser.add_argument('--port', type=int, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--mode', choices=['stdio', 'sse'], default=os.environ.get('MODE', 'stdio'),
                       help='MCP mode (stdio or sse)')
    
    args = parser.parse_args()
    server.run(port=args.port, debug=args.debug, mode=args.mode)


if __name__ == "__main__":
    main()
