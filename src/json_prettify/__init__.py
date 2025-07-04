"""JSON Prettify - A Python CLI tool for pretty-printing JSON with syntax highlighting."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "you@example.com"

from .prettify import prettify_json
from .formatter import format_json, format_json_stream
from .validator import (
    validate_json,
    validate_json_file,
    get_validation_errors,
    JSONValidationError,
    ValidationError
)

__all__ = [
    "prettify_json",
    "format_json",
    "format_json_stream",
    "validate_json",
    "validate_json_file", 
    "get_validation_errors",
    "JSONValidationError",
    "ValidationError"
]