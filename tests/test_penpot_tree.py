"""Tests for the penpot_tree module."""

import re
from unittest.mock import MagicMock, patch

import pytest
from anytree import Node, RenderTree

from penpot_mcp.tools.penpot_tree import (
    build_tree, 
    print_tree, 
    export_tree_to_dot, 
    find_page_containing_object, 
    find_object_in_tree, 
    convert_node_to_dict, 
    get_object_subtree,
    get_object_subtree_with_fields
)


@pytest.fixture
def sample_penpot_data():
    """Create sample Penpot file data for testing."""
    return {
        'components': {
            'comp1': {'name': 'Button', 'annotation': 'Primary button'},
            'comp2': {'name': 'Card', 'annotation': None}
        },
        'pagesIndex': {
            'page1': {
                'name': 'Home Page',
                'objects': {
                    '00000000-0000-0000-0000-000000000000': {
                        'type': 'frame',
                        'name': 'Root Frame',
                    },
                    'obj1': {
                        'type': 'frame',
                        'name': 'Header',
                        'parentId': '00000000-0000-0000-0000-000000000000'
                    },
                    'obj2': {
                        'type': 'text',
                        'name': 'Title',
                        'parentId': 'obj1'
                    },
                    'obj3': {
                        'type': 'frame',
                        'name': 'Button Instance',
                        'parentId': 'obj1',
                        'componentId': 'comp1'
                    }
                }
            },
            'page2': {
                'name': 'About Page',
                'objects': {
                    '00000000-0000-0000-0000-000000000000': {
                        'type': 'frame',
                        'name': 'Root Frame',
                    },
                    'obj4': {
                        'type': 'frame',
                        'name': 'Content',
                        'parentId': '00000000-0000-0000-0000-000000000000'
                    },
                    'obj5': {
                        'type': 'image',
                        'name': 'Logo',
                        'parentId': 'obj4'
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_tree(sample_penpot_data):
    """Create a sample tree from the sample data."""
    return build_tree(sample_penpot_data)


def test_build_tree(sample_penpot_data, sample_tree):
    """Test building a tree from Penpot file data."""
    # Check that the root is created
    assert sample_tree.name.startswith("SYNTHETIC-ROOT")
    
    # Check components section
    components_node = None
    for child in sample_tree.children:
        if "components (section)" in child.name:
            components_node = child
            break
    
    assert components_node is not None
    assert len(components_node.children) == 2
    
    # Check pages are created
    page_nodes = [child for child in sample_tree.children if "(page)" in child.name]
    assert len(page_nodes) == 2
    
    # Check objects within pages
    for page_node in page_nodes:
        if "Home Page" in page_node.name:
            # Check that objects are created under the page
            assert len(page_node.descendants) == 4  # Root frame + 3 objects
            
            # Check parent-child relationships
            for node in RenderTree(page_node):
                if hasattr(node[2], 'obj_id') and node[2].obj_id == 'obj2':
                    assert node[2].parent.obj_id == 'obj1'
                elif hasattr(node[2], 'obj_id') and node[2].obj_id == 'obj3':
                    assert node[2].parent.obj_id == 'obj1'
                    assert hasattr(node[2], 'componentRef')
                    assert node[2].componentRef == 'comp1'
                    assert hasattr(node[2], 'componentAnnotation')
                    assert node[2].componentAnnotation == 'Primary button'


def test_print_tree(sample_tree, capsys):
    """Test printing the tree to console."""
    print_tree(sample_tree)
    captured = capsys.readouterr()
    
    # Check that all pages and components are in the output
    assert "Home Page" in captured.out
    assert "About Page" in captured.out
    assert "comp1 (component) - Button" in captured.out
    assert "comp2 (component) - Card" in captured.out
    
    # Check that object types and names are displayed
    assert "(frame) - Header" in captured.out
    assert "(text) - Title" in captured.out
    
    # Check that component references are shown
    assert "refs component: comp1" in captured.out
    assert "Note: Primary button" in captured.out


def test_print_tree_with_filter(sample_tree, capsys):
    """Test printing the tree with a filter applied."""
    print_tree(sample_tree, filter_pattern="title")
    captured = capsys.readouterr()
    
    # Check that only the matching node and its ancestors are shown
    assert "Title" in captured.out
    assert "Header" in captured.out
    assert "Home Page" in captured.out
    assert "MATCH" in captured.out
    
    # Check that non-matching nodes are not included
    assert "Logo" not in captured.out
    assert "About Page" not in captured.out


@patch('anytree.exporter.DotExporter.to_picture')
def test_export_tree_to_dot(mock_to_picture, sample_tree):
    """Test exporting the tree to a DOT file."""
    result = export_tree_to_dot(sample_tree, "test_output.png")
    
    # Check that the exporter was called
    assert mock_to_picture.called
    assert result is True


@patch('anytree.exporter.DotExporter.to_picture', side_effect=Exception("Test exception"))
def test_export_tree_to_dot_exception(mock_to_picture, sample_tree, capsys):
    """Test handling exceptions when exporting the tree."""
    result = export_tree_to_dot(sample_tree, "test_output.png")
    
    # Check that the function returns False on error
    assert result is False
    
    # Check that an error message is displayed
    captured = capsys.readouterr()
    assert "Warning: Could not export" in captured.out
    assert "Make sure Graphviz is installed" in captured.out


def test_find_page_containing_object(sample_penpot_data):
    """Test finding which page contains a specific object."""
    # Test finding an object that exists
    page_id = find_page_containing_object(sample_penpot_data, 'obj2')
    assert page_id == 'page1'
    
    # Test finding an object in another page
    page_id = find_page_containing_object(sample_penpot_data, 'obj5')
    assert page_id == 'page2'
    
    # Test finding an object that doesn't exist
    page_id = find_page_containing_object(sample_penpot_data, 'nonexistent')
    assert page_id is None


def test_find_object_in_tree(sample_tree):
    """Test finding an object in the tree by its ID."""
    # Test finding an object that exists
    obj_dict = find_object_in_tree(sample_tree, 'obj3')
    assert obj_dict is not None
    assert obj_dict['id'] == 'obj3'
    assert obj_dict['type'] == 'frame'
    assert obj_dict['name'] == 'Button Instance'
    assert 'componentRef' in obj_dict
    assert obj_dict['componentRef'] == 'comp1'
    
    # Test finding an object that doesn't exist
    obj_dict = find_object_in_tree(sample_tree, 'nonexistent')
    assert obj_dict is None


def test_convert_node_to_dict():
    """Test converting a Node to a dictionary."""
    # Create a test node with children and attributes
    root = Node("root")
    root.obj_id = "root_id"
    root.obj_type = "frame"
    root.obj_name = "Root Frame"
    
    child1 = Node("child1", parent=root)
    child1.obj_id = "child1_id"
    child1.obj_type = "text"
    child1.obj_name = "Child 1"
    
    child2 = Node("child2", parent=root)
    child2.obj_id = "child2_id"
    child2.obj_type = "frame"
    child2.obj_name = "Child 2"
    child2.componentRef = "comp1"
    child2.componentAnnotation = "Test component"
    
    # Convert to dictionary
    result = convert_node_to_dict(root)
    
    # Check the result
    assert result['id'] == 'root_id'
    assert result['type'] == 'frame'
    assert result['name'] == 'Root Frame'
    assert len(result['children']) == 2
    
    # Check children
    child_ids = [child['id'] for child in result['children']]
    assert 'child1_id' in child_ids
    assert 'child2_id' in child_ids
    
    # Check component reference
    for child in result['children']:
        if child['id'] == 'child2_id':
            assert 'componentRef' in child
            assert child['componentRef'] == 'comp1'
            assert 'componentAnnotation' in child
            assert child['componentAnnotation'] == 'Test component'


def test_get_object_subtree(sample_penpot_data):
    """Test getting a simplified tree for an object."""
    file_data = {'data': sample_penpot_data}
    
    # Test getting a subtree for an existing object
    result = get_object_subtree(file_data, 'obj1')
    assert 'error' not in result
    assert 'tree' in result
    assert result['tree']['id'] == 'obj1'
    assert result['tree']['name'] == 'Header'
    assert result['page_id'] == 'page1'
    
    # Test getting a subtree for a non-existent object
    result = get_object_subtree(file_data, 'nonexistent')
    assert 'error' in result
    assert 'not found' in result['error']


def test_circular_reference_handling(sample_penpot_data):
    """Test handling of circular references in the tree structure."""
    # Create a circular reference
    sample_penpot_data['pagesIndex']['page1']['objects']['obj6'] = {
        'type': 'frame',
        'name': 'Circular Parent',
        'parentId': 'obj7'
    }
    sample_penpot_data['pagesIndex']['page1']['objects']['obj7'] = {
        'type': 'frame',
        'name': 'Circular Child',
        'parentId': 'obj6'
    }
    
    # Build tree with circular reference
    tree = build_tree(sample_penpot_data)
    
    # The tree should be built without errors
    # Check that the circular reference objects are attached to the page
    page_node = None
    for child in tree.children:
        if "(page)" in child.name and "Home Page" in child.name:
            page_node = child
            break
    
    assert page_node is not None
    
    # Find the circular reference objects
    circular_nodes = []
    for node in RenderTree(page_node):
        if hasattr(node[2], 'obj_id') and node[2].obj_id in ['obj6', 'obj7']:
            circular_nodes.append(node[2])
    
    # Check that the circular reference was resolved by attaching to parent
    assert len(circular_nodes) == 2


def test_get_object_subtree_with_fields(sample_penpot_data):
    """Test getting a filtered subtree for an object with specific fields."""
    file_data = {'data': sample_penpot_data}
    
    # Test with no field filtering (include all fields)
    result = get_object_subtree_with_fields(file_data, 'obj1')
    assert 'error' not in result
    assert 'tree' in result
    assert result['tree']['id'] == 'obj1'
    assert result['tree']['name'] == 'Header'
    assert result['tree']['type'] == 'frame'
    assert 'parentId' in result['tree']
    assert len(result['tree']['children']) == 2
    
    # Test with field filtering
    result = get_object_subtree_with_fields(file_data, 'obj1', include_fields=['name', 'type'])
    assert 'error' not in result
    assert 'tree' in result
    assert result['tree']['id'] == 'obj1'  # id is always included
    assert result['tree']['name'] == 'Header'
    assert result['tree']['type'] == 'frame'
    assert 'parentId' not in result['tree']  # should be filtered out
    assert len(result['tree']['children']) == 2
    
    # Test with depth limiting (depth=0, only the object itself)
    result = get_object_subtree_with_fields(file_data, 'obj1', depth=0)
    assert 'error' not in result
    assert 'tree' in result
    assert result['tree']['id'] == 'obj1'
    assert 'children' not in result['tree']  # No children at depth 0
    
    # Test for an object that doesn't exist
    result = get_object_subtree_with_fields(file_data, 'nonexistent')
    assert 'error' in result
    assert 'not found' in result['error'] 

def test_get_object_subtree_with_fields_deep_hierarchy():
    """Test getting a filtered subtree for an object with multiple levels of nesting."""
    # Create a more complex nested structure for testing depth parameter
    file_data = {
        'data': {
            'components': {
                'comp1': {
                    'id': 'comp1',
                    'name': 'Button',
                    'path': '/Components/Button',
                    'modifiedAt': '2023-01-01T12:00:00Z',
                    'mainInstanceId': 'main-button-instance',
                    'mainInstancePage': 'page1',
                    'annotation': 'Primary button'
                },
                'comp2': {
                    'id': 'comp2',
                    'name': 'Card',
                    'path': '/Components/Card',
                    'modifiedAt': '2023-01-02T12:00:00Z',
                    'mainInstanceId': 'main-card-instance',
                    'mainInstancePage': 'page1',
                    'annotation': 'Content card'
                }
            },
            'colors': {
                'color1': {
                    'path': '/Colors/Primary',
                    'color': '#3366FF',
                    'name': 'Primary Blue',
                    'modifiedAt': '2023-01-01T10:00:00Z',
                    'opacity': 1,
                    'id': 'color1'
                },
                'color2': {
                    'path': '/Colors/Secondary',
                    'color': '#FF6633',
                    'name': 'Secondary Orange',
                    'modifiedAt': '2023-01-01T10:30:00Z',
                    'opacity': 1,
                    'id': 'color2'
                }
            },
            'typographies': {
                'typo1': {
                    'lineHeight': '1.5',
                    'path': '/Typography/Heading',
                    'fontStyle': 'normal',
                    'textTransform': 'none',
                    'fontId': 'font1',
                    'fontSize': '24px',
                    'fontWeight': '600',
                    'name': 'Heading',
                    'modifiedAt': '2023-01-01T11:00:00Z',
                    'fontVariantId': 'var1',
                    'id': 'typo1',
                    'letterSpacing': '0',
                    'fontFamily': 'Inter'
                }
            },
            'pagesIndex': {
                'page1': {
                    'id': 'page1',
                    'name': 'Complex Page',
                    'options': {
                        'background': '#FFFFFF',
                        'grids': []
                    },
                    'objects': {
                        # Root frame (level 0)
                        '00000000-0000-0000-0000-000000000000': {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'type': 'frame',
                            'name': 'Root Frame',
                            'width': 1920,
                            'height': 1080,
                            'x': 0,
                            'y': 0,
                            'rotation': 0,
                            'selrect': {
                                'x': 0,
                                'y': 0,
                                'width': 1920,
                                'height': 1080,
                                'x1': 0,
                                'y1': 0,
                                'x2': 1920,
                                'y2': 1080
                            },
                            'fills': [
                                {
                                    'fillColor': '#FFFFFF',
                                    'fillOpacity': 1
                                }
                            ],
                            'layout': 'flex',
                            'layoutFlexDir': 'column',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'start'
                        },
                        # Main container (level 1)
                        'main-container': {
                            'id': 'main-container',
                            'type': 'frame',
                            'name': 'Main Container',
                            'parentId': '00000000-0000-0000-0000-000000000000',
                            'width': 1200,
                            'height': 800,
                            'x': 360,
                            'y': 140,
                            'rotation': 0,
                            'selrect': {
                                'x': 360,
                                'y': 140,
                                'width': 1200,
                                'height': 800,
                                'x1': 360,
                                'y1': 140,
                                'x2': 1560,
                                'y2': 940
                            },
                            'fills': [
                                {
                                    'fillColor': '#F5F5F5',
                                    'fillOpacity': 1
                                }
                            ],
                            'strokes': [
                                {
                                    'strokeStyle': 'solid',
                                    'strokeAlignment': 'center',
                                    'strokeWidth': 1,
                                    'strokeColor': '#E0E0E0',
                                    'strokeOpacity': 1
                                }
                            ],
                            'layout': 'flex',
                            'layoutFlexDir': 'column',
                            'layoutAlignItems': 'stretch',
                            'layoutJustifyContent': 'start',
                            'layoutGap': {
                                'row-gap': '0px',
                                'column-gap': '0px'
                            },
                            'layoutPadding': {
                                'padding-top': '0px',
                                'padding-right': '0px',
                                'padding-bottom': '0px',
                                'padding-left': '0px'
                            },
                            'constraintsH': 'center',
                            'constraintsV': 'center'
                        },
                        # Header section (level 2)
                        'header-section': {
                            'id': 'header-section',
                            'type': 'frame',
                            'name': 'Header Section',
                            'parentId': 'main-container',
                            'width': 1200,
                            'height': 100,
                            'x': 0,
                            'y': 0,
                            'rotation': 0,
                            'fills': [
                                {
                                    'fillColor': '#FFFFFF',
                                    'fillOpacity': 1
                                }
                            ],
                            'strokes': [
                                {
                                    'strokeStyle': 'solid',
                                    'strokeAlignment': 'bottom',
                                    'strokeWidth': 1,
                                    'strokeColor': '#EEEEEE',
                                    'strokeOpacity': 1
                                }
                            ],
                            'layout': 'flex',
                            'layoutFlexDir': 'row',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'space-between',
                            'layoutPadding': {
                                'padding-top': '20px',
                                'padding-right': '30px',
                                'padding-bottom': '20px',
                                'padding-left': '30px'
                            },
                            'constraintsH': 'stretch',
                            'constraintsV': 'top'
                        },
                        # Logo in header (level 3)
                        'logo': {
                            'id': 'logo',
                            'type': 'frame',
                            'name': 'Logo',
                            'parentId': 'header-section',
                            'width': 60,
                            'height': 60,
                            'x': 30,
                            'y': 20,
                            'rotation': 0,
                            'fills': [
                                {
                                    'fillColor': '#3366FF',
                                    'fillOpacity': 1
                                }
                            ],
                            'r1': 8,
                            'r2': 8,
                            'r3': 8,
                            'r4': 8,
                            'constraintsH': 'left',
                            'constraintsV': 'center'
                        },
                        # Navigation menu (level 3)
                        'nav-menu': {
                            'id': 'nav-menu',
                            'type': 'frame',
                            'name': 'Navigation Menu',
                            'parentId': 'header-section',
                            'width': 600,
                            'height': 60,
                            'x': 300,
                            'y': 20,
                            'rotation': 0,
                            'layout': 'flex',
                            'layoutFlexDir': 'row',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'center',
                            'layoutGap': {
                                'row-gap': '0px',
                                'column-gap': '20px'
                            },
                            'constraintsH': 'center',
                            'constraintsV': 'center'
                        },
                        # Menu items (level 4)
                        'menu-item-1': {
                            'id': 'menu-item-1',
                            'type': 'text',
                            'name': 'Home',
                            'parentId': 'nav-menu',
                            'width': 100,
                            'height': 40,
                            'x': 0,
                            'y': 10,
                            'rotation': 0,
                            'content': {
                                'type': 'root',
                                'children': [
                                    {
                                        'type': 'paragraph',
                                        'children': [
                                            {
                                                'type': 'text',
                                                'text': 'Home'
                                            }
                                        ]
                                    }
                                ]
                            },
                            'fills': [
                                {
                                    'fillColor': '#333333',
                                    'fillOpacity': 1
                                }
                            ],
                            'appliedTokens': {
                                'typography': 'typo1'
                            },
                            'constraintsH': 'start',
                            'constraintsV': 'center'
                        },
                        'menu-item-2': {
                            'id': 'menu-item-2',
                            'type': 'text',
                            'name': 'Products',
                            'parentId': 'nav-menu',
                            'width': 100,
                            'height': 40,
                            'x': 120,
                            'y': 10,
                            'rotation': 0,
                            'content': {
                                'type': 'root',
                                'children': [
                                    {
                                        'type': 'paragraph',
                                        'children': [
                                            {
                                                'type': 'text',
                                                'text': 'Products'
                                            }
                                        ]
                                    }
                                ]
                            },
                            'fills': [
                                {
                                    'fillColor': '#333333',
                                    'fillOpacity': 1
                                }
                            ]
                        },
                        'menu-item-3': {
                            'id': 'menu-item-3',
                            'type': 'text',
                            'name': 'About',
                            'parentId': 'nav-menu',
                            'width': 100,
                            'height': 40,
                            'x': 240,
                            'y': 10,
                            'rotation': 0,
                            'content': {
                                'type': 'root',
                                'children': [
                                    {
                                        'type': 'paragraph',
                                        'children': [
                                            {
                                                'type': 'text',
                                                'text': 'About'
                                            }
                                        ]
                                    }
                                ]
                            },
                            'fills': [
                                {
                                    'fillColor': '#333333',
                                    'fillOpacity': 1
                                }
                            ]
                        },
                        # Content section (level 2)
                        'content-section': {
                            'id': 'content-section',
                            'type': 'frame',
                            'name': 'Content Section',
                            'parentId': 'main-container',
                            'width': 1200,
                            'height': 700,
                            'x': 0,
                            'y': 100,
                            'rotation': 0,
                            'layout': 'flex',
                            'layoutFlexDir': 'column',
                            'layoutAlignItems': 'stretch',
                            'layoutJustifyContent': 'start',
                            'layoutGap': {
                                'row-gap': '0px',
                                'column-gap': '0px'
                            },
                            'constraintsH': 'stretch',
                            'constraintsV': 'top'
                        },
                        # Hero (level 3)
                        'hero': {
                            'id': 'hero',
                            'type': 'frame',
                            'name': 'Hero Section',
                            'parentId': 'content-section',
                            'width': 1200,
                            'height': 400,
                            'x': 0,
                            'y': 0,
                            'rotation': 0,
                            'fills': [
                                {
                                    'fillColor': '#F0F7FF',
                                    'fillOpacity': 1
                                }
                            ],
                            'layout': 'flex',
                            'layoutFlexDir': 'column',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'center',
                            'layoutPadding': {
                                'padding-top': '40px',
                                'padding-right': '40px',
                                'padding-bottom': '40px',
                                'padding-left': '40px'
                            },
                            'constraintsH': 'stretch',
                            'constraintsV': 'top'
                        },
                        # Hero title (level 4)
                        'hero-title': {
                            'id': 'hero-title',
                            'type': 'text',
                            'name': 'Welcome Title',
                            'parentId': 'hero',
                            'width': 600,
                            'height': 80,
                            'x': 300,
                            'y': 140,
                            'rotation': 0,
                            'content': {
                                'type': 'root',
                                'children': [
                                    {
                                        'type': 'paragraph',
                                        'children': [
                                            {
                                                'type': 'text',
                                                'text': 'Welcome to our Platform'
                                            }
                                        ]
                                    }
                                ]
                            },
                            'fills': [
                                {
                                    'fillColor': '#333333',
                                    'fillOpacity': 1
                                }
                            ],
                            'appliedTokens': {
                                'typography': 'typo1'
                            },
                            'constraintsH': 'center',
                            'constraintsV': 'center'
                        },
                        # Cards container (level 3)
                        'cards-container': {
                            'id': 'cards-container',
                            'type': 'frame',
                            'name': 'Cards Container',
                            'parentId': 'content-section',
                            'width': 1200,
                            'height': 300,
                            'x': 0,
                            'y': 400,
                            'rotation': 0,
                            'layout': 'flex',
                            'layoutFlexDir': 'row',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'space-around',
                            'layoutPadding': {
                                'padding-top': '25px',
                                'padding-right': '25px',
                                'padding-bottom': '25px',
                                'padding-left': '25px'
                            },
                            'constraintsH': 'stretch',
                            'constraintsV': 'top'
                        },
                        # Card instances (level 4)
                        'card-1': {
                            'id': 'card-1',
                            'type': 'frame',
                            'name': 'Card 1',
                            'parentId': 'cards-container',
                            'width': 300,
                            'height': 250,
                            'x': 50,
                            'y': 25,
                            'rotation': 0,
                            'componentId': 'comp2',
                            'fills': [
                                {
                                    'fillColor': '#FFFFFF',
                                    'fillOpacity': 1
                                }
                            ],
                            'strokes': [
                                {
                                    'strokeStyle': 'solid',
                                    'strokeAlignment': 'center',
                                    'strokeWidth': 1,
                                    'strokeColor': '#EEEEEE',
                                    'strokeOpacity': 1
                                }
                            ],
                            'r1': 8,
                            'r2': 8,
                            'r3': 8,
                            'r4': 8,
                            'layout': 'flex',
                            'layoutFlexDir': 'column',
                            'layoutAlignItems': 'center',
                            'layoutJustifyContent': 'start',
                            'layoutPadding': {
                                'padding-top': '20px',
                                'padding-right': '20px',
                                'padding-bottom': '20px',
                                'padding-left': '20px'
                            },
                            'constraintsH': 'center',
                            'constraintsV': 'center'
                        },
                        'card-2': {
                            'id': 'card-2',
                            'type': 'frame',
                            'name': 'Card 2',
                            'parentId': 'cards-container',
                            'width': 300,
                            'height': 250,
                            'x': 450,
                            'y': 25,
                            'rotation': 0,
                            'componentId': 'comp2',
                            'fills': [
                                {
                                    'fillColor': '#FFFFFF',
                                    'fillOpacity': 1
                                }
                            ],
                            'strokes': [
                                {
                                    'strokeStyle': 'solid',
                                    'strokeAlignment': 'center',
                                    'strokeWidth': 1,
                                    'strokeColor': '#EEEEEE',
                                    'strokeOpacity': 1
                                }
                            ],
                            'r1': 8,
                            'r2': 8,
                            'r3': 8,
                            'r4': 8
                        },
                        'card-3': {
                            'id': 'card-3',
                            'type': 'frame',
                            'name': 'Card 3',
                            'parentId': 'cards-container',
                            'width': 300,
                            'height': 250,
                            'x': 850,
                            'y': 25,
                            'rotation': 0,
                            'componentId': 'comp2',
                            'fills': [
                                {
                                    'fillColor': '#FFFFFF',
                                    'fillOpacity': 1
                                }
                            ],
                            'strokes': [
                                {
                                    'strokeStyle': 'solid',
                                    'strokeAlignment': 'center',
                                    'strokeWidth': 1,
                                    'strokeColor': '#EEEEEE',
                                    'strokeOpacity': 1
                                }
                            ],
                            'r1': 8,
                            'r2': 8,
                            'r3': 8,
                            'r4': 8
                        }
                    }
                }
            },
            'id': 'file1',
            'pages': ['page1'],
            'tokensLib': {
                'sets': {
                    'S-colors': {
                        'name': 'Colors',
                        'description': 'Color tokens',
                        'modifiedAt': '2023-01-01T09:00:00Z',
                        'tokens': {
                            'primary': {
                                'name': 'Primary',
                                'type': 'color',
                                'value': '#3366FF',
                                'description': 'Primary color',
                                'modifiedAt': '2023-01-01T09:00:00Z'
                            },
                            'secondary': {
                                'name': 'Secondary',
                                'type': 'color',
                                'value': '#FF6633',
                                'description': 'Secondary color',
                                'modifiedAt': '2023-01-01T09:00:00Z'
                            }
                        }
                    }
                },
                'themes': {
                    'default': {
                        'light': {
                            'name': 'Light',
                            'group': 'Default',
                            'description': 'Light theme',
                            'isSource': True,
                            'id': 'theme1',
                            'modifiedAt': '2023-01-01T09:30:00Z',
                            'sets': ['S-colors']
                        }
                    }
                },
                'activeThemes': ['light']
            }
        }
    }
    
    # Test 1: Full tree at maximum depth (default)
    result = get_object_subtree_with_fields(file_data, 'main-container')
    assert 'error' not in result
    assert result['tree']['id'] == 'main-container'
    assert result['tree']['name'] == 'Main Container'
    assert result['tree']['type'] == 'frame'
    
    # Verify first level children exist (header and content sections)
    children_names = [child['name'] for child in result['tree']['children']]
    assert 'Header Section' in children_names
    assert 'Content Section' in children_names
    
    # Verify second level children exist (deep nesting)
    header_section = next(child for child in result['tree']['children'] if child['name'] == 'Header Section')
    logo_in_header = next((child for child in header_section['children'] if child['name'] == 'Logo'), None)
    assert logo_in_header is not None
    
    nav_menu = next((child for child in header_section['children'] if child['name'] == 'Navigation Menu'), None)
    assert nav_menu is not None
    
    # Check if level 4 elements (menu items) exist
    menu_items = [child for child in nav_menu['children']]
    assert len(menu_items) == 3
    menu_item_names = [item['name'] for item in menu_items]
    assert 'Home' in menu_item_names
    assert 'Products' in menu_item_names
    assert 'About' in menu_item_names
    
    # Test 2: Depth = 1 (main container and its immediate children only)
    result = get_object_subtree_with_fields(file_data, 'main-container', depth=1)
    assert 'error' not in result
    assert result['tree']['id'] == 'main-container'
    assert 'children' in result['tree']
    
    # Should have header and content sections but no deeper elements
    children_names = [child['name'] for child in result['tree']['children']]
    assert 'Header Section' in children_names
    assert 'Content Section' in children_names
    
    # Verify no grandchildren are included
    header_section = next(child for child in result['tree']['children'] if child['name'] == 'Header Section')
    assert 'children' not in header_section
    
    # Test 3: Depth = 2 (main container, its children, and grandchildren)
    result = get_object_subtree_with_fields(file_data, 'main-container', depth=2)
    assert 'error' not in result
    
    # Should have header and content sections
    header_section = next(child for child in result['tree']['children'] if child['name'] == 'Header Section')
    content_section = next(child for child in result['tree']['children'] if child['name'] == 'Content Section')
    
    # Header section should have logo and nav menu but no menu items
    assert 'children' in header_section
    nav_menu = next((child for child in header_section['children'] if child['name'] == 'Navigation Menu'), None)
    assert nav_menu is not None
    assert 'children' not in nav_menu
    
    # Test 4: Field filtering with selective depth
    result = get_object_subtree_with_fields(
        file_data, 
        'main-container', 
        include_fields=['name', 'type'],
        depth=2
    )
    assert 'error' not in result
    
    # Main container should have only specified fields plus id
    assert set(result['tree'].keys()) == {'id', 'name', 'type', 'children'}
    assert 'width' not in result['tree']
    assert 'height' not in result['tree']
    
    # Children should also have only the specified fields
    header_section = next(child for child in result['tree']['children'] if child['name'] == 'Header Section')
    assert set(header_section.keys()) == {'id', 'name', 'type', 'children'}
    
    # Test 5: Testing component references
    result = get_object_subtree_with_fields(file_data, 'cards-container')
    assert 'error' not in result
    
    # Find the first card
    card = next(child for child in result['tree']['children'] if child['name'] == 'Card 1')
    assert 'componentId' in card
    assert card['componentId'] == 'comp2'  # References the Card component
    
    # Test 6: Test layout properties in objects
    result = get_object_subtree_with_fields(file_data, 'main-container', include_fields=['layout', 'layoutFlexDir', 'layoutAlignItems', 'layoutJustifyContent'])
    assert 'error' not in result
    assert result['tree']['layout'] == 'flex'
    assert result['tree']['layoutFlexDir'] == 'column'
    assert result['tree']['layoutAlignItems'] == 'stretch'
    assert result['tree']['layoutJustifyContent'] == 'start'
    
    # Test 7: Test text content structure
    result = get_object_subtree_with_fields(file_data, 'hero-title', include_fields=['content'])
    assert 'error' not in result
    assert result['tree']['content']['type'] == 'root'
    assert len(result['tree']['content']['children']) == 1
    assert result['tree']['content']['children'][0]['type'] == 'paragraph'
    assert result['tree']['content']['children'][0]['children'][0]['text'] == 'Welcome to our Platform'
    
    # Test 8: Test applied tokens
    result = get_object_subtree_with_fields(file_data, 'hero-title', include_fields=['appliedTokens'])
    assert 'error' not in result
    assert 'appliedTokens' in result['tree']
    assert result['tree']['appliedTokens']['typography'] == 'typo1'

def test_get_object_subtree_with_fields_root_frame():
    """Test getting a filtered subtree starting from the root frame."""
    # Use same complex nested structure from the previous test
    file_data = {
        'data': {
            'pagesIndex': {
                'page1': {
                    'name': 'Complex Page',
                    'objects': {
                        # Root frame (level 0)
                        '00000000-0000-0000-0000-000000000000': {
                            'type': 'frame',
                            'name': 'Root Frame',
                            'width': 1920,
                            'height': 1080
                        },
                        # Main container (level 1)
                        'main-container': {
                            'type': 'frame',
                            'name': 'Main Container',
                            'parentId': '00000000-0000-0000-0000-000000000000'
                        }
                    }
                }
            }
        }
    }
    
    # Test getting the root frame
    result = get_object_subtree_with_fields(file_data, '00000000-0000-0000-0000-000000000000')
    assert 'error' not in result
    assert result['tree']['id'] == '00000000-0000-0000-0000-000000000000'
    assert result['tree']['type'] == 'frame'
    assert 'children' in result['tree']
    assert len(result['tree']['children']) == 1
    assert result['tree']['children'][0]['name'] == 'Main Container' 