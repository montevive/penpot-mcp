"""Command-line interface for validating Penpot files against a schema."""

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional, Tuple

from jsonschema import SchemaError, ValidationError, validate

from penpot_mcp.utils import config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Validate a Penpot JSON file against a schema')
    parser.add_argument('input_file', help='Path to the Penpot JSON file to validate')
    parser.add_argument(
        '--schema',
        '-s',
        default=os.path.join(
            config.RESOURCES_PATH,
            'penpot-schema.json'),
        help='Path to the JSON schema file (default: resources/penpot-schema.json)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output with detailed validation errors')
    return parser.parse_args()


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.

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


def validate_penpot_file(data: Dict[str, Any], schema: Dict[str,
                         Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a Penpot file against a schema.

    Args:
        data: The Penpot file data
        schema: The JSON schema

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e)
    except SchemaError as e:
        return False, f"Schema error: {str(e)}"


def main() -> None:
    """Main entry point for the command."""
    args = parse_args()

    # Load the files
    print(f"Loading Penpot file: {args.input_file}")
    data = load_json_file(args.input_file)

    print(f"Loading schema file: {args.schema}")
    schema = load_json_file(args.schema)

    # Validate the file
    print("Validating file...")
    is_valid, error = validate_penpot_file(data, schema)

    if is_valid:
        print("✅ Validation successful! The file conforms to the schema.")
    else:
        print("❌ Validation failed!")
        if args.verbose and error:
            print("\nError details:")
            print(error)
        sys.exit(1)


if __name__ == '__main__':
    main()
