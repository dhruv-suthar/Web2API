"""
Prompt Builder Service

Builds prompts for OpenAI extraction based on schema type (JSON Schema vs natural language).
"""

import json
import logging
from typing import Union, Dict, Any

logger = logging.getLogger(__name__)

# System prompt for data extraction
SYSTEM_PROMPT = """You are a data extraction expert. Your job is to extract structured data from webpage content.

Rules:
1. Return ONLY valid JSON matching the requested schema
2. If a field cannot be found, use null
3. For arrays, return empty array [] if no items found
4. For numbers, extract numeric values only (no currency symbols)
5. For dates, use ISO 8601 format (YYYY-MM-DD)
6. For strings, preserve the exact text from the content
7. Do not invent or infer data that isn't explicitly in the content

Be precise. Do not invent data that isn't in the content."""


def build_system_prompt() -> str:
    """
    Build the system prompt for OpenAI extraction.
    
    Returns:
        System prompt string that instructs the model on extraction behavior
    """
    return SYSTEM_PROMPT


def build_user_prompt(schema: Union[str, Dict[str, Any]], markdown: str) -> str:
    """
    Build the user prompt for OpenAI extraction based on schema type.
    
    Handles two schema types:
    1. String (natural language) - e.g., "Extract product name, price, and description"
    2. Dict (JSON Schema) - e.g., {"type": "object", "properties": {...}}
    
    Args:
        schema: Either a natural language string describing what to extract,
                or a JSON Schema dict defining the structure
        markdown: The cleaned markdown content to extract from
        
    Returns:
        Formatted user prompt string
    """
    if not markdown or not markdown.strip():
        logger.warn("Empty markdown provided to build_user_prompt")
        markdown = ""
    
    # Handle string schema (natural language)
    if isinstance(schema, str):
        schema_str = schema.strip()
        if not schema_str:
            logger.warn("Empty string schema provided")
            schema_str = "Extract all relevant information from the content."
        
        prompt = f"""Extract the following information from the content:

{schema_str}

CONTENT:
{markdown}

Return the extracted data as valid JSON."""
        
        return prompt
    
    # Handle dict schema (JSON Schema)
    elif isinstance(schema, dict):
        try:
            # Pretty-print JSON Schema for readability
            schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
            
            prompt = f"""Extract data matching this JSON Schema:

```json
{schema_json}
```

CONTENT:
{markdown}

Return the extracted data as valid JSON matching the schema above."""
            
            return prompt
            
        except (TypeError, ValueError) as e:
            logger.error("Error serializing JSON Schema", {
                "error": str(e),
                "schema_type": type(schema).__name__
            })
            # Fallback to string representation
            schema_str = str(schema)
            prompt = f"""Extract data matching this schema:

{schema_str}

CONTENT:
{markdown}

Return the extracted data as valid JSON."""
            return prompt
    
    # Handle unexpected schema type
    else:
        logger.error("Unexpected schema type", {
            "schema_type": type(schema).__name__,
            "schema": str(schema)[:100]
        })
        # Fallback: treat as string
        schema_str = str(schema)
        prompt = f"""Extract information from the content:

{schema_str}

CONTENT:
{markdown}

Return the extracted data as valid JSON."""
        return prompt

