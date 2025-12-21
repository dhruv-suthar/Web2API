"""
Extractor services for structured data extraction from content.

This module provides:
- OpenAI extractor - Uses GPT models to extract structured data
- Prompt builder - Builds prompts for extraction based on schema type
"""

from .openai_extractor import extract
from .prompt_builder import build_system_prompt, build_user_prompt

__all__ = ["extract", "build_system_prompt", "build_user_prompt"]

