"""Command-line interface for the Penpot tree visualization tool."""

import argparse
import json
import sys
from typing import Any, Dict

from penpot_mcp.tools.penpot_tree import build_tree, export_tree_to_dot, print_tree


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate a tree from a Penpot JSON file')
    parser.add_argument('input_file', help='Path to the Penpot JSON file')
    parser.add_argument('--filter', '-f', help='Filter nodes by regex pattern')
    parser.add_argument('--export', '-e', help='Export tree to a file (supports PNG, SVG, etc.)')
    return parser.parse_args()


def load_penpot_file(file_path: str) -> Dict[str, Any]:
    """
    Load a Penpot JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        The loaded JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file isn't valid JSON
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"Error: File not found: {file_path}")
    except json.JSONDecodeError:
        sys.exit(f"Error: Invalid JSON file: {file_path}")


def main() -> None:
    """Main entry point for the command."""
    args = parse_args()

    # Load the Penpot file
    data = load_penpot_file(args.input_file)

    # Build the tree
    root = build_tree(data)

    # Export the tree if requested
    if args.export:
        export_tree_to_dot(root, args.export, args.filter)

    # Print the tree
    print_tree(root, args.filter)


if __name__ == '__main__':
    main()
