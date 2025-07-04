"""TDD tests for JSON validator functionality.

These tests are written BEFORE implementation (TDD approach).
All tests should FAIL initially until implementation is complete.
"""

import pytest
from pathlib import Path

# These imports will fail initially - that's expected in TDD
from json_prettify.validator import (
    validate_json,
    validate_json_file,
    get_validation_errors,
    JSONValidationError
)


class TestValidateJson:
    """Test cases for validate_json function."""
    
    def test_validate_valid_json_objects(self):
        """Test validation of valid JSON objects."""
        assert validate_json('{}') is True
        assert validate_json('{"key": "value"}') is True
        assert validate_json('{"name": "John", "age": 30}') is True
        assert validate_json('{"nested": {"key": "value"}}') is True
        
    def test_validate_valid_json_arrays(self):
        """Test validation of valid JSON arrays."""
        assert validate_json('[]') is True
        assert validate_json('[1, 2, 3]') is True
        assert validate_json('["a", "b", "c"]') is True
        assert validate_json('[{"id": 1}, {"id": 2}]') is True
        
    def test_validate_valid_json_primitives(self):
        """Test validation of valid JSON primitive values."""
        assert validate_json('null') is True
        assert validate_json('true') is True
        assert validate_json('false') is True
        assert validate_json('42') is True
        assert validate_json('-3.14') is True
        assert validate_json('"hello"') is True
        
    def test_validate_invalid_json_syntax(self):
        """Test validation detects syntax errors."""
        # Missing closing bracket
        result = validate_json('{"unclosed": "bracket"')
        assert result is not True
        assert isinstance(result, str)
        assert "line" in result.lower()
        
        # Trailing comma
        result = validate_json('{"key": "value",}')
        assert result is not True
        assert "trailing comma" in result.lower()
        
        # Single quotes
        result = validate_json("{'key': 'value'}")
        assert result is not True
        assert "single quotes" in result.lower() or "quote" in result.lower()
        
    def test_validate_error_messages_with_line_numbers(self):
        """Test that error messages include line numbers."""
        json_with_error = '''{"valid": "line1",
"invalid": "line2"
"missing": "comma"}'''
        
        result = validate_json(json_with_error)
        assert result is not True
        assert "line 3" in result or "line 2" in result  # Error around line 2-3
        
    def test_validate_multiple_errors(self):
        """Test validation reports multiple errors when present."""
        json_with_errors = '''{"key1": 'single quotes',
"key2": "valid",
"key3": "missing comma"
"key4": "value",}'''
        
        result = validate_json(json_with_errors)
        assert result is not True
        # Should mention at least one error
        assert "error" in result.lower()
        
    def test_validate_unicode_handling(self):
        """Test validation handles Unicode correctly."""
        assert validate_json('{"text": "Hello 世界"}') is True
        assert validate_json('{"emoji": "👋🌍"}') is True
        assert validate_json('{"escaped": "\\u4e16\\u754c"}') is True
        
    def test_validate_edge_cases(self):
        """Test validation of edge cases."""
        # Empty string
        result = validate_json('')
        assert result is not True
        assert "empty" in result.lower() or "no data" in result.lower()
        
        # Just whitespace
        result = validate_json('   \n\t  ')
        assert result is not True
        
        # Incomplete JSON
        result = validate_json('{')
        assert result is not True
        
        # Invalid escape sequences
        result = validate_json('{"bad": "\\x"}')
        assert result is not True


class TestValidateJsonFile:
    """Test cases for validate_json_file function."""
    
    def test_validate_valid_json_file(self, tmp_path):
        """Test validation of valid JSON file."""
        json_file = tmp_path / "valid.json"
        json_file.write_text('{"valid": true}')
        
        assert validate_json_file(str(json_file)) is True
        
    def test_validate_invalid_json_file(self, tmp_path):
        """Test validation of invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"invalid": json}')
        
        result = validate_json_file(str(json_file))
        assert result is not True
        assert isinstance(result, str)
        assert "invalid.json" in result  # Should include filename
        
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = validate_json_file("/path/to/nonexistent.json")
        assert result is not True
        assert "not found" in result.lower() or "does not exist" in result.lower()
        
    def test_validate_file_with_bom(self, tmp_path):
        """Test validation handles files with BOM (Byte Order Mark)."""
        json_file = tmp_path / "bom.json"
        # Write UTF-8 BOM followed by valid JSON
        json_file.write_bytes(b'\xef\xbb\xbf{"valid": true}')
        
        assert validate_json_file(str(json_file)) is True
        
    def test_validate_large_file(self, tmp_path):
        """Test validation of large JSON files."""
        json_file = tmp_path / "large.json"
        
        # Create a large but valid JSON file
        large_data = {"items": [{"id": i} for i in range(10000)]}
        import json
        json_file.write_text(json.dumps(large_data))
        
        assert validate_json_file(str(json_file)) is True


class TestGetValidationErrors:
    """Test cases for get_validation_errors function."""
    
    def test_get_errors_for_valid_json(self):
        """Test getting errors for valid JSON returns empty list."""
        errors = get_validation_errors('{"valid": true}')
        assert errors == []
        
    def test_get_errors_with_details(self):
        """Test getting detailed error information."""
        json_with_error = '{"key": "value",}'
        errors = get_validation_errors(json_with_error)
        
        assert len(errors) > 0
        error = errors[0]
        
        # Error should have these attributes
        assert hasattr(error, 'message')
        assert hasattr(error, 'line')
        assert hasattr(error, 'column')
        assert error.line > 0
        assert error.column >= 0
        
    def test_get_multiple_errors(self):
        """Test getting multiple validation errors."""
        json_with_errors = '''{"key1": 'single',
"key2": "valid"
"key3": "missing"}'''
        
        errors = get_validation_errors(json_with_errors)
        assert len(errors) >= 1  # At least one error
        
        # Each error should have details
        for error in errors:
            assert hasattr(error, 'message')
            assert hasattr(error, 'line')
            
    def test_get_errors_with_context(self):
        """Test that errors include context from the JSON."""
        json_with_error = '{"long_key_name": "some_value",}'
        errors = get_validation_errors(json_with_error)
        
        assert len(errors) > 0
        error = errors[0]
        
        # Error context might include the problematic part
        assert "," in error.message or "comma" in error.message.lower()


class TestJSONValidationError:
    """Test cases for JSONValidationError exception class."""
    
    def test_validation_error_creation(self):
        """Test creating validation error with details."""
        error = JSONValidationError(
            message="Unexpected token",
            line=5,
            column=10,
            context="...near this text..."
        )
        
        assert error.message == "Unexpected token"
        assert error.line == 5
        assert error.column == 10
        assert error.context == "...near this text..."
        
    def test_validation_error_string_representation(self):
        """Test string representation of validation error."""
        error = JSONValidationError(
            message="Missing comma",
            line=3,
            column=15
        )
        
        error_str = str(error)
        assert "Missing comma" in error_str
        assert "line 3" in error_str
        assert "column 15" in error_str
        
    def test_validation_error_without_position(self):
        """Test validation error without line/column info."""
        error = JSONValidationError(message="Invalid JSON")
        
        assert error.message == "Invalid JSON"
        assert error.line is None
        assert error.column is None


class TestValidatorEdgeCases:
    """Test edge cases for JSON validation."""
    
    def test_validate_deeply_nested_json(self):
        """Test validation of deeply nested structures."""
        # Create deeply nested JSON (100 levels)
        deep_json = '{"a":' * 100 + '1' + '}' * 100
        
        # Should validate successfully (within nesting limits)
        assert validate_json(deep_json) is True
        
    def test_validate_json_with_duplicated_keys(self):
        """Test validation detects duplicate keys."""
        # Standard JSON allows duplicate keys, but it's often an error
        json_with_dupes = '{"key": "value1", "key": "value2"}'
        
        # Validator might warn about this
        result = validate_json(json_with_dupes, strict=True)
        if result is not True:
            assert "duplicate" in result.lower()
            
    def test_validate_json_size_limits(self):
        """Test validation handles size limits gracefully."""
        # Create a very large JSON string (1MB+)
        large_json = '{"data": "' + 'x' * 1024 * 1024 + '"}'
        
        # Should still validate
        result = validate_json(large_json)
        assert result is True or "size" in str(result).lower()
        
    def test_validate_special_number_formats(self):
        """Test validation of special number formats."""
        # Scientific notation
        assert validate_json('{"sci": 1.23e-10}') is True
        
        # Large numbers
        assert validate_json('{"big": 12345678901234567890}') is True
        
        # Negative zero
        assert validate_json('{"negzero": -0}') is True
        
    def test_validate_control_characters(self):
        """Test validation of control characters in strings."""
        # Unescaped control characters are invalid
        result = validate_json('{"text": "Line1\nLine2"}')  # Raw newline
        if result is not True:
            assert "control" in result.lower() or "escape" in result.lower()