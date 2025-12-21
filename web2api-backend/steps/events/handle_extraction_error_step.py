"""
Handle Extraction Error Event Step

Subscribes to extraction.failed events.
Updates job status to failed and stores error details.
"""

from datetime import datetime, timezone
from typing import Dict, Any

# Import services - paths relative to project root for Motia bundling
from src.services.progress.progress_service import update_progress


# Input schema
input_schema = {
    "type": "object",
    "properties": {
        "job_id": {"type": "string"},
        "error": {"type": "string"},
        "stage": {"type": "string"},
        "url": {"type": "string"},
        "options": {"type": "object"},
        "validation_errors": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["job_id", "error"]
}

config = {
    "name": "HandleExtractionError",
    "type": "event",
    "description": "Handles failed extractions, updates status, logs errors",
    "subscribes": ["extraction.failed"],
    "emits": [],
    "flows": ["extraction-flow"],
    "input": input_schema,
    # Include service/util dependencies for Motia Cloud deployment
    # Paths are relative from steps/events/ to src/
    "includeFiles": [
        "../../src/services/__init__.py",
        "../../src/services/progress/__init__.py",
        "../../src/services/progress/progress_service.py",
    ],
    # Motia Cloud infrastructure config
    "infrastructure": {
        "handler": {
            "ram": 128,
            "timeout": 15
        },
        "queue": {
            "type": "standard",
            "maxRetries": 2,
            "visibilityTimeout": 30
        }
    }
}


async def handler(input_data: Dict[str, Any], context) -> None:
    """
    Handler for extraction failures - thin controller pattern.
    """
    job_id = input_data.get("job_id", "unknown")
    error_message = input_data.get("error", "Unknown error")
    stage = input_data.get("stage", "unknown")
    url = input_data.get("url")
    validation_errors = input_data.get("validation_errors", [])
    
    if not job_id or job_id == "unknown":
        context.logger.error("Error handler missing job_id", {"error": error_message})
        return
    
    failed_at = datetime.now(timezone.utc).isoformat()
    
    context.logger.error("Extraction failed", {
        "job_id": job_id,
        "error": error_message[:200],
        "stage": stage,
        "url": url
    })
    
    try:
        # Update job status to failed
        existing_job_result = await context.state.get("jobs", job_id)
        existing_job = existing_job_result.get("data", existing_job_result) if isinstance(existing_job_result, dict) else {}
        job_metadata = existing_job.copy() if existing_job else {}
        
        job_metadata.update({
            "status": "failed",
            "error": error_message,
            "failed_at": failed_at,
            "stage": stage
        })
        if url:
            job_metadata["url"] = url
        
        await context.state.set("jobs", job_id, job_metadata)
        
        # Store error in extractions
        error_details = {
            "job_id": job_id,
            "status": "failed",
            "error": error_message,
            "stage": stage,
            "failed_at": failed_at,
            "url": url,
            "validation_errors": validation_errors if validation_errors else None
        }
        await context.state.set("extractions", job_id, error_details)
        
    except Exception as e:
        context.logger.error("Failed to store error state", {"job_id": job_id, "error": str(e)})
    
    # Update progress stream
    progress_percent = {"fetching": 20, "extracting": 60, "storing": 90}.get(stage, 50)
    await update_progress(context.streams, job_id, "failed", progress_percent, f"[{stage}] {error_message[:100]}")
    
    context.logger.info("Error handling completed", {"job_id": job_id})

