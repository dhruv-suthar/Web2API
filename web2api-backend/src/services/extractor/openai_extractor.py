"""
OpenAI Extractor Service

Extracts structured data from markdown content using OpenAI's GPT models.
Supports both JSON Schema and natural language extraction prompts.
"""

import os
import json
import logging
from typing import Dict, Union, Any, Optional
from openai import OpenAI
from openai import APIError, RateLimitError, APITimeoutError, APIConnectionError

from .prompt_builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

# Default model configuration
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 60.0  # seconds
DEFAULT_MAX_RETRIES = 3


async def extract(
    markdown: str,
    schema: Union[str, Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Extract structured data from markdown content using OpenAI.
    
    This function:
    - Takes cleaned markdown content and a schema (JSON Schema or natural language)
    - Sends to OpenAI GPT model with JSON response format
    - Parses and returns extracted data as dictionary
    
    Args:
        markdown: Cleaned markdown content to extract from
        schema: Either a JSON Schema dict or natural language string describing what to extract
        options: Optional dictionary with extraction options:
            - model: OpenAI model to use (default: "gpt-4o-mini")
            - timeout: Request timeout in seconds (default: 60)
            - max_tokens: Maximum tokens in response (default: None, uses model default)
            - temperature: Sampling temperature (default: 0.0 for deterministic)
            - max_retries: Maximum retry attempts (default: 3)
    
    Returns:
        Dictionary with:
            - data: dict - Extracted data matching the schema
            - success: bool - Whether extraction succeeded
            - error: str (optional) - Error message if failed
            - model: str - Model used for extraction
            - usage: dict (optional) - Token usage information
    
    Raises:
        ValueError: If markdown or schema is invalid
    """
    # Validate inputs
    if not markdown or not markdown.strip():
        logger.error("Empty markdown provided to extract")
        raise ValueError("Markdown content cannot be empty")
    
    if not schema:
        logger.error("Empty schema provided to extract")
        raise ValueError("Schema cannot be empty")
    
    # Normalize inputs
    markdown = markdown.strip()
    
    # Parse options with defaults
    options = options or {}
    model = options.get("model", DEFAULT_MODEL)
    timeout = options.get("timeout", DEFAULT_TIMEOUT)
    max_tokens = options.get("max_tokens")
    temperature = options.get("temperature", 0.0)  # 0.0 for deterministic extraction
    max_retries = options.get("max_retries", DEFAULT_MAX_RETRIES)
    
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set in environment")
        return {
            "data": {},
            "success": False,
            "error": "OPENAI_API_KEY environment variable not set",
            "model": model
        }
    
    logger.info("Starting OpenAI extraction", {
        "model": model,
        "markdown_length": len(markdown),
        "schema_type": "string" if isinstance(schema, str) else "json_schema",
        "timeout": timeout
    })
    
    try:
        # Initialize OpenAI client
        client = OpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
        
        # Build prompts
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(schema, markdown)
        
        logger.debug("Built prompts for extraction", {
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt)
        })
        
        # Prepare request parameters
        request_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},  # Force JSON output
            "temperature": temperature
        }
        
        # Add max_tokens if specified
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        # Call OpenAI API
        response = client.chat.completions.create(**request_params)
        
        # Extract response content
        if not response.choices or len(response.choices) == 0:
            logger.error("OpenAI returned empty choices", {
                "model": model,
                "response_id": getattr(response, "id", None)
            })
            return {
                "data": {},
                "success": False,
                "error": "OpenAI returned empty response",
                "model": model
            }
        
        content = response.choices[0].message.content
        if not content:
            logger.error("OpenAI returned empty content", {
                "model": model,
                "response_id": getattr(response, "id", None)
            })
            return {
                "data": {},
                "success": False,
                "error": "OpenAI returned empty content",
                "model": model
            }
        
        # Parse JSON response
        try:
            extracted_data = json.loads(content)
            
            # Extract usage information if available
            usage_info = {}
            if hasattr(response, "usage") and response.usage:
                usage_info = {
                    "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(response.usage, "completion_tokens", None),
                    "total_tokens": getattr(response.usage, "total_tokens", None)
                }
            
            logger.info("OpenAI extraction completed successfully", {
                "model": model,
                "data_keys": list(extracted_data.keys()) if isinstance(extracted_data, dict) else "non-dict",
                "usage": usage_info
            })
            
            return {
                "data": extracted_data,
                "success": True,
                "model": model,
                "usage": usage_info
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            logger.error("JSON parsing error", {
                "error": str(e),
                "content_preview": content[:200] if content else None,
                "model": model
            })
            return {
                "data": {},
                "success": False,
                "error": error_msg,
                "model": model,
                "raw_response": content[:500]  # Include preview for debugging
            }
        
    except RateLimitError as e:
        error_msg = f"OpenAI rate limit exceeded: {str(e)}"
        logger.error("OpenAI rate limit error", {
            "error": str(e),
            "model": model
        })
        return {
            "data": {},
            "success": False,
            "error": error_msg,
            "model": model
        }
        
    except APITimeoutError as e:
        error_msg = f"OpenAI request timeout after {timeout} seconds: {str(e)}"
        logger.error("OpenAI timeout error", {
            "error": str(e),
            "timeout": timeout,
            "model": model
        })
        return {
            "data": {},
            "success": False,
            "error": error_msg,
            "model": model
        }
        
    except APIConnectionError as e:
        error_msg = f"OpenAI connection error: {str(e)}"
        logger.error("OpenAI connection error", {
            "error": str(e),
            "model": model
        })
        return {
            "data": {},
            "success": False,
            "error": error_msg,
            "model": model
        }
        
    except APIError as e:
        error_msg = f"OpenAI API error: {str(e)}"
        error_code = getattr(e, "code", None)
        error_type = getattr(e, "type", None)
        
        logger.error("OpenAI API error", {
            "error": str(e),
            "error_code": error_code,
            "error_type": error_type,
            "model": model
        })
        
        return {
            "data": {},
            "success": False,
            "error": error_msg,
            "model": model,
            "error_code": error_code,
            "error_type": error_type
        }
        
    except ValueError as e:
        error_msg = str(e)
        logger.error("Invalid input to extract", {
            "error": error_msg
        })
        return {
            "data": {},
            "success": False,
            "error": f"Invalid input: {error_msg}",
            "model": model
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error("Unexpected error during OpenAI extraction", {
            "error": error_msg,
            "error_type": error_type,
            "model": model
        })
        return {
            "data": {},
            "success": False,
            "error": f"Unexpected error: {error_msg}",
            "model": model
        }

