"""JSON Schema validation functionality."""

import json
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import jsonschema
from jsonschema import Draft7Validator, ValidationError as SchemaValidationError


class SchemaValidator:
    """Validates JSON data against JSON schemas."""
    
    def __init__(self, schema: Dict[str, Any]):
        """Initialize validator with schema."""
        self.schema = schema
        self.validator = Draft7Validator(schema)
    
    @classmethod
    def from_file(cls, schema_path: Path, encoding: str = 'utf-8') -> 'SchemaValidator':
        """Create validator from schema file."""
        try:
            with open(schema_path, 'r', encoding=encoding) as f:
                schema = json.load(f)
            return cls(schema)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading schema file: {e}")
    
    def validate(self, data: Any) -> List[str]:
        """
        Validate data against schema.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        for error in self.validator.iter_errors(data):
            # Build error path
            path = ""
            if error.path:
                path = "." + ".".join(str(p) for p in error.path)
            
            # Format error message
            if error.validator == 'required':
                errors.append(f"Missing required property '{error.validator_value[0]}' at root{path}")
            elif error.validator == 'type':
                errors.append(f"Invalid type at root{path}: expected {error.validator_value}, got {type(error.instance).__name__}")
            elif error.validator == 'enum':
                errors.append(f"Invalid value at root{path}: must be one of {error.validator_value}")
            elif error.validator == 'pattern':
                errors.append(f"String at root{path} does not match pattern '{error.validator_value}'")
            elif error.validator == 'minLength':
                errors.append(f"String at root{path} is too short (minimum length: {error.validator_value})")
            elif error.validator == 'maxLength':
                errors.append(f"String at root{path} is too long (maximum length: {error.validator_value})")
            elif error.validator == 'minimum':
                errors.append(f"Number at root{path} is below minimum ({error.validator_value})")
            elif error.validator == 'maximum':
                errors.append(f"Number at root{path} exceeds maximum ({error.validator_value})")
            elif error.validator == 'minItems':
                errors.append(f"Array at root{path} has too few items (minimum: {error.validator_value})")
            elif error.validator == 'maxItems':
                errors.append(f"Array at root{path} has too many items (maximum: {error.validator_value})")
            elif error.validator == 'additionalProperties':
                errors.append(f"Additional property not allowed at root{path}")
            else:
                errors.append(f"Schema validation error at root{path}: {error.message}")
        
        return errors
    
    def is_valid(self, data: Any) -> bool:
        """Check if data is valid against schema."""
        return self.validator.is_valid(data)


def validate_against_schema(
    json_data: Union[str, Dict, List], 
    schema_path: Path,
    encoding: str = 'utf-8'
) -> List[str]:
    """
    Validate JSON data against a schema file.
    
    Args:
        json_data: JSON string or parsed data
        schema_path: Path to JSON schema file
        encoding: File encoding
        
    Returns:
        List of error messages (empty if valid)
    """
    # Parse JSON if string
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON: {e}"]
    else:
        data = json_data
    
    # Load and validate against schema
    try:
        validator = SchemaValidator.from_file(schema_path, encoding)
        return validator.validate(data)
    except Exception as e:
        return [f"Schema validation error: {e}"]