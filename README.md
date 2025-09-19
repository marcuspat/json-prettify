# JSON Prettify

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful Python CLI tool for pretty-printing JSON with syntax highlighting, validation, and advanced features.

## ✨ Features

- 🎨 **Beautiful syntax highlighting** with Rich terminal library
- 📝 **Flexible formatting** - 2/4 spaces or tab indentation
- 🔍 **JSON validation** with detailed error reporting
- 📊 **JSON statistics** - analyze structure, size, and complexity
- 🛡️ **Schema validation** - validate against JSON Schema files
- 📁 **Multiple file support** with progress bars for large files
- 📤 **Output to file** or stdout
- 🎯 **Compact mode** for minified output
- 🔤 **Key sorting** - alphabetically sort object keys
- 🔧 **Customizable encoding** support
- 📈 **Progress bars** for large file operations
- 🌈 **Color/no-color modes** for different environments

## 🚀 Installation

```bash
pip install json-prettify
```

## 📖 Usage

### Basic Examples

```bash
# Pretty-print a JSON file
json-prettify data.json

# Read from stdin
echo '{"name":"John","age":30,"active":true}' | json-prettify

# Multiple files with separation
json-prettify file1.json file2.json file3.json

# Pipe from curl
curl -s https://api.github.com/users/octocat | json-prettify
```

### 🎨 Formatting Options

```bash
# Custom indentation (2, 4, or tab)
json-prettify data.json --indent 4
json-prettify data.json --indent tab

# Sort keys alphabetically
json-prettify data.json --sort-keys

# Compact output (minified)
json-prettify data.json --compact

# Disable colors (for scripts/CI)
json-prettify data.json --no-color
```

### 🔍 Validation Features

```bash
# Validate JSON syntax only
json-prettify data.json --validate-only

# Validate against JSON Schema
json-prettify data.json --schema schema.json

# Validate multiple files
json-prettify *.json --validate-only
```

### 📊 Advanced Features

```bash
# Show JSON statistics
json-prettify data.json --stats

# Output to file
json-prettify data.json --output formatted.json

# Custom encoding
json-prettify data.json --encoding utf-16

# Combine features
json-prettify data.json --sort-keys --indent 4 --stats --output result.json
```

### 📋 Example Output

**Input JSON:**
```json
{"name":"John","age":30,"city":"New York","hobbies":["reading","gaming"],"active":true}
```

**Pretty-printed with syntax highlighting:**
```json
{
  "name": "John",
  "age": 30,
  "city": "New York",
  "hobbies": [
    "reading",
    "gaming"
  ],
  "active": true
}
```

**With statistics (`--stats`):**
```
=== JSON Statistics ===
Size: 89 bytes
Maximum depth: 2

Type counts:
  Objects: 1
  Arrays: 1
  Strings: 4
  Numbers: 1
  Booleans: 1
  Nulls: 0

Key statistics:
  Total keys: 4
  Unique keys: 4
```

## 🛠️ Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--indent` | `-i` | Number of spaces for indentation (2, 4, or 'tab') (default: 2) |
| `--sort-keys` | `-s` | Sort object keys alphabetically |
| `--compact` | `-c` | Output compact JSON (no pretty-printing) |
| `--validate-only` | `-v` | Only validate JSON, don't format |
| `--no-color` | | Disable syntax highlighting and colored output |
| `--output` | `-o` | Write output to file instead of stdout |
| `--encoding` | `-e` | File encoding (default: utf-8) |
| `--schema` | | Validate JSON against a JSON Schema file |
| `--stats` | | Show JSON statistics (keys, depth, size, etc.) |
| `--version` | | Show version information |
| `--help` | | Show help message |

## 🔧 Advanced Use Cases

### Batch Processing

```bash
# Process all JSON files in a directory
find . -name "*.json" -exec json-prettify {} \;

# Validate all JSON files
json-prettify *.json --validate-only

# Format and save all files
for file in *.json; do
    json-prettify "$file" --output "formatted_$file"
done
```

### Schema Validation

```bash
# Create a schema file
cat > schema.json << 'EOF'
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "age": {"type": "number"},
    "email": {"type": "string", "format": "email"}
  },
  "required": ["name", "age"]
}
EOF

# Validate against schema
json-prettify user.json --schema schema.json
```

### Integration with Other Tools

```bash
# Format API response
curl -s https://api.example.com/data | json-prettify --sort-keys

# Validate and format config files
json-prettify config.json --validate-only && json-prettify config.json --output config_formatted.json

# Extract and format specific fields with jq
jq '.users[] | select(.active == true)' data.json | json-prettify --compact
```

## 📦 Development

This project uses Poetry for dependency management and follows modern Python development practices.

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/json-prettify.git
cd json-prettify

# Install dependencies with Poetry
poetry install

# Or use pip to install in development mode
pip install -e .
```

### Running Tests

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=json_prettify --cov-report=html

# Run specific test file
pytest tests/test_cli.py
```

### Code Quality

```bash
# Format code
black json_prettify tests

# Run linter
ruff check json_prettify tests

# Type checking
mypy json_prettify

# Run all quality checks
ruff check . && black --check . && mypy json_prettify
```

### Building and Publishing

```bash
# Build package
poetry build

# Test publish (dry run)
poetry publish --dry-run

# Publish to PyPI
poetry publish
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [Click](https://github.com/pallets/click) - Command line interface framework
- [Pygments](https://github.com/pygments/pygments) - Syntax highlighting
- [JSONSchema](https://github.com/python-jsonschema/jsonschema) - JSON Schema validation
