"""Core functionality for JSON prettification."""

import json
from typing import Any, Union


def prettify_json(
    json_str: str,
    indent: int = 2,
    sort_keys: bool = False,
    compact: bool = False,
) -> str:
    """Prettify JSON string with specified formatting options.

    Args:
        json_str: JSON string to prettify
        indent: Number of spaces for indentation (default: 2)
        sort_keys: Whether to sort object keys alphabetically (default: False)
        compact: Whether to output compact JSON (default: False)

    Returns:
        Prettified JSON string

    Raises:
        json.JSONDecodeError: If the input is not valid JSON
    """
    # Parse JSON
    data = json.loads(json_str)

    # Format JSON based on options
    if compact:
        return json.dumps(data, separators=(",", ":"), sort_keys=sort_keys)
    else:
        return json.dumps(
            data,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=False,
        )


def validate_json(json_str: str) -> Union[bool, str]:
    """Validate if a string is valid JSON.

    Args:
        json_str: String to validate

    Returns:
        True if valid JSON, error message string if invalid
    """
    try:
        json.loads(json_str)
        return True
    except json.JSONDecodeError as e:
        return f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"


def minify_json(json_str: str) -> str:
    """Minify JSON by removing unnecessary whitespace.

    Args:
        json_str: JSON string to minify

    Returns:
        Minified JSON string

    Raises:
        json.JSONDecodeError: If the input is not valid JSON
    """
    data = json.loads(json_str)
    return json.dumps(data, separators=(",", ":"))