"""
Get Status API Step

Retrieves the current status and progress of an extraction job.
Combines job metadata from state with real-time progress from stream.
"""

from typing import Dict, Any, Optional

from src.utils.state_utils import unwrap_state_data

# Response schema for 200 OK
response_schema_200 = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "Unique job identifier"
        },
        "status": {
            "type": "string",
            "enum": ["queued", "fetching", "fetched", "extracting", "extracted", "validating", "completed", "failed"],
            "description": "Current job status"
        },
        "percent": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Progress percentage (0-100)"
        },
        "message": {
            "type": "string",
            "description": "Optional status message"
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the job was created"
        },
        "updated_at": {
            "type": "string",
            "format": "date-time",
            "description": "When the status was last updated"
        },
        "url": {
            "type": "string",
            "description": "URL being scraped"
        },
        "scraper_id": {
            "type": "string",
            "description": "Scraper identifier used for this extraction"
        },
        "error": {
            "type": "string",
            "description": "Error message (only present if status is 'failed')"
        },
        "stage": {
            "type": "string",
            "description": "Stage where error occurred (only present if status is 'failed')"
        }
    },
    "required": ["job_id", "status", "percent", "created_at"]
}

# Response schema for 400 Bad Request
response_schema_400 = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string"
        }
    },
    "required": ["error"]
}

# Response schema for 404 Not Found
response_schema_404 = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string"
        }
    },
    "required": ["error"]
}

# Response schema for 500 Internal Server Error
response_schema_500 = {
    "type": "object",
    "properties": {
        "error": {
            "type": "string"
        }
    },
    "required": ["error"]
}

response_schema = {
    200: response_schema_200,
    400: response_schema_400,
    404: response_schema_404,
    500: response_schema_500
}

config = {
    "name": "GetStatus",
    "type": "api",
    "path": "/status/:jobId",
    "method": "GET",
    "description": "Get current status and progress of extraction job",
    "emits": [],
    "flows": ["extraction-flow"],
    "responseSchema": response_schema,
    "includeFiles": [
        "../../src/utils/__init__.py",
        "../../src/utils/state_utils.py",
    ]
}


async def get_stream_progress(context, job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get progress data from jobProgress stream.
    
    Args:
        context: Motia context with streams access
        job_id: Job identifier
    
    Returns:
        Progress data dict or None if not found/available
    """
    try:
        if hasattr(context.streams, 'jobProgress'):
            progress = await context.streams.jobProgress.get(job_id, job_id)
            return progress
        else:
            # context.logger.debug("jobProgress stream not available", {"job_id": job_id})
            return None
    except Exception as e:
        # Don't fail if stream access fails - log and return None
        # context.logger.warn("Failed to get stream progress", {
        #     "job_id": job_id,
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return None


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for retrieving job status and progress.
    
    Combines:
    - Job metadata from state (jobs group)
    - Real-time progress from stream (jobProgress stream)
    
    Args:
        req: Request dictionary containing:
            - pathParams: Path parameters containing 'jobId'
            - queryParams: Query parameters (empty for this endpoint)
            - body: Request body (empty for GET requests)
            - headers: Request headers
        context: Motia context containing:
            - state: State manager for retrieving job metadata
            - streams: Stream manager for retrieving progress
            - logger: Logger for structured logging
            - emit: Event emitter (not used in this step)
    
    Returns:
        Response dictionary with status and body containing combined status information
    """
    try:
        # Get job ID from path parameters
        path_params = req.get("pathParams", {})
        job_id = path_params.get("jobId")
        
        if not job_id:
            # context.logger.error("Get status failed - job ID not provided in path")
            return {
                "status": 400,
                "body": {
                    "error": "Job ID is required"
                }
            }
        
        # context.logger.info("Getting job status", {
        #     "job_id": job_id
        # })
        
        # Get job metadata from state
        job_result = await context.state.get("jobs", job_id)
        
        # Check if job exists
        if job_result is None:
            # context.logger.warn("Job not found", {
            #     "job_id": job_id
            # })
            return {
                "status": 404,
                "body": {
                    "error": f"Job with ID '{job_id}' not found"
                }
            }
        
        # Unwrap Motia state data
        job = unwrap_state_data(job_result)
        
        # Get progress from stream
        progress = await get_stream_progress(context, job_id)
        
        # Determine status - prioritize stream status if available, otherwise use job status
        if progress:
            progress_data = unwrap_state_data(progress)
            # Use stream status as it's more up-to-date
            status = progress_data.get("status", job.get("status", "queued"))
            percent = progress_data.get("percent", 0)
            message = progress_data.get("message")
            updated_at = progress_data.get("timestamp")  # Stream timestamp is the updated_at
        else:
            # Fallback to job metadata if stream not available
            status = job.get("status", "queued")
            percent = 0  # Default to 0 if no progress available
            message = None
            updated_at = job.get("updated_at") or job.get("completed_at") or job.get("failed_at") or job.get("created_at")
        
        # If job failed, check for error details
        error = None
        stage = None
        if status == "failed":
            # Check if error is in job metadata
            error = job.get("error")
            # Also check extraction results for error details
            if not error:
                extraction_result = await context.state.get("extractions", job_id)
                extraction = unwrap_state_data(extraction_result)
                if extraction and extraction.get("error"):
                        error = extraction.get("error")
                        stage = extraction.get("stage")
        
        # Build response body
        response_body = {
            "job_id": job_id,
            "status": status,
            "percent": percent,
            "created_at": job.get("created_at"),
            "updated_at": updated_at,
            "url": job.get("url", ""),
            "scraper_id": job.get("scraper_id")
        }
        
        # Add optional fields
        if message:
            response_body["message"] = message
        
        if error:
            response_body["error"] = error
        
        if stage:
            response_body["stage"] = stage
        
        # Remove None values for cleaner response
        response_body = {k: v for k, v in response_body.items() if v is not None}
        
        # context.logger.info("Job status retrieved successfully", {
        #     "job_id": job_id,
        #     "status": status,
        #     "percent": percent
        # })
        
        return {
            "status": 200,
            "body": response_body
        }
        
    except Exception as e:
        # context.logger.error("Failed to get job status - unexpected error", {
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return {
            "status": 500,
            "body": {
                "error": "Failed to get job status"
            }
        }

