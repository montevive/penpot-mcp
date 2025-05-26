"""
Tool for building and visualizing the structure of Penpot files as a tree.

This module provides functionality to parse Penpot file data and generate
a tree representation, which can be displayed or exported.
"""

import re
from typing import Any, Dict, Optional, Union, List

from anytree import Node, RenderTree
from anytree.exporter import DotExporter


def build_tree(data: Dict[str, Any]) -> Node:
    """
    Build a tree representation of Penpot file data.

    Args:
        data: The Penpot file data

    Returns:
        The root node of the tree
    """
    # Create nodes dictionary with ID as key
    nodes = {}

    # Create a synthetic root node with a special ID that won't conflict
    synthetic_root_id = "SYNTHETIC-ROOT"
    root = Node(f"{synthetic_root_id} (root) - Root")
    nodes[synthetic_root_id] = root

    # Add components section
    components_node = Node(f"components (section) - Components", parent=root)

    # Store component annotations for later reference
    component_annotations = {}

    # Process components
    for comp_id, comp_data in data.get('components', {}).items():
        comp_name = comp_data.get('name', 'Unnamed')
        comp_node = Node(f"{comp_id} (component) - {comp_name}", parent=components_node)
        nodes[comp_id] = comp_node

        # Store annotation if present
        if 'annotation' in comp_data and comp_data['annotation']:
            component_annotations[comp_id] = comp_data['annotation']

    # First pass: create all page nodes
    for page_id, page_data in data.get('pagesIndex', {}).items():
        # Create page node
        page_name = page_data.get('name', 'Unnamed')
        page_node = Node(f"{page_id} (page) - {page_name}", parent=root)
        nodes[page_id] = page_node

    # Second pass: process each page and its objects
    for page_id, page_data in data.get('pagesIndex', {}).items():
        page_name = page_data.get('name', 'Unnamed')

        # Create a page-specific dictionary for objects to avoid ID collisions
        page_nodes = {}

        # First, create all object nodes for this page
        for obj_id, obj_data in page_data.get('objects', {}).items():
            obj_type = obj_data.get('type', 'unknown')
            obj_name = obj_data.get('name', 'Unnamed')

            # Make a unique key that includes the page ID to avoid collisions
            page_obj_id = f"{page_id}:{obj_id}"

            node = Node(f"{obj_id} ({obj_type}) - {obj_name}")
            page_nodes[obj_id] = node  # Store with original ID for this page's lookup

            # Store additional properties for filtering
            node.obj_type = obj_type
            node.obj_name = obj_name
            node.obj_id = obj_id

            # Add component reference if this is a component instance
            if 'componentId' in obj_data and obj_data['componentId'] in nodes:
                comp_ref = obj_data['componentId']
                node.componentRef = comp_ref

                # If this component has an annotation, store it
                if comp_ref in component_annotations:
                    node.componentAnnotation = component_annotations[comp_ref]

        # Identify the all-zeros root frame for this page
        all_zeros_id = "00000000-0000-0000-0000-000000000000"
        page_root_frame = None

        # First, find and connect the all-zeros root frame if it exists
        if all_zeros_id in page_data.get('objects', {}):
            page_root_frame = page_nodes[all_zeros_id]
            page_root_frame.parent = nodes[page_id]

        # Then build parent-child relationships for this page
        for obj_id, obj_data in page_data.get('objects', {}).items():
            # Skip the all-zeros root frame as we already processed it
            if obj_id == all_zeros_id:
                continue

            parent_id = obj_data.get('parentId')

            # Skip if parent ID is the same as object ID (circular reference)
            if parent_id and parent_id == obj_id:
                print(
                    f"Warning: Object {obj_id} references itself as parent. Attaching to page instead.")
                page_nodes[obj_id].parent = nodes[page_id]
            elif parent_id and parent_id in page_nodes:
                # Check for circular references in the node hierarchy
                is_circular = False
                check_node = page_nodes[parent_id]
                while check_node.parent is not None:
                    if hasattr(check_node.parent, 'obj_id') and check_node.parent.obj_id == obj_id:
                        is_circular = True
                        break
                    check_node = check_node.parent

                if is_circular:
                    print(
                        f"Warning: Circular reference detected for {obj_id}. Attaching to page instead.")
                    page_nodes[obj_id].parent = nodes[page_id]
                else:
                    page_nodes[obj_id].parent = page_nodes[parent_id]
            else:
                # If no parent or parent not found, connect to the all-zeros root frame if it exists,
                # otherwise connect to the page
                if page_root_frame:
                    page_nodes[obj_id].parent = page_root_frame
                else:
                    page_nodes[obj_id].parent = nodes[page_id]

    return root


def print_tree(root: Node, filter_pattern: Optional[str] = None) -> None:
    """
    Print a tree representation to the console, with optional filtering.

    Args:
        root: The root node of the tree
        filter_pattern: Optional regex pattern to filter nodes
    """
    matched_nodes = []

    # Apply filtering
    if filter_pattern:
        # Find all nodes that match the filter
        pattern = re.compile(filter_pattern, re.IGNORECASE)

        # Helper function to check if a node matches the filter
        def matches_filter(node):
            if not hasattr(node, 'obj_type') and not hasattr(node, 'obj_name'):
                return False  # Root node or section nodes

            if pattern.search(
                    node.obj_type) or pattern.search(
                    node.obj_name) or pattern.search(
                    node.obj_id):
                return True
            return False

        # Find all matching nodes and their paths to root
        for pre, _, node in RenderTree(root):
            if matches_filter(node):
                matched_nodes.append(node)

        # If we found matches, only print these nodes and their ancestors
        if matched_nodes:
            print(f"Filtered results matching '{filter_pattern}':")

            # Build a set of all nodes to show (matching nodes and their ancestors)
            nodes_to_show = set()
            for node in matched_nodes:
                # Add the node and all its ancestors
                current = node
                while current is not None:
                    nodes_to_show.add(current)
                    current = current.parent

            # Print the filtered tree
            for pre, _, node in RenderTree(root):
                if node in nodes_to_show:
                    node_name = node.name
                    if hasattr(node, 'componentRef'):
                        comp_ref_str = f" (refs component: {node.componentRef}"
                        if hasattr(node, 'componentAnnotation'):
                            comp_ref_str += f" - Note: {node.componentAnnotation}"
                        comp_ref_str += ")"
                        node_name += comp_ref_str

                    # Highlight matched nodes
                    if node in matched_nodes:
                        print(f"{pre}{node_name} <-- MATCH")
                    else:
                        print(f"{pre}{node_name}")

            print(f"\nFound {len(matched_nodes)} matching objects.")
            return

    # If no filter or no matches, print the entire tree
    for pre, _, node in RenderTree(root):
        node_name = node.name
        if hasattr(node, 'componentRef'):
            comp_ref_str = f" (refs component: {node.componentRef}"
            if hasattr(node, 'componentAnnotation'):
                comp_ref_str += f" - Note: {node.componentAnnotation}"
            comp_ref_str += ")"
            node_name += comp_ref_str
        print(f"{pre}{node_name}")


def export_tree_to_dot(root: Node, output_file: str, filter_pattern: Optional[str] = None) -> bool:
    """
    Export the tree to a DOT file (Graphviz format).

    Args:
        root: The root node of the tree
        output_file: Path to save the exported file
        filter_pattern: Optional regex pattern to filter nodes

    Returns:
        True if successful, False otherwise
    """
    try:
        # If filtering, we may want to only export the filtered tree
        if filter_pattern:
            # TODO: Implement filtered export
            pass

        DotExporter(root).to_picture(output_file)
        print(f"Tree exported to {output_file}")
        return True
    except Exception as e:
        print(f"Warning: Could not export to {output_file}: {e}")
        print("Make sure Graphviz is installed: https://graphviz.org/download/")
        return False


def find_page_containing_object(content: Dict[str, Any], object_id: str) -> Optional[str]:
    """
    Find which page contains the specified object.

    Args:
        content: The Penpot file content
        object_id: The ID of the object to find

    Returns:
        The page ID containing the object, or None if not found
    """
    # Helper function to recursively search for an object in the hierarchy
    def find_object_in_hierarchy(objects_dict, target_id):
        # Check if the object is directly in the dictionary
        if target_id in objects_dict:
            return True

        # Check if the object is a child of any object in the dictionary
        for obj_id, obj_data in objects_dict.items():
            # Look for objects that have shapes (children)
            if "shapes" in obj_data and target_id in obj_data["shapes"]:
                return True

            # Check in children elements if any
            if "children" in obj_data:
                child_objects = {child["id"]: child for child in obj_data["children"]}
                if find_object_in_hierarchy(child_objects, target_id):
                    return True

        return False

    # Check each page
    for page_id, page_data in content.get('pagesIndex', {}).items():
        objects_dict = page_data.get('objects', {})
        if find_object_in_hierarchy(objects_dict, object_id):
            return page_id

    return None


def find_object_in_tree(tree: Node, target_id: str) -> Optional[Dict[str, Any]]:
    """
    Find an object in the tree by its ID and return its subtree as a dictionary.

    Args:
        tree: The root node of the tree
        target_id: The ID of the object to find

    Returns:
        Dictionary representation of the object's subtree, or None if not found
    """
    # Helper function to search in a node's children
    def find_object_in_children(node, target_id):
        for child in node.children:
            if hasattr(child, 'obj_id') and child.obj_id == target_id:
                return convert_node_to_dict(child)

            result = find_object_in_children(child, target_id)
            if result:
                return result
        return None

    # Iterate through the tree's children
    for child in tree.children:
        # Check if this is a page node (contains "(page)" in its name)
        if "(page)" in child.name:
            # Check all objects under this page
            for obj in child.children:
                if hasattr(obj, 'obj_id') and obj.obj_id == target_id:
                    return convert_node_to_dict(obj)

                # Check children recursively
                result = find_object_in_children(obj, target_id)
                if result:
                    return result
    return None


def convert_node_to_dict(node: Node) -> Dict[str, Any]:
    """
    Convert an anytree.Node to a dictionary format for API response.

    Args:
        node: The node to convert

    Returns:
        Dictionary representation of the node and its subtree
    """
    result = {
        'id': node.obj_id if hasattr(node, 'obj_id') else None,
        'type': node.obj_type if hasattr(node, 'obj_type') else None,
        'name': node.obj_name if hasattr(node, 'obj_name') else None,
        'children': []
    }

    # Add component reference if available
    if hasattr(node, 'componentRef'):
        result['componentRef'] = node.componentRef

    # Add component annotation if available
    if hasattr(node, 'componentAnnotation'):
        result['componentAnnotation'] = node.componentAnnotation

    # Recursively add children
    for child in node.children:
        result['children'].append(convert_node_to_dict(child))

    return result


def get_object_subtree(file_data: Dict[str, Any], object_id: str) -> Dict[str, Union[Dict, str]]:
    """
    Get a simplified tree representation of an object and its children.

    Args:
        file_data: The Penpot file data
        object_id: The ID of the object to get the tree for

    Returns:
        Dictionary containing the simplified tree or an error message
    """
    try:
        # Get the content from file data
        content = file_data.get('data')

        # Find which page contains the object
        page_id = find_page_containing_object(content, object_id)

        if not page_id:
            return {"error": f"Object {object_id} not found in file"}

        # Build the full tree
        full_tree = build_tree(content)

        # Find the object in the full tree and extract its subtree
        simplified_tree = find_object_in_tree(full_tree, object_id)

        if not simplified_tree:
            return {"error": f"Object {object_id} not found in tree structure"}

        return {
            "tree": simplified_tree,
            "page_id": page_id
        }
    except Exception as e:
        return {"error": str(e)}


def get_object_subtree_with_fields(file_data: Dict[str, Any], object_id: str, 
                                  include_fields: Optional[List[str]] = None, 
                                  depth: int = -1) -> Dict[str, Any]:
    """
    Get a filtered tree representation of an object with only specified fields.
    
    This function finds an object in the Penpot file data and returns a subtree
    with the object as the root, including only the specified fields and limiting
    the depth of the tree if requested.
    
    Args:
        file_data: The Penpot file data
        object_id: The ID of the object to get the tree for
        include_fields: List of field names to include in the output (None means include all)
        depth: Maximum depth of the tree (-1 means no limit)
    
    Returns:
        Dictionary containing the filtered tree or an error message
    """
    try:
        # Get the content from file data
        content = file_data.get('data', file_data)
        
        # Find which page contains the object
        page_id = find_page_containing_object(content, object_id)
        
        if not page_id:
            return {"error": f"Object {object_id} not found in file"}
            
        # Get the page data
        page_data = content.get('pagesIndex', {}).get(page_id, {})
        objects_dict = page_data.get('objects', {})
        
        # Check if the object exists in this page
        if object_id not in objects_dict:
            return {"error": f"Object {object_id} not found in page {page_id}"}
            
        # Function to recursively build the filtered object tree
        def build_filtered_object_tree(obj_id: str, current_depth: int = 0):
            if obj_id not in objects_dict:
                return None
                
            obj_data = objects_dict[obj_id]
            
            # Create a new dict with only the requested fields or all fields if None
            if include_fields is None:
                filtered_obj = obj_data.copy()
            else:
                filtered_obj = {field: obj_data[field] for field in include_fields if field in obj_data}
            
            # Always include the id field
            filtered_obj['id'] = obj_id
            
            # If depth limit reached, don't process children
            if depth != -1 and current_depth >= depth:
                return filtered_obj
                
            # Find all children of this object
            children = []
            for child_id, child_data in objects_dict.items():
                if child_data.get('parentId') == obj_id:
                    child_tree = build_filtered_object_tree(child_id, current_depth + 1)
                    if child_tree:
                        children.append(child_tree)
            
            # Add children field only if we have children
            if children:
                filtered_obj['children'] = children
                
            return filtered_obj
        
        # Build the filtered tree starting from the requested object
        object_tree = build_filtered_object_tree(object_id)
        
        if not object_tree:
            return {"error": f"Failed to build object tree for {object_id}"}
            
        return {
            "tree": object_tree,
            "page_id": page_id
        }
        
    except Exception as e:
        return {"error": str(e)}
