"""TDD tests for CLI module.

These tests are written BEFORE implementation (TDD approach).
All tests should FAIL initially until implementation is complete.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

# This import will fail initially - that's expected in TDD
from json_prettify.cli import main


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test.json"
    json_file.write_text('{"name": "Test", "value": 123, "active": true}')
    return json_file


@pytest.fixture
def invalid_json_file(tmp_path):
    """Create a temporary invalid JSON file for testing."""
    json_file = tmp_path / "invalid.json"
    json_file.write_text('{"invalid": json}')
    return json_file


@pytest.fixture
def large_json_file(tmp_path):
    """Create a large JSON file for testing streaming."""
    json_file = tmp_path / "large.json"
    data = {"items": [{"id": i, "data": "x" * 100} for i in range(1000)]}
    json_file.write_text(json.dumps(data))
    return json_file


class TestCLIBasicOptions:
    """Test basic CLI options and functionality."""

    def test_version_option(self, runner):
        """Test --version flag shows version info."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "json-prettify" in result.output.lower()
        assert "version" in result.output.lower()
        # Should show semantic version like 1.0.0
        assert any(char.isdigit() for char in result.output)

    def test_help_option(self, runner):
        """Test --help flag shows comprehensive help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        
        # Check all options are documented
        assert "--indent" in result.output
        assert "--sort-keys" in result.output
        assert "--compact" in result.output
        assert "--validate-only" in result.output
        assert "--no-color" in result.output
        assert "--output" in result.output
        assert "--encoding" in result.output
        
        # Check description
        assert "Pretty-print JSON" in result.output or "Format JSON" in result.output


class TestCLIFileInput:
    """Test CLI file input handling."""

    def test_prettify_single_file(self, runner, sample_json_file):
        """Test prettifying a single JSON file."""
        result = runner.invoke(main, [str(sample_json_file)])
        assert result.exit_code == 0
        
        # Output should be formatted JSON
        lines = result.output.strip().split('\n')
        assert len(lines) > 1  # Should be multi-line
        assert lines[0] == '{'
        assert lines[-1] == '}'
        assert '  "name": "Test"' in result.output
        assert '  "value": 123' in result.output
        assert '  "active": true' in result.output

    def test_prettify_multiple_files(self, runner, tmp_path):
        """Test prettifying multiple JSON files."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        file1.write_text('{"file": 1}')
        file2.write_text('{"file": 2}')
        
        result = runner.invoke(main, [str(file1), str(file2)])
        assert result.exit_code == 0
        
        # Should show both files
        assert '"file": 1' in result.output
        assert '"file": 2' in result.output
        # Should indicate which file is which
        assert "file1.json" in result.output or "---" in result.output

    def test_file_not_found_error(self, runner):
        """Test error handling for non-existent file."""
        result = runner.invoke(main, ["/path/to/nonexistent.json"])
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()
        assert "nonexistent.json" in result.output

    def test_permission_denied_error(self, runner, tmp_path):
        """Test error handling for permission denied."""
        protected_file = tmp_path / "protected.json"
        protected_file.write_text('{"test": true}')
        
        # Make file unreadable (Unix only)
        if os.name != 'nt':
            os.chmod(protected_file, 0o000)
            
            result = runner.invoke(main, [str(protected_file)])
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "permission" in result.output.lower() or "access" in result.output.lower()
            
            # Restore permissions for cleanup
            os.chmod(protected_file, 0o644)


class TestCLIStdinInput:
    """Test CLI stdin input handling."""

    def test_prettify_from_stdin(self, runner):
        """Test prettifying JSON from stdin."""
        input_json = '{"compact":true,"needs":"formatting"}'
        result = runner.invoke(main, input=input_json)
        assert result.exit_code == 0
        
        # Should be formatted
        assert '{\n' in result.output
        assert '  "compact": true' in result.output
        assert '  "needs": "formatting"' in result.output

    def test_stdin_with_piped_input(self, runner):
        """Test stdin input simulating pipe."""
        input_json = '[1,2,3,{"nested":true}]'
        result = runner.invoke(main, ['-'], input=input_json)
        assert result.exit_code == 0
        
        # Should format array nicely
        assert '[\n' in result.output
        assert '  1,' in result.output
        assert '  {\n    "nested": true\n  }' in result.output

    def test_empty_stdin(self, runner):
        """Test handling of empty stdin."""
        result = runner.invoke(main, input='')
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "empty" in result.output.lower() or "no input" in result.output.lower()


class TestCLIFormattingOptions:
    """Test CLI formatting options."""

    def test_indent_option_with_2_spaces(self, runner):
        """Test --indent 2 option."""
        input_json = '{"level1":{"level2":"value"}}'
        result = runner.invoke(main, ["--indent", "2"], input=input_json)
        assert result.exit_code == 0
        
        lines = result.output.split('\n')
        # Check 2-space indentation
        assert any(line.startswith('  "level1"') for line in lines)
        assert any(line.startswith('    "level2"') for line in lines)

    def test_indent_option_with_4_spaces(self, runner):
        """Test --indent 4 option."""
        input_json = '{"level1":{"level2":"value"}}'
        result = runner.invoke(main, ["--indent", "4"], input=input_json)
        assert result.exit_code == 0
        
        lines = result.output.split('\n')
        # Check 4-space indentation
        assert any(line.startswith('    "level1"') for line in lines)
        assert any(line.startswith('        "level2"') for line in lines)

    def test_indent_option_with_tab(self, runner):
        """Test --indent tab option."""
        input_json = '{"level1":{"level2":"value"}}'
        result = runner.invoke(main, ["--indent", "tab"], input=input_json)
        assert result.exit_code == 0
        
        # Should use tab characters
        assert '\t"level1"' in result.output
        assert '\t\t"level2"' in result.output

    def test_sort_keys_option(self, runner):
        """Test --sort-keys option."""
        input_json = '{"zebra":1,"apple":2,"middle":3,"banana":4}'
        result = runner.invoke(main, ["--sort-keys"], input=input_json)
        assert result.exit_code == 0
        
        # Keys should appear in alphabetical order
        output = result.output
        assert output.index('"apple"') < output.index('"banana"')
        assert output.index('"banana"') < output.index('"middle"')
        assert output.index('"middle"') < output.index('"zebra"')

    def test_compact_option(self, runner):
        """Test --compact option for minified output."""
        input_json = '{\n  "formatted": true,\n  "spaces": "everywhere"\n}'
        result = runner.invoke(main, ["--compact"], input=input_json)
        assert result.exit_code == 0
        
        # Should be minified
        assert result.output.strip() == '{"formatted":true,"spaces":"everywhere"}'
        assert '\n' not in result.output.strip()

    def test_no_color_option(self, runner):
        """Test --no-color option disables ANSI colors."""
        input_json = '{"test": true, "error": null}'
        
        # First test with color (default)
        result_color = runner.invoke(main, input=input_json)
        
        # Then test without color
        result_no_color = runner.invoke(main, ["--no-color"], input=input_json)
        assert result_no_color.exit_code == 0
        
        # Should not contain ANSI escape codes
        assert '\x1b[' not in result_no_color.output
        assert '\033[' not in result_no_color.output


class TestCLIValidationOption:
    """Test CLI validation-only mode."""

    def test_validate_only_valid_json(self, runner, sample_json_file):
        """Test --validate-only with valid JSON."""
        result = runner.invoke(main, ["--validate-only", str(sample_json_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
        assert "OK" in result.output or "✓" in result.output
        
        # Should NOT output the formatted JSON
        assert '  "name"' not in result.output

    def test_validate_only_invalid_json(self, runner, invalid_json_file):
        """Test --validate-only with invalid JSON."""
        result = runner.invoke(main, ["--validate-only", str(invalid_json_file)])
        assert result.exit_code == 1
        assert "invalid" in result.output.lower()
        assert "Error" in result.output
        
        # Should show error details
        assert "line" in result.output.lower()
        assert "json" in result.output.lower()

    def test_validate_only_from_stdin(self, runner):
        """Test --validate-only with stdin input."""
        valid_json = '{"valid": true}'
        result = runner.invoke(main, ["--validate-only"], input=valid_json)
        assert result.exit_code == 0
        assert "valid" in result.output.lower()
        
        invalid_json = '{"invalid": json}'
        result = runner.invoke(main, ["--validate-only"], input=invalid_json)
        assert result.exit_code == 1
        assert "Error" in result.output


class TestCLIOutputOption:
    """Test CLI output file option."""

    def test_output_to_file(self, runner, sample_json_file, tmp_path):
        """Test --output writes to file instead of stdout."""
        output_file = tmp_path / "output.json"
        
        result = runner.invoke(main, [
            str(sample_json_file),
            "--output", str(output_file),
            "--indent", "4"
        ])
        assert result.exit_code == 0
        
        # Should not print to stdout (except maybe status message)
        assert '  "name"' not in result.output
        
        # Should write to file
        assert output_file.exists()
        content = output_file.read_text()
        assert '    "name": "Test"' in content  # 4-space indent

    def test_output_overwrites_existing_file(self, runner, tmp_path):
        """Test --output overwrites existing file."""
        output_file = tmp_path / "output.json"
        output_file.write_text('{"old": "content"}')
        
        input_json = '{"new": "content"}'
        result = runner.invoke(main, [
            "--output", str(output_file)
        ], input=input_json)
        assert result.exit_code == 0
        
        # Should overwrite
        content = output_file.read_text()
        assert '"new": "content"' in content
        assert '"old"' not in content

    def test_output_creates_directories(self, runner, tmp_path):
        """Test --output creates parent directories if needed."""
        output_file = tmp_path / "new" / "dir" / "output.json"
        
        input_json = '{"test": true}'
        result = runner.invoke(main, [
            "--output", str(output_file)
        ], input=input_json)
        assert result.exit_code == 0
        
        assert output_file.exists()
        assert output_file.parent.exists()


class TestCLIEncodingOption:
    """Test CLI encoding option."""

    def test_encoding_utf8(self, runner, tmp_path):
        """Test --encoding utf-8 (default)."""
        json_file = tmp_path / "utf8.json"
        json_file.write_text('{"text": "Hello 世界"}', encoding='utf-8')
        
        result = runner.invoke(main, [str(json_file), "--encoding", "utf-8"])
        assert result.exit_code == 0
        assert "世界" in result.output

    def test_encoding_latin1(self, runner, tmp_path):
        """Test --encoding latin-1."""
        json_file = tmp_path / "latin1.json"
        json_file.write_text('{"text": "café"}', encoding='latin-1')
        
        result = runner.invoke(main, [str(json_file), "--encoding", "latin-1"])
        assert result.exit_code == 0
        assert "café" in result.output

    def test_encoding_error(self, runner, tmp_path):
        """Test encoding error handling."""
        json_file = tmp_path / "bad_encoding.json"
        # Write UTF-8 content
        json_file.write_text('{"text": "世界"}', encoding='utf-8')
        
        # Try to read as ASCII
        result = runner.invoke(main, [str(json_file), "--encoding", "ascii"])
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "encoding" in result.output.lower() or "decode" in result.output.lower()


class TestCLIErrorHandling:
    """Test CLI error handling and messages."""

    def test_invalid_json_shows_details(self, runner):
        """Test that invalid JSON errors show helpful details."""
        test_cases = [
            ('{"missing": "quote}', "quote"),
            ('{"trailing": "comma",}', "comma"),
            ("{'single': 'quotes'}", "quote"),
            ('{"incomplete": ', "incomplete"),
            ('{]', "bracket")
        ]
        
        for invalid_json, expected_hint in test_cases:
            result = runner.invoke(main, input=invalid_json)
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "JSON" in result.output
            # Should give hints about the error
            assert any(hint in result.output.lower() for hint in [expected_hint, "line", "column", "position"])

    def test_large_file_handling(self, runner, large_json_file):
        """Test handling of large JSON files."""
        result = runner.invoke(main, [str(large_json_file), "--compact"])
        assert result.exit_code == 0
        # Should complete without memory errors

    def test_binary_file_rejection(self, runner, tmp_path):
        """Test that binary files are rejected."""
        binary_file = tmp_path / "binary.json"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04')
        
        result = runner.invoke(main, [str(binary_file)])
        assert result.exit_code == 1
        assert "Error" in result.output
        assert "binary" in result.output.lower() or "decode" in result.output.lower()


class TestCLICombinedOptions:
    """Test combining multiple CLI options."""

    def test_format_and_sort_and_output(self, runner, tmp_path):
        """Test combining format, sort, and output options."""
        input_json = '{"z":1,"a":2,"m":{"y":3,"b":4}}'
        output_file = tmp_path / "sorted.json"
        
        result = runner.invoke(main, [
            "--indent", "4",
            "--sort-keys",
            "--output", str(output_file),
            "--no-color"
        ], input=input_json)
        assert result.exit_code == 0
        
        content = output_file.read_text()
        # Check sorting at all levels
        assert content.index('"a"') < content.index('"m"') < content.index('"z"')
        assert content.index('"b"') < content.index('"y"')
        # Check 4-space indent
        assert '    "a"' in content

    def test_validate_with_format_options(self, runner):
        """Test that format options are ignored with --validate-only."""
        input_json = '{"test": true}'
        result = runner.invoke(main, [
            "--validate-only",
            "--indent", "4",
            "--sort-keys",
            "--compact"  # Contradictory options
        ], input=input_json)
        assert result.exit_code == 0
        
        # Should only show validation result, not formatted output
        assert "valid" in result.output.lower()
        assert '    "test"' not in result.output  # No formatting

    def test_all_options_together(self, runner, tmp_path):
        """Test using many options together."""
        input_file = tmp_path / "input.json"
        output_file = tmp_path / "output.json"
        input_file.write_text('{"z": 1, "a": {"y": 2, "b": 3}}')
        
        result = runner.invoke(main, [
            str(input_file),
            "--indent", "2",
            "--sort-keys",
            "--no-color",
            "--output", str(output_file),
            "--encoding", "utf-8"
        ])
        assert result.exit_code == 0
        
        # Verify output file has all transformations
        content = output_file.read_text()
        assert content.startswith('{')
        assert '  "a"' in content  # 2-space indent
        assert content.index('"a"') < content.index('"z"')  # sorted