"""Tests for prettify module."""

import json
import pytest

from json_prettify.prettify import prettify_json, validate_json, minify_json


class TestPrettifyJson:
    """Test cases for prettify_json function."""

    def test_basic_prettify(self):
        """Test basic JSON prettification."""
        input_json = '{"name": "John", "age": 30}'
        expected = '{\n  "name": "John",\n  "age": 30\n}'
        assert prettify_json(input_json) == expected

    def test_custom_indent(self):
        """Test prettification with custom indentation."""
        input_json = '{"name": "John", "age": 30}'
        result = prettify_json(input_json, indent=4)
        assert "    " in result  # 4 spaces

    def test_sort_keys(self):
        """Test prettification with sorted keys."""
        input_json = '{"z": 1, "a": 2, "m": 3}'
        result = prettify_json(input_json, sort_keys=True)
        # Check that 'a' comes before 'm' and 'm' comes before 'z'
        assert result.index('"a"') < result.index('"m"') < result.index('"z"')

    def test_compact_output(self):
        """Test compact JSON output."""
        input_json = '{"name": "John", "age": 30}'
        result = prettify_json(input_json, compact=True)
        assert result == '{"name":"John","age":30}'

    def test_nested_json(self):
        """Test prettification of nested JSON."""
        input_json = '{"user": {"name": "John", "address": {"city": "NYC"}}}'
        result = prettify_json(input_json)
        assert "  " in result  # Check for indentation
        assert result.count("{") == 3  # Three opening braces

    def test_array_json(self):
        """Test prettification of JSON with arrays."""
        input_json = '{"items": [1, 2, 3], "names": ["Alice", "Bob"]}'
        result = prettify_json(input_json)
        assert "[\n" in result or "[ " in result  # Array formatting

    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        input_json = '{"message": "Hello 世界 🌍"}'
        result = prettify_json(input_json)
        assert "世界" in result
        assert "🌍" in result

    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            prettify_json('{"invalid": json}')


class TestValidateJson:
    """Test cases for validate_json function."""

    def test_valid_json(self):
        """Test validation of valid JSON."""
        assert validate_json('{"valid": true}') is True
        assert validate_json('[]') is True
        assert validate_json('null') is True

    def test_invalid_json(self):
        """Test validation of invalid JSON."""
        result = validate_json('{"invalid": json}')
        assert isinstance(result, str)
        assert "Invalid JSON" in result


class TestMinifyJson:
    """Test cases for minify_json function."""

    def test_minify_basic(self):
        """Test basic JSON minification."""
        input_json = '{\n  "name": "John",\n  "age": 30\n}'
        expected = '{"name":"John","age":30}'
        assert minify_json(input_json) == expected

    def test_minify_with_arrays(self):
        """Test minification with arrays."""
        input_json = '{\n  "items": [\n    1,\n    2,\n    3\n  ]\n}'
        expected = '{"items":[1,2,3]}'
        assert minify_json(input_json) == expected

    def test_minify_already_minified(self):
        """Test minifying already minified JSON."""
        input_json = '{"compact":true}'
        assert minify_json(input_json) == input_json