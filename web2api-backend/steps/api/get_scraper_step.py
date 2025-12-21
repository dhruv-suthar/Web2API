from typing import Dict, Any

# Response schema for 200 OK
response_schema = {
    200: {
        "type": "object",
        "properties": {
            "scraper_id": {
                "type": "string",
                "description": "Unique scraper identifier"
            },
            "name": {
                "type": "string",
                "description": "Human-readable name for this scraper"
            },
            "description": {
                "type": "string",
                "description": "What this scraper extracts"
            },
            "schema": {
                "description": "The extraction schema (JSON Schema or natural language)"
            },
            "example_url": {
                "type": "string",
                "description": "Example URL this scraper is designed for"
            },
            "webhook_url": {
                "type": "string",
                "description": "Default webhook URL for all extractions from this scraper"
            },
            "schedule": {
                "type": "string",
                "description": "Cron expression for scheduled re-scraping"
            },
            "options": {
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "integer",
                        "description": "Page load timeout in milliseconds"
                    },
                    "use_simple_scraper": {
                        "type": "boolean",
                        "description": "Force simple scraper instead of Firecrawl"
                    },
                    "wait_for": {
                        "type": "integer",
                        "description": "Wait time in ms for JS to render"
                    }
                }
            },
            "endpoint": {
                "type": "string",
                "description": "Full endpoint path: /api/scrape/{scraper_id}"
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "When the scraper was created"
            }
        },
        "required": ["scraper_id", "name", "schema", "endpoint", "created_at"]
    },
    400: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string"
            }
        },
        "required": ["error"]
    },
    404: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string"
            }
        },
        "required": ["error"]
    },
    500: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string"
            }
        },
        "required": ["error"]
    }
}

config = {
    "name": "GetScraper",
    "type": "api",
    "path": "/scrapers/:id",
    "method": "GET",
    "description": "Get a specific scraper by ID",
    "emits": [],
    "flows": ["scraper-management"],
    "responseSchema": response_schema
}


async def handler(req: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Handler for getting a specific scraper by ID.
    
    Args:
        req: Request dictionary containing:
            - pathParams: Path parameters containing 'id' (scraper_id)
            - queryParams: Query parameters (empty for this endpoint)
            - body: Request body (empty for GET requests)
            - headers: Request headers
        context: Motia context containing:
            - state: State manager for retrieving scrapers
            - logger: Logger for structured logging
            - emit: Event emitter (not used in this step)
    
    Returns:
        Response dictionary with status and body containing scraper details or error
    """
    try:
        # Get scraper ID from path parameters
        path_params = req.get("pathParams", {})
        scraper_id = path_params.get("id")
        
        if not scraper_id:
            # context.logger.error("Get scraper failed - scraper ID not provided in path")
            return {
                "status": 400,
                "body": {
                    "error": "Scraper ID is required"
                }
            }
        
        # context.logger.info("Getting scraper", {
        #     "scraper_id": scraper_id
        # })
        
        # Get scraper from state
        scraper = await context.state.get("scrapers", scraper_id)
        
        # Check if scraper exists
        if scraper is None:
            # context.logger.warn("Scraper not found", {
            #     "scraper_id": scraper_id
            # })
            return {
                "status": 404,
                "body": {
                    "error": f"Scraper with ID '{scraper_id}' not found"
                }
            }
        
        # Motia state returns {"data": {...actual_data...}}
        # Extract the actual scraper data from the wrapper
        scraper_data = scraper.get("data", scraper) if isinstance(scraper, dict) else scraper
        
        # Build endpoint URL
        endpoint = f"/api/scrape/{scraper_id}"
        
        # Format response with all scraper details
        response_data = {
            "scraper_id": scraper_data.get("scraper_id"),
            "name": scraper_data.get("name"),
            "description": scraper_data.get("description"),
            "schema": scraper_data.get("schema"),
            "example_url": scraper_data.get("example_url"),
            "webhook_url": scraper_data.get("webhook_url"),
            "schedule": scraper_data.get("schedule"),
            "options": scraper_data.get("options", {}),
            "endpoint": endpoint,
            "created_at": scraper_data.get("created_at")
        }
        
        # context.logger.info("Scraper retrieved successfully", {
        #     "scraper_id": scraper_id,
        #     "name": scraper_data.get("name")
        # })
        
        # Return response
        return {
            "status": 200,
            "body": response_data
        }
        
    except Exception as e:
        # context.logger.error("Failed to get scraper - unexpected error", {
        #     "error": str(e),
        #     "error_type": type(e).__name__
        # })
        return {
            "status": 500,
            "body": {
                "error": "Failed to get scraper"
            }
        }

