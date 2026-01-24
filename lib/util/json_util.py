"""Utility functions for JSON serialization and deserialization.

This module provides helper functions for reading, writing, and converting
JSON data to and from Python dictionaries.
"""

import json
from typing import Any, Dict, Optional


def get_from_string(json_str: str, print_error: bool = True) -> Optional[Dict[str, Any]]:
    """Convert a JSON string to a Python dictionary.

    Args:
        json_str: The JSON string to parse.
        print_error: Whether to print an error message if parsing fails.

    Returns:
        Parsed dictionary if successful, None if parsing fails.
    """
    try:
        return json.loads(json_str)
    except ValueError:
        if print_error:
            print("Invalid Json, ignored:\n{}".format(json_str))
        return None


def format_data(data: Dict[str, Any], flat: bool = False) -> str:
    """Convert a Python dictionary to a JSON string.

    Args:
        data: The dictionary to serialize.
        flat: If True, output compact JSON without indentation.
              If False, output pretty-printed JSON with 4-space indentation.

    Returns:
        JSON string representation of the data.
    """
    if flat:
        return json.dumps(data)
    else:
        return json.dumps(data, indent=4, sort_keys=True)


def get_from_path(path: str) -> Dict[str, Any]:
    """Load JSON data from a file path.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dictionary from the JSON file.
    """
    with open(path, "r") as f:
        return json.load(f)


def save_to_path(data: Dict[str, Any], path: str) -> None:
    """Save data to a JSON file.

    Args:
        data: The dictionary to save.
        path: Path to the output JSON file.
    """
    with open(path, "w") as output_file:
        json.dump(data, output_file, indent=4, sort_keys=True)
