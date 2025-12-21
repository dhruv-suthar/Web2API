"""
Extract with LLM Event Step

Subscribes to webpage.fetched events.
Extracts structured data from markdown using OpenAI GPT models.

Optimized for Motia Cloud:
- Event payloads kept under 4KB limit
- Large data (markdown, schema, extracted data) stored in state
"""

from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.utils.state_utils import unwrap_state_data
from src.services.extractor.openai_extractor import extract
from src.services.progress.progress_service import update_progress


# Input schema - minimal payload, large data fetched from state
input_schema = {
    "type": "object",
    "properties": {
        "job_id": {"type": "string"},
        "url": {"type": "string"},
        "scraper_id": {"type": "string"},
        "options": {
            "type": "object",
            "properties": {
                "model": {"type": "string", "default": "gpt-4o-mini"},
                "timeout": {"type": "integer", "default": 60},
                "temperature": {"type": "number", "default": 0.0},
                "max_retries": {"type": "integer", "default": 3}
            }
        },
        "cached": {"type": "boolean"},
        "markdown_length": {"type": "integer"}
    },
    "required": ["job_id"]
}

config = {
    "name": "ExtractWithLLM",
    "type": "event",
    "description": "Extracts structured data from markdown using OpenAI GPT",
    "subscribes": ["webpage.fetched"],
    "emits": ["extraction.completed", "extraction.failed"],
    "flows": ["extraction-flow"],
    "input": input_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/events/ to src/
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/state_utils.py",
        "../../src/services/__init__.py",
        "../../src/services/extractor/__init__.py",
        "../../src/services/extractor/openai_extractor.py",
        "../../src/services/extractor/prompt_builder.py",
        "../../src/services/progress/__init__.py",
        "../../src/services/progress/progress_service.py",
    ],
    # Motia Cloud infrastructure config
    "infrastructure": {
        "handler": {
            "ram": 256,
            "timeout": 120
        },
        "queue": {
            "type": "standard",
            "maxRetries": 3,
            "visibilityTimeout": 150
        }
    }
}


async def handler(input_data: Dict[str, Any], context) -> None:
    """
    Handler for LLM extraction - thin controller pattern.
    Fetches large data from state to comply with 4KB event payload limit.
    """
    job_id = input_data.get("job_id", "unknown")
    url = input_data.get("url")
    scraper_id = input_data.get("scraper_id")
    options = input_data.get("options", {})
    cached = input_data.get("cached", False)
    
    try:
        # 1. Validate input
        if not job_id or job_id == "unknown":
            await emit_failure(context, job_id, "job_id is required", "extracting")
            return
        
        # 2. Fetch large data from state (stored by fetch_webpage_step)
        fetch_payload_result = await context.state.get("fetch_payloads", job_id)
        fetch_payload = unwrap_state_data(fetch_payload_result)
        if not fetch_payload:
            await emit_failure(context, job_id, "Fetch payload not found in state", "extracting", url)
            return
        
        markdown = fetch_payload.get("markdown", "").strip()
        schema = fetch_payload.get("schema")
        metadata = fetch_payload.get("metadata", {})
        
        if not markdown:
            await emit_failure(context, job_id, "markdown is required", "extracting", url)
            return
        
        if not schema:
            await emit_failure(context, job_id, "schema is required", "extracting", url)
            return
        
        # 3. Parse extraction options
        extraction_options = {
            "model": options.get("model", "gpt-4o-mini"),
            "timeout": options.get("timeout", 60),
            "temperature": options.get("temperature", 0.0),
            "max_retries": options.get("max_retries", 3)
        }
        
        context.logger.info("Extracting with LLM", {
            "job_id": job_id,
            "model": extraction_options["model"],
            "content_length": len(markdown)
        })
        
        await update_progress(context.streams, job_id, "extracting", 60, f"Extracting with {extraction_options['model']}...")
        
        # 4. Call extractor service
        result = await extract(markdown, schema, extraction_options)
        
        if not result.get("success"):
            await emit_failure(context, job_id, f"Extraction failed: {result.get('error', 'Unknown')}", "extracting", url)
            return
        
        extracted_data = result.get("data", {})
        if not extracted_data:
            await emit_failure(context, job_id, "Extraction returned empty data", "extracting", url)
            return
        
        # 5. Store extracted data in state (avoids 4KB event limit)
        await context.state.set("extraction_payloads", job_id, {
            "data": extracted_data,
            "schema": schema,
            "model": result.get("model", extraction_options["model"]),
            "usage": result.get("usage", {}),
            "metadata": metadata
        })
        
        # 6. Update progress and emit minimal success payload
        await update_progress(context.streams, job_id, "extracted", 80, "Data extracted")
        
        await context.emit({
            "topic": "extraction.completed",
            "data": {
                "job_id": job_id,
                "url": url,
                "scraper_id": scraper_id,
                "cached": cached
            }
        })
        
        context.logger.info("Extraction completed", {
            "job_id": job_id,
            "model": result.get("model"),
            "data_keys": list(extracted_data.keys()) if isinstance(extracted_data, dict) else "non-dict"
        })
        
        # 7. Cleanup fetch payload from state (optional, saves memory)
        try:
            await context.state.delete("fetch_payloads", job_id)
        except Exception:
            pass
        
    except ValueError as e:
        await emit_failure(context, job_id, f"Invalid input: {str(e)}", "extracting", url)
    except Exception as e:
        context.logger.error("Extraction failed", {"job_id": job_id, "error": str(e)})
        await emit_failure(context, job_id, f"Unexpected error: {str(e)}", "extracting", url)


async def emit_failure(context, job_id: str, error: str, stage: str, url: str = None) -> None:
    """Emit extraction.failed event."""
    context.logger.error(f"Extraction failed: {error}", {"job_id": job_id, "stage": stage})
    await context.emit({
        "topic": "extraction.failed",
        "data": {
            "job_id": job_id,
            "error": error,
            "stage": stage,
            "url": url
        }
    })
