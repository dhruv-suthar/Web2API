"""
JSON Schema Validator Service

Validates data against JSON Schema specifications.
"""

from .json_schema_validator import validate, validate_strict

__all__ = ["validate", "validate_strict"]

