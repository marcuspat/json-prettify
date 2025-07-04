"""TDD tests for JSON formatter functionality.

These tests are written BEFORE implementation (TDD approach).
All tests should FAIL initially until implementation is complete.
"""

import json
import pytest
from pathlib import Path

# These imports will fail initially - that's expected in TDD
from json_prettify.formatter import format_json, format_json_stream


class TestFormatJson:
    """Test cases for format_json function."""

    def test_format_with_2_space_indent(self):
        """Test formatting JSON with 2-space indentation (default)."""
        input_json = '{"name":"John","age":30,"active":true}'
        expected = '{\n  "name": "John",\n  "age": 30,\n  "active": true\n}'
        
        result = format_json(input_json)
        assert result == expected
        
    def test_format_with_4_space_indent(self):
        """Test formatting JSON with 4-space indentation."""
        input_json = '{"name":"John","age":30,"nested":{"key":"value"}}'
        result = format_json(input_json, indent=4)
        
        # Check for 4-space indentation
        lines = result.split('\n')
        assert lines[1].startswith('    "name"')  # 4 spaces
        assert lines[4].startswith('        "key"')  # 8 spaces for nested
        
    def test_format_with_sort_keys(self):
        """Test formatting JSON with sorted keys."""
        input_json = '{"zebra":1,"apple":2,"middle":3,"banana":4}'
        result = format_json(input_json, sort_keys=True)
        
        # Keys should be in alphabetical order
        assert result.index('"apple"') < result.index('"banana"')
        assert result.index('"banana"') < result.index('"middle"')
        assert result.index('"middle"') < result.index('"zebra"')
        
    def test_format_with_compact_option(self):
        """Test formatting JSON with compact option (minified)."""
        input_json = '{\n  "name": "John",\n  "age": 30,\n  "items": [1, 2, 3]\n}'
        expected = '{"name":"John","age":30,"items":[1,2,3]}'
        
        result = format_json(input_json, compact=True)
        assert result == expected
        
    def test_format_preserves_unicode(self):
        """Test that formatting preserves Unicode characters."""
        input_json = '{"message":"Hello 世界 🌍","emoji":"👋"}'
        result = format_json(input_json)
        
        assert "世界" in result
        assert "🌍" in result
        assert "👋" in result
        
    def test_format_with_ensure_ascii_false(self):
        """Test formatting with ensure_ascii=False to preserve Unicode."""
        input_json = '{"text":"こんにちは"}'
        result = format_json(input_json, ensure_ascii=False)
        
        assert "こんにちは" in result
        assert "\\u" not in result  # Should not have Unicode escapes
        
    def test_format_deeply_nested_json(self):
        """Test formatting deeply nested JSON structures."""
        nested_data = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        input_json = json.dumps(nested_data, separators=(',', ':'))
        
        result = format_json(input_json, indent=2)
        
        # Check progressive indentation
        lines = result.split('\n')
        assert any('          "level5"' in line for line in lines)  # 10 spaces (5 levels * 2)
        
    def test_format_with_custom_separators(self):
        """Test formatting with custom separators."""
        input_json = '{"items":[1,2,3],"active":true}'
        result = format_json(input_json, indent=None, separators=(',', ': '))
        
        # Should be compact but with space after colons
        assert '{"items": [1,2,3],"active": true}' in result.replace(' ', '')


class TestFormatJsonStream:
    """Test cases for streaming JSON formatter (for large files)."""
    
    def test_stream_format_basic(self, tmp_path):
        """Test streaming format for basic JSON."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        # Create a moderately sized JSON file
        data = {"items": [{"id": i, "name": f"Item {i}"} for i in range(100)]}
        input_file.write_text(json.dumps(data))
        
        # Format using streaming
        format_json_stream(str(input_file), str(output_file), indent=2)
        
        # Verify output
        assert output_file.exists()
        result = json.loads(output_file.read_text())
        assert len(result["items"]) == 100
        
    def test_stream_format_large_file(self, tmp_path):
        """Test streaming format handles large files efficiently."""
        input_file = tmp_path / "large.json"
        output_file = tmp_path / "large_formatted.json"
        
        # Create a large JSON file (>10MB)
        large_data = {
            "records": [
                {
                    "id": i,
                    "data": "x" * 1000,  # 1KB per record
                    "nested": {"value": i * 2}
                }
                for i in range(10000)  # 10K records = ~10MB
            ]
        }
        input_file.write_text(json.dumps(large_data))
        
        # Format using streaming (should not load entire file into memory)
        format_json_stream(str(input_file), str(output_file), indent=2)
        
        # Verify output exists and is valid
        assert output_file.exists()
        assert output_file.stat().st_size > input_file.stat().st_size  # Formatted is larger
        
    def test_stream_format_with_options(self, tmp_path):
        """Test streaming format with various options."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        
        data = {"z": 1, "a": 2, "m": 3}
        input_file.write_text(json.dumps(data))
        
        # Format with sort_keys
        format_json_stream(str(input_file), str(output_file), indent=2, sort_keys=True)
        
        result_text = output_file.read_text()
        assert result_text.index('"a"') < result_text.index('"m"')
        assert result_text.index('"m"') < result_text.index('"z"')
        
    def test_stream_format_invalid_json(self, tmp_path):
        """Test streaming format handles invalid JSON gracefully."""
        input_file = tmp_path / "invalid.json"
        output_file = tmp_path / "output.json"
        
        input_file.write_text('{"invalid": json}')
        
        with pytest.raises(json.JSONDecodeError):
            format_json_stream(str(input_file), str(output_file))
            
    def test_stream_format_memory_efficiency(self, tmp_path):
        """Test that streaming doesn't load entire file into memory."""
        input_file = tmp_path / "huge.json"
        output_file = tmp_path / "huge_formatted.json"
        
        # Create a JSON file with streaming write
        with open(input_file, 'w') as f:
            f.write('{"items": [')
            for i in range(100000):  # 100K items
                if i > 0:
                    f.write(',')
                f.write(f'{{"id": {i}, "data": "{"x" * 100}"}}')
            f.write(']}')
        
        # This should complete without memory errors
        format_json_stream(str(input_file), str(output_file), chunk_size=8192)
        
        assert output_file.exists()


class TestFormatJsonEdgeCases:
    """Test edge cases for JSON formatting."""
    
    def test_format_empty_json(self):
        """Test formatting empty JSON structures."""
        assert format_json('{}') == '{}'
        assert format_json('[]') == '[]'
        
    def test_format_json_primitives(self):
        """Test formatting JSON primitive values."""
        assert format_json('null') == 'null'
        assert format_json('true') == 'true'
        assert format_json('false') == 'false'
        assert format_json('42') == '42'
        assert format_json('"string"') == '"string"'
        
    def test_format_special_float_values(self):
        """Test formatting special float values."""
        # JSON doesn't support Infinity or NaN, should raise error
        with pytest.raises(ValueError):
            format_json('{"value": Infinity}')
            
    def test_format_with_circular_reference_detection(self):
        """Test that formatter detects circular references."""
        # This would need special handling in implementation
        # JSON doesn't support circular references
        pass
        
    def test_format_preserves_number_precision(self):
        """Test that formatting preserves number precision."""
        input_json = '{"pi": 3.141592653589793, "large": 12345678901234567890}'
        result = format_json(input_json)
        
        # Verify precision is maintained
        parsed = json.loads(result)
        assert parsed["pi"] == 3.141592653589793
        assert parsed["large"] == 12345678901234567890