"""JSON validation functionality with detailed error reporting."""

import json
import os
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a JSON validation error with location information."""
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the validation error."""
        parts = [self.message]
        if self.line is not None:
            parts.append(f"at line {self.line}")
        if self.column is not None:
            parts.append(f"column {self.column}")
        if self.context:
            parts.append(f"near: {self.context}")
        return " ".join(parts)


class JSONValidationError(Exception):
    """Exception raised for JSON validation errors."""
    
    def __init__(
        self, 
        message: str, 
        line: Optional[int] = None, 
        column: Optional[int] = None,
        context: Optional[str] = None
    ):
        """Initialize validation error with details."""
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.context = context
    
    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [self.message]
        if self.line is not None:
            parts.append(f"at line {self.line}")
        if self.column is not None:
            parts.append(f"column {self.column}")
        if self.context:
            parts.append(f"near: {self.context}")
        return " ".join(parts)


def _get_line_and_column(text: str, pos: int) -> Tuple[int, int]:
    """Get line and column number from position in text."""
    lines = text[:pos].split('\n')
    line = len(lines)
    column = len(lines[-1]) + 1 if lines else 1
    return line, column


def _check_common_errors(json_string: str) -> Optional[str]:
    """Check for common JSON syntax errors."""
    if not json_string.strip():
        return "Empty or whitespace-only input"
    
    # Check for single quotes
    if "'" in json_string and not '"' in json_string:
        line_num = json_string[:json_string.index("'")].count('\n') + 1
        return f"Single quotes are not valid in JSON at line {line_num}"
    
    # Check for trailing commas (simple heuristic)
    stripped = json_string.strip()
    if stripped.endswith(',}') or stripped.endswith(',]'):
        lines = json_string.split('\n')
        for i, line in enumerate(lines):
            if line.strip().endswith(',}') or line.strip().endswith(',]'):
                return f"Trailing comma detected at line {i + 1}"
    
    # Check for incomplete JSON
    if stripped in ('{', '[', '"{', '"['):
        return "Incomplete JSON structure"
    
    return None


def validate_json(json_string: str, strict: bool = False) -> Union[bool, str]:
    """
    Validate a JSON string.
    
    Args:
        json_string: The JSON string to validate
        strict: If True, performs additional strict validation
        
    Returns:
        True if valid, error message string if invalid
    """
    # Check for common errors first
    common_error = _check_common_errors(json_string)
    if common_error:
        return common_error
    
    try:
        # Attempt to parse the JSON
        parsed = json.loads(json_string)
        
        # Additional strict mode checks
        if strict:
            # Check for duplicate keys (requires custom parser)
            # For now, just check if it's mentioned in the JSON
            if json_string.count('":') > len(set(k for k in parsed.keys())) if isinstance(parsed, dict) else 0:
                return "Possible duplicate keys detected"
        
        return True
        
    except json.JSONDecodeError as e:
        line, column = _get_line_and_column(json_string, e.pos)
        
        # Enhance error messages
        error_msg = str(e.msg).lower()
        
        if "expecting" in error_msg and "delimiter" in error_msg:
            return f"Missing comma or delimiter at line {line}, column {column}"
        elif "invalid" in error_msg and ("escape" in error_msg or "\\x" in str(e)):
            return f"Invalid escape sequence at line {line}, column {column}"
        elif "expecting value" in error_msg:
            if json_string.strip() == '':
                return "Empty input - no JSON data found"
            return f"Invalid value at line {line}, column {column}"
        elif "extra data" in error_msg:
            return f"Extra data after JSON at line {line}, column {column}"
        else:
            return f"JSON syntax error at line {line}, column {column}: {e.msg}"
    
    except ValueError as e:
        return f"Value error: {str(e)}"
    except Exception as e:
        return f"Validation error: {str(e)}"


def validate_json_file(filepath: str, encoding: str = 'utf-8') -> Union[bool, str]:
    """
    Validate a JSON file.
    
    Args:
        filepath: Path to the JSON file
        encoding: File encoding (default: utf-8)
        
    Returns:
        True if valid, error message string if invalid
    """
    # Check if file exists
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    
    try:
        with open(filepath, 'rb') as f:
            # Read raw bytes to handle BOM
            raw_data = f.read()
            
            # Handle UTF-8 BOM
            if raw_data.startswith(b'\xef\xbb\xbf'):
                raw_data = raw_data[3:]
            
            # Decode to string
            json_string = raw_data.decode(encoding)
        
        # Validate the content
        result = validate_json(json_string)
        
        # If invalid, prepend filename to error
        if result is not True:
            filename = os.path.basename(filepath)
            return f"{filename}: {result}"
        
        return True
        
    except UnicodeDecodeError as e:
        return f"Encoding error in {filepath}: {str(e)}"
    except IOError as e:
        return f"Error reading {filepath}: {str(e)}"
    except Exception as e:
        return f"Error validating {filepath}: {str(e)}"


def get_validation_errors(json_string: str) -> List[ValidationError]:
    """
    Get detailed validation errors for a JSON string.
    
    Args:
        json_string: The JSON string to validate
        
    Returns:
        List of ValidationError objects (empty if valid)
    """
    errors = []
    
    # Check for common errors
    common_error = _check_common_errors(json_string)
    if common_error:
        # Extract line number if present
        line = None
        if "line" in common_error:
            try:
                line = int(common_error.split("line")[1].split()[0])
            except:
                pass
        
        errors.append(ValidationError(
            message=common_error,
            line=line,
            column=0
        ))
        return errors
    
    try:
        json.loads(json_string)
        return []  # Valid JSON, no errors
        
    except json.JSONDecodeError as e:
        line, column = _get_line_and_column(json_string, e.pos)
        
        # Extract context around error
        lines = json_string.split('\n')
        if 0 <= line - 1 < len(lines):
            error_line = lines[line - 1]
            start = max(0, column - 20)
            end = min(len(error_line), column + 20)
            context = error_line[start:end].strip()
        else:
            context = None
        
        # Create detailed error message
        if "expecting" in e.msg.lower() and "delimiter" in e.msg.lower():
            message = "Missing comma between elements"
        elif "invalid" in e.msg.lower() and "escape" in e.msg.lower():
            message = "Invalid escape sequence in string"
        elif "expecting value" in e.msg.lower():
            message = "Expected a value but found invalid token"
        elif "extra data" in e.msg.lower():
            message = "Extra data after valid JSON"
        else:
            message = e.msg
        
        errors.append(ValidationError(
            message=message,
            line=line,
            column=column,
            context=context
        ))
        
    except Exception as e:
        errors.append(ValidationError(
            message=str(e),
            line=None,
            column=None
        ))
    
    return errors