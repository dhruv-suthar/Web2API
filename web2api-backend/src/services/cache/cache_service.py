"""
Cache Service

Handles caching of extraction results to avoid redundant LLM calls.
Cache key = hash(url + schema) to ensure different schemas get different cache entries.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def generate_extraction_cache_key(url: str, schema: Any) -> str:
    """
    Generate a unique cache key for extraction results.
    
    Key is based on URL + schema, so same URL with different schema = different cache.
    
    Args:
        url: Target URL
        schema: Extraction schema (string or dict)
        
    Returns:
        SHA256 hash string (first 16 chars)
    """
    # Normalize schema to string
    if isinstance(schema, dict):
        schema_str = json.dumps(schema, sort_keys=True)
    else:
        schema_str = str(schema)
    
    combined = f"{url}|{schema_str}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


async def get_cached_extraction(
    state,
    url: str,
    schema: Any
) -> Optional[Dict[str, Any]]:
    """
    Get cached extraction result if available.
    
    Args:
        state: Motia state object
        url: Target URL
        schema: Extraction schema
        
    Returns:
        Cached result dict if found, None otherwise
        {
            "data": {...},
            "url": str,
            "cached_at": str,
            "model": str,
            ...
        }
    """
    try:
        cache_key = generate_extraction_cache_key(url, schema)
        result = await state.get("extraction_cache", cache_key)
        
        if result:
            cached_data = result.get("data", result) if isinstance(result, dict) else result
            if cached_data and cached_data.get("data"):
                return cached_data
        
        return None
    except Exception:
        return None


async def cache_extraction_result(
    state,
    url: str,
    schema: Any,
    extraction_data: Dict[str, Any],
    model: str = None,
    scraper_id: str = None,
    metadata: Dict[str, Any] = None
) -> bool:
    """
    Cache an extraction result.
    
    Args:
        state: Motia state object
        url: Target URL
        schema: Extraction schema
        extraction_data: The extracted data to cache
        model: LLM model used
        scraper_id: Scraper ID
        metadata: Additional metadata
        
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        cache_key = generate_extraction_cache_key(url, schema)
        
        cache_entry = {
            "data": extraction_data,
            "url": url,
            "schema": schema,
            "scraper_id": scraper_id,
            "model": model,
            "metadata": metadata or {},
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        
        await state.set("extraction_cache", cache_key, cache_entry)
        return True
    except Exception:
        return False

