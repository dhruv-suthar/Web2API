"""
Store Results Event Step

Subscribes to extraction.completed events.
Validates, stores results, updates job status, and caches extraction for future use.

Optimized for Motia Cloud:
- Event payloads kept under 4KB limit
- Large data (extracted data, schema) fetched from state
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.services.validator.json_schema_validator import validate
from src.services.progress.progress_service import update_progress
from src.services.cache.cache_service import cache_extraction_result


# Input schema - minimal payload, large data fetched from state
input_schema = {
    "type": "object",
    "properties": {
        "job_id": {"type": "string"},
        "url": {"type": "string"},
        "scraper_id": {"type": "string"},
        "cached": {"type": "boolean"},
        "cache_type": {"type": "string"}
    },
    "required": ["job_id"]
}

config = {
    "name": "StoreResults",
    "type": "event",
    "description": "Validates and stores extraction results, caches for future use",
    "subscribes": ["extraction.completed"],
    "emits": ["results.stored", "extraction.failed"],
    "flows": ["extraction-flow"],
    "input": input_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/events/ to src/
    "includeFiles": [
        "../../src/services/__init__.py",
        "../../src/services/validator/__init__.py",
        "../../src/services/validator/json_schema_validator.py",
        "../../src/services/progress/__init__.py",
        "../../src/services/progress/progress_service.py",
        "../../src/services/cache/__init__.py",
        "../../src/services/cache/cache_service.py",
    ],
    # Motia Cloud infrastructure config
    "infrastructure": {
        "handler": {
            "ram": 256,
            "timeout": 30
        },
        "queue": {
            "type": "standard",
            "maxRetries": 3,
            "visibilityTimeout": 60
        }
    }
}


async def handler(input_data: Dict[str, Any], context) -> None:
    """
    Handler for storing extraction results - thin controller pattern.
    Fetches large data from state to comply with 4KB event payload limit.
    """
    job_id = input_data.get("job_id", "unknown")
    url = input_data.get("url")
    scraper_id = input_data.get("scraper_id")
    cached = input_data.get("cached", False)
    cache_type = input_data.get("cache_type")
    
    try:
        # 1. Validate required fields
        if not job_id or job_id == "unknown":
            await emit_failure(context, job_id, "job_id is required", "storing")
            return
        
        # 2. Fetch large data from state (stored by extract_with_llm_step or fetch_webpage_step)
        extraction_payload = await context.state.get("extraction_payloads", job_id)
        if not extraction_payload:
            await emit_failure(context, job_id, "Extraction payload not found in state", "storing", url)
            return
        
        extracted_data = extraction_payload.get("data")
        schema = extraction_payload.get("schema")
        model = extraction_payload.get("model")
        usage_info = extraction_payload.get("usage", {})
        metadata = extraction_payload.get("metadata", {})
        
        if not extracted_data:
            await emit_failure(context, job_id, "data is required", "storing", url)
            return
        
        if not isinstance(extracted_data, dict):
            await emit_failure(context, job_id, f"data must be dict, got {type(extracted_data).__name__}", "storing", url)
            return
        
        context.logger.info("Storing extraction results", {
            "job_id": job_id,
            "url": url,
            "cached": cached,
            "cache_type": cache_type
        })
        
        await update_progress(context.streams, job_id, "validating", 90, "Validating results...")
        
        # 3. Validate against JSON Schema if provided
        if schema and isinstance(schema, dict):
            try:
                is_valid, errors = validate(extracted_data, schema)
                if not is_valid:
                    error_msg = f"Validation failed: {', '.join(errors[:3])}"
                    context.logger.error("Validation failed", {"job_id": job_id, "errors": errors[:5]})
                    await emit_failure(context, job_id, error_msg, "storing", url)
                    return
            except Exception as e:
                context.logger.warn("Validation exception", {"job_id": job_id, "error": str(e)})
        
        # 4. Store extraction results
        completed_at = datetime.now(timezone.utc).isoformat()
        
        extraction_result = {
            "job_id": job_id,
            "status": "completed",
            "data": extracted_data,
            "url": url,
            "schema": schema,
            "scraper_id": scraper_id,
            "completed_at": completed_at,
            "model": model,
            "usage": usage_info,
            "cached": cached,
            "metadata": metadata
        }
        
        await context.state.set("extractions", job_id, extraction_result)
        
        # 5. Update job status
        try:
            existing_job_result = await context.state.get("jobs", job_id)
            existing_job = existing_job_result.get("data", existing_job_result) if isinstance(existing_job_result, dict) else {}
            job_metadata = existing_job.copy() if existing_job else {}
            job_metadata.update({
                "status": "completed",
                "completed_at": completed_at,
                "url": url,
                "scraper_id": scraper_id
            })
            await context.state.set("jobs", job_id, job_metadata)
        except Exception:
            pass
        
        # 6. Cache extraction result for future requests
        if not cached or cache_type != "extraction":
            if url and schema:
                cached_ok = await cache_extraction_result(
                    context.state,
                    url,
                    schema,
                    extracted_data,
                    model=model,
                    scraper_id=scraper_id,
                    metadata=metadata
                )
                if cached_ok:
                    context.logger.info("Extraction cached for future use", {"job_id": job_id, "url": url})
        
        # 7. Cleanup extraction payload from state (optional, saves memory)
        try:
            await context.state.delete("extraction_payloads", job_id)
            await context.state.delete("job_payloads", job_id)
        except Exception:
            pass
        
        # 8. Update progress and emit minimal payload
        await update_progress(context.streams, job_id, "completed", 100, "Extraction completed")
        
        await context.emit({
            "topic": "results.stored",
            "data": {
                "job_id": job_id,
                "url": url,
                "scraper_id": scraper_id,
                "completed_at": completed_at,
                "cached": cached
            }
        })
        
        context.logger.info("Store completed", {"job_id": job_id, "url": url})
        
    except Exception as e:
        context.logger.error("Store failed", {"job_id": job_id, "error": str(e)})
        await emit_failure(context, job_id, f"Unexpected error: {str(e)}", "storing", url)


async def emit_failure(context, job_id: str, error: str, stage: str, url: str = None) -> None:
    """Emit extraction.failed event."""
    context.logger.error(f"Store failed: {error}", {"job_id": job_id, "stage": stage})
    await context.emit({
        "topic": "extraction.failed",
        "data": {
            "job_id": job_id,
            "error": error,
            "stage": stage,
            "url": url
        }
    })
