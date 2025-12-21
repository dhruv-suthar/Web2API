"""
Get Results API Step

Retrieves extraction results by job ID.
Returns the extracted data and metadata for a completed extraction job.
"""

from typing import Dict, Any

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
            "enum": ["completed", "failed"],
            "description": "Job status"
        },
        "data": {
            "type": "object",
            "description": "Extracted data matching scraper schema (only present if status is 'completed')"
        },
        "url": {
            "type": "string",
            "description": "URL that was scraped"
        },
        "completed_at": {
            "type": "string",
            "format": "date-time",
            "description": "When extraction completed"
        },
        "cached": {
            "type": "boolean",
            "description": "Whether cached content was used"
        },
        "scraper_id": {
            "type": "string",
            "description": "Scraper identifier used for this extraction"
        },
        "model": {
            "type": "string",
            "description": "OpenAI model used for extraction"
        },
        "usage": {
            "type": "object",
            "description": "Token usage information from OpenAI"
        },
        "metadata": {
            "type": "object",
            "description": "Page metadata from scraper"
        },
        "error": {
            "type": "string",
            "description": "Error message (only present if status is 'failed')"
        },
        "stage": {
            "type": "string",
            "description": "Stage where error occurred (only present if status is 'failed')"
        },
        "validation_errors": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Schema validation errors (only present if validation failed)"
        }
    },
    "required": ["job_id", "status", "url"]
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
    "name": "GetResults",
    "type": "api",
    "path": "/results/:jobId",
    "method": "GET",
    "description": "Retrieve extraction results by job ID",
    "emits": [],
    "flows": ["extraction-flow"],
    "responseSchema": response_schema
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for retrieving extraction results by job ID.
    
    Args:
        req: Request dictionary containing:
            - pathParams: Path parameters containing 'jobId'
            - queryParams: Query parameters (empty for this endpoint)
            - body: Request body (empty for GET requests)
            - headers: Request headers
        context: Motia context containing:
            - state: State manager for retrieving extraction results
            - logger: Logger for structured logging
            - emit: Event emitter (not used in this step)
    
    Returns:
        Response dictionary with status and body containing extraction results or error
    """
    try:
        # Get job ID from path parameters
        path_params = req.get("pathParams", {})
        job_id = path_params.get("jobId")
        
        if not job_id:
            # context.logger.error("Get results failed - job ID not provided in path")
            return {
                "status": 400,
                "body": {
                    "error": "Job ID is required"
                }
            }
        
        # context.logger.info("Getting extraction results", {
        #     "job_id": job_id
        # })
        
        # Get extraction results from state
        extraction_result = await context.state.get("extractions", job_id)
        
        # Check if extraction exists
        if extraction_result is None:
            # context.logger.warn("Extraction results not found", {
            #     "job_id": job_id
            # })
            return {
                "status": 404,
                "body": {
                    "error": f"Extraction results for job ID '{job_id}' not found"
                }
            }
        
        # State returns the extraction dict directly (not wrapped)
        # The extraction dict contains: job_id, data, url, schema, scraper_id, etc.
        extraction = extraction_result if isinstance(extraction_result, dict) else {}
        
        # Check if extraction failed (error stored in extraction)
        if extraction.get("error"):
            # Failed extraction - return error details
            # context.logger.info("Returning failed extraction results", {
            #     "job_id": job_id,
            #     "stage": extraction.get("stage"),
            #     "error": extraction.get("error")
            # })
            
            return {
                "status": 200,
                "body": {
                    "job_id": job_id,
                    "status": "failed",
                    "url": extraction.get("url", ""),
                    "error": extraction.get("error"),
                    "stage": extraction.get("stage", "unknown"),
                    "failed_at": extraction.get("failed_at"),
                    "validation_errors": extraction.get("validation_errors"),
                    "scraper_id": extraction.get("scraper_id"),
                    "schema": extraction.get("schema")
                }
            }
        
        # Successful extraction - return results
        # context.logger.info("Returning successful extraction results", {
        #     "job_id": job_id,
        #     "url": extraction.get("url"),
        #     "has_data": bool(extraction.get("data")),
        #     "cached": extraction.get("cached", False)
        # })
        
        # Build response body
        response_body = {
            "job_id": job_id,
            "status": "completed",
            "data": extraction.get("data", {}),
            "url": extraction.get("url", ""),
            "completed_at": extraction.get("completed_at"),
            "cached": extraction.get("cached", False),
            "scraper_id": extraction.get("scraper_id"),
            "model": extraction.get("model"),
            "usage": extraction.get("usage"),
            "metadata": extraction.get("metadata")
        }
        
        # Only include validation_errors if present
        if extraction.get("validation_errors"):
            response_body["validation_errors"] = extraction.get("validation_errors")
        
        # Remove None values for cleaner response
        response_body = {k: v for k, v in response_body.items() if v is not None}
        
        return {
            "status": 200,
            "body": response_body
        }
        
    except Exception as e:
        # context.logger.error("Failed to get extraction results - unexpected error", {
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return {
            "status": 500,
            "body": {
                "error": "Failed to get extraction results"
            }
        }

