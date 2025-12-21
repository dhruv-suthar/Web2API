"""
JSON Schema Validator Service

Validates data against JSON Schema specifications.
Used to verify extracted data matches the expected schema structure.
"""

import logging
from typing import Dict, Any, List, Tuple, Union
import jsonschema
from jsonschema import ValidationError, SchemaError, Draft202012Validator

logger = logging.getLogger(__name__)


def validate(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against a JSON Schema.
    
    This function validates that the provided data conforms to the given JSON Schema.
    It collects all validation errors and returns them in a user-friendly format.
    
    Args:
        data: Dictionary containing the data to validate
        schema: JSON Schema dictionary defining the expected structure
        
    Returns:
        Tuple of (is_valid, errors):
            - is_valid: bool - True if data is valid, False otherwise
            - errors: List[str] - List of error messages (empty if valid)
    
    Examples:
        >>> schema = {
        ...     "type": "object",
        ...     "properties": {
        ...         "name": {"type": "string"},
        ...         "age": {"type": "number"}
        ...     },
        ...     "required": ["name"]
        ... }
        >>> data = {"name": "John", "age": 30}
        >>> is_valid, errors = validate(data, schema)
        >>> is_valid
        True
        >>> errors
        []
        
        >>> invalid_data = {"age": "thirty"}
        >>> is_valid, errors = validate(invalid_data, schema)
        >>> is_valid
        False
        >>> len(errors) > 0
        True
    """
    errors: List[str] = []
    
    # Validate inputs
    if not isinstance(data, dict):
        error_msg = f"Data must be a dictionary, got {type(data).__name__}"
        logger.error("Invalid data type for validation", {
            "data_type": type(data).__name__,
            "expected": "dict"
        })
        return False, [error_msg]
    
    if not isinstance(schema, dict):
        error_msg = f"Schema must be a dictionary, got {type(schema).__name__}"
        logger.error("Invalid schema type for validation", {
            "schema_type": type(schema).__name__,
            "expected": "dict"
        })
        return False, [error_msg]
    
    if not schema:
        error_msg = "Schema cannot be empty"
        logger.error("Empty schema provided for validation")
        return False, [error_msg]
    
    try:
        # First, validate the schema itself
        try:
            # Use Draft202012Validator to validate schema format
            Draft202012Validator.check_schema(schema)
        except SchemaError as e:
            error_msg = f"Invalid JSON Schema: {str(e)}"
            logger.error("Schema validation failed", {
                "error": str(e),
                "schema_path": getattr(e, "path", []),
                "schema_message": getattr(e, "message", "")
            })
            return False, [error_msg]
        
        # Validate data against schema
        # Use validate() which raises ValidationError on first error
        # To collect all errors, we'll use an iterator approach
        validator = Draft202012Validator(schema)
        
        # Collect all validation errors
        validation_errors = list(validator.iter_errors(data))
        
        if validation_errors:
            # Format errors into readable messages
            for error in validation_errors:
                error_path = " -> ".join(str(path) for path in error.absolute_path)
                error_message = error.message
                
                # Build a more descriptive error message
                if error_path:
                    formatted_error = f"{error_path}: {error_message}"
                else:
                    formatted_error = f"Root level: {error_message}"
                
                # Add context about what was expected
                if error.validator == "required":
                    formatted_error += f" (missing required field)"
                elif error.validator == "type":
                    formatted_error += f" (expected {error.validator_value}, got {type(error.instance).__name__})"
                elif error.validator == "enum":
                    formatted_error += f" (must be one of {error.validator_value})"
                
                errors.append(formatted_error)
            
            logger.warn("Data validation failed", {
                "error_count": len(errors),
                "data_keys": list(data.keys()) if isinstance(data, dict) else None,
                "first_error": errors[0] if errors else None
            })
            
            return False, errors
        
        # Validation passed
        logger.debug("Data validation passed", {
            "data_keys": list(data.keys()) if isinstance(data, dict) else None
        })
        
        return True, []
        
    except ValidationError as e:
        # This shouldn't happen if we're using iter_errors, but handle it anyway
        error_path = " -> ".join(str(path) for path in e.absolute_path)
        error_message = e.message
        
        if error_path:
            formatted_error = f"{error_path}: {error_message}"
        else:
            formatted_error = f"Root level: {error_message}"
        
        logger.error("Validation error", {
            "error": str(e),
            "error_path": error_path,
            "error_message": error_message
        })
        
        return False, [formatted_error]
        
    except SchemaError as e:
        # Schema itself is invalid (should have been caught earlier, but handle it)
        error_msg = f"Invalid JSON Schema: {str(e)}"
        logger.error("Schema error during validation", {
            "error": str(e),
            "schema_path": getattr(e, "path", []),
            "schema_message": getattr(e, "message", "")
        })
        return False, [error_msg]
        
    except Exception as e:
        error_msg = f"Unexpected error during validation: {str(e)}"
        error_type = type(e).__name__
        logger.error("Unexpected validation error", {
            "error": str(e),
            "error_type": error_type,
            "data_type": type(data).__name__,
            "schema_keys": list(schema.keys()) if isinstance(schema, dict) else None
        })
        return False, [error_msg]


def validate_strict(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against schema and raise exception on failure.
    
    This is a convenience function that raises ValidationError if validation fails,
    useful when you want exceptions instead of error lists.
    
    Args:
        data: Dictionary containing the data to validate
        schema: JSON Schema dictionary defining the expected structure
        
    Returns:
        True if validation passes
        
    Raises:
        ValidationError: If data doesn't match schema
        SchemaError: If schema is invalid
        ValueError: If inputs are invalid
    """
    if not isinstance(data, dict):
        raise ValueError(f"Data must be a dictionary, got {type(data).__name__}")
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema must be a dictionary, got {type(schema).__name__}")
    
    if not schema:
        raise ValueError("Schema cannot be empty")
    
    # Validate schema format
    Draft202012Validator.check_schema(schema)
    
    # Validate data
    jsonschema.validate(instance=data, schema=schema, cls=Draft202012Validator)
    
    return True

