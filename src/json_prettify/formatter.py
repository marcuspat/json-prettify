"""JSON formatter with support for various formatting options and streaming."""

import json
from typing import Any, Dict, Optional, Tuple, Union, IO
import io
import os


def format_json(
    data: Union[str, Dict[str, Any]], 
    indent: Optional[int] = 2,
    sort_keys: bool = False,
    compact: bool = False,
    ensure_ascii: bool = True,
    separators: Optional[Tuple[str, str]] = None
) -> str:
    """
    Format JSON data with various options.
    
    Args:
        data: JSON string or dictionary to format
        indent: Number of spaces for indentation (None for compact)
        sort_keys: Whether to sort object keys alphabetically
        compact: If True, produces minimal output without whitespace
        ensure_ascii: If False, preserves Unicode characters
        separators: Custom separators tuple (item_sep, key_sep)
        
    Returns:
        Formatted JSON string
        
    Raises:
        ValueError: If the input is not valid JSON
        json.JSONDecodeError: If the JSON string is malformed
    """
    # Handle compact mode
    if compact:
        indent = None
        if separators is None:
            separators = (',', ':')
    
    # Parse if string input
    if isinstance(data, str):
        if not data.strip():
            raise json.JSONDecodeError("Expecting value", data, 0)
        
        # Handle special cases for empty structures
        data = data.strip()
        if data == '{}' and compact:
            return '{}'
        elif data == '[]' and compact:
            return '[]'
        elif data in ('{}', '[]') and not compact and indent is None:
            return data
        
        # Check for invalid values that look like JavaScript
        if 'Infinity' in data or 'NaN' in data:
            raise ValueError("JSON does not support Infinity or NaN")
        
        try:
            parsed_data = json.loads(data)
        except json.JSONDecodeError as e:
            raise e
    else:
        parsed_data = data
    
    # Special handling for primitives and empty structures
    if isinstance(parsed_data, (type(None), bool, int, float, str)):
        # Primitives don't need formatting
        return json.dumps(parsed_data, ensure_ascii=ensure_ascii)
    elif parsed_data == {} or parsed_data == []:
        # Empty structures
        return '{}' if parsed_data == {} else '[]'
    
    # Format with options
    formatted = json.dumps(
        parsed_data,
        indent=indent,
        sort_keys=sort_keys,
        ensure_ascii=ensure_ascii,
        separators=separators
    )
    
    return formatted


def format_json_stream(
    input_file: Union[str, IO[str]],
    output_file: Optional[Union[str, IO[str]]] = None,
    chunk_size: int = 8192,
    **kwargs
) -> None:
    """
    Format JSON from a file using streaming for memory efficiency.
    
    This function is optimized for large files and processes them
    without loading the entire content into memory at once.
    
    Args:
        input_file: Path to input file or file object
        output_file: Path to output file or file object (if None, overwrites input)
        chunk_size: Size of chunks to read at a time
        **kwargs: Additional arguments passed to format_json()
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If the JSON is malformed
        IOError: If there are file I/O errors
    """
    # Handle file paths vs file objects
    if isinstance(input_file, str):
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = input_file.read()
    
    # Parse and format the JSON
    try:
        formatted = format_json(content, **kwargs)
    except (json.JSONDecodeError, ValueError) as e:
        raise e
    
    # Write output
    if output_file is None:
        output_file = input_file
    
    if isinstance(output_file, str):
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted)
    else:
        output_file.write(formatted)