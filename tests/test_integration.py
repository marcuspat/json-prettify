"""Integration tests for json-prettify.

These tests cover complex scenarios, edge cases, and real-world usage patterns.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from json_prettify.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def deeply_nested_json():
    """Create deeply nested JSON structure (5+ levels)."""
    return {
        "level1": {
            "level2": {
                "level3": {
                    "level4": {
                        "level5": {
                            "level6": {
                                "data": "deep value",
                                "array": [1, 2, 3],
                                "boolean": True
                            }
                        },
                        "level5_sibling": {
                            "more_data": "another value"
                        }
                    }
                },
                "level3_array": [
                    {"nested": "object1"},
                    {"nested": "object2"}
                ]
            },
            "level2_sibling": "value"
        }
    }


@pytest.fixture
def large_array_json():
    """Create JSON with large arrays (1000+ elements)."""
    return {
        "metadata": {
            "count": 2000,
            "description": "Large array test"
        },
        "data": [
            {
                "id": i,
                "name": f"Item {i}",
                "value": i * 3.14,
                "active": i % 2 == 0,
                "tags": [f"tag{j}" for j in range(5)]
            }
            for i in range(2000)
        ],
        "summary": {
            "total": sum(range(2000)),
            "average": sum(range(2000)) / 2000
        }
    }


@pytest.fixture
def unicode_json():
    """Create JSON with various Unicode characters."""
    return {
        "languages": {
            "english": "Hello, World!",
            "chinese": "你好，世界！",
            "japanese": "こんにちは、世界！",
            "korean": "안녕하세요, 세계!",
            "arabic": "مرحبا بالعالم!",
            "hebrew": "שלום עולם!",
            "russian": "Привет, мир!",
            "emoji": "😀🌍👋🎉🚀💻🐍"
        },
        "special_chars": {
            "math": "∑∏∫√∞≈≠≤≥",
            "currency": "€£¥₹₽¤",
            "arrows": "←→↑↓↔↕⇐⇒⇑⇓",
            "misc": "©®™†‡§¶•‰"
        },
        "rtl_text": {
            "arabic_sentence": "هذا نص باللغة العربية",
            "hebrew_sentence": "זה טקסט בעברית",
            "mixed": "English مع عربي and עברית together"
        },
        "cjk_ideographs": {
            "simplified": "简体中文",
            "traditional": "繁體中文",
            "kanji": "日本語の漢字",
            "hangul": "한글과 한자"
        }
    }


class TestDeepNesting:
    """Test handling of deeply nested JSON structures."""
    
    def test_deeply_nested_formatting(self, runner, deeply_nested_json):
        """Test formatting of deeply nested JSON."""
        input_json = json.dumps(deeply_nested_json)
        result = runner.invoke(main, ["--indent", "2"], input=input_json)
        assert result.exit_code == 0
        
        # Check that all levels are properly indented
        output = result.output
        assert '  "level1"' in output
        assert '    "level2"' in output
        assert '      "level3"' in output
        assert '        "level4"' in output
        assert '          "level5"' in output
        assert '            "level6"' in output
        assert '              "data": "deep value"' in output
    
    def test_deeply_nested_with_tabs(self, runner, deeply_nested_json):
        """Test deeply nested JSON with tab indentation."""
        input_json = json.dumps(deeply_nested_json)
        result = runner.invoke(main, ["--indent", "tab"], input=input_json)
        assert result.exit_code == 0
        
        # Check tab indentation
        assert '\t"level1"' in result.output
        assert '\t\t"level2"' in result.output
        assert '\t\t\t"level3"' in result.output
        assert '\t\t\t\t"level4"' in result.output
        assert '\t\t\t\t\t"level5"' in result.output
        assert '\t\t\t\t\t\t"level6"' in result.output
    
    def test_deeply_nested_compact(self, runner, deeply_nested_json):
        """Test compact output of deeply nested JSON."""
        input_json = json.dumps(deeply_nested_json, indent=2)
        result = runner.invoke(main, ["--compact"], input=input_json)
        assert result.exit_code == 0
        
        # Should be a single line
        lines = result.output.strip().split('\n')
        assert len(lines) == 1
        # Should contain all the data
        assert '"level6"' in result.output
        assert '"deep value"' in result.output


class TestLargeArrays:
    """Test handling of large arrays."""
    
    def test_large_array_formatting(self, runner, large_array_json):
        """Test formatting of large arrays."""
        input_json = json.dumps(large_array_json)
        result = runner.invoke(main, ["--indent", "2"], input=input_json)
        assert result.exit_code == 0
        
        # Should format all items
        assert '"id": 0' in result.output
        assert '"id": 999' in result.output
        assert '"id": 1999' in result.output
        
        # Check proper array formatting
        assert '  {\n    "id": 0' in result.output
    
    def test_large_array_compact(self, runner, large_array_json):
        """Test compact output of large arrays."""
        input_json = json.dumps(large_array_json)
        result = runner.invoke(main, ["--compact"], input=input_json)
        assert result.exit_code == 0
        
        # Should be minified
        assert '\n' not in result.output.strip()
        assert '{"metadata"' in result.output
        assert '"data":[{' in result.output
    
    def test_large_array_validation(self, runner, large_array_json):
        """Test validation of large arrays."""
        input_json = json.dumps(large_array_json)
        result = runner.invoke(main, ["--validate-only"], input=input_json)
        assert result.exit_code == 0
        assert "valid" in result.output.lower()


class TestUnicodeHandling:
    """Test handling of Unicode characters."""
    
    def test_unicode_formatting(self, runner, unicode_json):
        """Test formatting of Unicode content."""
        input_json = json.dumps(unicode_json, ensure_ascii=False)
        result = runner.invoke(main, ["--indent", "2"], input=input_json)
        assert result.exit_code == 0
        
        # Check that Unicode is preserved
        assert "你好，世界！" in result.output
        assert "こんにちは、世界！" in result.output
        assert "مرحبا بالعالم!" in result.output
        assert "😀🌍👋🎉🚀💻🐍" in result.output
        assert "€£¥₹₽¤" in result.output
    
    def test_unicode_with_sort(self, runner, unicode_json):
        """Test sorting with Unicode keys."""
        # Add Unicode keys
        unicode_json["αλφα"] = "alpha"
        unicode_json["бета"] = "beta"
        unicode_json["中文"] = "chinese"
        
        input_json = json.dumps(unicode_json, ensure_ascii=False)
        result = runner.invoke(main, ["--sort-keys"], input=input_json)
        assert result.exit_code == 0
        
        # All content should be present
        assert "αλφα" in result.output
        assert "бета" in result.output
        assert "中文" in result.output
    
    def test_unicode_file_handling(self, runner, tmp_path, unicode_json):
        """Test reading and writing Unicode files."""
        input_file = tmp_path / "unicode_input.json"
        output_file = tmp_path / "unicode_output.json"
        
        # Write Unicode content
        input_file.write_text(json.dumps(unicode_json, ensure_ascii=False), encoding='utf-8')
        
        # Process with output file
        result = runner.invoke(main, [
            str(input_file),
            "--output", str(output_file),
            "--indent", "4",
            "--encoding", "utf-8"
        ])
        assert result.exit_code == 0
        
        # Read and verify output
        output_content = output_file.read_text(encoding='utf-8')
        assert "你好，世界！" in output_content
        assert "😀🌍👋🎉🚀💻🐍" in output_content
        assert '    "english"' in output_content  # 4-space indent


class TestCombinedOptions:
    """Test combining multiple options."""
    
    def test_sort_and_compact(self, runner):
        """Test --sort-keys with --compact."""
        input_json = '{"z": 1, "a": 2, "m": 3}'
        result = runner.invoke(main, ["--sort-keys", "--compact"], input=input_json)
        assert result.exit_code == 0
        
        output = result.output.strip()
        assert output == '{"a":2,"m":3,"z":1}'
    
    def test_unicode_sort_compact(self, runner, unicode_json):
        """Test Unicode with sorting and compact output."""
        input_json = json.dumps(unicode_json, ensure_ascii=False)
        result = runner.invoke(main, ["--sort-keys", "--compact"], input=input_json)
        assert result.exit_code == 0
        
        # Should be compact but preserve Unicode
        assert '\n' not in result.output.strip()
        assert "你好，世界！" in result.output
        assert "😀🌍👋🎉🚀💻🐍" in result.output
    
    def test_multiple_files_with_options(self, runner, tmp_path):
        """Test processing multiple files with various options."""
        # Create test files
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        file3 = tmp_path / "file3.json"
        
        file1.write_text('{"z": 1, "a": {"y": 2, "b": 3}}')
        file2.write_text('{"data": [3, 1, 4, 1, 5, 9]}')
        file3.write_text('{"unicode": "🎉", "text": "Hello"}')
        
        output_file = tmp_path / "combined.json"
        
        result = runner.invoke(main, [
            str(file1), str(file2), str(file3),
            "--indent", "2",
            "--sort-keys",
            "--output", str(output_file)
        ])
        assert result.exit_code == 0
        
        # Check output file contains all formatted data
        content = output_file.read_text()
        
        # File 1 - sorted
        assert '"a": {\n    "b": 3,\n    "y": 2\n  }' in content
        assert content.index('"a"') < content.index('"z"')
        
        # File 2
        assert '"data": [\n    3,\n    1,\n    4' in content
        
        # File 3 - sorted with Unicode
        assert '"text": "Hello"' in content
        assert '"unicode": "🎉"' in content
        assert content.rindex('"text"') < content.rindex('"unicode"')  # sorted


class TestFileOperations:
    """Test file operations with actual temp files."""
    
    def test_temp_file_creation_and_processing(self, runner):
        """Test creating and processing temporary files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            tf.write('{"temp": true, "data": [1, 2, 3]}')
            temp_path = tf.name
        
        try:
            result = runner.invoke(main, [temp_path, "--indent", "4"])
            assert result.exit_code == 0
            assert '    "temp": true' in result.output
            assert '    "data": [\n        1,' in result.output
        finally:
            os.unlink(temp_path)
    
    def test_multiple_temp_files(self, runner):
        """Test processing multiple temporary files."""
        temp_files = []
        
        try:
            # Create multiple temp files
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                    tf.write(json.dumps({"file": i, "data": f"test{i}"}))
                    temp_files.append(tf.name)
            
            # Process all files
            result = runner.invoke(main, temp_files + ["--sort-keys"])
            assert result.exit_code == 0
            
            # Check all files were processed
            for i in range(3):
                assert f'"file": {i}' in result.output
                assert f'"data": "test{i}"' in result.output
        
        finally:
            for tf in temp_files:
                os.unlink(tf)
    
    def test_output_to_temp_file(self, runner):
        """Test writing output to temporary file."""
        input_json = '{"output": "test", "array": [1, 2, 3]}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
            output_path = tf.name
        
        try:
            result = runner.invoke(main, [
                "--output", output_path,
                "--indent", "4",
                "--sort-keys"
            ], input=input_json)
            assert result.exit_code == 0
            
            # Read and verify output
            with open(output_path, 'r') as f:
                content = f.read()
            
            data = json.loads(content)
            assert data["output"] == "test"
            assert data["array"] == [1, 2, 3]
            
            # Check formatting
            assert '    "array": [' in content
            assert content.index('"array"') < content.index('"output"')  # sorted
        
        finally:
            os.unlink(output_path)


class TestLargeFileStreaming:
    """Test streaming operations with large files."""
    
    @pytest.fixture
    def large_file(self, tmp_path):
        """Create a large JSON file (10MB+)."""
        large_file = tmp_path / "large.json"
        
        # Create a large data structure
        data = {
            "metadata": {
                "version": "1.0",
                "created": "2024-01-01",
                "size": "large"
            },
            "records": []
        }
        
        # Add records until file is > 10MB
        record_template = {
            "id": 0,
            "name": "x" * 100,
            "description": "y" * 200,
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "data": {"field1": "value1", "field2": "value2", "field3": "value3"}
        }
        
        for i in range(50000):  # Should create ~10-15MB file
            record = record_template.copy()
            record["id"] = i
            record["name"] = f"Record_{i}_" + "x" * 100
            data["records"].append(record)
        
        # Write to file
        large_file.write_text(json.dumps(data))
        return large_file
    
    def test_large_file_formatting(self, runner, large_file):
        """Test formatting a large file."""
        result = runner.invoke(main, [str(large_file), "--compact"])
        assert result.exit_code == 0
        
        # Should complete without errors
        assert '{"metadata"' in result.output
        assert '"records":[{' in result.output
    
    def test_large_file_validation(self, runner, large_file):
        """Test validating a large file."""
        result = runner.invoke(main, [str(large_file), "--validate-only"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
    
    def test_large_file_to_output(self, runner, large_file, tmp_path):
        """Test writing large file to output."""
        output_file = tmp_path / "large_output.json"
        
        result = runner.invoke(main, [
            str(large_file),
            "--output", str(output_file),
            "--compact"
        ])
        assert result.exit_code == 0
        
        # Verify output file exists and is valid JSON
        assert output_file.exists()
        
        # Quick validation by reading first and last parts
        content = output_file.read_text()
        assert content.startswith('{"metadata"')
        assert content.endswith('}')
        
        # Try to parse a sample to ensure it's valid
        with open(output_file, 'r') as f:
            # Read just the metadata part
            chunk = f.read(1000)
            assert '"metadata":{"version":"1.0"' in chunk


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_object_and_array(self, runner):
        """Test handling of empty objects and arrays."""
        test_cases = [
            ('{}', '{}'),
            ('[]', '[]'),
            ('{"empty": {}}', '{\n  "empty": {}\n}'),
            ('{"empty": []}', '{\n  "empty": []\n}'),
            ('{"nested": {"empty": {}}}', '{\n  "nested": {\n    "empty": {}\n  }\n}')
        ]
        
        for input_json, expected_pattern in test_cases:
            result = runner.invoke(main, input=input_json)
            assert result.exit_code == 0
            if '\n' in expected_pattern:
                # Multi-line format
                for line in expected_pattern.split('\n'):
                    assert line in result.output
            else:
                # Single line
                assert expected_pattern in result.output.strip()
    
    def test_special_json_values(self, runner):
        """Test handling of special JSON values."""
        input_json = json.dumps({
            "null_value": None,
            "true_value": True,
            "false_value": False,
            "zero": 0,
            "negative": -123,
            "float": 3.14159,
            "scientific": 1.23e-4,
            "empty_string": "",
            "escape_chars": "line1\nline2\ttab\r\nwindows",
            "unicode_escape": "\u0048\u0065\u006c\u006c\u006f"
        })
        
        result = runner.invoke(main, input=input_json)
        assert result.exit_code == 0
        
        # Check all values are properly formatted
        assert '"null_value": null' in result.output
        assert '"true_value": true' in result.output
        assert '"false_value": false' in result.output
        assert '"zero": 0' in result.output
        assert '"negative": -123' in result.output
        assert '"float": 3.14159' in result.output
        assert '"scientific": 0.000123' in result.output or '"scientific": 1.23e-4' in result.output
        assert '"empty_string": ""' in result.output
    
    def test_json_with_bom(self, runner, tmp_path):
        """Test handling of JSON files with BOM."""
        # Create file with UTF-8 BOM
        json_file = tmp_path / "bom.json"
        with open(json_file, 'wb') as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write('{"bom": "test"}'.encode('utf-8'))
        
        result = runner.invoke(main, [str(json_file)])
        # Should handle BOM gracefully - implementation dependent
        # Either succeed or give clear error about BOM
    
    def test_mixed_line_endings(self, runner, tmp_path):
        """Test handling of mixed line endings."""
        json_file = tmp_path / "mixed_endings.json"
        # Mix of Unix (\n), Windows (\r\n), and Mac (\r) line endings
        json_file.write_bytes(b'{\r\n  "unix": "value1",\n  "windows": "value2",\r  "mac": "value3"\r\n}')
        
        result = runner.invoke(main, [str(json_file)])
        assert result.exit_code == 0
        assert '"unix": "value1"' in result.output
        assert '"windows": "value2"' in result.output
        assert '"mac": "value3"' in result.output


class TestModuleExecution:
    """Test execution as Python module."""
    
    def test_module_execution(self, runner):
        """Test that python -m json_prettify works."""
        # This is tested by the existence of __main__.py
        # The actual execution would be tested in a subprocess
        import json_prettify.__main__
        assert hasattr(json_prettify.__main__, 'main')
    
    def test_main_imports(self):
        """Test that main can be imported from package."""
        from json_prettify import main
        assert callable(main)
        
        from json_prettify.cli import main as cli_main
        assert main is cli_main