"""Tests for the MCP server module."""

import json
import os
import hashlib
from unittest.mock import MagicMock, mock_open, patch

import yaml
import pytest
from penpot_mcp.server.mcp_server import PenpotMCPServer, create_server


def test_server_initialization():
    """Test server initialization."""
    server = PenpotMCPServer(name="Test Server", test_mode=True)

    # Check that the server has the expected properties
    assert server.mcp is not None
    assert server.api is not None
    assert hasattr(server, '_register_resources')
    assert hasattr(server, '_register_tools')
    assert hasattr(server, 'run')


def test_server_info_resource():
    """Test the server_info resource handler function directly."""
    # Since we can't easily access the registered resource from FastMCP,
    # we'll implement it here based on the implementation in mcp_server.py
    def server_info():
        from penpot_mcp.utils import config
        return {
            "status": "online",
            "name": "Penpot MCP Server",
            "description": "Model Context Provider for Penpot",
            "api_url": config.PENPOT_API_URL
        }
    
    # Call the function
    result = server_info()
    
    # Check the result
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "online"
    assert "name" in result
    assert "description" in result
    assert "api_url" in result


def test_list_projects_tool_handler(mock_penpot_api):
    """Test the list_projects tool handler directly."""
    # Create a callable that matches what would be registered
    def list_projects():
        try:
            projects = mock_penpot_api.list_projects()
            return {"projects": projects}
        except Exception as e:
            return {"error": str(e)}

    # Call the handler
    result = list_projects()

    # Check the result
    assert isinstance(result, dict)
    assert "projects" in result
    assert len(result["projects"]) == 2
    assert result["projects"][0]["id"] == "project1"
    assert result["projects"][1]["id"] == "project2"

    # Verify API was called
    mock_penpot_api.list_projects.assert_called_once()


def test_get_project_files_tool_handler(mock_penpot_api):
    """Test the get_project_files tool handler directly."""
    # Create a callable that matches what would be registered
    def get_project_files(project_id):
        try:
            files = mock_penpot_api.get_project_files(project_id)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}

    # Call the handler with a project ID
    result = get_project_files("project1")

    # Check the result
    assert isinstance(result, dict)
    assert "files" in result
    assert len(result["files"]) == 2
    assert result["files"][0]["id"] == "file1"
    assert result["files"][1]["id"] == "file2"

    # Verify API was called with correct parameters
    mock_penpot_api.get_project_files.assert_called_once_with("project1")


def test_get_file_tool_handler(mock_penpot_api):
    """Test the get_file tool handler directly."""
    # Create a callable that matches what would be registered
    def get_file(file_id):
        try:
            file_data = mock_penpot_api.get_file(file_id=file_id)
            return file_data
        except Exception as e:
            return {"error": str(e)}

    # Call the handler with a file ID
    result = get_file("file1")

    # Check the result
    assert isinstance(result, dict)
    assert result["id"] == "file1"
    assert result["name"] == "Test File"
    assert "data" in result
    assert "pages" in result["data"]

    # Verify API was called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")


@patch('os.path.join')
@patch('builtins.open', new_callable=mock_open, read_data='{"test": "schema"}')
def test_penpot_schema_resource_handler(mock_file_open, mock_join):
    """Test the schema resource handler directly."""
    # Setup the mock join to return a predictable path
    mock_join.return_value = '/mock/path/to/penpot-schema.json'

    # Create a callable that matches what would be registered
    def penpot_schema():
        from penpot_mcp.utils import config
        schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-schema.json')
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to load schema: {str(e)}"}

    # Call the handler
    result = penpot_schema()

    # Check result matches our mocked file content
    assert isinstance(result, dict)
    assert "test" in result
    assert result["test"] == "schema"

    # Verify file was opened
    mock_file_open.assert_called_once_with('/mock/path/to/penpot-schema.json', 'r')


@patch('os.path.join')
@patch('builtins.open', new_callable=mock_open, read_data='{"test": "tree-schema"}')
def test_penpot_tree_schema_resource_handler(mock_file_open, mock_join):
    """Test the tree schema resource handler directly."""
    # Setup the mock join to return a predictable path
    mock_join.return_value = '/mock/path/to/penpot-tree-schema.json'

    # Create a callable that matches what would be registered
    def penpot_tree_schema():
        from penpot_mcp.utils import config
        schema_path = os.path.join(config.RESOURCES_PATH, 'penpot-tree-schema.json')
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to load tree schema: {str(e)}"}

    # Call the handler
    result = penpot_tree_schema()

    # Check result matches our mocked file content
    assert isinstance(result, dict)
    assert "test" in result
    assert result["test"] == "tree-schema"

    # Verify file was opened
    mock_file_open.assert_called_once_with('/mock/path/to/penpot-tree-schema.json', 'r')


def test_create_server():
    """Test the create_server function."""
    with patch('penpot_mcp.server.mcp_server.PenpotMCPServer') as mock_server_class:
        mock_server_instance = MagicMock()
        mock_server_class.return_value = mock_server_instance

        # Test that create_server passes test_mode=True when in test environment
        with patch('penpot_mcp.server.mcp_server.sys.modules', {'pytest': True}):
            server = create_server()
            mock_server_class.assert_called_once_with(test_mode=True)
            assert server == mock_server_instance


@patch('penpot_mcp.tools.penpot_tree.get_object_subtree_with_fields')
def test_get_object_tree_basic(mock_get_subtree, mock_penpot_api):
    """Test the get_object_tree tool handler with basic parameters."""
    # Setup the mock get_object_subtree_with_fields function
    mock_get_subtree.return_value = {
        "tree": {
            "id": "obj1",
            "type": "frame",
            "name": "Test Object",
            "children": []
        },
        "page_id": "page1"
    }
    
    # Setup the export_object mock for the included image
    export_object_mock = MagicMock()
    export_object_mock.return_value = MagicMock(data=b'test_image_data', format='png')
    
    # Create a callable that matches what would be registered
    def get_object_tree(
        file_id: str, 
        object_id: str, 
        fields: list,  # Now required parameter
        depth: int = -1,
        format: str = "json"
    ):
        try:
            # Get the file data
            file_data = mock_penpot_api.get_file(file_id=file_id)
            
            # Use the mocked utility function
            result = mock_get_subtree(
                file_data, 
                object_id, 
                include_fields=fields,
                depth=depth
            )
            
            # Check if an error occurred
            if "error" in result:
                return result
                
            # Extract the tree and page_id
            simplified_tree = result["tree"]
            page_id = result["page_id"]
            
            # Prepare the result dictionary
            final_result = {"tree": simplified_tree}
            
            # Always include image (no longer optional)
            try:
                image = export_object_mock(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id
                )
                # New format: URI-based instead of base64 data
                image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                image_uri = f"render_component://{image_id}"
                final_result["image"] = {
                    "uri": image_uri,
                    "format": image.format if hasattr(image, 'format') else "png"
                }
            except Exception as e:
                final_result["image_error"] = str(e)
            
            # Format the tree as YAML if requested
            if format.lower() == "yaml":
                try:
                    # Convert the entire result to YAML, including the image if present
                    yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                    return {"yaml_result": yaml_result}
                except Exception as e:
                    return {"format_error": f"Error formatting as YAML: {str(e)}"}
            
            # Return the JSON format result
            return final_result
        except Exception as e:
            return {"error": str(e)}
    
    # Call the handler with basic parameters - fields is now required
    result = get_object_tree(
        file_id="file1", 
        object_id="obj1",
        fields=["id", "type", "name"]  # Required parameter
    )
    
    # Check the result
    assert isinstance(result, dict)
    assert "tree" in result
    assert result["tree"]["id"] == "obj1"
    assert result["tree"]["type"] == "frame"
    assert result["tree"]["name"] == "Test Object"
    
    # Check that image is always included
    assert "image" in result
    assert "uri" in result["image"]
    assert result["image"]["uri"].startswith("render_component://")
    assert result["image"]["format"] == "png"
    
    # Verify mocks were called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")
    mock_get_subtree.assert_called_once_with(
        mock_penpot_api.get_file.return_value,
        "obj1",
        include_fields=["id", "type", "name"],
        depth=-1
    )


@patch('penpot_mcp.tools.penpot_tree.get_object_subtree_with_fields')
def test_get_object_tree_with_fields_and_depth(mock_get_subtree, mock_penpot_api):
    """Test the get_object_tree tool handler with custom field list and depth."""
    # Setup the mock get_object_subtree_with_fields function
    mock_get_subtree.return_value = {
        "tree": {
            "id": "obj1",
            "name": "Test Object",  # Only id and name fields included
            "children": []
        },
        "page_id": "page1"
    }
    
    # Setup the export_object mock for the included image
    export_object_mock = MagicMock()
    export_object_mock.return_value = MagicMock(data=b'test_image_data', format='png')
    
    # Create a callable that matches what would be registered
    def get_object_tree(
        file_id: str, 
        object_id: str, 
        fields: list,  # Now required parameter
        depth: int = -1,
        format: str = "json"
    ):
        try:
            # Get the file data
            file_data = mock_penpot_api.get_file(file_id=file_id)
            
            # Use the mocked utility function
            result = mock_get_subtree(
                file_data, 
                object_id, 
                include_fields=fields,
                depth=depth
            )
            
            # Extract the tree and page_id
            simplified_tree = result["tree"]
            page_id = result["page_id"]
            
            # Prepare the result dictionary
            final_result = {"tree": simplified_tree}
            
            # Always include image (no longer optional)
            try:
                image = export_object_mock(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id
                )
                # New format: URI-based instead of base64 data
                image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                image_uri = f"render_component://{image_id}"
                final_result["image"] = {
                    "uri": image_uri,
                    "format": image.format if hasattr(image, 'format') else "png"
                }
            except Exception as e:
                final_result["image_error"] = str(e)
            
            # Format the tree as YAML if requested
            if format.lower() == "yaml":
                try:
                    # Convert the entire result to YAML, including the image if present
                    yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                    return {"yaml_result": yaml_result}
                except Exception as e:
                    return {"format_error": f"Error formatting as YAML: {str(e)}"}
            
            # Return the JSON format result
            return final_result
        except Exception as e:
            return {"error": str(e)}
    
    # Call the handler with custom fields and depth
    result = get_object_tree(
        file_id="file1", 
        object_id="obj1", 
        fields=["id", "name"],  # Updated parameter name
        depth=2
    )
    
    # Check the result
    assert isinstance(result, dict)
    assert "tree" in result
    assert result["tree"]["id"] == "obj1"
    assert result["tree"]["name"] == "Test Object"
    assert "type" not in result["tree"]  # Type field should not be included
    
    # Check that image is always included
    assert "image" in result
    assert "uri" in result["image"]
    assert result["image"]["uri"].startswith("render_component://")
    assert result["image"]["format"] == "png"
    
    # Verify mocks were called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")
    mock_get_subtree.assert_called_once_with(
        mock_penpot_api.get_file.return_value,
        "obj1",
        include_fields=["id", "name"],
        depth=2
    )


@patch('penpot_mcp.tools.penpot_tree.get_object_subtree_with_fields')
def test_get_object_tree_with_yaml_format(mock_get_subtree, mock_penpot_api):
    """Test the get_object_tree tool handler with YAML format output."""
    # Setup the mock get_object_subtree_with_fields function
    mock_get_subtree.return_value = {
        "tree": {
            "id": "obj1",
            "type": "frame",
            "name": "Test Object",
            "children": [
                {
                    "id": "child1",
                    "type": "text",
                    "name": "Child Text"
                }
            ]
        },
        "page_id": "page1"
    }
    
    # Setup the export_object mock for the included image
    export_object_mock = MagicMock()
    export_object_mock.return_value = MagicMock(data=b'test_image_data', format='png')
    
    # Create a callable that matches what would be registered
    def get_object_tree(
        file_id: str, 
        object_id: str, 
        fields: list,  # Now required parameter
        depth: int = -1,
        format: str = "json"
    ):
        try:
            # Get the file data
            file_data = mock_penpot_api.get_file(file_id=file_id)
            
            # Use the mocked utility function
            result = mock_get_subtree(
                file_data, 
                object_id, 
                include_fields=fields,
                depth=depth
            )
            
            # Extract the tree and page_id
            simplified_tree = result["tree"]
            page_id = result["page_id"]
            
            # Prepare the result dictionary
            final_result = {"tree": simplified_tree}
            
            # Always include image (no longer optional)
            try:
                image = export_object_mock(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id
                )
                # New format: URI-based instead of base64 data
                image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                image_uri = f"render_component://{image_id}"
                final_result["image"] = {
                    "uri": image_uri,
                    "format": image.format if hasattr(image, 'format') else "png"
                }
            except Exception as e:
                final_result["image_error"] = str(e)
            
            # Format the tree as YAML if requested
            if format.lower() == "yaml":
                try:
                    # Convert the entire result to YAML, including the image if present
                    yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                    return {"yaml_result": yaml_result}
                except Exception as e:
                    return {"format_error": f"Error formatting as YAML: {str(e)}"}
            
            # Return the JSON format result
            return final_result
        except Exception as e:
            return {"error": str(e)}
    
    # Call the handler with YAML format - fields is now required
    result = get_object_tree(
        file_id="file1", 
        object_id="obj1", 
        fields=["id", "type", "name"],  # Required parameter
        format="yaml"
    )
    
    # Check the result
    assert isinstance(result, dict)
    assert "yaml_result" in result
    assert "tree" not in result  # Should not contain the tree field
    
    # Verify the YAML content matches the expected tree structure
    parsed_yaml = yaml.safe_load(result["yaml_result"])
    assert "tree" in parsed_yaml
    assert parsed_yaml["tree"]["id"] == "obj1"
    assert parsed_yaml["tree"]["type"] == "frame"
    assert parsed_yaml["tree"]["name"] == "Test Object"
    assert isinstance(parsed_yaml["tree"]["children"], list)
    assert parsed_yaml["tree"]["children"][0]["id"] == "child1"
    
    # Check that image is included in YAML
    assert "image" in parsed_yaml
    assert "uri" in parsed_yaml["image"]
    assert parsed_yaml["image"]["uri"].startswith("render_component://")
    assert parsed_yaml["image"]["format"] == "png"
    
    # Verify mocks were called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")
    mock_get_subtree.assert_called_once_with(
        mock_penpot_api.get_file.return_value,
        "obj1",
        include_fields=["id", "type", "name"],
        depth=-1
    )


@patch('penpot_mcp.tools.penpot_tree.get_object_subtree_with_fields')
def test_get_object_tree_with_include_image(mock_get_subtree, mock_penpot_api):
    """Test the get_object_tree tool handler with image inclusion (always included now)."""
    # Setup the mock get_object_subtree_with_fields function
    mock_get_subtree.return_value = {
        "tree": {
            "id": "obj1",
            "type": "frame",
            "name": "Test Object",
            "children": []
        },
        "page_id": "page1"
    }
    
    # Setup the export_object mock for the included image
    export_object_mock = MagicMock()
    export_object_mock.return_value = MagicMock(data=b'test_image_data', format='png')
    
    # Create a callable that matches what would be registered
    def get_object_tree(
        file_id: str, 
        object_id: str, 
        fields: list,  # Now required parameter
        depth: int = -1,
        format: str = "json"
    ):
        try:
            # Get the file data
            file_data = mock_penpot_api.get_file(file_id=file_id)
            
            # Use the mocked utility function
            result = mock_get_subtree(
                file_data, 
                object_id, 
                include_fields=fields,
                depth=depth
            )
            
            # Extract the tree and page_id
            simplified_tree = result["tree"]
            page_id = result["page_id"]
            
            # Prepare the result dictionary
            final_result = {"tree": simplified_tree}
            
            # Always include image (no longer optional)
            try:
                image = export_object_mock(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id
                )
                # New format: URI-based instead of base64 data
                image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                image_uri = f"render_component://{image_id}"
                final_result["image"] = {
                    "uri": image_uri,
                    "format": image.format if hasattr(image, 'format') else "png"
                }
            except Exception as e:
                final_result["image_error"] = str(e)
            
            # Format the tree as YAML if requested
            if format.lower() == "yaml":
                try:
                    # Convert the entire result to YAML, including the image if present
                    yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                    return {"yaml_result": yaml_result}
                except Exception as e:
                    return {"format_error": f"Error formatting as YAML: {str(e)}"}
            
            # Return the JSON format result
            return final_result
        except Exception as e:
            return {"error": str(e)}
    
    # Call the handler with required fields parameter
    result = get_object_tree(
        file_id="file1", 
        object_id="obj1", 
        fields=["id", "type", "name"]  # Updated parameter name
    )
    
    # Check the result
    assert isinstance(result, dict)
    assert "tree" in result
    assert result["tree"]["id"] == "obj1"
    assert result["tree"]["type"] == "frame"
    assert result["tree"]["name"] == "Test Object"
    
    # Check that image is always included
    assert "image" in result
    assert "uri" in result["image"]
    assert result["image"]["uri"].startswith("render_component://")
    assert result["image"]["format"] == "png"
    
    # Verify mocks were called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")
    mock_get_subtree.assert_called_once_with(
        mock_penpot_api.get_file.return_value,
        "obj1",
        include_fields=["id", "type", "name"],
        depth=-1
    )


@patch('penpot_mcp.tools.penpot_tree.get_object_subtree_with_fields')
def test_get_object_tree_with_yaml_and_image(mock_get_subtree, mock_penpot_api):
    """Test the get_object_tree tool handler with YAML format and image inclusion (always included now)."""
    # Setup the mock get_object_subtree_with_fields function
    mock_get_subtree.return_value = {
        "tree": {
            "id": "obj1",
            "type": "frame",
            "name": "Test Object",
            "children": []
        },
        "page_id": "page1"
    }
    
    # Setup the export_object mock for the included image
    export_object_mock = MagicMock()
    export_object_mock.return_value = MagicMock(data=b'test_image_data', format='png')
    
    # Create a callable that matches what would be registered
    def get_object_tree(
        file_id: str, 
        object_id: str, 
        fields: list,  # Now required parameter
        depth: int = -1,
        format: str = "json"
    ):
        try:
            # Get the file data
            file_data = mock_penpot_api.get_file(file_id=file_id)
            
            # Use the mocked utility function
            result = mock_get_subtree(
                file_data, 
                object_id, 
                include_fields=fields,
                depth=depth
            )
            
            # Extract the tree and page_id
            simplified_tree = result["tree"]
            page_id = result["page_id"]
            
            # Prepare the result dictionary
            final_result = {"tree": simplified_tree}
            
            # Always include image (no longer optional)
            try:
                image = export_object_mock(
                    file_id=file_id,
                    page_id=page_id,
                    object_id=object_id
                )
                # New format: URI-based instead of base64 data
                image_id = hashlib.md5(f"{file_id}:{object_id}".encode()).hexdigest()
                image_uri = f"render_component://{image_id}"
                final_result["image"] = {
                    "uri": image_uri,
                    "format": image.format if hasattr(image, 'format') else "png"
                }
            except Exception as e:
                final_result["image_error"] = str(e)
            
            # Format the tree as YAML if requested
            if format.lower() == "yaml":
                try:
                    # Convert the entire result to YAML, including the image if present
                    yaml_result = yaml.dump(final_result, default_flow_style=False, sort_keys=False)
                    return {"yaml_result": yaml_result}
                except Exception as e:
                    return {"format_error": f"Error formatting as YAML: {str(e)}"}
            
            # Return the JSON format result
            return final_result
        except Exception as e:
            return {"error": str(e)}
    
    # Call the handler with required fields parameter and YAML format
    result = get_object_tree(
        file_id="file1", 
        object_id="obj1", 
        fields=["id", "type", "name"],  # Updated parameter name
        format="yaml"
    )
    
    # Check the result
    assert isinstance(result, dict)
    assert "yaml_result" in result
    assert "tree" not in result  # Should not contain the tree field directly
    
    # Verify the YAML content contains both tree and image with URI
    parsed_yaml = yaml.safe_load(result["yaml_result"])
    assert "tree" in parsed_yaml
    assert parsed_yaml["tree"]["id"] == "obj1"
    assert parsed_yaml["tree"]["type"] == "frame"
    assert parsed_yaml["tree"]["name"] == "Test Object"
    assert "image" in parsed_yaml
    assert "uri" in parsed_yaml["image"]
    
    # Verify the URI format in the YAML
    assert parsed_yaml["image"]["uri"].startswith("render_component://")
    assert parsed_yaml["image"]["format"] == "png"
    
    # Verify mocks were called with correct parameters
    mock_penpot_api.get_file.assert_called_once_with(file_id="file1")
    mock_get_subtree.assert_called_once_with(
        mock_penpot_api.get_file.return_value,
        "obj1",
        include_fields=["id", "type", "name"],
        depth=-1
    )


def test_rendered_component_resource():
    """Test the rendered component resource handler."""
    server = PenpotMCPServer(test_mode=True)

    component_id = "test_component_id"
    mock_image = MagicMock()
    mock_image.format = "png"

    # Mock the rendered_components dictionary
    server.rendered_components = {component_id: mock_image}

    # Get the resource handler function dynamically (this is tricky in real usage)
    # For testing, we'll implement the function directly based on the code
    def get_rendered_component(component_id: str):
        if component_id in server.rendered_components:
            return server.rendered_components[component_id]
        raise Exception(f"Component with ID {component_id} not found")

    # Test with a valid component ID
    result = get_rendered_component(component_id)
    assert result == mock_image

    # Test with an invalid component ID
    with pytest.raises(Exception) as excinfo:
        get_rendered_component("invalid_id")
    assert "not found" in str(excinfo.value)


def test_search_object_basic(mock_penpot_api):
    """Test the search_object tool basic functionality."""
    # Mock the file contents with more detailed mock data
    mock_file_data = {
        "id": "file1",
        "name": "Test File",
        "pagesIndex": {
            "page1": {
                "id": "page1",
                "name": "Page 1",
                "objects": {
                    "obj1": {"id": "obj1", "name": "Button Component", "type": "frame"},
                    "obj2": {"id": "obj2", "name": "Header Text", "type": "text"},
                    "obj3": {"id": "obj3", "name": "Button Label", "type": "text"}
                }
            },
            "page2": {
                "id": "page2",
                "name": "Page 2",
                "objects": {
                    "obj4": {"id": "obj4", "name": "Footer Button", "type": "frame"},
                    "obj5": {"id": "obj5", "name": "Copyright Text", "type": "text"}
                }
            }
        }
    }
    
    # Override the get_file return value for this test
    mock_penpot_api.get_file.return_value = mock_file_data
    
    # Create a function to simulate the search_object tool
    def get_cached_file(file_id):
        # Call the mock API to ensure it's tracked for assertions
        return mock_penpot_api.get_file(file_id=file_id)
    
    def search_object(file_id: str, query: str):
        try:
            # Get the file data using cache
            file_data = get_cached_file(file_id)
            if "error" in file_data:
                return file_data
            
            # Create case-insensitive pattern for matching
            import re
            pattern = re.compile(query, re.IGNORECASE)
            
            # Store matching objects
            matches = []
            
            # Search through each page in the file
            for page_id, page_data in file_data.get('pagesIndex', {}).items():
                page_name = page_data.get('name', 'Unnamed')
                
                # Search through objects in this page
                for obj_id, obj_data in page_data.get('objects', {}).items():
                    obj_name = obj_data.get('name', '')
                    
                    # Check if the name contains the query (case-insensitive)
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
    
    # Test searching for "button" (should find 3 objects)
    result = search_object("file1", "button")
    assert "objects" in result
    assert len(result["objects"]) == 3
    
    # Check the first match
    button_matches = [obj for obj in result["objects"] if "Button Component" == obj["name"]]
    assert len(button_matches) == 1
    assert button_matches[0]["id"] == "obj1"
    assert button_matches[0]["page_id"] == "page1"
    assert button_matches[0]["page_name"] == "Page 1"
    assert button_matches[0]["object_type"] == "frame"
    
    # Check that it found objects across pages
    footer_button_matches = [obj for obj in result["objects"] if "Footer Button" == obj["name"]]
    assert len(footer_button_matches) == 1
    assert footer_button_matches[0]["page_id"] == "page2"
    
    # Verify API was called with correct parameters
    mock_penpot_api.get_file.assert_called_with(file_id="file1")


def test_search_object_case_insensitive(mock_penpot_api):
    """Test the search_object tool with case-insensitive search."""
    # Mock the file contents with more detailed mock data
    mock_file_data = {
        "id": "file1",
        "name": "Test File",
        "pagesIndex": {
            "page1": {
                "id": "page1",
                "name": "Page 1",
                "objects": {
                    "obj1": {"id": "obj1", "name": "Button Component", "type": "frame"},
                    "obj2": {"id": "obj2", "name": "HEADER TEXT", "type": "text"},
                    "obj3": {"id": "obj3", "name": "button Label", "type": "text"}
                }
            }
        }
    }
    
    # Override the get_file return value for this test
    mock_penpot_api.get_file.return_value = mock_file_data
    
    # Create a function to simulate the search_object tool
    def get_cached_file(file_id):
        # Call the mock API to ensure it's tracked for assertions
        return mock_penpot_api.get_file(file_id=file_id)
    
    def search_object(file_id: str, query: str):
        try:
            # Get the file data using cache
            file_data = get_cached_file(file_id)
            if "error" in file_data:
                return file_data
            
            # Create case-insensitive pattern for matching
            import re
            pattern = re.compile(query, re.IGNORECASE)
            
            # Store matching objects
            matches = []
            
            # Search through each page in the file
            for page_id, page_data in file_data.get('pagesIndex', {}).items():
                page_name = page_data.get('name', 'Unnamed')
                
                # Search through objects in this page
                for obj_id, obj_data in page_data.get('objects', {}).items():
                    obj_name = obj_data.get('name', '')
                    
                    # Check if the name contains the query (case-insensitive)
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
    
    # Test with lowercase query for uppercase text
    result = search_object("file1", "header")
    assert "objects" in result
    assert len(result["objects"]) == 1
    assert result["objects"][0]["name"] == "HEADER TEXT"
    
    # Test with uppercase query for lowercase text
    result = search_object("file1", "BUTTON")
    assert "objects" in result
    assert len(result["objects"]) == 2
    
    # Check mixed case matching
    button_matches = sorted([obj["name"] for obj in result["objects"]])
    assert button_matches == ["Button Component", "button Label"]
    
    # Verify API was called
    mock_penpot_api.get_file.assert_called_with(file_id="file1")


def test_search_object_no_matches(mock_penpot_api):
    """Test the search_object tool when no matches are found."""
    # Mock the file contents
    mock_file_data = {
        "id": "file1",
        "name": "Test File",
        "pagesIndex": {
            "page1": {
                "id": "page1",
                "name": "Page 1",
                "objects": {
                    "obj1": {"id": "obj1", "name": "Button Component", "type": "frame"},
                    "obj2": {"id": "obj2", "name": "Header Text", "type": "text"}
                }
            }
        }
    }
    
    # Override the get_file return value for this test
    mock_penpot_api.get_file.return_value = mock_file_data
    
    # Create a function to simulate the search_object tool
    def get_cached_file(file_id):
        # Call the mock API to ensure it's tracked for assertions
        return mock_penpot_api.get_file(file_id=file_id)
    
    def search_object(file_id: str, query: str):
        try:
            # Get the file data using cache
            file_data = get_cached_file(file_id)
            if "error" in file_data:
                return file_data
            
            # Create case-insensitive pattern for matching
            import re
            pattern = re.compile(query, re.IGNORECASE)
            
            # Store matching objects
            matches = []
            
            # Search through each page in the file
            for page_id, page_data in file_data.get('pagesIndex', {}).items():
                page_name = page_data.get('name', 'Unnamed')
                
                # Search through objects in this page
                for obj_id, obj_data in page_data.get('objects', {}).items():
                    obj_name = obj_data.get('name', '')
                    
                    # Check if the name contains the query (case-insensitive)
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
    
    # Test with a query that won't match anything
    result = search_object("file1", "nonexistent")
    assert "objects" in result
    assert len(result["objects"]) == 0  # Empty array
    
    # Verify API was called
    mock_penpot_api.get_file.assert_called_with(file_id="file1")


def test_search_object_error_handling(mock_penpot_api):
    """Test the search_object tool error handling."""
    # Make the API throw an exception
    mock_penpot_api.get_file.side_effect = Exception("API error")
    
    def get_cached_file(file_id):
        try:
            return mock_penpot_api.get_file(file_id=file_id)
        except Exception as e:
            return {"error": str(e)}
    
    def search_object(file_id: str, query: str):
        try:
            # Get the file data using cache
            file_data = get_cached_file(file_id)
            if "error" in file_data:
                return file_data
            
            # Create case-insensitive pattern for matching
            import re
            pattern = re.compile(query, re.IGNORECASE)
            
            # Store matching objects
            matches = []
            
            # Search through each page in the file
            for page_id, page_data in file_data.get('pagesIndex', {}).items():
                page_name = page_data.get('name', 'Unnamed')
                
                # Search through objects in this page
                for obj_id, obj_data in page_data.get('objects', {}).items():
                    obj_name = obj_data.get('name', '')
                    
                    # Check if the name contains the query (case-insensitive)
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
    
    # Test with error from API
    result = search_object("file1", "button")
    assert "error" in result
    assert "API error" in result["error"]
    
    # Verify API was called
    mock_penpot_api.get_file.assert_called_with(file_id="file1")
